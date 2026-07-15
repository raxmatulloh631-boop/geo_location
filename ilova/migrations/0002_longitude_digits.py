# Generated for longitude max_digits and telefon blank

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ilova', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foydalanuvchiprofil',
            name='joriy_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='foydalanuvchiprofil',
            name='telefon',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Telefon raqami'),
        ),
        migrations.AlterField(
            model_name='harakattarixi',
            name='longitude',
            field=models.DecimalField(decimal_places=6, max_digits=10),
        ),
    ]
