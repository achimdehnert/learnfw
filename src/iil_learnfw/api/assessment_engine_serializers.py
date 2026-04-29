"""
iil_learnfw/api/serializers/assessment_engine.py

DRF-Serializer für die Assessment-Engine API.

Hinweis ADR-142: Die API-Schicht (DRF) bleibt für externe Integrationen
(SCORM, LTI, Mobile). HTMX-Views gehen direkt über AssessmentService.
"""
from __future__ import annotations

from rest_framework import serializers

from iil_learnfw.models.assessment_engine import (
    AssessmentAttempt,
    AssessmentDimension,
    AssessmentMaturityLevel,
    AssessmentQuestion,
    AssessmentType,
)


class AssessmentMaturityLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AssessmentMaturityLevel
        fields = [
            "public_id", "key", "label", "description",
            "color", "icon", "pct_min", "pct_max", "sort_order",
        ]


class AssessmentDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AssessmentDimension
        fields = ["public_id", "key", "label", "weight", "sort_order"]


class AssessmentTypeListSerializer(serializers.ModelSerializer):
    """Kompakte Darstellung für Listenansichten."""

    class Meta:
        model  = AssessmentType
        fields = [
            "public_id", "key", "title", "slug", "description",
            "scoring_strategy", "scale_min", "scale_max", "is_public",
            "certificate_enabled", "report_enabled",
        ]


class AssessmentTypeDetailSerializer(serializers.ModelSerializer):
    """Vollständige Darstellung inkl. Dimensionen und Reifegrade."""
    dimensions     = AssessmentDimensionSerializer(many=True, read_only=True)
    maturity_levels = AssessmentMaturityLevelSerializer(many=True, read_only=True)
    scale_labels   = serializers.JSONField()

    class Meta:
        model  = AssessmentType
        fields = [
            "public_id", "key", "title", "slug", "description",
            "scoring_strategy", "scale_min", "scale_max", "scale_labels",
            "is_public", "passing_score", "certificate_enabled", "report_enabled",
            "reassessment_months", "dimensions", "maturity_levels",
        ]


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    dimension_key   = serializers.CharField(source="dimension.key", read_only=True)
    dimension_label = serializers.CharField(source="dimension.label", read_only=True)

    class Meta:
        model  = AssessmentQuestion
        fields = [
            "public_id", "text", "help_text", "sort_order",
            "dimension_key", "dimension_label",
        ]


# ---------------------------------------------------------------------------
# Attempt-Serializer
# ---------------------------------------------------------------------------

class AssessmentStartSerializer(serializers.Serializer):
    """Input für POST /assessments/start/<type_slug>/"""
    # Kein Payload nötig — type_slug kommt aus URL
    # IP-Adresse wird aus request.META extrahiert, nicht aus Body (Sicherheit)
    pass


class AssessmentSubmitSerializer(serializers.Serializer):
    """
    Input für POST /assessments/<public_id>/submit/

    answers: {str(question_public_id): int_value}
    Werte werden im Service geclamppt (scale_min..scale_max).
    """
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Dict von question_public_id → Antwort-Wert (Integer).",
    )

    def validate_answers(self, value: dict) -> dict:
        # Validierung: alle Keys müssen valide UUIDs sein
        import uuid
        invalid_keys = []
        for k in value:
            try:
                uuid.UUID(str(k))
            except ValueError:
                invalid_keys.append(k)
        if invalid_keys:
            raise serializers.ValidationError(
                f"Ungültige Frage-IDs (erwartet UUIDs): {invalid_keys[:5]}"
            )
        return value


class DimensionResultSerializer(serializers.Serializer):
    key    = serializers.CharField()
    label  = serializers.CharField()
    score  = serializers.DecimalField(max_digits=6, decimal_places=2)
    pct    = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=4, decimal_places=2)


class AssessmentResultSerializer(serializers.Serializer):
    """Serialisierung des AssessmentResult-Dataclass."""
    total_score           = serializers.DecimalField(max_digits=8, decimal_places=2)
    total_pct             = serializers.IntegerField()
    maturity_key          = serializers.CharField()
    maturity_label        = serializers.CharField()
    maturity_color        = serializers.CharField()
    maturity_description  = serializers.CharField()
    dimensions            = DimensionResultSerializer(many=True)
    weakest               = serializers.CharField()
    strongest             = serializers.CharField()
    recommendations       = serializers.ListField(child=serializers.DictField())


class AssessmentAttemptResultSerializer(serializers.ModelSerializer):
    """Vollständige Attempt-Antwort nach Submit / für GET /result/"""
    maturity_level = AssessmentMaturityLevelSerializer(read_only=True)
    scores         = serializers.JSONField()
    has_report     = serializers.SerializerMethodField()

    class Meta:
        model  = AssessmentAttempt
        fields = [
            "public_id", "total_pct", "total_score",
            "maturity_level", "weakest_dimension", "strongest_dimension",
            "scores", "completed_at", "has_report",
        ]

    def get_has_report(self, obj) -> bool:
        return hasattr(obj, "report") and obj.report is not None
