from django.db import models


class DamageClaim(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    guarantee = models.ForeignKey(
        "guarantees.Guarantee", on_delete=models.PROTECT, related_name="claims"
    )
    amount_claimed = models.DecimalField(max_digits=10, decimal_places=2)
    evidence_urls = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by_sub = models.CharField(max_length=255)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_sub = models.CharField(max_length=255, blank=True)
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Claim #{self.pk} — {self.amount_claimed} ({self.status})"
