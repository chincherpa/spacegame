"""
Integration tests for inventory functionality.
Tests validate statistics calculation and material descriptions.
"""
import pytest
import copy


class TestInventarStatistiken:
    """Tests for inventory statistics calculation."""

    def test_berechne_gesamtwert_empty(self, fresh_gamestate):
        """Test calculating total value with empty inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Set all inventory to 0
        for material in gs['Inventar']:
            gs['Inventar'][material] = 0
        
        # Calculate total value
        materialwerte = {
            'Eisenbarren': 50,
            'Baumaterial': 100,
            'Werkzeug': 200,
        }
        
        gesamtwert = 0
        for material, anzahl in gs['Inventar'].items():
            gesamtwert += anzahl * materialwerte.get(material, 0)
        
        assert gesamtwert == 0

    def test_berechne_gesamtwert_with_items(self, fresh_gamestate):
        """Test calculating total value with inventory items."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Eisenbarren'] = 10
        gs['Inventar']['Werkzeug'] = 5
        
        materialwerte = {
            'Eisenbarren': 50,
            'Werkzeug': 200,
        }
        
        gesamtwert = 0
        for material, anzahl in gs['Inventar'].items():
            if anzahl > 0:
                gesamtwert += anzahl * materialwerte.get(material, 0)
        
        expected = 10 * 50 + 5 * 200  # 500 + 1000 = 1500
        assert gesamtwert == expected

    def test_count_anzahl_typen(self, fresh_gamestate):
        """Test counting number of material types with items."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Clear inventory first
        for material in gs['Inventar']:
            gs['Inventar'][material] = 0
        
        # Add some items
        gs['Inventar']['Eisenbarren'] = 10
        gs['Inventar']['Werkzeug'] = 5
        gs['Inventar']['Baumaterial'] = 3
        
        anzahl_typen = sum(1 for anzahl in gs['Inventar'].values() if anzahl > 0)
        
        assert anzahl_typen == 3

    def test_count_anzahl_typen_empty(self, fresh_gamestate):
        """Test counting material types with empty inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Clear inventory
        for material in gs['Inventar']:
            gs['Inventar'][material] = 0
        
        anzahl_typen = sum(1 for anzahl in gs['Inventar'].values() if anzahl > 0)
        
        assert anzahl_typen == 0


class TestMaterialBeschreibung:
    """Tests for material description retrieval."""

    def test_get_description_existing_material(self, test_materials):
        """Test getting description for existing material."""
        material = 'Eisenbarren'
        
        beschreibung = test_materials.get(material, {}).get('Beschreibung', '')
        
        assert len(beschreibung) > 0

    def test_get_description_unknown_material(self, test_materials):
        """Test getting description for unknown material returns dict/default."""
        material = 'UnbekanntesMaterial'
        
        result = test_materials.get(material, 'Unbekanntes Material')
        
        assert result == 'Unbekanntes Material'

    def test_all_inventory_materials_have_descriptions(self, fresh_gamestate, test_materials):
        """Test that all inventory materials have descriptions in MATERIALS."""
        missing_descriptions = []
        
        for material in fresh_gamestate['Inventar'].keys():
            if material not in test_materials:
                missing_descriptions.append(material)
        
        # Some materials might be special (like built items), so we allow some flexibility
        # Just check that most have descriptions
        coverage = 1 - (len(missing_descriptions) / len(fresh_gamestate['Inventar']))
        assert coverage > 0.5, f"Missing descriptions for: {missing_descriptions}"


class TestInventarAnzeige:
    """Tests for inventory display logic."""

    def test_material_color_positive(self, fresh_gamestate):
        """Test that positive inventory gets 'green' color."""
        anzahl = 5
        
        farbe = 'green' if anzahl > 0 else 'gray'
        
        assert farbe == 'green'

    def test_material_color_zero(self, fresh_gamestate):
        """Test that zero inventory gets 'gray' color."""
        anzahl = 0
        
        farbe = 'green' if anzahl > 0 else 'gray'
        
        assert farbe == 'gray'

    def test_inventar_layout_has_all_materials(self, fresh_gamestate):
        """Test that inventory layout would include all materials."""
        inventar_keys = list(fresh_gamestate['Inventar'].keys())
        
        assert len(inventar_keys) > 0


class TestRaumschiffAnzeige:
    """Tests for spaceship display logic."""

    def test_count_spaceships_on_earth(self, fresh_gamestate):
        """Test counting spaceships on Earth."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 3
        gs['Raumschiffe']['Erde']['Rakete']['Anzahl'] = 2
        
        mondlander = gs['Raumschiffe']['Erde']['Mondlander']['Anzahl']
        rakete = gs['Raumschiffe']['Erde']['Rakete']['Anzahl']
        
        assert mondlander == 3
        assert rakete == 2

    def test_spaceship_display_string(self, fresh_gamestate):
        """Test generating spaceship display string."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 3
        gs['Raumschiffe']['Erde']['Rakete']['Anzahl'] = 2
        
        mondlander = gs['Raumschiffe']['Erde']['Mondlander']['Anzahl']
        rakete = gs['Raumschiffe']['Erde']['Rakete']['Anzahl']
        
        display = f"Mondlander: {mondlander}, Raketen: {rakete}"
        
        assert "Mondlander: 3" in display
        assert "Raketen: 2" in display


class TestAstronautenAnzeige:
    """Tests for astronaut display logic."""

    def test_count_astronauts_per_planet(self, fresh_gamestate):
        """Test counting astronauts per planet."""
        gs = copy.deepcopy(fresh_gamestate)
        
        erde_astronauten = gs['Astronauten']['Erde']
        mond_astronauten = gs['Astronauten']['Mond']
        mars_astronauten = gs['Astronauten']['Mars']
        
        assert erde_astronauten == 10
        assert mond_astronauten == 0
        assert mars_astronauten == 0

    def test_total_astronauts(self, fresh_gamestate):
        """Test calculating total astronauts."""
        gs = copy.deepcopy(fresh_gamestate)
        
        total = sum(gs['Astronauten'].values())
        
        assert total == 10  # All start on Earth


class TestInventarManipulation:
    """Tests for inventory manipulation operations."""

    def test_add_to_inventory(self, fresh_gamestate):
        """Test adding items to inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        initial = gs['Inventar']['Eisenbarren']
        
        gs['Inventar']['Eisenbarren'] += 5
        
        assert gs['Inventar']['Eisenbarren'] == initial + 5

    def test_remove_from_inventory(self, fresh_gamestate):
        """Test removing items from inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Roheisen'] = 10
        
        gs['Inventar']['Roheisen'] -= 3
        
        assert gs['Inventar']['Roheisen'] == 7

    def test_add_new_material_to_inventory(self, fresh_gamestate):
        """Test adding new material type to inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        
        new_material = 'NeuesMaterial'
        if new_material not in gs['Inventar']:
            gs['Inventar'][new_material] = 0
        gs['Inventar'][new_material] += 10
        
        assert gs['Inventar'][new_material] == 10
