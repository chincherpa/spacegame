"""
Spielt das Spiel mit einem einfachen Bot von Zyklus 0 bis zum Sieg durch.

Der Bot benutzt nur die Funktionen, die auch die Buttons auslösen. Der Test
belegt, dass das Spiel ohne Sackgasse gewinnbar ist und wie lange es dauert.
"""
import config

MAX_ZYKLEN = 4000

# Arbeiter-Aufteilung (Summe der Arbeiter = 10)
JOB_PLAN = {'Laborarbeit': 3, 'Bergbau': 2, 'Wasseraufbereitung': 2, 'Staubsammlung': 1}


class Bot:
    def __init__(self, spiel):
        self.s = spiel

    # -- Grundversorgung ------------------------------------------------
    def jobs(self):
        laufend = [j.name for j in self.s.erde_jobs_aktiv]
        for name, soll in JOB_PLAN.items():
            for _ in range(soll - laufend.count(name)):
                self.s.starte_erde_job(name)

    def forschung(self):
        if self.s.bForschung_aktiv:
            return
        for name, daten in self.s.SCIENCE.items():
            if not self.s.GAMESTATE['Forschung'][name]['erforscht']:
                if self.s.iForschungspunkte >= daten['kosten']:
                    self.s.erforsche(name)
                return

    def brauche(self, name, menge):
        """Sorgt dafür, dass `menge` von `name` auf der Erde vorhanden ist."""
        fehlt = menge - self.s.get_bestand(name)
        if fehlt <= 0:
            return True
        if self.s.bBauen_aktiv or name not in self.s.GAMESTATE['Werkstatt']:
            return False                     # warten (Werkstatt belegt oder Rohstoff)
        if not self.s.GAMESTATE['Forschung'][name]['erforscht']:
            return False
        for zutat, pro_stueck in self.s.GAMESTATE['Werkstatt'][name]['material'].items():
            if not self.brauche(zutat, pro_stueck * fehlt):
                return False
        self.s.baue(name, fehlt)
        return False

    # -- Etappen: jede liefert True, sobald sie erledigt ist --------------
    def planet_entdecken(self, planet):
        gs = self.s.GAMESTATE
        if gs['Planeten'][planet]['entdeckt']:
            return True
        if self.s.raumsonde_flug is None and self.brauche('Raumsonde', 1):
            self.s.starte_raumsonde()
        return False

    def fliege(self, typ, ziel, astronauten, fracht, treibstoff, wasser):
        """Bringt Astronauten und Fracht ans Ziel; True, sobald sie dort sind.

        `treibstoff` ist der Verbrauch des Hinflugs; Treibstoff für den Rückflug
        steckt in `fracht`.
        """
        gs = self.s.GAMESTATE
        if gs['Astronauten'][ziel] >= astronauten:
            return True
        if self.s.aktive_reisen:
            return False
        bereit = all([
            self.brauche(typ, 1),
            self.brauche('Treibstoff', treibstoff + fracht.get('Treibstoff', 0)),
            self.s.get_bestand('Wasser') >= wasser,
            *[self.brauche(material, menge) for material, menge in fracht.items() if material != 'Treibstoff'],
        ])
        if bereit:
            assert self.s.starte_reise(typ, 'Erde', ziel, astronauten, fracht)
        return False

    def hole(self, typ, planet, material, menge):
        """Baut `material` auf `planet` ab und fliegt es unbemannt zur Erde."""
        if self.s.get_bestand(material) >= menge:
            return True
        if self.s.aktive_reisen:
            return False
        if self.s.lager(planet).get(material, 0) >= menge:
            assert self.s.starte_reise(typ, planet, 'Erde', 0, {material: menge})
        elif not self.s.mining_aktiv:
            assert self.s.starte_mining(planet)
        return False

    def mondgestein(self):
        if self.s.get_bestand('Mondgestein') >= 2 or self.s.get_bestand('Mondbasen Bauplan') >= 1:
            return True
        if not self.fliege('Mondlander', 'Mond', 2, {'Werkzeug': 1, 'Treibstoff': 1}, treibstoff=1, wasser=2):
            return False
        return self.hole('Mondlander', 'Mond', 'Mondgestein', 2)

    def gold(self):
        if self.s.get_bestand('Gold') >= 3:
            return True
        fracht = {'Werkzeug': 3, 'Baumaterial': 3, 'Treibstoff': 6}
        if not self.fliege('Rakete', 'Mars', 2, fracht, treibstoff=6, wasser=6):
            return False
        return self.hole('Rakete', 'Mars', 'Gold', 3)

    def station(self):
        if self.s.GAMESTATE['Spiel_gewonnen']:
            return True
        self.brauche('Weltraumstation', 1)
        return False

    def spiele(self):
        etappen = [
            lambda: self.planet_entdecken('Mond'),
            lambda: self.planet_entdecken('Mars'),
            self.mondgestein,
            self.gold,
            self.station,
        ]
        protokoll = []
        while etappen and self.s.iTicks < MAX_ZYKLEN:
            self.jobs()
            self.forschung()
            if etappen[0]():
                etappen.pop(0)
                protokoll.append(self.s.iTicks)
                continue
            self.s.verarbeite_tick()
        return protokoll


def test_spiel_ist_von_anfang_bis_sieg_spielbar(spiel):
    protokoll = Bot(spiel).spiele()
    gs = spiel.GAMESTATE
    print(f'\nEtappen erreicht in Zyklus: {protokoll} '
          f'(~{spiel.iTicks * config.TICK_INTERVAL / 60:.0f} Minuten Echtzeit)')

    assert gs['Spiel_gewonnen'], f'Nach {MAX_ZYKLEN} Zyklen nicht gewonnen, Etappen: {protokoll}'
    assert all(f['erforscht'] for f in gs['Forschung'].values())
    assert 'sieg' in gs['Erfolge']

    # Nichts darf ins Minus laufen
    assert all(menge >= 0 for menge in gs['Inventar'].values()), gs['Inventar']
    assert all(menge >= 0 for vorrat in gs['Lager'].values() for menge in vorrat.values())
    assert all(anzahl >= 0 for anzahl in gs['Astronauten'].values())
    assert all(typ['Anzahl'] >= 0 for planet in gs['Raumschiffe'].values() for typ in planet.values())
    assert sum(gs['Astronauten'].values()) == 10
    assert spiel.iCredits >= 0 and spiel.iForschungspunkte >= 0

    # Das Tutorial führt bis zum Schluss
    import tutorial
    spiel.aktualisiere_ziel_anzeige()
    assert tutorial.naechster_schritt(gs) is None


def test_spielstand_nach_sieg_laesst_sich_laden(spiel):
    Bot(spiel).spiele()
    spiel.dump_gamestate(2)
    assert spiel.lade_spielstand(2)
    assert spiel.GAMESTATE['Spiel_gewonnen']
    spiel.verarbeite_tick()
