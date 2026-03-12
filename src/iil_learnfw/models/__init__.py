"""iil-learnfw models.

All models use BigAutoField (ADR-022) and optional tenant_id (ADR-137).
"""

from .assessment import Answer, Attempt, AttemptAnswer, Question, Quiz  # noqa: F401
from .certificate import CertificateTemplate, IssuedCertificate  # noqa: F401
from .course import Category, Chapter, Course, Enrollment, Lesson  # noqa: F401
from .progress import UserProgress  # noqa: F401
