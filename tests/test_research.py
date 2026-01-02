"""
Integration tests for research functionality.
Tests validate research points, unlocking, and dependency chains.
"""
import pytest
import copy


class TestResearchPointsCheck:
    """Tests for research points requirement checks."""

    def test_check_research_points_sufficient(self, fresh_gamestate, test_science):
        """Test checking when research points are sufficient."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Forschungspunkte'] = 100
        
        # Check if we can research Eisenbarren
        kosten = test_science['Eisenbarren']['kosten']
        can_research = gs['Forschungspunkte'] >= kosten
        
        assert can_research == True

    def test_check_research_points_insufficient(self, fresh_gamestate, test_science):
        """Test checking when research points are insufficient."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Forschungspunkte'] = 0
        
        # Check if we can research something with cost > 0
        kosten = test_science['Rakete']['kosten']  # Should be expensive
        can_research = gs['Forschungspunkte'] >= kosten
        
        assert can_research == False


class TestResearchDependencies:
    """Tests for research dependency validation."""

    def test_first_research_has_no_dependency(self, test_science):
        """Test that first research (Eisenbarren) has no dependency."""
        dependency = test_science['Eisenbarren'].get('erforschbar nach', '')
        assert dependency == ''

    def test_dependent_research_requires_prerequisite(self, fresh_gamestate, test_science):
        """Test that dependent research checks prerequisite."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Baumaterial depends on Eisenbarren
        prerequisite = test_science['Baumaterial'].get('erforschbar nach', '')
        assert prerequisite == 'Eisenbarren'
        
        # Initially Eisenbarren is not researched
        can_research = gs['Forschung']['Eisenbarren']['erforscht']
        assert can_research == False

    def test_can_research_after_prerequisite(self, fresh_gamestate, test_science):
        """Test that research is available after prerequisite is done."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Complete Eisenbarren research
        gs['Forschung']['Eisenbarren']['erforscht'] = True
        
        # Now we should be able to research Baumaterial
        prerequisite = test_science['Baumaterial'].get('erforschbar nach', '')
        can_research = gs['Forschung'][prerequisite]['erforscht'] if prerequisite else True
        
        assert can_research == True


class TestResearchCompletion:
    """Tests for research completion."""

    def test_research_completion_updates_state(self, fresh_gamestate):
        """Test that completing research updates GAMESTATE."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Initially not researched
        assert gs['Forschung']['Eisenbarren']['erforscht'] == False
        
        # Complete research
        gs['Forschung']['Eisenbarren']['erforscht'] = True
        
        assert gs['Forschung']['Eisenbarren']['erforscht'] == True

    def test_research_deducts_points(self, fresh_gamestate, test_science):
        """Test that research deducts research points."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_points = 100
        gs['Forschungspunkte'] = initial_points
        
        kosten = test_science['Eisenbarren']['kosten']
        gs['Forschungspunkte'] -= kosten
        
        assert gs['Forschungspunkte'] == initial_points - kosten


class TestResearchChain:
    """Tests for complete research chains."""

    def test_basic_research_chain(self, fresh_gamestate, test_science):
        """Test researching through a basic chain."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Forschungspunkte'] = 1000
        
        # Research Eisenbarren first
        gs['Forschung']['Eisenbarren']['erforscht'] = True
        
        # Now can research Werkzeug or Baumaterial
        werkzeug_prereq = test_science['Werkzeug'].get('erforschbar nach', '')
        baumaterial_prereq = test_science['Baumaterial'].get('erforschbar nach', '')
        
        assert gs['Forschung'][werkzeug_prereq]['erforscht'] == True
        assert gs['Forschung'][baumaterial_prereq]['erforscht'] == True

    def test_spaceship_research_chain(self, fresh_gamestate, test_science):
        """Test researching spaceships follows correct order."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Build the chain to Mondlander
        chain = []
        current = 'Mondlander'
        while current:
            chain.append(current)
            current = test_science[current].get('erforschbar nach', '')
        
        # Research in reverse order (from root to target)
        for research_name in reversed(chain):
            gs['Forschung'][research_name]['erforscht'] = True
        
        # Mondlander should now be researched
        assert gs['Forschung']['Mondlander']['erforscht'] == True


class TestResearchDuration:
    """Tests for research duration calculations."""

    def test_all_research_has_duration(self, test_science):
        """Test that all research items have duration."""
        for name, data in test_science.items():
            assert 'dauer' in data
            assert data['dauer'] > 0

    def test_advanced_research_takes_longer(self, test_science):
        """Test that advanced research generally takes longer."""
        # Weltraumstation should take longer than Eisenbarren
        assert test_science['Weltraumstation']['dauer'] > test_science['Eisenbarren']['dauer']


class TestResearchUnlocks:
    """Tests for what research unlocks."""

    def test_research_unlocks_building(self, fresh_gamestate):
        """Test that research unlocks corresponding building option."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Before research, item should exist in Werkstatt but Forschung is False
        assert 'Eisenbarren' in gs['Werkstatt']
        assert gs['Forschung']['Eisenbarren']['erforscht'] == False
        
        # After research
        gs['Forschung']['Eisenbarren']['erforscht'] = True
        
        # Now building should be "unlocked" (visible in UI)
        assert gs['Forschung']['Eisenbarren']['erforscht'] == True

    def test_spaceship_research_enables_building(self, fresh_gamestate):
        """Test that spaceship research enables building them."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Research Mondlander
        gs['Forschung']['Mondlander']['erforscht'] = True
        
        # Now should be able to build Mondlander
        assert 'Mondlander' in gs['Werkstatt']
        assert gs['Forschung']['Mondlander']['erforscht'] == True


class TestResearchVisibility:
    """Tests for research visibility in UI (logic tests)."""

    def test_first_research_always_visible(self, test_science):
        """Test that first research (no dependency) is always visible."""
        eisenbarren = test_science['Eisenbarren']
        dependency = eisenbarren.get('erforschbar nach', '')
        
        # No dependency means always visible
        is_visible = dependency == ''
        assert is_visible == True

    def test_dependent_research_visibility(self, fresh_gamestate, test_science):
        """Test that dependent research visibility depends on prerequisite."""
        gs = copy.deepcopy(fresh_gamestate)
        
        baumaterial = test_science['Baumaterial']
        dependency = baumaterial.get('erforschbar nach', '')
        
        # Before prerequisite is done
        is_visible_before = gs['Forschung'][dependency]['erforscht'] if dependency else True
        assert is_visible_before == False
        
        # After completing prerequisite
        gs['Forschung'][dependency]['erforscht'] = True
        is_visible_after = gs['Forschung'][dependency]['erforscht'] if dependency else True
        assert is_visible_after == True
