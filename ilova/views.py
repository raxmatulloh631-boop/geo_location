import math
from datetime import time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Davomat, FoydalanuvchiProfil, HarakatTarixi,
    IshZonasi, IshchiZona, JarimaMukofot, TizimSozlamasi
)


def _is_boshliq(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _gps_context():
    from django.conf import settings
    seconds = getattr(settings, 'GPS_UPDATE_INTERVAL_SECONDS', 300)
    return {
        'gps_interval_ms': seconds * 1000,
        'gps_interval_minutes': max(1, round(seconds / 60)),
    }


# ── Asosiy yo'naltirish ──────────────────────────────────────────────────────

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if _is_boshliq(request.user):
        return redirect('ishchilar')
    return redirect('mobil')


# ── Login / Logout ────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return home_view(request)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return home_view(request)
        return render(request, 'login.html', {'error': 'Login yoki parol xato!'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Ishchi mobil panel ────────────────────────────────────────────────────────

@login_required
def mobil_view(request):
    try:
        profil = request.user.profil
    except FoydalanuvchiProfil.DoesNotExist:
        profil = None
    ctx = _gps_context()
    ctx['profil'] = profil
    return render(request, 'mobil.html', ctx)


# ── Dashboard (eski xarita) ───────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def dashboard_view(request):
    return render(request, 'dashboard.html')


# ── Ishchilar ro'yxati ────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def ishchilar_view(request):
    profillar = FoydalanuvchiProfil.objects.select_related('user').filter(
        user__is_staff=False, user__is_superuser=False
    ).order_by('ism')
    return render(request, 'ishchilar.html', {'profillar': profillar})


# ── Ishchi tahrirlash ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def ishchi_tahrirlash_view(request, profil_id):
    profil = get_object_or_404(FoydalanuvchiProfil, id=profil_id,
                                user__is_staff=False, user__is_superuser=False)
    zonalar = IshZonasi.objects.all()
    tanlangan_zonalar = profil.zonalari.values_list('zona_id', flat=True)

    if request.method == 'POST':
        # Ish vaqti
        vaqt_b = request.POST.get('vaqt_boshlanishi', '08:00')
        vaqt_y = request.POST.get('vaqt_yakuni', '17:00')
        try:
            h_b, m_b = map(int, vaqt_b.split(':'))
            h_y, m_y = map(int, vaqt_y.split(':'))
            profil.vaqt_boshlanishi = time(h_b, m_b)
            profil.vaqt_yakuni = time(h_y, m_y)
        except (ValueError, AttributeError):
            pass

        # Ism, telefon
        profil.ism = request.POST.get('ism', profil.ism).strip()
        profil.telefon = request.POST.get('telefon', profil.telefon).strip()
        profil.save()

        # Zonalar
        zona_idlar = request.POST.getlist('zonalar')
        profil.zonalari.all().delete()
        for zid in zona_idlar:
            try:
                zona = IshZonasi.objects.get(id=int(zid))
                IshchiZona.objects.create(profil=profil, zona=zona)
            except (IshZonasi.DoesNotExist, ValueError):
                pass

        return redirect('ishchilar')

    ctx = {
        'profil': profil,
        'zonalar': zonalar,
        'tanlangan_zonalar': list(tanlangan_zonalar),
    }
    return render(request, 'ishchi_tahrirlash.html', ctx)


# ── Ishchi lokatsiyasi ────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def ishchi_lokatsiya_view(request, profil_id):
    profil = get_object_or_404(FoydalanuvchiProfil, id=profil_id,
                                user__is_staff=False, user__is_superuser=False)
    return render(request, 'ishchi_lokatsiya.html', {'profil': profil})


# ── Jarima / Mukofot ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def jarima_view(request):
    profillar = FoydalanuvchiProfil.objects.filter(
        user__is_staff=False, user__is_superuser=False
    ).order_by('ism')
    yozuvlar = JarimaMukofot.objects.select_related('profil', 'yaratdi').order_by('-sana', '-id')

    if request.method == 'POST':
        profil_id = request.POST.get('profil_id')
        turi = request.POST.get('turi')
        miqdor = request.POST.get('miqdor', '0').replace(' ', '').replace(',', '')
        sabab = request.POST.get('sabab', '').strip()

        try:
            profil = FoydalanuvchiProfil.objects.get(id=int(profil_id))
            JarimaMukofot.objects.create(
                profil=profil,
                turi=turi,
                miqdor=int(miqdor),
                sabab=sabab,
                avtomatik=False,
                yaratdi=request.user,
            )
        except (FoydalanuvchiProfil.DoesNotExist, ValueError):
            pass
        return redirect('jarima')

    ctx = {'profillar': profillar, 'yozuvlar': yozuvlar}
    return render(request, 'jarima.html', ctx)


@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def jarima_ochir_view(request, yozuv_id):
    yozuv = get_object_or_404(JarimaMukofot, id=yozuv_id)
    yozuv.delete()
    return redirect('jarima')


# ── Ish zonalari ─────────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def zona_view(request):
    zonalar = IshZonasi.objects.all().order_by('-yaratildi')
    return render(request, 'zona.html', {'zonalar': zonalar})


@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def zona_ochir_view(request, zona_id):
    zona = get_object_or_404(IshZonasi, id=zona_id)
    zona.delete()
    return redirect('zona')


# ── API: Zona saqlash ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def zona_saqlash_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST kerak'}, status=405)
    import json
    try:
        data = json.loads(request.body)
        nomi = data.get('nomi', '').strip()
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        radius = int(data.get('radius', 200))
        if not nomi:
            return JsonResponse({'error': 'Zona nomi kiriting'}, status=400)
        zona = IshZonasi.objects.create(nomi=nomi, markaz_lat=lat, markaz_lng=lng, radius_metr=radius)
        return JsonResponse({'id': zona.id, 'nomi': zona.nomi})
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# ── API: Ishchi lokatsiyasi (AJAX) ────────────────────────────────────────────

@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def ishchi_lokatsiya_api(request, profil_id):
    profil = get_object_or_404(FoydalanuvchiProfil, id=profil_id)
    if profil.oxirgi_yangilanish:
        delta = (timezone.now() - profil.oxirgi_yangilanish).total_seconds()
        onlayn = delta <= 60
    else:
        onlayn = False

    return JsonResponse({
        'ism': profil.ism,
        'telefon': profil.telefon,
        'lat': float(profil.joriy_latitude) if profil.joriy_latitude else None,
        'lng': float(profil.joriy_longitude) if profil.joriy_longitude else None,
        'onlayn': onlayn,
        'vaqt': profil.oxirgi_yangilanish.strftime('%H:%M:%S') if profil.oxirgi_yangilanish else '—',
        'rasm': profil.rasm.url if profil.rasm else '/static/default_avatar.png',
    })


# ── API: GPS yangilash (ishchi tomonidan) ─────────────────────────────────────

class LokatsiyaYangilashAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            profil = request.user.profil
        except FoydalanuvchiProfil.DoesNotExist:
            return Response(
                {'error': "Profil topilmadi. Admin sizga profil yaratishi kerak."},
                status=status.HTTP_404_NOT_FOUND,
            )

        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        is_mock = request.data.get('is_mock_location', False)
        oflayn_nuqtalar = request.data.get('oflayn_nuqtalar') or []

        if is_mock in (True, 'true', 'True', 1, '1'):
            return Response({'error': 'Fake GPS taqiqlangan!'}, status=status.HTTP_400_BAD_REQUEST)

        if oflayn_nuqtalar:
            batch = []
            for nuqta in oflayn_nuqtalar:
                try:
                    vaqt = parse_datetime(str(nuqta.get('vaqt', ''))) or timezone.now()
                    if timezone.is_naive(vaqt):
                        vaqt = timezone.make_aware(vaqt, timezone.get_current_timezone())
                    batch.append(HarakatTarixi(
                        profil=profil,
                        latitude=nuqta['latitude'],
                        longitude=nuqta['longitude'],
                        vaqt=vaqt,
                    ))
                except (KeyError, TypeError, ValueError):
                    continue
            if batch:
                HarakatTarixi.objects.bulk_create(batch)

        if lat is not None and lng is not None:
            try:
                profil.joriy_latitude = float(lat)
                profil.joriy_longitude = float(lng)
                profil.save(update_fields=['joriy_latitude', 'joriy_longitude', 'oxirgi_yangilanish'])
                HarakatTarixi.objects.create(
                    profil=profil,
                    latitude=profil.joriy_latitude,
                    longitude=profil.joriy_longitude,
                    vaqt=timezone.now(),
                )

                # Geofence tekshirish — ish vaqtida zonadan tashqarida bo'lsa jarima
                _geofence_tekshir(profil, float(lat), float(lng))

            except (TypeError, ValueError):
                return Response({'error': "Noto'g'ri koordinatalar"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Muvaffaqiyatli yangilandi'}, status=status.HTTP_200_OK)


def _geofence_tekshir(profil, lat, lng):
    """Ishchi ish vaqtida zona tashqarisida bo'lsa avtomatik jarima yoz"""
    hozir = timezone.localtime()
    hozir_vaqt = hozir.time()

    # Ish vaqti ichida emasmi?
    if not (profil.vaqt_boshlanishi <= hozir_vaqt <= profil.vaqt_yakuni):
        return

    # Ishchiga bog'liq zonalar bormi?
    ishchi_zonalar = profil.zonalari.select_related('zona').all()
    if not ishchi_zonalar.exists():
        return

    # Kamida bitta zonada bo'lsa — jarima yo'q
    for iz in ishchi_zonalar:
        z = iz.zona
        d = _masofa(lat, lng, float(z.markaz_lat), float(z.markaz_lng))
        if d <= z.radius_metr:
            return  # Zona ichida — OK

    # Barcha zonalardan tashqarida — bugun jarima yozilganmi?
    bugun = hozir.date()
    allaqachon = JarimaMukofot.objects.filter(
        profil=profil, avtomatik=True, sana=bugun
    ).exists()
    if allaqachon:
        return

    JarimaMukofot.objects.create(
        profil=profil,
        turi='jarima',
        miqdor=0,
        sabab=f"Ish zonasidan tashqarida aniqlandi ({hozir.strftime('%H:%M')})",
        avtomatik=True,
    )


def _masofa(lat1, lng1, lat2, lng2):
    """Ikki nuqta orasidagi masofa (metr)"""
    R = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── API: Xarita ma'lumotlari ──────────────────────────────────────────────────

class XaritaMalumotlariAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        sozlama = TizimSozlamasi.objects.first()
        rejim = sozlama.rejim if sozlama else 'biznes'
        bugun = timezone.localdate()
        aktiv_profillar = []

        for p in FoydalanuvchiProfil.objects.select_related('user'):
            if p.user.is_staff or p.user.is_superuser:
                continue

            davomat = Davomat.objects.filter(profil=p, sana=bugun).first()
            status_text = davomat.status if davomat else 'kelmadi'
            if rejim == 'talim' and status_text == 'keldi':
                continue

            if p.oxirgi_yangilanish:
                delta = (timezone.now() - p.oxirgi_yangilanish).total_seconds()
                onlayn_status = 'onlayn' if delta <= 60 else 'oflayn'
            else:
                onlayn_status = 'oflayn'

            aktiv_profillar.append({
                'id': p.id,
                'ism': p.ism,
                'telefon': p.telefon,
                'rasm': p.rasm.url if p.rasm else '/static/default_avatar.png',
                'lat': float(p.joriy_latitude) if p.joriy_latitude is not None else None,
                'lng': float(p.joriy_longitude) if p.joriy_longitude is not None else None,
                'status': status_text,
                'aloqa': onlayn_status,
                'vaqt_boshlanishi': p.vaqt_boshlanishi.strftime('%H:%M'),
                'vaqt_yakuni': p.vaqt_yakuni.strftime('%H:%M'),
            })

        return Response({'rejim': rejim, 'majliz': aktiv_profillar})
