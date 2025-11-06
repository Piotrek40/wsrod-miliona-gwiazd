"""
Model imperium (cywilizacji)
"""
from dataclasses import dataclass, field
from typing import Optional
from src.config import Colors
import random


@dataclass
class Empire:
    """
    Imperium - gracz lub AI
    """
    id: int
    name: str
    color: tuple
    is_player: bool = False

    # Kolonie i statki
    home_system_id: Optional[int] = None
    explored_systems: set[int] = field(default_factory=set)

    # Technologie
    researched_technologies: set[str] = field(default_factory=set)
    current_research: Optional[str] = None  # ID badanej technologii
    research_progress: float = 0.0  # Zgromadzone punkty nauki dla obecnego badania

    # Zasoby (produkcja i zużycie)
    total_production: float = 0.0
    total_science: float = 0.0
    total_food: float = 0.0
    total_energy: float = 0.0

    # Zużycie zasobów
    food_upkeep: float = 0.0     # Ile żywności zużywa populacja
    energy_upkeep: float = 0.0   # Ile energii zużywają budynki/statki

    # Bilans zasobów (produkcja - zużycie)
    food_balance: float = 0.0
    energy_balance: float = 0.0

    # Efekty deficytu
    has_starvation: bool = False    # Czy trwa głód
    has_blackout: bool = False      # Czy jest blackout

    # Dyplomacja
    relations: dict[int, str] = field(default_factory=dict)  # empire_id -> status (war/peace/ally)

    # AI personality (tylko dla AI)
    ai_personality: Optional[str] = None  # aggressive, peaceful, scientific, expansionist

    def explore_system(self, system_id: int):
        """Odkryj system"""
        self.explored_systems.add(system_id)

    def has_explored(self, system_id: int) -> bool:
        """Czy system został odkryty"""
        return system_id in self.explored_systems

    def start_research(self, tech_id: str):
        """Rozpocznij badanie technologii"""
        self.current_research = tech_id
        self.research_progress = 0.0

    def add_research_points(self, points: float) -> bool:
        """
        Dodaj punkty nauki do obecnego badania.
        Zwraca True jeśli technologia została odkryta.
        """
        if not self.current_research:
            return False

        from src.config import TECHNOLOGIES
        tech = TECHNOLOGIES.get(self.current_research)
        if not tech:
            return False

        self.research_progress += points

        # Sprawdź czy badanie zakończone
        if self.research_progress >= tech.cost:
            self.researched_technologies.add(self.current_research)
            self.current_research = None
            self.research_progress = 0.0
            return True

        return False

    def can_research(self, tech_id: str) -> bool:
        """Sprawdź czy można badać daną technologię (prereq spełnione)"""
        from src.config import TECHNOLOGIES
        tech = TECHNOLOGIES.get(tech_id)
        if not tech:
            return False

        # Sprawdź czy już zbadana
        if tech_id in self.researched_technologies:
            return False

        # Sprawdź prereq
        for prereq_id in tech.prerequisites:
            if prereq_id not in self.researched_technologies:
                return False

        return True

    def get_available_technologies(self) -> list[str]:
        """Zwróć listę technologii dostępnych do badania"""
        from src.config import TECHNOLOGIES
        available = []
        for tech_id in TECHNOLOGIES.keys():
            if self.can_research(tech_id):
                available.append(tech_id)
        return available

    def has_technology(self, tech_id: str) -> bool:
        """Czy imperium posiada technologię"""
        return tech_id in self.researched_technologies

    def can_build(self, building_id: str) -> bool:
        """Sprawdź czy można budować dany budynek (technologia zbadana)"""
        from src.config import BUILDINGS
        building_def = BUILDINGS.get(building_id)
        if not building_def:
            return False

        # Jeśli nie wymaga tech, zawsze można
        if building_def.requires_tech is None:
            return True

        # Sprawdź czy tech zbadana
        return self.has_technology(building_def.requires_tech)

    def get_relation(self, other_empire_id: int) -> str:
        """Pobierz status relacji z innym imperium"""
        return self.relations.get(other_empire_id, "neutral")

    def set_relation(self, other_empire_id: int, status: str):
        """Ustaw status relacji z innym imperium"""
        self.relations[other_empire_id] = status

    @staticmethod
    def create_player(name: str = "Ziemia") -> 'Empire':
        """Stwórz imperium gracza"""
        return Empire(
            id=0,
            name=name,
            color=Colors.PLAYER,
            is_player=True
        )

    @staticmethod
    def create_ai(empire_id: int) -> 'Empire':
        """Stwórz imperium AI"""
        # Losowa nazwa
        names = [
            "Imperium Drakonów",
            "Federacja Andromedy",
            "Kolektyw Zetonu",
            "Rada Starszych",
            "Sojusz Alfa",
            "Dominium Omega"
        ]

        # Losowa osobowość AI
        personalities = ["aggressive", "peaceful", "scientific", "expansionist"]

        # Losowy kolor (ale nie zielony - to gracz)
        colors = [
            (255, 100, 100),  # Czerwony
            (100, 100, 255),  # Niebieski
            (255, 255, 100),  # Żółty
            (255, 100, 255),  # Magenta
            (100, 255, 255),  # Cyjan
        ]

        return Empire(
            id=empire_id,
            name=random.choice(names),
            color=random.choice(colors),
            is_player=False,
            ai_personality=random.choice(personalities)
        )
