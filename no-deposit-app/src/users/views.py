"""GDPR data export and account deletion endpoints."""

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditLog
from core.permissions import IsValidJWT
from users.utils import get_or_create_profile


class MeView(APIView):
    """
    GET  /api/v1/users/me/         — return own profile
    DELETE /api/v1/users/me/       — anonymise all personal data (GDPR erasure)
    """

    permission_classes = [IsValidJWT]

    def get(self, request):
        from .serializers import UserProfileSerializer

        profile = get_or_create_profile(request)
        return Response(UserProfileSerializer(profile).data)

    def delete(self, request):
        profile = get_or_create_profile(request)
        sub = request.auth.sub
        actor_ip = request.META.get("REMOTE_ADDR")

        # Anonymise personal fields; keep the row so FK relations stay intact
        profile.email = ""
        profile.phone = ""
        profile.keycloak_sub = f"deleted-{profile.pk}"
        profile.save(update_fields=["email", "phone", "keycloak_sub", "updated_at"])

        # Anonymise applications submitted by this tenant
        from properties.models import RentalApplication

        RentalApplication.objects.filter(tenant=profile).update(notes="[deleted]")

        AuditLog.record(
            entity_type="UserProfile",
            entity_id=profile.pk,
            action="gdpr_erasure",
            actor_id=sub,
            actor_ip=actor_ip,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeExportView(APIView):
    """
    GET /api/v1/users/me/export/   — full GDPR data export (JSON)
    """

    permission_classes = [IsValidJWT]

    def get(self, request):
        from claims.models import DamageClaim
        from guarantees.models import Guarantee
        from properties.models import RentalApplication

        from .serializers import UserProfileSerializer

        profile = get_or_create_profile(request)

        applications = (
            RentalApplication.objects.select_related("property")
            .filter(tenant=profile)
            .values("id", "property__address", "status", "submitted_at", "reviewed_at", "notes")
        )

        guarantees = Guarantee.objects.filter(application__tenant=profile).values(
            "id", "certificate_number", "valid_until", "status", "issued_at"
        )

        claims = (
            DamageClaim.objects.filter(guarantee__application__property__landlord=profile).values(
                "id", "amount_claimed", "status", "submitted_at"
            )
            if profile.role == "landlord"
            else []
        )

        return Response(
            {
                "exported_at": timezone.now().isoformat(),
                "profile": UserProfileSerializer(profile).data,
                "applications": list(applications),
                "guarantees": list(guarantees),
                "claims": list(claims),
            }
        )
