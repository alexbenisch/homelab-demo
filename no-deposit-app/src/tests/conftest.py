"""Shared fixtures for the no-deposit test suite.

Auth strategy: DRF force_authenticate sets request.auth = JWTPayload directly,
bypassing the JWKS network call entirely. All views use request.auth, not
request.user, so no real Django User is needed.
"""

import pytest
from rest_framework.test import APIClient

from core.auth import JWTPayload
from users.models import UserProfile


# ── JWT payload helpers ────────────────────────────────────────────────────────

def _payload(sub: str, email: str, roles: list[str]) -> JWTPayload:
    return JWTPayload({"sub": sub, "email": email, "realm_access": {"roles": roles}})


def _client(payload: JWTPayload) -> APIClient:
    c = APIClient()
    c.force_authenticate(token=payload)
    return c


@pytest.fixture
def tenant_payload() -> JWTPayload:
    return _payload("tenant-sub-1", "tenant@test.com", ["tenant"])


@pytest.fixture
def landlord_payload() -> JWTPayload:
    return _payload("landlord-sub-1", "landlord@test.com", ["landlord"])


@pytest.fixture
def agent_payload() -> JWTPayload:
    return _payload("agent-sub-1", "agent@test.com", ["agent"])


# ── UserProfile fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def tenant_profile(tenant_payload: JWTPayload) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(
        keycloak_sub=tenant_payload.sub,
        defaults={"email": tenant_payload.email, "role": "tenant"},
    )
    return profile


@pytest.fixture
def landlord_profile(landlord_payload: JWTPayload) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(
        keycloak_sub=landlord_payload.sub,
        defaults={"email": landlord_payload.email, "role": "landlord"},
    )
    return profile


@pytest.fixture
def agent_profile(agent_payload: JWTPayload) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(
        keycloak_sub=agent_payload.sub,
        defaults={"email": agent_payload.email, "role": "agent"},
    )
    return profile


# ── API client fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def tenant_client(tenant_payload: JWTPayload, tenant_profile: UserProfile) -> APIClient:
    return _client(tenant_payload)


@pytest.fixture
def landlord_client(landlord_payload: JWTPayload, landlord_profile: UserProfile) -> APIClient:
    return _client(landlord_payload)


@pytest.fixture
def agent_client(agent_payload: JWTPayload, agent_profile: UserProfile) -> APIClient:
    return _client(agent_payload)


@pytest.fixture
def anon_client() -> APIClient:
    return APIClient()  # no force_authenticate — request.auth will be None


# ── Domain object fixtures ────────────────────────────────────────────────────

@pytest.fixture
def property_obj(landlord_profile: UserProfile):
    from properties.models import Property
    return Property.objects.create(
        landlord=landlord_profile,
        address="1 Test Street, London",
        rent_amount="1200.00",
        status="available",
    )


@pytest.fixture
def pending_application(tenant_profile: UserProfile, property_obj):
    from properties.models import RentalApplication
    return RentalApplication.objects.create(
        property=property_obj,
        tenant=tenant_profile,
        status="pending",
    )


@pytest.fixture
def approved_application(pending_application, agent_profile: UserProfile):
    from django.utils import timezone
    pending_application.status = "approved"
    pending_application.reviewed_at = timezone.now()
    pending_application.reviewer_sub = agent_profile.keycloak_sub
    pending_application.save()
    return pending_application


@pytest.fixture
def active_guarantee(approved_application, agent_profile: UserProfile):
    from django.utils import timezone
    from guarantees.models import Guarantee
    return Guarantee.objects.create(
        application=approved_application,
        valid_until=timezone.now().date(),
        issued_by_sub=agent_profile.keycloak_sub,
    )
