import json
import time

import FreeSimpleGUI as sg

import config
from actions import ACTIONS
from materials import MATERIALS
from science import SCIENCE

sg.theme('Dark Teal 6')
# sg.main_global_pysimplegui_settings()

# # PERPLEXITY
# Im aktuellen Zustand des Spiels „Spacegame“ sind bereits viele Elemente und Spielmechaniken implementiert, aber der Code (insbesondere in main.py) sowie zahlreiche TODO-Kommentare und Codestellen zeigen, dass wichtige Feature-Bereiche noch nicht fertig entwickelt sind. Im Folgenden findest du eine Analyse der noch unfertigen Features sowie Hinweise, wie diese sinnvoll vollendet werden können:

# 1. Bau-System
# Status: Teilweise implementiert, Hinweise auf Bugs/Funktionslücken.
# Probleme:
# Im Code steht:
# python
# # Das Bau-System reparieren und vervollständigen?
# Es gibt Funktionen zum Starten/Beenden von Bauprozessen (baue(), beende_bauen()), aber Anpassungen für „Weltraumstation“/„Mondbasis“ sind nicht fertig bzw. im UI ist dies wohl noch fehlerhaft.
# Bau-Button-Logik ist nicht “idiotensicher” und es fehlt ggf. eine Queue für mehrere Bauaufträge.
# Lösungsvorschlag:
# Baue ein echtes Bauauftrags-Queue-System, damit mehrere Bauaufträge nacheinander abgearbeitet werden können.
# Stelle sicher, dass Fehlerbehandlung greift (z.B. Rückgabe von Materialien, wenn Bau abgebrochen wird).
# Füge optionale Bau-Abbruch/Abschluss-Benachrichtigungen ein, die auch ins Log geschrieben werden.
# Synchronisiere Baufortschritte mit UI/Progress-Bar und dem Inventar.

# 2. Reisen zwischen Planeten
# Status: Intern größtenteils vorbereitet (es existieren z.B. die Reise-Klasse, Methoden wie starte_reise()), aber UI-seitig/Tick-Verwaltung scheinbar noch nicht voll integriert.
# Probleme:
# Im UI fehlen ggf. Fortschrittsanzeigen und vollständige Übersicht laufender/beendeter Reisen.
# Tick-Logik für Reisen und die automatische Abwicklung bei Abschluss (Ressourcen verschieben, Astronauten umlagern etc.) könnte noch Fehler enthalten.
# Handle Ereignisse während der Reise (z.B. Pannen, zufällige Events) werden nur als TODO geführt.
# Lösungsvorschlag:
# Implementiere ein periodisches Event-Update pro Tick im Spiel-Loop, das alle aktiven Reisen auf Fortschritt prüft, die Reisen ggf. abschließt, und passende Logeinträge erzeugt.
# Entwickle ein UI-Panel, das alle Reisen inkl. Fortschrittsbalken und Details (Astronauten, Schiffe, Fracht) zeigt.
# Führe ein Zufallsevent-System ein, das je nach Reiseart/Entfernung Risiken oder Boni (Erfahrung, Ressourcenverlust etc.) generiert.

# 3. Forschungssystem
# Status: Die grundlegenden Mechaniken scheinen vorhanden, aber der Forschungsbaum mit Abhängigkeiten und Freischaltbedingungen ist lückenhaft verknüpft.
# Probleme:
# Forschungsabfolgen und Voraussetzungen werden in den Datenstrukturen begonnen, aber die Funktionalität „erforschbar nach“ wird nur rudimentär abgefragt.
# Es gibt Buttons zum Starten/Stoppen von Forschungen, aber kein echtes Queue-System oder Hilfestellung im UI zu Folgeforschungen.
# Lösungsvorschlag:
# Entwickle einen klaren Forschungsbaum mit Vorbedingungen: Ein Forschungsbutton wird nur aktiviert, wenn alle Voraussetzungen erforscht wurden.
# Zeige im UI eine visuelle Verbindung/Liste der möglichen nächsten Forschungen.
# Baue eine Option, um eine „Forschungsliste“ (Queue) abzuarbeiten.

# 4. Inventar-/Ressourcenmanagement & Werkstatt
# Status: Die Anzeige ist dynamisch, aber Erweiterungen sind noch offen (dynamische Materialbeschreibungen, neue Ressourcen, Produktionsketten).
# Probleme:
# Im UI können neue/gefundene Materialien nicht immer sofort angezeigt werden.
# Produktion neuer Materialien und Upgrade-Prozesse (z.B. Baumaterial aus diversen Grundstoffen) fehlen oder sind nicht nahtlos integriert.
# Lösungsvorschlag:
# Baue eine vollwertige dynamische Inventar-Anzeige, die neue Materialeinträge automatisch ergänzt.
# Erweitere die Werkstatt um Rezept-Abfragen – Produktionsketten, die auf Freischaltungen und Ressourcen geprüft werden.
# Entwickle einen Ressourcenabbau- und Verarbeitungssimulator (z.B. regelmäßiger automatischer Abbau).

# 5. Mondmissionen
# Status: Grundstruktur liegt an, Missionsstart/-abbruch/-abschluss ist abgebildet, aber das Missionssystem wirkt (Code + UI) noch linear und nicht modular-expandierbar.
# Probleme:
# Kein Missionsfortschritt im Hintergrund (parallel zu anderen Aktionen?).
# Belohnungen/Abhängigkeiten von Missionen sind nicht flexibel (z.B. Kettenmissionen, zufällige Modifikatoren).
# Lösungsvorschlag:
# send: Implementiere ein Missionsmanagement-System, das mehrere Missionen verwalten und parallel laufen lassen kann.
# Entwickle Missionstypen mit zufälligen Subzielen und unterschiedlichen Belohnungs-/Risikoausprägungen.
# Schaffe neue Missionstypen (z.B. zeitliche Anforderungen, Rettungsmissionen).

# 6. UI/UX Verbesserungen
# Status: Viele Funktionen sind sichtbar vorbereitet, aber Modifikationen für Feedback und Bedienkomfort fehlen (Tabs, Statistikausgabe).
# Lösungsvorschlag:
# Entwickle kontext-sensitive Tooltips und Hilfe-Panels.
# Füge fortlaufende Fortschrittsbalken, besser sichtbare Statusanzeigen und Feedback für nicht mögliche Aktionen ein.
# Implementiere eine interaktive Log-/Nachrichtenausgabe mit Filtermöglichkeit.

# 7. Speicher-/Ladesystem
# Status: Initial vorhanden, sollte jedoch erweitert und gründlich getestet werden.
# Lösungsvorschlag:
# Baue Autosave nach jeder wichtigen Änderung.
# Implementiere eine Rückmeldung im UI beim erfolgreichen Speichern oder Wiederherstellen.
# Ermögliche das Anlegen mehrerer Savegames und ein übersichtliches Lade-Menü.

# 8. Tutorial und Hilfesystem
# Status: Nur als Konzept vorhanden.
# Lösungsvorschlag:
# Füge ein Start-Tutorial ein (Modal-Fenster, Erklärtexte zu ersten Schritten).
# Implementiere kontextabhängige Hilfe für unbekannte Buttons/Materialien.

# Zusammengefasst:
# Das Spiel ist solide vorstrukturiert, aber wesentliche Kernfeatures (Auftrags-Queues für Bau/Forschung/Missionen; vollständiger Reisezyklus; Ereignissysteme; ausgereifte UI-Bedienung; Tutorials) sind noch unfertig oder fehleranfällig. Der weitere Ausbau sollte an diesen Punkten ansetzen, jeweils mit Fokus auf Modularität, Fehlerbehandlung, Benutzerführung und der Möglichkeit zur nachträglichen Erweiterung (neue Forschungen, Materialien, Missionstypen etc.).
# Wenn du möchtest, kann ich für einen der genannten Punkte Beispiel-Code zeigen und Stand/ToDo detailliert erläutern. Sag einfach, welche Baustelle dich interessiert!

# Todo
#   Das Bau-System reparieren und vervollständigen?
#   Reisen zwischen Planeten implementieren?
#   Die Mondmissionen aus actions.py integrieren?
# Das Interface verbessern?
# Ressourcenabbau-System hinzufügen?
#   die dynamische Inventar-Anzeige implementiere

## Mondmissionen
# Missionssystem mit verschiedenen Zielen (z.B. Proben sammeln, Module bauen, Forschung betreiben).
# Fortschrittsanzeige und Belohnungen (z.B. Forschungspunkte, seltene Materialien).
# Risiko- und Ereignissystem (z.B. Astronauten können Erfahrung sammeln oder verlieren).

