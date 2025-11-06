"""
Model planety
"""
from dataclasses import dataclass, field
from typing import Optional
from src.config import PlanetType, Colors, ShipType, SHIP_COST
import random


@dataclass
class Building:
    """Budynek na planecie"""
    name: str
    production_bonus: float = 0.0
    science_bonus: float = 0.0
    defense_bonus: float = 0.0


@dataclass
class ProductionItem:
    """Element kolejki produkcji"""
    item_type: str  # "ship" lub "building"
    ship_type: Optional[ShipType] = None
    building_name: Optional[str] = None
    total_cost: float = 0.0
    accumulated_production: float = 0.0

    @property
    def is_complete(self) -> bool:
        """Czy produkcja jest zakończona"""
        return self.accumulated_production >= self.total_cost

    @property
    def progress_percent(self) -> float:
        """Procent ukończenia"""
        if self.total_cost == 0:
            return 100.0
        return (self.accumulated_production / self.total_cost) * 100.0


@dataclass
class Planet:
    """
    Planeta w systemie gwiezdnym
    """
    name: str
    planet_type: PlanetType
    size: int  # 1-10, określa maksymalną populację
    mineral_richness: float  # 0.5-2.0, mnożnik produkcji
    x: float  # Pozycja względem gwiazdy (orbit)
    y: float

    # Właściciel
    owner_id: Optional[int] = None  # ID imperium (None = niezakolonizowana)

    # Populacja i zasoby
    population: float = 0.0
    max_population: float = field(init=False)

    # Budynki
    buildings: list[Building] = field(default_factory=list)

    # Produkcja
    production_queue: list = field(default_factory=list)

    def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        self.max_population = self.size * 10.0  # Rozmiar 5 = max 50 populacji

    @property
    def color(self) -> tuple:
        """Kolor planety według typu"""
        color_map = {
            PlanetType.EARTH_LIKE: Colors.PLANET_EARTH,
            PlanetType.DESERT: Colors.PLANET_DESERT,
            PlanetType.OCEAN: Colors.PLANET_OCEAN,
            PlanetType.ICE: Colors.PLANET_ICE,
            PlanetType.ROCK: Colors.PLANET_ROCK,
            PlanetType.GAS_GIANT: Colors.PLANET_GAS,
        }
        return color_map.get(self.planet_type, Colors.WHITE)

    @property
    def is_colonized(self) -> bool:
        """Czy planeta jest skolonizowana"""
        return self.owner_id is not None

    def colonize(self, empire_id: int, initial_population: float = 10.0):
        """Kolonizuj planetę"""
        self.owner_id = empire_id
        self.population = initial_population

    def calculate_production(self) -> float:
        """Oblicz produkcję planety na turę"""
        if not self.is_colonized:
            return 0.0

        base_production = self.population * self.mineral_richness

        # Bonusy z budynków
        building_bonus = sum(b.production_bonus for b in self.buildings)

        return base_production * (1.0 + building_bonus)

    def calculate_science(self) -> float:
        """Oblicz punkty nauki na turę"""
        if not self.is_colonized:
            return 0.0

        base_science = self.population * 0.5

        # Bonusy z budynków
        building_bonus = sum(b.science_bonus for b in self.buildings)

        return base_science * (1.0 + building_bonus)

    def grow_population(self, growth_rate: float = 0.05):
        """Wzrost populacji"""
        if not self.is_colonized:
            return

        if self.population < self.max_population:
            growth = self.population * growth_rate
            self.population = min(self.population + growth, self.max_population)

    def add_ship_to_queue(self, ship_type: ShipType):
        """Dodaj statek do kolejki produkcji"""
        cost = SHIP_COST.get(ship_type, 100)
        item = ProductionItem(
            item_type="ship",
            ship_type=ship_type,
            total_cost=cost
        )
        self.production_queue.append(item)

    def process_production(self) -> Optional[ProductionItem]:
        """Przetwórz produkcję na turę. Zwraca ukończony element jeśli jest."""
        if not self.production_queue or not self.is_colonized:
            return None

        # Pobierz pierwszy element z kolejki
        current_item = self.production_queue[0]

        # Dodaj produkcję z tej tury
        production_this_turn = self.calculate_production()
        current_item.accumulated_production += production_this_turn

        # Sprawdź czy ukończono
        if current_item.is_complete:
            self.production_queue.pop(0)
            return current_item

        return None

    @staticmethod
    def generate_random(name: str, orbit_x: float, orbit_y: float) -> 'Planet':
        """Generuj losową planetę"""
        planet_type = random.choice(list(PlanetType))
        size = random.randint(3, 10)
        mineral_richness = random.uniform(0.5, 2.0)

        return Planet(
            name=name,
            planet_type=planet_type,
            size=size,
            mineral_richness=mineral_richness,
            x=orbit_x,
            y=orbit_y
        )
