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

# Bazowa produkcja surowców na jednostkę populacji
BASE_PRODUCTION_PER_POP = 1.0   # Minerały/Produkcja
BASE_SCIENCE_PER_POP = 0.5      # Nauka
BASE_FOOD_PER_POP = 0.8         # Żywność
BASE_ENERGY_PER_POP = 0.3       # Energia

# Koszty utrzymania
POPULATION_FOOD_UPKEEP = 1.0    # Każda jednostka populacji zjada 1 żywności
POPULATION_ENERGY_UPKEEP = 0.1  # Każda jednostka populacji zużywa 0.1 energii

# Modyfikatory typu planety (mnożniki do bazowej produkcji)
# Format: {PlanetType: {'production': X, 'science': X, 'food': X, 'energy': X}}
PLANET_TYPE_MODIFIERS = {
    PlanetType.EARTH_LIKE: {
        'production': 1.0,   # 100% - standard
        'science': 1.0,      # 100%
        'food': 1.5,         # 150% - żyzna ziemia!
        'energy': 0.8,       # 80%
    },
    PlanetType.OCEAN: {
        'production': 0.7,   # 70% - trudno budować
        'science': 1.3,      # 130% - badania morskie
        'food': 1.4,         # 140% - dużo ryb
        'energy': 1.0,       # 100%
    },
    PlanetType.DESERT: {
        'production': 1.0,   # 100%
        'science': 0.8,      # 80%
        'food': 0.5,         # 50% - trudno uprawiać
        'energy': 1.5,       # 150% - dużo słońca!
    },
    PlanetType.ICE: {
        'production': 0.8,   # 80%
        'science': 1.5,      # 150% - stacje badawcze
        'food': 0.6,         # 60% - szklarnie
        'energy': 0.7,       # 70% - zimno
    },
    PlanetType.ROCK: {
        'production': 1.6,   # 160% - kopalnie!
        'science': 0.7,      # 70%
        'food': 0.0,         # 0% - brak atmosfery
        'energy': 0.8,       # 80%
    },
    PlanetType.GAS_GIANT: {
        'production': 0.0,
        'science': 0.0,
        'food': 0.0,
        'energy': 0.0,
    },
}

# Efekty deficytu zasobów (jak w Stellaris)
DEFICIT_EFFECTS = {
    'food': {
        'threshold': 0,           # Deficyt gdy < 0
        'effect': 'starvation',   # Nazwa efektu
        'penalty_per_turn': 0.05, # 5% populacji umiera co turę przy głodzie
        'description': 'Głód - populacja wymiera',
    },
    'energy': {
        'threshold': 0,
        'effect': 'blackout',
        'penalty_production': 0.5,  # -50% do produkcji
        'penalty_science': 0.5,      # -50% do nauki
        'description': 'Blackout - budynki wyłączone',
    },
}

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
from dataclasses import dataclass
from typing import Optional

@dataclass
class Technology:
    """Definicja technologii"""
    id: str
    name: str
    description: str
    cost: int  # Punkty nauki potrzebne do odkrycia
    category: str
    prerequisites: list[str]  # Lista ID technologii wymaganych
    unlocks_buildings: list[str]  # Lista ID budynków które odblokowuje
    unlocks_ships: list[str]  # Lista typów statków które odblokowuje
    unlocks_planet_types: list[str]  # Lista typów planet do kolonizacji

