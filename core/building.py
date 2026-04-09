"""
Building System for Spacegame.

Manages the construction/crafting mechanics including:
- Starting and stopping builds
- Build queue management
- Material checking and consumption
- Build completion
"""

import logging
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from core.game_state import GameState

logger = logging.getLogger(__name__)


@dataclass
class BuildOrder:
    """Represents a single build order in the queue."""
    item_name: str
    materials_consumed: dict = field(default_factory=dict)


class BuildingSystem:
    """
    Manages construction/crafting.
    
    Usage:
        building = BuildingSystem(game_state)
        
        # Queue a build
        if building.queue_build('Eisenbarren'):
            print("Queued!")
        
        # Each tick
        completed = building.tick()
        if completed:
            print(f"Built: {completed}")
    """
    
    def __init__(self, game_state: 'GameState'):
        """
        Initialize the building system.
        
        Args:
            game_state: The game state instance.
        """
        self.game_state = game_state
        self.queue: list[BuildOrder] = []
        self.current_build: Optional[str] = None
        self.progress: int = 0
        self.max_progress: int = 0
        logger.debug('BuildingSystem initialized')
    
    def can_build(self, name: str) -> tuple[bool, str]:
        """
        Check if a specific item can be built.
        
        Args:
            name: Name of the item to check.
            
        Returns:
            Tuple of (can_build, reason_if_not)
        """
        # Check if item exists in workshop
        item = self.game_state.get_workshop_item(name)
        if not item:
            return False, f"Unbekanntes Item: {name}"
        
        # Check if research is completed
        if not self.game_state.is_researched(name):
            return False, f"Forschung '{name}' noch nicht abgeschlossen"
        
        # Check materials
        for material, required in item.get('material', {}).items():
            available = self.game_state.get_inventory(material)
            if available < required:
                return False, f"Nicht genug {material} (benötigt: {required}, verfügbar: {available})"
        
        return True, ""
    
    def queue_build(self, name: str) -> bool:
        """
        Add an item to the build queue.
        
        Materials are consumed immediately when added to queue.
        
        Args:
            name: Name of the item to build.
            
        Returns:
            True if successfully added to queue.
        """
        can, reason = self.can_build(name)
        if not can:
            logger.warning(f"Cannot build '{name}': {reason}")
            return False
        
        item = self.game_state.get_workshop_item(name)
        materials = item.get('material', {})
        
        # Consume materials
        consumed = {}
        for material, required in materials.items():
            self.game_state.remove_from_inventory(material, required)
            consumed[material] = required
        
        # Add to queue
        order = BuildOrder(item_name=name, materials_consumed=consumed)
        self.queue.append(order)
        
        logger.info(f"Build queued: {name}")
        self.game_state.add_log(f"Bauauftrag hinzugefügt: {name}")
        
        return True
    
    def cancel_next(self) -> Optional[str]:
        """
        Cancel the next item in the queue (not current build).
        
        Materials are refunded.
        
        Returns:
            Name of cancelled item, or None if queue empty.
        """
        if not self.queue:
            return None
        
        order = self.queue.pop(0)
        
        # Refund materials
        for material, amount in order.materials_consumed.items():
            self.game_state.add_to_inventory(material, amount)
        
        logger.info(f"Build cancelled: {order.item_name}")
        self.game_state.add_log(f"Bauauftrag storniert: {order.item_name}")
        
        return order.item_name
    
    def stop_current(self) -> Optional[str]:
        """
        Stop the current build and refund materials.
        
        Returns:
            Name of stopped build, or None if nothing active.
        """
        if self.current_build is None:
            return None
        
        stopped = self.current_build
        item = self.game_state.get_workshop_item(stopped)
        
        # Refund materials
        for material, amount in item.get('material', {}).items():
            self.game_state.add_to_inventory(material, amount)
        
        # Reset state
        self.current_build = None
        self.progress = 0
        self.max_progress = 0
        
        logger.info(f"Build stopped: {stopped}")
        self.game_state.add_log(f"Bau gestoppt: {stopped}")
        
        return stopped
    
    def _start_next_build(self) -> bool:
        """
        Start the next build from the queue.
        
        Returns:
            True if a build was started.
        """
        if not self.queue:
            return False
        
        if self.current_build is not None:
            return False
        
        order = self.queue.pop(0)
        item = self.game_state.get_workshop_item(order.item_name)
        
        self.current_build = order.item_name
        self.progress = 0
        self.max_progress = item.get('dauer', 1)
        
        logger.info(f"Build started: {order.item_name} (duration: {self.max_progress} ticks)")
        self.game_state.add_log(f"Baue: {order.item_name}")
        
        return True
    
    def _complete_build(self) -> str:
        """
        Complete the current build and add item to inventory/spaceships.
        
        Returns:
            Name of completed item.
        """
        completed = self.current_build
        
        # Add to appropriate storage
        if completed in ['Mondlander', 'Rakete']:
            # Spaceships go to Earth
            self.game_state.add_spaceship('Erde', completed)
            self.game_state.add_log(f"'{completed}' gebaut - zur Erde hinzugefügt")
        else:
            # Other items go to inventory
            self.game_state.add_to_inventory(completed, 1)
            self.game_state.add_log(f"'{completed}' gebaut - ins Inventar gelegt")
        
        # Reset state
        self.current_build = None
        self.progress = 0
        self.max_progress = 0
        
        logger.info(f"Build completed: {completed}")
        
        return completed
    
    def tick(self) -> Optional[str]:
        """
        Process one tick of build progress.
        
        Call this method once per game tick.
        
        Returns:
            Name of completed item, or None if not completed.
        """
        # Start next build if idle
        if self.current_build is None and self.queue:
            self._start_next_build()
        
        if self.current_build is None:
            return None
        
        self.progress += 1
        
        if self.progress >= self.max_progress:
            return self._complete_build()
        
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if a build is currently in progress."""
        return self.current_build is not None
    
    @property
    def progress_percent(self) -> float:
        """Get current progress as percentage (0-100)."""
        if self.max_progress == 0:
            return 0.0
        return (self.progress / self.max_progress) * 100
    
    @property
    def queue_count(self) -> int:
        """Get number of items in the build queue."""
        return len(self.queue)
    
    def get_queue_names(self) -> list[str]:
        """Get list of item names in the queue."""
        return [order.item_name for order in self.queue]
