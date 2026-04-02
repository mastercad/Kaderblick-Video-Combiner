# Kaderblick Qt Theme wiederverwenden

Dieses Projekt enthaelt ein zentrales, wiederverwendbares Qt-Theme in `shared/kaderblick_qt_theme.py`.

Das Ziel ist, das Corporate Design nicht pro Projekt neu zu bauen, sondern in beliebigen GUI-Projekten mit wenig Code zu aktivieren.

## Unterstuetzte Qt-Bindings

- PyQt5
- PyQt6
- PySide6

## Enthaltene Bausteine

- `apply_application_theme(app)`
  Aktiviert Palette, Fusion-Style und das globale Stylesheet fuer die komplette Anwendung.
- `BrandWordmarkWidget(...)`
  Der eigentliche KADERBLICK-Schriftzug mit gruener `K`-Marke.
- `BrandHeaderWidget(...)`
  Das zentrale Banner fuer KADERBLICK-Anwendungen.
  Hintergrund, Typografie, Abstaende und Interaktionsstil kommen direkt aus dem Theme.

## Aktueller Ansatz

Das Branding wird zentral ueber das Theme bereitgestellt.

Die App bindet das Banner ueber `BrandHeaderWidget(...)` ein.

Damit liegt das Erscheinungsbild nicht mehr verteilt in einzelnen GUI-Dateien, sondern im Theme-Modul.

`BrandWordmarkWidget(...)` bleibt der kleinere Baustein fuer den reinen Schriftzug, falls du ihn separat brauchst.

## Wie ist `BrandHeaderWidget` jetzt zentral gelöst?

`BrandHeaderWidget` bekommt seinen Stil jetzt direkt aus dem globalen Theme.

Es gibt zwei zentrale Varianten:

1. `tone="brand"`
  gruener Header im Kaderblick-Look
2. `tone="surface"`
  helle Kartenvariante mit Rahmen

Der Standard ist `tone="brand"`. Dadurch ist der Header auch in anderen Projekten nicht mehr transparent.

## Empfohlene Verwendung in anderen Projekten

1. Datei `shared/kaderblick_qt_theme.py` in das Zielprojekt uebernehmen.
2. Optional auch `shared/__init__.py` uebernehmen.
3. Beim Start der Qt-App das Theme einmal zentral anwenden.
4. Fuer das KADERBLICK-Banner `BrandHeaderWidget` verwenden.

### Beispiel mit PyQt5 und zentralem Banner

```python
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from shared.kaderblick_qt_theme import BrandHeaderWidget, apply_application_theme


app = QApplication(sys.argv)
apply_application_theme(app)

window = QMainWindow()

central = QWidget()
layout = QVBoxLayout(central)

header = BrandHeaderWidget(subtitle="Mein weiteres Tool", tone="brand")
layout.addWidget(header)

window.setCentralWidget(central)

window.show()
sys.exit(app.exec_())
```

## Varianten

### Beispiel mit gruener Header-Variante

```python
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from shared.kaderblick_qt_theme import BrandHeaderWidget, apply_application_theme


app = QApplication(sys.argv)
apply_application_theme(app)

window = QMainWindow()
central = QWidget()
layout = QVBoxLayout(central)

header = BrandHeaderWidget(subtitle="Mein weiteres Tool", tone="brand")
layout.addWidget(header)
window.setCentralWidget(central)
window.show()

sys.exit(app.exec_())
```

### Beispiel mit heller Header-Variante

```python
header = BrandHeaderWidget(subtitle="Mein weiteres Tool", tone="surface")
```

## Banner und Aktionen

Wenn dein Projekt das Banner nicht nur anzeigen, sondern auch direkt als Aktionsleiste verwenden soll, wird das ebenfalls zentral ueber `BrandHeaderWidget` erweitert.

Typische Erweiterungen:

- Aktionen als Banner-Buttons
- Separatoren zwischen Aktionsgruppen
- gruene Primäraktion im Banner

Diese Logik soll im Theme-Baustein bleiben und nicht erneut lokal in einzelnen Fenstern nachgebaut werden.

## Architektur-Hinweis

Das Theme ist absichtlich nicht an `src.gui` gekoppelt. Dadurch kann das Modul direkt in anderen Projekten importiert oder als Basis fuer ein spaeteres eigenes Paket verwendet werden.

Wenn du das spaeter komplett zentralisieren willst, ist der naechste logische Schritt ein eigenes Repository oder ein kleines internes Python-Paket wie `kaderblick-qt-theme`.
