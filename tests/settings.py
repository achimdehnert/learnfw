"""Minimal Django settings for iil-learnfw tests."""

SECRET_KEY = "test-secret-key-not-for-production"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "iil_learnfw",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

IIL_LEARNFW = {
    "TENANT_AWARE": False,
    "AUTHORING_ENABLED": True,
    "GAMIFICATION_ENABLED": True,
}
