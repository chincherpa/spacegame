"""
Game Configuration Constants

This module contains all configurable values for the game.
Organized by category for easy reference.
"""

# =============================================================================
# WINDOW SETTINGS
# =============================================================================

TITLE = "Spacegame"
WINDOW_SIZE = (980, 740)
WINDOW_READ_TIMEOUT = 100  # milliseconds between window reads

# =============================================================================
# GAME TIMING
# =============================================================================

TICK_INTERVAL = 2  # seconds between game ticks

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

# Forschungspunkte für Sondenflüge, wenn schon alles entdeckt ist
PROBE_DATA_RESEARCH_POINTS = 15

# =============================================================================
# BONI DURCH MISSIONSBELOHNUNGEN
# =============================================================================

# Jedes Kommunikations_Upgrade liefert zusätzliche Forschungspunkte pro Intervall
# (10 Punkte in 20 Zyklen entsprechen etwa einem Arbeiter in Laborarbeit)
COMM_UPGRADE_SCIENCE_POINTS = 10
# Jedes Mondstation_Modul verkürzt Mond-Expeditionen (nie unter MINING_MIN_DAUER)
MOON_MODULE_MINING_TICKS = 1
MINING_MIN_DAUER = 2
# Astronaut_Erfahrung erhöht den Hauptertrag jeder Expedition (gedeckelt)
EXPERIENCE_MINING_BONUS_MAX = 3

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
