import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")


class Category(models.Model):
    name = models.CharField("Nomi", max_length=100)
    icon = models.CharField("Emoji/belgi", max_length=10, blank=True)
    color = models.CharField("Rang", max_length=7, default="#2e7d32")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return f"{self.icon} {self.name}"


class Place(models.Model):
    PRICE_CHOICES = [(0, "Ko'rsatilmagan"), (1, "Arzon"), (2, "O'rtacha"), (3, "Qimmat")]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategoriya")
    name = models.CharField("Nomi", max_length=200)
    description = models.TextField("Tavsif", blank=True)
    address = models.CharField("Manzil", max_length=255, blank=True)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    booking_phone = models.CharField(
        "Bron qilish uchun telefon", max_length=50, blank=True,
        help_text="Bo'sh qolsa, 'Bron qilish' tugmasi chiqmaydi")
    website = models.URLField("Sayt", blank=True)
    telegram = models.CharField("Telegram", max_length=100, blank=True,
                                help_text="@nom yoki to'liq havola")
    lat = models.FloatField("Kenglik (lat)")
    lng = models.FloatField("Uzunlik (lng)")
    photo = models.ImageField("Asosiy rasm", upload_to="places/", blank=True)
    video = models.FileField("Video (fayl)", upload_to="videos/", blank=True,
                            help_text="mp4 (H.264), 30-50 MB dan oshmasin")
    video_url = models.URLField("Video havolasi (YouTube)", blank=True,
                                help_text="Fayl o'rniga YouTube havolasini qo'yish mumkin")
    price_level = models.PositiveSmallIntegerField(
        "Narx darajasi", choices=PRICE_CHOICES, default=0,
        help_text="Choyxona/ovqatlanish joylari uchun. Boshqa joylarga tegmang.")
    price_note = models.CharField("Narx haqida", max_length=120, blank=True,
                                  help_text="Masalan: Osh taxminan 35-45 ming so'm")
    must_see = models.BooleanField("Ko'rishi shart (tavsiya)", default=False)
    always_open = models.BooleanField("Doim ochiq (24/7)", default=False)
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Joy"
        verbose_name_plural = "Joylar"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def is_open_now(self):
        """True = ochiq, False = yopiq, None = ish vaqti kiritilmagan."""
        if self.always_open:
            return True
        now = timezone.localtime()
        today = self.hours.filter(weekday=now.weekday()).first()
        if today is None:
            return None
        if not today.open_time or not today.close_time:
            return False
        return today.open_time <= now.time() <= today.close_time

    def status_text(self):
        s = self.is_open_now()
        return {True: "Hozir ochiq", False: "Hozir yopiq", None: "Ish vaqti noma'lum"}[s]

    def hours_display(self):
        today = timezone.localtime().weekday()
        res = []
        for h in self.hours.all():
            if h.open_time and h.close_time:
                t = f"{h.open_time:%H:%M} – {h.close_time:%H:%M}"
            else:
                t = "Dam olish"
            res.append({"day": h.get_weekday_display(), "time": t,
                        "today": h.weekday == today})
        return res

    def phone_tel(self):
        return re.sub(r"[^\d+]", "", self.phone or "")

    def booking_tel(self):
        return re.sub(r"[^\d+]", "", self.booking_phone or "")

    def telegram_url(self):
        t = (self.telegram or "").strip()
        if not t:
            return ""
        if t.startswith("http"):
            return t
        return "https://t.me/" + t.lstrip("@")

    def photo_urls(self):
        """Asosiy rasm + galereya rasmlari."""
        urls = []
        if self.photo:
            urls.append(self.photo.url)
        for ph in self.photos.all():
            if ph.approved:
                urls.append(ph.image.url)
        return urls

    def youtube_embed(self):
        """YouTube havolasidan embed manzilini yasaydi, bo'lmasa bo'sh qaytaradi."""
        if not self.video_url:
            return ""
        m = re.search(
            r"(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/))"
            r"([A-Za-z0-9_-]{11})", self.video_url)
        if not m:
            return ""
        return f"https://www.youtube-nocookie.com/embed/{m.group(1)}"


class PlacePhoto(models.Model):
    place = models.ForeignKey(Place, related_name="photos", on_delete=models.CASCADE)
    image = models.ImageField("Rasm", upload_to="places/gallery/")
    caption = models.CharField("Izoh", max_length=150, blank=True)
    order = models.PositiveSmallIntegerField("Tartib", default=0)
    approved = models.BooleanField(
        "Tasdiqlangan", default=True,
        help_text="Belgi olib tashlansa, rasm saytda ko'rinmaydi (o'chirmasdan yashirish uchun)")
    client_id = models.CharField(max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Galereya rasmi"
        verbose_name_plural = "Galereya rasmlari"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.place} — rasm {self.pk}"


class WorkingHours(models.Model):
    WEEKDAYS = [(0, "Dushanba"), (1, "Seshanba"), (2, "Chorshanba"),
                (3, "Payshanba"), (4, "Juma"), (5, "Shanba"), (6, "Yakshanba")]
    place = models.ForeignKey(Place, related_name="hours", on_delete=models.CASCADE)
    weekday = models.IntegerField("Hafta kuni", choices=WEEKDAYS)
    open_time = models.TimeField("Ochilish", null=True, blank=True)
    close_time = models.TimeField("Yopilish", null=True, blank=True)

    class Meta:
        verbose_name = "Ish vaqti"
        verbose_name_plural = "Ish vaqtlari"
        ordering = ["weekday"]
        unique_together = ("place", "weekday")

    def __str__(self):
        return self.get_weekday_display()


