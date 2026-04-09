# Core module for Spacegame
"""
Core game logic modules.

Usage:
    from core import GameState, ResearchSystem, BuildingSystem
"""

from core.game_state import GameState
from core.research import ResearchSystem
from core.building import BuildingSystem

__all__ = ['GameState', 'ResearchSystem', 'BuildingSystem']
