import copy
import json
import logging
import time

import FreeSimpleGUI as sg

import config
from actions import ACTIONS
from materials import MATERIALS
from mining import MINING_EXPEDITIONEN
from science import SCIENCE
from shop import SHOP, SHOP_MATERIALIEN

# Configure logging - set to DEBUG for development, INFO for production
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

sg.theme('Dark Teal 6')

# See docs/ROADMAP.md for feature roadmap and TODO items

# Game timing
TICK_INTERVAL = 2  # Tick interval in seconds
letzter_tick = time.time()

# Save feedback timer
iSaveStatusTimer = 0

# Research state
bForschung_aktiv = False
iAktueller_Forschungsfortschritt = None
forschungs_queue = []  # Queue for planned research orders

# Building state
bBauen_aktiv = False
iAktueller_Baufortschritt = None
sAktuelles_Bauen = None
iMax_Bauen = None
iAnzahl_Bauen = 1  # Anzahl der aktuell im Bau befindlichen Items
bau_queue = []  # Queue for planned build orders

# Active missions
missionen_aktiv = []
MISSION_SLOTS = list(ACTIONS.keys())  # Fixed order for UI slot indices

# Active mining expeditions
mining_aktiv = []
MINING_SLOTS = 6  # Max parallel expeditions shown in UI

# Active probe flight (discovers new planets)
raumsonde_flug = None

# Planets in fixed order; Erde is always known
ALLE_PLANETEN = ['Erde', 'Mond', 'Mars']

# Materials that can be loaded as cargo on trips
FRACHT_MATERIALIEN = ['Eisenbarren', 'Werkzeug', 'Baumaterial']

# Earth jobs system - jobs that generate research points and credits
ERDE_JOBS = {
    'Laborarbeit': {
        'beschreibung': 'Wissenschaftler arbeiten im Labor und generieren Forschungspunkte.',
        'dauer': 3,
        'benötigt_arbeiter': 1,
        'belohnung': {'Forschungspunkte': 2}
    },
    'Bergbau': {
        'beschreibung': 'Arbeiter bauen Roheisen ab.',
        'dauer': 2,
        'benötigt_arbeiter': 2,
        'belohnung': {'Roheisen': 3}
    },
    'Wasseraufbereitung': {
        'beschreibung': 'Wasser wird aufbereitet und gesammelt.',
        'dauer': 2,
        'benötigt_arbeiter': 1,
        'belohnung': {'Wasser': 2}
    },
    'Staubsammlung': {
        'beschreibung': 'Staub wird für Baumaterial gesammelt.',
        'dauer': 2,
        'benötigt_arbeiter': 1,
        'belohnung': {'Staub': 2}
    },
}

# Active Earth jobs
erde_jobs_aktiv = []


class ErdArbeit:
    """Represents an active job on Earth."""
    def __init__(self, job_name):
        self.name = job_name
        self.fortschritt = 0
        self.max_fortschritt = ERDE_JOBS[job_name]['dauer']
        self.aktiv = True

    def tick(self):
        if self.aktiv:
            self.fortschritt += 1
            if self.fortschritt >= self.max_fortschritt:
                self.aktiv = False
                return True  # Job abgeschlossen
        return False



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


class MiningInstance:
    """Represents an active mining expedition on a planet."""
    def __init__(self, planet):
        self.planet = planet
        self.fortschritt = 0
        self.max_fortschritt = MINING_EXPEDITIONEN[planet]['dauer']
        self.aktiv = True

    def tick(self):
        if self.aktiv:
            self.fortschritt += 1
            if self.fortschritt >= self.max_fortschritt:
                self.aktiv = False
                return True
        return False


class RaumsondenFlug:
    """Represents an active probe flight that discovers new planets."""
    def __init__(self, fortschritt=0):
        self.fortschritt = fortschritt
        self.max_fortschritt = SCIENCE['Raumsonde']['dauer']
        self.aktiv = True

    def tick(self):
        if self.aktiv:
            self.fortschritt += 1
            if self.fortschritt >= self.max_fortschritt:
                self.aktiv = False
                return True
        return False


def merge_defaults(default, loaded):
  """Ergänzt fehlende Schlüssel aus dem Default-GAMESTATE (Savegame-Migration)."""
  for key, value in default.items():
    if key not in loaded:
      loaded[key] = copy.deepcopy(value)
    elif isinstance(value, dict) and isinstance(loaded[key], dict):
      merge_defaults(value, loaded[key])
  return loaded


def load_gamestate():
  logger.debug('load_gamestate()')
  from gamestate import GAMESTATE as DEFAULT_GAMESTATE
  try:
    with open(config.SAVEFILE, "r") as file:
      logger.debug('config.SAVEFILE gefunden')
      loaded = json.load(file)
      # Alte Spielstände um neue Schlüssel ergänzen
      return merge_defaults(copy.deepcopy(DEFAULT_GAMESTATE), loaded)
  except FileNotFoundError:
    logger.debug('GAMESTATE importiert')
    return copy.deepcopy(DEFAULT_GAMESTATE)

GAMESTATE = load_gamestate()
for _m in GAMESTATE.get('AktiveMissionen', []):
    if _m['name'] in ACTIONS:
        _mi = MissionInstance(_m['name'])
        _mi.fortschritt = _m['fortschritt']
        missionen_aktiv.append(_mi)
for _m in GAMESTATE.get('AktivesMining', []):
    if _m['planet'] in MINING_EXPEDITIONEN:
        _mi = MiningInstance(_m['planet'])
        _mi.fortschritt = _m['fortschritt']
        mining_aktiv.append(_mi)
_sonde = GAMESTATE.get('AktiveRaumsonde')
if _sonde:
    raumsonde_flug = RaumsondenFlug(fortschritt=_sonde.get('fortschritt', 0))
# Abgeschlossene Mondmissionen aus dem Spielstand in ACTIONS übernehmen
for _name, _daten in GAMESTATE.get('Mondmissionen', {}).items():
    if _name in ACTIONS:
        ACTIONS[_name]['erforscht'] = _daten.get('erforscht', False)
for x, y in GAMESTATE.items():
  logger.debug(f'{x}: {y}')

for x, y in SCIENCE.items():
  logger.debug(f'{x}: {y}')

iForschungspunkte = GAMESTATE['Forschungspunkte']

def dump_gamestate():
  logger.debug('dump_gamestate()')
  global iSaveStatusTimer
  GAMESTATE['Ticks'] = iTicks
  GAMESTATE['Credits'] = iCredits
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Log'] = lLog
  GAMESTATE['AktiveMissionen'] = [
      {'name': m.name, 'fortschritt': m.fortschritt}
      for m in missionen_aktiv
  ]
  GAMESTATE['AktivesMining'] = [
      {'planet': m.planet, 'fortschritt': m.fortschritt}
      for m in mining_aktiv
  ]
  GAMESTATE['AktiveReisen'] = [
      {
          'raumschiff_typ': r.raumschiff_typ,
          'von_planet': r.von_planet,
          'zu_planet': r.zu_planet,
          'astronauten': r.astronauten,
          'fracht': r.fracht,
          'start_tick': r.start_tick,
          'end_tick': r.end_tick,
      }
      for r in aktive_reisen if not r.abgeschlossen
  ]
  GAMESTATE['AktiveRaumsonde'] = (
      {'fortschritt': raumsonde_flug.fortschritt} if raumsonde_flug and raumsonde_flug.aktiv else None
  )
  with open(config.SAVEFILE, "w") as outfile:
    json.dump(GAMESTATE, outfile, indent=2)
  iSaveStatusTimer = 15
  try:
    window['save_status'].update(visible=True, value='Gespeichert')
  except (KeyError, NameError):
    pass  # Window not yet created

