from django.apps import AppConfig


class CustomerModuleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.customer_module"
    label = "customer_module"
    verbose_name = "Customer Module"

    def ready(self):
        import apps.customer_module.signals  # noqa: F401
