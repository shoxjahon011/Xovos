from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('xarita/', views.map_view, name='map'),
    path('tavsiya/', views.recommend, name='recommend'),
    path('transport/', views.transport, name='transport'),
    path('joy/<int:pk>/', views.place_detail, name='detail'),
    path('api/joy/<int:pk>/', views.place_json, name='place_json'),
    path('api/joy/<int:pk>/baho/', views.rate_place, name='rate'),
    path('api/joy/<int:pk>/rasm/', views.upload_photo, name='upload_photo'),
    path('sw.js', views.service_worker),
    path('manifest.json', views.manifest),
]