def zeige_Forschung(sAktuelle_Forschung):
  logger.debug(f'zeige_Forschung({sAktuelle_Forschung})')
  window['do_research'].update(visible=False)
  window['already_researched'].update(visible=False)

  window['desc_research'].update(visible=True, value=SCIENCE[sAktuelle_Forschung]['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f"Forschungsdauer: {SCIENCE[sAktuelle_Forschung]['dauer']} Zyklen")
  window['desc_costs'].update(visible=True, value=f"Forschungskosten: {SCIENCE[sAktuelle_Forschung]['kosten']}")
  erforschbar_nach = SCIENCE[sAktuelle_Forschung].get('erforschbar nach', '')
  if erforschbar_nach:
    status = '✓' if GAMESTATE['Forschung'][erforschbar_nach]['erforscht'] else '✗'
    window['desc_voraussetzung'].update(visible=True, value=f"Voraussetzung: {erforschbar_nach} {status}")
  else:
    window['desc_voraussetzung'].update(visible=True, value="Keine Voraussetzung")

  if SCIENCE[sAktuelle_Forschung]['kosten'] > iForschungspunkte:
    window['comment'].update(visible=True, value='Forschungspunkte reichen nicht aus')
    return
  else:
    window['comment'].update(visible=False, value='')

  bereits_erforscht = GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']
  if not bereits_erforscht:
    if not bForschung_aktiv:
      window['do_research'].update(visible=True)
      window['queue_research'].update(visible=False)
    else:
      window['do_research'].update(visible=False)
      window['queue_research'].update(visible=True)
  else:
    window['queue_research'].update(visible=False)

  window['already_researched'].update(visible=bereits_erforscht)

def aktualisiere_forschungs_buttons():
  """Aktualisiert Sichtbarkeit und Farbe aller Forschungs- und Werkstatt-Buttons."""
  for name, daten in SCIENCE.items():
    erforscht = GAMESTATE['Forschung'][name]['erforscht']
    erforschbar_nach = daten.get('erforschbar nach', '')
    sichtbar = not erforschbar_nach or GAMESTATE['Forschung'][erforschbar_nach]['erforscht']
    try:
      window[f'Erforsche {name}'].update(visible=sichtbar)
      if erforscht:
        window[f'Erforsche {name}'].update(button_color=('black', 'green'))
      window[f'img_{name}'].update(visible=erforscht)
      window[f'baue_{name}'].update(visible=erforscht)
    except KeyError:
      pass

def aktualisiere_bau_queue_anzeige():
  queue_text = '\n'.join(bau_queue) if bau_queue else "Keine Aufträge in der Warteschlange."
  try:
    window['bau_queue_anzeige'].update(value=queue_text)
  except KeyError:
    pass  # Falls Feld gerade nicht sichtbar ist

def aktualisiere_forschungs_queue_anzeige():
  queue_text = '\n'.join(forschungs_queue) if forschungs_queue else "Keine Aufträge in der Warteschlange."
  try:
    window['forschungs_queue_anzeige'].update(value=queue_text)
  except KeyError:
    pass

def forschungsauftrag_hinzufuegen(name):
  global forschungs_queue
  forschungs_queue.append(name)
  add2log(f"Forschungsauftrag '{name}' zur Warteschlange hinzugefügt")
  aktualisiere_forschungs_queue_anzeige()

def zeige_bauen(sAktuelles_Bauen):
  logger.debug('zeige_bauen()')
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

    # Produktionskette: Rohstoffe gesamt (nur wenn mind. ein direktes Material herstellbar ist)
    direkte = set(item['material'].keys())
    if any(m in GAMESTATE['Werkstatt'] for m in direkte):
      rohstoffe = berechne_rohstoffe(sAktuelles_Bauen)
      materialien_text += "\nRohstoffe gesamt:\n"
      for rohstoff, anzahl in rohstoffe.items():
        verfügbar = GAMESTATE['Inventar'].get(rohstoff, 0)
        status = '✓' if verfügbar >= anzahl else '✗'
        materialien_text += f"  {status} {rohstoff}: {anzahl} (verfügbar: {verfügbar})\n"

    window['desc_materialien'].update(value=materialien_text, visible=True)

    # Maximale Anzahl berechnen (limitiert durch verfügbare Materialien)
    max_anzahl = None
    for material, anzahl in item['material'].items():
      verfügbar = GAMESTATE['Inventar'].get(material, 0)
      mögliche = verfügbar // anzahl if anzahl > 0 else 999
      if max_anzahl is None or mögliche < max_anzahl:
        max_anzahl = mögliche
    max_anzahl = max(max_anzahl or 0, 0)

    # Spinner aktualisieren
    if max_anzahl > 0:
      spin_values = list(range(1, max_anzahl + 1))
      aktuell = window['anzahl_bauen'].get()
      try:
        aktuell = int(aktuell)
      except (ValueError, TypeError):
        aktuell = 1
      aktuell = min(max(aktuell, 1), max_anzahl)
      window['anzahl_bauen'].update(values=spin_values, value=aktuell, visible=True)
      window['label_anzahl_bauen'].update(visible=True)
    else:
      window['anzahl_bauen'].update(values=[1], value=1, visible=False)
      window['label_anzahl_bauen'].update(visible=False)

    # Prüfen ob alle Materialien für mindestens 1 Item verfügbar sind
    kann_bauen = max_anzahl >= 1

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

def berechne_rohstoffe(item_name, menge=1, rohstoffe=None):
  """Berechnet rekursiv alle Rohstoffe (nicht herstellbare Materialien) für ein Item."""
  if rohstoffe is None:
    rohstoffe = {}
  if item_name in GAMESTATE['Werkstatt']:
    for material, anzahl in GAMESTATE['Werkstatt'][item_name]['material'].items():
      berechne_rohstoffe(material, anzahl * menge, rohstoffe)
  else:
    rohstoffe[item_name] = rohstoffe.get(item_name, 0) + menge
  return rohstoffe

def bauauftrag_hinzufuegen(item_name):
  global bau_queue
  bau_queue.append(item_name)
  add2log(f"Bauauftrag '{item_name}' wurde zur Warteschlange hinzugefügt.")
  aktualisiere_bau_queue_anzeige()  # Neue Funktion, siehe unten

def baue(sAktuelles_Bauen):
  logger.debug('baue()')
  """Startet den Bau-Prozess"""
  global bBauen_aktiv, iAktueller_Baufortschritt, iMax_Bauen, iAnzahl_Bauen

  # Anzahl aus Spinner lesen
  try:
    iAnzahl_Bauen = int(window['anzahl_bauen'].get())
  except (ValueError, TypeError):
    iAnzahl_Bauen = 1
  iAnzahl_Bauen = max(iAnzahl_Bauen, 1)

  # Prüfen ob alle Materialien für die gewünschte Anzahl verfügbar sind
  item = GAMESTATE['Werkstatt'][sAktuelles_Bauen]
  for material, anzahl in item['material'].items():
    if GAMESTATE['Inventar'].get(material, 0) < anzahl * iAnzahl_Bauen:
      add2log(f"Nicht genug {material} zum Bauen von {iAnzahl_Bauen}x {sAktuelles_Bauen}")
      return

  # Materialien sofort abziehen (für alle Items auf einmal)
  for material, anzahl in item['material'].items():
    GAMESTATE['Inventar'][material] -= anzahl * iAnzahl_Bauen

  # Bau-Prozess starten (Dauer skaliert mit Anzahl)
  bBauen_aktiv = True
  iMax_Bauen = int(item['dauer'] / config.TICK) * iAnzahl_Bauen
  iAktueller_Baufortschritt = 0

  # UI aktualisieren
  window['do_bauen'].update(visible=False)
  window['bauen_unmöglich'].update(visible=False)
  window['anzahl_bauen'].update(visible=False)
  window['label_anzahl_bauen'].update(visible=False)
  window['progressbar_Bauen'].update(current_count=0, max=iMax_Bauen, visible=True)
  window['stop_bauen'].update(visible=True)

  # Inventar-Anzeige aktualisieren
  aktualisiere_inventar_anzeige()

  add2log(f"Baue {iAnzahl_Bauen}x '{sAktuelles_Bauen}' - Materialien verbraucht")

def beende_bauen(sAktuelles_Bauen):
  logger.debug('beende_bauen()')
  """Beendet den Bau-Prozess erfolgreich"""
  global bBauen_aktiv

  # Gebauten Gegenstand zum Inventar/Raumschiffe hinzufügen
  if sAktuelles_Bauen in ['Mondlander', 'Rakete']:
    # Raumschiffe zur Erde hinzufügen
    GAMESTATE['Raumschiffe']['Erde'][sAktuelles_Bauen]['Anzahl'] += iAnzahl_Bauen
    add2log(f"{iAnzahl_Bauen}x '{sAktuelles_Bauen}' erfolgreich gebaut - zur Erde hinzugefügt")
  else:
    # Andere Gegenstände ins Inventar
    if sAktuelles_Bauen not in GAMESTATE['Inventar']:
      GAMESTATE['Inventar'][sAktuelles_Bauen] = 0
    GAMESTATE['Inventar'][sAktuelles_Bauen] += iAnzahl_Bauen
    add2log(f"{iAnzahl_Bauen}x '{sAktuelles_Bauen}' erfolgreich gebaut - ins Inventar gelegt")

  # Siegbedingung: Weltraumstation fertiggestellt
  if sAktuelles_Bauen == 'Weltraumstation' and not GAMESTATE.get('Spiel_gewonnen'):
    GAMESTATE['Spiel_gewonnen'] = True
    add2log("*** SIEG! Die Weltraumstation ist fertiggestellt - du hast das Spiel gewonnen! ***")
    sg.popup_no_wait(
      'Glückwunsch!\n\n'
      'Die Weltraumstation ist fertiggestellt.\n'
      'Du hast das Spiel gewonnen!\n\n'
      'Du kannst gerne weiterspielen, forschen und das Sonnensystem erkunden.',
      title='Spiel gewonnen!',
      keep_on_top=True,
    )

  dump_gamestate()
  # Bau-Prozess beenden
  bBauen_aktiv = False
  window['progressbar_Bauen'].update(visible=False)
  window['stop_bauen'].update(visible=False)

  # UI vollständig aktualisieren
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_hq_anzeige()
  zeige_bauen(sAktuelles_Bauen)  # Erneut anzeigen für nächsten Bau
  aktualisiere_bau_queue_anzeige()


def stoppe_bauen():
  logger.debug('stoppe_bauen()')
  """Stoppt den Bau-Prozess und gibt Materialien zurück"""
  global bBauen_aktiv

  if bBauen_aktiv and sAktuelles_Bauen:
    item = GAMESTATE['Werkstatt'][sAktuelles_Bauen]

    # Berechne fertige und noch offene Items anhand des Fortschritts
    ticks_pro_item = int(item['dauer'] / config.TICK)
    fertige_items = iAktueller_Baufortschritt // ticks_pro_item if ticks_pro_item > 0 else 0
    fertige_items = min(fertige_items, iAnzahl_Bauen)
    offene_items = iAnzahl_Bauen - fertige_items

    # Fertige Items ins Inventar/Raumschiffe
    if fertige_items > 0:
      if sAktuelles_Bauen in ['Mondlander', 'Rakete']:
        GAMESTATE['Raumschiffe']['Erde'][sAktuelles_Bauen]['Anzahl'] += fertige_items
        add2log(f"{fertige_items}x '{sAktuelles_Bauen}' fertiggestellt")
      else:
        if sAktuelles_Bauen not in GAMESTATE['Inventar']:
          GAMESTATE['Inventar'][sAktuelles_Bauen] = 0
        GAMESTATE['Inventar'][sAktuelles_Bauen] += fertige_items
        add2log(f"{fertige_items}x '{sAktuelles_Bauen}' fertiggestellt")

    # Materialien für offene Items zurückgeben
    if offene_items > 0:
      for material, anzahl in item['material'].items():
        GAMESTATE['Inventar'][material] += anzahl * offene_items
      add2log(f"Materialien für {offene_items}x '{sAktuelles_Bauen}' zurückgegeben")

    bBauen_aktiv = False
    window['progressbar_Bauen'].update(visible=False)
    window['stop_bauen'].update(visible=False)

    dump_gamestate()
    aktualisiere_inventar_anzeige()
    aktualisiere_raumschiff_anzeige()
    zeige_bauen(sAktuelles_Bauen)

def erforsche(sAktuelle_Forschung):
  logger.debug('erforsche()')
  global bForschung_aktiv
  global iAktueller_Forschungsfortschritt
  global iMax_Forschung
  global iForschungspunkte
  kosten = SCIENCE[sAktuelle_Forschung]['kosten']
  if iForschungspunkte < kosten:
    add2log(f"Nicht genug Forschungspunkte für '{sAktuelle_Forschung}' (benötigt: {kosten})")
    return False
  iForschungspunkte -= kosten
  window['do_research'].update(visible=False)
  bForschung_aktiv = True
  iMax_Forschung = SCIENCE[sAktuelle_Forschung]['dauer'] / config.TICK
  iAktueller_Forschungsfortschritt = 0
  window['progressbar_Forschung'].update(current_count=0, max=iMax_Forschung)
  window['progressbar_Forschung'].update(visible=True)
  window['stop_research'].update(visible=True)
  return True

def get_materials_from_inventory():
  logger.debug('get_materials_from_inventory()')
  lMaterials = []
  for material, amount in GAMESTATE['Inventar'].items():
    lMaterials.append([sg.Text(material)])
  return lMaterials

def get_amounts_from_inventory():
  logger.debug('get_amounts_from_inventory()')
  lAmounts = []
  for material, amount in GAMESTATE['Inventar'].items():
    lAmounts.append([sg.Text(amount)])
  return lAmounts

def add2log(sString):
  logger.debug(f'add2log({sString})')
  global lLog
  global sLog
  lLog.append(f"{iTicks}\t{sString}")
  if len(lLog) > config.LOG_MAX_ENTRIES:
    lLog = lLog[-config.LOG_MAX_ENTRIES:]
  sLog = '\n'.join(lLog[::-1])
  window['Log'].update(value=sLog)

# NEW
def erstelle_inventar_layout():
  logger.debug('erstelle_inventar_layout()')
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

  # Dynamische Einträge für jedes Material (nur sichtbar wenn anzahl > 0)
  for material, anzahl in GAMESTATE['Inventar'].items():
    beschreibung = get_material_beschreibung(material)
    inventar_zeilen.append([
      sg.Column([
        [
          sg.Text(material, size=(20, 1), key=f'inv_name_{material}'),
          sg.Text(str(anzahl), size=(10, 1), key=f'inv_anzahl_{material}'),
          sg.Text(beschreibung, size=(35, 2), key=f'inv_desc_{material}', font=('Arial', 8)),
        ]
      ], key=f'inv_row_{material}', visible=anzahl > 0, pad=(0, 0))
    ])

  return inventar_zeilen

def get_material_beschreibung(material):
  logger.debug('get_material_beschreibung()')
  """Gibt eine Beschreibung für jedes Material zurück"""
  return MATERIALS.get(material, {'Beschreibung': f'Unbekanntes Material: {material}'}).get('Beschreibung', 'no description found')

def aktualisiere_inventar_anzeige():
  logger.debug('aktualisiere_inventar_anzeige()')
  """Aktualisiert die Inventar-Anzeige dynamisch"""
  for material, anzahl in GAMESTATE['Inventar'].items():
    try:
      window[f'inv_anzahl_{material}'].update(value=str(anzahl))
      window[f'inv_row_{material}'].update(visible=anzahl > 0)
    except KeyError:
      logger.debug(f"Material {material} nicht in Anzeige gefunden")
      pass

def aktualisiere_raumschiff_anzeige():
  logger.debug('aktualisiere_raumschiff_anzeige()')
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

    # Raumschiffe auf dem Mars (falls sichtbar)
    if GAMESTATE['Planeten']['Mars']['entdeckt']:
      mondlander_mars = GAMESTATE['Raumschiffe']['Mars']['Mondlander']['Anzahl']
      rakete_mars = GAMESTATE['Raumschiffe']['Mars']['Rakete']['Anzahl']

      window['raumschiffe_mars'].update(
        value=f"Mondlander: {mondlander_mars}, Raketen: {rakete_mars}"
      )

  except KeyError:
    logger.debug("Raumschiff-Anzeige konnte nicht aktualisiert werden")

def erstelle_raumschiff_uebersicht():
  logger.debug('erstelle_raumschiff_uebersicht()')
  """Erstellt eine Übersicht aller Raumschiffe (Mond/Mars werden bei Entdeckung eingeblendet)"""
  mond = GAMESTATE['Planeten']['Mond']['entdeckt']
  mars = GAMESTATE['Planeten']['Mars']['entdeckt']
  return [
    [sg.Text('Raumschiffe auf der Erde:', font=('Arial', 10, 'bold'))],
    [sg.Text('', key='raumschiffe_erde', size=(50, 1))],
    [sg.Text('Raumschiffe auf dem Mond:', font=('Arial', 10, 'bold'), key='raumschiffe_mond_label', visible=mond)],
    [sg.Text('', key='raumschiffe_mond', size=(50, 1), visible=mond)],
    [sg.Text('Raumschiffe auf dem Mars:', font=('Arial', 10, 'bold'), key='raumschiffe_mars_label', visible=mars)],
    [sg.Text('', key='raumschiffe_mars', size=(50, 1), visible=mars)],
  ]

def berechne_inventar_statistiken():
  logger.debug('berechne_inventar_statistiken()')
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
  logger.debug('aktualisiere_inventar_statistiken()')
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
    logger.debug('__init__()')
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
    logger.debug('fortschritt()')
    if aktuelle_tick >= self.end_tick:
      return 100
    return min(100, ((aktuelle_tick - self.start_tick) / self.dauer) * 100)

  def ist_abgeschlossen(self, aktuelle_tick):
    logger.debug('ist_abgeschlossen()')
    return aktuelle_tick >= self.end_tick

def get_verfuegbare_raumschiffe(planet):
  logger.debug('get_verfuegbare_raumschiffe()')
  """Gibt verfügbare Raumschiffe auf einem Planeten zurück"""
  verfuegbare = {}
  for raumschiff_typ in ['Mondlander', 'Rakete']:
    anzahl = GAMESTATE['Raumschiffe'][planet][raumschiff_typ]['Anzahl']
    if anzahl > 0:
      verfuegbare[raumschiff_typ] = anzahl
  return verfuegbare

def get_raumschiff_kapazitaet(raumschiff_typ):
  logger.debug('get_raumschiff_kapazitaet()')
  """Gibt die Kapazitäten eines Raumschiffs zurück"""
  eintrag = SCIENCE.get(raumschiff_typ, {})
  astronauten = eintrag.get('Sitzplätze', 0)
  fracht = eintrag.get('Frachtplätze', 0)
  # Reichweite kann optional gesetzt werden, falls im SCIENCE vorhanden
  reichweite = eintrag.get('reichweite', 0)
  return {'astronauten': astronauten, 'fracht': fracht, 'reichweite': reichweite}

def kann_reisen(von_planet, zu_planet, raumschiff_typ):
  logger.debug('kann_reisen()')
  """Prüft ob eine Reise möglich ist"""
  # Prüfen ob Zielplanet entdeckt ist (Erde ist immer bekannt)
  if zu_planet != 'Erde' and not GAMESTATE['Planeten'][zu_planet].get('entdeckt', False):
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
  logger.debug('starte_reise()')
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
  global iForschungspunkte
  logger.debug('beende_reise()')
  """Beendet eine Reise und bringt Raumschiff ans Ziel"""
  # Raumschiff am Zielort hinzufügen (am Start bereits beim Reisestart abgezogen)
  GAMESTATE['Raumschiffe'][reise.zu_planet][reise.raumschiff_typ]['Anzahl'] += 1
  # Astronauten am Zielplanet hinzufügen (am Start bereits beim Reisestart abgezogen)
  GAMESTATE['Astronauten'][reise.zu_planet] += reise.astronauten
  # Fracht am Zielplanet ins Inventar
  for material, anzahl in reise.fracht.items():
    GAMESTATE['Inventar'][material] = GAMESTATE['Inventar'].get(material, 0) + anzahl
  add2log(f"Reise abgeschlossen: {reise.raumschiff_typ} ist auf {reise.zu_planet} angekommen "
          f"({reise.astronauten} Astronauten, Fracht: {reise.fracht if reise.fracht else 'keine'})")

  # Spezielle Aktionen je nach Zielplanet
  if reise.zu_planet == 'Mond' and not GAMESTATE['Planeten']['Mond']['entdeckt']:
    GAMESTATE['Planeten']['Mond']['entdeckt'] = True
    add2log("Mond entdeckt!")
    iForschungspunkte += config.MOON_DISCOVERY_RESEARCH_POINTS

  if reise.zu_planet == 'Mars' and not GAMESTATE['Planeten']['Mars']['entdeckt']:
    GAMESTATE['Planeten']['Mars']['entdeckt'] = True
    add2log("Mars entdeckt!")
    iForschungspunkte += config.MARS_DISCOVERY_RESEARCH_POINTS

  reise.abgeschlossen = True
  dump_gamestate()
  aktualisiere_alle_anzeigen()

def verwalte_aktive_reisen():
  logger.debug('verwalte_aktive_reisen()')
  """Verwaltet alle aktiven Reisen"""
  global aktive_reisen
  for reise in aktive_reisen[:]:  # Copy der Liste für sichere Iteration
    if not reise.abgeschlossen and reise.ist_abgeschlossen(iTicks):
      beende_reise(reise)

  # Abgeschlossene Reisen entfernen
  aktive_reisen = [r for r in aktive_reisen if not r.abgeschlossen]

def aktualisiere_reise_anzeige():
  logger.debug('aktualisiere_reise_anzeige()')
  """Aktualisiert die Anzeige der aktiven Reisen (Reisen-Tab und HQ-Übersicht)"""
  reise_text = ""
  for reise in aktive_reisen:
    if not reise.abgeschlossen:
      fortschritt = reise.fortschritt(iTicks)
      verbleibend = max(0, reise.end_tick - iTicks)
      reise_text += f"{reise.raumschiff_typ}: {reise.von_planet} → {reise.zu_planet} ({fortschritt:.0f}%, noch {verbleibend} Zyklen)\n"
  if not reise_text:
    reise_text = "Keine aktiven Reisen"
  for key in ('aktive_reisen', 'aktive_reisen_uebersicht'):
    try:
      window[key].update(value=reise_text)
    except KeyError:
      pass  # Element existiert noch nicht

def aktualisiere_alle_anzeigen():
  logger.debug('aktualisiere_alle_anzeigen()')
  """Aktualisiert alle UI-Elemente"""
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_reise_anzeige()
  aktualisiere_planeten_anzeige()
  aktualisiere_tab_sichtbarkeit()
  aktualisiere_entdeckungs_ui()
  aktualisiere_hq_anzeige()

def aktualisiere_entdeckungs_ui():
  """Blendet Elemente ein, die von entdeckten Planeten abhängen."""
  mond = GAMESTATE['Planeten']['Mond']['entdeckt']
  mars = GAMESTATE['Planeten']['Mars']['entdeckt']
  sichtbarkeiten = {
    'astronauten_mond': mond,
    'astronauten_mars': mars,
    'raumschiffe_mond_label': mond,
    'raumschiffe_mond': mond,
    'raumschiffe_mars_label': mars,
    'raumschiffe_mars': mars,
    'tab_mond': mond,
    'tab_mars': mars,
    'reise_von_Mond': mond,
    'reise_zu_Mond': mond,
    'reise_von_Mars': mars,
    'reise_zu_Mars': mars,
    'mining_mars_title': mars,
    'mining_mars_desc': mars,
    'mining_mars_req': mars,
    'mining_mars_kosten': mars,
    'mining_mars_belohnung': mars,
    'mining_starte_Mars': mars,
  }
  for key, sichtbar in sichtbarkeiten.items():
    try:
      window[key].update(visible=sichtbar)
    except Exception:
      pass

def aktualisiere_hq_anzeige():
  """Aktualisiert Raumsonden-Button und -Status im HQ."""
  alles_entdeckt = GAMESTATE['Planeten']['Mond']['entdeckt'] and GAMESTATE['Planeten']['Mars']['entdeckt']
  sonden_im_inventar = GAMESTATE['Inventar'].get('Raumsonde', 0)
  flug_aktiv = raumsonde_flug is not None and raumsonde_flug.aktiv
  try:
    window['hq_sonde_hinweis'].update(visible=not alles_entdeckt)
    window['starte_raumsonde'].update(visible=sonden_im_inventar > 0 and not flug_aktiv)
    if flug_aktiv:
      window['raumsonde_status'].update(
        visible=True,
        value=f"Raumsonde unterwegs: {raumsonde_flug.fortschritt}/{raumsonde_flug.max_fortschritt} Zyklen"
      )
    elif sonden_im_inventar == 0 and not alles_entdeckt:
      window['raumsonde_status'].update(
        visible=True,
        value="Keine Raumsonde im Inventar - erforsche und baue eine in der Werkstatt."
      )
    else:
      window['raumsonde_status'].update(visible=False)
  except KeyError:
    pass

def starte_raumsonde():
  """Startet eine Raumsonde aus dem Inventar, um neue Planeten zu entdecken."""
  global raumsonde_flug
  logger.debug('starte_raumsonde()')
  if raumsonde_flug is not None and raumsonde_flug.aktiv:
    add2log("Es ist bereits eine Raumsonde unterwegs")
    return
  if GAMESTATE['Inventar'].get('Raumsonde', 0) < 1:
    add2log("Keine Raumsonde im Inventar - erforsche und baue eine in der Werkstatt")
    return
  GAMESTATE['Inventar']['Raumsonde'] -= 1
  raumsonde_flug = RaumsondenFlug()
  add2log("Raumsonde gestartet! Sie erkundet den Weltraum...")
  aktualisiere_inventar_anzeige()
  aktualisiere_hq_anzeige()

def beende_raumsondenflug():
  """Wertet einen abgeschlossenen Raumsondenflug aus: entdeckt Mond, dann Mars."""
  global raumsonde_flug, iForschungspunkte
  logger.debug('beende_raumsondenflug()')
  if not GAMESTATE['Planeten']['Mond']['entdeckt']:
    GAMESTATE['Planeten']['Mond']['entdeckt'] = True
    iForschungspunkte += config.MOON_DISCOVERY_RESEARCH_POINTS
    add2log(f"Die Raumsonde hat den MOND entdeckt! +{config.MOON_DISCOVERY_RESEARCH_POINTS} Forschungspunkte")
    add2log("Neue Bereiche freigeschaltet: Planeten, Reisen, Mondmissionen, Mining")
  elif not GAMESTATE['Planeten']['Mars']['entdeckt']:
    GAMESTATE['Planeten']['Mars']['entdeckt'] = True
    iForschungspunkte += config.MARS_DISCOVERY_RESEARCH_POINTS
    add2log(f"Die Raumsonde hat den MARS entdeckt! +{config.MARS_DISCOVERY_RESEARCH_POINTS} Forschungspunkte")
  else:
    iForschungspunkte += 15
    add2log("Die Raumsonde hat wertvolle Daten gesammelt: +15 Forschungspunkte")
  raumsonde_flug = None
  dump_gamestate()
  aktualisiere_alle_anzeigen()

def aktualisiere_tab_sichtbarkeit():
  """Blendet Tabs ein/aus je nach Spielfortschritt."""
  mond = GAMESTATE['Planeten']['Mond']['entdeckt']
  werkstatt = any(v['erforscht'] for v in GAMESTATE['Forschung'].values())
  try:
    window['tab_Werkstatt'].update(visible=werkstatt)
    window['tab_Planeten'].update(visible=mond)
    window['tab_Reisen'].update(visible=mond)
    window['tab_Mondmissionen'].update(visible=mond)
    window['tab_Mining'].update(visible=mond)
  except Exception:
    pass

def aktualisiere_planeten_anzeige():
  logger.debug('aktualisiere_planeten_anzeige()')
  """Aktualisiert die Astronauten-Anzeige auf den Planeten"""
  try:
    # HQ Tab
    window['astronauten_erde'].update(value=f"Astronauten auf der Erde: {GAMESTATE['Astronauten']['Erde']}")
    window['planet_erde_astronauten'].update(value=f"Astronauten auf der Erde {GAMESTATE['Astronauten']['Erde']}")

    if GAMESTATE['Planeten']['Mond']['entdeckt']:
      window['astronauten_mond'].update(value=f"Astronauten auf dem Mond: {GAMESTATE['Astronauten']['Mond']}")
      window['planet_mond_astronauten'].update(value=f"Astronauten auf dem Mond {GAMESTATE['Astronauten']['Mond']}")
    if GAMESTATE['Planeten']['Mars']['entdeckt']:
      window['astronauten_mars'].update(value=f"Astronauten auf dem Mars: {GAMESTATE['Astronauten']['Mars']}")
      window['planet_mars_astronauten'].update(value=f"Astronauten auf dem Mars {GAMESTATE['Astronauten']['Mars']}")
  except KeyError:
    pass

def erstelle_reise_interface():
  logger.debug('erstelle_reise_interface()')
  """Erstellt das Interface für Reisen"""

  # Radiobuttons für alle Planeten anlegen; unentdeckte werden erst später eingeblendet
  def planet_sichtbar(planet):
    return planet == 'Erde' or GAMESTATE['Planeten'][planet]['entdeckt']

  planet_radio_von = [sg.Radio(planet, 'reise_von', key=f'reise_von_{planet}', enable_events=True, visible=planet_sichtbar(planet)) for planet in ALLE_PLANETEN]
  planet_radio_zu = [sg.Radio(planet, 'reise_zu', key=f'reise_zu_{planet}', enable_events=True, visible=planet_sichtbar(planet)) for planet in ALLE_PLANETEN]
  # Raumschiff-Typen
  raumschiff_typen = ['Mondlander', 'Rakete']
  raumschiff_radio = [sg.Radio(typ, 'reise_raumschiff', key=f'reise_raumschiff_{typ}', enable_events=True) for typ in raumschiff_typen]
  # Fracht-Spinner (Wertebereiche werden beim Öffnen des Tabs aktualisiert)
  material_rows = [[sg.Text(f'{mat}:'), sg.Spin([i for i in range(0, GAMESTATE['Inventar'].get(mat, 0)+1)], initial_value=0, key=f'fracht_{mat}')] for mat in FRACHT_MATERIALIEN]
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

def get_reise_auswahl(values):
  """Liest die aktuell ausgewählten Reise-Optionen aus den Radiobuttons."""
  von_planet = next((p for p in ALLE_PLANETEN if values.get(f'reise_von_{p}')), None)
  zu_planet = next((p for p in ALLE_PLANETEN if values.get(f'reise_zu_{p}')), None)
  raumschiff_typ = next((t for t in ['Mondlander', 'Rakete'] if values.get(f'reise_raumschiff_{t}')), None)
  return von_planet, zu_planet, raumschiff_typ

def aktualisiere_reise_info(values):
  """Zeigt Informationen zur aktuell ausgewählten Reise an."""
  von_planet, zu_planet, raumschiff_typ = get_reise_auswahl(values)
  if not (von_planet and zu_planet and raumschiff_typ):
    return
  if von_planet == zu_planet:
    window['reise_info'].update(value="Start- und Zielplanet sind identisch")
    return
  kann_reisen_result, grund = kann_reisen(von_planet, zu_planet, raumschiff_typ)
  if kann_reisen_result:
    entfernung = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
    kapazitaet = get_raumschiff_kapazitaet(raumschiff_typ)
    verfuegbar = GAMESTATE['Raumschiffe'][von_planet][raumschiff_typ]['Anzahl']
    info_text = f"Entfernung: {entfernung} Zyklen\n"
    info_text += f"Kapazität: {kapazitaet['astronauten']} Astronauten, {kapazitaet['fracht']} Fracht\n"
    info_text += f"Verfügbar auf {von_planet}: {verfuegbar}x {raumschiff_typ}"
    window['reise_info'].update(value=info_text)
  else:
    window['reise_info'].update(value=f"Nicht möglich: {grund}")

def aktualisiere_fracht_spinner():
  """Passt die Wertebereiche der Fracht-Spinner an den Inventarbestand an."""
  for mat in FRACHT_MATERIALIEN:
    bestand = GAMESTATE['Inventar'].get(mat, 0)
    try:
      aktuell = int(window[f'fracht_{mat}'].get())
    except (ValueError, TypeError, KeyError):
      aktuell = 0
    try:
      window[f'fracht_{mat}'].update(values=[i for i in range(0, bestand + 1)], value=min(aktuell, bestand))
    except KeyError:
      pass

# Neues Tab für Reisen
lTab_Reisen = erstelle_reise_interface()


# ============ EARTH JOBS SYSTEM ============

def starte_erde_job(job_name):
    """Startet einen Erd-Job."""
    global erde_jobs_aktiv
    logger.debug(f'starte_erde_job({job_name})')
    
    job_info = ERDE_JOBS[job_name]
    benötigte_arbeiter = job_info.get('benötigt_arbeiter', 1)
    
    # Prüfen ob genug Arbeiter verfügbar
    verfuegbare_arbeiter = GAMESTATE['Arbeiter']['Erde']
    
    # Zähle bereits beschäftigte Arbeiter
    beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) for j in erde_jobs_aktiv if j.aktiv)
    freie_arbeiter = verfuegbare_arbeiter - beschäftigte
    
    if freie_arbeiter < benötigte_arbeiter:
        add2log(f"Nicht genug freie Arbeiter für '{job_name}' (benötigt: {benötigte_arbeiter}, frei: {freie_arbeiter})")
        return False
    
    # Job starten
    neuer_job = ErdArbeit(job_name)
    erde_jobs_aktiv.append(neuer_job)
    add2log(f"Erd-Job '{job_name}' gestartet")
    aktualisiere_erde_jobs_anzeige()
    return True


