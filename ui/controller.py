"""
UI Controller for Spacegame.

The UIController manages all UI updates by observing the GameState
and automatically updating the window elements when state changes.

This separates the UI update logic from the game logic.
"""

import logging
from typing import TYPE_CHECKING, Any, Optional, Callable

if TYPE_CHECKING:
    from core.game_state import GameState
    import FreeSimpleGUI as sg

logger = logging.getLogger(__name__)


class UIController:
    """
    Controls UI updates based on GameState changes.
    
    The UIController observes the GameState and automatically updates
    the appropriate window elements when state changes occur.
    
    Usage:
        from core import GameState
        from ui import UIController
        
        game = GameState()
        window = sg.Window(...)
        
        ui = UIController(window, game)
        
        # UI automatically updates when game state changes
        game.credits += 100  # Window updates automatically
    """
    
    def __init__(self, window: Any, game_state: 'GameState'):
        """
        Initialize the UI controller.
        
        Args:
            window: FreeSimpleGUI window instance.
            game_state: The game state to observe.
        """
        self.window = window
        self.game_state = game_state
        self._log_entries: list[str] = []
        
        # Register as observer
        game_state.add_observer(self._on_state_change)
        
        logger.debug('UIController initialized')
    
    def _on_state_change(self, key: str, value: Any) -> None:
        """
        Handle state changes from GameState.
        
        This method is called automatically when GameState properties change.
        
        Args:
            key: The key that changed (e.g., 'credits', 'ticks', 'research_completed').
            value: The new value.
        """
        try:
            if key == 'credits':
                self._update_credits(value)
            elif key == 'ticks':
                self._update_ticks(value)
            elif key == 'research_points':
                self._update_research_points(value)
            elif key == 'research_completed':
                self._on_research_completed(value)
            elif key == 'planet_discovered':
                self._on_planet_discovered(value)
            elif key == 'log':
                self._on_log_entry(value)
            elif key.startswith('inventory_'):
                material = key.replace('inventory_', '')
                self._update_inventory_item(material, value)
            elif key.startswith('spaceships_'):
                self._update_spaceships()
            elif key.startswith('astronauts_'):
                self._update_astronauts()
        except Exception as e:
            logger.error(f'UI update error for {key}: {e}')
    
    # ========== Top Bar Updates ==========
    
    def _update_credits(self, value: int) -> None:
        """Update credits display."""
        self._safe_update('tCredits', value=f'Credits: {value}')
    
    def _update_ticks(self, value: int) -> None:
        """Update ticks/cycle display."""
        self._safe_update('tCycles', value=f'Cycle: {value}')
    
    def _update_research_points(self, value: int) -> None:
        """Update research points display."""
        self._safe_update('tForschungspunkte', value=f'Forschungspunkte: {value}')
    
    # ========== Research Updates ==========
    
    def _on_research_completed(self, name: str) -> None:
        """Handle research completion."""
        # Show checkmark
        self._safe_update(f'img_{name}', visible=True)
        
        # Update research button color
        self._safe_update(
            f'Erforsche {name}',
            button_color=('black', 'green')
        )
        
        # Show build button if available
        self._safe_update(f'baue_{name}', visible=True)
        
        # Hide progress bar
        self._safe_update('progressbar_Forschung', visible=False)
        self._safe_update('stop_research', visible=False)
        self._safe_update('already_researched', visible=True)
        
        logger.debug(f'UI updated for completed research: {name}')
    
    def update_research_progress(self, current: int, maximum: int) -> None:
        """Update research progress bar."""
        self._safe_update(
            'progressbar_Forschung',
            current_count=current,
            max=maximum,
            visible=True
        )
        self._safe_update('stop_research', visible=True)
    
    def show_research_info(self, name: str, description: str, duration: int, 
                           cost: int, can_afford: bool, is_researched: bool) -> None:
        """Display research information panel."""
        self._safe_update('desc_research', value=description, visible=True)
        self._safe_update('desc_dauer', value=f"Forschungsdauer: {duration} Zyklen", visible=True)
        self._safe_update('desc_costs', value=f"Forschungskosten: {cost}", visible=True)
        
        if is_researched:
            self._safe_update('do_research', visible=False)
            self._safe_update('already_researched', visible=True)
            self._safe_update('comment', visible=False)
        elif not can_afford:
            self._safe_update('do_research', visible=False)
            self._safe_update('already_researched', visible=False)
            self._safe_update('comment', value='Forschungspunkte reichen nicht aus', visible=True)
        else:
            self._safe_update('do_research', visible=True)
            self._safe_update('already_researched', visible=False)
            self._safe_update('comment', visible=False)
    
    # ========== Building Updates ==========
    
    def update_build_progress(self, current: int, maximum: int) -> None:
        """Update build progress bar."""
        self._safe_update(
            'progressbar_Bauen',
            current_count=current,
            max=maximum,
            visible=True
        )
        self._safe_update('stop_bauen', visible=True)
    
    def hide_build_progress(self) -> None:
        """Hide build progress bar."""
        self._safe_update('progressbar_Bauen', visible=False)
        self._safe_update('stop_bauen', visible=False)
    
    def show_build_info(self, name: str, description: str, duration: int,
                        materials: dict, can_build: bool, reason: str = '') -> None:
        """Display build information panel."""
        # Description and duration
        self._safe_update('desc_bauen', value=f"{description}\n\nDauer: {duration} Zyklen")
        
        # Materials list
        materials_text = "Benötigte Materialien:\n"
        for material, required in materials.items():
            available = self.game_state.get_inventory(material)
            materials_text += f"• {material}: {required} (verfügbar: {available})\n"
        self._safe_update('desc_materialien', value=materials_text, visible=True)
        
        # Build button
        if can_build:
            self._safe_update('do_bauen', visible=True)
            self._safe_update('bauen_unmöglich', visible=False)
        else:
            self._safe_update('do_bauen', visible=False)
            self._safe_update('bauen_unmöglich', value=reason, visible=bool(reason))
    
    def update_build_queue(self, queue_names: list[str]) -> None:
        """Update build queue display."""
        queue_text = '\n'.join(queue_names) if queue_names else "Keine Aufträge in der Warteschlange."
        self._safe_update('bau_queue_anzeige', value=queue_text)
    
    # ========== Inventory Updates ==========
    
    def _update_inventory_item(self, material: str, amount: int) -> None:
        """Update a single inventory item display."""
        color = 'green' if amount > 0 else 'gray'
        self._safe_update(f'inv_anzahl_{material}', value=str(amount), text_color=color)
    
    def update_inventory(self) -> None:
        """Update all inventory displays."""
        for material, amount in self.game_state.raw.get('Inventar', {}).items():
            self._update_inventory_item(material, amount)
    
    def update_inventory_stats(self, total_value: int, type_count: int) -> None:
        """Update inventory statistics."""
        self._safe_update('inventar_gesamtwert', value=f"{total_value:,} Credits")
        self._safe_update('inventar_anzahl_typen', value=str(type_count))
    
    # ========== Spaceship Updates ==========
    
    def _update_spaceships(self) -> None:
        """Update spaceship displays."""
        self.update_spaceships()
    
    def update_spaceships(self) -> None:
        """Update spaceship displays for all planets."""
        # Earth
        mondlander = self.game_state.get_spaceships('Erde', 'Mondlander')
        rakete = self.game_state.get_spaceships('Erde', 'Rakete')
        self._safe_update('raumschiffe_erde', value=f"Mondlander: {mondlander}, Raketen: {rakete}")
        
        # Moon (if discovered)
        if self.game_state.is_planet_discovered('Mond'):
            mondlander = self.game_state.get_spaceships('Mond', 'Mondlander')
            rakete = self.game_state.get_spaceships('Mond', 'Rakete')
            self._safe_update('raumschiffe_mond', value=f"Mondlander: {mondlander}, Raketen: {rakete}")
        
        # Mars (if discovered)
        if self.game_state.is_planet_discovered('Mars'):
            mondlander = self.game_state.get_spaceships('Mars', 'Mondlander')
            rakete = self.game_state.get_spaceships('Mars', 'Rakete')
            self._safe_update('raumschiffe_mars', value=f"Mondlander: {mondlander}, Raketen: {rakete}")
    
    # ========== Astronaut Updates ==========
    
    def _update_astronauts(self) -> None:
        """Update astronaut displays."""
        self.update_astronauts()
    
    def update_astronauts(self) -> None:
        """Update astronaut displays for all planets."""
        self._safe_update(
            'astronauten_erde',
            value=f"Astronauten auf der Erde: {self.game_state.get_astronauts('Erde')}"
        )
        
        if self.game_state.is_planet_discovered('Mond'):
            self._safe_update(
                'astronauten_mond',
                value=f"Astronauten auf dem Mond: {self.game_state.get_astronauts('Mond')}"
            )
        
        if self.game_state.is_planet_discovered('Mars'):
            self._safe_update(
                'astronauten_mars',
                value=f"Astronauten auf dem Mars: {self.game_state.get_astronauts('Mars')}"
            )
    
    # ========== Planet Discovery ==========
    
    def _on_planet_discovered(self, planet: str) -> None:
        """Handle planet discovery."""
        # Show planet-specific elements
        if planet == 'Mond':
            self._safe_update('astronauten_mond', visible=True)
            # Note: Tab visibility would need window recreation
        elif planet == 'Mars':
            self._safe_update('astronauten_mars', visible=True)
        
        logger.debug(f'UI updated for discovered planet: {planet}')
    
    # ========== Travel Updates ==========
    
    def update_active_travels(self, travel_text: str) -> None:
        """Update active travels display."""
        self._safe_update('aktive_reisen', value=travel_text if travel_text else "Keine aktiven Reisen")
    
    # ========== Mission Updates ==========
    
    def update_active_missions(self, mission_text: str) -> None:
        """Update active missions display."""
        self._safe_update(
            'laufende_missionen_anzeige',
            value=mission_text if mission_text else "Keine laufenden Missionen."
        )
    
    def update_moon_mission_progress(self, current: int, maximum: int) -> None:
        """Update moon mission progress bar."""
        self._safe_update(
            'progressbar_Mondmission',
            current_count=current,
            max=maximum,
            visible=True
        )
        self._safe_update('stop_mondmission', visible=True)
    
    # ========== Earth Jobs Updates ==========
    
    def update_earth_jobs(self, jobs_text: str, free_workers: int, total_workers: int) -> None:
        """Update earth jobs display."""
        self._safe_update(
            'aktive_erde_jobs',
            value=jobs_text if jobs_text else "Keine laufenden Jobs."
        )
        self._safe_update(
            'freie_arbeiter',
            value=f"Freie Arbeiter: {free_workers} / {total_workers}"
        )
    
    def show_earth_job_info(self, description: str, rewards: str) -> None:
        """Display earth job information."""
        self._safe_update('erde_job_beschreibung', value=description)
        self._safe_update('erde_job_belohnung', value=rewards)
    
    # ========== Log Updates ==========
    
    def _on_log_entry(self, entry: str) -> None:
        """Handle new log entry."""
        self._log_entries.append(entry)
        # Show newest first
        log_text = '\n'.join(reversed(self._log_entries))
        self._safe_update('Log', value=log_text)
    
    def add_log(self, message: str) -> None:
        """Add a message to the log."""
        self.game_state.add_log(message)
    
    # ========== Tab Image Updates ==========
    
    def update_tab_image(self, tab_key: str) -> None:
        """Update the main image based on selected tab."""
        image_map = {
            'tab_HQ': 'TAB_HQ',
            'tab_Arbeit': 'TAB_HQ',
            'tab_Forschung': 'TAB_FORSCHUNG',
            'tab_Inventar': 'TAB_INVENTAR',
            'tab_Planeten': 'TAB_PLANETEN',
            'tab_Shop': 'TAB_SHOP',
            'tab_Werkstatt': 'TAB_WERKSTATT',
            'tab_Reisen': 'TAB_REISEN',
            'tab_Mondmissionen': 'TAB_MONDMISSIONEN',
        }
        
        image_name = image_map.get(tab_key, 'TAB_HQ')
        image_path = rf"images\{image_name}.png"
        
        try:
            self.window['img_Spalte3'].update(filename=image_path)
        except Exception as e:
            logger.warning(f"Failed to update tab image for {tab_key}: {e}")
            try:
                self.window['img_Spalte3'].update(filename=r"images\TAB_HQ.png")
            except:
                pass
    
    # ========== Full Refresh ==========
    
    def refresh_all(self) -> None:
        """Refresh all UI elements from current game state."""
        self._update_credits(self.game_state.credits)
        self._update_ticks(self.game_state.ticks)
        self._update_research_points(self.game_state.research_points)
        self.update_inventory()
        self.update_spaceships()
        self.update_astronauts()
    
    # ========== Helper Methods ==========
    
    def _safe_update(self, key: str, **kwargs) -> bool:
        """
        Safely update a window element.
        
        Args:
            key: Element key.
            **kwargs: Update arguments.
            
        Returns:
            True if update succeeded.
        """
        try:
            # Check if key exists using the key_dict to avoid FreeSimpleGUI error messages
            key_dict = getattr(self.window, 'key_dict', None) or getattr(self.window, 'AllKeysDict', {})
            if key not in key_dict:
                return False
            self.window[key].update(**kwargs)
            return True
        except KeyError:
            return False
        except Exception as e:
            logger.error(f"Failed to update {key}: {e}")
            return False
    
    def window_refresh(self) -> None:
        """Force a window refresh."""
        try:
            self.window.refresh()
        except Exception as e:
            logger.error(f"Window refresh failed: {e}")
