# Atrelle Fit-Pipeline — Auftrag für Claude Code

Du arbeitest an einer bestehenden Pipeline für die Fashion-Marke Atrelle.
Im Projektordner liegen bereits:

- `atrelle_products.json` — 453 Produkte mit Name, Kategorie, Slot, Farben, Preis, Bildpfad
- `products/` — 453 saubere Produkt-PNGs (kein Katalogtext, keine Preise)
- `generate_fits.py` — funktionierender Basis-Generator
- `atrelle__katalog.pdf` — der Original-Katalog (voll rasterisiert, kein Textlayer)

Lies zuerst `README.md` und `generate_fits.py`, bevor du irgendwas änderst.

---

## Was die Pipeline am Ende können muss

Ein einziger Befehl erzeugt beliebig viele fertige Fits:

```
python generate_fits.py --count 10
```

Pro Fit ein Ordner mit:
- genau 4 Atrelle-Hauptprodukten als Einzelbilder
- optional 1 Atrelle-Gürtel als Einzelbild (nur wenn der Fit ihn verträgt)
- 1 Uhrenbild + 1 Parfümbild
- `prompt.txt` — fertiger Flatlay-Prompt
- `manifest.json` — Inhalt des Fits

---

## Harte Regeln (nicht verhandelbar)

**Produktbilder**
- Referenzbilder kommen ausschließlich aus `products/` oder werden neu aus dem Katalog-PDF gecroppt
- Jede Referenzdatei enthält GENAU EIN Produkt
- Kein Produkt darf angeschnitten sein — der volle sichtbare Produktkörper bleibt erhalten
- Keine Produktnamen, keine Preise, keine Nachbarprodukte, keine Katalogränder im Bild
- Nie ein Produkt per KI neu generieren oder erfinden

**Fit-Zusammenstellung**
- Genau 4 Hauptprodukte, immer mit Sneaker
- Gürtel ersetzt nie eines der 4 Hauptprodukte — er kommt zusätzlich dazu
- Gürtel nur, wenn eine echte Hose/Shorts im Fit ist (nicht bei Tracksuit-Sets)
- Gürtel ausschließlich aus dem Atrelle-Katalog
- Nur `male_safe: true` Produkte verwenden
- Pro Fit eine andere Uhr und ein anderes Parfüm, farblich zum Look passend
- Uhr immer klassisch/elegant — keine Sportuhren, keine G-Shocks

**Prompt**
- Alle gewählten Produkte namentlich im Prompt nennen
- Uhr und Parfüm ausdrücklich im Prompt nennen
- Gürtel im Prompt nennen, falls gewählt
- Flatlay immer auf hellem, flauschigem Teppich — nie Sand, Gras oder anderer Untergrund
- Format 9:16
- Sneaker-Hinweis (Seitenansicht, stylisch positioniert) nur wenn Sneaker im Fit
- Absolute Referenztreue verlangen: Schnitt, Form, Silhouette, Proportionen, Farbe, Material, Muster, Nähte, Applikationen, Logos, Sohlenform, Schnürung, Verschlüsse, Taschen, Reißverschlüsse — exakt wie im Referenzbild, nichts interpretieren, nichts modernisieren, nichts vereinfachen

---

## Aufgabe 1 — Produktnamen bereinigen

Die Namen in `atrelle_products.json` stammen aus OCR und haben Fehler
(z.B. „weif" statt „weiß", „Giirtel" statt „Gürtel", vereinzelt Müll-Präfixe).

Geh alle 453 Namen durch, korrigiere systematisch die OCR-Fehler und
schreib die bereinigte Datei zurück. Häufige Muster:
- `weif`, `weiK`, `weiB` → `weiß`
- `gruen` → `grün`, `Girtel`/`Giirtel` → `Gürtel`
- führende Einzelbuchstaben oder Zeichenmüll entfernen

Zeig mir am Ende eine Liste aller Änderungen zur Kontrolle.

## Aufgabe 2 — Uhren- und Parfümbilder

Aktuell stehen Uhr und Parfüm nur als Text im Prompt.
Bau einen lokalen Asset-Ordner `assets/watches/` und `assets/perfumes/`
mit echten Produktfotos (offizielle Herstellerbilder, per Websuche).

Der Generator kopiert dann pro Fit das passende Uhren- und Parfümbild
mit in den Fit-Ordner, genau wie die Produktbilder.

Hinweis: viele CDNs blockieren Direktdownloads. Casio-Bilder lassen sich
von casio.com mit einem Mozilla-User-Agent ziehen.

## Aufgabe 3 — Duplikat-Schutz

Leg eine `history.json` an, die alle bisher erzeugten Produkt-Kombinationen
speichert. Der Generator darf keine Kombination zweimal ausgeben, solange
noch ungenutzte möglich sind. Uhr und Parfüm sollen sich über die letzten
10 Fits nicht wiederholen.

## Aufgabe 4 — Farb-Logik verbessern

Aktuell matched der Generator nur über Farbnamen im Produktnamen.
Bau eine echte Bildanalyse: extrahier pro Produkt die dominanten Farben
(z.B. per k-means auf dem PNG, Hintergrund ignorieren), speicher sie als
`dominant_colors` in der JSON, und nutze die für das Fit-Matching.

Ziel: Fits sollen farblich stimmig sein, nicht zufällig zusammengewürfelt.

## Aufgabe 5 — Try-On-Prompt

Erzeuge pro Fit optional einen zweiten Prompt `prompt_tryon.txt`:
Ganzkörper-Spiegelselfie im 9:16-Format, Person aus einem Referenzfoto
(Gesicht, Statur, Hautfarbe, Haare 1:1 übernehmen), Hintergrund und
Kameraperspektive aus einem Spiegelfoto-Referenzbild, nur Person und
Outfit werden ausgetauscht.

Schalter: `--tryon`

## Aufgabe 6 — Tägliche Automatisierung

Richte ein, dass die Pipeline täglich automatisch läuft und die Fits
in einen Ordner mit Datumsstempel schreibt. Erklär mir kurz, was ich
dafür einmalig auf meinem System einrichten muss.

---

## Pflicht-Check vor jedem Fit

Bau diese Prüfung als Funktion in den Generator ein. Ein Fit gilt als
NICHT FERTIG, wenn auch nur ein Punkt fehlschlägt:

- [ ] Genau 4 Atrelle-Hauptprodukte
- [ ] Alle 4 existieren in `atrelle_products.json`
- [ ] Genau 1 klassische/elegante Uhr
- [ ] Genau 1 Parfüm
- [ ] Gürtel-Eignung geprüft
- [ ] Falls passend: Gürtel aus dem Atrelle-Katalog ergänzt
- [ ] Jede Referenzdatei enthält nur EIN Produkt
- [ ] Kein Produkt angeschnitten
- [ ] Keine Preise, keine Produktnamen, keine Nachbarprodukte in den Bildern
- [ ] Alle gewählten Produkte namentlich im Prompt genannt
- [ ] Uhr, Parfüm und ggf. Gürtel im Prompt genannt
- [ ] Keine zusätzlichen Produkte erfunden
- [ ] Keine Produkte verschiedener Fits vermischt

Wenn ein Check fehlschlägt: Fit verwerfen und neu würfeln, mit Log-Ausgabe warum.

---

## Arbeitsweise

Geh die Aufgaben der Reihe nach durch. Nach jeder Aufgabe:
Testlauf mit `--count 3`, zeig mir das Ergebnis, dann weiter zur nächsten.
Keine Aufgabe überspringen, keine Rückfragen bei Details die du selbst
entscheiden kannst.
