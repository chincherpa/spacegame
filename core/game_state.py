"""
GameState class for managing game state with observer pattern.

This module provides a centralized way to manage the game state,
with support for observers that can react to state changes.
"""

import json
import logging
from typing import Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# Default initial game state
DEFAULT_STATE = {
    'Ticks': 0,
    'Credits': 10,
    'Forschungspunkte': 0,

    'Astronauten': {
        'Erde': 10,
        'Mond': 0,
        'Mars': 0
    },

    'Arbeiter': {
        'Erde': 10,
        'Mond': 0,
        'Mars': 0
    },

    'Raumschiffe': {
        'Erde': {
            'Mondlander': {'Anzahl': 0},
            'Rakete': {'Anzahl': 0}
        },
        'Mond': {
            'Mondlander': {'Anzahl': 0},
            'Rakete': {'Anzahl': 0}
        },
        'Mars': {
            'Mondlander': {'Anzahl': 0},
            'Rakete': {'Anzahl': 0}
        },
    },

    'Forschung': {
        'Eisenbarren': {'erforscht': False},
        'Baumaterial': {'erforscht': False},
        'Werkzeug': {'erforscht': False},
        'Treibstoff': {'erforscht': False},
        'Raumsonde': {'erforscht': False},
        'Mondlander': {'erforscht': False},
        'Rakete': {'erforscht': False},
        'Mondbasen Bauplan': {'erforscht': False},
        'Weltraumstation': {'erforscht': False},
    },

    'Werkstatt': {
        'Baumaterial': {
            'beschreibung': 'Baumaterial aus Staub und Wasser herstellen.',
            'dauer': 2,
            'material': {'Staub': 1, 'Wasser': 1},
        },
        'Eisenbarren': {
            'beschreibung': 'Eisenbarren aus Roheisen schmelzen.',
            'dauer': 2,
            'material': {'Roheisen': 1},
        },
        'Werkzeug': {
            'beschreibung': 'Werkzeug aus Eisenbarren und Wasser herstellen.',
            'dauer': 2,
            'material': {'Eisenbarren': 1, 'Wasser': 1},
        },
        'Raumsonde': {
            'beschreibung': 'Eine Raumsonde für Weltraumerkundung.',
            'dauer': 2,
            'material': {'Eisenbarren': 5, 'Werkzeug': 5},
        },
        'Mondlander': {
            'beschreibung': 'Ein Transportschiff zum Mond.',
            'dauer': 2,
            'material': {'Eisenbarren': 10, 'Werkzeug': 10},
        },
        'Rakete': {
            'beschreibung': 'Eine Rakete für interplanetare Reisen.',
            'dauer': 2,
            'material': {'Eisenbarren': 30, 'Werkzeug': 20},
        },
        'Weltraumstation': {
            'beschreibung': 'Eine große Raumstation.',
            'dauer': 10,
            'material': {'Mondlander': 5, 'Eisenbarren': 100, 'Werkzeug': 10},
        },
    },

    'Inventar': {
        'Baumaterial': 0,
        'Eisenbarren': 0,
        'Roheisen': 10,
        'Staub': 5,
        'Gold': 0,
        'Werkzeug': 0,
        'Wasser': 10,
        'Raumsonde': 0,
        'Mondgestein': 0,
        'Seltene_Mineralien': 0,
        'Mondstation_Modul': 0,
        'Astronaut_Erfahrung': 0,
        'Lebenserhaltung_Upgrade': 0,
        'Kommunikations_Upgrade': 0,
        'Mondbasen Bauplan': 0,
    },

    'Planeten': {
        'Erde': {
            'Entfernung': {'Mond': 1, 'Mars': 3}
        },
        'Mond': {
            'entdeckt': False,
            'Entfernung': {'Erde': 1, 'Mars': 2}
        },
        'Mars': {
            'entdeckt': False,
            'Entfernung': {'Erde': 3, 'Mond': 2}
        },
    },

    'Log': ['Spiel gestartet'],

    'Mondmissionen': {
        'Erkundung und Probenentnahme': {'erforscht': False},
        'Konstruktion und Reparatur von Strukturen': {'erforscht': False, 'benötigt_baumaterial': 3},
        'Navigation und Anpassung an die geringere Schwerkraft': {'erforscht': False},
        'Raumfahrttechnik und -navigation': {'erforscht': False},
        'Geologische Untersuchungen': {'erforscht': False},
        'Lebenserhaltungssysteme': {'erforscht': False},
        'Kommunikation und Datenübertragung': {'erforscht': False},
        'Mondbasen-Design': {'erforscht': False}
    },
}


