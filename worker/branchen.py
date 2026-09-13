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
        "name_sperre": r"klinik|zentrum\s+für|gemeinschaftspraxis|schule|akademie|gmbh|\bug\b|zentrum|reha\b|kollegen|partner|praxisgemeinschaft|krankenhaus|mvz|institut|verein|ambulan|förder|sozialstation|caritas|diakonie|\bawo\b|\bdrk\b|malteser|johanniter",
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


# ── Erweiterung 12.09.2026 (Claude, 100.000-Leads-Auftrag) ──────────────
# Zielgruppen für den Karten-Lauf (D-092) mit hohem Handy-Anteil: Solo-
# Dienstleister ohne Ladengeschäft/Praxis, oft nur per Mobilnummer
# erreichbar. Beruf-Labels sind bestehende CRM-Berufe (lib/pool-nachschub.ts),
# wo es sie gibt. tag_filter leer = nur Karten-Lauf, kein OSM-Scan.
# Die Solo-Sperre (D-099) hängt automatisch an jeder name_sperre.
SOLO_SPERRE = (
    r"gmbh|\bug\b|\bag\b|\bkg\b|\bohg\b|zentrum|reha\b|kollegen|partner|"
    r"praxisgemeinschaft|gemeinschaftspraxis|klinik|krankenhaus|\bmvz\b|institut|"
    r"akademie|verein|e\.\s?v\.|ambulan|förder|sozialstation|caritas|diakonie|"
    r"\bawo\b|\bdrk\b|malteser|johanniter|stadt\b|gemeinde|landkreis|kreis\b"
)

