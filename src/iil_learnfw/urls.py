"""URL configuration for iil-learnfw.

Consumer-Hubs include this in their urls.py:
    path("schulungen/", include("iil_learnfw.urls"))
"""

from django.urls import path

from . import views

app_name = "iil_learnfw"

urlpatterns: list = [
    path("", views.course_list, name="course-list"),
    path("<slug:slug>/", views.course_detail, name="course-detail"),
    # 0.6.0 (writing-hub#994 K4): die Lektion selbst — vorher zeigte der Kurs nur Titel.
    path("<slug:slug>/lektion/<int:pk>/", views.lesson_detail, name="lesson-detail"),
]
