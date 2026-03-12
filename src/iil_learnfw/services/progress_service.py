"""Progress service — track lesson progress, course completion (ADR-041)."""

import logging

from django.utils import timezone

from ..models.progress import UserProgress

logger = logging.getLogger(__name__)


def start_lesson(user, lesson_id: int) -> UserProgress:
    """Mark a lesson as in_progress for a user."""
    from ..models.course import Lesson

    lesson = Lesson.objects.get(pk=lesson_id)
    progress, created = UserProgress.objects.get_or_create(
        user=user,
        lesson=lesson,
        defaults={
            "tenant_id": getattr(lesson, "tenant_id", None),
            "status": "in_progress",
            "started_at": timezone.now(),
        },
    )
    if not created and progress.status == "not_started":
        progress.status = "in_progress"
        progress.started_at = timezone.now()
        progress.save(update_fields=["status", "started_at"])
    return progress


def complete_lesson(user, lesson_id: int) -> UserProgress:
    """Mark a lesson as completed for a user."""
    progress = UserProgress.objects.get(user=user, lesson_id=lesson_id)
    if progress.status != "completed":
        progress.status = "completed"
        progress.completed_at = timezone.now()
        progress.save(update_fields=["status", "completed_at"])
        logger.info("User %s completed lesson %d", user, lesson_id)
    return progress


def get_course_progress(user, course_id: int) -> dict:
    """Calculate course completion percentage for a user."""
    from ..models.course import Lesson

    total = Lesson.objects.filter(
        chapter__course_id=course_id, is_mandatory=True
    ).count()
    if total == 0:
        return {"total": 0, "completed": 0, "percentage": 100}

    completed = UserProgress.objects.filter(
        user=user,
        lesson__chapter__course_id=course_id,
        lesson__is_mandatory=True,
        status="completed",
    ).count()

    return {
        "total": total,
        "completed": completed,
        "percentage": round((completed / total) * 100),
    }
