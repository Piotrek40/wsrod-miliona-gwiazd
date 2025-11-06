"""
Model galaktyki i systemów gwiezdnych
"""
from dataclasses import dataclass, field
from typing import Optional
import random
import math

from src.config import (
    StarType, Colors, GALAXY_WIDTH, GALAXY_HEIGHT,
    NUM_STAR_SYSTEMS, MIN_SYSTEM_DISTANCE,
    MIN_PLANETS_PER_SYSTEM, MAX_PLANETS_PER_SYSTEM,
    STAR_SIZE_MIN, STAR_SIZE_MAX,
    PLANET_ORBIT_RADIUS_MIN, PLANET_ORBIT_RADIUS_MAX
)
from src.models.planet import Planet


@dataclass
class StarSystem:
    """
    System gwiezdny z gwiazdą i planetami
    """
    id: int
    name: str
    x: float
    y: float
    star_type: StarType
    star_size: int
    planets: list[Planet] = field(default_factory=list)

    # Eksploracja
    explored_by: set[int] = field(default_factory=set)  # IDs imperiów które odkryły system

    @property
    def color(self) -> tuple:
        """Kolor gwiazdy według typu"""
        color_map = {
            StarType.YELLOW: Colors.STAR_YELLOW,
            StarType.WHITE: Colors.STAR_WHITE,
            StarType.RED: Colors.STAR_RED,
            StarType.BLUE: Colors.STAR_BLUE,
        }
        return color_map.get(self.star_type, Colors.WHITE)

    def is_explored_by(self, empire_id: int) -> bool:
        """Czy system jest odkryty przez imperium"""
        return empire_id in self.explored_by

    def explore(self, empire_id: int):
        """Odkryj system dla imperium"""
        self.explored_by.add(empire_id)

    def get_colonized_planets(self, empire_id: Optional[int] = None) -> list[Planet]:
        """Zwróć skolonizowane planety (opcjonalnie filtrowane po właścicielu)"""
        colonized = [p for p in self.planets if p.is_colonized]
        if empire_id is not None:
            colonized = [p for p in colonized if p.owner_id == empire_id]
        return colonized

    def get_free_planets(self) -> list[Planet]:
        """Zwróć nieskolonizowane planety"""
        return [p for p in self.planets if not p.is_colonized]

    def get_colonizable_planets(self, colonizable_types: list) -> list[Planet]:
        """Zwróć nieskolonizowane planety które można kolonizować (filtrowane po typie)"""
        return [
            p for p in self.planets
            if not p.is_colonized and p.planet_type in colonizable_types
        ]

    @staticmethod
    def generate_random(system_id: int, x: float, y: float) -> 'StarSystem':
        """Generuj losowy system gwiezdny"""
        # Wybierz typ gwiazdy
        star_type = random.choice(list(StarType))
        star_size = random.randint(STAR_SIZE_MIN, STAR_SIZE_MAX)

        # Generuj nazwę
        prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
        suffixes = ["Centauri", "Orionis", "Draconis", "Phoenicis", "Cassiopeiae", "Andromedae"]
        name = f"{random.choice(prefixes)} {random.choice(suffixes)} {system_id}"

        system = StarSystem(
            id=system_id,
            name=name,
            x=x,
            y=y,
            star_type=star_type,
            star_size=star_size
        )

        # Generuj planety
        num_planets = random.randint(MIN_PLANETS_PER_SYSTEM, MAX_PLANETS_PER_SYSTEM)
        for i in range(num_planets):
            # Pozycja planety na orbicie (wokół gwiazdy)
            angle = (i / num_planets) * 2 * math.pi
            radius = random.uniform(PLANET_ORBIT_RADIUS_MIN, PLANET_ORBIT_RADIUS_MAX)
            planet_x = math.cos(angle) * radius
            planet_y = math.sin(angle) * radius

            planet_name = f"{system.name} {chr(65 + i)}"  # A, B, C, ...
            planet = Planet.generate_random(planet_name, planet_x, planet_y)
            system.planets.append(planet)

        return system


@dataclass
class Galaxy:
    """
    Galaktyka - zbiór systemów gwiezdnych
    """
    width: float
    height: float
    systems: list[StarSystem] = field(default_factory=list)

    def get_system_at(self, x: float, y: float, tolerance: float = 20.0) -> Optional[StarSystem]:
        """Znajdź system w danej pozycji (z tolerancją kliknięcia)"""
        for system in self.systems:
            distance = math.sqrt((system.x - x)**2 + (system.y - y)**2)
            if distance <= tolerance:
                return system
        return None

    def get_systems_in_range(self, x: float, y: float, range_radius: float) -> list[StarSystem]:
        """Zwróć systemy w zasięgu od danego punktu"""
        systems_in_range = []
        for system in self.systems:
            distance = math.sqrt((system.x - x)**2 + (system.y - y)**2)
            if distance <= range_radius:
                systems_in_range.append(system)
        return systems_in_range

    def find_system_by_id(self, system_id: int) -> Optional[StarSystem]:
        """Znajdź system po ID"""
        for system in self.systems:
            if system.id == system_id:
                return system
        return None

    @staticmethod
    def generate() -> 'Galaxy':
        """Generuj galaktykę z losowo rozmieszczonymi systemami"""
        galaxy = Galaxy(width=GALAXY_WIDTH, height=GALAXY_HEIGHT)

        # Generuj systemy z minimalną odległością między sobą
        attempts = 0
        max_attempts = NUM_STAR_SYSTEMS * 100

        while len(galaxy.systems) < NUM_STAR_SYSTEMS and attempts < max_attempts:
            attempts += 1

            # Losowa pozycja
            x = random.uniform(100, GALAXY_WIDTH - 100)
            y = random.uniform(100, GALAXY_HEIGHT - 100)

            # Sprawdź odległość od innych systemów
            too_close = False
            for existing_system in galaxy.systems:
                distance = math.sqrt((existing_system.x - x)**2 + (existing_system.y - y)**2)
                if distance < MIN_SYSTEM_DISTANCE:
                    too_close = True
                    break

            if not too_close:
                system = StarSystem.generate_random(len(galaxy.systems), x, y)
                galaxy.systems.append(system)

        return galaxy
