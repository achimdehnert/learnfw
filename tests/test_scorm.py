"""Tests for SCORM models and CourseManager."""

import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models.course import Course, CourseManager
from iil_learnfw.models.scorm import ScormPackage, ScormTracking

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="scormuser", password="test1234")


@pytest.fixture
def course(db):
    return Course.objects.create(
        title="SCORM Course", slug="scorm-course", status="published"
    )


@pytest.fixture
def global_course(db):
    return Course.objects.create(
        title="Global Course",
        slug="global-course",
        status="published",
        is_global=True,
    )


@pytest.fixture
def tenant_course(db):
    tid = uuid.uuid4()
    return Course.objects.create(
        title="Tenant Course",
        slug="tenant-course",
        status="published",
        tenant_id=tid,
    ), tid


@pytest.fixture
def package(db, course):
    return ScormPackage.objects.create(
        course=course,
        scorm_version="1.2",
        manifest={"title": "Test SCORM"},
        entry_point="index.html",
    )


@pytest.mark.django_db
class TestScormPackage:
    def test_should_create_package(self, package, course):
        assert package.pk is not None
        assert package.course == course
        assert package.scorm_version == "1.2"
        assert package.manifest == {"title": "Test SCORM"}

    def test_should_str(self, package):
        assert "SCORM 1.2" in str(package)

    def test_should_support_2004(self, course):
        pkg = ScormPackage.objects.create(
            course=course, scorm_version="2004"
        )
        assert pkg.scorm_version == "2004"


@pytest.mark.django_db
class TestScormTracking:
    def test_should_create_tracking(self, user, package):
        tracking = ScormTracking.objects.create(
            user=user, package=package, status="incomplete"
        )
        assert tracking.pk is not None
        assert tracking.status == "incomplete"

    def test_should_track_score(self, user, package):
        tracking = ScormTracking.objects.create(
            user=user,
            package=package,
            status="completed",
            score_raw=85.5,
            score_min=0,
            score_max=100,
        )
        assert tracking.score_raw == 85.5

    def test_should_track_time(self, user, package):
        tracking = ScormTracking.objects.create(
            user=user,
            package=package,
            total_time=timedelta(hours=1, minutes=30),
        )
        assert tracking.total_time == timedelta(hours=1, minutes=30)

    def test_should_store_suspend_data(self, user, package):
        tracking = ScormTracking.objects.create(
            user=user,
            package=package,
            suspend_data="bookmark=slide5;score=42",
        )
        assert "slide5" in tracking.suspend_data

    def test_should_enforce_unique_user_package(self, user, package):
        from django.db import IntegrityError

        ScormTracking.objects.create(user=user, package=package)
        with pytest.raises(IntegrityError):
            ScormTracking.objects.create(user=user, package=package)


@pytest.mark.django_db
class TestCourseManager:
    def test_should_have_custom_manager(self):
        assert isinstance(Course.objects, CourseManager)

    def test_should_filter_published(self, course):
        Course.objects.create(
            title="Draft", slug="draft", status="draft"
        )
        published = Course.objects.published()
        assert published.count() == 1
        assert published.first() == course

    def test_should_return_tenant_and_global(
        self, global_course, tenant_course
    ):
        tc, tid = tenant_course
        qs = Course.objects.for_tenant(tid)
        assert global_course in qs
        assert tc in qs

    def test_should_exclude_other_tenant(
        self, global_course, tenant_course
    ):
        _, tid = tenant_course
        other_tid = uuid.uuid4()
        qs = Course.objects.for_tenant(other_tid)
        assert global_course in qs
        slugs = list(qs.values_list("slug", flat=True))
        assert "tenant-course" not in slugs

    def test_should_combine_tenant_and_published(
        self, global_course, tenant_course
    ):
        tc, tid = tenant_course
        Course.objects.create(
            title="Draft Tenant",
            slug="draft-tenant",
            status="draft",
            tenant_id=tid,
        )
        qs = Course.objects.for_tenant_published(tid)
        assert global_course in qs
        assert tc in qs
        assert qs.count() == 2
