"""
iil_learnfw/seeds/dsgvo_readiness.py

Seed-Daten: DSGVO/GDPR-Readiness Assessment (5 Dimensionen, Likert-Skala).

Datenschutz-Grundverordnung (EU 2016/679).
Prüft die organisatorische DSGVO-Compliance in 5 Kernbereichen.

Zielgruppe: Verantwortliche und Auftragsverarbeiter.
"""
from __future__ import annotations

SEED: dict = {
    "key":              "dsgvo_readiness",
    "title":            "DSGVO-Readiness Check",
    "slug":             "dsgvo-readiness",
    "description": (
        "Wie gut erfüllt Ihre Organisation die DSGVO-Anforderungen? "
        "Dieser Check bewertet Ihren Datenschutz-Reifegrad in 5 Dimensionen."
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
    "reassessment_months": 12,
    "retention_days":      730,

    "dimensions": [
        {
            "key":        "organisation_governance",
            "label":      "Organisation & Governance",
            "weight":     "1.00",
            "sort_order": 1,
            "questions": [
                {
                    "key":        "org_q1",
                    "text":       "Ein Datenschutzbeauftragter (DSB) ist benannt und der Aufsichtsbehörde gemeldet.",
                    "help_text":  "Art. 37-39 DSGVO. Pflicht ab 20 Personen mit regelmäßiger DV.",
                    "sort_order": 1,
                },
                {
                    "key":        "org_q2",
                    "text":       "Es gibt eine dokumentierte Datenschutzrichtlinie/-strategie.",
                    "sort_order": 2,
                },
                {
                    "key":        "org_q3",
                    "text":       "Datenschutz-Verantwortlichkeiten sind klar definiert und kommuniziert.",
                    "sort_order": 3,
                },
                {
                    "key":        "org_q4",
                    "text":       "Regelmäßige Datenschutz-Schulungen finden für alle Mitarbeitenden statt.",
                    "sort_order": 4,
                },
            ],
        },
        {
            "key":        "verzeichnis_dokumentation",
            "label":      "Verarbeitungsverzeichnis & Dokumentation",
            "weight":     "1.00",
            "sort_order": 2,
            "questions": [
                {
                    "key":        "vvt_q1",
                    "text":       "Ein vollständiges Verzeichnis von Verarbeitungstätigkeiten (VVT) existiert (Art. 30).",
                    "sort_order": 1,
                },
                {
                    "key":        "vvt_q2",
                    "text":       "Alle Verarbeitungstätigkeiten haben eine dokumentierte Rechtsgrundlage.",
                    "sort_order": 2,
                },
                {
                    "key":        "vvt_q3",
                    "text":       "Auftragsverarbeitungsverträge (AVV) sind mit allen Dienstleistern geschlossen.",
                    "sort_order": 3,
                },
                {
                    "key":        "vvt_q4",
                    "text":       "Datenschutz-Folgenabschätzungen (DSFA) werden bei Bedarf durchgeführt (Art. 35).",
                    "sort_order": 4,
                },
            ],
        },
        {
            "key":        "betroffenenrechte",
            "label":      "Betroffenenrechte",
            "weight":     "1.00",
            "sort_order": 3,
            "questions": [
                {
                    "key":        "br_q1",
                    "text":       "Prozesse zur Bearbeitung von Auskunftsanfragen (Art. 15) sind etabliert.",
                    "sort_order": 1,
                },
                {
                    "key":        "br_q2",
                    "text":       "Das Recht auf Löschung (Art. 17) kann technisch und organisatorisch umgesetzt werden.",
                    "sort_order": 2,
                },
                {
                    "key":        "br_q3",
                    "text":       "Datenportabilität (Art. 20) ist für relevante Verarbeitungen möglich.",
                    "sort_order": 3,
                },
                {
                    "key":        "br_q4",
                    "text":       "Betroffenenanfragen werden innerhalb eines Monats beantwortet.",
                    "sort_order": 4,
                },
            ],
        },
        {
            "key":        "technisch_organisatorisch",
            "label":      "Technisch-Organisatorische Maßnahmen (TOM)",
            "weight":     "1.00",
            "sort_order": 4,
            "questions": [
                {
                    "key":        "tom_q1",
                    "text":       "Zugriffskontrollen stellen sicher, dass nur Berechtigte auf personenbezogene Daten zugreifen.",
                    "sort_order": 1,
                },
                {
                    "key":        "tom_q2",
                    "text":       "Personenbezogene Daten werden verschlüsselt gespeichert und übertragen.",
                    "sort_order": 2,
                },
                {
                    "key":        "tom_q3",
                    "text":       "Löschkonzepte mit definierten Aufbewahrungsfristen sind implementiert.",
                    "sort_order": 3,
                },
                {
                    "key":        "tom_q4",
                    "text":       "Privacy by Design und Privacy by Default sind in der Softwareentwicklung verankert (Art. 25).",
                    "sort_order": 4,
                },
            ],
        },
        {
            "key":        "datenpannen_meldung",
            "label":      "Datenpannen & Meldepflichten",
            "weight":     "1.00",
            "sort_order": 5,
            "questions": [
                {
                    "key":        "dp_q1",
                    "text":       "Ein Prozess zur Erkennung und Bewertung von Datenpannen existiert.",
                    "sort_order": 1,
                },
                {
                    "key":        "dp_q2",
                    "text":       "Datenpannen können innerhalb von 72 Stunden an die Aufsichtsbehörde gemeldet werden (Art. 33).",
                    "sort_order": 2,
                },
                {
                    "key":        "dp_q3",
                    "text":       "Betroffene werden bei hohem Risiko unverzüglich benachrichtigt (Art. 34).",
                    "sort_order": 3,
                },
            ],
        },
    ],

    "maturity_levels": [
        {
            "key":         "kritisch",
            "label":       "Kritisch",
            "description": "Erhebliche DSGVO-Lücken. Risiko von Bußgeldern und Reputationsschäden.",
            "color":       "#EF4444",
            "icon":        "alert-triangle",
            "pct_min":     0,
            "pct_max":     25,
            "sort_order":  1,
        },
        {
            "key":         "grundlagen",
            "label":       "Grundlagen",
            "description": "Basismaßnahmen vorhanden, aber systematische DSGVO-Umsetzung fehlt.",
            "color":       "#F97316",
            "icon":        "alert-circle",
            "pct_min":     26,
            "pct_max":     50,
            "sort_order":  2,
        },
        {
            "key":         "fortgeschritten",
            "label":       "Fortgeschritten",
            "description": "Gute DSGVO-Compliance. Einzelne Bereiche benötigen Nachbesserung.",
            "color":       "#EAB308",
            "icon":        "shield",
            "pct_min":     51,
            "pct_max":     75,
            "sort_order":  3,
        },
        {
            "key":         "konform",
            "label":       "DSGVO-konform",
            "description": "Umfassende DSGVO-Compliance. Empfehlung: jährliche Re-Assessments.",
            "color":       "#22C55E",
            "icon":        "shield-check",
            "pct_min":     76,
            "pct_max":     100,
            "sort_order":  4,
        },
    ],

    "recommendations": [
        {
            "dimension_key":     "organisation_governance",
            "threshold_below_pct": 50,
            "title":             "Datenschutz-Organisation aufbauen",
            "description":       "Benennen Sie einen DSB, erstellen Sie eine Datenschutzrichtlinie und schulen Sie Mitarbeitende.",
            "priority":          1,
        },
        {
            "dimension_key":     "verzeichnis_dokumentation",
            "threshold_below_pct": 50,
            "title":             "Verarbeitungsverzeichnis vervollständigen",
            "description":       "Erstellen Sie ein vollständiges VVT nach Art. 30 und prüfen Sie Rechtsgrundlagen + AVVs.",
            "priority":          2,
        },
        {
            "dimension_key":     "betroffenenrechte",
            "threshold_below_pct": 50,
            "title":             "Betroffenenrechte-Prozesse implementieren",
            "description":       "Definieren Sie Prozesse für Auskunft, Löschung, Berichtigung und Datenportabilität.",
            "priority":          3,
        },
        {
            "dimension_key":     "technisch_organisatorisch",
            "threshold_below_pct": 50,
            "title":             "TOM-Konzept erstellen und umsetzen",
            "description":       "Implementieren Sie Zugriffskontrollen, Verschlüsselung, Löschkonzepte und Privacy by Design.",
            "priority":          4,
        },
        {
            "dimension_key":     "datenpannen_meldung",
            "threshold_below_pct": 50,
            "title":             "Datenpannen-Meldeprozess einrichten",
            "description":       "Art. 33/34 DSGVO fordern 72h-Meldung an Aufsichtsbehörde. Definieren Sie Meldewege und üben Sie den Prozess.",
            "priority":          5,
        },
    ],
}
