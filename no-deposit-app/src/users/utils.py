from users.models import UserProfile


_ROLE_PRIORITY = ["admin", "agent", "landlord", "tenant"]


def get_or_create_profile(request) -> UserProfile:
    """Resolve the calling user's UserProfile from JWT claims, creating if absent."""
    auth = request.auth
    role = next((r for r in _ROLE_PRIORITY if auth.has_role(r)), "tenant")
    profile, _ = UserProfile.objects.get_or_create(
        keycloak_sub=auth.sub,
        defaults={"email": auth.email, "role": role},
    )
    return profile
