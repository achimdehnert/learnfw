"""Minimal Django settings for iil-learnfw tests."""

SECRET_KEY = "test-secret-key-not-for-production"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "iil_learnfw",
]

# Views werden über die Bibliotheks-URLs getestet (0.6.0, Lektionsseite) —
# vorher liefen die Tests nur gegen Modelle, Services und die API.
ROOT_URLCONF = "tests.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

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
    # Assessment Engine (ADR-142)
    "ASSESSMENT_ENGINE_ENABLED": True,
    "ASSESSMENT_REPORT_ENGINE": "none",
    "ASSESSMENT_LEAD_CAPTURE": False,
    "ASSESSMENT_IP_HASH_SALT": "test-salt-not-for-production",
    "DEFAULT_TENANT_ID": "00000000-0000-0000-0000-000000000000",
}
