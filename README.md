# Atrelle Fit-Kit

Fertige Produktdatenbank + Generator für tägliche Flatlay-Fits.

## Inhalt

```
atrelle_kit/
├── atrelle_products.json     453 Produkte inkl. dominant_colors (Bildanalyse)
├── products/                 453 saubere PNGs (kein Text, kein Preis)
├── assets/
│   ├── watches.json          Uhren-Katalog (Quelle, Farbton, Lizenz)
│   ├── perfumes.json         Parfüm-Katalog
│   ├── watches/              heruntergeladene Uhrenbilder
│   └── perfumes/             heruntergeladene Parfümbilder
├── generate_fits.py          Fit-Generator (Farbharmonie, Duplikat-Schutz, Check)
├── fetch_assets.py           lädt Uhren-/Parfümbilder (idempotent)
├── analyze_colors.py         dominante Produktfarben per k-means
├── clean_names.py            OCR-Namensbereinigung (einmalig gelaufen)
├── run_daily.sh / .bat       täglicher Lauf mit Datumsordner
└── README.md
```

## Einmalig einrichten

```bash
pip install Pillow numpy
python fetch_assets.py        # Uhren-/Parfümbilder holen
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
python generate_fits.py --count 5 --tryon          # zusätzlich prompt_tryon.txt
python generate_fits.py --count 5 --reset-history   # Duplikat-Historie leeren
```

Themes: `streetwear`, `summer`, `winter`, `clean`, `colorful`
Ohne `--theme` wird pro Fit zufällig eins gewählt.

Pro Fit-Ordner: 4 Produktbilder, optional Gürtelbild, 1 Uhr- und 1 Parfümbild,
`prompt.txt`, optional `prompt_tryon.txt`, `manifest.json`. Jeder Fit durchläuft
vor dem Schreiben einen Pflicht-Check (4 Hauptprodukte, Sneaker, genau 1 Uhr +
1 Parfüm, Gürtel-Regeln, alle Namen im Prompt); fällt er durch, wird neu gewürfelt.

## Manuelles Hochladen (ChatGPT / Gemini)

Alle Bilder sind lückenlos in Upload-Reihenfolge benannt (`1_`, `2_`, `3_`, …):
erst die Produkte, dann Gürtel, Uhr, Parfüm. Pro Fit:

1. Bilder in dieser Reihenfolge hochladen.
2. `prompt.txt` komplett kopieren und in dieselbe Nachricht einfügen.

Im Ausgabeordner liegt zusätzlich **`fits_uebersicht.md`** — pro Fit die
Bildliste und der komplett kopierbare Prompt untereinander, zum schnellen
Durcharbeiten.

**Bild-Limit:** ChatGPT und Gemini erlauben je **10 Bilder** pro Nachricht/Prompt.
Ein Fit hat max. 7 Bilder (4 Produkte + Gürtel + Uhr + Parfüm) und passt damit
immer in eine einzige Nachricht — kein Aufteilen nötig.

## Täglich automatisch

Der Tageslauf steckt in `run_daily.sh` (Mac/Linux) bzw. `run_daily.bat` (Windows).
Er stellt zuerst die Uhren-/Parfümbilder sicher (`fetch_assets.py`, idempotent),
schreibt die Fits nach `fits/JJJJ-MM-TT/` und protokolliert nach `logs/JJJJ-MM-TT.log`.
Über `history.json` wiederholen sich Kombinationen über Tage hinweg nicht.

Konfiguration über Umgebungsvariablen: `COUNT` (Anzahl, Default 7), `TRYON=1`
(zusätzlich Try-On-Prompts).

**Einmalig einrichten — Mac/Linux** (`crontab -e`), täglich 6:00 Uhr:
```
0 6 * * * COUNT=7 /pfad/zu/atrelle_kit/run_daily.sh
```

**Einmalig einrichten — Windows** (Aufgabenplanung / Task Scheduler):
Neue Aufgabe → Trigger „täglich 06:00" → Aktion „Programm starten" →
Programm/Skript: `C:\pfad\zu\atrelle_kit\run_daily.bat`.

Voraussetzung einmalig: Python 3 + `pip install Pillow numpy`.

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
