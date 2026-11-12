import copy
import logging
import time

import FreeSimpleGUI as sg

import achievements
import config
import saveslots
import travel_rules
import tutorial
from actions import ACTIONS
from gamestate import GAMESTATE as DEFAULT_GAMESTATE
from materials import MATERIALS
from mining import MINING_EXPEDITIONEN
from science import SCIENCE
from shop import (
    SHOP,
    SHOP_MATERIALIEN,
    VERKAUFSPREISE,
    ist_verkaufbar,
    verkaufbare_materialien,
    verkaufe,
    verkaufspreis,
)

# Configure logging - set to DEBUG for development, INFO for production
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

sg.theme('Dark Teal 6')

# Gut lesbare Akzentfarben auf dem dunklen Theme-Hintergrund
# ('green'/'red' sind auf Petrol kaum zu erkennen).
FARBE_OK = '#8EF0A4'
FARBE_FEHLER = '#FF9E9E'
FARBE_HINWEIS = '#FFE08A'
FARBE_ERFORSCHT = ('black', '#6CCB7F')

# Game timing
TICK_INTERVAL = config.TICK_INTERVAL  # Tick interval in seconds
letzter_tick = time.time()

# Save feedback timer
iSaveStatusTimer = 0

# Slot, in den Autosave und Beenden schreiben (wird beim Laden/Speichern gesetzt)
aktiver_slot = saveslots.gemerkter_slot()

# Forschung: `sAktuelle_Forschung` ist nur die Auswahl im UI,
# `sLaufende_Forschung` der tatsächlich laufende Auftrag.
bForschung_aktiv = False
sLaufende_Forschung = None
iAktueller_Forschungsfortschritt = 0
iMax_Forschung = 0
forschungs_queue = []  # Namen geplanter Forschungen

# Werkstatt: `sAktuelles_Bauen` ist die Auswahl im UI, `sLaufender_Bau` der Auftrag.
bBauen_aktiv = False
sLaufender_Bau = None
sAktuelles_Bauen = None
iAktueller_Baufortschritt = 0
iMax_Bauen = 0
iAnzahl_Bauen = 1  # Stückzahl des laufenden Auftrags
bau_queue = []  # Geplante Bauaufträge: {'name': ..., 'anzahl': ...}

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

# Materials that can be loaded as cargo on trips. Cargo lands in the storage
# (Lager) of the destination planet. Missions, mining and departing ships
# consume from the storage of their planet, and yields end up there as well.
FRACHT_MATERIALIEN = ['Werkzeug', 'Baumaterial', 'Treibstoff', 'Wasser',
                      'Mondgestein', 'Seltene_Mineralien', 'Gold', 'Roheisen', 'Staub']

# Rewards that are knowledge or permanent upgrades rather than goods: they take
# effect everywhere at once and are kept in the inventory instead of a storage.
IMMATERIELLE_BELOHNUNGEN = {
    'Mondbasen Bauplan', 'Mondstation_Modul', 'Astronaut_Erfahrung',
    'Lebenserhaltung_Upgrade', 'Kommunikations_Upgrade',
}

# Startplanet, der im Reise-Formular gewählt ist (für die Fracht-Spinner)
sReise_von = None

# Items tracked in GAMESTATE['Raumschiffe'] instead of GAMESTATE['Inventar'].
# Recipes may reference them (the Weltraumstation needs 5 Mondlander), so
# stock lookups have to consult the right pool.
RAUMSCHIFF_TYPEN = ['Mondlander', 'Rakete']

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
        self.max_fortschritt = mining_dauer(planet)
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


def fortschrittsbalken(aktuell, maximum, breite=10):
  """Kleiner Text-Fortschrittsbalken für Multiline-/Text-Anzeigen, z.B. '▰▰▰▱▱▱▱▱▱▱'."""
  if maximum <= 0:
    return '▱' * breite
  gefuellt = max(0, min(breite, round(aktuell / maximum * breite)))
  return '▰' * gefuellt + '▱' * (breite - gefuellt)


def get_bestand(material, planet='Erde'):
  """Bestand eines Materials - egal ob es im Inventar oder als Raumschiff geführt wird."""
  if material in RAUMSCHIFF_TYPEN:
    return GAMESTATE['Raumschiffe'][planet][material]['Anzahl']
  return GAMESTATE['Inventar'].get(material, 0)


def aendere_bestand(material, menge, planet='Erde'):
  """Verändert den Bestand eines Materials um `menge` (kann negativ sein)."""
  if material in RAUMSCHIFF_TYPEN:
    GAMESTATE['Raumschiffe'][planet][material]['Anzahl'] += menge
  else:
    GAMESTATE['Inventar'][material] = GAMESTATE['Inventar'].get(material, 0) + menge


def lager(planet):
  """Materialvorrat eines Planeten: das Inventar auf der Erde, sonst das Lager."""
  if planet == 'Erde':
    return GAMESTATE['Inventar']
  return GAMESTATE.setdefault('Lager', {}).setdefault(planet, {})


def vergib_belohnung(planet, belohnung):
  """Verbucht eine Belohnung, die auf `planet` anfällt.

  Güter landen im Vorrat des Planeten und müssen von dort abgeholt werden.
  Forschungspunkte, Credits und Upgrades wirken sofort.
  """
  global iForschungspunkte, iCredits
  vorrat = lager(planet)
  for name, menge in belohnung.items():
    if name == 'Forschungspunkte':
      iForschungspunkte += menge
    elif name == 'Credits':
      iCredits += menge
      achievements.zaehle(GAMESTATE, 'credits_verdient', menge)
    elif name in IMMATERIELLE_BELOHNUNGEN:
      GAMESTATE['Inventar'][name] = GAMESTATE['Inventar'].get(name, 0) + menge
    else:
      vorrat[name] = vorrat.get(name, 0) + menge


def formatiere_mengen(mengen):
  """'3 Werkzeug, 1 Baumaterial' - oder 'leer'."""
  teile = [f'{menge} {name}' for name, menge in mengen.items() if menge]
  return ', '.join(teile) if teile else 'leer'


def material_bedarf(eintrag):
  """Materialbedarf einer Mission/Expedition aus ihren 'benötigt_*'-Schlüsseln.

  'benötigt_astronauten' ist kein Material und wird ausgelassen.
  """
  return {
    key[len('benötigt_'):].title(): wert
    for key, wert in eintrag.items()
    if key.startswith('benötigt_') and key != 'benötigt_astronauten'
  }


def gebundene_astronauten(planet):
  """Astronauten, die auf einem Planeten in Missionen oder Expeditionen stecken."""
  gebunden = sum(
    MINING_EXPEDITIONEN[m.planet].get('benötigt_astronauten', 0)
    for m in mining_aktiv if m.planet == planet
  )
  if planet == 'Mond':
    gebunden += sum(ACTIONS[m.name].get('benötigt_astronauten', 0) for m in missionen_aktiv)
  return gebunden


def freie_astronauten(planet):
  """Astronauten auf einem Planeten, die gerade nichts zu tun haben."""
  return GAMESTATE['Astronauten'].get(planet, 0) - gebundene_astronauten(planet)


def mission_abgeschlossen(name):
  """Wurde diese Mondmission schon abgeschlossen?"""
  return GAMESTATE.get('Mondmissionen', {}).get(name, {}).get('erforscht', False)


def mining_dauer(planet):
  """Dauer einer Expedition; Mondstation-Module verkürzen Mond-Expeditionen."""
  dauer = MINING_EXPEDITIONEN[planet]['dauer']
  if planet == 'Mond':
    module = GAMESTATE['Inventar'].get('Mondstation_Modul', 0)
    dauer = max(config.MINING_MIN_DAUER, dauer - module * config.MOON_MODULE_MINING_TICKS)
  return dauer


def mining_belohnung(planet):
  """Ertrag einer Expedition; Astronauten-Erfahrung erhöht den Hauptertrag."""
  belohnung = dict(MINING_EXPEDITIONEN[planet]['belohnung'])
  bonus = min(GAMESTATE['Inventar'].get('Astronaut_Erfahrung', 0), config.EXPERIENCE_MINING_BONUS_MAX)
  if bonus > 0 and belohnung:
    haupt = next(iter(belohnung))
    belohnung[haupt] += bonus
  return belohnung


def bekannte_materialien():
  """Alle Materialien, die im Spielverlauf auftauchen können.

  Wird für das Inventar-Layout gebraucht: Zeilen werden einmalig beim Start
  angelegt, deshalb müssen auch Materialien dabei sein, die man erst später
  findet (Mining-, Missions- und Ereignisbelohnungen).
  """
  namen = set(GAMESTATE['Inventar'])
  namen.update(MATERIALS)
  namen.update(GAMESTATE['Werkstatt'])
  for exp in MINING_EXPEDITIONEN.values():
    namen.update(exp.get('belohnung', {}))
  for mission in ACTIONS.values():
    namen.update(mission.get('belohnung', {}))
  for job in ERDE_JOBS.values():
    namen.update(job.get('belohnung', {}))
  for ereignis in travel_rules.REISE_EREIGNISSE:
    namen.update(ereignis.get('effekt', {}).get('material', {}))
  # Nicht-Materialien und Raumschiffe (haben eine eigene Übersicht) herausfiltern
  namen.discard('Forschungspunkte')
  namen.discard('Credits')
  namen.difference_update(RAUMSCHIFF_TYPEN)
  return sorted(namen)


def merge_defaults(default, loaded):
  """Ergänzt fehlende Schlüssel aus dem Default-GAMESTATE (Savegame-Migration)."""
  for key, value in default.items():
    if key not in loaded:
      loaded[key] = copy.deepcopy(value)
    elif isinstance(value, dict) and isinstance(loaded[key], dict):
      merge_defaults(value, loaded[key])
  return loaded


def neuer_spielstand():
  """Frischer Spielstand für ein neues Spiel."""
  return copy.deepcopy(DEFAULT_GAMESTATE)


def load_gamestate(slot=1):
  """Lädt einen Spielstand aus einem Slot; fällt auf den Default-Spielstand zurück."""
  logger.debug(f'load_gamestate(slot={slot})')
  # Eine unlesbare Datei wird beiseitegelegt statt später überschrieben.
  sicherung = saveslots.sichere_beschaedigten_slot(slot)
  if sicherung:
    logger.warning(f'Spielstand in Slot {slot} war unlesbar und wurde nach {sicherung} verschoben')
  loaded = saveslots.lade_slot(slot)
  if loaded is None:
    logger.debug('Kein Spielstand gefunden - Default GAMESTATE')
    return neuer_spielstand()
  # Alte Spielstände um neue Schlüssel ergänzen
  merge_defaults(neuer_spielstand(), loaded)
  # Rezepte und Entfernungen sind Spielregeln, kein Spielfortschritt: immer die
  # aktuellen Werte verwenden, auch wenn der Spielstand ältere enthält.
  loaded['Werkstatt'] = copy.deepcopy(DEFAULT_GAMESTATE['Werkstatt'])
  for planet, daten in DEFAULT_GAMESTATE['Planeten'].items():
    loaded['Planeten'][planet]['Entfernung'] = copy.deepcopy(daten['Entfernung'])
  return loaded


GAMESTATE = load_gamestate(aktiver_slot)


def setze_aktiven_slot(slot):
  """Macht `slot` zum aktiven Slot und merkt ihn für den nächsten Start."""
  global aktiver_slot
  if slot != aktiver_slot or saveslots.gemerkter_slot() != slot:
    saveslots.merke_slot(slot)
  aktiver_slot = slot


def dump_gamestate(slot=None, zeige_status=True):
  """Schreibt den aktuellen Spielstand in einen Speicherslot.

  Ohne Angabe wird der aktive Slot benutzt (der zuletzt geladene oder
  gespeicherte), damit Autosave nie einen fremden Slot überschreibt.
  `zeige_status=False` lässt das Fenster in Ruhe - nötig beim Beenden, wenn
  es schon geschlossen ist.
  """
  global iSaveStatusTimer
  if slot is None:
    slot = aktiver_slot
  setze_aktiven_slot(slot)
  logger.debug(f'dump_gamestate(slot={slot})')
  GAMESTATE['Ticks'] = iTicks
  GAMESTATE['Credits'] = iCredits
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Log'] = lLog
  GAMESTATE['AktiveForschung'] = (
      {'name': sLaufende_Forschung, 'fortschritt': iAktueller_Forschungsfortschritt}
      if bForschung_aktiv else None
  )
  GAMESTATE['ForschungsQueue'] = list(forschungs_queue)
  GAMESTATE['AktiverBau'] = (
      {'name': sLaufender_Bau, 'anzahl': iAnzahl_Bauen, 'fortschritt': iAktueller_Baufortschritt}
      if bBauen_aktiv else None
  )
  GAMESTATE['BauQueue'] = [dict(auftrag) for auftrag in bau_queue]
  GAMESTATE['AktiveErdJobs'] = [
      {'name': j.name, 'fortschritt': j.fortschritt}
      for j in erde_jobs_aktiv if j.aktiv
  ]
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
          'ereignis': r.ereignis,
      }
      for r in aktive_reisen if not r.abgeschlossen
  ]
  GAMESTATE['AktiveRaumsonde'] = (
      {'fortschritt': raumsonde_flug.fortschritt} if raumsonde_flug and raumsonde_flug.aktiv else None
  )
  saveslots.speichere_slot(slot, GAMESTATE)
  if zeige_status:
    iSaveStatusTimer = 15
    window['save_status'].update(visible=True, value=f'Gespeichert (Slot {slot})')


