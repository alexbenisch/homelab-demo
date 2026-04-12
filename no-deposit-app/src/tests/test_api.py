"""API endpoint tests.

Uses force_authenticate to inject JWTPayload, bypassing JWKS validation.
Celery tasks run eagerly (CELERY_TASK_ALWAYS_EAGER=True in settings_ci).
Emails use the dummy backend so no SMTP calls are made.
"""

import pytest

pytestmark = pytest.mark.django_db


# ── Authentication ─────────────────────────────────────────────────────────────

class TestAuthentication:
    def test_unauthenticated_request_rejected(self, anon_client):
        # OAuthProxyJWTAuthentication provides WWW-Authenticate: Bearer,
        # so DRF returns 401 (not 403) for unauthenticated requests.
        resp = anon_client.get("/api/v1/applications/")
        assert resp.status_code == 401

    def test_authenticated_request_allowed(self, tenant_client):
        resp = tenant_client.get("/api/v1/applications/")
        assert resp.status_code == 200


# ── Applications ───────────────────────────────────────────────────────────────

class TestApplications:
    def test_tenant_can_submit_application(self, tenant_client, property_obj):
        resp = tenant_client.post("/api/v1/applications/", {"property": property_obj.pk})
        assert resp.status_code == 201
        assert resp.data["status"] == "pending"

    def test_landlord_cannot_submit_application(self, landlord_client, property_obj):
        resp = landlord_client.post("/api/v1/applications/", {"property": property_obj.pk})
        assert resp.status_code == 403

    def test_agent_cannot_submit_application(self, agent_client, property_obj):
        resp = agent_client.post("/api/v1/applications/", {"property": property_obj.pk})
        assert resp.status_code == 403

    def test_tenant_sees_only_own_applications(
        self, tenant_client, pending_application, agent_client, property_obj
    ):
        # pending_application belongs to tenant_profile fixture
        resp = tenant_client.get("/api/v1/applications/")
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["id"] == pending_application.pk

    def test_agent_sees_all_applications(self, agent_client, pending_application):
        resp = agent_client.get("/api/v1/applications/")
        assert resp.status_code == 200
        assert any(a["id"] == pending_application.pk for a in resp.data)

    def test_agent_can_approve_application(self, agent_client, pending_application):
        resp = agent_client.patch(
            f"/api/v1/applications/{pending_application.pk}/review/",
            {"decision": "approved"},
        )
        assert resp.status_code == 200
        assert resp.data["status"] == "approved"

    def test_agent_can_reject_application(self, agent_client, pending_application):
        resp = agent_client.patch(
            f"/api/v1/applications/{pending_application.pk}/review/",
            {"decision": "rejected", "notes": "Insufficient income"},
        )
        assert resp.status_code == 200
        assert resp.data["status"] == "rejected"

    def test_tenant_cannot_review_application(self, tenant_client, pending_application):
        resp = tenant_client.patch(
            f"/api/v1/applications/{pending_application.pk}/review/",
            {"decision": "approved"},
        )
        assert resp.status_code == 403

    def test_cannot_review_already_reviewed_application(
        self, agent_client, approved_application
    ):
        resp = agent_client.patch(
            f"/api/v1/applications/{approved_application.pk}/review/",
            {"decision": "rejected"},
        )
        assert resp.status_code == 400


# ── Guarantees ────────────────────────────────────────────────────────────────

class TestGuarantees:
    def test_agent_can_issue_guarantee(self, agent_client, approved_application):
        from django.utils import timezone
        resp = agent_client.post("/api/v1/guarantees/", {
            "application": approved_application.pk,
            "valid_until": (timezone.now().date()).isoformat(),
        })
        assert resp.status_code == 201
        assert resp.data["certificate_number"].startswith("ND-")

    def test_cannot_issue_guarantee_for_pending_application(
        self, agent_client, pending_application
    ):
        from django.utils import timezone
        resp = agent_client.post("/api/v1/guarantees/", {
            "application": pending_application.pk,
            "valid_until": timezone.now().date().isoformat(),
        })
        assert resp.status_code == 400

    def test_cannot_issue_duplicate_guarantee(
        self, agent_client, approved_application, active_guarantee
    ):
        from django.utils import timezone
        resp = agent_client.post("/api/v1/guarantees/", {
            "application": approved_application.pk,
            "valid_until": timezone.now().date().isoformat(),
        })
        assert resp.status_code == 400


# ── Claims ────────────────────────────────────────────────────────────────────

class TestClaims:
    def test_landlord_can_submit_claim(self, landlord_client, active_guarantee):
        resp = landlord_client.post("/api/v1/claims/", {
            "guarantee": active_guarantee.pk,
            "amount_claimed": "500.00",
            "evidence_urls": [],
        })
        assert resp.status_code == 201
        assert resp.data["status"] == "open"

    def test_tenant_cannot_submit_claim(self, tenant_client, active_guarantee):
        resp = tenant_client.post("/api/v1/claims/", {
            "guarantee": active_guarantee.pk,
            "amount_claimed": "500.00",
        })
        assert resp.status_code == 403


# ── GDPR endpoints ────────────────────────────────────────────────────────────

class TestGDPR:
    def test_me_returns_own_profile(self, tenant_client, tenant_profile):
        resp = tenant_client.get("/api/v1/users/me/")
        assert resp.status_code == 200
        assert resp.data["role"] == "tenant"
        assert resp.data["email"] == tenant_profile.email

    def test_me_export_contains_profile(self, tenant_client, tenant_profile):
        resp = tenant_client.get("/api/v1/users/me/export/")
        assert resp.status_code == 200
        assert "profile" in resp.data
        assert "applications" in resp.data
        assert "exported_at" in resp.data

    def test_me_delete_anonymises_profile(self, tenant_client, tenant_profile):
        resp = tenant_client.delete("/api/v1/users/me/")
        assert resp.status_code == 204
        tenant_profile.refresh_from_db()
        assert tenant_profile.email == ""
        assert tenant_profile.keycloak_sub.startswith("deleted-")


# ── Metrics ───────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_metrics_endpoint_accessible_without_auth(self, anon_client):
        resp = anon_client.get("/metrics")
        assert resp.status_code == 200
        assert b"python_gc_objects" in resp.content or b"django_" in resp.content
