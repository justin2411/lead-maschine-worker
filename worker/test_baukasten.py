# -*- coding: utf-8 -*-
"""D-276/D-277: Anbieter-Impressum auf Berufs-Baukästen zählt nicht. Ohne Netz: python3 worker/test_baukasten.py"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baukasten import BERUFS_BAUKASTEN, anbieter_seite, berufs_baukasten, ohne_anbieter  # noqa: E402

RF = re.compile(r"\bgmbh\b|hrb\s?\d")

assert berufs_baukasten("https://anna-muster.hebamio.de/") == "hebamio.de"
assert berufs_baukasten("anna-muster.hebamio.de") == "hebamio.de"
for w in ("https://hebamio.de/", "https://www.hebamio.de/", "https://hebamme-muster.de/", "https://xhebamio.de/", ""):
    assert berufs_baukasten(w) is None, w

anbieter = " hebamio impressum somedio software gmbh musterstrasse 1 12345 musterstadt"
assert anbieter_seite(anbieter, "https://anna.hebamio.de/")
assert not anbieter_seite(anbieter, "https://hebamme-muster.de/")
eigen = "impressum anna muster, hebamme, musterweg 2 " + "x " * 200 + "erstellt mit hebamio (somedio software gmbh)"
assert not anbieter_seite(eigen, "https://anna.hebamio.de/")

def treffer(text, w):
    return [m.group(0) for m in ohne_anbieter(list(RF.finditer(text)), text, w)]

assert treffer(anbieter, "https://anna.hebamio.de/") == []
assert treffer(anbieter, "https://hebamme-muster.de/") == ["gmbh"]
assert treffer("startseite ... © 2026 hebamio gmbh", "https://anna.hebamio.de/") == []
assert treffer("hebammenpraxis muster gmbh, hrb 1234" + " " * 200 + "© hebamio gmbh",
               "https://anna.hebamio.de/") == ["gmbh", "hrb 1"]
print("ok")

# D-277: agtcm-therapeut.de (Heilpraktiker, eigenes Impressum je Praxis)
assert berufs_baukasten("https://praxis-muster.agtcm-therapeut.de/") == "agtcm-therapeut.de"
assert berufs_baukasten("https://www.agtcm-therapeut.de/") is None
assert BERUFS_BAUKASTEN["agtcm-therapeut.de"] == "Heilpraktiker"
assert anbieter_seite("impressum agtcm e.v. arbeitsgemeinschaft fuer klassische akupunktur und tcm",
                      "https://praxis.agtcm-therapeut.de/")
praxis = "impressum anna muster, heilpraktikerin, kontakt: anna@agtcm-therapeut.de " + "x " * 200
assert not anbieter_seite(praxis, "https://praxis.agtcm-therapeut.de/")
assert treffer("praxis muster" + " " * 200 + "webdesign triple-i gmbh", "https://praxis.agtcm-therapeut.de/") == []
print("ok agtcm")
