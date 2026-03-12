"""SCORM models: ScormPackage, ScormTracking (ADR-139 Phase 3)."""

import logging

from django.conf import settings
from django.db import models

from .course import TenantMixin

logger = logging.getLogger(__name__)


def scorm_upload_path(instance, filename):
    """Upload path for SCORM packages: scorm/<tenant_id>/<filename>."""
    tid = instance.tenant_id or "global"
    return f"scorm/{tid}/{filename}"


class ScormPackage(TenantMixin):
    """An imported SCORM 1.2 or 2004 package."""

    VERSION_CHOICES = [
        ("1.2", "SCORM 1.2"),
        ("2004", "SCORM 2004"),
    ]

    course = models.ForeignKey(
        "iil_learnfw.Course",
        on_delete=models.CASCADE,
        related_name="scorm_packages",
    )
    scorm_version = models.CharField(
        max_length=4, choices=VERSION_CHOICES, default="1.2"
    )
    package_file = models.FileField(upload_to=scorm_upload_path)
    manifest = models.JSONField(
        default=dict,
        blank=True,
        help_text="Parsed imsmanifest.xml as JSON.",
    )
    entry_point = models.CharField(
        max_length=500,
        blank=True,
        help_text="Relative path to launch file within package.",
    )
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-imported_at"]

    def __str__(self):
        return f"SCORM {self.scorm_version} | {self.course.title}"


class ScormTracking(TenantMixin):
    """Runtime tracking data for a user's SCORM session."""

    STATUS_CHOICES = [
        ("not_attempted", "Not Attempted"),
        ("incomplete", "Incomplete"),
        ("completed", "Completed"),
        ("passed", "Passed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_scorm_tracking",
    )
    package = models.ForeignKey(
        ScormPackage,
        on_delete=models.CASCADE,
        related_name="tracking_entries",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_attempted"
    )
    score_raw = models.FloatField(null=True, blank=True)
    score_min = models.FloatField(default=0)
    score_max = models.FloatField(default=100)
    total_time = models.DurationField(
        null=True, blank=True,
        help_text="Total time spent in SCORM session.",
    )
    suspend_data = models.TextField(
        blank=True,
        help_text="SCORM suspend_data for session resume.",
    )
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "package")]

    def __str__(self):
        return f"{self.user} | {self.package} | {self.status}"
