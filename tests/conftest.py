"""
Pytest configuration and shared fixtures for Spacegame tests.
"""
import copy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def fresh_gamestate():
    """Provides a fresh copy of the default GAMESTATE for each test."""
    from gamestate import GAMESTATE
    return copy.deepcopy(GAMESTATE)


@pytest.fixture
def test_actions():
    """Provides the ACTIONS dictionary."""
    from actions import ACTIONS
    return ACTIONS


@pytest.fixture
def test_science():
    """Provides the SCIENCE dictionary."""
    from science import SCIENCE
    return SCIENCE


@pytest.fixture
def test_materials():
    """Provides the MATERIALS dictionary."""
    from materials import MATERIALS
    return MATERIALS


@pytest.fixture
def test_shop():
    """Provides the SHOP dictionary."""
    from shop import SHOP
    return SHOP


@pytest.fixture
def mock_window():
    """Provides a mock for the FreeSimpleGUI window."""
    mock = MagicMock()
    # Mock common window methods
    mock.__getitem__ = MagicMock(return_value=MagicMock())
    mock.read = MagicMock(return_value=(None, {}))
    mock.refresh = MagicMock()
    mock.close = MagicMock()
    return mock


@pytest.fixture
def mock_sg():
    """Provides a mock for the entire FreeSimpleGUI module."""
    mock = MagicMock()
    mock.Window = MagicMock(return_value=MagicMock())
    mock.theme = MagicMock()
    mock.Text = MagicMock()
    mock.Button = MagicMock()
    mock.Column = MagicMock()
    mock.Tab = MagicMock()
    mock.TabGroup = MagicMock()
    mock.ProgressBar = MagicMock()
    mock.Multiline = MagicMock()
    mock.HorizontalSeparator = MagicMock()
    mock.VerticalSeparator = MagicMock()
    mock.Radio = MagicMock()
    mock.Spin = MagicMock()
    mock.Menu = MagicMock()
    mock.Image = MagicMock()
    return mock


@pytest.fixture
def gamestate_with_research(fresh_gamestate):
    """Provides GAMESTATE with some research completed."""
    gs = fresh_gamestate
    gs['Forschung']['Eisenbarren']['erforscht'] = True
    gs['Forschung']['Baumaterial']['erforscht'] = True
    gs['Forschung']['Werkzeug']['erforscht'] = True
    return gs


@pytest.fixture
def gamestate_with_resources(fresh_gamestate):
    """Provides GAMESTATE with many resources for testing."""
    gs = fresh_gamestate
    gs['Inventar']['Eisenbarren'] = 100
    gs['Inventar']['Werkzeug'] = 50
    gs['Inventar']['Baumaterial'] = 50
    gs['Inventar']['Roheisen'] = 100
    gs['Inventar']['Wasser'] = 100
    gs['Inventar']['Staub'] = 100
    gs['Credits'] = 100000
    gs['Forschungspunkte'] = 1000
    return gs


@pytest.fixture
def gamestate_with_moon_discovered(fresh_gamestate):
    """Provides GAMESTATE with Moon discovered."""
    gs = fresh_gamestate
    gs['Planeten']['Mond']['entdeckt'] = True
    gs['Astronauten']['Mond'] = 5
    gs['Raumschiffe']['Mond']['Mondlander']['Anzahl'] = 2
    return gs


@pytest.fixture
def gamestate_with_spaceships(fresh_gamestate):
    """Provides GAMESTATE with spaceships on Earth."""
    gs = fresh_gamestate
    gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 3
    gs['Raumschiffe']['Erde']['Rakete']['Anzahl'] = 2
    gs['Forschung']['Mondlander']['erforscht'] = True
    gs['Forschung']['Rakete']['erforscht'] = True
    return gs


@pytest.fixture
def temp_savefile(tmp_path):
    """Provides a temporary path for save file testing."""
    return tmp_path / "test_savefile.json"
