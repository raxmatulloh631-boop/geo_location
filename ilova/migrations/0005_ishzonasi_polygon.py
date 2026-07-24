from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('ilova', '0004_ishzonasi_ishchzona_jarimamukofot'),
    ]
    operations = [
        migrations.AddField(
            model_name='ishzonasi',
            name='polygon_coords',
            field=models.JSONField(blank=True, null=True, verbose_name='Polygon koordinatlar'),
        ),
    ]