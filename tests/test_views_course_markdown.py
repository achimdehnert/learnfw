"""Kurs- und Kapitelbeschreibung sind Markdown (0.6.0, writing-hub#994 [47]).

Die Modulbeschreibung aus writing-hub kommt mit ``**Titel**`` und Listen; auf
der Kursseite standen Sterne und Bindestriche roh im Text.
"""

from __future__ import annotations

import uuid

import pytest
from django.test import Client
from django.urls import reverse

from iil_learnfw.models import Chapter, Course

TENANT = uuid.UUID("00000000-0000-0000-0000-000000000000")


@pytest.fixture
def kurs(db):
    course = Course.objects.create(
        title="Digital & AI Strategy",
        status="published",
        description="**Digital & AI Strategy** (Nr. 10130)\n\n- 5 ECTS\n- Pflichtfach",
        tenant_id=TENANT,
    )
    Chapter.objects.create(course=course, title="Termin 1", ordering=1, description="Lernziele:\n\n- Ziel A\n- Ziel B", tenant_id=TENANT)
    return course


def test_should_render_course_and_chapter_description_as_markdown(kurs):
    body = Client().get(reverse("iil_learnfw:course-detail", args=[kurs.slug])).content.decode()
    assert "<strong>Digital &amp; AI Strategy</strong>" in body
    assert "<li>5 ECTS</li>" in body
    assert "<li>Ziel A</li>" in body
    assert "**Digital" not in body
    assert "- Ziel A" not in body


def test_should_not_pass_raw_html_in_the_description_through(kurs):
    kurs.description = "Text <script>alert(1)</script>"
    kurs.save()
    body = Client().get(reverse("iil_learnfw:course-detail", args=[kurs.slug])).content.decode()
    assert "<script>" not in body
