#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verbands-Konnektor (M5, D-089) — liest freigegebene Verbands-/
Verzeichnisquellen aus und meldet Treffer MIT Ansprechperson an die App.

Regeln (M-2, verbindlich): ehrlicher User-Agent, 1 Anfrage/Sekunde je
Domain, harter Seiten-Deckel je Quelle, Stopp bei Sperr-Signalen
(Captcha/429/403-Serie) — Sperren werden protokolliert, nie überwunden.
Nur Quellen aus worker/quellen.py (= von Justin freigegeben).

Extraktion: Seitentext (HTML→Text bzw. PDF via pypdf) wird in Blöcken
an die Claude-API gegeben, die Einträge als JSON liefert (Name, Telefon,
E-Mail, Website, Ort, PLZ). Ohne ANTHROPIC_API_KEY greift ein einfaches
Regel-Fallback (E-Mail-Anker + Umfeld). Kosten: ~0,25 Cent je Block.

Aufruf (aus suchlauf.yml): --branche <key> --quellen <csv> --suchlauf-id
<uuid> --limit <n>. Läuft nur, wenn quellen mindestens einen
verband_*-Schlüssel der Branche enthält.
"""

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from leadkern import drossel, normalisierung

from quellen import QUELLEN, BRANCHE_ZU_QUELLEN
from anreicherung import App, ki_abfrage, KI_CALLS, drossle

USER_AGENT = "LeadMaschine2-Suchlauf/1.0 (+https://github.com/justin2411/lead-maschine-worker)"
PAKET_GROESSE = 100
BLOCK_ZEICHEN = 6000


def log(msg: str) -> None:
    print(msg, flush=True)


def hole_roh(url: str, timeout: int = 20) -> tuple[int, bytes]:
    drossle(url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as antwort:
            return antwort.status, antwort.read(8_000_000)
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, b""
    except Exception:
        return 0, b""


def html_zu_text(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    # mailto-/tel-Links sichtbar machen, bevor die Tags fallen
    text = re.sub(r'href="mailto:([^"?]+)[^"]*"', r'> E-Mail: \1 <', text)
    text = re.sub(r'href="tel:([^"]+)"', r'> Telefon: \1 <', text)
    text = re.sub(r'href="(https?://[^"]+)"', r'> Web: \1 <', text)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</td>|</tr>|</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    for a, b in (("&amp;", "&"), ("&nbsp;", " "), ("&auml;", "ä"), ("&ouml;", "ö"),
                 ("&uuml;", "ü"), ("&szlig;", "ß"), ("&Auml;", "Ä"), ("&Ouml;", "Ö"), ("&Uuml;", "Ü")):
        text = text.replace(a, b)
    return re.sub(r"[ \t]+", " ", text)


def pdf_zu_text(daten: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(daten))
    return "\n".join((seite.extract_text() or "") for seite in reader.pages)


EXTRAKTIONS_PROMPT = (
    "Du liest einen Ausschnitt aus einem öffentlichen Verbands-/Branchenverzeichnis "
    "(deutsche Selbstständige). Extrahiere ALLE Einträge als JSON-Array:\n"
    '[{"name": "Vorname Nachname (oder Betriebsname)", "telefon": "", "email": "", '
    '"website": "", "ort": "", "plz": ""}]\n'
    "Nur Werte, die WIRKLICH im Text stehen — nichts erfinden, fehlende Felder leer. "
    "Verbands-/Vereins-Kontakte (Geschäftsstelle, Vorstand, info@verband…) auslassen. "
    "Gib NUR das JSON-Array zurück.\n\nText:\n"
)


def ki_extraktion(text: str) -> list[dict]:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    eintraege: list[dict] = []
    bloecke = [text[i:i + BLOCK_ZEICHEN] for i in range(0, len(text), BLOCK_ZEICHEN - 300)]
    for block in bloecke:
        if not re.search(r"@|Telefon|Tel\.|\d{4,}", block):
            continue  # Block ohne Kontaktdaten spart den Call
        if key:
            try:
                antwort = ki_abfrage(EXTRAKTIONS_PROMPT + block)
                # ki_abfrage parst das ERSTE {...}-Objekt — für Arrays selbst parsen
                if isinstance(antwort, dict):
                    antwort = [antwort]
                if isinstance(antwort, list):
                    eintraege.extend(e for e in antwort if isinstance(e, dict))
                    continue
            except Exception as ex:  # noqa: BLE001
                log(f"  KI-Extraktion fehlgeschlagen ({ex}) — Regel-Fallback")
        eintraege.extend(regel_extraktion(block))
    return eintraege


_ETIKETTEN = {"telefon", "tel", "mobil", "handy", "fax", "mail", "e-mail", "email",
              "web", "www", "kontakt", "adresse", "internet", "homepage", "e"}


def _naechster(muster: str, umfeld: str, ref: int):
    """Der Treffer, der der Referenz-Position am nächsten liegt."""
    bester, abstand = None, 10**9
    for m in re.finditer(muster, umfeld):
        d = min(abs(m.start() - ref), abs(m.end() - ref))
        if d < abstand:
            bester, abstand = m, d
    return bester


def regel_extraktion(text: str) -> list[dict]:
    """Fallback ohne KI: E-Mail als Anker; Telefon/PLZ = nächstliegender
    Treffer (damit nicht der Nachbar-Eintrag zugeordnet wird)."""
    eintraege = []
    for m in re.finditer(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
        start = max(0, m.start() - 350)
        umfeld = text[start:m.end() + 100]
        ref = m.start() - start
        tel = _naechster(r"(?:\+49|0)[\d\s/()\-\.]{6,18}\d", umfeld, ref)
        plz = _naechster(r"\b\d{5}\b", umfeld, ref)
        name = ""
        for zeile in reversed(text[start:m.start()].splitlines()):
            if re.search(r"\d", zeile):
                continue  # Adress-/Telefonzeilen sind keine Namen
            worte = [w.strip("-") for w in re.findall(r"[A-ZÄÖÜ][a-zäöüß\-]+", zeile)]
            worte = [w for w in worte if w.lower() not in _ETIKETTEN and len(w) >= 3]
            if len(worte) >= 2:
                name = " ".join(worte[:3])
                break
        eintraege.append({
            "name": name, "telefon": tel.group(0).strip() if tel else "",
            "email": m.group(0), "website": "", "ort": "",
            "plz": plz.group(0) if plz else "",
        })
    return eintraege


def naechste_seite(html: str, basis: str) -> str | None:
    """Generische Paginierung: rel=next, ?page=, /page/…"""
    m = re.search(r'<a[^>]+rel="next"[^>]+href="([^"]+)"', html, re.I) or \
        re.search(r'<link[^>]+rel="next"[^>]+href="([^"]+)"', html, re.I) or \
        re.search(r'<a[^>]+href="([^"]*[?&]page=\d+[^"]*)"[^>]*>(?:\s*(?:&raquo;|›|»|weiter|next|&gt;)\s*)</a>', html, re.I)
    if m:
        return urllib.parse.urljoin(basis, m.group(1).replace("&amp;", "&"))
    return None


def lese_quelle(key: str, limit: int, client: App, suchlauf_id: str,
                stufen: dict, verluste: dict, gesehen: set, paket: list) -> None:
    rezept = QUELLEN[key]
    quelle_waechter = drossel.Quelle(key)
    warteschlange = list(rezept["start_urls"])
    besucht: set[str] = set()
    zielgruppe = rezept["zielgruppe"]

    def sende_paket() -> None:
        if not paket:
            return
        antwort = client._req("POST", "/api/fabrik2/import-treffer",
                              {"suchlauf_id": suchlauf_id, "treffer": list(paket)})
        log(f"  Paket gemeldet: neu {antwort.get('neu', '?')}, dublette {antwort.get('dublette', '?')}")
        paket.clear()

    while warteschlange and len(besucht) < rezept["max_seiten"]:
        if limit and stufen["gemeldet"] >= limit:
            break
        url = warteschlange.pop(0)
        if url in besucht:
            continue
        besucht.add(url)
        status, roh = hole_roh(url)
        stufen["seiten_geladen"] += 1
        quelle_waechter.pruefe_antwort(status, "" if url.endswith(".pdf") else roh[:5000].decode("utf-8", "replace"))
        if status != 200 or not roh:
            log(f"  {url} → HTTP {status}, übersprungen")
            continue

        if url.lower().endswith(".pdf"):
            try:
                text = pdf_zu_text(roh)
            except Exception as ex:  # noqa: BLE001
                log(f"  PDF nicht lesbar ({ex}): {url}")
                continue
        else:
            html = roh.decode("utf-8", "replace")
            # Unterseiten/PDF-Links nach Rezept einreihen
            if rezept.get("unterseiten"):
                for lm in re.finditer(r'href="([^"]+)"', html):
                    link = urllib.parse.urljoin(url, lm.group(1))
                    if re.search(rezept["unterseiten"], link, re.I) and \
                       urllib.parse.urlsplit(link).netloc == urllib.parse.urlsplit(url).netloc and \
                       link not in besucht:
                        warteschlange.append(link)
            folge = naechste_seite(html, url)
            if folge and folge not in besucht:
                warteschlange.append(folge)
            if rezept["typ"] == "pdf":
                continue  # Startseite dient nur der PDF-Link-Suche
            text = html_zu_text(html)

        for e in ki_extraktion(text):
            if limit and stufen["gemeldet"] >= limit:
                break
            name = str(e.get("name") or "").strip()
            telefon = str(e.get("telefon") or "").strip()
            email = str(e.get("email") or "").strip()
            plz = str(e.get("plz") or "").strip()
            stufen["roh_extrahiert"] += 1
            if not name:
                verluste["ohne_name"] += 1
                continue
            if not telefon and not plz:
                verluste["ohne_schluessel"] += 1
                continue
            schluessel = normalisierung.telefon(telefon)["key"] or f"{name.lower()}|{plz}|{email.lower()}"
            if schluessel in gesehen:
                verluste["doppelt_im_lauf"] += 1
                continue
            gesehen.add(schluessel)
            ist_person = len(name.split()) >= 2 and not re.search(r"\d|gmbh|e\.\s?v\.", name, re.I)
            paket.append({
                "name": name,
                "telefon": telefon,
                "email": email,
                "website": str(e.get("website") or "").strip(),
                "ort": str(e.get("ort") or "").strip(),
                "plz": plz,
                "branche": zielgruppe,
                "quelle": key,
                "quell_link": url,
                # Ansprechperson (D-089): macht die 4 Parameter komplett
                **({"kontakt": {"name": name, "rolle": zielgruppe, "email": email, "telefon": telefon}}
                   if ist_person else {}),
            })
            stufen["gemeldet"] += 1
            if normalisierung.telefon(telefon)["art"] == "mobil":
                stufen["mit_handy"] += 1
            if len(paket) >= PAKET_GROESSE:
                sende_paket()
    sende_paket()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verbands-Konnektor (Fabrik 2, M5)")
    parser.add_argument("--branche", required=True)
    parser.add_argument("--quellen", default="")
    parser.add_argument("--suchlauf-id", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    client = App()
    if not client.basis or not client.token:
        log("FEHLER: APP_URL und WORKER_TOKEN müssen gesetzt sein.")
        return 1

    angefordert = {q.strip() for q in args.quellen.split(",") if q.strip()}
    passend = [k for k in BRANCHE_ZU_QUELLEN.get(args.branche, [])
               if k in angefordert or "verbaende" in angefordert]
    if not passend:
        log("Keine freigegebene Verbandsquelle angefordert — nichts zu tun.")
        return 0

    stufen = {"seiten_geladen": 0, "roh_extrahiert": 0, "gemeldet": 0, "mit_handy": 0}
    verluste = {"ohne_name": 0, "ohne_schluessel": 0, "doppelt_im_lauf": 0}
    gesehen: set = set()
    paket: list = []
    fehler = []
    for key in passend:
        log(f"Quelle {key} …")
        try:
            lese_quelle(key, args.limit, client, args.suchlauf_id, stufen, verluste, gesehen, paket)
        except drossel.QuelleGesperrt as ex:
            log(f"  GESPERRT: {ex} — Quelle wird nicht weiter abgerufen.")
            fehler.append({"quelle": key, "fehler": str(ex)})
        except Exception as ex:  # noqa: BLE001 — Ausfall einer Quelle stoppt den Lauf nicht
            log(f"  FEHLER bei {key}: {ex}")
            fehler.append({"quelle": key, "fehler": str(ex)[:300]})

    body = {"suchlauf_id": args.suchlauf_id,
            "foerderband": {"stufen_verbaende": stufen, "verluste_verbaende": verluste,
                            "ki_extraktion_calls": KI_CALLS["n"]}}
    if fehler:
        body["quellen_fehler"] = fehler
    client._req("POST", "/api/fabrik2/bericht", body)
    log(f"Verbände fertig: {json.dumps(stufen)} / Verluste {json.dumps(verluste)} / KI-Calls {KI_CALLS['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
