from django.contrib import admin

from .models import DamageClaim


@admin.register(DamageClaim)
class DamageClaimAdmin(admin.ModelAdmin):
    list_display = ["pk", "guarantee", "amount_claimed", "status", "submitted_at", "reviewed_at"]
    list_filter = ["status"]
    search_fields = ["submitted_by_sub", "reviewer_sub", "guarantee__certificate_number"]
    readonly_fields = ["submitted_at", "submitted_by_sub"]
    actions = ["approve", "reject", "set_under_review"]

    @admin.action(description="Set selected claims to Under Review")
    def set_under_review(self, request, queryset):
        queryset.filter(status="open").update(status="under_review")

    @admin.action(description="Approve selected claims")
    def approve(self, request, queryset):
        from django.utils import timezone

        queryset.filter(status="under_review").update(
            status="approved",
            reviewed_at=timezone.now(),
            reviewer_sub=getattr(request, "jwt_sub", "admin"),
        )

    @admin.action(description="Reject selected claims")
    def reject(self, request, queryset):
        from django.utils import timezone

        queryset.filter(status="under_review").update(
            status="rejected",
            reviewed_at=timezone.now(),
            reviewer_sub=getattr(request, "jwt_sub", "admin"),
        )
