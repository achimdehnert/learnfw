"""
iil_learnfw/checks.py

Django System Checks für iil-learnfw.
ADR-083: Settings-Validation via Django System Check, nicht via raise ImproperlyConfigured.

Registriert:
  E001  ASSESSMENT_IP_HASH_SALT fehlt (deploy=True → nur in Produktion Error)
  W001  ASSESSMENT_IP_HASH_SALT fehlt (deploy=False → in Dev Warning)
  E002  ASSESSMENT_ENGINE_ENABLED aber WeasyPrint nicht installiert
  E003  Scoring-Strategie-Wert in AssessmentType ungültig (optional, via DB-Check)
"""
from __future__ import annotations

import logging

from django.core.checks import Error, Warning, register

logger = logging.getLogger(__name__)


def _get_learnfw_setting(key: str, default=None):
    """Liest aus IIL_LEARNFW-Dict in settings."""
    from django.conf import settings  # noqa: PLC0415
    return getattr(settings, "IIL_LEARNFW", {}).get(key, default)


# ---------------------------------------------------------------------------
# E001 / W001: ASSESSMENT_IP_HASH_SALT
# ---------------------------------------------------------------------------

@register(deploy=True)
def check_assessment_ip_hash_salt_deploy(app_configs, **kwargs):
    """
    In Produktion (deploy=True): Error wenn Salt fehlt.
    Verhindert dass DSGVO-relevantes IP-Hashing ohne Salt deployed wird.
    """
    errors = []
    salt = _get_learnfw_setting("ASSESSMENT_IP_HASH_SALT", "")
    if not salt:
        errors.append(Error(
            "IIL_LEARNFW['ASSESSMENT_IP_HASH_SALT'] ist nicht konfiguriert.",
            hint=(
                "Setze IIL_LEARNFW['ASSESSMENT_IP_HASH_SALT'] auf einen "
                "sicheren zufälligen Wert (min. 32 Zeichen) in den Settings. "
                "Beispiel: python -c \"import secrets; print(secrets.token_hex(32))\""
            ),
            id="iil_learnfw.E001",
        ))
    return errors


@register()
def check_assessment_ip_hash_salt_dev(app_configs, **kwargs):
    """
    In Entwicklung: Warning wenn Salt fehlt (kein Hard-Block).
    """
    warnings = []
    salt = _get_learnfw_setting("ASSESSMENT_IP_HASH_SALT", "")
    if not salt:
        warnings.append(Warning(
            "IIL_LEARNFW['ASSESSMENT_IP_HASH_SALT'] ist nicht konfiguriert.",
            hint=(
                "In Produktion wird dies zu einem Error (E001). "
                "Für Development genügt ein beliebiger String."
            ),
            id="iil_learnfw.W001",
        ))
    return warnings


# ---------------------------------------------------------------------------
# E002: WeasyPrint-Check wenn Report-Engine konfiguriert
# ---------------------------------------------------------------------------

@register(deploy=True)
def check_assessment_report_engine(app_configs, **kwargs):
    """
    Wenn ASSESSMENT_REPORT_ENGINE='weasyprint', muss weasyprint installiert sein.
    """
    errors = []
    engine = _get_learnfw_setting("ASSESSMENT_REPORT_ENGINE", "none")
    if engine == "weasyprint":
        try:
            import weasyprint  # noqa: F401
        except ImportError:
            errors.append(Error(
                "IIL_LEARNFW['ASSESSMENT_REPORT_ENGINE']='weasyprint', "
                "aber weasyprint ist nicht installiert.",
                hint="pip install weasyprint — oder setze ASSESSMENT_REPORT_ENGINE='none'.",
                id="iil_learnfw.E002",
            ))
    return errors


# ---------------------------------------------------------------------------
# W002: ASSESSMENT_LEAD_CAPTURE ohne E-Mail-Backend
# ---------------------------------------------------------------------------

@register(deploy=True)
def check_assessment_lead_capture(app_configs, **kwargs):
    """
    Wenn ASSESSMENT_LEAD_CAPTURE=True, muss ein reales E-Mail-Backend konfiguriert sein.
    """
    warnings = []
    lead_capture = _get_learnfw_setting("ASSESSMENT_LEAD_CAPTURE", False)
    if lead_capture:
        from django.conf import settings  # noqa: PLC0415
        backend = getattr(settings, "EMAIL_BACKEND", "")
        if "console" in backend or "dummy" in backend or "locmem" in backend:
            warnings.append(Warning(
                f"ASSESSMENT_LEAD_CAPTURE=True, aber EMAIL_BACKEND='{backend}' "
                "sendet keine echten E-Mails.",
                hint="Setze EMAIL_BACKEND auf einen SMTP- oder SES-Backend in Produktion.",
                id="iil_learnfw.W002",
            ))
    return warnings
