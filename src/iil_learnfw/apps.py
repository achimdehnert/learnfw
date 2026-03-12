"""Django AppConfig for iil-learnfw."""

from django.apps import AppConfig


class IilLearnfwConfig(AppConfig):
    """IIL Learning Platform Framework."""

    name = "iil_learnfw"
    verbose_name = "IIL Learning Platform"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Import signals on app ready."""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
