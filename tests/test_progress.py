"""Tests for iil-learnfw progress models and service."""

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models import Chapter, Course, Lesson, UserProgress
from iil_learnfw.services.progress_service import (
    complete_lesson,
    get_course_progress,
    start_lesson,
)

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(username="learner", password="test")


@pytest.fixture
def course_with_lessons():
    course = Course.objects.create(title="Progress Course", slug="prog-c1")
    chapter = Chapter.objects.create(course=course, title="Ch1")
    l1 = Lesson.objects.create(
        chapter=chapter, title="Lesson 1", ordering=0, is_mandatory=True,
    )
    l2 = Lesson.objects.create(
        chapter=chapter, title="Lesson 2", ordering=1, is_mandatory=True,
    )
    l3 = Lesson.objects.create(
        chapter=chapter, title="Bonus", ordering=2, is_mandatory=False,
    )
    return course, [l1, l2, l3]


@pytest.mark.django_db
class TestProgressModel:
    """UserProgress model tests."""

    def test_should_create_progress(self, user, course_with_lessons):
        _, lessons = course_with_lessons
        progress = UserProgress.objects.create(
            user=user, lesson=lessons[0], status="not_started",
        )
        assert progress.pk is not None
        assert progress.completed_at is None


@pytest.mark.django_db
class TestProgressService:
    """Progress service tests."""

    def test_should_start_lesson(self, user, course_with_lessons):
        _, lessons = course_with_lessons
        progress = start_lesson(user, lessons[0].pk)
        assert progress.status == "in_progress"
        assert progress.started_at is not None

    def test_should_complete_lesson(self, user, course_with_lessons):
        _, lessons = course_with_lessons
        start_lesson(user, lessons[0].pk)
        progress = complete_lesson(user, lessons[0].pk)
        assert progress.status == "completed"
        assert progress.completed_at is not None

    def test_should_calculate_course_progress_zero(self, user, course_with_lessons):
        course, _ = course_with_lessons
        result = get_course_progress(user, course.pk)
        assert result["total"] == 2  # only mandatory lessons
        assert result["completed"] == 0
        assert result["percentage"] == 0

    def test_should_calculate_course_progress_50(self, user, course_with_lessons):
        course, lessons = course_with_lessons
        start_lesson(user, lessons[0].pk)
        complete_lesson(user, lessons[0].pk)

        result = get_course_progress(user, course.pk)
        assert result["total"] == 2
        assert result["completed"] == 1
        assert result["percentage"] == 50

    def test_should_calculate_course_progress_100(self, user, course_with_lessons):
        course, lessons = course_with_lessons
        for lesson in lessons[:2]:  # only mandatory
            start_lesson(user, lesson.pk)
            complete_lesson(user, lesson.pk)

        result = get_course_progress(user, course.pk)
        assert result["percentage"] == 100