def zeige_Forschung(name):
  """Zeigt Details und passende Buttons zur ausgewählten Technologie."""
  logger.debug(f'zeige_Forschung({name})')
  daten = SCIENCE[name]
  window['desc_research'].update(visible=True, value=daten['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f"Forschungsdauer: {daten['dauer']} Zyklen")
  window['desc_costs'].update(visible=True, value=f"Forschungskosten: {daten['kosten']} Forschungspunkte")
  erforschbar_nach = daten.get('erforschbar nach', '')
  if erforschbar_nach:
    status = '✓' if GAMESTATE['Forschung'][erforschbar_nach]['erforscht'] else '✗'
    window['desc_voraussetzung'].update(visible=True, value=f"Voraussetzung: {erforschbar_nach} {status}")
  else:
    window['desc_voraussetzung'].update(visible=True, value="Keine Voraussetzung")

  erforscht = GAMESTATE['Forschung'][name]['erforscht']
  laeuft = bForschung_aktiv and sLaufende_Forschung == name
  geplant = name in forschungs_queue
  zu_teuer = daten['kosten'] > iForschungspunkte
  offen = not erforscht and not laeuft and not geplant

  if laeuft:
    hinweis = 'Wird gerade erforscht'
  elif geplant:
    hinweis = 'Steht in der Warteschlange'
  elif offen and zu_teuer and not bForschung_aktiv:
    hinweis = 'Forschungspunkte reichen nicht aus'
  else:
    hinweis = ''
  window['comment'].update(visible=bool(hinweis), value=hinweis)
  window['already_researched'].update(visible=erforscht)
  window['do_research'].update(visible=offen and not bForschung_aktiv and not zu_teuer)
  # In die Warteschlange darf auch, was noch zu teuer ist: es startet, sobald die Punkte reichen.
  window['queue_research'].update(visible=offen and bForschung_aktiv)


def aktualisiere_forschungs_buttons():
  """Aktualisiert Sichtbarkeit und Farbe aller Forschungs- und Werkstatt-Buttons."""
  for name, daten in SCIENCE.items():
    erforscht = GAMESTATE['Forschung'][name]['erforscht']
    erforschbar_nach = daten.get('erforschbar nach', '')
    sichtbar = not erforschbar_nach or GAMESTATE['Forschung'][erforschbar_nach]['erforscht']
    window[f'Erforsche {name}'].update(visible=sichtbar)
    window[f'Erforsche {name}'].update(
      button_color=FARBE_ERFORSCHT if erforscht else sg.theme_button_color())
    window[f'img_{name}'].update(visible=erforscht)
    window[f'baue_{name}'].update(visible=erforscht)

def aktualisiere_bau_queue_anzeige():
  """Zeigt die Bau-Warteschlange; beim vordersten Auftrag auch, worauf er wartet."""
  if not bau_queue:
    window['bau_queue_anzeige'].update(value="Keine Aufträge in der Warteschlange.")
    return
  zeilen = [f"{a['anzahl']}x {a['name']}" for a in bau_queue]
  fehlt = bau_materialien_reichen(bau_queue[0]['name'], bau_queue[0]['anzahl'])
  if fehlt:
    zeilen[0] += f"  (wartet auf {fehlt})"
  window['bau_queue_anzeige'].update(value='\n'.join(zeilen))

def aktualisiere_forschungs_queue_anzeige():
  queue_text = '\n'.join(forschungs_queue) if forschungs_queue else "Keine Aufträge in der Warteschlange."
  window['forschungs_queue_anzeige'].update(value=queue_text)

def forschungsauftrag_hinzufuegen(name):
  """Stellt eine Forschung in die Warteschlange (jede höchstens einmal)."""
  if GAMESTATE['Forschung'][name]['erforscht'] or name in forschungs_queue or sLaufende_Forschung == name:
    return
  forschungs_queue.append(name)
  add2log(f"Forschungsauftrag '{name}' zur Warteschlange hinzugefügt")
  aktualisiere_forschungs_queue_anzeige()
  zeige_Forschung(name)


def zeige_bauen(sAktuelles_Bauen):
  """Zeigt Informationen zum ausgewählten Bau-Item"""
  if sAktuelles_Bauen in GAMESTATE['Werkstatt']:
    item = GAMESTATE['Werkstatt'][sAktuelles_Bauen]

    # Beschreibung und Dauer anzeigen
    window['desc_bauen'].update(value=f"{item['beschreibung']}\n\nDauer: {item['dauer']} Zyklen")

    # Benötigte Materialien anzeigen
    materialien_text = "Benötigte Materialien:\n"
    for material, anzahl in item['material'].items():
      verfügbar = get_bestand(material)
      hinweis = ' [auf der Erde]' if material in RAUMSCHIFF_TYPEN else ''
      materialien_text += f"• {material}: {anzahl} (verfügbar: {verfügbar}){hinweis}\n"

    # Produktionskette: Rohstoffe gesamt (nur wenn mind. ein direktes Material herstellbar ist)
    direkte = set(item['material'].keys())
    if any(m in GAMESTATE['Werkstatt'] for m in direkte):
      rohstoffe = berechne_rohstoffe(sAktuelles_Bauen)
      materialien_text += "\nRohstoffe gesamt:\n"
      for rohstoff, anzahl in rohstoffe.items():
        verfügbar = get_bestand(rohstoff)
        status = '✓' if verfügbar >= anzahl else '✗'
        materialien_text += f"  {status} {rohstoff}: {anzahl} (verfügbar: {verfügbar})\n"

    window['desc_materialien'].update(value=materialien_text, visible=True)

    # Maximale Anzahl berechnen (limitiert durch verfügbare Materialien)
    max_anzahl = None
    for material, anzahl in item['material'].items():
      verfügbar = get_bestand(material)
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

    # Läuft schon ein Bau, kann der Auftrag nur in die Warteschlange.
    window['do_bauen'].update(visible=kann_bauen and not bBauen_aktiv)
    window['queue_bauen'].update(visible=kann_bauen and bBauen_aktiv)
    window['bauen_unmöglich'].update(visible=not kann_bauen, value="Nicht genug Materialien!")

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

def lese_bau_anzahl():
  """Stückzahl aus dem Werkstatt-Spinner (mindestens 1)."""
  try:
    return max(int(window['anzahl_bauen'].get()), 1)
  except (ValueError, TypeError):
    return 1


def bau_materialien_reichen(name, anzahl):
  """Liefert das erste fehlende Material für `anzahl` Stück - oder None."""
  for material, menge in GAMESTATE['Werkstatt'][name]['material'].items():
    if get_bestand(material) < menge * anzahl:
      return material
  return None


def bauauftrag_hinzufuegen(name, anzahl):
  """Stellt einen Bauauftrag in die Warteschlange.

  Material wird erst beim Start des Auftrags abgezogen; reicht es dann nicht,
  wartet der Auftrag in der Warteschlange.
  """
  bau_queue.append({'name': name, 'anzahl': anzahl})
  add2log(f"Bauauftrag {anzahl}x '{name}' zur Warteschlange hinzugefügt")
  aktualisiere_bau_queue_anzeige()


def baue(name, anzahl=None):
  """Startet einen Bau; ohne `anzahl` gilt der Wert des Spinners."""
  global bBauen_aktiv, sLaufender_Bau, iAktueller_Baufortschritt, iMax_Bauen, iAnzahl_Bauen
  if bBauen_aktiv:
    add2log("Es wird bereits gebaut - stelle den Auftrag in die Warteschlange")
    return False
  if anzahl is None:
    anzahl = lese_bau_anzahl()
  if not GAMESTATE['Forschung'].get(name, {}).get('erforscht', False):
    add2log(f"'{name}' ist noch nicht erforscht")
    return False

  fehlt = bau_materialien_reichen(name, anzahl)
  if fehlt:
    add2log(f"Nicht genug {fehlt} zum Bauen von {anzahl}x {name}")
    return False

  # Materialien sofort abziehen (für alle Items auf einmal)
  item = GAMESTATE['Werkstatt'][name]
  for material, menge in item['material'].items():
    aendere_bestand(material, -menge * anzahl)

  # Bau-Prozess starten (Dauer skaliert mit Anzahl)
  bBauen_aktiv = True
  sLaufender_Bau = name
  iAnzahl_Bauen = anzahl
  iMax_Bauen = item['dauer'] * anzahl
  iAktueller_Baufortschritt = 0

  add2log(f"Baue {anzahl}x '{name}' - Materialien verbraucht")
  aktualisiere_bau_anzeige()
  return True


def aktualisiere_bau_anzeige():
  """Bringt Fortschrittsbalken, Buttons und Bestände der Werkstatt auf Stand."""
  window['progressbar_Bauen'].update(current_count=iAktueller_Baufortschritt if bBauen_aktiv else 0,
                                     max=max(iMax_Bauen, 1), visible=bBauen_aktiv)
  window['stop_bauen'].update(visible=bBauen_aktiv)
  window['bau_status'].update(
    visible=bBauen_aktiv,
    value=f"Im Bau: {iAnzahl_Bauen}x {sLaufender_Bau}" if bBauen_aktiv else '')
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_hq_anzeige()
  aktualisiere_bau_queue_anzeige()
  if sAktuelles_Bauen:
    zeige_bauen(sAktuelles_Bauen)


def beende_bauen():
  """Schliesst den laufenden Bau ab und legt das Ergebnis ins Inventar."""
  global bBauen_aktiv, sLaufender_Bau
  name, anzahl = sLaufender_Bau, iAnzahl_Bauen

  aendere_bestand(name, anzahl)
  if name in RAUMSCHIFF_TYPEN:
    add2log(f"{anzahl}x '{name}' erfolgreich gebaut - zur Erde hinzugefügt")
  else:
    add2log(f"{anzahl}x '{name}' erfolgreich gebaut - ins Inventar gelegt")
  achievements.zaehle(GAMESTATE, 'gebaute_items', anzahl)

  bBauen_aktiv = False
  sLaufender_Bau = None

  # Siegbedingung: Weltraumstation fertiggestellt
  if name == 'Weltraumstation' and not GAMESTATE.get('Spiel_gewonnen'):
    GAMESTATE['Spiel_gewonnen'] = True
    add2log("*** SIEG! Die Weltraumstation ist fertiggestellt - du hast das Spiel gewonnen! ***")
    sg.popup_no_wait(
      'Glückwunsch!\n\n'
      'Die Weltraumstation ist fertiggestellt.\n'
      f'Du hast das Spiel in {iTicks} Zyklen gewonnen!\n\n'
      'Du kannst weiterspielen oder über "File → Neues Spiel" von vorn beginnen.',
      title='Spiel gewonnen!',
      keep_on_top=True,
    )

  dump_gamestate()
  aktualisiere_bau_anzeige()


def stoppe_bauen():
  """Stoppt den laufenden Bau; Material für unfertige Stücke kommt zurück."""
  global bBauen_aktiv, sLaufender_Bau
  if not bBauen_aktiv:
    return
  name = sLaufender_Bau
  item = GAMESTATE['Werkstatt'][name]

  # Fertige und noch offene Stücke anhand des Fortschritts
  fertige_items = min(iAktueller_Baufortschritt // item['dauer'], iAnzahl_Bauen)
  offene_items = iAnzahl_Bauen - fertige_items

  if fertige_items > 0:
    aendere_bestand(name, fertige_items)
    achievements.zaehle(GAMESTATE, 'gebaute_items', fertige_items)
    add2log(f"{fertige_items}x '{name}' fertiggestellt")
  if offene_items > 0:
    for material, menge in item['material'].items():
      aendere_bestand(material, menge * offene_items)
    add2log(f"Materialien für {offene_items}x '{name}' zurückgegeben")

  bBauen_aktiv = False
  sLaufender_Bau = None
  dump_gamestate()
  aktualisiere_bau_anzeige()


def erforsche(name):
  """Startet eine Forschung und zieht die Forschungspunkte ab."""
  global bForschung_aktiv, sLaufende_Forschung
  global iAktueller_Forschungsfortschritt, iMax_Forschung, iForschungspunkte
  daten = SCIENCE[name]
  if bForschung_aktiv:
    add2log("Es wird bereits geforscht - stelle den Auftrag in die Warteschlange")
    return False
  if GAMESTATE['Forschung'][name]['erforscht']:
    add2log(f"'{name}' ist bereits erforscht")
    return False
  voraussetzung = daten.get('erforschbar nach', '')
  if voraussetzung and not GAMESTATE['Forschung'][voraussetzung]['erforscht']:
    add2log(f"'{name}' braucht zuerst '{voraussetzung}'")
    return False
  if iForschungspunkte < daten['kosten']:
    add2log(f"Nicht genug Forschungspunkte für '{name}' (benötigt: {daten['kosten']})")
    return False
  iForschungspunkte -= daten['kosten']
  bForschung_aktiv = True
  sLaufende_Forschung = name
  iMax_Forschung = max(1, int(daten['dauer']))
  iAktueller_Forschungsfortschritt = 0
  add2log(f"Erforsche '{name}'")
  aktualisiere_forschungs_anzeige()
  return True


def aktualisiere_forschungs_anzeige():
  """Bringt Fortschrittsbalken und Buttons der Forschung auf Stand."""
  window['progressbar_Forschung'].update(
    current_count=iAktueller_Forschungsfortschritt if bForschung_aktiv else 0,
    max=max(iMax_Forschung, 1), visible=bForschung_aktiv)
  window['stop_research'].update(visible=bForschung_aktiv)
  window['forschung_status'].update(
    visible=bForschung_aktiv,
    value=f"Läuft: {sLaufende_Forschung}" if bForschung_aktiv else '')
  aktualisiere_forschungs_buttons()
  aktualisiere_forschungs_queue_anzeige()
  aktualisiere_tab_sichtbarkeit()
  if sAktuelle_Forschung:
    zeige_Forschung(sAktuelle_Forschung)


def beende_forschung():
  """Schliesst die laufende Forschung ab."""
  global bForschung_aktiv, sLaufende_Forschung
  name = sLaufende_Forschung
  GAMESTATE['Forschung'][name]['erforscht'] = True
  achievements.zaehle(GAMESTATE, 'forschungen_abgeschlossen')
  add2log(f"Forschung von '{name}' beendet")
  bForschung_aktiv = False
  sLaufende_Forschung = None
  dump_gamestate()
  aktualisiere_forschungs_anzeige()


def stoppe_forschung():
  """Bricht die laufende Forschung ab und erstattet ihre Kosten."""
  global bForschung_aktiv, sLaufende_Forschung, iForschungspunkte
  if not bForschung_aktiv:
    return
  name = sLaufende_Forschung
  iForschungspunkte += SCIENCE[name]['kosten']
  add2log(f"Forschung von '{name}' gestoppt - Forschungspunkte zurückerstattet")
  bForschung_aktiv = False
  sLaufende_Forschung = None
  aktualisiere_forschungs_anzeige()


def formatiere_log(eintraege):
  """Log für die Anzeige: neueste Einträge oben, Zyklus als rechtsbündige Spalte."""
  zeilen = []
  for eintrag in reversed(eintraege):
    zyklus, sep, text = str(eintrag).partition('\t')
    zeilen.append(f'{zyklus:>6} │ {text}' if sep else str(eintrag))
  return '\n'.join(zeilen)

def add2log(sString):
  logger.debug(f'add2log({sString})')
  global lLog
  global sLog
  lLog.append(f"{iTicks}\t{sString}")
  if len(lLog) > config.LOG_MAX_ENTRIES:
    lLog = lLog[-config.LOG_MAX_ENTRIES:]
  sLog = formatiere_log(lLog)
  window['Log'].update(value=sLog)

def erstelle_inventar_layout():
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

  # Dynamische Einträge für jedes Material (nur sichtbar wenn anzahl > 0).
  # Es werden alle bekannten Materialien angelegt - auch solche, die erst
  # später gefunden werden -, damit Funde sofort angezeigt werden können.
  for material in bekannte_materialien():
    anzahl = GAMESTATE['Inventar'].get(material, 0)
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
  """Gibt eine Beschreibung für jedes Material zurück"""
  return MATERIALS.get(material, {'Beschreibung': f'Unbekanntes Material: {material}'}).get('Beschreibung', 'no description found')

def aktualisiere_inventar_anzeige():
  """Aktualisiert die Inventar-Anzeige dynamisch"""
  for material, anzahl in GAMESTATE['Inventar'].items():
    window[f'inv_anzahl_{material}'].update(value=str(anzahl))
    window[f'inv_row_{material}'].update(visible=anzahl > 0)

def aktualisiere_raumschiff_anzeige():
  """Aktualisiert die Raumschiff-Anzeige"""
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


def erstelle_raumschiff_uebersicht():
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
  """Berechnet Gesamtwert und Typenzahl des Inventars (inkl. Raumschiffe)."""
  logger.debug('berechne_inventar_statistiken()')
  gesamtwert = 0
  anzahl_typen = 0

  for material, anzahl in GAMESTATE['Inventar'].items():
    if anzahl > 0:
      anzahl_typen += 1
      gesamtwert += anzahl * config.MATERIAL_VALUES.get(material, 0)

  # Raumschiffe werden separat geführt, zählen aber zum Vermögen
  for planet in GAMESTATE['Raumschiffe'].values():
    for typ in RAUMSCHIFF_TYPEN:
      anzahl = planet.get(typ, {}).get('Anzahl', 0)
      if anzahl > 0:
        gesamtwert += anzahl * config.MATERIAL_VALUES.get(typ, 0)

  return gesamtwert, anzahl_typen

def aktualisiere_inventar_statistiken():
  """Aktualisiert die Inventar-Statistiken"""
  gesamtwert, anzahl_typen = berechne_inventar_statistiken()

  window['inventar_gesamtwert'].update(value=f"{gesamtwert:,} Credits")
  window['inventar_anzahl_typen'].update(value=str(anzahl_typen))

# Globale Variablen für Reisen
aktive_reisen = []  # Liste aller aktiven Reisen

class Reise:
  """Ein Raumschiff, das zwischen zwei Planeten unterwegs ist."""
  def __init__(self, raumschiff_typ, von_planet, zu_planet, astronauten, fracht):
    self.raumschiff_typ = raumschiff_typ
    self.von_planet = von_planet
    self.zu_planet = zu_planet
    self.astronauten = astronauten
    self.fracht = fracht  # Dictionary mit Materialien
    self.start_tick = iTicks
    self.dauer = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
    self.end_tick = self.start_tick + self.dauer
    self.abgeschlossen = False
    # Aufgelöstes Zufallsereignis (siehe travel_rules), wird bei Ankunft verrechnet
    self.ereignis = None

  def fortschritt(self, aktuelle_tick):
    """Fortschritt in Prozent; berücksichtigt durch Ereignisse verschobene Ankunft."""
    gesamt = self.end_tick - self.start_tick
    if gesamt <= 0 or aktuelle_tick >= self.end_tick:
      return 100
    return max(0, min(100, (aktuelle_tick - self.start_tick) / gesamt * 100))

  def ist_abgeschlossen(self, aktuelle_tick):
    return aktuelle_tick >= self.end_tick

def get_raumschiff_kapazitaet(raumschiff_typ):
  """Gibt die Kapazitäten eines Raumschiffs zurück"""
  eintrag = SCIENCE.get(raumschiff_typ, {})
  astronauten = eintrag.get('Sitzplätze', 0)
  fracht = eintrag.get('Frachtplätze', 0)
  # Reichweite kann optional gesetzt werden, falls im SCIENCE vorhanden
  reichweite = eintrag.get('reichweite', 0)
  return {'astronauten': astronauten, 'fracht': fracht, 'reichweite': reichweite}

def get_reise_kosten(raumschiff_typ, von_planet, zu_planet, astronauten):
  """Treibstoff- und Lebenserhaltungsbedarf einer geplanten Reise."""
  entfernung = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
  upgrades = GAMESTATE['Inventar'].get('Lebenserhaltung_Upgrade', 0)
  return travel_rules.berechne_reisekosten(raumschiff_typ, entfernung, astronauten, upgrades)


def kann_reisen(von_planet, zu_planet, raumschiff_typ):
  """Prüft ob eine Reise möglich ist"""
  # Prüfen ob Startplanet bekannt ist (Erde ist immer bekannt)
  if von_planet != 'Erde' and not GAMESTATE['Planeten'][von_planet].get('entdeckt', False):
    return False, "Startplanet nicht entdeckt"
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

def pruefe_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict):
  """Prüft alle Bedingungen einer Reise.

  Rückgabe: (ok, grund, verbrauch). Treibstoff, Wasser und Fracht kommen aus
  dem Vorrat des Startplaneten (Erde: Inventar, sonst Lager).
  """
  if von_planet == zu_planet:
    return False, "Start- und Zielplanet sind identisch", {}
  moeglich, grund = kann_reisen(von_planet, zu_planet, raumschiff_typ)
  if not moeglich:
    return False, grund, {}
  kapazitaet = get_raumschiff_kapazitaet(raumschiff_typ)
  if astronauten_anzahl < 0 or any(menge < 0 for menge in fracht_dict.values()):
    return False, "Negative Mengen sind nicht erlaubt", {}
  frei = freie_astronauten(von_planet)
  if astronauten_anzahl > frei:
    gebunden = gebundene_astronauten(von_planet)
    zusatz = f", {gebunden} sind in Missionen/Expeditionen gebunden" if gebunden else ''
    return False, f"Nicht genug freie Astronauten auf {von_planet} (frei: {frei}{zusatz})", {}
  if astronauten_anzahl > kapazitaet['astronauten']:
    return False, f"Zu viele Astronauten für {raumschiff_typ} (max. {kapazitaet['astronauten']})", {}
  if sum(fracht_dict.values()) > kapazitaet['fracht']:
    return False, f"Zu viel Fracht für {raumschiff_typ} (max. {kapazitaet['fracht']})", {}

  verbrauch = get_reise_kosten(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl)
  # Verbrauch und Fracht teilen sich denselben Vorrat.
  bedarf = dict(verbrauch)
  for material, menge in fracht_dict.items():
    bedarf[material] = bedarf.get(material, 0) + menge
  ausreichend, fehlend = travel_rules.pruefe_reisekosten(lager(von_planet), bedarf)
  if not ausreichend:
    ort = 'Es fehlt' if von_planet == 'Erde' else f'Im Lager auf {von_planet} fehlt'
    return False, f'{ort}: ' + travel_rules.formatiere_reisekosten(fehlend), verbrauch
  return True, '', verbrauch


def starte_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict):
  """Startet eine neue Reise. Rückgabe: True bei Erfolg."""
  fracht_dict = {material: menge for material, menge in fracht_dict.items() if menge}
  ok, grund, verbrauch = pruefe_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict)
  if not ok:
    add2log(f"Reise nicht möglich: {grund}")
    return False
  # Ressourcen abziehen
  GAMESTATE['Raumschiffe'][von_planet][raumschiff_typ]['Anzahl'] -= 1
  GAMESTATE['Astronauten'][von_planet] -= astronauten_anzahl
  vorrat = lager(von_planet)
  for mengen in (verbrauch, fracht_dict):
    for material, menge in mengen.items():
      vorrat[material] -= menge
  neue_reise = Reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict)
  aktive_reisen.append(neue_reise)
  add2log(f"Reise gestartet: {raumschiff_typ} von {von_planet} nach {zu_planet} mit "
          f"{astronauten_anzahl} Astronauten und Fracht {formatiere_mengen(fracht_dict) if fracht_dict else 'keine'} "
          f"(Verbrauch: {travel_rules.formatiere_reisekosten(verbrauch)})")
  wuerfle_reiseereignis(neue_reise)
  return True


