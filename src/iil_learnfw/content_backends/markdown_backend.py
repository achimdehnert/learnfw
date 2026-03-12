"""Markdown content backend."""

import logging

from .base import AbstractContentBackend

logger = logging.getLogger(__name__)


class MarkdownBackend(AbstractContentBackend):
    """Renders Markdown lesson content to HTML."""

    def can_handle(self, content_type: str) -> bool:
        return content_type == "markdown"

    def render(self, lesson) -> str:
        """Render markdown content to HTML."""
        try:
            import markdown
        except ImportError:
            logger.warning(
                "markdown package not installed. "
                "Install with: pip install iil-learnfw[markdown]"
            )
            return lesson.content_text

        return markdown.markdown(
            lesson.content_text,
            extensions=["extra", "codehilite", "toc"],
        )
