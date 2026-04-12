"""Unit tests for model-level behaviour (no HTTP)."""

import pytest

pytestmark = pytest.mark.django_db


class TestAuditLog:
    def test_record_creates_entry(self):
        from audit.models import AuditLog

        log = AuditLog.record(
            entity_type="RentalApplication",
            entity_id=99,
            action="submitted",
            actor_id="sub-abc",
            actor_ip="10.0.0.1",
            payload={"note": "test"},
        )
        assert log.pk is not None
        assert log.entity_type == "RentalApplication"
        assert log.entity_id == "99"
        assert log.action == "submitted"
        assert log.payload == {"note": "test"}

    def test_update_raises(self):
        from audit.models import AuditLog

        log = AuditLog.record(
            entity_type="Test",
            entity_id=1,
            action="created",
            actor_id="sub",
            actor_ip=None,
        )
        log.action = "tampered"
        with pytest.raises(PermissionError, match="immutable"):
            log.save()

    def test_delete_raises(self):
        from audit.models import AuditLog

        log = AuditLog.record(
            entity_type="Test",
            entity_id=2,
            action="created",
            actor_id="sub",
            actor_ip=None,
        )
        with pytest.raises(PermissionError, match="cannot be deleted"):
            log.delete()

    def test_payload_defaults_to_empty_dict(self):
        from audit.models import AuditLog

        log = AuditLog.record(
            entity_type="Test",
            entity_id=3,
            action="x",
            actor_id="sub",
            actor_ip=None,
        )
        assert log.payload == {}


class TestGuaranteeCertificateNumber:
    def test_format(self, active_guarantee):
        cert = active_guarantee.certificate_number
        assert cert.startswith("ND-")
        assert len(cert) == 13  # "ND-" + 10 uppercase hex chars
        assert cert[3:].isupper() or cert[3:].isalnum()

    def test_auto_generated_on_create(self, approved_application):
        from django.utils import timezone

        from guarantees.models import Guarantee

        g = Guarantee.objects.create(
            application=approved_application,
            valid_until=timezone.now().date(),
            issued_by_sub="agent-sub",
        )
        assert g.certificate_number != ""
        assert g.certificate_number.startswith("ND-")


class TestUserProfile:
    def test_str_includes_role_and_email(self, tenant_profile):
        s = str(tenant_profile)
        assert "tenant" in s
        assert "tenant@test.com" in s

    def test_role_choices_valid(self, agent_profile, landlord_profile, tenant_profile):
        for profile in [agent_profile, landlord_profile, tenant_profile]:
            assert profile.role in ("tenant", "landlord", "agent", "admin")
