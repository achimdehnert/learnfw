"""Enrollment service — enroll, withdraw, is_enrolled (ADR-041)."""

import logging

from django.utils import timezone

from ..models.course import Course, Enrollment

logger = logging.getLogger(__name__)


def enroll(user, course_id: int) -> Enrollment:
    """Enroll a user in a course."""
    course = Course.objects.get(pk=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        user=user,
        course=course,
        defaults={"tenant_id": getattr(course, "tenant_id", None)},
    )
    if not created and enrollment.status == "withdrawn":
        enrollment.status = "active"
        enrollment.save(update_fields=["status"])
    logger.info("User %s enrolled in %s (created=%s)", user, course.title, created)
    return enrollment


def withdraw(user, course_id: int) -> None:
    """Withdraw a user from a course."""
    Enrollment.objects.filter(user=user, course_id=course_id).update(
        status="withdrawn"
    )
    logger.info("User %s withdrawn from course %d", user, course_id)


def is_enrolled(user, course_id: int) -> bool:
    """Check if user is actively enrolled."""
    return Enrollment.objects.filter(
        user=user, course_id=course_id, status="active"
    ).exists()


def complete_enrollment(user, course_id: int) -> None:
    """Mark enrollment as completed."""
    Enrollment.objects.filter(user=user, course_id=course_id, status="active").update(
        status="completed", completed_at=timezone.now()
    )
    logger.info("User %s completed course %d", user, course_id)