class GameState:
    """
    Manages the game state with support for observers.
    
    Usage:
        # Create a new game
        game = GameState()
        
        # Load from file
        game = GameState.load('savefile.json')
        
        # Access properties
        print(game.credits)
        game.credits += 100
        
        # Save to file
        game.save('savefile.json')
    """
    
    def __init__(self, initial_state: Optional[dict] = None):
        """
        Initialize game state.
        
        Args:
            initial_state: Optional dictionary with initial state.
                          Uses DEFAULT_STATE if not provided.
        """
        import copy
        self._state = copy.deepcopy(initial_state or DEFAULT_STATE)
        self._observers: list[Callable[[str, Any], None]] = []
        logger.debug('GameState initialized')
    
    # ========== Observer Pattern ==========
    
    def add_observer(self, callback: Callable[[str, Any], None]) -> None:
        """
        Add an observer that will be called on state changes.
        
        Args:
            callback: Function(key, value) called when state changes.
        """
        self._observers.append(callback)
        logger.debug(f'Observer added, total: {len(self._observers)}')
    
    def remove_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Remove an observer."""
        self._observers.remove(callback)
    
    def _notify_observers(self, key: str, value: Any) -> None:
        """Notify all observers of a state change."""
        for observer in self._observers:
            try:
                observer(key, value)
            except Exception as e:
                logger.error(f'Observer error: {e}')
    
    # ========== Basic Properties ==========
    
    @property
    def ticks(self) -> int:
        """Current game tick/cycle."""
        return self._state['Ticks']
    
    @ticks.setter
    def ticks(self, value: int) -> None:
        self._state['Ticks'] = value
        self._notify_observers('ticks', value)
    
    @property
    def credits(self) -> int:
        """Current credits."""
        return self._state['Credits']
    
    @credits.setter
    def credits(self, value: int) -> None:
        self._state['Credits'] = value
        self._notify_observers('credits', value)
    
    @property
    def research_points(self) -> int:
        """Current research points (Forschungspunkte)."""
        return self._state['Forschungspunkte']
    
    @research_points.setter
    def research_points(self, value: int) -> None:
        self._state['Forschungspunkte'] = value
        self._notify_observers('research_points', value)
    
    # ========== Inventory ==========
    
    def get_inventory(self, material: str) -> int:
        """Get amount of a material in inventory."""
        return self._state['Inventar'].get(material, 0)
    
    def set_inventory(self, material: str, amount: int) -> None:
        """Set amount of a material in inventory."""
        self._state['Inventar'][material] = amount
        self._notify_observers(f'inventory_{material}', amount)
    
    def add_to_inventory(self, material: str, amount: int) -> None:
        """Add amount to a material in inventory."""
        current = self.get_inventory(material)
        self.set_inventory(material, current + amount)
    
    def remove_from_inventory(self, material: str, amount: int) -> bool:
        """
        Remove amount from inventory if available.
        
        Returns:
            True if successfully removed, False if not enough.
        """
        current = self.get_inventory(material)
        if current >= amount:
            self.set_inventory(material, current - amount)
            return True
        return False
    
    # ========== Research ==========
    
    def is_researched(self, name: str) -> bool:
        """Check if a technology is researched."""
        return self._state['Forschung'].get(name, {}).get('erforscht', False)
    
    def complete_research(self, name: str) -> None:
        """Mark a technology as researched."""
        if name in self._state['Forschung']:
            self._state['Forschung'][name]['erforscht'] = True
            self._notify_observers('research_completed', name)
            logger.info(f'Research completed: {name}')
    
    # ========== Planets ==========
    
    def is_planet_discovered(self, planet: str) -> bool:
        """Check if a planet is discovered."""
        if planet == 'Erde':
            return True
        return self._state['Planeten'].get(planet, {}).get('entdeckt', False)
    
    def discover_planet(self, planet: str) -> None:
        """Mark a planet as discovered."""
        if planet in self._state['Planeten']:
            self._state['Planeten'][planet]['entdeckt'] = True
            self._notify_observers('planet_discovered', planet)
            logger.info(f'Planet discovered: {planet}')
    
    def get_planet_distance(self, from_planet: str, to_planet: str) -> int:
        """Get distance between two planets."""
        return self._state['Planeten'][from_planet]['Entfernung'].get(to_planet, 0)
    
    # ========== Astronauts ==========
    
    def get_astronauts(self, planet: str) -> int:
        """Get number of astronauts on a planet."""
        return self._state['Astronauten'].get(planet, 0)
    
    def set_astronauts(self, planet: str, count: int) -> None:
        """Set number of astronauts on a planet."""
        self._state['Astronauten'][planet] = count
        self._notify_observers(f'astronauts_{planet}', count)
    
    def transfer_astronauts(self, from_planet: str, to_planet: str, count: int) -> bool:
        """Transfer astronauts between planets."""
        current = self.get_astronauts(from_planet)
        if current >= count:
            self.set_astronauts(from_planet, current - count)
            self.set_astronauts(to_planet, self.get_astronauts(to_planet) + count)
            return True
        return False
    
    # ========== Workers ==========
    
    def get_workers(self, planet: str) -> int:
        """Get number of workers on a planet."""
        return self._state['Arbeiter'].get(planet, 0)
    
    # ========== Spaceships ==========
    
    def get_spaceships(self, planet: str, ship_type: str) -> int:
        """Get number of spaceships of a type on a planet."""
        return self._state['Raumschiffe'].get(planet, {}).get(ship_type, {}).get('Anzahl', 0)
    
    def set_spaceships(self, planet: str, ship_type: str, count: int) -> None:
        """Set number of spaceships of a type on a planet."""
        self._state['Raumschiffe'][planet][ship_type]['Anzahl'] = count
        self._notify_observers(f'spaceships_{planet}_{ship_type}', count)
    
    def add_spaceship(self, planet: str, ship_type: str) -> None:
        """Add a spaceship to a planet."""
        current = self.get_spaceships(planet, ship_type)
        self.set_spaceships(planet, ship_type, current + 1)
    
    # ========== Workshop ==========
    
    def get_workshop_item(self, name: str) -> dict:
        """Get workshop item definition."""
        return self._state['Werkstatt'].get(name, {})
    
    def can_build(self, name: str) -> tuple[bool, str]:
        """
        Check if an item can be built.
        
        Returns:
            Tuple of (can_build, reason)
        """
        item = self.get_workshop_item(name)
        if not item:
            return False, f"Unbekanntes Item: {name}"
        
        for material, required in item.get('material', {}).items():
            available = self.get_inventory(material)
            if available < required:
                return False, f"Nicht genug {material} (benötigt: {required}, verfügbar: {available})"
        
        return True, ""
    
    # ========== Log ==========
    
    @property
    def log(self) -> list[str]:
        """Game log entries."""
        return self._state['Log']
    
    def add_log(self, message: str) -> None:
        """Add a message to the game log."""
        entry = f"{self.ticks}\t{message}"
        self._state['Log'].append(entry)
        self._notify_observers('log', entry)
    
    # ========== Raw State Access ==========
    
    @property
    def raw(self) -> dict:
        """Direct access to raw state dict (for compatibility)."""
        return self._state
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for compatibility."""
        return self._state[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like assignment for compatibility."""
        self._state[key] = value
        self._notify_observers(key, value)
    
    # ========== Save/Load ==========
    
    def save(self, filepath: str) -> None:
        """
        Save game state to a JSON file.
        
        Args:
            filepath: Path to the save file.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
        logger.info(f'Game saved to {filepath}')
    
    @classmethod
    def load(cls, filepath: str) -> 'GameState':
        """
        Load game state from a JSON file.
        
        Args:
            filepath: Path to the save file.
            
        Returns:
            GameState instance with loaded data.
        """
        path = Path(filepath)
        if not path.exists():
            logger.warning(f'Save file not found: {filepath}, using default state')
            return cls()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        logger.info(f'Game loaded from {filepath}')
        return cls(state)
    
    # ========== Utilities ==========
    
    def reset(self) -> None:
        """Reset to default state."""
        import copy
        self._state = copy.deepcopy(DEFAULT_STATE)
        self._notify_observers('reset', True)
        logger.info('Game state reset to default')
