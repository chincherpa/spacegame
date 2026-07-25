"""
Erfolge (Achievements) und Statistiken.

Statistiken werden im GAMESTATE unter 'Statistik' mitgeführt, Erfolge unter
'Erfolge' (Liste der freigeschalteten Keys). Beide Strukturen werden über
merge_defaults automatisch in alte Spielstände ergänzt.

Reine Logik ohne GUI.
"""

# Zählerfelder der Statistik mit Startwert 0.
STATISTIK_FELDER = (
    'jobs_abgeschlossen',
    'forschungen_abgeschlossen',
    'gebaute_items',
    'reisen_abgeschlossen',
    'missionen_abgeschlossen',
    'mining_abgeschlossen',
    'sonden_gestartet',
    'credits_verdient',
    'credits_ausgegeben',
    'materialien_verkauft',
    'reiseereignisse',
)


def leere_statistik():
    """Frische Statistik mit allen Zählern auf 0."""
    return {feld: 0 for feld in STATISTIK_FELDER}


def statistik(gamestate):
    """Statistik-dict des Spielstands; legt fehlende Felder an."""
    stats = gamestate.setdefault('Statistik', {})
    for feld in STATISTIK_FELDER:
        stats.setdefault(feld, 0)
    return stats


def zaehle(gamestate, feld, menge=1):
    """Erhöht einen Statistikzähler und liefert den neuen Wert."""
    stats = statistik(gamestate)
    if feld not in stats:
        stats[feld] = 0
    stats[feld] += menge
    return stats[feld]


def _stat(gs, feld):
    return gs.get('Statistik', {}).get(feld, 0)


def _inventar(gs, name):
    return gs.get('Inventar', {}).get(name, 0)


# Jeder Erfolg: key, name, beschreibung, bedingung(gs) -> bool,
# optional belohnung {'Credits': n, 'Forschungspunkte': n}.
ERFOLGE = [
    {
        'key': 'erste_forschung',
        'name': 'Wissensdurst',
        'beschreibung': 'Schliesse deine erste Forschung ab.',
        'bedingung': lambda gs: _stat(gs, 'forschungen_abgeschlossen') >= 1,
        'belohnung': {'Forschungspunkte': 3},
    },
    {
        'key': 'fleissige_haende',
        'name': 'Fleissige Hände',
        'beschreibung': 'Schliesse 25 Erd-Jobs ab.',
        'bedingung': lambda gs: _stat(gs, 'jobs_abgeschlossen') >= 25,
        'belohnung': {'Credits': 50},
    },
    {
        'key': 'werkbank',
        'name': 'Serienfertigung',
        'beschreibung': 'Stelle insgesamt 50 Gegenstände in der Werkstatt her.',
        'bedingung': lambda gs: _stat(gs, 'gebaute_items') >= 50,
        'belohnung': {'Credits': 100},
    },
    {
        'key': 'mond_entdeckt',
        'name': 'Ein kleiner Schritt',
        'beschreibung': 'Entdecke den Mond.',
        'bedingung': lambda gs: gs.get('Planeten', {}).get('Mond', {}).get('entdeckt', False),
        'belohnung': {'Forschungspunkte': 5},
    },
    {
        'key': 'mars_entdeckt',
        'name': 'Der rote Planet',
        'beschreibung': 'Entdecke den Mars.',
        'bedingung': lambda gs: gs.get('Planeten', {}).get('Mars', {}).get('entdeckt', False),
        'belohnung': {'Forschungspunkte': 10},
    },
    {
        'key': 'erste_landung',
        'name': 'Fussabdruck',
        'beschreibung': 'Bringe zum ersten Mal Astronauten auf den Mond.',
        'bedingung': lambda gs: gs.get('Astronauten', {}).get('Mond', 0) > 0,
        'belohnung': {'Credits': 100},
    },
    {
        'key': 'vielflieger',
        'name': 'Vielflieger',
        'beschreibung': 'Schliesse 10 Reisen ab.',
        'bedingung': lambda gs: _stat(gs, 'reisen_abgeschlossen') >= 10,
        'belohnung': {'Credits': 150},
    },
    {
        'key': 'alle_missionen',
        'name': 'Mondprogramm',
        'beschreibung': 'Schliesse alle Mondmissionen ab.',
        'bedingung': lambda gs: bool(gs.get('Mondmissionen')) and all(
            m.get('erforscht') for m in gs.get('Mondmissionen', {}).values()
        ),
        'belohnung': {'Forschungspunkte': 50, 'Credits': 500},
    },
    {
        'key': 'schuerfer',
        'name': 'Schürfrechte',
        'beschreibung': 'Schliesse 15 Mining-Expeditionen ab.',
        'bedingung': lambda gs: _stat(gs, 'mining_abgeschlossen') >= 15,
        'belohnung': {'Credits': 200},
    },
    {
        'key': 'goldgraeber',
        'name': 'Goldgräber',
        'beschreibung': 'Besitze gleichzeitig 5 Gold.',
        'bedingung': lambda gs: _inventar(gs, 'Gold') >= 5,
        'belohnung': {'Credits': 250},
    },
    {
        'key': 'haendler',
        'name': 'Handelsreisender',
        'beschreibung': 'Verkaufe 100 Materialien im Shop.',
        'bedingung': lambda gs: _stat(gs, 'materialien_verkauft') >= 100,
        'belohnung': {'Credits': 200},
    },
    {
        'key': 'pechvogel',
        'name': 'Zwischenfälle',
        'beschreibung': 'Erlebe 5 Ereignisse während einer Reise.',
        'bedingung': lambda gs: _stat(gs, 'reiseereignisse') >= 5,
        'belohnung': {'Forschungspunkte': 15},
    },
    {
        'key': 'alle_forschungen',
        'name': 'Allwissend',
        'beschreibung': 'Erforsche alle Technologien.',
        'bedingung': lambda gs: bool(gs.get('Forschung')) and all(
            f.get('erforscht') for f in gs.get('Forschung', {}).values()
        ),
        'belohnung': {'Credits': 1000},
    },
    {
        'key': 'sieg',
        'name': 'Heimat im Orbit',
        'beschreibung': 'Baue die Weltraumstation und gewinne das Spiel.',
        'bedingung': lambda gs: gs.get('Spiel_gewonnen', False),
        'belohnung': {},
    },
]

