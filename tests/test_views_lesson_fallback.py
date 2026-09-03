"""``render_markdown`` ohne das Extra ``[markdown]`` — der Fallback-Pfad.

Ein Hub ohne das Extra bekommt escaped Absätze statt gar nichts; und auch dort
darf Roh-HTML aus dem Inhalt nicht durchkommen.
"""

from __future__ import annotations

import sys

from iil_learnfw.views import render_markdown


def test_should_fall_back_to_escaped_paragraphs_without_the_markdown_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "markdown", None)  # import markdown → ImportError
    html = render_markdown("Erster Absatz\nmit Umbruch\n\nZweiter <b>Absatz</b>")
    assert html == "<p>Erster Absatz<br>mit Umbruch</p><p>Zweiter &lt;b&gt;Absatz&lt;/b&gt;</p>"


def test_should_return_empty_for_empty_text(monkeypatch):
    monkeypatch.setitem(sys.modules, "markdown", None)
    assert render_markdown("") == ""
