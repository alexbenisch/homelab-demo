from django.contrib import admin

from .models import Property, RentalApplication


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["address", "landlord", "rent_amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["address", "landlord__email"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(RentalApplication)
class RentalApplicationAdmin(admin.ModelAdmin):
    list_display = ["pk", "tenant", "property", "status", "submitted_at", "reviewed_at"]
    list_filter = ["status"]
    search_fields = ["tenant__email", "reviewer_sub"]
    readonly_fields = ["submitted_at"]
    actions = ["approve", "reject"]

    @admin.action(description="Approve selected applications")
    def approve(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status="pending").update(
            status="approved",
            reviewed_at=timezone.now(),
            reviewer_sub=getattr(request, "jwt_sub", "admin"),
        )

    @admin.action(description="Reject selected applications")
    def reject(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status="pending").update(
            status="rejected",
            reviewed_at=timezone.now(),
            reviewer_sub=getattr(request, "jwt_sub", "admin"),
        )
