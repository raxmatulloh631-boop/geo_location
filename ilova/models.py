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


class Davomat(models.Model):
    STATUS_CHOICES = [
        ('keldi', 'Keldi / Kuzatish shartmas'),
        ('kelmadi', 'Kelmagan / Qidirilmoqda'),
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
