"""
iil_learnfw/services/recommendation_service.py

Empfehlungs-Service für Assessment-Ergebnisse.

Korrekturen gegenüber ADR-142-PROPOSED:
  K-2  War als "Pure function" deklariert, machte aber DB-Zugriff ohne Tenant-Filter.
       Jetzt klar als Service-Methode mit obligatorischem tenant_id-Parameter.
       Threshold-Vergleich auf pct-Basis (konsistent mit K-6 / threshold_below_pct).
  NEU-K1  tenant_id ist uuid.UUID (nicht int) — konsistent mit TenantMixin
"""
from __future__ import annotations

import logging
import uuid as uuid_mod
from typing import Any

from iil_learnfw.services.assessment_scoring import DimensionResult

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service für die Ermittlung von Lern-Empfehlungen basierend auf
    Dimensions-Scoring-Ergebnissen.

    Kein "Pure function" — enthält DB-Zugriff, muss immer mit tenant_id
    aufgerufen werden.
    """

    @staticmethod
    def get_recommendations(
        *,
        assessment_type,                      # AssessmentType-Instanz
        tenant_id:         uuid_mod.UUID | None,  # K-2: obligatorisch, kein Default
        dimension_results: list[DimensionResult],
    ) -> list[dict[str, Any]]:
        """
        Gibt Empfehlungen zurück, sortiert nach Dringlichkeit (gap desc, priority asc).

        Tenant-Isolation: Nur Empfehlungen des jeweiligen Tenants.
        Threshold-Vergleich: `dimension_pct < threshold_below_pct` (0-100).
        """
        from iil_learnfw.models.assessment_engine import AssessmentRecommendation  # noqa: PLC0415

        if not dimension_results:
            return []

        # Einmaliger DB-Fetch aller Empfehlungen für diesen Assessment-Typ + Tenant
        # (besser als N Queries in einer Schleife)
        all_recs = (
            AssessmentRecommendation.objects
            .filter(
                dimension__assessment_type=assessment_type,
                tenant_id=tenant_id,              # K-2: Tenant-Isolation
                deleted_at__isnull=True,
            )
            .select_related("dimension", "course", "lesson")
            .order_by("priority")
        )

        # Index by dimension key für O(1)-Lookup
        recs_by_dim: dict[str, list] = {}
        for rec in all_recs:
            dk = rec.dimension.key
            recs_by_dim.setdefault(dk, []).append(rec)

        recommendations: list[dict[str, Any]] = []

        for dim_result in dimension_results:
            dim_recs = recs_by_dim.get(dim_result.key, [])
            for rec in dim_recs:
                # K-2/K-6: Vergleich auf pct-Basis (threshold_below_pct ist 0-100)
                if dim_result.pct < rec.threshold_below_pct:
                    gap_pct = rec.threshold_below_pct - dim_result.pct
                    recommendations.append({
                        "dimension_key":    dim_result.key,
                        "dimension_label":  dim_result.label,
                        "dimension_pct":    dim_result.pct,
                        "gap_pct":          gap_pct,
                        "title":            rec.title,
                        "description":      rec.description,
                        "priority":         rec.priority,
                        "course_id":        str(rec.course.public_id) if rec.course else None,
                        "course_title":     rec.course.title if rec.course else None,
                        "lesson_id":        str(rec.lesson.public_id) if rec.lesson else None,
                        "lesson_title":     rec.lesson.title if rec.lesson else None,
                        "external_url":     rec.external_url,
                    })

        # Sortierung: höchste Dringlichkeit (gap_pct desc) → niedrigste Prioritätsnummer
        recommendations.sort(key=lambda r: (-r["gap_pct"], r["priority"]))

        logger.debug(
            "RecommendationService: %d Empfehlungen für Tenant %s, Assessment '%s'",
            len(recommendations), tenant_id, assessment_type.key,
        )
        return recommendations

    @staticmethod
    def get_recommendations_for_report(
        *,
        attempt,    # AssessmentAttempt — bereits completed
        tenant_id: uuid_mod.UUID | None,
        max_count: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Convenience-Wrapper: Lädt Dimensions aus dem persistierten `attempt.scores`
        und ruft get_recommendations auf.

        Verwendung: PDF-Report-Generator, um Empfehlungen bei Report-Generierung
        neu zu berechnen (falls Recommendations seit Submit aktualisiert wurden).
        """
        from decimal import Decimal

        from iil_learnfw.services.assessment_scoring import DimensionResult  # noqa: PLC0415

        dim_results = [
            DimensionResult(
                key=dk,
                label=data.get("label", dk),
                score=Decimal(str(data.get("score", "0"))),
                pct=int(data.get("pct", 0)),
                weight=Decimal(str(data.get("weight", "1.0"))),
            )
            for dk, data in attempt.scores.items()
        ]

        recs = RecommendationService.get_recommendations(
            assessment_type=attempt.assessment_type,
            tenant_id=tenant_id,
            dimension_results=dim_results,
        )
        return recs[:max_count]