# Drzewo technologii
TECHNOLOGIES = {
    # === TIER 1 - Początkowe (dostępne od startu) ===

    "basic_farming": Technology(
        id="basic_farming",
        name="Zaawansowane Rolnictwo",
        description="Ulepszone techniki uprawy zwiększają produkcję żywności",
        cost=100,
        category="Biotechnologia",
        prerequisites=[],
        unlocks_buildings=["farm"],
        unlocks_ships=[],
        unlocks_planet_types=[],
    ),

    "basic_industry": Technology(
        id="basic_industry",
        name="Automatyzacja Przemysłowa",
        description="Roboty zwiększają wydajność fabryk",
        cost=100,
        category="Konstrukcja",
        prerequisites=[],
        unlocks_buildings=["factory"],
        unlocks_ships=[],
        unlocks_planet_types=[],
    ),

    "basic_power": Technology(
        id="basic_power",
        name="Fuzja Jądrowa",
        description="Reaktory fuzyjne dostarczają czystej energii",
        cost=100,
        category="Fizyka",
        prerequisites=[],
        unlocks_buildings=["power_plant"],
        unlocks_ships=[],
        unlocks_planet_types=[],
    ),

    "basic_research": Technology(
        id="basic_research",
        name="Laboratoria Badawcze",
        description="Specjalistyczne laboratoria przyspieszają badania",
        cost=100,
        category="Komputery",
        prerequisites=[],
        unlocks_buildings=["research_lab"],
        unlocks_ships=[],
        unlocks_planet_types=[],
    ),

    # === TIER 2 - Średniozaawansowane ===

    "advanced_farming": Technology(
        id="advanced_farming",
        name="Hydroponika",
        description="Uprawy bez gleby - jeszcze więcej żywności",
        cost=250,
        category="Biotechnologia",
        prerequisites=["basic_farming"],
        unlocks_buildings=["hydroponic_farm"],
        unlocks_ships=[],
        unlocks_planet_types=[],
    ),

    "ice_colonization": Technology(
        id="ice_colonization",
        name="Kolonizacja Lodowa",
        description="Kopuły cieplne pozwalają kolonizować lodowe planety",
        cost=300,
        category="Chemia",
        prerequisites=["basic_power"],
        unlocks_buildings=[],
        unlocks_ships=[],
        unlocks_planet_types=["ICE"],
    ),

    "advanced_ships": Technology(
        id="advanced_ships",
        name="Zaawansowane Kadłuby",
        description="Większe statki do walki i eksploracji",
        cost=200,
        category="Konstrukcja",
        prerequisites=["basic_industry"],
        unlocks_buildings=[],
        unlocks_ships=["FIGHTER", "CRUISER"],
        unlocks_planet_types=[],
    ),

    # === TIER 3 - Zaawansowane ===

    "rock_colonization": Technology(
        id="rock_colonization",
        name="Kopuły Skalne",
        description="Hermetyczne kopuły do kolonizacji planet bez atmosfery",
        cost=500,
        category="Konstrukcja",
        prerequisites=["ice_colonization", "basic_industry"],
        unlocks_buildings=[],
        unlocks_ships=[],
        unlocks_planet_types=["ROCK"],
    ),

    "rare_metal_extraction": Technology(
        id="rare_metal_extraction",
        name="Głębokie Wiercenie",
        description="Dostęp do metali rzadkich w skorupie planetarnej",
        cost=400,
        category="Konstrukcja",
        prerequisites=["basic_industry"],
        unlocks_buildings=["mining_complex"],
        unlocks_ships=[],
        unlocks_planet_types=[],
    ),

    "battleships": Technology(
        id="battleships",
        name="Pancerniki Wojenne",
        description="Potężne statki wojenne - kręgosłup floty",
        cost=600,
        category="Konstrukcja",
        prerequisites=["advanced_ships", "rare_metal_extraction"],
        unlocks_buildings=[],
        unlocks_ships=["BATTLESHIP"],
        unlocks_planet_types=[],
    ),
}

# === BUDYNKI ===
@dataclass
class BuildingDefinition:
    """Definicja budynku"""
    id: str
    name: str
    description: str
    cost: int  # Koszt produkcji
    upkeep_energy: float  # Koszt utrzymania w energii/turę
    requires_tech: Optional[str]  # ID wymaganej technologii (None = dostępny od startu)

    # Bonusy (dodawane do produkcji planety)
    production_bonus: float = 0.0
    science_bonus: float = 0.0
    food_bonus: float = 0.0
    energy_bonus: float = 0.0

    # Bonusy płaskie (dodawane bezpośrednio, nie mnożnik)
    production_flat: float = 0.0
    science_flat: float = 0.0
    food_flat: float = 0.0
    energy_flat: float = 0.0

BUILDINGS = {
    # === TIER 1 - Podstawowe budynki ===

    "farm": BuildingDefinition(
        id="farm",
        name="Farma",
        description="Zwiększa produkcję żywności o 50%",
        cost=150,
        upkeep_energy=1.0,
        requires_tech="basic_farming",
        food_bonus=0.5,  # +50% do żywności
    ),

    "factory": BuildingDefinition(
        id="factory",
        name="Fabryka",
        description="Zwiększa produkcję o 40%",
        cost=200,
        upkeep_energy=2.0,
        requires_tech="basic_industry",
        production_bonus=0.4,  # +40% do produkcji
    ),

    "power_plant": BuildingDefinition(
        id="power_plant",
        name="Elektrownia Fuzji",
        description="Dodaje +15 energii",
        cost=180,
        upkeep_energy=0.0,  # Produkuje energię, nie zużywa
        requires_tech="basic_power",
        energy_flat=15.0,  # +15 energii (płaska wartość)
    ),

    "research_lab": BuildingDefinition(
        id="research_lab",
        name="Laboratorium",
        description="Zwiększa produkcję nauki o 60%",
        cost=220,
        upkeep_energy=2.5,
        requires_tech="basic_research",
        science_bonus=0.6,  # +60% do nauki
    ),

    # === TIER 2 - Zaawansowane ===

    "hydroponic_farm": BuildingDefinition(
        id="hydroponic_farm",
        name="Farma Hydroponiczna",
        description="Zwiększa produkcję żywności o 90% + 10 płasko",
        cost=350,
        upkeep_energy=3.0,
        requires_tech="advanced_farming",
        food_bonus=0.9,  # +90%
        food_flat=10.0,  # +10 żywności
    ),

    "mining_complex": BuildingDefinition(
        id="mining_complex",
        name="Kompleks Wydobywczy",
        description="Wydobywa metale rzadkie. +70% produkcji (wymaga złóż na planecie)",
        cost=500,
        upkeep_energy=4.0,
        requires_tech="rare_metal_extraction",
        production_bonus=0.7,  # +70% do produkcji
    ),
}

TECH_CATEGORIES = [
    "Fizyka",
    "Napędy",
    "Konstrukcja",
    "Komputery",
    "Biotechnologia",
    "Chemia"
]
