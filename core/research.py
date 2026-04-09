"""
Research System for Spacegame.

Manages the research mechanics including:
- Starting and stopping research
- Progress tracking
- Prerequisite checking
- Research completion
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.game_state import GameState

logger = logging.getLogger(__name__)


class ResearchSystem:
    """
    Manages research progression.
    
    Usage:
        research = ResearchSystem(game_state, SCIENCE)
        
        # Start research
        if research.can_research('Eisenbarren')[0]:
            research.start('Eisenbarren')
        
        # Each tick
        completed = research.tick()
        if completed:
            print(f"Completed: {completed}")
    """
    
    def __init__(self, game_state: 'GameState', science_data: dict):
        """
        Initialize the research system.
        
        Args:
            game_state: The game state instance.
            science_data: Dictionary with research definitions (from science.py).
        """
        self.game_state = game_state
        self.science = science_data
        self.current_research: Optional[str] = None
        self.progress: int = 0
        self.max_progress: int = 0
        logger.debug('ResearchSystem initialized')
    
    def can_research(self, name: str) -> tuple[bool, str]:
        """
        Check if a specific research can be started.
        
        Args:
            name: Name of the research to check.
            
        Returns:
            Tuple of (can_research, reason_if_not)
        """
        # Check if research exists
        if name not in self.science:
            return False, f"Unbekannte Forschung: {name}"
        
        research = self.science[name]
        
        # Check if already researched
        if self.game_state.is_researched(name):
            return False, "Bereits erforscht"
        
        # Check if currently researching something
        if self.current_research is not None:
            return False, f"Aktuelle Forschung: {self.current_research}"
        
        # Check research points
        cost = research.get('kosten', 0)
        if self.game_state.research_points < cost:
            return False, f"Nicht genug Forschungspunkte (benötigt: {cost})"
        
        # Check prerequisites
        prerequisite = research.get('erforschbar nach', '')
        if prerequisite and not self.game_state.is_researched(prerequisite):
            return False, f"Benötigt zuerst: {prerequisite}"
        
        return True, ""
    
    def start(self, name: str) -> bool:
        """
        Start researching a technology.
        
        Args:
            name: Name of the research to start.
            
        Returns:
            True if research started successfully.
        """
        can, reason = self.can_research(name)
        if not can:
            logger.warning(f"Cannot start research '{name}': {reason}")
            return False
        
        research = self.science[name]
        
        # Deduct research points
        cost = research.get('kosten', 0)
        self.game_state.research_points -= cost
        
        # Start research
        self.current_research = name
        self.progress = 0
        self.max_progress = research.get('dauer', 1)
        
        logger.info(f"Research started: {name} (duration: {self.max_progress} ticks)")
        self.game_state.add_log(f"Forschung gestartet: {name}")
        
        return True
    
    def stop(self) -> Optional[str]:
        """
        Stop current research and refund points.
        
        Returns:
            Name of stopped research, or None if nothing was active.
        """
        if self.current_research is None:
            return None
        
        stopped = self.current_research
        research = self.science[stopped]
        
        # Refund research points
        cost = research.get('kosten', 0)
        self.game_state.research_points += cost
        
        # Reset state
        self.current_research = None
        self.progress = 0
        self.max_progress = 0
        
        logger.info(f"Research stopped: {stopped}, points refunded: {cost}")
        self.game_state.add_log(f"Forschung gestoppt: {stopped}")
        
        return stopped
    
    def tick(self) -> Optional[str]:
        """
        Process one tick of research progress.
        
        Call this method once per game tick.
        
        Returns:
            Name of completed research, or None if not completed.
        """
        if self.current_research is None:
            return None
        
        self.progress += 1
        
        if self.progress >= self.max_progress:
            completed = self.current_research
            
            # Mark as researched
            self.game_state.complete_research(completed)
            
            # Reset state
            self.current_research = None
            self.progress = 0
            self.max_progress = 0
            
            logger.info(f"Research completed: {completed}")
            self.game_state.add_log(f"Forschung abgeschlossen: {completed}")
            
            return completed
        
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if research is currently in progress."""
        return self.current_research is not None
    
    @property
    def progress_percent(self) -> float:
        """Get current progress as percentage (0-100)."""
        if self.max_progress == 0:
            return 0.0
        return (self.progress / self.max_progress) * 100
    
    def get_available_research(self) -> list[str]:
        """
        Get list of research that can currently be started.
        
        Returns:
            List of research names that meet all requirements.
        """
        available = []
        for name in self.science:
            can, _ = self.can_research(name)
            if can:
                available.append(name)
        return available
    
    def get_unlocked_research(self) -> list[str]:
        """
        Get list of research that is visible (prerequisites met but maybe not affordable).
        
        Returns:
            List of research names that are unlocked.
        """
        unlocked = []
        for name, data in self.science.items():
            if self.game_state.is_researched(name):
                # Already researched, still show it
                unlocked.append(name)
                continue
            
            prerequisite = data.get('erforschbar nach', '')
            if not prerequisite or self.game_state.is_researched(prerequisite):
                unlocked.append(name)
        
        return unlocked
