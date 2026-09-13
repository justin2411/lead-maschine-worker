#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brave-Suche als Fabrik-2-Quelle (D-091) — nutzt das bestehende
Brave-API-Kontingent der Fabrik 1 (bezahlte Such-API, kein Auslesen
fremder Seiten gegen deren Regeln).

Ablauf je Branche: Suchanfragen „<Begriff> <Stadt>" über die größten
Städte → organische Treffer → Portale/Bekanntes raus → je neuer Domain
Impressum nachschlagen (leadkern, KI optional) → Treffer MIT Name/
Telefon/E-Mail an die App melden. Die M3-Kette übernimmt danach den
Feinschliff (bzw. Sparschaltung, wenn schon alles da ist).

Kontingent-Schutz: FABRIK2_BRAVE_MAX_ANFRAGEN je Lauf (Default 100),
1 Anfrage/Sekunde, jede Anfrage wird gezählt und im Förderband gemeldet
(brave_anfragen) — die Übersicht zeigt den Monatsverbrauch beider
Fabriken. Env: BRAVE_API_KEY (gleicher Schlüssel wie Fabrik 1).
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from leadkern import normalisierung, vorfilter, web

from anreicherung import App, ki_abfrage, KI_CALLS, drossle
from verbaende import hole_roh, html_zu_text

USER_AGENT = "LeadMaschine2-Suchlauf/1.0 (+https://github.com/justin2411/lead-maschine-worker)"
PAKET_GROESSE = 50

