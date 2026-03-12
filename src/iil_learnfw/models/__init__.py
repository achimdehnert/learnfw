"""iil-learnfw models.

All models use BigAutoField (ADR-022) and optional tenant_id (ADR-137).
"""

from .course import Category, Chapter, Course, Enrollment, Lesson  # noqa: F401