def wuerfle_reiseereignis(reise):
  """Zieht ein Zufallsereignis für eine gestartete Reise und wendet es an.

  Zeitliche Effekte verschieben sofort die Ankunft, alles andere wird bei der
  Ankunft in beende_reise() verrechnet.
  """
  if not config.TRAVEL_EVENTS_ENABLED:
    return
  ereignis = travel_rules.waehle_reiseereignis(reise.dauer, hat_fracht=bool(reise.fracht))
  if ereignis is None:
    return
  ergebnis = travel_rules.wende_reiseereignis_an(
    ereignis, reise.fracht, schiff=reise.raumschiff_typ, ziel=reise.zu_planet
  )
  reise.ereignis = ergebnis
  reise.fracht = ergebnis['fracht']
  # Ankunft verschieben, aber nie vor den aktuellen Zyklus
  reise.end_tick = max(iTicks + 1, reise.end_tick + ergebnis['ticks'])
  achievements.zaehle(GAMESTATE, 'reiseereignisse')
  add2log(f"Zwischenfall: {ergebnis['text']}")

def beende_reise(reise):
  """Beendet eine Reise und bringt Raumschiff, Astronauten und Fracht ans Ziel."""
  global iForschungspunkte, iCredits
  # Raumschiff am Zielort hinzufügen (am Start bereits beim Reisestart abgezogen)
  GAMESTATE['Raumschiffe'][reise.zu_planet][reise.raumschiff_typ]['Anzahl'] += 1
  # Astronauten am Zielplanet hinzufügen (am Start bereits beim Reisestart abgezogen)
  GAMESTATE['Astronauten'][reise.zu_planet] += reise.astronauten
  # Fracht in den Vorrat des Zielplaneten (Erde: Inventar, sonst Lager)
  vorrat = lager(reise.zu_planet)
  for material, anzahl in reise.fracht.items():
    vorrat[material] = vorrat.get(material, 0) + anzahl
  add2log(f"Reise abgeschlossen: {reise.raumschiff_typ} ist auf {reise.zu_planet} angekommen "
          f"({reise.astronauten} Astronauten, Fracht: {formatiere_mengen(reise.fracht) if reise.fracht else 'keine'})")

  # Auswirkungen eines unterwegs gezogenen Ereignisses verrechnen
  if reise.ereignis:
    ergebnis = reise.ereignis
    gewinne = []
    # Funde und Verluste betreffen das Schiff, also den Vorrat am Ziel.
    for material, menge in ergebnis.get('material', {}).items():
      vorrat[material] = max(0, vorrat.get(material, 0) + menge)
      gewinne.append(f'{menge:+d} {material}')
    if ergebnis.get('forschungspunkte'):
      iForschungspunkte += ergebnis['forschungspunkte']
      gewinne.append(f"{ergebnis['forschungspunkte']:+d} Forschungspunkte")
    if ergebnis.get('credits'):
      iCredits += ergebnis['credits']
      achievements.zaehle(GAMESTATE, 'credits_verdient', ergebnis['credits'])
      gewinne.append(f"{ergebnis['credits']:+d} Credits")
    if gewinne:
      add2log(f"{ergebnis['name']}: " + ', '.join(gewinne))
    reise.ereignis = None

  achievements.zaehle(GAMESTATE, 'reisen_abgeschlossen')

  reise.abgeschlossen = True
  dump_gamestate()
  aktualisiere_alle_anzeigen()