def beende_erde_job(job):
    """Beendet einen Erd-Job und gibt Belohnung."""
    global iForschungspunkte
    logger.debug(f'beende_erde_job({job.name})')
    
    job_info = ERDE_JOBS[job.name]
    belohnung = job_info.get('belohnung', {})
    
    for ressource, menge in belohnung.items():
        if ressource == 'Forschungspunkte':
            iForschungspunkte += menge
        elif ressource in GAMESTATE['Inventar']:
            GAMESTATE['Inventar'][ressource] += menge
        else:
            GAMESTATE['Inventar'][ressource] = menge
    
    belohnung_text = ', '.join([f"{menge} {ressource}" for ressource, menge in belohnung.items()])
    add2log(f"Erd-Job '{job.name}' abgeschlossen! Belohnung: {belohnung_text}")
    aktualisiere_inventar_anzeige()


def aktualisiere_erde_jobs_anzeige():
    """Aktualisiert die Anzeige der aktiven Erd-Jobs."""
    try:
        if not erde_jobs_aktiv:
            window['aktive_erde_jobs'].update(value="Keine laufenden Jobs.")
        else:
            text = ""
            for job in erde_jobs_aktiv:
                if job.aktiv:
                    text += f"• {job.name}: {job.fortschritt}/{job.max_fortschritt} Zyklen\n"
            window['aktive_erde_jobs'].update(value=text if text else "Keine laufenden Jobs.")
        
        # Aktualisiere freie Arbeiter
        beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) for j in erde_jobs_aktiv if j.aktiv)
        freie = GAMESTATE['Arbeiter']['Erde'] - beschäftigte
        window['freie_arbeiter'].update(value=f"Freie Arbeiter: {freie} / {GAMESTATE['Arbeiter']['Erde']}")
    except KeyError:
        pass


