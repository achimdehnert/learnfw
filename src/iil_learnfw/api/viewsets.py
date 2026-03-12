"""DRF ViewSets for iil-learnfw."""

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models.assessment import Attempt, Quiz
from ..models.certificate import IssuedCertificate
from ..models.course import Category, Course, Enrollment
from ..models.gamification import UserBadge, UserPoints
from ..models.progress import UserProgress
from ..services.enrollment_service import enroll, withdraw
from ..services.gamification_service import get_leaderboard
from ..services.progress_service import complete_lesson, get_course_progress, start_lesson
from .serializers import (
    AttemptSerializer,
    CategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    IssuedCertificateSerializer,
    LeaderboardEntrySerializer,
    QuizSerializer,
    UserBadgeSerializer,
    UserPointsSerializer,
    UserProgressSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve course categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve courses."""

    queryset = Course.objects.filter(status="published")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        """Enroll the current user in this course."""
        enrollment = enroll(request.user, int(pk))
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        """Withdraw the current user from this course."""
        withdraw(request.user, int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """Get current user's progress in this course."""
        data = get_course_progress(request.user, int(pk))
        return Response(data)


class EnrollmentViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """List current user's enrollments."""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)


class ProgressViewSet(viewsets.GenericViewSet):
    """Track lesson progress."""

    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="start/(?P<lesson_id>[0-9]+)")
    def start(self, request, lesson_id=None):
        """Start a lesson."""
        progress = start_lesson(request.user, int(lesson_id))
        return Response(UserProgressSerializer(progress).data)

    @action(detail=False, methods=["post"], url_path="complete/(?P<lesson_id>[0-9]+)")
    def complete(self, request, lesson_id=None):
        """Complete a lesson."""
        progress = complete_lesson(request.user, int(lesson_id))
        return Response(UserProgressSerializer(progress).data)


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve quizzes."""

    queryset = Quiz.objects.filter(is_active=True)
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]


class AttemptViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """List and retrieve quiz attempts for current user."""

    serializer_class = AttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user)


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve issued certificates."""

    serializer_class = IssuedCertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IssuedCertificate.objects.filter(user=self.request.user)


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve user badges."""

    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user).select_related("badge")


class LeaderboardViewSet(viewsets.ViewSet):
    """Leaderboard endpoint."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get leaderboard."""
        entries = get_leaderboard()
        serializer = LeaderboardEntrySerializer(entries, many=True)
        return Response(serializer.data)


class MyPointsViewSet(viewsets.ViewSet):
    """Current user's points and streak."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get current user's points."""
        try:
            points = UserPoints.objects.get(user=request.user)
            return Response(UserPointsSerializer(points).data)
        except UserPoints.DoesNotExist:
            return Response({
                "total_points": 0, "current_streak": 0,
                "longest_streak": 0, "last_activity_date": None,
            })
