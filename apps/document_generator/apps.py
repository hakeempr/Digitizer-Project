from django.apps import AppConfig


class DocumentGeneratorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.document_generator"
    label = "document_generator"
    verbose_name = "Document Generator"
