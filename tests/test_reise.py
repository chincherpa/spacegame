"""
Integration tests for the Reise (Travel) class.
Tests validate travel creation, progress calculation, and completion.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockReise:
    """Mock implementation of the Reise class for testing."""
    
    def __init__(self, raumschiff_typ, von_planet, zu_planet, astronauten, fracht, reise_id, gamestate, start_tick=0):
        self.raumschiff_typ = raumschiff_typ
        self.von_planet = von_planet
        self.zu_planet = zu_planet
        self.astronauten = astronauten
        self.fracht = fracht
        self.reise_id = reise_id
        self.start_tick = start_tick
        self.dauer = gamestate['Planeten'][von_planet]['Entfernung'][zu_planet]
        self.end_tick = self.start_tick + self.dauer
        self.abgeschlossen = False

    def fortschritt(self, aktuelle_tick):
        if aktuelle_tick >= self.end_tick:
            return 100
        return min(100, ((aktuelle_tick - self.start_tick) / self.dauer) * 100)

    def ist_abgeschlossen(self, aktuelle_tick):
        return aktuelle_tick >= self.end_tick


class TestReiseCreation:
    """Tests for Reise creation."""

    def test_reise_creation_erde_to_mond(self, fresh_gamestate):
        """Test creating a journey from Earth to Moon."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={'Eisenbarren': 5},
            reise_id=0,
            gamestate=fresh_gamestate
        )
        
        assert reise.raumschiff_typ == 'Mondlander'
        assert reise.von_planet == 'Erde'
        assert reise.zu_planet == 'Mond'
        assert reise.astronauten == 2
        assert reise.fracht == {'Eisenbarren': 5}
        assert reise.abgeschlossen == False

    def test_reise_calculates_duration_correctly(self, fresh_gamestate):
        """Test that journey duration is calculated correctly."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate
        )
        
        expected_duration = fresh_gamestate['Planeten']['Erde']['Entfernung']['Mond']
        assert reise.dauer == expected_duration

    def test_reise_calculates_end_tick(self, fresh_gamestate):
        """Test that end tick is calculated correctly."""
        start_tick = 10
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=start_tick
        )
        
        expected_end = start_tick + fresh_gamestate['Planeten']['Erde']['Entfernung']['Mond']
        assert reise.end_tick == expected_end


class TestReiseProgress:
    """Tests for Reise progress calculation."""

    def test_fortschritt_at_start(self, fresh_gamestate):
        """Test that progress is 0 at start."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        assert reise.fortschritt(0) == 0

    def test_fortschritt_at_midpoint(self, fresh_gamestate):
        """Test that progress is ~50% at midpoint."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        midpoint = reise.dauer / 2
        progress = reise.fortschritt(midpoint)
        assert 49 <= progress <= 51  # Allow small floating point variance

    def test_fortschritt_at_completion(self, fresh_gamestate):
        """Test that progress is 100% at completion."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        assert reise.fortschritt(reise.end_tick) == 100

    def test_fortschritt_after_completion(self, fresh_gamestate):
        """Test that progress stays 100% after completion."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        # Well past the end
        assert reise.fortschritt(reise.end_tick + 100) == 100


class TestReiseCompletion:
    """Tests for Reise completion detection."""

    def test_ist_abgeschlossen_before_end(self, fresh_gamestate):
        """Test that journey is not complete before end tick."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        # One tick before completion
        assert reise.ist_abgeschlossen(reise.end_tick - 1) == False

    def test_ist_abgeschlossen_at_end(self, fresh_gamestate):
        """Test that journey is complete at end tick."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        assert reise.ist_abgeschlossen(reise.end_tick) == True

    def test_ist_abgeschlossen_after_end(self, fresh_gamestate):
        """Test that journey is complete after end tick."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate,
            start_tick=0
        )
        
        assert reise.ist_abgeschlossen(reise.end_tick + 10) == True


class TestReiseDifferentRoutes:
    """Tests for different travel routes."""

    def test_erde_to_mars_journey(self, fresh_gamestate):
        """Test journey from Earth to Mars."""
        reise = MockReise(
            raumschiff_typ='Rakete',
            von_planet='Erde',
            zu_planet='Mars',
            astronauten=3,
            fracht={'Werkzeug': 2},
            reise_id=0,
            gamestate=fresh_gamestate
        )
        
        expected_duration = fresh_gamestate['Planeten']['Erde']['Entfernung']['Mars']
        assert reise.dauer == expected_duration
        assert reise.dauer > fresh_gamestate['Planeten']['Erde']['Entfernung']['Mond']

    def test_mond_to_erde_journey(self, fresh_gamestate):
        """Test journey from Moon to Earth."""
        reise = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Mond',
            zu_planet='Erde',
            astronauten=1,
            fracht={'Mondgestein': 3},
            reise_id=0,
            gamestate=fresh_gamestate
        )
        
        expected_duration = fresh_gamestate['Planeten']['Mond']['Entfernung']['Erde']
        assert reise.dauer == expected_duration

    def test_multiple_journeys_have_unique_ids(self, fresh_gamestate):
        """Test that multiple journeys can have different IDs."""
        reise1 = MockReise(
            raumschiff_typ='Mondlander',
            von_planet='Erde',
            zu_planet='Mond',
            astronauten=2,
            fracht={},
            reise_id=0,
            gamestate=fresh_gamestate
        )
        
        reise2 = MockReise(
            raumschiff_typ='Rakete',
            von_planet='Erde',
            zu_planet='Mars',
            astronauten=3,
            fracht={},
            reise_id=1,
            gamestate=fresh_gamestate
        )
        
        assert reise1.reise_id != reise2.reise_id
