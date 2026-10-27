from django.core.management.base import BaseCommand
from places.models import Category, Place


class Command(BaseCommand):
    help = "Boshlang'ich kategoriyalarni va bitta namuna joyni yaratadi"

    def handle(self, *args, **opts):
        data = [("Maktab", "🏫", "#1976d2"), ("Muzey", "🏛", "#8e24aa"),
                ("Choyxona", "🍵", "#2e7d32"), ("Hokimiyat", "🏢", "#455a64"),
                ("Adliya", "⚖️", "#6d4c41"), ("Tarixiy joy", "🕌", "#ef6c00"),
                ("Yo'l", "🛣", "#c62828")]
        for name, icon, color in data:
            Category.objects.get_or_create(name=name, defaults={"icon": icon, "color": color})
        cat = Category.objects.get(name="Hokimiyat")
        Place.objects.get_or_create(
            name="NAMUNA: Xovos tumani (o'chirib tashlang)",
            defaults={"category": cat, "lat": 40.2, "lng": 68.77, "always_open": True,
                      "description": "Bu sinov uchun namuna. Haqiqiy koordinatani kiriting."})
        self.stdout.write("Tayyor")