from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.landing, name="landing"),
    path("tenant/", views.tenant_portal, name="tenant"),
    path("landlord/", views.landlord_portal, name="landlord"),
    path("agency/", views.agency_portal, name="agency"),
]
