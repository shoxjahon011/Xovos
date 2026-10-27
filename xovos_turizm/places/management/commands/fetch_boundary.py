import json
import time
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from places.models import DistrictBoundary

URL = "https://nominatim.openstreetmap.org/search?"
HEADERS = {"User-Agent": "xovos-turizm/1.0 (local development)"}

DEFAULT_QUERIES = [
    "Xovos tumani",
    "Khavast District",
    "Хавастский район",
    "Khavast District Sirdaryo",
]


def search(q):
    params = urllib.parse.urlencode({
        "q": q,
        "format": "jsonv2",
        "polygon_geojson": 1,
        "polygon_threshold": 0.0003,   # nuqtalarni ixchamlashtiradi
        "countrycodes": "uz",
        "limit": 10,
        "accept-language": "uz",
    })
    req = urllib.request.Request(URL + params, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def ring_area(ring):
    lngs = [c[0] for c in ring]
    lats = [c[1] for c in ring]
    return (max(lngs) - min(lngs)) * (max(lats) - min(lats))


def biggest_ring(geom):
    """Polygon yoki MultiPolygon'dan eng katta tashqi halqani oladi."""
    if geom["type"] == "Polygon":
        rings = [geom["coordinates"][0]]
    elif geom["type"] == "MultiPolygon":
        rings = [p[0] for p in geom["coordinates"]]
    else:
        return None
    return max(rings, key=ring_area)


class Command(BaseCommand):
    help = "Xovos tumani chegarasini OpenStreetMap'dan yuklab bazaga saqlaydi"

    def add_arguments(self, parser):
        parser.add_argument("--query", help="Qidiruv matni (ixtiyoriy)")
        parser.add_argument("--list", action="store_true",
                            help="Faqat topilgan natijalarni ko'rsatadi, saqlamaydi")
        parser.add_argument("--pick", type=int,
                            help="Ro'yxatdan shu raqamli natijani tanlaydi")
        parser.add_argument("--file", help="Tayyor .geojson fayldan o'qish")

    def handle(self, *args, **opts):
        if opts["file"]:
            with open(opts["file"], encoding="utf-8") as f:
                gj = json.load(f)
            feats = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
            geom = feats[0].get("geometry", feats[0])
            ring = biggest_ring(geom)
            if not ring:
                raise CommandError("Faylda Polygon topilmadi.")
            self.save(ring, "Xovos tumani")
            return

        queries = [opts["query"]] if opts["query"] else DEFAULT_QUERIES
        found = []
        for q in queries:
            self.stdout.write(f"Qidirilmoqda: {q}")
            try:
                res = search(q)
            except Exception as e:
                raise CommandError(
                    f"OSM'ga ulanib bo'lmadi: {e}\n"
                    "Internet borligini tekshiring yoki keyinroq urinib ko'ring.")
            for r in res:
                g = r.get("geojson")
                if g and g.get("type") in ("Polygon", "MultiPolygon"):
                    if all(r["osm_id"] != x["osm_id"] for x in found):
                        found.append(r)
            if found:
                break
            time.sleep(1.2)   # Nominatim: soniyada 1 tadan ko'p so'rov yo'q

        if not found:
            raise CommandError(
                "Chegara topilmadi. --query bilan boshqa nom sinab ko'ring, "
                "masalan: --query \"Khavast\"")

        # Avval "boundary" turidagilar
        found.sort(key=lambda r: 0 if r.get("category") == "boundary" else 1)

        self.stdout.write("\nTopilgan natijalar:")
        for i, r in enumerate(found):
            ring = biggest_ring(r["geojson"])
            self.stdout.write(
                f"  [{i}] {r['display_name']}\n"
                f"       tur: {r.get('category')}/{r.get('type')}, "
                f"nuqta: {len(ring)}")

        if opts["list"]:
            return

        idx = opts["pick"] if opts["pick"] is not None else 0
        if idx < 0 or idx >= len(found):
            raise CommandError("--pick raqami noto'g'ri.")
        chosen = found[idx]
        self.stdout.write(f"\nTanlandi: [{idx}] {chosen['display_name']}")
        self.save(biggest_ring(chosen["geojson"]), "Xovos tumani")

    def save(self, ring, name):
        pts = [(c[1], c[0]) for c in ring]          # (lat, lng)
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        text = "\n".join(f"{lat:.6f}, {lng:.6f}" for lat, lng in pts)
        DistrictBoundary.objects.update(is_active=False)
        DistrictBoundary.objects.create(name=name, border=text, is_active=True)
        lats = [p[0] for p in pts]
        lngs = [p[1] for p in pts]
        self.stdout.write(self.style.SUCCESS(
            f"Saqlandi: {len(pts)} ta nuqta.\n"
            f"Chegara oralig'i: lat {min(lats):.3f}–{max(lats):.3f}, "
            f"lng {min(lngs):.3f}–{max(lngs):.3f}"))