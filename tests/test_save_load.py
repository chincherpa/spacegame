"""
Integration tests for save/load functionality.
Tests validate game state serialization and deserialization.
"""
import pytest
import json
import copy
import tempfile
from pathlib import Path


class TestLoadGamestate:
    """Tests for loading game state."""

    def test_load_from_existing_file(self, fresh_gamestate, tmp_path):
        """Test loading gamestate from existing file."""
        # Create a save file
        save_file = tmp_path / "test_save.json"
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Credits'] = 999
        test_state['Ticks'] = 100
        
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        # Load it back
        with open(save_file, 'r') as f:
            loaded_state = json.load(f)
        
        assert loaded_state['Credits'] == 999
        assert loaded_state['Ticks'] == 100

    def test_load_fallback_when_file_missing(self, fresh_gamestate):
        """Test fallback to default gamestate when file missing."""
        # When file doesn't exist, should get default GAMESTATE
        # This simulates the behavior in main.py
        try:
            with open("nonexistent_file_12345.json", "r") as f:
                loaded = json.load(f)
        except FileNotFoundError:
            loaded = copy.deepcopy(fresh_gamestate)
        
        assert 'Credits' in loaded
        assert 'Ticks' in loaded

    def test_loaded_state_has_all_keys(self, fresh_gamestate, tmp_path):
        """Test that loaded state has all required keys."""
        save_file = tmp_path / "test_save.json"
        
        with open(save_file, 'w') as f:
            json.dump(fresh_gamestate, f)
        
        with open(save_file, 'r') as f:
            loaded_state = json.load(f)
        
        required_keys = ['Ticks', 'Credits', 'Forschungspunkte', 'Astronauten', 
                         'Raumschiffe', 'Forschung', 'Inventar', 'Planeten', 'Log']
        
        for key in required_keys:
            assert key in loaded_state, f"Missing key: {key}"


class TestDumpGamestate:
    """Tests for saving game state."""

    def test_dump_creates_file(self, fresh_gamestate, tmp_path):
        """Test that dumping gamestate creates a file."""
        save_file = tmp_path / "test_save.json"
        
        with open(save_file, 'w') as f:
            json.dump(fresh_gamestate, f)
        
        assert save_file.exists()

    def test_dump_preserves_data(self, fresh_gamestate, tmp_path):
        """Test that dumped data matches original."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Credits'] = 12345
        test_state['Forschungspunkte'] = 999
        
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Credits'] == 12345
        assert loaded['Forschungspunkte'] == 999

    def test_dump_with_indent(self, fresh_gamestate, tmp_path):
        """Test dumping with indentation for readability."""
        save_file = tmp_path / "test_save.json"
        
        with open(save_file, 'w') as f:
            json.dump(fresh_gamestate, f, indent=2)
        
        content = save_file.read_text()
        assert '\n' in content  # Should have newlines due to indent


class TestGamestateIntegrity:
    """Tests for gamestate integrity after save/load cycle."""

    def test_save_load_cycle_preserves_credits(self, fresh_gamestate, tmp_path):
        """Test that credits survive save/load cycle."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        original_credits = 5000
        test_state['Credits'] = original_credits
        
        # Save
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        # Load
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Credits'] == original_credits

    def test_save_load_cycle_preserves_inventory(self, fresh_gamestate, tmp_path):
        """Test that inventory survives save/load cycle."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Inventar']['Eisenbarren'] = 50
        test_state['Inventar']['Werkzeug'] = 25
        
        # Save
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        # Load
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Inventar']['Eisenbarren'] == 50
        assert loaded['Inventar']['Werkzeug'] == 25

    def test_save_load_cycle_preserves_research(self, fresh_gamestate, tmp_path):
        """Test that research state survives save/load cycle."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Forschung']['Eisenbarren']['erforscht'] = True
        test_state['Forschung']['Werkzeug']['erforscht'] = True
        
        # Save
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        # Load
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Forschung']['Eisenbarren']['erforscht'] == True
        assert loaded['Forschung']['Werkzeug']['erforscht'] == True

    def test_save_load_cycle_preserves_planets(self, fresh_gamestate, tmp_path):
        """Test that planet discovery survives save/load cycle."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Planeten']['Mond']['entdeckt'] = True
        
        # Save
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        # Load
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Planeten']['Mond']['entdeckt'] == True

    def test_save_load_cycle_preserves_log(self, fresh_gamestate, tmp_path):
        """Test that game log survives save/load cycle."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Log'].append("Test log entry 1")
        test_state['Log'].append("Test log entry 2")
        
        # Save
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        # Load
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert "Test log entry 1" in loaded['Log']
        assert "Test log entry 2" in loaded['Log']


class TestSavefileCorruption:
    """Tests for handling corrupted save files."""

    def test_handle_empty_file(self, tmp_path):
        """Test handling an empty save file."""
        save_file = tmp_path / "empty_save.json"
        save_file.write_text("")
        
        # Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            with open(save_file, 'r') as f:
                json.load(f)

    def test_handle_invalid_json(self, tmp_path):
        """Test handling invalid JSON in save file."""
        save_file = tmp_path / "invalid_save.json"
        save_file.write_text("{invalid json content}")
        
        # Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            with open(save_file, 'r') as f:
                json.load(f)

    def test_handle_incomplete_data(self, tmp_path):
        """Test handling incomplete gamestate data."""
        save_file = tmp_path / "incomplete_save.json"
        incomplete_data = {"Credits": 100}  # Missing other required keys
        
        with open(save_file, 'w') as f:
            json.dump(incomplete_data, f)
        
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        # File loads, but missing keys
        assert 'Credits' in loaded
        assert 'Inventar' not in loaded


class TestDynamicGameProgress:
    """Tests for saving dynamic game progress."""

    def test_save_after_building(self, fresh_gamestate, tmp_path):
        """Test saving after building something."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Inventar']['Eisenbarren'] = 10
        test_state['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 2
        
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Inventar']['Eisenbarren'] == 10
        assert loaded['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == 2

    def test_save_after_travel(self, fresh_gamestate, tmp_path):
        """Test saving after completing a journey."""
        save_file = tmp_path / "test_save.json"
        
        test_state = copy.deepcopy(fresh_gamestate)
        test_state['Planeten']['Mond']['entdeckt'] = True
        test_state['Astronauten']['Erde'] = 8
        test_state['Astronauten']['Mond'] = 2
        test_state['Raumschiffe']['Mond']['Mondlander']['Anzahl'] = 1
        
        with open(save_file, 'w') as f:
            json.dump(test_state, f)
        
        with open(save_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['Planeten']['Mond']['entdeckt'] == True
        assert loaded['Astronauten']['Mond'] == 2
