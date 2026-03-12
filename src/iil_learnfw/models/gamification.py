"""Gamification models: Badge, UserBadge, UserPoints, PointsTransaction."""

import logging

from django.conf import settings
from django.db import models

from .course import TenantMixin

logger = logging.getLogger(__name__)


class Badge(TenantMixin):
    """An achievement badge that can be awarded to users."""

    TRIGGER_CHOICES = [
        ("course_completed", "Course Completed"),
        ("quiz_passed", "Quiz Passed"),
        ("streak_reached", "Streak Reached"),
        ("points_reached", "Points Reached"),
        ("custom", "Custom"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    icon = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    trigger = models.CharField(
        max_length=20, choices=TRIGGER_CHOICES, default="custom"
    )
    threshold = models.PositiveIntegerField(
        default=1,
        help_text="Threshold for auto-award (e.g. 5 courses, 100 points).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserBadge(TenantMixin):
    """A badge awarded to a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_badges",
    )
    badge = models.ForeignKey(
        Badge, on_delete=models.CASCADE, related_name="awards"
    )
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "badge")]

    def __str__(self):
        return f"{self.user} | {self.badge.name}"


class UserPoints(TenantMixin):
    """Aggregated points for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_points",
    )
    total_points = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "user points"

    def __str__(self):
        return f"{self.user} | {self.total_points}pts | streak {self.current_streak}d"


class PointsTransaction(TenantMixin):
    """A single points award/deduction event."""

    SOURCE_CHOICES = [
        ("lesson", "Lesson Completed"),
        ("quiz", "Quiz Passed"),
        ("badge", "Badge Awarded"),
        ("manual", "Manual"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_points_transactions",
    )
    points = models.IntegerField(help_text="Positive = award, negative = deduction.")
    reason = models.CharField(max_length=200)
    source_type = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default="manual"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} | {self.points:+d}pts | {self.reason}"
