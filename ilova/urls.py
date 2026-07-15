from django.urls import path

from .views import (
    LokatsiyaYangilashAPI,
    XaritaMalumotlariAPI,
    dashboard_view,
    home_view,
    login_view,
    logout_view,
    mobil_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('mobil/', mobil_view, name='mobil'),
    path('api/update/', LokatsiyaYangilashAPI.as_view(), name='api_update'),
    path('api/map-data/', XaritaMalumotlariAPI.as_view(), name='api_map_data'),
]
