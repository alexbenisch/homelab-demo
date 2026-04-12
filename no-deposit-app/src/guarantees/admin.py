from django.contrib import admin

from .models import Guarantee


@admin.register(Guarantee)
class GuaranteeAdmin(admin.ModelAdmin):
    list_display = ["certificate_number", "application", "status", "valid_until", "issued_at"]
    list_filter = ["status"]
    search_fields = ["certificate_number", "issued_by_sub"]
    readonly_fields = ["certificate_number", "issued_at", "issued_by_sub"]
