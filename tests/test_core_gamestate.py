"""
Unit tests for the core GameState class.
"""
import pytest
import json
import tempfile
from pathlib import Path


class TestGameStateBasics:
    """Tests for basic GameState functionality."""

    def test_import_gamestate(self):
        """Test that GameState can be imported."""
        from core.game_state import GameState
        assert GameState is not None

    def test_create_default_gamestate(self):
        """Test creating GameState with default values."""
        from core.game_state import GameState
        gs = GameState()
        assert gs.ticks == 0
        assert gs.credits == 10
        assert gs.research_points == 0

    def test_create_with_custom_state(self):
        """Test creating GameState with custom initial state."""
        from core.game_state import GameState
        custom = {
            'Ticks': 100,
            'Credits': 500,
            'Forschungspunkte': 50,
            'Astronauten': {'Erde': 5, 'Mond': 3, 'Mars': 0},
            'Arbeiter': {'Erde': 10, 'Mond': 0, 'Mars': 0},
            'Raumschiffe': {},
            'Forschung': {},
            'Werkstatt': {},
            'Inventar': {},
            'Planeten': {},
            'Log': [],
            'Mondmissionen': {}
        }
        gs = GameState(custom)
        assert gs.ticks == 100
        assert gs.credits == 500
        assert gs.research_points == 50


class TestGameStateProperties:
    """Tests for GameState property accessors."""

    def test_ticks_getter_setter(self):
        """Test ticks property."""
        from core.game_state import GameState
        gs = GameState()
        gs.ticks = 42
        assert gs.ticks == 42

    def test_credits_getter_setter(self):
        """Test credits property."""
        from core.game_state import GameState
        gs = GameState()
        gs.credits = 1000
        assert gs.credits == 1000

    def test_research_points_getter_setter(self):
        """Test research_points property."""
        from core.game_state import GameState
        gs = GameState()
        gs.research_points = 25
        assert gs.research_points == 25


class TestGameStateInventory:
    """Tests for inventory management."""

    def test_get_inventory(self):
        """Test getting inventory amount."""
        from core.game_state import GameState
        gs = GameState()
        assert gs.get_inventory('Roheisen') == 10  # Default value
        assert gs.get_inventory('NonExistent') == 0

    def test_set_inventory(self):
        """Test setting inventory amount."""
        from core.game_state import GameState
        gs = GameState()
        gs.set_inventory('Gold', 100)
        assert gs.get_inventory('Gold') == 100

    def test_add_to_inventory(self):
        """Test adding to inventory."""
        from core.game_state import GameState
        gs = GameState()
        gs.add_to_inventory('Roheisen', 5)
        assert gs.get_inventory('Roheisen') == 15  # 10 default + 5

    def test_remove_from_inventory_success(self):
        """Test removing from inventory when sufficient."""
        from core.game_state import GameState
        gs = GameState()
        result = gs.remove_from_inventory('Roheisen', 5)
        assert result is True
        assert gs.get_inventory('Roheisen') == 5

    def test_remove_from_inventory_failure(self):
        """Test removing from inventory when insufficient."""
        from core.game_state import GameState
        gs = GameState()
        result = gs.remove_from_inventory('Roheisen', 100)
        assert result is False
        assert gs.get_inventory('Roheisen') == 10  # Unchanged


class TestGameStateResearch:
    """Tests for research management."""

    def test_is_researched_false(self):
        """Test checking unresearched technology."""
        from core.game_state import GameState
        gs = GameState()
        assert gs.is_researched('Eisenbarren') is False

    def test_complete_research(self):
        """Test completing research."""
        from core.game_state import GameState
        gs = GameState()
        gs.complete_research('Eisenbarren')
        assert gs.is_researched('Eisenbarren') is True


class TestGameStatePlanets:
    """Tests for planet management."""

    def test_earth_always_discovered(self):
        """Test that Earth is always discovered."""
        from core.game_state import GameState
        gs = GameState()
        assert gs.is_planet_discovered('Erde') is True

    def test_moon_starts_undiscovered(self):
        """Test that Moon starts undiscovered."""
        from core.game_state import GameState
        gs = GameState()
        assert gs.is_planet_discovered('Mond') is False

    def test_discover_planet(self):
        """Test discovering a planet."""
        from core.game_state import GameState
        gs = GameState()
        gs.discover_planet('Mond')
        assert gs.is_planet_discovered('Mond') is True

    def test_planet_distance(self):
        """Test getting planet distance."""
        from core.game_state import GameState
        gs = GameState()
        assert gs.get_planet_distance('Erde', 'Mond') == 1
        assert gs.get_planet_distance('Erde', 'Mars') == 3


class TestGameStateObservers:
    """Tests for observer pattern."""

    def test_add_observer(self):
        """Test adding an observer."""
        from core.game_state import GameState
        gs = GameState()
        observed = []
        
        def observer(key, value):
            observed.append((key, value))
        
        gs.add_observer(observer)
        gs.credits = 100
        
        assert len(observed) == 1
        assert observed[0] == ('credits', 100)

    def test_multiple_observers(self):
        """Test multiple observers are called."""
        from core.game_state import GameState
        gs = GameState()
        count = [0]
        
        def observer1(k, v):
            count[0] += 1
        
        def observer2(k, v):
            count[0] += 1
        
        gs.add_observer(observer1)
        gs.add_observer(observer2)
        gs.ticks = 10
        
        assert count[0] == 2


class TestGameStateSaveLoad:
    """Tests for save/load functionality."""

    def test_save_and_load(self):
        """Test saving and loading game state."""
        from core.game_state import GameState
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            # Create and modify state
            gs = GameState()
            gs.credits = 999
            gs.ticks = 123
            gs.complete_research('Eisenbarren')
            
            # Save
            gs.save(filepath)
            
            # Load into new instance
            gs2 = GameState.load(filepath)
            
            # Verify
            assert gs2.credits == 999
            assert gs2.ticks == 123
            assert gs2.is_researched('Eisenbarren') is True
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns default state."""
        from core.game_state import GameState
        gs = GameState.load('nonexistent_file_12345.json')
        assert gs.credits == 10  # Default value


class TestGameStateDictAccess:
    """Tests for dict-like access (backward compatibility)."""

    def test_getitem(self):
        """Test dict-like get access."""
        from core.game_state import GameState
        gs = GameState()
        assert gs['Credits'] == 10

    def test_setitem(self):
        """Test dict-like set access."""
        from core.game_state import GameState
        gs = GameState()
        gs['Credits'] = 500
        assert gs.credits == 500

    def test_raw_access(self):
        """Test raw dict access."""
        from core.game_state import GameState
        gs = GameState()
        assert isinstance(gs.raw, dict)
        assert gs.raw['Ticks'] == 0
