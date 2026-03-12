"""DRF serializers for iil-learnfw."""

from rest_framework import serializers

from ..models.assessment import Answer, Attempt, Question, Quiz
from ..models.certificate import IssuedCertificate
from ..models.course import Category, Chapter, Course, Enrollment, Lesson
from ..models.gamification import Badge, UserBadge, UserPoints
from ..models.progress import UserProgress


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon", "ordering"]
        read_only_fields = ["id"]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id", "chapter", "title", "content_type",
            "estimated_duration_minutes", "ordering", "is_mandatory",
        ]
        read_only_fields = ["id"]


class ChapterSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ["id", "course", "title", "description", "ordering", "lessons"]
        read_only_fields = ["id"]


class CourseListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default="")

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "status",
            "category", "category_name", "is_global",
            "estimated_duration_minutes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CourseDetailSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default="")

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "status",
            "category", "category_name", "is_global",
            "marketplace_enabled", "module_code",
            "estimated_duration_minutes", "passing_score",
            "created_at", "updated_at", "chapters",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id", "user", "course", "course_title",
            "status", "enrolled_at", "completed_at",
        ]
        read_only_fields = ["id", "user", "enrolled_at", "completed_at"]


class UserProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = UserProgress
        fields = [
            "id", "user", "lesson", "lesson_title",
            "status", "started_at", "completed_at", "time_spent_seconds",
        ]
        read_only_fields = ["id", "user", "started_at", "completed_at"]


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text", "ordering"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "quiz", "question_type", "text",
            "points", "ordering", "answers",
        ]
        read_only_fields = ["id"]


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id", "course", "chapter", "title",
            "passing_score", "max_attempts", "time_limit_minutes",
            "shuffle_questions", "question_count",
        ]
        read_only_fields = ["id"]


class AttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id", "user", "quiz", "quiz_title",
            "started_at", "completed_at", "score", "passed",
        ]
        read_only_fields = ["id", "user", "started_at", "completed_at", "score", "passed"]


class IssuedCertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = IssuedCertificate
        fields = [
            "id", "user", "course", "course_title",
            "issued_at", "expires_at", "verification_token",
        ]
        read_only_fields = ["id", "user", "issued_at", "verification_token"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "slug", "icon", "description", "trigger", "threshold"]
        read_only_fields = ["id"]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ["id", "badge", "awarded_at"]
        read_only_fields = ["id", "awarded_at"]


class UserPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPoints
        fields = ["total_points", "current_streak", "longest_streak", "last_activity_date"]
        read_only_fields = fields


class LeaderboardEntrySerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username")
    total_points = serializers.IntegerField()
    current_streak = serializers.IntegerField()
