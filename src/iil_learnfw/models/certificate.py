"""Certificate models: CertificateTemplate, IssuedCertificate."""

import logging
import uuid

from django.conf import settings
from django.db import models

from .course import TenantMixin, tenant_upload_path

logger = logging.getLogger(__name__)


class CertificateTemplate(TenantMixin):
    """Template for generating PDF certificates."""

    name = models.CharField(max_length=200)
    html_template = models.TextField(
        help_text="HTML template for WeasyPrint rendering. "
        "Available context: {{ user }}, {{ course }}, {{ issued_at }}."
    )
    logo = models.FileField(
        upload_to=tenant_upload_path, blank=True
    )
    signature_image = models.FileField(
        upload_to=tenant_upload_path, blank=True
    )
    valid_for_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Certificate validity in days (NULL = no expiry).",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default template for courses without explicit template.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IssuedCertificate(TenantMixin):
    """A certificate issued to a user for completing a course."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_certificates",
    )
    course = models.ForeignKey(
        "iil_learnfw.Course",
        on_delete=models.CASCADE,
        related_name="issued_certificates",
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_certificates",
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    verification_token = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True,
        help_text="Public verification token (non-PK UUID, ADR-022).",
    )
    pdf_file = models.FileField(
        upload_to=tenant_upload_path, blank=True
    )

    class Meta:
        unique_together = [("user", "course")]
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.user} | {self.course.title} | {self.issued_at:%Y-%m-%d}"
