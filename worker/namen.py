#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Namens-Finder ohne KI (12.09.2026, 100.000-Leads-Auftrag).

Hintergrund: Die KI-Aufrufe des Workers schlagen seit dem 06.09. fehl
(HTTP 400), seitdem fand die Anreicherung bei Karten-Treffern kaum noch
Ansprechpartner — ohne Personenname aber kein Lead (D-035). Dieses Modul
zieht den Inhaber-Namen mit einem Vornamen-Lexikon aus Impressum,
Kontakt-, Über-mich- und Datenschutz-Seiten, ganz ohne KI. Grundidee wie
D-107 (`public.vornamen_lexikon`): Ein Wort aus dem Lexikon, gefolgt von
einem groß geschriebenen Nachnamen, in der Nähe von Signalwörtern wie
„Inhaberin", „Verantwortlich", „Angaben gemäß § 5".

Bewusst konservativ: lieber kein Name als ein falscher (die Bereinigungen
vom 06.–08.09. haben gezeigt, was Fetzen im Namensfeld anrichten).
"""

import re

VORNAMEN = {
    "Maria", "Josef", "Marie", "Sophie", "Emily", "Amira", "Noel", "Hanne", "Jule", "Merle", "Wibke",
    "Gesche", "Antje", "Silja", "Femke", "Elke", "Heino", "Hauke", "Harm", "Onno", "Enno", "Tjark",
    "Aabeda", "Aaron", "Achim", "Adelheid", "Admir", "Adrian", "Agata", "Agnes", "Agnieszka",
    "Ahmet", "Aileen", "Aleksandra", "Alessa", "Alex", "Alexa", "Alexander", "Alexandra",
    "Alfons", "Alfred", "Ali", "Alice", "Alina", "Alma", "Almut", "Alois", "Amalie", "Amelie",
    "Ana", "Andre", "Andrea", "Andreas", "Anett", "Anette", "Angela", "Angelika", "Angelina",
    "Angie", "Anika", "Anita", "Anja", "Anke", "Ann-Kathrin", "Anna", "Anna-Lena",
    "Anna-Maria", "Annabell", "Annalena", "Anne", "Annegret", "Anneliese", "Annemarie",
    "Annett", "Annette", "Annika", "Ansgar", "Antje", "Anton", "Antonia", "Antonio", "Ariane",
    "Armin", "Arne", "Arthur", "Artur", "Astrid", "Auguste", "Axel", "Aylin", "Ayse",
    "Barbara", "Bastian", "Beata", "Beate", "Beatrix", "Ben", "Benedikt", "Benjamin", "Benno",
    "Berit", "Bernadette", "Bernd", "Bernhard", "Berta", "Bettina", "Bianca", "Bianka",
    "Birgit", "Birte", "Björn", "Boris", "Brigitte", "Brita", "Britta", "Bruno", "Burkhard",
    "Bärbel", "Carina", "Carl", "Carla", "Carlotta", "Carmen", "Carola", "Carolin", "Caroline",
    "Carsten", "Catharina", "Catherina", "Catherine", "Cathleen", "Cathrin", "Catrin",
    "Cecilia", "Celina", "Celine", "Cem", "Chantal", "Charlotte", "Chiara", "Chris", "Christa",
    "Christel", "Christian", "Christiana", "Christiane", "Christin", "Christina", "Christine",
    "Christoph", "Christopher", "Cindy", "Clara", "Claudia", "Colin", "Conny", "Constantin",
    "Constanze", "Cora", "Cordula", "Corinna", "Cornelia", "Curt", "Cäcilie", "Dagmar",
    "Damaris", "Dana", "Daniel", "Daniela", "Danielle", "Danuta", "Daria", "David", "Deborah",
    "Denis", "Denise", "Deniz", "Dennis", "Derya", "Desiree", "Detlef", "Diana", "Diane",
    "Dieter", "Dietmar", "Dilara", "Dimitri", "Dirk", "Dominic", "Dominik", "Dominika",
    "Doreen", "Doris", "Dorit", "Dorota", "Dorothea", "Dorothee", "Dörthe", "Ebru", "Eckhard",
    "Edeltraud", "Edgar", "Edith", "Edmund", "Eduard", "Egon", "Eike", "Eileen", "Elena",
    "Elfriede", "Elias", "Elif", "Elisa", "Elisabeth", "Elke", "Ella", "Ellen", "Elsa",
    "Elvira", "Emil", "Emilia", "Emma", "Emre", "Enrico", "Enzo", "Eric", "Erich", "Erik",
    "Erika", "Erna", "Ernst", "Erwin", "Esra", "Esther", "Eugen", "Eugenia", "Eva", "Evelin",
    "Evelyn", "Evi", "Ewa", "Ewald", "Ewelina", "Fabian", "Fanny", "Fatma", "Felicitas",
    "Felix", "Fenja", "Ferdinand", "Finn", "Fiona", "Flora", "Florian", "Frances", "Frank",
    "Franz", "Franziska", "Frauke", "Freya", "Frieda", "Friederike", "Friedrich", "Gabi",
    "Gabriela", "Gabriele", "Galina", "Georg", "Georgios", "Gerald", "Gerd", "Gerda",
    "Gerhard", "Gerlinde", "Gerrit", "Gert", "Gertraud", "Gertrud", "Gertrude", "Gesa",
    "Gesine", "Gina", "Gisela", "Gloria", "Gordon", "Gregor", "Greta", "Grete", "Grit",
    "Gudrun", "Guido", "Gunda", "Gunter", "Gunther", "Gustav", "Günter", "Günther", "Hajo",
    "Hakan", "Hanna", "Hannah", "Hannelore", "Hannes", "Hanns", "Hans", "Hans-Jürgen",
    "Hans-Peter", "Harald", "Hartmut", "Hatice", "Hedwig", "Heidi", "Heidrun", "Heike",
    "Heiko", "Heiner", "Heinrich", "Heinz", "Helen", "Helena", "Helene", "Helga", "Helma",
    "Helmut", "Helmuth", "Henning", "Henriette", "Henrike", "Henry", "Herbert", "Hermann",
    "Herta", "Herwig", "Hilde", "Hildegard", "Hilmar", "Holger", "Horst", "Hubert", "Hubertus",
    "Hülya", "Ida", "Ilka", "Ilona", "Ilse", "Imke", "Ina", "Ines", "Inga", "Inge", "Ingeborg",
    "Ingo", "Ingolf", "Ingrid", "Inka", "Inken", "Inna", "Insa", "Irene", "Irina", "Iris",
    "Irma", "Irmgard", "Isabel", "Isabell", "Isabella", "Isabelle", "Ivan", "Ivana", "Ivonne",
    "Iwona", "Jacob", "Jacqueline", "Jakob", "Jan", "Jana", "Janet", "Janina", "Janine",
    "Janna", "Jannik", "Jannis", "Jaqueline", "Jasmin", "Jasmina", "Jeanette", "Jeannette",
    "Jelena", "Jennifer", "Jenny", "Jens", "Jessica", "Jessika", "Joachim", "Joanna", "Jochen",
    "Joel", "Johanna", "Johannes", "Jonas", "Jonathan", "Josef", "Josephine", "Joshua", "Jost",
    "Judith", "Juergen", "Jule", "Julia", "Julian", "Juliane", "Julien", "Juri", "Justin",
    "Justina", "Justine", "Justus", "Justyna", "Jutta", "Jörg", "Jörn", "Jürgen", "Kai",
    "Karen", "Karin", "Karina", "Karl", "Karl-Heinz", "Karla", "Karola", "Karolin", "Karoline",
    "Karsten", "Kaspar", "Katarzyna", "Katharina", "Katherina", "Kathleen", "Kathrin", "Kati",
    "Katja", "Katrin", "Kerstin", "Kevin", "Kilian", "Kim", "Kimberly", "Kira", "Kirsten",
    "Kirstin", "Klara", "Klaudia", "Klaus", "Klaus-Dieter", "Klothilde", "Konrad",
    "Konstantin", "Kora", "Korbinian", "Kornelia", "Kristin", "Kristina", "Ksenia", "Kurt",
    "Käthe", "Lara", "Larisa", "Larissa", "Lars", "Laura", "Lea", "Leila", "Lena", "Leni",
    "Lennard", "Lennart", "Leo", "Leon", "Leonard", "Leoni", "Leonie", "Leopold", "Lieselotte",
    "Lilia", "Lilly", "Lina", "Linda", "Lioba", "Lisa", "Lisa-Marie", "Lisanne", "Lore",
    "Lorenz", "Lothar", "Luca", "Lucas", "Lucia", "Lucie", "Ludmila", "Ludwig", "Luis",
    "Luisa", "Luise", "Lukas", "Lutz", "Lydia", "Lynn", "Madlen", "Magda", "Magdalena", "Maik",
    "Maike", "Maja", "Malgorzata", "Malin", "Malte", "Mandy", "Manfred", "Manja", "Manuel",
    "Manuela", "Mara", "Marc", "Marcel", "Marco", "Marcus", "Mareen", "Mareike", "Maren",
    "Margarete", "Margarethe", "Margarita", "Margit", "Margot", "Margret", "Margrit", "Marian",
    "Marianne", "Marie", "Marie-Luise", "Marietta", "Marija", "Marina", "Mario", "Marion",
    "Marita", "Marius", "Mark", "Marko", "Markus", "Marleen", "Marlene", "Marlies", "Marlis",
    "Marta", "Martha", "Martin", "Martina", "Marvin", "Maryam", "Marzena", "Mathias",
    "Mathilda", "Mathilde", "Matteo", "Matthias", "Max", "Maximilian", "Maya", "Mechthild",
    "Mechtild", "Mehmet", "Meike", "Meinhard", "Melanie", "Melek", "Melina", "Melissa",
    "Melitta", "Mia", "Michael", "Michaela", "Michelle", "Mihaela", "Mike", "Mila", "Milena",
    "Mirco", "Miriam", "Mirjam", "Mirjana", "Mirko", "Mischa", "Mohamed", "Mohammad",
    "Mohammed", "Mona", "Monica", "Monika", "Monique", "Moritz", "Murat", "Mustafa", "Myriam",
    "Nadia", "Nadine", "Nadja", "Nancy", "Natalia", "Natalie", "Natalija", "Natascha",
    "Nathalie", "Nele", "Nelli", "Niclas", "Nico", "Nicola", "Nicole", "Niels", "Niklas",
    "Nikolaus", "Nils", "Nina", "Noah", "Nora", "Norbert", "Norman", "Oksana", "Olaf", "Ole",
    "Olena", "Olga", "Oliver", "Olivia", "Oskar", "Ottfried", "Ottilie", "Ottmar", "Otto",
    "Pamela", "Pascal", "Patricia", "Patrick", "Patrizia", "Paul", "Paula", "Paulina",
    "Pauline", "Peggy", "Peter", "Petra", "Philip", "Philipp", "Pia", "Pierre", "Polina",
    "Quirin", "Rahel", "Raimund", "Rainer", "Ralf", "Ralph", "Ramona", "Raphael", "Raphaela",
    "Rebecca", "Rebekka", "Regina", "Regine", "Reiner", "Reinhard", "Rena", "Renata", "Renate",
    "Rene", "Ricarda", "Richard", "Rico", "Rita", "Robert", "Robin", "Roland", "Rolf", "Roman",
    "Romina", "Romy", "Ronald", "Ronja", "Ronny", "Rosa", "Rosalie", "Rosemarie", "Rosina",
    "Rudolf", "Rupert", "Ruth", "Rüdiger", "Sabina", "Sabine", "Sabrina", "Samira", "Samuel",
    "Sandra", "Sandy", "Sara", "Sarah", "Sarina", "Sascha", "Saskia", "Sebastian", "Selin",
    "Selina", "Sepp", "Sergej", "Serkan", "Sevilay", "Sevim", "Shervin", "Sibylla", "Sibylle",
    "Siegfried", "Sieglinde", "Siegmar", "Sigmund", "Sigrid", "Sigrun", "Silke", "Silvana",
    "Silvia", "Simon", "Simone", "Sina", "Sofia", "Solveig", "Sonja", "Sophia", "Sophie",
    "Stefan", "Stefanie", "Steffen", "Steffi", "Stephan", "Stephanie", "Susan", "Susann",
    "Susanne", "Susi", "Suzanne", "Sven", "Svenja", "Svetlana", "Swantje", "Swetlana", "Sylke",
    "Sylvester", "Sylvia", "Sören", "Tabea", "Tamara", "Tania", "Tanja", "Tatiana", "Tatjana",
    "Teresa", "Theo", "Theodor", "Theresa", "Theresia", "Thiemo", "Thilo", "Thomas", "Thoralf",
    "Thorsten", "Tim", "Timo", "Tina", "Tino", "Tobias", "Tom", "Tomas", "Toni", "Torsten",
    "Traudel", "Trude", "Tugba", "Tünde", "Udo", "Ulf", "Ulla", "Ulrich", "Ulrike", "Urs",
    "Ursel", "Ursula", "Urszula", "Uta", "Ute", "Uwe", "Valentin", "Valentina", "Valeria",
    "Vanessa", "Veit", "Vera", "Verena", "Veronika", "Vesna", "Victoria", "Viktor", "Viktoria",
    "Vincent", "Viola", "Vitus", "Vivian", "Vivien", "Vladimir", "Volker", "Volkmar",
    "Waldemar", "Walter", "Waltraud", "Werner", "Wiebke", "Wilfried", "Wilhelm", "Willi",
    "Wilma", "Wolf", "Wolfgang", "Wolfram", "Xaver", "Yannick", "Yasemin", "Yasin", "Yasmin",
    "Yusuf", "Yvette", "Yvonne", "Zana", "Zeynep", "Zita",
}

# Wörter, die nie ein Nachname sind (Navigation, Rechtstexte, Gewerbe)
KEIN_NACHNAME = re.compile(
    r"^(gmbh|ug|ag|kg|ohg|straße|strasse|str|weg|allee|platz|ring|gasse|impressum|datenschutz|"
    r"kontakt|telefon|tel|fax|mobil|mail|e-mail|web|home|start|über|ueber|uns|mich|praxis|studio|"
    r"salon|kosmetik|massage|physiotherapie|osteopathie|hebamme|hebammen|tagesmutter|yoga|coaching|"
    r"coach|training|beratung|service|team|inhaber|inhaberin|geschäftsführer|geschäftsführerin|"
    r"verantwortlich|verantwortliche|verantwortlicher|vertreten|angaben|gemäß|nach|und|oder|für|"
    r"mit|von|zu|zur|zum|am|im|an|in|der|die|das|des|dem|den|ein|eine|einer|sie|ihr|ihre|wir|"
    r"unser|unsere|mein|meine|herzlich|willkommen|montag|dienstag|mittwoch|donnerstag|freitag|"
    r"samstag|sonntag|uhr|termin|termine|öffnungszeiten|leistungen|preise|aktuelles|news|blog|"
    r"galerie|bilder|anfahrt|jobs|karriere|shop|login|cookie|cookies|einstellungen|akzeptieren|"
    r"ablehnen|mehr|weiter|zurück|menü|menu|suche|newsletter|facebook|instagram|whatsapp|youtube|"
    r"deutschland|berlin|hamburg|münchen|köln|frankfurt|stuttgart|düsseldorf|leipzig|dortmund|"
    r"essen|bremen|dresden|hannover|nürnberg|dipl|dr|prof|med|phil|ing|jur|rer|nat|mba|bsc|msc|"
    r"ba|ma|sc|heilpraktiker|heilpraktikerin|physiotherapeut|physiotherapeutin|kosmetikerin|"
    r"friseur|friseurin|fotograf|fotografin|trainer|trainerin|lehrer|lehrerin|therapeut|therapeutin|"
    r"berater|beraterin|designer|designerin|makler|maklerin|meister|meisterin|hundeschule|"
    r"hundetrainer|hundetrainerin|ernährungsberatung|ernährungsberaterin|osteopath|osteopathin|"
    r"logopädin|ergotherapeutin|podologin|fußpflege|nageldesign|permanent|make-up|makeup|"
    r"personal|business|life|mental|wedding|events|event|musik|tanz|kunst|natur|vital|balance|"
    r"harmonie|wellness|beauty|nails|hair|style|styling|care|body|mind|soul|spirit)$",
    re.I,
)

TITEL = re.compile(r"^(dr|prof|dipl|med|dent|phil|rer|nat|ing|jur|mag|dipl\.-[a-z]+)\.?$", re.I)

# Signalwörter: davor/dahinter steht meist der Inhaber-Name
SIGNAL = re.compile(
    r"inhaber|inhaberin|verantwortlich|vertreten\s+durch|vertretungsberechtigt|angaben\s+gem|"
    r"§\s*5|tmg|ddg|betreiber|betreiberin|ansprechpartner|ansprechpartnerin|kontaktperson|"
    r"geschäftsführ|leitung|praxisinhaber|studioinhaber|über\s+mich|ueber\s+mich|mein\s+name|"
    r"ich\s+bin|ich\s+heiße|redaktionell|diensteanbieter|anbieter|verantwortlicher\s+im\s+sinne",
    re.I,
)

# Berufsbezeichnung direkt vor dem Namen („Hebamme Frauke Bittner") ist ein Signal
BERUF_SIGNAL = re.compile(
    r"(hebamme|heilpraktiker(in)?|physiotherapeut(in)?|osteopath(in)?|kosmetikerin|friseur(in|meister(in)?)?|"
    r"fotograf(in)?|tätowierer(in)?|trainer(in)?|coach|lehrer(in)?|therapeut(in)?|berater(in)?|"
    r"designer(in)?|makler(in)?|meister(in)?|tagesmutter|tagesvater|doula|stillberaterin|logopäd(e|in)|"
    r"ergotherapeut(in)?|podolog(e|in)|fußpfleger(in)?|masseur(in)?|hundetrainer(in)?|hufschmied|"
    r"gutachter(in)?|übersetzer(in)?|dolmetscher(in)?|gärtner(in)?|schneider(in)?|redner(in)?|"
    r"dj|musiker(in)?|inhaber(in)?|praxis|studio)\s*:?\s*$",
    re.I,
)

def _vornamen_regex() -> str:
    # Längste zuerst, damit „Anna-Lena" vor „Anna" greift
    return "|".join(re.escape(n) for n in sorted(VORNAMEN, key=len, reverse=True))


# Der Vorname wird direkt gegen das Lexikon gematcht — ein Ansatz „beliebiges
# großes Wort, danach prüfen" fraß bei „Hebamme Frauke Bittner" das Paar
# „Hebamme Frauke" und übersah den echten Namen.
NAME_MUSTER = re.compile(
    r"(?<![\wäöüÄÖÜß-])"
    r"((?:Dr\.?\s+|Prof\.?\s+|Dipl\.[\w-]*\.?\s+|med\.?\s+)*)"      # Titel
    r"(" + _vornamen_regex() + r")"                                    # Vorname (Lexikon)
    r"(?:[ \t]+([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?))?"        # Zweitvorname (optional, gleiche Zeile)
    r"[ \t]+((?:von|van|de|zu|zur|van der|von der|da|di)[ \t]+)?"      # Adelspartikel
    r"([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)"                    # Nachname
    r"(?![\wäöüÄÖÜß-])"
)


def _kandidaten(text: str) -> list[dict]:
    """Alle „Vorname Nachname"-Treffer mit Kontext-Score."""
    treffer: list[dict] = []
    for m in NAME_MUSTER.finditer(text):
        vor, zweit, partikel, nach = m.group(2), m.group(3), m.group(4) or "", m.group(5)
        # Zweitvorname nur, wenn er selbst ein Vorname ist — sonst ist er der
        # Nachname („Frauke Bittner Mobil" → Nachname Bittner, nicht Mobil)
        if zweit and zweit not in VORNAMEN:
            nach, partikel, zweit = zweit, "", None
        if KEIN_NACHNAME.match(nach) or TITEL.match(nach) or len(nach) < 2:
            continue
        davor = text[max(0, m.start() - 120):m.start()]
        danach = text[m.end():m.end() + 60]
        score = 1
        if SIGNAL.search(davor):
            score += 3
        elif BERUF_SIGNAL.search(davor[-40:]):
            score += 2
        elif re.search(r"©|copyright|\(c\)", davor[-40:], re.I):
            score += 2  # Fußzeile „© 2024 Nadine Weber" nennt fast immer die Inhaberin
        if SIGNAL.search(danach):
            score += 1
        if re.search(r"impressum", text[max(0, m.start() - 600):m.start()], re.I):
            score += 1
        vorname = f"{vor} {zweit}" if zweit else vor
        treffer.append({"vorname": vorname, "nachname": f"{partikel}{nach}".strip(), "score": score})
    return treffer


