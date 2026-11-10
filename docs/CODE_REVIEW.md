# Code Review Spacegame

Stand: Commit `0cd6ddd` (Branch `ccr-44f99259-lhgtp3`), 10.11.2026

## Umfang und Methode

- Gelesen: `main.py` komplett, alle Daten- und Logikmodule (`gamestate.py`, `science.py`, `actions.py`, `mining.py`, `shop.py`, `travel_rules.py`, `saveslots.py`, `achievements.py`, `config.py`, `materials.py`), `core/` und `ui/` sowie Stichproben aus `tests/`.
- Ausgeführt: `pytest` (705 Tests grün) und `pyflakes`.
- **Nicht** ausgeführt: das Spiel selbst (keine GUI in der Review-Umgebung). Alle Befunde zu `main.py` stammen aus dem Lesen des Codes, nicht aus einem Reproduktionslauf.

## Kurzfassung

Die reinen Logikmodule (`travel_rules.py`, `shop.py`, `saveslots.py`, `achievements.py`) sind sauber, GUI-frei und gut getestet. Die Probleme sitzen fast alle in `main.py`:

1. Auswahl und laufender Vorgang teilen sich in Forschung und Werkstatt dieselbe Variable. Damit lassen sich teure Technologien und Gegenstände zum Preis der billigsten bekommen.
2. Autosave und Beenden schreiben immer in Slot 1, auch wenn Slot 2 oder 3 geladen wurde.
3. Laufende Forschung und laufender Bau werden nicht gespeichert, die Kosten sind aber schon abgezogen.
4. Die 705 Tests importieren `main.py` nie. Sie prüfen Datenmodule, `core/`/`ui/` (vom Spiel ungenutzt) und in den Tests nachgebaute Kopien der Spielklassen.

---

## Hoch

### H1: Forschung: Auswahl während laufender Forschung tauscht das Ergebnis

`sAktuelle_Forschung` ist gleichzeitig „im UI ausgewählt“ und „wird gerade erforscht“.

- `main.py:2467-2469`: Klick auf eine Technologie setzt `sAktuelle_Forschung`, auch wenn `bForschung_aktiv` ist.
- `main.py:2332`: Beim Abschluss wird `GAMESTATE['Forschung'][sAktuelle_Forschung]` auf erforscht gesetzt, also die zuletzt angeklickte Technologie.
- `main.py:2480`: Beim Abbruch werden die Kosten der angeklickten Technologie erstattet.

Folgen:

- „Baumaterial“ (1 Punkt, 3 Zyklen) starten, „Rakete“ anklicken: Rakete ist nach 3 Zyklen für 1 Punkt erforscht, Baumaterial nicht.
- „Baumaterial“ starten, „Rakete“ anklicken, stoppen: 35 Punkte Erstattung für 1 Punkt Einsatz, beliebig wiederholbar.

Erreichbar sind alle Technologien, deren Button sichtbar ist (Voraussetzung erforscht).

### H2: Werkstatt: derselbe Fehler mit `sAktuelles_Bauen`

- `main.py:2541-2543`: Klick auf ein Produkt setzt `sAktuelles_Bauen` auch während eines Baus.
- `main.py:2365`: `beende_bauen(sAktuelles_Bauen)` legt das angeklickte Produkt ins Inventar.
- `main.py:554-587`: `stoppe_bauen()` erstattet die Materialien des angeklickten Produkts.

Folgen:

- 1x Baumaterial starten, „Rakete“ anklicken: nach 2 Zyklen steht eine Rakete auf der Erde.
- Ist die Weltraumstation erforscht, gewinnt derselbe Trick das Spiel ohne 5 Mondlander und 100 Eisenbarren.
- Baumaterial starten, „Rakete“ anklicken, stoppen: +30 Eisenbarren und +20 Werkzeug aus dem Nichts.

**Fix für H1 und H2:** laufenden Vorgang in eigenen Variablen halten (`sLaufende_Forschung`, `sLaufender_Bau`), die nur `erforsche()` bzw. `baue()` setzen. Abschluss, Abbruch und Erstattung lesen nur diese.

### H3: Autosave und Beenden überschreiben immer Slot 1

