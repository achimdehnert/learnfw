"""
iil_learnfw/seeds/ki_souveraenitaet.py

Seed-Daten: KI-Souveränität Assessment (D4, 4 Dimensionen, WeightedLikert).

Referenz: ADR-004 (QuickCheck D4), ADR-142 (Assessment-Engine).
Konfiguration entspricht dem bestehenden QuickCheck D4 Scoring-Schema.

Fragestellungen mit Fachexperten abgestimmt (ADR-142, Risiko: Fachexpertise).
"""
from __future__ import annotations

SEED: dict = {
    "key":              "ki_souveraenitaet",
    "title":            "KI-Souveränität Check",
    "slug":             "ki-souveraenitaet",
    "description": (
        "Wie souverän ist Ihre Organisation im Umgang mit Künstlicher Intelligenz? "
        "Dieser Check bewertet Ihren KI-Reifegrad in 4 Dimensionen."
    ),
    "scoring_strategy": "weighted_likert",
    "scale_min":        1,
    "scale_max":        4,
    "scale_labels": [
        {"value": 1, "label": "Trifft nicht zu"},
        {"value": 2, "label": "Trifft kaum zu"},
        {"value": 3, "label": "Trifft weitgehend zu"},
        {"value": 4, "label": "Trifft vollständig zu"},
    ],
    "is_public":           True,
    "is_active":           True,
    "certificate_enabled": False,
    "report_enabled":      True,
    "passing_score":       0,
    "reassessment_months": 6,
    "retention_days":      730,

    "dimensions": [
        {
            "key":        "strategie_governance",
            "label":      "KI-Strategie & Governance",
            "weight":     "1.50",   # Höchste Gewichtung (strategisch)
            "sort_order": 1,
            "questions": [
                {
                    "key":        "strat_gov_q1",
                    "text":       "Unsere Organisation hat eine dokumentierte KI-Strategie, die mit der Unternehmensstrategie verknüpft ist.",
                    "help_text":  "Denken Sie an Roadmaps, Vorstandsbeschlüsse, OKRs mit KI-Bezug.",
                    "sort_order": 1,
                },
                {
                    "key":        "strat_gov_q2",
                    "text":       "Es gibt klare Verantwortlichkeiten für KI-Projekte und deren Governance (z. B. AI Owner, AI Board).",
                    "sort_order": 2,
                },
                {
                    "key":        "strat_gov_q3",
                    "text":       "KI-Investitionen werden systematisch evaluiert und priorisiert.",
                    "sort_order": 3,
                },
            ],
        },
        {
            "key":        "daten_kompetenz",
            "label":      "Datenkompetenz & -infrastruktur",
            "weight":     "1.25",
            "sort_order": 2,
            "questions": [
                {
                    "key":        "daten_q1",
                    "text":       "Relevante Daten für KI-Anwendungen sind identifiziert, zugänglich und in ausreichender Qualität vorhanden.",
                    "sort_order": 1,
                },
                {
                    "key":        "daten_q2",
                    "text":       "Unser Unternehmen verfügt über eine strukturierte Daten-Governance (Datenkatalog, Datenqualitätsmanagement).",
                    "sort_order": 2,
                },
                {
                    "key":        "daten_q3",
                    "text":       "Mitarbeitende im Umgang mit Daten sind geschult und verstehen Daten-Grundkonzepte.",
                    "sort_order": 3,
                },
            ],
        },
        {
            "key":        "ki_kompetenz",
            "label":      "KI-Kompetenz & Kultur",
            "weight":     "1.00",
            "sort_order": 3,
            "questions": [
                {
                    "key":        "ki_komp_q1",
                    "text":       "Führungskräfte verstehen die Grundprinzipien von KI und können fundierte Entscheidungen zu KI-Investitionen treffen.",
                    "sort_order": 1,
                },
                {
                    "key":        "ki_komp_q2",
                    "text":       "Mitarbeitende werden aktiv für den Einsatz von KI-Tools befähigt.",
                    "sort_order": 2,
                },
                {
                    "key":        "ki_komp_q3",
                    "text":       "KI-Experimente und schnelles Lernen werden in unserer Unternehmenskultur gefördert.",
                    "sort_order": 3,
                },
            ],
        },
        {
            "key":        "ethik_compliance",
            "label":      "KI-Ethik & Compliance",
            "weight":     "1.25",
            "sort_order": 4,
            "questions": [
                {
                    "key":        "ethik_q1",
                    "text":       "Risiken durch KI-Einsatz (Bias, Transparenz, Datenschutz) werden systematisch bewertet.",
                    "sort_order": 1,
                },
                {
                    "key":        "ethik_q2",
                    "text":       "Unser Unternehmen ist vorbereitet auf die Anforderungen des EU AI Acts.",
                    "sort_order": 2,
                },
                {
                    "key":        "ethik_q3",
                    "text":       "Ethische Leitlinien für den KI-Einsatz sind dokumentiert und kommuniziert.",
                    "sort_order": 3,
                },
            ],
        },
    ],

    "maturity_levels": [
        {
            "key":         "einsteiger",
            "label":       "KI-Einsteiger",
            "description": (
                "Ihre Organisation steht am Beginn der KI-Reise. "
                "Grundlegende Strukturen für KI-Strategie und Datenkompetenz fehlen noch. "
                "Jetzt ist der richtige Zeitpunkt, die Basis zu legen."
            ),
            "color":       "#DC2626",
            "icon":        "seedling",
            "pct_min":     0,
            "pct_max":     24,
            "sort_order":  1,
        },
        {
            "key":         "lernender",
            "label":       "KI-Lernender",
            "description": (
                "Erste KI-Initiativen sind gestartet, aber noch nicht systematisch verankert. "
                "Daten-Infrastruktur und Governance-Strukturen sind im Aufbau."
            ),
            "color":       "#EA580C",
            "icon":        "book-open",
            "pct_min":     25,
            "pct_max":     49,
            "sort_order":  2,
        },
        {
            "key":         "fortgeschrittener",
            "label":       "Fortgeschrittener",
            "description": (
                "KI ist in wesentlichen Bereichen operativ im Einsatz. "
                "Governance und Kompetenzen sind entwickelt, aber noch nicht vollständig integriert."
            ),
            "color":       "#CA8A04",
            "icon":        "trending-up",
            "pct_min":     50,
            "pct_max":     74,
            "sort_order":  3,
        },
        {
            "key":         "souveraen",
            "label":       "KI-Souverän",
            "description": (
                "Ihre Organisation gestaltet KI-Transformation aktiv und souverän. "
                "Strategie, Daten, Kompetenz und Compliance sind systematisch verankert."
            ),
            "color":       "#16A34A",
            "icon":        "shield-check",
            "pct_min":     75,
            "pct_max":     100,
            "sort_order":  4,
        },
    ],

    # Empfehlungen (Beispiel, vollständige Liste durch Fachexperten)
    "recommendations": [
        {
            "dimension_key":      "strategie_governance",
            "title":              "KI-Strategie entwickeln",
            "description":        "Entwickeln Sie eine dokumentierte KI-Strategie mit klaren Zielen und Verantwortlichkeiten.",
            "threshold_below_pct": 50,
            "priority":           1,
            "external_url":       "https://learn.iil.de/kurse/ki-strategie-grundlagen",
        },
        {
            "dimension_key":      "daten_kompetenz",
            "title":              "Data Literacy Programm",
            "description":        "Befähigen Sie Ihre Mitarbeitenden im sicheren Umgang mit Daten.",
            "threshold_below_pct": 60,
            "priority":           2,
        },
        {
            "dimension_key":      "ethik_compliance",
            "title":              "EU AI Act Vorbereitung",
            "description":        "Analysieren Sie Ihre KI-Systeme gegen die Anforderungen des EU AI Acts.",
            "threshold_below_pct": 75,
            "priority":           1,
        },
    ],
}
