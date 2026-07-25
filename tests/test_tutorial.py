"""
Tests für das Tutorial-/Hilfesystem.
"""
import copy

import pytest

import tutorial


class TestNaechsterSchritt:
    def test_frisches_spiel_startet_beim_ersten_schritt(self, fresh_gamestate):
        schritt = tutorial.naechster_schritt(fresh_gamestate)
        assert schritt is not None
        assert schritt['key'] == tutorial.TUTORIAL_SCHRITTE[0]['key']

    def test_schritt_wandert_weiter(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        vorher = tutorial.naechster_schritt(gs)['key']
        gs['Forschungspunkte'] = 10
        assert tutorial.naechster_schritt(gs)['key'] != vorher

    def test_gewonnenes_spiel_hat_keine_offenen_schritte(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Spiel_gewonnen'] = True
        gs['Forschungspunkte'] = 999
        for f in gs['Forschung'].values():
            f['erforscht'] = True
        for p in ('Mond', 'Mars'):
            gs['Planeten'][p]['entdeckt'] = True
        gs['Astronauten']['Mond'] = 3
        gs['Inventar']['Raumsonde'] = 1
        gs['Inventar']['Mondbasen Bauplan'] = 1
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 1
        for m in gs['Mondmissionen'].values():
            m['erforscht'] = True
        assert tutorial.naechster_schritt(gs) is None

    def test_unvollstaendiger_spielstand_stuerzt_nicht_ab(self):
        assert tutorial.naechster_schritt({}) is not None

    def test_leeres_dict_liefert_ersten_schritt(self):
        assert tutorial.naechster_schritt({})['key'] == tutorial.TUTORIAL_SCHRITTE[0]['key']


class TestFortschritt:
    def test_frisches_spiel_hat_null_erledigt(self, fresh_gamestate):
        erledigt, gesamt = tutorial.fortschritt(fresh_gamestate)
        assert erledigt == 0
        assert gesamt == len(tutorial.TUTORIAL_SCHRITTE)

    def test_fortschritt_waechst(self, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        vorher, _ = tutorial.fortschritt(gs)
        gs['Forschung']['Eisenbarren']['erforscht'] = True
        gs['Forschungspunkte'] = 10
        nachher, _ = tutorial.fortschritt(gs)
        assert nachher > vorher

    def test_erledigt_nie_groesser_als_gesamt(self, fresh_gamestate):
        erledigt, gesamt = tutorial.fortschritt(fresh_gamestate)
        assert 0 <= erledigt <= gesamt


class TestZielText:
    def test_enthaelt_fortschritt_und_titel(self, fresh_gamestate):
        text = tutorial.ziel_text(fresh_gamestate)
        assert text.startswith('[0/')
        assert tutorial.TUTORIAL_SCHRITTE[0]['titel'] in text

    def test_abschlusstext_wenn_alles_erledigt(self, monkeypatch, fresh_gamestate):
        monkeypatch.setattr(tutorial, 'naechster_schritt', lambda gs: None)
        assert 'Alle Ziele erreicht' in tutorial.ziel_text(fresh_gamestate)


class TestSchrittDaten:
    @pytest.mark.parametrize('schritt', tutorial.TUTORIAL_SCHRITTE,
                             ids=[s['key'] for s in tutorial.TUTORIAL_SCHRITTE])
    def test_pflichtfelder(self, schritt):
        for feld in ('key', 'titel', 'text', 'erfuellt'):
            assert feld in schritt
        assert callable(schritt['erfuellt'])

    def test_keys_sind_eindeutig(self):
        keys = [s['key'] for s in tutorial.TUTORIAL_SCHRITTE]
        assert len(keys) == len(set(keys))

    @pytest.mark.parametrize('schritt', tutorial.TUTORIAL_SCHRITTE,
                             ids=[s['key'] for s in tutorial.TUTORIAL_SCHRITTE])
    def test_bedingung_ist_im_frischen_spiel_false(self, schritt, fresh_gamestate):
        """Kein Schritt darf schon zu Spielbeginn als erledigt gelten."""
        assert schritt['erfuellt'](fresh_gamestate) is False

    def test_letzter_schritt_ist_der_sieg(self):
        assert tutorial.TUTORIAL_SCHRITTE[-1]['key'] == 'weltraumstation'


class TestHilfeTexte:
    @pytest.mark.parametrize('tab_key', sorted(tutorial.HILFE_TEXTE))
    def test_hilfetexte_sind_nicht_leer(self, tab_key):
        assert len(tutorial.HILFE_TEXTE[tab_key]) > 50

    def test_unbekannter_tab_faellt_auf_allgemeine_hilfe_zurueck(self):
        assert tutorial.hilfe_fuer_tab('tab_Gibtsnicht') == tutorial.HILFE_ALLGEMEIN

    def test_bekannter_tab_liefert_eigenen_text(self):
        assert tutorial.hilfe_fuer_tab('tab_Reisen') == tutorial.HILFE_TEXTE['tab_Reisen']

    def test_allgemeine_hilfe_nennt_das_spielziel(self):
        assert 'Weltraumstation' in tutorial.HILFE_ALLGEMEIN
