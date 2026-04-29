# iil-learnfw

Django Learning Platform Framework — Courses, Quizzes, Certificates, Gamification, SCORM.

Part of the [IIL Platform](https://github.com/achimdehnert/platform) ecosystem.

## Architecture Decision

- **ADR-139**: Package design, models, services, API
- **ADR-140**: Learn-Hub (central deployment using this package)
- **ADR-137**: Multi-Tenancy (TenantManager, RLS)

## Installation

```bash
# Minimal
pip install iil-learnfw

# All extras
pip install "iil-learnfw[all]"

# Specific extras
pip install "iil-learnfw[api,tenancy,certificates]"
```

## Quick Start

```python
# settings.py
INSTALLED_APPS = [
    "iil_learnfw",   # Python module name (pip package: iil-learnfw)
    ...
]

IIL_LEARNFW = {
    "TENANT_AWARE": True,        # Enable multi-tenancy (requires `tenancy` extra)
    "AUTHORING_ENABLED": True,   # Allow course creation via admin/API
    "ENROLLMENT_MODE": "self_enroll",  # Options: self_enroll | invite_only | open
}
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("schulungen/", include("iil_learnfw.urls")),
]
```

## Extras

| Extra | Dependencies | Features |
|---|---|---|
| `api` | djangorestframework, drf-spectacular | REST API + OpenAPI docs |
| `tenancy` | django-tenancy | Multi-tenant support (ADR-137) |
| `certificates` | weasyprint, qrcode | PDF certificates with QR verification |
| `pptx` | python-pptx | PPTX slide import, auto-split |
| `scorm` | lxml | SCORM 1.2/2004 import/export |
| `markdown` | markdown, pymdown-extensions | Markdown content rendering |
| `grading` | httpx | External grading service integration |
| `all` | All of the above | Full feature set |

## Modules

| Module | Responsibility |
|---|---|
| `iil_learnfw.courses` | Course → Chapter → Lesson, Categories, Enrollment |
| `iil_learnfw.content` | Content backends: Markdown, PDF, PPTX |
| `iil_learnfw.progress` | User progress tracking, completion |
| `iil_learnfw.assessments` | Quizzes, questions, attempts, scoring |
| `iil_learnfw.certificates` | PDF generation, verification URLs |
| `iil_learnfw.onboarding` | Mandatory courses, checklists |
| `iil_learnfw.gamification` | Points, badges, streaks, leaderboards |
| `iil_learnfw.scorm` | SCORM import/export |

## Deployment

Run migrations after installation:

```bash
python manage.py migrate
```

For multi-tenant setups, configure `TENANT_AWARE: True` in `IIL_LEARNFW` and ensure each request carries a `tenant_id` (see ADR-137).

Production checklist:
- Set `DEBUG=False` and configure `ALLOWED_HOSTS`
- Configure media storage (PDF certificates, PPTX uploads)
- Set `CACHES` to Redis for session/progress caching

## License

MIT
