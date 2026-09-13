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
    # D-138 (13.09.2026, Justin: "Hebammen-Listen ja, Leads in der Rueckhand halten"): oeffentliche
    # Hebammenlisten aus dem Quellen-Scout (robots ok, kein Nutzungsverbot). Stand: Testlauf 50 je Quelle,
    # Vollabzug erst nach Justins Freigabe je Quelle.
    "verband_hebammen_heidenheim": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://kliniken-heidenheim.de/klinikum-wAssets/docs/frauenheilkunde-und-geburtshilfe/Hebammenliste_2023.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_mkk": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.mkk.de/media/resources/pdf/mkk_de_1/buergerservice_1/lebenslagen_1/gesundheit_1/57_3_gesundheit/berufsaufsicht/hebammen/Hebammenliste_Homepage.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_konstanz": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.lrakn.de/site/lrakn-frueheHilfen/get/params_E1054755970/3269316/Hebammen%20im%20Landkreis%20Konstanz_Stand%20September%202023.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_giessen": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.lkgi.de/wp-content/uploads/2025/04/Hebammenliste-LKGI.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_hildesheim": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.landkreishildesheim.de/PDF/Hebammenliste_Landkreis_Hildesheim.PDF?ObjSvrID=3711&ObjID=976&ObjLa=1&Ext=PDF&WTR=1&_ts=1765802007"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_marburg": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.profamilia.de/fileadmin/beratungsstellen/marburg/Hebammen-Liste_aktuell.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_traunstein": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.aekv-traunstein.de/images/stories/Startseite/pdf/Hebammenverzeichnis_%C3%B6ffentlich_TS_BGL.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_leverkusen": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.klinikum-lev.de/media/10_kliniken-zentren/mutter-kind/hebammenliste.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_limburg": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.landkreis-limburg-weilburg.de/fileadmin/landkreis/downloads/gesundheit/Hebammen-Liste-18.pdf"],
        "typ": "pdf",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_kissingen": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.beratungswegweiser-kg.de/familien/fruehe-hilfen/liste/"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_hassfurt": {
        "zielgruppe": "Hebamme",
        "start_urls": ["https://www.schwanger-in-hassfurt.de/schwangerschaft-geburt/hebammenliste/"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 3,
    },
    "verband_hebammen_hamburg_geburt": {
        "zielgruppe": "Hebamme",
        "start_urls": ["http://www.geburt-in-hamburg.de/geburt-in-hamburg-2/hebammen/"],
        "typ": "html",
        "unterseiten": None,
        "max_seiten": 3,
    },
}

# Branche-Schlüssel (branchen.py) → passende Verbandsquellen
BRANCHE_ZU_QUELLEN = {
    "hebammen": ["verband_hebammen_bb", "verband_hebammen_saar",
                 "verband_hebammen_heidenheim",
                 "verband_hebammen_mkk",
                 "verband_hebammen_konstanz",
                 "verband_hebammen_giessen",
                 "verband_hebammen_hildesheim",
                 "verband_hebammen_marburg",
                 "verband_hebammen_traunstein",
                 "verband_hebammen_leverkusen",
                 "verband_hebammen_limburg",
                 "verband_hebammen_kissingen",
                 "verband_hebammen_hassfurt",
                 "verband_hebammen_hamburg_geburt",],
    "doulas": ["verband_gfg_doulas"],
    "business_coaches": ["verband_dvct_coaches"],
    "kosmetikerin": ["verband_bfd_kosmetik"],
    "lehrer_selbststaendig": ["verband_vnn_lehrer"],
}
