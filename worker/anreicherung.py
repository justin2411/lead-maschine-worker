#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stapel-Anreicherung (M3) — Modul-Kette 1–10 über die Treffer eines
Suchlaufs (E-3 = Stapel-Modus Pflicht) oder eine einzelne Firma.

Nutzt das gemeinsame Paket `leadkern` (M0) für alle Prüf- und
Normalisierungslogik. Parallelität: 5 Firmen gleichzeitig, Drosselung
1 Anfrage/Sekunde JE ZIEL-DOMAIN. Fortschritt wird alle 20 Firmen an
die App gemeldet, jedes Ergebnis einzeln (Diff + Modul-Status + Ampel).

Module (Umsetzungsplan §4, angewendet auf Fabrik 2):
  1  Name Normalizer         leadkern.normalisierung (Inhaber-Kandidat)
  2  Existenz-Check          Short-Circuit: Website tot UND Quelle alt -> verworfen
  3  Gelbe Seiten            ÜBERSPRUNGEN bis M5 (Quellen-Reihenfolge, Auftrag v2)
  4  Website-Finder          DuckDuckGo-HTML-Suche, nur wenn Website fehlt
  5  URL-Checker             leadkern.web.url_pruefen (Titel muss passen)
  6  Website-Auslesen        Impressum-/Kontakt-Seite laden (max. 5 Seiten, 10 s)
  7  KI-Analyse              Claude-API (ANTHROPIC_API_KEY) — ohne Key übersprungen
  8  E-Mail-Validierung      leadkern.email.validieren (MX, generisch markieren)
  9  Zweitquellen-Abgleich   Impressum-Telefon vs. Quellen-Telefon -> Konflikt
  10 Finale Validierung      KI-Gesamtbild -> Ampel; ohne Key: Regel-Ampel

