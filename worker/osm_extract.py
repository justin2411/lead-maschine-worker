#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OSM-Extract-Suchlauf (M2) — liest Betriebe einer Branche aus dem
Geofabrik-Deutschland-Extract und meldet sie an die Fabrik 2 im CRM.

Ablauf:
  1. germany-latest.osm.pbf von Geofabrik laden (ehrlicher User-Agent,
     ein einziger Download pro Lauf — KEINE Overpass-Massenabfragen)
  2. Vorfilter mit `osmium tags-filter` auf die POI-Familien
     (office/healthcare/shop/amenity/leisure/craft/social_facility)
     → kleine Datei, die Python dann schnell durchgehen kann
  3. pyosmium-Scan über die Vorauswahl mit den Branchen-Matchern
     aus branchen.py (Tag-Sätze ODER Namens-Muster, minus Sperr-Muster)
  4. Treffer in Paketen à 100 an POST $APP_URL/api/fabrik2/import-treffer
  5. Abschlussbericht (Förderband-Zähler + Status) an
     POST $APP_URL/api/fabrik2/bericht

Datenquelle: © OpenStreetMap contributors, Lizenz ODbL 1.0
(https://www.openstreetmap.org/copyright). Die Attribution wird im CRM
an der Trefferliste angezeigt.

Umgebungsvariablen: APP_URL (z. B. https://4570-98.vercel.app),
WORKER_TOKEN (Bearer für die beiden Fabrik-2-Endpunkte).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

from branchen import BRANCHEN

GEOFABRIK_URL = "https://download.geofabrik.de/europe/germany-latest.osm.pbf"
USER_AGENT = "LeadMaschine2-Suchlauf/1.0 (+https://github.com/justin2411/lead-maschine-worker)"
POI_FAMILIEN = ["office", "healthcare", "shop", "amenity", "leisure", "craft", "social_facility"]
PAKET_GROESSE = 100


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------- Download

def lade_extract(ziel: str) -> None:
    """Lädt den Geofabrik-Extract (~4 GB) mit ehrlichem User-Agent."""
    if os.path.exists(ziel) and os.path.getsize(ziel) > 1_000_000_000:
        log(f"Extract schon da ({os.path.getsize(ziel) / 1e9:.1f} GB) — Download übersprungen.")
        return
    log(f"Lade {GEOFABRIK_URL} …")
    req = urllib.request.Request(GEOFABRIK_URL, headers={"User-Agent": USER_AGENT})
    start = time.time()
    with urllib.request.urlopen(req, timeout=120) as antwort, open(ziel, "wb") as f:
        gesamt = 0
        while True:
            stueck = antwort.read(8 * 1024 * 1024)
            if not stueck:
                break
            f.write(stueck)
            gesamt += len(stueck)
            if gesamt % (512 * 1024 * 1024) < 8 * 1024 * 1024:
                log(f"  … {gesamt / 1e9:.1f} GB")
    log(f"Download fertig: {gesamt / 1e9:.2f} GB in {time.time() - start:.0f}s")


def vorfilter(quelle: str, ziel: str) -> None:
    """`osmium tags-filter` — C++-Vorfilter, macht aus 4 GB ein kleines POI-File."""
    ausdruecke = [f"nwr/{fam}" for fam in POI_FAMILIEN]
    log(f"Vorfilter: osmium tags-filter auf {', '.join(POI_FAMILIEN)} …")
    start = time.time()
    subprocess.run(
        ["osmium", "tags-filter", quelle, *ausdruecke, "-o", ziel, "--overwrite"],
        check=True,
    )
    log(f"Vorfilter fertig: {os.path.getsize(ziel) / 1e6:.0f} MB in {time.time() - start:.0f}s")


# ---------------------------------------------------------------- Matching

def passt_tags(tags: dict, saetze: list) -> bool:
    for satz in saetze:
        if all(tags.get(k) == v for k, v in satz.items()):
            return True
    return False


def extrahiere(tags: dict) -> dict:
    strasse = " ".join(x for x in [tags.get("addr:street"), tags.get("addr:housenumber")] if x)
    return {
        "name": (tags.get("name") or "").strip(),
        "strasse": strasse,
        "plz": (tags.get("addr:postcode") or "").strip(),
        "ort": (tags.get("addr:city") or "").strip(),
        "telefon": (tags.get("phone") or tags.get("contact:phone") or "").strip(),
        "website": (tags.get("website") or tags.get("contact:website") or "").strip(),
        "email": (tags.get("email") or tags.get("contact:email") or "").strip(),
    }


def telefon_grob(telefon: str) -> str:
    """Grober Dedupe-Schlüssel innerhalb des Laufs (die App normalisiert richtig)."""
    return re.sub(r"\D", "", telefon)


def ist_handy(telefon: str) -> bool:
    """Grobe Handy-Erkennung (015x/016x/017x) — der Handy-Fokus wird im
    Förderband mitgezählt; fein klassifiziert die App bzw. leadkern."""
    ziffern = telefon_grob(telefon)
    if ziffern.startswith("00"):
        ziffern = ziffern[2:]
    elif ziffern.startswith("0"):
        ziffern = "49" + ziffern[1:]
    if ziffern.startswith("490"):
        ziffern = "49" + ziffern[3:]
    return ziffern.startswith(("4915", "4916", "4917"))


# ---------------------------------------------------------------- Melden

class AppClient:
    def __init__(self, app_url: str, token: str, suchlauf_id: str):
        self.basis = app_url.rstrip("/")
        self.token = token
        self.suchlauf_id = suchlauf_id

    def _post(self, pfad: str, body: dict) -> dict:
        daten = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.basis}{pfad}",
            data=daten,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        letzte_ex = None
        for versuch in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as antwort:
                    return json.loads(antwort.read().decode("utf-8"))
            except Exception as ex:  # noqa: BLE001 — Netz-Fehler tolerieren, mit Backoff
                letzte_ex = ex
                wartezeit = 2 ** (versuch + 1)
                log(f"  POST {pfad} fehlgeschlagen ({ex}) — neuer Versuch in {wartezeit}s")
                time.sleep(wartezeit)
        raise RuntimeError(f"POST {pfad} endgültig fehlgeschlagen: {letzte_ex}")

    def melde_paket(self, paket: list) -> dict:
        return self._post("/api/fabrik2/import-treffer", {
            "suchlauf_id": self.suchlauf_id,
            "treffer": paket,
        })

    def melde_bericht(self, foerderband: dict, status: str, quellen_fehler=None) -> None:
        body = {"suchlauf_id": self.suchlauf_id, "foerderband": foerderband, "status": status}
        if quellen_fehler:
            body["quellen_fehler"] = quellen_fehler
        self._post("/api/fabrik2/bericht", body)


# ---------------------------------------------------------------- Hauptlauf

def scanne(poi_datei: str, branche: dict, limit: int, client: AppClient):
    """Geht die POI-Vorauswahl durch und meldet Treffer paketweise."""
    import osmium

    name_regex = re.compile(branche["name_regex"], re.IGNORECASE) if branche.get("name_regex") else None
    name_sperre = re.compile(branche["name_sperre"], re.IGNORECASE) if branche.get("name_sperre") else None
    tag_saetze = branche.get("tag_filter") or []
    beruf = branche["beruf"]

    stufen = {"poi_vorauswahl": 0, "branchen_treffer": 0, "gemeldet": 0, "mit_handy": 0}
    verluste = {"name_sperre": 0, "ohne_name": 0, "ohne_schluessel": 0, "doppelt_im_lauf": 0}
    gesehen = set()
    paket = []
    limit_erreicht = False

    def sende_paket():
        if not paket:
            return
        antwort = client.melde_paket(paket)
        log(f"  Paket gemeldet: neu {antwort.get('neu', '?')}, "
            f"dublette {antwort.get('dublette', '?')}, "
            f"blacklist {antwort.get('blacklist', '?')}")
        paket.clear()

    class Handler(osmium.SimpleHandler):
        def _pruefe(self, obj, osm_typ: str):
            nonlocal limit_erreicht
            if limit_erreicht:
                return
            tags = {t.k: t.v for t in obj.tags}
            if not tags:
                return
            stufen["poi_vorauswahl"] += 1
            name = (tags.get("name") or "").strip()

            treffer = passt_tags(tags, tag_saetze)
            if not treffer and name_regex is not None and name and name_regex.search(name):
                treffer = True
            if not treffer:
                return
            stufen["branchen_treffer"] += 1

            if not name:
                verluste["ohne_name"] += 1
                return
            if name_sperre is not None and name_sperre.search(name):
                verluste["name_sperre"] += 1
                return

            felder = extrahiere(tags)
            if not felder["telefon"] and not felder["plz"]:
                # Ohne Telefon und ohne PLZ hat die App keinen Dedupe-Schlüssel
                verluste["ohne_schluessel"] += 1
                return

            lauf_key = telefon_grob(felder["telefon"]) or f'{name.lower()}|{felder["plz"]}'
            if lauf_key in gesehen:
                verluste["doppelt_im_lauf"] += 1
                return
            gesehen.add(lauf_key)

            felder["branche"] = beruf
            felder["quelle"] = "osm"
            felder["quell_link"] = f"https://www.openstreetmap.org/{osm_typ}/{obj.id}"
            paket.append(felder)
            stufen["gemeldet"] += 1
            if ist_handy(felder["telefon"]):
                stufen["mit_handy"] += 1
            if len(paket) >= PAKET_GROESSE:
                sende_paket()
            if limit and stufen["gemeldet"] >= limit:
                limit_erreicht = True

        def node(self, n):
            self._pruefe(n, "node")

        def way(self, w):
            self._pruefe(w, "way")

        def relation(self, r):
            self._pruefe(r, "relation")

    log("Scanne POI-Vorauswahl …")
    start = time.time()
    Handler().apply_file(poi_datei)
    sende_paket()
    log(f"Scan fertig in {time.time() - start:.0f}s: {json.dumps(stufen)} / Verluste {json.dumps(verluste)}")
    return stufen, verluste


def main() -> int:
    parser = argparse.ArgumentParser(description="OSM-Extract-Suchlauf (Fabrik 2, M2)")
    # Mehrere Branchen je Lauf (12.09.2026): der 4-GB-Download und der
    # osmium-Vorfilter kosten ~15 Minuten, der Scan je Branche nur ~1. Ein
    # Lauf pro Branche hat am 06.09. das Actions-Monatskontingent an einem
    # Tag aufgebraucht. Komma-Liste spart den Faktor 10.
    parser.add_argument("--branche", required=True,
                        help=f"eine oder mehrere (Komma) von: {', '.join(BRANCHEN)}")
    parser.add_argument("--quellen", default="osm", help="Komma-Liste; hier zählt nur 'osm'")
    parser.add_argument("--suchlauf-id", required=True,
                        help="eine ID je Branche, gleiche Reihenfolge (Komma)")
    parser.add_argument("--limit", type=int, default=0, help="max. gemeldete Treffer (0 = alle)")
    parser.add_argument("--arbeitsordner", default=os.environ.get("RUNNER_TEMP", "/tmp"))
    args = parser.parse_args()

    app_url = os.environ.get("APP_URL", "")
    token = os.environ.get("WORKER_TOKEN", "")
    if not app_url or not token:
        log("FEHLER: APP_URL und WORKER_TOKEN müssen gesetzt sein (Repo-Secrets).")
        return 1

    branchen = [b.strip() for b in args.branche.split(",") if b.strip()]
    ids = [i.strip() for i in args.suchlauf_id.split(",") if i.strip()]
    unbekannt = [b for b in branchen if b not in BRANCHEN]
    if unbekannt:
        log(f"FEHLER: unbekannte Branche(n) {', '.join(unbekannt)}. Bekannt: {', '.join(BRANCHEN)}")
        return 1
    if len(ids) != len(branchen):
        log(f"FEHLER: {len(branchen)} Branchen, aber {len(ids)} Suchlauf-IDs — muss gleich sein.")
        return 1
    if "osm" not in [q.strip() for q in args.quellen.split(",") if q.strip()]:
        log("Quelle 'osm' nicht angefordert — nichts zu tun.")
        return 0

    extract = os.path.join(args.arbeitsordner, "germany-latest.osm.pbf")
    poi_datei = os.path.join(args.arbeitsordner, "poi-vorauswahl.osm.pbf")
    clients = [AppClient(app_url, token, i) for i in ids]

    try:
        for c in clients:
            c.melde_bericht({"stufen": {}}, "laeuft")
        # Einmal laden und vorfiltern — danach jede Branche über dieselbe
        # POI-Vorauswahl scannen.
        lade_extract(extract)
        vorfilter(extract, poi_datei)
        os.remove(extract)  # 4 GB sofort freigeben, die Vorauswahl reicht
        for name, client in zip(branchen, clients):
            log(f"── Branche {name} ({branchen.index(name)+1}/{len(branchen)})")
            stufen, verluste = scanne(poi_datei, BRANCHEN[name], args.limit, client)
            client.melde_bericht(
                {"stufen": stufen, "verluste_worker": verluste, "name_quelle": {"osm": stufen["gemeldet"]}},
                "fertig",
            )
        log(f"Suchlauf fertig gemeldet ({len(branchen)} Branchen in einem Lauf).")
        return 0
    except Exception as ex:  # noqa: BLE001 — Fehler ehrlich an die App melden
        log(f"FEHLER im Suchlauf: {ex}")
        # Jede Branche des Laufs bekommt ihren eigenen Fehlerbericht, sonst
        # bleiben die anderen Suchlauf-Zeilen ewig auf "laeuft" stehen.
        for c in clients:
            try:
                c.melde_bericht({}, "fehlgeschlagen", quellen_fehler=[{"quelle": "osm", "fehler": str(ex)[:500]}])
            except Exception as melde_ex:  # noqa: BLE001
                log(f"Fehlerbericht selbst fehlgeschlagen: {melde_ex}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