def finde_personenname(texte: list[str]) -> dict | None:
    """Bester Inhaber-Name über mehrere Seitentexte (Impressum zuerst).

    Rückgabe {vorname, nachname, score} oder None. Mehrfache Nennungen
    desselben Namens über Seiten hinweg zählen zusammen; ein Name muss
    mindestens Score 2 erreichen (Signalwort ODER zweimal gesehen ODER im
    Impressum-Block), sonst gilt er als Zufallstreffer (z. B. Kundenstimme).
    """
    summe: dict[str, dict] = {}
    for text in texte:
        if not text:
            continue
        gesehen_hier: set[str] = set()
        for k in _kandidaten(text):
            schluessel = f"{k['vorname']} {k['nachname']}".lower()
            eintrag = summe.setdefault(schluessel, {"vorname": k["vorname"], "nachname": k["nachname"], "score": 0})
            if schluessel in gesehen_hier:
                eintrag["score"] = max(eintrag["score"], k["score"])
            else:
                eintrag["score"] += k["score"]
                gesehen_hier.add(schluessel)
    if not summe:
        return None
    bester = max(summe.values(), key=lambda e: e["score"])
    if bester["score"] < 2:
        return None
    # Mehrere gleich starke Namen (Gemeinschaftspraxis, Team-Seite) → unsicher
    gleich = [e for e in summe.values() if e["score"] == bester["score"]]
    if len(gleich) > 1 and bester["score"] < 4:
        return None
    return bester


