"""
Model planety
"""
from dataclasses import dataclass, field
from typing import Optional
from src.config import (
    PlanetType, Colors, ShipType, SHIP_COST,
    BASE_PRODUCTION_PER_POP, BASE_SCIENCE_PER_POP,
    BASE_FOOD_PER_POP, BASE_ENERGY_PER_POP,
    PLANET_TYPE_MODIFIERS
)
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

    # Specjalne zasoby (generowane losowo)
    has_rare_metals: bool = False  # Czy planeta ma złoża metali rzadkich
    has_crystals: bool = False     # Czy planeta ma kryształy (bardzo rzadkie)

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
        """Oblicz produkcję (minerały) planety na turę"""
        if not self.is_colonized:
            return 0.0

        # Bazowa produkcja z populacji
        base_production = self.population * BASE_PRODUCTION_PER_POP * self.mineral_richness

        # Modyfikator typu planety
        planet_modifier = PLANET_TYPE_MODIFIERS.get(self.planet_type, {}).get('production', 1.0)
        base_production *= planet_modifier

        # Bonusy z budynków
        building_bonus = sum(b.production_bonus for b in self.buildings)

        return base_production * (1.0 + building_bonus)

    def calculate_science(self) -> float:
        """Oblicz punkty nauki na turę"""
        if not self.is_colonized:
            return 0.0

        # Bazowa nauka z populacji
        base_science = self.population * BASE_SCIENCE_PER_POP

        # Modyfikator typu planety
        planet_modifier = PLANET_TYPE_MODIFIERS.get(self.planet_type, {}).get('science', 1.0)
        base_science *= planet_modifier

        # Bonusy z budynków
        building_bonus = sum(b.science_bonus for b in self.buildings)

        return base_science * (1.0 + building_bonus)

    def calculate_food(self) -> float:
        """Oblicz produkcję żywności na turę"""
        if not self.is_colonized:
            return 0.0

        # Bazowa produkcja żywności z populacji
        base_food = self.population * BASE_FOOD_PER_POP

        # Modyfikator typu planety (ważny - pustynne/skalne mają mało żywności!)
        planet_modifier = PLANET_TYPE_MODIFIERS.get(self.planet_type, {}).get('food', 1.0)
        base_food *= planet_modifier

        # TODO: Bonusy z budynków (farmy)
        # building_bonus = sum(b.food_bonus for b in self.buildings)

        return base_food

    def calculate_energy(self) -> float:
        """Oblicz produkcję energii na turę"""
        if not self.is_colonized:
            return 0.0

        # Bazowa produkcja energii z populacji
        base_energy = self.population * BASE_ENERGY_PER_POP

        # Modyfikator typu planety (pustynne dają więcej energii słonecznej!)
        planet_modifier = PLANET_TYPE_MODIFIERS.get(self.planet_type, {}).get('energy', 1.0)
        base_energy *= planet_modifier

        # TODO: Bonusy z budynków (elektrownie)
        # building_bonus = sum(b.energy_bonus for b in self.buildings)

        return base_energy

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

        # Generuj specjalne zasoby (rzadkie!)
        has_rare_metals = False
        has_crystals = False

        # Metale rzadkie: 30% szans na skalnych, 10% na innych
        if planet_type == PlanetType.ROCK:
            has_rare_metals = random.random() < 0.3
        elif planet_type in [PlanetType.EARTH_LIKE, PlanetType.DESERT]:
            has_rare_metals = random.random() < 0.1

        # Kryształy: BARDZO rzadkie - 5% na lodowych, 2% na skalnych
        if planet_type == PlanetType.ICE:
            has_crystals = random.random() < 0.05
        elif planet_type == PlanetType.ROCK:
            has_crystals = random.random() < 0.02

        return Planet(
            name=name,
            planet_type=planet_type,
            size=size,
            mineral_richness=mineral_richness,
            x=orbit_x,
            y=orbit_y,
            has_rare_metals=has_rare_metals,
            has_crystals=has_crystals
        )
