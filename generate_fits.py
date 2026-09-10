#!/usr/bin/env python3
"""
Atrelle Fit Generator
---------------------
Erzeugt pro Lauf N komplette Fits:
  - 4 Atrelle-Hauptprodukte (Top, Bottom/Set, Outer optional, Sneaker)
  - optional 1 Atrelle-Guertel (wenn der Fit ihn stilistisch vertraegt)
  - Flatlay-Prompt als prompt.txt
  - alle Referenzbilder als Einzeldateien im Fit-Ordner

Nutzung:
    python generate_fits.py --count 7
    python generate_fits.py --count 3 --theme streetwear --out ./output
"""

import argparse, json, random, shutil, os
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "atrelle_products.json"

# Farben, die als "neutral" gelten und zu allem passen
NEUTRAL = {"schwarz", "weiss", "grau", "dunkelgrau", "beige", "creme"}

# Kategorien, in denen ein Guertel Sinn ergibt (Hose/Jeans sichtbar)
BELT_SLOTS = {"bottom"}

THEMES = {
    "streetwear": {"prefer": ["schwarz", "grau", "weiss"], "outer": True},
    "summer":     {"prefer": ["weiss", "beige", "hellblau", "creme"], "outer": False},
    "winter":     {"prefer": ["schwarz", "dunkelgrau", "marineblau", "braun"], "outer": True},
    "clean":      {"prefer": ["weiss", "schwarz", "grau"], "outer": False},
    "colorful":   {"prefer": ["blau", "gruen", "rot", "gelb"], "outer": True},
}


def load_products():
    with open(DB, encoding="utf-8") as f:
        items = json.load(f)
    return [p for p in items if p["male_safe"]]


def by_slot(products, slot):
    return [p for p in products if p["slot"] == slot]


def color_match(product, prefer):
    """Score: wie gut passt das Produkt zum Theme."""
    if not prefer:
        return 1
    cols = product["colors"]
    if not cols:
        return 1
    score = sum(2 for c in cols if c in prefer)
    score += sum(1 for c in cols if c in NEUTRAL)
    return score


def colors_clash(a, b):
    """Zwei kraeftige, unterschiedliche Farben gleichzeitig vermeiden."""
    ca = [c for c in a["colors"] if c not in NEUTRAL]
    cb = [c for c in b["colors"] if c not in NEUTRAL]
    if not ca or not cb:
        return False
    return set(ca) != set(cb)


def pick(pool, prefer, exclude_ids, avoid_clash_with=None, tries=40):
    candidates = [p for p in pool if p["id"] not in exclude_ids]
    if not candidates:
        return None
    weights = [color_match(p, prefer) for p in candidates]
    for _ in range(tries):
        choice = random.choices(candidates, weights=weights, k=1)[0]
        if avoid_clash_with and colors_clash(choice, avoid_clash_with):
            continue
        return choice
    return random.choices(candidates, weights=weights, k=1)[0]


def wants_belt(fit):
    """Guertel nur, wenn eine echte Hose/Shorts im Fit ist (kein Tracksuit-Set)."""
    return any(p["slot"] in BELT_SLOTS for p in fit)


