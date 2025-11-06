"""
Model statku kosmicznego
"""
from dataclasses import dataclass, field
from typing import Optional
from src.config import ShipType, SHIP_SPEED
import math


@dataclass
class Ship:
    """
    Statek kosmiczny
    """
    id: int
    name: str
    ship_type: ShipType
    owner_id: int

    # Pozycja
    x: float
    y: float

    # Cel ruchu
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    target_system_id: Optional[int] = None

    # Parametry
    max_hp: float = 100.0
    current_hp: float = 100.0
    attack: float = 10.0
    defense: float = 5.0
    speed: float = field(init=False)

    # Stan
    is_moving: bool = False

    def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        self.speed = SHIP_SPEED.get(self.ship_type, 2.0)

    @property
    def is_alive(self) -> bool:
        """Czy statek jest żywy"""
        return self.current_hp > 0

    @property
    def hp_percentage(self) -> float:
        """Procent HP"""
        return (self.current_hp / self.max_hp) * 100.0

    def move_to(self, x: float, y: float, system_id: Optional[int] = None):
        """Ustaw cel ruchu"""
        self.target_x = x
        self.target_y = y
        self.target_system_id = system_id
        self.is_moving = True

    def update_movement(self, delta_time: float = 1.0):
        """Zaktualizuj pozycję statku (wywołaj co turę/klatkę)"""
        if not self.is_moving or self.target_x is None or self.target_y is None:
            return

        # Oblicz kierunek
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        # Jeśli jesteśmy blisko celu, zatrzymaj się
        if distance < self.speed * delta_time:
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            self.target_x = None
            self.target_y = None
            return

        # Ruch w kierunku celu
        direction_x = dx / distance
        direction_y = dy / distance

        self.x += direction_x * self.speed * delta_time
        self.y += direction_y * self.speed * delta_time

    def take_damage(self, damage: float):
        """Otrzymaj obrażenia"""
        actual_damage = max(0, damage - self.defense)
        self.current_hp -= actual_damage
        if self.current_hp < 0:
            self.current_hp = 0

    def repair(self, amount: float):
        """Napraw statek"""
        self.current_hp = min(self.current_hp + amount, self.max_hp)

    @staticmethod
    def create_ship(ship_id: int, ship_type: ShipType, owner_id: int, x: float, y: float) -> 'Ship':
        """Stwórz nowy statek"""
        # Różne parametry dla różnych typów statków
        stats = {
            ShipType.SCOUT: {"hp": 50, "attack": 5, "defense": 2},
            ShipType.FIGHTER: {"hp": 80, "attack": 15, "defense": 5},
            ShipType.CRUISER: {"hp": 150, "attack": 25, "defense": 10},
            ShipType.BATTLESHIP: {"hp": 300, "attack": 50, "defense": 20},
            ShipType.COLONY_SHIP: {"hp": 100, "attack": 0, "defense": 5},
            ShipType.TRANSPORT: {"hp": 80, "attack": 5, "defense": 5},
        }

        ship_stats = stats.get(ship_type, {"hp": 100, "attack": 10, "defense": 5})

        ship = Ship(
            id=ship_id,
            name=f"{ship_type.value} #{ship_id}",
            ship_type=ship_type,
            owner_id=owner_id,
            x=x,
            y=y,
            max_hp=ship_stats["hp"],
            current_hp=ship_stats["hp"],
            attack=ship_stats["attack"],
            defense=ship_stats["defense"]
        )

        return ship


@dataclass
class Fleet:
    """
    Flota - grupa statków
    """
    id: int
    name: str
    owner_id: int
    ships: list[Ship] = field(default_factory=list)

    @property
    def x(self) -> float:
        """Pozycja X floty (średnia pozycja statków)"""
        if not self.ships:
            return 0.0
        return sum(s.x for s in self.ships) / len(self.ships)

    @property
    def y(self) -> float:
        """Pozycja Y floty (średnia pozycja statków)"""
        if not self.ships:
            return 0.0
        return sum(s.y for s in self.ships) / len(self.ships)

    @property
    def total_attack(self) -> float:
        """Całkowita siła ataku floty"""
        return sum(s.attack for s in self.ships if s.is_alive)

    @property
    def total_defense(self) -> float:
        """Całkowita obrona floty"""
        return sum(s.defense for s in self.ships if s.is_alive)

    def add_ship(self, ship: Ship):
        """Dodaj statek do floty"""
        self.ships.append(ship)

    def remove_destroyed_ships(self):
        """Usuń zniszczone statki"""
        self.ships = [s for s in self.ships if s.is_alive]

    def move_to(self, x: float, y: float, system_id: Optional[int] = None):
        """Przenieś całą flotę"""
        for ship in self.ships:
            ship.move_to(x, y, system_id)

    def update_movement(self, delta_time: float = 1.0):
        """Zaktualizuj ruch wszystkich statków"""
        for ship in self.ships:
            ship.update_movement(delta_time)
