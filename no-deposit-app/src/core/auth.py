import threading

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

_jwks_client = None
_jwks_lock = threading.Lock()


def _get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        with _jwks_lock:
            if _jwks_client is None:
                _jwks_client = jwt.PyJWKClient(settings.OIDC_OP_JWKS_ENDPOINT, cache_keys=True)
    return _jwks_client


class JWTPayload:
    """Wraps a decoded Keycloak JWT payload; used as request.auth in DRF views."""

    def __init__(self, payload: dict):
        self.payload = payload
        self.sub: str = payload.get("sub", "")
        self.email: str = payload.get("email", "")
        realm_access = payload.get("realm_access", {})
        self.roles: set[str] = set(realm_access.get("roles", []))

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def __repr__(self) -> str:
        return f"<JWTPayload sub={self.sub} roles={self.roles}>"


class OAuthProxyJWTAuthentication(BaseAuthentication):
    """
    DRF authentication class for the oauth2-proxy architecture.

    oauth2-proxy sets X-Forwarded-Access-Token on every forwarded request.
    We validate it against Keycloak's JWKS and expose claims as request.auth.
    request.user is left as AnonymousUser; use permission classes for role checks.
    """

    def authenticate(self, request):
        token = request.META.get("HTTP_X_FORWARDED_ACCESS_TOKEN")
        if not token:
            return None

        try:
            client = _get_jwks_client()
            signing_key = client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.OIDC_RP_CLIENT_ID,
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}")

        return (request._request.user, JWTPayload(payload))

    def authenticate_header(self, request):
        return "Bearer"
