"""URLconf der Test-Settings: die Bibliotheks-URLs unter ``kurse/`` wie in learn-hub."""

from django.urls import include, path

urlpatterns = [
    path("kurse/", include("iil_learnfw.urls")),
]
