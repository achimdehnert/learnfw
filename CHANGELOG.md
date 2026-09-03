# Changelog — learnfw

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.6.0] — 2026-09-03

### Added
- **Lektionsseite** `views.lesson_detail` + `iil_learnfw:lesson-detail` (`<slug>/lektion/<pk>/`): Markdown gerendert (`render_markdown`, Extra `[markdown]`, sonst escaped Absätze), PDF/PPTX/externe Lektionen als Schaltfläche in neuem Tab, Vor/Zurück in Leserichtung über Kapitelgrenzen, Position „Lektion n von N". Vorher war ein Kurs ein Inhaltsverzeichnis: `content_text`, `content_file`, `external_url` wurden gespeichert und nie gezeigt (writing-hub#994 K4).
- `course_detail.html`: jede Lektion verlinkt ihre Seite; Kurs- und Kapitelbeschreibung werden als Markdown gerendert (`render_markdown`, Roh-HTML bleibt draußen).
- Tests laufen jetzt auch gegen die Views (`tests/urls.py`, `ROOT_URLCONF`, `TEMPLATES` in den Test-Settings).

---

## [0.5.4] — 2026-04-28

### Fixed
- `assessment_engine.py`: 6× `CheckConstraint(check=...)` → `CheckConstraint(condition=...)` — Django 5.x Deprecation behoben (`RemovedInDjango60Warning`)
- `assessment_service.py`: E741 — Lambda-Variable `l` → `lvl` (Ruff-Lint-Fix)

### Changed
- `pyproject.toml`: `line-length` 100 → 160 (Seed-Strings; verhindert Ruff-Umbrüche in Fixtures)
- `pyproject.toml`: Python 3.11 aus CI-Matrix entfernt (`requires-python = ">=3.12"`)
- `publish.yml`: Python 3.11 → 3.12 in CI; `id-token: write` + `environment: pypi` entfernt (nicht erforderlich für token-basiertes Upload)

---

## [0.5.3] — 2026-04-21

### Added
- `py.typed` marker — PEP 561 compliance, enables downstream type checking (ADR-155)
- `Makefile` — standardized local development targets (platform-audit)
- `MIT LICENSE` file

### Changed
- `requires-python = ">=3.12"` — aligns with platform-wide Python standard
- `django>=5.0,<6.0` upper bound — compatibility scoping
- `.windsurf/` excluded from sdist/wheel builds (`.gitignore` + hatch exclude)
