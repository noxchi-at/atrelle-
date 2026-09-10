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

import argparse, colorsys, json, random, shutil, os
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "atrelle_products.json"

# Farben, die als "neutral" gelten und zu allem passen
NEUTRAL = {"schwarz", "weiss", "grau", "dunkelgrau", "hellgrau", "anthrazit",
           "silber", "beige", "creme", "sand", "khaki"}

# Kategorien, in denen ein Guertel Sinn ergibt (Hose/Jeans sichtbar)
BELT_SLOTS = {"bottom"}

# Max. Bilder, die ChatGPT und Gemini gemeinsam pro Nachricht/Prompt zulassen.
# ChatGPT: 10 pro Nachricht (Web seit 02/2026 bis 20), Gemini: 10 pro Prompt.
# Ein Fit hat max. 7 Bilder (4 Produkte + Guertel + Uhr + Parfuem) -> immer drunter.
MAX_UPLOAD = 10

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


def product_color_names(product):
    """Farbnamen aus manuellem Token-Feld + Bildanalyse (dominant_colors)."""
    names = set(product.get("colors") or [])
    for c in product.get("dominant_colors", []):
        if c.get("weight", 0) >= 0.15:
            names.add(c["name"])
    return names


def accent_hsv(product):
    """Kraeftigste Akzentfarbe des Produkts als (h,s,v) aus der Bildanalyse.
    None, wenn das Produkt praktisch neutral ist (nur schwarz/weiss/grau/...)."""
    best = None
    for c in product.get("dominant_colors", []):
        r, g, b = [v / 255.0 for v in c["rgb"]]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s >= 0.22 and v >= 0.15 and c.get("weight", 0) >= 0.12:
            if best is None or s > best[1]:
                best = (h, s, v)
    return best


def is_neutral(product):
    return accent_hsv(product) is None


def _hue_diff(h1, h2):
    d = abs(h1 - h2) % 1.0
    return min(d, 1.0 - d)   # 0..0.5


def color_match(product, prefer):
    """Score: wie gut passt das Produkt zum Theme (Namen aus Feld + Analyse)."""
    if not prefer:
        return 1
    cols = product_color_names(product)
    if not cols:
        return 1
    score = sum(2 for c in cols if c in prefer)
    score += sum(1 for c in cols if c in NEUTRAL)
    return max(score, 1)


def colors_clash(a, b):
    """Zwei kraeftige, unterschiedlich-farbige Teile vermeiden.
    Neutral vs. alles = kein Clash; zwei Akzentfarben clashen, wenn ihr
    Farbton (Hue) zu weit auseinanderliegt (nicht mehr analog)."""
    aa, ba = accent_hsv(a), accent_hsv(b)
    if aa is None or ba is None:
        return False
    return _hue_diff(aa[0], ba[0]) > 0.12   # ~43 Grad


def pick(pool, prefer, exclude_ids, avoid_clash_with=None, tries=40):
    candidates = [p for p in pool if p["id"] not in exclude_ids]
    if not candidates:
        return None
    weights = [color_match(p, prefer) for p in candidates]
    if isinstance(avoid_clash_with, list):
        avoid = [o for o in avoid_clash_with if o]
    elif avoid_clash_with:
        avoid = [avoid_clash_with]
    else:
        avoid = []
    for _ in range(tries):
        choice = random.choices(candidates, weights=weights, k=1)[0]
        if any(colors_clash(choice, o) for o in avoid):
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

        bottom = pick(by_slot(products, "bottom"), prefer, used, avoid_clash_with=fit)
        fit.append(bottom); used.add(bottom["id"])

        if want_outer:
            outer = pick(by_slot(products, "outer"), prefer, used, avoid_clash_with=fit)
            if outer:
                fit.append(outer); used.add(outer["id"])

    # Sneaker sind Pflicht
    shoes = pick([p for p in by_slot(products, "shoes") if "Sneaker" in p["name"]],
                 prefer, used, avoid_clash_with=fit)
    fit.append(shoes); used.add(shoes["id"])

    # auf genau 4 Hauptprodukte auffuellen
    filler_slots = ["cap", "eyewear", "bag"]
    while len(fit) < 4:
        slot = filler_slots.pop(0) if filler_slots else "top"
        extra = pick(by_slot(products, slot), prefer, used, avoid_clash_with=fit)
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


def build_fresh_fit(products, theme, seen_combos, tries=400):
    """Baut einen Fit, dessen Haupt-Kombination noch nicht in `seen_combos`
    vorkam. Sind alle moeglichen Kombinationen erschoepft, wird nach `tries`
    Versuchen die letzte zurueckgegeben (mit Warnung)."""
    last = None
    for _ in range(tries):
        fit, belt = build_fit(products, theme)
        sig = fit_signature(fit)
        last = (fit, belt, sig)
        if sig not in seen_combos:
            return fit, belt, sig
    print(f"  [warn] keine neue Kombination nach {tries} Versuchen gefunden "
          f"(Pool erschoepft) - erlaube Wiederholung")
    return last


