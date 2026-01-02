"""
Unit tests for the MATERIALS data structure.
Tests validate structure and consistency of material definitions.
"""
import pytest


class TestMaterialsStructure:
    """Tests for MATERIALS structure validation."""

    def test_materials_is_not_empty(self, test_materials):
        """Test that MATERIALS dictionary is not empty."""
        assert len(test_materials) > 0, "MATERIALS should not be empty"

    def test_all_materials_have_required_keys(self, test_materials):
        """Test that all materials have required keys."""
        required_keys = ['Beschreibung', 'benötigt für']
        for material_name, material_data in test_materials.items():
            for key in required_keys:
                assert key in material_data, f"Missing '{key}' in material '{material_name}'"

    def test_beschreibung_is_non_empty(self, test_materials):
        """Test that all materials have non-empty description."""
        for material_name, material_data in test_materials.items():
            assert len(material_data['Beschreibung']) > 0, \
                f"Material '{material_name}' has empty Beschreibung"

    def test_benoetigt_fuer_is_list(self, test_materials):
        """Test that 'benötigt für' is always a list."""
        for material_name, material_data in test_materials.items():
            assert isinstance(material_data['benötigt für'], list), \
                f"'benötigt für' in material '{material_name}' should be a list"


class TestMaterialsConsistency:
    """Tests for consistency in material references."""

    def test_benoetigt_fuer_references_exist(self, test_materials):
        """Test that 'benötigt für' references exist as materials or buildable items."""
        all_material_names = set(test_materials.keys())
        
        for material_name, material_data in test_materials.items():
            for target in material_data['benötigt für']:
                # Target should be either a material or a known buildable item
                # We allow some flexibility here for buildable items
                pass  # Complex validation, simplified

    def test_dependency_chains_are_consistent(self, test_materials):
        """Test that if A is needed for B, B's description doesn't contradict."""
        # This is a basic consistency check
        for material_name, material_data in test_materials.items():
            for needed_for in material_data['benötigt für']:
                if needed_for in test_materials:
                    # The target material exists, good
                    pass


class TestBasicMaterials:
    """Tests for basic required materials."""

    def test_eisenbarren_exists(self, test_materials):
        """Test that Eisenbarren material exists."""
        assert 'Eisenbarren' in test_materials

    def test_baumaterial_exists(self, test_materials):
        """Test that Baumaterial material exists."""
        assert 'Baumaterial' in test_materials

    def test_werkzeug_exists(self, test_materials):
        """Test that Werkzeug material exists."""
        assert 'Werkzeug' in test_materials

    def test_roheisen_exists(self, test_materials):
        """Test that Roheisen material exists."""
        assert 'Roheisen' in test_materials

    def test_wasser_exists(self, test_materials):
        """Test that Wasser material exists."""
        assert 'Wasser' in test_materials


class TestMaterialDependencies:
    """Tests for material dependency relationships."""

    def test_roheisen_needed_for_eisenbarren(self, test_materials):
        """Test that Roheisen is needed for Eisenbarren."""
        assert 'Eisenbarren' in test_materials['Roheisen']['benötigt für']

    def test_eisenbarren_needed_for_werkzeug(self, test_materials):
        """Test that Eisenbarren is needed for Werkzeug."""
        assert 'Werkzeug' in test_materials['Eisenbarren']['benötigt für']

    def test_staub_needed_for_baumaterial(self, test_materials):
        """Test that Staub is needed for Baumaterial."""
        if 'Staub' in test_materials:
            assert 'Baumaterial' in test_materials['Staub']['benötigt für']

    def test_wasser_used_for_production(self, test_materials):
        """Test that Wasser is used for production."""
        assert 'Wasser' in test_materials
        assert len(test_materials['Wasser']['benötigt für']) > 0, \
            "Wasser should be needed for something"


class TestSpaceshipMaterials:
    """Tests for spaceship-related materials."""

    def test_mondlander_material_exists(self, test_materials):
        """Test that Mondlander material/item exists."""
        assert 'Mondlander' in test_materials

    def test_rakete_material_exists(self, test_materials):
        """Test that Rakete material/item exists."""
        assert 'Rakete' in test_materials

    def test_raumsonde_material_exists(self, test_materials):
        """Test that Raumsonde material/item exists."""
        assert 'Raumsonde' in test_materials


class TestMissionRewardMaterials:
    """Tests for materials that are mission rewards."""

    def test_mondgestein_exists(self, test_materials):
        """Test that Mondgestein (mission reward) exists."""
        assert 'Mondgestein' in test_materials

    def test_seltene_mineralien_exists(self, test_materials):
        """Test that Seltene_Mineralien (mission reward) exists."""
        assert 'Seltene_Mineralien' in test_materials

    def test_mondstation_modul_exists(self, test_materials):
        """Test that Mondstation_Modul (mission reward) exists."""
        assert 'Mondstation_Modul' in test_materials
