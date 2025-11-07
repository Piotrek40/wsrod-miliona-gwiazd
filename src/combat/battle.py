"""
System bitew między flotami
"""
from dataclasses import dataclass, field
from typing import Optional
import random
import math
from src.models.ship import Ship


@dataclass
class BattleResult:
    """Wynik bitwy"""
    attacker_empire_id: int
    defender_empire_id: int
    attacker_won: bool
    attacker_ships_destroyed: int
    defender_ships_destroyed: int
    attacker_survivors: list[Ship]
    defender_survivors: list[Ship]
    rounds: int

    @property
    def total_ships_destroyed(self) -> int:
        return self.attacker_ships_destroyed + self.defender_ships_destroyed


class Battle:
    """
    Pojedyncza bitwa między dwiema flotami
    """

    COMBAT_RANGE = 100.0  # Zasięg inicjowania bitwy
    MAX_ROUNDS = 50  # Maksymalna liczba rund (zapobieganie infinite loop)

    def __init__(self, attacker_ships: list[Ship], defender_ships: list[Ship],
                 location_x: float, location_y: float):
        """
        Inicjalizuj bitwę

        Args:
            attacker_ships: Lista statków atakujących
            defender_ships: Lista statków obrońców
            location_x, location_y: Pozycja bitwy
        """
        self.attacker_ships = [s for s in attacker_ships if s.is_alive]
        self.defender_ships = [s for s in defender_ships if s.is_alive]
        self.location_x = location_x
        self.location_y = location_y
        self.round = 0
        self.is_over = False
        self.result: Optional[BattleResult] = None

        # Statystyki początkowe
        self.initial_attacker_count = len(self.attacker_ships)
        self.initial_defender_count = len(self.defender_ships)

        if self.attacker_ships and self.defender_ships:
            self.attacker_empire_id = self.attacker_ships[0].owner_id
            self.defender_empire_id = self.defender_ships[0].owner_id
        else:
            self.attacker_empire_id = -1
            self.defender_empire_id = -1

    @property
    def attacker_survivors(self) -> list[Ship]:
        """Żywi atakujący"""
        return [s for s in self.attacker_ships if s.is_alive]

    @property
    def defender_survivors(self) -> list[Ship]:
        """Żywi obrońcy"""
        return [s for s in self.defender_ships if s.is_alive]

    def can_continue(self) -> bool:
        """Czy bitwa może się toczyć dalej"""
        if self.is_over:
            return False
        if self.round >= self.MAX_ROUNDS:
            return False
        if not self.attacker_survivors:
            return False
        if not self.defender_survivors:
            return False
        return True

    def execute_round(self):
        """Wykonaj jedną rundę walki"""
        if not self.can_continue():
            self.finish_battle()
            return

        self.round += 1

        # Faza 1: Atakujący strzelają
        self._execute_attacks(self.attacker_survivors, self.defender_survivors)

        # Sprawdź czy obrońcy przetrwali
        if not self.defender_survivors:
            self.finish_battle()
            return

        # Faza 2: Obrońcy odpowiadają
        self._execute_attacks(self.defender_survivors, self.attacker_survivors)

        # Sprawdź czy atakujący przetrwali
        if not self.attacker_survivors:
            self.finish_battle()
            return

        # Sprawdź limit rund
        if self.round >= self.MAX_ROUNDS:
            self.finish_battle()

    def _execute_attacks(self, attackers: list[Ship], targets: list[Ship]):
        """
        Wykonaj serię ataków

        Args:
            attackers: Statki atakujące
            targets: Statki będące celami
        """
        for attacker in attackers:
            if not attacker.is_alive:
                continue

            if not targets:
                break

            # Wybierz losowy cel spośród żywych
            alive_targets = [t for t in targets if t.is_alive]
            if not alive_targets:
                break

            target = random.choice(alive_targets)

            # Oblicz obrażenia
            damage = self._calculate_damage(attacker, target)

            # Zadaj obrażenia
            target.take_damage(damage)

    def _calculate_damage(self, attacker: Ship, defender: Ship) -> float:
        """
        Oblicz obrażenia z uwzględnieniem ataku, obrony i RNG

        Args:
            attacker: Statek atakujący
            defender: Statek broniący się

        Returns:
            float: Wartość obrażeń
        """
        # Bazowe obrażenia = atak atakującego
        base_damage = attacker.attack

        # Redukcja przez obronę (max 80% redukcji)
        defense_reduction = min(0.8, defender.defense / (defender.defense + 50))

        # Obrażenia po obronie
        damage_after_defense = base_damage * (1 - defense_reduction)

        # RNG factor (80% - 120%)
        rng_factor = random.uniform(0.8, 1.2)

        final_damage = damage_after_defense * rng_factor

        return max(1.0, final_damage)  # Minimum 1 obrażenie

    def finish_battle(self):
        """Zakończ bitwę i oblicz wynik"""
        self.is_over = True

        attacker_won = len(self.attacker_survivors) > len(self.defender_survivors)

        attacker_destroyed = self.initial_attacker_count - len(self.attacker_survivors)
        defender_destroyed = self.initial_defender_count - len(self.defender_survivors)

        self.result = BattleResult(
            attacker_empire_id=self.attacker_empire_id,
            defender_empire_id=self.defender_empire_id,
            attacker_won=attacker_won,
            attacker_ships_destroyed=attacker_destroyed,
            defender_ships_destroyed=defender_destroyed,
            attacker_survivors=self.attacker_survivors,
            defender_survivors=self.defender_survivors,
            rounds=self.round
        )

    def execute_full_battle(self) -> BattleResult:
        """
        Wykonaj całą bitwę do końca (auto-resolve)

        Returns:
            BattleResult: Wynik bitwy
        """
        while self.can_continue():
            self.execute_round()

        if not self.is_over:
            self.finish_battle()

        return self.result

    @staticmethod
    def detect_battles(all_ships: list[Ship], empires_relations: dict[tuple[int, int], str]) -> list['Battle']:
        """
        Wykryj wszystkie potencjalne bitwy na mapie

        Args:
            all_ships: Lista wszystkich statków w grze
            empires_relations: Słownik relacji między imperiami {(emp1_id, emp2_id): "war"/"peace"/"neutral"}

        Returns:
            list[Battle]: Lista bitew do rozegrania
        """
        battles = []

        # Grupuj statki według pozycji (zaokrąglone do 50 jednostek)
        from collections import defaultdict
        ship_groups = defaultdict(list)

        for ship in all_ships:
            if not ship.is_alive:
                continue

            # Zaokrąglij pozycję do siatki 50x50
            grid_x = round(ship.x / 50) * 50
            grid_y = round(ship.y / 50) * 50
            ship_groups[(grid_x, grid_y)].append(ship)

        # Sprawdź każdą grupę pod kątem wrogich statków
        for location, ships_at_location in ship_groups.items():
            if len(ships_at_location) < 2:
                continue

            # Pogrupuj według właściciela
            empire_groups = defaultdict(list)
            for ship in ships_at_location:
                empire_groups[ship.owner_id].append(ship)

            # Sprawdź wszystkie pary imperiów
            empire_ids = list(empire_groups.keys())
            for i in range(len(empire_ids)):
                for j in range(i + 1, len(empire_ids)):
                    emp1 = empire_ids[i]
                    emp2 = empire_ids[j]

                    # Sprawdź czy są w stanie wojny
                    relation_key = (min(emp1, emp2), max(emp1, emp2))
                    relation = empires_relations.get(relation_key, "neutral")

                    if relation == "war":
                        # Stwórz bitwę
                        battle = Battle(
                            attacker_ships=empire_groups[emp1],
                            defender_ships=empire_groups[emp2],
                            location_x=location[0],
                            location_y=location[1]
                        )
                        battles.append(battle)

        return battles

    @staticmethod
    def are_ships_in_combat_range(ship1: Ship, ship2: Ship) -> bool:
        """
        Sprawdź czy dwa statki są w zasięgu walki

        Args:
            ship1: Pierwszy statek
            ship2: Drugi statek

        Returns:
            bool: True jeśli w zasięgu
        """
        distance = math.sqrt((ship1.x - ship2.x)**2 + (ship1.y - ship2.y)**2)
        return distance <= Battle.COMBAT_RANGE
