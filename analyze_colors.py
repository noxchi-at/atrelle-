#!/usr/bin/env python3
"""
Aufgabe 4 - Dominante Produktfarben per Bildanalyse.

Fuer jedes Produkt-PNG:
  1. reinweissen Hintergrund maskieren (Produkte sind Cutouts auf 255/255/255)
  2. dominante Farben per k-means (numpy) bestimmen, nach Clustergroesse sortiert
  3. jede Farbe auf das deutsche Farb-Vokabular mappen (schwarz, weiss, blau, ...)

Ergebnis wird als `dominant_colors` (Liste aus {hex, rgb, name, weight})
in atrelle_products.json gespeichert.

Nutzung:
    python analyze_colors.py            # nur Produkte ohne Analyse
    python analyze_colors.py --force    # alle neu analysieren
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).parent
DB = BASE / "atrelle_products.json"

# Referenzfarben -> deutsches Vokabular (RGB-Anker)
PALETTE = {
    "schwarz": (20, 20, 20),
    "anthrazit": (55, 58, 62),
    "dunkelgrau": (90, 90, 92),
    "grau": (140, 140, 142),
    "hellgrau": (200, 200, 202),
    "weiss": (245, 245, 245),
    "creme": (240, 233, 214),
    "beige": (214, 197, 162),
    "sand": (200, 178, 140),
    "braun": (110, 74, 44),
    "khaki": (120, 110, 70),
    "gold": (198, 160, 60),
    "silber": (192, 196, 200),
    "rot": (190, 40, 40),
    "rosa": (230, 150, 180),
    "orange": (225, 130, 45),
    "gelb": (225, 205, 60),
    "gruen": (60, 140, 70),
    "mint": (150, 210, 180),
    "tuerkis": (50, 170, 170),
    "blau": (45, 85, 180),
    "hellblau": (120, 170, 225),
    "babyblau": (170, 205, 235),
    "dunkelblau": (25, 40, 95),
    "marineblau": (30, 45, 80),
    "lila": (130, 80, 170),
}
PAL_NAMES = list(PALETTE)
PAL_RGB = np.array([PALETTE[n] for n in PAL_NAMES], dtype=float)


def nearest_name(rgb):
    d = np.sqrt(((PAL_RGB - np.array(rgb, dtype=float)) ** 2).sum(axis=1))
    return PAL_NAMES[int(d.argmin())]


def foreground_pixels(img):
    """Gibt die Vordergrund-Pixel (Nx3) zurueck; reinweisser Hintergrund raus."""
    arr = np.asarray(img.convert("RGB"), dtype=np.uint8).reshape(-1, 3)
    mn = arr.min(axis=1)
    mx = arr.max(axis=1)
    is_bg = (mn > 244) & ((mx - mn) < 12)          # nahezu reinweiss + entsaettigt
    fg = arr[~is_bg]
    if fg.shape[0] < arr.shape[0] * 0.02:          # fast alles weiss -> weisses Produkt
        soft = (mn > 250) & ((mx - mn) < 6)
        fg = arr[~soft]
    if fg.shape[0] == 0:
        fg = arr
    return fg.astype(float)


def kmeans(px, k=4, iters=12, seed=0):
    rng = np.random.default_rng(seed)
    if px.shape[0] > 4000:
        px = px[rng.choice(px.shape[0], 4000, replace=False)]
    k = min(k, px.shape[0])
    centers = px[rng.choice(px.shape[0], k, replace=False)].copy()
    labels = np.zeros(px.shape[0], dtype=int)
    for _ in range(iters):
        d = ((px[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = d.argmin(axis=1)
        for j in range(k):
            m = labels == j
            if m.any():
                centers[j] = px[m].mean(axis=0)
    counts = np.bincount(labels, minlength=k)
    return centers, counts


def dominant_colors(img, top=3):
    px = foreground_pixels(img)
    centers, counts = kmeans(px)
    order = counts.argsort()[::-1]
    total = counts.sum() or 1
    out = []
    for j in order:
        if counts[j] == 0:
            continue
        rgb = [int(round(v)) for v in centers[j]]
        out.append({
            "hex": "#%02x%02x%02x" % tuple(rgb),
            "rgb": rgb,
            "name": nearest_name(rgb),
            "weight": round(float(counts[j] / total), 3),
        })
        if len(out) >= top:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    items = json.loads(DB.read_text(encoding="utf-8"))
    done = 0
    for p in items:
        if p.get("dominant_colors") and not args.force:
            continue
        img_path = BASE / p["image"]
        if not img_path.exists():
            print(f"  [skip] {p['id']} Bild fehlt: {p['image']}")
            continue
        with Image.open(img_path) as im:
            p["dominant_colors"] = dominant_colors(im)
        done += 1
        if done % 50 == 0:
            print(f"  ... {done} analysiert")

    DB.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Fertig. {done} Produkte analysiert, {len(items)} gesamt.")


if __name__ == "__main__":
    main()
