"""Default settings for iil-learnfw.

Consumers override via IIL_LEARNFW dict in their Django settings.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULTS = {
    "TENANT_AWARE": False,
    "AUTHORING_ENABLED": False,
    "ONBOARDING_ENABLED": False,
    "ENROLLMENT_MODE": "self_enroll",  # "self_enroll" | "admin_only" | "approval"
    "ENABLE_REVIEW_WORKFLOW": False,
    "CONTENT_VERSIONING": False,
    "PPTX_AUTO_SPLIT": True,
    "PPTX_EXTRACT_NOTES": True,
    "PPTX_GENERATE_PDF": False,
    "MARKDOWN_EDITOR": "easymde",  # "easymde" | "textarea"
    "AUTO_SAVE_INTERVAL": 30,  # seconds, 0 = disabled
    "CERTIFICATE_ENGINE": "weasyprint",  # "weasyprint" | "none"
    "GAMIFICATION_ENABLED": True,
    "LEADERBOARD_SIZE": 10,
    "POINTS_PER_LESSON": 10,
    "POINTS_PER_QUIZ_PASS": 50,
    "STREAK_THRESHOLD_DAYS": 1,
    # Grading (ADR-150)
    "GRADING_ENABLED": False,
    "GRADING_API_KEY": "",
    "GRADING_API_BASE": "https://api.openai.com/v1",
    "GRADING_MODEL": "gpt-4o-mini",
    "GRADING_TIMEOUT": 15.0,
    "GRADING_SYSTEM_PROMPT": "",
    # Assessment Engine (ADR-142/150)
    "ASSESSMENT_ENGINE_ENABLED": True,
    "ASSESSMENT_REPORT_ENGINE": "none",  # "weasyprint" | "none"
    "ASSESSMENT_IP_HASH_SALT": "",
    "DEFAULT_TENANT_ID": "00000000-0000-0000-0000-000000000000",
}


def get_setting(key: str):
    """Get a learnfw setting with fallback to defaults."""
    user_settings = getattr(settings, "IIL_LEARNFW", {})
    if key in user_settings:
        return user_settings[key]
    if key in DEFAULTS:
        return DEFAULTS[key]
    raise KeyError(f"Unknown iil-learnfw setting: {key}")