def erstelle_erde_jobs_tab():
    """Erstellt das Tab für Erd-Jobs."""
    logger.debug('erstelle_erde_jobs_tab()')
    
    job_buttons = []
    for job_name, job_info in ERDE_JOBS.items():
        belohnung_text = ', '.join([f"{menge} {ressource}" for ressource, menge in job_info['belohnung'].items()])
        job_buttons.append([
            sg.Button(job_name, key=f'start_erde_job_{job_name}'),
            sg.Text(f"({job_info.get('benötigt_arbeiter', 1)} Arbeiter, {job_info['dauer']} Zyklen)")
        ])
        job_buttons.append([
            sg.Text(f"  {job_info['beschreibung']}  →  {belohnung_text}", size=(60, 2), font=('Arial', 8))
        ])

    return [
        [sg.Text('Arbeiten auf der Erde', font=('Arial', 12, 'bold'))],
        [sg.Text('Setze Arbeiter ein um Ressourcen und Forschungspunkte zu verdienen.')],
        [sg.HorizontalSeparator()],
        [sg.Text('', key='freie_arbeiter', font=('Arial', 10, 'bold'))],
        [sg.HorizontalSeparator()],
        [sg.Text('Verfügbare Jobs:', font=('Arial', 10, 'bold'))],
        *job_buttons,
        [sg.HorizontalSeparator()],
        [sg.Text('Laufende Jobs:', font=('Arial', 10, 'bold'))],
        [sg.Multiline('', key='aktive_erde_jobs', size=(50, 5), disabled=True)],
    ]


