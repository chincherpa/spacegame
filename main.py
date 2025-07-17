import json

import PySimpleGUI as sg

import config
from actions import ACTIONS
from materials import MATERIALS
from science import SCIENCE

sg.theme('Dark Teal 6')

# Todo
#   Das Bau-System reparieren und vervollständigen?
#   Reisen zwischen Planeten implementieren?
#   Die Mondmissionen aus actions.py integrieren?
# Das Interface verbessern?
# Ressourcenabbau-System hinzufügen?
#   die dynamische Inventar-Anzeige implementiere

bForschung_aktiv = False
# bBauen_aktiv = False
iAktueller_Forschungsfortschritt = None
# iAktueller_Baufortschritt = None

bBauen_aktiv = False
iAktueller_Baufortschritt = None
sAktuelles_Bauen = None
iMax_Bauen = None

# Globale Variablen für Mondmissionen
bMondmission_aktiv = False
iAktueller_Mondmissionsfortschritt = 0
sAktuelle_Mondmission = None
iMax_Mondmission = None

def load_gamestate():
  try:
    with open(config.SAVEFILE, "r") as file:
      print('config.SAVEFILE gefunden')
      return json.load(file)
  except FileNotFoundError:
    from gamestate import GAMESTATE
    print('GAMESTATE importiert')
    return GAMESTATE

GAMESTATE = load_gamestate()

def dump_gamestate():
  GAMESTATE['Ticks'] = fTicks
  GAMESTATE['Credits'] = iCredits
  GAMESTATE['Forschungspunkte'] = iForschungspunkte
  GAMESTATE['Log'] = lLog
  with open(config.SAVEFILE, "w") as outfile: 
    json.dump(GAMESTATE, outfile, indent=2)

