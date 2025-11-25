"""
Manager zarządzający bitwami w grze
"""
import math
from typing import Optional
from src.combat.battle import Battle, BattleResult
from src.models.ship import Ship
from src.models.empire import Empire


class CombatManager:
    """
    Zarządza systemem walki w grze
    """

    def __init__(self):
        self.active_battles: list[Battle] = []
        self.battle_history: list[BattleResult] = []
        self.pending_ship_removals: list[Ship] = []  # Statki do usunięcia po turze

    def detect_and_create_battles(self, all_ships: list[Ship], empires: list[Empire]) -> int:
        """
        Wykryj wszystkie potencjalne bitwy i utwórz je

        Args:
            all_ships: Lista wszystkich statków w grze
            empires: Lista wszystkich imperiów

        Returns:
            int: Liczba utworzonych bitew
        """
        # Zbuduj słownik relacji
        relations = {}
        for i, emp1 in enumerate(empires):
            for j, emp2 in enumerate(empires):
                if i != j:
                    relation_key = (min(emp1.id, emp2.id), max(emp1.id, emp2.id))
                    relations[relation_key] = emp1.get_relation(emp2.id)

        # Wykryj bitwy
        new_battles = Battle.detect_battles(all_ships, relations)

        # Dodaj nowe bitwy
        self.active_battles.extend(new_battles)

        return len(new_battles)

    def resolve_all_battles(self) -> list[BattleResult]:
        """
        Rozwiąż wszystkie aktywne bitwy (auto-resolve)

        Returns:
            list[BattleResult]: Lista wyników bitew
        """
        results = []

        for battle in self.active_battles:
            if not battle.is_over:
                result = battle.execute_full_battle()
                results.append(result)
                self.battle_history.append(result)

                # Zaznacz zniszczone statki do usunięcia
                for ship in battle.attacker_ships + battle.defender_ships:
                    if not ship.is_alive:
                        self.pending_ship_removals.append(ship)

        # Wyczyść zakończone bitwy
        self.active_battles = [b for b in self.active_battles if not b.is_over]

        return results

    def remove_destroyed_ships(self, all_ships: list[Ship]) -> int:
        """
        Usuń zniszczone statki z gry

        Args:
            all_ships: Lista wszystkich statków w grze (modyfikowana in-place)

        Returns:
            int: Liczba usuniętych statków
        """
        removed_count = 0

        for ship in self.pending_ship_removals:
            if ship in all_ships:
                all_ships.remove(ship)
                removed_count += 1

        self.pending_ship_removals.clear()

        return removed_count

    def process_combat_turn(self, all_ships: list[Ship], empires: list[Empire]) -> dict:
        """
        Przetworz całą turę walki (główna funkcja wywoływana co turę)

        Args:
            all_ships: Lista wszystkich statków w grze
            empires: Lista wszystkich imperiów

        Returns:
            dict: Statystyki tury {
                'battles_created': int,
                'battles_resolved': int,
                'total_ships_destroyed': int,
                'results': list[BattleResult]
            }
        """
        # Wykryj i utwórz nowe bitwy
        battles_created = self.detect_and_create_battles(all_ships, empires)

        # Rozwiąż wszystkie bitwy
        results = self.resolve_all_battles()

        # Usuń zniszczone statki
        ships_destroyed = self.remove_destroyed_ships(all_ships)

        return {
            'battles_created': battles_created,
            'battles_resolved': len(results),
            'total_ships_destroyed': ships_destroyed,
            'results': results
        }

    def get_battle_at_location(self, x: float, y: float, radius: float = 100) -> Optional[Battle]:
        """
        Znajdź bitwę w danej lokalizacji

        Args:
            x, y: Współrzędne
            radius: Promień wyszukiwania

        Returns:
            Optional[Battle]: Znaleziona bitwa lub None
        """
        for battle in self.active_battles:
            distance = math.sqrt((battle.location_x - x)**2 + (battle.location_y - y)**2)
            if distance <= radius:
                return battle
        return None

    def get_recent_battles(self, count: int = 10) -> list[BattleResult]:
        """
        Pobierz ostatnie bitwy z historii

        Args:
            count: Liczba bitew do pobrania

        Returns:
            list[BattleResult]: Lista ostatnich bitew
        """
        return self.battle_history[-count:] if self.battle_history else []

    def clear_history(self):
        """Wyczyść historię bitew (do oszczędzania pamięci)"""
        self.battle_history.clear()
