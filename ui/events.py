"""
Event Dispatcher for Spacegame.

Provides a centralized event handling system that decouples
UI events from game logic.

Events are string identifiers that can have handlers registered.
When an event is fired, all registered handlers are called.
"""

import logging
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents a fired event with optional data."""
    name: str
    data: dict = field(default_factory=dict)
    handled: bool = False


# Type alias for event handler functions
EventHandler = Callable[[Event], None]


class EventDispatcher:
    """
    Central event dispatcher for UI and game events.
    
    Usage:
        dispatcher = EventDispatcher()
        
        # Register handlers
        dispatcher.register('research_clicked', handle_research)
        dispatcher.register('build_clicked', handle_build)
        
        # Fire events
        dispatcher.fire('research_clicked', {'name': 'Eisenbarren'})
        
        # In main loop
        event, values = window.read()
        dispatcher.dispatch_window_event(event, values)
    """
    
    def __init__(self):
        """Initialize the event dispatcher."""
        self._handlers: dict[str, list[EventHandler]] = {}
        self._prefix_handlers: dict[str, EventHandler] = {}
        logger.debug('EventDispatcher initialized')
    
    def register(self, event_name: str, handler: EventHandler) -> None:
        """
        Register a handler for a specific event.
        
        Args:
            event_name: Name of the event to handle.
            handler: Function to call when event fires.
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug(f'Handler registered for event: {event_name}')
    
    def register_prefix(self, prefix: str, handler: EventHandler) -> None:
        """
        Register a handler for events starting with a prefix.
        
        Useful for dynamic events like 'Erforsche Eisenbarren', 'Erforsche Werkzeug'.
        
        Args:
            prefix: Prefix to match (e.g., 'Erforsche ').
            handler: Function to call when matching event fires.
        """
        self._prefix_handlers[prefix] = handler
        logger.debug(f'Prefix handler registered for: {prefix}')
    
    def unregister(self, event_name: str, handler: EventHandler) -> bool:
        """
        Unregister a handler.
        
        Args:
            event_name: Name of the event.
            handler: Handler to remove.
            
        Returns:
            True if handler was found and removed.
        """
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                return True
            except ValueError:
                pass
        return False
    
    def fire(self, event_name: str, data: Optional[dict] = None) -> Event:
        """
        Fire an event and call all registered handlers.
        
        Args:
            event_name: Name of the event to fire.
            data: Optional data to pass to handlers.
            
        Returns:
            The Event object after all handlers have run.
        """
        event = Event(name=event_name, data=data or {})
        
        # Check exact match handlers
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                try:
                    handler(event)
                    if event.handled:
                        break
                except Exception as e:
                    logger.error(f'Handler error for {event_name}: {e}')
        
        # Check prefix handlers if not yet handled
        if not event.handled:
            for prefix, handler in self._prefix_handlers.items():
                if event_name.startswith(prefix):
                    try:
                        # Add extracted suffix to data
                        event.data['_suffix'] = event_name[len(prefix):]
                        handler(event)
                        if event.handled:
                            break
                    except Exception as e:
                        logger.error(f'Prefix handler error for {prefix}: {e}')
        
        return event
    
    def dispatch_window_event(self, event: str, values: dict) -> Event:
        """
        Dispatch a FreeSimpleGUI window event.
        
        Convenience method that extracts event data from the values dict.
        
        Args:
            event: The event string from window.read().
            values: The values dict from window.read().
            
        Returns:
            The Event object after processing.
        """
        if event is None:
            return Event(name='__NONE__')
        
        return self.fire(event, {'_values': values, **values})
    
    def has_handler(self, event_name: str) -> bool:
        """Check if any handler is registered for an event."""
        if event_name in self._handlers and self._handlers[event_name]:
            return True
        
        for prefix in self._prefix_handlers:
            if event_name.startswith(prefix):
                return True
        
        return False


class GameEventBus:
    """
    Specialized event bus for game events (non-UI).
    
    Used for game logic events like:
    - research_completed
    - build_completed
    - planet_discovered
    - mission_started
    """
    
    # Singleton instance
    _instance: Optional['GameEventBus'] = None
    
    def __new__(cls) -> 'GameEventBus':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
        return cls._instance
    
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Subscribe to a game event."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Unsubscribe from a game event."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish a game event."""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f'Game event handler error for {event_type}: {e}')
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        cls._instance = None