# Tab für Erd-Jobs erstellen
lTab_ErdeJobs = erstelle_erde_jobs_tab()



def aktualisiere_missionen_anzeige():
  if not GAMESTATE['Planeten']['Mond']['entdeckt']:
    return
  active_by_name = {m.name: m for m in missionen_aktiv}
  try:
    for i, name in enumerate(MISSION_SLOTS):
      m = active_by_name.get(name)
      if m:
        pct = int(m.fortschritt / m.max_fortschritt * 100) if m.max_fortschritt > 0 else 0
        label = f"{name}: {m.fortschritt}/{m.max_fortschritt} Zyklen"
        window[f'slot_{i}_text'].update(value=label, visible=True)
        window[f'slot_{i}_bar'].update(current_count=pct, visible=True)
        window[f'slot_{i}_stop'].update(visible=True)
      else:
        window[f'slot_{i}_text'].update(visible=False)
        window[f'slot_{i}_bar'].update(visible=False)
        window[f'slot_{i}_stop'].update(visible=False)
  except (KeyError, NameError):
    pass

def zeige_mondmission(sAktuelle_Mission):
  logger.debug('zeige_mondmission()')
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
  mission_already_running = any(m.name == sAktuelle_Mission for m in missionen_aktiv)
  if kann_mission and not mission_already_running:
    window['do_mondmission'].update(visible=True)
    window['mondmission_unmöglich'].update(visible=False)
  else:
    window['do_mondmission'].update(visible=False)
    if mission_already_running:
      window['mondmission_unmöglich'].update(visible=True, value="Mission läuft bereits")
    elif grund:
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
  GAMESTATE.setdefault('Mondmissionen', {}).setdefault(missionsname, {})['erforscht'] = True
  add2log(f"Mission '{missionsname}' abgeschlossen!")
  dump_gamestate()

def stoppe_mondmission(mission_name: str):
  logger.debug(f'stoppe_mondmission({mission_name})')
  """Stoppt eine Mondmission und gibt Ressourcen zurück"""
  global iCredits
  mission_inst = next((m for m in missionen_aktiv if m.name == mission_name), None)
  if not mission_inst:
    return
  mission = ACTIONS[mission_name]
  iCredits += mission['kosten']
  for key, value in mission.items():
    if key.startswith('benötigt_') and key != 'benötigt_astronauten':
      ressource = key.replace('benötigt_', '').title()
      GAMESTATE['Inventar'][ressource] += value
  missionen_aktiv.remove(mission_inst)
  aktualisiere_inventar_anzeige()
  aktualisiere_missionen_anzeige()
  add2log(f"Mondmission '{mission_name}' abgebrochen - Ressourcen zurückgegeben")

def starte_mining(planet):
    """Startet eine Mining-Expedition auf dem angegebenen Planeten."""
    global iCredits
    exp = MINING_EXPEDITIONEN[planet]
    astronauten = GAMESTATE['Astronauten'].get(planet, 0)
    if astronauten < exp['benötigt_astronauten']:
        add2log(f"Mining {planet}: Nicht genug Astronauten ({astronauten}/{exp['benötigt_astronauten']})")
        aktualisiere_mining_anzeige()
        return
    for key, wert in exp.items():
        if key.startswith('benötigt_') and key != 'benötigt_astronauten':
            ressource = key.replace('benötigt_', '').title()
            if GAMESTATE['Inventar'].get(ressource, 0) < wert:
                add2log(f"Mining {planet}: Nicht genug {ressource} ({GAMESTATE['Inventar'].get(ressource, 0)}/{wert})")
                aktualisiere_mining_anzeige()
                return
    for key, wert in exp.items():
        if key.startswith('benötigt_') and key != 'benötigt_astronauten':
            ressource = key.replace('benötigt_', '').title()
            GAMESTATE['Inventar'][ressource] -= wert
    mining_aktiv.append(MiningInstance(planet))
    add2log(f"Mining-Expedition auf dem {planet} gestartet")
    aktualisiere_inventar_anzeige()
    aktualisiere_mining_anzeige()


def beende_mining(mining_inst):
    """Schließt eine Mining-Expedition ab und vergibt Belohnungen."""
    global iForschungspunkte
    exp = MINING_EXPEDITIONEN[mining_inst.planet]
    for ressource, menge in exp['belohnung'].items():
        if ressource == 'Forschungspunkte':
            iForschungspunkte += menge
        else:
            GAMESTATE['Inventar'][ressource] = GAMESTATE['Inventar'].get(ressource, 0) + menge
    add2log(f"Mining-Expedition auf dem {mining_inst.planet} abgeschlossen! Ressourcen erhalten.")
    aktualisiere_inventar_anzeige()
    dump_gamestate()


def stoppe_mining(slot_index):
    """Bricht eine Mining-Expedition ab und erstattet die Kosten."""
    if slot_index >= len(mining_aktiv):
        return
    mining_inst = mining_aktiv[slot_index]
    exp = MINING_EXPEDITIONEN[mining_inst.planet]
    for key, wert in exp.items():
        if key.startswith('benötigt_') and key != 'benötigt_astronauten':
            ressource = key.replace('benötigt_', '').title()
            GAMESTATE['Inventar'][ressource] = GAMESTATE['Inventar'].get(ressource, 0) + wert
    mining_aktiv.pop(slot_index)
    add2log(f"Mining-Expedition auf dem {mining_inst.planet} abgebrochen - Ressourcen zurückgegeben")
    aktualisiere_inventar_anzeige()
    aktualisiere_mining_anzeige()


