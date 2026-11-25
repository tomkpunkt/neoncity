# Neonstadt

Ein ruhiges Aufbauspiel im Browser: Du baust eine Neon-Megastadt auf nassem, spiegelndem Wasser. Es gibt kein Geld, keine Ziele und keinen Druck, nur Bauen, Formen und Zuschauen. Vorbilder sind [Townscaper](https://store.steampowered.com/app/1291340/Townscaper/), [Altstadt](https://store.steampowered.com/app/5123730/Altstadt/) und [Miniopolis](https://store.steampowered.com/app/3814960/miniopolis/).

![Neonstadt: Startviertel bei Nacht und Regen, mit Tilt-Shift](docs/vorschau.jpg)

## Spielen

Die Seite besteht aus einer einzigen Datei, `index.html`. Die Bibliotheken kommen vom CDN, darum braucht sie beim Laden Internet.

```sh
python3 -m http.server 8000   # dann http://localhost:8000 öffnen
```

Das Spiel läuft auch als Claude-Artefakt. Über GitHub Pages lässt es sich direkt aus dem Hauptordner ausliefern.

## Steuerung

| | Maus und Tastatur | Touch |
|---|---|---|
| Werkzeug anwenden | Linksklick | Tippen |
| Fläche aufziehen, Push/Pull | Linke Taste gedrückt ziehen | Mit einem Finger ziehen |
| Geklickte Etage abreißen | Rechtsklick | Lange drücken |
| Drehen | Rechte Taste ziehen oder `Q` / `E` halten | Zwei Finger |
| Zoomen | Mausrad oder `+` / `−` halten | Zwei Finger auseinander |
| Schieben | `WASD` oder Pfeiltasten halten (mit `Shift` schneller), mittlere Maustaste | – |

Die Kamera gleitet beim Halten der Tasten weich los und rollt nach dem Loslassen aus.

Weitere Tasten: `1`–`8` Werkzeuge, `Strg+Z` / `Strg+Y` Rückgängig und Wiederholen, `T` Tilt-Shift, `N` Stimmung, `R` Regen, `M` Ton, `Leertaste` Rundflug, `P` Fotomodus, `Esc` abbrechen.

## Werkzeuge

- **Bauen**: Ein Klick aufs Wasser oder aufs Dach setzt einen Block, ein Klick auf eine Unterseite setzt ihn darunter. Klickst du an eine Wand, landet der Block im Nachbarfeld auf genau dieser Höhe; steht dort nichts darunter, ragt er frei aus (**Überhang**). Mit Ziehen entsteht ein Rechteck auf der Höhe, an der du ansetzt, zum Beispiel ein 4×4-Block auf dem Wasser oder eine Platte, die von einer Fassade aus über die Straße ragt.
- **Formen** (Push/Pull wie in Miniopolis): Du greifst ein Dach, eine Unterseite oder eine Fassade und ziehst. Dächer gehen hoch oder runter, Unterseiten wachsen nach unten oder werden hochgeschoben, Fassaden schiebst du Felder weit raus oder rein. Die betroffene Fläche leuchtet beim Zeigen auf und wandert beim Ziehen mit.
- **Kanten**: Außenecken werden **eckig**, **schräg**, **rund** (nach außen gewölbt) oder **hohl** (nach innen gezogen). **Innenecken** von L- oder U-förmigen Gebäuden werden schräg oder rund ausgefüllt. Ein Klick auf die Dachmitte ändert das ganze Gebäude, Ziehen eine ganze Fläche.
- **Straße**: Wahlweise Straße oder Platz. Zwei Straßenfelder nebeneinander werden eine **breite Straße** mit doppelter Mittellinie, gestrichelten Fahrstreifen und Zebrastreifen an Kreuzungen. Auf einem Gebäude wird das Erdgeschoss zum Durchgang mit Neon-Bogen.
- **Park**: Leuchtbäume und Glühwürmchen.
- **Neon**: Ein Klick auf eine Fassade setzt ein Leuchtschild, ein Klick aufs Dach schaltet die Werbetafel an oder aus.
- **Gestalten**: Färbt das ganze Gebäude um oder wechselt den Stil, je nach Auswahl im Dock.
- **Abriss**: Ein Klick nimmt genau die geklickte Etage weg, auch aus der Mitte eines Turms; so entstehen Löcher und Überhänge. Mit Ziehen wird alles im Rechteck ab dieser Höhe abgeschnitten.

Farben und Stile (Konzern, Megablock, Container, Pagode) wählst du im Dock. Bei „Zufall“ übernehmen Anbauten den Stil des Gebäudes, an das du baust.

## Was sich von selbst ergibt

Nachbarn gleicher Farbe und gleichen Stils verschmelzen zu einem Gebäude. Je nach Lage entstehen dann:
- Läden mit Markise an Straßen, Plätzen und Parks,
- Leuchtschilder, große Hochformat-Werbung an hohen Fassaden, Klimageräte, Balkone, Vordächer mit Lampions,
- auf den Dächern Wassertanks, Antennen mit Blinklicht, Helipads und Werbetafeln,
- Licht unter Überhängen; frei schwebende Teile bekommen Stützen bis zum Boden oder ins Wasser,
- Glas-Skywalks zwischen Türmen und Lampionketten zwischen Containern,
- Suchscheinwerfer auf den höchsten Türmen.

Das Startviertel hat zweispurige Hauptachsen mit Brückenhäusern darüber, Nebenstraßen mit Durchgängen, einen Platz mit Hologramm und Gebäude, die übers Wasser auskragen. Autos fahren auf den Straßen (Rechtsverkehr), fliegende Autos suchen sich ihre Höhe über den Dächern, Fußgänger gehen auf Straßen und Plätzen.

## Technik

- **three.js 0.170.0** als ES-Modul über eine Importmap von jsDelivr, dazu OrbitControls, `Reflector` für das Wasser (Wellen- und Regenverzerrung, Nebel im Shader; Regen und Vorschau werden nicht gespiegelt), `EffectComposer` mit `UnrealBloomPass`, `OutputPass`, zwei Tilt-Shift-Pässen und einem eigenen Pass für Farbsaum, Sättigung, Vignette, Körnung, Scanlines und Glitch.
- **Tilt-Shift**: Ein 9-Tap-Weichzeichner, getrennt nach waagerecht und senkrecht. Er beginnt erst außerhalb eines scharfen Bandes, und dieses Band folgt dem Blickpunkt der Kamera. Dazu kommt etwas mehr Sättigung für den Miniatur-Look.
- **GSAP 3.12.5** für den Kameraflug beim Start und die Übergänge zwischen Stimmungen (`lagSmoothing(0)`, damit langsame Geräte nicht hängen bleiben).
- **Tone.js 14.8.49** für Synth-Pad, Bass und Regenrauschen. Jede Etage spielt beim Bauen einen höheren Ton der Pentatonik.
- **Stadtmodell**: Jedes Feld hat eine Bodenart `g` und eine Etagen-Maske `m`, in der Bit `k` für Etage `k` steht. Damit sind Überhänge, Löcher, Durchgänge und Brücken dasselbe: Etagen, unter denen nichts liegt.
- **Rendering**: Jede Bauteilart ist ein `InstancedMesh`-„Eimer“ mit einem Draw-Call, insgesamt 61 Eimer. Leere Eimer werden nicht gezeichnet. Nach jeder Änderung wird die ganze Stadt aus dem Raster neu aufgebaut, das sind höchstens 20 × 20 × 18 Felder. Ein in `onBeforeCompile` eingesetzter Vertex-Shader lässt geänderte Etagen federnd aufploppen: Drehpunkt und Zeitpunkt je Instanz, und nur ab der geänderten Etage. Fassaden bekommen Welt-UVs, damit Texturen über verschmolzene Gebäude und runde Ecken durchlaufen. Ein Streulicht-Term färbt Wände in Bodennähe mit Neon ein.
- **Eckformen**: Ein Stockwerk mit geformter Ecke besteht aus vier Viertel-Prismen (eckig, schräg, rund, hohl), die je nach Ecke gedreht und skaliert werden. Innenecken bekommen ein Füllstück im leeren Diagonalfeld (Dreieck oder Viertelkreis-Hohlkehle). Die Fenster der angrenzenden Wände werden passend gekürzt.
- **Straßen**: Jedes Straßenfeld wird eingeordnet als gerade (x oder z), Kreuzung oder Ende/Kurve. Zwei gerade Felder gleicher Richtung nebeneinander ergeben eine breite Straße. Liegt in Fahrtrichtung eine Kreuzung oder ein Platz, kommt ein Zebrastreifen dazu.
- **Zufall**: Alles, was zum Bau gehört, kommt aus einem Hash von Feld, Etage und Richtung. Dieselbe Stadt sieht deshalb nach dem Laden genauso aus. `Math.random` steuert nur die Optik, also Partikel, Fensterflackern, Verkehr und Texturen.

### Spielstand

- Wird automatisch in `localStorage` gespeichert, Schlüssel `neonstadt-v2`. Ein alter Stand unter `neonstadt-v1` wird beim ersten Start gelesen und umgebaut. Effektstufe und Tilt-Shift liegen unter `neonstadt-q` und `neonstadt-tilt`.
- Format 2: `{v:2, app:'neonstadt', n:20, name, cells:[[index, g, m, s, c, schilder?, werbetafel?, ecken?], …]}`. Dabei ist `g` die Bodenart (0 Wasser, 1 Straße, 2 Park, 3 Platz) und `m` die Etagen-Maske. `s` ist der Stil, `c` die Farbe, `schilder` eine Liste von `[Richtung, Etage, Motiv]` und `ecken` die Form der vier Ecken (0 eckig, 1 schräg, 2 rund, 3 hohl).
- Format 1 (`[index, k, h, s, c, a, …]` mit Höhe `h` und Durchgang `a`) wird beim Laden in eine Maske umgerechnet.
- Der **Stadt-Code** im Menü ist das JSON als Base64 mit dem Präfix `NEON2:`. Codes mit `NEON1:` und reines JSON werden ebenfalls angenommen. Beim Laden werden alle Felder geprüft und begrenzt.

### Testschnittstelle

`window.NEON` bietet `G`, `rebuild`, `snap`, `load`, `restore`, `pick`, `makePlan`, `rectPlan`, `extrude`, `pullApply`, `regionOf`, `topRegion`, `botRegion`, `sideRegion`, `undo`, `redo`, `setTool`, `generate`, `project`, `setQuality`, `setTilt`, `tiltOn`, `killIntro`, `topOf`, `rng`, `segOf`, `hl`, `gcars`, `STATS`, `B`, `camera` und `controls`.

## Prüfen

```sh
pip install playwright && python3 -m playwright install chromium
python3 tests/pruefung.py            # Screenshots landen im Temp-Ordner
```

Das Skript holt die Bibliotheken per `npm pack` und leitet die CDN-Adressen auf diese Kopien um. Dann prüft es 20 Punkte:
- Startviertel und Autos auf den Straßen,
- 4×4-Fläche als ein Gebäude,
- Push/Pull an Dach und Fassade samt leuchtender Fläche,
- Abrunden und Undo/Redo,
- Stadt-Code-Rundreise und Umbau von Format 1,
- Überhang per Seitenklick, Etage aus der Mitte abreißen,
- gefüllte Innenecke und Hohlkehle,
- Abriss-Rechteck,
- weiches Gleiten mit der Tastatur, Tilt-Shift-Schalter,
- Tippen am Handy,
- keine Seitenfehler.

**Stand 2026-11-25** (Commit mit diesem README):
- **Ausgeführt:** alle 20 Prüfungen grün, in Headless-Chrome mit Software-WebGL (SwiftShader) bei 1400×860 und 390×844.
- **Nicht geprüft:** die Bildrate auf echter Grafikkarte, der Ton (headless startet kein AudioContext) und echtes Safari auf iPhone oder iPad.
- Läuft es zu langsam, schaltet das Spiel nach etwa 6 s unter 24 fps selbst auf „Effekte: Schonend“ (ohne Spiegelung, Schatten und Kantenglättung). Auf Touch-Geräten ist das die Grundeinstellung. Tilt-Shift lässt sich mit `T` oder im Menü ausschalten.

## Herkunft

- Gebaut mit Claude am 2026-11-25.
- Techniken aus [tomkpunkt/gamedev](https://github.com/tomkpunkt/gamedev):
  - [Pointer Events für Maus und Touch](https://github.com/tomkpunkt/gamedev/blob/main/techniken/touch-pointer-eingabe-sandbox/README.md) (Tippen und Ziehen trennen, lange drücken, zwei Finger brechen eine Geste ab)
  - [Undo als Schnappschuss](https://github.com/tomkpunkt/gamedev/blob/main/techniken/sandbox-editor-grundfunktionen/README.md)
  - [Speichern in Claude-Artefakten](https://github.com/tomkpunkt/gamedev/blob/main/techniken/claude-artifact-persistenz/README.md) (`localStorage` mit try/catch, ehrliche Rückmeldung, Code statt Download)
  - [Spielstände mit Migration](https://github.com/tomkpunkt/gamedev/blob/main/techniken/spielzustand-schreibgrenze-spielstaende/README.md) (Format 1 wird weiter gelesen)
  - [Zufall trennen](https://github.com/tomkpunkt/gamedev/blob/main/techniken/golden-master-umbau-absichern/README.md) (Logik und Optik)
  - [Playwright mit Bibliotheken aus npm](https://github.com/tomkpunkt/gamedev/blob/main/techniken/playwright-canvas-pruefung/README.md)
- Alle Schilder, Werbetafeln und Namen sind frei erfunden. Es stecken keine Inhalte, Namen oder Logos aus Cyberpunk 2077 darin.
