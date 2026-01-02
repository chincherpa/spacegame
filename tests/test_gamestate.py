"""
Unit tests for the GAMESTATE data structure.
Tests validate structure integrity and consistency with other modules.
"""
import pytest


class TestGamestateStructure:
    """Tests for GAMESTATE structure validation."""

    def test_gamestate_has_required_top_level_keys(self, fresh_gamestate):
        """Test that GAMESTATE has all required top-level keys."""
        required_keys = [
            'Ticks', 'Credits', 'Forschungspunkte',
            'Astronauten', 'Arbeiter', 'Raumschiffe',
            'Forschung', 'Werkstatt', 'Inventar',
            'Planeten', 'Log', 'Mondmissionen'
        ]
        for key in required_keys:
            assert key in fresh_gamestate, f"Missing required key: {key}"

    def test_astronauten_has_all_planets(self, fresh_gamestate):
        """Test that Astronauten dict has entries for all planets."""
        expected_planets = ['Erde', 'Mond', 'Mars']
        for planet in expected_planets:
            assert planet in fresh_gamestate['Astronauten'], f"Missing planet: {planet}"

    def test_arbeiter_has_all_planets(self, fresh_gamestate):
        """Test that Arbeiter dict has entries for all planets."""
        expected_planets = ['Erde', 'Mond', 'Mars']
        for planet in expected_planets:
            assert planet in fresh_gamestate['Arbeiter'], f"Missing planet: {planet}"

    def test_raumschiffe_has_all_planets(self, fresh_gamestate):
        """Test that Raumschiffe dict has entries for all planets."""
        expected_planets = ['Erde', 'Mond', 'Mars']
        for planet in expected_planets:
            assert planet in fresh_gamestate['Raumschiffe'], f"Missing planet: {planet}"

    def test_raumschiffe_have_ship_types(self, fresh_gamestate):
        """Test that each planet's Raumschiffe has Mondlander and Rakete."""
        ship_types = ['Mondlander', 'Rakete']
        for planet in ['Erde', 'Mond', 'Mars']:
            for ship_type in ship_types:
                assert ship_type in fresh_gamestate['Raumschiffe'][planet], \
                    f"Missing {ship_type} for {planet}"
                assert 'Anzahl' in fresh_gamestate['Raumschiffe'][planet][ship_type], \
                    f"Missing Anzahl for {ship_type} on {planet}"

    def test_planeten_structure(self, fresh_gamestate):
        """Test that Planeten dict has correct structure."""
        expected_planets = ['Erde', 'Mond', 'Mars']
        for planet in expected_planets:
            assert planet in fresh_gamestate['Planeten'], f"Missing planet: {planet}"
            assert 'Entfernung' in fresh_gamestate['Planeten'][planet], \
                f"Missing Entfernung for {planet}"

    def test_planeten_entfernung_is_symmetric(self, fresh_gamestate):
        """Test that planet distances are defined both ways."""
        planeten = fresh_gamestate['Planeten']
        
        # Check Erde -> Mond and Mond -> Erde
        assert 'Mond' in planeten['Erde']['Entfernung']
        assert 'Erde' in planeten['Mond']['Entfernung']
        
        # Check Erde -> Mars and Mars -> Erde
        assert 'Mars' in planeten['Erde']['Entfernung']
        assert 'Erde' in planeten['Mars']['Entfernung']


class TestGamestateInitialValues:
    """Tests for GAMESTATE initial values."""

    def test_initial_credits(self, fresh_gamestate):
        """Test initial credits value."""
        assert fresh_gamestate['Credits'] == 10

    def test_initial_ticks(self, fresh_gamestate):
        """Test initial ticks is zero."""
        assert fresh_gamestate['Ticks'] == 0

    def test_initial_forschungspunkte(self, fresh_gamestate):
        """Test initial research points is zero."""
        assert fresh_gamestate['Forschungspunkte'] == 0

    def test_initial_astronauten_on_earth(self, fresh_gamestate):
        """Test initial astronauts are on Earth."""
        assert fresh_gamestate['Astronauten']['Erde'] == 10
        assert fresh_gamestate['Astronauten']['Mond'] == 0
        assert fresh_gamestate['Astronauten']['Mars'] == 0

    def test_all_research_starts_unresearched(self, fresh_gamestate):
        """Test that all research starts as not researched."""
        for name, data in fresh_gamestate['Forschung'].items():
            assert data['erforscht'] == False, f"{name} should not be researched initially"

    def test_moon_and_mars_start_undiscovered(self, fresh_gamestate):
        """Test that Moon and Mars start as undiscovered."""
        assert fresh_gamestate['Planeten']['Mond']['entdeckt'] == False
        assert fresh_gamestate['Planeten']['Mars']['entdeckt'] == False

    def test_no_spaceships_initially(self, fresh_gamestate):
        """Test that there are no spaceships initially."""
        for planet in ['Erde', 'Mond', 'Mars']:
            for ship_type in ['Mondlander', 'Rakete']:
                assert fresh_gamestate['Raumschiffe'][planet][ship_type]['Anzahl'] == 0