def verwalte_aktive_reisen():
  """Schliesst alle Reisen ab, deren Ankunftszyklus erreicht ist."""
  for reise in aktive_reisen[:]:  # Kopie der Liste für sichere Iteration
    if reise.ist_abgeschlossen(iTicks):
      aktive_reisen.remove(reise)
      beende_reise(reise)

def stelle_reise_her(daten):
  """Baut eine gespeicherte Reise wieder auf und hängt sie an aktive_reisen an."""
  reise = Reise(daten['raumschiff_typ'], daten['von_planet'], daten['zu_planet'],
                daten['astronauten'], daten['fracht'])
  reise.start_tick = daten['start_tick']
  reise.end_tick = daten['end_tick']
  reise.ereignis = daten.get('ereignis')
  aktive_reisen.append(reise)
  return reise


def aktualisiere_reise_anzeige():
  """Aktualisiert die Anzeige der aktiven Reisen (Reisen-Tab und HQ-Übersicht)"""
  reise_text = ""
  for reise in aktive_reisen:
    if not reise.abgeschlossen:
      fortschritt = reise.fortschritt(iTicks)
      verbleibend = max(0, reise.end_tick - iTicks)
      reise_text += (f"{fortschrittsbalken(fortschritt, 100)}  {reise.raumschiff_typ}: "
                     f"{reise.von_planet} → {reise.zu_planet} ({fortschritt:.0f}%, noch {verbleibend} Zyklen)\n")
  if not reise_text:
    reise_text = "Keine aktiven Reisen"
  for key in ('aktive_reisen', 'aktive_reisen_uebersicht'):
    window[key].update(value=reise_text)

def aktualisiere_alle_anzeigen():
  """Aktualisiert alle UI-Elemente"""
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_reise_anzeige()
  aktualisiere_planeten_anzeige()
  aktualisiere_tab_sichtbarkeit()
  aktualisiere_entdeckungs_ui()
  aktualisiere_hq_anzeige()
  aktualisiere_ziel_anzeige()
  aktualisiere_verkauf_anzeige()


_statusleiste_cache = {}

def aktualisiere_statusleiste():
  """Frischt die Statusleiste auf - nur Felder, deren Wert sich geändert hat."""
  beschaeftigt = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) for j in erde_jobs_aktiv if j.aktiv)
  werte = {
    'tCycles': f'Zyklus {iTicks}',
    'tCredits': f'Credits: {iCredits:,}'.replace(',', '.'),
    'tForschungspunkte': f'Forschungspunkte: {iForschungspunkte}',
    'tArbeiter': f"Arbeiter frei: {GAMESTATE['Arbeiter']['Erde'] - beschaeftigt}/{GAMESTATE['Arbeiter']['Erde']}",
  }
  for key, text in werte.items():
    if _statusleiste_cache.get(key) != text:
      window[key].update(value=text)
      _statusleiste_cache[key] = text


def aktualisiere_ziel_anzeige():
  """Aktualisiert die 'Nächstes Ziel'-Anzeige (Tutorial) im HQ."""
  # Credits/Forschungspunkte werden als globale Variablen geführt; für die
  # Zielprüfung muss der Spielstand den aktuellen Stand kennen.
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Credits'] = iCredits
  window['naechstes_ziel'].update(value=tutorial.ziel_text(GAMESTATE))


def pruefe_und_melde_erfolge():
  """Prüft die Erfolge und verrechnet die Belohnungen der neu freigeschalteten."""
  global iCredits, iForschungspunkte
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Credits'] = iCredits
  neue = achievements.pruefe_erfolge(GAMESTATE)
  for erfolg in neue:
    belohnung = erfolg.get('belohnung', {})
    credits = belohnung.get('Credits', 0)
    punkte = belohnung.get('Forschungspunkte', 0)
    iCredits += credits
    iForschungspunkte += punkte
    if credits:
      achievements.zaehle(GAMESTATE, 'credits_verdient', credits)
    zusatz = ''
    if credits or punkte:
      teile = [f'+{credits} Credits'] if credits else []
      if punkte:
        teile.append(f'+{punkte} Forschungspunkte')
      zusatz = ' (' + ', '.join(teile) + ')'
    add2log(f"Erfolg freigeschaltet: {erfolg['name']} - {erfolg['beschreibung']}{zusatz}")
  return neue

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
    'mining_status_Mars': mars,
    'mining_starte_Mars': mars,
  }
  for key, sichtbar in sichtbarkeiten.items():
    window[key].update(visible=sichtbar)

def aktualisiere_hq_anzeige():
  """Aktualisiert Raumsonden-Button und -Status im HQ."""
  alles_entdeckt = GAMESTATE['Planeten']['Mond']['entdeckt'] and GAMESTATE['Planeten']['Mars']['entdeckt']
  sonden_im_inventar = GAMESTATE['Inventar'].get('Raumsonde', 0)
  flug_aktiv = raumsonde_flug is not None and raumsonde_flug.aktiv
  window['hq_sonde_hinweis'].update(visible=not alles_entdeckt)
  window['starte_raumsonde'].update(visible=sonden_im_inventar > 0 and not flug_aktiv)
  if flug_aktiv:
    window['raumsonde_status'].update(
      visible=True,
      value=(f"Raumsonde unterwegs {fortschrittsbalken(raumsonde_flug.fortschritt, raumsonde_flug.max_fortschritt)} "
             f"{raumsonde_flug.fortschritt}/{raumsonde_flug.max_fortschritt} Zyklen")
    )
  elif sonden_im_inventar == 0 and not alles_entdeckt:
    window['raumsonde_status'].update(
      visible=True,
      value="Keine Raumsonde im Inventar - erforsche und baue eine in der Werkstatt."
    )
  else:
    window['raumsonde_status'].update(visible=False)

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
  achievements.zaehle(GAMESTATE, 'sonden_gestartet')
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
    iForschungspunkte += config.PROBE_DATA_RESEARCH_POINTS
    add2log(f"Die Raumsonde hat wertvolle Daten gesammelt: +{config.PROBE_DATA_RESEARCH_POINTS} Forschungspunkte")
  raumsonde_flug = None
  dump_gamestate()
  aktualisiere_alle_anzeigen()

def aktualisiere_tab_sichtbarkeit():
  """Blendet Tabs ein/aus je nach Spielfortschritt."""
  mond = GAMESTATE['Planeten']['Mond']['entdeckt']
  werkstatt = any(v['erforscht'] for v in GAMESTATE['Forschung'].values())
  window['tab_Werkstatt'].update(visible=werkstatt)
  window['tab_Planeten'].update(visible=mond)
  window['tab_Reisen'].update(visible=mond)
  window['tab_Mondmissionen'].update(visible=mond)
  window['tab_Mining'].update(visible=mond)

def aktualisiere_planeten_anzeige():
  """Aktualisiert die Astronauten-Anzeige im HQ und die Infos im Planeten-Tab"""
  for planet, artikel in (('Erde', 'der'), ('Mond', 'dem'), ('Mars', 'dem')):
    if planet != 'Erde' and not GAMESTATE['Planeten'][planet]['entdeckt']:
      continue
    window[f'astronauten_{planet.lower()}'].update(
      value=f"Astronauten auf {artikel} {planet}: {GAMESTATE['Astronauten'][planet]}")
    window[f'planet_{planet.lower()}_info'].update(value=planeten_info_text(planet))

def erstelle_reise_interface():
  """Erstellt das Interface für Reisen"""

  # Radiobuttons für alle Planeten anlegen; unentdeckte werden erst später eingeblendet
  def planet_sichtbar(planet):
    return planet == 'Erde' or GAMESTATE['Planeten'][planet]['entdeckt']

  planet_radio_von = [sg.Radio(planet, 'reise_von', key=f'reise_von_{planet}', enable_events=True, visible=planet_sichtbar(planet)) for planet in ALLE_PLANETEN]
  planet_radio_zu = [sg.Radio(planet, 'reise_zu', key=f'reise_zu_{planet}', enable_events=True, visible=planet_sichtbar(planet)) for planet in ALLE_PLANETEN]
  # Raumschiff-Typen
  raumschiff_radio = [sg.Radio(typ, 'reise_raumschiff', key=f'reise_raumschiff_{typ}', enable_events=True) for typ in RAUMSCHIFF_TYPEN]
  # Fracht-Spinner (Wertebereiche werden beim Öffnen des Tabs aktualisiert)
  fracht_felder = [
    [sg.Text(f"{mat.replace('_', ' ')}:", size=(16, 1)),
     sg.Spin([i for i in range(0, GAMESTATE['Inventar'].get(mat, 0)+1)], initial_value=0, key=f'fracht_{mat}',
             size=(4, 1), readonly=True, enable_events=True)]
    for mat in FRACHT_MATERIALIEN
  ]
  # Drei Felder pro Zeile, damit das Formular nicht zu hoch wird
  material_rows = [
    [teil for feld in fracht_felder[i:i + 3] for teil in feld]
    for i in range(0, len(fracht_felder), 3)
  ]
  return [
    [sg.Text('Reise planen', font=('Arial', 12, 'bold'))],
    [sg.HorizontalSeparator()],
    [sg.Text('Von Planet:'), *planet_radio_von],
    [sg.Text('Zu Planet:'), *planet_radio_zu],
    [sg.Text('Raumschiff:'), *raumschiff_radio],
    [sg.HorizontalSeparator()],
    [sg.Text('Astronauten:'), sg.Spin([i for i in range(0, 11)], initial_value=0, size=(5, 1),
                                      key='reise_astronauten', readonly=True, enable_events=True)],
    [sg.Text('Fracht (optional):', key='fracht_hinweis', size=(70, 2))],
    *material_rows,
    [sg.HorizontalSeparator()],
    [sg.Text('', key='reise_info', size=(70, 4))],
    [sg.Button('Reise starten', key='starte_reise'), sg.Button('Abbrechen', key='reise_abbrechen')],
    [sg.HorizontalSeparator()],
    [sg.Text('Aktive Reisen:', font=('Arial', 10, 'bold'))],
    [sg.Multiline('', key='aktive_reisen', size=(60, 4), disabled=True)],
  ]

def get_reise_auswahl(values):
  """Liest die aktuell ausgewählten Reise-Optionen aus den Radiobuttons."""
  von_planet = next((p for p in ALLE_PLANETEN if values.get(f'reise_von_{p}')), None)
  zu_planet = next((p for p in ALLE_PLANETEN if values.get(f'reise_zu_{p}')), None)
  raumschiff_typ = next((t for t in RAUMSCHIFF_TYPEN if values.get(f'reise_raumschiff_{t}')), None)
  return von_planet, zu_planet, raumschiff_typ


def lese_zahl(values, key):
  """Ganzzahl aus einem Eingabefeld; unlesbare Eingaben zählen als 0."""
  try:
    return int(values.get(key, 0) or 0)
  except (ValueError, TypeError):
    return 0


def lese_reise_ladung(values):
  """Astronautenzahl und Fracht aus dem Reise-Formular."""
  astronauten = lese_zahl(values, 'reise_astronauten')
  fracht = {}
  for material in FRACHT_MATERIALIEN:
    menge = lese_zahl(values, f'fracht_{material}')
    if menge:
      fracht[material] = menge
  return astronauten, fracht


def rueckflug_warnung(raumschiff_typ, von_planet, zu_planet, fracht):
  """Warnt, wenn am Ziel der Treibstoff für den Rückflug fehlen wird.

  Abflüge verbrauchen Treibstoff aus dem Lager des Startplaneten. Auf der Erde
  lässt er sich jederzeit herstellen, auf Mond und Mars muss er als Fracht hin.
  """
  if zu_planet == 'Erde':
    return ''
  rueck = travel_rules.berechne_reisekosten(
    raumschiff_typ, GAMESTATE['Planeten'][zu_planet]['Entfernung'][von_planet], 0)
  vorhanden = lager(zu_planet).get('Treibstoff', 0) + fracht.get('Treibstoff', 0)
  fehlt = rueck.get('Treibstoff', 0) - vorhanden
  if fehlt > 0:
    return (f"Achtung: Auf {zu_planet} fehlen dann {fehlt} Treibstoff für den Rückflug "
            f"- als Fracht mitnehmen.")
  return ''