BEGRIFFE = {
    "tagesmuetter": "Tagesmutter Kindertagespflege",
    "hebammen": "Hebamme freiberuflich",
    "business_coaches": "Business Coach",
    "yogalehrer": "Yogalehrerin Yogastudio",
    "ernaehrungsberater": "Ernährungsberatung selbstständig",
    "doulas": "Doula Geburtsbegleitung",
    "heilpraktiker": "Heilpraktikerin Naturheilpraxis",
    "kosmetikerin": "Kosmetikstudio",
    "lehrer_selbststaendig": "Musikunterricht Nachhilfe privat",
    "pflegefachkraefte": "ambulanter Pflegedienst inhabergeführt",
    # Erweiterung 06.09.2026 (Claude, 5.000-Leads-Auftrag)
    "friseure": "Friseursalon inhabergeführt",
    "physiotherapeuten": "Physiotherapie Praxis",
    "ergotherapeuten": "Ergotherapie Praxis",
    "logopaeden": "Logopädie Praxis",
    "osteopathen": "Osteopathie Praxis",
    "fusspflege": "Fußpflege Podologie",
    "taetowierer": "Tattoostudio",
    "fotografen": "Fotograf Fotostudio",
    "goldschmiede": "Goldschmied Schmuckwerkstatt",
    "hundefriseure": "Hundefriseur Hundesalon",
    "hundetrainer": "Hundetrainer Hundeschule",
    "tierheilpraktiker": "Tierheilpraktiker",
    "immobilienmakler": "Immobilienmakler",
    "handwerksmeister": "Meisterbetrieb Handwerk",
    # Erweiterung 12.09.2026 (Claude, 100.000-Leads-Auftrag): Karten-Zielgruppen
    # mit hohem Handy-Anteil (Definition in branchen.KARTEN_ZIELGRUPPEN)
    "personal_trainer": "Personal Trainer",
    "pilates": "Pilates Studio",
    "nageldesign": "Nagelstudio Nageldesign",
    "wimpern_pmu": "Wimpernverlängerung Permanent Make-up",
    "mobile_kosmetik": "mobile Kosmetikerin Hausbesuch",
    "make_up_artist": "Make-up Artist Brautstyling",
    "mobile_fusspflege": "mobile Fußpflege Hausbesuch",
    "mobile_friseure": "mobiler Friseur Hausbesuch",
    "barbiere": "Barbershop Barbier",
    "masseure": "Massagepraxis mobile Massage",
    "hochzeitsplaner": "Hochzeitsplaner Weddingplaner",
    "freie_redner": "Freier Trauredner Hochzeitsredner",
    "trauerredner": "Trauerredner",
    "hochzeitsfotografen": "Hochzeitsfotograf",
    "djs": "Hochzeits DJ Event DJ",
    "musiklehrer": "Klavierunterricht Gitarrenunterricht privat",
    "nachhilfe": "Nachhilfe privat Einzelunterricht",
    "sprachlehrer": "Sprachlehrer Privatunterricht",
    "lerntherapeuten": "Lerntherapie Praxis",
    "hp_psychotherapie": "Heilpraktiker für Psychotherapie",
    "hypnose": "Hypnose Praxis Hypnosetherapie",
    "mentalcoaches": "Mentalcoach Mentaltraining",
    "karrierecoaches": "Karrierecoach Bewerbungscoaching",
    "stillberaterinnen": "Stillberaterin IBCLC",
    "trageberatung": "Trageberatung Babymassage Kurs",
    "hebammen_praxis": "Hebammenpraxis Wochenbettbetreuung",
    "kindertagespflege": "Kindertagespflege Tagespflegeperson",
    "abnehmcoach": "Abnehmcoach Ernährungscoach",
    "chiropraktiker": "Chiropraktiker Praxis",
    "tierphysio": "Tierphysiotherapie Hundephysiotherapie",
    "hundesitter": "Hundesitter Gassi-Service Dogwalker",
    "reitlehrer": "mobiler Reitlehrer Reitunterricht",
    "hufschmiede": "Hufschmied Hufbeschlag",
    "kfz_gutachter": "Kfz Gutachter Sachverständiger",
    "uebersetzer": "Übersetzer Dolmetscher beeidigt",
    "webdesigner": "Webdesigner Freelancer",
    "grafikdesigner": "Grafikdesigner freiberuflich",
    "virtuelle_assistenz": "Virtuelle Assistentin",
    "gartenpflege": "Gartenpflege Gartenservice",
    "hausmeisterservice": "Hausmeisterservice",
    "reinigungsservice": "Haushaltshilfe Reinigungsservice privat",
    "seniorenassistenz": "Seniorenbetreuung Alltagsbegleitung privat",
    "schneiderinnen": "Änderungsschneiderei Maßschneiderei",
    "piercer": "Piercingstudio",
    # Welle 13 (12.09.2026): mehr Breite
    "mobile_physio": "mobile Physiotherapie Hausbesuche",
    "mobile_ergo": "mobile Ergotherapie Hausbesuch",
    "mobile_logo": "mobile Logopädie Hausbesuch",
    "kinderbetreuung": "Kinderbetreuung privat Nanny",
    "tanzlehrer": "Tanzlehrer Privatunterricht",
    "kampfsport": "Kampfsporttrainer Selbstverteidigung Kurs",
    "schwimmlehrer": "Schwimmlehrer privat Schwimmkurs",
    "golf_tennis": "Tennistrainer Golflehrer privat",
    "ernaehrung_kinder": "Ernährungsberatung Kinder Schwangere",
    "psych_berater": "Psychologische Beratung Lebensberatung",
    "paarberater": "Paarberatung Eheberatung",
    "mediatoren": "Mediator Mediation",
    "videografen": "Videograf Hochzeitsvideo Imagefilm",
    "texter": "Texter Content freiberuflich",
    "illustratoren": "Illustrator Künstlerin Atelier",
    "buchhalter": "selbstständige Buchhalterin Buchhaltungsservice",
    "ordnungscoach": "Ordnungscoach Aufräumcoach",
    "fahrradmechaniker": "mobiler Fahrradmechaniker Fahrradwerkstatt",
    "autopflege": "Fahrzeugaufbereitung Autopflege Smart Repair",
    "schluesseldienst": "Schlüsseldienst",
    "umzugshelfer": "Umzugshelfer Möbeltaxi Kleintransporte",
    "kinderfotografen": "Newborn Fotografin Familienfotograf",
    "tierfotografen": "Tierfotograf Hundefotografie",
    "musiker": "Sängerin Hochzeit Musiker Live",
    "kinderanimation": "Kinderzauberer Kinderanimation Clown",
    "floristen": "Florist Blumenladen inhabergeführt",
    "catering_solo": "Privatkoch Catering Kochkurs",
    "kindersport": "Kinderturnen Ballettschule privat",
    "tierpsychologen": "Tierpsychologe Hundeverhaltensberatung",
    "pferdetrainer": "Pferdetrainer Bereiter",
    "handwerk_elektro": "Elektriker Meisterbetrieb",
    "handwerk_maler": "Malerbetrieb Malermeister",
    "handwerk_fliesen": "Fliesenleger",
    "handwerk_dach": "Dachdecker Meisterbetrieb",
    "handwerk_shk": "Sanitär Heizung Installateur",
    "handwerk_tischler": "Tischlerei Schreinerei",
    "handwerk_raum": "Raumausstatter Polsterei",
    # Welle 20
    "fahrlehrer": "Fahrschule Fahrlehrer",
    "versicherungsmakler": "Versicherungsmakler unabhängig",
    "finanzberater": "Finanzberater Honorarberater",
    "baufinanzierer": "Baufinanzierung Vermittler",
    "energieberater": "Energieberater Gebäudeenergieberater",
    "bausachverstaendige": "Bausachverständiger Baugutachter",
    "architekten_solo": "Architekt Architekturbüro Einzelunternehmen",
    "innenarchitekten": "Innenarchitekt Einrichtungsberatung",
    "statiker": "Statiker Tragwerksplaner",
    "schornsteinfeger": "Schornsteinfeger Bezirksschornsteinfeger",
    "handwerk_zimmerer": "Zimmerei Holzbau Zimmerermeister",
    "handwerk_maurer": "Maurermeister Bauunternehmen Einzelunternehmen",
    "handwerk_stuck": "Stuckateur Trockenbau",
    "handwerk_boden": "Bodenleger Parkettleger",
    "handwerk_metall": "Metallbau Schlosserei Schweißer",
    "handwerk_glaser": "Glaserei Fensterbau Rollladenbau",
    "kuechenmonteure": "Küchenmontage Möbelmontage Monteur",
    "entruempler": "Entrümpelung Haushaltsauflösung",
    "fensterputzer": "Fensterputzer Glasreinigung",
    "baumpfleger": "Baumpflege Baumfällung Arborist",
    "pflasterer": "Pflasterarbeiten Zaunbau Terrassenbau",
    "schaedlingsbekaempfer": "Schädlingsbekämpfer Kammerjäger",
    "pv_monteure": "Photovoltaik Montage Solarteur Einzelunternehmen",
    "pc_notdienst": "PC Notdienst Computerhilfe vor Ort",
    "handyreparatur": "Handyreparatur Smartphone Reparatur",
    "polsterer": "Polsterei Sattlerei",
    "schuhmacher": "Schuhmacher Schuhreparatur",
    "uhrmacher": "Uhrmacher Uhrenreparatur",
    "foodtrucks": "Foodtruck Streetfood Einzelunternehmen",
    "privatkoeche": "Privatkoch Mietkoch Kochkurse",
    "mobile_barkeeper": "mobiler Barkeeper Cocktailservice",
    "babysitter": "Babysitter Nanny Kinderbetreuung privat",
    "alltagsbegleiter": "Alltagsbegleiter Betreuungskraft Seniorenbetreuung privat",
    "trauerbegleiter": "Trauerbegleiter Trauerbegleitung",
    "reiki_shiatsu": "Reiki Shiatsu Ayurveda Kinesiologie Praxis",
    "astrologen": "Astrologe Kartenlegen Beratung",
    "feng_shui": "Feng Shui Beratung",
    "tauchlehrer": "Tauchschule Surfschule Kiteschule Tauchlehrer",
    "bergfuehrer": "Bergführer Wanderführer Outdoor Guide",
    "stadtfuehrer": "Stadtführer Gästeführer",
    "reisebuero_solo": "mobiler Reiseberater Reisebüro Einzelunternehmen",
    "social_media_freelancer": "Social Media Manager Freelancer",
    "seo_freelancer": "SEO Freelancer Online Marketing Berater",
    "pr_berater": "PR Berater Pressearbeit Freelancer",
    "unternehmensberater_solo": "Unternehmensberater Einzelunternehmen",
    "datenschutzbeauftragte": "externer Datenschutzbeauftragter",
    "arbeitssicherheit": "Fachkraft für Arbeitssicherheit Brandschutzbeauftragter extern",
    "dozenten": "freiberuflicher Dozent Trainer Seminare",
    "stimmtrainer": "Gesangslehrer Stimmtrainer Rhetoriktrainer",
    "malschulen": "Malschule Malkurse Töpferkurse Atelier",
    "kuenstler": "freischaffender Künstler Atelier",
    "werbetechniker": "Werbetechnik Beschriftung Fahrzeugfolierung",
    "restauratoren": "Restaurator Möbelrestaurierung",
    "immobilienbewerter": "Immobiliengutachter Wertgutachten",
    "drohnenpiloten": "Drohnenpilot Luftaufnahmen",
    "dellentechniker": "Dellentechniker Dellendoktor Beulendoktor",
    "autoglaser": "Autoglaser Steinschlagreparatur mobil",
    "mobile_reifendienst": "mobiler Reifenservice Reifendienst",
    "motorradwerkstatt": "Motorradwerkstatt Einzelunternehmen",
    "wohnmobilservice": "Wohnmobil Service Caravan Werkstatt",
    "kurierdienste": "Kurierdienst Kurierfahrer Einzelunternehmen",
    "chauffeure": "Chauffeurservice Mietwagen mit Fahrer Einzelunternehmen",
    "moebeltaxi": "Möbeltaxi Kleintransporte",
    "alleinunterhalter": "Alleinunterhalter Zauberer Entertainer",
    "tontechniker": "Tontechniker Veranstaltungstechnik Einzelunternehmen",
    "naehservice": "Nähservice Änderungsschneiderei",
    "imker": "Imkerei Imker",
    "hofladen_solo": "Hofladen Direktvermarkter Landwirt",
    "winzer": "Winzer Weingut Familienbetrieb",
    "brauer": "Kleinbrauerei Brennerei Einzelunternehmen",
}

