"""Celery tasks for transactional email notifications."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def _send(subject: str, template: str, context: dict, to: list[str]) -> None:
    body = render_to_string(template, context)
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=to,
        fail_silently=False,
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_application_submitted(self, application_id: int) -> None:
    """Notify agents that a new application needs review."""
    from properties.models import RentalApplication
    from users.models import UserProfile

    try:
        app = RentalApplication.objects.select_related("property", "tenant").get(pk=application_id)
        agents = UserProfile.objects.filter(role="agent").exclude(email="")
        if not agents.exists():
            return
        _send(
            subject=f"New application #{app.pk} awaiting review",
            template="notifications/email/application_submitted.txt",
            context={"application": app},
            to=list(agents.values_list("email", flat=True)),
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_application_reviewed(self, application_id: int) -> None:
    """Notify tenant their application was approved or rejected."""
    from properties.models import RentalApplication

    try:
        app = RentalApplication.objects.select_related("tenant").get(pk=application_id)
        if not app.tenant.email:
            return
        _send(
            subject=f"Your rental application has been {app.status}",
            template="notifications/email/application_reviewed.txt",
            context={"application": app},
            to=[app.tenant.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_guarantee_issued(self, guarantee_id: int) -> None:
    """Notify tenant and landlord that a guarantee certificate was issued."""
    from guarantees.models import Guarantee

    try:
        guarantee = Guarantee.objects.select_related(
            "application__tenant", "application__property__landlord"
        ).get(pk=guarantee_id)
        tenant = guarantee.application.tenant
        landlord = guarantee.application.property.landlord
        recipients = [e for e in [tenant.email, landlord.email] if e]
        if not recipients:
            return
        _send(
            subject=f"Guarantee certificate {guarantee.certificate_number} issued",
            template="notifications/email/guarantee_issued.txt",
            context={"guarantee": guarantee},
            to=recipients,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_claim_submitted(self, claim_id: int) -> None:
    """Notify agents that a new damage claim was submitted."""
    from claims.models import DamageClaim
    from users.models import UserProfile

    try:
        claim = DamageClaim.objects.select_related("guarantee").get(pk=claim_id)
        agents = UserProfile.objects.filter(role="agent").exclude(email="")
        if not agents.exists():
            return
        _send(
            subject=f"New damage claim #{claim.pk} submitted",
            template="notifications/email/claim_submitted.txt",
            context={"claim": claim},
            to=list(agents.values_list("email", flat=True)),
        )
    except Exception as exc:
        raise self.retry(exc=exc)
