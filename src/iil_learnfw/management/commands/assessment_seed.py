"""
iil_learnfw/management/commands/assessment_seed.py

Management-Command: Seed-Daten für Assessment-Typen importieren.

Korrekturen gegenüber ADR-142-PROPOSED:
  H-5  --tenant-id als Required-Parameter (Multi-Tenant sicher)
       Idempotenz: update_or_create statt delete+create
       Vollständige Transaktion
       Maturity-Overlap-Validierung nach Seed
       set -euo pipefail Äquivalent: exception_on_error=True
  NEU-K1  tenant_id ist UUID-String (nicht int)
  NEU-R1  Question.key für stabile Seed-Identifikation
"""
from __future__ import annotations

import importlib
import logging
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

logger = logging.getLogger(__name__)

# Verfügbare Seeds: key → Modul-Pfad
AVAILABLE_SEEDS: dict[str, str] = {
    "ki_souveraenitaet": "iil_learnfw.seeds.ki_souveraenitaet",
    "dsgvo_readiness":   "iil_learnfw.seeds.dsgvo_readiness",
    "nis2_readiness":    "iil_learnfw.seeds.nis2_readiness",
    "it_security":       "iil_learnfw.seeds.it_security",
}


class Command(BaseCommand):
    help = "Importiert Assessment-Seed-Daten (idempotent, multi-tenant-sicher)."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--type",
            dest="seed_type",
            choices=list(AVAILABLE_SEEDS.keys()),
            help="Einzelnen Assessment-Typ importieren.",
        )
        group.add_argument(
            "--all",
            action="store_true",
            dest="all_seeds",
            help="Alle verfügbaren Assessment-Typen importieren.",
        )
        parser.add_argument(
            "--tenant-id",
            type=str,
            required=True,          # H-5: immer required in Multi-Tenant
            dest="tenant_id",
            help="Tenant-UUID für den Seed-Import (Platform-Standard: immer angeben).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            default=False,
            help=(
                "Soft-Löscht existierende Datensätze vor dem Import. "
                "Achtung: Betrifft NUR den angegebenen Tenant (--tenant-id)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            dest="dry_run",
            help="Simuliert den Import ohne DB-Änderungen.",
        )

    def handle(self, *args, **options):
        tenant_id  = options["tenant_id"]
        reset      = options["reset"]
        dry_run    = options["dry_run"]

        if options["all_seeds"]:
            seed_keys = list(AVAILABLE_SEEDS.keys())
        else:
            seed_keys = [options["seed_type"]]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN: Keine DB-Änderungen."))

        errors = []
        for key in seed_keys:
            try:
                self._import_seed(
                    seed_key=key,
                    tenant_id=tenant_id,
                    reset=reset,
                    dry_run=dry_run,
                )
            except Exception as exc:
                errors.append(f"{key}: {exc}")
                self.stderr.write(self.style.ERROR(f"FEHLER bei '{key}': {exc}"))

        if errors:
            raise CommandError(
                f"{len(errors)} Seed(s) fehlgeschlagen:\n" + "\n".join(errors)
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seed-Import abgeschlossen: {len(seed_keys)} Typ(en) für Tenant {tenant_id}."
        ))

    @transaction.atomic
    def _import_seed(
        self,
        *,
        seed_key:  str,
        tenant_id: int,
        reset:     bool,
        dry_run:   bool,
    ) -> None:
        from django.utils import timezone  # noqa: PLC0415

        from iil_learnfw.models.assessment_engine import (  # noqa: PLC0415
            AssessmentDimension,
            AssessmentMaturityLevel,
            AssessmentQuestion,
            AssessmentRecommendation,
            AssessmentType,
        )
        from iil_learnfw.services.assessment_service import AssessmentService  # noqa: PLC0415

        module_path = AVAILABLE_SEEDS[seed_key]
        module      = importlib.import_module(module_path)
        seed_data: dict[str, Any] = module.SEED

        self.stdout.write(f"  → Importiere '{seed_key}' für Tenant {tenant_id} ...")

        if dry_run:
            self.stdout.write(f"     [DRY-RUN] Würde Seed '{seed_key}' importieren.")
            return

        # H-5: Reset nur für diesen Tenant
        if reset:
            now = timezone.now()
            deleted_types = AssessmentType.objects.filter(
                key=seed_key, tenant_id=tenant_id
            ).update(deleted_at=now)
            self.stdout.write(
                self.style.WARNING(f"     Reset: {deleted_types} AssessmentType(s) soft-gelöscht.")
            )

        # AssessmentType (idempotent)
        at, created = AssessmentType.objects.update_or_create(
            key=seed_key,
            tenant_id=tenant_id,
            defaults={
                "title":               seed_data["title"],
                "slug":                seed_data.get("slug", seed_key.replace("_", "-")),
                "description":         seed_data.get("description", ""),
                "scoring_strategy":    seed_data.get("scoring_strategy", "likert"),
                "scale_min":           seed_data.get("scale_min", 1),
                "scale_max":           seed_data.get("scale_max", 4),
                "scale_labels":        seed_data.get("scale_labels", []),
                "is_public":           seed_data.get("is_public", True),
                "is_active":           seed_data.get("is_active", True),
                "passing_score":       seed_data.get("passing_score", 0),
                "certificate_enabled": seed_data.get("certificate_enabled", False),
                "report_enabled":      seed_data.get("report_enabled", True),
                "reassessment_months": seed_data.get("reassessment_months", 6),
                "retention_days":      seed_data.get("retention_days", 730),
                "deleted_at":          None,  # Reaktivieren falls soft-deleted
            },
        )
        action = "erstellt" if created else "aktualisiert"
        self.stdout.write(f"     AssessmentType {action}: {at.key}")

        # Dimensionen
        dim_objects: dict[str, AssessmentDimension] = {}
        for dim_data in seed_data.get("dimensions", []):
            dim, _ = AssessmentDimension.objects.update_or_create(
                assessment_type=at,
                key=dim_data["key"],
                tenant_id=tenant_id,
                defaults={
                    "label":      dim_data["label"],
                    "weight":     dim_data.get("weight", "1.00"),
                    "sort_order": dim_data.get("sort_order", 0),
                    "is_active":  dim_data.get("is_active", True),
                    "deleted_at": None,
                },
            )
            dim_objects[dim.key] = dim

            # Fragen
            for q_data in dim_data.get("questions", []):
                # NEU-R1: Stabiler key für idempotentes Seeding
                q_key = q_data.get("key", "")
                if q_key:
                    lookup = {"dimension": dim, "key": q_key, "tenant_id": tenant_id}
                else:
                    lookup = {"dimension": dim, "text": q_data["text"], "tenant_id": tenant_id}
                AssessmentQuestion.objects.update_or_create(
                    **lookup,
                    defaults={
                        "key":        q_key,
                        "text":       q_data["text"],
                        "help_text":  q_data.get("help_text", ""),
                        "sort_order": q_data.get("sort_order", 0),
                        "is_active":  q_data.get("is_active", True),
                        "deleted_at": None,
                    },
                )

        # Reifegrade
        for ml_data in seed_data.get("maturity_levels", []):
            AssessmentMaturityLevel.objects.update_or_create(
                assessment_type=at,
                key=ml_data["key"],
                tenant_id=tenant_id,
                defaults={
                    "label":       ml_data["label"],
                    "description": ml_data.get("description", ""),
                    "color":       ml_data["color"],
                    "icon":        ml_data.get("icon", ""),
                    "pct_min":     ml_data["pct_min"],   # K-6: pct, nicht score
                    "pct_max":     ml_data["pct_max"],
                    "sort_order":  ml_data.get("sort_order", 0),
                    "deleted_at":  None,
                },
            )

        # Empfehlungen (falls in Seed-Daten)
        for rec_data in seed_data.get("recommendations", []):
            dim = dim_objects.get(rec_data["dimension_key"])
            if not dim:
                logger.warning(
                    "Seed '%s': Dimension '%s' für Empfehlung '%s' nicht gefunden.",
                    seed_key, rec_data["dimension_key"], rec_data.get("title", "?"),
                )
                continue
            AssessmentRecommendation.objects.update_or_create(
                dimension=dim,
                title=rec_data["title"],
                tenant_id=tenant_id,
                defaults={
                    "description":        rec_data.get("description", ""),
                    "threshold_below_pct": rec_data.get("threshold_below_pct", 50),
                    "priority":           rec_data.get("priority", 0),
                    "external_url":       rec_data.get("external_url", ""),
                    "deleted_at":         None,
                },
            )

        # H-7: Überlappungs-Validierung nach dem Seed
        overlap_errors = AssessmentService.validate_maturity_ranges(
            assessment_type_id=at.pk,
            tenant_id=tenant_id,
        )
        if overlap_errors:
            # Rollback durch @transaction.atomic
            raise CommandError(
                f"Maturity-Level-Überlappungen in '{seed_key}':\n"
                + "\n".join(f"  • {e}" for e in overlap_errors)
            )

        self.stdout.write(self.style.SUCCESS(
            f"     ✓ '{seed_key}': "
            f"{len(dim_objects)} Dimensionen, "
            f"{len(seed_data.get('maturity_levels', []))} Reifegrade"
        ))
