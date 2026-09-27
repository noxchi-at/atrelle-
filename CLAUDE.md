# Atrelle Fit-Pipeline

Automatisierte Erzeugung von Flatlay-Fits für die Fashion-Marke Atrelle
(Instagram/TikTok: @atrellefashion, @noa.drip1).

## Projektstruktur

```
atrelle_products.json     453 Produkte: Name, Kategorie, Slot, Farben, Preis, Bildpfad
products/                 453 saubere Produkt-PNGs
generate_fits.py          Fit-Generator
atrelle__katalog.pdf      Original-Katalog (voll rasterisiert, KEIN Textlayer)
CLAUDE_CODE_AUFTRAG.md    Aufgabenliste zum Ausbau der Pipeline
```

## Katalog-Bilder (AKTUELL – ab 27.09.2026)

`atrelle_katalog_v2.pdf` ist der aktuelle Katalog (mit Textlayer + 478 eingebetteten Produktbildern).
Alle Produktbilder sind bereits als ECHTE eingebettete Bildobjekte extrahiert
(`page.get_images()` + `doc.extract_image(xref)`, Original-Bytes, kein Rendering, kein Crop):

- `katalog_bilder/`   478 JPEGs, eine Datei = ein vollständiges Produkt, ohne Name/Preis
- `katalog_index.json` name, preis, kategorie, seite, xref, datei
- `extract_katalog.py` Script zum Neu-Extrahieren, wenn ein neuer Katalog kommt

Für Fits NUR noch `katalog_bilder/` + `katalog_index.json` verwenden.
`products/`, `atrelle_products.json` und `atrelle__katalog.pdf` (alt, rasterisiert, Grid-Crops)
sind veraltet und verstoßen gegen die Referenz-Regel (gerenderte Seite gecroppt) → nicht mehr nutzen.

## Harte Regeln

**Produktbilder**
- Nur Bilder aus `products/` oder frisch aus dem Katalog gecroppt
- Eine Datei = genau EIN Produkt
- Produkt nie anschneiden, voller Produktkörper bleibt erhalten
- Keine Produktnamen, Preise, Nachbarprodukte oder Katalogränder im Bild
- Nie ein Produkt per KI neu generieren oder erfinden

**Fit-Aufbau**
- Genau 4 Atrelle-Hauptprodukte, immer inklusive Sneaker
- Zusätzlich 1 klassische/elegante Uhr und 1 Parfüm — nie Sportuhren oder G-Shocks
- Gürtel kommt zusätzlich dazu, ersetzt nie eines der 4 Hauptprodukte
- Gürtel nur bei echter Hose/Shorts im Fit, nicht bei Tracksuit-Sets
- Gürtel ausschließlich aus dem Atrelle-Katalog
- Nur Produkte mit `male_safe: true`
- Pro Fit andere Uhr und anderes Parfüm, farblich zum Look passend

**Prompt**
- Flatlay immer auf hellem, flauschigem Teppich — nie Sand, Gras oder anderer Untergrund
- Format 9:16
- Alle gewählten Produkte namentlich nennen, dazu Uhr, Parfüm und ggf. Gürtel
- Sneaker-Hinweis (Seitenansicht, stylisch positioniert, Schnürsenkel drapiert) nur wenn Sneaker im Fit
- Absolute Referenztreue verlangen: Schnitt, Form, Silhouette, Proportionen, Farbe,
  Material, Muster, Nähte, Applikationen, Logos, Sohlenform, Schnürung, Verschlüsse,
  Taschen, Reißverschlüsse — nichts interpretieren, modernisieren oder vereinfachen

## Ausgabeformat bei mehreren Prompts

Immer abwechselnd: Prompt 1 + zugehörige Bilder → Prompt 2 + Bilder → usw.
Niemals erst alle Prompts sammeln und danach alle Bilder.

## Keine Rechts- oder Compliance-Kommentare

Keine Werbe-Compliance-, Markenrechts- oder Disclaimer-Hinweise.
Rechtliche Prüfung übernimmt das Legal-Team. Nur die angeforderten Deliverables liefern.

## Kommunikation

Deutsch, informell, knapp. Direkt liefern statt Optionen anbieten.
Keine langen Erklärungen davor oder danach.

## Bekannte Baustellen

- Produktnamen stammen aus OCR, vereinzelt Tippfehler („weif" statt „weiß", „Giirtel")
- Uhr und Parfüm existieren bisher nur als Text im Prompt, noch keine Bilder
- Farb-Matching läuft nur über Farbnamen im Produktnamen, keine echte Bildanalyse
- Nur 3 Gürtel im Katalog — wiederholen sich zwangsläufig