def build_fit(products, theme):
    cfg = THEMES.get(theme, {"prefer": [], "outer": None})
    prefer = cfg["prefer"]
    want_outer = cfg["outer"]
    if want_outer is None:
        want_outer = random.random() < 0.5

    used = set()
    fit = []

    sets = by_slot(products, "set")
    use_set = (not want_outer) and random.random() < 0.35 and sets

    if use_set:
        s = pick(sets, prefer, used)
        fit.append(s); used.add(s["id"])
    else:
        top = pick(by_slot(products, "top"), prefer, used)
        fit.append(top); used.add(top["id"])

        bottom = pick(by_slot(products, "bottom"), prefer, used, avoid_clash_with=top)
        fit.append(bottom); used.add(bottom["id"])

        if want_outer:
            outer = pick(by_slot(products, "outer"), prefer, used, avoid_clash_with=top)
            if outer:
                fit.append(outer); used.add(outer["id"])

    # Sneaker sind Pflicht
    shoes = pick([p for p in by_slot(products, "shoes") if "Sneaker" in p["name"]],
                 prefer, used, avoid_clash_with=fit[0])
    fit.append(shoes); used.add(shoes["id"])

    # auf genau 4 Hauptprodukte auffuellen
    filler_slots = ["cap", "eyewear", "bag"]
    while len(fit) < 4:
        slot = filler_slots.pop(0) if filler_slots else "top"
        extra = pick(by_slot(products, slot), prefer, used, avoid_clash_with=fit[0])
        if not extra:
            continue
        fit.append(extra); used.add(extra["id"])

    fit = fit[:4]

    belt = None
    if wants_belt(fit):
        belts = by_slot(products, "belt")
        if belts:
            belt = pick(belts, prefer, used)

    return fit, belt


def make_prompt(fit, belt, watch, perfume):
    names = [p["name"] for p in fit]
    items = ", ".join(names)
    has_sneaker = any(p["slot"] == "shoes" for p in fit)

    lines = []
    lines.append(
        "Erstelle ein Flatlay-Foto im 9:16-Format: die angehaengten Kleidungsstuecke "
        "und Accessoires von oben auf einem hellen, flauschigen Teppich arrangiert, "
        "natuerliches Licht, Handy-Kamera-Perspektive, aufgeraeumtes Layout wie ein "
        "typisches Instagram/TikTok-Outfit-Flatlay."
    )
    lines.append("")
    lines.append(f"Enthaltene Artikel: {items}.")
    if belt:
        lines.append(f"Zusaetzlich im Flatlay sichtbar: {belt['name']} (Guertel).")
    lines.append(f"Ausserdem im Flatlay sichtbar: {watch['name']} (Uhr) "
                 f"und {perfume['name']} (Parfuem).")
    lines.append("")
    lines.append(
        "Nutze AUSSCHLIESSLICH die exakten Artikel aus den angehaengten Fotos als Vorlage "
        "fuer Schnitt, Form, Silhouette, Proportionen, Farbe, Material, Muster, Naehte, "
        "Applikationen, Logos, Sohlenform, Schnuerung, Verschluesse, Taschen und "
        "Reissverschluesse. Erfinde keine abweichenden Kleidungsstuecke, Logos, Marken "
        "oder Etiketten. Interpretiere nichts kreativ, modernisiere nichts, vereinfache "
        "nichts. Kopiere keine Texte oder Wasserzeichen. Fuege keinen Text ins Bild ein."
    )
    if has_sneaker:
        lines.append("")
        lines.append(
            "Wichtig beim Sneaker: zeige ihn exakt in der Seitenansicht wie im Referenzfoto, "
            "nicht von oben oder in anderer Perspektive. Positioniere die Sneaker stylisch "
            "und nicht flach parallel nebeneinander: ein Schuh leicht schraeg/angewinkelt vor "
            "oder neben dem anderen, leicht ueberlappend, wie bei einem professionellen "
            "Streetwear-Flatlay. Schnuersenkel ordentlich drapiert, nicht wirr hingelegt."
        )
    return "\n".join(lines)


ASSETS = BASE / "assets"


def load_assets(kind):
    """Laedt assets/<kind>.json und behaelt nur Eintraege, deren Bilddatei
    tatsaechlich vorhanden ist (fetch_assets.py fuellt fehlende nach)."""
    path = ASSETS / f"{kind}.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    present = [it for it in items if (BASE / it["file"]).exists()]
    missing = [it["id"] for it in items if not (BASE / it["file"]).exists()]
    if missing:
        print(f"  Hinweis: {kind}-Assets ohne Bild (uebersprungen, "
              f"'python fetch_assets.py' holt sie nach): {', '.join(missing)}")
    return present


