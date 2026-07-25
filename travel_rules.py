"""
Reise-Regeln: Treibstoffverbrauch, Lebenserhaltung und Zufallsereignisse.

Dieses Modul enthält ausschliesslich reine Logik ohne GUI-Abhängigkeiten,
damit die Regeln unabhängig vom Spielfenster getestet werden können.
"""

import random

# =============================================================================
# TREIBSTOFF & LEBENSERHALTUNG
# =============================================================================

# Treibstoff pro Entfernungseinheit je Raumschifftyp.
TREIBSTOFF_PRO_ENTFERNUNG = {
    'Mondlander': 1,
    'Rakete': 2,
}

# Wasser pro Astronaut und Entfernungseinheit (Lebenserhaltung).
WASSER_PRO_ASTRONAUT_UND_ENTFERNUNG = 1

# Ein 'Lebenserhaltung_Upgrade' im Inventar senkt den Wasserbedarf.
LEBENSERHALTUNG_UPGRADE_RABATT = 0.5


def berechne_reisekosten(raumschiff_typ, entfernung, astronauten, lebenserhaltung_upgrades=0):
    """Berechnet den Verbrauch einer Reise.

    Rückgabe: dict mit den benötigten Materialien, z.B. {'Treibstoff': 3, 'Wasser': 2}.
    Materialien mit Bedarf 0 tauchen nicht auf.
    """
    entfernung = max(0, int(entfernung))
    astronauten = max(0, int(astronauten))

    treibstoff = TREIBSTOFF_PRO_ENTFERNUNG.get(raumschiff_typ, 1) * entfernung

    wasser = astronauten * entfernung * WASSER_PRO_ASTRONAUT_UND_ENTFERNUNG
    if lebenserhaltung_upgrades > 0 and wasser > 0:
        # Jedes Upgrade halbiert den Restbedarf, mindestens bleibt 1 Wasser übrig.
        faktor = LEBENSERHALTUNG_UPGRADE_RABATT ** min(lebenserhaltung_upgrades, 4)
        wasser = max(1, int(round(wasser * faktor)))

    kosten = {}
    if treibstoff > 0:
        kosten['Treibstoff'] = treibstoff
    if wasser > 0:
        kosten['Wasser'] = wasser
    return kosten


def pruefe_reisekosten(inventar, kosten):
    """Prüft, ob die Reisekosten aus dem Inventar bezahlt werden können.

    Rückgabe: (bool, dict der fehlenden Mengen).
    """
    fehlend = {}
    for material, menge in kosten.items():
        vorhanden = inventar.get(material, 0)
        if vorhanden < menge:
            fehlend[material] = menge - vorhanden
    return (not fehlend), fehlend


def formatiere_reisekosten(kosten):
    """Formatiert Reisekosten für die Anzeige."""
    if not kosten:
        return 'keine'
    return ', '.join(f'{menge} {material}' for material, menge in kosten.items())


# =============================================================================
# ZUFALLSEREIGNISSE WÄHREND DER REISE
# =============================================================================

# Jedes Ereignis besitzt:
#   gewicht       - relative Häufigkeit
#   text          - Logtext (kann {schiff}, {ziel} enthalten)
#   effekt        - was passiert (siehe wende_reiseereignis_an)
#   nur_mit_fracht- Ereignis nur ziehen, wenn Fracht an Bord ist
REISE_EREIGNISSE = [
    {
        'key': 'mikrometeorit',
        'name': 'Mikrometeoriten-Einschlag',
        'gewicht': 3,
        'text': 'Ein Mikrometeorit trifft die {schiff}. Reparaturen kosten Zeit.',
        'effekt': {'ticks': 1},
    },
    {
        'key': 'triebwerksstoerung',
        'name': 'Triebwerksstörung',
        'gewicht': 2,
        'text': 'Triebwerksstörung an Bord der {schiff}! Der Flug nach {ziel} verzögert sich.',
        'effekt': {'ticks': 2},
    },
    {
        'key': 'sonnenwind',
        'name': 'Günstiger Sonnenwind',
        'gewicht': 3,
        'text': 'Ein günstiger Sonnenwind schiebt die {schiff} schneller Richtung {ziel}.',
        'effekt': {'ticks': -1},
    },
    {
        'key': 'kometenstaub',
        'name': 'Kometenstaub gesammelt',
        'gewicht': 3,
        'text': 'Die {schiff} durchquert eine Staubwolke und sammelt Material ein.',
        'effekt': {'material': {'Staub': 3}},
    },
    {
        'key': 'asteroidenfund',
        'name': 'Asteroidenfund',
        'gewicht': 2,
        'text': 'Ein kleiner Asteroid wird eingefangen und ausgeschlachtet.',
        'effekt': {'material': {'Roheisen': 4, 'Seltene_Mineralien': 1}},
    },
    {
        'key': 'messdaten',
        'name': 'Wertvolle Messdaten',
        'gewicht': 3,
        'text': 'Die Crew der {schiff} sammelt unterwegs wertvolle Messdaten.',
        'effekt': {'forschungspunkte': 5},
    },
    {
        'key': 'funkspruch',
        'name': 'Bergungsprämie',
        'gewicht': 2,
        'text': 'Die {schiff} birgt einen alten Satelliten - die Bergungsprämie wird ausgezahlt.',
        'effekt': {'credits': 25},
    },
    {
        'key': 'frachtverlust',
        'name': 'Frachtverlust',
        'gewicht': 2,
        'text': 'Eine Ladungssicherung versagt - ein Teil der Fracht der {schiff} geht verloren.',
        'effekt': {'fracht_verlust': 1},
        'nur_mit_fracht': True,
    },
    {
        'key': 'treibstoffleck',
        'name': 'Treibstoffleck',
        'gewicht': 2,
        'text': 'Ein Leck im Tank der {schiff} - Treibstoff geht verloren.',
        'effekt': {'material': {'Treibstoff': -1}},
    },
]

