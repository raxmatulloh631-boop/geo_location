from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FoydalanuvchiProfil


@receiver(post_save, sender=User)
def ensure_worker_flags(sender, instance, created, **kwargs):
    if created and not instance.is_superuser and instance.is_staff:
        User.objects.filter(pk=instance.pk).update(is_staff=False)


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        FoydalanuvchiProfil.objects.get_or_create(
            user=instance,
            defaults={
                'ism': instance.get_full_name() or instance.username,
                'telefon': '',
            },
        )
