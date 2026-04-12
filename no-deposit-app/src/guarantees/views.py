from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import AuditLog
from core.permissions import IsValidJWT
from users.utils import get_or_create_profile

from .models import Guarantee
from .serializers import GuaranteeSerializer, IssueGuaranteeSerializer, ValidateGuaranteeSerializer


class GuaranteeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsValidJWT]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        auth = self.request.auth
        if auth.has_role("agent") or auth.has_role("admin"):
            return Guarantee.objects.select_related("application__tenant").all()
        if auth.has_role("landlord"):
            profile = get_or_create_profile(self.request)
            return Guarantee.objects.filter(application__property__landlord=profile).select_related(
                "application"
            )
        if auth.has_role("tenant"):
            profile = get_or_create_profile(self.request)
            return Guarantee.objects.filter(application__tenant=profile).select_related(
                "application"
            )
        return Guarantee.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return IssueGuaranteeSerializer
        if self.action == "validate":
            return ValidateGuaranteeSerializer
        return GuaranteeSerializer

    def create(self, request, *args, **kwargs):
        if not (request.auth.has_role("agent") or request.auth.has_role("admin")):
            return Response({"detail": "Agent role required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = IssueGuaranteeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]
        if application.status != "approved":
            return Response(
                {"detail": "Guarantee can only be issued for approved applications."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if hasattr(application, "guarantee"):
            return Response(
                {"detail": "A guarantee already exists for this application."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        guarantee = serializer.save(issued_by_sub=request.auth.sub)

        # Generate and upload PDF certificate if object storage is configured
        from core.storage import storage_configured

        if storage_configured():
            try:
                from .pdf import generate_certificate_pdf, store_certificate

                pdf_bytes = generate_certificate_pdf(guarantee)
                guarantee.document_url = store_certificate(guarantee, pdf_bytes)
                guarantee.save(update_fields=["document_url"])
            except Exception:
                pass  # Non-fatal; document_url remains blank until retry

        AuditLog.record(
            entity_type="Guarantee",
            entity_id=guarantee.pk,
            action="issued",
            actor_id=request.auth.sub,
            actor_ip=request.META.get("REMOTE_ADDR"),
            payload={"certificate_number": guarantee.certificate_number},
        )
        from notifications.tasks import send_guarantee_issued

        send_guarantee_issued.delay(guarantee.pk)
        return Response(GuaranteeSerializer(guarantee).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="validate", permission_classes=[IsValidJWT])
    def validate(self, request, pk=None):
        guarantee = self.get_object()
        return Response(ValidateGuaranteeSerializer(guarantee).data)
