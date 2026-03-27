"""Keyword-based grading fallback — no external API needed."""

from __future__ import annotations

from iil_learnfw.grading.base import GradingBackend, GradingResult


class KeywordFallback(GradingBackend):
    """Simple keyword matching for self-test grading.

    Counts how many expected keywords appear in the user's answer.
    Score = (hits / total_keywords) * 100.

    Extracted from coach-hub apps/learning/grading.py (ADR-150).
    """

    def grade(
        self,
        questions: list[dict],
        answers: list[str],
    ) -> list[GradingResult]:
        results = []
        for q, a in zip(questions, answers):
            a_lower = a.lower().strip()
            if not a_lower:
                results.append(GradingResult(
                    score=0,
                    feedback="Keine Antwort eingegeben.",
                ))
                continue

            kw = q.get("keywords", [])
            if not kw:
                results.append(GradingResult(
                    score=50,
                    feedback=(
                        "Antwort erhalten \u2014 "
                        "automatische Bewertung nicht m\u00f6glich."
                    ),
                ))
                continue

            hits = sum(1 for k in kw if k.lower() in a_lower)
            pct = round(hits / len(kw) * 100)

            if pct >= 80:
                fb = "Sehr gut \u2014 alle Kernpunkte genannt!"
            elif pct >= 50:
                fb = (
                    "Teilweise richtig. "
                    f"Musterantwort: {q['expected']}"
                )
            else:
                fb = (
                    "Leider nicht korrekt. "
                    f"Richtige Antwort: {q['expected']}"
                )
            results.append(GradingResult(score=pct, feedback=fb))
        return results
