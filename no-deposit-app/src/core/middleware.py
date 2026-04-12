import jwt


class JWTUserMiddleware:
    """
    Reads the JWT from X-Forwarded-Access-Token (set by oauth2-proxy) and
    attaches a minimal user-like object to request so portal views can access
    email and roles without hitting the database.

    This middleware runs for all requests (HTML + API). DRF views use the
    separate OAuthProxyJWTAuthentication class which does full validation.
    Here we decode without signature verification because oauth2-proxy has
    already validated the token at the ingress layer.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.META.get("HTTP_X_FORWARDED_ACCESS_TOKEN")
        if token:
            try:
                payload = jwt.decode(
                    token, options={"verify_signature": False, "verify_exp": False}
                )
                realm_access = payload.get("realm_access", {})
                request.jwt_roles = set(realm_access.get("roles", []))
                request.jwt_email = payload.get("email", "")
                request.jwt_sub = payload.get("sub", "")
            except jwt.InvalidTokenError:
                request.jwt_roles = set()
                request.jwt_email = ""
                request.jwt_sub = ""
        else:
            request.jwt_roles = set()
            request.jwt_email = ""
            request.jwt_sub = ""

        return self.get_response(request)
