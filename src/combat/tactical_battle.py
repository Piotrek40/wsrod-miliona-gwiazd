"""
Tactical Combat System - Master of Orion style turn-based tactical battles
"""
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum
import math
import random

from src.models.ship import Ship, ShipType


class CombatAction(Enum):
    """Akcje dostępne w walce"""
    MOVE = "move"
    ATTACK = "attack"
    SPECIAL = "special"
    PASS = "pass"
    RETREAT = "retreat"


@dataclass
class GridPosition:
    """Pozycja na gridzie bojowym"""
    x: int
    y: int

    def distance_to(self, other: 'GridPosition') -> float:
        """Oblicz dystans do innej pozycji (Manhattan distance dla square grid)"""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __eq__(self, other):
        if not isinstance(other, GridPosition):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


@dataclass
class ShipCombatState:
    """Stan statku w walce taktycznej"""
    ship: Ship
    position: GridPosition
    has_moved: bool = False
    has_attacked: bool = False
    movement_points: int = 0  # Pozostałe punkty ruchu w tej turze

    def reset_turn(self):
        """Zresetuj stan na nową turę"""
        self.has_moved = False
        self.has_attacked = False
        # Punkty ruchu bazowane na prędkości statku
        self.movement_points = max(1, int(self.ship.speed))

    @property
    def can_act(self) -> bool:
        """Czy statek może jeszcze działać w tej turze"""
        return not (self.has_moved and self.has_attacked)

    @property
    def weapon_range(self) -> int:
        """Zasięg broni statku (w tile'ach)"""
        # Bazowane na typie statku
        ranges = {
            ShipType.SCOUT: 2,
            ShipType.FIGHTER: 3,
            ShipType.CRUISER: 4,
            ShipType.BATTLESHIP: 5,
            ShipType.COLONY_SHIP: 0,  # Nie ma broni
        }
        return ranges.get(self.ship.ship_type, 3)


class CombatGrid:
    """Siatka pozycji dla walki taktycznej"""

    def __init__(self, width: int = 12, height: int = 8):
        self.width = width
        self.height = height
        self.tile_size = 60  # Piksel na tile dla renderowania

    def is_valid_position(self, pos: GridPosition) -> bool:
        """Sprawdź czy pozycja jest w granicach gridu"""
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def get_neighbors(self, pos: GridPosition, distance: int = 1) -> List[GridPosition]:
        """Pobierz sąsiadujące pozycje w określonym dystansie"""
        neighbors = []
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if dx == 0 and dy == 0:
                    continue
                # Manhattan distance
                if abs(dx) + abs(dy) <= distance:
                    new_pos = GridPosition(pos.x + dx, pos.y + dy)
                    if self.is_valid_position(new_pos):
                        neighbors.append(new_pos)
        return neighbors

    def get_path(self, start: GridPosition, end: GridPosition, occupied: set) -> List[GridPosition]:
        """
        Znajdź ścieżkę od start do end (A* simplified)
        occupied - set pozycji zajętych przez inne statki
        """
        if start == end:
            return [start]

        # Prosty pathfinding - bezpośrednia linia z omijaniem przeszkód
        path = [start]
        current = GridPosition(start.x, start.y)

        while current != end:
            # Oblicz kierunek do celu
            dx = 1 if end.x > current.x else (-1 if end.x < current.x else 0)
            dy = 1 if end.y > current.y else (-1 if end.y < current.y else 0)

            # Próbuj przesunąć się w kierunku celu
            next_pos = GridPosition(current.x + dx, current.y + dy)

            # Jeśli zajęte, spróbuj alternatywnego ruchu
            if next_pos in occupied:
                # Spróbuj tylko X lub tylko Y
                alt1 = GridPosition(current.x + dx, current.y)
                alt2 = GridPosition(current.x, current.y + dy)

                if alt1 not in occupied and self.is_valid_position(alt1):
                    next_pos = alt1
                elif alt2 not in occupied and self.is_valid_position(alt2):
                    next_pos = alt2
                else:
                    # Nie można się ruszyć - przerwij
                    break

            if not self.is_valid_position(next_pos):
                break

            current = next_pos
            path.append(current)

            # Zabezpieczenie przed nieskończoną pętlą
            if len(path) > 100:
                break

        return path

    def positions_in_range(self, center: GridPosition, range_tiles: int) -> List[GridPosition]:
        """Pobierz wszystkie pozycje w zasięgu (dla ataku)"""
        positions = []
        for x in range(max(0, center.x - range_tiles), min(self.width, center.x + range_tiles + 1)):
            for y in range(max(0, center.y - range_tiles), min(self.height, center.y + range_tiles + 1)):
                pos = GridPosition(x, y)
                if pos.distance_to(center) <= range_tiles:
                    positions.append(pos)
        return positions


