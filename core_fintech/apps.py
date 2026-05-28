from django.apps import AppConfig


class CoreFintechConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core_fintech"

    def ready(self):
        # Importing signals here registers all @receiver decorators
        # with Django's signal dispatcher when the app starts up.
        import core_fintech.signals  # noqa: F401
