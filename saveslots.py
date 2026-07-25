"""
Mehrere Speicherslots.

Reine Datei-/Datenlogik ohne GUI, damit sie unabhängig testbar ist.
Slot 1 benutzt weiterhin `config.SAVEFILE`, damit bestehende Spielstände
ohne Migration erhalten bleiben.
"""

import json
import os
from datetime import datetime

import config

SLOT_ANZAHL = 3


def slot_datei(slot):
    """Dateiname für einen Slot (1-basiert). Slot 1 = klassischer Spielstand."""
    if slot < 1 or slot > SLOT_ANZAHL:
        raise ValueError(f'Ungültiger Speicherslot: {slot} (erlaubt: 1-{SLOT_ANZAHL})')
    if slot == 1:
        return config.SAVEFILE
    basis, endung = os.path.splitext(config.SAVEFILE)
    return f'{basis}_{slot}{endung}'


def _fortschritt_text(daten):
    """Kurzbeschreibung des Spielfortschritts für die Slot-Übersicht."""
    if daten.get('Spiel_gewonnen'):
        return 'Gewonnen'
    planeten = daten.get('Planeten', {})
    if planeten.get('Mars', {}).get('entdeckt'):
        return 'Mars entdeckt'
    if planeten.get('Mond', {}).get('entdeckt'):
        return 'Mond entdeckt'
    erforscht = sum(
        1 for v in daten.get('Forschung', {}).values()
        if isinstance(v, dict) and v.get('erforscht')
    )
    if erforscht:
        return f'{erforscht} Technologien erforscht'
    return 'Spielbeginn'


def slot_info(slot):
    """Metadaten eines Slots für die Anzeige.

    Liefert immer ein dict; `vorhanden` zeigt an, ob ein Spielstand existiert.
    Beschädigte Dateien werden als `beschaedigt` markiert statt zu werfen.
    """
    datei = slot_datei(slot)
    info = {
        'slot': slot,
        'datei': datei,
        'vorhanden': False,
        'beschaedigt': False,
        'ticks': 0,
        'credits': 0,
        'forschungspunkte': 0,
        'fortschritt': '-',
        'gespeichert': '',
    }
    if not os.path.exists(datei):
        return info

    info['vorhanden'] = True
    try:
        with open(datei, 'r', encoding='utf-8') as fh:
            daten = json.load(fh)
    except (json.JSONDecodeError, OSError):
        info['beschaedigt'] = True
        info['fortschritt'] = 'beschädigt'
        return info

    if not isinstance(daten, dict):
        info['beschaedigt'] = True
        info['fortschritt'] = 'beschädigt'
        return info

    info['ticks'] = daten.get('Ticks', 0)
    info['credits'] = daten.get('Credits', 0)
    info['forschungspunkte'] = daten.get('Forschungspunkte', 0)
    info['fortschritt'] = _fortschritt_text(daten)
    try:
        info['gespeichert'] = datetime.fromtimestamp(
            os.path.getmtime(datei)
        ).strftime('%d.%m.%Y %H:%M')
    except OSError:
        info['gespeichert'] = ''
    return info


def alle_slots():
    """Infos zu allen Slots, aufsteigend sortiert."""
    return [slot_info(s) for s in range(1, SLOT_ANZAHL + 1)]


def slot_beschriftung(info):
    """Einzeilige Beschreibung eines Slots für Menüs und Popups."""
    if not info['vorhanden']:
        return f"Slot {info['slot']}: (leer)"
    if info['beschaedigt']:
        return f"Slot {info['slot']}: beschädigte Datei"
    teile = [
        f"Zyklus {info['ticks']}",
        f"{info['credits']} Credits",
        info['fortschritt'],
    ]
    text = f"Slot {info['slot']}: " + ' | '.join(teile)
    if info['gespeichert']:
        text += f" ({info['gespeichert']})"
    return text


def speichere_slot(slot, gamestate):
    """Schreibt einen Spielstand in einen Slot."""
    datei = slot_datei(slot)
    with open(datei, 'w', encoding='utf-8') as fh:
        json.dump(gamestate, fh, indent=2, ensure_ascii=False)
    return datei


def lade_slot(slot):
    """Liest einen Spielstand aus einem Slot.

    Rückgabe: geladenes dict oder None, wenn der Slot leer/beschädigt ist.
    """
    datei = slot_datei(slot)
    if not os.path.exists(datei):
        return None
    try:
        with open(datei, 'r', encoding='utf-8') as fh:
            daten = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None
    return daten if isinstance(daten, dict) else None


def loesche_slot(slot):
    """Löscht den Spielstand eines Slots. Rückgabe: True, wenn gelöscht wurde."""
    datei = slot_datei(slot)
    if os.path.exists(datei):
        os.remove(datei)
        return True
    return False