def check_fit(fit, belt, watch, perfume, prompt, valid_ids):
    """Pflicht-Check vor jedem Fit. Gibt (ok, [Probleme]) zurueck.
    Ein Fit gilt als NICHT FERTIG, sobald ein Punkt fehlschlaegt."""
    p = []

    # genau 4 Hauptprodukte
    if len(fit) != 4:
        p.append(f"nicht genau 4 Hauptprodukte ({len(fit)})")
    # alle existieren im Katalog
    for it in fit:
        if it["id"] not in valid_ids:
            p.append(f"Produkt {it['id']} nicht im Katalog")
    # nur male_safe
    for it in fit:
        if not it.get("male_safe"):
            p.append(f"Produkt {it['id']} ist nicht male_safe")
    # immer inkl. Sneaker
    sneakers = [it for it in fit if it["slot"] == "shoes" and "Sneaker" in it["name"]]
    if len(sneakers) < 1:
        p.append("kein Sneaker im Fit")
    # genau 1 klassische Uhr
    if not watch:
        p.append("keine Uhr")
    elif "klassisch" not in watch.get("type", ""):
        p.append(f"Uhr nicht als klassisch/elegant markiert: {watch.get('name')}")
    # genau 1 Parfuem
    if not perfume:
        p.append("kein Parfuem")
    # Guertel-Eignung
    if wants_belt(fit):
        if belt is not None:
            if belt["slot"] != "belt" or belt["id"] not in valid_ids:
                p.append("Guertel nicht aus dem Atrelle-Katalog (slot 'belt')")
    else:
        if belt is not None:
            p.append("Guertel gesetzt, obwohl keine Hose/Shorts im Fit (Set/Tracksuit)")
    # jede Referenzdatei = genau EIN Produkt: Bildquelle aus products/, IDs eindeutig
    ids = [it["id"] for it in fit]
    if len(set(ids)) != len(ids):
        p.append("doppelte Produkte im Fit (Mischung/Duplikat)")
    for it in fit:
        if not str(it["image"]).startswith("products/"):
            p.append(f"Produktbild nicht aus products/: {it['id']}")
    # keine Produkte verschiedener Fits vermischt: Accessoires nicht aus Produktliste
    if watch and watch["id"] in ids:
        p.append("Uhr-ID kollidiert mit Produkt")
    if perfume and perfume["id"] in ids:
        p.append("Parfuem-ID kollidiert mit Produkt")
    # alle Namen im Prompt genannt
    for it in fit:
        if it["name"] not in prompt:
            p.append(f"Produkt nicht im Prompt genannt: {it['name']}")
    if watch and watch["name"] not in prompt:
        p.append(f"Uhr nicht im Prompt genannt: {watch['name']}")
    if perfume and perfume["name"] not in prompt:
        p.append(f"Parfuem nicht im Prompt genannt: {perfume['name']}")
    if belt and belt["name"] not in prompt:
        p.append(f"Guertel nicht im Prompt genannt: {belt['name']}")

    return (len(p) == 0), p


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


