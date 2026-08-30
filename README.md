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

M1: Skeleton (Workflow nimmt Inputs an, no-op). Der OSM-Extract-Konnektor
kommt mit **M2**.