`dump_gamestate(slot=1)` (`main.py:281`) wird an neun Stellen ohne Argument aufgerufen: Forschungs- und Bauende, Reiseankunft, Sonde, Mission, Mining, Autosave (`main.py:2419`) und Beenden (`main.py:2431`). `lade_spielstand(slot)` (`main.py:2174`) merkt sich den geladenen Slot nicht.

Folge: Wer Slot 2 lädt und weiterspielt, überschreibt beim nächsten Ereignis oder beim Schließen den Spielstand in Slot 1.

**Fix:** aktiven Slot als Zustand führen (beim Laden und beim manuellen Speichern setzen) und als Default in `dump_gamestate()` verwenden.

### H4: Speichern während Forschung oder Bau vernichtet die Einsätze

`erforsche()` zieht die Punkte sofort ab (`main.py:599`), `baue()` die Materialien (`main.py:491-493`). Weder Fortschritt noch Auftrag landen in `dump_gamestate()`. Beim Beenden mitten im Bau der Weltraumstation sind 5 Mondlander, 100 Eisenbarren, 10 Werkzeug und der Bauplan nach dem Neustart weg. Der Kommentar in `main.py:2191` nennt das Verhalten, der Spieler erfährt es nicht.

Ebenfalls nicht gespeichert: Erd-Jobs (kostenlos, daher harmlos) und die Forschungs-Warteschlange.

**Fix:** laufende Forschung und laufenden Bau wie Missionen und Reisen serialisieren, oder vor dem Speichern erstatten.

### H5: Negative Astronautenzahl bei Reisen

Der Spinner `reise_astronauten` ist ein editierbares Feld. Getippte Werte kommen als String an, `main.py:2553-2556` macht daraus per `int()` auch `-3`. `starte_reise()` prüft nur Obergrenzen (`main.py:858-864`):

- `main.py:882`: `Astronauten[von] -= -3` erhöht den Bestand am Start sofort um 3.
- `main.py:924`: Am Ziel werden 3 abgezogen, der Bestand kann negativ werden.

Mit einem Schiff auf dem Mond lassen sich so Mond-Astronauten erzeugen, ohne sie hinzufliegen. `travel_rules.berechne_reisekosten()` klemmt auf 0, die Reise kostet also auch kein Wasser.

**Fix:** `astronauten_anzahl < 0` in `starte_reise()` ablehnen, Spinner zusätzlich `readonly=True`.

---

## Mittel

### M1: Mining bindet keine Astronauten und hat kein Slot-Limit

`starte_mining()` (`main.py:1575-1598`) prüft nur, ob genug Astronauten auf dem Planeten sind. Anders als bei Mondmissionen (`main.py:1515`) werden laufende Expeditionen nicht abgezogen. Mit 2 Astronauten laufen beliebig viele Expeditionen parallel, jede für 1 Werkzeug (12 Credits Verkaufswert) gegen 4 Mondgestein und 1 Seltene Mineralien (250 Credits Verkaufswert).

`MINING_SLOTS = 6` begrenzt nur die Anzeige. Die siebte Expedition läuft unsichtbar und lässt sich nicht abbrechen.

### M2: Gebundene Astronauten können abreisen

`starte_reise()` (`main.py:858`) vergleicht mit dem Gesamtbestand des Planeten. Astronauten in laufenden Missionen können wegfliegen, die Mission läuft trotzdem zu Ende.

### M3: Bau-Warteschlange ist nicht erreichbar

`bauauftrag_hinzufuegen()` (`main.py:466`) wird nirgends aufgerufen. Anzeige und „Nächsten Bauauftrag stornieren“ (`main.py:1851-1853`) sind sichtbar, bleiben aber immer leer. Würde die Queue befüllt, läse `baue()` die Stückzahl aus dem aktuellen Spinner-Wert, nicht aus dem Auftrag.

### M4: Shop zeigt andere Schiffsdaten als das Spiel benutzt

| Rakete | `shop.py` (Anzeige) | `science.py` (Spiellogik) |
|---|---|---|
| Frachtplätze | 10 | 6 |
| Reichweite | 5 | 10 |

`main.py:1955-1962` baut die Shop-Beschreibung aus `SHOP`, `get_raumschiff_kapazitaet()` (`main.py:810-818`) liest `SCIENCE`. Der Käufer sieht 10 Frachtplätze und bekommt 6.

### M5: Tests decken `main.py` nicht ab

