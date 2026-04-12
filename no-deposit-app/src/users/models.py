from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("tenant", "Tenant"),
        ("landlord", "Landlord"),
        ("agent", "Agent"),
        ("admin", "Admin"),
    ]

    keycloak_sub = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.role}:{self.email or self.keycloak_sub[:12]}"
