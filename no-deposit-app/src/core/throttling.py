"""DRF throttle classes keyed on Keycloak subject (sub claim)."""

from rest_framework.throttling import SimpleRateThrottle


class JWTBaseThrottle(SimpleRateThrottle):
    """Rate throttle that keys on the JWT sub claim instead of request.user."""

    def get_cache_key(self, request, view):
        auth = getattr(request, "auth", None)
        if auth is None or not getattr(auth, "sub", None):
            return None  # unauthenticated — let IsValidJWT reject it
        return self.cache_format % {
            "scope": self.scope,
            "ident": auth.sub,
        }


class BurstRateThrottle(JWTBaseThrottle):
    scope = "burst"


class SustainedRateThrottle(JWTBaseThrottle):
    scope = "sustained"
