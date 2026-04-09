# UI module for Spacegame
"""
User interface modules for separating UI from game logic.

Usage:
    from ui import UIController, EventDispatcher, GameHandlers
"""

from ui.controller import UIController
from ui.events import EventDispatcher, GameEventBus, Event
from ui.handlers import GameHandlers, register_all_handlers

__all__ = [
    'UIController',
    'EventDispatcher',
    'GameEventBus',
    'Event',
    'GameHandlers',
    'register_all_handlers'
]

