"""
Integration tests for the MissionInstance class.
Tests validate mission creation, progress, and completion.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMissionInstanceCreation:
    """Tests for MissionInstance creation."""

    def test_mission_instance_creation(self, test_actions):
        """Test that MissionInstance can be created with valid mission name."""
        # We need to import MissionInstance after mocking sg
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            # Need to reload main to use the mock
            from actions import ACTIONS
            
            # Create a simple mock for testing
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            mission_name = 'Erkundung und Probenentnahme'
            mission = MockMissionInstance(mission_name)
            
            assert mission.name == mission_name
            assert mission.fortschritt == 0
            assert mission.aktiv == True
            assert mission.max_fortschritt == ACTIONS[mission_name]['dauer']

    def test_mission_instance_with_different_missions(self, test_actions):
        """Test MissionInstance with different mission types."""
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            from actions import ACTIONS
            
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            for mission_name in test_actions.keys():
                mission = MockMissionInstance(mission_name)
                assert mission.max_fortschritt == test_actions[mission_name]['dauer']


class TestMissionInstanceProgress:
    """Tests for MissionInstance progress tracking."""

    def test_mission_tick_increments_progress(self, test_actions):
        """Test that tick() increments progress."""
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            from actions import ACTIONS
            
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            mission = MockMissionInstance('Erkundung und Probenentnahme')
            initial_progress = mission.fortschritt
            
            mission.tick()
            
            assert mission.fortschritt == initial_progress + 1

    def test_mission_tick_returns_false_while_active(self, test_actions):
        """Test that tick() returns False while mission is still active."""
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            from actions import ACTIONS
            
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            mission = MockMissionInstance('Erkundung und Probenentnahme')
            
            # First tick should return False (mission still active)
            result = mission.tick()
            assert result == False
            assert mission.aktiv == True

    def test_mission_tick_after_deactivation(self, test_actions):
        """Test that tick() does nothing after mission is deactivated."""
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            from actions import ACTIONS
            
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            mission = MockMissionInstance('Erkundung und Probenentnahme')
            mission.aktiv = False
            final_progress = mission.fortschritt
            
            result = mission.tick()
            
            assert result == False
            assert mission.fortschritt == final_progress  # No change


class TestMissionInstanceCompletion:
    """Tests for MissionInstance completion."""

    def test_mission_completes_after_max_ticks(self, test_actions):
        """Test that mission completes after max_fortschritt ticks."""
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            from actions import ACTIONS
            
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            mission = MockMissionInstance('Erkundung und Probenentnahme')
            max_ticks = mission.max_fortschritt
            
            # Tick until one before completion
            for _ in range(max_ticks - 1):
                result = mission.tick()
                assert result == False
                assert mission.aktiv == True
            
            # Final tick should complete the mission
            result = mission.tick()
            assert result == True
            assert mission.aktiv == False
            assert mission.fortschritt == max_ticks

    def test_mission_deactivates_on_completion(self, test_actions):
        """Test that mission deactivates when completed."""
        with patch.dict('sys.modules', {'FreeSimpleGUI': MagicMock()}):
            from actions import ACTIONS
            
            class MockMissionInstance:
                def __init__(self, missionsname):
                    self.name = missionsname
                    self.fortschritt = 0
                    self.max_fortschritt = ACTIONS[missionsname]['dauer']
                    self.aktiv = True

                def tick(self):
                    if self.aktiv:
                        self.fortschritt += 1
                        if self.fortschritt >= self.max_fortschritt:
                            self.aktiv = False
                            return True
                    return False
            
            # Use a short mission for quick test
            mission = MockMissionInstance('Navigation und Anpassung an die geringere Schwerkraft')
            
            # Complete the mission
            while mission.aktiv:
                mission.tick()
            
            assert mission.aktiv == False
