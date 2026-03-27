"""
iil_learnfw/seeds/nis2_readiness.py

Seed-Daten: NIS2-Readiness Assessment (5 Dimensionen, Likert-Skala).

NIS2-Richtlinie (EU 2022/2555) — Umsetzungsfrist: 17. Oktober 2024.
Prüft die organisatorische Vorbereitung auf NIS2-Anforderungen.

Zielgruppe: Betreiber wesentlicher und wichtiger Einrichtungen.
"""
from __future__ import annotations

SEED: dict = {
    "key":              "nis2_readiness",
    "title":            "NIS2-Readiness Check",
    "slug":             "nis2-readiness",
    "description": (
        "Wie gut ist Ihre Organisation auf die NIS2-Richtlinie vorbereitet? "
        "Dieser Check bewertet Ihren Reifegrad in 5 Dimensionen."
    ),
    "scoring_strategy": "likert",
    "scale_min":        1,
    "scale_max":        4,
    "scale_labels": [
        {"value": 1, "label": "Nicht umgesetzt"},
        {"value": 2, "label": "Teilweise umgesetzt"},
        {"value": 3, "label": "Weitgehend umgesetzt"},
        {"value": 4, "label": "Vollständig umgesetzt"},
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
            "key":        "governance_risiko",
            "label":      "Governance & Risikomanagement",
            "weight":     "1.00",
            "sort_order": 1,
            "questions": [
                {
                    "key":        "gov_q1",
                    "text":       "Es existiert ein dokumentiertes Cybersicherheits-Managementsystem (ISMS/CSMS).",
                    "help_text":  "Z.B. ISO 27001, BSI IT-Grundschutz oder vergleichbar.",
                    "sort_order": 1,
                },
                {
                    "key":        "gov_q2",
                    "text":       "Die Geschäftsleitung trägt nachweislich Verantwortung für die Cybersicherheit (Art. 20 NIS2).",
                    "sort_order": 2,
                },
                {
                    "key":        "gov_q3",
                    "text":       "Regelmäßige Risikoanalysen werden durchgeführt und dokumentiert.",
                    "sort_order": 3,
                },
                {
                    "key":        "gov_q4",
                    "text":       "Es gibt ein Budget und dedizierte Ressourcen für Cybersicherheit.",
                    "sort_order": 4,
                },
            ],
        },
        {
            "key":        "incident_management",
            "label":      "Incident Management & Meldepflichten",
            "weight":     "1.00",
            "sort_order": 2,
            "questions": [
                {
                    "key":        "inc_q1",
                    "text":       "Es gibt einen dokumentierten Incident-Response-Plan mit definierten Rollen.",
                    "sort_order": 1,
                },
                {
                    "key":        "inc_q2",
                    "text":       "Sicherheitsvorfälle können innerhalb von 24h an die zuständige Behörde gemeldet werden (Art. 23 NIS2).",
                    "sort_order": 2,
                },
                {
                    "key":        "inc_q3",
                    "text":       "Incident-Response-Übungen werden mindestens jährlich durchgeführt.",
                    "sort_order": 3,
                },
                {
                    "key":        "inc_q4",
                    "text":       "Die Meldewege an BSI/ENISA sind bekannt und getestet.",
                    "sort_order": 4,
                },
            ],
        },
        {
            "key":        "supply_chain",
            "label":      "Lieferketten-Sicherheit",
            "weight":     "1.00",
            "sort_order": 3,
            "questions": [
                {
                    "key":        "sc_q1",
                    "text":       "Kritische Lieferanten und Dienstleister sind identifiziert und bewertet.",
                    "sort_order": 1,
                },
                {
                    "key":        "sc_q2",
                    "text":       "Cybersicherheitsanforderungen sind vertraglich mit Lieferanten vereinbart.",
                    "sort_order": 2,
                },
                {
                    "key":        "sc_q3",
                    "text":       "Es gibt einen Prozess zur regelmäßigen Überprüfung der Lieferanten-Sicherheit.",
                    "sort_order": 3,
                },
            ],
        },
        {
            "key":        "technische_massnahmen",
            "label":      "Technische Sicherheitsmaßnahmen",
            "weight":     "1.00",
            "sort_order": 4,
            "questions": [
                {
                    "key":        "tech_q1",
                    "text":       "Multi-Faktor-Authentifizierung ist für alle kritischen Systeme implementiert.",
                    "sort_order": 1,
                },
                {
                    "key":        "tech_q2",
                    "text":       "Netzwerksegmentierung trennt kritische von unkritischen Systemen.",
                    "sort_order": 2,
                },
                {
                    "key":        "tech_q3",
                    "text":       "Verschlüsselung wird für Daten in Transit und at Rest eingesetzt.",
                    "sort_order": 3,
                },
                {
                    "key":        "tech_q4",
                    "text":       "Schwachstellen-Management (Patching, Scanning) ist etabliert.",
                    "sort_order": 4,
                },
                {
                    "key":        "tech_q5",
                    "text":       "Business-Continuity- und Disaster-Recovery-Pläne sind dokumentiert und getestet.",
                    "sort_order": 5,
                },
            ],
        },
        {
            "key":        "awareness_schulung",
            "label":      "Awareness & Schulung",
            "weight":     "1.00",
            "sort_order": 5,
            "questions": [
                {
                    "key":        "awa_q1",
                    "text":       "Mitarbeitende erhalten regelmäßig Cybersicherheits-Schulungen.",
                    "sort_order": 1,
                },
                {
                    "key":        "awa_q2",
                    "text":       "Die Geschäftsleitung nimmt an Cybersicherheits-Schulungen teil (Art. 20 Abs. 2 NIS2).",
                    "sort_order": 2,
                },
                {
                    "key":        "awa_q3",
                    "text":       "Phishing-Simulationen oder ähnliche Awareness-Tests werden durchgeführt.",
                    "sort_order": 3,
                },
            ],
        },
    ],

    "maturity_levels": [
        {
            "key":         "kritisch",
            "label":       "Kritisch",
            "description": "Erhebliche Lücken bei der NIS2-Vorbereitung. Sofortige Maßnahmen erforderlich.",
            "color":       "#EF4444",
            "icon":        "alert-triangle",
            "pct_min":     0,
            "pct_max":     25,
            "sort_order":  1,
        },
        {
            "key":         "grundlagen",
            "label":       "Grundlagen",
            "description": "Erste Maßnahmen vorhanden, aber systematische Umsetzung fehlt.",
            "color":       "#F97316",
            "icon":        "alert-circle",
            "pct_min":     26,
            "pct_max":     50,
            "sort_order":  2,
        },
        {
            "key":         "fortgeschritten",
            "label":       "Fortgeschritten",
            "description": "Gute Vorbereitung. Einzelne Bereiche benötigen noch Nachbesserung.",
            "color":       "#EAB308",
            "icon":        "shield",
            "pct_min":     51,
            "pct_max":     75,
            "sort_order":  3,
        },
        {
            "key":         "konform",
            "label":       "NIS2-konform",
            "description": "Umfassende NIS2-Vorbereitung. Regelmäßige Re-Assessments empfohlen.",
            "color":       "#22C55E",
            "icon":        "shield-check",
            "pct_min":     76,
            "pct_max":     100,
            "sort_order":  4,
        },
    ],

    "recommendations": [
        {
            "dimension_key":     "governance_risiko",
            "threshold_below_pct": 50,
            "title":             "ISMS/CSMS aufbauen",
            "description":       "Implementieren Sie ein Cybersicherheits-Managementsystem nach ISO 27001 oder BSI IT-Grundschutz.",
            "priority":          1,
        },
        {
            "dimension_key":     "incident_management",
            "threshold_below_pct": 50,
            "title":             "Incident-Response-Plan erstellen",
            "description":       "Erstellen Sie einen Incident-Response-Plan mit 24h-Meldepflicht und definieren Sie Meldewege an BSI.",
            "priority":          2,
        },
        {
            "dimension_key":     "supply_chain",
            "threshold_below_pct": 50,
            "title":             "Lieferanten-Risikobewertung durchführen",
            "description":       "Identifizieren Sie kritische Lieferanten und vereinbaren Sie Cybersicherheitsanforderungen vertraglich.",
            "priority":          3,
        },
        {
            "dimension_key":     "technische_massnahmen",
            "threshold_below_pct": 50,
            "title":             "Technische Basishygiene sicherstellen",
            "description":       "Implementieren Sie MFA, Netzwerksegmentierung, Verschlüsselung und Schwachstellen-Management.",
            "priority":          4,
        },
        {
            "dimension_key":     "awareness_schulung",
            "threshold_below_pct": 50,
            "title":             "Cybersicherheits-Schulungsprogramm starten",
            "description":       "NIS2 Art. 20 fordert Schulungen für Geschäftsleitung und Mitarbeitende. Starten Sie ein regelmäßiges Programm.",
            "priority":          5,
        },
    ],
}