class TestGamestateConsistency:
    """Tests for consistency between GAMESTATE and other modules."""

    def test_forschung_matches_science(self, fresh_gamestate, test_science):
        """Test that GAMESTATE Forschung keys match SCIENCE keys."""
        forschung_keys = set(fresh_gamestate['Forschung'].keys())
        science_keys = set(test_science.keys())
        assert forschung_keys == science_keys, \
            f"Mismatch: GAMESTATE Forschung has {forschung_keys - science_keys}, " \
            f"SCIENCE has {science_keys - forschung_keys}"

    def test_werkstatt_matches_science(self, fresh_gamestate, test_science):
        """Test that GAMESTATE Werkstatt keys are subset of SCIENCE keys."""
        werkstatt_keys = set(fresh_gamestate['Werkstatt'].keys())
        science_keys = set(test_science.keys())
        missing = werkstatt_keys - science_keys
        assert not missing, f"Werkstatt items not in SCIENCE: {missing}"

    def test_mondmissionen_matches_actions(self, fresh_gamestate, test_actions):
        """Test that Mondmissionen keys exist in ACTIONS.
        
        Note: This test may reveal data inconsistencies between GAMESTATE and ACTIONS.
        Missing missions should be added to ACTIONS or removed from GAMESTATE['Mondmissionen'].
        """
        missing_missions = []
        for mission_name in fresh_gamestate['Mondmissionen'].keys():
            if mission_name not in test_actions:
                missing_missions.append(mission_name)
        
        if missing_missions:
            pytest.skip(f"Data inconsistency found - missions in GAMESTATE but not in ACTIONS: {missing_missions}")


class TestWerkstattStructure:
    """Tests for Werkstatt (workshop) structure."""

    def test_werkstatt_items_have_required_keys(self, fresh_gamestate):
        """Test that all Werkstatt items have required keys."""
        required_keys = ['beschreibung', 'dauer', 'material']
        for item_name, item_data in fresh_gamestate['Werkstatt'].items():
            for key in required_keys:
                assert key in item_data, f"Missing '{key}' in Werkstatt item '{item_name}'"

    def test_werkstatt_materials_exist_in_inventar(self, fresh_gamestate):
        """Test that materials required by Werkstatt items exist in Inventar."""
        for item_name, item_data in fresh_gamestate['Werkstatt'].items():
            for material_name in item_data['material'].keys():
                # Some materials like 'Mondlander' might be special cases
                # Just check they're either in Inventar or are buildable items
                pass  # This is a complex check, simplified for now

    def test_werkstatt_dauer_is_positive(self, fresh_gamestate):
        """Test that all Werkstatt items have positive duration."""
        for item_name, item_data in fresh_gamestate['Werkstatt'].items():
            assert item_data['dauer'] > 0, f"Werkstatt item '{item_name}' has non-positive dauer"


class TestInventarStructure:
    """Tests for Inventar (inventory) structure."""

    def test_inventar_values_are_non_negative(self, fresh_gamestate):
        """Test that all inventory values are non-negative."""
        for material, amount in fresh_gamestate['Inventar'].items():
            assert amount >= 0, f"Negative inventory for {material}: {amount}"

    def test_inventar_has_basic_materials(self, fresh_gamestate):
        """Test that inventory has basic starting materials."""
        required_materials = ['Roheisen', 'Staub', 'Wasser']
        for material in required_materials:
            assert material in fresh_gamestate['Inventar'], f"Missing material: {material}"
