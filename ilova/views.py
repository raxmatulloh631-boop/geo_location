from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Davomat, FoydalanuvchiProfil, HarakatTarixi, TizimSozlamasi


def _is_boshliq(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _gps_context():
    seconds = getattr(settings, 'GPS_UPDATE_INTERVAL_SECONDS', 300)
    return {
        'gps_interval_ms': seconds * 1000,
        'gps_interval_minutes': max(1, round(seconds / 60)),
    }


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if _is_boshliq(request.user):
        return redirect('dashboard')
    return redirect('mobil')


@login_required
@user_passes_test(_is_boshliq, login_url='mobil')
def dashboard_view(request):
    return render(request, 'dashboard.html')


@login_required
def mobil_view(request):
    try:
        profil = request.user.profil
    except FoydalanuvchiProfil.DoesNotExist:
        profil = None
    ctx = _gps_context()
    ctx['profil'] = profil
    return render(request, 'mobil.html', ctx)


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
                    batch.append(
                        HarakatTarixi(
                            profil=profil,
                            latitude=nuqta['latitude'],
                            longitude=nuqta['longitude'],
                            vaqt=vaqt,
                        )
                    )
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
            except (TypeError, ValueError):
                return Response({'error': "Noto'g'ri koordinatalar"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Muvaffaqiyatli yangilandi'}, status=status.HTTP_200_OK)


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
                onlayn_status = (
                    'onlayn'
                    if (timezone.now() - p.oxirgi_yangilanish).total_seconds() <= 900
                    else 'oflayn'
                )
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
