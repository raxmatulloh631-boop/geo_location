from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ilova', '0003_timefield_defaults'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IshZonasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nomi', models.CharField(max_length=100, verbose_name='Zona nomi')),
                ('markaz_lat', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Markaz (Lat)')),
                ('markaz_lng', models.DecimalField(decimal_places=6, max_digits=10, verbose_name='Markaz (Lng)')),
                ('radius_metr', models.PositiveIntegerField(default=200, verbose_name='Radius (metr)')),
                ('yaratildi', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='IshchiZona',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zonalari', to='ilova.foydalanuvchiprofil')),
                ('zona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ishchilar', to='ilova.ishzonasi')),
            ],
            options={
                'unique_together': {('profil', 'zona')},
            },
        ),
        migrations.CreateModel(
            name='JarimaMukofot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turi', models.CharField(choices=[('jarima', 'Jarima'), ('mukofot', 'Mukofot')], max_length=10)),
                ('miqdor', models.PositiveIntegerField(verbose_name="Miqdor (so'm)")),
                ('sabab', models.TextField(verbose_name='Sabab')),
                ('avtomatik', models.BooleanField(default=False, verbose_name='Avtomatik (geofence)')),
                ('sana', models.DateField(auto_now_add=True)),
                ('profil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jarima_mukofotlar', to='ilova.foydalanuvchiprofil')),
                ('yaratdi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="Kim qo'shdi")),
            ],
        ),
    ]
