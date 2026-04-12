import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "no_deposit.settings")

app = Celery("no_deposit")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
