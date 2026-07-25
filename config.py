"""
Game Configuration Constants

This module contains all configurable values for the game.
Organized by category for easy reference.
"""

# =============================================================================
# WINDOW SETTINGS
# =============================================================================

TITLE = "Spacegame"
WINDOW_SIZE = (900, 660)
WINDOW_READ_TIMEOUT = 100  # milliseconds window.read() waits for an event

# =============================================================================
# GAME TIMING
# =============================================================================

TICK_INTERVAL = 2  # seconds of wall-clock time between game ticks
TICK_MULTIPLIER = 1  # divisor turning a 'dauer' into ticks (dauer / TICK_MULTIPLIER)

# Starting resources are NOT configured here - the initial game state lives in
# gamestate.py (GAMESTATE), which is what load_gamestate() falls back to.

# =============================================================================
# PASSIVE INCOME (per tick interval)
# =============================================================================

CREDITS_EXTRA = 1  # Credits gained
CREDITS_EXTRA_TICKS = 20  # Every N ticks

SCIENCE_POINTS_EXTRA = 1  # Research points gained
SCIENCE_POINTS_EXTRA_TICKS = 20  # Every N ticks

# =============================================================================
# DISCOVERY REWARDS
# =============================================================================

MOON_DISCOVERY_RESEARCH_POINTS = 5
MARS_DISCOVERY_RESEARCH_POINTS = 10

# Spaceship capacities are read from SCIENCE (Sitzplaetze / Frachtplaetze /
# reichweite). A type missing there falls back to 0, which makes kann_reisen()
# reject the trip - see get_raumschiff_kapazitaet() in main.py.

# =============================================================================
# MATERIAL VALUES (for inventory statistics)
# =============================================================================

MATERIAL_VALUES = {
    'Eisenbarren': 50,
    'Baumaterial': 100,
    'Werkzeug': 200,
    'Roheisen': 20,
    'Staub': 5,
    'Wasser': 10,
    'Treibstoff': 30,
    'Gold': 500,
    'Raumsonde': 1000,
    'Mondlander': 5000,
    'Rakete': 15000,
    'Weltraumstation': 50000,
    'Mondgestein': 100,
    'Seltene_Mineralien': 300,
    'Mondstation_Modul': 400,
    'Mondbasen Bauplan': 800,
    'Lebenserhaltung_Upgrade': 350,
    'Kommunikations_Upgrade': 350,
    'Astronaut_Erfahrung': 50,
}

# =============================================================================
# TRAVEL
# =============================================================================

TRAVEL_EVENTS_ENABLED = True  # Zufallsereignisse während Reisen

# =============================================================================
# FILE PATHS
# =============================================================================

SAVEFILE = "savefile.json"
IMAGE_PATH = "images"

# =============================================================================
# UI SETTINGS
# =============================================================================

LOG_MAX_ENTRIES = 100  # Maximum log entries to display
AUTOSAVE_INTERVAL = 150  # Ticks between automatic saves (~5 minutes)

# Earth job durations and worker counts are defined per job in ERDE_JOBS
# (main.py), not here.