# Wahrscheinlichkeit pro Entfernungseinheit, dass überhaupt ein Ereignis eintritt.
EREIGNIS_CHANCE_PRO_ENTFERNUNG = 0.25
EREIGNIS_CHANCE_MAX = 0.75


def ereignis_chance(entfernung):
    """Wahrscheinlichkeit, dass eine Reise dieser Länge ein Ereignis auslöst."""
    return min(EREIGNIS_CHANCE_MAX, max(0.0, entfernung * EREIGNIS_CHANCE_PRO_ENTFERNUNG))


def waehle_reiseereignis(entfernung, hat_fracht=False, rng=None):
    """Zieht ein Zufallsereignis für eine Reise - oder None, wenn nichts passiert.

    `rng` erlaubt deterministische Tests (z.B. random.Random(42)).
    """
    rng = rng or random
    if rng.random() >= ereignis_chance(entfernung):
        return None

    kandidaten = [
        e for e in REISE_EREIGNISSE
        if hat_fracht or not e.get('nur_mit_fracht', False)
    ]
    if not kandidaten:
        return None

    gewichte = [e['gewicht'] for e in kandidaten]
    return rng.choices(kandidaten, weights=gewichte, k=1)[0]


def wende_reiseereignis_an(ereignis, fracht, schiff='Raumschiff', ziel='dem Ziel'):
    """Berechnet die Auswirkungen eines Ereignisses.

    Verändert `fracht` nicht, sondern liefert ein Ergebnis-dict:
        ticks             - zusätzliche (oder negative) Reisezyklen
        material          - Materialänderungen fürs Inventar (kann negativ sein)
        forschungspunkte  - Änderung der Forschungspunkte
        credits           - Änderung der Credits
        fracht            - die (ggf. reduzierte) Fracht
        text              - fertig formatierter Logtext
    """
    effekt = ereignis.get('effekt', {})
    neue_fracht = dict(fracht or {})
    material = dict(effekt.get('material', {}))

    verlust = effekt.get('fracht_verlust', 0)
    verlorene_fracht = {}
    if verlust and neue_fracht:
        # Verliert `verlust` Einheiten, beginnend beim grössten Posten.
        for name in sorted(neue_fracht, key=lambda k: -neue_fracht[k]):
            if verlust <= 0:
                break
            weg = min(verlust, neue_fracht[name])
            neue_fracht[name] -= weg
            verlorene_fracht[name] = weg
            verlust -= weg
        neue_fracht = {k: v for k, v in neue_fracht.items() if v > 0}

    text = ereignis['text'].format(schiff=schiff, ziel=ziel)
    if verlorene_fracht:
        text += ' Verloren: ' + ', '.join(f'{v} {k}' for k, v in verlorene_fracht.items())

    return {
        'key': ereignis['key'],
        'name': ereignis['name'],
        'ticks': effekt.get('ticks', 0),
        'material': material,
        'forschungspunkte': effekt.get('forschungspunkte', 0),
        'credits': effekt.get('credits', 0),
        'fracht': neue_fracht,
        'verlorene_fracht': verlorene_fracht,
        'text': text,
    }
