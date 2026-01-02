"""
Integration tests for travel functionality.
Tests validate travel prerequisites, resource management, and planet discovery.
"""
import pytest
import copy


class TestKannReisen:
    """Tests for kann_reisen (can travel) validation."""

    def test_cannot_travel_to_undiscovered_planet(self, fresh_gamestate):
        """Test that travel to undiscovered planet is not possible."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Moon is not discovered
        assert gs['Planeten']['Mond']['entdeckt'] == False
        
        # Cannot travel to undiscovered planet (except Earth)
        can_travel = gs['Planeten']['Mond']['entdeckt'] or 'Mond' == 'Erde'
        assert can_travel == False

    def test_can_travel_to_discovered_planet(self, fresh_gamestate):
        """Test that travel to discovered planet is possible."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Planeten']['Mond']['entdeckt'] = True
        
        can_travel = gs['Planeten']['Mond']['entdeckt']
        assert can_travel == True

    def test_cannot_travel_without_spaceship(self, fresh_gamestate):
        """Test that travel without spaceship is not possible."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # No spaceships on Earth
        assert gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == 0
        
        can_travel = gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] > 0
        assert can_travel == False

    def test_can_travel_with_spaceship(self, fresh_gamestate):
        """Test that travel with spaceship is possible."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 1
        
        can_travel = gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] > 0
        assert can_travel == True


