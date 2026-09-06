#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Karten-Lauf über gosom/google-maps-scraper (D-092).

⚠️ BEWUSSTE AUSNAHME zur Fabrik-Regel „kein Umgehen": Google Maps
untersagt automatisiertes Auslesen in den Nutzungsbedingungen und blockt
es aktiv. Auf Justins ausdrückliche Einzel-Ansage (30.08.2026) trotzdem
als Quelle gebaut — so konservativ wie möglich: geringe Parallelität,
harter Anfragen-/Städte-Deckel, KEINE Proxy-Rotation, KEIN Captcha-Löser,
Stopp bei leeren/blockierten Ergebnissen. Standardmäßig abgewählt.

Ablauf: je Branche „Begriff + Stadt" als gosom-Queries (Deckel
FABRIK2_MAPS_MAX_STAEDTE), gosom schreibt CSV, wir lesen sie, filtern
Portale/Ketten (leadkern), melden Treffer paketweise. Telefon aus Maps
ist oft Festnetz → M3-Impressum-Nachschlag zieht danach Handy/Namen nach.

Voraussetzung im Workflow: das gosom-Binary liegt unter $GOSOM_BIN
(Default './google-maps-scraper'). Env: APP_URL, WORKER_TOKEN.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time

from leadkern import normalisierung, vorfilter

from anreicherung import App
from brave_suche import BEGRIFFE, STAEDTE, PORTAL_DOMAINS

