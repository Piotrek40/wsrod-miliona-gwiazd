"""
Model planety
"""
from dataclasses import dataclass, field
from typing import Optional
from src.config import PlanetType, Colors
import random


@dataclass
class Building:
    """Budynek na planecie"""
    name: str
    production_bonus: float = 0.0
    science_bonus: float = 0.0
    defense_bonus: float = 0.0


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
