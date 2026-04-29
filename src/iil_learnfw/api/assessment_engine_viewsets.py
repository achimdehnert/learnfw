"""
iil_learnfw/api/viewsets/assessment_engine.py

DRF-ViewSets für die Assessment-Engine.

Platform-Standard: Business-Logik ausschließlich im Service-Layer.
ViewSets sind dünn: Validierung → Service-Call → Serialisierung.

Tenant-Isolation: tenant_id wird IMMER aus dem Request-Kontext gezogen,
nie aus dem Request-Body.

NEU-K4: `platform_context` existiert nicht als Python-Package.
        _get_tenant_id() muss von jedem Konsumenten überschrieben werden
        (z.B. via Middleware, Subdomain, oder Settings).
"""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from iil_learnfw.api.assessment_engine_serializers import (
    AssessmentResultSerializer,
    AssessmentSubmitSerializer,
    AssessmentTypeDetailSerializer,
    AssessmentTypeListSerializer,
)
from iil_learnfw.models.assessment_engine import AssessmentAttempt, AssessmentType
from iil_learnfw.services.assessment_service import (
    AssessmentService,
    AssessmentValidationError,
)

logger = logging.getLogger(__name__)


def _get_tenant_id(request):
    """
    Platform-Standard: tenant_id aus Request-Kontext.
    Niemals aus Request-Body oder GET-Parameter.

    NEU-K4: Konsumenten müssen diesen Resolver überschreiben.
    Typische Implementierungen:
    - request.tenant.id (Middleware-basiert)
    - settings.PLATFORM_TENANT_ID (Single-Tenant)
    - Subdomain-Lookup
    """
    # Default: Versuche gängige Konventionen
    if hasattr(request, "tenant") and hasattr(request.tenant, "id"):
        return request.tenant.id
    # Fallback: Platform-Standard-Tenant aus Settings
    from django.conf import settings as django_settings
    default_tid = getattr(django_settings, "IIL_LEARNFW", {}).get("DEFAULT_TENANT_ID")
    if default_tid:
        import uuid
        return uuid.UUID(str(default_tid)) if not isinstance(default_tid, uuid.UUID) else default_tid
    return None


class AssessmentTypeViewSet(ReadOnlyModelViewSet):
    """
    Verfügbare Assessment-Typen auflisten und Details abrufen.

    GET /api/assessments/types/
    GET /api/assessments/types/<slug>/
    GET /api/assessments/types/<slug>/questions/
    """
    lookup_field = "slug"
    permission_classes = [AllowAny]  # Öffentliche Liste — Tenant-Filter reicht

    def get_queryset(self):
        tenant_id = _get_tenant_id(self.request)
        return (
            AssessmentType.objects
            .filter(
                tenant_id=tenant_id,
                is_active=True,
                deleted_at__isnull=True,
            )
            .prefetch_related("dimensions", "maturity_levels")
            .order_by("title")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AssessmentTypeDetailSerializer
        return AssessmentTypeListSerializer

    @action(detail=True, methods=["get"], url_path="questions")
    def questions(self, request, slug=None):
        """
        GET /api/assessments/types/<slug>/questions/
        Gibt alle aktiven Fragen für einen Assessment-Typ zurück.
        """
        from iil_learnfw.api.serializers.assessment_engine import AssessmentQuestionSerializer  # noqa
        from iil_learnfw.models.assessment_engine import AssessmentQuestion  # noqa

        assessment_type = self.get_object()
        tenant_id       = _get_tenant_id(request)

        questions = (
            AssessmentQuestion.objects
            .filter(
                dimension__assessment_type=assessment_type,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
                is_active=True,
            )
            .select_related("dimension")
            .order_by("dimension__sort_order", "sort_order")
        )
        serializer = AssessmentQuestionSerializer(questions, many=True)
        return Response(serializer.data)


class AssessmentAttemptViewSet(GenericViewSet):
    """
    Assessment starten, Antworten einreichen, Ergebnis abrufen.

    POST /api/assessments/attempts/start/<type_slug>/
    POST /api/assessments/attempts/<public_id>/submit/
    GET  /api/assessments/attempts/<public_id>/result/
    """
    lookup_field   = "public_id"
    lookup_value_regex = r"[0-9a-f-]{36}"

    def get_queryset(self):
        tenant_id = _get_tenant_id(self.request)
        return AssessmentAttempt.objects.filter(
            tenant_id=tenant_id,
            deleted_at__isnull=True,
        )

    def get_permissions(self):
        """
        start/submit: AllowAny (anonyme Assessments möglich)
        result: IsAuthenticated für eingeloggte User, aber auch anonym via public_id
        """
        return [AllowAny()]

    @action(
        detail=False,
        methods=["post"],
        url_path=r"start/(?P<type_slug>[\w-]+)",
    )
    def start(self, request, type_slug: str):
        """
        POST /api/assessments/attempts/start/<type_slug>/

        Startet einen neuen Attempt. Gibt public_id zurück.
        """
        tenant_id  = _get_tenant_id(request)
        ip_address = request.META.get("REMOTE_ADDR", "")
        user       = request.user if request.user.is_authenticated else None

        try:
            attempt = AssessmentService.start_attempt(
                assessment_type_slug=type_slug,
                tenant_id=tenant_id,
                user=user,
                ip_address=ip_address,
            )
        except AssessmentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "attempt_public_id": str(attempt.public_id),
                "assessment_type":   type_slug,
                "started_at":        attempt.started_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, public_id: str):
        """
        POST /api/assessments/attempts/<public_id>/submit/

        Body: {"answers": {"<question_public_id>": <int_value>, ...}}
        """
        tenant_id  = _get_tenant_id(request)
        serializer = AssessmentSubmitSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            result = AssessmentService.submit_attempt(
                attempt_public_id=public_id,
                tenant_id=tenant_id,
                raw_answers=serializer.validated_data["answers"],
            )
        except AssessmentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            AssessmentResultSerializer(result).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def result(self, request, public_id: str):
        """
        GET /api/assessments/attempts/<public_id>/result/

        Gibt persistiertes Ergebnis zurück (kein Re-Scoring).
        """
        tenant_id = _get_tenant_id(request)

        try:
            result_dict = AssessmentService.get_result(
                attempt_public_id=public_id,
                tenant_id=tenant_id,
            )
        except AssessmentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(result_dict)


