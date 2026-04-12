"""Hetzner Object Storage client (MinIO SDK)."""

from datetime import timedelta

from django.conf import settings
from minio import Minio


def get_minio_client() -> Minio:
    """Return a configured MinIO client for Hetzner Object Storage."""
    # Strip scheme — MinIO SDK takes host:port only
    endpoint = settings.HETZNER_OBJECT_STORAGE_ENDPOINT.replace("https://", "").replace("http://", "")
    return Minio(
        endpoint=endpoint,
        access_key=settings.HETZNER_OBJECT_STORAGE_ACCESS_KEY,
        secret_key=settings.HETZNER_OBJECT_STORAGE_SECRET_KEY,
        secure=True,
    )


def presigned_put_url(key: str, content_type: str, expiry_seconds: int | None = None) -> str:
    """Generate a pre-signed PUT URL for direct client upload."""
    client = get_minio_client()
    expiry = timedelta(seconds=expiry_seconds or settings.S3_PRESIGNED_URL_EXPIRY)
    return client.presigned_put_object(
        bucket_name=settings.HETZNER_OBJECT_STORAGE_BUCKET_NAME,
        object_name=key,
        expires=expiry,
    )


def presigned_get_url(key: str, expiry_seconds: int | None = None) -> str:
    """Generate a pre-signed GET URL for temporary download access."""
    client = get_minio_client()
    expiry = timedelta(seconds=expiry_seconds or settings.S3_PRESIGNED_URL_EXPIRY)
    return client.presigned_get_object(
        bucket_name=settings.HETZNER_OBJECT_STORAGE_BUCKET_NAME,
        object_name=key,
        expires=expiry,
    )


def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    """Upload raw bytes directly to object storage."""
    import io

    client = get_minio_client()
    client.put_object(
        bucket_name=settings.HETZNER_OBJECT_STORAGE_BUCKET_NAME,
        object_name=key,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def storage_configured() -> bool:
    return bool(settings.HETZNER_OBJECT_STORAGE_ENDPOINT)
