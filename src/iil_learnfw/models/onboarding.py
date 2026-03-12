"""Onboarding models: OnboardingFlow, OnboardingStep, UserOnboardingState."""

import logging

from django.conf import settings
from django.db import models

from .course import TenantMixin

logger = logging.getLogger(__name__)


class OnboardingFlow(TenantMixin):
    """A sequence of steps for new user onboarding."""

    TRIGGER_CHOICES = [
        ("first_login", "First Login"),
        ("role_change", "Role Change"),
        ("manual", "Manual Assignment"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger = models.CharField(
        max_length=20, choices=TRIGGER_CHOICES, default="first_login"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class OnboardingStep(TenantMixin):
    """A single step within an onboarding flow."""

    flow = models.ForeignKey(
        OnboardingFlow, on_delete=models.CASCADE, related_name="steps"
    )
    course = models.ForeignKey(
        "iil_learnfw.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_steps",
    )
    quiz = models.ForeignKey(
        "iil_learnfw.Quiz",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_steps",
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return f"{self.flow.name} > {self.title}"


class UserOnboardingState(TenantMixin):
    """Tracks a user's progress through onboarding steps."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("skipped", "Skipped"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_onboarding_states",
    )
    flow = models.ForeignKey(
        OnboardingFlow, on_delete=models.CASCADE, related_name="user_states"
    )
    step = models.ForeignKey(
        OnboardingStep, on_delete=models.CASCADE, related_name="user_states"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "step")]

    def __str__(self):
        return f"{self.user} | {self.step.title} | {self.status}"
