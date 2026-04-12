from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "entity_type", "entity_id", "action", "actor_id", "actor_ip"]
    list_filter = ["entity_type", "action"]
    search_fields = ["entity_id", "actor_id"]
    readonly_fields = ["entity_type", "entity_id", "action", "actor_id", "actor_ip", "payload", "timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
