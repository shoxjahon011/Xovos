import json

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.staticfiles import finders
from django.db.models import Avg, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Category, DistrictBoundary, Place, PlacePhoto, Rating, Route, Transport


def places_qs():
    return (Place.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("photos")
            .annotate(avg=Avg("ratings__stars"), cnt=Count("ratings", distinct=True)))


def serialize_place(p):
    photos = p.photo_urls()
    return {
        "id": p.id, "name": p.name, "lat": p.lat, "lng": p.lng,
        "category": p.category_id, "cat_name": p.category.name,
        "icon": p.category.icon, "color": p.category.color,
        "address": p.address,
        "status": p.status_text(), "open": p.is_open_now(),
        "price": p.price_level, "price_note": p.price_note,
        "must_see": p.must_see,
        "avg": round(p.avg, 1) if p.avg else 0, "cnt": p.cnt,
        "photo": photos[0] if photos else "",
        "url": f"/joy/{p.id}/",
    }


def home(request):
    return render(request, "places/home.html")


def map_view(request):
    categories = list(Category.objects.values("id", "name", "icon", "color"))
    places = [serialize_place(p) for p in places_qs()]
    routes = []
    for r in Route.objects.filter(is_active=True):
        pts = r.points()
        if len(pts) >= 2:
            routes.append({
                "id": r.id, "name": r.name, "destination": r.destination,
                "description": r.description, "color": r.color, "points": pts,
            })
    boundary = None
    b = DistrictBoundary.objects.filter(is_active=True).first()
    if b:
        pts = b.points()
        if len(pts) >= 3:
            boundary = pts
    return render(request, "places/map.html", {
        "categories": categories,
        "places": places,
        "routes": routes,
        "boundary": boundary,
    })


def recommend(request):
    places = [serialize_place(p) for p in places_qs()]
    return render(request, "places/recommend.html", {"places": places})


def transport(request):
    items = Transport.objects.filter(is_active=True)
    return render(request, "places/transport.html", {"transports": items})


def place_detail(request, pk):
    place = get_object_or_404(places_qs(), pk=pk)
    rating = {"avg": round(place.avg, 1) if place.avg else 0, "cnt": place.cnt}
    return render(request, "places/detail.html", {
        "place": place,
        "photos": place.photo_urls(),
        "hours": place.hours.all(),
        "youtube": place.youtube_embed(),
        "telegram_url": place.telegram_url(),
        "phone_tel": place.phone_tel(),
        "booking_tel": place.booking_tel(),
        "rating": rating,
    })


def place_json(request, pk):
    """Xarita ustidagi oyna uchun joy ma'lumoti."""
    p = get_object_or_404(places_qs(), pk=pk)
    data = serialize_place(p)
    data.update({
        "description": p.description,
        "phone": p.phone,
        "phone_tel": p.phone_tel(),
        "booking_tel": p.booking_tel(),
        "website": p.website,
        "telegram": p.telegram_url(),
        "photos": p.photo_urls(),
        "always_open": p.always_open,
        "video": p.video.url if p.video else "",
        "youtube": p.youtube_embed(),
        "video_link": p.video_url,
        "hours": p.hours_display(),
    })
    return JsonResponse(data)


@require_POST
def rate_place(request, pk):
    place = get_object_or_404(Place, pk=pk, is_active=True)
    try:
        data = json.loads(request.body)
        stars = int(data.get("stars"))
        client = str(data.get("client_id", ""))[:64]
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "noto'g'ri so'rov"}, status=400)
    if not 1 <= stars <= 5 or len(client) < 8:
        return JsonResponse({"error": "noto'g'ri qiymat"}, status=400)
    Rating.objects.update_or_create(place=place, client_id=client,
                                    defaults={"stars": stars})
    agg = place.ratings.aggregate(avg=Avg("stars"), cnt=Count("id"))
    return JsonResponse({"avg": round(agg["avg"], 1), "count": agg["cnt"]})


MAX_PHOTOS = 15


@require_POST
def upload_photo(request, pk):
    """Foydalanuvchi rasm yuklaydi, rasm darrov chiqadi. O'chirishni faqat admin qiladi."""
    place = get_object_or_404(Place, pk=pk, is_active=True)
    client = request.POST.get("client_id", "")[:64]
    f = request.FILES.get("image")
    if len(client) < 8 or not f:
        return JsonResponse({"error": "Rasm tanlanmadi"}, status=400)
    if f.size > 8 * 1024 * 1024:
        return JsonResponse({"error": "Rasm juda katta (8 MB gacha)"}, status=413)
    if place.photos.count() >= MAX_PHOTOS:
        return JsonResponse({"error": f"Bu joyga {MAX_PHOTOS} tadan ortiq rasm qo'shib bo'lmaydi"}, status=409)
    try:
        forms.ImageField().clean(f)          # haqiqiy rasm ekanini tekshiradi
    except ValidationError:
        return JsonResponse({"error": "Bu fayl rasm emas"}, status=400)
    PlacePhoto.objects.create(place=place, image=f, client_id=client, approved=True)
    return JsonResponse({"ok": True, "left": MAX_PHOTOS - place.photos.count()})


def service_worker(request):
    path = finders.find("places/sw.js")
    with open(path, "rb") as f:
        resp = HttpResponse(f.read(), content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    return resp


def manifest(request):
    path = finders.find("places/manifest.json")
    with open(path, "rb") as f:
        return HttpResponse(f.read(), content_type="application/manifest+json")