"""
iil_learnfw/models/assessment_engine.py

Assessment-Engine — Generische Maturity/Readiness-Assessment-Infrastruktur.

Korrekturen gegenüber ADR-142-PROPOSED:
  B-1  BigAutoField PK auf allen Modellen
  B-2  public_id UUIDField auf allen Modellen
  B-3  UniqueConstraint statt unique_together
  B-4  deleted_at (Soft-Delete) auf allen Modellen
  H-1  updated_at auf allen Modellen
  H-2  i18n via gettext_lazy
  H-6  ScoringStrategyChoices als TextChoices
  M-2  RegexValidator für color-Feld
  M-5  sort_order statt ordering (Feldname)
  K-6  pct_min/pct_max statt score_min/score_max für Maturity-Lookup

Meta-Review-Korrekturen (NEU-K1, NEU-K2, NEU-R1):
  NEU-K1  tenant_id ist UUIDField (nicht int) — konsistent mit TenantMixin
  NEU-K2  Import-Pfad: TenantMixin lebt in iil_learnfw.models.course, nicht mixins
  NEU-R1  AssessmentQuestion.key-Feld für stabile Seed-Identifikation
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# Platform-standard: TenantMixin stellt tenant_id = UUIDField(null=True, db_index=True) bereit
# KEINE ForeignKey zum Tenant-Modell (Platform-Standard)
from iil_learnfw.models.course import TenantMixin

# ---------------------------------------------------------------------------
# Hilfsmittel
# ---------------------------------------------------------------------------

_HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message=_("Muss ein gültiger Hex-Farbcode sein (z. B. #1A2B3C)."),
)


class ScoringStrategyChoices(models.TextChoices):
    LIKERT          = "likert",           _("Likert-Skala (1-N)")
    WEIGHTED_LIKERT = "weighted_likert",  _("Gewichtete Likert-Skala")
    QUIZ            = "quiz",             _("Quiz (Richtig/Falsch)")
    SURVEY          = "survey",           _("Umfrage (kein Scoring)")


# ---------------------------------------------------------------------------
# Soft-Delete Manager
# ---------------------------------------------------------------------------

class ActiveManager(models.Manager):
    """Standard-Manager: filtert soft-gelöschte Datensätze aus."""

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager inkl. soft-gelöschter Datensätze (für Admin / Reports)."""
    pass


# ---------------------------------------------------------------------------
# Konfigurationsmodelle
# ---------------------------------------------------------------------------

