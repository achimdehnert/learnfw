"""Assessment models: Quiz, Question, Answer, Attempt, AttemptAnswer."""

import logging

from django.conf import settings
from django.db import models

from .course import TenantMixin

logger = logging.getLogger(__name__)


class Quiz(TenantMixin):
    """A quiz/test associated with a course or chapter."""

    course = models.ForeignKey(
        "iil_learnfw.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    chapter = models.ForeignKey(
        "iil_learnfw.Chapter",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    title = models.CharField(max_length=300)
    passing_score = models.PositiveIntegerField(
        default=80, help_text="Minimum score (%) to pass."
    )
    max_attempts = models.PositiveIntegerField(
        default=0, help_text="0 = unlimited attempts."
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time limit in minutes (NULL = no limit)."
    )
    shuffle_questions = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "quizzes"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Question(TenantMixin):
    """A single question within a quiz."""

    QUESTION_TYPE_CHOICES = [
        ("multiple_choice", "Multiple Choice"),
        ("single_choice", "Single Choice"),
        ("free_text", "Free Text"),
        ("matching", "Matching"),
    ]

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, default="single_choice"
    )
    text = models.TextField()
    explanation = models.TextField(
        blank=True, help_text="Shown after answering."
    )
    points = models.PositiveIntegerField(default=1)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return f"Q{self.ordering}: {self.text[:50]}"


class Answer(TenantMixin):
    """An answer option for MC/SC questions."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.text[:50]}"


class Attempt(TenantMixin):
    """A user's attempt at a quiz."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learnfw_attempts",
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="attempts"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Score as percentage (0-100).",
    )
    passed = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        status = "passed" if self.passed else "failed" if self.passed is False else "in progress"
        return f"{self.user} | {self.quiz.title} | {status}"


class AttemptAnswer(TenantMixin):
    """A user's answer to a single question within an attempt."""

    attempt = models.ForeignKey(
        Attempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="attempt_answers"
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempt_selections",
        help_text="Selected answer (MC/SC).",
    )
    free_text = models.TextField(
        blank=True, help_text="Free text response."
    )
    is_correct = models.BooleanField(null=True, blank=True)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("attempt", "question")]

    def __str__(self):
        return f"Attempt {self.attempt_id} | Q{self.question.ordering}"