def aktualisiere_mining_anzeige():
    """Aktualisiert die Fortschrittsanzeige aller aktiven Mining-Expeditionen."""
    if not GAMESTATE['Planeten']['Mond']['entdeckt']:
        return
    try:
        for i in range(MINING_SLOTS):
            if i < len(mining_aktiv):
                mi = mining_aktiv[i]
                pct = int(mi.fortschritt / mi.max_fortschritt * 100) if mi.max_fortschritt > 0 else 0
                label = f"{mi.planet}: {mi.fortschritt}/{mi.max_fortschritt} Zyklen"
                window[f'mining_slot_{i}_text'].update(value=label, visible=True)
                window[f'mining_slot_{i}_bar'].update(current_count=pct, visible=True)
                window[f'mining_slot_{i}_stop'].update(visible=True)
            else:
                window[f'mining_slot_{i}_text'].update(visible=False)
                window[f'mining_slot_{i}_bar'].update(visible=False)
                window[f'mining_slot_{i}_stop'].update(visible=False)
    except (KeyError, NameError):
        pass


def erstelle_mining_tab():
    """Erstellt das Tab für Mining-Expeditionen."""
    mond_exp = MINING_EXPEDITIONEN['Mond']
    mars_exp = MINING_EXPEDITIONEN['Mars']

    mond_belohnung = ', '.join(f"{r} +{m}" for r, m in mond_exp['belohnung'].items())
    mars_belohnung = ', '.join(f"{r} +{m}" for r, m in mars_exp['belohnung'].items())

    mars_sichtbar = GAMESTATE['Planeten']['Mars']['entdeckt']

    linke_spalte = [
        [sg.Text('Mond-Expedition', font=('Arial', 11, 'bold'))],
        [sg.Text(mond_exp['beschreibung'], size=(35, 2))],
        [sg.Text(f"Astronauten auf Mond nötig: {mond_exp['benötigt_astronauten']}")],
        [sg.Text(f"Kosten: 1 Werkzeug")],
        [sg.Text(f"Belohnung: {mond_belohnung}")],
        [sg.Button('Expedition starten', key='mining_starte_Mond')],
        [sg.HorizontalSeparator()],
        [sg.Text('Mars-Expedition', font=('Arial', 11, 'bold'), visible=mars_sichtbar, key='mining_mars_title')],
        [sg.Text(mars_exp['beschreibung'], size=(35, 2), visible=mars_sichtbar, key='mining_mars_desc')],
        [sg.Text(f"Astronauten auf Mars nötig: {mars_exp['benötigt_astronauten']}", visible=mars_sichtbar, key='mining_mars_req')],
        [sg.Text(f"Kosten: 1 Werkzeug, 1 Baumaterial", visible=mars_sichtbar, key='mining_mars_kosten')],
        [sg.Text(f"Belohnung: {mars_belohnung}", visible=mars_sichtbar, key='mining_mars_belohnung')],
        [sg.Button('Expedition starten', key='mining_starte_Mars', visible=mars_sichtbar)],
    ]

    rechte_spalte = [
        [sg.Text('Laufende Expeditionen:', font=('Arial', 10, 'bold'))],
        *[
            [
                sg.Text('', key=f'mining_slot_{i}_text', size=(35, 1), visible=False),
                sg.ProgressBar(100, orientation='h', size=(12, 15), key=f'mining_slot_{i}_bar', visible=False),
                sg.Button('■', key=f'mining_slot_{i}_stop', visible=False, tooltip='Expedition abbrechen'),
            ]
            for i in range(MINING_SLOTS)
        ],
    ]

    return [
        [sg.Text('Mining — Ressourcen-Expeditionen', font=('Arial', 12, 'bold'))],
        [sg.HorizontalSeparator()],
        [
            sg.Column(linke_spalte, vertical_alignment='top'),
            sg.VerticalSeparator(),
            sg.Column(rechte_spalte, vertical_alignment='top'),
        ],
    ]


# Neue Tab für Mondmissionen
def erstelle_mondmission_tab():
  logger.debug('erstelle_mondmission_tab()')
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
        [sg.Text('Laufende Missionen:', font=('Arial', 10, 'bold'))],
        *[
          [
            sg.Text('', key=f'slot_{i}_text', size=(40, 1), visible=False),
            sg.ProgressBar(100, orientation='h', size=(12, 15), key=f'slot_{i}_bar', visible=False),
            sg.Button('■', key=f'slot_{i}_stop', visible=False, tooltip='Mission abbrechen'),
          ]
          for i in range(len(MISSION_SLOTS))
        ],
      ], vertical_alignment='top'),
    ],
  ]

# Fügen Sie das neue Tab zur LAYOUT-Definition hinzu:
lTab_Mondmissionen = erstelle_mondmission_tab()
lTab_Mining = erstelle_mining_tab()

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
  [sg.Text('Sende eine Raumsonde in den Weltraum, um etwas zu entdecken', key='hq_sonde_hinweis',
           visible=not (GAMESTATE['Planeten']['Mond']['entdeckt'] and GAMESTATE['Planeten']['Mars']['entdeckt']))],
  [sg.Button('Starte Raumsonde', key='starte_raumsonde', visible=GAMESTATE['Inventar'].get('Raumsonde', 0) > 0)],
  [sg.Text('', key='raumsonde_status', size=(60, 1), visible=False)],

  [sg.HorizontalSeparator()],
  # Aktive Reisen (Übersicht)
  [sg.Text('Aktive Reisen:', font=('Arial', 10, 'bold'))],
  [sg.Text('', key='aktive_reisen_uebersicht', size=(60, 3))],
]

lTab_Forschung = [
  [
    sg.Column([
      [
        sg.Button(button_text=name, key=f'Erforsche {name}', visible=name == 'Eisenbarren' or GAMESTATE['Forschung'][data['erforschbar nach']]['erforscht'] or
                  (data.get('erforschbar nach', '') and GAMESTATE['Forschung'].get(data.get('erforschbar nach', ''), {}).get('erforscht', False))),
        sg.Image('images/checkmark.png', visible=GAMESTATE['Forschung'][name]['erforscht'], key=f'img_{name}')
      ]
      for name, data in SCIENCE.items()
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='desc_research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [sg.Text('', key='desc_costs', visible=False)],
      [sg.Text('', key='desc_voraussetzung', visible=False)],
      [sg.Text('', key='comment', visible=False)],
      [
        sg.Button('Erforschen', key='do_research', visible=False),
        sg.Text('erforscht', key='already_researched', visible=False)
      ],
      [
        sg.ProgressBar(0, orientation='h', size=(20, 20), key='progressbar_Forschung', visible=False),
        sg.Button('Erforschen stoppen', key='stop_research', visible=False),
      ],
      [sg.Button('In Queue stellen', key='queue_research', visible=False)],
      [sg.Text('Warteschlange:', font=('Arial', 10, 'bold'))],
      [sg.Multiline('Keine Aufträge in der Warteschlange.', key='forschungs_queue_anzeige', size=(30, 3), disabled=True)],
      [sg.Button('Storniere Forschungsauftrag', key='storniere_forschungsauftrag')],
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
      [sg.Text('', key='desc_materialien', size=(40, 12), visible=False)],
      [sg.Text('Anzahl:', key='label_anzahl_bauen', visible=False), sg.Spin(values=[1], initial_value=1, key='anzahl_bauen', size=(5, 1), visible=False), sg.Button('Bauen', key='do_bauen', visible=False)],
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
  logger.debug('erstelle_inventar_tab()')
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
  [sg.Text(f"Astronauten auf der Erde {GAMESTATE['Astronauten']['Erde']}", key='planet_erde_astronauten')],
]

lTab_Mond = [
  [sg.Text('Mond')],
  [sg.Text(f"Astronauten auf dem Mond {GAMESTATE['Astronauten']['Mond']}", key='planet_mond_astronauten')],
]

lTab_Mars = [
  [sg.Text('Mars')],
  [sg.Text(f"Astronauten auf dem Mars {GAMESTATE['Astronauten']['Mars']}", key='planet_mars_astronauten')],
]

tabs_planets = [
    [sg.Tab('Erde', lTab_Erde, key='tab_erde')],
    [sg.Tab('Mond', lTab_Mond, key='tab_mond', visible=GAMESTATE['Planeten']['Mond']['entdeckt'])],
    [sg.Tab('Mars', lTab_Mars, key='tab_mars', visible=GAMESTATE['Planeten']['Mars']['entdeckt'])],
]

lTab_Planets = [
  [
    sg.TabGroup(
      tabs_planets,
      expand_x=True,
      expand_y=True,
    )
  ]
]

# ============ SHOP SYSTEM ============

# Angebot zusammenstellen: Materialien + Raumschiffe
SHOP_ITEMS = {}
for _name, _daten in SHOP_MATERIALIEN.items():
  SHOP_ITEMS[_name] = {
    'kosten': _daten['Kosten'],
    'beschreibung': _daten['Beschreibung'],
    'typ': 'material',
  }
for _name, _daten in SHOP.items():
  SHOP_ITEMS[_name] = {
    'kosten': _daten['Kosten'],
    'beschreibung': (f"Fertiges Raumschiff, wird auf der Erde geliefert.\n"
                     f"Sitzplätze: {_daten['Sitze']}, Frachtplätze: {_daten['Frachtplätze']}, "
                     f"Reichweite: {_daten['Reichweite']}"),
    'typ': 'raumschiff',
  }

sAktueller_Shop_Artikel = None

def shop_artikel_kaufbar(name):
  """Prüft ob ein Shop-Artikel aktuell gekauft werden kann."""
  item = SHOP_ITEMS[name]
  if item['typ'] == 'raumschiff' and not GAMESTATE['Forschung'].get(name, {}).get('erforscht', False):
    return False, f"'{name}' muss zuerst erforscht werden"
  if iCredits < item['kosten']:
    return False, f"Nicht genug Credits (Preis: {item['kosten']})"
  return True, ''

def zeige_shop_artikel(name):
  """Zeigt Beschreibung, Preis und Kaufen-Button für einen Shop-Artikel."""
  logger.debug(f'zeige_shop_artikel({name})')
  item = SHOP_ITEMS[name]
  window['shop_beschreibung'].update(visible=True, value=f"{name}\n\n{item['beschreibung']}")
  window['shop_preis'].update(visible=True, value=f"Preis: {item['kosten']} Credits pro Stück")
  kaufbar, grund = shop_artikel_kaufbar(name)
  window['shop_label_anzahl'].update(visible=kaufbar)
  window['shop_anzahl'].update(visible=kaufbar)
  window['do_kaufen'].update(visible=kaufbar)
  window['shop_kommentar'].update(visible=not kaufbar, value=grund)

def kaufe_shop_artikel(name):
  """Kauft einen Shop-Artikel gegen Credits."""
  global iCredits
  logger.debug(f'kaufe_shop_artikel({name})')
  item = SHOP_ITEMS[name]
  kaufbar, grund = shop_artikel_kaufbar(name)
  if not kaufbar:
    add2log(f"Kauf nicht möglich: {grund}")
    zeige_shop_artikel(name)
    return
  try:
    anzahl = max(1, int(window['shop_anzahl'].get()))
  except (ValueError, TypeError):
    anzahl = 1
  gesamt = item['kosten'] * anzahl
  if iCredits < gesamt:
    add2log(f"Nicht genug Credits für {anzahl}x {name} ({gesamt} Credits)")
    zeige_shop_artikel(name)
    return
  iCredits -= gesamt
  if item['typ'] == 'raumschiff':
    GAMESTATE['Raumschiffe']['Erde'][name]['Anzahl'] += anzahl
  else:
    GAMESTATE['Inventar'][name] = GAMESTATE['Inventar'].get(name, 0) + anzahl
  add2log(f"{anzahl}x {name} gekauft für {gesamt} Credits")
  window['tCredits'].update(f'Credits: {iCredits}')
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_hq_anzeige()
  zeige_shop_artikel(name)

lTab_Shop = [
  [sg.Text('Shop', font=('Arial', 12, 'bold'))],
  [sg.Text('Kaufe Materialien und Raumschiffe gegen Credits.')],
  [sg.HorizontalSeparator()],
  [
    sg.Column([
      [sg.Button(button_text=name, key=f'shop_{name}', size=(15, 1))]
      for name in SHOP_ITEMS
    ], vertical_alignment='top'),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='shop_beschreibung', visible=False, size=(45, 5))],
      [sg.Text('', key='shop_preis', visible=False)],
      [
        sg.Text('Anzahl:', key='shop_label_anzahl', visible=False),
        sg.Spin([i for i in range(1, 101)], initial_value=1, key='shop_anzahl', size=(5, 1), visible=False),
        sg.Button('Kaufen', key='do_kaufen', visible=False),
      ],
      [sg.Text('', key='shop_kommentar', visible=False, text_color='red')],
    ], vertical_alignment='top'),
  ],
]