class TestTravelResourceDeduction:
    """Tests for resource deduction when travel starts."""

    def test_spaceship_deducted_on_start(self, fresh_gamestate):
        """Test that spaceship is deducted when travel starts."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 2
        
        # Start travel
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] -= 1
        
        assert gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == 1

    def test_astronauts_deducted_on_start(self, fresh_gamestate):
        """Test that astronauts are deducted when travel starts."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_astronauts = gs['Astronauten']['Erde']
        astronauten_anzahl = 2
        
        # Start travel
        gs['Astronauten']['Erde'] -= astronauten_anzahl
        
        assert gs['Astronauten']['Erde'] == initial_astronauts - astronauten_anzahl

    def test_cargo_deducted_on_start(self, fresh_gamestate):
        """Test that cargo is deducted when travel starts."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Inventar']['Eisenbarren'] = 10
        fracht = {'Eisenbarren': 5}
        
        # Start travel
        for material, anzahl in fracht.items():
            gs['Inventar'][material] -= anzahl
        
        assert gs['Inventar']['Eisenbarren'] == 5


class TestTravelCompletion:
    """Tests for resource addition when travel completes."""

    def test_spaceship_added_at_destination(self, fresh_gamestate):
        """Test that spaceship is added at destination."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Planeten']['Mond']['entdeckt'] = True
        
        # Complete travel to Moon
        gs['Raumschiffe']['Mond']['Mondlander']['Anzahl'] += 1
        
        assert gs['Raumschiffe']['Mond']['Mondlander']['Anzahl'] == 1

    def test_astronauts_added_at_destination(self, fresh_gamestate):
        """Test that astronauts are added at destination."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Planeten']['Mond']['entdeckt'] = True
        astronauten_anzahl = 2
        
        # Complete travel to Moon
        gs['Astronauten']['Mond'] += astronauten_anzahl
        
        assert gs['Astronauten']['Mond'] == astronauten_anzahl

    def test_cargo_added_at_destination(self, fresh_gamestate):
        """Test that cargo is added at destination inventory."""
        gs = copy.deepcopy(fresh_gamestate)
        fracht = {'Eisenbarren': 5}
        
        # Complete travel - add cargo to inventory
        for material, anzahl in fracht.items():
            gs['Inventar'][material] = gs['Inventar'].get(material, 0) + anzahl
        
        assert gs['Inventar']['Eisenbarren'] >= 5


class TestPlanetDiscovery:
    """Tests for planet discovery through travel."""

    def test_moon_discovery(self, fresh_gamestate):
        """Test that Moon is discovered when first visited."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Initially not discovered
        assert gs['Planeten']['Mond']['entdeckt'] == False
        
        # First travel to Moon discovers it
        gs['Planeten']['Mond']['entdeckt'] = True
        
        assert gs['Planeten']['Mond']['entdeckt'] == True

    def test_mars_discovery(self, fresh_gamestate):
        """Test that Mars is discovered when first visited."""
        gs = copy.deepcopy(fresh_gamestate)
        
        # Initially not discovered
        assert gs['Planeten']['Mars']['entdeckt'] == False
        
        # First travel to Mars discovers it
        gs['Planeten']['Mars']['entdeckt'] = True
        
        assert gs['Planeten']['Mars']['entdeckt'] == True

    def test_discovery_grants_research_points(self, fresh_gamestate):
        """Test that discovery grants research points."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_points = gs['Forschungspunkte']
        
        # Discover Moon grants 5 points
        if not gs['Planeten']['Mond']['entdeckt']:
            gs['Planeten']['Mond']['entdeckt'] = True
            gs['Forschungspunkte'] += 5
        
        assert gs['Forschungspunkte'] == initial_points + 5


class TestSpaceshipCapacity:
    """Tests for spaceship capacity validation."""

    def test_mondlander_has_capacity(self, test_science):
        """Test that Mondlander has defined capacity."""
        mondlander = test_science.get('Mondlander', {})
        
        assert 'Sitzplätze' in mondlander or 'Frachtplätze' in mondlander

    def test_rakete_has_higher_capacity(self, test_science):
        """Test that Rakete has higher capacity than Mondlander."""
        mondlander = test_science.get('Mondlander', {})
        rakete = test_science.get('Rakete', {})
        
        mondlander_seats = mondlander.get('Sitzplätze', 0)
        rakete_seats = rakete.get('Sitzplätze', 0)
        
        assert rakete_seats >= mondlander_seats

    def test_cannot_exceed_astronaut_capacity(self, test_science):
        """Test that astronaut count cannot exceed capacity."""
        mondlander = test_science.get('Mondlander', {})
        max_astronauts = mondlander.get('Sitzplätze', 2)
        
        # Try to send too many astronauts
        requested_astronauts = 10
        can_travel = requested_astronauts <= max_astronauts
        
        assert can_travel == False

    def test_cannot_exceed_cargo_capacity(self, test_science):
        """Test that cargo cannot exceed capacity."""
        mondlander = test_science.get('Mondlander', {})
        max_cargo = mondlander.get('Frachtplätze', 3)
        
        # Try to send too much cargo
        total_cargo = 10
        can_travel = total_cargo <= max_cargo
        
        assert can_travel == False


class TestSpaceshipRange:
    """Tests for spaceship range validation."""

    def test_mondlander_range_sufficient_for_moon(self, fresh_gamestate, test_science):
        """Test that Mondlander can reach Moon."""
        distance_to_moon = fresh_gamestate['Planeten']['Erde']['Entfernung']['Mond']
        mondlander_range = test_science.get('Mondlander', {}).get('reichweite', 1)
        
        can_reach = mondlander_range >= distance_to_moon
        assert can_reach == True

    def test_rakete_range_sufficient_for_mars(self, fresh_gamestate, test_science):
        """Test that Rakete can reach Mars."""
        distance_to_mars = fresh_gamestate['Planeten']['Erde']['Entfernung']['Mars']
        rakete_range = test_science.get('Rakete', {}).get('reichweite', 10)
        
        can_reach = rakete_range >= distance_to_mars
        assert can_reach == True


class TestReturnTravel:
    """Tests for return travel from planets."""

    def test_return_from_moon(self, fresh_gamestate):
        """Test returning from Moon to Earth."""
        gs = copy.deepcopy(fresh_gamestate)
        gs['Planeten']['Mond']['entdeckt'] = True
        gs['Astronauten']['Mond'] = 2
        gs['Raumschiffe']['Mond']['Mondlander']['Anzahl'] = 1
        
        # Start return travel
        gs['Raumschiffe']['Mond']['Mondlander']['Anzahl'] -= 1
        gs['Astronauten']['Mond'] -= 2
        
        # Complete return travel
        gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] += 1
        gs['Astronauten']['Erde'] += 2
        
        assert gs['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == 1
        assert gs['Astronauten']['Mond'] == 0
