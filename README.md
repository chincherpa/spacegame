# Spacegame

Aufbauspiel in Echtzeit: Von den ersten Arbeitern auf der Erde über Mond und
Mars bis zur eigenen Weltraumstation.

## Start

```
pip install -r requirements.txt
python main.py
```

FreeSimpleGUI braucht tkinter. Unter Debian/Ubuntu: `sudo apt-get install python3-tk`.

## Spielablauf

1. **Arbeit**: Arbeiter liefern Rohstoffe und Forschungspunkte.
2. **Forschung**: Technologien schalten Rezepte in der Werkstatt frei.
3. **Werkstatt**: Vom Eisenbarren bis zur Rakete. Aufträge lassen sich einreihen.
4. **Raumsonde**: Im HQ gestartet entdeckt sie erst den Mond, dann den Mars.
5. **Reisen**: Raumschiffe bringen Astronauten und Fracht zu den Planeten.
   Fracht landet im Lager des Ziels und versorgt dort Missionen, Mining und
   den Rückflug (Treibstoff, Wasser).
6. **Mondmissionen und Mining**: bringen Credits, Mondgestein und dauerhafte Upgrades.
   Abgebaute Güter liegen im Lager vor Ort und müssen zur Erde geflogen werden.
7. **Mars**: Nur dort gibt es das Gold für die Weltraumstation.
8. **Weltraumstation** bauen: gewonnen.

Alle paar Sekunden vergeht ein Zyklus. Die Anzeige "Nächstes Ziel" im HQ führt
durch das Spiel, F1 zeigt die Hilfe zum aktuellen Tab.

## Speichern

Drei Slots über das Menü "File". Autosave und Beenden schreiben in den aktiven
Slot, also den zuletzt geladenen oder gespeicherten; mit ihm startet das Spiel
auch beim nächsten Mal. Laufende Forschung,
Bauaufträge, Reisen und Missionen werden mitgespeichert. Strg+S speichert sofort.

## Aufbau

| Datei | Inhalt |
|---|---|
| `main.py` | Fenster, Spielzustand, Tick- und Event-Verarbeitung |
| `gamestate.py` | Startzustand und Werkstatt-Rezepte |
| `science.py`, `actions.py`, `mining.py`, `shop.py`, `materials.py` | Spieldaten |
| `travel_rules.py` | Reisekosten und Zufallsereignisse |
| `saveslots.py` | Speicherslots |
| `achievements.py`, `tutorial.py` | Erfolge, Ziele und Hilfetexte |
| `config.py` | Stellschrauben (Tempo, Einkommen, Boni) |

## Tests

```
python -m pytest
```

Die Tests brauchen kein Fenster: `tests/fake_sg.py` ersetzt FreeSimpleGUI.
`tests/test_durchspielen.py` spielt das Spiel mit einem Bot bis zum Sieg durch.