lLog = GAMESTATE['Log']
sLog = '\n'.join(lLog[::-1])
logger.debug(f'Game log: {sLog}')

_mond = GAMESTATE['Planeten']['Mond']['entdeckt']
_werkstatt_freigeschaltet = any(v['erforscht'] for v in GAMESTATE['Forschung'].values())

tabs = [
  [sg.Tab('HQ', lTab_HQ, key='tab_HQ')],
  [sg.Tab('Arbeit', lTab_ErdeJobs, key='tab_Arbeit')],
  [sg.Tab('Forschung', lTab_Forschung, key='tab_Forschung')],
  [sg.Tab('Werkstatt', lTab_Werkstatt, key='tab_Werkstatt', visible=_werkstatt_freigeschaltet)],
  [sg.Tab('Inventar', lTab_Inventory, key='tab_Inventar')],
  [sg.Tab('Shop', lTab_Shop, key='tab_Shop')],
  [sg.Tab('Planeten', lTab_Planets, key='tab_Planeten', visible=_mond)],
  [sg.Tab('Reisen', lTab_Reisen, key='tab_Reisen', visible=_mond)],
  [sg.Tab('Mondmissionen', lTab_Mondmissionen, key='tab_Mondmissionen', visible=_mond)],
  [sg.Tab('Mining', lTab_Mining, key='tab_Mining', visible=_mond)],
]

