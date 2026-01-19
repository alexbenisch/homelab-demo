# Django CRM Dockerfile
# Based on https://github.com/DjangoCRM/django-crm

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r crm && useradd -r -g crm -u 1000 crm

# Set work directory
WORKDIR /app

# Clone Django CRM repository
RUN git clone --depth 1 https://github.com/DjangoCRM/django-crm.git .

# Install Python dependencies (exclude mysqlclient since we use PostgreSQL)
RUN grep -v mysqlclient requirements.txt > requirements-pg.txt \
    && pip install --no-cache-dir -r requirements-pg.txt \
    && pip install --no-cache-dir \
    psycopg2-binary \
    gunicorn \
    whitenoise

# Copy custom settings for production
COPY settings_docker.py /app/webcrm/settings_docker.py
COPY entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Collect static files
RUN python manage.py collectstatic --noinput --settings=webcrm.settings || true

# Change ownership
RUN chown -R crm:crm /app

# Switch to non-root user
USER crm

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "webcrm.wsgi:application"]