def aktualisiere_reise_info(values):
  """Zeigt Informationen zur aktuell ausgewählten Reise an."""
  von_planet, zu_planet, raumschiff_typ = get_reise_auswahl(values)
  if von_planet:
    window['fracht_hinweis'].update(
      value=f"Fracht (optional) - Vorrat auf {von_planet}: "
            f"{formatiere_mengen({m: lager(von_planet).get(m, 0) for m in FRACHT_MATERIALIEN})}")
  else:
    window['fracht_hinweis'].update(value='Fracht (optional):')
  if not (von_planet and zu_planet and raumschiff_typ):
    return
  astronauten, fracht = lese_reise_ladung(values)
  ok, grund, verbrauch = pruefe_reise(raumschiff_typ, von_planet, zu_planet, astronauten, fracht)
  if not verbrauch:
    window['reise_info'].update(value=f"Nicht möglich: {grund}")
    return

  entfernung = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
  kapazitaet = get_raumschiff_kapazitaet(raumschiff_typ)
  verfuegbar = GAMESTATE['Raumschiffe'][von_planet][raumschiff_typ]['Anzahl']
  zeilen = [
    f"Entfernung: {entfernung} Zyklen | Verfügbar auf {von_planet}: {verfuegbar}x {raumschiff_typ}",
    f"Kapazität: {kapazitaet['astronauten']} Astronauten, {kapazitaet['fracht']} Fracht",
    f"Verbrauch: {travel_rules.formatiere_reisekosten(verbrauch)}",
  ]
  if not ok:
    zeilen.append(f"Nicht möglich: {grund}")
  else:
    warnung = rueckflug_warnung(raumschiff_typ, von_planet, zu_planet, fracht)
    if warnung:
      zeilen.append(warnung)
  window['reise_info'].update(value='\n'.join(zeilen))


def aktualisiere_fracht_spinner():
  """Passt die Wertebereiche der Fracht-Spinner an den Vorrat des Startplaneten an."""
  vorrat = lager(sReise_von or 'Erde')
  for mat in FRACHT_MATERIALIEN:
    bestand = vorrat.get(mat, 0)
    try:
      aktuell = int(window[f'fracht_{mat}'].get())
    except (ValueError, TypeError):
      aktuell = 0
    window[f'fracht_{mat}'].update(values=list(range(0, bestand + 1)), value=max(0, min(aktuell, bestand)))

lTab_Reisen = erstelle_reise_interface()


# ============ EARTH JOBS SYSTEM ============

def starte_erde_job(job_name, still=False):
    """Startet einen Erd-Job. `still=True` schreibt nichts ins Logbuch (Wiederholung)."""
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
    if not still:
        add2log(f"Erd-Job '{job_name}' gestartet")
    aktualisiere_erde_jobs_anzeige()
    return True


def beende_erde_job(job, still=False):
    """Beendet einen Erd-Job und gibt Belohnung. `still=True`: kein Logeintrag."""
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
    
    achievements.zaehle(GAMESTATE, 'jobs_abgeschlossen')
    if not still:
        belohnung_text = ', '.join([f"{menge} {ressource}" for ressource, menge in belohnung.items()])
        add2log(f"Erd-Job '{job.name}' abgeschlossen! Belohnung: {belohnung_text}")
    aktualisiere_inventar_anzeige()


def aktualisiere_erde_jobs_anzeige():
    """Aktualisiert die Anzeige der aktiven Erd-Jobs."""
    if not erde_jobs_aktiv:
        window['aktive_erde_jobs'].update(value="Keine laufenden Jobs.")
    else:
        text = ""
        for job in erde_jobs_aktiv:
            if job.aktiv:
                text += (f"{fortschrittsbalken(job.fortschritt, job.max_fortschritt)}  "
                         f"{job.name} ({job.fortschritt}/{job.max_fortschritt} Zyklen)\n")
        window['aktive_erde_jobs'].update(value=text if text else "Keine laufenden Jobs.")
        
    # Aktualisiere freie Arbeiter
    beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) for j in erde_jobs_aktiv if j.aktiv)
    freie = GAMESTATE['Arbeiter']['Erde'] - beschäftigte
    window['freie_arbeiter'].update(value=f"Freie Arbeiter: {freie} / {GAMESTATE['Arbeiter']['Erde']}")


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
        [sg.Checkbox('Fertige Jobs automatisch wiederholen', key='erde_jobs_wiederholen',
                     default=GAMESTATE.get('Jobs_wiederholen', False), enable_events=True,
                     tooltip='Jeder abgeschlossene Job startet sofort neu, bis du den Haken entfernst.')],
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
  """Zeigt den Fortschritt der laufenden Mondmissionen."""
  active_by_name = {m.name: m for m in missionen_aktiv}
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

def pruefe_mondmission(name):
  """Prüft, ob eine Mondmission gestartet werden kann. Rückgabe: (ok, grund)."""
  mission = ACTIONS[name]
  if mission_abgeschlossen(name):
    return False, "Mission bereits abgeschlossen!"
  if any(m.name == name for m in missionen_aktiv):
    return False, "Mission läuft bereits"
  offen = [v for v in mission.get('voraussetzung', []) if not mission_abgeschlossen(v)]
  if offen:
    return False, "Zuerst abschliessen: " + ', '.join(offen)
  benoetigt = mission.get('benötigt_astronauten', 0)
  frei = freie_astronauten('Mond')
  if frei < benoetigt:
    return False, f"Nicht genug freie Astronauten auf dem Mond (benötigt: {benoetigt}, frei: {frei})"
  if iCredits < mission['kosten']:
    return False, f"Nicht genug Credits (benötigt: {mission['kosten']})"
  vorrat = lager('Mond')
  for material, menge in material_bedarf(mission).items():
    if vorrat.get(material, 0) < menge:
      return False, (f"Im Mond-Lager fehlt {material} (benötigt: {menge}, vorhanden: "
                     f"{vorrat.get(material, 0)}) - als Fracht mitbringen")
  return True, ''


def zeige_mondmission(name):
  """Zeigt Informationen zur ausgewählten Mondmission"""
  mission = ACTIONS[name]
  window['desc_mondmission'].update(
    visible=True,
    value=f"{mission['beschreibung']}\n\nDauer: {mission['dauer']} Zyklen\nKosten: {mission['kosten']} Credits"
  )

  vorrat = lager('Mond')
  text = "Anforderungen:\n"
  text += (f"• Astronauten: {mission.get('benötigt_astronauten', 0)} "
           f"(frei auf dem Mond: {freie_astronauten('Mond')})\n")
  for material, menge in material_bedarf(mission).items():
    text += f"• {material}: {menge} (im Mond-Lager: {vorrat.get(material, 0)})\n"
  for vor in mission.get('voraussetzung', []):
    text += f"• Mission '{vor}' {'✓' if mission_abgeschlossen(vor) else '✗'}\n"
  text += "\nBelohnungen:\n"
  for belohnung, wert in mission['belohnung'].items():
    text += f"• {belohnung.replace('_', ' ')}: {wert}\n"
  window['desc_mondmission_anforderungen'].update(value=text, visible=True)

  ok, grund = pruefe_mondmission(name)
  abgeschlossen = mission_abgeschlossen(name)
  window['do_mondmission'].update(visible=ok)
  window['mondmission_completed'].update(visible=abgeschlossen)
  window['mondmission_unmöglich'].update(visible=not ok and not abgeschlossen, value=grund)


def starte_mondmission(name):
  """Startet eine Mondmission: zieht Credits und Material aus dem Mond-Lager ab."""
  global iCredits
  ok, grund = pruefe_mondmission(name)
  if not ok:
    add2log(f"Mission '{name}' nicht möglich: {grund}")
    return False
  mission = ACTIONS[name]
  iCredits -= mission['kosten']
  achievements.zaehle(GAMESTATE, 'credits_ausgegeben', mission['kosten'])
  vorrat = lager('Mond')
  for material, menge in material_bedarf(mission).items():
    vorrat[material] -= menge
  missionen_aktiv.append(MissionInstance(name))
  add2log(f"Mission '{name}' gestartet.")
  aktualisiere_missionen_anzeige()
  aktualisiere_planeten_anzeige()
  zeige_mondmission(name)
  return True


def beende_mondmission(missionsname):
  """Vergibt die Belohnungen einer abgeschlossenen Mondmission (Güter ins Mond-Lager)."""
  vergib_belohnung('Mond', ACTIONS[missionsname]['belohnung'])
  GAMESTATE.setdefault('Mondmissionen', {}).setdefault(missionsname, {})['erforscht'] = True
  achievements.zaehle(GAMESTATE, 'missionen_abgeschlossen')
  add2log(f"Mission '{missionsname}' abgeschlossen! Erhalten: "
          f"{formatiere_mengen(ACTIONS[missionsname]['belohnung'])} (Güter liegen im Mond-Lager)")
  aktualisiere_inventar_anzeige()
  dump_gamestate()


def stoppe_mondmission(mission_name: str):
  """Stoppt eine Mondmission und gibt Credits und Material zurück"""
  global iCredits
  mission_inst = next((m for m in missionen_aktiv if m.name == mission_name), None)
  if not mission_inst:
    return
  mission = ACTIONS[mission_name]
  iCredits += mission['kosten']
  achievements.zaehle(GAMESTATE, 'credits_ausgegeben', -mission['kosten'])
  vorrat = lager('Mond')
  for material, menge in material_bedarf(mission).items():
    vorrat[material] = vorrat.get(material, 0) + menge
  missionen_aktiv.remove(mission_inst)
  aktualisiere_missionen_anzeige()
  aktualisiere_planeten_anzeige()
  add2log(f"Mondmission '{mission_name}' abgebrochen - Ressourcen zurückgegeben")


def pruefe_mining(planet):
  """Prüft, ob eine Expedition gestartet werden kann. Rückgabe: (ok, grund)."""
  exp = MINING_EXPEDITIONEN[planet]
  if len(mining_aktiv) >= MINING_SLOTS:
    return False, f"Es laufen bereits {MINING_SLOTS} Expeditionen"
  frei = freie_astronauten(planet)
  if frei < exp['benötigt_astronauten']:
    return False, f"Nicht genug freie Astronauten ({frei}/{exp['benötigt_astronauten']})"
  vorrat = lager(planet)
  for material, menge in material_bedarf(exp).items():
    if vorrat.get(material, 0) < menge:
      return False, (f"Im {planet}-Lager fehlt {material} ({vorrat.get(material, 0)}/{menge}) "
                     f"- als Fracht mitbringen")
  return True, ''


def starte_mining(planet):
    """Startet eine Mining-Expedition auf dem angegebenen Planeten."""
    ok, grund = pruefe_mining(planet)
    if not ok:
        add2log(f"Mining {planet}: {grund}")
        return False
    vorrat = lager(planet)
    for material, menge in material_bedarf(MINING_EXPEDITIONEN[planet]).items():
        vorrat[material] -= menge
    mining_aktiv.append(MiningInstance(planet))
    add2log(f"Mining-Expedition auf dem {planet} gestartet")
    aktualisiere_mining_anzeige()
    aktualisiere_planeten_anzeige()
    return True


def beende_mining(mining_inst):
    """Schließt eine Mining-Expedition ab; der Ertrag landet im Lager des Planeten."""
    belohnung = mining_belohnung(mining_inst.planet)
    vergib_belohnung(mining_inst.planet, belohnung)
    achievements.zaehle(GAMESTATE, 'mining_abgeschlossen')
    add2log(f"Mining-Expedition auf dem {mining_inst.planet} abgeschlossen! "
            f"Im {mining_inst.planet}-Lager: {formatiere_mengen(belohnung)}")
    aktualisiere_inventar_anzeige()
    dump_gamestate()


def stoppe_mining(slot_index):
    """Bricht eine Mining-Expedition ab und erstattet die Kosten."""
    if slot_index >= len(mining_aktiv):
        return
    mining_inst = mining_aktiv.pop(slot_index)
    vorrat = lager(mining_inst.planet)
    for material, menge in material_bedarf(MINING_EXPEDITIONEN[mining_inst.planet]).items():
        vorrat[material] = vorrat.get(material, 0) + menge
    add2log(f"Mining-Expedition auf dem {mining_inst.planet} abgebrochen - Ressourcen zurückgegeben")
    aktualisiere_mining_anzeige()
    aktualisiere_planeten_anzeige()


def aktualisiere_mining_anzeige():
    """Aktualisiert Voraussetzungen und Fortschritt der Mining-Expeditionen."""
    for planet in MINING_EXPEDITIONEN:
        ok, grund = pruefe_mining(planet)
        window[f'mining_status_{planet}'].update(
            value=(f"Freie Astronauten: {freie_astronauten(planet)} | Lager: {formatiere_mengen(lager(planet))}\n"
                   f"Dauer: {mining_dauer(planet)} Zyklen | Ertrag: {formatiere_mengen(mining_belohnung(planet))}"
                   + ('' if ok else f"\n{grund}")))
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