def zeige_Forschung(sAktuelle_Forschung):
  window['do_research'].update(visible=False)
  window['already_researched'].update(visible=False)

  window['desc_research'].update(visible=True, value=SCIENCE[sAktuelle_Forschung]['beschreibung'])
  window['desc_dauer'].update(visible=True, value=f"Forschungsdauer: {SCIENCE[sAktuelle_Forschung]['dauer']} Zyklen")

  if not bForschung_aktiv and not GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
    window['do_research'].update(visible=True)

  # if GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht']:
  window['already_researched'].update(visible=GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'])

def zeige_bauen(sAktuelles_Bauen):
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

def baue(sAktuelles_Bauen):
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

def stoppe_bauen():
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
  lMaterials = []
  for material, amount in GAMESTATE['Inventar'].items():
    lMaterials.append([sg.Text(material)])
  return lMaterials

def get_amounts_from_inventory():
  lAmounts = []
  for material, amount in GAMESTATE['Inventar'].items():
    lAmounts.append([sg.Text(amount)])
  return lAmounts

def add2log(sString):
  global lLog
  global sLog
  lLog.append(f"{round(fTicks, 1)}\t{sString}")
  sLog = '\n'.join(lLog[::-1])
  window['Log'].update(value=sLog)

# NEW
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
    """Gibt eine Beschreibung für jedes Material zurück"""
    return MATERIALS.get(material, 'Unbekanntes Material')

def aktualisiere_inventar_anzeige():
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
        self.raumschiff_typ = raumschiff_typ
        self.von_planet = von_planet
        self.zu_planet = zu_planet
        self.astronauten = astronauten
        self.fracht = fracht  # Dictionary mit Materialien
        self.reise_id = reise_id
        self.start_tick = fTicks
        self.dauer = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
        self.end_tick = self.start_tick + self.dauer
        self.abgeschlossen = False
    
    def ist_abgeschlossen(self, aktuelle_tick):
        return aktuelle_tick >= self.end_tick
    
    def fortschritt(self, aktuelle_tick):
        if aktuelle_tick >= self.end_tick:
            return 100
        return min(100, ((aktuelle_tick - self.start_tick) / self.dauer) * 100)

def get_verfuegbare_raumschiffe(planet):
    """Gibt verfügbare Raumschiffe auf einem Planeten zurück"""
    verfuegbare = {}
    for raumschiff_typ in ['Mondlander', 'Rakete']:
        anzahl = GAMESTATE['Raumschiffe'][planet][raumschiff_typ]['Anzahl']
        if anzahl > 0:
            verfuegbare[raumschiff_typ] = anzahl
    return verfuegbare

def get_raumschiff_kapazitaet(raumschiff_typ):
    """Gibt die Kapazitäten eines Raumschiffs zurück"""
    eintrag = SCIENCE.get(raumschiff_typ, {})
    astronauten = eintrag.get('Sitzplätze', 0)
    fracht = eintrag.get('Frachtplätze', 0)
    # Reichweite kann optional gesetzt werden, falls im SCIENCE vorhanden
    reichweite = eintrag.get('reichweite', 0)
    return {'astronauten': astronauten, 'fracht': fracht, 'reichweite': reichweite}

def kann_reisen(von_planet, zu_planet, raumschiff_typ):
    """Prüft ob eine Reise möglich ist"""
    # Prüfen ob Zielplanet entdeckt ist
    if not GAMESTATE['Planeten'][zu_planet]['entdeckt'] and zu_planet != 'Erde':
        return False, "Zielplanet nicht entdeckt"
    
    # Prüfen ob Raumschiff verfügbar
    if GAMESTATE['Raumschiffe'][von_planet][raumschiff_typ]['Anzahl'] <= 0:
        return False, f"Kein {raumschiff_typ} auf {von_planet} verfügbar"
    
    # Prüfen ob Reichweite ausreicht
    entfernung = GAMESTATE['Planeten'][von_planet]['Entfernung'][zu_planet]
    reichweite = get_raumschiff_kapazitaet(raumschiff_typ)['reichweite']
    
    if entfernung > reichweite:
        return False, f"Reichweite von {raumschiff_typ} zu gering"
    
    return True, "Reise möglich"

def starte_reise(raumschiff_typ, von_planet, zu_planet, astronauten_anzahl, fracht_dict):
    """Startet eine neue Reise"""
    global aktive_reisen
    
    # Validierung
    kann_reisen_result, grund = kann_reisen(von_planet, zu_planet, raumschiff_typ)
    if not kann_reisen_result:
        add2log(f"Reise nicht möglich: {grund}")
        return False
    
    kapazitaet = get_raumschiff_kapazitaet(raumschiff_typ)
    
    # Prüfen ob genug Astronauten verfügbar
    if astronauten_anzahl > GAMESTATE['Astronauten'][von_planet]:
        add2log(f"Nicht genug Astronauten auf {von_planet}")
        return False
    
    # Prüfen ob Astronauten-Kapazität ausreicht
    if astronauten_anzahl > kapazitaet['astronauten']:
        add2log(f"{raumschiff_typ} kann nur {kapazitaet['astronauten']} Astronauten transportieren")
        return False
    
    # Prüfen ob Fracht-Kapazität ausreicht
    fracht_gesamt = sum(fracht_dict.values())
    if fracht_gesamt > kapazitaet['fracht']:
        add2log(f"{raumschiff_typ} kann nur {kapazitaet['fracht']} Fracht-Einheiten transportieren")
        return False
    
    # Prüfen ob Fracht verfügbar ist
    for material, anzahl in fracht_dict.items():
        if GAMESTATE['Inventar'].get(material, 0) < anzahl:
            add2log(f"Nicht genug {material} verfügbar")
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
    
    add2log(f"{raumschiff_typ} gestartet von {von_planet} nach {zu_planet}")
    add2log(f"Astronauten: {astronauten_anzahl}, Fracht: {fracht_gesamt} Einheiten")
    
    aktualisiere_reise_anzeige()
    return True

def beende_reise(reise):
    """Beendet eine Reise und bringt Raumschiff ans Ziel"""
    # Raumschiff am Zielort hinzufügen
    GAMESTATE['Raumschiffe'][reise.zu_planet][reise.raumschiff_typ]['Anzahl'] += 1
    
    # Astronauten am Zielort hinzufügen
    GAMESTATE['Astronauten'][reise.zu_planet] += reise.astronauten
    
    # Fracht am Zielort hinzufügen (ins Inventar)
    for material, anzahl in reise.fracht.items():
        GAMESTATE['Inventar'][material] += anzahl
    
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
    """Verwaltet alle aktiven Reisen"""
    global aktive_reisen
    
    for reise in aktive_reisen[:]:  # Copy der Liste für sichere Iteration
        if not reise.abgeschlossen and reise.ist_abgeschlossen(fTicks):
            beende_reise(reise)
    
    # Abgeschlossene Reisen entfernen
    aktive_reisen = [r for r in aktive_reisen if not r.abgeschlossen]

def aktualisiere_reise_anzeige():
    """Aktualisiert die Anzeige der aktiven Reisen"""
    try:
        if not aktive_reisen:
            window['aktive_reisen'].update(value="Keine aktiven Reisen")
        else:
            reise_text = ""
            for reise in aktive_reisen:
                if not reise.abgeschlossen:
                    fortschritt = reise.fortschritt(fTicks)
                    reise_text += f"{reise.raumschiff_typ}: {reise.von_planet} → {reise.zu_planet} ({fortschritt:.1f}%)\n"
            
            window['aktive_reisen'].update(value=reise_text if reise_text else "Keine aktiven Reisen")
    except KeyError:
        pass  # Element existiert noch nicht

def aktualisiere_alle_anzeigen():
    """Aktualisiert alle UI-Elemente"""
    aktualisiere_inventar_anzeige()
    aktualisiere_raumschiff_anzeige()
    aktualisiere_inventar_statistiken()
    aktualisiere_reise_anzeige()
    aktualisiere_planeten_anzeige()

def aktualisiere_planeten_anzeige():
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
    """Erstellt das Interface für Reisen"""
    
    # Dropdown für Startplaneten
    verfuegbare_planeten = ['Erde']
    if GAMESTATE['Planeten']['Mond']['entdeckt']:
        verfuegbare_planeten.append('Mond')
    if GAMESTATE['Planeten']['Mars']['entdeckt']:
        verfuegbare_planeten.append('Mars')
    
    return [
        [sg.Text('Reise planen', font=('Arial', 12, 'bold'))],
        [sg.HorizontalSeparator()],
        
        # Reise-Planung
        [sg.Text('Von Planet:'), sg.Combo(verfuegbare_planeten, key='reise_von', enable_events=True, readonly=True)],
        [sg.Text('Zu Planet:'), sg.Combo(verfuegbare_planeten, key='reise_zu', enable_events=True, readonly=True)],
        [sg.Text('Raumschiff:'), sg.Combo([], key='reise_raumschiff', enable_events=True, readonly=True)],
        
        [sg.HorizontalSeparator()],
        
        # Ladung
        [sg.Text('Astronauten:'), sg.Spin([i for i in range(0, 11)], initial_value=0, key='reise_astronauten')],
        [sg.Text('Fracht (optional):')],
        [sg.Text('Eisenbarren:'), sg.Spin([i for i in range(0, 21)], initial_value=0, key='fracht_Eisenbarren')],
        [sg.Text('Werkzeug:'), sg.Spin([i for i in range(0, 21)], initial_value=0, key='fracht_Werkzeug')],
        [sg.Text('Baumaterial:'), sg.Spin([i for i in range(0, 21)], initial_value=0, key='fracht_Baumaterial')],
        
        [sg.HorizontalSeparator()],
        
        # Reise-Info
        [sg.Text('', key='reise_info', size=(50, 3))],
        [sg.Button('Reise starten', key='starte_reise'), sg.Button('Abbrechen', key='reise_abbrechen')],
        
        [sg.HorizontalSeparator()],
        
        # Aktive Reisen
        [sg.Text('Aktive Reisen:', font=('Arial', 10, 'bold'))],
        [sg.Multiline('', key='aktive_reisen', size=(50, 8), disabled=True)],
    ]

# Neues Tab für Reisen
lTab_Reisen = erstelle_reise_interface()

def zeige_mondmission(sAktuelle_Mission):
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
    """Startet eine Mondmission"""
    global bMondmission_aktiv, iAktueller_Mondmissionsfortschritt, iMax_Mondmission
    
    mission = ACTIONS[sAktuelle_Mission]
    
    # Credits sofort abziehen
    global iCredits
    iCredits -= mission['kosten']
    
    # Ressourcen sofort abziehen
    for key, value in mission.items():
        if key.startswith('benötigt_') and key != 'benötigt_astronauten':
            ressource = key.replace('benötigt_', '').title()
            GAMESTATE['Inventar'][ressource] -= value
    
    # Mission-Prozess starten
    bMondmission_aktiv = True
    iMax_Mondmission = int(mission['dauer'] / config.TICK)
    iAktueller_Mondmissionsfortschritt = 0
    
    # UI aktualisieren
    window['do_mondmission'].update(visible=False)
    window['mondmission_unmöglich'].update(visible=False)
    window['progressbar_Mondmission'].update(current_count=0, max=iMax_Mondmission, visible=True)
    window['stop_mondmission'].update(visible=True)
    
    # Inventar-Anzeige aktualisieren
    aktualisiere_inventar_anzeige()
    
    add2log(f"Mondmission '{sAktuelle_Mission}' gestartet")

def beende_mondmission(sAktuelle_Mission):
    """Beendet eine Mondmission erfolgreich"""
    global bMondmission_aktiv, iCredits, iForschungspunkte
    
    mission = ACTIONS[sAktuelle_Mission]
    
    # Belohnungen vergeben
    for belohnung, wert in mission['belohnung'].items():
        if belohnung == 'Forschungspunkte':
            iForschungspunkte += wert
        elif belohnung == 'Credits':
            iCredits += wert
        else:
            # Andere Belohnungen ins Inventar
            if belohnung not in GAMESTATE['Inventar']:
                GAMESTATE['Inventar'][belohnung] = 0
            GAMESTATE['Inventar'][belohnung] += wert
    
    # Mission als abgeschlossen markieren
    ACTIONS[sAktuelle_Mission]['erforscht'] = True
    
    # Mission-Prozess beenden
    bMondmission_aktiv = False
    window['progressbar_Mondmission'].update(visible=False)
    window['stop_mondmission'].update(visible=False)
    window['mondmission_completed'].update(visible=True)
    
    # UI aktualisieren
    aktualisiere_inventar_anzeige()
    
    add2log(f"Mondmission '{sAktuelle_Mission}' erfolgreich abgeschlossen!")
    
    # Belohnungen loggen
    belohnungen_text = "Belohnungen erhalten: "
    for belohnung, wert in mission['belohnung'].items():
        belohnungen_text += f"{belohnung.replace('_', ' ')}: {wert}, "
    add2log(belohnungen_text[:-2])

def stoppe_mondmission():
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
            ], vertical_alignment='top'),
        ],
    ]

