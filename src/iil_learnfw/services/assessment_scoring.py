"""
iil_learnfw/services/assessment_scoring.py

Scoring-Service — Strategy Pattern für alle Assessment-Typen.

Korrekturen gegenüber ADR-142-PROPOSED:
  K-1  scale_min/scale_max werden korrekt verwendet (hardcodiertes 4 entfernt)
  K-4  WeightedLikertScoring vollständig implementiert
  K-5  ScoringStrategy als ABC mit @abstractmethod
  K-6  Maturity-Lookup über total_pct (0-100), nicht über Rohscore
  M-4  Registry als Klasse mit register()-Methode
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
import dataclasses
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ergebnis-Dataclasses (frozen → threadsafe, hashable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DimensionResult:
    """Scoring-Ergebnis einer einzelnen Dimension."""
    key:        str
    label:      str
    score:      Decimal           # Durchschnitt auf Skala [scale_min, scale_max]
    pct:        int               # 0-100 normalisiert
    weight:     Decimal           # Gewichtungsfaktor (für WeightedLikert relevant)


@dataclass(frozen=True)
class AssessmentResult:
    """Vollständiges Scoring-Ergebnis eines Attempts."""
    total_score:          Decimal              # Rohsumme aller Antworten
    total_pct:            int                  # 0-100 normalisiert (Maturity-Lookup-Basis!)
    maturity_key:         str
    maturity_label:       str
    maturity_color:       str
    maturity_description: str
    dimensions:           list[DimensionResult]
    weakest:              str                  # dimension.key
    strongest:            str                  # dimension.key
    recommendations:      list[dict[str, Any]] = field(default_factory=list)
    # Befüllt durch RecommendationService.get_recommendations()


# ---------------------------------------------------------------------------
# Typing-Hilfsmittel für Scoring-Inputs
# ---------------------------------------------------------------------------

class _MaturityLevelProtocol:
    """Duck-typing für AssessmentMaturityLevel-Instanzen."""
    key:         str
    label:       str
    color:       str
    description: str
    pct_min:     int
    pct_max:     int


class _DimensionProtocol:
    """Duck-typing für AssessmentDimension-Instanzen."""
    key:    str
    label:  str
    weight: Decimal


class _QuestionProtocol:
    """Duck-typing für AssessmentQuestion-Instanzen."""
    pk:        int
    public_id: object  # uuid.UUID
    dimension: _DimensionProtocol


# ---------------------------------------------------------------------------
# Basis-Strategie (ABC)
# ---------------------------------------------------------------------------

class ScoringStrategy(ABC):
    """
    Abstrakte Basis für alle Scoring-Strategien.

    Alle Implementierungen müssen pure functions sein:
    kein DB-Zugriff, kein Side-Effect. Der Aufrufer (AssessmentService)
    fetcht alle benötigten ORM-Objekte und übergibt sie als Parameter.
    """

    @abstractmethod
    def score(
        self,
        questions:       list,               # list[AssessmentQuestion]
        answers:         dict[str, Any],      # {str(question.public_id): snapshot_dict|raw_value}
        dimensions:      list,               # list[AssessmentDimension]
        maturity_levels: list,               # list[AssessmentMaturityLevel] — aufsteigend nach pct_min
        scale_min:       int,
        scale_max:       int,
    ) -> AssessmentResult:
        ...


# ---------------------------------------------------------------------------
# LikertScoring
# ---------------------------------------------------------------------------

class LikertScoring(ScoringStrategy):
    """
    Likert-Skala (scale_min-N) → Dimensions-Durchschnitte → Maturity-Level.

    Verwendet von: KI-Souveränität, DSGVO, NIS2, IT-Security.

    Maturity-Lookup: über total_pct (0-100), nicht Rohscore.
    """

    def score(
        self,
        questions:       list,
        answers:         dict[str, Any],
        dimensions:      list,
        maturity_levels: list,
        scale_min:       int,
        scale_max:       int,
    ) -> AssessmentResult:
        scale_range = scale_max - scale_min
        if scale_range <= 0:
            raise ValueError(
                f"Ungültige Skala: scale_min={scale_min} muss < scale_max={scale_max} sein."
            )

        # Antworten aus Snapshot-Format extrahieren
        # Unterstützt sowohl Snapshot-Dict als auch rohen int-Wert (Rückwärtskompatibilität)
        dim_values:   dict[str, list[int]]  = {}
        dim_meta:     dict[str, dict]       = {}

        for q in questions:
            dk = q.dimension.key
            if dk not in dim_values:
                dim_values[dk] = []
                dim_meta[dk] = {
                    "label":  q.dimension.label,
                    "weight": q.dimension.weight,
                }

            raw = answers.get(str(q.public_id))
            if raw is None:
                # Fallback: versuche alten PK-basierten Key (Migration QuickCheck → Engine)
                raw = answers.get(str(q.pk))
            if raw is None:
                continue

            # Snapshot-Dict oder roher Wert
            val = raw.get("value", raw) if isinstance(raw, dict) else raw

            try:
                val_int = int(val)
            except (TypeError, ValueError):
                logger.warning("Ungültiger Antwort-Wert %r für Frage %s — wird ignoriert.", val, q.public_id)
                continue

            # K-1: scale_min/scale_max korrekt verwenden
            clamped = max(scale_min, min(val_int, scale_max))
            dim_values[dk].append(clamped)

        # Rohsumme und max-möglicher Wert
        all_values  = [v for vals in dim_values.values() for v in vals]
        total_raw   = sum(all_values)
        max_possible = len(all_values) * scale_max
        min_possible = len(all_values) * scale_min

        # K-6: total_pct normalisiert auf 0-100
        if max_possible > min_possible:
            total_pct = round(
                (total_raw - min_possible) / (max_possible - min_possible) * 100
            )
        else:
            total_pct = 0
        total_pct = max(0, min(100, total_pct))

        # Dimensions-Ergebnisse
        dim_results: list[DimensionResult] = []
        for dk, vals in dim_values.items():
            if not vals:
                avg = Decimal(str(scale_min))
                pct = 0
            else:
                raw_avg = sum(vals) / len(vals)
                avg     = Decimal(str(raw_avg)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                # K-1: Normalisierung über gesamte Skala (nicht hardcodiert /3)
                pct     = round((float(avg) - scale_min) / scale_range * 100)
                pct     = max(0, min(100, pct))

            dim_results.append(DimensionResult(
                key=dk,
                label=dim_meta[dk]["label"],
                score=avg,
                pct=pct,
                weight=dim_meta[dk]["weight"],
            ))

        weakest   = min(dim_results, key=lambda d: d.score).key if dim_results else ""
        strongest = max(dim_results, key=lambda d: d.score).key if dim_results else ""

        # K-6: Maturity-Lookup über total_pct
        maturity = self._resolve_maturity(total_pct, maturity_levels)

        return AssessmentResult(
            total_score=Decimal(str(total_raw)),
            total_pct=total_pct,
            maturity_key=maturity.key if maturity else "",
            maturity_label=maturity.label if maturity else "",
            maturity_color=maturity.color if maturity else "#6B7280",
            maturity_description=maturity.description if maturity else "",
            dimensions=dim_results,
            weakest=weakest,
            strongest=strongest,
        )

    @staticmethod
    def _resolve_maturity(total_pct: int, maturity_levels: list):
        """
        Findet den passenden Reifegrad für einen Gesamt-Prozentsatz.

        Erwartet `maturity_levels` aufsteigend sortiert nach `pct_min`.
        Gibt den höchsten Reifegrad zurück, bei dem `pct_min <= total_pct`.
        """
        if not maturity_levels:
            return None
        matched = None
        for level in maturity_levels:
            if level.pct_min <= total_pct:
                matched = level
        return matched or maturity_levels[0]


# ---------------------------------------------------------------------------
# WeightedLikertScoring  (K-4: vollständig implementiert)
# ---------------------------------------------------------------------------

class WeightedLikertScoring(LikertScoring):
    """
    Likert-Skala mit gewichteten Dimensionen.

    `AssessmentDimension.weight` bestimmt den Anteil jeder Dimension
    am Gesamt-Prozentsatz. Dimensionen mit weight=2.0 gehen doppelt ein.

    Beispiel KI-Souveränität: 'KI-Governance' (weight=1.5) > 'Daten-Grundlagen' (weight=1.0)
    """

    def score(
        self,
        questions:       list,
        answers:         dict[str, Any],
        dimensions:      list,
        maturity_levels: list,
        scale_min:       int,
        scale_max:       int,
    ) -> AssessmentResult:
        # Zunächst Standard-LikertScoring für Dimensions-Ergebnisse
        base_result = super().score(
            questions, answers, dimensions, maturity_levels, scale_min, scale_max
        )

        if not base_result.dimensions:
            return base_result

        # Gewichteten Gesamt-Prozentsatz neu berechnen
        total_weight    = sum(float(d.weight) for d in base_result.dimensions)
        weighted_sum    = sum(float(d.pct) * float(d.weight) for d in base_result.dimensions)

        if total_weight > 0:
            weighted_pct = round(weighted_sum / total_weight)
        else:
            weighted_pct = base_result.total_pct

        weighted_pct = max(0, min(100, weighted_pct))
        maturity     = self._resolve_maturity(weighted_pct, maturity_levels)

        # Ergebnis mit korrigiertem total_pct zurückgeben
        # (dataclass frozen=True → neues Objekt via replace-Pattern)
        return dataclasses.replace(
            base_result,
            total_pct=weighted_pct,
            maturity_key=maturity.key if maturity else "",
            maturity_label=maturity.label if maturity else "",
            maturity_color=maturity.color if maturity else "#6B7280",
            maturity_description=maturity.description if maturity else "",
        )


# ---------------------------------------------------------------------------
# QuizScoring
# ---------------------------------------------------------------------------

class QuizScoring(ScoringStrategy):
    """
    Quiz-Scoring: Richtig/Falsch → Prozent.
    Delegiert an bestehenden scoring_service.py für Abwärtskompatibilität.

    Likert-spezifische Parameter (scale_min/scale_max) werden ignoriert.
    """

    def score(
        self,
        questions:       list,
        answers:         dict[str, Any],
        dimensions:      list,
        maturity_levels: list,
        scale_min:       int,
        scale_max:       int,
    ) -> AssessmentResult:
        correct_count   = 0
        total_count     = len(questions)

        for q in questions:
            raw  = answers.get(str(q.public_id)) or answers.get(str(q.pk))
            if raw is None:
                continue
            val  = raw.get("value", raw) if isinstance(raw, dict) else raw
            if getattr(q, "correct_answer", None) is not None and str(val) == str(q.correct_answer):
                correct_count += 1

        total_pct = round(correct_count / total_count * 100) if total_count else 0
        maturity  = LikertScoring._resolve_maturity(total_pct, maturity_levels)

        return AssessmentResult(
            total_score=Decimal(str(correct_count)),
            total_pct=total_pct,
            maturity_key=maturity.key if maturity else "",
            maturity_label=maturity.label if maturity else "",
            maturity_color=maturity.color if maturity else "#6B7280",
            maturity_description=maturity.description if maturity else "",
            dimensions=[],
            weakest="",
            strongest="",
        )


# ---------------------------------------------------------------------------
# SurveyScoring
# ---------------------------------------------------------------------------

class SurveyScoring(ScoringStrategy):
    """
    Umfrage: keine Bewertung, nur Antwort-Aggregation.
    total_pct=0, maturity immer erster Eintrag.
    """

    def score(
        self,
        questions:       list,
        answers:         dict[str, Any],
        dimensions:      list,
        maturity_levels: list,
        scale_min:       int,
        scale_max:       int,
    ) -> AssessmentResult:
        return AssessmentResult(
            total_score=Decimal("0"),
            total_pct=0,
            maturity_key="",
            maturity_label="",
            maturity_color="#6B7280",
            maturity_description="",
            dimensions=[],
            weakest="",
            strongest="",
        )


# ---------------------------------------------------------------------------
# Strategy-Registry  (M-4: als Klasse statt Modul-Level-Dict)
# ---------------------------------------------------------------------------

class ScoringStrategyRegistry:
    """
    Registry für Scoring-Strategien.

    Konsumenten (z. B. coach-hub) können eigene Strategien registrieren:

        from iil_learnfw.services.assessment_scoring import scoring_registry
        scoring_registry.register("custom_strategy", MyCustomScoring)
    """

    def __init__(self) -> None:
        self._strategies: dict[str, type[ScoringStrategy]] = {}

    def register(self, key: str, cls: type[ScoringStrategy]) -> None:
        if not issubclass(cls, ScoringStrategy):
            raise TypeError(f"{cls} muss ScoringStrategy erweitern.")
        self._strategies[key] = cls
        logger.debug("ScoringStrategy '%s' registriert: %s", key, cls.__name__)

    def get(self, key: str) -> ScoringStrategy:
        cls = self._strategies.get(key)
        if cls is None:
            available = ", ".join(self._strategies.keys())
            raise ValueError(
                f"Unbekannte Scoring-Strategie: '{key}'. "
                f"Verfügbar: {available}"
            )
        return cls()

    def available(self) -> list[str]:
        return list(self._strategies.keys())


# Singleton-Registry
scoring_registry = ScoringStrategyRegistry()
scoring_registry.register("likert",           LikertScoring)
scoring_registry.register("weighted_likert",  WeightedLikertScoring)
scoring_registry.register("quiz",             QuizScoring)
scoring_registry.register("survey",           SurveyScoring)
