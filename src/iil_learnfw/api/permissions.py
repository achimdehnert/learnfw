"""DRF permissions for iil-learnfw."""

from rest_framework.permissions import BasePermission


class IsEnrolled(BasePermission):
    """Allow access only if user is enrolled in the course."""

    def has_object_permission(self, request, view, obj):
        from ..models.course import Enrollment

        course = getattr(obj, "course", obj)
        return Enrollment.objects.filter(
            user=request.user, course=course, status="active"
        ).exists()


class IsAuthorOrReadOnly(BasePermission):
    """Allow write access only to the course author."""

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        course = getattr(obj, "course", obj)
        return course.author == request.user