class Rating(models.Model):
    """Anonim 5 yulduzli baho: bitta qurilma bitta joyga bitta baho beradi."""
    place = models.ForeignKey(Place, related_name="ratings", on_delete=models.CASCADE,
                              verbose_name="Joy")
    client_id = models.CharField(max_length=64)
    stars = models.PositiveSmallIntegerField(
        "Yulduz", validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Baho"
        verbose_name_plural = "Baholar"
        unique_together = ("place", "client_id")

    def __str__(self):
        return f"{self.place} — {self.stars}★"


class Transport(models.Model):
    KINDS = [("bus", "🚌 Avtobus"), ("minibus", "🚐 Marshrutka"),
             ("taxi", "🚕 Taksi"), ("train", "🚆 Poyezd")]

    kind = models.CharField("Turi", max_length=10, choices=KINDS, default="bus")
    name = models.CharField("Nomi", max_length=150,
                            help_text="Masalan: Xovos – Guliston marshrutkasi")
    route = models.CharField("Yo'nalish", max_length=255, blank=True,
                             help_text="Masalan: Xovos → Guliston → Toshkent")
    stop_name = models.CharField("Olib ketish bekati", max_length=200, blank=True)
    stop_lat = models.FloatField("Bekat lat", null=True, blank=True)
    stop_lng = models.FloatField("Bekat lng", null=True, blank=True)
    times = models.TextField(
        "Jo'nash soatlari", blank=True,
        help_text="Har qatorga bitta soat: 06:30. Soat bo'lmasa, pastdagi izohga yozing.")
    note = models.CharField("Izoh", max_length=200, blank=True,
                            help_text="Masalan: Odam to'lganda jo'naydi / 24 soat")
    price = models.CharField("Narxi", max_length=100, blank=True)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Transport"
        verbose_name_plural = "Transport"
        ordering = ["kind", "name"]

    def __str__(self):
        return self.name

    def departures(self):
        return sorted({(int(h), int(m)) for h, m in TIME_RE.findall(self.times or "")})

    def times_list(self):
        return [f"{h:02d}:{m:02d}" for h, m in self.departures()]

    def next_departure(self):
        deps = self.departures()
        if not deps:
            return None
        now = timezone.localtime()
        cur = now.hour * 60 + now.minute
        for h, m in deps:
            t = h * 60 + m
            if t >= cur:
                return {"time": f"{h:02d}:{m:02d}", "text": self._fmt(t - cur),
                        "tomorrow": False}
        h, m = deps[0]
        return {"time": f"{h:02d}:{m:02d}", "text": "", "tomorrow": True}

    @staticmethod
    def _fmt(mins):
        if mins == 0:
            return "hozir"
        h, m = divmod(mins, 60)
        if h and m:
            return f"{h} soat {m} daqiqadan keyin"
        if h:
            return f"{h} soatdan keyin"
        return f"{m} daqiqadan keyin"


class Route(models.Model):
    name = models.CharField("Yo'l nomi", max_length=200)
    destination = models.CharField("Qayoqqa olib boradi", max_length=255, blank=True,
                                   help_text="Masalan: Xovos shahridan Sardoba suv ombori tomon")
    description = models.TextField("Tavsif", blank=True)
    color = models.CharField("Chiziq rangi", max_length=7, default="#c62828")
    coordinates = models.TextField(
        "Koordinatalar",
        help_text="Har qatorga bitta nuqta: lat, lng (masalan: 40.2105, 68.7712). "
                  "Kamida 2 ta nuqta. Yo'l boshidan oxirigacha tartib bilan yozing.")
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Yo'l"
        verbose_name_plural = "Yo'llar"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def points(self):
        pts = []
        for line in self.coordinates.splitlines():
            line = line.strip()
            if not line:
                continue
            a, b = line.replace(";", ",").split(",")[:2]
            pts.append([float(a), float(b)])
        return pts

    def clean(self):
        try:
            pts = self.points()
        except ValueError:
            raise ValidationError({"coordinates": "Har qator 'lat, lng' ko'rinishida bo'lishi kerak."})
        if len(pts) < 2:
            raise ValidationError({"coordinates": "Kamida 2 ta nuqta kerak."})
        for lat, lng in pts:
            if not (39.5 <= lat <= 41.0 and 68.0 <= lng <= 69.5):
                raise ValidationError({"coordinates":
                    f"Nuqta ({lat}, {lng}) Xovos atrofidan tashqarida. "
                    "Tartib: avval lat (taxminan 40.x), keyin lng (taxminan 68.x)."})


class DistrictBoundary(models.Model):
    name = models.CharField("Nomi", max_length=100, default="Xovos tumani")
    border = models.TextField(
        "Chegara nuqtalari",
        help_text="Xaritada chegara bo'ylab bosib chizing. Har qatorda: lat, lng")
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Tuman chegarasi"
        verbose_name_plural = "Tuman chegarasi"

    def __str__(self):
        return self.name

    def points(self):
        pts = []
        for line in self.border.splitlines():
            line = line.strip()
            if not line:
                continue
            a, b = line.replace(";", ",").split(",")[:2]
            pts.append([float(a), float(b)])
        return pts

    def clean(self):
        try:
            pts = self.points()
        except ValueError:
            raise ValidationError({"border": "Har qator 'lat, lng' ko'rinishida bo'lishi kerak."})
        if len(pts) < 3:
            raise ValidationError({"border": "Kamida 3 ta nuqta kerak."})