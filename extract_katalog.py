"""Extrahiert ALLE eingebetteten Produktbilder aus atrelle_katalog_v2.pdf (echte Bildobjekte,
kein Seiten-Rendering) + Produktname/Preis/Kategorie aus dem Text unter dem Bild."""
import json, re, pymupdf, sys
pdf = sys.argv[1] if len(sys.argv) > 1 else "atrelle_katalog_v2.pdf"
d = pymupdf.open(pdf)
out, cat, seen = [], None, {}
def slug(s):
    s = s.lower().replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")
for pn, page in enumerate(d):
    blocks = [b for b in page.get_text("blocks")]
    for b in blocks:  # Kategorie-Überschrift (steht über "N Produkte, ...")
        if "Produkte" in b[4] and "Farbvarianten" in b[4]:
            prev = [c for c in blocks if c[3] <= b[1] + 1 and abs(c[0]-b[0]) < 5]
            if prev: cat = prev[-1][4].strip()
    for img in page.get_images(full=True):
        xref, smask = img[0], img[1]
        for r in page.get_image_rects(xref):
            cx = (r.x0 + r.x1) / 2
            below = sorted([b for b in blocks if 0 <= b[1] - r.y1 < 20 and b[0] < cx < b[2]], key=lambda b: b[1])
            name = below[0][4].strip() if below else f"unbenannt_p{pn+1}_x{xref}"
            price = next((b[4].strip() for b in blocks if "EUR" in b[4] and 10 < b[1]-r.y1 < 35 and b[0] < cx < b[2]), "")
            base = slug(name); seen[base] = seen.get(base, 0) + 1
            fn = base if seen[base] == 1 else f"{base}_{seen[base]}"
            ex = d.extract_image(xref)  # Original-Bytes des eingebetteten Objekts, unverändert
            if smask:  # nur bei Alpha-Maske: als PNG mit Transparenz speichern
                pix = pymupdf.Pixmap(pymupdf.Pixmap(d, xref), pymupdf.Pixmap(d, smask))
                if pix.n - pix.alpha > 3: pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                ext, data = "png", pix.tobytes("png")
            else:
                ext, data = ex["ext"], ex["image"]
            path = f"katalog_bilder/{fn}.{ext}"
            open(path, "wb").write(data)
            out.append({"name": name, "preis": price, "kategorie": cat, "seite": pn+1,
                        "xref": xref, "datei": path, "px": [ex["width"], ex["height"]]})
json.dump(out, open("katalog_index.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "Bilder;", sum(1 for o in out if o["name"].startswith("unbenannt")), "ohne Namen")
