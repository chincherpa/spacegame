"""
Regressionstests für die Konsistenz der Spieldaten.

Diese Tests decken die Fehlerklasse ab, die das Spiel unspielbar gemacht hat:
Rezepte und Belohnungen, die auf Dinge verweisen, die es so nicht gibt, sowie
Kosten, die im Verhältnis zum restlichen Spiel unerreichbar sind.
"""
import pytest

import config
from actions import ACTIONS
from gamestate import GAMESTATE
from materials import MATERIALS
from mining import MINING_EXPEDITIONEN
from science import SCIENCE
from shop import SHOP, SHOP_MATERIALIEN

# Gegenstände, die in GAMESTATE['Raumschiffe'] statt im Inventar geführt werden.
RAUMSCHIFF_TYPEN = {'Mondlander', 'Rakete'}

WERKSTATT = GAMESTATE['Werkstatt']
INVENTAR = GAMESTATE['Inventar']


def _ist_lagerbar(name):
    """Kann dieser Gegenstand überhaupt irgendwo gehalten werden?"""
    return name in INVENTAR or name in RAUMSCHIFF_TYPEN


class TestWerkstattRezepte:
    """Jedes Rezept muss aus Zutaten bestehen, die man auch bekommen kann."""

    @pytest.mark.parametrize('item', sorted(WERKSTATT))
    def test_zutaten_sind_beschaffbar(self, item):
        for zutat in WERKSTATT[item]['material']:
            assert _ist_lagerbar(zutat) or zutat in WERKSTATT, (
                f"Rezept '{item}' braucht '{zutat}', das weder im Inventar noch "
                f'als Raumschiff noch als Werkstatt-Produkt existiert'
            )

    @pytest.mark.parametrize('item', sorted(WERKSTATT))
    def test_zutaten_sind_in_materials_beschrieben(self, item):
        for zutat in WERKSTATT[item]['material']:
            assert zutat in MATERIALS, f"Rezept '{item}': '{zutat}' fehlt in materials.py"

    @pytest.mark.parametrize('item', sorted(WERKSTATT))
    def test_dauer_und_mengen_sind_positiv(self, item):
        assert WERKSTATT[item]['dauer'] > 0
        for zutat, menge in WERKSTATT[item]['material'].items():
            assert menge > 0, f"{item}: {zutat} hat Menge {menge}"

    @pytest.mark.parametrize('item', sorted(WERKSTATT))
    def test_beschreibung_ist_gepflegt(self, item):
        beschreibung = WERKSTATT[item]['beschreibung']
        assert beschreibung and not beschreibung.startswith('Text Beschreibung'), (
            f"'{item}' hat noch einen Platzhaltertext"
        )

    def test_kein_rezept_baut_sich_selbst(self):
        for item, daten in WERKSTATT.items():
            assert item not in daten['material'], f"'{item}' ist seine eigene Zutat"

    def test_rezepte_sind_zyklenfrei(self):
        """Sonst würde berechne_rohstoffe() endlos rekursieren."""
        def pruefe(item, pfad):
            if item not in WERKSTATT:
                return
            assert item not in pfad, f'Zyklus im Rezeptbaum: {" -> ".join(pfad + [item])}'
            for zutat in WERKSTATT[item]['material']:
                pruefe(zutat, pfad + [item])

        for item in WERKSTATT:
            pruefe(item, [])


