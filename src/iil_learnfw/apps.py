"""Django AppConfig for iil-learnfw."""

from django.apps import AppConfig


class IilLearnfwConfig(AppConfig):
    """IIL Learning Platform Framework."""

    name = "iil_learnfw"
    verbose_name = "IIL Learning Platform"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Import signals and register system checks on app ready."""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
        # ADR-142: Assessment Engine system checks (ADR-083 compliant)
        try:
            from . import checks  # noqa: F401
        except ImportError:
            pass