NAMENSSEITEN = ("impressum", "kontakt", "ueber-mich", "über-mich", "ueber-uns", "über-uns",
                "about", "team", "datenschutz", "vita", "profil")


def namens_urls(website: str) -> list[str]:
    basis = website.rstrip("/")
    return [f"{basis}/{p}" for p in NAMENSSEITEN]


def namenslinks_aus_html(html: str, website: str) -> list[str]:
    """Interne Links, deren Text/Pfad nach Impressum/Kontakt/Über-mich aussieht."""
    import urllib.parse
    gefunden: list[str] = []
    for m in re.finditer(r'<a[^>]+href="([^"#?]+)[^"]*"[^>]*>(.*?)</a>', html, re.I | re.S):
        href, text = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        probe = f"{href} {text}".lower()
        if any(p in probe for p in NAMENSSEITEN) or re.search(r"impressum|kontakt|über mich|ueber mich|über uns|wir über|team|vita", probe):
            url = urllib.parse.urljoin(website if website.endswith("/") else website + "/", href)
            if urllib.parse.urlsplit(url).netloc == urllib.parse.urlsplit(website).netloc and url not in gefunden:
                gefunden.append(url)
    return gefunden[:8]


def html_zu_text(html: str) -> str:
    """HTML → lesbarer Text (Kopie aus verbaende.py, um Import-Zirkel zu vermeiden)."""
    text = re.sub(r"<(script|style|nav|footer|svg)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    text = re.sub(r'href="mailto:([^"?]+)[^"]*"', r'> E-Mail: \1 <', text)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</td>|</tr>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    for a, b in (("&amp;", "&"), ("&nbsp;", " "), ("&auml;", "ä"), ("&ouml;", "ö"), ("&uuml;", "ü"),
                 ("&szlig;", "ß"), ("&Auml;", "Ä"), ("&Ouml;", "Ö"), ("&Uuml;", "Ü"), ("&#39;", "'"), ("&quot;", '"')):
        text = text.replace(a, b)
    return re.sub(r"[ \t]+", " ", text)


def namens_nachlauf(website: str, geladen: dict[str, str], hole, max_seiten: int = 4) -> tuple[dict | None, list[str]]:
    """Namens-Suche über die schon geladenen Seiten plus bis zu `max_seiten`
    weitere Kandidaten-Seiten (Impressum/Kontakt/Über-mich/Datenschutz).
    `hole(url) -> (status, html)` kommt aus anreicherung.py (gedrosselt).
    Rückgabe (Treffer|None, Liste der geprüften URLs)."""
    texte: list[str] = [html_zu_text(h) for h in geladen.values() if h]
    geprueft = list(geladen.keys())
    kandidaten: list[str] = []
    start_html = geladen.get(website) or geladen.get(website.rstrip("/")) or ""
    if not start_html:
        try:
            status, start_html = hole(website)
            geprueft.append(website)
            if status == 200 and start_html:
                texte.append(html_zu_text(start_html))
                geladen[website] = start_html  # für den KI-Nachschlag (6c) aufheben
        except Exception:  # noqa: BLE001
            start_html = ""
    if start_html:
        kandidaten.extend(namenslinks_aus_html(start_html, website))
    for u in namens_urls(website):
        if u not in kandidaten:
            kandidaten.append(u)
    # Impressum-Fund schon stark genug? Dann keine weiteren Seiten laden.
    treffer = finde_personenname(texte)
    if treffer and treffer["score"] >= 4:
        return treffer, geprueft
    n = 0
    for url in kandidaten:
        if n >= max_seiten:
            break
        if url in geprueft or url.rstrip("/") in geprueft:
            continue
        try:
            status, html = hole(url)
        except Exception:  # noqa: BLE001
            continue
        geprueft.append(url)
        n += 1
        if status == 200 and html:
            texte.append(html_zu_text(html))
            geladen[url] = html  # für den KI-Nachschlag (6c) aufheben
            treffer = finde_personenname(texte)
            if treffer and treffer["score"] >= 4:
                break
    return finde_personenname(texte), geprueft
