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
        "tag_filter": [{"amenity": "childcare"}, {"amenity": "kindergarten", "kindergarten": "childcare"}, {"social_facility": "childcare"}],
        "name_regex": r"tagesmutter|tagesvater|tagesmama|tagespapa|tagespflege|kindertagespflege|gro(ß|ss)tagespflege|tageskind|tageskinder|tagesfamilie",
        "name_sperre": r"kita|kindergarten|krippe|hort|e\.\s?v\.|ggmbh|awo|drk|caritas|diakonie|johanniter|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "hebammen": {
        "beruf": "Hebamme",
        "tag_filter": [{"healthcare": "midwife"}],
        "name_regex": r"hebamme|geburtshaus|wochenbett|geburtsvorbereitung|r[üu]ckbildung",
        "name_sperre": r"klinik|krankenhaus|geburtshaus\s+team|zentrum\s+für|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "business_coaches": {
        "beruf": "Life-/Business-Coach",
        "tag_filter": [{"office": "coaching"}],
        "name_regex": r"business\s?coach|life\s?coach|karrierecoach|systemische[rs]?\s+coach",
        "name_sperre": r"akademie|institut|ausbildung|icf|dbvc|gmbh\s*&\s*co|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "yogalehrer": {
        "beruf": "Yogalehrer",
        "tag_filter": [{"sport": "yoga"}, {"shop": "yoga"}, {"leisure": "fitness_centre", "sport": "yoga"}, {"sport": "pilates"}],
        "name_regex": r"yoga|pilates|yogini|yogaraum|yogaloft|yogaschule|yogastudio|yogalehrer",
        "name_sperre": r"fitnessstudio|mcfit|clever\s?fit|fitx|kette|franchise|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "ernaehrungsberater": {
        "beruf": "Ernährungsberater",
        "tag_filter": [{"healthcare": "nutrition_counselling"}, {"office": "nutrition"}, {"healthcare": "dietitian"}],
        "name_regex": r"ern[äa]hrungsberat|ern[äa]hrungscoach|ern[äa]hrungstherap|di[äa]tberat|abnehmcoach|ern[äa]hrungspraxis",
        "name_sperre": r"klinik|krankenhaus|krankenkasse|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "doulas": {
        "beruf": "Doula",
        "tag_filter": [],
        "name_regex": r"doula|geburtsbegleit",
        "name_sperre": r"verband|netzwerk|ausbildung|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "heilpraktiker": {
        "beruf": "Heilpraktiker",
        "tag_filter": [{"healthcare": "alternative"}, {"healthcare": "alternative", "healthcare:speciality": "naturopathy"}, {"shop": "herbalist"}],
        "name_regex": r"heilpraktik|naturheilpraxis|naturheilkunde|hom[öo]opath|praxis\s+f[üu]r\s+naturheil",
        "name_sperre": r"klinik|zentrum\s+für|gemeinschaftspraxis|schule|akademie",
    },
    "kosmetikerin": {
        "beruf": "Kosmetikerin",
        "tag_filter": [{"shop": "beauty"}, {"shop": "cosmetics"}],
        "name_regex": r"kosmetikstudio|kosmetikerin|fu(ß|ss)pflege",
        "name_sperre": r"douglas|rossmann|dm[-\s]|müller|parfümerie|kette|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "lehrer_selbststaendig": {
        "beruf": "Lehrer (selbstständig)",
        "tag_filter": [{"amenity": "music_school"}, {"amenity": "language_school"}, {"amenity": "prep_school"}],
        "name_regex": r"nachhilfe|musikunterricht|klavierunterricht|gitarrenunterricht|sprachunterricht",
        "name_sperre": r"volkshochschule|vhs|goethe[-\s]institut|berlitz|schülerhilfe|studienkreis|stadt|gemeinde|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "pflegefachkraefte": {
        "beruf": "Pflegefachkraft",
        "tag_filter": [{"social_facility": "ambulatory_care"}],
        "name_regex": r"ambulante\s+pflege|pflegedienst|hauskrankenpflege|pflegeberat",
        "name_sperre": r"caritas|diakonie|awo|drk|malteser|johanniter|gmbh\s*&\s*co|heim|residenz|stift|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    # Solo-Regel (Justin, 06.09.2026): jede name_sperre enthält zusätzlich die
    # Nicht-Solo-Marker (GmbH, Zentrum, Reha, Kollegen/Partner, Gemeinschafts-
    # praxis, Klinik, MVZ, Institut, Verein, Wohlfahrtsverbände …).
    # ── Erweiterung 06.09.2026 (Claude, 5.000-Leads-Auftrag): kostenfreie
    # OSM-Zielgruppen, Beruf-Labels = bestehende CRM-Berufe. Sperren zielen
    # auf Ketten/Kapitalgesellschaften/Institutionen (D-035: nur Solo).
    "friseure": {
        "beruf": "Friseur",
        "tag_filter": [{"shop": "hairdresser"}],
        "name_regex": r"friseur|fris[öo]r|haarstudio|hairstyl|coiffeur|barber",
        "name_sperre": r"klier|essanelle|super\s?cut|supercut|hair\s?express|cut\s?(&|and)\s?color|hairkiller|top\s?hair|hairfree|gmbh|kette|franchise|schule|akademie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "physiotherapeuten": {
        "beruf": "Physiotherapeut",
        "tag_filter": [{"healthcare": "physiotherapist"}],
        "name_regex": r"physiotherap|krankengymnast",
        "name_sperre": r"klinik|krankenhaus|reha[-\s]?zentrum|gmbh|zentrum\s+für|therapiezentrum|versorgungszentrum|\bmvz\b|caritas|diakonie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "ergotherapeuten": {
        "beruf": "Ergotherapeut",
        "tag_filter": [{"healthcare": "occupational_therapist"}],
        "name_regex": r"ergotherap",
        "name_sperre": r"klinik|krankenhaus|gmbh|zentrum\s+für|therapiezentrum|\bmvz\b|lebenshilfe|caritas|diakonie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "logopaeden": {
        "beruf": "Logopäde",
        "tag_filter": [{"healthcare": "speech_therapist"}],
        "name_regex": r"logop[äa]d|sprachtherap|stimmtherap",
        "name_sperre": r"klinik|krankenhaus|gmbh|zentrum\s+für|therapiezentrum|\bmvz\b|caritas|diakonie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "osteopathen": {
        "beruf": "Osteopath",
        "tag_filter": [],
        "name_regex": r"osteopath",
        "name_sperre": r"klinik|gmbh|zentrum\s+für|schule|akademie|institut|verband|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "fusspflege": {
        "beruf": "Fußpflegerin",
        "tag_filter": [{"healthcare": "podiatrist"}],
        "name_regex": r"fu(ß|ss)pflege|podolog",
        "name_sperre": r"klinik|gmbh|sanitätshaus|schule|akademie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "taetowierer": {
        "beruf": "Tätowiererin",
        "tag_filter": [{"shop": "tattoo"}],
        "name_regex": r"tattoo|t[äa]tow",
        "name_sperre": r"gmbh|supply|convention|entfernung|laser|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "fotografen": {
        "beruf": "Fotograf",
        "tag_filter": [{"craft": "photographer"}],
        "name_regex": r"fotograf|photograph|fotostudio",
        "name_sperre": r"cewe|pixum|picture\s?people|foto\s?koch|\bdm\b|rossmann|müller|gmbh|studioline|fotofix|automat|schule|akademie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "goldschmiede": {
        "beruf": "Goldschmied",
        "tag_filter": [{"craft": "jeweller"}, {"craft": "goldsmith"}],
        "name_regex": r"goldschmied|schmuckdesign|schmuckatelier|schmuckwerkstatt",
        "name_sperre": r"\bchrist\b|swarovski|pandora|thomas\s?sabo|bijou|gmbh|degussa|pro\s?aurum|ankauf|kette|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "hundefriseure": {
        "beruf": "Hundefriseur",
        "tag_filter": [{"shop": "pet_grooming"}],
        "name_regex": r"hundesalon|hundefriseur|fellpflege|hundepflege|grooming",
        "name_sperre": r"fressnapf|zoo\s?&\s?co|zookauf|gmbh|tierklinik|tierarzt|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "hundetrainer": {
        "beruf": "Hundetrainer",
        "tag_filter": [],
        "name_regex": r"hundeschule|hundetrain|hundeerzieh",
        "name_sperre": r"verein|e\.\s?v\.|gmbh|tierheim|tierschutz|akademie|ausbildung|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "tierheilpraktiker": {
        "beruf": "Tierheilpraktiker",
        "tag_filter": [],
        "name_regex": r"tierheilprak|tierphysio|tierosteopath|hundephysio|pferdephysio",
        "name_sperre": r"tierklinik|tierarzt|tierärzt|gmbh|schule|akademie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "immobilienmakler": {
        "beruf": "Immobilienmakler",
        "tag_filter": [{"office": "estate_agent"}],
        "name_regex": r"immobilienmakler",
        "name_sperre": r"gmbh|\bag\b|\bkg\b|engel\s?&\s?völkers|von\s?poll|re/?max|sparkasse|volksbank|\blbs\b|postbank|planethome|homeday|mcmakler|dahler|vonovia|wohnungsbau|hausverwaltung|bauträger|baugesellschaft|immobilien24|\bbank\b|genossenschaft|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
    "handwerksmeister": {
        "beruf": "Handwerksmeister",
        "tag_filter": [{"craft": "electrician"}, {"craft": "plumber"}, {"craft": "hvac"}, {"craft": "roofer"}, {"craft": "painter"}, {"craft": "carpenter"}, {"craft": "tiler"}, {"craft": "joiner"}],
        "name_regex": r"meisterbetrieb|elektromeister|malermeister|dachdeckermeister|installateurmeister",
        "name_sperre": r"gmbh|\bag\b|&\s?co|\bkg\b|\bohg\b|\bug\b|stadtwerke|e\.\s?v\.|innung|bauunternehm|baugesellschaft|energieversorg|filiale|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|mvz|institut|akademie|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
    },
}