Kein Test importiert `main.py`, weil das Modul beim Import Spielstand lädt, Fenster öffnet und die Hauptschleife startet. Stattdessen:

- `tests/test_reise.py` testet eine `MockReise`, `tests/test_earth_jobs.py` eine Kopie von `ERDE_JOBS` und `MockErdArbeit`. Diese Tests bleiben grün, egal was in `main.py` passiert.
- `tests/test_core_gamestate.py`, `test_research.py`, `test_building.py`, `test_ui_events.py` testen `core/` und `ui/`, die das Spiel nicht benutzt.

H1 bis H5 und M1 liegen alle in ungetestetem Code. Ein erster Schritt mit wenig Umbau: Spiellogik ohne `window`-Zugriffe in ein Modul ziehen und die Hauptschleife hinter `if __name__ == '__main__':` legen.

### M6: Drei Quellen für den Startzustand

- `gamestate.GAMESTATE`: vom Spiel benutzt.
- `core.game_state.DEFAULT_STATE`: veraltet. Es fehlen die Rezepte für Treibstoff und Mondbasen Bauplan, das Inventarfeld Treibstoff und acht Top-Level-Schlüssel (`Statistik`, `Erfolge`, `AktiveReisen` usw.).
- `config.START_*` (`config.py:27-32`): unbenutzt.

`core/` und `ui/` sind zusammen rund 1.800 Zeilen, die nur von Tests importiert werden (steht auch in `todos.md`). Entweder migrieren oder löschen. Im jetzigen Zustand laufen sie weiter auseinander.

### M7: Statische Spieldaten liegen im Spielstand

`Werkstatt` (Rezepte, Dauer, Beschreibung) und `Planeten.Entfernung` werden mitgespeichert. `merge_defaults()` (`main.py:234-241`) ergänzt nur fehlende Schlüssel. Geänderte Mengen, Dauern oder entfernte Zutaten erreichen alte Spielstände nie. Rezepte gehören in ein Datenmodul wie `science.py`, der Spielstand sollte nur veränderliche Werte enthalten.

Umgekehrt wird `ACTIONS[...]['erforscht']` zur Laufzeit in den Moduldaten mutiert (`main.py:1550`, `2223`) und parallel in `GAMESTATE['Mondmissionen']` geführt.

### M8: Beschädigter Spielstand wird stillschweigend überschrieben

`saveslots.lade_slot()` liefert bei kaputtem JSON `None`, `load_gamestate()` startet dann ein neues Spiel, und der Tutorial-Dump (`main.py:2312`) überschreibt die Datei sofort. `speichere_slot()` (`saveslots.py:121-126`) schreibt direkt in die Zieldatei. Ein Absturz während des Schreibens erzeugt genau diesen Fall.

**Fix:** in temporäre Datei schreiben und `os.replace()`. Beschädigte Datei vor dem Überschreiben umbenennen.

### M9: `savefile.json` ist eingecheckt

Der persönliche Spielstand (Zyklus 530) liegt im Repo und fehlt in `.gitignore`. Jedes Spielen erzeugt ein geändertes Arbeitsverzeichnis, ein frischer Clone startet nicht bei null. `savefile*.json` ignorieren und die Datei aus dem Index nehmen.

---

## Niedrig

