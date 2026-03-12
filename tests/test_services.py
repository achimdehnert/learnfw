"""Tests for iil-learnfw services."""

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models import Course, Enrollment
from iil_learnfw.services.course_service import archive_course, publish_course
from iil_learnfw.services.enrollment_service import (
    complete_enrollment,
    enroll,
    is_enrolled,
    withdraw,
)

User = get_user_model()


@pytest.mark.django_db
class TestCourseService:
    """Course service tests."""

    def test_should_publish_draft_course(self):
        course = Course.objects.create(title="Draft", slug="draft", status="draft")
        result = publish_course(course.pk)
        assert result.status == "published"

    def test_should_reject_publish_archived_course(self):
        course = Course.objects.create(title="Old", slug="old", status="archived")
        with pytest.raises(ValueError, match="Cannot publish"):
            publish_course(course.pk)

    def test_should_archive_course(self):
        course = Course.objects.create(title="Active", slug="active", status="published")
        result = archive_course(course.pk)
        assert result.status == "archived"


@pytest.mark.django_db
class TestEnrollmentService:
    """Enrollment service tests."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="student", password="test")

    @pytest.fixture
    def course(self):
        return Course.objects.create(title="Course", slug="svc-c1")

    def test_should_enroll_user(self, user, course):
        enrollment = enroll(user, course.pk)
        assert enrollment.status == "active"
        assert is_enrolled(user, course.pk) is True

    def test_should_withdraw_user(self, user, course):
        enroll(user, course.pk)
        withdraw(user, course.pk)
        assert is_enrolled(user, course.pk) is False

    def test_should_re_enroll_withdrawn_user(self, user, course):
        enroll(user, course.pk)
        withdraw(user, course.pk)
        enrollment = enroll(user, course.pk)
        assert enrollment.status == "active"

    def test_should_complete_enrollment(self, user, course):
        enroll(user, course.pk)
        complete_enrollment(user, course.pk)
        enrollment = Enrollment.objects.get(user=user, course=course)
        assert enrollment.status == "completed"
        assert enrollment.completed_at is not None
