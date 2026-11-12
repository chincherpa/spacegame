"""
Pytest configuration and shared fixtures for Spacegame tests.
"""
import copy
import sys
from pathlib import Path

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
def spiel(tmp_path, monkeypatch):
    """Importiert main.py frisch mit einem Fenster-Ersatz und leerem Spielstand.

    Jeder Test bekommt ein eigenes Arbeitsverzeichnis, damit Spielstände nicht
    zwischen Tests (oder ins Repo) durchsickern. Zufallsereignisse auf Reisen
    sind abgeschaltet, damit Abläufe vorhersagbar bleiben.
    """
    import config
    from tests import fake_sg

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, 'TRAVEL_EVENTS_ENABLED', False)
    monkeypatch.setitem(sys.modules, 'FreeSimpleGUI', fake_sg.erstelle_modul())
    monkeypatch.delitem(sys.modules, 'main', raising=False)
    import main
    yield main
    sys.modules.pop('main', None)
