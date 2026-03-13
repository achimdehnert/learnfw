"""iil-learnfw template views."""

from django.shortcuts import render

from iil_learnfw.models import Course


def course_list(request):
    """Public course listing."""
    courses = Course.objects.published()
    return render(
        request, "iil_learnfw/course_list.html", {"courses": courses},
    )
