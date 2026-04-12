from rest_framework import serializers

from .models import Guarantee


class GuaranteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guarantee
        fields = [
            "id", "application", "certificate_number",
            "valid_until", "status", "document_url", "issued_at", "issued_by_sub",
        ]
        read_only_fields = ["certificate_number", "issued_at", "issued_by_sub"]


class IssueGuaranteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guarantee
        fields = ["application", "valid_until"]


class ValidateGuaranteeSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Guarantee
        fields = ["certificate_number", "status", "valid_until", "is_valid"]

    def get_is_valid(self, obj) -> bool:
        from django.utils import timezone
        return obj.status == "active" and obj.valid_until >= timezone.now().date()
