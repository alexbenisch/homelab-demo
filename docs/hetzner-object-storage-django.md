# Hetzner Object Storage with Django

Source: https://github.com/hetzneronline/community-content/blob/master/tutorials/object-storage-django-storages/01.en.md  
Author: Mitja Martini — License: MIT

---

## Key Differences from AWS S3

- **No bucket-name subdomain**: Hetzner does NOT prefix the bucket name to the domain. All buckets in a region share the same domain. This affects CORS (you can't lock down by bucket origin) — do **not** serve static files from Object Storage for this reason.
- **Signature version**: Must use `s3` (not the default `s3v4`). Set `signature_version = "s3"` on storage backends.
- **Checksum settings** (boto3/django-storages): Set both to `WHEN_REQUIRED` or uploads fail:
  ```ini
  AWS_REQUEST_CHECKSUM_CALCULATION=WHEN_REQUIRED
  AWS_RESPONSE_CHECKSUM_CALCULATION=WHEN_REQUIRED
  ```
- **Addressing style**: Use `virtual` (`AWS_S3_ADDRESSING_STYLE = "virtual"`).
- **Endpoint URL**: `https://fsn1.your-objectstorage.com` (Falkenstein). No bucket name in the URL.

---

## django-storages Setup (if using boto3 backend)

```python
# settings.py
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_S3_ENDPOINT_URL = "https://fsn1.your-objectstorage.com"
AWS_DEFAULT_ACL = None  # private by default
```

```python
# storage_backends.py
from storages.backends.s3boto3 import S3Boto3Storage

class BaseMediaStorage(S3Boto3Storage):
    signature_version = "s3"   # REQUIRED for Hetzner
    file_overwrite = False
    custom_domain = False

class PublicMediaStorage(BaseMediaStorage):
    location = "media"
    default_acl = "public-read"

class PrivateMediaStorage(BaseMediaStorage):
    location = "private"
    default_acl = "private"
```

---

## MinIO SDK Setup (used in no-deposit-app)

The no-deposit-app uses the MinIO Python SDK directly (not django-storages/boto3). Key notes:

- Strip `https://` from the endpoint before passing to `Minio()` constructor — it takes hostname only.
- `secure=True` for HTTPS.
- Presigned GET URLs expire in 15 min (`S3_PRESIGNED_URL_EXPIRY = 900`).
- File overwrite = `True` (cost optimisation — no versioned duplicates).

```python
from minio import Minio

client = Minio(
    endpoint="fsn1.your-objectstorage.com",  # no scheme
    access_key=settings.HETZNER_OBJECT_STORAGE_ACCESS_KEY,
    secret_key=settings.HETZNER_OBJECT_STORAGE_SECRET_KEY,
    secure=True,
)
```

---

## Bucket Setup Checklist

1. Create bucket in [Hetzner Cloud Console](https://console.hetzner.cloud/) → Object Storage
   - Visibility: **Private**
   - Object Lock: Disabled
2. Generate S3 credentials under Security → S3 credentials
3. Store `ACCESS KEY` and `SECRET KEY` in `.env` and Kubernetes SOPS secret

---

## Seven Things to Get Right

1. Private bucket for private files
2. Correct signature version: `s3` (not `s3v4`) — boto3/django-storages only
3. Correct endpoint URL (`https://fsn1.your-objectstorage.com`) — path style, no bucket prefix
4. ACLs: `private` or `public-read` per object
5. Presigned URLs for private file access (expire after N seconds)
6. Set `AWS_REQUEST_CHECKSUM_CALCULATION=WHEN_REQUIRED` — boto3/django-storages only
7. Do **not** serve static files from Object Storage (CORS limitation)

---

## Environment Variables

```ini
# .env / K8s secret
HETZNER_OBJECT_STORAGE_ENDPOINT=https://fsn1.your-objectstorage.com
HETZNER_OBJECT_STORAGE_BUCKET_NAME=no-deposit
HETZNER_OBJECT_STORAGE_ACCESS_KEY=...
HETZNER_OBJECT_STORAGE_SECRET_KEY=...
HETZNER_OBJECT_STORAGE_REGION=fsn1
```

Note: The no-deposit-app uses `HETZNER_OBJECT_STORAGE_*` naming throughout — no `AWS_*` variables.
