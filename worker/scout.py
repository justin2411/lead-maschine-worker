#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quellen-Scout für Hebammen-Listen (D-138, Justin 13.09.2026: „Hebammen-Listen
und Verbände ja starten — aber in der Rückhand halten").

SUCHT nur, zapft nichts an: DuckDuckGo-HTML-Suche (1 Anfrage/Sekunde, ehrlicher
User-Agent) nach öffentlichen Hebammenlisten (Landkreise, Gesundheitsämter,
Hebammenzentralen, Netzwerke, Landesverbände), prüft je Kandidat robots.txt,
lädt EINE Seite/PDF, zählt Telefonnummern/E-Mails und sucht nach Nutzungs-
verboten. Ergebnis: Rangliste im Job-Log + scout-ergebnis.json (Artefakt).
Gesperrte Plattformen (AGB/robots, siehe QUELLEN-KATALOG) werden gar nicht
erst angefasst. Das Anzapfen läuft später über worker/quellen.py (Rezept je
Quelle, Testlauf 50) — nie aus diesem Skript.
"""
import io, json, re, sys, time, urllib.parse, urllib.request, urllib.robotparser

UA = "LeadMaschine2-Scout/1.0 (+https://github.com/justin2411/lead-maschine-worker)"
GESPERRT = ("ammely", "hebammensuche", "gkv-spitzenverband", "berliner-hebammenvermittlung",
            "meine-tagesmutter", "facebook", "instagram", "gelbeseiten", "11880", "dasoertliche",
            "jameda", "doctolib", "kununu", "wikipedia", "youtube", "amazon", "ebay", "kleinanzeigen",
            "yelp", "golocal", "duckduckgo", "google", "bing", "linkedin", "xing", "pinterest",
            "tiktok", "aok", "tk.de", "barmer", "dak.de", "ikk", "bkk", "knappschaft", "hebammenverband.de")
BUNDESLAENDER = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen",
                 "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz",
                 "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]
FRAGEN_JE_LAND = ["Hebammenliste {bl} pdf", "Hebammen Liste Landkreis {bl} Gesundheitsamt",
                  "Hebammenzentrale {bl} Hebammen Kontakt Telefon", "Hebammennetzwerk {bl} Hebammen Übersicht"]
FRAGEN_ALLGEMEIN = ["Hebammenliste Landkreis pdf", "Liste freiberuflicher Hebammen pdf Telefon",
                    "Hebammen im Landkreis Übersicht pdf", "Hebammenverzeichnis Stadt pdf",
                    "Hebammenliste Gesundheitsamt", "Hebammen Kreis Liste Wochenbettbetreuung Telefon",
                    "Hebammenzentrale Liste Hebammen", "Hebammen Landesverband Hebammensuche Liste"]
TEL = re.compile(r"(?:\+49|0)[\s\-/().]*\d(?:[\s\-/().]*\d){7,13}")
MAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
VERBOT = re.compile(r"(gewerblich\w* nutzung|auslesen|automatisiert\w* abruf|datenbank\w*recht|"
                    r"nutzung der daten .{0,40}untersagt|werbliche nutzung|keine weitergabe)", re.I)
letzte: dict[str, float] = {}


def drossle(url: str) -> None:
    host = urllib.parse.urlsplit(url).netloc
    frei = letzte.get(host, 0) + 1.0
    if time.monotonic() < frei:
        time.sleep(frei - time.monotonic())
    letzte[host] = time.monotonic()


def hole(url: str, timeout: int = 20) -> tuple[int, bytes]:
    drossle(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as a:
            return a.status, a.read(6_000_000)
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, b""
    except Exception:
        return 0, b""


def ddg(frage: str) -> list[dict]:
    status, roh = hole("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(frage))
    if status != 200 or not roh:
        print(f"  DDG {status} für {frage!r}")
        if status in (403, 429):
            raise RuntimeError("DuckDuckGo sperrt — Scout stoppt (keine Umgehung)")
        return []
    html = roh.decode("utf-8", "replace")
    if re.search(r"captcha|anomaly", html, re.I):
        raise RuntimeError("DuckDuckGo Captcha — Scout stoppt (keine Umgehung)")
    treffer = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>(?:.*?class="result__snippet"[^>]*>(.*?)</a>)?', html, re.S):
        url = m.group(1)
        if "uddg=" in url:
            url = (urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("uddg") or [""])[0]
        titel = re.sub(r"<[^>]+>", "", m.group(2) or "")
        snippet = re.sub(r"<[^>]+>", "", m.group(3) or "")
        if url.startswith("http"):
            treffer.append({"url": url, "titel": titel.strip(), "snippet": snippet.strip()})
    return treffer


def kandidat(t: dict) -> bool:
    u = t["url"].lower(); host = urllib.parse.urlsplit(u).netloc
    if any(g in host for g in GESPERRT):
        return False
    text = (t["titel"] + " " + t["snippet"]).lower()
    if "hebamm" not in text and "hebamm" not in u:
        return False
    return u.endswith(".pdf") or any(w in text or w in u for w in
                                     ("liste", "verzeichnis", "übersicht", "uebersicht", "zentrale", "netzwerk", "suche"))


def robots_ok(url: str) -> bool:
    teile = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    try:
        status, roh = hole(f"{teile.scheme}://{teile.netloc}/robots.txt", timeout=10)
        if status != 200:
            return True
        rp.parse(roh.decode("utf-8", "replace").splitlines())
        return rp.can_fetch("*", url) and rp.can_fetch(UA, url)
    except Exception:
        return True


def bewerte(t: dict) -> dict:
    url = t["url"]
    erg = {**t, "robots_ok": robots_ok(url), "http": 0, "typ": "pdf" if url.lower().endswith(".pdf") else "html",
           "telefone": 0, "emails": 0, "verbot": "", "zeichen": 0}
    if not erg["robots_ok"]:
        return erg
    status, roh = hole(url)
    erg["http"] = status
    if status != 200 or not roh:
        return erg
    if erg["typ"] == "pdf" or roh[:5] == b"%PDF-":
        erg["typ"] = "pdf"
        try:
            from pypdf import PdfReader
            text = "\n".join((s.extract_text() or "") for s in PdfReader(io.BytesIO(roh)).pages[:60])
        except Exception as ex:  # noqa: BLE001
            erg["verbot"] = f"PDF nicht lesbar: {ex}"[:80]
            return erg
    else:
        html = roh.decode("utf-8", "replace")
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
    erg["zeichen"] = len(text)
    erg["telefone"] = len(set(re.sub(r"\D", "", m.group(0)) for m in TEL.finditer(text)))
    erg["emails"] = len(set(m.group(0).lower() for m in MAIL.finditer(text)))
    v = VERBOT.search(text)
    erg["verbot"] = text[max(0, v.start() - 60):v.end() + 60].replace("\n", " ") if v else ""
    return erg


def main() -> int:
    max_kand = int((sys.argv[1] if len(sys.argv) > 1 else "150") or 150)
    fragen = list(FRAGEN_ALLGEMEIN) + [f.format(bl=bl) for bl in BUNDESLAENDER for f in FRAGEN_JE_LAND]
    gesehen: dict[str, dict] = {}
    try:
        for i, frage in enumerate(fragen, 1):
            for t in ddg(frage):
                if kandidat(t) and t["url"] not in gesehen:
                    t["frage"] = frage
                    gesehen[t["url"]] = t
            print(f"[{i}/{len(fragen)}] {frage!r} → bisher {len(gesehen)} Kandidaten", flush=True)
    except RuntimeError as ex:
        print(f"ABBRUCH Suche: {ex}")
    kand = list(gesehen.values())
    # PDFs und Behörden-/Verbands-Domains zuerst, höchstens max_kand prüfen
    def prio(t):
        u = t["url"].lower()
        return (0 if u.endswith(".pdf") else 1, 0 if re.search(r"kreis|landkreis|stadt|gesundheitsamt|hebammen", u) else 1)
    kand.sort(key=prio)
    kand = kand[:max_kand]
    print(f"\n{len(kand)} Kandidaten werden geprüft (robots.txt + 1 Abruf je Kandidat) …", flush=True)
    ergebnisse = []
    for i, t in enumerate(kand, 1):
        e = bewerte(t)
        ergebnisse.append(e)
        print(f"  [{i}/{len(kand)}] tel={e['telefone']:>3} mail={e['emails']:>3} http={e['http']} robots={'ok' if e['robots_ok'] else 'NEIN'} {e['typ']} {e['url'][:110]}", flush=True)
    ergebnisse.sort(key=lambda e: (-(e["telefone"] + e["emails"]), e["url"]))
    with open("scout-ergebnis.json", "w", encoding="utf-8") as f:
        json.dump(ergebnisse, f, ensure_ascii=False, indent=1)
    print("\n## Rangliste (Kontakte je Seite, nur robots-frei, HTTP 200)")
    print("| Kontakte | Tel | Mail | Typ | Verbot? | URL |")
    print("|---|---|---|---|---|---|")
    for e in ergebnisse:
        if e["robots_ok"] and e["http"] == 200 and (e["telefone"] + e["emails"]) >= 5:
            print(f"| {e['telefone'] + e['emails']} | {e['telefone']} | {e['emails']} | {e['typ']} | {('JA: ' + e['verbot'][:60]) if e['verbot'] else '-'} | {e['url']} |")
    gesperrt = [e for e in ergebnisse if not e["robots_ok"]]
    print(f"\nrobots-gesperrt (nicht angefasst): {len(gesperrt)}")
    for e in gesperrt:
        print("  ", e["url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
