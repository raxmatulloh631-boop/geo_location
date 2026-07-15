from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Davomat, FoydalanuvchiProfil, HarakatTarixi, TizimSozlamasi


class FoydalanuvchiProfilInline(admin.StackedInline):
    model = FoydalanuvchiProfil
    can_delete = False
    extra = 0
    fields = (
        'ism', 'telefon', 'rasm',
        'vaqt_boshlanishi', 'vaqt_yakuni',
        'joriy_latitude', 'joriy_longitude', 'oxirgi_yangilanish',
    )
    readonly_fields = ('joriy_latitude', 'joriy_longitude', 'oxirgi_yangilanish')


class WorkerUserAdmin(BaseUserAdmin):
    inlines = [FoydalanuvchiProfilInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')

    def get_inline_instances(self, request, obj=None):
        # Yangi user: signal profil yaratadi — UNIQUE konflikt bo'lmasin
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        if not obj.is_superuser and not request.user.is_superuser:
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'is_staff' in form.base_fields:
                form.base_fields['is_staff'].disabled = True
                form.base_fields['is_staff'].initial = False
        return form


admin.site.unregister(User)
admin.site.register(User, WorkerUserAdmin)


@admin.register(TizimSozlamasi)
class TizimSozlamasiAdmin(admin.ModelAdmin):
    list_display = ['rejim']


@admin.register(FoydalanuvchiProfil)
class FoydalanuvchiProfilAdmin(admin.ModelAdmin):
    list_display = ['ism', 'telefon', 'user', 'vaqt_boshlanishi', 'vaqt_yakuni', 'oxirgi_yangilanish']
    search_fields = ['ism', 'telefon', 'user__username']
    list_select_related = ['user']
    readonly_fields = ['joriy_latitude', 'joriy_longitude', 'oxirgi_yangilanish']


@admin.register(Davomat)
class DavomatAdmin(admin.ModelAdmin):
    list_display = ['profil', 'sana', 'status']
    list_filter = ['status', 'sana']


@admin.register(HarakatTarixi)
class HarakatTarixiAdmin(admin.ModelAdmin):
    list_display = ['profil', 'latitude', 'longitude', 'vaqt']
    list_filter = ['profil', 'vaqt']
