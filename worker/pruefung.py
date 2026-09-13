"""
Prüf-Worker (D-120, 13.09.2026): kontrolliert fertige Fabrik-2-Leads gegen
ihre Website — ohne KI, nur Regeln. Justin: „einen Worker, der die neuen
Leads alle überprüft: Name richtig, Website, Telefonnummer, Ansprechperson,
E-Mail".

Je Lead (100-%-Regel, Justin 13.09.: Website, richtiger Name, E-Mail, Handynummer,
passend zur AV-Beratung = Solo-Selbstständige):
  0. Solo-Check: Team/Mitarbeiter/Filialen/GmbH auf Website oder im Impressum → Rückhand.
  1. Website laden (Startseite; dazu Impressum/Kontakt/Über-mich-Seiten,
     höchstens vier). Nicht ladbar → „Website nicht erreichbar".
  2. Name: Vor- UND Nachname müssen auf einer der Seiten stehen. Nur der
     Nachname → „Vorname nicht auf Website"; gar nichts → „Name nicht auf
     Website" (dann ist die Ansprechperson wahrscheinlich falsch zugeordnet).
  3. Handynummer: Pflicht. Lead-Nummer muss auf der Seite stehen; ist sie
     Festnetz, wird eine Handynummer von der Website nachgetragen (nachtrag.phone).
  4. E-Mail: Pflicht. Domain gleich Website-Domain oder Adresse auf der Seite;
     fehlt sie, wird sie von der Website nachgetragen (nachtrag.email).
  5. Fremde Website: Titel/Text deutet auf Portal, Verzeichnis, PDF, Behörde.

Ergebnis geht an /api/fabrik2/pruefung-ergebnis und landet in
leads.lead_quality: „geprüft ✓" oder „geprüft: <Mängel>". Nichts wird
gelöscht — das entscheidet das Team im CRM.

Aufruf:  python worker/pruefung.py --limit 300
Env:     APP_URL, WORKER_TOKEN
Ausgabe: GITHUB_OUTPUT rest=<offene Leads> (für den Ketten-Modus)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from leadkern import web

sys.path.insert(0, os.path.dirname(__file__))
from namen import VORNAMEN, html_zu_text, namens_urls  # noqa: E402

VORNAMEN_LEX = {str(v).strip().lower() for v in (VORNAMEN.keys() if isinstance(VORNAMEN, dict) else VORNAMEN)}

USER_AGENT = "lead-maschine-pruefung/1.0"
PARALLEL = 4
MAX_SEITEN = 4

# Solo-Regel (D-099 / Justin 13.09.: „passende Leads für unsere AV-Beratung"):
# Hinweise auf Personal, Filialen oder Kapitalgesellschaften halten den Lead zurück.
KEIN_SOLO_MUSTER = re.compile(
    r"unser(e)?\s+(team|mitarbeiter(innen)?|filialen|standorte|niederlassungen)|"
    r"wir\s+sind\s+ein\s+team|team\s+von\s+\d+|\d+\s+mitarbeiter|"
    r"\b(gmbh|ug\s*\(haftungsbeschränkt\)|\bag\b|\bkg\b|ohg|franchise|zentrale)\b|"
    r"geschäftsführer(in)?:|handelsregister|hrb\s?\d", re.I)
# Plausibilität Ansprechpartner (Justin 13.09.: „richtigen Namen des AP … kein Quatsch"):
# Firmen-/Berufsbegriffe, Titel oder Ziffern im Namensfeld → kein Personenname.
KEIN_PERSONENNAME = re.compile(
    r"praxis|service|beauty|studio|salon|heilpr|gmbh|kosmetik|physio|ergo|therap|coach|team|"
    r"massage|nails|nagel|design|foto|consult|media|medien|shop|store|handel|\bbau\b|elektro|"
    r"dach|maler|garten|pflege|mobil|zentrum|institut|schule|akademie|agentur|büro|buero|"
    r"werkstatt|betrieb|firma|inhaber|geschäftsf|\d", re.I)
# Floskeln/Menüpunkte, die als „Name" gelandet sind (z. B. „Sprechen Sie", „Gordon House" = Google-Adresse)
QUATSCH_MUSTER = re.compile(
    r"\b(sie|ihr|ihre|ihrem|ihren|uns|mich|dich|wir|menu|menü|home|jetzt|anfrage|angebot|angebote|kontakt|"
    r"cookie|cookies|datenschutz|impressum|leistungen|preise|fragen|website|telefon|phone|email|e-mail|mail|"
    r"adresse|anbieter|verantwortlich|verantwortlicher|social|instagram|facebook|youtube|google|toggle|page|"
    r"select|close|open|blog|about|start|startseite|über|ueber|willkommen|herzlich|dein|deine|der|die|das|"
    r"des|den|dem|und|für|fuer|mit|zum|zur|vom|von der|str|straße|strasse|weg|platz|gasse|allee|"
    r"gordon house|main|number|name|infos|info|aktuelle|hilfreiche|kostenlos|kostenlose|kostenloses|kostenfrei|"
    r"kostenfreies|erstgespräch|buchen|anrufen|rückruf|nutzen|senden|besuchen|vereinbaren|lassen|sprechen|"
    r"bewerten|schließen|erweitern|anfordern|erreichbarkeit|einstellungen|dokumente|partner|experte|expertin|"
    r"reise|aufgabe|kunden|brautpaar|sollten|hat|bei|per|am|im|an)\b", re.I)
# Namenspartikel (van der Kaay, von der Ohe, de la Cruz) sind keine Floskeln
PARTIKEL_MUSTER = re.compile(r"\b(van|von|de|da|del|della|di|du|le|la|el|al|ter|ten|zu|zur|zum)(\s+(der|den|dem|de|la|le|het))?\s+", re.I)
TITEL_MUSTER = re.compile(r"^(?:(?:dr|prof|dipl|med|dent|phil|rer|nat|ing|mag|jur|h\.?c|habil)\.?[-\w.]*\s+)+", re.I)
HANDY_MUSTER = re.compile(r"(?:\+49|0049|0)[\s./-]?1[5-7]\d[\d\s./-]{6,12}")
MAIL_MUSTER = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
MAIL_SPERRE = re.compile(r"example|wixpress|sentry|noreply|no-reply|webmaster@|@(google|apple|facebook|instagram|jimdo|wordpress|1und1|ionos|strato)\.", re.I)

FREMD_MUSTER = re.compile(
    r"gelbe\s?seiten|11880|dasoertliche|das\s?örtliche|jameda|doctolib|yelp|kununu|"
    r"branchenbuch|stadtbranchenbuch|cylex|firmenwissen|northdata|unternehmensverzeichnis|"
    r"stellenangebot|jobbörse|wikipedia|facebook\.com|instagram\.com|linkedin\.com|xing\.com|"
    r"ebay-kleinanzeigen|kleinanzeigen\.de|amtsblatt|landkreis|stadtverwaltung", re.I)


def log(msg: str) -> None:
    print(msg, flush=True)


_dom_lock = threading.Lock()
_dom_zuletzt: dict[str, float] = {}


def drossle(url: str) -> None:
    domain = urllib.parse.urlsplit(url if "//" in url else f"https://{url}").netloc or "unbekannt"
    with _dom_lock:
        jetzt = time.monotonic()
        frei_ab = max(jetzt, _dom_zuletzt.get(domain, 0.0) + 1.0)
        _dom_zuletzt[domain] = frei_ab
    if frei_ab > time.monotonic():
        time.sleep(frei_ab - time.monotonic())


def hole(url: str, timeout: int = 10) -> tuple[int, str]:
    drossle(url)
    return web.hole_seite(url, timeout=timeout)


class App:
    def __init__(self):
        self.basis = os.environ.get("APP_URL", "").rstrip("/")
        self.token = os.environ.get("WORKER_TOKEN", "")

    def _post(self, pfad: str, body: dict) -> dict:
        req = urllib.request.Request(
            f"{self.basis}{pfad}", data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json", "User-Agent": USER_AGENT})
        letzte = None
        for versuch in range(8):
            try:
                with urllib.request.urlopen(req, timeout=90) as antwort:
                    return json.loads(antwort.read().decode())
            except Exception as ex:  # noqa: BLE001
                letzte = ex
                wartezeit = min(60, 3 * 2 ** versuch) + random.uniform(0, 5)
                log(f"  POST {pfad} fehlgeschlagen ({ex}) — Versuch {versuch + 2}/8 in {wartezeit:.0f}s")
                time.sleep(wartezeit)
        raise RuntimeError(f"POST {pfad} endgültig fehlgeschlagen: {letzte}")

    def arbeit(self, limit: int) -> tuple[list[dict], int]:
        a = self._post("/api/fabrik2/pruefung-arbeit", {"limit": limit})
        return a.get("leads", []), int(a.get("rest", 0) or 0)

    def ergebnis(self, body: dict) -> None:
        self._post("/api/fabrik2/pruefung-ergebnis", body)


# ── Normalisierung ────────────────────────────────────────────────────
def _norm(text: str) -> str:
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e"), ("è", "e")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def _ziffern(text: str) -> str:
    return re.sub(r"\D", "", text)


def _telefon_kern(phone: str) -> str:
    """Nationale Ziffernfolge ohne Länderkennung und ohne führende 0."""
    z = _ziffern(phone)
    if z.startswith("0049"):
        z = z[4:]
    elif z.startswith("49") and len(z) >= 11:
        z = z[2:]
    return z.lstrip("0")


def _domain(url: str) -> str:
    host = urllib.parse.urlsplit(url if "//" in url else f"https://{url}").netloc.lower()
    return re.sub(r"^www\.", "", host)


def _website_url(website: str) -> str:
    w = (website or "").strip()
    if not w:
        return ""
    return w if "//" in w else f"https://{w}"


# ── Seiten laden ──────────────────────────────────────────────────────
def lade_seiten(website: str) -> tuple[dict[str, str], str]:
    """Startseite + Impressum/Kontakt/Über-mich. Rückgabe: {url: html}, Fehlertext."""
    url = _website_url(website)
    geladen: dict[str, str] = {}
    status, html, fehler = 0, "", ""
    for versuch in range(2):
        try:
            status, html = hole(url)
            fehler = ""
        except Exception as ex:  # noqa: BLE001
            status, html, fehler = 0, "", f"Website nicht erreichbar ({type(ex).__name__})"
        if html and status < 400:
            break
        if status not in (0, 429, 502, 503, 504):
            break
        if versuch == 0:
            time.sleep(5)
    if fehler:
        return {}, fehler
    if status >= 400 or not html:
        return {}, f"Website nicht erreichbar (HTTP {status})"
    geladen[url] = html
    kandidaten: list[str] = []
    try:
        imp = web.impressum_finden(website, hole=hole)
        if imp:
            kandidaten.append(imp)
    except Exception:  # noqa: BLE001
        pass
    for u in namens_urls(website):
        if u not in kandidaten:
            kandidaten.append(u)
    for u in kandidaten[:MAX_SEITEN]:
        if u in geladen:
            continue
        try:
            s, h = hole(u)
            if s < 400 and h:
                geladen[u] = h
        except Exception:  # noqa: BLE001
            continue
    return geladen, ""


# ── Prüfung ───────────────────────────────────────────────────────────
def pruefe(lead: dict) -> dict:
    name = (lead.get("name") or "").strip()
    phone = (lead.get("phone") or "").strip()
    email = (lead.get("email") or "").strip().lower()
    website = (lead.get("website") or "").strip()
    checks: dict = {"name": None, "telefon": None, "email": None, "website": None}
    maengel: list[str] = []

    if not website:
        return {"ergebnis": "maengel", "text": "geprüft: keine Website hinterlegt",
                "checks": {**checks, "website": False}}

    geladen, fehler = lade_seiten(website)
    if fehler:
        return {"ergebnis": "fehler", "text": f"geprüft: {fehler}", "checks": {**checks, "website": False}}
    checks["website"] = True
    checks["seiten"] = len(geladen)

    texte = [html_zu_text(h) for h in geladen.values()]
    voll = _norm(" ".join(texte))
    roh = " ".join(geladen.values())

    # Fremde Website (Portal, Verzeichnis, Behörde)
    if FREMD_MUSTER.search(_domain(website)) or FREMD_MUSTER.search(_norm(website)):
        maengel.append("Website ist ein Portal/Verzeichnis")
        checks["website"] = "fremd"

    # Name: erst Plausibilität (Personenname, 2–3 Wörter, Vorname bekannt), dann Abgleich mit Website
    name_ohne_titel = TITEL_MUSTER.sub("", name).strip() or name
    name_kern = PARTIKEL_MUSTER.sub(" ", " " + name_ohne_titel).strip() or name_ohne_titel
    worte = [w for w in re.split(r"\s+", name_kern) if w]
    teile = [t for t in re.split(r"[\s-]+", _norm(name_kern)) if len(t) >= 2]
    if KEIN_PERSONENNAME.search(name_ohne_titel) or QUATSCH_MUSTER.search(name_kern):
        checks["name"] = False
        maengel.append("kein Personenname")
    elif len(worte) < 2 or len(worte) > 3 or len(teile) < 2:
        checks["name"] = False
        maengel.append("Name unvollständig")
    else:
        vorname, nachname = teile[0], teile[-1]
        vorname_bekannt = vorname in VORNAMEN_LEX or (len(teile) >= 3 and teile[1] in VORNAMEN_LEX)
        vn_da = re.search(r"\b" + re.escape(vorname) + r"\b", voll) is not None
        nn_da = re.search(r"\b" + re.escape(nachname) + r"\b", voll) is not None
        # Unbekannter Vorname (nicht im Lexikon): Name muss als ganze Wortfolge auf der Website stehen
        ganz_da = re.search(r"\b" + re.escape(vorname) + r"\b(?:\W+\w+){0,2}?\W+" + re.escape(nachname) + r"\b", voll) is not None \
            or re.search(r"\b" + re.escape(nachname) + r"\b\W+" + re.escape(vorname) + r"\b", voll) is not None
        checks["vorname_lexikon"] = vorname_bekannt
        if vn_da and nn_da and (vorname_bekannt or ganz_da):
            checks["name"] = True
        elif vn_da and nn_da:
            checks["name"] = "getrennt"
            maengel.append("Vorname unbekannt, Name nicht als Ganzes auf Website")
        elif nn_da:
            checks["name"] = "nachname"
            maengel.append("Vorname nicht auf Website")
        else:
            checks["name"] = False
            maengel.append("Name nicht auf Website")

    # Solo-Check (Impressum/Startseite): Team, Filialen, GmbH → Rückhand
    solo_treffer = KEIN_SOLO_MUSTER.search(voll)
    if solo_treffer:
        checks["solo"] = False
        maengel.append(f"kein Solo-Betrieb ({solo_treffer.group(0).strip()[:30]})")
    else:
        checks["solo"] = True

    # Telefon: Handy-Pflicht (Justin 13.09.). Lead-Nummer auf der Website?
    # Ist die Lead-Nummer Festnetz, Handynummer von der Website nachtragen.
    seiten_ziffern = _ziffern(roh)
    kern = _telefon_kern(phone)
    ist_handy = kern.startswith(("15", "16", "17"))
    nachtrag: dict = {}
    if len(kern) >= 7 and kern in seiten_ziffern:
        checks["telefon"] = True
    else:
        checks["telefon"] = False
    if not ist_handy:
        handys = [h for h in HANDY_MUSTER.findall(roh) if len(_telefon_kern(h)) >= 10]
        if handys:
            nachtrag["phone"] = re.sub(r"\s+", " ", handys[0]).strip()
            checks["handy_nachgetragen"] = True
            checks["telefon"] = True
            ist_handy = True
        else:
            maengel.append("keine Handynummer (nur Festnetz)")
    elif not checks["telefon"]:
        maengel.append("Handynummer nicht auf Website")

    # E-Mail: Pflicht (Justin 13.09.). Fehlt sie, von der Website nachtragen.
    dom_web = _domain(website)
    if email and "@" in email:
        dom_mail = email.split("@", 1)[1]
        if dom_mail == dom_web or (dom_web and dom_mail.endswith("." + dom_web)) or email in roh.lower():
            checks["email"] = True
        else:
            checks["email"] = False
            maengel.append("E-Mail passt nicht zur Website")
    else:
        kandidaten = [m for m in MAIL_MUSTER.findall(roh) if not MAIL_SPERRE.search(m)]
        eigene = [m for m in kandidaten if dom_web and m.lower().split("@", 1)[1] == dom_web]
        wahl = (eigene or kandidaten)[:1]
        if wahl:
            nachtrag["email"] = wahl[0].lower()
            checks["email"] = True
            checks["email_nachgetragen"] = True
        else:
            checks["email"] = False
            maengel.append("keine E-Mail gefunden")

    alles_ok = (checks["name"] is True and checks["telefon"] is True and ist_handy
                and checks["email"] is True and checks["website"] is True and checks["solo"] is True)
    if alles_ok:
        return {"ergebnis": "ok", "text": "geprüft ✓", "checks": checks, "nachtrag": nachtrag}
    return {"ergebnis": "maengel", "text": ("geprüft: " + "; ".join(maengel))[:200], "checks": checks, "nachtrag": nachtrag}


def bearbeite(app: App, lead: dict, zaehler: dict, lock: threading.Lock) -> None:
    try:
        erg = pruefe(lead)
    except Exception as ex:  # noqa: BLE001
        erg = {"ergebnis": "fehler", "text": f"geprüft: Prüfung abgebrochen ({type(ex).__name__})", "checks": {}}
    try:
        app.ergebnis({"lead_id": lead["id"], **erg})
    except Exception as ex:  # noqa: BLE001
        log(f"  Ergebnis für {lead['id']} nicht meldbar: {ex}")
        with lock:
            zaehler["nicht_gemeldet"] += 1
        return
    with lock:
        zaehler[erg["ergebnis"]] += 1
        zaehler["fertig"] += 1
        if zaehler["fertig"] % 25 == 0:
            log(f"  {zaehler['fertig']} geprüft — ok {zaehler['ok']}, Mängel {zaehler['maengel']}, Fehler {zaehler['fehler']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args()
    app = App()
    if not app.basis or not app.token:
        log("APP_URL/WORKER_TOKEN fehlen")
        return 2
    leads, rest = app.arbeit(args.limit)
    log(f"Prüfung: {len(leads)} Leads reserviert, {max(0, rest - len(leads))} danach noch offen")
    zaehler = {"fertig": 0, "ok": 0, "maengel": 0, "fehler": 0, "nicht_gemeldet": 0}
    lock = threading.Lock()
    start = time.time()
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        for lead in leads:
            pool.submit(bearbeite, app, lead, zaehler, lock)
    dauer = time.time() - start
    log(f"Fertig: {zaehler} in {dauer:.0f}s")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"rest={max(0, rest - len(leads))}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"Prüfung: {zaehler['fertig']} Leads — ok {zaehler['ok']}, Mängel {zaehler['maengel']}, "
                     f"Fehler {zaehler['fehler']} · {dauer:.0f}s · danach offen: {max(0, rest - len(leads))}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
