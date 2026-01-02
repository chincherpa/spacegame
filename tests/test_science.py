"""
Unit tests for the SCIENCE data structure.
Tests validate structure, dependencies, and consistency of research definitions.
"""
import pytest


class TestScienceStructure:
    """Tests for SCIENCE structure validation."""

    def test_science_is_not_empty(self, test_science):
        """Test that SCIENCE dictionary is not empty."""
        assert len(test_science) > 0, "SCIENCE should not be empty"

    def test_all_science_have_required_keys(self, test_science):
        """Test that all science items have required keys."""
        required_keys = ['beschreibung', 'dauer', 'kosten']
        for science_name, science_data in test_science.items():
            for key in required_keys:
                assert key in science_data, f"Missing '{key}' in science '{science_name}'"

    def test_science_dauer_is_positive(self, test_science):
        """Test that all science items have positive duration."""
        for science_name, science_data in test_science.items():
            assert science_data['dauer'] > 0, f"Science '{science_name}' has non-positive dauer"

    def test_science_kosten_is_non_negative(self, test_science):
        """Test that all science items have non-negative cost."""
        for science_name, science_data in test_science.items():
            assert science_data['kosten'] >= 0, f"Science '{science_name}' has negative kosten"

    def test_science_beschreibung_is_non_empty(self, test_science):
        """Test that all science items have non-empty description."""
        for science_name, science_data in test_science.items():
            assert len(science_data['beschreibung']) > 0, \
                f"Science '{science_name}' has empty beschreibung"


class TestScienceDependencies:
    """Tests for science research dependencies."""

    def test_erforschbar_nach_exists(self, test_science):
        """Test that erforschbar nach key exists in all science items."""
        for science_name, science_data in test_science.items():
            assert 'erforschbar nach' in science_data, \
                f"Missing 'erforschbar nach' in science '{science_name}'"

    def test_erforschbar_nach_is_valid(self, test_science):
        """Test that dependency references exist in SCIENCE."""
        for science_name, science_data in test_science.items():
            dependency = science_data.get('erforschbar nach', '')
            if dependency:  # Non-empty dependency should exist
                assert dependency in test_science, \
                    f"Science '{science_name}' depends on unknown '{dependency}'"

    def test_first_research_has_no_dependency(self, test_science):
        """Test that at least one research has no dependency (entry point)."""
        has_entry_point = False
        for science_name, science_data in test_science.items():
            if science_data.get('erforschbar nach', '') == '':
                has_entry_point = True
                break
        assert has_entry_point, "At least one science should have no dependency"

    def test_no_cyclic_dependencies(self, test_science):
        """Test that there are no cyclic dependencies in research tree."""
        for start_name in test_science.keys():
            visited = set()
            current = start_name
            while current:
                if current in visited:
                    pytest.fail(f"Cyclic dependency detected starting from '{start_name}'")
                visited.add(current)
                current = test_science[current].get('erforschbar nach', '')

    def test_eisenbarren_is_first_research(self, test_science):
        """Test that Eisenbarren has no dependency (is first research)."""
        assert 'Eisenbarren' in test_science
        assert test_science['Eisenbarren'].get('erforschbar nach', '') == '', \
            "Eisenbarren should be the first researchable item"


class TestScienceSpaceships:
    """Tests for spaceship-related science items."""

    def test_spaceship_science_has_capacity(self, test_science):
        """Test that spaceship science items have capacity information."""
        spaceships = ['Mondlander', 'Rakete', 'Raumsonde']
        for ship in spaceships:
            if ship in test_science:
                if ship != 'Raumsonde':  # Raumsonde might not have seats
                    assert 'Sitzplätze' in test_science[ship] or 'Frachtplätze' in test_science[ship], \
                        f"Spaceship '{ship}' should have capacity info"

    def test_spaceship_science_has_reichweite(self, test_science):
        """Test that spaceship science items have range information."""
        spaceships = ['Mondlander', 'Rakete', 'Raumsonde']
        for ship in spaceships:
            if ship in test_science:
                assert 'reichweite' in test_science[ship], \
                    f"Spaceship '{ship}' should have reichweite"

    def test_mondlander_exists(self, test_science):
        """Test that Mondlander science exists."""
        assert 'Mondlander' in test_science

    def test_rakete_exists(self, test_science):
        """Test that Rakete science exists."""
        assert 'Rakete' in test_science


class TestScienceResearchChain:
    """Tests for complete research chains."""

    def test_research_chain_to_weltraumstation(self, test_science):
        """Test that there's a valid chain to research Weltraumstation."""
        assert 'Weltraumstation' in test_science
        
        # Build the dependency chain
        chain = []
        current = 'Weltraumstation'
        while current:
            chain.append(current)
            current = test_science[current].get('erforschbar nach', '')
        
        # Chain should end at a research with no dependency
        assert test_science[chain[-1]].get('erforschbar nach', '') == '', \
            "Research chain should end at a root research"

    def test_basic_research_order(self, test_science):
        """Test that basic research follows expected order."""
        # Eisenbarren should be first
        assert test_science['Eisenbarren'].get('erforschbar nach', '') == ''
        
        # Baumaterial and Werkzeug should depend on Eisenbarren
        if 'Baumaterial' in test_science:
            assert test_science['Baumaterial'].get('erforschbar nach') == 'Eisenbarren'
        if 'Werkzeug' in test_science:
            assert test_science['Werkzeug'].get('erforschbar nach') == 'Eisenbarren'
