"""iil-learnfw grading — AI-supported answer grading.

Backends:
- LLMGrading: OpenAI/Groq API (configurable)
- KeywordFallback: Simple keyword matching (no API needed)
"""

from iil_learnfw.grading.base import (  # noqa: F401
    GradingBackend,
    GradingResult,
)
from iil_learnfw.grading.keyword import KeywordFallback  # noqa: F401
from iil_learnfw.grading.llm import LLMGrading  # noqa: F401

__all__ = ["GradingBackend", "GradingResult", "LLMGrading", "KeywordFallback"]
