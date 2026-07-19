from datetime import time

from django.contrib.auth.models import User
from django.db import models


class TizimSozlamasi(models.Model):
    REJIM_CHOICES = [
        ('biznes', 'Kompaniya / Ishchilar'),
        ('talim', "O'quv markazi / O'quvchilar"),
    ]
    rejim = models.CharField(max_length=20, choices=REJIM_CHOICES, default='biznes')

    def __str__(self):
        return f"Joriy rejim: {self.get_rejim_display()}"


class FoydalanuvchiProfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    ism = models.CharField(max_length=100, verbose_name='Ismi familyasi')
    telefon = models.CharField(max_length=20, blank=True, default='', verbose_name='Telefon raqami')
    rasm = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Rasm (Avatar)')

    joriy_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    joriy_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    oxirgi_yangilanish = models.DateTimeField(auto_now=True)

    vaqt_boshlanishi = models.TimeField(default=time(8, 0), verbose_name='Boshlanish vaqti')
    vaqt_yakuni = models.TimeField(default=time(17, 0), verbose_name='Tugash vaqti')

    def __str__(self):
        return self.ism or self.user.username


class IshZonasi(models.Model):
    """Ish zonasi — xaritada belgilangan polygon yoki markaz + radius"""
    nomi = models.CharField(max_length=100, verbose_name='Zona nomi')
    markaz_lat = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Markaz (Lat)')
    markaz_lng = models.DecimalField(max_digits=10, decimal_places=6, verbose_name='Markaz (Lng)')
    radius_metr = models.PositiveIntegerField(default=200, verbose_name='Radius (metr)')
    yaratildi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nomi


class IshchiZona(models.Model):
    """Qaysi ishchi qaysi zona bilan bog'liq"""
    profil = models.ForeignKey(FoydalanuvchiProfil, on_delete=models.CASCADE, related_name='zonalari')
    zona = models.ForeignKey(IshZonasi, on_delete=models.CASCADE, related_name='ishchilar')

    class Meta:
        unique_together = ('profil', 'zona')

    def __str__(self):
        return f"{self.profil.ism} → {self.zona.nomi}"


class Davomat(models.Model):
    STATUS_CHOICES = [
        ('keldi', 'Keldi'),
        ('kelmadi', 'Kelmagan'),
    ]
    profil = models.ForeignKey(FoydalanuvchiProfil, on_delete=models.CASCADE, related_name='davomatlari')
    sana = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='kelmadi')

    def __str__(self):
        return f'{self.profil.ism} - {self.sana} - {self.status}'


class HarakatTarixi(models.Model):
    profil = models.ForeignKey(FoydalanuvchiProfil, on_delete=models.CASCADE, related_name='tarixi')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    vaqt = models.DateTimeField(verbose_name='GPS olingan vaqt')

    class Meta:
        ordering = ['vaqt']

    def __str__(self):
        return f'{self.profil.ism} @ {self.vaqt}'


class JarimaMukofot(models.Model):
    TURI_CHOICES = [
        ('jarima', 'Jarima'),
        ('mukofot', 'Mukofot'),
    ]
    profil = models.ForeignKey(FoydalanuvchiProfil, on_delete=models.CASCADE, related_name='jarima_mukofotlar')
    turi = models.CharField(max_length=10, choices=TURI_CHOICES)
    miqdor = models.PositiveIntegerField(verbose_name="Miqdor (so'm)")
    sabab = models.TextField(verbose_name='Sabab')
    avtomatik = models.BooleanField(default=False, verbose_name='Avtomatik (geofence)')
    sana = models.DateField(auto_now_add=True)
    yaratdi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Kim qo\'shdi')

    def __str__(self):
        return f"{self.profil.ism} — {self.turi} — {self.miqdor:,} so'm"
