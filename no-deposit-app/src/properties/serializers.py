from rest_framework import serializers

from .models import Property, RentalApplication


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "address", "rent_amount", "status", "created_at"]
        read_only_fields = ["created_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalApplication
        fields = [
            "id", "property", "tenant", "status",
            "submitted_at", "reviewed_at", "reviewer_sub", "notes",
        ]
        read_only_fields = ["tenant", "status", "submitted_at", "reviewed_at", "reviewer_sub"]


class CreateApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalApplication
        fields = ["property"]


class ReviewApplicationSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approved", "rejected"])
    notes = serializers.CharField(required=False, allow_blank=True)
