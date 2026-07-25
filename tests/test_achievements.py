"""
Tests für Erfolge und Statistik.
"""
import copy

import pytest

import achievements


class TestStatistik:
    def test_leere_statistik_hat_alle_felder_auf_null(self):
        stats = achievements.leere_statistik()
        assert set(stats) == set(achievements.STATISTIK_FELDER)
        assert all(v == 0 for v in stats.values())

    def test_statistik_ergaenzt_fehlende_felder(self):
        gs = {'Statistik': {'jobs_abgeschlossen': 3}}
        stats = achievements.statistik(gs)
        assert stats['jobs_abgeschlossen'] == 3
        assert stats['reisen_abgeschlossen'] == 0

    def test_statistik_wird_bei_bedarf_angelegt(self):
        gs = {}
        achievements.statistik(gs)
        assert 'Statistik' in gs

    def test_zaehle_erhoeht_und_liefert_neuen_wert(self):
        gs = {}
        assert achievements.zaehle(gs, 'jobs_abgeschlossen') == 1
        assert achievements.zaehle(gs, 'jobs_abgeschlossen', 4) == 5

    def test_zaehle_legt_unbekanntes_feld_an(self):
        gs = {}
        assert achievements.zaehle(gs, 'neues_feld', 2) == 2

    def test_statistik_uebersicht_nennt_alle_felder(self, fresh_gamestate):
        text = achievements.statistik_uebersicht(fresh_gamestate)
        for feld in achievements.STATISTIK_FELDER:
            assert achievements.STATISTIK_LABELS[feld] in text

    def test_alle_felder_haben_ein_label(self):
        assert set(achievements.STATISTIK_FELDER) <= set(achievements.STATISTIK_LABELS)


class TestErfolgeFreischalten:
    def test_frisches_spiel_schaltet_nichts_frei(self, fresh_gamestate):
        assert achievements.pruefe_erfolge(copy.deepcopy(fresh_gamestate)) == []

    def test_erfolg_wird_freigeschaltet(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Statistik']['forschungen_abgeschlossen'] = 1
        neu = achievements.pruefe_erfolge(gs)
        assert [e['key'] for e in neu] == ['erste_forschung']
        assert 'erste_forschung' in gs['Erfolge']

    def test_erfolg_wird_nicht_doppelt_vergeben(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Statistik']['forschungen_abgeschlossen'] = 1
        achievements.pruefe_erfolge(gs)
        assert achievements.pruefe_erfolge(gs) == []

    def test_mehrere_erfolge_gleichzeitig(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Planeten']['Mond']['entdeckt'] = True
        gs['Planeten']['Mars']['entdeckt'] = True
        keys = {e['key'] for e in achievements.pruefe_erfolge(gs)}
        assert {'mond_entdeckt', 'mars_entdeckt'} <= keys

    def test_sieg_erfolg(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Spiel_gewonnen'] = True
        assert 'sieg' in {e['key'] for e in achievements.pruefe_erfolge(gs)}

    def test_alle_missionen_erst_wenn_wirklich_alle(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        namen = list(gs['Mondmissionen'])
        gs['Mondmissionen'][namen[0]]['erforscht'] = True
        assert 'alle_missionen' not in {e['key'] for e in achievements.pruefe_erfolge(gs)}
        for name in namen:
            gs['Mondmissionen'][name]['erforscht'] = True
        assert 'alle_missionen' in {e['key'] for e in achievements.pruefe_erfolge(gs)}

    def test_leeres_missions_dict_schaltet_nichts_frei(self):
        gs = {'Mondmissionen': {}, 'Forschung': {}}
        keys = {e['key'] for e in achievements.pruefe_erfolge(gs)}
        assert 'alle_missionen' not in keys
        assert 'alle_forschungen' not in keys

    def test_unvollstaendiger_spielstand_stuerzt_nicht_ab(self):
        assert isinstance(achievements.pruefe_erfolge({}), list)

    def test_freigeschaltet_legt_liste_an(self):
        gs = {}
        assert achievements.freigeschaltet(gs) == []
        assert gs['Erfolge'] == []


class TestErfolgsDaten:
    @pytest.mark.parametrize('erfolg', achievements.ERFOLGE,
                             ids=[e['key'] for e in achievements.ERFOLGE])
    def test_pflichtfelder(self, erfolg):
        for feld in ('key', 'name', 'beschreibung', 'bedingung'):
            assert feld in erfolg
        assert callable(erfolg['bedingung'])

    def test_keys_sind_eindeutig(self):
        keys = [e['key'] for e in achievements.ERFOLGE]
        assert len(keys) == len(set(keys))

    def test_namen_sind_eindeutig(self):
        namen = [e['name'] for e in achievements.ERFOLGE]
        assert len(namen) == len(set(namen))

    @pytest.mark.parametrize('erfolg', achievements.ERFOLGE,
                             ids=[e['key'] for e in achievements.ERFOLGE])
    def test_belohnung_nutzt_bekannte_schluessel(self, erfolg):
        assert set(erfolg.get('belohnung', {})) <= {'Credits', 'Forschungspunkte'}

    @pytest.mark.parametrize('erfolg', achievements.ERFOLGE,
                             ids=[e['key'] for e in achievements.ERFOLGE])
    def test_bedingung_ist_im_frischen_spiel_false(self, erfolg, fresh_gamestate):
        assert erfolg['bedingung'](fresh_gamestate) is False

    @pytest.mark.parametrize('erfolg', achievements.ERFOLGE,
                             ids=[e['key'] for e in achievements.ERFOLGE])
    def test_statistikbasierte_erfolge_nutzen_echte_felder(self, erfolg):
        """Ein Tippfehler im Feldnamen würde den Erfolg unerreichbar machen."""
        import inspect
        import re
        quelle = inspect.getsource(erfolg['bedingung'])
        for benutzt in re.findall(r"_stat\(gs, '([^']+)'\)", quelle):
            assert benutzt in achievements.STATISTIK_FELDER, f'Unbekanntes Statistikfeld: {benutzt}'

    def test_uebersicht_listet_alle_erfolge(self, fresh_gamestate):
        text = achievements.erfolgs_uebersicht(fresh_gamestate)
        for erfolg in achievements.ERFOLGE:
            assert erfolg['name'] in text

    def test_uebersicht_markiert_freigeschaltete(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Erfolge'] = ['sieg']
        zeile = [z for z in achievements.erfolgs_uebersicht(gs).splitlines() if 'Heimat im Orbit' in z][0]
        assert zeile.startswith('✓')
