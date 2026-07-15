from django.apps import AppConfig


class IlovaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ilova'

    def ready(self):
        import ilova.signals  # noqa: F401
