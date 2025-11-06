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
    current_research: Optional[str] = None
    research_points: float = 0.0

    # Zasoby
    total_production: float = 0.0
    total_science: float = 0.0

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

    def research_technology(self, tech_name: str):
        """Rozpocznij badanie technologii"""
        self.current_research = tech_name

    def complete_research(self):
        """Zakończ badanie obecnej technologii"""
        if self.current_research:
            self.researched_technologies.add(self.current_research)
            self.current_research = None

    def has_technology(self, tech_name: str) -> bool:
        """Czy imperium posiada technologię"""
        return tech_name in self.researched_technologies

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
