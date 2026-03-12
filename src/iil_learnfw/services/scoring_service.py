"""Scoring service — quiz evaluation, pass/fail (ADR-041)."""

import logging
from decimal import Decimal

from django.utils import timezone

from ..models.assessment import Answer, Attempt, AttemptAnswer, Question

logger = logging.getLogger(__name__)


def submit_answer(
    attempt_id: int,
    question_id: int,
    selected_answer_id: int | None = None,
    free_text: str = "",
) -> AttemptAnswer:
    """Submit an answer for a question in an attempt."""
    question = Question.objects.get(pk=question_id)
    is_correct = None
    points = 0

    if selected_answer_id and question.question_type in (
        "single_choice", "multiple_choice"
    ):
        answer = Answer.objects.get(pk=selected_answer_id)
        is_correct = answer.is_correct
        points = question.points if is_correct else 0

    attempt_answer, _ = AttemptAnswer.objects.update_or_create(
        attempt_id=attempt_id,
        question=question,
        defaults={
            "selected_answer_id": selected_answer_id,
            "free_text": free_text,
            "is_correct": is_correct,
            "points_awarded": points,
            "tenant_id": question.tenant_id,
        },
    )
    return attempt_answer


def finish_attempt(attempt_id: int) -> Attempt:
    """Finalize an attempt: calculate score and pass/fail."""
    attempt = Attempt.objects.get(pk=attempt_id)
    if attempt.completed_at is not None:
        return attempt

    total_points = sum(
        q.points for q in attempt.quiz.questions.all()
    )
    awarded_points = sum(
        a.points_awarded for a in attempt.answers.all()
    )

    if total_points > 0:
        score = Decimal(awarded_points) / Decimal(total_points) * 100
    else:
        score = Decimal("100")

    attempt.score = score
    attempt.passed = score >= attempt.quiz.passing_score
    attempt.completed_at = timezone.now()
    attempt.save(update_fields=["score", "passed", "completed_at"])

    status = "passed" if attempt.passed else "failed"
    logger.info(
        "Attempt %d finished: %s (%.1f%%)", attempt_id, status, score
    )
    return attempt


def can_retry(user, quiz_id: int) -> bool:
    """Check if user can make another attempt at a quiz."""
    from ..models.assessment import Quiz

    quiz = Quiz.objects.get(pk=quiz_id)
    if quiz.max_attempts == 0:
        return True
    attempt_count = Attempt.objects.filter(
        user=user, quiz=quiz, completed_at__isnull=False
    ).count()
    return attempt_count < quiz.max_attempts