def erstelle_mining_tab():
    """Erstellt das Tab für Mining-Expeditionen."""
    mond_exp = MINING_EXPEDITIONEN['Mond']
    mars_exp = MINING_EXPEDITIONEN['Mars']

    def kosten(exp):
        return (f"Braucht {exp['benötigt_astronauten']} freie Astronauten und im Lager vor Ort: "
                f"{formatiere_mengen(material_bedarf(exp))}")

    mars_sichtbar = GAMESTATE['Planeten']['Mars']['entdeckt']

    linke_spalte = [
        [sg.Text('Mond-Expedition', font=('Arial', 11, 'bold'))],
        [sg.Text(mond_exp['beschreibung'], size=(45, 1))],
        [sg.Text(kosten(mond_exp), size=(45, 2))],
        [sg.Text('', key='mining_status_Mond', size=(45, 4))],
        [sg.Button('Expedition starten', key='mining_starte_Mond')],
        [sg.HorizontalSeparator()],
        [sg.Text('Mars-Expedition', font=('Arial', 11, 'bold'), visible=mars_sichtbar, key='mining_mars_title')],
        [sg.Text(mars_exp['beschreibung'], size=(45, 1), visible=mars_sichtbar, key='mining_mars_desc')],
        [sg.Text(kosten(mars_exp), size=(45, 2), visible=mars_sichtbar, key='mining_mars_req')],
        [sg.Text('', key='mining_status_Mars', size=(45, 4), visible=mars_sichtbar)],
        [sg.Button('Expedition starten', key='mining_starte_Mars', visible=mars_sichtbar)],
    ]

    rechte_spalte = [
        [sg.Text('Laufende Expeditionen:', font=('Arial', 10, 'bold'))],
        *[
            [
                sg.Text('', key=f'mining_slot_{i}_text', size=(22, 1), visible=False),
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


def erstelle_mondmission_tab():
  """Erstellt das Tab für Mondmissionen"""
  return [
    [sg.Text('Mondmissionen', font=('Arial', 12, 'bold'))],
    [sg.Text('Brauchen freie Astronauten auf dem Mond; Material kommt aus dem Mond-Lager (Fracht).', font=('Arial', 10, 'italic'))],
    [sg.HorizontalSeparator()],

    [
      sg.Column([
        *[[sg.Button(name, key=f'mondmission_{name}', size=(44, 1))] for name in ACTIONS],
      ], vertical_alignment='top'),

      sg.VerticalSeparator(),

      sg.Column([
        [sg.Text('', key='desc_mondmission', size=(50, 6), visible=False)],
        [sg.Text('', key='desc_mondmission_anforderungen', size=(50, 8), visible=False)],
        [sg.Button('Mission starten', key='do_mondmission', visible=False)],
        [sg.Text('', key='mondmission_unmöglich', visible=False, text_color=FARBE_FEHLER)],
        [sg.Text('Mission abgeschlossen', key='mondmission_completed', visible=False, text_color=FARBE_OK)],
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

lTab_Mondmissionen = erstelle_mondmission_tab()
lTab_Mining = erstelle_mining_tab()

# Menü-Einträge tragen ihren Key hinter '::'; das Event enthält den kompletten
# String, das angezeigte Label nur den Teil davor.
_SLOTS = range(1, saveslots.SLOT_ANZAHL + 1)
menu_def = [
  ['&File', [
    'Neues Spiel::neues_spiel',
    '---',
    '&Speichern', [f'Slot {s}::save_slot_{s}' for s in _SLOTS],
    '&Laden', [f'Slot {s}::load_slot_{s}' for s in _SLOTS],
    'Spielstände anzeigen::slot_uebersicht',
    '---',
    'Exit::exit',
  ]],
  ['&Hilfe', [
    'Kurzanleitung::hilfe_allgemein',
    'Hilfe zum aktuellen Tab::hilfe_tab',
    'Erfolge und Statistik::erfolge_anzeigen',
  ]],
]

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

  [sg.HorizontalSeparator()],
  # Tutorial: nächstes Ziel
  [sg.Text('Nächstes Ziel:', font=('Arial', 10, 'bold'))],
  [sg.Text('', key='naechstes_ziel', size=(60, 4), text_color='light green')],
  [sg.Button('Kurzanleitung', key='zeige_kurzanleitung'),
   sg.Button('Erfolge und Statistik', key='zeige_erfolge')],
]

lTab_Forschung = [
  [
    sg.Column([
      [
        sg.Button(button_text=name, key=f'Erforsche {name}',
                  visible=(not data.get('erforschbar nach')
                           or GAMESTATE['Forschung'][data['erforschbar nach']]['erforscht'])),
        sg.Image('images/checkmark.png', visible=GAMESTATE['Forschung'][name]['erforscht'], key=f'img_{name}')
      ]
      for name, data in SCIENCE.items()
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('Wähle links eine Technologie aus, um Details zu sehen.', key='desc_research', size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
      [sg.Text('', key='desc_costs', visible=False)],
      [sg.Text('', key='desc_voraussetzung', visible=False)],
      [sg.Text('', key='comment', visible=False, text_color=FARBE_FEHLER)],
      [
        sg.Button('Erforschen', key='do_research', visible=False),
        sg.Text('✓ bereits erforscht', key='already_researched', visible=False, text_color=FARBE_OK)
      ],
      [
        sg.ProgressBar(1, orientation='h', size=(20, 20), key='progressbar_Forschung', visible=False),
        sg.Button('Erforschen stoppen', key='stop_research', visible=False),
      ],
      [sg.Text('', key='forschung_status', visible=False, text_color=FARBE_HINWEIS, size=(30, 1))],
      [sg.Button('In Queue stellen', key='queue_research', visible=False)],
      [sg.Text('Warteschlange:', font=('Arial', 10, 'bold'))],
      [sg.Multiline('Keine Aufträge in der Warteschlange.', key='forschungs_queue_anzeige', size=(30, 3), disabled=True)],
      [sg.Button('Letzten Forschungsauftrag stornieren', key='storniere_forschungsauftrag')],
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
      [sg.Text('Wähle links ein Produkt aus, um Rezept und Bestand zu sehen.', key='desc_bauen', size=(40, 4))],
      [sg.Text('', key='desc_materialien', size=(40, 12), visible=False)],
      [sg.Text('Anzahl:', key='label_anzahl_bauen', visible=False), sg.Spin(values=[1], initial_value=1, key='anzahl_bauen', size=(5, 1), readonly=True, visible=False),
       sg.Button('Bauen', key='do_bauen', visible=False),
       sg.Button('In Queue stellen', key='queue_bauen', visible=False)],
      [sg.Text('', key='bauen_unmöglich', visible=False, text_color=FARBE_FEHLER)],
      [sg.ProgressBar(1, orientation='h', size=(30, 20), key='progressbar_Bauen', visible=False)],
      [sg.Text('', key='bau_status', visible=False, text_color=FARBE_HINWEIS, size=(40, 1)),
       sg.Button('Bauen stoppen', key='stop_bauen', visible=False)],
      [sg.Text('Warteschlange:', font=('Arial',10,'bold'))],
      [sg.Multiline('Keine Aufträge in der Warteschlange.', key='bau_queue_anzeige', size=(40,3), disabled=True)],
      [sg.Button('Nächsten Bauauftrag stornieren', key='storniere_bauauftrag')]
    ]),
  ],
]

def erstelle_inventar_tab():
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
    [sg.Text('Gesamtwert des Inventars:', size=(30, 1)), sg.Text('', key='inventar_gesamtwert', size=(20, 1))],
    [sg.Text('Anzahl verschiedener Materialien:', size=(30, 1)), sg.Text('', key='inventar_anzahl_typen', size=(20, 1))],
  ]

lTab_Inventory = erstelle_inventar_tab()

PLANETEN_BESCHREIBUNG = {
  'Erde': 'Heimatplanet und Hauptquartier. Hier arbeiten die Arbeiter, hier wird geforscht und gebaut.',
  'Mond': 'Erdtrabant mit Mondgestein und seltenen Mineralien. Ziel der Mondmissionen und Mond-Expeditionen.',
  'Mars': 'Der rote Planet - weit entfernt, aber reich an Rohstoffen. Expeditionen brauchen gute Ausrüstung.',
}


def planeten_info_text(planet):
  """Mehrzeiliger Info-Text für den Planeten-Tab (Astronauten, Schiffe, Entfernungen)."""
  schiffe = GAMESTATE['Raumschiffe'].get(planet, {})
  schiffe_text = ', '.join(f"{typ}: {schiffe.get(typ, {}).get('Anzahl', 0)}" for typ in RAUMSCHIFF_TYPEN)
  entfernungen = GAMESTATE['Planeten'][planet].get('Entfernung', {})
  bekannte = [
    f'{ziel} {dist}' for ziel, dist in entfernungen.items()
    if ziel == 'Erde' or GAMESTATE['Planeten'].get(ziel, {}).get('entdeckt')
  ]
  zeilen = [
    f"Astronauten: {GAMESTATE['Astronauten'].get(planet, 0)}",
    f'Raumschiffe: {schiffe_text}',
    f"Entfernungen: {', '.join(bekannte) if bekannte else '-'}",
  ]
  if planet == 'Erde':
    zeilen.insert(1, f"Arbeiter: {GAMESTATE['Arbeiter']['Erde']}")
  else:
    zeilen[0] += f" (frei: {freie_astronauten(planet)})"
    zeilen.append(f"Lager: {formatiere_mengen(lager(planet))}")
  return '\n'.join(zeilen)


def erstelle_planeten_tab(planet):
  return [
    [sg.Text(planet, font=('Arial', 12, 'bold'))],
    [sg.Text(PLANETEN_BESCHREIBUNG[planet], size=(60, 2), font=('Arial', 10, 'italic'))],
    [sg.HorizontalSeparator()],
    [sg.Text(planeten_info_text(planet), key=f'planet_{planet.lower()}_info', size=(60, 5))],
  ]


lTab_Erde = erstelle_planeten_tab('Erde')
lTab_Mond = erstelle_planeten_tab('Mond')
lTab_Mars = erstelle_planeten_tab('Mars')

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
                     f"Sitzplätze: {SCIENCE[_name]['Sitzplätze']}, Frachtplätze: {SCIENCE[_name]['Frachtplätze']}, "
                     f"Reichweite: {SCIENCE[_name]['reichweite']}"),
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
  achievements.zaehle(GAMESTATE, 'credits_ausgegeben', gesamt)
  aendere_bestand(name, anzahl)
  add2log(f"{anzahl}x {name} gekauft für {gesamt} Credits")
  aktualisiere_inventar_anzeige()
  aktualisiere_raumschiff_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_hq_anzeige()
  aktualisiere_verkauf_anzeige()
  zeige_shop_artikel(name)


# ---- Verkauf ----------------------------------------------------------------

def get_verkauf_auswahl():
  """Aktuell im Verkaufs-Dropdown gewähltes Material (oder None)."""
  wahl = window['verkauf_material'].get()
  return wahl if wahl and ist_verkaufbar(wahl) else None


def aktualisiere_verkauf_anzeige():
  """Aktualisiert Dropdown, Mengen-Spinner und Erlösvorschau im Shop."""
  materialien = verkaufbare_materialien(GAMESTATE['Inventar'])
  bisher = window['verkauf_material'].get()
  wahl = bisher if bisher in materialien else (materialien[0] if materialien else '')
  window['verkauf_material'].update(values=materialien, value=wahl)

  if not wahl:
    window['verkauf_menge'].update(values=[0], value=0)
    window['verkauf_info'].update(value='Keine verkaufbaren Materialien im Inventar.')
    window['do_verkaufen'].update(disabled=True)
    return

  bestand = GAMESTATE['Inventar'].get(wahl, 0)
  try:
    menge = int(window['verkauf_menge'].get())
  except (ValueError, TypeError):
    menge = 1
  menge = min(max(menge, 1), bestand)
  window['verkauf_menge'].update(values=list(range(1, bestand + 1)), value=menge)
  window['do_verkaufen'].update(disabled=False)
  window['verkauf_info'].update(
    value=(f'{wahl}: {VERKAUFSPREISE[wahl]} Credits/Stück, Bestand {bestand}\n'
           f'Erlös für {menge}x: {verkaufspreis(wahl, menge)} Credits')
  )


def verkaufe_material():
  """Verkauft die im Shop gewählte Menge des gewählten Materials."""
  global iCredits
  wahl = get_verkauf_auswahl()
  if not wahl:
    add2log('Kein verkaufbares Material ausgewählt')
    return
  try:
    menge = int(window['verkauf_menge'].get())
  except (ValueError, TypeError):
    menge = 1
  erfolg, erloes, meldung = verkaufe(GAMESTATE['Inventar'], wahl, menge)
  add2log(meldung if erfolg else f'Verkauf nicht möglich: {meldung}')
  if not erfolg:
    aktualisiere_verkauf_anzeige()
    return
  iCredits += erloes
  achievements.zaehle(GAMESTATE, 'credits_verdient', erloes)
  achievements.zaehle(GAMESTATE, 'materialien_verkauft', menge)
  aktualisiere_inventar_anzeige()
  aktualisiere_inventar_statistiken()
  aktualisiere_verkauf_anzeige()
  if sAktueller_Shop_Artikel:
    zeige_shop_artikel(sAktueller_Shop_Artikel)

_verkaufbar_start = verkaufbare_materialien(GAMESTATE['Inventar'])

lTab_Shop = [
  [sg.Text('Shop', font=('Arial', 12, 'bold'))],
  [sg.Text('Kaufe Materialien und Raumschiffe - oder mache Überschüsse zu Credits.')],
  [sg.HorizontalSeparator()],
  [sg.Text('Kaufen', font=('Arial', 10, 'bold'))],
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
        sg.Spin([i for i in range(1, 101)], initial_value=1, key='shop_anzahl', size=(5, 1), readonly=True, visible=False),
        sg.Button('Kaufen', key='do_kaufen', visible=False),
      ],
      [sg.Text('', key='shop_kommentar', visible=False, text_color=FARBE_FEHLER)],
    ], vertical_alignment='top'),
  ],
  [sg.HorizontalSeparator()],
  [sg.Text('Verkaufen', font=('Arial', 10, 'bold'))],
  [
    sg.Text('Material:'),
    sg.Combo(_verkaufbar_start, default_value=(_verkaufbar_start[0] if _verkaufbar_start else ''),
             key='verkauf_material', size=(22, 1), readonly=True, enable_events=True),
    sg.Text('Menge:'),
    sg.Spin([i for i in range(1, 1001)], initial_value=1, key='verkauf_menge',
            size=(5, 1), readonly=True, enable_events=True),
    sg.Button('Verkaufen', key='do_verkaufen'),
  ],
  [sg.Text('', key='verkauf_info', size=(60, 2))],
]

# Bild je Tab
TAB_BILDER = {
  'tab_HQ': 'TAB_HQ',
  'tab_Arbeit': 'TAB_ARBEIT',
  'tab_Forschung': 'TAB_FORSCHUNG',
  'tab_Inventar': 'TAB_INVENTAR',
  'tab_Planeten': 'TAB_PLANETEN',
  'tab_Shop': 'TAB_SHOP',
  'tab_Werkstatt': 'TAB_WERKSTATT',
  'tab_Reisen': 'TAB_REISEN',
  'tab_Mondmissionen': 'TAB_MONDMISSIONEN',
  'tab_Mining': 'TAB_PLANETEN',
}


def safe_update_image(image_key):
  """Tauscht das grosse Tab-Bild aus; fällt bei Fehlern auf das HQ-Bild zurück."""
  image_path = f"{config.IMAGE_PATH}/{TAB_BILDER.get(image_key, 'TAB_HQ')}.png"
  try:
    window['img_Spalte3'].update(filename=image_path)
  except Exception as e:
    logger.warning(f'Bild für {image_key} ({image_path}) konnte nicht geladen werden: {e}')
    try:
      window['img_Spalte3'].update(filename=f'{config.IMAGE_PATH}/TAB_HQ.png')
    except Exception:
      pass


def zeige_slot_uebersicht():
  """Popup mit allen Speicherslots."""
  zeilen = [saveslots.slot_beschriftung(info) for info in saveslots.alle_slots()]
  sg.popup_scrolled('\n'.join(zeilen), title='Spielstände', size=(70, 10), keep_on_top=True)


def zeige_erfolge_popup():
  """Popup mit Erfolgen und Statistik."""
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Credits'] = iCredits
  text = ('ERFOLGE\n'
          f'{achievements.erfolgs_uebersicht(GAMESTATE)}\n\n'
          'STATISTIK\n'
          f'{achievements.statistik_uebersicht(GAMESTATE)}')
  sg.popup_scrolled(text, title='Erfolge und Statistik', size=(70, 28), keep_on_top=True)


def uebernehme_spielstand():
  """Baut alle Laufzeitvariablen aus GAMESTATE neu auf (Start, Laden, neues Spiel)."""
  global iTicks, iCredits, iForschungspunkte, lLog, sLog, raumsonde_flug
  global bForschung_aktiv, sLaufende_Forschung, iAktueller_Forschungsfortschritt, iMax_Forschung
  global bBauen_aktiv, sLaufender_Bau, iAktueller_Baufortschritt, iMax_Bauen, iAnzahl_Bauen

  iTicks = GAMESTATE['Ticks']
  iCredits = GAMESTATE['Credits']
  iForschungspunkte = GAMESTATE['Forschungspunkte']
  lLog = GAMESTATE['Log']
  sLog = formatiere_log(lLog)

  # Laufende Forschung
  forschung = GAMESTATE.get('AktiveForschung')
  bForschung_aktiv = bool(forschung) and forschung.get('name') in SCIENCE
  sLaufende_Forschung = forschung['name'] if bForschung_aktiv else None
  iMax_Forschung = max(1, int(SCIENCE[sLaufende_Forschung]['dauer'])) if bForschung_aktiv else 0
  iAktueller_Forschungsfortschritt = forschung.get('fortschritt', 0) if bForschung_aktiv else 0
  forschungs_queue[:] = [n for n in GAMESTATE.get('ForschungsQueue', []) if n in SCIENCE]

  # Laufender Bau
  bau = GAMESTATE.get('AktiverBau')
  bBauen_aktiv = bool(bau) and bau.get('name') in GAMESTATE['Werkstatt']
  sLaufender_Bau = bau['name'] if bBauen_aktiv else None
  iAnzahl_Bauen = max(1, int(bau.get('anzahl', 1))) if bBauen_aktiv else 1
  iMax_Bauen = GAMESTATE['Werkstatt'][sLaufender_Bau]['dauer'] * iAnzahl_Bauen if bBauen_aktiv else 0
  iAktueller_Baufortschritt = bau.get('fortschritt', 0) if bBauen_aktiv else 0
  bau_queue[:] = [
    {'name': a['name'], 'anzahl': max(1, int(a.get('anzahl', 1)))}
    for a in GAMESTATE.get('BauQueue', []) if a.get('name') in GAMESTATE['Werkstatt']
  ]

  erde_jobs_aktiv.clear()
  for eintrag in GAMESTATE.get('AktiveErdJobs', []):
    if eintrag.get('name') in ERDE_JOBS:
      job = ErdArbeit(eintrag['name'])
      job.fortschritt = eintrag.get('fortschritt', 0)
      erde_jobs_aktiv.append(job)
  # Missionen vor dem Mining: mining_dauer() hängt nicht davon ab, die
  # Astronautenbindung aber von beiden Listen.
  missionen_aktiv.clear()
  for eintrag in GAMESTATE.get('AktiveMissionen', []):
    if eintrag['name'] in ACTIONS:
      instanz = MissionInstance(eintrag['name'])
      instanz.fortschritt = eintrag['fortschritt']
      missionen_aktiv.append(instanz)
  mining_aktiv.clear()
  for eintrag in GAMESTATE.get('AktivesMining', []):
    if eintrag['planet'] in MINING_EXPEDITIONEN:
      instanz = MiningInstance(eintrag['planet'])
      instanz.fortschritt = eintrag['fortschritt']
      mining_aktiv.append(instanz)
  aktive_reisen.clear()
  for eintrag in GAMESTATE.get('AktiveReisen', []):
    stelle_reise_her(eintrag)
  sonde = GAMESTATE.get('AktiveRaumsonde')
  raumsonde_flug = RaumsondenFlug(fortschritt=sonde.get('fortschritt', 0)) if sonde else None


def aktualisiere_ui_komplett():
  """Frischt nach Start, Laden oder neuem Spiel sämtliche Anzeigen auf."""
  global sAktuelle_Forschung, sAktuelles_Bauen, sAktuelle_Mondmission, sAktueller_Shop_Artikel
  sAktuelle_Forschung = None
  sAktuelles_Bauen = None
  sAktuelle_Mondmission = None
  sAktueller_Shop_Artikel = None
  window['Log'].update(value=sLog)
  # Detailbereiche zurücksetzen; sie füllen sich bei der nächsten Auswahl wieder
  for key in ('desc_dauer', 'desc_costs', 'desc_voraussetzung', 'comment', 'do_research',
              'already_researched', 'queue_research', 'desc_materialien', 'label_anzahl_bauen',
              'anzahl_bauen', 'do_bauen', 'queue_bauen', 'bauen_unmöglich', 'desc_mondmission',
              'desc_mondmission_anforderungen', 'do_mondmission', 'mondmission_unmöglich',
              'mondmission_completed', 'shop_beschreibung', 'shop_preis', 'shop_label_anzahl',
              'shop_anzahl', 'do_kaufen', 'shop_kommentar'):
    window[key].update(visible=False)
  window['desc_research'].update(value='Wähle links eine Technologie aus, um Details zu sehen.')
  window['desc_bauen'].update(value='Wähle links ein Produkt aus, um Rezept und Bestand zu sehen.')
  window['erde_jobs_wiederholen'].update(value=GAMESTATE.get('Jobs_wiederholen', False))
  aktualisiere_statusleiste()
  aktualisiere_alle_anzeigen()
  aktualisiere_erde_jobs_anzeige()
  aktualisiere_missionen_anzeige()
  aktualisiere_mining_anzeige()
  aktualisiere_forschungs_anzeige()
  aktualisiere_bau_anzeige()
  aktualisiere_fracht_spinner()


def lade_spielstand(slot):
  """Lädt einen Spielstand aus einem Slot und macht ihn zum aktiven Slot."""
  global GAMESTATE
  if saveslots.lade_slot(slot) is None:
    add2log(f'Slot {slot} enthält keinen (lesbaren) Spielstand')
    return False
  GAMESTATE = load_gamestate(slot)
  setze_aktiven_slot(slot)
  uebernehme_spielstand()
  aktualisiere_ui_komplett()
  add2log(f'Spielstand aus Slot {slot} geladen!')
  return True


def neues_spiel():
  """Beginnt im aktiven Slot ein neues Spiel."""
  global GAMESTATE
  GAMESTATE = neuer_spielstand()
  GAMESTATE['Tutorial_gezeigt'] = True
  uebernehme_spielstand()
  aktualisiere_ui_komplett()
  add2log(f'Neues Spiel gestartet (Slot {aktiver_slot})')
  dump_gamestate()


sLog = formatiere_log(GAMESTATE['Log'])

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

_STATUS_FONT = ('Arial', 10, 'bold')
LAYOUT = [
  [sg.Menu(menu_def)],
  # Statusleiste: wird bei jeder Änderung sofort aufgefrischt (aktualisiere_statusleiste)
  [
    sg.Text('', key='tCycles', font=_STATUS_FONT, size=(12, 1)),
    sg.Text('', key='tCredits', font=_STATUS_FONT, size=(15, 1)),
    sg.Text('', key='tForschungspunkte', font=_STATUS_FONT, size=(22, 1)),
    sg.Text('', key='tArbeiter', font=_STATUS_FONT, size=(20, 1)),
    sg.Push(),
    sg.Text('', key='save_status', text_color=FARBE_OK, visible=False),
  ],
  [
    sg.Column([
      [sg.TabGroup(
      tabs,
      expand_x=True, expand_y=True, change_submits=True, enable_events=True, key='TabGroup_Main', tab_location='top')]
    ], expand_x=True, expand_y=True, pad=(0, 0)),
    sg.Column([[sg.Image('images/TAB_HQ.png', key='img_Spalte3')]], vertical_alignment='center'),
  ],
  [sg.Text('Logbuch', font=('Arial', 9, 'bold'))],
  [sg.Multiline(sLog, font=('Consolas', 9), disabled=True, size=(100, 5), key='Log',
                expand_x=True, autoscroll=False, background_color='#14303D', text_color='#D6E6EC')],
]

# Auswahl im UI (nur Anzeige - laufende Vorgänge haben eigene Variablen)
sAktuelle_Forschung = None
sAktuelle_Mondmission = None

# Laufzeitwerte; uebernehme_spielstand() füllt sie aus GAMESTATE
iTicks = 0
iCredits = 0
iForschungspunkte = 0
lLog = []
uebernehme_spielstand()

window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True, finalize=True)
# Tastenkürzel: Strg+S speichert in den aktiven Slot, F1 öffnet die Hilfe zum aktuellen Tab
window.bind('<Control-s>', 'hotkey_speichern')
window.bind('<F1>', 'hotkey_hilfe')

