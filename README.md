# Atrelle Fit-Kit

Fertige Produktdatenbank + Generator für tägliche Flatlay-Fits.

## Inhalt

```
atrelle_kit/
├── atrelle_products.json     453 Produkte, strukturiert
├── products/                 453 saubere PNGs (kein Text, kein Preis)
├── generate_fits.py          Fit-Generator
└── README.md
```

## Sofort loslegen

```bash
python generate_fits.py --count 7
```

Erzeugt 7 Ordner unter `./fits/`, jeder mit:
- 4 Produktbilder (Top, Bottom, Outer, Sneaker)
- optional ein Gürtelbild (nur wenn eine Hose/Shorts im Fit ist)
- `prompt.txt` — fertiger Flatlay-Prompt zum Kopieren
- `manifest.json` — welche Produkte drin sind

## Optionen

```bash
python generate_fits.py --count 10 --theme streetwear
python generate_fits.py --count 3 --theme summer --out ./montag
python generate_fits.py --count 5 --seed 42        # reproduzierbar
```

Themes: `streetwear`, `summer`, `winter`, `clean`, `colorful`
Ohne `--theme` wird pro Fit zufällig eins gewählt.

## Täglich automatisch

**Mac/Linux** — `crontab -e`, dann:
```
0 6 * * * cd /pfad/zu/atrelle_kit && python3 generate_fits.py --count 7 --out fits/$(date +\%Y-\%m-\%d)
```

**Windows** — Task Scheduler, tägliche Aufgabe, Programm `python`, Argumente `generate_fits.py --count 7`.

## Datenstruktur

```json
{
  "id": "ATR001",
  "name": "Casa Summer Set",
  "category": "Sets & Tracksuits",
  "slot": "set",
  "colors": ["weiss"],
  "price_eur": 59.99,
  "image": "products/p02_r0_c0.png",
  "male_safe": true,
  "is_main_product": true,
  "source": { "page": 2, "row": 0, "col": 0 }
}
```

**Slots:** `set`, `top`, `bottom`, `outer`, `shoes`, `belt`, `bag`, `cap`, `eyewear`

**Kategorien im Katalog:**

| Kategorie | Anzahl |
|---|---|
| Sneaker | 130 |
| Taschen & Wallets | 64 |
| Sets & Tracksuits | 63 |
| T-Shirts & Shirts | 45 |
| Sweater & Strick | 30 |
| Hoodies, Zipper & Jacken | 30 |
| Shorts | 27 |
| Sandalen, Heels & Slides | 21 |
| Sonnenbrillen | 16 |
| Caps | 12 |
| Hosen & Jeans | 12 |
| Gürtel | 3 |

`male_safe: false` filtert Damen-Artikel (Heels, Ballerinas, Handtaschen) automatisch raus — der Generator nutzt nur `male_safe: true`.

## Was Claude Code als Nächstes ausbauen kann

- **Higgsfield-Anbindung**: Prompt + Bilder direkt per API rendern lassen, statt manuell hochzuladen
- **Uhren/Parfüm-Bilder**: aktuell nur als Text im Prompt — Bilddownload ergänzen
- **Try-On-Prompts**: zweiter Prompt pro Fit mit Noa als Model
- **Duplikat-Schutz**: Log über bereits benutzte Kombinationen, damit sich Fits über Wochen nicht wiederholen
- **Farb-Logik verfeinern**: aktuell simples Matching über Farbnamen, könnte über echte Bildanalyse laufen

## Bekannte Einschränkungen

- Produktnamen stammen aus OCR — vereinzelt können Tippfehler drin sein (z.B. „weif" statt „weiß"). Für die Bildgenerierung irrelevant, für Textausgabe ggf. nachbessern.
- Der Katalog listet 478 Farbvarianten; 453 sind als eigenständige Kacheln extrahiert. Die Differenz sind Varianten, die im Katalog keine eigene Kachel haben.
- Nur 3 Gürtel im Katalog — bei vielen Fits pro Tag wiederholen die sich zwangsläufig.
