# Neonstadt

Ein ruhiges Aufbauspiel im Browser: Du baust eine Neon-Megastadt auf nassem, spiegelndem Wasser. Es gibt kein Geld, keine Ziele und keinen Druck, nur Bauen, Formen und Zuschauen. Vorbilder sind [Townscaper](https://store.steampowered.com/app/1291340/Townscaper/), [Altstadt](https://store.steampowered.com/app/5123730/Altstadt/) und [Miniopolis](https://store.steampowered.com/app/3814960/miniopolis/).

![Neonstadt: Startviertel bei Nacht und Regen](docs/vorschau.jpg)

## Spielen

Die Seite besteht aus einer einzigen Datei, `index.html`. Die Bibliotheken kommen vom CDN, darum braucht sie beim Laden Internet.

```sh
python3 -m http.server 8000   # dann http://localhost:8000 öffnen
```

Das Spiel läuft auch als Claude-Artefakt. Über GitHub Pages lässt es sich direkt aus dem Hauptordner ausliefern.

## Steuerung

| | Maus | Touch |
|---|---|---|
| Werkzeug anwenden | Linksklick | Tippen |
| Fläche aufziehen, Push/Pull | Linke Taste gedrückt ziehen | Mit einem Finger ziehen |
| Eine Etage abreißen | Rechtsklick | Lange drücken |
| Drehen | Rechte Taste ziehen (oder Linke Taste neben der Stadt) | Zwei Finger |
| Zoomen | Mausrad | Zwei Finger auseinander |
| Schieben | Mittlere Taste, Pfeiltasten oder WASD | – |

Tasten: `1`–`8` Werkzeuge, `Strg+Z` / `Strg+Y` Rückgängig und Wiederholen, `Q` / `E` um 45° drehen, `N` Stimmung, `R` Regen, `M` Ton, `Leertaste` Rundflug, `P` Fotomodus, `Esc` abbrechen.

## Werkzeuge

- **Bauen**: Ein Klick setzt einen Block oder stockt auf. Klickst du seitlich an ein Gebäude, wächst das Nachbarfeld bis auf die geklickte Höhe. Mit Ziehen entsteht ein Rechteck als zusammenhängendes Gebäude, auf dem Wasser, auf einem Dach oder an einer Fassade in genau dieser Höhe.
- **Formen** (Push/Pull wie in Miniopolis): Du greifst ein Dach (alle gleich hohen Felder desselben Gebäudes) und ziehst es hoch oder runter. Greifst du eine Fassade, schiebst du sie Felder weit raus oder rein.
- **Kanten**: Jede Außenecke wird eckig, schräg oder rund. Ein Klick auf die Dachmitte ändert das ganze Gebäude, Ziehen eine ganze Fläche. Runde und schräge Ecken bekommen eigene Fenster.
- **Straße**: Setzt Straßen. Auf einem Gebäude ab zwei Etagen entsteht ein Durchgang mit Neon-Bogen. Vier Straßenfelder im Quadrat werden zum Platz, oft mit Hologramm.
- **Park**: Leuchtbäume und Glühwürmchen.
- **Neon**: Ein Klick auf eine Fassade setzt ein Leuchtschild, ein Klick aufs Dach schaltet die Werbetafel an oder aus.
- **Gestalten**: Färbt das ganze Gebäude um oder wechselt den Stil, je nach Auswahl im Dock.
- **Abriss**: Ein Klick nimmt eine Etage weg. Mit Ziehen wird alles im Rechteck auf diese Höhe zurückgeschnitten.

Farben und Stile (Konzern, Megablock, Container, Pagode) wählst du im Dock. Bei „Zufall“ übernehmen Anbauten den Stil des Gebäudes, an das du baust.

## Was sich von selbst ergibt

Nachbarn gleicher Farbe und gleichen Stils verschmelzen zu einem Gebäude. Je nach Lage entstehen dann:
- Läden mit Markise an Straßen und Parks,
- Leuchtschilder, Klimageräte, Balkone, Vordächer mit Lampions,
- auf den Dächern Wassertanks, Antennen mit Blinklicht, Helipads und Werbetafeln,
- Glas-Skywalks zwischen Türmen und Lampionketten zwischen Containern,
- Suchscheinwerfer auf den höchsten Türmen.

Fliegende Autos suchen sich ihre Flughöhe über den Dächern selbst, Fußgänger gehen auf den Straßen.

## Technik

- **three.js 0.170.0** als ES-Modul über eine Importmap von jsDelivr, dazu OrbitControls, `Reflector` für das Wasser (Wellen- und Regenverzerrung, Nebel im Shader), `EffectComposer` mit `UnrealBloomPass`, `OutputPass` und einem eigenen Pass für Farbsaum, Vignette, Körnung, Scanlines und Glitch.
- **GSAP 3.12.5** für den Kameraflug beim Start, die Übergänge zwischen Stimmungen und das Drehen um 45°.
- **Tone.js 14.8.49** für Synth-Pad, Bass und Regenrauschen. Jede Etage spielt beim Bauen einen höheren Ton der Pentatonik.
- **Rendering**: Jede Bauteilart ist ein `InstancedMesh`-„Eimer“ mit einem Draw-Call, insgesamt 46 Eimer. Leere Eimer werden nicht gezeichnet. Nach jeder Änderung wird die ganze Stadt aus dem Raster neu aufgebaut, das sind höchstens 20 × 20 × 18 Felder. Ein in `onBeforeCompile` eingesetzter Vertex-Shader lässt geänderte Felder federnd aufploppen (`aPop`: Drehpunkt und Zeitpunkt je Instanz). Fassaden bekommen Welt-UVs, damit Texturen über verschmolzene Gebäude und runde Ecken durchlaufen. Ein Streulicht-Term färbt Wände in Bodennähe mit Neon ein.
- **Eckformen**: Ein Stockwerk mit geformter Ecke besteht aus vier Viertel-Prismen (eckig, schräg, rund), die je nach Ecke gedreht und skaliert werden.
- **Zufall**: Alles, was zum Bau gehört, kommt aus einem Hash von Feld, Etage und Richtung. Dieselbe Stadt sieht deshalb nach dem Laden genauso aus. `Math.random` steuert nur die Optik, also Partikel, Fensterflackern und Texturen.

### Spielstand

- Wird automatisch in `localStorage` gespeichert, Schlüssel `neonstadt-v1`. Die Effektstufe liegt unter `neonstadt-q`.
- Format `{v:1, app:'neonstadt', n:20, name, cells:[[index, k, h, s, c, a, schilder?, werbetafel?, ecken?], …]}`. Dabei ist `k` die Art (0 Wasser, 1 Straße, 2 Park, 3 Gebäude), `h` die Höhe, `s` der Stil, `c` die Farbe, `a` ein Durchgang im Erdgeschoss und `ecken` die Form der vier Ecken (0 eckig, 1 schräg, 2 rund).
- Der **Stadt-Code** im Menü ist dieses JSON als Base64 mit dem Präfix `NEON1:`. Beim Laden werden alle Felder geprüft und begrenzt.

### Testschnittstelle

`window.NEON` bietet `G`, `rebuild`, `snap`, `load`, `restore`, `pick`, `makePlan`, `rectPlan`, `extrude`, `undo`, `redo`, `setTool`, `generate`, `project`, `setQuality`, `STATS`, `camera` und `controls`.

## Prüfen

```sh
pip install playwright && python3 -m playwright install chromium
python3 tests/pruefung.py            # Screenshots landen im Temp-Ordner
```

Das Skript holt die Bibliotheken per `npm pack` und leitet die CDN-Adressen auf diese Kopien um. Dann prüft es 12 Punkte: Startviertel, 4×4-Fläche, Push/Pull an Dach und Fassade, Abrunden, Undo und Redo, Stadt-Code-Rundreise, Abriss-Rechteck, Tippen am Handy und ob es Seitenfehler gibt.

**Stand 2026-11-25** (Commit mit diesem README):
- **Ausgeführt:** alle 12 Prüfungen grün, in Headless-Chrome mit Software-WebGL (SwiftShader) bei 1400×860 und 390×844.
- **Nicht geprüft:** die Bildrate auf echter Grafikkarte, der Ton (headless startet kein AudioContext) und echtes Safari auf iPhone oder iPad.
- Läuft es zu langsam, schaltet das Spiel nach etwa 6 s unter 24 fps selbst auf „Effekte: Schonend“ (ohne Spiegelung, Schatten und Kantenglättung). Auf Touch-Geräten ist das die Grundeinstellung.

## Herkunft

- Gebaut mit Claude am 2026-11-25.
- Techniken aus [tomkpunkt/gamedev](https://github.com/tomkpunkt/gamedev):
  - [Pointer Events für Maus und Touch](https://github.com/tomkpunkt/gamedev/blob/main/techniken/touch-pointer-eingabe-sandbox/README.md) (Tippen und Ziehen trennen, lange drücken, zwei Finger brechen eine Geste ab)
  - [Undo als Schnappschuss](https://github.com/tomkpunkt/gamedev/blob/main/techniken/sandbox-editor-grundfunktionen/README.md)
  - [Speichern in Claude-Artefakten](https://github.com/tomkpunkt/gamedev/blob/main/techniken/claude-artifact-persistenz/README.md) (`localStorage` mit try/catch, ehrliche Rückmeldung, Code statt Download)
  - [Zufall trennen](https://github.com/tomkpunkt/gamedev/blob/main/techniken/golden-master-umbau-absichern/README.md) (Logik und Optik)
  - [Playwright mit Bibliotheken aus npm](https://github.com/tomkpunkt/gamedev/blob/main/techniken/playwright-canvas-pruefung/README.md)
- Alle Schilder, Werbetafeln und Namen sind frei erfunden. Es stecken keine Inhalte, Namen oder Logos aus Cyberpunk 2077 darin.
