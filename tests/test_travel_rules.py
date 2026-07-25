"""
Tests für travel_rules: Treibstoffverbrauch, Lebenserhaltung und Reiseereignisse.
"""
import random

import pytest

import travel_rules


class TestReisekosten:
    """Treibstoff- und Wasserbedarf einer Reise."""

    def test_treibstoff_skaliert_mit_entfernung(self):
        nah = travel_rules.berechne_reisekosten('Mondlander', 1, 0)
        fern = travel_rules.berechne_reisekosten('Mondlander', 3, 0)
        assert nah['Treibstoff'] == 1
        assert fern['Treibstoff'] == 3

    def test_rakete_verbraucht_mehr_als_mondlander(self):
        lander = travel_rules.berechne_reisekosten('Mondlander', 2, 0)
        rakete = travel_rules.berechne_reisekosten('Rakete', 2, 0)
        assert rakete['Treibstoff'] > lander['Treibstoff']

    def test_wasser_skaliert_mit_astronauten_und_entfernung(self):
        kosten = travel_rules.berechne_reisekosten('Rakete', 3, 4)
        assert kosten['Wasser'] == 12

    def test_ohne_astronauten_kein_wasser(self):
        kosten = travel_rules.berechne_reisekosten('Mondlander', 2, 0)
        assert 'Wasser' not in kosten

    def test_lebenserhaltung_upgrade_senkt_wasserbedarf(self):
        ohne = travel_rules.berechne_reisekosten('Rakete', 3, 4, lebenserhaltung_upgrades=0)
        mit = travel_rules.berechne_reisekosten('Rakete', 3, 4, lebenserhaltung_upgrades=1)
        assert mit['Wasser'] < ohne['Wasser']

    def test_upgrade_laesst_mindestens_ein_wasser_uebrig(self):
        kosten = travel_rules.berechne_reisekosten('Mondlander', 1, 1, lebenserhaltung_upgrades=4)
        assert kosten['Wasser'] >= 1

    def test_unbekannter_schiffstyp_bekommt_grundverbrauch(self):
        kosten = travel_rules.berechne_reisekosten('Sternenkreuzer', 2, 0)
        assert kosten['Treibstoff'] == 2

    def test_negative_werte_werden_abgefangen(self):
        assert travel_rules.berechne_reisekosten('Mondlander', -5, -5) == {}


class TestPruefeReisekosten:
    """Abgleich der Kosten mit dem Inventar."""

    def test_ausreichendes_inventar(self):
        ok, fehlend = travel_rules.pruefe_reisekosten(
            {'Treibstoff': 5, 'Wasser': 5}, {'Treibstoff': 2, 'Wasser': 3}
        )
        assert ok is True
        assert fehlend == {}

    def test_fehlende_menge_wird_benannt(self):
        ok, fehlend = travel_rules.pruefe_reisekosten(
            {'Treibstoff': 1}, {'Treibstoff': 3, 'Wasser': 2}
        )
        assert ok is False
        assert fehlend == {'Treibstoff': 2, 'Wasser': 2}

    def test_leere_kosten_sind_immer_erfuellbar(self):
        ok, fehlend = travel_rules.pruefe_reisekosten({}, {})
        assert ok is True
        assert fehlend == {}

    def test_formatierung(self):
        assert travel_rules.formatiere_reisekosten({}) == 'keine'
        assert '2 Treibstoff' in travel_rules.formatiere_reisekosten({'Treibstoff': 2})


class TestEreignisChance:
    def test_chance_steigt_mit_entfernung(self):
        assert travel_rules.ereignis_chance(1) < travel_rules.ereignis_chance(2)

    def test_chance_ist_gedeckelt(self):
        assert travel_rules.ereignis_chance(100) == travel_rules.EREIGNIS_CHANCE_MAX

    def test_keine_entfernung_keine_chance(self):
        assert travel_rules.ereignis_chance(0) == 0.0


class TestWaehleReiseereignis:
    def test_kein_ereignis_wenn_wurf_zu_hoch(self):
        class NieRng:
            def random(self):
                return 0.99
        assert travel_rules.waehle_reiseereignis(1, rng=NieRng()) is None

    def test_ereignis_wenn_wurf_niedrig(self):
        class ImmerRng(random.Random):
            def random(self):
                return 0.0
        ereignis = travel_rules.waehle_reiseereignis(3, rng=ImmerRng(1))
        assert ereignis is not None
        assert 'key' in ereignis and 'effekt' in ereignis

    def test_frachtereignis_nur_mit_fracht(self):
        """Ereignisse mit nur_mit_fracht dürfen ohne Fracht nicht gezogen werden."""
        class ImmerRng(random.Random):
            def random(self):
                return 0.0
        gezogen = {
            travel_rules.waehle_reiseereignis(5, hat_fracht=False, rng=ImmerRng(seed))['key']
            for seed in range(200)
        }
        nur_mit_fracht = {
            e['key'] for e in travel_rules.REISE_EREIGNISSE if e.get('nur_mit_fracht')
        }
        assert nur_mit_fracht, 'Testvoraussetzung: es gibt Fracht-Ereignisse'
        assert not (gezogen & nur_mit_fracht)

    def test_deterministisch_mit_gleichem_seed(self):
        a = travel_rules.waehle_reiseereignis(3, rng=random.Random(7))
        b = travel_rules.waehle_reiseereignis(3, rng=random.Random(7))
        assert (a or {}).get('key') == (b or {}).get('key')


