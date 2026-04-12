"""PDF guarantee certificate generation using WeasyPrint + Hetzner Object Storage."""

from django.template.loader import render_to_string

from core.storage import presigned_get_url, upload_bytes


def generate_certificate_pdf(guarantee) -> bytes:
    """Render a guarantee certificate as PDF bytes."""
    html = render_to_string(
        "certificates/guarantee.html",
        {
            "guarantee": guarantee,
            "application": guarantee.application,
            "property": guarantee.application.property,
            "tenant": guarantee.application.tenant,
        },
    )
    from weasyprint import HTML

    return HTML(string=html, base_url=None).write_pdf()


def store_certificate(guarantee, pdf_bytes: bytes) -> str:
    """Upload PDF to Hetzner Object Storage and return a pre-signed GET URL."""
    key = f"certificates/{guarantee.certificate_number}.pdf"
    upload_bytes(key, pdf_bytes, content_type="application/pdf")
    return presigned_get_url(key)
