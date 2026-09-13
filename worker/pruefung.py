"""
Prüf-Worker (D-120, 13.09.2026): kontrolliert fertige Fabrik-2-Leads gegen
ihre Website — ohne KI, nur Regeln. Justin: „einen Worker, der die neuen
Leads alle überprüft: Name richtig, Website, Telefonnummer, Ansprechperson,
E-Mail".

Je Lead:
  1. Website laden (Startseite; dazu Impressum/Kontakt/Über-mich-Seiten,
     höchstens vier). Nicht ladbar → „Website nicht erreichbar".
  2. Name: Vor- UND Nachname müssen auf einer der Seiten stehen. Nur der
     Nachname → „Vorname nicht auf Website"; gar nichts → „Name nicht auf
     Website" (dann ist die Ansprechperson wahrscheinlich falsch zugeordnet).
  3. Telefon: die Ziffernfolge der Lead-Nummer (ab der Vorwahl, ohne Länder-
     kennung) muss in der ziffernbereinigten Seite vorkommen.
  4. E-Mail (nur wenn vorhanden): Domain gleich Website-Domain ODER Adresse
     steht auf einer Seite. Sonst weicher Mangel.
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
from namen import html_zu_text, namens_urls  # noqa: E402

USER_AGENT = "lead-maschine-pruefung/1.0"
PARALLEL = 4
MAX_SEITEN = 4

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
    status, html = 0, ""
    try:
        status, html = hole(url)
    except Exception as ex:  # noqa: BLE001
        return {}, f"Website nicht erreichbar ({type(ex).__name__})"
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

    # Name
    teile = [t for t in re.split(r"[\s-]+", _norm(name)) if len(t) >= 2]
    if len(teile) >= 2:
        vorname, nachname = teile[0], teile[-1]
        vn_da = re.search(r"\b" + re.escape(vorname) + r"\b", voll) is not None
        nn_da = re.search(r"\b" + re.escape(nachname) + r"\b", voll) is not None
        if vn_da and nn_da:
            checks["name"] = True
        elif nn_da:
            checks["name"] = "nachname"
            maengel.append("Vorname nicht auf Website")
        else:
            checks["name"] = False
            maengel.append("Name nicht auf Website")
    else:
        checks["name"] = False
        maengel.append("Name unvollständig")

    # Telefon
    kern = _telefon_kern(phone)
    if len(kern) >= 7:
        seiten_ziffern = _ziffern(roh)
        checks["telefon"] = kern in seiten_ziffern
        if not checks["telefon"]:
            maengel.append("Telefon nicht auf Website")
    else:
        checks["telefon"] = False
        maengel.append("Telefonnummer unplausibel")

    # E-Mail (weicher Mangel)
    if email and "@" in email:
        dom_mail = email.split("@", 1)[1]
        dom_web = _domain(website)
        if dom_mail == dom_web or (dom_web and dom_mail.endswith("." + dom_web)) or email in roh.lower():
            checks["email"] = True
        else:
            checks["email"] = False
            maengel.append("E-Mail passt nicht zur Website")
    else:
        checks["email"] = None

    if checks["name"] is True and checks["telefon"] is True and checks["website"] is True:
        return {"ergebnis": "ok", "text": "geprüft ✓", "checks": checks}
    return {"ergebnis": "maengel", "text": ("geprüft: " + "; ".join(maengel))[:200], "checks": checks}


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