class TestForschungUndWerkstatt:
    """Forschungsbaum und Herstellbarkeit müssen zusammenpassen."""

    @pytest.mark.parametrize('name', sorted(SCIENCE))
    def test_forschung_hat_einen_gamestate_eintrag(self, name):
        assert name in GAMESTATE['Forschung']

    @pytest.mark.parametrize('name', sorted(SCIENCE))
    def test_voraussetzung_existiert(self, name):
        voraussetzung = SCIENCE[name].get('erforschbar nach', '')
        if voraussetzung:
            assert voraussetzung in SCIENCE, (
                f"'{name}' verlangt unbekannte Voraussetzung '{voraussetzung}'"
            )

    @pytest.mark.parametrize('name', sorted(SCIENCE))
    def test_erforschtes_ist_auch_herstellbar(self, name):
        """Die Werkstatt zeigt für jede Forschung einen Bauen-Button.

        Fehlt das Rezept, führt der Button ins Leere (war bei 'Treibstoff' so).
        """
        assert name in WERKSTATT, f"Forschung '{name}' hat kein Werkstatt-Rezept"

    def test_kein_zyklus_im_forschungsbaum(self):
        for name in SCIENCE:
            gesehen, aktuell = set(), name
            while aktuell:
                assert aktuell not in gesehen, f'Zyklus im Forschungsbaum bei {name}'
                gesehen.add(aktuell)
                aktuell = SCIENCE[aktuell].get('erforschbar nach', '')

    def test_genau_eine_wurzelforschung(self):
        wurzeln = [n for n, d in SCIENCE.items() if not d.get('erforschbar nach', '')]
        assert wurzeln == ['Eisenbarren']

    @pytest.mark.parametrize('name', sorted(SCIENCE))
    def test_kosten_bleiben_in_erreichbarer_groessenordnung(self, name):
        """Rakete/Weltraumstation kosteten einmal 2000 bzw. 5000 Forschungspunkte.

        Bei ~2 Forschungspunkten pro Erd-Job wäre das Endspiel unerreichbar.
        """
        assert 0 < SCIENCE[name]['kosten'] <= 200, (
            f"'{name}' kostet {SCIENCE[name]['kosten']} Forschungspunkte - "
            f'das ist gegenüber dem Rest des Spiels unerreichbar'
        )

    @pytest.mark.parametrize('name', sorted(SCIENCE))
    def test_dauer_ist_positiv(self, name):
        assert SCIENCE[name]['dauer'] > 0


class TestSiegbedingung:
    """Die Weltraumstation ist das Spielziel und muss tatsächlich baubar sein."""

    def test_weltraumstation_ist_erforschbar_und_baubar(self):
        assert 'Weltraumstation' in SCIENCE
        assert 'Weltraumstation' in WERKSTATT

    def test_alle_zutaten_sind_herstellbar_oder_vorhanden(self):
        for zutat in WERKSTATT['Weltraumstation']['material']:
            assert zutat in WERKSTATT or _ist_lagerbar(zutat), (
                f"Weltraumstation braucht '{zutat}', das nirgends herkommt"
            )

    def test_mondbasen_bauplan_wird_wirklich_gebraucht(self):
        """materials.py sagt, der Bauplan sei für die Weltraumstation nötig."""
        assert 'Weltraumstation' in MATERIALS['Mondbasen Bauplan']['benötigt für']
        assert 'Mondbasen Bauplan' in WERKSTATT['Weltraumstation']['material']

    def test_raumschiff_zutaten_kommen_aus_dem_raumschiff_pool(self):
        """Gebaute Mondlander landen in GAMESTATE['Raumschiffe'], nicht im Inventar.

        Das Rezept darf sie deshalb nicht im Inventar erwarten - genau daran
        war die Weltraumstation vorher nicht baubar.
        """
        zutaten = set(WERKSTATT['Weltraumstation']['material'])
        for typ in zutaten & RAUMSCHIFF_TYPEN:
            assert typ not in INVENTAR, (
                f"'{typ}' darf keinen Inventarplatz haben, sonst sind die Bestände doppelt"
            )
            for planet in GAMESTATE['Raumschiffe'].values():
                assert typ in planet


class TestBelohnungen:
    """Belohnungen dürfen keine Gegenstände erfinden, die es nicht gibt."""

    @pytest.mark.parametrize('planet', sorted(MINING_EXPEDITIONEN))
    def test_mining_belohnungen_haben_einen_platz(self, planet):
        for ressource in MINING_EXPEDITIONEN[planet]['belohnung']:
            if ressource == 'Forschungspunkte':
                continue
            assert ressource in INVENTAR, (
                f"Mining {planet} belohnt '{ressource}' - dafür gibt es keinen Inventarplatz"
            )

    @pytest.mark.parametrize('planet', sorted(MINING_EXPEDITIONEN))
    def test_mining_anforderungen_sind_echte_materialien(self, planet):
        for key in MINING_EXPEDITIONEN[planet]:
            if key.startswith('benötigt_') and key != 'benötigt_astronauten':
                ressource = key.replace('benötigt_', '').title()
                assert ressource in INVENTAR, f'Mining {planet} verlangt unbekanntes {ressource}'

    @pytest.mark.parametrize('mission', sorted(ACTIONS))
    def test_missionsbelohnungen_haben_einen_platz(self, mission):
        for ressource in ACTIONS[mission]['belohnung']:
            if ressource in ('Forschungspunkte', 'Credits'):
                continue
            assert ressource in INVENTAR, (
                f"Mission '{mission}' belohnt '{ressource}' ohne Inventarplatz"
            )

    @pytest.mark.parametrize('mission', sorted(ACTIONS))
    def test_missionsanforderungen_sind_echte_materialien(self, mission):
        for key in ACTIONS[mission]:
            if key.startswith('benötigt_') and key != 'benötigt_astronauten':
                ressource = key.replace('benötigt_', '').title()
                assert ressource in INVENTAR, (
                    f"Mission '{mission}' verlangt '{ressource}', das es nicht gibt"
                )

    @pytest.mark.parametrize('material', sorted(INVENTAR))
    def test_jedes_inventarmaterial_ist_beschrieben(self, material):
        assert material in MATERIALS, f"'{material}' hat keine Beschreibung in materials.py"


