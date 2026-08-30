# Lead-Maschine 2.0 — Suchlauf-Worker

Python-Worker (GitHub Actions, `workflow_dispatch`) für die bundesweiten
Suchläufe der Lead-Maschine 2.0. Liest die aktivierten Quellen, normalisiert
Treffer und meldet sie paketweise an `POST /api/import-treffer` der App
(Bearer `WORKER_TOKEN`).

## Feste Regeln (verbindlich, siehe App-Repo docs/)

- **Kein Umgehen:** keine Proxies, keine Captcha-Löser, keine Verschleierung.
  Ehrlicher User-Agent mit Kontaktangabe, Drosselung 1 Anfrage/Sekunde je
  Quelle, automatischer Stopp bei Sperr-Signalen (Captcha / 429-/403-Serie) —
  Sperren werden protokolliert, nie überwunden.
- **OSM als lokaler Extract:** Deutschland-Extract (Geofabrik, `.osm.pbf`)
  im Lauf herunterladen und lokal nach Branchen-Tags auswerten — keine
  Overpass-Massenabfragen. Attribution „© OpenStreetMap contributors".
- **Fehlertoleranz:** Ausfall einer Quelle bricht den Lauf nicht ab.
- Wortwahl: „Suchlauf/Suche/Auslesen/Ernte".

## Secrets

`WORKER_TOKEN` (gleicher Wert wie in der App) · `APP_URL` (z. B. die
Vercel-Production-URL).

## Stand

**M2: OSM-Extract-Quelle ist gebaut.** Ablauf pro Lauf
(`.github/workflows/suchlauf.yml` → `worker/osm_extract.py`):

1. `germany-latest.osm.pbf` (~4 GB) von Geofabrik laden — ein Download
   pro Lauf, ehrlicher User-Agent, keine Overpass-Massenabfragen.
2. Vorfilter mit `osmium tags-filter` auf die POI-Familien
   `office/healthcare/shop/amenity/leisure/craft/social_facility`.
3. pyosmium-Scan mit den Branchen-Matchern aus `worker/branchen.py`
   (Tag-Sätze ODER Namens-Muster, minus Sperr-Muster; 10 Start-Branchen
   aus E-2). Die Matcher sind ein Kalibrier-Start — nach dem ersten
   Testlauf nachziehen.
4. Treffer in Paketen à 100 an `POST $APP_URL/api/fabrik2/import-treffer`
   (Dedupe + Blacklist macht die App).
5. Förderband-Zähler + Status an `POST $APP_URL/api/fabrik2/bericht`.

Datenquelle: **© OpenStreetMap contributors, ODbL 1.0**
(https://www.openstreetmap.org/copyright).

Als Nächstes: M3 (Anreicherungs-Kette: Website/Impressum-Nachschlag).
