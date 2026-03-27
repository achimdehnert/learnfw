"""Abstract base for grading backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GradingResult:
    """Result of grading a single answer."""

    score: int  # 0-100
    feedback: str


class GradingBackend(ABC):
    """Abstract grading backend.

    Implementations must be stateless — no DB access.
    The caller provides questions and answers as plain dicts/strings.
    """

    @abstractmethod
    def grade(
        self,
        questions: list[dict],
        answers: list[str],
    ) -> list[GradingResult]:
        """Grade user answers against expected answers.

        Args:
            questions: List of question dicts with keys:
                - question: str (the question text)
                - expected: str (the expected answer)
                - keywords: list[str] (optional, for keyword matching)
            answers: List of user answer strings (same length as questions).

        Returns:
            List of GradingResult (same length as questions).
        """
        ...
