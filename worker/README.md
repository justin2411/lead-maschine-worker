Quellen-Konnektoren (je ein Python-Modul), Reihenfolge nach
Arbeitsauftrag v2: osm_extract.py (M2, fertig — Geofabrik-Extract lokal
auswerten) → verbaende.py (M5, wertvollste Quelle: Inhaber-Namen) →
gelbe_seiten.py (M5, fragilste Quelle, strenge Stopp-Logik). KEIN WLW.
Gemeinsame Bausteine kommen ab M3 aus dem Paket `leadkern`
(normalisierung, drosselung 1 Anfrage/s, Stopp bei Sperr-Signalen);
gemeldet wird in Paketen à 100 an die App.