aktualisiere_ui_komplett()
pruefe_und_melde_erfolge()


def verarbeite_forschungs_tick():
  """Ein Zyklus Forschung: Fortschritt, Abschluss und Start aus der Warteschlange."""
  global iAktueller_Forschungsfortschritt
  if bForschung_aktiv:
    iAktueller_Forschungsfortschritt += 1
    if iAktueller_Forschungsfortschritt >= iMax_Forschung:
      beende_forschung()
    else:
      window['progressbar_Forschung'].update(current_count=iAktueller_Forschungsfortschritt)

  if not bForschung_aktiv and forschungs_queue:
    naechste = forschungs_queue[0]
    if GAMESTATE['Forschung'][naechste]['erforscht']:
      forschungs_queue.pop(0)
      aktualisiere_forschungs_queue_anzeige()
    elif iForschungspunkte >= SCIENCE[naechste]['kosten']:
      # Reichen die Punkte noch nicht, wartet der Auftrag in der Warteschlange.
      forschungs_queue.pop(0)
      erforsche(naechste)


def verarbeite_bau_tick():
  """Ein Zyklus Werkstatt: Fortschritt, Abschluss und Start aus der Warteschlange."""
  global iAktueller_Baufortschritt
  if bBauen_aktiv:
    iAktueller_Baufortschritt += 1
    if iAktueller_Baufortschritt >= iMax_Bauen:
      beende_bauen()
    else:
      window['progressbar_Bauen'].update(current_count=iAktueller_Baufortschritt)

  if not bBauen_aktiv and bau_queue:
    auftrag = bau_queue[0]
    # Fehlt Material, wartet der Auftrag, bis es da ist.
    if bau_materialien_reichen(auftrag['name'], auftrag['anzahl']) is None:
      bau_queue.pop(0)
      baue(auftrag['name'], auftrag['anzahl'])
    else:
      aktualisiere_bau_queue_anzeige()