class TestMondmissionen:
    def test_ui_missionen_und_gamestate_passen_zusammen(self):
        """GAMESTATE['Mondmissionen'] speichert den Abschluss - beide Listen müssen
        deckungsgleich sein, sonst gibt es unspeicherbare oder tote Missionen."""
        assert set(ACTIONS) == set(GAMESTATE['Mondmissionen'])

    @pytest.mark.parametrize('mission', sorted(ACTIONS))
    def test_mission_lohnt_sich(self, mission):
        daten = ACTIONS[mission]
        assert daten['belohnung'].get('Credits', 0) > daten['kosten'], (
            f"'{mission}' kostet mehr Credits als sie einbringt"
        )

    @pytest.mark.parametrize('mission', sorted(ACTIONS))
    def test_kosten_bleiben_im_rahmen_der_wirtschaft(self, mission):
        """Missionen kosteten einmal 5000-25000 Credits bei +1 Credit / 20 Zyklen."""
        assert 0 < ACTIONS[mission]['kosten'] <= 1000

    @pytest.mark.parametrize('mission', sorted(ACTIONS))
    def test_dauer_und_astronauten_sind_positiv(self, mission):
        assert ACTIONS[mission]['dauer'] > 0
        assert ACTIONS[mission].get('benötigt_astronauten', 0) > 0


class TestShopUndWerte:
    @pytest.mark.parametrize('name', sorted(SHOP))
    def test_kaufbare_raumschiffe_sind_erforschbar(self, name):
        assert name in SCIENCE, f"Shop verkauft '{name}', das nicht erforschbar ist"

    @pytest.mark.parametrize('name', sorted(SHOP_MATERIALIEN))
    def test_kaufbare_materialien_existieren(self, name):
        assert name in INVENTAR

    @pytest.mark.parametrize('material', sorted(INVENTAR))
    def test_inventarmaterialien_haben_einen_wert(self, material):
        """Ohne Wert zählt das Material nicht zum Inventarvermögen."""
        assert material in config.MATERIAL_VALUES, (
            f"'{material}' fehlt in config.MATERIAL_VALUES"
        )

    @pytest.mark.parametrize('material', sorted(config.MATERIAL_VALUES))
    def test_materialwerte_sind_plausibel(self, material):
        wert = config.MATERIAL_VALUES[material]
        assert 0 < wert <= 100000, f"'{material}' hat den unplausiblen Wert {wert}"


class TestPlaneten:
    def test_entfernungen_sind_symmetrisch(self):
        for von, daten in GAMESTATE['Planeten'].items():
            for zu, entfernung in daten['Entfernung'].items():
                rueck = GAMESTATE['Planeten'][zu]['Entfernung'][von]
                assert entfernung == rueck, f'{von}->{zu} ({entfernung}) != {zu}->{von} ({rueck})'

    def test_jeder_planet_kennt_jeden_anderen(self):
        planeten = set(GAMESTATE['Planeten'])
        for name, daten in GAMESTATE['Planeten'].items():
            assert set(daten['Entfernung']) == planeten - {name}

    def test_entfernungen_sind_positiv(self):
        for daten in GAMESTATE['Planeten'].values():
            assert all(e > 0 for e in daten['Entfernung'].values())

    def test_erde_ist_immer_bekannt(self):
        assert 'entdeckt' not in GAMESTATE['Planeten']['Erde']

    def test_astronauten_und_raumschiffe_kennen_alle_planeten(self):
        planeten = set(GAMESTATE['Planeten'])
        assert set(GAMESTATE['Astronauten']) == planeten
        assert set(GAMESTATE['Raumschiffe']) == planeten

    def test_mondlander_reichweite_erreicht_den_mond(self):
        reichweite = SCIENCE['Mondlander']['reichweite']
        assert reichweite >= GAMESTATE['Planeten']['Erde']['Entfernung']['Mond']

    def test_rakete_erreicht_den_mars(self):
        reichweite = SCIENCE['Rakete']['reichweite']
        assert reichweite >= GAMESTATE['Planeten']['Erde']['Entfernung']['Mars']