ERFOLGE_NACH_KEY = {e['key']: e for e in ERFOLGE}


def freigeschaltet(gamestate):
    """Liste der bereits freigeschalteten Erfolgs-Keys."""
    return gamestate.setdefault('Erfolge', [])


def pruefe_erfolge(gamestate):
    """Prüft alle Erfolge und liefert die neu freigeschalteten zurück.

    Der Spielstand wird um die neuen Keys ergänzt; Belohnungen werden NICHT
    hier verrechnet - das übernimmt der Aufrufer, weil Credits und
    Forschungspunkte im Spiel als globale Variablen geführt werden.
    """
    bereits = freigeschaltet(gamestate)
    neu = []
    for erfolg in ERFOLGE:
        if erfolg['key'] in bereits:
            continue
        try:
            if erfolg['bedingung'](gamestate):
                bereits.append(erfolg['key'])
                neu.append(erfolg)
        except (KeyError, TypeError, AttributeError):
            continue
    return neu


def erfolgs_uebersicht(gamestate):
    """Textübersicht aller Erfolge (freigeschaltet und offen)."""
    bereits = set(freigeschaltet(gamestate))
    zeilen = []
    for erfolg in ERFOLGE:
        marke = '✓' if erfolg['key'] in bereits else '✗'
        zeilen.append(f"{marke} {erfolg['name']} - {erfolg['beschreibung']}")
    return '\n'.join(zeilen)


STATISTIK_LABELS = {
    'jobs_abgeschlossen': 'Abgeschlossene Erd-Jobs',
    'forschungen_abgeschlossen': 'Abgeschlossene Forschungen',
    'gebaute_items': 'Hergestellte Gegenstände',
    'reisen_abgeschlossen': 'Abgeschlossene Reisen',
    'missionen_abgeschlossen': 'Abgeschlossene Mondmissionen',
    'mining_abgeschlossen': 'Abgeschlossene Mining-Expeditionen',
    'sonden_gestartet': 'Gestartete Raumsonden',
    'credits_verdient': 'Verdiente Credits',
    'credits_ausgegeben': 'Ausgegebene Credits',
    'materialien_verkauft': 'Verkaufte Materialien',
    'reiseereignisse': 'Ereignisse während Reisen',
}


def statistik_uebersicht(gamestate):
    """Textübersicht der Statistik."""
    stats = statistik(gamestate)
    return '\n'.join(
        f'{STATISTIK_LABELS.get(feld, feld)}: {stats.get(feld, 0)}'
        for feld in STATISTIK_FELDER
    )