# Fügen Sie das neue Tab zur LAYOUT-Definition hinzu:
lTab_Mondmissionen = erstelle_mondmission_tab()

# NEW ENDE

menu_def = [['&File', ['&Load', '&Save']]]

lTab_HQ = [
    [sg.Text('Headquarters', font=('Arial', 12, 'bold'))],
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
    
    [sg.HorizontalSeparator()],
    
    # Aktive Reisen (Übersicht)
    [sg.Text('Aktive Reisen:', font=('Arial', 10, 'bold'))],
    [sg.Text('', key='aktive_reisen_uebersicht', size=(50, 3))],
]

lTab_Forschung = [
  [
    sg.Column([
      [
        sg.Button(button_text=name, key=f'Erforsche {name}', visible=not data.get('erforschbar nach', '') or GAMESTATE['Forschung'][data.get('erforschbar nach', '')]['erforscht']),
        sg.Image(r'images\checkmark.png', visible=GAMESTATE['Forschung'][name]['erforscht'], key=f'img_{name}')
      ]
      for name, data in SCIENCE.items()
    ]),
    sg.VerticalSeparator(),
    sg.Column([
      [sg.Text('', key='desc_research', visible=False, size=(30, 6))],
      [sg.Text('', key='desc_dauer', visible=False)],
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

lForschung_auf_Erde = ['Raumsonde', 'Mondlander', 'Rakete']  # , 'Weltraumstation']

lTab_Werkstatt = [
    [
        sg.Column([
            [sg.Button('Eisenbarren', key='baue_Eisenbarren', visible=GAMESTATE['Forschung']['Eisenbarren']['erforscht'])],
            [sg.Button('Werkzeug', key='baue_Werkzeug', visible=GAMESTATE['Forschung']['Werkzeug']['erforscht'])],
            [sg.Button('Baumaterial', key='baue_Baumaterial', visible=GAMESTATE['Forschung']['Baumaterial']['erforscht'])],
            [sg.Button('Raumsonde', key='baue_Raumsonde', visible=GAMESTATE['Forschung']['Raumsonde']['erforscht'])],
            [sg.Button('Mondlander', key='baue_Mondlander', visible=GAMESTATE['Forschung']['Mondlander']['erforscht'])],
            [sg.Button('Rakete', key='baue_Rakete', visible=GAMESTATE['Forschung']['Rakete']['erforscht'])],
            [sg.Button('Weltraumstation', key='baue_Weltraumstation', visible=GAMESTATE['Forschung']['Weltraumstation']['erforscht'])],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text('', key='desc_bauen', size=(40, 4))],
            [sg.Text('', key='desc_materialien', size=(40, 6), visible=False)],
            [sg.Button('Bauen', key='do_bauen', visible=False)],
            [sg.Text('', key='bauen_unmöglich', visible=False, text_color='red')],
            [sg.ProgressBar(0, orientation='h', size=(30, 20), key='progressbar_Bauen', visible=False)],
            [sg.Button('Bauen stoppen', key='stop_bauen', visible=False)],
        ]),
    ],
]

# Ersetze das alte lTab_Inventory durch:
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

lTab_Planets = [
  [
    sg.TabGroup(
      [
        [sg.Tab('Erde', lTab_Erde, key='tab_erde')],
        [sg.Tab('Mond', lTab_Mond, key='tab_mond')],
        [sg.Tab('Mars', lTab_Mars, key='tab_mars')],
      ],
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
      [sg.Button('Kaufen', key='do_kaufen', visible='wenn credits reichen')],
    ]),
  ],
]

lLog = GAMESTATE['Log']
sLog = '\n'.join(lLog[::-1])
print(sLog)

LAYOUT = [[sg.Menu(menu_def, )],
  [
    [
      sg.Text(text='Cycle:', key='tCycles'),
      sg.Text(text='Credits:', key='tCredits'),
      sg.Text(text='Forschungspunkte:', key='tForschungspunkte'),
    ],
    # sg.Column(
    #   [
    #     [sg.Button(button_text='HQ')],
    #     [sg.Button(button_text='Forschung')],
    #     [sg.Button(button_text='Inventar')],
    #     [sg.Button(button_text='Planeten')],
    #     [sg.Button(button_text='Shop')],
    #   ]
    # ),
    sg.Column([
      [sg.TabGroup([
        [
            sg.Tab('HQ', lTab_HQ, key='TAB_HQ', image_source=r'images\TAB_HQ.png', image_subsample=config.IMAGE_SUBSAMPLE),
            sg.Tab('Reisen', lTab_Reisen, key='TAB_REISEN', image_source=r'images\TAB_REISEN.png', image_subsample=config.IMAGE_SUBSAMPLE, visible=GAMESTATE['Forschung']['Mondlander']['erforscht']),
            sg.Tab('Mondmissionen', lTab_Mondmissionen, key='TAB_MONDMISSIONEN', image_source=r'images\TAB_MONDMISSIONEN.png', image_subsample=config.IMAGE_SUBSAMPLE, visible=GAMESTATE['Forschung']['Raumsonde']['erforscht']),
            sg.Tab('Forschung', lTab_Forschung, key='TAB_FORSCHUNG', image_source=r'images\TAB_FORSCHUNG.png', image_subsample=config.IMAGE_SUBSAMPLE),
            sg.Tab('Werkstatt', lTab_Werkstatt, key='TAB_WERKSTATT', image_source=r'images\TAB_WERKSTATT.png', image_subsample=config.IMAGE_SUBSAMPLE),
            sg.Tab('Inventar', lTab_Inventory, key='TAB_INVENTAR', image_source=r'images\TAB_INVENTAR.png', image_subsample=config.IMAGE_SUBSAMPLE),
            sg.Tab('Planeten', lTab_Planets, key='TAB_PLANETEN', image_source=r'images\TAB_PLANETEN.png', image_subsample=config.IMAGE_SUBSAMPLE),
            sg.Tab('Shop', lTab_Shop, key='TAB_SHOP', image_source=r'images\TAB_SHOP.png', image_subsample=config.IMAGE_SUBSAMPLE),
        ]
    ], expand_x=True, expand_y=True, change_submits=True, enable_events=True, key='TabGroup_Main', tab_location='top')]
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

fTicks = GAMESTATE['Ticks']
iCredits = GAMESTATE['Credits']
iForschungspunkte = GAMESTATE['Forschungspunkte']
inventory = GAMESTATE['Inventar']
sAktuelle_Forschung = list(SCIENCE.keys())[0]

# window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True)
window = sg.Window(config.TITLE, LAYOUT, size=config.WINDOW_SIZE, resizable=True, finalize=True)

# Bei Spielstart einmalig ausführen:
aktualisiere_inventar_anzeige()
aktualisiere_raumschiff_anzeige()
aktualisiere_inventar_statistiken()

while True:
  event, values = window.read(config.WINDOW_READ)
  fTicks += config.TICK
  window['tCycles'].update(f'Cycle: {fTicks:.1f}')
  window['tCredits'].update(f'Credits: {iCredits}')
  window['tForschungspunkte'].update(f'Forschungspunkte: {iForschungspunkte}')

  # print(f'START {event = }')
  # print(f'START {values = }')

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
    baue(sAktuelles_Bauen)

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

  elif event == 'Save':
    dump_gamestate()

  elif event == 'Load':
    GAMESTATE = load_gamestate()
    fTicks = GAMESTATE['Ticks']
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
      von_planet = values['reise_von']
      zu_planet = values['reise_zu']
      raumschiff_typ = values['reise_raumschiff']
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

  if bForschung_aktiv:
    iAktueller_Forschungsfortschritt += 1
    window['progressbar_Forschung'].update(current_count=iAktueller_Forschungsfortschritt)
    if iAktueller_Forschungsfortschritt == iMax_Forschung:
      add2log(f"Forschung von '{sAktuelle_Forschung}' beendet")
      bForschung_aktiv = False
      GAMESTATE['Forschung'][sAktuelle_Forschung]['erforscht'] = True

      window['progressbar_Forschung'].update(visible=False)
      window['stop_research'].update(visible=False)
      window['already_researched'].update(visible=True)
      window[f'img_{sAktuelle_Forschung}'].update(visible=True)
      for sForschung in lForschung_auf_Erde:
        if GAMESTATE['Forschung'][sForschung]['erforscht']:
          window[f'Erforsche {sForschung}'].update(visible=True)
          window[f'Erforsche {sForschung}'].update(button_color = ('black','green'))
          # window[f'Erforsche {sAktuelle_Forschung}'].update(button_color = ('black','green'))

      # window.refresh()

  if bBauen_aktiv:
      iAktueller_Baufortschritt += 1
      window['progressbar_Bauen'].update(current_count=iAktueller_Baufortschritt)
      if iAktueller_Baufortschritt >= iMax_Bauen:
          beende_bauen(sAktuelles_Bauen)
    #   window['stop_research'].update(visible=False)
    #   window[f'img_{sAktuelles_Bauen}'].update(visible=True)
    #   for sForschung in lForschung_auf_Erde:
    #     window[f'baue_{sForschung}'].update(visible=GAMESTATE['Forschung'][sForschung]['erforscht'])

      # window.refresh()

  # In der Hauptschleife bei jedem Tick:
  if True:  # Immer ausführen
    verwalte_aktive_reisen()

    # Reise-Anzeige regelmäßig aktualisieren
    if fTicks % 1 == 0:  # Jede Sekunde
      aktualisiere_reise_anzeige()

    if fTicks % 2 == 0:  # Jede 2. Sekunde
      iCredits += 1
      print('gif credit')

    if bMondmission_aktiv:
      iAktueller_Mondmissionsfortschritt += 1
      window['progressbar_Mondmission'].update(current_count=iAktueller_Mondmissionsfortschritt)
      if iAktueller_Mondmissionsfortschritt >= iMax_Mondmission:
        beende_mondmission(sAktuelle_Mondmission)

  if event != '__TIMEOUT__':
    # Inventar nur aktualisieren wenn sich etwas geändert haben könnte
    if event in ['do_bauen', 'stop_bauen'] or event.startswith('baue_') or bBauen_aktiv:
        aktualisiere_inventar_anzeige()
        aktualisiere_raumschiff_anzeige()
        aktualisiere_inventar_statistiken()
