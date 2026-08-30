# -*- coding: utf-8 -*-
"""Rezepte der freigegebenen Verbandsquellen (M5, D-089).

NUR Quellen, die Justin ausdrücklich freigegeben hat (Ablauf: benennen →
Testrun 50 → Freigabe → Vollabzug). Der Quellen-Katalog mit Ampel-Prüfung
(robots.txt, AGB-Auslese-Verbote) liegt im CRM-Repo unter
docs/lead-maschine/QUELLEN-KATALOG.md — TABU-Quellen werden hier NIE
eingetragen.

Felder je Rezept:
  zielgruppe        Berufs-Label (= branche im CRM)
  start_urls        Einstiegsseiten (HTML) oder PDF-Links
  typ               'html' | 'pdf'
  unterseiten       Regex — Links auf derselben Domain, denen zusätzlich
                    gefolgt wird (z. B. Landkreis-Unterseiten); None = keine
  max_seiten        harte Obergrenze an Seitenabrufen je Lauf (Drossel 1/s)
"""

QUELLEN = {
    "verband_hebammen_bb": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.hebammen-brandenburg.de/hebammensuche.html"],
        "typ": "html",
        "unterseiten": r"hebammen(?:suche|liste)?[\w\-]*\.html",
        "max_seiten": 25,
    },
    "verband_hebammen_saar": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.hebammenverband-saar.de/familien/hebammensuche"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 5,
    },
    "verband_gfg_doulas": {
        "zielgruppe": "Doula",
        # Übersichtsseite verlinkt die aktuellen Kontaktlisten-PDFs —
        # der Konnektor folgt allen PDF-Links, deren Name 'doula' enthält.
        "start_urls": ["https://gfg-bv.de/begleitung-oder-kursleitung-finden/"],
        "typ": "pdf",
        "unterseiten": r"doula[\w\-]*\.pdf",
        "max_seiten": 10,
    },
    "verband_dvct_coaches": {
        "zielgruppe": "Life-/Business-Coach",
        # Paginierte Liste (~43 Seiten) — der Konnektor folgt den
        # Weiter-/Seiten-Links automatisch (rel=next, ?page=, /page/).
        "start_urls": ["https://www.dvct.de/dev/coach"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 50,
    },
    "verband_bfd_kosmetik": {
        "zielgruppe": "Kosmetikerin",
        "start_urls": ["https://bfd-ev.com/kosmetikinstute/"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 5,
    },
    "verband_vnn_lehrer": {
        "zielgruppe": "Lehrer (selbstständig)",
        "start_urls": ["https://www.nachhilfeschulen.org/mitgliederuebersicht/"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 30,
    },
}

# Branche-Schlüssel (branchen.py) → passende Verbandsquellen
BRANCHE_ZU_QUELLEN = {
    "hebammen": ["verband_hebammen_bb", "verband_hebammen_saar"],
    "doulas": ["verband_gfg_doulas"],
    "business_coaches": ["verband_dvct_coaches"],
    "kosmetikerin": ["verband_bfd_kosmetik"],
    "lehrer_selbststaendig": ["verband_vnn_lehrer"],
}
