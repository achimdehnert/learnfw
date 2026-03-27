"""Built-in assessment seed data for iil-learnfw.

Usage:
    python manage.py assessment_seed --key ki_souveraenitaet
    python manage.py assessment_seed --key nis2_readiness
    python manage.py assessment_seed --key dsgvo_readiness
"""

AVAILABLE_SEEDS = {
    "ki_souveraenitaet": "iil_learnfw.seeds.ki_souveraenitaet",
    "nis2_readiness": "iil_learnfw.seeds.nis2_readiness",
    "dsgvo_readiness": "iil_learnfw.seeds.dsgvo_readiness",
}
