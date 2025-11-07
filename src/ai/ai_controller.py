"""
Kontroler AI dla imperiów komputerowych
"""
import random
from typing import Optional
from src.models.empire import Empire
from src.models.galaxy import Galaxy, StarSystem
from src.models.ship import Ship, ShipType
from src.models.planet import Planet
from src.config import TECHNOLOGIES, BUILDINGS, COLONIZABLE_PLANET_TYPES, PlanetType


class AIController:
    """
    Kontroler AI - zarządza działaniami imperium AI
    """

    def __init__(self, empire: Empire, galaxy: Galaxy):
        self.empire = empire
        self.galaxy = galaxy

        # Parametry zachowania bazując na personality
        self._setup_personality_params()

    def _setup_personality_params(self):
        """Ustaw parametry zachowania na podstawie personality AI"""
        personality = self.empire.ai_personality or "balanced"

        # Priorytety (0.0 - 1.0)
        if personality == "aggressive":
            self.military_priority = 0.8
            self.expansion_priority = 0.6
            self.research_priority = 0.3
            self.scout_count_target = 2
            self.military_ratio = 0.6  # 60% produkcji na wojsko

        elif personality == "peaceful":
            self.military_priority = 0.3
            self.expansion_priority = 0.7
            self.research_priority = 0.8
            self.scout_count_target = 4
            self.military_ratio = 0.2

        elif personality == "scientific":
            self.military_priority = 0.4
            self.expansion_priority = 0.5
            self.research_priority = 0.9
            self.scout_count_target = 3
            self.military_ratio = 0.3

        elif personality == "expansionist":
            self.military_priority = 0.5
            self.expansion_priority = 0.9
            self.research_priority = 0.4
            self.scout_count_target = 5
            self.military_ratio = 0.4

        else:  # balanced
            self.military_priority = 0.5
            self.expansion_priority = 0.6
            self.research_priority = 0.6
            self.scout_count_target = 3
            self.military_ratio = 0.4

    def make_turn_decisions(self, all_ships: list[Ship]):
        """
        Wykonaj decyzje AI na turę

        Args:
            all_ships: Lista wszystkich statków w grze
        """
        # Pobierz statki tego imperium
        my_ships = [s for s in all_ships if s.owner_id == self.empire.id]

        # 1. Eksploracja
        self._handle_exploration(my_ships)

        # 2. Kolonizacja
        self._handle_colonization(my_ships)

        # 3. Badania
        self._handle_research()

        # 4. Produkcja na planetach
        self._handle_production()

    def _handle_exploration(self, my_ships: list[Ship]):
        """
        Zarządzaj eksploracją (wysyłaj scouty do nieodkrytych systemów)

        Args:
            my_ships: Statki tego imperium
        """
        # Policz scouti
        scouts = [s for s in my_ships if s.ship_type == ShipType.SCOUT]
        idle_scouts = [s for s in scouts if not s.is_moving]

        # Znajdź nieodkryte systemy
        unexplored_systems = [
            system for system in self.galaxy.systems
            if not self.empire.has_explored(system.id)
        ]

        if not unexplored_systems:
            return  # Wszystko odkryte

        # Wyślij idle scouty do eksploracji
        for scout in idle_scouts[:len(unexplored_systems)]:
            # Wybierz najbliższy nieodkryty system
            closest_system = min(unexplored_systems, key=lambda s: self._distance(scout.x, scout.y, s.x, s.y))

            # Wyślij scouta
            scout.move_to(closest_system.x, closest_system.y, closest_system.id)
            unexplored_systems.remove(closest_system)

            if not unexplored_systems:
                break

    def _handle_colonization(self, my_ships: list[Ship]):
        """
        Zarządzaj kolonizacją (wysyłaj colony ships do dobrych planet)

        Args:
            my_ships: Statki tego imperium
        """
        # Pobierz colony ships
        colony_ships = [s for s in my_ships if s.ship_type == ShipType.COLONY_SHIP]
        idle_colony_ships = [s for s in colony_ships if not s.is_moving]

        if not idle_colony_ships:
            return

        # Znajdź dobre planety do kolonizacji
        colonizable_types = set(COLONIZABLE_PLANET_TYPES)

        # Dodaj zaawansowane typy jeśli AI ma technologie
        if "ice_colonization" in self.empire.researched_technologies:
            colonizable_types.add(PlanetType.ICE)
        if "rock_colonization" in self.empire.researched_technologies:
            colonizable_types.add(PlanetType.ROCK)

        # Znajdź wolne planety w odkrytych systemach
        good_planets = []
        for system in self.galaxy.systems:
            if self.empire.has_explored(system.id):
                for planet in system.get_colonizable_planets(list(colonizable_types)):
                    # Sprawdź czy nie ma już colony shipa w drodze
                    already_targeted = any(
                        cs.is_moving and cs.target_system_id == system.id
                        for cs in colony_ships
                    )
                    if not already_targeted:
                        good_planets.append((system, planet))

        if not good_planets:
            return

        # Wyślij colony ships do najlepszych planet
        for colony_ship in idle_colony_ships[:len(good_planets)]:
            system, planet = random.choice(good_planets)  # Losowy wybór (można ulepszyć)
            colony_ship.move_to(system.x, system.y, system.id)
            good_planets.remove((system, planet))

            if not good_planets:
                break

    def _handle_research(self):
        """Zarządzaj badaniami technologicznymi"""
        if self.empire.current_research:
            return  # Już coś badamy

        # Znajdź dostępne technologie
        available_techs = []
        for tech_id, tech in TECHNOLOGIES.items():
            if tech_id not in self.empire.researched_technologies:
                # Sprawdź prerequisites
                if all(prereq in self.empire.researched_technologies for prereq in tech.prerequisites):
                    available_techs.append((tech_id, tech))

        if not available_techs:
            return

        # Wybierz technologię bazując na personality
        chosen_tech = self._choose_research(available_techs)
        if chosen_tech:
            self.empire.start_research(chosen_tech)

    def _choose_research(self, available_techs: list[tuple[str, any]]) -> Optional[str]:
        """
        Wybierz technologię do badania bazując na personality

        Args:
            available_techs: Lista (tech_id, tech_def)

        Returns:
            str: Wybrane tech_id lub None
        """
        if not available_techs:
            return None

        personality = self.empire.ai_personality or "balanced"

        # Aggressive - priorytet militarnych tech
        if personality == "aggressive":
            military_techs = [t for t in available_techs if "battleship" in t[0].lower() or "weapon" in t[0].lower()]
            if military_techs:
                return random.choice(military_techs)[0]

        # Scientific - priorytet badań
        elif personality == "scientific":
            science_techs = [t for t in available_techs if t[1].category == "Komputery" or "laboratory" in t[0].lower()]
            if science_techs:
                return random.choice(science_techs)[0]

        # Expansionist - priorytet kolonizacji
        elif personality == "expansionist":
            expansion_techs = [t for t in available_techs if "colonization" in t[0].lower()]
            if expansion_techs:
                return random.choice(expansion_techs)[0]

        # Peaceful/Balanced - wszystkie tech równo
        return random.choice(available_techs)[0]

    def _handle_production(self):
        """Zarządzaj produkcją na planetach"""
        # Pobierz planety AI
        my_planets = []
        for system in self.galaxy.systems:
            for planet in system.planets:
                if planet.is_colonized and planet.owner_id == self.empire.id:
                    my_planets.append((system, planet))

        # Dla każdej planety zdecyduj co budować
        for system, planet in my_planets:
            if len(planet.production_queue) < 3:  # Maksymalnie 3 itemy w kolejce
                self._decide_planet_production(system, planet)

    def _decide_planet_production(self, system: StarSystem, planet: Planet):
        """
        Zdecyduj co budować na planecie

        Args:
            system: System gwiezdny
            planet: Planeta
        """
        # Losuj co budować bazując na priority
        roll = random.random()

        # Najpierw sprawdź czy potrzebujemy podstawowych budynków
        if len(planet.buildings) < 2:
            # Buduj podstawowe budynki (farma, fabryka)
            available_buildings = self._get_available_buildings()
            if available_buildings:
                building_id = random.choice(available_buildings)
                building_cost = BUILDINGS[building_id].cost
                planet.add_building_to_queue(building_id, building_cost)
                return

        # Zdecyduj: budynek vs statek
        if roll < 0.3:  # 30% szans na budynek
            available_buildings = self._get_available_buildings()
            if available_buildings:
                building_id = random.choice(available_buildings)
                building_cost = BUILDINGS[building_id].cost
                planet.add_building_to_queue(building_id, building_cost)
                return

        # Buduj statki
        ship_type = self._choose_ship_to_build()
        planet.add_ship_to_queue(ship_type)

    def _get_available_buildings(self) -> list[str]:
        """Pobierz listę budynków które AI może budować"""
        available = []
        for building_id, building_def in BUILDINGS.items():
            # Sprawdź czy AI ma wymagane tech
            if building_def.requires_tech:
                if building_def.requires_tech not in self.empire.researched_technologies:
                    continue
            available.append(building_id)
        return available

    def _choose_ship_to_build(self) -> ShipType:
        """
        Wybierz typ statku do zbudowania

        Returns:
            ShipType: Typ statku
        """
        personality = self.empire.ai_personality or "balanced"
        roll = random.random()

        # Aggressive - dużo wojska
        if personality == "aggressive":
            if roll < 0.1:
                return ShipType.SCOUT
            elif roll < 0.3:
                return ShipType.COLONY_SHIP
            elif roll < 0.5:
                return ShipType.FIGHTER
            elif roll < 0.8:
                return ShipType.CRUISER
            else:
                # Battleship jeśli ma tech
                if "rare_metal_extraction" in self.empire.researched_technologies:
                    return ShipType.BATTLESHIP
                return ShipType.CRUISER

        # Expansionist - dużo colony ships i scoutów
        elif personality == "expansionist":
            if roll < 0.3:
                return ShipType.SCOUT
            elif roll < 0.6:
                return ShipType.COLONY_SHIP
            elif roll < 0.8:
                return ShipType.FIGHTER
            else:
                return ShipType.CRUISER

        # Scientific/Peaceful - mało wojska, więcej eksploracji
        elif personality in ["scientific", "peaceful"]:
            if roll < 0.3:
                return ShipType.SCOUT
            elif roll < 0.5:
                return ShipType.COLONY_SHIP
            elif roll < 0.75:
                return ShipType.FIGHTER
            else:
                return ShipType.CRUISER

        # Balanced
        else:
            if roll < 0.2:
                return ShipType.SCOUT
            elif roll < 0.4:
                return ShipType.COLONY_SHIP
            elif roll < 0.6:
                return ShipType.FIGHTER
            elif roll < 0.85:
                return ShipType.CRUISER
            else:
                if "rare_metal_extraction" in self.empire.researched_technologies:
                    return ShipType.BATTLESHIP
                return ShipType.CRUISER

    def _distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Oblicz dystans między dwoma punktami"""
        import math
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