Fehlerverhalten: Modul-Fehler bricht die Kette NICHT ab (außer Modul 2),
sondern steht im Modul-Status. Jede Anreicherung ist wiederholbar.
Kosten-Deckel: ANREICHERUNG_MAX_PRO_LAUF (Default 500).
"""

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from leadkern import drossel, email as lk_email, normalisierung, web

USER_AGENT = "LeadMaschine2-Suchlauf/1.0 (+https://github.com/justin2411/lead-maschine-worker)"
PARALLEL = 5
MELDE_TAKT = 20
KI_MODELL = "claude-haiku-4-5-20251001"


def log(msg: str) -> None:
    print(msg, flush=True)


# ── Drosselung je Ziel-Domain (1 Anfrage/s, über alle Threads) ────────
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


# ── App-Anbindung ────────────────────────────────────────────────────
class App:
    def __init__(self):
        self.basis = os.environ.get("APP_URL", "").rstrip("/")
        self.token = os.environ.get("WORKER_TOKEN", "")

    def _req(self, methode: str, pfad: str, body: dict | None = None) -> dict:
        daten = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.basis}{pfad}", data=daten, method=methode,
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json", "User-Agent": USER_AGENT})
        letzte = None
        for versuch in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as antwort:
                    return json.loads(antwort.read().decode())
            except Exception as ex:  # noqa: BLE001
                letzte = ex
                time.sleep(2 ** (versuch + 1))
        raise RuntimeError(f"{methode} {pfad} endgültig fehlgeschlagen: {letzte}")

    def arbeit(self, suchlauf_id: str, firma_id: str, limit: int) -> list[dict]:
        q = []
        if suchlauf_id:
            q.append(f"suchlauf_id={urllib.parse.quote(suchlauf_id)}")
        if firma_id:
            q.append(f"firma_id={urllib.parse.quote(firma_id)}")
        if limit:
            q.append(f"limit={limit}")
        return self._req("GET", f"/api/fabrik2/anreicherung-arbeit?{'&'.join(q)}").get("firmen", [])

    def ergebnis(self, body: dict) -> None:
        self._req("POST", "/api/fabrik2/anreicherung-ergebnis", body)

    def status(self, suchlauf_id: str, status: str, zaehler: dict) -> None:
        if not suchlauf_id:
            return
        self._req("POST", "/api/fabrik2/anreicherung-status",
                  {"suchlauf_id": suchlauf_id, "anreicherung_status": status, "zaehler": zaehler})


# ── KI-Anbindung (Modul 7 + 10) — ohne Key sauber übersprungen ───────
_ki_lock = threading.Lock()
KI_CALLS = {"n": 0}  # Kostenanzeige (D-088): jede Abfrage zählt


def ki_abfrage(prompt: str) -> dict | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    with _ki_lock:
        KI_CALLS["n"] += 1
    body = json.dumps({
        "model": KI_MODELL, "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body, method="POST",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as antwort:
        text = json.loads(antwort.read().decode())["content"][0]["text"]
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0)) if m else None


PORTAL_DOMAINS = (
    "gelbeseiten", "11880", "dasoertliche", "golocal", "yelp", "facebook",
    "instagram", "branchenbuch", "werkenntdenbesten", "firmenwissen",
    "northdata", "wikipedia", "kununu", "duckduckgo",
)


def website_suchen(name: str, ort: str) -> str:
    """Modul 4: DuckDuckGo-HTML-Suche (1 Anfrage, ehrlicher User-Agent)."""
    frage = urllib.parse.quote_plus(f"{name} {ort}".strip())
    status, html = hole(f"https://html.duckduckgo.com/html/?q={frage}", timeout=10)
    quelle = drossel.Quelle("duckduckgo")
    quelle.pruefe_antwort(status, html)  # Captcha/Sperre -> QuelleGesperrt
    if status != 200 or not html:
        return ""
    for m in re.finditer(r'href="([^"]+)"', html):
        url = m.group(1)
        if "uddg=" in url:  # DDG-Weiterleitung entpacken
            qs = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            url = (qs.get("uddg") or [""])[0]
        if not url.startswith("http"):
            continue
        netloc = urllib.parse.urlsplit(url).netloc.lower()
        if any(p in netloc for p in PORTAL_DOMAINS):
            continue
        return f"https://{netloc}"
    return ""


# ── Die Kette ────────────────────────────────────────────────────────
def kette(firma: dict) -> dict:
    start = time.monotonic()
    module: dict[str, str] = {}
    diff: dict[str, object] = {}
    felder: dict[str, str] = {}
    kontakte: list[dict] = []
    konflikte: list[str] = []
    verworfen_grund = ""

    name = firma.get("name") or ""
    website = (firma.get("website") or "").strip()
    telefon = (firma.get("telefon") or "").strip()
    email_alt = (firma.get("email") or "").strip()

    # ── Sparschaltung (D-088): sind ALLE 4 Parameter schon da
    # (Ansprechperson mit Vor+Nachname, Telefon, E-Mail, Zielgruppe),
    # braucht es keine Web-/KI-Schritte — nur E-Mail-Check + Ampel.
    kontakte_da = [k for k in (firma.get("kontakte") or [])
                   if len(str(k.get("name") or "").split()) >= 2]
    if kontakte_da and telefon and email_alt and (firma.get("branche") or "").strip():
        module["1_name"] = "ok"
        module["vollstaendig"] = "Module 2–9 übersprungen (alle 4 Parameter vorhanden)"
        ampel = "gruen"
        try:
            pruefung = lk_email.validieren(email_alt)
            diff["email_pruefung"] = pruefung
            module["8_email"] = pruefung["status"]
            if pruefung["status"] == "ungueltig":
                konflikte.append("email_ungueltig")
                ampel = "gelb"
        except Exception as ex:  # noqa: BLE001
            module["8_email"] = f"fehler: {ex}"
        if konflikte:
            diff["konflikte"] = konflikte
        diff["vollstaendig"] = True
        module["10_final"] = "ok (regeln, 0 KI-Calls)"
        return {
            "firma_id": firma["id"], "modul_status": module, "ergebnis_diff": diff,
            "felder": {}, "kontakte": [],  # bestehende Kontakte bleiben unangetastet
            "ampel": ampel, "verworfen_grund": "",
            "dauer_ms": int((time.monotonic() - start) * 1000),
        }

    # 1 · Name Normalizer
    kandidat = normalisierung.inhaber_kandidat(name)
    if kandidat:
        diff["inhaber_kandidat"] = kandidat
    module["1_name"] = "ok"

    # 2 · Existenz-Check (Short-Circuit)
    web_lebt = None
    if website:
        try:
            pruefung = hole_pruefung(website, name)
            web_lebt = pruefung["erreichbar"] and not pruefung["ist_parkplatz"]
            diff["url_pruefung"] = pruefung
        except Exception as ex:  # noqa: BLE001
            module["2_existenz"] = f"fehler: {ex}"
    quelle_frisch = quelle_juenger_24_monate(firma.get("quellen"))
    tel_plausibel = normalisierung.telefon(telefon)["art"] != "ungueltig" if telefon else False
    if website and web_lebt is False and not quelle_frisch:
        verworfen_grund = "Existenz-Check: Website tot und keine frische Quelle"
        module["2_existenz"] = "short_circuit"
        return abschluss(module, diff, felder, kontakte, konflikte, verworfen_grund, start, firma)
    module.setdefault("2_existenz", "ok" if (web_lebt or quelle_frisch or tel_plausibel) else "schwach")

    # 3 · Gelbe Seiten — erst mit M5 (Quellen-Reihenfolge, Auftrag v2)
    module["3_gelbe_seiten"] = "uebersprungen"

    # 4+5 · Website-Finder + URL-Checker
    if not website:
        try:
            gefunden = website_suchen(name, firma.get("ort") or "")
            if gefunden:
                pruefung = hole_pruefung(gefunden, name)
                if pruefung["erreichbar"] and pruefung["titel_passt"] and not pruefung["ist_parkplatz"]:
                    website = gefunden
                    felder["website"] = gefunden
                    module["4_website_finder"] = "ok"
                else:
                    # falsche Website ist schlimmer als keine
                    module["4_website_finder"] = "verworfen (Titel passt nicht)"
            else:
                module["4_website_finder"] = "nichts gefunden"
        except drossel.QuelleGesperrt as ex:
            module["4_website_finder"] = f"gesperrt: {ex}"
        except Exception as ex:  # noqa: BLE001
            module["4_website_finder"] = f"fehler: {ex}"
    else:
        module["4_website_finder"] = "uebersprungen (Website vorhanden)"
    module["5_url_check"] = "ok" if web_lebt else ("fehler" if website and web_lebt is False else "ohne Website")

    # 6+7 · Impressum laden + auslesen (KI optional)
    if website and web_lebt is not False:
        try:
            imp_url = web.impressum_finden(website, hole=hole)
            geladen = 0
            impressum = {}
            for url in [u for u in (imp_url, f"{website.rstrip('/')}/kontakt") if u]:
                if geladen >= 5:
                    break
                status_code, html = hole(url, timeout=10)
                geladen += 1
                if status_code == 200 and html:
                    impressum = web.impressum_auslesen(html, ki_abfrage=ki_abfrage)
                    if impressum.get("nachname"):
                        break
            if impressum:
                module["6_website_auslesen"] = "ok"
                module["7_ki_analyse"] = "ok" if os.environ.get("ANTHROPIC_API_KEY") else "uebersprungen (kein Key)"
                if impressum.get("nachname"):
                    kontakte.append({
                        "name": f'{impressum.get("vorname", "")} {impressum["nachname"]}'.strip(),
                        "rolle": impressum.get("rolle") or "",
                        "email": impressum.get("email") or "",
                        "telefon": impressum.get("telefon") or "",
                        "quelle": "impressum",
                    })
                    diff["ist_einzelperson"] = bool(impressum.get("ist_einzelperson"))
                if impressum.get("email") and not email_alt:
                    felder["email"] = impressum["email"]
                imp_tel = (impressum.get("telefon") or "").strip()
                if imp_tel:
                    imp_art = normalisierung.telefon(imp_tel)["art"]
                    if not telefon:
                        felder["telefon"] = imp_tel
                    elif imp_art == "mobil" and normalisierung.telefon(telefon)["art"] == "festnetz":
                        # Handy-Fokus: Mobilnummer schlägt Festnetz
                        felder["telefon"] = imp_tel
                        diff["telefon_vorher"] = telefon
                    # 9 · Zweitquellen-Abgleich (Impressum vs. Quelle)
                    if telefon and normalisierung.telefon(imp_tel)["key"] and \
                       normalisierung.telefon(telefon)["key"] and \
                       normalisierung.telefon(imp_tel)["key"] != normalisierung.telefon(telefon)["key"] and \
                       imp_art != "mobil":
                        konflikte.append("telefon_widerspruch")
            else:
                module["6_website_auslesen"] = "kein Impressum gefunden"
        except Exception as ex:  # noqa: BLE001
            module["6_website_auslesen"] = f"fehler: {ex}"
    else:
        module["6_website_auslesen"] = "ohne Website"
    module.setdefault("7_ki_analyse", "uebersprungen")
    module["9_zweitquellen"] = "konflikt" if konflikte else "ok"

    # 8 · E-Mail-Validierung
    email_neu = felder.get("email") or email_alt
    if email_neu:
        try:
            pruefung = lk_email.validieren(email_neu)
            diff["email_pruefung"] = pruefung
            if pruefung["status"] == "ungueltig":
                konflikte.append("email_ungueltig")
                felder.pop("email", None)
            for k in kontakte:
                if k.get("email") == email_neu:
                    k["validiert"] = pruefung["status"] == "gueltig"
            module["8_email"] = pruefung["status"]
        except Exception as ex:  # noqa: BLE001
            module["8_email"] = f"fehler: {ex}"
    else:
        module["8_email"] = "keine E-Mail"

    if konflikte:
        diff["konflikte"] = konflikte
    return abschluss(module, diff, felder, kontakte, konflikte, verworfen_grund, start, firma)


def hole_pruefung(url: str, name: str) -> dict:
    return web.url_pruefen(url, name, hole=hole)


def quelle_juenger_24_monate(quellen) -> bool:
    if not isinstance(quellen, list):
        return False
    grenze = time.time() - 24 * 30.44 * 86400
    for q in quellen:
        gesehen = str((q or {}).get("gesehen_am") or "")
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", gesehen)
        if m and time.mktime((int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, 0, 0, 0, -1)) > grenze:
            return True
    return False


def abschluss(module, diff, felder, kontakte, konflikte, verworfen_grund, start, firma) -> dict:
    # 10 · Finale Validierung -> Ampel
    ampel = None
    if verworfen_grund:
        ampel = "rot"
        module["10_final"] = "verworfen"
    else:
        ki = None
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                ki = ki_abfrage(
                    "Du prüfst einen angereicherten Firmen-Lead (deutsche Solo-/Kleinbetriebe, "
                    "Zielgruppe Altersvorsorge-Beratung). Gib NUR JSON zurück: "
                    '{"ampel": "gruen"|"gelb"|"rot", "grund": "..."}. '
                    "gruen = Daten stimmig und übernehmbar. "
                    "gelb = Lücken oder Konflikte, bitte von Hand sichten — auch SPÄRLICHE "
                    "Daten (nur Name+Telefon+Ort, keine Website) sind gelb, nicht rot: "
                    "Kleinbetriebe haben oft keinen Webauftritt. "
                    "rot = NUR bei aktiven Widersprüchen oder klaren Fehl-Treffern "
                    "(z. B. Name ist eine Einrichtung/Kette, Telefon passt sicher nicht, "
                    "Daten wirken erfunden).\n\nDaten:\n" + json.dumps({
                        "firma": {k: firma.get(k) for k in ("name", "plz", "ort", "telefon", "website", "email", "branche")},
                        "neue_felder": felder, "kontakte": kontakte,
                        "konflikte": konflikte, "diff": {k: v for k, v in diff.items() if k != "url_pruefung"},
                    }, ensure_ascii=False))
            except Exception as ex:  # noqa: BLE001
                module["10_final"] = f"ki_fehler: {ex}"
        if ki and ki.get("ampel") in ("gruen", "gelb", "rot"):
            ampel = ki["ampel"]
            diff["ampel_grund"] = str(ki.get("grund") or "")[:300]
            module["10_final"] = "ok (ki)"
        else:
            # Regel-Ampel ohne KI: Kontakt + Telefon + keine Konflikte = grün
            telefon_da = bool(felder.get("telefon") or firma.get("telefon"))
            ampel = "gruen" if (kontakte and telefon_da and not konflikte) else "gelb"
            module.setdefault("10_final", "ok (regeln)")
    return {
        "firma_id": firma["id"],
        "modul_status": module,
        "ergebnis_diff": diff,
        "felder": felder,
        "kontakte": kontakte[:10],
        "ampel": ampel,
        "verworfen_grund": verworfen_grund,
        "dauer_ms": int((time.monotonic() - start) * 1000),
    }


# ── Stapel-Steuerung ─────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Stapel-Anreicherung (Fabrik 2, M3)")
    parser.add_argument("--suchlauf-id", default="")
    parser.add_argument("--firma-id", default="")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if not args.suchlauf_id and not args.firma_id:
        log("FEHLER: --suchlauf-id oder --firma-id nötig.")
        return 1
    app = App()
    if not app.basis or not app.token:
        log("FEHLER: APP_URL und WORKER_TOKEN müssen gesetzt sein.")
        return 1

    deckel = int(os.environ.get("ANREICHERUNG_MAX_PRO_LAUF", "500") or 500)
    limit = min(args.limit, deckel) if args.limit else deckel

    firmen = app.arbeit(args.suchlauf_id, args.firma_id, limit)
    log(f"Anreicherung: {len(firmen)} Firmen (Deckel {deckel}, Parallelität {PARALLEL})")
    zaehler = {"gesamt": len(firmen), "fertig": 0, "gruen": 0, "gelb": 0, "rot": 0,
               "verworfen": 0, "ki_calls": 0}
    if not firmen:
        app.status(args.suchlauf_id, "fertig", zaehler)
        return 0
    app.status(args.suchlauf_id, "laeuft", zaehler)

    lock = threading.Lock()

    def bearbeite(firma: dict) -> None:
        try:
            ergebnis = kette(firma)
        except Exception as ex:  # noqa: BLE001 — eine Firma reißt den Stapel nicht mit
            log(f"  FEHLER bei '{firma.get('name')}': {ex}")
            ergebnis = {
                "firma_id": firma["id"], "modul_status": {"kette": f"fehler: {ex}"},
                "ergebnis_diff": {}, "felder": {}, "kontakte": [],
                "ampel": "gelb", "verworfen_grund": "", "dauer_ms": 0,
            }
        app.ergebnis(ergebnis)
        with lock:
            zaehler["fertig"] += 1
            if ergebnis["verworfen_grund"]:
                zaehler["verworfen"] += 1
            elif ergebnis["ampel"] in zaehler:
                zaehler[ergebnis["ampel"]] += 1
            zaehler["ki_calls"] = KI_CALLS["n"]
            if zaehler["fertig"] % MELDE_TAKT == 0:
                app.status(args.suchlauf_id, "laeuft", dict(zaehler))
                log(f"  {zaehler['fertig']}/{zaehler['gesamt']} … "
                    f"(grün {zaehler['gruen']}, gelb {zaehler['gelb']}, verworfen {zaehler['verworfen']})")

    try:
        with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
            list(pool.map(bearbeite, firmen))
        zaehler["ki_calls"] = KI_CALLS["n"]
        app.status(args.suchlauf_id, "fertig", zaehler)
        log(f"Anreicherung fertig: {json.dumps(zaehler)} "
            f"(KI-Kosten grob: ~{KI_CALLS['n'] * 0.25:.0f} Cent)")
        return 0
    except Exception as ex:  # noqa: BLE001
        log(f"FEHLER im Stapel: {ex}")
        try:
            app.status(args.suchlauf_id, "fehler", zaehler)
        except Exception:  # noqa: BLE001
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
