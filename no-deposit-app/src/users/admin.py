from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["email", "role", "keycloak_sub", "created_at"]
    list_filter = ["role"]
    search_fields = ["email", "keycloak_sub"]
    readonly_fields = ["keycloak_sub", "created_at", "updated_at"]