- **`zeige_Forschung()` bricht zu früh ab** (`main.py:335-337`): Bei zu wenig Punkten kommt das `return` vor der „bereits erforscht“-Anzeige. Eine erforschte Technologie zeigt dann „Forschungspunkte reichen nicht aus“, und der Queue-Button behält den Zustand der vorherigen Auswahl.
- **Latenter `KeyError`** (`main.py:1805`): `GAMESTATE['Forschung'][data['erforschbar nach']]` funktioniert nur, weil genau Eisenbarren keine Voraussetzung hat. Eine zweite Wurzel-Technologie lässt das Spiel beim Start abstürzen. Der zweite Teil des Ausdrucks (`main.py:1806`) macht dasselbe sicher und reicht allein.
- **Unerreichbarer Code:** Entdeckung per Reise (`main.py:953-961`). `kann_reisen()` verlangt, dass das Ziel schon entdeckt ist.
- **Fracht ohne Funktion:** Es gibt ein globales Inventar. Fracht wird beim Start abgezogen und bei Ankunft wieder gutgeschrieben, belegt nur Frachtplätze und kann durch „Frachtverlust“ schrumpfen. Mitnehmen lohnt sich nie.
- **Reisefortschritt nach Verzögerung:** `Reise.fortschritt()` (`main.py:790-794`) rechnet mit der ursprünglichen `dauer`. Nach einem Verzögerungsereignis steht die Anzeige auf 100 %, bevor das Schiff ankommt.
- **Unbenutzter Code:** `get_materials_from_inventory()`, `get_amounts_from_inventory()` (`main.py:611-623`), `get_verfuegbare_raumschiffe()` (`main.py:800`), `inventory` (`main.py:2286`), `Reise.reise_id`, `shipnames.py`, `data/`, die Events `'HQ'`, `'Forschung'` usw. (`main.py:2455-2465`).
- **Unbenutzte Konfiguration:** `START_*`, `DEFAULT_*`, `WINDOW_READ`, `IMAGE_SUBSAMPLE`, `PROGRESS_BAR_SIZE` in `config.py`. `WINDOW_READ_TIMEOUT` existiert, `main.py:2316` nutzt die feste Zahl 100. `MOON_DISCOVERY_RESEARCH_POINTS` kommt aus der Konfiguration, die 15 Punkte für spätere Sondenflüge stehen fest in `main.py:1162`.
- **Docstrings an falscher Stelle:** In rund 25 Funktionen steht `logger.debug(...)` vor dem Docstring (z. B. `main.py:390-391`). Der String ist dann ein wirkungsloser Ausdruck, `help()` und IDE zeigen nichts.
- **Fest verdrahtete Kostenangaben:** „Kosten: 1 Werkzeug“ (`main.py:1668`, `1675`) statt aus `MINING_EXPEDITIONEN`. Die Zuordnung `benötigt_x` zu Inventarname per `.title()` (`main.py:1522` u. a.) funktioniert nur, solange Schlüssel und Materialname zufällig zusammenpassen.
- **Breite `except`-Blöcke um UI-Updates** (`except KeyError: pass`, `except Exception: pass`, z. B. `main.py:1104`, `1178`): verdecken Tippfehler in Element-Keys.
- **Unnötige Arbeit pro Tick:** `main.py:2366-2370` setzt während jedes Bau-Ticks alle Werkstatt-Buttons neu und ruft `window.refresh()` auf. `kaufe_shop_artikel()` und `verkaufe_material()` schreiben `tCredits` direkt (`main.py:2010`, `2079`) in anderem Format als die Statusleiste, die es danach korrigiert.
- **pyflakes:** sechs überflüssige `global`-Deklarationen, zwei f-Strings ohne Platzhalter in `main.py`, unbenutzte Importe in `ui/controller.py` und `ui/handlers.py`.
- **Stil:** Einrückung wechselt zwischen 2 und 4 Leerzeichen, Namensschema zwischen ungarisch (`iTicks`, `bBauen_aktiv`, `lLog`) und snake_case, Kommentare zwischen Deutsch und Englisch. Reste wie `# NEW`, `# NEW ENDE`, `# Ersetze das alte ...` beschreiben frühere Änderungen statt den Code.
- **Kein README:** Start (`python main.py`) und Voraussetzungen stehen nur als Kommentar in `requirements.txt`.

---

## Balance (keine Fehler, zur Kenntnis)

- Passives Einkommen: 1 Credit pro 20 Zyklen (40 Sekunden). Eine Raumsonde kostet Rohstoffe für 65 Credits im Shop (10 Roheisen, 5 Wasser) und verkauft sich für 200. Der Handel über die Werkstatt ersetzt jede andere Einnahmequelle.
- Mondmissionen sind einmalig, Mining unbegrenzt (siehe M1).

---

## Empfohlene Reihenfolge

1. H1 und H2 (eine gemeinsame Ursache, kleiner Fix).
2. H3 (aktiven Slot merken).
3. H5 und M1 (je eine fehlende Prüfung).
4. H4 (laufende Forschung und Bau speichern).
5. M9, M4, M3 (Aufräumen mit sichtbarem Effekt).
6. M5 bis M7 (Logik aus `main.py` lösen, `core/` und `ui/` entweder nutzen oder entfernen). Das ist die Voraussetzung, damit Tests Fehler wie H1 bis H5 künftig finden.
