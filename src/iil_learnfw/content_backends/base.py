"""Abstract content backend."""

from abc import ABC, abstractmethod


class AbstractContentBackend(ABC):
    """Base class for content rendering backends."""

    @abstractmethod
    def render(self, lesson) -> str:
        """Render lesson content to HTML."""
        ...

    @abstractmethod
    def can_handle(self, content_type: str) -> bool:
        """Check if this backend handles the given content type."""
        ...
