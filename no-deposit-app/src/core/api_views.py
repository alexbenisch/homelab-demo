import uuid

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsTenant, IsValidJWT
from core.storage import presigned_put_url, storage_configured


class KYCUploadRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.ChoiceField(choices=["image/jpeg", "image/png", "application/pdf"])


class KYCUploadView(APIView):
    """
    Returns a pre-signed PUT URL for direct KYC document upload to Hetzner Object Storage.
    The file is uploaded by the client directly — it never passes through Django.
    """

    permission_classes = [IsTenant]

    def post(self, request):
        serializer = KYCUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not storage_configured():
            return Response(
                {"detail": "Object storage not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        filename = serializer.validated_data["filename"]
        content_type = serializer.validated_data["content_type"]
        key = f"kyc/{request.auth.sub}/{uuid.uuid4().hex}/{filename}"

        upload_url = presigned_put_url(key, content_type=content_type)
        return Response(
            {
                "upload_url": upload_url,
                "key": key,
                "expires_in": settings.S3_PRESIGNED_URL_EXPIRY,
            },
            status=status.HTTP_200_OK,
        )


class PaymentIntentView(APIView):
    """Stub: returns a mock payment intent. Replace with Stripe/Mollie in Phase 6."""

    permission_classes = [IsValidJWT]

    def post(self, request):
        return Response(
            {
                "payment_intent_id": f"pi_stub_{uuid.uuid4().hex[:16]}",
                "status": "requires_payment_method",
                "amount": request.data.get("amount"),
                "currency": request.data.get("currency", "eur"),
                "note": "Payment processing not yet implemented.",
            }
        )
