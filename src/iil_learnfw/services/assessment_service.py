"""
iil_learnfw/services/assessment_service.py

Assessment-Orchestrierungsschicht — einziger erlaubter Einstiegspunkt für
Business-Logik rund um Assessments.

Platform-Standard: Business-Logik ausschließlich im Service-Layer.
Views, Tasks und Management-Commands rufen NUR diesen Service auf.

Korrekturen gegenüber ADR-142-PROPOSED:
  K-2  Tenant-Isolation bei allen Queries
  K-3  Antworten als Snapshot gespeichert (public_id, text, version)
  K-6  Maturity-Lookup über total_pct
  H-7  Überlappungsfreiheits-Prüfung für Maturity-Ranges im Service-Layer

Meta-Review-Korrekturen:
  NEU-K1  tenant_id ist uuid.UUID (nicht int) — konsistent mit TenantMixin
  NEU-K3  iil_learnfw.conf.get_setting existiert nicht → django.conf.settings
  NEU-H1  import dataclasses an Dateianfang
  NEU-H4  Lücken-Prüfung in Maturity-Ranges
  NEU-M1  select_related() mit expliziten Feldern
"""
from __future__ import annotations

import dataclasses
import hashlib
import logging
import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Any

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import transaction
from django.utils import timezone as django_timezone

from iil_learnfw.models.assessment_engine import (
    AssessmentAttempt,
    AssessmentMaturityLevel,
    AssessmentQuestion,
    AssessmentReport,
    AssessmentType,
)
from iil_learnfw.services.assessment_scoring import (
    AssessmentResult,
    scoring_registry,
)
from iil_learnfw.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class AssessmentValidationError(ValueError):
    """Fachliche Validierungsfehler (Eingabe, Konfiguration)."""
    pass


