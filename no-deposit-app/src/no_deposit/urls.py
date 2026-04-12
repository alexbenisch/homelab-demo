import django_prometheus.urls
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from claims.views import ClaimViewSet
from core.api_views import KYCUploadView, PaymentIntentView
from guarantees.views import GuaranteeViewSet
from properties.views import ApplicationViewSet
from users.views import MeExportView, MeView

router = DefaultRouter()
router.register("applications", ApplicationViewSet, basename="application")
router.register("guarantees", GuaranteeViewSet, basename="guarantee")
router.register("claims", ClaimViewSet, basename="claim")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),
    # API v1
    path("api/v1/", include(router.urls)),
    path("api/v1/documents/upload/", KYCUploadView.as_view(), name="kyc-upload"),
    path("api/v1/payments/intent/", PaymentIntentView.as_view(), name="payment-intent"),
    path("api/v1/users/me/", MeView.as_view(), name="user-me"),
    path("api/v1/users/me/export/", MeExportView.as_view(), name="user-me-export"),
    # OpenAPI schema + Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Portal views
    path("", include("core.urls")),
    # Prometheus metrics — internal only, scraped directly via no-deposit-metrics service
    path("", include(django_prometheus.urls)),
]
