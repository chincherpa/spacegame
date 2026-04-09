"""
Event Handlers for Spacegame.

This module contains handler functions for UI events.
Each handler receives an Event object and can access the game systems.
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.game_state import GameState
    from core.research import ResearchSystem
    from core.building import BuildingSystem
    from ui.controller import UIController
    from ui.events import Event

logger = logging.getLogger(__name__)


class GameHandlers:
    """
    Collection of event handlers for game events.
    
    This class holds references to game systems and provides
    handler methods that can be registered with the EventDispatcher.
    
    Usage:
        handlers = GameHandlers(game, research, building, ui)
        
        dispatcher.register('do_research', handlers.on_do_research)
        dispatcher.register_prefix('Erforsche ', handlers.on_research_selected)
    """
    
    def __init__(
        self,
        game_state: 'GameState',
        research_system: 'ResearchSystem',
        building_system: 'BuildingSystem',
        ui_controller: 'UIController',
        science_data: dict,
        actions_data: dict,
        earth_jobs_data: dict
    ):
        """
        Initialize handlers with game systems.
        
        Args:
            game_state: The game state.
            research_system: The research system.
            building_system: The building system.
            ui_controller: The UI controller.
            science_data: SCIENCE dictionary.
            actions_data: ACTIONS dictionary.
            earth_jobs_data: ERDE_JOBS dictionary.
        """
        self.game = game_state
        self.research = research_system
        self.building = building_system
        self.ui = ui_controller
        self.science = science_data
        self.actions = actions_data
        self.earth_jobs = earth_jobs_data
        
        # Track current selections
        self.current_research_selection: str = ''
        self.current_build_selection: str = ''
        self.current_mission_selection: str = ''
    
    # ========== Research Handlers ==========
    
    def on_research_selected(self, event: 'Event') -> None:
        """Handle research button click to show info."""
        research_name = event.data.get('_suffix', '')
        if not research_name:
            return
        
        self.current_research_selection = research_name
        research_data = self.science.get(research_name, {})
        
        self.ui.show_research_info(
            name=research_name,
            description=research_data.get('beschreibung', ''),
            duration=research_data.get('dauer', 0),
            cost=research_data.get('kosten', 0),
            can_afford=self.game.research_points >= research_data.get('kosten', 0),
            is_researched=self.game.is_researched(research_name)
        )
        
        event.handled = True
        logger.debug(f'Research selected: {research_name}')
    
    def on_do_research(self, event: 'Event') -> None:
        """Handle starting research."""
        if not self.current_research_selection:
            return
        
        if self.research.start(self.current_research_selection):
            # UI will update automatically via observer
            pass
        
        event.handled = True
    
    def on_stop_research(self, event: 'Event') -> None:
        """Handle stopping research."""
        stopped = self.research.stop()
        if stopped:
            self.ui._safe_update('progressbar_Forschung', visible=False)
            self.ui._safe_update('stop_research', visible=False)
            self.ui._safe_update('do_research', visible=True)
        
        event.handled = True
    
    # ========== Building Handlers ==========
    
    def on_build_selected(self, event: 'Event') -> None:
        """Handle build button click to show info."""
        build_name = event.data.get('_suffix', '')
        if not build_name:
            return
        
        self.current_build_selection = build_name
        item = self.game.get_workshop_item(build_name)
        
        can_build, reason = self.building.can_build(build_name)
        
        self.ui.show_build_info(
            name=build_name,
            description=item.get('beschreibung', ''),
            duration=item.get('dauer', 0),
            materials=item.get('material', {}),
            can_build=can_build and not self.building.is_active,
            reason=reason if not can_build else ''
        )
        
        event.handled = True
        logger.debug(f'Build selected: {build_name}')
    
    def on_do_build(self, event: 'Event') -> None:
        """Handle queueing a build."""
        if not self.current_build_selection:
            return
        
        if self.building.queue_build(self.current_build_selection):
            self.ui.update_build_queue(self.building.get_queue_names())
            self.ui.update_inventory()
            # Refresh build info
            self.on_build_selected(event)
        
        event.handled = True
    
    def on_stop_build(self, event: 'Event') -> None:
        """Handle stopping current build."""
        stopped = self.building.stop_current()
        if stopped:
            self.ui.hide_build_progress()
            self.ui.update_inventory()
        
        event.handled = True
    
    def on_cancel_build_queue(self, event: 'Event') -> None:
        """Handle cancelling next queued build."""
        cancelled = self.building.cancel_next()
        if cancelled:
            self.ui.update_build_queue(self.building.get_queue_names())
            self.ui.update_inventory()
        else:
            self.game.add_log("Keine Bauaufträge zu stornieren.")
        
        event.handled = True
    
    # ========== Tab Handlers ==========
    
    def on_tab_changed(self, event: 'Event') -> None:
        """Handle tab change."""
        values = event.data.get('_values', {})
        current_tab = values.get('TabGroup_Main', '')
        
        if current_tab:
            self.ui.update_tab_image(current_tab)
            
            # Refresh relevant data
            if current_tab == 'tab_Inventar':
                self.ui.update_inventory()
                self.ui.update_spaceships()
            elif current_tab == 'tab_Forschung' and self.current_research_selection:
                # Re-show current research info
                pass
        
        event.handled = True
    
    # ========== Save/Load Handlers ==========
    
    def on_save(self, event: 'Event') -> None:
        """Handle save game."""
        import config
        self.game.save(config.SAVEFILE)
        self.game.add_log("Spiel gespeichert.")
        event.handled = True
    
    def on_load(self, event: 'Event') -> None:
        """Handle load game."""
        import config
        from core.game_state import GameState
        
        # Load new state
        new_state = GameState.load(config.SAVEFILE)
        
        # Copy state to current game
        self.game._state = new_state._state
        
        # Refresh UI
        self.ui.refresh_all()
        self.game.add_log("Spiel geladen.")
        event.handled = True
    
    # ========== Earth Job Handlers ==========
    
    def on_earth_job_selected(self, event: 'Event') -> None:
        """Handle earth job button click."""
        job_name = event.data.get('_suffix', '')
        if not job_name or job_name not in self.earth_jobs:
            return
        
        job_info = self.earth_jobs[job_name]
        belohnung_text = ', '.join([
            f"{menge} {ressource}" 
            for ressource, menge in job_info.get('belohnung', {}).items()
        ])
        
        self.ui.show_earth_job_info(
            description=job_info.get('beschreibung', ''),
            rewards=belohnung_text
        )
        
        event.handled = True


def register_all_handlers(
    dispatcher,
    handlers: GameHandlers
) -> None:
    """
    Register all handlers with the dispatcher.
    
    Args:
        dispatcher: The EventDispatcher.
        handlers: The GameHandlers instance.
    """
    # Research
    dispatcher.register_prefix('Erforsche ', handlers.on_research_selected)
    dispatcher.register('do_research', handlers.on_do_research)
    dispatcher.register('stop_research', handlers.on_stop_research)
    
    # Building
    dispatcher.register_prefix('baue_', handlers.on_build_selected)
    dispatcher.register('do_bauen', handlers.on_do_build)
    dispatcher.register('stop_bauen', handlers.on_stop_build)
    dispatcher.register('storniere_bauauftrag', handlers.on_cancel_build_queue)
    
    # Tabs
    dispatcher.register('TabGroup_Main', handlers.on_tab_changed)
    
    # Save/Load
    dispatcher.register('Save', handlers.on_save)
    dispatcher.register('Load', handlers.on_load)
    
    # Earth Jobs
    dispatcher.register_prefix('start_erde_job_', handlers.on_earth_job_selected)
    
    logger.info(f'Registered {10} handlers with dispatcher')
