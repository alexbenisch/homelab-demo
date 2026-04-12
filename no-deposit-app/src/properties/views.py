from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import AuditLog
from core.permissions import IsAgentOrAdmin, IsValidJWT
from users.utils import get_or_create_profile

from .models import Property, RentalApplication
from .serializers import (
    ApplicationSerializer,
    CreateApplicationSerializer,
    PropertySerializer,
    ReviewApplicationSerializer,
)


class PropertyViewSet(viewsets.ModelViewSet):
    """
    Landlords manage their own properties.
    Agents/admins can list all properties (read-only).
    Tenants see all available properties (read-only, for browsing).
    """

    serializer_class = PropertySerializer
    permission_classes = [IsValidJWT]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        auth = self.request.auth
        if auth.has_role("agent") or auth.has_role("admin"):
            return Property.objects.select_related("landlord").all()
        if auth.has_role("landlord"):
            profile = get_or_create_profile(self.request)
            return Property.objects.filter(landlord=profile)
        # Tenants can browse available properties
        return Property.objects.filter(status="available")

    def create(self, request, *args, **kwargs):
        if not request.auth.has_role("landlord"):
            return Response(
                {"detail": "Landlord role required."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = get_or_create_profile(request)
        prop = serializer.save(landlord=profile)
        AuditLog.record(
            entity_type="Property",
            entity_id=prop.pk,
            action="created",
            actor_id=request.auth.sub,
            actor_ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(PropertySerializer(prop).data, status=status.HTTP_201_CREATED)


class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsValidJWT]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        auth = self.request.auth
        if auth.has_role("agent") or auth.has_role("admin"):
            return RentalApplication.objects.select_related("property", "tenant").all()
        profile = get_or_create_profile(self.request)
        return RentalApplication.objects.select_related("property").filter(tenant=profile)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateApplicationSerializer
        if self.action == "review":
            return ReviewApplicationSerializer
        return ApplicationSerializer

    def create(self, request, *args, **kwargs):
        if not request.auth.has_role("tenant"):
            return Response({"detail": "Tenant role required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = get_or_create_profile(request)
        application = serializer.save(tenant=profile)
        AuditLog.record(
            entity_type="RentalApplication",
            entity_id=application.pk,
            action="submitted",
            actor_id=request.auth.sub,
            actor_ip=request.META.get("REMOTE_ADDR"),
        )
        from notifications.tasks import send_application_submitted

        send_application_submitted.delay(application.pk)
        out = ApplicationSerializer(application)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="review", permission_classes=[IsAgentOrAdmin])
    def review(self, request, pk=None):
        application = self.get_object()
        if application.status != "pending":
            return Response(
                {"detail": "Only pending applications can be reviewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReviewApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        notes = serializer.validated_data.get("notes", "")
        application.status = decision
        application.reviewed_at = timezone.now()
        application.reviewer_sub = request.auth.sub
        application.notes = notes
        application.save()
        AuditLog.record(
            entity_type="RentalApplication",
            entity_id=application.pk,
            action=decision,
            actor_id=request.auth.sub,
            actor_ip=request.META.get("REMOTE_ADDR"),
            payload={"notes": notes},
        )
        from notifications.tasks import send_application_reviewed

        send_application_reviewed.delay(application.pk)
        return Response(ApplicationSerializer(application).data)