LAYOUT = [
  [sg.Menu(menu_def)],
  [
    [
      sg.Text(text='Cycle:', key='tCycles'),
      sg.Text(text='Credits:', key='tCredits'),
      sg.Text(text='Forschungspunkte:', key='tForschungspunkte'),
      sg.Text('', key='save_status', text_color='green', visible=False),
    ],
    sg.Column([
      [sg.TabGroup(
      tabs,
      expand_x=True, expand_y=True, change_submits=True, enable_events=True, key='TabGroup_Main', tab_location='top')]
    ]),
    sg.Column([[sg.Image('images/TAB_HQ.png', key='img_Spalte3')]])
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
logger.debug(f'{iForschungspunkte = }')
inventory = GAMESTATE['Inventar']
sAktuelle_Forschung = list(SCIENCE.keys())[0]

# Gespeicherte Reisen wiederherstellen (benötigt iTicks)
for _r in GAMESTATE.get('AktiveReisen', []):
  _reise = Reise(_r['raumschiff_typ'], _r['von_planet'], _r['zu_planet'],
                 _r['astronauten'], _r['fracht'], len(aktive_reisen))
  _reise.start_tick = _r['start_tick']
  _reise.end_tick = _r['end_tick']
  aktive_reisen.append(_reise)

window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True, finalize=True)

# Bei Spielstart einmalig ausführen:
aktualisiere_alle_anzeigen()
aktualisiere_erde_jobs_anzeige()
aktualisiere_missionen_anzeige()
aktualisiere_mining_anzeige()
aktualisiere_forschungs_buttons()

sAktuelle_Mondmission = None  # Aktuell im UI ausgewählte Mission
while True:
  event, values = window.read(timeout=100)  # kurzer timeout!
  current_time = time.time()

  # Echtzeit-Tick-Handling
  if current_time - letzter_tick >= TICK_INTERVAL:
    iTicks += 1
    logger.debug(f'Cycle: {iTicks}')
    logger.debug(f'Forschungspunkte: {iForschungspunkte}')
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
        dump_gamestate()

        # Update UI elements for completed research
        window['progressbar_Forschung'].update(visible=False)
        window['stop_research'].update(visible=False)
        window['already_researched'].update(visible=True)
        aktualisiere_forschungs_buttons()
        aktualisiere_tab_sichtbarkeit()

    # Forschungs-Queue-Handling: Wenn keine Forschung läuft, aber etwas in der Queue ist → Starte nächste Forschung
    if not bForschung_aktiv and len(forschungs_queue) > 0:
      naechste_forschung = forschungs_queue[0]
      if GAMESTATE['Forschung'][naechste_forschung]['erforscht']:
        # Bereits erforscht - aus der Queue entfernen
        forschungs_queue.pop(0)
        aktualisiere_forschungs_queue_anzeige()
      elif iForschungspunkte >= SCIENCE[naechste_forschung]['kosten']:
        sAktuelle_Forschung = forschungs_queue.pop(0)
        erforsche(sAktuelle_Forschung)
        aktualisiere_forschungs_queue_anzeige()

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

    # Aktive Reisen verwalten
    if aktive_reisen:
      verwalte_aktive_reisen()

    # Raumsondenflug verwalten
    if raumsonde_flug is not None and raumsonde_flug.aktiv:
      if raumsonde_flug.tick():
        beende_raumsondenflug()
      else:
        aktualisiere_hq_anzeige()

    for mission in missionen_aktiv[:]:  # Kopie der Liste, da ggf. Missionen entfernt werden
      if mission.aktiv:
        abgeschlossen = mission.tick()
        if abgeschlossen:
          beende_mondmission(mission.name)
          missionen_aktiv.remove(mission)
    aktualisiere_missionen_anzeige()

    # Mining expeditions processing
    for mi in mining_aktiv[:]:
        if mi.aktiv:
            abgeschlossen = mi.tick()
            if abgeschlossen:
                beende_mining(mi)
                mining_aktiv.remove(mi)
    aktualisiere_mining_anzeige()

    # Earth Jobs processing
    for job in erde_jobs_aktiv[:]:
      if job.aktiv:
        abgeschlossen = job.tick()
        if abgeschlossen:
          beende_erde_job(job)
          erde_jobs_aktiv.remove(job)
    aktualisiere_erde_jobs_anzeige()

  # Reise-Anzeige regelmäßig aktualisieren
    aktualisiere_reise_anzeige()

    if iTicks % config.CREDITS_EXTRA_TICKS == 0:
      iCredits += config.CREDITS_EXTRA

    if iTicks % config.SCIENCE_POINTS_EXTRA_TICKS == 0:
      iForschungspunkte += config.SCIENCE_POINTS_EXTRA

    if iTicks % config.AUTOSAVE_INTERVAL == 0:
      dump_gamestate()

    if iSaveStatusTimer > 0:
      iSaveStatusTimer -= 1
      if iSaveStatusTimer == 0:
        window['save_status'].update(visible=False)

  if event in (sg.WINDOW_CLOSED, 'Exit'):
    dump_gamestate()
    break

  def safe_update_image(image_key):
    """Safely updates the main image with fallback."""
    # Map of keys to their corresponding image filenames (without .png)
    image_map = {
        'tab_HQ': 'TAB_HQ',
        'tab_Arbeit': 'TAB_HQ', # Fallback to HQ for now
        'tab_Forschung': 'TAB_FORSCHUNG',
        'tab_Inventar': 'TAB_INVENTAR',
        'tab_Planeten': 'TAB_PLANETEN',
        'tab_Shop': 'TAB_SHOP',
        'tab_Werkstatt': 'TAB_WERKSTATT',
        'tab_Reisen': 'TAB_REISEN',
        'tab_Mondmissionen': 'TAB_MONDMISSIONEN',
        'tab_Mining': 'TAB_PLANETEN',
        'HQ': 'TAB_HQ',
        'Forschung': 'TAB_FORSCHUNG',
        'Inventar': 'TAB_INVENTAR',
        'Planeten': 'TAB_PLANETEN',
        'Shop': 'TAB_SHOP'
    }
    
    image_to_load = image_map.get(image_key, 'TAB_HQ')
    image_path = f"images/{image_to_load}.png"
    
    try:
      window['img_Spalte3'].update(filename=image_path)
    except Exception as e:
      logger.warning(f"Failed to update image for {image_key} ({image_path}): {e}")
      try:
        window['img_Spalte3'].update(filename="images/TAB_HQ.png")
      except:
        pass

  if event == 'TabGroup_Main' and values['TabGroup_Main'] == 'tab_Inventar':
    aktualisiere_inventar_anzeige()
    aktualisiere_raumschiff_anzeige()
    aktualisiere_inventar_statistiken()

  if event == 'TabGroup_Main':
    current_tab = values['TabGroup_Main']
    safe_update_image(current_tab)

    if current_tab == 'tab_Forschung':
      zeige_Forschung(sAktuelle_Forschung)
    elif current_tab == 'tab_Reisen':
      aktualisiere_fracht_spinner()
      aktualisiere_reise_anzeige()

  elif event in ['HQ', 'Forschung', 'Inventar', 'Planeten', 'Shop']:
    tab_map = {
        'HQ': 'tab_HQ',
        'Forschung': 'tab_Forschung',
        'Inventar': 'tab_Inventar',
        'Planeten': 'tab_Planeten',
        'Shop': 'tab_Shop'
    }
    target_tab = tab_map.get(event)
    window[target_tab].select()
    safe_update_image(event)

  elif event.startswith('Erforsche '):
    sAktuelle_Forschung = event.split(' ', 1)[1]
    zeige_Forschung(sAktuelle_Forschung)

  elif event == 'do_research':
    add2log(f"Erforsche '{sAktuelle_Forschung}'")
    erforsche(sAktuelle_Forschung)

  elif event == 'stop_research':
    window['progressbar_Forschung'].update(visible=False)
    window['stop_research'].update(visible=False)
    window['do_research'].update(visible=True)
    if bForschung_aktiv:
      iForschungspunkte += SCIENCE[sAktuelle_Forschung]['kosten']
      add2log(f"Forschung von '{sAktuelle_Forschung}' gestoppt - Forschungspunkte zurückerstattet")
    bForschung_aktiv = False

  elif event == 'queue_research':
    forschungsauftrag_hinzufuegen(sAktuelle_Forschung)

  elif event == 'storniere_forschungsauftrag':
    if forschungs_queue:
      removed = forschungs_queue.pop()
      add2log(f"Forschungsauftrag '{removed}' storniert")
      aktualisiere_forschungs_queue_anzeige()

  elif event == 'starte_bauen':
    add2log(f"Baue '{sAktuelles_Bauen}'")
    baue(sAktuelles_Bauen)

  elif event == 'stop_bauen':
    stoppe_bauen()

  elif event == 'storniere_bauauftrag':
    if bau_queue:
      canceled = bau_queue.pop(0)
      add2log(f"Bauauftrag '{canceled}' aus der Warteschlange entfernt.")
      aktualisiere_bau_queue_anzeige()
    else:
      add2log("Keine Bauaufträge zu stornieren.")

  # Earth Jobs event handling
  elif event and event.startswith('start_erde_job_'):
    job_name = event.replace('start_erde_job_', '')
    if job_name in ERDE_JOBS:
      starte_erde_job(job_name)


  elif event == 'Save':
    dump_gamestate()
    add2log("Spielstand erfolgreich gespeichert!")

  elif event == 'Load':
    GAMESTATE = load_gamestate()
    iTicks = GAMESTATE['Ticks']
    iCredits = GAMESTATE['Credits']
    iForschungspunkte = GAMESTATE['Forschungspunkte']
    lLog = GAMESTATE['Log']
    # Laufende UI-Vorgänge zurücksetzen (nicht gespeicherte Forschung/Bau verfällt)
    bForschung_aktiv = False
    bBauen_aktiv = False
    forschungs_queue.clear()
    bau_queue.clear()
    window['progressbar_Forschung'].update(visible=False)
    window['stop_research'].update(visible=False)
    window['progressbar_Bauen'].update(visible=False)
    window['stop_bauen'].update(visible=False)
    # Laufende Vorgänge aus dem Spielstand wiederherstellen
    missionen_aktiv.clear()
    for _m in GAMESTATE.get('AktiveMissionen', []):
      if _m['name'] in ACTIONS:
        _mi = MissionInstance(_m['name'])
        _mi.fortschritt = _m['fortschritt']
        missionen_aktiv.append(_mi)
    mining_aktiv.clear()
    for _m in GAMESTATE.get('AktivesMining', []):
      if _m['planet'] in MINING_EXPEDITIONEN:
        _mi = MiningInstance(_m['planet'])
        _mi.fortschritt = _m['fortschritt']
        mining_aktiv.append(_mi)
    aktive_reisen.clear()
    for _r in GAMESTATE.get('AktiveReisen', []):
      _reise = Reise(_r['raumschiff_typ'], _r['von_planet'], _r['zu_planet'],
                     _r['astronauten'], _r['fracht'], len(aktive_reisen))
      _reise.start_tick = _r['start_tick']
      _reise.end_tick = _r['end_tick']
      aktive_reisen.append(_reise)
    _sonde = GAMESTATE.get('AktiveRaumsonde')
    raumsonde_flug = RaumsondenFlug(fortschritt=_sonde.get('fortschritt', 0)) if _sonde else None
    for _name, _daten in GAMESTATE.get('Mondmissionen', {}).items():
      if _name in ACTIONS:
        ACTIONS[_name]['erforscht'] = _daten.get('erforscht', False)
    # Alle Anzeigen auffrischen
    window['tCycles'].update(f'Cycle: {iTicks}')
    window['tCredits'].update(f'Credits: {iCredits}')
    window['tForschungspunkte'].update(f'Forschungspunkte: {iForschungspunkte}')
    aktualisiere_alle_anzeigen()
    aktualisiere_erde_jobs_anzeige()
    aktualisiere_missionen_anzeige()
    aktualisiere_mining_anzeige()
    aktualisiere_forschungs_buttons()
    aktualisiere_forschungs_queue_anzeige()
    aktualisiere_bau_queue_anzeige()
    add2log("Spielstand erfolgreich geladen!")

  elif event == 'refreshwindow':
    logger.debug('window.refresh()')
    logger.debug(SCIENCE[sAktuelle_Forschung])
    window.refresh()

  elif event.startswith('baue_'):
      sAktuelles_Bauen = event.replace('baue_', '')
      zeige_bauen(sAktuelles_Bauen)

  elif event == 'do_bauen':
      baue(sAktuelles_Bauen)

  elif event == 'stop_bauen':
      stoppe_bauen()

  elif event.startswith(('reise_von_', 'reise_zu_', 'reise_raumschiff_')):
      aktualisiere_reise_info(values)

  elif event == 'starte_reise':
      von_planet, zu_planet, raumschiff_typ = get_reise_auswahl(values)
      try:
          astronauten_anzahl = int(values.get('reise_astronauten', 0) or 0)
      except (ValueError, TypeError):
          astronauten_anzahl = 0
      # Fracht zusammenstellen
      fracht_dict = {}
      for material in FRACHT_MATERIALIEN:
          try:
              anzahl = int(values.get(f'fracht_{material}', 0) or 0)
          except (ValueError, TypeError):
              anzahl = 0
          if anzahl > 0:
              fracht_dict[material] = anzahl
      if von_planet and zu_planet and raumschiff_typ:
          if von_planet == zu_planet:
              add2log("Start- und Zielplanet sind identisch")
          elif starte_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict):
              aktualisiere_alle_anzeigen()
              aktualisiere_fracht_spinner()
              aktualisiere_reise_info(values)
      else:
          add2log("Bitte Startplanet, Zielplanet und Raumschiff auswählen")

  elif event == 'reise_abbrechen':
      # Reise-Formular zurücksetzen
      for _p in ALLE_PLANETEN:
          window[f'reise_von_{_p}'].update(value=False)
          window[f'reise_zu_{_p}'].update(value=False)
      for _t in ['Mondlander', 'Rakete']:
          window[f'reise_raumschiff_{_t}'].update(value=False)
      window['reise_astronauten'].update(value=0)
      for _mat in FRACHT_MATERIALIEN:
          window[f'fracht_{_mat}'].update(value=0)
      window['reise_info'].update(value='')

  elif event == 'starte_raumsonde':
      starte_raumsonde()

  elif event.startswith('shop_'):
      sAktueller_Shop_Artikel = event.replace('shop_', '')
      zeige_shop_artikel(sAktueller_Shop_Artikel)

  elif event == 'do_kaufen':
      if sAktueller_Shop_Artikel:
          kaufe_shop_artikel(sAktueller_Shop_Artikel)

  elif event.startswith('mondmission_'):
    sAktuelle_Mondmission = event.replace('mondmission_', '')
    zeige_mondmission(sAktuelle_Mondmission)

  elif event == 'do_mondmission':
    starte_mondmission(sAktuelle_Mondmission)

  elif any(event == f'slot_{i}_stop' for i in range(len(MISSION_SLOTS))):
    for i, name in enumerate(MISSION_SLOTS):
      if event == f'slot_{i}_stop':
        stoppe_mondmission(name)
        break

  elif event == 'mining_starte_Mond':
    starte_mining('Mond')

  elif event == 'mining_starte_Mars':
    starte_mining('Mars')

  elif any(event == f'mining_slot_{i}_stop' for i in range(MINING_SLOTS)):
    for i in range(MINING_SLOTS):
      if event == f'mining_slot_{i}_stop':
        stoppe_mining(i)
        break

  if event != '__TIMEOUT__':
    # Inventar nur aktualisieren wenn sich etwas geändert haben könnte
    if event in ['do_bauen', 'stop_bauen'] or event.startswith('baue_') or bBauen_aktiv:
        aktualisiere_inventar_anzeige()
        aktualisiere_raumschiff_anzeige()
        aktualisiere_inventar_statistiken()

  # logger.debug(f'{event = } {iCredits = }')

  # for x, y in GAMESTATE['Forschung'].items():
  #   print(x, y)
  # print('#' * 50)