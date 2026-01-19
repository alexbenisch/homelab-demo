#!/bin/bash
set -e

# Patch Django settings with environment variables
if [ -n "$DJANGO_ALLOWED_HOSTS" ]; then
    echo "Patching ALLOWED_HOSTS..."
    HOSTS_LIST=$(echo "$DJANGO_ALLOWED_HOSTS" | sed "s/,/', '/g")
    sed -i "s/ALLOWED_HOSTS = \[.*\]/ALLOWED_HOSTS = ['$HOSTS_LIST']/" /app/webcrm/settings.py
fi

if [ -n "$DJANGO_SECRET_KEY" ]; then
    echo "Patching SECRET_KEY..."
    sed -i "s/^SECRET_KEY = .*/SECRET_KEY = '$DJANGO_SECRET_KEY'/" /app/webcrm/settings.py
fi

# Configure PostgreSQL database
if [ -n "$POSTGRES_HOST" ]; then
    echo "Patching DATABASE settings for PostgreSQL..."
    cat > /tmp/db_patch.py << 'DBPATCH'
import os
settings_file = '/app/webcrm/settings.py'
with open(settings_file, 'r') as f:
    content = f.read()

# Find and replace DATABASES section
import re
db_config = f"""DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '{os.environ.get('POSTGRES_DB', 'django_crm')}',
        'USER': '{os.environ.get('POSTGRES_USER', 'crm')}',
        'PASSWORD': '{os.environ.get('POSTGRES_PASSWORD', '')}',
        'HOST': '{os.environ.get('POSTGRES_HOST', 'postgres')}',
        'PORT': '{os.environ.get('POSTGRES_PORT', '5432')}',
    }}
}}"""

# Replace the DATABASES block
pattern = r"DATABASES\s*=\s*\{[^}]+\{[^}]+\}[^}]+\}"
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, db_config, content, flags=re.DOTALL)
else:
    content += "\n" + db_config

with open(settings_file, 'w') as f:
    f.write(content)
DBPATCH
    python /tmp/db_patch.py
fi

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! python -c "import psycopg2; psycopg2.connect(host='$POSTGRES_HOST', port='$POSTGRES_PORT', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is up!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Load initial fixtures if database is empty
echo "Loading fixtures if needed..."
python manage.py loaddata --ignorenonexistent fixtures/*.json 2>/dev/null || true

# Create superuser if not exists
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
    User.objects.create_superuser(username, email, password)
    print('Superuser created.')
else:
    print('Superuser already exists.')
" || true
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting application..."
exec "$@"
