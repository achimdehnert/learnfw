"""Tests for gamification models and service."""

import pytest
from django.contrib.auth import get_user_model

from iil_learnfw.models.gamification import (
    Badge,
    PointsTransaction,
    UserPoints,
)
from iil_learnfw.services.gamification_service import (
    award_points,
    check_and_award_badges,
    get_leaderboard,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="gamer", password="test1234")


@pytest.fixture
def user2(db):
    return User.objects.create_user(username="gamer2", password="test1234")


@pytest.fixture
def badge(db):
    return Badge.objects.create(
        name="First Steps",
        slug="first-steps",
        trigger="points_reached",
        threshold=50,
    )


@pytest.fixture
def streak_badge(db):
    return Badge.objects.create(
        name="Streak Master",
        slug="streak-master",
        trigger="streak_reached",
        threshold=3,
    )


@pytest.mark.django_db
class TestBadgeModel:
    def test_should_create_badge(self, badge):
        assert badge.pk is not None
        assert badge.slug == "first-steps"
        assert badge.threshold == 50

    def test_should_str(self, badge):
        assert str(badge) == "First Steps"


@pytest.mark.django_db
class TestUserPointsModel:
    def test_should_create_user_points(self, user):
        up = UserPoints.objects.create(user=user, total_points=100)
        assert up.total_points == 100
        assert up.current_streak == 0

    def test_should_str(self, user):
        up = UserPoints.objects.create(
            user=user, total_points=42, current_streak=3
        )
        assert "42pts" in str(up)
        assert "streak 3d" in str(up)


@pytest.mark.django_db
class TestAwardPoints:
    def test_should_award_points(self, user):
        tx = award_points(user, 10, "Lesson completed", source_type="lesson")
        assert isinstance(tx, PointsTransaction)
        assert tx.points == 10
        up = UserPoints.objects.get(user=user)
        assert up.total_points == 10

    def test_should_accumulate_points(self, user):
        award_points(user, 10, "Lesson 1")
        award_points(user, 20, "Lesson 2")
        up = UserPoints.objects.get(user=user)
        assert up.total_points == 30

    def test_should_not_go_negative(self, user):
        award_points(user, 10, "Lesson 1")
        award_points(user, -50, "Penalty")
        up = UserPoints.objects.get(user=user)
        assert up.total_points == 0

    def test_should_track_streak(self, user):
        award_points(user, 10, "Day 1")
        up = UserPoints.objects.get(user=user)
        assert up.current_streak == 1
        assert up.longest_streak == 1


@pytest.mark.django_db
class TestCheckAndAwardBadges:
    def test_should_award_points_badge(self, user, badge):
        award_points(user, 60, "Big lesson")
        awarded = check_and_award_badges(user)
        assert len(awarded) == 1
        assert awarded[0].badge == badge

    def test_should_not_award_twice(self, user, badge):
        award_points(user, 60, "Big lesson")
        check_and_award_badges(user)
        awarded = check_and_award_badges(user)
        assert len(awarded) == 0

    def test_should_award_streak_badge(self, user, streak_badge):
        UserPoints.objects.create(
            user=user, total_points=0, current_streak=5, longest_streak=5
        )
        awarded = check_and_award_badges(user)
        assert len(awarded) == 1
        assert awarded[0].badge == streak_badge

    def test_should_not_award_below_threshold(self, user, badge):
        award_points(user, 10, "Small lesson")
        awarded = check_and_award_badges(user)
        assert len(awarded) == 0


@pytest.mark.django_db
class TestLeaderboard:
    def test_should_return_leaderboard(self, user, user2):
        award_points(user, 100, "Big")
        award_points(user2, 50, "Medium")
        lb = get_leaderboard()
        assert len(lb) == 2
        assert lb[0]["total_points"] >= lb[1]["total_points"]

    def test_should_limit_leaderboard(self, user, user2):
        award_points(user, 100, "Big")
        award_points(user2, 50, "Medium")
        lb = get_leaderboard(limit=1)
        assert len(lb) == 1