## Reisen zwischen Planeten
# Auswahl von Raumschiff, Start- und Zielplanet, Astronauten und Fracht.
# Reisezeit und Fortschrittsanzeige.
# Ereignisse während der Reise (z.B. Pannen, Entdeckungen).
# Ressourcenverbrauch (Treibstoff, Lebenserhaltung).

## Forschungssystem
# Forschungsbaum mit Abhängigkeiten.
# Forschungspunkte als Ressource.
# Freischalten neuer Technologien und Baupläne.

## Bau-System
# Bau von Raumschiffen, Stationen und Modulen.
# Materialverbrauch und Bauzeit.
# Fortschrittsanzeige und Abbruchmöglichkeit.

## Inventar- und Ressourcenmanagement
# Dynamische Anzeige des Inventars.
# Sammeln, Lagern und Verarbeiten von Ressourcen.
# Handelssystem (Shop, Tausch mit NPCs).

## Astronauten-Management
# Zuweisung zu Missionen und Reisen.
# Erfahrung, Gesundheit und Skills.
# Training und Upgrades.

## Planeten- und Stationsverwaltung
# Ausbau von Basen und Stationen.
# Verwaltung von Modulen und Upgrades.
# Entdeckung neuer Planeten und Ressourcen.

## Ereignisse und Zufallsbegegnungen
# Zufällige Events (Meteoriten, technische Defekte, Entdeckungen).
# Entscheidungen mit Konsequenzen.

## UI/UX Verbesserungen
# Übersichtliche Tabs für alle Bereiche.
# Fortschrittsbalken, Tooltips, Statusanzeigen.

## Speichern/Laden des Spielstands
# Automatisches und manuelles Speichern.
# Laden und Fortsetzen des Spiels.

## Tutorial und Hilfesystem
# Einführung für neue Spieler.
# Kontextabhängige Hilfe.

TICK_INTERVAL = 2  # Tick-Abstand in Sekunden (z.B. alle 1 Sekunde ein Tick)
letzter_tick = time.time()

bForschung_aktiv = False
# bBauen_aktiv = False
iAktueller_Forschungsfortschritt = None
# iAktueller_Baufortschritt = None

bBauen_aktiv = False
iAktueller_Baufortschritt = None
sAktuelles_Bauen = None
iMax_Bauen = None
bau_queue = []            # Die Warteschlange der geplanten Bauaufträge
sAktuelles_Bauen = None   # Bleibt bestehen, wird jetzt von der Queue gefüllt!

missionen_aktiv = []  # Liste der laufenden Missionen

class MissionInstance:
  def __init__(self, missionsname):
    self.name = missionsname
    self.fortschritt = 0
    self.max_fortschritt = ACTIONS[missionsname]['dauer']  # Dauer aus ACTIONS
    self.aktiv = True

  def tick(self):
    if self.aktiv:
      self.fortschritt += 1
      if self.fortschritt >= self.max_fortschritt:
        self.aktiv = False
        return True  # Mission abgeschlossen
    return False

# Globale Variablen für Mondmissionen
bMondmission_aktiv = False
iAktueller_Mondmissionsfortschritt = 0
sAktuelle_Mondmission = None
iMax_Mondmission = 5

def load_gamestate():
  print('load_gamestate()')
  try:
    with open(config.SAVEFILE, "r") as file:
      print('config.SAVEFILE gefunden')
      return json.load(file)
  except FileNotFoundError:
    from gamestate import GAMESTATE
    print('GAMESTATE importiert')
    return GAMESTATE

GAMESTATE = load_gamestate()
iForschungspunkte = GAMESTATE['Forschungspunkte']

def dump_gamestate():
  print('dump_gamestate()')
  GAMESTATE['Ticks'] = iTicks
  GAMESTATE['Credits'] = iCredits
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Log'] = lLog
  with open(config.SAVEFILE, "w") as outfile:
    json.dump(GAMESTATE, outfile, indent=2)