class TestWendeReiseereignisAn:
    def _ereignis(self, key):
        return next(e for e in travel_rules.REISE_EREIGNISSE if e['key'] == key)

    def test_verzoegerung_liefert_positive_ticks(self):
        ergebnis = travel_rules.wende_reiseereignis_an(self._ereignis('triebwerksstoerung'), {})
        assert ergebnis['ticks'] > 0

    def test_sonnenwind_liefert_negative_ticks(self):
        ergebnis = travel_rules.wende_reiseereignis_an(self._ereignis('sonnenwind'), {})
        assert ergebnis['ticks'] < 0

    def test_materialfund_wird_gemeldet(self):
        ergebnis = travel_rules.wende_reiseereignis_an(self._ereignis('asteroidenfund'), {})
        assert ergebnis['material']['Roheisen'] > 0

    def test_frachtverlust_reduziert_fracht(self):
        fracht = {'Eisenbarren': 3, 'Werkzeug': 1}
        ergebnis = travel_rules.wende_reiseereignis_an(self._ereignis('frachtverlust'), fracht)
        assert sum(ergebnis['fracht'].values()) == sum(fracht.values()) - 1
        assert ergebnis['verlorene_fracht']

    def test_frachtverlust_veraendert_original_nicht(self):
        fracht = {'Eisenbarren': 3}
        travel_rules.wende_reiseereignis_an(self._ereignis('frachtverlust'), fracht)
        assert fracht == {'Eisenbarren': 3}

    def test_frachtverlust_ohne_fracht_ist_harmlos(self):
        ergebnis = travel_rules.wende_reiseereignis_an(self._ereignis('frachtverlust'), {})
        assert ergebnis['fracht'] == {}
        assert ergebnis['verlorene_fracht'] == {}

    def test_leere_posten_verschwinden_aus_der_fracht(self):
        ergebnis = travel_rules.wende_reiseereignis_an(
            self._ereignis('frachtverlust'), {'Werkzeug': 1}
        )
        assert 'Werkzeug' not in ergebnis['fracht']

    def test_text_enthaelt_schiff_und_ziel(self):
        ergebnis = travel_rules.wende_reiseereignis_an(
            self._ereignis('triebwerksstoerung'), {}, schiff='Rakete', ziel='Mars'
        )
        assert 'Rakete' in ergebnis['text'] and 'Mars' in ergebnis['text']

    def test_treibstoffleck_ist_negativ(self):
        ergebnis = travel_rules.wende_reiseereignis_an(self._ereignis('treibstoffleck'), {})
        assert ergebnis['material']['Treibstoff'] < 0


class TestEreignisDaten:
    """Strukturprüfungen, damit neue Ereignisse nicht kaputt eingetragen werden."""

    @pytest.mark.parametrize('ereignis', travel_rules.REISE_EREIGNISSE,
                             ids=[e['key'] for e in travel_rules.REISE_EREIGNISSE])
    def test_pflichtfelder(self, ereignis):
        for feld in ('key', 'name', 'gewicht', 'text', 'effekt'):
            assert feld in ereignis, f"{ereignis.get('key')} fehlt {feld}"
        assert ereignis['gewicht'] > 0

    def test_keys_sind_eindeutig(self):
        keys = [e['key'] for e in travel_rules.REISE_EREIGNISSE]
        assert len(keys) == len(set(keys))

    @pytest.mark.parametrize('ereignis', travel_rules.REISE_EREIGNISSE,
                             ids=[e['key'] for e in travel_rules.REISE_EREIGNISSE])
    def test_effekt_nutzt_bekannte_schluessel(self, ereignis):
        erlaubt = {'ticks', 'material', 'forschungspunkte', 'credits', 'fracht_verlust'}
        assert set(ereignis['effekt']) <= erlaubt

    @pytest.mark.parametrize('ereignis', travel_rules.REISE_EREIGNISSE,
                             ids=[e['key'] for e in travel_rules.REISE_EREIGNISSE])
    def test_text_ist_formatierbar(self, ereignis):
        ereignis['text'].format(schiff='Rakete', ziel='Mars')

    @pytest.mark.parametrize('ereignis', travel_rules.REISE_EREIGNISSE,
                             ids=[e['key'] for e in travel_rules.REISE_EREIGNISSE])
    def test_belohnungsmaterialien_sind_bekannt(self, ereignis):
        """Ereignisse dürfen keine Materialien erfinden, die es im Spiel nicht gibt."""
        from materials import MATERIALS
        for material in ereignis['effekt'].get('material', {}):
            assert material in MATERIALS, f'Unbekanntes Material: {material}'