class AssessmentReportViewSet(RetrieveModelMixin, GenericViewSet):
    """
    Berichte abrufen und als PDF herunterladen.

    GET  /api/assessments/reports/<public_id>/
    GET  /api/assessments/reports/<public_id>/download_pdf/
    """
    lookup_field       = "public_id"
    lookup_value_regex = r"[0-9a-f-]{36}"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from iil_learnfw.models.assessment_engine import AssessmentReport  # noqa
        tenant_id = _get_tenant_id(self.request)
        return AssessmentReport.objects.filter(
            tenant_id=tenant_id,
            deleted_at__isnull=True,
        ).select_related("attempt", "attempt__assessment_type", "attempt__maturity_level")

    def get_serializer_class(self):
        from iil_learnfw.api.serializers.assessment_engine import AssessmentAttemptResultSerializer  # noqa
        return AssessmentAttemptResultSerializer

    @action(detail=True, methods=["get"], url_path="download_pdf")
    def download_pdf(self, request, public_id: str):
        """
        GET /api/assessments/reports/<public_id>/download_pdf/

        Gibt PDF zurück. Generiert es on-demand wenn nicht vorhanden
        und WeasyPrint konfiguriert ist.
        """
        from django.http import FileResponse, Http404  # noqa
        from django.conf import settings as django_settings  # noqa

        report = self.get_object()

        if not report.pdf_file:
            learnfw_cfg = getattr(django_settings, "IIL_LEARNFW", {})
            engine = learnfw_cfg.get("ASSESSMENT_REPORT_ENGINE", "none")
            if engine == "weasyprint":
                # Generierung on-demand (synchron für API, Celery-Task für async)
                from iil_learnfw.reports.weasyprint_report import generate_pdf  # noqa
                tenant_id = _get_tenant_id(request)
                generate_pdf(report=report, tenant_id=tenant_id)
                report.refresh_from_db()
            else:
                return Response(
                    {"detail": "PDF-Report nicht verfügbar (ASSESSMENT_REPORT_ENGINE='none')."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        if not report.pdf_file:
            raise Http404("PDF konnte nicht generiert werden.")

        return FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"assessment-report-{report.public_id}.pdf",
        )
