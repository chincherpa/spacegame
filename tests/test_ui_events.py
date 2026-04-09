"""
Unit tests for the UI event system.
"""
import pytest


class TestEventDispatcher:
    """Tests for EventDispatcher functionality."""

    def test_import_dispatcher(self):
        """Test that EventDispatcher can be imported."""
        from ui.events import EventDispatcher
        assert EventDispatcher is not None

    def test_create_dispatcher(self):
        """Test creating a dispatcher."""
        from ui.events import EventDispatcher
        dispatcher = EventDispatcher()
        assert dispatcher is not None

    def test_register_and_fire(self):
        """Test registering and firing an event."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        received = []
        
        def handler(event):
            received.append(event.name)
        
        dispatcher.register('test_event', handler)
        dispatcher.fire('test_event')
        
        assert received == ['test_event']

    def test_fire_with_data(self):
        """Test firing an event with data."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        received_data = []
        
        def handler(event):
            received_data.append(event.data)
        
        dispatcher.register('test_event', handler)
        dispatcher.fire('test_event', {'key': 'value'})
        
        assert received_data == [{'key': 'value'}]

    def test_multiple_handlers(self):
        """Test multiple handlers for same event."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        count = [0]
        
        def handler1(event):
            count[0] += 1
        
        def handler2(event):
            count[0] += 1
        
        dispatcher.register('test_event', handler1)
        dispatcher.register('test_event', handler2)
        dispatcher.fire('test_event')
        
        assert count[0] == 2

    def test_prefix_handler(self):
        """Test prefix-based event handling."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        received = []
        
        def handler(event):
            received.append(event.data.get('_suffix'))
        
        dispatcher.register_prefix('Erforsche ', handler)
        
        dispatcher.fire('Erforsche Eisenbarren')
        dispatcher.fire('Erforsche Werkzeug')
        dispatcher.fire('Other event')  # Should not match
        
        assert received == ['Eisenbarren', 'Werkzeug']

    def test_unregister_handler(self):
        """Test unregistering a handler."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        received = []
        
        def handler(event):
            received.append(event.name)
        
        dispatcher.register('test_event', handler)
        dispatcher.fire('test_event')
        
        dispatcher.unregister('test_event', handler)
        dispatcher.fire('test_event')
        
        assert len(received) == 1  # Only first fire should be handled

    def test_event_handled_flag(self):
        """Test that handled flag stops further handlers."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        received = []
        
        def handler1(event):
            received.append('handler1')
            event.handled = True
        
        def handler2(event):
            received.append('handler2')
        
        dispatcher.register('test_event', handler1)
        dispatcher.register('test_event', handler2)
        dispatcher.fire('test_event')
        
        assert received == ['handler1']  # handler2 should not run

    def test_has_handler(self):
        """Test checking for handler existence."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        
        def handler(event):
            pass
        
        assert dispatcher.has_handler('test_event') is False
        
        dispatcher.register('test_event', handler)
        assert dispatcher.has_handler('test_event') is True

    def test_dispatch_window_event(self):
        """Test dispatching window events."""
        from ui.events import EventDispatcher
        
        dispatcher = EventDispatcher()
        received = []
        
        def handler(event):
            received.append(event.data.get('_values'))
        
        dispatcher.register('button_click', handler)
        dispatcher.dispatch_window_event('button_click', {'input': 'test'})
        
        assert received[0] == {'input': 'test'}


class TestGameEventBus:
    """Tests for GameEventBus singleton."""

    def test_singleton(self):
        """Test that GameEventBus is a singleton."""
        from ui.events import GameEventBus
        
        GameEventBus.reset()  # Ensure clean state
        
        bus1 = GameEventBus()
        bus2 = GameEventBus()
        
        assert bus1 is bus2

    def test_publish_subscribe(self):
        """Test publish/subscribe pattern."""
        from ui.events import GameEventBus
        
        GameEventBus.reset()
        bus = GameEventBus()
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.subscribe('game_event', handler)
        bus.publish('game_event', 'test_data')
        
        assert received == ['test_data']

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        from ui.events import GameEventBus
        
        GameEventBus.reset()
        bus = GameEventBus()
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.subscribe('game_event', handler)
        bus.publish('game_event', 'first')
        
        bus.unsubscribe('game_event', handler)
        bus.publish('game_event', 'second')
        
        assert received == ['first']


class TestEvent:
    """Tests for Event dataclass."""

    def test_create_event(self):
        """Test creating an Event."""
        from ui.events import Event
        
        event = Event(name='test')
        assert event.name == 'test'
        assert event.data == {}
        assert event.handled is False

    def test_event_with_data(self):
        """Test creating an Event with data."""
        from ui.events import Event
        
        event = Event(name='test', data={'key': 'value'})
        assert event.data == {'key': 'value'}

    def test_event_handled(self):
        """Test setting handled flag."""
        from ui.events import Event
        
        event = Event(name='test')
        event.handled = True
        assert event.handled is True
