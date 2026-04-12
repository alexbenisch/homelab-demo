import uuid

from django.db import models


def _default_certificate_number():
    return f"ND-{uuid.uuid4().hex[:10].upper()}"


class Guarantee(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("claimed", "Claimed"),
    ]

    application = models.OneToOneField(
        "properties.RentalApplication",
        on_delete=models.PROTECT,
        related_name="guarantee",
    )
    certificate_number = models.CharField(
        max_length=50, unique=True, default=_default_certificate_number
    )
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    document_url = models.URLField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by_sub = models.CharField(max_length=255)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.certificate_number} ({self.status})"
