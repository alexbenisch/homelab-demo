#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import psycopg2; psycopg2.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is up!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Loading fixtures if needed..."
python manage.py loaddata --ignorenonexistent fixtures/*.json 2>/dev/null || true

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser if not exists..."
    python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username, email, password)
    from common.models import UserProfile
    UserProfile.objects.get_or_create(user=user)
    print('Superuser and profile created.')
else:
    user = User.objects.get(username=username)
    from common.models import UserProfile
    UserProfile.objects.get_or_create(user=user)
    print('Superuser already exists, profile ensured.')
" || true
fi

echo "Starting application..."
exec "$@"