def zeige_Forschung(sAktuelle_Forschung):
  print(f'zeige_Forschung({sAktuelle_Forschung})')
  window['do_research'].update(visible=False)
  window['already_researched'].update(visible=False)

  window['desc_research'].update(visible=True, value=SCIENCE[sAktuelle_Forschung]['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f"Forschungsdauer: {SCIENCE[sAktuelle_Forschung]['dauer']} Zyklen")
  window['desc_costs'].update(visible=True, value=f"Forschungskosten: {SCIENCE[sAktuelle_Forschung]['kosten']}")

  if SCIENCE[sAktuelle_Forschung]['kosten'] > iForschungspunkte:
    window['comment'].update(visible=True, value='Forschungspunkte reichen nicht aus')
    return
  else:
    window['comment'].update(visible=False, value='')

  if not bForschung_aktiv and not GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
    window['do_research'].update(visible=True)

  # if GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
  window['already_researched'].update(visible=GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'])

def aktualisiere_bau_queue_anzeige():
  queue_text = '\n'.join(bau_queue) if bau_queue else "Keine Aufträge in der Warteschlange."
  try:
    window['bau_queue_anzeige'].update(value=queue_text)
  except KeyError:
    pass  # Falls Feld gerade nicht sichtbar ist

def zeige_bauen(sAktuelles_Bauen):
  print('zeige_bauen()')
  """Zeigt Informationen zum ausgewählten Bau-Item"""
  if sAktuelles_Bauen in GAMESTATE['Werkstatt']:
    item = GAMESTATE['Werkstatt'][sAktuelles_Bauen]

    # Beschreibung und Dauer anzeigen
    window['desc_bauen'].update(value=f"{item['beschreibung']}\n\nDauer: {item['dauer']} Zyklen")

    # Benötigte Materialien anzeigen
    materialien_text = "Benötigte Materialien:\n"
    for material, anzahl in item['material'].items():
      verfügbar = GAMESTATE['Inventar'].get(material, 0)
      materialien_text += f"• {material}: {anzahl} (verfügbar: {verfügbar})\n"

    window['desc_materialien'].update(value=materialien_text, visible=True)

    # Prüfen ob alle Materialien verfügbar sind
    kann_bauen = True
    for material, anzahl in item['material'].items():
      if GAMESTATE['Inventar'].get(material, 0) < anzahl:
        kann_bauen = False
        break

    # Bauen-Button nur anzeigen wenn möglich und nicht bereits am Bauen
    if kann_bauen and not bBauen_aktiv:
      window['do_bauen'].update(visible=True)
      window['bauen_unmöglich'].update(visible=False)
    else:
      window['do_bauen'].update(visible=False)
      if not kann_bauen:
        window['bauen_unmöglich'].update(visible=True, value="Nicht genug Materialien!")
      else:
        window['bauen_unmöglich'].update(visible=False)

def bauauftrag_hinzufuegen(item_name):
  global bau_queue
  bau_queue.append(item_name)
  add2log(f"Bauauftrag '{item_name}' wurde zur Warteschlange hinzugefügt.")
  aktualisiere_bau_queue_anzeige()  # Neue Funktion, siehe unten

def baue(sAktuelles_Bauen):
  print('baue()')
  """Startet den Bau-Prozess"""
  global bBauen_aktiv, iAktueller_Baufortschritt, iMax_Bauen

  # Prüfen ob alle Materialien verfügbar sind
  item = GAMESTATE['Werkstatt'][sAktuelles_Bauen]
  for material, anzahl in item['material'].items():
    if GAMESTATE['Inventar'].get(material, 0) < anzahl:
      add2log(f"Nicht genug {material} zum Bauen von {sAktuelles_Bauen}")
      return

  # Materialien sofort abziehen
  for material, anzahl in item['material'].items():
    GAMESTATE['Inventar'][material] -= anzahl

  # Bau-Prozess starten
  bBauen_aktiv = True
  iMax_Bauen = int(item['dauer'] / config.TICK)
  iAktueller_Baufortschritt = 0

  # UI aktualisieren
  window['do_bauen'].update(visible=False)
  window['bauen_unmöglich'].update(visible=False)
  window['progressbar_Bauen'].update(current_count=0, max=iMax_Bauen, visible=True)
  window['stop_bauen'].update(visible=True)

  # Inventar-Anzeige aktualisieren
  aktualisiere_inventar_anzeige()

  add2log(f"Baue '{sAktuelles_Bauen}' - Materialien verbraucht")

def beende_bauen(sAktuelles_Bauen):
  print('beende_bauen()')
  """Beendet den Bau-Prozess erfolgreich"""
  global bBauen_aktiv

  # Gebauten Gegenstand zum Inventar/Raumschiffe hinzufügen
  if sAktuelles_Bauen in ['Mondlander', 'Rakete']:
    # Raumschiffe zur Erde hinzufügen
    GAMESTATE['Raumschiffe']['Erde'][sAktuelles_Bauen]['Anzahl'] += 1
    add2log(f"'{sAktuelles_Bauen}' erfolgreich gebaut - zur Erde hinzugefügt")
  else:
    # Andere Gegenstände ins Inventar
    if sAktuelles_Bauen not in GAMESTATE['Inventar']:
      GAMESTATE['Inventar'][sAktuelles_Bauen] = 0
    GAMESTATE['Inventar'][sAktuelles_Bauen] += 1
    add2log(f"'{sAktuelles_Bauen}' erfolgreich gebaut - ins Inventar gelegt")

  # Bau-Prozess beenden
  bBauen_aktiv = False
  window['progressbar_Bauen'].update(visible=False)
  window['stop_bauen'].update(visible=False)

  # UI vollständig aktualisieren
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  zeige_bauen(sAktuelles_Bauen)  # Erneut anzeigen für nächsten Bau
  aktualisiere_bau_queue_anzeige()


def stoppe_bauen():
  print('stoppe_bauen()')
  """Stoppt den Bau-Prozess und gibt Materialien zurück"""
  global bBauen_aktiv

  if bBauen_aktiv and sAktuelles_Bauen:
    # Materialien zurückgeben
    item = GAMESTATE['Werkstatt'][sAktuelles_Bauen]
    for material, anzahl in item['material'].items():
      GAMESTATE['Inventar'][material] += anzahl

    bBauen_aktiv = False
    window['progressbar_Bauen'].update(visible=False)
    window['stop_bauen'].update(visible=False)

    aktualisiere_inventar_anzeige()
    zeige_bauen(sAktuelles_Bauen)

    add2log(f"Bau von '{sAktuelles_Bauen}' gestoppt - Materialien zurückgegeben")

def erforsche(sAktuelle_Forschung):
  print('erforsche()')
  global bForschung_aktiv
  global iAktueller_Forschungsfortschritt
  global iMax_Forschung
  window['do_research'].update(visible=False)
  bForschung_aktiv = True
  iMax_Forschung = SCIENCE[sAktuelle_Forschung]['dauer'] / config.TICK
  iAktueller_Forschungsfortschritt = 0
  window['progressbar_Forschung'].update(current_count=0, max=iMax_Forschung)
  window['progressbar_Forschung'].update(visible=True)
  window['stop_research'].update(visible=True)

def get_materials_from_inventory():
  print('get_materials_from_inventory()')
  lMaterials = []
  for material, amount in GAMESTATE['Inventar'].items():
    lMaterials.append([sg.Text(material)])
  return lMaterials

def get_amounts_from_inventory():
  print('get_amounts_from_inventory()')
  lAmounts = []
  for material, amount in GAMESTATE['Inventar'].items():
    lAmounts.append([sg.Text(amount)])
  return lAmounts

def add2log(sString):
  print(f'add2log({sString})')
  global lLog
  global sLog
  lLog.append(f"{iTicks}\t{sString}")
  sLog = '\n'.join(lLog[::-1])
  window['Log'].update(value=sLog)

# NEW
def erstelle_inventar_layout():
  print('erstelle_inventar_layout()')
  """Erstellt das Layout für die Inventar-Anzeige dynamisch"""
  inventar_zeilen = []

  # Header
  inventar_zeilen.append([
    sg.Text('Material', size=(20, 1), font=('Arial', 10, 'bold')),
    sg.Text('Anzahl', size=(10, 1), font=('Arial', 10, 'bold')),
    sg.Text('Beschreibung', size=(30, 1), font=('Arial', 10, 'bold'))
  ])

  # Trennlinie
  inventar_zeilen.append([sg.HorizontalSeparator()])

  # Dynamische Einträge für jedes Material
  for material, anzahl in GAMESTATE['Inventar'].items():
    beschreibung = get_material_beschreibung(material)
    farbe = 'green' if anzahl > 0 else 'gray'

    inventar_zeilen.append([
      sg.Text(material, size=(20, 1), key=f'inv_name_{material}'),
      sg.Text(str(anzahl), size=(10, 1), key=f'inv_anzahl_{material}', text_color=farbe),
      sg.Text(beschreibung, size=(30, 1), key=f'inv_desc_{material}', font=('Arial', 8))
    ])

  return inventar_zeilen

def get_material_beschreibung(material):
  print('get_material_beschreibung()')
  """Gibt eine Beschreibung für jedes Material zurück"""
  return MATERIALS.get(material, 'Unbekanntes Material')

def aktualisiere_inventar_anzeige():
  print('aktualisiere_inventar_anzeige()')
  """Aktualisiert die Inventar-Anzeige dynamisch"""
  for material, anzahl in GAMESTATE['Inventar'].items():
    try:
      # Anzahl aktualisieren
      farbe = 'green' if anzahl > 0 else 'gray'
      window[f'inv_anzahl_{material}'].update(value=str(anzahl), text_color=farbe)
    except KeyError:
      # Material existiert noch nicht in der Anzeige - Layout neu erstellen
      print(f"Material {material} nicht in Anzeige gefunden - Layout wird neu erstellt")
      # Hier könntest du das komplette Layout neu erstellen, falls nötig
      pass

def aktualisiere_raumschiff_anzeige():
  print('aktualisiere_raumschiff_anzeige()')
  """Aktualisiert die Raumschiff-Anzeige"""
  try:
    # Raumschiffe auf der Erde
    mondlander_erde = GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl']
    rakete_erde = GAMESTATE['Raumschiffe']['Erde']['Rakete']['Anzahl']

    window['raumschiffe_erde'].update(
      value=f"Mondlander: {mondlander_erde}, Raketen: {rakete_erde}"
    )

    # Raumschiffe auf dem Mond (falls sichtbar)
    if GAMESTATE['Planeten']['Mond']['entdeckt']:
      mondlander_mond = GAMESTATE['Raumschiffe']['Mond']['Mondlander']['Anzahl']
      rakete_mond = GAMESTATE['Raumschiffe']['Mond']['Rakete']['Anzahl']

      window['raumschiffe_mond'].update(
        value=f"Mondlander: {mondlander_mond}, Raketen: {rakete_mond}"
      )

  except KeyError:
    print("Raumschiff-Anzeige konnte nicht aktualisiert werden")

def erstelle_raumschiff_uebersicht():
  print('erstelle_raumschiff_uebersicht()')
  """Erstellt eine Übersicht aller Raumschiffe"""
  raumschiff_layout = []

  # Erde
  raumschiff_layout.append([
    sg.Text('Raumschiffe auf der Erde:', font=('Arial', 10, 'bold'))
  ])
  raumschiff_layout.append([
    sg.Text('', key='raumschiffe_erde', size=(50, 1))
  ])

  # Mond (falls entdeckt)
  if GAMESTATE['Planeten']['Mond']['entdeckt']:
    raumschiff_layout.append([
      sg.Text('Raumschiffe auf dem Mond:', font=('Arial', 10, 'bold'))
    ])
    raumschiff_layout.append([
      sg.Text('', key='raumschiffe_mond', size=(50, 1))
    ])

  # Mars (falls entdeckt)
  if GAMESTATE['Planeten']['Mars']['entdeckt']:
    raumschiff_layout.append([
      sg.Text('Raumschiffe auf dem Mars:', font=('Arial', 10, 'bold'))
    ])
    raumschiff_layout.append([
      sg.Text('', key='raumschiffe_mars', size=(50, 1))
    ])

  return raumschiff_layout

def berechne_inventar_statistiken():
  print('berechne_inventar_statistiken()')
  """Berechnet Statistiken für das Inventar"""
  gesamtwert = 0
  anzahl_typen = 0

  # Materialwerte (beispielhaft)
  materialwerte = {
    'Eisenbarren': 9999999,
    'Baumaterial': 100,
    'Werkzeug': 200,
    'Roheisen': 20,
    'Staub': 5,
    'Wasser': 10,
    'Gold': 500,
    'Raumsonde': 1000,
    'Mondlander': 5000,
    'Rakete': 15000,
    'Weltraumstation': 50000
  }

  for material, anzahl in GAMESTATE['Inventar'].items():
    if anzahl > 0:
      anzahl_typen += 1
      gesamtwert += anzahl * materialwerte.get(material, 0)

  return gesamtwert, anzahl_typen

def aktualisiere_inventar_statistiken():
  print('aktualisiere_inventar_statistiken()')
  """Aktualisiert die Inventar-Statistiken"""
  gesamtwert, anzahl_typen = berechne_inventar_statistiken()

  try:
    window['inventar_gesamtwert'].update(value=f"{gesamtwert:,} Credits")
    window['inventar_anzahl_typen'].update(value=str(anzahl_typen))
  except KeyError:
    pass  # Fenster-Elemente existieren noch nicht

# Globale Variablen für Reisen
aktive_reisen = []  # Liste aller aktiven Reisen

class Reise:
  def __init__(self, raumschiff_typ, von_planet, zu_planet, astronauten, fracht, reise_id):
    print('__init__()')
    self.raumschiff_typ = raumschiff_typ
    self.von_planet = von_planet
    self.zu_planet = zu_planet
    self.astronauten = astronauten
    self.fracht = fracht  # Dictionary mit Materialien
    self.reise_id = reise_id
    self.start_tick = iTicks
    self.dauer = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
    self.end_tick = self.start_tick + self.dauer
    self.abgeschlossen = False

  def fortschritt(self, aktuelle_tick):
    print('fortschritt()')
    if aktuelle_tick >= self.end_tick:
      return 100
    return min(100, ((aktuelle_tick - self.start_tick) / self.dauer) * 100)

  def ist_abgeschlossen(self, aktuelle_tick):
    print('ist_abgeschlossen()')
    return aktuelle_tick >= self.end_tick

def get_verfuegbare_raumschiffe(planet):
  print('get_verfuegbare_raumschiffe()')
  """Gibt verfügbare Raumschiffe auf einem Planeten zurück"""
  verfuegbare = {}
  for raumschiff_typ in ['Mondlander', 'Rakete']:
    anzahl = GAMESTATE['Raumschiffe'][planet][raumschiff_typ]['Anzahl']
    if anzahl > 0:
      verfuegbare[raumschiff_typ] = anzahl
  return verfuegbare

def get_raumschiff_kapazitaet(raumschiff_typ):
  print('get_raumschiff_kapazitaet()')
  """Gibt die Kapazitäten eines Raumschiffs zurück"""
  eintrag = SCIENCE.get(raumschiff_typ, {})
  astronauten = eintrag.get('Sitzplätze', 0)
  fracht = eintrag.get('Frachtplätze', 0)
  # Reichweite kann optional gesetzt werden, falls im SCIENCE vorhanden
  reichweite = eintrag.get('reichweite', 0)
  return {'astronauten': astronauten, 'fracht': fracht, 'reichweite': reichweite}

def kann_reisen(von_planet, zu_planet, raumschiff_typ):
  print('kann_reisen()')
  """Prüft ob eine Reise möglich ist"""
  # Prüfen ob Zielplanet entdeckt ist
  if not GAMESTATE['Planeten'][zu_planet]['entdeckt'] and zu_planet != 'Erde':
    return False, "Zielplanet nicht entdeckt"
  # Prüfen ob Raumschiff verfügbar
  if GAMESTATE['Raumschiffe'][von_planet][raumschiff_typ]['Anzahl'] <= 0:
    return False, f"Kein {raumschiff_typ} auf {von_planet} verfügbar"
  # Prüfen ob Reichweite ausreicht
  entfernung = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
  reichweite = get_raumschiff_kapazitaet(raumschiff_typ).get('reichweite', 0)
  if reichweite== 0:
    return False, f"Reichweite von {raumschiff_typ} = {reichweite}"
  elif entfernung > reichweite:
    return False, f"Reichweite von {raumschiff_typ} {reichweite} zu gering - {entfernung}"
  return True, "Reise möglich"

def starte_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict):
  print('starte_reise()')
  """Startet eine neue Reise"""
  global aktive_reisen
  kann_reisen_result, grund = kann_reisen(von_planet, zu_planet, raumschiff_typ)
  if not kann_reisen_result:
    add2log(f"Reise nicht möglich: {grund}")
    return False
  kapazitaet = get_raumschiff_kapazitaet(raumschiff_typ)
  # Prüfen ob genug Astronauten verfügbar
  if astronauten_anzahl > GAMESTATE['Astronauten'][von_planet]:
    add2log("Nicht genug Astronauten verfügbar")
    return False
  # Prüfen ob Astronauten-Kapazität ausreicht
  if astronauten_anzahl > kapazitaet['astronauten']:
    add2log("Zu viele Astronauten für dieses Raumschiff")
    return False
  # Prüfen ob Fracht-Kapazität ausreicht
  fracht_gesamt = sum(fracht_dict.values())
  if fracht_gesamt > kapazitaet['fracht']:
    add2log("Zu viel Fracht für dieses Raumschiff")
    return False
  # Prüfen ob Fracht verfügbar ist
  for material, anzahl in fracht_dict.items():
    if GAMESTATE['Inventar'].get(material, 0) < anzahl:
      add2log(f"Nicht genug {material} im Inventar")
      return False
  # Ressourcen abziehen
  GAMESTATE['Raumschiffe'][von_planet][raumschiff_typ]['Anzahl'] -= 1
  GAMESTATE['Astronauten'][von_planet] -= astronauten_anzahl
  for material, anzahl in fracht_dict.items():
    GAMESTATE['Inventar'][material] -= anzahl
  # Reise erstellen
  reise_id = len(aktive_reisen)
  neue_reise = Reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict, reise_id)
  aktive_reisen.append(neue_reise)
  add2log(f"Reise gestartet: {raumschiff_typ} von {von_planet} nach {zu_planet} mit {astronauten_anzahl} Astronauten und Fracht {fracht_dict}")
  return True

def beende_reise(reise):
  print('beende_reise()')
  """Beendet eine Reise und bringt Raumschiff ans Ziel"""
  # Raumschiff am Zielort hinzufügen
  GAMESTATE['Raumschiffe'][reise.zu_planet][reise.raumschiff_typ]['Anzahl'] += 1
  reise.abgeschlossen = True
  # Astronauten am Zielplanet hinzufügen und am Startplanet abziehen
  GAMESTATE['Astronauten'][reise.zu_planet] += reise.astronauten
  GAMESTATE['Astronauten'][reise.von_planet] -= reise.astronauten
  if reise.raumschiff_typ in GAMESTATE['Raumschiffe'][reise.zu_planet]:
    GAMESTATE['Raumschiffe'][reise.zu_planet][reise.raumschiff_typ]['Anzahl'] += 1
  # Fracht am Zielplanet ins Inventar
  for material, anzahl in reise.fracht.items():
    GAMESTATE['Inventar'][material] = GAMESTATE['Inventar'].get(material, 0) + anzahl
  add2log(f"Reise abgeschlossen: {reise.raumschiff_typ} ist auf {reise.zu_planet} angekommen.")

  # Spezielle Aktionen je nach Zielplanet
  if reise.zu_planet == 'Mond' and not GAMESTATE['Planeten']['Mond']['entdeckt']:
    GAMESTATE['Planeten']['Mond']['entdeckt'] = True
    add2log("Mond entdeckt!")
    iForschungspunkte += 50

  if reise.zu_planet == 'Mars' and not GAMESTATE['Planeten']['Mars']['entdeckt']:
    GAMESTATE['Planeten']['Mars']['entdeckt'] = True
    add2log("Mars entdeckt!")
    iForschungspunkte += 100

  add2log(f"{reise.raumschiff_typ} erreicht {reise.zu_planet}")
  add2log(f"Astronauten: {reise.astronauten}, Fracht gelandet")

  reise.abgeschlossen = True
  aktualisiere_alle_anzeigen()

def verwalte_aktive_reisen():
  print('verwalte_aktive_reisen()')
  """Verwaltet alle aktiven Reisen"""
  global aktive_reisen
  globale_ticks = iTicks
  for reise in aktive_reisen:
    if not reise.abgeschlossen and reise.ist_abgeschlossen(globale_ticks):
      beende_reise(reise)
  for reise in aktive_reisen[:]:  # Copy der Liste für sichere Iteration
    if not reise.abgeschlossen and reise.ist_abgeschlossen(iTicks):
      beende_reise(reise)

  # Abgeschlossene Reisen entfernen
  aktive_reisen = [r for r in aktive_reisen if not r.abgeschlossen]

def aktualisiere_reise_anzeige():
  print('aktualisiere_reise_anzeige()')
  """Aktualisiert die Anzeige der aktiven Reisen"""
  try:
    if not aktive_reisen:
      pass
      # window['aktive_reisen'].update(value="Keine aktiven Reisen")
    else:
      reise_text = ""
      for reise in aktive_reisen:
        if not reise.abgeschlossen:
          fortschritt = reise.fortschritt(iTicks)
          reise_text += f"{reise.raumschiff_typ}: {reise.von_planet} → {reise.zu_planet} ({fortschritt:.1f}%)\n"

      window['aktive_reisen'].update(value=reise_text if reise_text else "Keine aktiven Reisen")
  except KeyError:
    pass  # Element existiert noch nicht

def aktualisiere_alle_anzeigen():
  print('aktualisiere_alle_anzeigen()')
  """Aktualisiert alle UI-Elemente"""
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_reise_anzeige()
  aktualisiere_planeten_anzeige()

def aktualisiere_planeten_anzeige():
  print('aktualisiere_planeten_anzeige()')
  """Aktualisiert die Astronauten-Anzeige auf den Planeten"""
  try:
    # HQ Tab
    window['astronauten_erde'].update(value=f"Astronauten auf der Erde: {GAMESTATE['Astronauten']['Erde']}")

    if GAMESTATE['Planeten']['Mond']['entdeckt']:
      window['astronauten_mond'].update(value=f"Astronauten auf dem Mond: {GAMESTATE['Astronauten']['Mond']}")
    if GAMESTATE['Planeten']['Mars']['entdeckt']:
      window['astronauten_mars'].update(value=f"Astronauten auf dem Mars: {GAMESTATE['Astronauten']['Mars']}")
  except KeyError:
    pass

def erstelle_reise_interface():
  print('erstelle_reise_interface()')
  """Erstellt das Interface für Reisen"""

  # Radiobuttons für Start- und Zielplanet
  verfuegbare_planeten = ['Erde']
  if GAMESTATE['Planeten']['Mond']['entdeckt']:
    verfuegbare_planeten.append('Mond')
  if GAMESTATE['Planeten']['Mars']['entdeckt']:
    verfuegbare_planeten.append('Mars')
  planet_radio_von = [sg.Radio(planet, 'reise_von', key=f'reise_von_{planet}', enable_events=True) for planet in verfuegbare_planeten]
  planet_radio_zu = [sg.Radio(planet, 'reise_zu', key=f'reise_zu_{planet}', enable_events=True) for planet in verfuegbare_planeten]
  # Raumschiff-Typen
  raumschiff_typen = ['Mondlander', 'Rakete']
  raumschiff_radio = [sg.Radio(typ, 'reise_raumschiff', key=f'reise_raumschiff_{typ}', enable_events=True) for typ in raumschiff_typen]
  # Materialliste dynamisch aus Inventar
  material_keys = [k for k in GAMESTATE['Inventar'].keys() if k in ['Eisenbarren', 'Werkzeug', 'Baumaterial']]
  material_rows = [[sg.Text(f'{mat}:'), sg.Spin([i for i in range(0, GAMESTATE['Inventar'][mat]+1)], initial_value=0, key=f'fracht_{mat}')] for mat in material_keys]
  return [
    [sg.Text('Reise planen', font=('Arial', 12, 'bold'))],
    [sg.HorizontalSeparator()],
    [sg.Text('Von Planet:'), *planet_radio_von],
    [sg.Text('Zu Planet:'), *planet_radio_zu],
    [sg.Text('Raumschiff:'), *raumschiff_radio],
    [sg.HorizontalSeparator()],
    [sg.Text('Astronauten:'), sg.Spin([i for i in range(0, 11)], initial_value=0, key='reise_astronauten')],
    [sg.Text('Fracht (optional):')],
    *material_rows,
    [sg.HorizontalSeparator()],
    [sg.Text('', key='reise_info', size=(50, 3))],
    [sg.Button('Reise starten', key='starte_reise'), sg.Button('Abbrechen', key='reise_abbrechen')],
    [sg.HorizontalSeparator()],
    [sg.Text('Aktive Reisen:', font=('Arial', 10, 'bold'))],
    [sg.Multiline('', key='aktive_reisen', size=(50, 8), disabled=True)],
  ]

# Neues Tab für Reisen
lTab_Reisen = erstelle_reise_interface()

def aktualisiere_missionen_anzeige():
  text = ""
  for m in missionen_aktiv:
    status = "abgeschlossen" if not m.aktiv else f"{m.fortschritt}/{m.max_fortschritt} Zyklen"
    text += f"- {m.name}: {status}\n"
  try:
    if GAMESTATE['Planeten']['Mond']['entdeckt']:
      window['laufende_missionen_anzeige'].update(value=text if text else "Keine laufenden Missionen.")
  except KeyError:
    pass

def zeige_mondmission(sAktuelle_Mission):
  print('zeige_mondmission()')
  """Zeigt Informationen zur ausgewählten Mondmission"""
  window['do_mondmission'].update(visible=False)
  window['mondmission_completed'].update(visible=False)

  mission = ACTIONS[sAktuelle_Mission]

  # Beschreibung und Dauer anzeigen
  window['desc_mondmission'].update(
    visible=True,

    value=f"{mission['beschreibung']}\n\nDauer: {mission['dauer']} Zyklen\nKosten: {mission['kosten']} Credits"
  )

  # Anforderungen anzeigen
  anforderungen_text = "Anforderungen:\n"
  for key, value in mission.items():
    if key.startswith('benötigt_'):
      ressource = key.replace('benötigt_', '').replace('_', ' ').title()
      verfügbar = GAMESTATE['Inventar'].get(key.replace('benötigt_', '').title(), 0)
      if key == 'benötigt_astronauten':
        verfügbar = GAMESTATE['Astronauten']['Mond']
      anforderungen_text += f"• {ressource}: {value} (verfügbar: {verfügbar})\n"

  # Belohnungen anzeigen
  belohnungen_text = "\nBelohnungen:\n"
  for belohnung, wert in mission['belohnung'].items():
    belohnungen_text += f"• {belohnung.replace('_', ' ')}: {wert}\n"

  window['desc_mondmission_anforderungen'].update(
    value=anforderungen_text + belohnungen_text,

    visible=True
  )

  # Prüfen ob Mission durchführbar ist
  kann_mission = True
  grund = ""

  # Prüfen ob auf dem Mond
  if GAMESTATE['Astronauten']['Mond'] == 0:
    kann_mission = False
    grund = "Keine Astronauten auf dem Mond!"

  # Prüfen ob genug Credits
  elif iCredits < mission['kosten']:
    kann_mission = False
    grund = "Nicht genug Credits!"

  # Prüfen ob Mission bereits abgeschlossen
  elif mission['erforscht']:
    kann_mission = False
    grund = "Mission bereits abgeschlossen!"
    window['mondmission_completed'].update(visible=True)

  # Prüfen ob Anforderungen erfüllt sind
  else:
    for key, value in mission.items():
      if key.startswith('benötigt_'):
        if key == 'benötigt_astronauten':
          if GAMESTATE['Astronauten']['Mond'] < value:
            kann_mission = False
            grund = f"Nicht genug Astronauten auf dem Mond (benötigt: {value})"
            break
        else:
          ressource = key.replace('benötigt_', '').title()
          if GAMESTATE['Inventar'].get(ressource, 0) < value:
            kann_mission = False
            grund = f"Nicht genug {ressource} (benötigt: {value})"
            break

  # Mission-Button anzeigen/verstecken
  if kann_mission and not bMondmission_aktiv:
    window['do_mondmission'].update(visible=True)
    window['mondmission_unmöglich'].update(visible=False)
  else:
    window['do_mondmission'].update(visible=False)
    if grund:
      window['mondmission_unmöglich'].update(visible=True, value=grund)
    else:
      window['mondmission_unmöglich'].update(visible=False)

def starte_mondmission(sAktuelle_Mission):
  global missionen_aktiv, iCredits
  mission = ACTIONS[sAktuelle_Mission]

  # Voraussetzungen prüfen (wie gehabt)
  if iCredits < mission['kosten']:
    add2log("Nicht genug Credits für Mission!")
    return
  for key, value in mission.items():
    if key.startswith('benötigt_') and key != 'benötigt_astronauten':
      ressource = key.replace('benötigt_', '').title()
      if GAMESTATE['Inventar'].get(ressource, 0) < value:
        add2log(f"Nicht genug {ressource}")
        return
  # Ressourcen abziehen (wie gehabt)
  iCredits -= mission['kosten']
  for key, value in mission.items():
    if key.startswith('benötigt_') and key != 'benötigt_astronauten':
      ressource = key.replace('benötigt_', '').title()
      GAMESTATE['Inventar'][ressource] -= value
  # Neue MissionInstanz starten und in die Liste eintragen
  missionen_aktiv.append(MissionInstance(sAktuelle_Mission))
  add2log(f"Mission '{sAktuelle_Mission}' gestartet.")
  aktualisiere_missionen_anzeige()

def beende_mondmission(missionsname):
  global iForschungspunkte, iCredits
  mission = ACTIONS[missionsname]
  for belohnung, wert in mission['belohnung'].items():
    if belohnung == 'Forschungspunkte':
      iForschungspunkte += wert
    elif belohnung == 'Credits':
      iCredits += wert
    else:
      if belohnung not in GAMESTATE['Inventar']:
        GAMESTATE['Inventar'][belohnung] = 0
      GAMESTATE['Inventar'][belohnung] += wert
  ACTIONS[missionsname]['erforscht'] = True
  add2log(f"Mission '{missionsname}' abgeschlossen!")

def stoppe_mondmission():
  print('stoppe_mondmission()')
  """Stoppt eine Mondmission und gibt Ressourcen zurück"""
  global bMondmission_aktiv, iCredits

  if bMondmission_aktiv and sAktuelle_Mondmission:
    mission = ACTIONS[sAktuelle_Mondmission]

    # Credits zurückgeben
    iCredits += mission['kosten']

    # Ressourcen zurückgeben
    for key, value in mission.items():
      if key.startswith('benötigt_') and key != 'benötigt_astronauten':
        ressource = key.replace('benötigt_', '').title()
        GAMESTATE['Inventar'][ressource] += value

    bMondmission_aktiv = False
    window['progressbar_Mondmission'].update(visible=False)
    window['stop_mondmission'].update(visible=False)

    aktualisiere_inventar_anzeige()
    zeige_mondmission(sAktuelle_Mondmission)

    add2log(f"Mondmission '{sAktuelle_Mondmission}' abgebrochen - Ressourcen zurückgegeben")

# Neue Tab für Mondmissionen
def erstelle_mondmission_tab():
  print('erstelle_mondmission_tab()')
  """Erstellt das Tab für Mondmissionen"""
  return [
    [sg.Text('Mondmissionen', font=('Arial', 12, 'bold'))],
    [sg.Text('Nur verfügbar wenn Astronauten auf dem Mond sind', font=('Arial', 10, 'italic'))],
    [sg.HorizontalSeparator()],

    [
      sg.Column([
        [sg.Button('Erkundung und Probenentnahme', key='mondmission_Erkundung und Probenentnahme')],
        [sg.Button('Konstruktion und Reparatur', key='mondmission_Konstruktion und Reparatur von Strukturen')],
        [sg.Button('Navigation und Schwerkraft', key='mondmission_Navigation und Anpassung an die geringere Schwerkraft')],
        [sg.Button('Raumfahrttechnik', key='mondmission_Raumfahrttechnik und -navigation')],
        [sg.Button('Geologische Untersuchungen', key='mondmission_Geologische Untersuchungen')],
        [sg.Button('Lebenserhaltungssysteme', key='mondmission_Lebenserhaltungssysteme')],
        [sg.Button('Kommunikation', key='mondmission_Kommunikation und Datenübertragung')],
        [sg.Button('Mondbasen-Design', key='mondmission_Mondbasen-Design')],
      ], vertical_alignment='top'),

      sg.VerticalSeparator(),

      sg.Column([
        [sg.Text('', key='desc_mondmission', size=(50, 6), visible=False)],
        [sg.Text('', key='desc_mondmission_anforderungen', size=(50, 8), visible=False)],
        [sg.Button('Mission starten', key='do_mondmission', visible=False)],
        [sg.Text('', key='mondmission_unmöglich', visible=False, text_color='red')],
        [sg.Text('Mission abgeschlossen', key='mondmission_completed', visible=False, text_color='green')],
        [sg.ProgressBar(0, orientation='h', size=(40, 20), key='progressbar_Mondmission', visible=False)],
        [sg.Button('Mission stoppen', key='stop_mondmission', visible=False)],
        [sg.Text('Laufende Missionen:', font=('Arial',10, 'bold'))],
        [sg.Multiline('', key='laufende_missionen_anzeige', size=(50, 4), disabled=True)],
      ], vertical_alignment='top'),
    ],
  ]

# Fügen Sie das neue Tab zur LAYOUT-Definition hinzu:
lTab_Mondmissionen = erstelle_mondmission_tab()

# NEW ENDE

menu_def = [['&File', ['&Load', '&Save']]]

lTab_HQ = [
  [sg.Text('Headquarter', font=('Arial', 12, 'bold'))],
  [sg.HorizontalSeparator()],

  # Astronauten-Übersicht
  [sg.Text('Astronauten-Verteilung:', font=('Arial', 10, 'bold'))],
  [sg.Text(f"Astronauten auf der Erde: {GAMESTATE['Astronauten']['Erde']}", key='astronauten_erde')],
  [sg.Text(f"Astronauten auf dem Mond: {GAMESTATE['Astronauten']['Mond']}", key='astronauten_mond', visible=GAMESTATE['Planeten']['Mond']['entdeckt'])],
  [sg.Text(f"Astronauten auf dem Mars: {GAMESTATE['Astronauten']['Mars']}", key='astronauten_mars', visible=GAMESTATE['Planeten']['Mars']['entdeckt'])],

  [sg.HorizontalSeparator()],

  # Schnell-Aktionen
  [sg.Text('Schnell-Aktionen:', font=('Arial', 10, 'bold'))],
  [sg.Text('Sende eine Raumsonde in den Weltraum, um etwas zu entdecken', visible=not GAMESTATE['Planeten']['Mond']['entdeckt'])],
  [sg.Button('Starte Raumsonde', key='starte_raumsonde', visible=bool(GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl']))],
]

if GAMESTATE['Planeten']['Mond']['entdeckt']:
  lTab_HQ.append([sg.HorizontalSeparator()])
  # Aktive Reisen (Übersicht)
  lTab_HQ.append([sg.Text('Aktive Reisen:', font=('Arial', 10, 'bold'))])
  lTab_HQ.append([sg.Text('', key='aktive_reisen_uebersicht', size=(50, 3))])

lTab_Forschung = [
  [
    sg.Column([
      [
        sg.Button(button_text=name, key=f'Erforsche {name}', visible=name == 'Eisenbarren' or GAMESTATE['Forschung'][SCIENCE[data['erforschbar nach']]]['erforscht'] or
                  (data.get('erforschbar nach', '') and GAMESTATE['Forschung'].get(data.get('erforschbar nach', ''), {}).get('erforscht', False))),
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung'][name]['erforscht'], key=f'img_{name}')
      ]
      for name, data in SCIENCE.items()
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='desc_research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [sg.Text('', key='desc_costs', visible=False)],
      [sg.Text('', key='comment', visible=False)],
      [
        sg.Button('Erforschen', key='do_research', visible=False),
        sg.Text('erforscht', key='already_researched', visible=False)
      ],
      [
        sg.ProgressBar(0, orientation='h', size=(20, 20), key='progressbar_Forschung', visible=False),
        sg.Button('Erforschen stoppen', key='stop_research', visible=False),
      ],
    ]),
  ],
]

lTab_Werkstatt = [
  [
    sg.Column([
      [
        sg.Button(button_text=name, key=f'baue_{name}', visible=GAMESTATE['Forschung'][name]['erforscht']),
      ]
      for name in SCIENCE

    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='desc_bauen', size=(40, 4))],
      [sg.Text('', key='desc_materialien', size=(40, 6), visible=False)],
      [sg.Button('Bauen', key='do_bauen', visible=False)],
      [sg.Text('', key='bauen_unmöglich', visible=False, text_color='red')],
      [sg.ProgressBar(0, orientation='h', size=(30, 20), key='progressbar_Bauen', visible=False)],
      [sg.Button('Bauen stoppen', key='stop_bauen', visible=False)],
      [sg.Text('Warteschlange:', font=('Arial',10,'bold'))],
      [sg.Multiline('', key='bau_queue_anzeige', size=(40,3), disabled=True)],
      [sg.Button('Nächsten Bauauftrag stornieren', key='storniere_bauauftrag')]
    ]),
  ],
]

# Ersetze das alte lTab_Inventory durch:
def erstelle_inventar_tab():
  print('erstelle_inventar_tab()')
  """Erstellt das komplette Inventar-Tab dynamisch"""
  inventar_layout = erstelle_inventar_layout()
  raumschiff_layout = erstelle_raumschiff_uebersicht()

  return [
    [sg.Text('Inventar', font=('Arial', 12, 'bold'))],
    [sg.HorizontalSeparator()],

    # Materialien
    [sg.Text('Materialien:', font=('Arial', 10, 'bold'))],
    [sg.Column(inventar_layout, scrollable=True, vertical_scroll_only=True, size=(600, 200))],

    [sg.HorizontalSeparator()],

    # Raumschiffe
    [sg.Text('Raumschiffe:', font=('Arial', 10, 'bold'))],
    [sg.Column(raumschiff_layout, size=(600, 100))],

    [sg.HorizontalSeparator()],

    # Statistiken
    [sg.Text('Statistiken:', font=('Arial', 10, 'bold'))],
    [sg.Text('Gesamtwert des Inventars:', size=(20, 1)), sg.Text('', key='inventar_gesamtwert')],
    [sg.Text('Anzahl verschiedener Materialien:', size=(20, 1)), sg.Text('', key='inventar_anzahl_typen')],
  ]

# Aktualisiere die LAYOUT-Definition:
lTab_Inventory = erstelle_inventar_tab()

lTab_Erde = [
  [sg.Text('Erde')],
  [sg.Text(f"Astronauten auf der Erde {GAMESTATE['Astronauten']['Erde']}")],
]

lTab_Mond = [
  [sg.Text('Mond')],
  [sg.Text(f"Astronauten auf dem Mond {GAMESTATE['Astronauten']['Mond']}")],
]

lTab_Mars = [
  [sg.Text('Mars')],
  [sg.Text(f"Astronauten auf dem Mars {GAMESTATE['Astronauten']['Mars']}")],
]

tabs_planets = [
    [sg.Tab('Erde', lTab_Erde, key='tab_erde')],
]

if GAMESTATE['Planeten']['Mond']['entdeckt']:
    tabs_planets.append([sg.Tab('Mond', lTab_Mond, key='tab_mond')])

if GAMESTATE['Planeten']['Mars']['entdeckt']:
    tabs_planets.append([sg.Tab('Mars', lTab_Mars, key='tab_mars')])

lTab_Planets = [
  [
    sg.TabGroup(
      tabs_planets,
      expand_x=True,
      expand_y=True,
    )
  ]
]

lTab_Shop = [
  [
    sg.Column([
      [sg.Button(button_text='Baumaterial')],
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('Beschreibung:')],
      [sg.Text('', key='desc_fsfsdfsdf', visible=False, size=(30, 6))],
      [sg.Button('Kaufen', key='do_kaufen', visible='wenn credits reichen'=='wenn credits reichen')],
    ]),
  ],
]

lLog = GAMESTATE['Log']
sLog = '\n'.join(lLog[::-1])
print(sLog)

tabs = [
  [sg.Tab('HQ', lTab_HQ, key='tab_HQ')],
  [sg.Tab('Forschung', lTab_Forschung, key='tab_Forschung')],
  [sg.Tab('Inventar', lTab_Inventory, key='tab_Inventar')],
  [sg.Tab('Planeten', lTab_Planets, key='tab_Planeten')],
  [sg.Tab('Shop', lTab_Shop, key='tab_Shop')],
  [sg.Tab('Werkstatt', lTab_Werkstatt, key='tab_Werkstatt')],
]

if GAMESTATE['Planeten']['Mond']['entdeckt']:
  tabs.append([sg.Tab('Reisen', lTab_Reisen, key='tab_Reisen')])
  tabs.append([sg.Tab('Mondmissionen', lTab_Mondmissionen, key='tab_Mondmissionen')])

LAYOUT = [
  [sg.Menu(menu_def)],
  [
    [
      sg.Text(text='Cycle:', key='tCycles'),
      sg.Text(text='Credits:', key='tCredits'),
      sg.Text(text='Forschungspunkte:', key='tForschungspunkte'),
    ],
    sg.Column([
      [sg.TabGroup(
      tabs,
      expand_x=True, expand_y=True, change_submits=True, enable_events=True, key='TabGroup_Main', tab_location='top')]
    ]),
    sg.Column([[sg.Image(r'images\TAB_HQ.png', key='img_Spalte3')]])
  ],

  [
    [
      sg.Column([
        [sg.Multiline(sLog, font=('Consolas', 8), disabled=True, size=(615, 50), key='Log')]
      ],
      size=(615, 50)
      )
    ]
  ]
]

iTicks = GAMESTATE['Ticks']
iCredits = GAMESTATE['Credits']
iForschungspunkte = GAMESTATE['Forschungspunkte']
print(f'{iForschungspunkte = }')
inventory = GAMESTATE['Inventar']
sAktuelle_Forschung = list(SCIENCE.keys())[0]

# window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True)
window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True, finalize=True)

