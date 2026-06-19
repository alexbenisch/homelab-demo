import os

# Pull in all upstream CRM settings (INSTALLED_APPS, MIDDLEWARE, URL config, etc.)
# then override what we need for Docker/Kubernetes deployment.
from webcrm.settings import *  # noqa: F401, F403

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)  # noqa: F821
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'django_crm'),
        'USER': os.environ.get('POSTGRES_USER', 'crm'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Insert WhiteNoise immediately after SecurityMiddleware
_whitenoise = 'whitenoise.middleware.WhiteNoiseMiddleware'
_security = 'django.middleware.security.SecurityMiddleware'
if _whitenoise not in MIDDLEWARE:  # noqa: F821
    _idx = MIDDLEWARE.index(_security)  # noqa: F821
    MIDDLEWARE = list(MIDDLEWARE)  # noqa: F821
    MIDDLEWARE.insert(_idx + 1, _whitenoise)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F821
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # noqa: F821

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True
