"""Course service — CRUD, publishing, ordering (ADR-041)."""

import logging

from django.db import transaction

from ..models.course import Course

logger = logging.getLogger(__name__)


def publish_course(course_id: int) -> Course:
    """Publish a course (draft → published)."""
    course = Course.objects.get(pk=course_id)
    if course.status not in ("draft", "review"):
        raise ValueError(f"Cannot publish course in status '{course.status}'.")
    course.status = "published"
    course.save(update_fields=["status", "updated_at"])
    logger.info("Course %s published (id=%d)", course.title, course.pk)
    return course


def archive_course(course_id: int) -> Course:
    """Archive a course (any status → archived)."""
    course = Course.objects.get(pk=course_id)
    course.status = "archived"
    course.save(update_fields=["status", "updated_at"])
    logger.info("Course %s archived (id=%d)", course.title, course.pk)
    return course


@transaction.atomic
def reorder_chapters(course_id: int, chapter_ids: list[int]) -> None:
    """Reorder chapters within a course."""
    for idx, chapter_id in enumerate(chapter_ids):
        Course.objects.get(pk=course_id).chapters.filter(pk=chapter_id).update(ordering=idx)
