"""iil-learnfw models.

All models use BigAutoField (ADR-022) and optional tenant_id (ADR-137).
"""

from .assessment import Answer, Attempt, AttemptAnswer, Question, Quiz  # noqa: F401
from .certificate import CertificateTemplate, IssuedCertificate  # noqa: F401
from .course import Category, Chapter, Course, CourseManager, Enrollment, Lesson  # noqa: F401
from .gamification import Badge, PointsTransaction, UserBadge, UserPoints  # noqa: F401
from .onboarding import OnboardingFlow, OnboardingStep, UserOnboardingState  # noqa: F401
from .progress import UserProgress  # noqa: F401
from .scorm import ScormPackage, ScormTracking  # noqa: F401
