"""
tests/test_assessment_engine.py

Test-Suite für die Assessment-Engine.

Abdeckung:
  - Alle BLOCKER-Korrekturen (B-1 bis B-4) als Regression-Tests
  - Alle KRITISCH-Korrekturen (K-1 bis K-6) als Regression-Tests
  - Service-Layer: start, submit, result
  - Scoring-Strategien
  - Tenant-Isolation
  - Seed-Idempotenz

Anforderung ADR-141 (PostgreSQL Testing): Tests laufen gegen echte PG-DB,
kein SQLite. Marker @pytest.mark.django_db(transaction=True) für Transaktions-Tests.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from django.test import TestCase

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tenant_id():
    return uuid.UUID("00000000-0000-0000-0000-000000000042")


@pytest.fixture
def other_tenant_id():
    return uuid.UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture
def assessment_type(db, tenant_id):
    """Erstellt einen einfachen Likert-4-Punkte AssessmentType."""
    from iil_learnfw.models.assessment_engine import AssessmentType
    return AssessmentType.objects.create(
        key="test_ki",
        title="Test KI-Souveränität",
        slug="test-ki",
        tenant_id=tenant_id,
        scoring_strategy="likert",
        scale_min=1,
        scale_max=4,
        is_public=True,
        is_active=True,
    )


@pytest.fixture
def assessment_type_5pt(db, tenant_id):
    """5-Punkte Skala für K-1 Regression-Tests."""
    from iil_learnfw.models.assessment_engine import AssessmentType
    return AssessmentType.objects.create(
        key="test_nis2",
        title="Test NIS2",
        slug="test-nis2",
        tenant_id=tenant_id,
        scoring_strategy="likert",
        scale_min=1,
        scale_max=5,
        is_public=True,
        is_active=True,
    )


@pytest.fixture
def dimensions(db, assessment_type, tenant_id):
    from iil_learnfw.models.assessment_engine import AssessmentDimension
    dims = []
    for i, (key, label, weight) in enumerate([
        ("governance",    "KI-Governance",    Decimal("1.5")),
        ("datenkompetenz","Datenkompetenz",    Decimal("1.0")),
        ("ethik",         "KI-Ethik",         Decimal("1.0")),
    ]):
        dims.append(AssessmentDimension.objects.create(
            assessment_type=assessment_type,
            tenant_id=tenant_id,
            key=key,
            label=label,
            weight=weight,
            sort_order=i,
        ))
    return dims


@pytest.fixture
def questions(db, dimensions, tenant_id):
    from iil_learnfw.models.assessment_engine import AssessmentQuestion
    qs = []
    for dim in dimensions:
        for j in range(3):
            qs.append(AssessmentQuestion.objects.create(
                dimension=dim,
                tenant_id=tenant_id,
                text=f"Frage {j+1} in {dim.key}",
                sort_order=j,
            ))
    return qs


@pytest.fixture
def maturity_levels(db, assessment_type, tenant_id):
    from iil_learnfw.models.assessment_engine import AssessmentMaturityLevel
    levels_data = [
        ("starter",       "Starter",         0,  24,  "#DC2626"),
        ("entwicklung",   "In Entwicklung",  25, 49,  "#EA580C"),
        ("fortgeschritt", "Fortgeschritten", 50, 74,  "#CA8A04"),
        ("reif",          "KI-reif",         75, 100, "#16A34A"),
    ]
    levels = []
    for i, (key, label, pct_min, pct_max, color) in enumerate(levels_data):
        levels.append(AssessmentMaturityLevel.objects.create(
            assessment_type=assessment_type,
            tenant_id=tenant_id,
            key=key,
            label=label,
            description=f"Beschreibung {label}",
            pct_min=pct_min,
            pct_max=pct_max,
            color=color,
            sort_order=i,
        ))
    return levels


# ---------------------------------------------------------------------------
# B-1: BigAutoField PK
# ---------------------------------------------------------------------------

class TestPlatformStandardsBigAutoField:
    """B-1 Regression: Alle Modelle haben BigAutoField PK."""

    @pytest.mark.django_db
    def test_assessment_type_pk_is_bigautofield(self, assessment_type):
        from django.db import models
        field = type(assessment_type)._meta.get_field("id")
        assert isinstance(field, models.BigAutoField), \
            f"id sollte BigAutoField sein, ist aber {type(field).__name__}"

    @pytest.mark.django_db
    def test_all_models_have_big_auto_pk(self):
        from django.db import models
        from iil_learnfw.models.assessment_engine import (
            AssessmentAttempt,
            AssessmentDimension,
            AssessmentMaturityLevel,
            AssessmentQuestion,
            AssessmentRecommendation,
            AssessmentReport,
            AssessmentType,
        )
        for model_cls in [
            AssessmentType, AssessmentDimension, AssessmentQuestion,
            AssessmentMaturityLevel, AssessmentRecommendation,
            AssessmentAttempt, AssessmentReport,
        ]:
            pk_field = model_cls._meta.get_field("id")
            assert isinstance(pk_field, models.BigAutoField), \
                f"{model_cls.__name__}.id ist kein BigAutoField (ist: {type(pk_field).__name__})"


# ---------------------------------------------------------------------------
# B-2: public_id auf allen Modellen
# ---------------------------------------------------------------------------

class TestPlatformStandardsPublicId:
    """B-2 Regression: Alle User-Data-Modelle haben public_id UUIDField."""

    @pytest.mark.django_db
    def test_all_models_have_public_id(self):
        from django.db import models
        from iil_learnfw.models.assessment_engine import (
            AssessmentAttempt,
            AssessmentDimension,
            AssessmentMaturityLevel,
            AssessmentQuestion,
            AssessmentRecommendation,
            AssessmentReport,
            AssessmentType,
        )
        for model_cls in [
            AssessmentType, AssessmentDimension, AssessmentQuestion,
            AssessmentMaturityLevel, AssessmentRecommendation,
            AssessmentAttempt, AssessmentReport,
        ]:
            field_names = [f.name for f in model_cls._meta.get_fields()]
            assert "public_id" in field_names, \
                f"{model_cls.__name__} hat kein public_id-Feld"
            pk_field = model_cls._meta.get_field("public_id")
            assert isinstance(pk_field, models.UUIDField), \
                f"{model_cls.__name__}.public_id ist kein UUIDField"


# ---------------------------------------------------------------------------
# B-3: UniqueConstraint (nicht unique_together)
# ---------------------------------------------------------------------------

class TestPlatformStandardsUniqueConstraint:
    """B-3 Regression: Kein unique_together auf Modellen."""

    def test_no_unique_together_on_dimension(self):
        from iil_learnfw.models.assessment_engine import AssessmentDimension
        meta = AssessmentDimension._meta
        assert not meta.unique_together, \
            "AssessmentDimension sollte kein unique_together haben (B-3: UniqueConstraint verwenden)"

    def test_dimension_has_unique_constraint(self):
        from iil_learnfw.models.assessment_engine import AssessmentDimension
        constraint_names = [c.name for c in AssessmentDimension._meta.constraints]
        assert any("dimension" in n and "key" in n for n in constraint_names), \
            f"AssessmentDimension hat keinen UniqueConstraint für (assessment_type, key). Gefunden: {constraint_names}"


# ---------------------------------------------------------------------------
# B-4: Soft-Delete (deleted_at) auf allen Modellen
# ---------------------------------------------------------------------------

class TestPlatformStandardsSoftDelete:
    """B-4 Regression: Soft-Delete auf allen User-Data-Modellen."""

    @pytest.mark.django_db
    def test_soft_delete_assessment_type(self, assessment_type):
        from django.utils import timezone
        assessment_type.deleted_at = timezone.now()
        assessment_type.save(update_fields=["deleted_at"])

        from iil_learnfw.models.assessment_engine import AssessmentType
        # Standard-Manager soll soft-gelöschte nicht liefern
        assert not AssessmentType.objects.filter(pk=assessment_type.pk).exists()
        # all_objects soll sie liefern
        assert AssessmentType.all_objects.filter(pk=assessment_type.pk).exists()

    @pytest.mark.django_db
    def test_all_models_have_deleted_at(self):
        from iil_learnfw.models.assessment_engine import (
            AssessmentAttempt, AssessmentDimension, AssessmentMaturityLevel,
            AssessmentQuestion, AssessmentRecommendation, AssessmentReport, AssessmentType,
        )
        for model_cls in [
            AssessmentType, AssessmentDimension, AssessmentQuestion,
            AssessmentMaturityLevel, AssessmentRecommendation,
            AssessmentAttempt, AssessmentReport,
        ]:
            field_names = [f.name for f in model_cls._meta.get_fields()]
            assert "deleted_at" in field_names, \
                f"{model_cls.__name__} hat kein deleted_at-Feld (B-4)"


# ---------------------------------------------------------------------------
# K-1: scale_min/scale_max werden verwendet (kein hardcodiertes 4)
# ---------------------------------------------------------------------------

class TestLikertScoringScaleRespected:
    """K-1 Regression: LikertScoring beachtet assessment_type.scale_min/scale_max."""

    def _make_mock_question(self, dim_key="dim1", pk=1, public_id=None):
        from unittest.mock import MagicMock
        q = MagicMock()
        q.pk = pk
        q.public_id = public_id or uuid.uuid4()
        q.dimension.key = dim_key
        q.dimension.label = "Test Dimension"
        q.dimension.weight = Decimal("1.0")
        return q

    def _make_mock_maturity(self, key, pct_min, pct_max):
        from unittest.mock import MagicMock
        m = MagicMock()
        m.key = key
        m.label = key.capitalize()
        m.color = "#123456"
        m.description = ""
        m.pct_min = pct_min
        m.pct_max = pct_max
        return m

    def test_5pt_scale_top_answer_gives_100pct(self):
        """Auf 5-Punkt-Skala muss Antwort=5 → 100% ergeben."""
        from iil_learnfw.services.assessment_scoring import LikertScoring
        q = self._make_mock_question()
        answers = {str(q.public_id): 5}
        maturity = [self._make_mock_maturity("top", 0, 100)]

        result = LikertScoring().score(
            questions=[q], answers=answers, dimensions=[],
            maturity_levels=maturity, scale_min=1, scale_max=5
        )
        assert result.total_pct == 100, \
            f"5-Punkt-Skala, Antwort=5 sollte 100% geben, bekam {result.total_pct}%"

    def test_4pt_scale_top_answer_gives_100pct(self):
        """Auf 4-Punkt-Skala muss Antwort=4 → 100% ergeben."""
        from iil_learnfw.services.assessment_scoring import LikertScoring
        q = self._make_mock_question()
        answers = {str(q.public_id): 4}
        maturity = [self._make_mock_maturity("top", 0, 100)]

        result = LikertScoring().score(
            questions=[q], answers=answers, dimensions=[],
            maturity_levels=maturity, scale_min=1, scale_max=4
        )
        assert result.total_pct == 100, \
            f"4-Punkt-Skala, Antwort=4 sollte 100% geben, bekam {result.total_pct}%"

    def test_4pt_scale_min_answer_gives_0pct(self):
        """Auf 4-Punkt-Skala muss Antwort=1 → 0% ergeben."""
        from iil_learnfw.services.assessment_scoring import LikertScoring
        q = self._make_mock_question()
        answers = {str(q.public_id): 1}
        maturity = [self._make_mock_maturity("bottom", 0, 100)]

        result = LikertScoring().score(
            questions=[q], answers=answers, dimensions=[],
            maturity_levels=maturity, scale_min=1, scale_max=4
        )
        assert result.total_pct == 0, \
            f"4-Punkt-Skala, Antwort=1 sollte 0% geben, bekam {result.total_pct}%"

    def test_value_clamped_to_scale(self):
        """Werte außerhalb der Skala werden geclamppt."""
        from iil_learnfw.services.assessment_scoring import LikertScoring
        q = self._make_mock_question()
        answers = {str(q.public_id): 99}  # Weit außerhalb scale_max=4
        maturity = [self._make_mock_maturity("top", 0, 100)]

        result = LikertScoring().score(
            questions=[q], answers=answers, dimensions=[],
            maturity_levels=maturity, scale_min=1, scale_max=4
        )
        assert result.total_pct == 100  # Geclamppt auf 4 → 100%


# ---------------------------------------------------------------------------
# K-3: Antworten als Snapshot (public_id-basiert)
# ---------------------------------------------------------------------------

class TestAnswerSnapshot:
    """K-3 Regression: Submit speichert Snapshot mit question.public_id als Key."""

    @pytest.mark.django_db
    def test_submit_stores_snapshot_format(
        self, assessment_type, dimensions, questions, maturity_levels, tenant_id
    ):
        from iil_learnfw.services.assessment_service import AssessmentService

        attempt = AssessmentService.start_attempt(
            assessment_type_slug=assessment_type.slug,
            tenant_id=tenant_id,
        )

        raw_answers = {str(q.public_id): i % 4 + 1 for i, q in enumerate(questions)}
        AssessmentService.submit_attempt(
            attempt_public_id=str(attempt.public_id),
            tenant_id=tenant_id,
            raw_answers=raw_answers,
        )

        attempt.refresh_from_db()
        # Alle Keys müssen UUIDs sein (public_id-Format)
        for key in attempt.answers.keys():
            try:
                uuid.UUID(key)
            except ValueError:
                pytest.fail(f"Antwort-Key '{key}' ist keine UUID — erwartet question.public_id")

        # Snapshot-Wert muss question_text enthalten
        first_key = list(attempt.answers.keys())[0]
        assert "question_text" in attempt.answers[first_key], \
            "Snapshot sollte question_text enthalten"
        assert "question_version" in attempt.answers[first_key], \
            "Snapshot sollte question_version enthalten"


# ---------------------------------------------------------------------------
# K-2: Tenant-Isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    """K-2 Regression: Kein Cross-Tenant-Datenzugriff möglich."""

    @pytest.mark.django_db
    def test_attempt_not_accessible_from_other_tenant(
        self, assessment_type, dimensions, questions, maturity_levels, tenant_id, other_tenant_id
    ):
        from iil_learnfw.services.assessment_service import (
            AssessmentService,
            AssessmentValidationError,
        )

        attempt = AssessmentService.start_attempt(
            assessment_type_slug=assessment_type.slug,
            tenant_id=tenant_id,
        )

        with pytest.raises(AssessmentValidationError):
            AssessmentService.get_result(
                attempt_public_id=str(attempt.public_id),
                tenant_id=other_tenant_id,  # Falscher Tenant
            )

    @pytest.mark.django_db
    def test_start_attempt_wrong_tenant_raises(self, assessment_type, other_tenant_id):
        from iil_learnfw.services.assessment_service import (
            AssessmentService,
            AssessmentValidationError,
        )
        with pytest.raises(AssessmentValidationError):
            AssessmentService.start_attempt(
                assessment_type_slug=assessment_type.slug,
                tenant_id=other_tenant_id,
            )


# ---------------------------------------------------------------------------
# K-4: WeightedLikertScoring
# ---------------------------------------------------------------------------

class TestWeightedLikertScoring:
    """K-4 Regression: WeightedLikertScoring berücksichtigt Gewichtungen."""

    def _make_questions_with_weights(self, dims_weights: list[tuple[str, Decimal]]):
        from unittest.mock import MagicMock
        questions = []
        for dk, weight in dims_weights:
            q = MagicMock()
            q.pk = id(q)
            q.public_id = uuid.uuid4()
            q.dimension.key = dk
            q.dimension.label = dk
            q.dimension.weight = weight
            questions.append(q)
        return questions

    def _make_maturity(self, pct_min, pct_max):
        from unittest.mock import MagicMock
        m = MagicMock()
        m.key, m.label, m.color, m.description = "mid", "Mid", "#aaa", ""
        m.pct_min, m.pct_max = pct_min, pct_max
        return m

    def test_equal_weights_same_as_unweighted(self):
        """Mit identischen Gewichtungen muss WeightedLikert == Likert."""
        from iil_learnfw.services.assessment_scoring import LikertScoring, WeightedLikertScoring

        qs = self._make_questions_with_weights([
            ("dim1", Decimal("1.0")),
            ("dim2", Decimal("1.0")),
        ])
        answers = {str(q.public_id): 3 for q in qs}
        maturity = [self._make_maturity(0, 100)]

        likert_result   = LikertScoring().score(qs, answers, [], maturity, 1, 4)
        weighted_result = WeightedLikertScoring().score(qs, answers, [], maturity, 1, 4)

        assert likert_result.total_pct == weighted_result.total_pct

    def test_higher_weight_pulls_score(self):
        """Dimension mit weight=2.0 soll Gesamtscore stärker beeinflussen."""
        from iil_learnfw.services.assessment_scoring import WeightedLikertScoring

        # dim1 (weight=2.0) antwortet mit 4 (max)
        # dim2 (weight=1.0) antwortet mit 1 (min)
        qs = self._make_questions_with_weights([
            ("high_weight", Decimal("2.0")),
            ("low_weight",  Decimal("1.0")),
        ])
        answers = {
            str(qs[0].public_id): 4,  # high_weight: max
            str(qs[1].public_id): 1,  # low_weight: min
        }
        maturity = [self._make_maturity(0, 100)]

        result = WeightedLikertScoring().score(qs, answers, [], maturity, 1, 4)

        # Ungewichtet: (100 + 0) / 2 = 50%
        # Gewichtet:   (100*2 + 0*1) / 3 ≈ 67%
        assert result.total_pct > 50, \
            f"WeightedLikert mit höherem Gewicht auf max-Dimension soll > 50% geben, bekam {result.total_pct}%"


# ---------------------------------------------------------------------------
# K-5: ScoringStrategy als ABC
# ---------------------------------------------------------------------------

class TestScoringStrategyABC:
    """K-5 Regression: ScoringStrategy ist ABC mit abstractmethod."""

    def test_cannot_instantiate_base_class(self):
        from iil_learnfw.services.assessment_scoring import ScoringStrategy
        with pytest.raises(TypeError):
            ScoringStrategy()

    def test_incomplete_subclass_raises_on_instantiation(self):
        from iil_learnfw.services.assessment_scoring import ScoringStrategy
        class IncompleteStrategy(ScoringStrategy):
            pass  # score() nicht implementiert

        with pytest.raises(TypeError):
            IncompleteStrategy()


# ---------------------------------------------------------------------------
# K-6: Maturity-Lookup über total_pct
# ---------------------------------------------------------------------------

class TestMaturityLookupOnPct:
    """K-6 Regression: Maturity-Lookup verwendet total_pct (0-100), nicht Rohscore."""

    def _make_maturity_levels(self):
        from unittest.mock import MagicMock
        levels = []
        for key, pct_min, pct_max in [
            ("starter",  0,  24),
            ("entwickl", 25, 49),
            ("fortgesch",50, 74),
            ("reif",     75, 100),
        ]:
            m = MagicMock()
            m.key = key
            m.label = key
            m.color = "#aaa"
            m.description = ""
            m.pct_min = pct_min
            m.pct_max = pct_max
            levels.append(m)
        return levels

    def test_80pct_gives_reif(self):
        from iil_learnfw.services.assessment_scoring import LikertScoring
        q = unittest_mock_question()
        answers = {str(q.public_id): 4}  # max → 100%

        result = LikertScoring().score(
            questions=[q], answers=answers, dimensions=[],
            maturity_levels=self._make_maturity_levels(), scale_min=1, scale_max=4
        )
        assert result.maturity_key == "reif", \
            f"100% sollte 'reif' geben, bekam '{result.maturity_key}'"

    def test_30pct_gives_entwicklung(self):
        from iil_learnfw.services.assessment_scoring import LikertScoring
        # scale 1-4, Antwort 2 → pct = (2-1)/(4-1)*100 ≈ 33%
        q = unittest_mock_question()
        answers = {str(q.public_id): 2}

        result = LikertScoring().score(
            questions=[q], answers=answers, dimensions=[],
            maturity_levels=self._make_maturity_levels(), scale_min=1, scale_max=4
        )
        assert result.maturity_key == "entwickl", \
            f"~33% sollte 'entwickl' geben, bekam '{result.maturity_key}'"


def unittest_mock_question(dim_key="dim1"):
    from unittest.mock import MagicMock
    q = MagicMock()
    q.pk = 1
    q.public_id = uuid.uuid4()
    q.dimension.key = dim_key
    q.dimension.label = "Dimension"
    q.dimension.weight = Decimal("1.0")
    return q


# ---------------------------------------------------------------------------
# H-7: Maturity-Overlap-Validierung
# ---------------------------------------------------------------------------

class TestMaturityOverlapValidation:
    """H-7: Überlappende Maturity-Ranges werden erkannt."""

    @pytest.mark.django_db
    def test_overlapping_ranges_detected(self, assessment_type, tenant_id):
        from iil_learnfw.models.assessment_engine import AssessmentMaturityLevel
        from iil_learnfw.services.assessment_service import AssessmentService

        AssessmentMaturityLevel.objects.create(
            assessment_type=assessment_type, tenant_id=tenant_id,
            key="a", label="A", description="", color="#aaaaaa", pct_min=0, pct_max=50
        )
        AssessmentMaturityLevel.objects.create(
            assessment_type=assessment_type, tenant_id=tenant_id,
            key="b", label="B", description="", color="#bbbbbb", pct_min=40, pct_max=100
            # Überlappung 40-50 mit Level A
        )
        errors = AssessmentService.validate_maturity_ranges(
            assessment_type_id=assessment_type.pk,
            tenant_id=tenant_id,
        )
        assert len(errors) > 0, "Überlappende Maturity-Ranges sollten erkannt werden"

    @pytest.mark.django_db
    def test_non_overlapping_ranges_valid(self, assessment_type, maturity_levels, tenant_id):
        from iil_learnfw.services.assessment_service import AssessmentService

        errors = AssessmentService.validate_maturity_ranges(
            assessment_type_id=assessment_type.pk,
            tenant_id=tenant_id,
        )
        assert errors == [], f"Valide Ranges sollten keine Fehler geben, bekam: {errors}"


# ---------------------------------------------------------------------------
# Service-Integrationstests
# ---------------------------------------------------------------------------

class TestAssessmentServiceIntegration:
    """Vollständiger Assessment-Durchlauf (start → submit → result)."""

    @pytest.mark.django_db(transaction=True)
    def test_full_assessment_flow(
        self, assessment_type, dimensions, questions, maturity_levels, tenant_id
    ):
        from iil_learnfw.services.assessment_service import AssessmentService

        # Start
        attempt = AssessmentService.start_attempt(
            assessment_type_slug=assessment_type.slug,
            tenant_id=tenant_id,
        )
        assert attempt.completed_at is None

        # Submit
        raw_answers = {str(q.public_id): 3 for q in questions}
        result = AssessmentService.submit_attempt(
            attempt_public_id=str(attempt.public_id),
            tenant_id=tenant_id,
            raw_answers=raw_answers,
        )
        assert result.total_pct > 0
        assert result.total_pct <= 100
        assert result.maturity_key != ""

        # Result
        result_dict = AssessmentService.get_result(
            attempt_public_id=str(attempt.public_id),
            tenant_id=tenant_id,
        )
        assert result_dict["total_pct"] == result.total_pct
        assert result_dict["has_report"] is True

    @pytest.mark.django_db
    def test_submit_twice_raises(
        self, assessment_type, dimensions, questions, maturity_levels, tenant_id
    ):
        from iil_learnfw.services.assessment_service import (
            AssessmentService, AssessmentValidationError,
        )
        attempt = AssessmentService.start_attempt(
            assessment_type_slug=assessment_type.slug,
            tenant_id=tenant_id,
        )
        raw_answers = {str(q.public_id): 2 for q in questions}
        AssessmentService.submit_attempt(
            attempt_public_id=str(attempt.public_id),
            tenant_id=tenant_id,
            raw_answers=raw_answers,
        )
        with pytest.raises(AssessmentValidationError, match="bereits eingereicht"):
            AssessmentService.submit_attempt(
                attempt_public_id=str(attempt.public_id),
                tenant_id=tenant_id,
                raw_answers=raw_answers,
            )