class AssessmentType(TenantMixin):
    """
    Definition eines Assessment-Typs (z. B. 'ki_souveraenitaet', 'dsgvo_readiness').

    Ein AssessmentType ist die zentrale Konfigurationseinheit. Er definiert
    Scoring-Strategie, Skala, Reifegrade und Metadaten.
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    key            = models.CharField(max_length=50, unique=True, verbose_name=_("Schlüssel"))
    title          = models.CharField(max_length=300, verbose_name=_("Titel"))
    slug           = models.SlugField(max_length=300, unique=True, verbose_name=_("Slug"))
    description    = models.TextField(blank=True, verbose_name=_("Beschreibung"))
    scoring_strategy = models.CharField(
        max_length=30,
        choices=ScoringStrategyChoices,
        default=ScoringStrategyChoices.LIKERT,
        verbose_name=_("Scoring-Strategie"),
    )
    scale_min      = models.PositiveSmallIntegerField(default=1, verbose_name=_("Skalenminimum"))
    scale_max      = models.PositiveSmallIntegerField(default=4, verbose_name=_("Skalenmaximum"))
    scale_labels   = models.JSONField(
        default=list,
        verbose_name=_("Skalen-Labels"),
        help_text=_('Schema: [{"value": 1, "label": "Trifft nicht zu"}, ...]'),
    )
    is_public      = models.BooleanField(
        default=False, verbose_name=_("Öffentlich (anonym ohne Login)"),
    )
    is_active      = models.BooleanField(default=True, verbose_name=_("Aktiv"))
    course         = models.ForeignKey(
        "iil_learnfw.Course",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assessments",
        verbose_name=_("Verknüpfter Kurs"),
    )
    passing_score          = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Mindest-Prozentsatz zum Bestehen"),
        help_text=_("0 = kein Bestehen erforderlich. Wert in Prozent (0-100)."),
    )
    certificate_enabled    = models.BooleanField(default=False, verbose_name=_("Zertifikat aktiviert"))
    report_enabled         = models.BooleanField(default=True, verbose_name=_("Bericht aktiviert"))
    reassessment_months    = models.PositiveSmallIntegerField(
        default=6, verbose_name=_("Re-Assessment nach N Monaten"),
    )
    retention_days         = models.PositiveIntegerField(
        default=730,
        verbose_name=_("Aufbewahrungsfrist (Tage)"),
        help_text=_("DSGVO: Standard 730 Tage (24 Monate)."),
    )

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))
    updated_at  = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))
    deleted_at  = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ["title"]
        verbose_name = _("Assessment-Typ")
        verbose_name_plural = _("Assessment-Typen")
        constraints = [
            models.CheckConstraint(
                check=models.Q(scale_min__lt=models.F("scale_max")),
                name="assessment_type_scale_min_lt_max",
            ),
            models.CheckConstraint(
                check=models.Q(passing_score__lte=100),
                name="assessment_type_passing_score_max_100",
            ),
        ]

    def __str__(self) -> str:
        return f"AssessmentType({self.public_id}): {self.title}"


class AssessmentDimension(TenantMixin):
    """
    Bewertungsdimension innerhalb eines Assessment-Typs.

    Beispiel: KI-Souveränität hat Dimensionen wie 'Datenkompetenz', 'KI-Governance'.
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="dimensions",
        verbose_name=_("Assessment-Typ"),
    )
    key         = models.CharField(max_length=50, verbose_name=_("Schlüssel"))
    label       = models.CharField(max_length=200, verbose_name=_("Bezeichnung"))
    weight      = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0,
        verbose_name=_("Gewichtung"),
        help_text=_("Wird von WeightedLikertScoring verwendet. Standard: 1.0"),
    )
    sort_order  = models.PositiveSmallIntegerField(
        default=0, verbose_name=_("Sortierreihenfolge"),
    )
    is_active   = models.BooleanField(default=True, verbose_name=_("Aktiv"))

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))
    updated_at  = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))
    deleted_at  = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ["sort_order"]
        verbose_name = _("Assessment-Dimension")
        verbose_name_plural = _("Assessment-Dimensionen")
        constraints = [
            # B-3: UniqueConstraint statt unique_together
            models.UniqueConstraint(
                fields=["assessment_type", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_assessment_dimension_type_key_active",
            ),
        ]

    def __str__(self) -> str:
        return f"AssessmentDimension({self.public_id}): {self.label}"


class AssessmentQuestion(TenantMixin):
    """
    Einzelne Frage innerhalb einer Dimension.

    Das `version`-Feld wird inkrementiert, wenn der Fragetext geändert wird.
    Historische Attempts speichern Frage-Snapshot (assessment_service.submit_attempt).
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    dimension   = models.ForeignKey(
        AssessmentDimension,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("Dimension"),
    )
    key         = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Stabiler Schlüssel"),
        help_text=_("Idempotenter Seed-Key (z.B. 'strat_gov_q1'). Leer = text-basierte Deduplizierung."),
    )
    text        = models.TextField(verbose_name=_("Fragetext"))
    help_text   = models.TextField(blank=True, verbose_name=_("Hilfetext"))
    sort_order  = models.PositiveSmallIntegerField(
        default=0, verbose_name=_("Sortierreihenfolge"),
    )
    is_active   = models.BooleanField(default=True, verbose_name=_("Aktiv"))
    version     = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Version"),
        help_text=_("Wird bei Textänderungen inkrementiert. Historische Antworten bleiben zuordenbar."),
    )

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))
    updated_at  = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))
    deleted_at  = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ["dimension__sort_order", "sort_order"]
        verbose_name = _("Assessment-Frage")
        verbose_name_plural = _("Assessment-Fragen")

    def __str__(self) -> str:
        return f"AssessmentQuestion({self.public_id}): {self.text[:60]}"


class AssessmentMaturityLevel(TenantMixin):
    """
    Reifegrad-Stufe mit Schwellenwerten (in Prozent, 0-100).

    WICHTIG: `pct_min` und `pct_max` sind PROZENT-Werte (0-100),
    nicht Rohpunkte. Der Maturity-Lookup erfolgt auf `AssessmentAttempt.total_pct`.
    Überlappungsfreiheit wird im Service-Layer sichergestellt (kein DB-Constraint möglich).
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="maturity_levels",
        verbose_name=_("Assessment-Typ"),
    )
    key         = models.CharField(max_length=50, verbose_name=_("Schlüssel"))
    label       = models.CharField(max_length=200, verbose_name=_("Bezeichnung"))
    description = models.TextField(verbose_name=_("Beschreibung"))
    color       = models.CharField(
        max_length=7,
        validators=[_HEX_COLOR_VALIDATOR],
        verbose_name=_("Farbe (Hex)"),
    )
    icon        = models.CharField(max_length=50, blank=True, verbose_name=_("Icon"))
    # K-6: pct_min/pct_max statt score_min/score_max — Einheit: Prozent (0-100)
    pct_min     = models.PositiveSmallIntegerField(verbose_name=_("Mindest-Prozent"))
    pct_max     = models.PositiveSmallIntegerField(verbose_name=_("Maximal-Prozent"))
    sort_order  = models.PositiveSmallIntegerField(default=0, verbose_name=_("Sortierreihenfolge"))

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))
    updated_at  = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))
    deleted_at  = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ["pct_min"]
        verbose_name = _("Assessment-Reifegrad")
        verbose_name_plural = _("Assessment-Reifegrade")
        constraints = [
            models.CheckConstraint(
                check=models.Q(pct_min__lte=models.F("pct_max")),
                name="assessment_maturity_pct_min_lte_max",
            ),
            models.CheckConstraint(
                check=models.Q(pct_max__lte=100),
                name="assessment_maturity_pct_max_lte_100",
            ),
            models.UniqueConstraint(
                fields=["assessment_type", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="uq_assessment_maturity_type_key_active",
            ),
        ]

    def __str__(self) -> str:
        return f"AssessmentMaturityLevel({self.public_id}): {self.label} ({self.pct_min}-{self.pct_max}%)"


class AssessmentRecommendation(TenantMixin):
    """
    Empfehlung bei Schwäche in einer Dimension → verlinkt auf Kurs/Lektion.

    Aktivierungsbedingung: `dimension.score_pct < threshold_below_pct`
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    dimension       = models.ForeignKey(
        AssessmentDimension,
        on_delete=models.CASCADE,
        related_name="recommendations",
        verbose_name=_("Dimension"),
    )
    # Schwellenwert in Prozent (0-100), nicht als Rohwert
    threshold_below_pct = models.PositiveSmallIntegerField(
        verbose_name=_("Schwellenwert (%)"),
        help_text=_("Empfehlung aktiv wenn Dimensions-Score (%) unter diesem Wert liegt. 0-100."),
    )
    title           = models.CharField(max_length=300, verbose_name=_("Titel"))
    description     = models.TextField(verbose_name=_("Beschreibung"))
    priority        = models.PositiveSmallIntegerField(default=0, verbose_name=_("Priorität"))
    course          = models.ForeignKey(
        "iil_learnfw.Course",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="recommended_by",
        verbose_name=_("Empfohlener Kurs"),
    )
    lesson          = models.ForeignKey(
        "iil_learnfw.Lesson",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="recommended_by",
        verbose_name=_("Empfohlene Lektion"),
    )
    external_url    = models.URLField(blank=True, verbose_name=_("Externe URL"))

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))
    updated_at  = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))
    deleted_at  = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ["priority"]
        verbose_name = _("Assessment-Empfehlung")
        verbose_name_plural = _("Assessment-Empfehlungen")
        constraints = [
            models.CheckConstraint(
                check=models.Q(threshold_below_pct__lte=100),
                name="assessment_rec_threshold_lte_100",
            ),
        ]

    def __str__(self) -> str:
        return f"AssessmentRecommendation({self.public_id}): {self.title[:60]}"


# ---------------------------------------------------------------------------
# Ergebnis-Modelle
# ---------------------------------------------------------------------------

class AssessmentAttempt(TenantMixin):
    """
    Eine Durchführung eines Assessments (Login-Nutzer oder anonym).

    Antworten werden als Snapshot gespeichert (K-3):
        {str(question.public_id): {"question_text": "...", "value": 3, "question_version": 1}}
    So bleibt der Attempt auch nach Frage-Änderungen rekonstruierbar (DSGVO/Audit).

    Maturity-Lookup: über `total_pct` (0-100), nicht `total_score` (K-6).
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("Assessment-Typ"),
    )
    user            = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assessment_attempts",
        verbose_name=_("Benutzer"),
    )
    # Antwort-Snapshot (nicht rohe PKs — K-3)
    answers         = models.JSONField(
        default=dict,
        verbose_name=_("Antworten (Snapshot)"),
        help_text=_(
            'Schema: {str(question.public_id): {"question_text": "...", "value": 3, "question_version": 1}}'
        ),
    )
    # Ergebnisse
    scores          = models.JSONField(
        default=dict,
        verbose_name=_("Dimensions-Scores"),
        help_text=_('Schema: {dimension_key: {"score": "2.75", "pct": 58, "weight": "1.00"}}'),
    )
    total_score     = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name=_("Gesamt-Rohscore"),
    )
    total_pct       = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Gesamt-Prozent (0-100)"),
    )
    maturity_level  = models.ForeignKey(
        AssessmentMaturityLevel,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Erreichter Reifegrad"),
    )
    weakest_dimension   = models.CharField(max_length=50, blank=True, verbose_name=_("Schwächste Dimension"))
    strongest_dimension = models.CharField(max_length=50, blank=True, verbose_name=_("Stärkste Dimension"))

    # Timing
    started_at      = models.DateTimeField(auto_now_add=True, verbose_name=_("Gestartet am"))
    completed_at    = models.DateTimeField(null=True, blank=True, verbose_name=_("Abgeschlossen am"))
    updated_at      = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))

    # DSGVO
    ip_hash         = models.CharField(max_length=64, blank=True, verbose_name=_("IP-Hash"))
    retention_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Aufbewahrung endet am"))
    deleted_at      = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ["-started_at"]
        verbose_name = _("Assessment-Durchführung")
        verbose_name_plural = _("Assessment-Durchführungen")
        # H-3: Compound-Indizes für häufige Queries
        indexes = [
            models.Index(
                fields=["assessment_type", "user", "tenant_id"],
                name="idx_attempt_type_user_tenant",
            ),
            models.Index(
                fields=["tenant_id", "deleted_at", "-started_at"],
                name="idx_attempt_tenant_del_date",
            ),
            models.Index(
                fields=["retention_expires_at"],
                condition=models.Q(deleted_at__isnull=True),
                name="idx_attempt_retention_active",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_pct__lte=100),
                name="assessment_attempt_total_pct_lte_100",
            ),
        ]

    def __str__(self) -> str:
        return f"AssessmentAttempt({self.public_id}): {self.assessment_type_id} {self.total_pct}%"


