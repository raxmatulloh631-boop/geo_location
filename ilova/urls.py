from django.urls import path
from .views import (
    LokatsiyaYangilashAPI,
    XaritaMalumotlariAPI,
    dashboard_view,
    hisobot_ishchi_view,
    hisobot_sana_view,
    hisobot_view,
    home_view,
    ishchi_lokatsiya_api,
    ishchi_lokatsiya_view,
    ishchi_tahrirlash_view,
    ishchilar_view,
    jarima_ochir_view,
    jarima_view,
    login_view,
    logout_view,
    mobil_view,
    zona_ochir_view,
    zona_saqlash_api,
    zona_view,
)

urlpatterns = [
    # Asosiy
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Boshliq
    path('ishchilar/', ishchilar_view, name='ishchilar'),
    path('ishchilar/<int:profil_id>/tahrirlash/', ishchi_tahrirlash_view, name='ishchi_tahrirlash'),
    path('ishchilar/<int:profil_id>/lokatsiya/', ishchi_lokatsiya_view, name='ishchi_lokatsiya'),
    path('jarima/', jarima_view, name='jarima'),
    path('jarima/<int:yozuv_id>/ochir/', jarima_ochir_view, name='jarima_ochir'),
    path('zona/', zona_view, name='zona'),
    path('zona/<int:zona_id>/ochir/', zona_ochir_view, name='zona_ochir'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('hisobot/', hisobot_view, name='hisobot'),
    path('hisobot/<int:yil>/<int:oy>/<int:kun>/', hisobot_sana_view, name='hisobot_sana'),
    path('hisobot/ishchi/<int:profil_id>/', hisobot_ishchi_view, name='hisobot_ishchi'),

    # Ishchi
    path('mobil/', mobil_view, name='mobil'),

    # API
    path('api/update/', LokatsiyaYangilashAPI.as_view(), name='api_update'),
    path('api/map-data/', XaritaMalumotlariAPI.as_view(), name='api_map_data'),
    path('api/ishchi/<int:profil_id>/lokatsiya/', ishchi_lokatsiya_api, name='api_ishchi_lokatsiya'),
    path('api/zona/saqlash/', zona_saqlash_api, name='api_zona_saqlash'),
]
