"""DRF Router for iil-learnfw API."""

from rest_framework.routers import DefaultRouter

from . import viewsets

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

urlpatterns = router.urls
