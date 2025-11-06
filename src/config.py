"""
Konfiguracja gry "Wśród Miliona Gwiazd"
"""
from enum import Enum

# === OKNO GRY ===
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Wśród Miliona Gwiazd"

# === KOLORY ===
class Colors:
    """Paleta kolorów gry"""
    # Podstawowe
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    # UI
    DARK_GRAY = (42, 42, 42)
    LIGHT_GRAY = (100, 100, 100)
    UI_BORDER = (74, 158, 255)
    UI_HIGHLIGHT = (100, 180, 255)
    UI_TEXT = (220, 220, 220)

    # Imperia
    PLAYER = (0, 255, 0)  # Zielony
    ENEMY = (255, 0, 0)  # Czerwony
    ALLY = (74, 158, 255)  # Niebieski
    NEUTRAL = (150, 150, 150)  # Szary

    # Gwiazdy (według typu)
    STAR_YELLOW = (255, 255, 100)
    STAR_WHITE = (255, 255, 255)
    STAR_RED = (255, 100, 100)
    STAR_BLUE = (150, 200, 255)

    # Planety (według typu)
    PLANET_EARTH = (100, 200, 100)  # Ziemiopodobna
    PLANET_DESERT = (200, 180, 100)  # Pustynna
    PLANET_OCEAN = (50, 100, 200)  # Oceaniczna
    PLANET_ICE = (200, 230, 255)  # Lodowa
    PLANET_ROCK = (150, 100, 80)  # Skalista
    PLANET_GAS = (255, 200, 150)  # Gazowy olbrzym

    # Mgła wojny
    FOG_OF_WAR = (80, 80, 100)  # Jaśniejszy szaro-niebieski, lepiej widoczny

# === GALAKTYKA ===
GALAXY_WIDTH = 3000  # Szerokość mapy galaktyki w pikselach
GALAXY_HEIGHT = 2000  # Wysokość mapy galaktyki
NUM_STAR_SYSTEMS = 40  # Liczba systemów gwiezdnych
MIN_SYSTEM_DISTANCE = 150  # Minimalna odległość między systemami
BACKGROUND_STARS = 200  # Liczba dekoracyjnych gwiazdek w tle

# === SYSTEMY GWIEZDNE ===
MIN_PLANETS_PER_SYSTEM = 1
MAX_PLANETS_PER_SYSTEM = 5
STAR_SIZE_MIN = 8
STAR_SIZE_MAX = 15

# === PLANETY ===
PLANET_SIZE_MIN = 3
PLANET_SIZE_MAX = 8
PLANET_ORBIT_RADIUS_MIN = 30
PLANET_ORBIT_RADIUS_MAX = 80

class PlanetType(Enum):
    """Typy planet"""
    EARTH_LIKE = "Ziemiopodobna"
    DESERT = "Pustynna"
    OCEAN = "Oceaniczna"
    ICE = "Lodowa"
    ROCK = "Skalista"
    GAS_GIANT = "Gazowy Olbrzym"

class StarType(Enum):
    """Typy gwiazd"""
    YELLOW = "Żółty karzeł"
    WHITE = "Biały karzeł"
    RED = "Czerwony olbrzym"
    BLUE = "Niebieska gwiazda"

# === STATKI ===
class ShipType(Enum):
    """Typy statków"""
    SCOUT = "Zwiadowca"
    FIGHTER = "Myśliwiec"
    CRUISER = "Krążownik"
    BATTLESHIP = "Pancernik"
    COLONY_SHIP = "Statek kolonistów"
    TRANSPORT = "Transportowiec"

SHIP_SPEED = {
    ShipType.SCOUT: 3.0,
    ShipType.FIGHTER: 2.5,
    ShipType.CRUISER: 2.0,
    ShipType.BATTLESHIP: 1.5,
    ShipType.COLONY_SHIP: 1.5,
    ShipType.TRANSPORT: 2.0,
}

SHIP_COST = {
    ShipType.SCOUT: 50,
    ShipType.FIGHTER: 80,
    ShipType.CRUISER: 150,
    ShipType.BATTLESHIP: 300,
    ShipType.COLONY_SHIP: 100,
    ShipType.TRANSPORT: 70,
}

# === KAMERA ===
CAMERA_MOVE_SPEED = 10
CAMERA_ZOOM_MIN = 0.5
CAMERA_ZOOM_MAX = 2.0
CAMERA_ZOOM_STEP = 0.1

# === GRA ===
STARTING_SHIPS = {
    ShipType.SCOUT: 2,
    ShipType.COLONY_SHIP: 1,
}

NUM_AI_EMPIRES = 3  # Liczba imperiów AI

# === UI ===
PANEL_WIDTH = 300
PANEL_PADDING = 10
FONT_SIZE_SMALL = 14
FONT_SIZE_MEDIUM = 18
FONT_SIZE_LARGE = 24
BUTTON_HEIGHT = 40

# === EKONOMIA ===
BASE_POPULATION_GROWTH = 0.1  # 10% wzrostu na turę
BASE_PRODUCTION_PER_POP = 1.0
BASE_SCIENCE_PER_POP = 0.5

# === KOLONIZACJA ===
# Typy planet które można kolonizować na początku gry (bez zaawansowanych technologii)
COLONIZABLE_PLANET_TYPES = [
    PlanetType.EARTH_LIKE,  # Ziemiopodobna - najlepsza
    PlanetType.OCEAN,       # Oceaniczna - dobra
    PlanetType.DESERT,      # Pustynna - słabsza ale możliwa
]

# Typy wymagające zaawansowanych technologii (TODO: dodać system technologii)
ADVANCED_COLONIZATION_TYPES = [
    PlanetType.ICE,         # Lodowa - wymaga technologii środowiskowych
    PlanetType.ROCK,        # Skalista - wymaga zaawansowanych kopuł
]

# Niekolonizowalne (nigdy)
NON_COLONIZABLE_TYPES = [
    PlanetType.GAS_GIANT,   # Gazowy olbrzym - niemożliwe do skolonizowania
]

# === BADANIA ===
TECH_CATEGORIES = [
    "Fizyka",
    "Napędy",
    "Konstrukcja",
    "Komputery",
    "Biotechnologia",
    "Chemia"
]