class AssessmentService:
    """
    Haupt-Service für Assessment-Durchführung.

    Alle public Methoden sind synchron und transaktional.
    Celery-Tasks für PDF-Generierung werden aus diesem Service getriggert.
    """

    # ------------------------------------------------------------------
    # Attempt starten
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def start_attempt(
        *,
        assessment_type_slug: str,
        tenant_id:            uuid_mod.UUID | None,
        user=None,              # Optional: eingeloggter User
        ip_address:           str = "",
    ) -> AssessmentAttempt:
        """
        Startet einen neuen Attempt für den gegebenen Assessment-Typ.

        Erstellt einen neuen AssessmentAttempt-Datensatz.
        Gibt öffentliche Fehler via AssessmentValidationError zurück.
        """
        try:
            assessment_type = AssessmentType.objects.select_related("course").get(
                slug=assessment_type_slug,
                tenant_id=tenant_id,        # K-2: Tenant-Isolation
                deleted_at__isnull=True,
            )
        except AssessmentType.DoesNotExist:
            raise AssessmentValidationError(
                f"Assessment-Typ '{assessment_type_slug}' nicht gefunden."
            )

        if not assessment_type.is_active:
            raise AssessmentValidationError(
                f"Assessment-Typ '{assessment_type_slug}' ist nicht aktiv."
            )

        if not assessment_type.is_public and user is None:
            raise AssessmentValidationError(
                "Dieses Assessment erfordert einen eingeloggten Benutzer."
            )

        ip_hash = AssessmentService._hash_ip(ip_address) if ip_address else ""

        attempt = AssessmentAttempt.objects.create(
            assessment_type=assessment_type,
            tenant_id=tenant_id,
            user=user,
            ip_hash=ip_hash,
            answers={},
            scores={},
        )
        logger.info(
            "AssessmentAttempt gestartet: %s (type=%s, tenant=%s)",
            attempt.public_id, assessment_type_slug, tenant_id,
        )
        return attempt

    # ------------------------------------------------------------------
    # Attempt einreichen
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def submit_attempt(
        *,
        attempt_public_id: str,
        tenant_id:         uuid_mod.UUID | None,
        raw_answers:       dict[str, Any],  # {str(question_pk_or_public_id): value}
    ) -> AssessmentResult:
        """
        Berechnet Scoring, persistiert Ergebnis, erstellt Report.

        K-3: Antworten werden als Snapshot gespeichert (public_id, text, version).
        K-6: Maturity-Lookup über total_pct.
        """
        try:
            attempt = AssessmentAttempt.objects.select_related(
                "assessment_type",
            ).get(
                public_id=attempt_public_id,
                tenant_id=tenant_id,        # K-2: Tenant-Isolation
                deleted_at__isnull=True,
            )
        except AssessmentAttempt.DoesNotExist:
            raise AssessmentValidationError(
                f"Attempt '{attempt_public_id}' nicht gefunden."
            )

        if attempt.completed_at is not None:
            raise AssessmentValidationError("Dieser Attempt wurde bereits eingereicht.")

        at = attempt.assessment_type

        # Fragen laden — mit Tenant-Filter (K-2)
        questions = list(
            AssessmentQuestion.objects.select_related("dimension")
            .filter(
                dimension__assessment_type=at,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
                is_active=True,
            )
            .order_by("dimension__sort_order", "sort_order")
        )

        if not questions:
            raise AssessmentValidationError(
                f"Assessment-Typ '{at.key}' hat keine aktiven Fragen."
            )

        # K-3: Snapshot-Format erstellen
        # Key = str(question.public_id), Value = {text, value, question_version}
        answers_snapshot = AssessmentService._build_snapshot(questions, raw_answers)

        # Maturity-Levels laden — mit Tenant-Filter (K-2)
        maturity_levels = list(
            AssessmentMaturityLevel.objects.filter(
                assessment_type=at,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
            ).order_by("pct_min")  # K-6: aufsteigend nach pct_min
        )

        dimensions = list(
            at.dimensions.filter(
                tenant_id=tenant_id,
                deleted_at__isnull=True,
                is_active=True,
            ).order_by("sort_order")
        )

        # Scoring
        strategy = scoring_registry.get(at.scoring_strategy)
        result   = strategy.score(
            questions=questions,
            answers=answers_snapshot,
            dimensions=dimensions,
            maturity_levels=maturity_levels,
            scale_min=at.scale_min,
            scale_max=at.scale_max,
        )

        # Empfehlungen hinzufügen
        recommendations = RecommendationService.get_recommendations(
            assessment_type=at,
            tenant_id=tenant_id,
            dimension_results=result.dimensions,
        )
        result = dataclasses.replace(result, recommendations=recommendations)

        # Maturity-FK auflösen
        maturity_obj = None
        if result.maturity_key:
            maturity_obj = AssessmentMaturityLevel.objects.filter(
                assessment_type=at,
                key=result.maturity_key,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
            ).first()

        # Attempt persistieren
        scores_serializable = {
            d.key: {
                "score": str(d.score),
                "pct":   d.pct,
                "weight": str(d.weight),
                "label": d.label,
            }
            for d in result.dimensions
        }
        retention_expires = AssessmentService._calc_retention(at.retention_days)

        attempt.answers               = answers_snapshot
        attempt.scores                = scores_serializable
        attempt.total_score           = result.total_score
        attempt.total_pct             = result.total_pct
        attempt.maturity_level        = maturity_obj
        attempt.weakest_dimension     = result.weakest
        attempt.strongest_dimension   = result.strongest
        attempt.completed_at          = django_timezone.now()
        attempt.retention_expires_at  = retention_expires
        attempt.save(update_fields=[
            "answers", "scores", "total_score", "total_pct",
            "maturity_level", "weakest_dimension", "strongest_dimension",
            "completed_at", "retention_expires_at", "updated_at",
        ])

        # Report erstellen
        if at.report_enabled:
            AssessmentReport.objects.update_or_create(
                attempt=attempt,
                defaults={
                    "tenant_id":       tenant_id,
                    "recommendations": recommendations,
                },
            )

        logger.info(
            "AssessmentAttempt eingereicht: %s — %d%% (%s)",
            attempt.public_id, result.total_pct, result.maturity_key,
        )
        return result

    # ------------------------------------------------------------------
    # Ergebnis abrufen
    # ------------------------------------------------------------------

    @staticmethod
    def get_result(
        *,
        attempt_public_id: str,
        tenant_id:         uuid_mod.UUID | None,
    ) -> dict[str, Any]:
        """
        Gibt das persistierte Ergebnis eines abgeschlossenen Attempts zurück.
        Tenant-Isolation obligatorisch.
        """
        try:
            attempt = AssessmentAttempt.objects.select_related(
                "assessment_type",
                "maturity_level",
                "report",
            ).get(
                public_id=attempt_public_id,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
            )
        except AssessmentAttempt.DoesNotExist:
            raise AssessmentValidationError(
                f"Attempt '{attempt_public_id}' nicht gefunden."
            )

        if attempt.completed_at is None:
            raise AssessmentValidationError("Dieser Attempt ist noch nicht abgeschlossen.")

        return {
            "attempt_public_id":  str(attempt.public_id),
            "assessment_type":    attempt.assessment_type.key,
            "total_pct":          attempt.total_pct,
            "total_score":        str(attempt.total_score),
            "maturity_key":       attempt.maturity_level.key if attempt.maturity_level else "",
            "maturity_label":     attempt.maturity_level.label if attempt.maturity_level else "",
            "maturity_color":     attempt.maturity_level.color if attempt.maturity_level else "#6B7280",
            "weakest":            attempt.weakest_dimension,
            "strongest":          attempt.strongest_dimension,
            "scores":             attempt.scores,
            "completed_at":       attempt.completed_at.isoformat(),
            "has_report":         hasattr(attempt, "report") and attempt.report is not None,
            "has_certificate":    (
                hasattr(attempt, "report")
                and attempt.report is not None
                and attempt.report.certificate_id is not None
            ),
        }

    # ------------------------------------------------------------------
    # Soft-Delete / DSGVO
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def anonymize_attempt(
        *,
        attempt_public_id: str,
        tenant_id:         uuid_mod.UUID | None,
    ) -> None:
        """
        DSGVO Art. 17: Anonymisiert einen Attempt.
        Löscht PII (ip_hash, user_fk), behält aggregierte Scores für Statistik.
        """
        rows = AssessmentAttempt.objects.filter(
            public_id=attempt_public_id,
            tenant_id=tenant_id,
        ).update(
            user_id=None,
            ip_hash="",
            answers={},
            deleted_at=django_timezone.now(),
        )
        if rows == 0:
            logger.warning(
                "anonymize_attempt: Attempt %s nicht gefunden (tenant=%s)",
                attempt_public_id, tenant_id,
            )

    # ------------------------------------------------------------------
    # Maturity-Overlap-Prüfung (H-7)
    # ------------------------------------------------------------------

    @staticmethod
    def validate_maturity_ranges(
        *,
        assessment_type_id: int,
        tenant_id:          uuid_mod.UUID | None,
    ) -> list[str]:
        """
        Prüft ob Maturity-Level-Ranges überlappungsfrei sind.
        Gibt Liste von Fehlermeldungen zurück (leer = OK).

        Aufruf:
        - Im Management-Command assessment_seed nach dem Laden
        - Im Admin-Save-Hook von AssessmentMaturityLevel
        """
        levels = list(
            AssessmentMaturityLevel.objects.filter(
                assessment_type_id=assessment_type_id,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
            ).order_by("pct_min")
        )

        errors = []
        for i, current in enumerate(levels):
            for other in levels[i + 1:]:
                if current.pct_min <= other.pct_min <= current.pct_max:
                    errors.append(
                        f"Überlappung: '{current.key}' ({current.pct_min}-{current.pct_max}%) "
                        f"und '{other.key}' ({other.pct_min}-{other.pct_max}%)"
                    )

        # NEU-H4: Lücken-Prüfung (fehlende Prozentbereiche)
        if levels and not errors:
            sorted_levels = sorted(levels, key=lambda l: l.pct_min)
            if sorted_levels[0].pct_min > 0:
                errors.append(
                    f"Lücke: 0-{sorted_levels[0].pct_min - 1}% ist keinem Reifegrad zugeordnet."
                )
            for i in range(len(sorted_levels) - 1):
                gap_start = sorted_levels[i].pct_max + 1
                gap_end = sorted_levels[i + 1].pct_min - 1
                if gap_start <= gap_end:
                    errors.append(
                        f"Lücke: {gap_start}-{gap_end}% ist keinem Reifegrad zugeordnet."
                    )
            if sorted_levels[-1].pct_max < 100:
                errors.append(
                    f"Lücke: {sorted_levels[-1].pct_max + 1}-100% ist keinem Reifegrad zugeordnet."
                )
        return errors

    # ------------------------------------------------------------------
    # Private Hilfsmethoden
    # ------------------------------------------------------------------

    @staticmethod
    def _build_snapshot(
        questions:   list,
        raw_answers: dict[str, Any],
    ) -> dict[str, dict]:
        """
        K-3: Erstellt Antwort-Snapshot mit Question-public_id als Key.

        Akzeptiert sowohl public_id-Keys als auch PK-Keys (Migration-Kompatibilität).
        """
        snapshot: dict[str, dict] = {}
        for q in questions:
            # Suche Antwort: zuerst public_id, dann PK
            raw = raw_answers.get(str(q.public_id)) or raw_answers.get(str(q.pk))
            if raw is None:
                continue
            val = raw.get("value", raw) if isinstance(raw, dict) else raw
            snapshot[str(q.public_id)] = {
                "question_text":    q.text,
                "value":            val,
                "question_version": q.version,
            }
        return snapshot

    @staticmethod
    def _hash_ip(ip_address: str) -> str:
        """
        DSGVO-konformes IP-Hashing mit Salt aus Settings.
        Platform-Standard: ASSESSMENT_IP_HASH_SALT via IIL_LEARNFW-Settings.
        """
        learnfw_settings = getattr(settings, "IIL_LEARNFW", {})
        salt = learnfw_settings.get("ASSESSMENT_IP_HASH_SALT", "")
        if not salt:
            logger.warning(
                "ASSESSMENT_IP_HASH_SALT nicht konfiguriert — IP-Hashing ohne Salt unsicher."
            )
        salted = f"{salt}:{ip_address}"
        return hashlib.sha256(salted.encode()).hexdigest()

    @staticmethod
    def _calc_retention(retention_days: int) -> datetime:
        """Berechnet den Ablaufzeitpunkt der Aufbewahrungsfrist."""
        from datetime import timedelta
        return django_timezone.now() + timedelta(days=retention_days)
