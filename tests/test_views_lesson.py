"""Die Lektionsseite (0.6.0, writing-hub#994 K4).

Vorher zeigte die Kursseite nur Titel; ``content_text``, ``content_file`` und
``external_url`` wurden gespeichert, aber nie gezeigt. Belegt hier: Markdown
wird gerendert (und Roh-HTML im Inhalt nicht durchgereicht), eine Datei-Lektion
zeigt ihren Link, die Kursseite verlinkt jede Lektion, Vor/Zurück laufen in
Leserichtung über Kapitelgrenzen, und Entwürfe wie fremde Kurse sind 404.
"""

from __future__ import annotations

import uuid

import pytest
from django.test import Client
from django.urls import reverse

from iil_learnfw.models import Chapter, Course, Lesson
from iil_learnfw.views import render_markdown

TENANT = uuid.UUID("00000000-0000-0000-0000-000000000000")


@pytest.fixture
def kurs(db):
    course = Course.objects.create(title="Digital & AI Strategy", status="published", tenant_id=TENANT)
    k1 = Chapter.objects.create(course=course, title="Termin 1", ordering=1, tenant_id=TENANT)
    k2 = Chapter.objects.create(course=course, title="Termin 2", ordering=2, tenant_id=TENANT)
    l1 = Lesson.objects.create(
        chapter=k1,
        title="Grundlagen",
        content_type="markdown",
        content_text="Untertitel\n\n- erster Punkt\n- zweiter Punkt\n\n_Notiz_",
        ordering=1,
        tenant_id=TENANT,
    )
    l2 = Lesson.objects.create(
        chapter=k1,
        title="Foliensatz: Grundlagen",
        content_type="pdf",
        external_url="https://writing.example/vorlesungen/abc/deck.pdf",
        ordering=2,
        tenant_id=TENANT,
    )
    l3 = Lesson.objects.create(chapter=k2, title="Übung: Einstiegs-Case", content_type="markdown", content_text="Aufgabe.", ordering=1, tenant_id=TENANT)
    return course, (l1, l2, l3)


def _url(course, lesson):
    return reverse("iil_learnfw:lesson-detail", args=[course.slug, lesson.pk])


def test_should_render_markdown_as_html():
    html = render_markdown("Untertitel\n\n- a\n- b\n\n_Notiz_")
    assert "<ul>" in html and "<li>a</li>" in html and "<em>Notiz</em>" in html


def test_should_render_a_markdown_lesson(kurs):
    course, (l1, _, _) = kurs
    resp = Client().get(_url(course, l1))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert 'data-testid="lektion-inhalt"' in body
    assert "<li>erster Punkt</li>" in body
    assert "<em>Notiz</em>" in body
    assert "Lektion 1 von 3" in body


def test_should_show_the_file_link_for_a_pdf_lesson(kurs):
    course, (_, l2, _) = kurs
    body = Client().get(_url(course, l2)).content.decode()
    assert 'data-testid="lektion-datei"' in body
    assert 'href="https://writing.example/vorlesungen/abc/deck.pdf"' in body
    assert "Foliensatz öffnen (PDF)" in body
    assert 'data-testid="lektion-inhalt"' not in body


def test_should_link_every_lesson_from_the_course_page(kurs):
    course, lektionen = kurs
    body = Client().get(reverse("iil_learnfw:course-detail", args=[course.slug])).content.decode()
    for lek in lektionen:
        assert f'href="{_url(course, lek)}"' in body, lek.title


def test_should_page_forward_and_back_in_reading_order_across_chapters(kurs):
    course, (l1, l2, l3) = kurs
    body1 = Client().get(_url(course, l1)).content.decode()
    assert f'href="{_url(course, l2)}" rel="next"' in body1
    assert 'rel="prev"' not in body1
    body2 = Client().get(_url(course, l2)).content.decode()
    assert f'href="{_url(course, l1)}" rel="prev"' in body2
    assert f'href="{_url(course, l3)}" rel="next"' in body2  # über die Kapitelgrenze
    body3 = Client().get(_url(course, l3)).content.decode()
    assert 'rel="next"' not in body3


def test_should_hide_lessons_of_a_draft_course(kurs):
    course, (l1, _, _) = kurs
    course.status = "draft"
    course.save()
    assert Client().get(_url(course, l1)).status_code == 404


def test_should_not_serve_a_lesson_under_another_courses_slug(kurs, db):
    course, (l1, _, _) = kurs
    fremd = Course.objects.create(title="Anderer Kurs", status="published", tenant_id=TENANT)
    assert Client().get(reverse("iil_learnfw:lesson-detail", args=[fremd.slug, l1.pk])).status_code == 404


def test_should_not_pass_raw_html_from_content_through(kurs):
    course, (l1, _, _) = kurs
    l1.content_text = "Text <script>alert(1)</script>"
    l1.save()
    body = Client().get(_url(course, l1)).content.decode()
    assert "<script>" not in body
