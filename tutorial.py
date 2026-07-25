"""
Tutorial und kontextabhängige Hilfe.

Das Tutorial ist kein starrer Klick-durch-Assistent, sondern eine Liste von
Zielen. Der jeweils erste noch nicht erfüllte Schritt wird als "Nächstes Ziel"
im HQ angezeigt und passt sich damit automatisch dem Spielstand an - auch nach
dem Laden eines alten Spielstands.

Reine Logik ohne GUI, damit sie testbar bleibt.
"""


def _erforscht(gs, name):
    return gs.get('Forschung', {}).get(name, {}).get('erforscht', False)


def _im_inventar(gs, name, menge=1):
    return gs.get('Inventar', {}).get(name, 0) >= menge


def _entdeckt(gs, planet):
    return gs.get('Planeten', {}).get(planet, {}).get('entdeckt', False)


def _raumschiffe(gs, typ):
    return sum(
        planet.get(typ, {}).get('Anzahl', 0)
        for planet in gs.get('Raumschiffe', {}).values()
    )


# Reihenfolge = Spielverlauf. Der erste Schritt mit erfuellt(gs) == False ist
# das aktuelle Ziel.
TUTORIAL_SCHRITTE = [
    {
        'key': 'erste_arbeit',
        'titel': 'Arbeiter einsetzen',
        'text': ('Im Tab "Arbeit" setzt du deine Arbeiter ein. "Laborarbeit" liefert '
                 'Forschungspunkte, "Bergbau" liefert Roheisen. Ohne Forschungspunkte '
                 'geht nichts weiter.'),
        'erfuellt': lambda gs: gs.get('Forschungspunkte', 0) >= 5 or _erforscht(gs, 'Eisenbarren'),
    },
    {
        'key': 'eisenbarren',
        'titel': 'Eisenbarren erforschen',
        'text': ('Erforsche im Tab "Forschung" die Eisenbarren. Damit schaltest du die '
                 'Werkstatt frei und kannst Rohstoffe verarbeiten.'),
        'erfuellt': lambda gs: _erforscht(gs, 'Eisenbarren'),
    },
    {
        'key': 'werkzeug',
        'titel': 'Werkzeug erforschen und bauen',
        'text': ('Werkzeug wird für Raumsonden, Missionen und Mining gebraucht. '
                 'Erforsche es und stelle in der Werkstatt welches her.'),
        'erfuellt': lambda gs: _erforscht(gs, 'Werkzeug'),
    },
    {
        'key': 'treibstoff',
        'titel': 'Treibstoff erforschen',
        'text': ('Ohne Treibstoff fliegt kein Raumschiff. Erforsche Treibstoff und '
                 'produziere ihn danach in der Werkstatt.'),
        'erfuellt': lambda gs: _erforscht(gs, 'Treibstoff'),
    },
    {
        'key': 'raumsonde_bauen',
        'titel': 'Raumsonde bauen',
        'text': ('Erforsche die Raumsonde und baue sie in der Werkstatt. Sie kostet '
                 '5 Eisenbarren und 5 Werkzeug.'),
        'erfuellt': lambda gs: _im_inventar(gs, 'Raumsonde') or _entdeckt(gs, 'Mond'),
    },
    {
        'key': 'sonde_starten',
        'titel': 'Raumsonde starten',
        'text': ('Starte die Raumsonde im HQ über "Starte Raumsonde". Sie entdeckt '
                 'zuerst den Mond und danach den Mars.'),
        'erfuellt': lambda gs: _entdeckt(gs, 'Mond'),
    },
    {
        'key': 'mondlander',
        'titel': 'Mondlander bauen',
        'text': ('Erforsche und baue einen Mondlander. Erst damit kommen Astronauten '
                 'zum Mond - und nur dort funktionieren Mondmissionen und Mining.'),
        'erfuellt': lambda gs: _raumschiffe(gs, 'Mondlander') > 0 or gs.get('Astronauten', {}).get('Mond', 0) > 0,
    },
    {
        'key': 'zum_mond',
        'titel': 'Astronauten zum Mond bringen',
        'text': ('Plane im Tab "Reisen" einen Flug Erde → Mond mit Astronauten an Bord. '
                 'Vergiss den Treibstoff und das Wasser für die Lebenserhaltung nicht.'),
        'erfuellt': lambda gs: gs.get('Astronauten', {}).get('Mond', 0) > 0,
    },
    {
        'key': 'mondmission',
        'titel': 'Erste Mondmission abschliessen',
        'text': ('Mit Astronauten auf dem Mond kannst du Mondmissionen starten. Sie '
                 'bringen Credits, Forschungspunkte und seltene Materialien.'),
        'erfuellt': lambda gs: any(
            m.get('erforscht') for m in gs.get('Mondmissionen', {}).values()
        ),
    },
    {
        'key': 'bauplan',
        'titel': 'Mondbasen Bauplan herstellen',
        'text': ('Erforsche den Mondbasen Bauplan und stelle ihn in der Werkstatt her. '
                 'Er wird für die Weltraumstation gebraucht (benötigt Mondgestein).'),
        'erfuellt': lambda gs: _im_inventar(gs, 'Mondbasen Bauplan'),
    },
    {
        'key': 'weltraumstation',
        'titel': 'Weltraumstation bauen',
        'text': ('Das Ziel des Spiels: Baue die Weltraumstation. Du brauchst dafür '
                 '5 Mondlander, 100 Eisenbarren, 10 Werkzeug und 1 Mondbasen Bauplan.'),
        'erfuellt': lambda gs: gs.get('Spiel_gewonnen', False),
    },
]


