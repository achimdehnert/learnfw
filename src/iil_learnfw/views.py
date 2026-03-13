"""iil-learnfw template views."""

from django.shortcuts import get_object_or_404, render

from iil_learnfw.models import Course


def course_list(request):
    """Public course listing."""
    courses = Course.objects.published()
    return render(
        request, "iil_learnfw/course_list.html", {"courses": courses},
    )


def course_detail(request, slug):
    """Course detail page with chapters and lessons."""
    course = get_object_or_404(
        Course.objects.filter(status="published"), slug=slug,
    )
    chapters = course.chapters.prefetch_related("lessons").all()
    return render(
        request,
        "iil_learnfw/course_detail.html",
        {"course": course, "chapters": chapters},
    )