STAEDTE = [
    "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf",
    "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden", "Hannover", "Nürnberg",
    "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster", "Mannheim",
    "Karlsruhe", "Augsburg", "Wiesbaden", "Mönchengladbach", "Gelsenkirchen",
    "Aachen", "Braunschweig", "Chemnitz", "Kiel", "Halle", "Magdeburg", "Freiburg",
    "Krefeld", "Mainz", "Lübeck", "Erfurt", "Oberhausen", "Rostock", "Kassel",
    "Hagen", "Potsdam", "Saarbrücken", "Hamm", "Ludwigshafen", "Mülheim",
    "Oldenburg", "Osnabrück", "Leverkusen", "Heidelberg", "Darmstadt", "Solingen",
    "Regensburg", "Herne", "Paderborn", "Neuss", "Ingolstadt", "Offenbach",
    "Fürth", "Ulm", "Würzburg", "Heilbronn", "Pforzheim", "Wolfsburg", "Göttingen",
    "Bottrop", "Reutlingen", "Koblenz", "Bremerhaven", "Erlangen", "Bergisch Gladbach",
    "Remscheid", "Recklinghausen", "Trier", "Jena", "Moers", "Salzgitter", "Siegen",
    "Gütersloh", "Hildesheim", "Hanau", "Kaiserslautern", "Cottbus", "Schwerin",
    "Witten", "Gera", "Iserlohn", "Ludwigsburg", "Esslingen", "Zwickau", "Düren",
    "Ratingen", "Flensburg", "Lünen", "Villingen-Schwenningen", "Konstanz", "Marl",
    "Worms", "Velbert", "Neumünster", "Rosenheim", "Bamberg", "Bayreuth", "Fulda",
    # Erweiterung 12.09.2026: Mittelstädte für die Städte-Blöcke ab maps_ab=100
    "Landshut", "Aschaffenburg", "Kempten", "Passau", "Straubing", "Weiden", "Amberg",
    "Schweinfurt", "Coburg", "Hof", "Ansbach", "Neu-Ulm", "Memmingen", "Lindau",
    "Friedrichshafen", "Ravensburg", "Tübingen", "Göppingen", "Schwäbisch Gmünd", "Aalen",
    "Heidenheim", "Sindelfingen", "Böblingen", "Waiblingen", "Fellbach", "Leonberg",
    "Bietigheim-Bissingen", "Baden-Baden", "Rastatt", "Offenburg", "Lörrach", "Singen",
    "Bruchsal", "Weinheim", "Schwetzingen", "Speyer", "Landau in der Pfalz", "Neustadt an der Weinstraße",
    "Frankenthal", "Bad Kreuznach", "Neuwied", "Andernach", "Bad Homburg", "Rüsselsheim",
    "Gießen", "Marburg", "Wetzlar", "Limburg", "Bad Hersfeld", "Celle", "Lüneburg",
    "Wolfenbüttel", "Goslar", "Hameln", "Stade", "Cuxhaven", "Wilhelmshaven", "Emden",
    "Delmenhorst", "Nordhorn", "Lingen", "Rheine", "Bocholt", "Wesel", "Dinslaken", "Kleve",
    "Viersen", "Grevenbroich", "Dormagen", "Bergheim", "Kerpen", "Euskirchen", "Troisdorf",
    "Siegburg", "Gummersbach", "Lüdenscheid", "Arnsberg", "Soest", "Lippstadt", "Minden",
    "Herford", "Detmold", "Bad Salzuflen", "Unna", "Castrop-Rauxel", "Gladbeck", "Dorsten",
    "Ahlen", "Bad Oeynhausen", "Elmshorn", "Norderstedt", "Pinneberg", "Itzehoe", "Husum",
    "Schleswig", "Eckernförde", "Stralsund", "Greifswald", "Neubrandenburg", "Wismar", "Güstrow",
    "Brandenburg an der Havel", "Frankfurt (Oder)", "Oranienburg", "Falkensee", "Eberswalde",
    "Bernau bei Berlin", "Dessau-Roßlau", "Lutherstadt Wittenberg", "Halberstadt", "Stendal",
    "Weimar", "Gotha", "Eisenach", "Nordhausen", "Suhl", "Plauen", "Görlitz", "Bautzen",
    "Freiberg", "Pirna", "Riesa", "Meißen", "Zittau", "Homburg", "Neunkirchen", "Völklingen",
    "Saarlouis", "St. Wendel", "Merzig", "Garmisch-Partenkirchen", "Traunstein", "Bad Reichenhall",
    "Deggendorf", "Erding", "Freising", "Dachau", "Fürstenfeldbruck", "Starnberg", "Landsberg am Lech",
    "Kaufbeuren", "Günzburg", "Dillingen", "Nördlingen", "Donauwörth", "Neuburg an der Donau",
    "Eichstätt", "Roth", "Schwabach", "Forchheim", "Kulmbach", "Kronach", "Lichtenfels",
    "Bad Kissingen", "Kitzingen", "Bad Neustadt", "Lohr am Main", "Miltenberg", "Wertheim",
    "Tauberbischofsheim", "Mosbach", "Buchen", "Sinsheim", "Wiesloch", "Leimen", "Ettlingen",
    "Bretten", "Mühlacker", "Calw", "Nagold", "Freudenstadt", "Horb", "Rottweil", "Tuttlingen",
    "Balingen", "Albstadt", "Hechingen", "Metzingen", "Nürtingen", "Kirchheim unter Teck",
    "Schorndorf", "Backnang", "Schwäbisch Hall", "Crailsheim", "Öhringen", "Künzelsau",
    "Bad Mergentheim", "Neckarsulm", "Bad Rappenau", "Eppingen",
]