KARTEN_ZIELGRUPPEN = {
    # key: (Beruf-Label, name_regex, zusätzliche Sperre)
    "personal_trainer":   ("Personal Trainer", r"personal\s?train|fitness\s?coach|fitness\s?trainer", r"mcfit|clever\s?fit|fitx|fitness\s?first|john\s?reed|kieser|injoy|easyfitness|bodystreet"),
    "pilates":            ("Yogalehrer", r"pilates|yoga", r"mcfit|clever\s?fit|fitx|fitness\s?first"),
    "nageldesign":        ("Nageldesignerin", r"nagel|nail", r""),
    "wimpern_pmu":        ("Kosmetikerin", r"wimpern|lash|permanent|microblading|brow", r"douglas|rossmann"),
    "mobile_kosmetik":    ("Kosmetikerin", r"kosmetik|beauty", r"douglas|rossmann|parfümerie"),
    "make_up_artist":     ("Make-up-Artist", r"make-?up|visagist|styling", r"douglas|rossmann"),
    "mobile_fusspflege":  ("Fußpflegerin", r"fu(ß|ss)pflege|podolog", r"sanitätshaus"),
    "mobile_friseure":    ("Friseur", r"friseur|fris[öo]r|haar|hair", r"klier|essanelle|super\s?cut|hair\s?express|hairkiller|top\s?hair"),
    "barbiere":           ("Friseur", r"barber|barbier|herrenfriseur", r"klier|essanelle|super\s?cut"),
    "masseure":           ("Masseur", r"massage|masseur", r"thai\s?massage\s?gmbh|wellness\s?hotel|\bspa\b|therme|hotel"),
    "hochzeitsplaner":    ("Hochzeitsplaner", r"hochzeit|wedding", r""),
    "freie_redner":       ("Freier Redner", r"redner|rednerin|trauredner|zeremonie", r"standesamt|kirche|pfarr"),
    "trauerredner":       ("Trauerredner", r"trauerredner|trauerrednerin|trauerbegleit", r"bestattung|bestatter|friedhof|kirche|pfarr"),
    "hochzeitsfotografen":("Hochzeitsfotograf", r"fotograf|photograph", r"cewe|pixum|picture\s?people|studioline|\bdm\b|rossmann"),
    "djs":                ("DJ", r"\bdj\b|discjockey", r"agentur\s?gmbh|club|diskothek|disco\b"),
    "musiklehrer":        ("Musiklehrer", r"unterricht|musiklehrer|klavier|gitarre|gesang", r"musikschule\s+der\s+stadt|städtisch|kreismusikschule|vhs|volkshochschule|yamaha|music\s?store|thomann"),
    "nachhilfe":          ("Nachhilfelehrer", r"nachhilfe|lernhilfe|einzelunterricht", r"schülerhilfe|studienkreis|abacus|lernstudio\s?barbarossa|mini-?lernkreis|vhs|volkshochschule"),
    "sprachlehrer":       ("Sprachlehrer", r"sprach|deutsch|englisch|spanisch|französisch|italienisch", r"berlitz|inlingua|vhs|volkshochschule|goethe|sprachschule\s?gmbh|wall\s?street"),
    "lerntherapeuten":    ("Lerntherapeut", r"lerntherap|legasthenie|dyskalkulie", r"schülerhilfe|studienkreis"),
    "hp_psychotherapie":  ("Heilpraktiker für Psychotherapie", r"psychotherap|heilpraktik|psycholog", r"psychologische[r]?\s+psychotherapeut|ärztlich|kassensitz|\bdr\.\s?med|facharzt|psychiater"),
    "hypnose":            ("Hypnosecoach", r"hypnos", r"schule|ausbildung"),
    "mentalcoaches":      ("Mentalcoach", r"mental|coach", r"schule|ausbildung|\bicf\b|dbvc"),
    "karrierecoaches":    ("Life-/Business-Coach", r"coach|beratung|bewerbung", r"schule|ausbildung|\bicf\b|dbvc|arbeitsagentur|jobcenter|ihk"),
    "stillberaterinnen":  ("Stillberaterin", r"still|laktation|ibclc", r"klinik|krankenhaus"),
    "trageberatung":      ("Trageberaterin", r"trage|babymassage|baby", r"klinik|krankenhaus|familienzentrum|familienbildung"),
    "hebammen_praxis":    ("Hebamme", r"hebamme|wochenbett|geburt", r"klinik|krankenhaus|geburtshaus\s+team"),
    "kindertagespflege":  ("Tagesmutter", r"tagespflege|tagesmutter|tagesvater|tageskind|tagesmama", r"kita|kindergarten|krippe|hort|ggmbh|elterninitiative"),
    "abnehmcoach":        ("Ernährungsberater", r"ern[äa]hrung|abnehm|di[äa]t|gewicht", r"klinik|krankenhaus|krankenkasse|weight\s?watchers|apotheke"),
    "chiropraktiker":     ("Chiropraktiker", r"chiropra", r"klinik|orthopäd|\bdr\.\s?med|facharzt"),
    "tierphysio":         ("Tierphysiotherapeut", r"tierphysio|hundephysio|pferdephysio|tierosteo", r"tierklinik|tierarzt|tierärzt"),
    "hundesitter":        ("Tierpfleger", r"hundesitter|gassi|dogwalk|dog\s?walk|hundebetreuung|tierbetreuung|katzensitter|hundepension|hundetagesstätte", r"tierheim|tierschutz|gnadenhof"),
    "reitlehrer":         ("Reitlehrer", r"reit|pferd|horse", r"reiterhof\s?gmbh|reitverein|reit-\s?und\s?fahrverein|gestüt\s?gmbh|landgestüt"),
    "hufschmiede":        ("Hufschmied", r"huf", r"tierklinik"),
    "kfz_gutachter":      ("Kfz-Gutachter", r"gutachter|sachverständig|kfz", r"dekra|tüv|gtü|küs|autohaus|werkstatt\s?gmbh"),
    "uebersetzer":        ("Übersetzer", r"übersetz|dolmetsch|translat", r"gmbh|agentur\s?gmbh|lingua\s?gmbh"),
    "webdesigner":        ("IT-Freelancer", r"web|design|digital|medien", r"gmbh|agentur\s?gmbh"),
    "grafikdesigner":     ("Grafikdesigner", r"grafik|design|illustrat", r"gmbh|agentur\s?gmbh|druckerei"),
    "virtuelle_assistenz":("Virtuelle Assistentin", r"assisten|büroservice|backoffice", r"gmbh"),
    "gartenpflege":       ("Gärtner", r"garten|grün|baum", r"galabau\s?gmbh|stadt|friedhof|gartencenter|baumarkt|dehner|obi|bauhaus"),
    "hausmeisterservice": ("Hausmeisterservice", r"hausmeister|haus-?service|kleinreparatur", r"gmbh|facility|wohnungsbau|hausverwaltung"),
    "reinigungsservice":  ("Reinigungskraft", r"reinigung|putz|haushaltshilfe|fensterputz", r"gebäudereinigung\s?gmbh|facility|gmbh|helpling|book\s?a\s?tiger"),
    "seniorenassistenz":  ("Seniorenassistent", r"senior|alltagsbegleit|betreuung", r"pflegedienst|caritas|diakonie|awo|drk|gmbh|24\s?stunden|heim|residenz|stift"),
    "schneiderinnen":     ("Schneiderin", r"schneider|näh|änderung", r"gmbh|c&a|h&m|textilreinigung"),
    "piercer":            ("Tätowiererin", r"piercing|tattoo", r"gmbh|supply|laser|entfernung"),
    # ── Welle 13 (12.09.2026, 19:20): mehr Breite — Justin: „nicht nur Friseure, wir brauchen viele Zielgruppen"
    "mobile_physio":      ("Physiotherapeut", r"physio|krankengymnast|hausbesuch", r"klinik|reha|zentrum|\bmvz\b"),
    "mobile_ergo":        ("Ergotherapeut", r"ergo|hausbesuch", r"klinik|reha|zentrum"),
    "mobile_logo":        ("Logopäde", r"logop|sprach|hausbesuch", r"klinik|reha|zentrum"),
    "kinderbetreuung":    ("Tagesmutter", r"kinderbetreu|nanny|babysit|tagesmutter", r"kita|kindergarten|agentur|gmbh|betreut\.de|sitly"),
    "tanzlehrer":         ("Tanzlehrer", r"tanz", r"adtv\s?gmbh|tanzschule\s?gmbh|verein|club\b"),
    "kampfsport":         ("Kampfsporttrainer", r"kampfsport|karate|judo|taekwondo|krav|boxen|kickbox|selbstverteidigung", r"verein|e\.\s?v\.|gmbh"),
    "schwimmlehrer":      ("Schwimmlehrer", r"schwimm|aqua", r"verein|dlrg|stadt|bad\b|bäder|therme"),
    "golf_tennis":        ("Sporttrainer", r"golf|tennis|trainer|pro\b", r"verein|club\b|gmbh|golfplatz|anlage"),
    "ernaehrung_kinder":  ("Ernährungsberater", r"ern[äa]hrung|kinder|schwanger|still", r"klinik|krankenkasse"),
    "psych_berater":      ("Psychologischer Berater", r"psycholog|berat|lebensberat|krise", r"psychotherapeut|\bdr\.\s?med|facharzt|kassensitz|klinik"),
    "paarberater":        ("Familienberater", r"paar|ehe|familie|beziehung|systemisch", r"caritas|diakonie|pro\s?familia|stadt|kirche|pfarr"),
    "mediatoren":         ("Mediator", r"mediat|konflikt", r"anwalt|rechtsanwalt|kanzlei|notar"),
    "videografen":        ("Hochzeitsfotograf", r"video|film|drohne|imagefilm", r"gmbh|studio\s?gmbh|sender|tv\b"),
    "texter":             ("Grafikdesigner", r"text|content|lektor|redakt|social\s?media|marketing", r"gmbh|agentur\s?gmbh|verlag"),
    "illustratoren":      ("Grafikdesigner", r"illustrat|zeichn|künstler|kunst|malerin?\b", r"galerie\s?gmbh|museum|schule"),
    "buchhalter":         ("Buchhalter", r"buchhalt|buchführ|lohnbüro|bürodienst", r"steuerberat|wirtschaftsprüf|kanzlei|gmbh|datev"),
    "ordnungscoach":      ("Ordnungscoach", r"ordnung|aufräum|organis|feng\s?shui|entrümpel", r"gmbh|entsorgung|container"),
    "fahrradmechaniker":  ("Fahrradmechaniker", r"fahrrad|bike|rad\b|zweirad", r"gmbh|filiale|decathlon|fahrrad\s?xxl|lucky\s?bike|bike\s?discount"),
    "autopflege":         ("Kfz-Aufbereiter", r"aufbereit|autopflege|lackdoktor|smart\s?repair|folier", r"autohaus|gmbh|werkstatt\s?gmbh|kette"),
    "schluesseldienst":   ("Schlüsseldienst", r"schlüssel|schloss|aufsperr", r"gmbh|24h\s?gmbh|notdienst\s?gmbh|sicherheitstechnik\s?gmbh"),
    "umzugshelfer":       ("Umzugshelfer", r"umzug|transport|möbeltaxi|kleintransport", r"gmbh|spedition|logistik|kg\b"),
    "kinderfotografen":   ("Fotograf", r"fotograf|newborn|baby|kinder|familien", r"cewe|pixum|picture\s?people|studioline|\bdm\b|rossmann"),
    "tierfotografen":     ("Fotograf", r"fotograf|tier|hund|pferd", r"cewe|pixum|picture\s?people|studioline"),
    "musiker":            ("Musiker", r"musik|sänger|band|gesang|pianist|gitarrist|saxophon|geiger", r"agentur\s?gmbh|gmbh|verein|orchester|philharmon|theater|oper"),
    "kinderanimation":    ("Eventkünstler", r"zauber|clown|animation|kinderfest|ballon|entertainer|künstler", r"agentur\s?gmbh|gmbh|verein"),
    "floristen":          ("Florist", r"florist|blumen|floral", r"gmbh|blume\s?2000|blumen\s?risse|fleurop|filiale|gartencenter"),
    "catering_solo":      ("Caterer", r"catering|privatkoch|kochkurs|mietkoch|foodtruck", r"gmbh|kg\b|kantine|mensa|hotel|restaurant\s?gmbh"),
    "kindersport":        ("Sporttrainer", r"kinder|sport|turnen|bewegung|ballett|zirkus", r"verein|e\.\s?v\.|gmbh|stadt"),
    "tierpsychologen":    ("Tierheilpraktiker", r"tierpsycholog|verhaltensberat|hundeernährung|katzen|tierkommunikat", r"tierklinik|tierarzt|tierärzt|tierheim"),
    "pferdetrainer":      ("Reitlehrer", r"pferd|reit|horse|dressur|spring|bereiter", r"reiterhof\s?gmbh|reitverein|gestüt\s?gmbh|landgestüt|verein"),
    # Handwerk je Gewerk (Label bleibt „Handwerksmeister")
    "handwerk_elektro":   ("Handwerksmeister", r"elektro|elektrik", r"stadtwerke|innung|baumarkt|obi|bauhaus|hornbach|toom|energieversorg|netze"),
    "handwerk_maler":     ("Handwerksmeister", r"maler|lackier", r"innung|baumarkt|obi|bauhaus|hornbach|toom|brillux|caparol"),
    "handwerk_fliesen":   ("Handwerksmeister", r"fliesen|platten", r"innung|baumarkt|obi|bauhaus|hornbach|toom|fliesenhandel|fliesen\s?discount"),
    "handwerk_dach":      ("Handwerksmeister", r"dach", r"innung|baumarkt|obi|bauhaus|hornbach|toom|dachbaustoffe"),
    "handwerk_shk":       ("Handwerksmeister", r"sanitär|heizung|installat|klempner|gas|wasser", r"stadtwerke|innung|baumarkt|obi|bauhaus|hornbach|toom|energieversorg|viessmann|vaillant|buderus"),
    "handwerk_tischler":  ("Handwerksmeister", r"tischler|schreiner|holz|möbel", r"innung|baumarkt|obi|bauhaus|hornbach|toom|ikea|möbelhaus|xxxlutz|roller|poco"),
    "handwerk_raum":      ("Handwerksmeister", r"raumausstatt|polster|boden|parkett|tapezier", r"innung|baumarkt|obi|bauhaus|hornbach|toom|ikea|möbelhaus"),
    # Welle 20 (13.09.2026): 70 weitere Solo-Gruppen, Katalog war abgefahren
    "fahrlehrer": ("Fahrlehrer", r"fahrschule|fahrlehrer", r"gmbh|academy\s?gmbh|verkehrsinstitut"),
    "energieberater": ("Energieberater", r"energieberat|energieausweis|gebäudeenergie", r"stadtwerke|gmbh|verbraucherzentrale|ag\b"),
    "bausachverstaendige": ("Bausachverständiger", r"sachverständ|gutachter|bauschaden|schimmel", r"tüv|dekra|gmbh|ag\b|institut"),
    "architekten_solo": ("Architekt", r"architekt|planung|bauplanung", r"gmbh|ag\b|partner|partnerschaft|mbb|bda\s?gmbh|planungsgesellschaft"),
    "innenarchitekten": ("Innenarchitekt", r"innenarchitekt|interior|raumgestalt|einrichtungsberat", r"gmbh|möbelhaus|ikea|xxxlutz"),
    "statiker": ("Statiker", r"statik|tragwerk|bauingenieur", r"gmbh|ag\b|partner|ingenieurgesellschaft"),
    "schornsteinfeger": ("Schornsteinfeger", r"schornsteinfeger|kaminkehrer|bezirksschornstein", r"innung|gmbh"),
    "handwerk_zimmerer": ("Handwerksmeister", r"zimmer|holzbau|dachstuhl", r"innung|baumarkt|obi|bauhaus|hornbach|toom|gmbh|fertighaus"),
    "handwerk_maurer": ("Handwerksmeister", r"maurer|bau\b|bauunternehm|rohbau|putz", r"innung|baumarkt|gmbh|ag\b|bauträger|generalunternehm"),
    "handwerk_stuck": ("Handwerksmeister", r"stuck|putz|trockenbau|gips", r"innung|baumarkt|gmbh|knauf|rigips"),
    "handwerk_boden": ("Handwerksmeister", r"boden|parkett|estrich|laminat|teppich", r"innung|baumarkt|obi|bauhaus|hornbach|toom|gmbh|kette"),
    "handwerk_metall": ("Handwerksmeister", r"metall|schlosser|schweiß|stahl|schmied", r"innung|gmbh|ag\b|stahlwerk|kg\b"),
    "handwerk_glaser": ("Handwerksmeister", r"glas|fenster|rolll?aden|verglas", r"innung|gmbh|ag\b|velux|schüco|kette|fensterwerk"),
    "kuechenmonteure": ("Möbelmonteur", r"küche|möbel|montage|monteur|aufbau", r"ikea|xxxlutz|roller|poco|höffner|gmbh|küchenstudio\s?gmbh"),
    "entruempler": ("Entrümpler", r"entrümpel|haushaltsauflösung|entsorg|räumung", r"gmbh|container|stadtreinigung|kg\b|recycling"),
    "fensterputzer": ("Fensterputzer", r"fenster|glasrein|gebäuderein", r"gmbh|kg\b|dussmann|piepenbrock|wisag|kette"),
    "baumpfleger": ("Baumpfleger", r"baum|fällung|klettern|arborist", r"gmbh|forst|stadt|landkreis|kg\b"),
    "pflasterer": ("Pflasterer", r"pflaster|garten\s?und\s?landschaft|gala|zaun|terrasse", r"gmbh|kg\b|baumarkt|obi|bauhaus"),
    "schaedlingsbekaempfer": ("Schädlingsbekämpfer", r"schädling|kammerjäger|taubenabwehr|wespen", r"gmbh|rentokil|anticimex|kg\b"),
    "pv_monteure": ("Solarteur", r"solar|photovoltaik|pv\b|wärmepumpe|energie", r"gmbh|ag\b|stadtwerke|enpal|1komma5|zolar|kg\b|e\.on|eon|vattenfall"),
    "pc_notdienst": ("IT-Freelancer", r"pc|computer|it-|edv|notdienst|laptop", r"gmbh|media\s?markt|saturn|cyberport|kg\b"),
    "handyreparatur": ("Handyreparatur", r"handy|smartphone|iphone|display|repair", r"gmbh|media\s?markt|saturn|telekom|vodafone|o2|kette|apple"),
    "polsterer": ("Polsterer", r"polster|sattler|leder|aufpolster", r"gmbh|möbelhaus|ikea|xxxlutz"),
    "schuhmacher": ("Schuhmacher", r"schuh|schlüssel|absatz|orthopädie", r"mister\s?minit|gmbh|deichmann|kette"),
    "uhrmacher": ("Uhrmacher", r"uhr|schmuck|goldschmied", r"christ|gmbh|juwelier\s?gmbh|kette"),
    "foodtrucks": ("Foodtruck-Betreiber", r"food|truck|imbiss|catering|streetfood", r"gmbh|kg\b|franchise|mcdonald|burger\s?king|subway"),
    "privatkoeche": ("Privatkoch", r"koch|köchin|kochkurs|catering|dinner", r"gmbh|restaurant\s?gmbh|hotel|kette"),
    "mobile_barkeeper": ("Barkeeper", r"bar|cocktail|barkeeper|mobile\s?bar", r"gmbh|hotel|club\s?gmbh|kette"),
    "babysitter": ("Babysitter", r"babysit|kinderbetreu|nanny|leihoma", r"gmbh|kita|kindergarten|verein|e\.\s?v\."),
    "alltagsbegleiter": ("Alltagsbegleiter", r"alltag|betreuung|senioren|begleit|hauswirtschaft", r"gmbh|pflegedienst|caritas|diakonie|awo|drk|verein"),
    "trauerbegleiter": ("Trauerbegleiter", r"trauer|abschied|sterbe|hospiz", r"bestattung|gmbh|hospiz\s?verein|verein|kirche"),
    "reiki_shiatsu": ("Heilpraktiker", r"reiki|shiatsu|ayurveda|klang|kinesiolog|energet|aroma", r"gmbh|hotel|therme|spa\s?gmbh"),
    "astrologen": ("Astrologe", r"astrolog|kartenleg|tarot|medium|hellseh|numerolog", r"gmbh|hotline|0900"),
    "feng_shui": ("Feng-Shui-Berater", r"feng|shui|raumenergie|geomant", r"gmbh"),
    "tauchlehrer": ("Tauchlehrer", r"tauch|dive|scuba|surf|kite|segel|wassersport", r"gmbh|verein|e\.\s?v\.|padi\s?gmbh"),
    "bergfuehrer": ("Bergführer", r"berg|wander|kletter|outdoor|guide", r"gmbh|dav\b|alpenverein|verein|e\.\s?v\."),
    "stadtfuehrer": ("Stadtführer", r"stadtführ|gästeführ|tour|erlebnis", r"gmbh|tourismus\s?gmbh|stadt\b|tourist-?info"),
    "reisebuero_solo": ("Reiseberater", r"reise|urlaub|travel", r"tui|dertour|gmbh|ag\b|kette|alltours|fti|lufthansa"),
    "social_media_freelancer": ("Social-Media-Manager", r"social|media|content|marketing|online", r"gmbh|agentur\s?gmbh|ag\b|kg\b"),
    "seo_freelancer": ("Online-Marketing-Berater", r"seo|sea|ads|marketing|online|web", r"gmbh|agentur\s?gmbh|ag\b|kg\b"),
    "pr_berater": ("PR-Berater", r"pr\b|presse|kommunikation|public", r"gmbh|agentur\s?gmbh|ag\b"),
    "unternehmensberater_solo": ("Unternehmensberater", r"berat|consult|strategie|interim", r"gmbh|ag\b|kpmg|pwc|deloitte|ey\b|mckinsey|bcg|roland\s?berger|accenture|partner"),
    "datenschutzbeauftragte": ("Datenschutzbeauftragter", r"datenschutz|dsgvo|compliance|it-sicherheit", r"gmbh|ag\b|tüv|dekra"),
    "arbeitssicherheit": ("Fachkraft für Arbeitssicherheit", r"arbeitssicher|sifa|brandschutz|sicherheits", r"gmbh|tüv|dekra|bg\s?bau|berufsgenossenschaft|ag\b"),
    "dozenten": ("Dozent", r"dozent|trainer|seminar|schulung|training", r"gmbh|ihk|vhs|volkshochschule|akademie|institut|ag\b"),
    "stimmtrainer": ("Gesangslehrer", r"stimm|gesang|vocal|sprech|rhetorik", r"gmbh|musikschule\s?gmbh|akademie"),
    "malschulen": ("Kunstlehrer", r"mal|kunst|atelier|zeichen|töpfer|keramik", r"gmbh|museum|volkshochschule|vhs|verein"),
    "kuenstler": ("Künstler", r"künstler|atelier|malerei|bildhauer|skulptur", r"gmbh|galerie\s?gmbh|museum|verein"),
    "werbetechniker": ("Werbetechniker", r"werbetechnik|beschriftung|folier|schilder|plott", r"gmbh|kg\b|kette"),
    "restauratoren": ("Restaurator", r"restaur|antik|möbelrestaur|kunstrestaur", r"gmbh|museum|denkmalamt"),
    "immobilienbewerter": ("Immobiliengutachter", r"immobilienbewert|wertgutacht|gutachter|sachverständ", r"gmbh|sparkasse|bank|ag\b|tüv|dekra"),
    "drohnenpiloten": ("Drohnenpilot", r"drohne|luftaufnahme|luftbild|copter|uav", r"gmbh|dji|ag\b"),
    "dellentechniker": ("Dellentechniker", r"dellen|hagel|smart\s?repair|beulen|lackdoktor", r"autohaus|gmbh|kette|carglass"),
    "autoglaser": ("Autoglaser", r"autoglas|scheiben|steinschlag|windschutz", r"carglass|gmbh|autohaus|kette|junited|wintec"),
    "mobile_reifendienst": ("Reifendienst", r"reifen|rad\b|räder|felgen", r"gmbh|pneuhage|euromaster|vergölst|atu|a\.t\.u|reifen\s?direkt|kette"),
    "motorradwerkstatt": ("Motorradmechaniker", r"motorrad|moto|bike|zweirad|roller", r"gmbh|honda|yamaha|bmw|kawasaki|ktm|polo|louis|kette"),
    "wohnmobilservice": ("Wohnmobiltechniker", r"wohnmobil|caravan|camping|wohnwagen", r"gmbh|hymer|dethleffs|kette|ag\b"),
    "kurierdienste": ("Kurierfahrer", r"kurier|bote|express|transport|lieferservice", r"gmbh|dhl|ups|hermes|dpd|gls|fedex|kg\b|logistik"),
    "chauffeure": ("Chauffeur", r"chauffeur|limousine|fahrservice|mietwagen|taxi", r"gmbh|sixt|europcar|uber|kette|zentrale"),
    "moebeltaxi": ("Möbeltaxi-Fahrer", r"möbeltaxi|transport|umzug|kleintransport", r"gmbh|spedition|logistik|kg\b"),
    "alleinunterhalter": ("Alleinunterhalter", r"alleinunterhalter|entertainer|zauber|comedy|sänger|band", r"gmbh|agentur\s?gmbh|theater"),
    "tontechniker": ("Tontechniker", r"ton|licht|event|veranstaltungstechnik|beschallung", r"gmbh|kg\b|ag\b"),
    "naehservice": ("Schneiderin", r"näh|schneider|änderung|stoff|textil", r"gmbh|kette"),
    "imker": ("Imker", r"imker|honig|biene", r"gmbh|verein|e\.\s?v\."),
    "hofladen_solo": ("Direktvermarkter", r"hof|landwirt|bauer|direktvermarkt|hofladen", r"gmbh|kg\b|genossenschaft|edeka|rewe"),
    "winzer": ("Winzer", r"wein|winzer|weingut", r"gmbh|kg\b|genossenschaft|ag\b"),
    "brauer": ("Brauer", r"brau|bier|destill|brenner", r"gmbh|kg\b|ag\b|radeberger|bitburger|krombacher|warsteiner"),
}

for _key, (_beruf, _regex, _sperre) in KARTEN_ZIELGRUPPEN.items():
    if _key in BRANCHEN:
        continue
    BRANCHEN[_key] = {
        "beruf": _beruf,
        "tag_filter": [],
        "name_regex": _regex,
        "name_sperre": (f"{_sperre}|" if _sperre else "") + SOLO_SPERRE,
    }