def naechster_schritt(gamestate):
    """Erster noch nicht erfüllter Tutorial-Schritt - oder None, wenn alles erledigt."""
    for schritt in TUTORIAL_SCHRITTE:
        try:
            if not schritt['erfuellt'](gamestate):
                return schritt
        except (KeyError, TypeError, AttributeError):
            # Ein unvollständiger Spielstand darf das Tutorial nicht abstürzen lassen.
            return schritt
    return None


def fortschritt(gamestate):
    """(erledigte Schritte, Gesamtzahl) für eine Fortschrittsanzeige."""
    gesamt = len(TUTORIAL_SCHRITTE)
    erledigt = 0
    for schritt in TUTORIAL_SCHRITTE:
        try:
            if schritt['erfuellt'](gamestate):
                erledigt += 1
            else:
                break
        except (KeyError, TypeError, AttributeError):
            break
    return erledigt, gesamt


def ziel_text(gamestate):
    """Fertig formatierter Text für die "Nächstes Ziel"-Anzeige im HQ."""
    schritt = naechster_schritt(gamestate)
    erledigt, gesamt = fortschritt(gamestate)
    if schritt is None:
        return f'Alle Ziele erreicht ({gesamt}/{gesamt}) - viel Spass beim Weiterspielen!'
    return f'[{erledigt}/{gesamt}] {schritt["titel"]}: {schritt["text"]}'


# =============================================================================
# KONTEXTHILFE PRO TAB
# =============================================================================

