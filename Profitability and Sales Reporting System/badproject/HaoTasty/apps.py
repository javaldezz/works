from django.apps import AppConfig

class HaotastyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "HaoTasty"

    def ready(self):
        import HaoTasty.signals  # import signals file
