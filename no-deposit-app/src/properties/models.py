from django.db import models


class Property(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("rented", "Rented"),
        ("inactive", "Inactive"),
    ]

    landlord = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.PROTECT,
        related_name="properties",
        limit_choices_to={"role": "landlord"},
    )
    address = models.TextField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.address[:60]} ({self.status})"


class RentalApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="applications")
    tenant = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.PROTECT,
        related_name="applications",
        limit_choices_to={"role": "tenant"},
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_sub = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Application #{self.pk} — {self.tenant} ({self.status})"
