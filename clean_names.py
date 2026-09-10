#!/usr/bin/env python3
"""
Aufgabe 1 - OCR-Namen bereinigen.

Korrigiert systematisch OCR-Fehler in den Produktnamen von
atrelle_products.json und schreibt die Datei zurueck. Am Ende wird eine
Liste aller Aenderungen ausgegeben (id | alt -> neu).

Marken-/Stil-Kuerzel (GG, LV, RL, CB, CC, CRTZ, ...) sind Absicht und
werden NICHT angetastet. Geaendert werden nur:
  - verlorene Umlaute / ss->weif-Bruch (gruen->gruen, turkis->tuerkis, ...)
  - Muell-Praefixe (Vig:, SDYEDE, RH ads DRO, BE, Re:)
  - abgeschnittene Woerter / kaputte Klammern
  - Zeichenmuell am Ende
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "atrelle_products.json"

# 1) Systematische Umlaut-/ss-Restaurierung (Reihenfolge beachten).
#    Werden als Teilstring-Ersetzung auf den Namen angewandt.
SUBSTR_FIXES = [
    ("gruen", "grün"),        # gruen -> gruen
    ("militar", "militär"),   # militargrun -> militaer... (vor grun)
    ("grun", "grün"),         # mintgrun, grun-braun, militaergrun
    ("turkis", "türkis"),     # turkis, dunkelturkis
    ("Griin", "Grün"),        # CP Zipper (Griin)
    ("dunkelbiau", "dunkelblau"),  # OCR i->l
    ("babybiau", "babyblau"),      # OCR i->l
    ("Guertel", "Gürtel"),    # ue-Transliteration von Guertel
    ("weif", "weiß"),         # DRK-AF1 Sneaker (weif)
]

# 2) Gezielte Fixes pro exaktem Namen (Praefix-Muell, Trunkierung, Klammern).
#    Angewandt NACH den Substring-Fixes, daher stehen hier bereits
#    korrigierte Umlaute (z.B. "Gürtel").
EXACT_FIXES = {
    # Muell-Praefixe
    "Vig: Alcatraz Shorts Babyblue": "Alcatraz Shorts Babyblue",
    "SDYEDE Chrome Longsleeve (blau)": "Chrome Longsleeve (blau)",
    "RH ads DRO GG Gürtel und Portmonee (gold-silber)": "GG Gürtel und Portmonee (gold-silber)",
    "BE GG Gürtel und Portmonee (schwarz-silber)": "GG Gürtel und Portmonee (schwarz-silber)",
    "Re: Vanguard Sonnenbrille (weiss)": "Vanguard Sonnenbrille (weiss)",
    # Zeichenmuell am Ende
    "Chrome Tee “": "Chrome Tee",
    "Cups Sneaker (rot-)": "Cups Sneaker (rot)",
    "C-ier Sonnenbrille (lila-)": "C-ier Sonnenbrille (lila)",
    # Kaputte / stray Klammern bei N-Miler & UA Short Sets
    "N-Miler Short Set (many different colors) (Pink and Mint Green(shorts)":
        "N-Miler Short Set (many different colors) (Pink and Mint Green(shorts))",
    "N-Miler Short Set (many different colors) (Mint Green and Pink(shorts)":
        "N-Miler Short Set (many different colors) (Mint Green and Pink(shorts))",
    "N-Miler Short Set (many different ) colors) (Mint Green and Black(shorts))":
        "N-Miler Short Set (many different colors) (Mint Green and Black(shorts))",
    "N-Miler Short Set (many different ) colors) (Black and Pink(shorts))":
        "N-Miler Short Set (many different colors) (Black and Pink(shorts))",
    "UA Short Set (White and Black(shorts": "UA Short Set (White and Black(shorts))",
    "UA Short Set (White and Blue(shorts": "UA Short Set (White and Blue(shorts))",
    # Abgeschnittene Woerter / fehlende Klammer
    "Gel Runner Sneaker (schwarz-silber": "Gel Runner Sneaker (schwarz-silber)",
    "Nano Speedy Handtasche (himmelbla": "Nano Speedy Handtasche (himmelblau)",
    "CC Timeless Tasche (Schwarz-Silber": "CC Timeless Tasche (Schwarz-Silber)",
    "CC Small Size Bag (Grau (Wildleder)": "CC Small Size Bag (Grau (Wildleder))",
    "Vespera Sonnenbrille (schwarz-gold": "Vespera Sonnenbrille (schwarz-gold)",
    "Vespera Sonnenbrille (weiss-schwar:": "Vespera Sonnenbrille (weiss-schwarz)",
}


def clean(name: str) -> str:
    out = name
    for a, b in SUBSTR_FIXES:
        out = out.replace(a, b)
    if out in EXACT_FIXES:
        out = EXACT_FIXES[out]
    # generische Aufraeumung: doppelte Leerzeichen
    while "  " in out:
        out = out.replace("  ", " ")
    return out.strip()


def main():
    items = json.loads(DB.read_text(encoding="utf-8"))
    changes = []
    for p in items:
        old = p["name"]
        new = clean(old)
        if new != old:
            changes.append((p["id"], old, new))
            p["name"] = new
        # Kategorie "Guertel" mitziehen (gleiche OCR-Klasse)
        if p.get("category") == "Guertel":
            p["category"] = "Gürtel"

    DB.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{len(changes)} Namen geaendert:\n")
    for cid, old, new in changes:
        print(f"  {cid} | {old!r} -> {new!r}")


if __name__ == "__main__":
    main()
