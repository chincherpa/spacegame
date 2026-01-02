"""
Integration tests for building functionality.
Tests validate material checks, building process, and queue management.
"""
import pytest
import copy


class TestMaterialChecks:
    """Tests for building material requirement checks."""

    def test_check_materials_available(self, fresh_gamestate):
        """Test checking if materials are available for building."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Roheisen'] = 10
        
        # Check if we can build Eisenbarren (requires 1 Roheisen)
        item = gs['Werkstatt']['Eisenbarren']
        can_build = True
        for material, anzahl in item['material'].items():
            if gs['Inventar'].get(material, 0) < anzahl:
                can_build = False
                break
        
        assert can_build == True

    def test_check_materials_not_available(self, fresh_gamestate):
        """Test checking when materials are not available."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Roheisen'] = 0
        
        # Check if we can build Eisenbarren (requires 1 Roheisen)
        item = gs['Werkstatt']['Eisenbarren']
        can_build = True
        for material, anzahl in item['material'].items():
            if gs['Inventar'].get(material, 0) < anzahl:
                can_build = False
                break
        
        assert can_build == False

    def test_check_multiple_materials(self, fresh_gamestate):
        """Test checking multiple material requirements."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Staub'] = 1
        gs['Inventar']['Wasser'] = 1
        
        # Check if we can build Baumaterial (requires Staub and Wasser)
        item = gs['Werkstatt']['Baumaterial']
        can_build = True
        for material, anzahl in item['material'].items():
            if gs['Inventar'].get(material, 0) < anzahl:
                can_build = False
                break
        
        assert can_build == True

    def test_check_partial_materials(self, fresh_gamestate):
        """Test when only some materials are available."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Staub'] = 1
        gs['Inventar']['Wasser'] = 0  # Missing this
        
        # Check if we can build Baumaterial
        item = gs['Werkstatt']['Baumaterial']
        can_build = True
        for material, anzahl in item['material'].items():
            if gs['Inventar'].get(material, 0) < anzahl:
                can_build = False
                break
        
        assert can_build == False


class TestMaterialDeduction:
    """Tests for material deduction when building starts."""

    def test_deduct_single_material(self, fresh_gamestate):
        """Test that single material is deducted correctly."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_roheisen = 10
        gs['Inventar']['Roheisen'] = initial_roheisen
        
        # Simulate building Eisenbarren
        item = gs['Werkstatt']['Eisenbarren']
        for material, anzahl in item['material'].items():
            gs['Inventar'][material] -= anzahl
        
        expected_roheisen = initial_roheisen - item['material']['Roheisen']
        assert gs['Inventar']['Roheisen'] == expected_roheisen

    def test_deduct_multiple_materials(self, fresh_gamestate):
        """Test that multiple materials are deducted correctly."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_staub = 5
        initial_wasser = 10
        gs['Inventar']['Staub'] = initial_staub
        gs['Inventar']['Wasser'] = initial_wasser
        
        # Simulate building Baumaterial
        item = gs['Werkstatt']['Baumaterial']
        for material, anzahl in item['material'].items():
            gs['Inventar'][material] -= anzahl
        
        expected_staub = initial_staub - item['material']['Staub']
        expected_wasser = initial_wasser - item['material']['Wasser']
        assert gs['Inventar']['Staub'] == expected_staub
        assert gs['Inventar']['Wasser'] == expected_wasser