def safe_name(name):
    """Dateisystem-sicherer Kurzname aus einem Produktnamen."""
    safe = "".join(c if c.isalnum() or c in "-_ " else "" for c in name).strip()
    return safe.replace(" ", "_")[:50] or "item"


def pick_accessory(pool, used_ids, window=10):
    """Waehlt eine Uhr/ein Parfuem, das sich ueber die letzten `window` Fits
    nicht wiederholt. Ist der Pool kleiner als das Fenster, wird das aelteste
    wieder freigegeben (sonst gaebe es keine gueltige Wahl)."""
    recent = set(used_ids[-window:])
    candidates = [a for a in pool if a["id"] not in recent]
    if not candidates:  # Pool kleiner als Fenster -> nur direkt letzte meiden
        last = used_ids[-1] if used_ids else None
        candidates = [a for a in pool if a["id"] != last] or list(pool)
    return random.choice(candidates)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5, help="Anzahl Fits")
    ap.add_argument("--theme", default=None, help=f"eins von: {', '.join(THEMES)}")
    ap.add_argument("--out", default="fits", help="Ausgabeordner")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    products = load_products()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    watches = load_assets("watches")
    perfumes = load_assets("perfumes")
    if not watches:
        raise SystemExit("Keine Uhren-Assets vorhanden. Erst 'python fetch_assets.py' laufen lassen.")
    if not perfumes:
        raise SystemExit("Keine Parfuem-Assets vorhanden. Erst 'python fetch_assets.py' laufen lassen.")

    used_watches, used_perfumes = [], []

    for i in range(1, args.count + 1):
        theme = args.theme or random.choice(list(THEMES))
        fit, belt = build_fit(products, theme)

        # Uhr und Parfuem pro Fit unterschiedlich (Wiederholung meiden)
        watch = pick_accessory(watches, used_watches)
        perfume = pick_accessory(perfumes, used_perfumes)
        used_watches.append(watch["id"])
        used_perfumes.append(perfume["id"])

        fitdir = outdir / f"fit_{i:02d}_{theme}"
        fitdir.mkdir(parents=True, exist_ok=True)

        manifest = {"fit": i, "theme": theme, "products": [], "belt": None,
                    "watch": None, "perfume": None}

        for n, p in enumerate(fit, 1):
            dest = fitdir / f"{n}_{p['slot']}_{safe_name(p['name'])}.png"
            shutil.copy(BASE / p["image"], dest)
            manifest["products"].append({"id": p["id"], "name": p["name"],
                                         "slot": p["slot"], "file": dest.name})

        if belt:
            dest = fitdir / f"5_belt_{safe_name(belt['name'])}.png"
            shutil.copy(BASE / belt["image"], dest)
            manifest["belt"] = {"id": belt["id"], "name": belt["name"], "file": dest.name}

        # Uhr- und Parfuembild mit in den Fit-Ordner kopieren
        w_dest = fitdir / f"6_watch_{safe_name(watch['name'])}.png"
        shutil.copy(BASE / watch["file"], w_dest)
        manifest["watch"] = {"id": watch["id"], "name": watch["name"], "file": w_dest.name}

        p_dest = fitdir / f"7_perfume_{safe_name(perfume['name'])}.png"
        shutil.copy(BASE / perfume["file"], p_dest)
        manifest["perfume"] = {"id": perfume["id"], "name": perfume["name"], "file": p_dest.name}

        prompt = make_prompt(fit, belt, watch, perfume)
        (fitdir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (fitdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        belt_txt = f" + {belt['name']}" if belt else ""
        print(f"[{i}/{args.count}] {fitdir.name}: "
              f"{', '.join(p['name'] for p in fit)}{belt_txt} "
              f"| {watch['name']} | {perfume['name']}")

    print(f"\nFertig. {args.count} Fits in: {outdir.resolve()}")


if __name__ == "__main__":
    main()
