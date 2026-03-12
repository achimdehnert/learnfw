"""Tests for iil-learnfw course models."""

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models import Category, Chapter, Course, Enrollment, Lesson

User = get_user_model()


@pytest.mark.django_db
class TestCourseModel:
    """Course model tests."""

    def test_should_create_course_with_defaults(self):
        course = Course.objects.create(title="Test Course", slug="test-course")
        assert course.pk is not None
        assert course.status == "draft"
        assert course.is_global is False
        assert course.tenant_id is None

    def test_should_auto_generate_slug(self):
        course = Course.objects.create(title="My Learning Course")
        assert course.slug == "my-learning-course"

    def test_should_create_global_course(self):
        course = Course.objects.create(
            title="Global Course", slug="global", is_global=True
        )
        assert course.is_global is True
        assert course.tenant_id is None


@pytest.mark.django_db
class TestChapterLesson:
    """Chapter and Lesson tests."""

    def test_should_create_chapter_with_lessons(self):
        course = Course.objects.create(title="Course", slug="c1")
        chapter = Chapter.objects.create(course=course, title="Chapter 1")
        lesson = Lesson.objects.create(
            chapter=chapter,
            title="Lesson 1",
            content_type="markdown",
            content_text="# Hello",
        )
        assert lesson.pk is not None
        assert chapter.lessons.count() == 1
        assert course.chapters.count() == 1


@pytest.mark.django_db
class TestEnrollment:
    """Enrollment model tests."""

    def test_should_enroll_user(self):
        user = User.objects.create_user(username="learner", password="test")
        course = Course.objects.create(title="Course", slug="c2")
        enrollment = Enrollment.objects.create(user=user, course=course)
        assert enrollment.status == "active"
        assert enrollment.completed_at is None


@pytest.mark.django_db
class TestCategory:
    """Category model tests."""

    def test_should_create_category(self):
        cat = Category.objects.create(name="Compliance", slug="compliance")
        assert str(cat) == "Compliance"