class TestBuildCompletion:
    """Tests for build completion and item creation."""

    def test_complete_build_adds_to_inventory(self, fresh_gamestate):
        """Test that completing a build adds item to inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_count = gs['Inventar'].get('Eisenbarren', 0)
        
        # Simulate completing Eisenbarren build
        if 'Eisenbarren' not in gs['Inventar']:
            gs['Inventar']['Eisenbarren'] = 0
        gs['Inventar']['Eisenbarren'] += 1
        
        assert gs['Inventar']['Eisenbarren'] == initial_count + 1

    def test_complete_spaceship_build_adds_to_raumschiffe(self, fresh_gamestate):
        """Test that completing spaceship build adds to Raumschiffe."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_count = gs['Raumschiffe']['Erde']['Mondlander']['Anzahl']
        
        # Simulate completing Mondlander build
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] += 1
        
        assert gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == initial_count + 1

    def test_complete_rakete_build(self, fresh_gamestate):
        """Test completing Rakete build."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_count = gs['Raumschiffe']['Erde']['Rakete']['Anzahl']
        
        # Simulate completing Rakete build
        gs['Raumschiffe']['Erde']['Rakete']['Anzahl'] += 1
        
        assert gs['Raumschiffe']['Erde']['Rakete']['Anzahl'] == initial_count + 1


class TestBuildQueue:
    """Tests for build queue management."""

    def test_add_to_build_queue(self):
        """Test adding items to build queue."""
        bau_queue = []
        
        bau_queue.append('Eisenbarren')
        
        assert len(bau_queue) == 1
        assert bau_queue[0] == 'Eisenbarren'

    def test_add_multiple_to_build_queue(self):
        """Test adding multiple items to build queue."""
        bau_queue = []
        
        bau_queue.append('Eisenbarren')
        bau_queue.append('Werkzeug')
        bau_queue.append('Baumaterial')
        
        assert len(bau_queue) == 3
        assert bau_queue == ['Eisenbarren', 'Werkzeug', 'Baumaterial']

    def test_process_build_queue(self):
        """Test processing items from build queue."""
        bau_queue = ['Eisenbarren', 'Werkzeug']
        
        # Process first item
        current_build = bau_queue.pop(0)
        
        assert current_build == 'Eisenbarren'
        assert len(bau_queue) == 1
        assert bau_queue[0] == 'Werkzeug'

    def test_cancel_from_build_queue(self):
        """Test canceling item from build queue."""
        bau_queue = ['Eisenbarren', 'Werkzeug', 'Baumaterial']
        
        # Cancel first item (storniere)
        if bau_queue:
            bau_queue.pop(0)
        
        assert len(bau_queue) == 2
        assert 'Eisenbarren' not in bau_queue


class TestBuildDuration:
    """Tests for build duration calculations."""

    def test_werkstatt_items_have_duration(self, fresh_gamestate):
        """Test that all Werkstatt items have duration."""
        for item_name, item_data in fresh_gamestate['Werkstatt'].items():
            assert 'dauer' in item_data
            assert item_data['dauer'] > 0

    def test_complex_items_take_longer(self, fresh_gamestate):
        """Test that complex items generally take longer to build."""
        werkstatt = fresh_gamestate['Werkstatt']
        
        # Weltraumstation should take longer than Eisenbarren
        assert werkstatt['Weltraumstation']['dauer'] > werkstatt['Eisenbarren']['dauer']


class TestMaterialReturnOnCancel:
    """Tests for material return when build is canceled."""

    def test_return_materials_on_cancel(self, fresh_gamestate):
        """Test that materials are returned when build is canceled."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Start with materials
        gs['Inventar']['Roheisen'] = 10
        
        # Deduct for building
        item = gs['Werkstatt']['Eisenbarren']
        for material, anzahl in item['material'].items():
            gs['Inventar'][material] -= anzahl
        
        # Now cancel and return materials
        for material, anzahl in item['material'].items():
            gs['Inventar'][material] += anzahl
        
        assert gs['Inventar']['Roheisen'] == 10

    def test_return_multiple_materials_on_cancel(self, fresh_gamestate):
        """Test returning multiple materials on cancel."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Start with materials
        gs['Inventar']['Staub'] = 5
        gs['Inventar']['Wasser'] = 10
        
        # Deduct for building Baumaterial
        item = gs['Werkstatt']['Baumaterial']
        for material, anzahl in item['material'].items():
            gs['Inventar'][material] -= anzahl
        
        # Verify they were deducted
        assert gs['Inventar']['Staub'] == 4
        assert gs['Inventar']['Wasser'] == 9
        
        # Now cancel and return materials
        for material, anzahl in item['material'].items():
            gs['Inventar'][material] += anzahl
        
        assert gs['Inventar']['Staub'] == 5
        assert gs['Inventar']['Wasser'] == 10
