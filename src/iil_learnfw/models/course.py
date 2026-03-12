"""Course structure models: Category, Course, Chapter, Lesson, Enrollment."""

import logging

from django.conf import settings
from django.db import models
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def tenant_upload_path(instance, filename):
    """Tenant-aware upload path: tenants/{tid}/learnfw/{model}/{file}."""
    tid = getattr(instance, "tenant_id", None) or "shared"
    model_name = instance.__class__.__name__.lower()
    return f"tenants/{tid}/learnfw/{model_name}/{filename}"


class TenantMixin(models.Model):
    """Mixin adding tenant_id to all learnfw models (ADR-137, ADR-139)."""

    tenant_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Tenant UUID (NULL = single-tenant mode or global content).",
    )

    class Meta:
        abstract = True


class Category(TenantMixin):
    """Course category for grouping."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(TenantMixin):
    """A learning course containing chapters and lessons."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "In Review"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses"
    )
    cover_image = models.ImageField(upload_to=tenant_upload_path, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_global = models.BooleanField(
        default=False,
        help_text="If True, visible to ALL tenants (platform-wide content).",
    )
    module_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="billing-hub ModuleSubscription code for marketplace courses.",
    )
    marketplace_enabled = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_courses",
    )
    estimated_duration_minutes = models.PositiveIntegerField(default=0)
    passing_score = models.PositiveIntegerField(
        default=80, help_text="Minimum score (%) to pass."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Chapter(TenantMixin):
    """A chapter grouping lessons within a course."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering"]
        unique_together = [("course", "ordering")]

    def __str__(self):
        return f"{self.course.title} > {self.title}"


class Lesson(TenantMixin):
    """A single lesson within a chapter."""

    CONTENT_TYPE_CHOICES = [
        ("markdown", "Markdown"),
        ("pdf", "PDF"),
        ("pptx", "PowerPoint"),
        ("external", "External URL"),
    ]

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=300)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default="markdown")
    content_text = models.TextField(
        blank=True, help_text="Markdown content (when content_type=markdown)."
    )
    content_file = models.FileField(
        upload_to=tenant_upload_path, blank=True, help_text="PDF or PPTX file."
    )
    external_url = models.URLField(blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(default=5)
    ordering = models.PositiveIntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return self.title


class Enrollment(TenantMixin):
    """Tracks user enrollment in a course."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("withdrawn", "Withdrawn"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learnfw_enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "course")]

    def __str__(self):
        return f"{self.user} → {self.course.title}"
