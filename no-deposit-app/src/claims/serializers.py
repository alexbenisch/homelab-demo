from rest_framework import serializers

from .models import DamageClaim


class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageClaim
        fields = [
            "id", "guarantee", "amount_claimed", "evidence_urls", "status",
            "submitted_at", "submitted_by_sub", "reviewed_at", "reviewer_sub", "reviewer_notes",
        ]
        read_only_fields = ["submitted_at", "submitted_by_sub", "reviewed_at", "reviewer_sub"]


class CreateClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageClaim
        fields = ["guarantee", "amount_claimed", "evidence_urls"]
