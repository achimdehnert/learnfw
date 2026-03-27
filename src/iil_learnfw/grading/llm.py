"""LLM-based grading via OpenAI/Groq-compatible API.

Extracted from coach-hub apps/learning/grading.py (ADR-150).
Configurable via IIL_LEARNFW settings:
    GRADING_API_KEY, GRADING_API_BASE, GRADING_MODEL
"""

from __future__ import annotations

import json
import logging

from iil_learnfw.grading.base import GradingBackend, GradingResult
from iil_learnfw.grading.keyword import KeywordFallback

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Du bist ein freundlicher KI-Tutor. Du bewertest Freitext-Antworten \
auf Wissensfragen.

Für jede Frage erhältst du:
- Die Frage
- Die erwartete Musterantwort
- Die Antwort des Teilnehmers

Bewerte jede Antwort mit:
- "score": 0-100 (0=falsch, 50=teilweise, 100=korrekt)
- "feedback": 1-2 Sätze auf Deutsch — freundlich, konstruktiv

Antworte AUSSCHLIESSLICH als JSON-Array. Beispiel:
[{"score": 85, "feedback": "Sehr gut! ..."}]
"""


def _build_user_prompt(
    questions: list[dict],
    answers: list[str],
) -> str:
    parts = []
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        parts.append(
            f"Frage {i}: {q['question']}\n"
            f"Musterantwort: {q['expected']}\n"
            f"Teilnehmer-Antwort: {a}\n"
        )
    return "\n".join(parts)


class LLMGrading(GradingBackend):
    """Grade answers via OpenAI/Groq-compatible chat completion API.

    Falls back to KeywordFallback if:
    - No API key configured
    - API call fails
    - Response is malformed

    Args:
        api_key: API key (or read from settings).
        api_base: API base URL (default: OpenAI).
        model: Model name (default: gpt-4o-mini).
        timeout: Request timeout in seconds.
        system_prompt: Custom system prompt (optional).
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 15.0,
        system_prompt: str = "",
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = timeout
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self._fallback = KeywordFallback()

    @classmethod
    def from_settings(cls) -> "LLMGrading":
        """Create instance from Django IIL_LEARNFW settings."""
        from iil_learnfw.settings import get_setting

        return cls(
            api_key=get_setting("GRADING_API_KEY"),
            api_base=get_setting("GRADING_API_BASE"),
            model=get_setting("GRADING_MODEL"),
            timeout=get_setting("GRADING_TIMEOUT"),
            system_prompt=get_setting("GRADING_SYSTEM_PROMPT"),
        )

    def grade(
        self,
        questions: list[dict],
        answers: list[str],
    ) -> list[GradingResult]:
        if not self.api_key:
            return self._fallback.grade(questions, answers)

        try:
            import httpx
        except ImportError:
            logger.warning(
                "httpx not installed. Install with: "
                "pip install 'iil-learnfw[grading]'"
            )
            return self._fallback.grade(questions, answers)

        try:
            prompt = _build_user_prompt(questions, answers)
            resp = httpx.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0.1,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            raw_results = json.loads(content)
            if (isinstance(raw_results, list)
                    and len(raw_results) == len(questions)):
                return [
                    GradingResult(
                        score=max(0, min(100, int(r.get("score", 0)))),
                        feedback=str(r.get("feedback", "")),
                    )
                    for r in raw_results
                ]
            logger.warning(
                "LLM returned %d results, expected %d",
                len(raw_results),
                len(questions),
            )
        except Exception:
            logger.exception("AI grading failed, falling back to keywords")

        return self._fallback.grade(questions, answers)


def grade_answers(
    questions: list[dict],
    answers: list[str],
    api_key: str = "",
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> list[GradingResult]:
    """Convenience function — grade answers with LLM or keyword fallback.

    This is the simplest way to use grading:

        from iil_learnfw.grading import grade_answers
        results = grade_answers(questions, answers, api_key="sk-...")
    """
    grader = LLMGrading(api_key=api_key, api_base=api_base, model=model)
    return grader.grade(questions, answers)
