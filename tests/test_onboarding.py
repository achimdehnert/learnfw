"""Tests for onboarding models."""

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models.course import Course
from iil_learnfw.models.onboarding import (
    OnboardingFlow,
    OnboardingStep,
    UserOnboardingState,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="learner", password="test1234")


@pytest.fixture
def flow(db):
    return OnboardingFlow.objects.create(
        name="New Employee Onboarding",
        trigger="first_login",
    )


@pytest.fixture
def course(db):
    return Course.objects.create(title="Intro Course", slug="intro-course")


@pytest.fixture
def step(flow, course):
    return OnboardingStep.objects.create(
        flow=flow,
        course=course,
        title="Complete Intro Course",
        is_required=True,
        ordering=1,
    )


@pytest.mark.django_db
class TestOnboardingFlow:
    def test_should_create_flow(self, flow):
        assert flow.pk is not None
        assert flow.name == "New Employee Onboarding"
        assert flow.trigger == "first_login"
        assert flow.is_active is True

    def test_should_str(self, flow):
        assert str(flow) == "New Employee Onboarding"


@pytest.mark.django_db
class TestOnboardingStep:
    def test_should_create_step(self, step, flow, course):
        assert step.pk is not None
        assert step.flow == flow
        assert step.course == course
        assert step.is_required is True

    def test_should_str(self, step):
        assert str(step) == "New Employee Onboarding > Complete Intro Course"

    def test_should_order_steps(self, flow):
        OnboardingStep.objects.create(flow=flow, title="Step A", ordering=2)
        OnboardingStep.objects.create(flow=flow, title="Step B", ordering=1)
        steps = list(OnboardingStep.objects.filter(flow=flow))
        assert steps[0].ordering <= steps[1].ordering


@pytest.mark.django_db
class TestUserOnboardingState:
    def test_should_create_state(self, user, flow, step):
        state = UserOnboardingState.objects.create(
            user=user, flow=flow, step=step, status="pending"
        )
        assert state.pk is not None
        assert state.status == "pending"

    def test_should_complete_state(self, user, flow, step):
        from django.utils import timezone

        state = UserOnboardingState.objects.create(
            user=user, flow=flow, step=step, status="in_progress"
        )
        state.status = "completed"
        state.completed_at = timezone.now()
        state.save()
        state.refresh_from_db()
        assert state.status == "completed"
        assert state.completed_at is not None

    def test_should_enforce_unique_user_step(self, user, flow, step):
        from django.db import IntegrityError

        UserOnboardingState.objects.create(user=user, flow=flow, step=step)
        with pytest.raises(IntegrityError):
            UserOnboardingState.objects.create(user=user, flow=flow, step=step)
