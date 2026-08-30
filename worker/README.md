Hier entstehen ab M2 die Quellen-Konnektoren (je ein Python-Modul):
osm_extract.py (Geofabrik-Extract lokal auswerten) → gelbe_seiten.py →
wlw.py → verbaende.py. Gemeinsame Bausteine: normalisierung, drosselung
(1 Anfrage/s), stopp-logik (Sperr-Signale), melden (Pakete à 100 an die App).
