"""Tests for DRF API ViewSets."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from iil_learnfw.api.viewsets import (
    CategoryViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    LeaderboardViewSet,
    MyPointsViewSet,
)
from iil_learnfw.models.course import Category, Course, Enrollment
from iil_learnfw.models.gamification import UserPoints
from iil_learnfw.services.gamification_service import award_points

User = get_user_model()


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="apiuser", password="test1234")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Python", slug="python")


@pytest.fixture
def course(db, category):
    return Course.objects.create(
        title="Django Basics",
        slug="django-basics",
        category=category,
        status="published",
    )


@pytest.fixture
def draft_course(db, category):
    return Course.objects.create(
        title="Draft Course",
        slug="draft-course",
        category=category,
        status="draft",
    )


def _auth_request(factory, user, method, path, data=None):
    """Create an authenticated request."""
    fn = getattr(factory, method)
    request = fn(path, data=data, content_type="application/json")
    request.user = user
    return request


@pytest.mark.django_db
class TestCategoryViewSet:
    def test_should_list_categories(self, factory, user, category):
        request = _auth_request(factory, user, "get", "/api/categories/")
        view = CategoryViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Python"

    def test_should_retrieve_category(self, factory, user, category):
        request = _auth_request(factory, user, "get", f"/api/categories/{category.pk}/")
        view = CategoryViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=category.pk)
        assert response.status_code == 200
        assert response.data["slug"] == "python"


@pytest.mark.django_db
class TestCourseViewSet:
    def test_should_list_published_courses(self, factory, user, course, draft_course):
        request = _auth_request(factory, user, "get", "/api/courses/")
        view = CourseViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Django Basics"

    def test_should_retrieve_course_detail(self, factory, user, course):
        request = _auth_request(factory, user, "get", f"/api/courses/{course.pk}/")
        view = CourseViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=course.pk)
        assert response.status_code == 200
        assert "chapters" in response.data

    def test_should_enroll_in_course(self, factory, user, course):
        request = _auth_request(
            factory, user, "post", f"/api/courses/{course.pk}/enroll/"
        )
        view = CourseViewSet.as_view({"post": "enroll"})
        response = view(request, pk=course.pk)
        assert response.status_code == 201
        assert Enrollment.objects.filter(user=user, course=course).exists()

    def test_should_withdraw_from_course(self, factory, user, course):
        Enrollment.objects.create(user=user, course=course, status="active")
        request = _auth_request(
            factory, user, "post", f"/api/courses/{course.pk}/withdraw/"
        )
        view = CourseViewSet.as_view({"post": "withdraw"})
        response = view(request, pk=course.pk)
        assert response.status_code == 204

    def test_should_require_auth(self, factory, course):
        from django.contrib.auth.models import AnonymousUser

        request = factory.get("/api/courses/")
        request.user = AnonymousUser()
        view = CourseViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 403


@pytest.mark.django_db
class TestEnrollmentViewSet:
    def test_should_list_own_enrollments(self, factory, user, course):
        Enrollment.objects.create(user=user, course=course, status="active")
        request = _auth_request(factory, user, "get", "/api/enrollments/")
        view = EnrollmentViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_should_not_see_others_enrollments(self, factory, user, course):
        other = User.objects.create_user(username="other", password="test1234")
        Enrollment.objects.create(user=other, course=course, status="active")
        request = _auth_request(factory, user, "get", "/api/enrollments/")
        view = EnrollmentViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert len(response.data) == 0


@pytest.mark.django_db
class TestLeaderboardViewSet:
    def test_should_return_leaderboard(self, factory, user):
        award_points(user, 100, "Test")
        request = _auth_request(factory, user, "get", "/api/leaderboard/")
        view = LeaderboardViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["total_points"] == 100


@pytest.mark.django_db
class TestMyPointsViewSet:
    def test_should_return_zero_when_no_points(self, factory, user):
        request = _auth_request(factory, user, "get", "/api/my-points/")
        view = MyPointsViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert response.data["total_points"] == 0

    def test_should_return_points(self, factory, user):
        UserPoints.objects.create(user=user, total_points=42, current_streak=3)
        request = _auth_request(factory, user, "get", "/api/my-points/")
        view = MyPointsViewSet.as_view({"get": "list"})
        response = view(request)
        assert response.status_code == 200
        assert response.data["total_points"] == 42
        assert response.data["current_streak"] == 3
