# Changelog — learnfw

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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

## [0.5.3] — Unreleased

### Added
- Initial release.