PORTAL_DOMAINS = re.compile(
    r"gelbeseiten|11880|dasoertliche|golocal|yelp|facebook|instagram|linkedin|xing|"
    r"branchenbuch|werkenntdenbesten|firmenwissen|northdata|wikipedia|kununu|youtube|"
    r"pinterest|tiktok|jameda|doctolib|treatwell|ammely|betreut\.de|kleinanzeigen|"
    r"ebay|amazon|etsy|google|stadtbranchenbuch|cylex|yellowmap|meinestadt|verzeichnis",
    re.I,
)


def log(msg: str) -> None:
    print(msg, flush=True)


BRAVE_ANFRAGEN = {"n": 0}


def brave_suche(frage: str, key: str) -> list[dict]:
    """Eine Brave-API-Anfrage (gezählt, 1/s über drossle)."""
    drossle("api.search.brave.com")
    BRAVE_ANFRAGEN["n"] += 1
    url = ("https://api.search.brave.com/res/v1/web/search?"
           + urllib.parse.urlencode({"q": frage, "country": "de", "count": 20, "search_lang": "de"}))
    req = urllib.request.Request(url, headers={
        "X-Subscription-Token": key, "Accept": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as antwort:
        daten = json.loads(antwort.read().decode())
    return ((daten.get("web") or {}).get("results")) or []


def titel_zu_name(titel: str) -> str:
    """Seitentitel grob zum Namens-Kandidaten machen."""
    t = re.split(r"[|–—•·]| - ", titel or "")[0].strip()
    t = re.sub(r"\b(Startseite|Home|Willkommen( bei)?|Herzlich willkommen)\b", "", t, flags=re.I).strip(" -–|·")
    return t[:120]


def main() -> int:
    parser = argparse.ArgumentParser(description="Brave-Suche (Fabrik 2, D-091)")
    parser.add_argument("--branche", required=True)
    parser.add_argument("--quellen", default="")
    parser.add_argument("--suchlauf-id", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if "brave" not in {q.strip() for q in args.quellen.split(",") if q.strip()}:
        log("Quelle 'brave' nicht angefordert — nichts zu tun.")
        return 0
    key = os.environ.get("BRAVE_API_KEY", "").strip()
    if not key:
        log("FEHLER: BRAVE_API_KEY fehlt (Worker-Secret) — Brave-Quelle übersprungen.")
        return 0
    client = App()
    if not client.basis or not client.token:
        log("FEHLER: APP_URL und WORKER_TOKEN müssen gesetzt sein.")
        return 1

    max_anfragen = int(os.environ.get("FABRIK2_BRAVE_MAX_ANFRAGEN", "100") or 100)
    begriff = BEGRIFFE.get(args.branche, args.branche)
    zielgruppe = args.branche

    # Zielgruppen-Label aus branchen.py (Anzeigename)
    try:
        from branchen import BRANCHEN
        zielgruppe = BRANCHEN.get(args.branche, {}).get("beruf", args.branche)
    except Exception:  # noqa: BLE001
        pass

    stufen = {"brave_anfragen": 0, "domains": 0, "impressum_ok": 0, "gemeldet": 0, "mit_handy": 0}
    verluste = {"portal": 0, "ohne_name": 0, "ohne_schluessel": 0, "doppelt_im_lauf": 0}
    gesehen_domains: set[str] = set()
    paket: list[dict] = []

    def sende_paket() -> None:
        if not paket:
            return
        antwort = client._req("POST", "/api/fabrik2/import-treffer",
                              {"suchlauf_id": args.suchlauf_id, "treffer": list(paket)})
        log(f"  Paket gemeldet: neu {antwort.get('neu', '?')}, dublette {antwort.get('dublette', '?')}")
        paket.clear()

    log(f"Brave-Suche: '{begriff} <Stadt>' - max. {max_anfragen} Anfragen, Limit {args.limit or 'alle'}")
    try:
        for stadt in STAEDTE:
            if BRAVE_ANFRAGEN["n"] >= max_anfragen:
                log(f"Anfragen-Deckel erreicht ({max_anfragen}).")
                break
            if args.limit and stufen["gemeldet"] >= args.limit:
                break
            try:
                ergebnisse = brave_suche(f"{begriff} {stadt}", key)
            except Exception as ex:  # noqa: BLE001
                log(f"  Brave-Anfrage fehlgeschlagen ({stadt}): {ex}")
                if "429" in str(ex):
                    log("  Kontingent/Rate erschöpft — Stopp.")
                    break
                continue
            stufen["brave_anfragen"] = BRAVE_ANFRAGEN["n"]
            for r in ergebnisse:
                if args.limit and stufen["gemeldet"] >= args.limit:
                    break
                url = str(r.get("url") or "")
                netloc = urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")
                if not netloc:
                    continue
                if PORTAL_DOMAINS.search(netloc):
                    verluste["portal"] += 1
                    continue
                if netloc in gesehen_domains:
                    verluste["doppelt_im_lauf"] += 1
                    continue
                gesehen_domains.add(netloc)
                stufen["domains"] += 1

                # Impressum nachschlagen — liefert Name/Telefon/E-Mail
                name = titel_zu_name(str(r.get("title") or ""))
                telefon, email, plz, ort = "", "", "", ""
                kontakt_name = ""
                try:
                    imp_url = web.impressum_finden(f"https://{netloc}",
                                                   hole=lambda u, timeout=10: _hole_text(u))
                    if imp_url:
                        status, html = _hole_text(imp_url)
                        if status == 200 and html:
                            imp = web.impressum_auslesen(html, ki_abfrage=ki_abfrage)
                            if imp.get("nachname"):
                                kontakt_name = f'{imp.get("vorname", "")} {imp["nachname"]}'.strip()
                            telefon = imp.get("telefon") or ""
                            email = imp.get("email") or ""
                            adr = normalisierung.adresse(html_zu_text(html)[:2000])
                            plz, ort = adr["plz"], adr["ort"]
                            stufen["impressum_ok"] += 1
                except Exception:  # noqa: BLE001 — Domain-Ausfall ist normal
                    pass

                if not name and not kontakt_name:
                    verluste["ohne_name"] += 1
                    continue
                if not telefon and not plz:
                    verluste["ohne_schluessel"] += 1
                    continue
                firma = {"name": kontakt_name or name, "branche": zielgruppe}
                if vorfilter.ist_institution({"name": firma["name"], "website": netloc}):
                    verluste["portal"] += 1
                    continue
                treffer = {
                    "name": kontakt_name or name,
                    "telefon": telefon, "email": email, "plz": plz, "ort": ort,
                    "website": f"https://{netloc}",
                    "branche": zielgruppe, "quelle": "brave", "quell_link": url,
                }
                if kontakt_name:
                    treffer["kontakt"] = {"name": kontakt_name, "rolle": zielgruppe,
                                          "email": email, "telefon": telefon}
                paket.append(treffer)
                stufen["gemeldet"] += 1
                if normalisierung.telefon(telefon)["art"] == "mobil":
                    stufen["mit_handy"] += 1
                if len(paket) >= PAKET_GROESSE:
                    sende_paket()
        sende_paket()
    finally:
        stufen["brave_anfragen"] = BRAVE_ANFRAGEN["n"]
        client._req("POST", "/api/fabrik2/bericht", {
            "suchlauf_id": args.suchlauf_id,
            "foerderband": {"stufen_brave": stufen, "verluste_brave": verluste,
                            "brave_anfragen": BRAVE_ANFRAGEN["n"],
                            "ki_extraktion_calls": KI_CALLS["n"]},
        })
        log(f"Brave fertig: {json.dumps(stufen)} / Verluste {json.dumps(verluste)}")
    return 0


def _hole_text(url: str, timeout: int = 10) -> tuple[int, str]:
    status, roh = hole_roh(url, timeout=timeout)
    return status, roh.decode("utf-8", "replace") if roh else ""


if __name__ == "__main__":
    sys.exit(main())
