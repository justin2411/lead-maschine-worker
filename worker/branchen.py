# -*- coding: utf-8 -*-
"""Branchen-Katalog für den OSM-Extract-Suchlauf (M2, E-2 vom 30.08.2026).

Jede Branche definiert:
  beruf        – Anzeigename, geht als `branche` an die App
  tag_filter   – Liste von {key: value}-Sätzen; ein Objekt passt, wenn
                 EINER der Sätze vollständig erfüllt ist
  name_regex   – zusätzlich (ODER): Objekt passt, wenn der Name matcht
                 (nur innerhalb der POI-Vorauswahl, siehe osm_extract.py)
  name_sperre  – Objekt fliegt raus, wenn der Name matcht (Institutionen,
                 Ketten, falsche Treffer)

Die Tags sind ein KALIBRIER-START — nach dem ersten Testlauf (50er-
Stichprobe, Freigabe-Ablauf) werden sie nachgezogen. OSM liefert Masse,
nicht Qualität (Recherche §2) — die Qualität entsteht in der
Anreicherungs-Kette (M3).
"""

BRANCHEN = {
    "tagesmuetter": {
        "beruf": "Tagesmutter",
        "tag_filter": [{"amenity": "childcare"}],
        "name_regex": r"tagesmutter|tagesvater|tagespflege|tageskinder",
        "name_sperre": r"kita|kindergarten|krippe|hort|e\.\s?v\.|ggmbh|awo|drk|caritas|diakonie|johanniter",
    },
    "hebammen": {
        "beruf": "Hebamme",
        "tag_filter": [{"healthcare": "midwife"}],
        "name_regex": r"hebamme",
        "name_sperre": r"klinik|krankenhaus|geburtshaus\s+team|zentrum\s+für",
    },
    "business_coaches": {
        "beruf": "Life-/Business-Coach",
        "tag_filter": [{"office": "coaching"}],
        "name_regex": r"business\s?coach|life\s?coach|karrierecoach|systemische[rs]?\s+coach",
        "name_sperre": r"akademie|institut|ausbildung|icf|dbvc|gmbh\s*&\s*co",
    },
    "yogalehrer": {
        "beruf": "Yogalehrer",
        "tag_filter": [{"sport": "yoga"}, {"shop": "yoga"}],
        "name_regex": r"yoga|pilates",
        "name_sperre": r"fitnessstudio|mcfit|clever\s?fit|fitx|kette|franchise",
    },
    "ernaehrungsberater": {
        "beruf": "Ernährungsberater",
        "tag_filter": [{"healthcare": "nutrition_counselling"}],
        "name_regex": r"ern[äa]hrungsberat|di[äa]tberat",
        "name_sperre": r"klinik|krankenhaus|krankenkasse",
    },
    "doulas": {
        "beruf": "Doula",
        "tag_filter": [],
        "name_regex": r"doula",
        "name_sperre": r"verband|netzwerk|ausbildung",
    },
    "heilpraktiker": {
        "beruf": "Heilpraktiker",
        "tag_filter": [{"healthcare": "alternative"}],
        "name_regex": r"heilpraktik|naturheilpraxis",
        "name_sperre": r"klinik|zentrum\s+für|gemeinschaftspraxis|schule|akademie",
    },
    "kosmetikerin": {
        "beruf": "Kosmetikerin",
        "tag_filter": [{"shop": "beauty"}, {"shop": "cosmetics"}],
        "name_regex": r"kosmetikstudio|kosmetikerin|fu(ß|ss)pflege",
        "name_sperre": r"douglas|rossmann|dm[-\s]|müller|parfümerie|kette",
    },
    "lehrer_selbststaendig": {
        "beruf": "Lehrer (selbstständig)",
        "tag_filter": [{"amenity": "music_school"}, {"amenity": "language_school"}, {"amenity": "prep_school"}],
        "name_regex": r"nachhilfe|musikunterricht|klavierunterricht|gitarrenunterricht|sprachunterricht",
        "name_sperre": r"volkshochschule|vhs|goethe[-\s]institut|berlitz|schülerhilfe|studienkreis|stadt|gemeinde",
    },
    "pflegefachkraefte": {
        "beruf": "Pflegefachkraft",
        "tag_filter": [{"social_facility": "ambulatory_care"}],
        "name_regex": r"ambulante\s+pflege|pflegedienst|hauskrankenpflege|pflegeberat",
        "name_sperre": r"caritas|diakonie|awo|drk|malteser|johanniter|gmbh\s*&\s*co|heim|residenz|stift",
    },
}
