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
WINDOW_READ_TIMEOUT = 100  # milliseconds between window reads

# =============================================================================
# GAME TIMING
# =============================================================================

TICK_INTERVAL = 2  # seconds between game ticks
TICK_MULTIPLIER = 1  # For research/build duration calculation (dauer / TICK)

# =============================================================================
# STARTING RESOURCES
# =============================================================================

START_CREDITS = 10  # Initial credits (note: GAMESTATE uses 10, not 500)
START_ASTRONAUTS = 10  # Initial astronauts on Earth
START_WORKERS = 10  # Initial workers on Earth
START_ROHEISEN = 10  # Initial raw iron
START_STAUB = 5  # Initial dust
START_WASSER = 10  # Initial water

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

# =============================================================================
# SPACESHIP CAPACITIES (fallback if not in SCIENCE)
# =============================================================================

DEFAULT_ASTRONAUT_CAPACITY = 2
DEFAULT_CARGO_CAPACITY = 3
DEFAULT_RANGE = 1

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
IMAGE_SUBSAMPLE = 8  # For scaling images

# =============================================================================
# UI SETTINGS
# =============================================================================

LOG_MAX_ENTRIES = 100  # Maximum log entries to display
AUTOSAVE_INTERVAL = 150  # Ticks between automatic saves (~5 minutes)
PROGRESS_BAR_SIZE = (20, 20)  # Default progress bar dimensions

# =============================================================================
# EARTH JOBS TIMING
# =============================================================================

DEFAULT_JOB_DURATION = 2  # Default job duration in ticks
DEFAULT_WORKERS_REQUIRED = 1  # Default workers per job

# =============================================================================
# DEPRECATED (kept for backward compatibility)
# =============================================================================

TICK = TICK_MULTIPLIER  # Old name, use TICK_MULTIPLIER instead
WINDOW_READ = WINDOW_READ_TIMEOUT * 20  # Old name, use WINDOW_READ_TIMEOUT
