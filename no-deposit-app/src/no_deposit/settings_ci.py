"""Minimal settings for CI test runs — SQLite, no external services."""

from .settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Run Celery tasks synchronously inline — no Redis needed
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Suppress email output
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Skip JWKS network call — tests supply their own auth
OIDC_OP_JWKS_ENDPOINT = ""
