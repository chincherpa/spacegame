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
                 'Der Flug kostet Treibstoff und Wasser. Nimm Werkzeug und 1 Treibstoff als '
                 'Fracht mit: Missionen, Mining und der Rückflug verbrauchen Material aus '
                 'dem Mond-Lager.'),
        'erfuellt': lambda gs: gs.get('Astronauten', {}).get('Mond', 0) > 0,
    },
    {
        'key': 'mondmission',
        'titel': 'Mondgestein zur Erde bringen',
        'text': ('Mit freien Astronauten und Werkzeug im Mond-Lager kannst du im Tab '
                 '"Mining" Mondgestein abbauen. Der Ertrag liegt im Mond-Lager: lade '
                 '2 Mondgestein als Fracht ein und fliege sie zur Erde (das Schiff '
                 'braucht dafür Treibstoff im Mond-Lager).'),
        'erfuellt': lambda gs: (
            _im_inventar(gs, 'Mondgestein', 2) or _im_inventar(gs, 'Mondbasen Bauplan')
            or gs.get('Spiel_gewonnen', False)
        ),
    },
    {
        'key': 'bauplan',
        'titel': 'Mondbasen Bauplan herstellen',
        'text': ('Erforsche den Mondbasen Bauplan und stelle ihn in der Werkstatt her. '
                 'Er wird für die Weltraumstation gebraucht (benötigt Mondgestein).'),
        'erfuellt': lambda gs: _im_inventar(gs, 'Mondbasen Bauplan') or gs.get('Spiel_gewonnen', False),
    },
    {
        'key': 'mars_entdecken',
        'titel': 'Mars entdecken',
        'text': ('Für die Weltraumstation brauchst du Gold - das gibt es nur auf dem '
                 'Mars. Starte eine zweite Raumsonde, um ihn zu entdecken.'),
        'erfuellt': lambda gs: _entdeckt(gs, 'Mars') or gs.get('Spiel_gewonnen', False),
    },
    {
        'key': 'gold',
        'titel': 'Gold vom Mars holen',
        'text': ('Nur die Rakete erreicht den Mars. Bringe 2 Astronauten sowie je 3 Werkzeug '
                 'und Baumaterial und 6 Treibstoff für den Rückflug als Fracht hin. Starte im '
                 'Tab "Mining" Expeditionen, bis 3 Gold im Mars-Lager liegen, und fliege '
                 'sie zur Erde.'),
        'erfuellt': lambda gs: _im_inventar(gs, 'Gold', 3) or gs.get('Spiel_gewonnen', False),
    },
    {
        'key': 'weltraumstation',
        'titel': 'Weltraumstation bauen',
        'text': ('Das Ziel des Spiels: Baue die Weltraumstation. Du brauchst dafür '
                 '5 Mondlander (auf der Erde), 100 Eisenbarren, 10 Werkzeug, '
                 '1 Mondbasen Bauplan und 3 Gold.'),
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
        'noch frei sind. Mit dem Haken "automatisch wiederholen" startet jeder '
        'fertige Job sofort neu.\n\n'
        'Laborarbeit ist am Anfang die wichtigste Quelle für Forschungspunkte.'
    ),
    'tab_Forschung': (
        'Forschung\n\n'
        'Forschung kostet Forschungspunkte und Zeit. Technologien bauen '
        'aufeinander auf - die Voraussetzung steht in der Beschreibung.\n\n'
        'Läuft bereits eine Forschung, kannst du weitere in die Warteschlange '
        'stellen; sie starten, sobald die Punkte reichen. Ein Abbruch erstattet '
        'die Forschungspunkte zurück.'
    ),
    'tab_Werkstatt': (
        'Werkstatt\n\n'
        'Hier stellst du aus Rohstoffen Waren, Raumschiffe und am Ende die '
        'Weltraumstation her. Die Materialien werden sofort beim Start abgezogen.\n\n'
        '"Rohstoffe gesamt" zeigt die komplette Produktionskette bis zu den '
        'Grundstoffen. Ein Abbruch gibt die Materialien für noch nicht fertige '
        'Stücke zurück.\n\n'
        'Läuft bereits ein Bau, kannst du weitere Aufträge in die Warteschlange '
        'stellen. Ihr Material wird erst beim Start abgezogen.'
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
        'Übersicht über Erde, Mond und Mars: Astronauten, Raumschiffe und das '
        'Lager vor Ort. Neue Planeten entdeckst du mit der Raumsonde.'
    ),
    'tab_Reisen': (
        'Reisen\n\n'
        'Wähle Start, Ziel und Raumschiff. Reisen verbrauchen Treibstoff '
        '(abhängig von der Entfernung) und Wasser für die Lebenserhaltung der '
        'Astronauten - beides aus dem Vorrat des Startplaneten. Für den Rückflug '
        'von Mond oder Mars muss der Treibstoff also als Fracht mit.\n\n'
        'Fracht landet im Lager des Zielplaneten. Nur von dort können Missionen '
        'und Mining sie verbrauchen. Umgekehrt liegen deren Erträge im Lager vor '
        'Ort und müssen zur Erde geflogen werden, bevor du sie verbauen oder '
        'verkaufen kannst. Astronauten in laufenden Missionen oder Expeditionen '
        'können nicht mitfliegen.\n\n'
        'Achtung auf die Reichweite: Der Mondlander schafft nur Entfernung 1. '
        'Unterwegs kann es Zwischenfälle geben - Pannen, Funde oder günstigen '
        'Sonnenwind.'
    ),
    'tab_Mondmissionen': (
        'Mondmissionen\n\n'
        'Missionen laufen parallel im Hintergrund. Sie binden freie Astronauten '
        'auf dem Mond, kosten Credits und verbrauchen Material aus dem Mond-Lager '
        '(als Fracht hinbringen). Manche bauen auf anderen Missionen auf.\n\n'
        'Jede Mission kann einmal abgeschlossen werden. Mondgestein und '
        'Mineralien landen im Mond-Lager, Upgrades wirken sofort und dauerhaft:\n'
        '- Astronaut_Erfahrung: mehr Ertrag beim Mining\n'
        '- Mondstation_Modul: kürzere Mond-Expeditionen\n'
        '- Lebenserhaltung_Upgrade: weniger Wasser auf Reisen\n'
        '- Kommunikations_Upgrade: laufend zusätzliche Forschungspunkte'
    ),
    'tab_Mining': (
        'Mining\n\n'
        'Expeditionen bauen Rohstoffe auf Mond und Mars ab. Jede bindet 2 freie '
        'Astronauten vor Ort und verbraucht Material aus dem Lager des Planeten. '
        'Der Ertrag landet im selben Lager - hole ihn mit einem Raumschiff ab.\n\n'
        'Der Mond liefert Mondgestein und seltene Mineralien, der Mars Roheisen '
        'und Gold. Gold brauchst du für die Weltraumstation.'
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
    '   Fracht landet im Lager des Zielplaneten. Treibstoff für den Rückflug '
    'muss als Fracht mit.\n'
    '6. Mondmissionen und Mining bringen Credits, Forschungspunkte, Mondgestein '
    'und Upgrades. Sie verbrauchen Material aus dem Lager vor Ort; ihre Erträge '
    'liegen ebenfalls dort und müssen zur Erde geflogen werden.\n'
    '7. Mit der Rakete zum Mars: dort gibt es Gold.\n'
    '8. Mondbasen Bauplan herstellen und die Weltraumstation bauen - gewonnen.\n\n'
    'Das Spiel läuft in Echtzeit: alle paar Sekunden vergeht ein Zyklus. '
    'Es wird automatisch in den aktiven Slot gespeichert - auch laufende '
    'Forschung und Bauaufträge. Über "File" kannst du in drei Slots speichern '
    'und laden oder ein neues Spiel beginnen.\n\n'
    'Tipp: Die Anzeige "Nächstes Ziel" im HQ sagt dir jederzeit, was als '
    'Nächstes ansteht.\n\n'
    'Tastenkürzel: Strg+S speichert in den aktiven Slot, F1 zeigt die Hilfe zum aktuellen Tab.'
)


def hilfe_fuer_tab(tab_key):
    """Hilfetext zu einem Tab; fällt auf die allgemeine Hilfe zurück."""
    return HILFE_TEXTE.get(tab_key, HILFE_ALLGEMEIN)
