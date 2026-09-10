#!/usr/bin/env python3
"""
Aufgabe 2 - Uhren- und Parfuembilder beschaffen.

Laedt die in assets/watches.json und assets/perfumes.json definierten
Produktfotos herunter und legt sie normalisiert (PNG, max. 900px) unter
assets/watches/ bzw. assets/perfumes/ ab.

Eigenschaften:
  - idempotent: vorhandene, gueltige Dateien werden uebersprungen
  - Mozilla-User-Agent (viele CDNs blocken sonst)
  - Retry mit exponentiellem Backoff (429/Netzfehler)
  - "commons:Datei.jpg" wird ueber den MD5-Pfad zu upload.wikimedia.org aufgeloest
  - jede geladene Datei wird mit PIL auf Gueltigkeit geprueft

Nutzung:
    python fetch_assets.py            # laedt fehlende Assets
    python fetch_assets.py --force    # laedt alle neu
"""
import argparse
import hashlib
import io
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

from PIL import Image

BASE = Path(__file__).parent
CATALOGS = {
    "watches": BASE / "assets" / "watches.json",
    "perfumes": BASE / "assets" / "perfumes.json",
}
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
MAX_PX = 900


def commons_url(filename: str, site: str = "commons", width: int = 0) -> str:
    """Rechnet den upload.wikimedia.org-Pfad aus dem Dateinamen (MD5-Schema).

    Originale werden aus dem CDN-Cache zuverlaessig geliefert; die On-the-fly-
    Thumbnail-URL liefert fuer manche Dateien 400. Default daher Original,
    optional eine Thumbnail-Breite (width>0).
    """
    f = filename.replace(" ", "_")
    h = hashlib.md5(f.encode("utf-8")).hexdigest()
    a, ab = h[0], h[0:2]
    if width:
        return f"https://upload.wikimedia.org/wikipedia/{site}/thumb/{a}/{ab}/{f}/{width}px-{f}"
    return f"https://upload.wikimedia.org/wikipedia/{site}/{a}/{ab}/{f}"


def resolve(source: str) -> str:
    if source.startswith("commons:"):
        return commons_url(source[len("commons:"):])
    return source


def download(url: str, tries: int = 4) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if not data:
                raise ValueError("leere Antwort")
            return data
        except Exception as e:  # noqa: BLE001
            last = e
            wait = 2 ** attempt
            print(f"      Versuch {attempt + 1}/{tries} fehlgeschlagen ({e}); warte {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Download endgueltig fehlgeschlagen: {last}")


def normalize_and_save(data: bytes, dest: Path):
    img = Image.open(io.BytesIO(data))
    img.load()
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_PX:
        scale = MAX_PX / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "PNG")


def is_valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:  # noqa: BLE001
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="alle Assets neu laden")
    args = ap.parse_args()

    ok, skipped, failed = [], [], []
    for cat, path in CATALOGS.items():
        items = json.loads(path.read_text(encoding="utf-8"))
        print(f"\n== {cat}: {len(items)} Eintraege ==")
        for it in items:
            dest = BASE / it["file"]
            if not args.force and is_valid(dest):
                print(f"  [skip] {it['id']} {it['name']} (bereits vorhanden)")
                skipped.append(it["id"])
                continue
            url = resolve(it["source"])
            print(f"  [get ] {it['id']} {it['name']}")
            print(f"         {url}")
            try:
                data = download(url)
                normalize_and_save(data, dest)
                if not is_valid(dest):
                    raise RuntimeError("gespeicherte Datei ist kein gueltiges Bild")
                print(f"         -> {it['file']} ({dest.stat().st_size // 1024} KB)")
                ok.append(it["id"])
            except Exception as e:  # noqa: BLE001
                print(f"         FEHLER: {e}")
                failed.append((it["id"], it["name"], str(e)))

    print("\n=== Zusammenfassung ===")
    print(f"  geladen : {len(ok)}  {ok}")
    print(f"  skip    : {len(skipped)}")
    if failed:
        print(f"  FEHLER  : {len(failed)}")
        for fid, name, err in failed:
            print(f"    - {fid} {name}: {err}")
    else:
        print("  FEHLER  : 0")


if __name__ == "__main__":
    main()
