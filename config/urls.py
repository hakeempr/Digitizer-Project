"""Root URL configuration for Handwritten Notes Digitizer."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("django-admin/",    admin.site.urls),
    path("api/v1/auth/",     include("apps.accounts.urls")),
    path("api/v1/admin/",    include("apps.admin_module.urls")),
    path("api/v1/customer/", include("apps.customer_module.urls")),
    path("api/v1/ocr/",      include("apps.ocr_engine.urls")),
    path("api/v1/documents/",include("apps.document_generator.urls")),
    path("api/v1/notify/",   include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