@dataclass
class TacticalBattleResult:
    """Wynik walki taktycznej"""
    attacker_empire_id: int
    defender_empire_id: int
    attacker_won: bool
    defender_won: bool
    attacker_survivors: List[Ship]
    defender_survivors: List[Ship]
    attacker_ships_destroyed: int
    defender_ships_destroyed: int
    rounds: int
    location: Tuple[float, float]
    player_retreated: bool = False


class TacticalBattle:
    """
    Główna klasa walki taktycznej
    Turn-based tactical combat w stylu Master of Orion
    """

    def __init__(self,
                 attacker_empire_id: int,
                 defender_empire_id: int,
                 attacker_ships: List[Ship],
                 defender_ships: List[Ship],
                 location: Tuple[float, float],
                 player_empire_id: int):

        self.attacker_empire_id = attacker_empire_id
        self.defender_empire_id = defender_empire_id
        self.location = location
        self.player_empire_id = player_empire_id

        # Grid
        self.grid = CombatGrid(width=12, height=8)

        # Stany statków
        self.attacker_states: List[ShipCombatState] = []
        self.defender_states: List[ShipCombatState] = []

        # Inicjalizuj pozycje startowe
        self._initialize_ship_positions(attacker_ships, defender_ships)

        # Kolejka inicjatywy
        self.initiative_queue: List[ShipCombatState] = []
        self._initialize_initiative()

        # Stan bitwy
        self.current_ship_index = 0
        self.round_number = 1
        self.battle_ended = False
        self.max_rounds = 50

        # Auto-resolve dla AI vs AI
        self.is_player_involved = (
            self.attacker_empire_id == player_empire_id or
            self.defender_empire_id == player_empire_id
        )

    def _initialize_ship_positions(self, attacker_ships: List[Ship], defender_ships: List[Ship]):
        """Ustaw początkowe pozycje statków na gridzie"""

        # Atakujący na lewej stronie (x=0-2)
        for i, ship in enumerate(attacker_ships):
            x = i % 3  # 3 kolumny
            y = i // 3  # Rzędy
            if y >= self.grid.height:
                y = self.grid.height - 1

            state = ShipCombatState(
                ship=ship,
                position=GridPosition(x, y)
            )
            state.reset_turn()
            self.attacker_states.append(state)

        # Obrońcy na prawej stronie (x=9-11)
        for i, ship in enumerate(defender_ships):
            x = self.grid.width - 1 - (i % 3)  # 3 kolumny od prawej
            y = i // 3  # Rzędy
            if y >= self.grid.height:
                y = self.grid.height - 1

            state = ShipCombatState(
                ship=ship,
                position=GridPosition(x, y)
            )
            state.reset_turn()
            self.defender_states.append(state)

    def _initialize_initiative(self):
        """Stwórz kolejkę inicjatywy bazując na prędkości statków"""
        all_states = self.attacker_states + self.defender_states
        # Sortuj po prędkości (malejąco) + losowy tie-breaker
        self.initiative_queue = sorted(
            all_states,
            key=lambda s: (s.ship.speed, random.random()),
            reverse=True
        )

    def get_current_ship(self) -> Optional[ShipCombatState]:
        """Pobierz statek który teraz ma turę"""
        if self.battle_ended:
            return None

        # Pomiń martwe statki
        while self.current_ship_index < len(self.initiative_queue):
            state = self.initiative_queue[self.current_ship_index]
            if state.ship.is_alive:
                return state
            self.current_ship_index += 1

        return None

    def next_turn(self):
        """Przejdź do następnej tury"""
        self.current_ship_index += 1

        # Jeśli koniec rundy, zresetuj
        if self.current_ship_index >= len(self.initiative_queue):
            self._end_round()

    def _end_round(self):
        """Zakończ rundę i rozpocznij nową"""
        self.round_number += 1
        self.current_ship_index = 0

        # Zresetuj stany wszystkich statków
        for state in self.initiative_queue:
            if state.ship.is_alive:
                state.reset_turn()

        # Sprawdź warunki końca bitwy
        self._check_battle_end()

    def _check_battle_end(self):
        """Sprawdź czy bitwa się skończyła"""
        attackers_alive = sum(1 for s in self.attacker_states if s.ship.is_alive)
        defenders_alive = sum(1 for s in self.defender_states if s.ship.is_alive)

        if attackers_alive == 0 or defenders_alive == 0:
            self.battle_ended = True
        elif self.round_number > self.max_rounds:
            self.battle_ended = True

    def get_occupied_positions(self) -> set:
        """Pobierz wszystkie zajęte pozycje na gridzie"""
        occupied = set()
        for state in self.attacker_states + self.defender_states:
            if state.ship.is_alive:
                occupied.add(state.position)
        return occupied

    def get_ship_at_position(self, pos: GridPosition) -> Optional[ShipCombatState]:
        """Pobierz statek na danej pozycji"""
        for state in self.attacker_states + self.defender_states:
            if state.ship.is_alive and state.position == pos:
                return state
        return None

    def can_move_to(self, ship_state: ShipCombatState, target_pos: GridPosition) -> bool:
        """Sprawdź czy statek może się ruszyć na daną pozycję"""
        if not self.grid.is_valid_position(target_pos):
            return False

        if ship_state.has_moved:
            return False

        # Sprawdź czy pozycja jest wolna
        occupied = self.get_occupied_positions()
        if target_pos in occupied:
            return False

        # Sprawdź dystans (punkty ruchu)
        distance = ship_state.position.distance_to(target_pos)
        return distance <= ship_state.movement_points

    def move_ship(self, ship_state: ShipCombatState, target_pos: GridPosition) -> bool:
        """Przesuń statek na nową pozycję"""
        if not self.can_move_to(ship_state, target_pos):
            return False

        ship_state.position = target_pos
        ship_state.has_moved = True
        return True

    def get_targets_in_range(self, ship_state: ShipCombatState) -> List[ShipCombatState]:
        """Pobierz cele w zasięgu broni"""
        targets = []
        weapon_range = ship_state.weapon_range

        # Określ wrogie statki
        if ship_state in self.attacker_states:
            enemy_states = self.defender_states
        else:
            enemy_states = self.attacker_states

        # Sprawdź które są w zasięgu
        for enemy in enemy_states:
            if not enemy.ship.is_alive:
                continue

            distance = ship_state.position.distance_to(enemy.position)
            if distance <= weapon_range:
                targets.append(enemy)

        return targets

    def attack(self, attacker_state: ShipCombatState, target_state: ShipCombatState) -> float:
        """
        Wykonaj atak
        Returns: obrażenia zadane
        """
        if attacker_state.has_attacked:
            return 0.0

        # Sprawdź zasięg
        distance = attacker_state.position.distance_to(target_state.position)
        if distance > attacker_state.weapon_range:
            return 0.0

        # Oblicz obrażenia (z istniejącego systemu)
        base_damage = attacker_state.ship.attack

        # Obrona zmniejsza obrażenia (max 80%)
        defense_reduction = min(0.8, target_state.ship.defense / (target_state.ship.defense + 50))
        damage_after_defense = base_damage * (1 - defense_reduction)

        # RNG factor (80% - 120%)
        rng_factor = random.uniform(0.8, 1.2)
        final_damage = max(1.0, damage_after_defense * rng_factor)

        # Zastosuj obrażenia
        target_state.ship.current_hp -= final_damage
        if target_state.ship.current_hp <= 0:
            target_state.ship.current_hp = 0

        # Oznacz że zaatakował
        attacker_state.has_attacked = True

        return final_damage

    def ai_take_turn(self, ship_state: ShipCombatState):
        """AI wykonuje turę za statek"""

        # Znajdź najbliższego wroga
        if ship_state in self.attacker_states:
            enemies = self.defender_states
        else:
            enemies = self.attacker_states

        alive_enemies = [e for e in enemies if e.ship.is_alive]
        if not alive_enemies:
            return

        # Znajdź najbliższego
        nearest = min(alive_enemies, key=lambda e: ship_state.position.distance_to(e.position))

        # Sprawdź czy możemy zaatakować
        targets_in_range = self.get_targets_in_range(ship_state)

        if nearest in targets_in_range and not ship_state.has_attacked:
            # ATAKUJ!
            self.attack(ship_state, nearest)
        elif not ship_state.has_moved:
            # Przesuń się bliżej wroga
            # Znajdź najlepszą pozycję (bliżej wroga, w zasięgu)
            occupied = self.get_occupied_positions()
            possible_moves = self.grid.get_neighbors(ship_state.position, ship_state.movement_points)

            best_move = None
            best_distance = float('inf')

            for move_pos in possible_moves:
                if move_pos not in occupied:
                    dist = move_pos.distance_to(nearest.position)
                    if dist < best_distance:
                        best_distance = dist
                        best_move = move_pos

            if best_move:
                self.move_ship(ship_state, best_move)

                # Spróbuj zaatakować po ruchu
                targets_after_move = self.get_targets_in_range(ship_state)
                if nearest in targets_after_move and not ship_state.has_attacked:
                    self.attack(ship_state, nearest)

    def auto_resolve(self) -> TacticalBattleResult:
        """
        Auto-resolve bitwy (dla AI vs AI)
        Używa prostej symulacji turn-based
        """
        while not self.battle_ended and self.round_number <= self.max_rounds:
            current = self.get_current_ship()
            if not current:
                break

            # AI wykonuje turę
            self.ai_take_turn(current)

            # Następna tura
            self.next_turn()

        # Stwórz wynik
        return self._create_result()

    def _create_result(self) -> TacticalBattleResult:
        """Stwórz obiekt wyniku bitwy"""
        attacker_survivors = [s.ship for s in self.attacker_states if s.ship.is_alive]
        defender_survivors = [s.ship for s in self.defender_states if s.ship.is_alive]

        attacker_destroyed = len(self.attacker_states) - len(attacker_survivors)
        defender_destroyed = len(self.defender_states) - len(defender_survivors)

        attacker_won = len(defender_survivors) == 0 and len(attacker_survivors) > 0
        defender_won = len(attacker_survivors) == 0 and len(defender_survivors) > 0

        return TacticalBattleResult(
            attacker_empire_id=self.attacker_empire_id,
            defender_empire_id=self.defender_empire_id,
            attacker_won=attacker_won,
            defender_won=defender_won,
            attacker_survivors=attacker_survivors,
            defender_survivors=defender_survivors,
            attacker_ships_destroyed=attacker_destroyed,
            defender_ships_destroyed=defender_destroyed,
            rounds=self.round_number,
            location=self.location
        )

    def retreat(self) -> TacticalBattleResult:
        """Gracz wycofuje się z bitwy"""
        result = self._create_result()
        result.player_retreated = True
        self.battle_ended = True
        return result