PAKET_GROESSE = 100


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Karten-Lauf (Fabrik 2, D-092)")
    parser.add_argument("--branche", required=True)
    parser.add_argument("--quellen", default="")
    parser.add_argument("--suchlauf-id", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if "maps" not in {q.strip() for q in args.quellen.split(",") if q.strip()}:
        log("Quelle 'maps' nicht angefordert — nichts zu tun.")
        return 0
    client = App()
    if not client.basis or not client.token:
        log("FEHLER: APP_URL und WORKER_TOKEN müssen gesetzt sein.")
        return 1
    binary = os.environ.get("GOSOM_BIN", "./google-maps-scraper")
    if not os.path.exists(binary):
        log(f"FEHLER: gosom-Binary nicht gefunden ({binary}) — Karten-Lauf übersprungen.")
        client._req("POST", "/api/fabrik2/bericht", {
            "suchlauf_id": args.suchlauf_id,
            "quellen_fehler": [{"quelle": "maps", "fehler": "gosom-Binary fehlt"}]})
        return 0

    begriff = BEGRIFFE.get(args.branche, args.branche)
    try:
        from branchen import BRANCHEN
        zielgruppe = BRANCHEN.get(args.branche, {}).get("beruf", args.branche)
    except Exception:  # noqa: BLE001
        zielgruppe = args.branche

    max_staedte = int(os.environ.get("FABRIK2_MAPS_MAX_STAEDTE", "20") or 20)
    tiefe = int(os.environ.get("FABRIK2_MAPS_TIEFE", "1") or 1)  # gosom -depth, klein halten
    ab = int(os.environ.get("FABRIK2_MAPS_STAEDTE_AB", "0") or 0)  # Versatz für Folgeläufe
    staedte = STAEDTE[ab:ab + max_staedte]

    stufen = {"queries": len(staedte), "roh": 0, "gemeldet": 0, "mit_handy": 0}
    verluste = {"portal": 0, "ohne_name": 0, "ohne_schluessel": 0, "doppelt_im_lauf": 0}
    gesehen: set[str] = set()
    paket: list[dict] = []

    def sende_paket() -> None:
        if not paket:
            return
        antwort = client._req("POST", "/api/fabrik2/import-treffer",
                              {"suchlauf_id": args.suchlauf_id, "treffer": list(paket)})
        log(f"  Paket gemeldet: neu {antwort.get('neu', '?')}, dublette {antwort.get('dublette', '?')}")
        paket.clear()

    with tempfile.TemporaryDirectory() as tmp:
        query_datei = os.path.join(tmp, "queries.txt")
        with open(query_datei, "w", encoding="utf-8") as f:
            for stadt in staedte:
                f.write(f"{begriff} {stadt}\n")
        csv_datei = os.path.join(tmp, "ergebnisse.csv")

        log(f"Karten-Lauf: {len(staedte)} Städte, gosom -depth {tiefe} -c 1 (gedrosselt, kein Proxy)")
        try:
            # -c 1: minimale Parallelität; -depth klein; kein Proxy, kein Captcha-Solver
            proc = subprocess.run(
                [binary, "-input", query_datei, "-results", csv_datei,
                 "-c", "1", "-depth", str(tiefe), "-lang", "de", "-exit-on-inactivity", "3m"],
                capture_output=True, text=True, timeout=90 * 60)
            if proc.returncode != 0:
                log(f"  gosom Rückgabe {proc.returncode}: {proc.stderr[-500:]}")
        except subprocess.TimeoutExpired:
            log("  gosom Zeitlimit erreicht — verwerte, was da ist.")
        except Exception as ex:  # noqa: BLE001
            log(f"  gosom-Fehler: {ex}")
            client._req("POST", "/api/fabrik2/bericht", {
                "suchlauf_id": args.suchlauf_id,
                "quellen_fehler": [{"quelle": "maps", "fehler": str(ex)[:300]}]})
            return 0

        if not os.path.exists(csv_datei):
            log("  Keine CSV erzeugt (evtl. blockiert) — Stopp, kein Umgehen.")
            client._req("POST", "/api/fabrik2/bericht", {
                "suchlauf_id": args.suchlauf_id,
                "foerderband": {"stufen_maps": stufen, "verluste_maps": verluste},
                "quellen_fehler": [{"quelle": "maps", "fehler": "keine Ergebnisse (evtl. Block)"}]})
            return 0

        with open(csv_datei, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if args.limit and stufen["gemeldet"] >= args.limit:
                    break
                stufen["roh"] += 1
                name = (row.get("title") or row.get("name") or "").strip()
                telefon = (row.get("phone") or "").strip()
                website = (row.get("website") or "").strip()
                # gosom-Adressfelder variieren je Version
                adr_roh = (row.get("address") or row.get("complete_address") or "").strip()
                adr = normalisierung.adresse(adr_roh)
                plz, ort = adr["plz"], adr["ort"] or (row.get("city") or "").strip()
                if not name:
                    verluste["ohne_name"] += 1
                    continue
                if not telefon and not plz:
                    verluste["ohne_schluessel"] += 1
                    continue
                if PORTAL_DOMAINS.search(website) or vorfilter.ist_institution({"name": name, "website": website}):
                    verluste["portal"] += 1
                    continue
                schluessel = normalisierung.telefon(telefon)["key"] or f"{name.lower()}|{plz}"
                if schluessel in gesehen:
                    verluste["doppelt_im_lauf"] += 1
                    continue
                gesehen.add(schluessel)
                paket.append({
                    "name": name, "telefon": telefon, "website": website,
                    "plz": plz, "ort": ort, "branche": zielgruppe,
                    "quelle": "maps", "quell_link": (row.get("link") or row.get("google_maps_url") or ""),
                })
                stufen["gemeldet"] += 1
                if normalisierung.telefon(telefon)["art"] == "mobil":
                    stufen["mit_handy"] += 1
                if len(paket) >= PAKET_GROESSE:
                    sende_paket()
        sende_paket()

    client._req("POST", "/api/fabrik2/bericht", {
        "suchlauf_id": args.suchlauf_id,
        "foerderband": {"stufen_maps": stufen, "verluste_maps": verluste}})
    log(f"Karten-Lauf fertig: {json.dumps(stufen)} / Verluste {json.dumps(verluste)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