# Bei Spielstart einmalig ausführen:
aktualisiere_inventar_anzeige()
aktualisiere_raumschiff_anzeige()
aktualisiere_inventar_statistiken()

while True:
  event, values = window.read(timeout=100)  # kurzer timeout!
  current_time = time.time()

  # Echtzeit-Tick-Handling
  if current_time - letzter_tick >= TICK_INTERVAL:
    iTicks += 1
    print(f'Cycle: {iTicks}')
    print(f'Forschungspunkte: {iForschungspunkte}')
    letzter_tick = current_time
    window['tCycles'].update(f'Cycle: {iTicks}')
    window['tCredits'].update(f'Credits: {iCredits}')
    window['tForschungspunkte'].update(f'Forschungspunkte: {iForschungspunkte}')

    if bForschung_aktiv:
      iAktueller_Forschungsfortschritt += 1
      window['progressbar_Forschung'].update(current_count=iAktueller_Forschungsfortschritt)
      if iAktueller_Forschungsfortschritt == iMax_Forschung:
        add2log(f"Forschung von '{sAktuelle_Forschung}' beendet")
        bForschung_aktiv = False
        GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'] = True
        
        # Update building buttons visibility
        for name in SCIENCE:
          window[f'baue_{name}'].update(visible=GAMESTATE['Forschung'][name]['erforscht'])

        # Update UI elements for completed research
        window['progressbar_Forschung'].update(visible=False)
        window['stop_research'].update(visible=False)
        window['already_researched'].update(visible=True)
        window[f'img_{sAktuelle_Forschung}'].update(visible=True)
        
        # Update research button visibility for all items
        for forschung_name, forschung_data in SCIENCE.items():
          erforschbar_nach = forschung_data.get('erforschbar nach', '')
          
          # Show button if no prerequisite OR if prerequisite is researched
          if not erforschbar_nach or GAMESTATE['Forschung'][erforschbar_nach]['erforscht']:
            window[f'Erforsche {forschung_name}'].update(visible=True)
            
            # Change color to green if already researched
            if GAMESTATE['Forschung'][forschung_name]['erforscht']:
              window[f'Erforsche {forschung_name}'].update(button_color=('black', 'green'))
          else:
            window[f'Erforsche {forschung_name}'].update(visible=False)
      # if iAktueller_Forschungsfortschritt == iMax_Forschung:
      #   add2log(f"Forschung von '{sAktuelle_Forschung}' beendet")
      #   bForschung_aktiv = False
      #   GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'] = True
      #   for name in SCIENCE:
      #     window[f'baue_{name}'].update(visible=GAMESTATE['Forschung'][name]['erforscht'])

      #   window['progressbar_Forschung'].update(visible=False)
      #   window['stop_research'].update(visible=False)
      #   window['already_researched'].update(visible=True)
      #   window[f'img_{sAktuelle_Forschung}'].update(visible=True)
      #   for sForschung in list(SCIENCE.keys()):
      #     if GAMESTATE['Forschung'][sForschung]['erforscht']:
      #       window[f'Erforsche {sForschung}'].update(visible=True)
      #       window[f'Erforsche {sForschung}'].update(button_color = ('black','green'))
            # window[f'Erforsche {sAktuelle_Forschung}'].update(button_color = ('black','green'))

        # for name in ['Eisenbarren', 'Werkzeug', 'Baumaterial', 'Raumsonde', 'Mondlander', 'Rakete', 'Weltraumstation']:
        #   window[f'baue_{name}'].update(visible=GAMESTATE['Forschung'][name]['erforscht'])
        # window.refresh()

    # Bau-Queue-Handling: Wenn kein Bau läuft, aber etwas in der Queue ist → Starte nächsten Bau
    if not bBauen_aktiv and len(bau_queue) > 0:
      sAktuelles_Bauen = bau_queue.pop(0)
      baue(sAktuelles_Bauen)    # Startet den üblichen Bauprozess
      aktualisiere_bau_queue_anzeige()

    if bBauen_aktiv:
        iAktueller_Baufortschritt += 1
        window['progressbar_Bauen'].update(current_count=iAktueller_Baufortschritt)
        if iAktueller_Baufortschritt >= iMax_Bauen:
            beende_bauen(sAktuelles_Bauen)
        window['stop_research'].update(visible=False)
        window[f'img_{sAktuelles_Bauen}'].update(visible=True)
        for sForschung in list(SCIENCE.keys()):
          window[f'baue_{sForschung}'].update(visible=GAMESTATE['Forschung'][sForschung]['erforscht'])

        window.refresh()

    # if aktive_reisen:
    #   verwalte_aktive_reisen()


    if bMondmission_aktiv:
      iAktueller_Mondmissionsfortschritt += 1
      window['progressbar_Mondmission'].update(current_count=iAktueller_Mondmissionsfortschritt)
      if iAktueller_Mondmissionsfortschritt >= iMax_Mondmission:
        beende_mondmission(sAktuelle_Mondmission)

    for mission in missionen_aktiv[:]:  # Kopie der Liste, da ggf. Missionen entfernt werden
      if mission.aktiv:
        abgeschlossen = mission.tick()
        if abgeschlossen:
          beende_mondmission(mission.name)
          missionen_aktiv.remove(mission)
    aktualisiere_missionen_anzeige()

  # Reise-Anzeige regelmäßig aktualisieren
    aktualisiere_reise_anzeige()

    if iTicks % config.CREDITS_EXTRA_TICKS == 0:
      iCredits += config.CREDITS_EXTRA

    if iTicks % config.SCIENCE_POINTS_EXTRA_TICKS == 0:
      iForschungspunkte += config.SCIENCE_POINTS_EXTRA

  if event in (sg.WINDOW_CLOSED, 'Exit'):
    dump_gamestate()
    break

  if event == 'TabGroup_Main' and values['TabGroup_Main'] == 'TAB_INVENTAR':
    aktualisiere_inventar_anzeige()
    aktualisiere_raumschiff_anzeige()
    aktualisiere_inventar_statistiken()

  if event == 'TabGroup_Main':
    window['img_Spalte3'].update(filename=rf"images\{values['TabGroup_Main']}.png")
    if values['TabGroup_Main'] == 'TAB_FORSCHUNG':
      zeige_Forschung(sAktuelle_Forschung)

  elif event == 'HQ':
    window['tab_HQ'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_HQ.png')

  elif event == 'Forschung':
    window['tab_Forschung'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_FORSCHUNG.png')

  elif event == 'Inventar':
    window['tab_Inventar'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_INVENTAR.png')

  elif event == 'Planeten':
    window['tab_Planeten'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_PLANETEN.png')

  elif event == 'Shop':
    window['tab_Shop'].select()
    window['img_Spalte3'].update(filename=r'images\TAB_SHOP.png')

  elif 'Erforsche ' in event:
    _, sAktuelle_Forschung = event.split(' ')
    zeige_Forschung(sAktuelle_Forschung)

  elif 'Baue ' in event:
    _, sAktuelles_Bauen = event.split(' ')
    # baue(sAktuelles_Bauen)
    bauauftrag_hinzufuegen(sAktuelles_Bauen)

  elif event == 'do_research':
    add2log(f"Erforsche '{sAktuelle_Forschung}'")
    erforsche(sAktuelle_Forschung)

  elif event == 'stop_research':
    window['progressbar_Forschung'].update(visible=False)
    window['stop_research'].update(visible=False)
    window['do_research'].update(visible=True)
    add2log(f"Forschung von '{sAktuelle_Forschung}' gestoppt")
    bForschung_aktiv = False

  elif event == 'starte_bauen':
    add2log(f"Baue '{sAktuelles_Bauen}'")
    baue(sAktuelles_Bauen)

  elif event == 'stop_bauen':
    print('stop_bauen')

  elif event == 'storniere_bauauftrag':
    if bau_queue:
      canceled = bau_queue.pop(0)
      add2log(f"Bauauftrag '{canceled}' aus der Warteschlange entfernt.")
      aktualisiere_bau_queue_anzeige()
    else:
      add2log("Keine Bauaufträge zu stornieren.")

  elif event == 'Save':
    dump_gamestate()

  elif event == 'Load':
    GAMESTATE = load_gamestate()
    iTicks = GAMESTATE['Ticks']
    iCredits = GAMESTATE['Credits']
    iForschungspunkte = GAMESTATE['Forschungspunkte']

  elif event == 'refreshwindow':
    print('window.refresh()')
    print(SCIENCE[sAktuelle_Forschung])
    window.refresh()

  elif event.startswith('baue_'):
      sAktuelles_Bauen = event.replace('baue_', '')
      zeige_bauen(sAktuelles_Bauen)

  elif event == 'do_bauen':
      baue(sAktuelles_Bauen)

  elif event == 'stop_bauen':
      stoppe_bauen()

  elif event == 'reise_von':
      # Aktualisiere verfügbare Raumschiffe
      von_planet = values['reise_von']
      if von_planet:
          verfuegbare = get_verfuegbare_raumschiffe(von_planet)
          raumschiffe = list(verfuegbare.keys())
          window['reise_raumschiff'].update(values=raumschiffe, value='')

  elif event == 'reise_zu' or event == 'reise_raumschiff':
      # Aktualisiere Reise-Informationen
      von_planet = values['reise_von']
      zu_planet = values['reise_zu']
      raumschiff_typ = values['reise_raumschiff']

      if von_planet and zu_planet and raumschiff_typ:
          kann_reisen_result, grund = kann_reisen(von_planet, zu_planet, raumschiff_typ)
          if kann_reisen_result:
              entfernung = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
              kapazitaet = get_raumschiff_kapazitaet(raumschiff_typ)
              info_text = f"Entfernung: {entfernung} Zyklen\n"
              info_text += f"Kapazität: {kapazitaet['astronauten']} Astronauten, {kapazitaet['fracht']} Fracht"
              window['reise_info'].update(value=info_text)
          else:
              window['reise_info'].update(value=f"Nicht möglich: {grund}")

  elif event == 'starte_reise':
      # Radiobutton-Auswahl für Planeten und Raumschiff
      verfuegbare_planeten = ['Erde']
      if GAMESTATE['Planeten']['Mond']['entdeckt']:
          verfuegbare_planeten.append('Mond')
      if GAMESTATE['Planeten']['Mars']['entdeckt']:
          verfuegbare_planeten.append('Mars')
      von_planet = next((planet for planet in verfuegbare_planeten if values.get(f'reise_von_{planet}')), None)
      zu_planet = next((planet for planet in verfuegbare_planeten if values.get(f'reise_zu_{planet}')), None)
      raumschiff_typen = ['Mondlander', 'Rakete']
      raumschiff_typ = next((typ for typ in raumschiff_typen if values.get(f'reise_raumschiff_{typ}')), None)
      astronauten_anzahl = values['reise_astronauten']
      # Fracht zusammenstellen
      fracht_dict = {}
      for material in ['Eisenbarren', 'Werkzeug', 'Baumaterial']:
          anzahl = values.get(f'fracht_{material}', 0)
          if anzahl > 0:
              fracht_dict[material] = anzahl
      if von_planet and zu_planet and raumschiff_typ:
          starte_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict)

  elif event.startswith('mondmission_'):
    sAktuelle_Mondmission = event.replace('mondmission_', '')
    zeige_mondmission(sAktuelle_Mondmission)

  elif event == 'do_mondmission':
    starte_mondmission(sAktuelle_Mondmission)

  elif event == 'stop_mondmission':
    stoppe_mondmission()

  if event != '__TIMEOUT__':
    # Inventar nur aktualisieren wenn sich etwas geändert haben könnte
    if event in ['do_bauen', 'stop_bauen'] or event.startswith('baue_') or bBauen_aktiv:
        aktualisiere_inventar_anzeige()
        aktualisiere_raumschiff_anzeige()
        aktualisiere_inventar_statistiken()

  # print(f'{event = } {iCredits = }')

  # for x, y in GAMESTATE['Forschung'].items():
  #   print(x, y)
  # print('#' * 50)