def make_tryon_prompt(fit, belt, watch, perfume):
    """Try-On-Prompt: Ganzkoerper-Spiegelselfie im 9:16-Format.
    Person aus einem Referenzfoto, Szene/Perspektive aus einem Spiegelfoto,
    nur Person und Outfit werden getauscht - Outfit exakt aus den Produktfotos."""
    items = ", ".join(p["name"] for p in fit)
    has_sneaker = any(p["slot"] == "shoes" for p in fit)

    lines = []
    lines.append(
        "Erstelle ein fotorealistisches Ganzkoerper-Spiegelselfie im 9:16-Hochformat. "
        "Eine Person haelt ein Smartphone und fotografiert sich im Spiegel, traegt das "
        "unten genannte Outfit komplett am Koerper."
    )
    lines.append("")
    lines.append(
        "PERSON: uebernimm Gesicht, Statur, Hautfarbe und Haare 1:1 aus dem angehaengten "
        "Personen-Referenzfoto. Aendere Identitaet, Koerperbau und Gesichtszuege nicht."
    )
    lines.append(
        "SZENE: uebernimm Hintergrund, Raum, Licht, Spiegel und Kameraperspektive 1:1 aus "
        "dem angehaengten Spiegelfoto-Referenzbild. Nur Person und Outfit werden ausgetauscht."
    )
    lines.append("")
    lines.append(f"OUTFIT (am Koerper getragen): {items}.")
    if belt:
        lines.append(f"Dazu getragen: {belt['name']} (Guertel).")
    lines.append(f"Accessoires: {watch['name']} (Uhr am Handgelenk); "
                 f"{perfume['name']} (Parfuem) dezent im Bild, z.B. in der freien Hand oder Tasche.")
    lines.append("")
    lines.append(
        "Nutze fuer JEDES Kleidungsstueck AUSSCHLIESSLICH das jeweils angehaengte Produktfoto "
        "als Vorlage fuer Schnitt, Form, Silhouette, Proportionen, Farbe, Material, Muster, "
        "Naehte, Applikationen, Logos, Sohlenform, Schnuerung, Verschluesse, Taschen und "
        "Reissverschluesse. Kombiniere die Teile realistisch am Koerper (Oberteil, Hose/Shorts, "
        "ggf. Jacke/Weste, Sneaker). Erfinde keine abweichenden Kleidungsstuecke, Logos oder "
        "Marken, interpretiere nichts kreativ, modernisiere und vereinfache nichts. Fuege "
        "keinen Text und keine Wasserzeichen ein."
    )
    if has_sneaker:
        lines.append(
            "Die Sneaker exakt wie im Referenzfoto (Form, Sohle, Schnuerung, Farbe), "
            "korrekt an den Fuessen getragen."
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


HISTORY = BASE / "history.json"


def load_history():
    if HISTORY.exists():
        h = json.loads(HISTORY.read_text(encoding="utf-8"))
    else:
        h = {}
    h.setdefault("combos", [])      # Liste sortierter Haupt-ID-Signaturen
    h.setdefault("watches", [])     # Uhr-IDs in Reihenfolge
    h.setdefault("perfumes", [])    # Parfuem-IDs in Reihenfolge
    return h


def save_history(h):
    HISTORY.write_text(json.dumps(h, indent=2, ensure_ascii=False), encoding="utf-8")


def fit_signature(fit):
    """Eindeutige Signatur einer Produkt-Kombination (die 4 Hauptprodukte)."""
    return "|".join(sorted(p["id"] for p in fit))


def write_overview(outdir, overview, tryon_on):
    """Schreibt fits_uebersicht.md: pro Fit die Bild-Upload-Reihenfolge und
    den komplett kopierbaren Prompt untereinander - fuers manuelle Hochladen
    bei ChatGPT und Gemini."""
    md = []
    md.append("# Fits-Übersicht — Upload für ChatGPT & Gemini\n")
    md.append("**So gehst du pro Fit vor:**\n")
    md.append("1. Fit-Ordner öffnen.")
    md.append("2. Bilder in der angegebenen Reihenfolge (1, 2, 3, …) hochladen.")
    md.append("3. Den Prompt-Block darunter komplett kopieren und in dieselbe "
              "Nachricht einfügen.\n")
    md.append(f"**Bild-Limit:** ChatGPT und Gemini erlauben je {MAX_UPLOAD} Bilder "
              "pro Nachricht/Prompt. Jeder Fit hat max. 7 Bilder (4 Produkte + "
              "Gürtel + Uhr + Parfüm) und passt damit immer in **eine** Nachricht.\n")
    if tryon_on:
        md.append("Zu jedem Fit gibt es zusätzlich einen **Try-On-Prompt** "
                  "(Spiegelselfie). Dafür zusätzlich das Personen-Referenzfoto und "
                  "das Spiegelfoto-Referenzbild hochladen.\n")
    md.append(f"_{len(overview)} Fits._\n")
    md.append("---\n")

    for o in overview:
        md.append(f"## Fit {o['i']:02d} — {o['theme']}  \n")
        md.append(f"Ordner: `{o['dir']}`  ·  {len(o['upload'])} Bilder\n")
        md.append(f"**Bilder in Upload-Reihenfolge:**\n")
        for n, (fname, label) in enumerate(o["upload"], 1):
            md.append(f"{n}. `{fname}` — {label}")
        md.append("")
        md.append("**Prompt (komplett kopieren):**\n")
        md.append("```")
        md.append(o["prompt"])
        md.append("```\n")
        if o["tryon"]:
            md.append("**Try-On-Prompt (komplett kopieren):**\n")
            md.append("```")
            md.append(o["tryon"])
            md.append("```\n")
        md.append("---\n")

    (outdir / "fits_uebersicht.md").write_text("\n".join(md), encoding="utf-8")


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
    ap.add_argument("--reset-history", action="store_true",
                    help="history.json vor dem Lauf leeren")
    ap.add_argument("--tryon", action="store_true",
                    help="zusaetzlich prompt_tryon.txt (Spiegelselfie) pro Fit erzeugen")
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

    all_ids = {p["id"] for p in json.loads(DB.read_text(encoding="utf-8"))}

    history = load_history()
    if args.reset_history:
        history = {"combos": [], "watches": [], "perfumes": []}
    seen_combos = set(history["combos"])
    used_watches = list(history["watches"])
    used_perfumes = list(history["perfumes"])

    overview = []

    for i in range(1, args.count + 1):
        theme = args.theme or random.choice(list(THEMES))

        # Fit bauen + Pflicht-Check; bei Fehlschlag verwerfen und neu wuerfeln
        chosen = None
        for attempt in range(1, 51):
            fit, belt, sig = build_fresh_fit(products, theme, seen_combos)
            watch = pick_accessory(watches, used_watches)
            perfume = pick_accessory(perfumes, used_perfumes)
            prompt = make_prompt(fit, belt, watch, perfume)
            ok, problems = check_fit(fit, belt, watch, perfume, prompt, all_ids)
            if ok:
                chosen = (fit, belt, sig, watch, perfume, prompt)
                break
            print(f"  [Fit {i} verworfen, Versuch {attempt}] " + "; ".join(problems))
        if chosen is None:
            raise SystemExit(f"Fit {i}: kein gueltiger Fit nach 50 Versuchen")

        fit, belt, sig, watch, perfume, prompt = chosen
        seen_combos.add(sig)
        history["combos"].append(sig)
        used_watches.append(watch["id"])
        used_perfumes.append(perfume["id"])

        fitdir = outdir / f"fit_{i:02d}_{theme}"
        fitdir.mkdir(parents=True, exist_ok=True)

        manifest = {"fit": i, "theme": theme, "products": [], "belt": None,
                    "watch": None, "perfume": None, "upload_order": []}

        # Alle Bilder in EINER lueckenlosen Upload-Reihenfolge nummerieren
        # (1_, 2_, 3_ ...): erst die Produkte, dann Guertel, Uhr, Parfuem.
        upload = []  # (filename, label) in Reihenfolge
        idx = 0

        def add_image(src_rel, slot_tag, name, label):
            nonlocal idx
            idx += 1
            dest = fitdir / f"{idx}_{slot_tag}_{safe_name(name)}.png"
            shutil.copy(BASE / src_rel, dest)
            upload.append((dest.name, label))
            return dest.name

        for p in fit:
            fname = add_image(p["image"], p["slot"], p["name"], f"{p['name']} ({p['slot']})")
            manifest["products"].append({"id": p["id"], "name": p["name"],
                                         "slot": p["slot"], "file": fname})

        if belt:
            fname = add_image(belt["image"], "belt", belt["name"], f"{belt['name']} (Guertel)")
            manifest["belt"] = {"id": belt["id"], "name": belt["name"], "file": fname}

        fname = add_image(watch["file"], "watch", watch["name"], f"{watch['name']} (Uhr)")
        manifest["watch"] = {"id": watch["id"], "name": watch["name"], "file": fname}

        fname = add_image(perfume["file"], "perfume", perfume["name"], f"{perfume['name']} (Parfuem)")
        manifest["perfume"] = {"id": perfume["id"], "name": perfume["name"], "file": fname}

        manifest["upload_order"] = [f for f, _ in upload]
        if len(upload) > MAX_UPLOAD:
            print(f"  [warn] Fit {i} hat {len(upload)} Bilder > Limit {MAX_UPLOAD} "
                  f"(ChatGPT/Gemini) - in zwei Nachrichten hochladen")

        (fitdir / "prompt.txt").write_text(prompt, encoding="utf-8")
        tryon = None
        if args.tryon:
            tryon = make_tryon_prompt(fit, belt, watch, perfume)
            (fitdir / "prompt_tryon.txt").write_text(tryon, encoding="utf-8")
        (fitdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        overview.append({
            "dir": fitdir.name, "i": i, "theme": theme,
            "upload": upload, "prompt": prompt, "tryon": tryon,
        })

        belt_txt = f" + {belt['name']}" if belt else ""
        print(f"[{i}/{args.count}] {fitdir.name}: "
              f"{', '.join(p['name'] for p in fit)}{belt_txt} "
              f"| {watch['name']} | {perfume['name']}")

    write_overview(outdir, overview, args.tryon)

    # History persistieren (combos vollstaendig, Accessoire-Verlauf begrenzt)
    history["watches"] = used_watches[-100:]
    history["perfumes"] = used_perfumes[-100:]
    save_history(history)

    print(f"\nFertig. {args.count} Fits in: {outdir.resolve()}")
    print(f"History: {len(history['combos'])} Kombinationen gesamt in {HISTORY.name}")


if __name__ == "__main__":
    main()
