from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import AuditLog
from core.permissions import IsAgentOrAdmin, IsValidJWT
from users.utils import get_or_create_profile

from .models import DamageClaim
from .serializers import ClaimSerializer, CreateClaimSerializer, ReviewClaimSerializer


class ClaimViewSet(viewsets.ModelViewSet):
    permission_classes = [IsValidJWT]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        auth = self.request.auth
        if auth.has_role("agent") or auth.has_role("admin"):
            return DamageClaim.objects.select_related("guarantee").all()
        if auth.has_role("landlord"):
            profile = get_or_create_profile(self.request)
            return DamageClaim.objects.filter(
                guarantee__application__property__landlord=profile
            ).select_related("guarantee")
        return DamageClaim.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateClaimSerializer
        return ClaimSerializer

    def create(self, request, *args, **kwargs):
        if not request.auth.has_role("landlord"):
            return Response({"detail": "Landlord role required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CreateClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        guarantee = serializer.validated_data["guarantee"]
        if guarantee.status != "active":
            return Response(
                {"detail": "Claims can only be submitted against active guarantees."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        claim = serializer.save(submitted_by_sub=request.auth.sub)
        AuditLog.record(
            entity_type="DamageClaim",
            entity_id=claim.pk,
            action="submitted",
            actor_id=request.auth.sub,
            actor_ip=request.META.get("REMOTE_ADDR"),
            payload={"amount_claimed": str(claim.amount_claimed)},
        )
        from notifications.tasks import send_claim_submitted

        send_claim_submitted.delay(claim.pk)
        return Response(ClaimSerializer(claim).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="review", permission_classes=[IsAgentOrAdmin])
    def review(self, request, pk=None):
        claim = self.get_object()
        if claim.status in ("approved", "rejected"):
            return Response(
                {"detail": "Claim has already been resolved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReviewClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        notes = serializer.validated_data.get("notes", "")
        claim.status = decision
        claim.reviewed_at = timezone.now()
        claim.reviewer_sub = request.auth.sub
        claim.reviewer_notes = notes
        claim.save()
        AuditLog.record(
            entity_type="DamageClaim",
            entity_id=claim.pk,
            action=decision,
            actor_id=request.auth.sub,
            actor_ip=request.META.get("REMOTE_ADDR"),
            payload={"notes": notes},
        )
        return Response(ClaimSerializer(claim).data)
