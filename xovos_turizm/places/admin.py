from django.contrib import admin
from .models import (Category, Place, PlacePhoto, WorkingHours, Route,
                     DistrictBoundary, Rating, Transport)


class MapAdminMixin:
    """Admin sahifasiga xarita (Leaflet) qo'shadi."""
    class Media:
        css = {"all": ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",)}
        js = (
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "places/admin_map.js",
        )


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
    extra = 3


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 7
    max_num = 7


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "color")


@admin.register(Place)
class PlaceAdmin(MapAdminMixin, admin.ModelAdmin):
    list_display = ("name", "category", "price_level", "must_see", "phone", "is_active")
    list_filter = ("category", "price_level", "must_see", "is_active")
    search_fields = ("name", "address")
    inlines = [PlacePhotoInline, WorkingHoursInline]


@admin.register(Transport)
class TransportAdmin(MapAdminMixin, admin.ModelAdmin):
    list_display = ("name", "kind", "stop_name", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name", "route", "stop_name")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("place", "stars", "created_at")
    list_filter = ("stars", "place")
    readonly_fields = ("place", "client_id", "stars", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False


@admin.register(Route)
class RouteAdmin(MapAdminMixin, admin.ModelAdmin):
    list_display = ("name", "destination", "color", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "destination")


@admin.register(DistrictBoundary)
class DistrictBoundaryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")

    class Media:
        css = {"all": ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",)}
        js = (
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "places/admin_boundary.js",
        )