HILFE_TEXTE = {
    'tab_HQ': (
        'HQ - Übersicht\n\n'
        'Hier siehst du, wo deine Astronauten sind, welche Reisen laufen und was '
        'dein nächstes Ziel ist.\n\n'
        'Die Raumsonde startest du von hier aus. Sie entdeckt zuerst den Mond, '
        'danach den Mars. Jeder weitere Flug bringt Forschungspunkte.'
    ),
    'tab_Arbeit': (
        'Arbeit - Erde\n\n'
        'Arbeiter erledigen Jobs, die Rohstoffe und Forschungspunkte liefern. '
        'Jeder Job bindet Arbeiter für seine Laufzeit; oben siehst du, wie viele '
        'noch frei sind.\n\n'
        'Laborarbeit ist am Anfang die wichtigste Quelle für Forschungspunkte.'
    ),
    'tab_Forschung': (
        'Forschung\n\n'
        'Forschung kostet Forschungspunkte und Zeit. Technologien bauen '
        'aufeinander auf - die Voraussetzung steht in der Beschreibung.\n\n'
        'Läuft bereits eine Forschung, kannst du weitere in die Warteschlange '
        'stellen. Ein Abbruch erstattet die Forschungspunkte zurück.'
    ),
    'tab_Werkstatt': (
        'Werkstatt\n\n'
        'Hier stellst du aus Rohstoffen Waren, Raumschiffe und am Ende die '
        'Weltraumstation her. Die Materialien werden sofort beim Start abgezogen.\n\n'
        '"Rohstoffe gesamt" zeigt die komplette Produktionskette bis zu den '
        'Grundstoffen. Ein Abbruch gibt die Materialien für noch nicht fertige '
        'Stücke zurück.'
    ),
    'tab_Inventar': (
        'Inventar\n\n'
        'Alle Materialien und Raumschiffe mit Bestand. Materialien mit Bestand 0 '
        'werden ausgeblendet und tauchen automatisch auf, sobald du welche findest.'
    ),
    'tab_Shop': (
        'Shop\n\n'
        'Kaufen: Rohstoffe und (erforschte) Raumschiffe gegen Credits.\n'
        'Verkaufen: überschüssige Materialien zu Geld machen - der Verkaufspreis '
        'liegt unter dem Einkaufspreis.\n\n'
        'Credits brauchst du vor allem für Mondmissionen.'
    ),
    'tab_Planeten': (
        'Planeten\n\n'
        'Übersicht über Erde, Mond und Mars sowie die dort stationierten '
        'Astronauten. Neue Planeten entdeckst du mit der Raumsonde.'
    ),
    'tab_Reisen': (
        'Reisen\n\n'
        'Wähle Start, Ziel und Raumschiff. Reisen verbrauchen Treibstoff '
        '(abhängig von der Entfernung) und Wasser für die Lebenserhaltung der '
        'Astronauten.\n\n'
        'Achtung auf die Reichweite: Der Mondlander schafft nur Entfernung 1. '
        'Unterwegs kann es Zwischenfälle geben - Pannen, Funde oder günstigen '
        'Sonnenwind.'
    ),
    'tab_Mondmissionen': (
        'Mondmissionen\n\n'
        'Missionen laufen parallel im Hintergrund und benötigen Astronauten auf '
        'dem Mond, Credits und teilweise Material.\n\n'
        'Jede Mission kann einmal abgeschlossen werden und bringt dann '
        'Forschungspunkte, Credits und seltene Materialien.'
    ),
    'tab_Mining': (
        'Mining\n\n'
        'Expeditionen bauen Rohstoffe auf Mond und Mars ab. Sie benötigen '
        'Astronauten vor Ort und Werkzeug.\n\n'
        'Mining ist die verlässlichste Quelle für Mondgestein und seltene '
        'Mineralien.'
    ),
}

HILFE_ALLGEMEIN = (
    'Spacegame - Kurzanleitung\n\n'
    'Ziel: Baue die Weltraumstation.\n\n'
    'Der Weg dorthin:\n'
    '1. Arbeiter auf der Erde einsetzen (Tab "Arbeit") - liefert Rohstoffe und '
    'Forschungspunkte.\n'
    '2. Technologien erforschen (Tab "Forschung").\n'
    '3. In der Werkstatt produzieren - vom Eisenbarren bis zur Rakete.\n'
    '4. Raumsonde bauen und im HQ starten: sie entdeckt Mond und Mars.\n'
    '5. Mit Mondlander/Rakete Astronauten und Fracht bewegen (Tab "Reisen").\n'
    '6. Mondmissionen und Mining bringen Credits, Forschungspunkte und seltene '
    'Materialien.\n'
    '7. Mondbasen Bauplan herstellen und die Weltraumstation bauen - gewonnen.\n\n'
    'Das Spiel läuft in Echtzeit: alle paar Sekunden vergeht ein Zyklus. '
    'Es wird automatisch gespeichert; über "File" kannst du zusätzlich in drei '
    'Slots speichern und laden.\n\n'
    'Tipp: Die Anzeige "Nächstes Ziel" im HQ sagt dir jederzeit, was als '
    'Nächstes ansteht.'
)


def hilfe_fuer_tab(tab_key):
    """Hilfetext zu einem Tab; fällt auf die allgemeine Hilfe zurück."""
    return HILFE_TEXTE.get(tab_key, HILFE_ALLGEMEIN)
