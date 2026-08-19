# iil-learnfw — Agent-Kontext

> Schema: pkg-agents-v1 · geprüft von `platform/tools/check_agents_md.py` ·
> GENERIERT von `platform/tools/gen_pkg_agents_md.py` (#2075 K2, ADR-266) —
> nicht von Hand pflegen; Fakten-Drift → Generator erneut laufen lassen.

## Zweck

Django Learning Platform Framework — Courses, Quizzes, Certificates, Gamification, SCORM

Details und Nutzungsbeispiele: `README.md`. Dieses Paket ist Teil der
iil-PyPI-Fleet (Programm: platform ADR-266 / #2075).

## Setup & Test (Einstiegskommando)

Ein Kommando, frischer Clone, Python >=3.12:

```bash
make setup && make test
```

Keine weiteren Vorbedingungen (kein Postgres, keine Env-Variablen) — wäre das
falsch, ist es ein Schema-Verstoß und gehört hier dokumentiert.

## Public API

Top-Level-Module:

- `iil_learnfw`

Extras: `iil-learnfw[all]`, `iil-learnfw[api]`, `iil-learnfw[certificates]`, `iil-learnfw[dev]`, `iil-learnfw[grading]`, `iil-learnfw[markdown]`, `iil-learnfw[pptx]`, `iil-learnfw[scorm]`, `iil-learnfw[tenancy]`

## Architektur-Constraints

- Library, kein App-Code: keine Deploy-/Prod-Kopplung.
- Änderungen an der Public API sind Semver-relevant (Frühwarn-Metrik #2075 K3).
- CI-Kontrakt: reusable `_ci-pypi.yml` (ADR-226); `make test` muss dem
  CI-Testlauf entsprechen.

## Release

Publish via `publish.yml` (OIDC) — nie manuell (ADR-226/266; Release nur über CI).
