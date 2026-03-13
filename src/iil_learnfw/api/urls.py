"""DRF Router for iil-learnfw API."""

from rest_framework.routers import DefaultRouter

from . import viewsets
from .assessment_engine_viewsets import (
    AssessmentAttemptViewSet,
    AssessmentReportViewSet,
    AssessmentTypeViewSet,
)

router = DefaultRouter()
router.register("categories", viewsets.CategoryViewSet)
router.register("courses", viewsets.CourseViewSet)
router.register("enrollments", viewsets.EnrollmentViewSet, basename="enrollment")
router.register("progress", viewsets.ProgressViewSet, basename="progress")
router.register("quizzes", viewsets.QuizViewSet)
router.register("attempts", viewsets.AttemptViewSet, basename="attempt")
router.register("certificates", viewsets.CertificateViewSet, basename="certificate")
router.register("badges", viewsets.BadgeViewSet, basename="badge")
router.register("leaderboard", viewsets.LeaderboardViewSet, basename="leaderboard")
router.register("my-points", viewsets.MyPointsViewSet, basename="my-points")
# Assessment Engine (ADR-142)
router.register("assessments/types", AssessmentTypeViewSet, basename="assessment-type")
router.register("assessments/attempts", AssessmentAttemptViewSet, basename="assessment-attempt")
router.register("assessments/reports", AssessmentReportViewSet, basename="assessment-report")

urlpatterns = router.urls
