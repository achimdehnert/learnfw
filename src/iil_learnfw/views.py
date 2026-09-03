"""iil-learnfw template views.

Drei öffentliche Seiten: Kursliste, Kursseite (Kapitel + Lektionstitel) und —
seit 0.6.0 — die **Lektionsseite**. Ohne sie war ein Kurs ein Inhaltsverzeichnis:
``Lesson.content_text`` (Markdown), ``content_file`` und ``external_url``
wurden angelegt, aber nirgends gezeigt (writing-hub#994 K4).
"""

from __future__ import annotations

import html

from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.safestring import mark_safe

from iil_learnfw.models import Course, Lesson


def course_list(request):
    """Public course listing."""
    courses = Course.objects.published()
    return render(
        request,
        "iil_learnfw/course_list.html",
        {"courses": courses},
    )


def course_detail(request, slug):
    """Course detail page with chapters and lessons."""
    course = get_object_or_404(
        Course.objects.filter(status="published"),
        slug=slug,
    )
    chapters = list(course.chapters.prefetch_related("lessons").all())
    # Kurs- und Kapitelbeschreibung sind Markdown (Modulbeschreibung aus writing-hub,
    # Lernziel-Listen) — vorher standen die Sterne und Bindestriche roh auf der Seite.
    for chapter in chapters:
        chapter.beschreibung_html = mark_safe(render_markdown(chapter.description))  # noqa: S308
    return render(
        request,
        "iil_learnfw/course_detail.html",
        {
            "course": course,
            "chapters": chapters,
            "beschreibung_html": mark_safe(render_markdown(course.description)),  # noqa: S308
        },
    )


def render_markdown(text: str) -> str:
    """Markdown → HTML für ``content_type="markdown"``.

    Mit dem Extra ``iil-learnfw[markdown]`` echtes Markdown (Listen, Betonung,
    Überschriften); ohne es escaped Absätze. Roh-HTML im Inhalt wird in beiden
    Fällen nicht durchgereicht — Bündel kommen auch von außen.
    """
    if not text:
        return ""
    try:
        import markdown  # optionales Extra
    except ImportError:  # pragma: no cover — Umgebung ohne Extra
        absaetze = [f"<p>{html.escape(a).replace(chr(10), '<br>')}</p>" for a in text.split("\n\n") if a.strip()]
        return "".join(absaetze)
    # html.escape vorab: python-markdown lässt eingebettetes HTML sonst durch.
    return markdown.markdown(html.escape(text, quote=False), extensions=["extra", "sane_lists"], output_format="html")


def _lektionen_des_kurses(course: Course) -> list[Lesson]:
    """Alle Lektionen des Kurses in Leserichtung (Kapitel, dann Lektion)."""
    return list(Lesson.objects.filter(chapter__course=course).select_related("chapter").order_by("chapter__ordering", "ordering", "pk"))


def lesson_detail(request, slug, pk):
    """Eine Lektion lesen: Markdown gerendert, Datei oder Link als Schaltfläche,
    dazu Vor/Zurück in Leserichtung. Nur in veröffentlichten Kursen; eine
    Lektion aus einem anderen Kurs ist unter diesem Slug 404."""
    course = get_object_or_404(Course.objects.filter(status="published"), slug=slug)
    lektionen = _lektionen_des_kurses(course)
    lesson = next((lek for lek in lektionen if lek.pk == pk), None)
    if lesson is None:
        raise Http404("Lektion nicht in diesem Kurs")
    pos = lektionen.index(lesson)
    zurueck = lektionen[pos - 1] if pos > 0 else None
    weiter = lektionen[pos + 1] if pos + 1 < len(lektionen) else None

    datei_url = ""
    if lesson.content_file:
        datei_url = lesson.content_file.url
    elif lesson.external_url:
        datei_url = lesson.external_url

    inhalt_html = mark_safe(render_markdown(lesson.content_text)) if lesson.content_type == "markdown" else ""  # noqa: S308

    return render(
        request,
        "iil_learnfw/lesson_detail.html",
        {
            "course": course,
            "chapter": lesson.chapter,
            "lesson": lesson,
            "inhalt_html": inhalt_html,
            "datei_url": datei_url,
            "zurueck": zurueck,
            "weiter": weiter,
            "position": pos + 1,
            "anzahl": len(lektionen),
        },
    )
