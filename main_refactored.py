"""
Spacegame - Refactored Main Module

This is a demonstration of how the refactored architecture works.
It can eventually replace main.py once fully tested.

Architecture:
- GameState: Central state management with observer pattern
- ResearchSystem/BuildingSystem: Game logic subsystems
- UIController: Automatic UI updates via observers
- EventDispatcher: Decoupled event handling
- GameHandlers: Event handler implementations
"""

import logging
import time
from typing import Optional

import FreeSimpleGUI as sg

import config
from core import GameState, ResearchSystem, BuildingSystem
from ui import UIController, EventDispatcher
from ui.handlers import GameHandlers, register_all_handlers
from actions import ACTIONS
from science import SCIENCE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Theme
sg.theme('Dark Teal 6')


class SpaceGame:
    """
    Main game class that orchestrates all systems.
    
    This is the refactored approach - all game logic is encapsulated
    in the GameState and subsystems, while the main loop only handles
    events and ticks.
    """
    
    # Earth jobs definition (could be moved to data/)
    ERDE_JOBS = {
        'Laborarbeit': {
            'beschreibung': 'Wissenschaftler arbeiten im Labor und generieren Forschungspunkte.',
            'dauer': 3,
            'benötigt_arbeiter': 1,
            'belohnung': {'Forschungspunkte': 2}
        },
        'Bergbau': {
            'beschreibung': 'Arbeiter bauen Roheisen ab.',
            'dauer': 2,
            'benötigt_arbeiter': 2,
            'belohnung': {'Roheisen': 3}
        },
        'Wasseraufbereitung': {
            'beschreibung': 'Wasser wird aufbereitet und gesammelt.',
            'dauer': 2,
            'benötigt_arbeiter': 1,
            'belohnung': {'Wasser': 2}
        },
        'Staubsammlung': {
            'beschreibung': 'Staub wird für Baumaterial gesammelt.',
            'dauer': 2,
            'benötigt_arbeiter': 1,
            'belohnung': {'Staub': 2}
        },
    }
    
    def __init__(self):
        """Initialize the game."""
        logger.info('Initializing SpaceGame...')
        
        # Load or create game state
        self.game = GameState.load(config.SAVEFILE)
        
        # Initialize subsystems
        self.research = ResearchSystem(self.game, SCIENCE)
        self.building = BuildingSystem(self.game)
        
        # Create window (simplified layout for demo)
        self.window = self._create_window()
        
        # Initialize UI controller
        self.ui = UIController(self.window, self.game)
        
        # Initialize event system
        self.dispatcher = EventDispatcher()
        self.handlers = GameHandlers(
            self.game,
            self.research,
            self.building,
            self.ui,
            SCIENCE,
            ACTIONS,
            self.ERDE_JOBS
        )
        register_all_handlers(self.dispatcher, self.handlers)
        
        # Timing
        self.last_tick = time.time()
        self.running = True
        
        logger.info('SpaceGame initialized successfully')
    
    def _create_window(self) -> sg.Window:
        """Create the main window with a simplified layout for testing."""
        # This is a minimal layout for testing the new architecture
        # The full layout from main.py would be used in production
        
        layout = [
            # Top bar
            [
                sg.Text(f'Cycle: {self.game.ticks}', key='tCycles'),
                sg.Text(f'Credits: {self.game.credits}', key='tCredits'),
                sg.Text(f'Forschungspunkte: {self.game.research_points}', key='tForschungspunkte'),
            ],
            [sg.HorizontalSeparator()],
            
            # Research section
            [sg.Text('Forschung:', font=('Arial', 12, 'bold'))],
            [
                sg.Button('Eisenbarren', key='Erforsche Eisenbarren'),
                sg.Button('Baumaterial', key='Erforsche Baumaterial', visible=False),
                sg.Button('Werkzeug', key='Erforsche Werkzeug', visible=False),
            ],
            [sg.Text('', key='desc_research', size=(50, 3))],
            [sg.Text('', key='desc_dauer')],
            [sg.Text('', key='desc_costs')],
            [sg.Text('', key='comment', text_color='red')],
            [
                sg.Button('Erforschen', key='do_research', visible=False),
                sg.Text('erforscht', key='already_researched', visible=False, text_color='green'),
            ],
            [
                sg.ProgressBar(10, orientation='h', size=(30, 20), key='progressbar_Forschung', visible=False),
                sg.Button('Stop', key='stop_research', visible=False),
            ],
            
            [sg.HorizontalSeparator()],
            
            # Building section
            [sg.Text('Werkstatt:', font=('Arial', 12, 'bold'))],
            [
                sg.Button('Eisenbarren', key='baue_Eisenbarren', visible=False),
                sg.Button('Baumaterial', key='baue_Baumaterial', visible=False),
                sg.Button('Werkzeug', key='baue_Werkzeug', visible=False),
            ],
            [sg.Text('', key='desc_bauen', size=(50, 3))],
            [sg.Text('', key='desc_materialien', size=(50, 3), visible=False)],
            [
                sg.Button('Bauen', key='do_bauen', visible=False),
                sg.Text('', key='bauen_unmöglich', text_color='red', visible=False),
            ],
            [
                sg.ProgressBar(10, orientation='h', size=(30, 20), key='progressbar_Bauen', visible=False),
                sg.Button('Stop', key='stop_bauen', visible=False),
            ],
            [sg.Text('Queue:', font=('Arial', 10))],
            [sg.Text('', key='bau_queue_anzeige', size=(40, 2))],
            [sg.Button('Stornieren', key='storniere_bauauftrag')],
            
            [sg.HorizontalSeparator()],
            
            # Inventory section
            [sg.Text('Inventar:', font=('Arial', 12, 'bold'))],
            [
                sg.Text('Roheisen:', size=(15, 1)),
                sg.Text(str(self.game.get_inventory('Roheisen')), key='inv_anzahl_Roheisen'),
            ],
            [
                sg.Text('Eisenbarren:', size=(15, 1)),
                sg.Text(str(self.game.get_inventory('Eisenbarren')), key='inv_anzahl_Eisenbarren'),
            ],
            [
                sg.Text('Wasser:', size=(15, 1)),
                sg.Text(str(self.game.get_inventory('Wasser')), key='inv_anzahl_Wasser'),
            ],
            [
                sg.Text('Staub:', size=(15, 1)),
                sg.Text(str(self.game.get_inventory('Staub')), key='inv_anzahl_Staub'),
            ],
            
            [sg.HorizontalSeparator()],
            
            # Log
            [sg.Text('Log:', font=('Arial', 10, 'bold'))],
            [sg.Multiline('', key='Log', size=(60, 8), disabled=True, autoscroll=True)],
            
            [sg.HorizontalSeparator()],
            
            # Control buttons
            [
                sg.Button('Save'),
                sg.Button('Load'),
                sg.Button('Exit'),
            ],
        ]
        
        return sg.Window(
            f"{config.TITLE} (Refactored)",
            layout,
            size=(700, 800),
            resizable=True,
            finalize=True
        )
    
    def tick(self) -> None:
        """Process one game tick."""
        self.game.ticks += 1
        
        # Process research
        if self.research.is_active:
            self.ui.update_research_progress(
                self.research.progress,
                self.research.max_progress
            )
            completed = self.research.tick()
            if completed:
                # Update visibility of dependent buttons
                self._update_research_button_visibility()
        
        # Process building
        if self.building.is_active or self.building.queue_count > 0:
            if self.building.is_active:
                self.ui.update_build_progress(
                    self.building.progress,
                    self.building.max_progress
                )
            completed = self.building.tick()
            if completed:
                self.ui.hide_build_progress()
                self.ui.update_build_queue(self.building.get_queue_names())
        
        # Passive income
        if self.game.ticks % config.CREDITS_EXTRA_TICKS == 0:
            self.game.credits += config.CREDITS_EXTRA
        
        if self.game.ticks % config.SCIENCE_POINTS_EXTRA_TICKS == 0:
            self.game.research_points += config.SCIENCE_POINTS_EXTRA
    
    def _update_research_button_visibility(self) -> None:
        """Update research and build button visibility based on completed research."""
        for name, data in SCIENCE.items():
            # Check if this research should be visible
            prerequisite = data.get('erforschbar nach', '')
            is_visible = not prerequisite or self.game.is_researched(prerequisite)
            
            # Update research button
            try:
                self.window[f'Erforsche {name}'].update(visible=is_visible)
                if self.game.is_researched(name):
                    self.window[f'Erforsche {name}'].update(button_color=('black', 'green'))
            except:
                pass
            
            # Update build button
            try:
                self.window[f'baue_{name}'].update(visible=self.game.is_researched(name))
            except:
                pass
    
    def run(self) -> None:
        """Main game loop."""
        logger.info('Starting game loop...')
        
        # Initial UI refresh
        self.ui.refresh_all()
        self._update_research_button_visibility()
        
        while self.running:
            # Read window events
            event, values = self.window.read(timeout=100)
            current_time = time.time()
            
            # Handle window close
            if event in (sg.WINDOW_CLOSED, 'Exit'):
                self.running = False
                continue
            
            # Process tick if interval passed
            if current_time - self.last_tick >= config.TICK_INTERVAL:
                self.tick()
                self.last_tick = current_time
            
            # Dispatch event
            if event and event != '__TIMEOUT__':
                dispatched = self.dispatcher.dispatch_window_event(event, values)
                
                if not dispatched.handled:
                    # Handle events not covered by dispatcher
                    logger.debug(f'Unhandled event: {event}')
        
        # Cleanup
        self.shutdown()
    
    def shutdown(self) -> None:
        """Clean up and save before exit."""
        logger.info('Shutting down...')
        self.game.save(config.SAVEFILE)
        self.window.close()
        logger.info('Game saved and window closed.')


def main():
    """Entry point."""
    game = SpaceGame()
    game.run()


if __name__ == '__main__':
    main()
