"""Gamification service — points, badges, streaks (ADR-041)."""

import logging
from datetime import date

from django.db import transaction

from ..models.gamification import Badge, PointsTransaction, UserBadge, UserPoints
from ..settings import get_setting

logger = logging.getLogger(__name__)


def award_points(
    user, points: int, reason: str, source_type: str = "manual",
    tenant_id=None,
) -> PointsTransaction:
    """Award points to a user and update streak."""
    tx = PointsTransaction.objects.create(
        user=user,
        points=points,
        reason=reason,
        source_type=source_type,
        tenant_id=tenant_id,
    )

    user_points, _ = UserPoints.objects.get_or_create(
        user=user, defaults={"tenant_id": tenant_id}
    )
    user_points.total_points = max(0, user_points.total_points + points)

    today = date.today()
    threshold = get_setting("STREAK_THRESHOLD_DAYS")
    if user_points.last_activity_date:
        delta = (today - user_points.last_activity_date).days
        if delta <= threshold:
            if delta > 0:
                user_points.current_streak += 1
        else:
            user_points.current_streak = 1
    else:
        user_points.current_streak = 1

    user_points.longest_streak = max(
        user_points.longest_streak, user_points.current_streak
    )
    user_points.last_activity_date = today
    user_points.save()

    logger.info(
        "User %s awarded %+d pts (%s), total=%d, streak=%d",
        user, points, reason, user_points.total_points,
        user_points.current_streak,
    )
    return tx


@transaction.atomic
def check_and_award_badges(user, tenant_id=None) -> list[UserBadge]:
    """Check all active badges and award any newly earned ones."""
    awarded = []
    badges = Badge.objects.filter(is_active=True)
    if tenant_id:
        badges = badges.filter(tenant_id=tenant_id)

    user_points_obj = UserPoints.objects.filter(user=user).first()
    total_points = user_points_obj.total_points if user_points_obj else 0
    streak = user_points_obj.current_streak if user_points_obj else 0

    for badge in badges:
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            continue

        earned = False
        if badge.trigger == "points_reached" and total_points >= badge.threshold:
            earned = True
        elif badge.trigger == "streak_reached" and streak >= badge.threshold:
            earned = True

        if earned:
            ub = UserBadge.objects.create(
                user=user, badge=badge, tenant_id=tenant_id,
            )
            awarded.append(ub)
            logger.info("Badge '%s' awarded to %s", badge.name, user)

    return awarded


def get_leaderboard(tenant_id=None, limit: int | None = None) -> list[dict]:
    """Get top users by total points."""
    if limit is None:
        limit = get_setting("LEADERBOARD_SIZE")

    qs = UserPoints.objects.select_related("user").order_by("-total_points")
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    return [
        {
            "user": up.user,
            "total_points": up.total_points,
            "current_streak": up.current_streak,
            "longest_streak": up.longest_streak,
        }
        for up in qs[:limit]
    ]
