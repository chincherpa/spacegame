"""
Integration tests for the workshop / building system.

These tests call the real baue(), beende_bauen(), stoppe_bauen() and
berechne_rohstoffe() functions from main.py through the `game` fixture, so the
material bookkeeping under test is the bookkeeping the game actually performs.
"""
import pytest

import config


def _set_build_amount(game, amount):
    """Make the 'anzahl_bauen' spinner report `amount` to baue()."""
    game.window.__getitem__.return_value.get.return_value = amount


def _start_build(game, item):
    """Start a build the way the event loop does.

    The loop assigns the module-level `sAktuelles_Bauen` and then calls
    `baue(sAktuelles_Bauen)`; `stoppe_bauen()` reads that global, so a test that
    only called baue() would cancel nothing.
    """
    game.sAktuelles_Bauen = item
    game.baue(item)


class TestMaterialChecks:
    """baue() must refuse to start when materials are missing."""

    def test_build_starts_when_material_is_available(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        _start_build(game, 'Eisenbarren')
        assert game.bBauen_aktiv is True

    def test_build_refused_without_material(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 0
        _start_build(game, 'Eisenbarren')
        assert game.bBauen_aktiv is False

    def test_build_refused_with_partial_material(self, game):
        # Baumaterial needs Staub and Wasser; supply only one of them.
        rezept = game.GAMESTATE['Werkstatt']['Baumaterial']['material']
        assert len(rezept) > 1, 'expected a multi-material recipe'
        first, second = list(rezept)[0], list(rezept)[1]
        game.GAMESTATE['Inventar'][first] = rezept[first]
        game.GAMESTATE['Inventar'][second] = 0
        _start_build(game, 'Baumaterial')
        assert game.bBauen_aktiv is False

    def test_material_is_deducted_on_start(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        kosten = game.GAMESTATE['Werkstatt']['Eisenbarren']['material']['Roheisen']
        _start_build(game, 'Eisenbarren')
        assert game.GAMESTATE['Inventar']['Roheisen'] == 10 - kosten

    def test_multi_build_deducts_for_every_item(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        kosten = game.GAMESTATE['Werkstatt']['Eisenbarren']['material']['Roheisen']
        _set_build_amount(game, 3)
        _start_build(game, 'Eisenbarren')
        assert game.iAnzahl_Bauen == 3
        assert game.GAMESTATE['Inventar']['Roheisen'] == 10 - 3 * kosten

    def test_multi_build_refused_when_only_one_is_affordable(self, game):
        kosten = game.GAMESTATE['Werkstatt']['Eisenbarren']['material']['Roheisen']
        game.GAMESTATE['Inventar']['Roheisen'] = kosten
        _set_build_amount(game, 3)
        _start_build(game, 'Eisenbarren')
        assert game.bBauen_aktiv is False
        assert game.GAMESTATE['Inventar']['Roheisen'] == kosten, 'material was consumed anyway'


class TestBuildDuration:
    """iMax_Bauen must never collapse to zero (regression guard)."""

    def test_duration_scales_with_amount(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        _set_build_amount(game, 2)
        _start_build(game, 'Eisenbarren')
        dauer = game.GAMESTATE['Werkstatt']['Eisenbarren']['dauer']
        assert game.iMax_Bauen == max(1, int(dauer / config.TICK_MULTIPLIER)) * 2

    def test_duration_is_at_least_one_tick_per_item(self, game, monkeypatch):
        # A TICK_MULTIPLIER larger than the recipe duration used to round the
        # build time down to 0, finishing the build instantly.
        monkeypatch.setattr(config, 'TICK_MULTIPLIER', 100)
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        _set_build_amount(game, 2)
        _start_build(game, 'Eisenbarren')
        assert game.iMax_Bauen >= 2


class TestBeendeBauen:
    """Finishing a build must hand over the items."""

    def test_item_lands_in_inventory(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        before = game.GAMESTATE['Inventar'].get('Eisenbarren', 0)
        _start_build(game, 'Eisenbarren')
        game.beende_bauen('Eisenbarren')
        assert game.GAMESTATE['Inventar']['Eisenbarren'] == before + 1
        assert game.bBauen_aktiv is False

    def test_multi_build_delivers_every_item(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        before = game.GAMESTATE['Inventar'].get('Eisenbarren', 0)
        _set_build_amount(game, 3)
        _start_build(game, 'Eisenbarren')
        game.beende_bauen('Eisenbarren')
        assert game.GAMESTATE['Inventar']['Eisenbarren'] == before + 3

    def test_spaceships_go_to_the_fleet_not_the_inventory(self, game):
        rezept = game.GAMESTATE['Werkstatt']['Mondlander']['material']
        for material, amount in rezept.items():
            game.GAMESTATE['Inventar'][material] = amount + 5
        before = game.GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl']
        _start_build(game, 'Mondlander')
        game.beende_bauen('Mondlander')
        assert game.GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == before + 1

    def test_build_is_counted_in_statistics(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        before = game.GAMESTATE['Statistik'].get('gebaute_items', 0)
        _start_build(game, 'Eisenbarren')
        game.beende_bauen('Eisenbarren')
        assert game.GAMESTATE['Statistik']['gebaute_items'] == before + 1

    def test_finishing_the_space_station_wins_the_game(self, game):
        rezept = game.GAMESTATE['Werkstatt']['Weltraumstation']['material']
        for material, amount in rezept.items():
            game.GAMESTATE['Inventar'][material] = amount + 5
        assert not game.GAMESTATE.get('Spiel_gewonnen')
        _start_build(game, 'Weltraumstation')
        game.beende_bauen('Weltraumstation')
        assert game.GAMESTATE['Spiel_gewonnen'] is True


class TestStoppeBauen:
    """Cancelling must refund the unfinished items and credit the finished ones."""

    def test_cancel_before_any_progress_refunds_everything(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        _start_build(game, 'Eisenbarren')
        game.iAktueller_Baufortschritt = 0
        game.stoppe_bauen()
        assert game.GAMESTATE['Inventar']['Roheisen'] == 10
        assert game.bBauen_aktiv is False

    def test_cancel_midway_keeps_finished_items_and_refunds_the_rest(self, game):
        kosten = game.GAMESTATE['Werkstatt']['Eisenbarren']['material']['Roheisen']
        dauer = game.GAMESTATE['Werkstatt']['Eisenbarren']['dauer']
        ticks_pro_item = max(1, int(dauer / config.TICK_MULTIPLIER))

        game.GAMESTATE['Inventar']['Roheisen'] = 10
        barren_before = game.GAMESTATE['Inventar'].get('Eisenbarren', 0)
        _set_build_amount(game, 3)
        _start_build(game, 'Eisenbarren')
        assert game.GAMESTATE['Inventar']['Roheisen'] == 10 - 3 * kosten

        # Exactly one of the three items is finished.
        game.iAktueller_Baufortschritt = ticks_pro_item
        game.stoppe_bauen()

        assert game.GAMESTATE['Inventar']['Eisenbarren'] == barren_before + 1
        # Two unfinished items -> their material comes back.
        assert game.GAMESTATE['Inventar']['Roheisen'] == 10 - 3 * kosten + 2 * kosten

    def test_no_material_is_created_or_destroyed_on_cancel(self, game):
        """Roheisen spent must equal Roheisen embodied in the delivered items."""
        kosten = game.GAMESTATE['Werkstatt']['Eisenbarren']['material']['Roheisen']
        dauer = game.GAMESTATE['Werkstatt']['Eisenbarren']['dauer']
        ticks_pro_item = max(1, int(dauer / config.TICK_MULTIPLIER))

        game.GAMESTATE['Inventar']['Roheisen'] = 20
        game.GAMESTATE['Inventar']['Eisenbarren'] = 0
        _set_build_amount(game, 4)
        _start_build(game, 'Eisenbarren')
        game.iAktueller_Baufortschritt = 2 * ticks_pro_item
        game.stoppe_bauen()

        roheisen_spent = 20 - game.GAMESTATE['Inventar']['Roheisen']
        barren_made = game.GAMESTATE['Inventar']['Eisenbarren']
        assert roheisen_spent == barren_made * kosten

    def test_cancel_when_nothing_is_building_is_a_no_op(self, game):
        game.GAMESTATE['Inventar']['Roheisen'] = 10
        game.bBauen_aktiv = False
        game.stoppe_bauen()
        assert game.GAMESTATE['Inventar']['Roheisen'] == 10


class TestBerechneRohstoffe:
    """berechne_rohstoffe() resolves a recipe down to raw materials."""

    def test_direct_recipe(self, game):
        rohstoffe = game.berechne_rohstoffe('Eisenbarren')
        assert rohstoffe['Roheisen'] == (
            game.GAMESTATE['Werkstatt']['Eisenbarren']['material']['Roheisen'])

    def test_amount_scales_linearly(self, game):
        one = game.berechne_rohstoffe('Eisenbarren', 1)
        three = game.berechne_rohstoffe('Eisenbarren', 3)
        for material, amount in one.items():
            assert three[material] == amount * 3

    def test_nested_recipe_resolves_to_raw_materials(self, game):
        """Werkzeug is made from Eisenbarren, which is made from Roheisen."""
        rohstoffe = game.berechne_rohstoffe('Werkzeug')
        assert 'Roheisen' in rohstoffe, rohstoffe
        assert rohstoffe['Roheisen'] > 0

    def test_raw_material_is_returned_as_itself(self, game):
        rohstoffe = game.berechne_rohstoffe('Roheisen', 5)
        assert rohstoffe == {'Roheisen': 5}