def verarbeite_tick():
  """Lässt genau einen Spielzyklus vergehen."""
  global iTicks, iCredits, iForschungspunkte, iSaveStatusTimer
  iTicks += 1
  logger.debug(f'Cycle: {iTicks}')

  verarbeite_forschungs_tick()
  verarbeite_bau_tick()

  if aktive_reisen:
    verwalte_aktive_reisen()

  if raumsonde_flug is not None and raumsonde_flug.aktiv:
    if raumsonde_flug.tick():
      beende_raumsondenflug()
    else:
      aktualisiere_hq_anzeige()

  for mission in missionen_aktiv[:]:  # Kopie, da Missionen entfernt werden
    if mission.tick():
      missionen_aktiv.remove(mission)
      beende_mondmission(mission.name)
  aktualisiere_missionen_anzeige()

  for mi in mining_aktiv[:]:
    if mi.tick():
      mining_aktiv.remove(mi)
      beende_mining(mi)
  aktualisiere_mining_anzeige()

  # Mit "automatisch wiederholen" startet ein fertiger Job sofort neu; das
  # Logbuch bleibt dabei frei für wichtigere Meldungen.
  wiederholen = GAMESTATE.get('Jobs_wiederholen', False)
  for job in erde_jobs_aktiv[:]:
    if job.tick():
      erde_jobs_aktiv.remove(job)
      beende_erde_job(job, still=wiederholen)
      if wiederholen:
        starte_erde_job(job.name, still=True)
  aktualisiere_erde_jobs_anzeige()

  aktualisiere_reise_anzeige()
  aktualisiere_planeten_anzeige()
  # Vorräte ändern sich laufend (Bau, Jobs, Ankünfte): Fracht-Auswahl nachziehen
  aktualisiere_fracht_spinner()

  if iTicks % config.CREDITS_EXTRA_TICKS == 0:
    iCredits += config.CREDITS_EXTRA

  if iTicks % config.SCIENCE_POINTS_EXTRA_TICKS == 0:
    upgrades = GAMESTATE['Inventar'].get('Kommunikations_Upgrade', 0)
    iForschungspunkte += config.SCIENCE_POINTS_EXTRA + upgrades * config.COMM_UPGRADE_SCIENCE_POINTS

  if iTicks % config.AUTOSAVE_INTERVAL == 0:
    dump_gamestate()

  if iSaveStatusTimer > 0:
    iSaveStatusTimer -= 1
    if iSaveStatusTimer == 0:
      window['save_status'].update(visible=False)

  # Erfolge und Tutorial-Ziel einmal pro Zyklus auffrischen
  pruefe_und_melde_erfolge()
  aktualisiere_ziel_anzeige()
  aktualisiere_statusleiste()


def verarbeite_tab_wechsel(tab, values):
  """Frischt beim Öffnen eines Tabs dessen Anzeige auf."""
  safe_update_image(tab)
  if tab == 'tab_Forschung':
    if sAktuelle_Forschung:
      zeige_Forschung(sAktuelle_Forschung)
  elif tab == 'tab_Werkstatt':
    if sAktuelles_Bauen:
      zeige_bauen(sAktuelles_Bauen)
  elif tab == 'tab_Inventar':
    aktualisiere_inventar_anzeige()
    aktualisiere_raumschiff_anzeige()
    aktualisiere_inventar_statistiken()
  elif tab == 'tab_Reisen':
    aktualisiere_reise_anzeige()
    aktualisiere_fracht_spinner()
    aktualisiere_reise_info(values)
  elif tab == 'tab_Shop':
    aktualisiere_verkauf_anzeige()
    if sAktueller_Shop_Artikel:
      zeige_shop_artikel(sAktueller_Shop_Artikel)
  elif tab == 'tab_HQ':
    aktualisiere_ziel_anzeige()
    aktualisiere_hq_anzeige()
  elif tab == 'tab_Planeten':
    aktualisiere_planeten_anzeige()
  elif tab == 'tab_Mondmissionen':
    if sAktuelle_Mondmission:
      zeige_mondmission(sAktuelle_Mondmission)
  elif tab == 'tab_Mining':
    aktualisiere_mining_anzeige()


def verarbeite_reise_event(event, values):
  """Events des Reise-Formulars."""
  global sReise_von
  von_planet, zu_planet, raumschiff_typ = get_reise_auswahl(values)
  sReise_von = von_planet
  if event == 'starte_reise':
    if not (von_planet and zu_planet and raumschiff_typ):
      add2log("Bitte Startplanet, Zielplanet und Raumschiff auswählen")
      return
    astronauten, fracht = lese_reise_ladung(values)
    if starte_reise(raumschiff_typ, von_planet, zu_planet, astronauten, fracht):
      aktualisiere_alle_anzeigen()
      aktualisiere_mining_anzeige()
      window['reise_astronauten'].update(value=0)
      for material in FRACHT_MATERIALIEN:
        window[f'fracht_{material}'].update(value=0)
      aktualisiere_fracht_spinner()
      window['reise_info'].update(value='Reise gestartet.')
  elif event == 'reise_abbrechen':
    sReise_von = None
    for planet in ALLE_PLANETEN:
      window[f'reise_von_{planet}'].update(value=False)
      window[f'reise_zu_{planet}'].update(value=False)
    for typ in RAUMSCHIFF_TYPEN:
      window[f'reise_raumschiff_{typ}'].update(value=False)
    window['reise_astronauten'].update(value=0)
    for material in FRACHT_MATERIALIEN:
      window[f'fracht_{material}'].update(value=0)
    window['reise_info'].update(value='')
    window['fracht_hinweis'].update(value='Fracht (optional):')
    aktualisiere_fracht_spinner()
  else:
    if event.startswith('reise_von_'):
      aktualisiere_fracht_spinner()
    aktualisiere_reise_info(values)


def verarbeite_event(event, values):
  """Verarbeitet ein Fenster-Event. Rückgabe: False, wenn das Spiel enden soll."""
  global sAktuelle_Forschung, sAktuelles_Bauen, sAktuelle_Mondmission, sAktueller_Shop_Artikel
  values = values or {}

  if event in (sg.WINDOW_CLOSED, 'Exit::exit'):
    # Nach einem Klick auf das X existiert das Fenster nicht mehr.
    dump_gamestate(zeige_status=False)
    return False

  if event == 'TabGroup_Main':
    verarbeite_tab_wechsel(values.get('TabGroup_Main'), values)

  # ---- Forschung ----
  elif event.startswith('Erforsche '):
    sAktuelle_Forschung = event.split(' ', 1)[1]
    zeige_Forschung(sAktuelle_Forschung)

  elif event == 'do_research':
    if sAktuelle_Forschung:
      erforsche(sAktuelle_Forschung)

  elif event == 'stop_research':
    stoppe_forschung()

  elif event == 'queue_research':
    if sAktuelle_Forschung:
      forschungsauftrag_hinzufuegen(sAktuelle_Forschung)

  elif event == 'storniere_forschungsauftrag':
    if forschungs_queue:
      add2log(f"Forschungsauftrag '{forschungs_queue.pop()}' storniert")
      aktualisiere_forschungs_anzeige()
    else:
      add2log("Keine Forschungsaufträge zu stornieren.")

  # ---- Werkstatt ----
  elif event.startswith('baue_'):
    sAktuelles_Bauen = event[len('baue_'):]
    zeige_bauen(sAktuelles_Bauen)

  elif event == 'do_bauen':
    if sAktuelles_Bauen:
      baue(sAktuelles_Bauen)

  elif event == 'queue_bauen':
    if sAktuelles_Bauen:
      bauauftrag_hinzufuegen(sAktuelles_Bauen, lese_bau_anzahl())

  elif event == 'stop_bauen':
    stoppe_bauen()

  elif event == 'storniere_bauauftrag':
    if bau_queue:
      auftrag = bau_queue.pop(0)
      add2log(f"Bauauftrag {auftrag['anzahl']}x '{auftrag['name']}' aus der Warteschlange entfernt.")
      aktualisiere_bau_queue_anzeige()
    else:
      add2log("Keine Bauaufträge zu stornieren.")

  # ---- Erd-Jobs ----
  elif event == 'erde_jobs_wiederholen':
    GAMESTATE['Jobs_wiederholen'] = bool(values.get('erde_jobs_wiederholen'))
    add2log('Fertige Jobs werden automatisch wiederholt' if GAMESTATE['Jobs_wiederholen']
            else 'Jobs laufen aus und werden nicht mehr wiederholt')

  elif event.startswith('start_erde_job_'):
    job_name = event[len('start_erde_job_'):]
    if job_name in ERDE_JOBS:
      starte_erde_job(job_name)

  # ---- Speichern / Laden / Hilfe (Menü) ----
  elif event == 'Neues Spiel::neues_spiel':
    antwort = sg.popup_yes_no(
      f'Ein neues Spiel überschreibt den Spielstand in Slot {aktiver_slot}.\n\n'
      'Wirklich neu beginnen?', title='Neues Spiel', keep_on_top=True)
    if antwort == 'Yes':
      neues_spiel()

  elif '::save_slot_' in event:
    slot = int(event.rsplit('_', 1)[1])
    dump_gamestate(slot)
    add2log(f"Spielstand in Slot {slot} gespeichert!")

  elif '::load_slot_' in event:
    lade_spielstand(int(event.rsplit('_', 1)[1]))

  elif event == 'hotkey_speichern':
    dump_gamestate()
    add2log(f"Spielstand in Slot {aktiver_slot} gespeichert! (Strg+S)")

  elif event in ('hotkey_hilfe', 'Hilfe zum aktuellen Tab::hilfe_tab'):
    tab = values.get('TabGroup_Main', 'tab_HQ')
    sg.popup_scrolled(tutorial.hilfe_fuer_tab(tab), title='Hilfe', size=(70, 18), keep_on_top=True)

  elif event == 'Spielstände anzeigen::slot_uebersicht':
    zeige_slot_uebersicht()

  elif event in ('Kurzanleitung::hilfe_allgemein', 'zeige_kurzanleitung'):
    sg.popup_scrolled(tutorial.HILFE_ALLGEMEIN, title='Kurzanleitung', size=(70, 30), keep_on_top=True)

  elif event in ('Erfolge und Statistik::erfolge_anzeigen', 'zeige_erfolge'):
    zeige_erfolge_popup()

  # ---- Reisen ----
  elif event in ('starte_reise', 'reise_abbrechen', 'reise_astronauten') or event.startswith(
      ('reise_von_', 'reise_zu_', 'reise_raumschiff_', 'fracht_')):
    verarbeite_reise_event(event, values)

  elif event == 'starte_raumsonde':
    starte_raumsonde()

  # ---- Shop ----
  elif event.startswith('shop_'):
    sAktueller_Shop_Artikel = event[len('shop_'):]
    zeige_shop_artikel(sAktueller_Shop_Artikel)

  elif event == 'do_kaufen':
    if sAktueller_Shop_Artikel:
      kaufe_shop_artikel(sAktueller_Shop_Artikel)

  elif event in ('verkauf_material', 'verkauf_menge'):
    aktualisiere_verkauf_anzeige()

  elif event == 'do_verkaufen':
    verkaufe_material()

  # ---- Mondmissionen ----
  elif event.startswith('mondmission_'):
    sAktuelle_Mondmission = event[len('mondmission_'):]
    zeige_mondmission(sAktuelle_Mondmission)

  elif event == 'do_mondmission':
    if sAktuelle_Mondmission:
      starte_mondmission(sAktuelle_Mondmission)

  elif event.startswith('slot_') and event.endswith('_stop'):
    stoppe_mondmission(MISSION_SLOTS[int(event.split('_')[1])])
    if sAktuelle_Mondmission:
      zeige_mondmission(sAktuelle_Mondmission)

  # ---- Mining ----
  elif event.startswith('mining_starte_'):
    starte_mining(event[len('mining_starte_'):])

  elif event.startswith('mining_slot_') and event.endswith('_stop'):
    stoppe_mining(int(event.split('_')[2]))

  aktualisiere_statusleiste()
  return True


def hauptschleife():
  """Echtzeit-Schleife: alle TICK_INTERVAL Sekunden ein Zyklus, dazwischen Events."""
  global letzter_tick
  while True:
    event, values = window.read(timeout=config.WINDOW_READ_TIMEOUT)
    jetzt = time.time()
    if jetzt - letzter_tick >= TICK_INTERVAL:
      letzter_tick = jetzt
      verarbeite_tick()
    if event != sg.TIMEOUT_KEY and not verarbeite_event(event, values):
      break
  window.close()


if __name__ == '__main__':
  # Beim allerersten Start die Kurzanleitung zeigen
  if not GAMESTATE.get('Tutorial_gezeigt'):
    GAMESTATE['Tutorial_gezeigt'] = True
    sg.popup_scrolled(tutorial.HILFE_ALLGEMEIN, title='Willkommen bei Spacegame',
                      size=(70, 30), keep_on_top=True)
    dump_gamestate()
  hauptschleife()
