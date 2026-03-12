"""Progress tracking models: UserProgress, LessonCompletion."""

import logging

from django.conf import settings
from django.db import models

from .course import TenantMixin

logger = logging.getLogger(__name__)


class UserProgress(TenantMixin):
    """Tracks a user's progress on a single lesson."""

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_progress",
    )
    lesson = models.ForeignKey(
        "iil_learnfw.Lesson",
        on_delete=models.CASCADE,
        related_name="user_progress",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_started"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("user", "lesson")]
        verbose_name_plural = "user progress"

    def __str__(self):
        return f"{self.user} | {self.lesson.title} | {self.status}"
