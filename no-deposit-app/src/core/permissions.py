from rest_framework.permissions import BasePermission


class IsValidJWT(BasePermission):
    """Default permission: request must carry a valid JWT (set by oauth2-proxy)."""

    def has_permission(self, request, view):
        return request.auth is not None


class HasRole(BasePermission):
    role: str = ""

    def has_permission(self, request, view):
        return bool(request.auth and self.role and request.auth.has_role(self.role))


class IsTenant(HasRole):
    role = "tenant"


class IsLandlord(HasRole):
    role = "landlord"


class IsAgent(HasRole):
    role = "agent"


class IsAdmin(HasRole):
    role = "admin"


class IsAgentOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.auth:
            return False
        return request.auth.has_role("agent") or request.auth.has_role("admin")