class AssessmentReport(TenantMixin):
    """
    Generierter Bericht für ein abgeschlossenes Assessment.

    `recommendations` ist ein Snapshot zum Zeitpunkt der Report-Generierung
    (bewusste Denormalisierung für PDF-Unveränderlichkeit).
    """

    id             = models.BigAutoField(primary_key=True)
    public_id      = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
        verbose_name=_("Public ID"),
    )
    attempt         = models.OneToOneField(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="report",
        verbose_name=_("Durchführung"),
    )
    recommendations = models.JSONField(
        default=list,
        verbose_name=_("Empfehlungs-Snapshot"),
        help_text=_(
            "Snapshot zum Generierungszeitpunkt. "
            "Schema: [{dimension_key, gap_pct, title, description, priority, course_id, lesson_id, external_url}]"
        ),
    )
    # H-4: Storage-Backend aus Platform-Context
    pdf_file        = models.FileField(
        upload_to="assessments/reports/%Y/%m/",
        blank=True,
        verbose_name=_("PDF-Datei"),
    )
    certificate     = models.ForeignKey(
        "iil_learnfw.IssuedCertificate",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Ausgestelltes Zertifikat"),
    )

    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Generiert am"))
    updated_at   = models.DateTimeField(auto_now=True, verbose_name=_("Aktualisiert am"))
    deleted_at   = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Gelöscht am"))

    objects     = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = _("Assessment-Bericht")
        verbose_name_plural = _("Assessment-Berichte")

    def __str__(self) -> str:
        return f"AssessmentReport({self.public_id}): attempt={self.attempt_id}"
