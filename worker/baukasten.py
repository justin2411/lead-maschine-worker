"""
Berufs-Baukästen (D-274 / D-276): Mini-Homepage-Anbieter eines Berufs, bei denen
jede Unterdomain die Seite einer Solo-Selbstständigen ist (zurzeit hebamio.de →
Hebamme, `name.hebamio.de`).

Gemeinsame Quelle für den Sammler (CRM-Repo, `server/commoncrawl/sammler.py`,
importiert über WORKER_DIR) und die Worker hier (Prüfung, Anreicherung). Neue
Einträge nur nach Testlauf 50 (D-274).

Auf diesen Hosts gehört das Impressum (und Fußzeilen wie „© hebamio GmbH“) dem
Software-Anbieter, nicht der Hebamme. Rechtsform, Handelsregister oder Team-
Hinweise daraus sagen nichts über den Betrieb selbst (D-276, Fund 20.10.2026:
146 Hebammen in der Rückhand mit „kein Solo-Betrieb (gmbh)“).
"""
from __future__ import annotations

import re
import urllib.parse

BERUFS_BAUKASTEN = {"hebamio.de": "Hebamme"}

# Erkennungszeichen des Anbieters (Text nach _norm: klein, Umlaute ausgeschrieben).
BAUKASTEN_ANBIETER = {
    "hebamio.de": re.compile(r"somedio|hebamio\s+(gmbh|impressum)|(©|\(c\)|copyright)\s*(\d{4}\s*)?hebamio", re.I),
}
# Ein Rechtsform-Treffer so nah an einem Anbieter-Zeichen gehört zum Anbieter.
ANBIETER_ABSTAND = 80
# Steht ein Anbieter-Zeichen so weit vorn, ist die ganze Seite das Anbieter-Impressum.
ANBIETER_KOPF = 300


def berufs_baukasten(website: str) -> str | None:
    """Basis-Domain, wenn die Website eine Unterdomain eines Berufs-Baukastens ist."""
    w = (website or "").strip()
    host = urllib.parse.urlsplit(w if "//" in w else f"https://{w}").hostname or ""
    host = host.lower().rstrip(".")
    for basis in BERUFS_BAUKASTEN:
        if host.endswith("." + basis) and host != "www." + basis:
            return basis
    return None


def anbieter_seite(text: str, website: str) -> bool:
    """Ist der (normierte) Seitentext das Impressum des Baukasten-Anbieters?"""
    basis = berufs_baukasten(website)
    return bool(basis) and BAUKASTEN_ANBIETER[basis].search(text[:ANBIETER_KOPF]) is not None


def ohne_anbieter(treffer: list[re.Match], text: str, website: str) -> list[re.Match]:
    """Treffer im (normierten) Text ohne die, die neben einem Anbieter-Zeichen stehen."""
    basis = berufs_baukasten(website)
    if not basis:
        return treffer
    zeichen = [(m.start(), m.end()) for m in BAUKASTEN_ANBIETER[basis].finditer(text)]
    return [t for t in treffer
            if not any(t.start() - ANBIETER_ABSTAND <= e and s <= t.end() + ANBIETER_ABSTAND for s, e in zeichen)]
