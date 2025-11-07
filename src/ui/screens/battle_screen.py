"""
Ekran walki taktycznej - Master of Orion style tactical combat
"""
import pygame
from typing import Optional, List, Tuple
from src.combat.tactical_battle import (
    TacticalBattle, ShipCombatState, GridPosition,
    CombatAction, TacticalBattleResult
)
from src.config import Colors, WINDOW_WIDTH, WINDOW_HEIGHT
from src.ui.widgets import Button, draw_text


class BattleScreen:
    """
    Ekran walki taktycznej z grid-based combat
    """

    def __init__(self, screen: pygame.Surface, tactical_battle: TacticalBattle):
        self.screen = screen
        self.battle = tactical_battle

        # Layout
        self.grid_offset_x = 100
        self.grid_offset_y = 120
        self.tile_size = tactical_battle.grid.tile_size

        # Stan UI
        self.selected_ship: Optional[ShipCombatState] = None
        self.highlighted_positions: List[GridPosition] = []
        self.target_positions: List[GridPosition] = []
        self.mode = "select"  # "select", "move", "attack"

        # Przyciski
        self.retreat_button = Button(
            WINDOW_WIDTH - 200, 20, 180, 40,
            "Wycofaj się",
            callback=self._on_retreat
        )
        self.end_turn_button = Button(
            WINDOW_WIDTH - 200, 70, 180, 40,
            "Zakończ turę",
            callback=self._on_end_turn
        )
        self.pass_button = Button(
            WINDOW_WIDTH - 200, 120, 180, 40,
            "Pomiń",
            callback=self._on_pass
        )

        # Wynik bitwy (gdy się zakończy)
        self.battle_result: Optional[TacticalBattleResult] = None

        # Animacje
        self.attack_animation: Optional[dict] = None
        self.move_animation: Optional[dict] = None

    def render(self):
        """Renderuj ekran walki"""
        # Tło
        self.screen.fill((10, 10, 20))

        # Tytuł
        self._render_header()

        # Grid i statki
        self._render_grid()
        self._render_ships()
        self._render_highlights()

        # Animacje
        if self.attack_animation:
            self._render_attack_animation()

        # UI
        self._render_bottom_panel()

        # Przyciski
        self.retreat_button.draw(self.screen)
        self.end_turn_button.draw(self.screen)
        self.pass_button.draw(self.screen)

        # Jeśli bitwa się skończyła, pokaż wynik
        if self.battle.battle_ended:
            self._render_battle_end()

    def _render_header(self):
        """Renderuj górny pasek z informacjami"""
        # Tło
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 100)
        pygame.draw.rect(self.screen, (20, 20, 30), header_rect)
        pygame.draw.line(self.screen, Colors.WHITE, (0, 100), (WINDOW_WIDTH, 100), 2)

        # Tytuł
        draw_text(
            self.screen,
            "⚔️ WALKA TAKTYCZNA ⚔️",
            WINDOW_WIDTH // 2, 20,
            Colors.WHITE,
            size=32,
            center=True
        )

        # Runda
        draw_text(
            self.screen,
            f"Runda: {self.battle.round_number}",
            20, 20,
            Colors.WHITE,
            size=24
        )

        # Aktualna tura
        current = self.battle.get_current_ship()
        if current:
            turn_text = f"Tura: {current.ship.name or current.ship.ship_type.value}"
            draw_text(
                self.screen,
                turn_text,
                20, 55,
                Colors.YELLOW,
                size=20
            )

        # Liczniki statków
        attacker_alive = sum(1 for s in self.battle.attacker_states if s.ship.is_alive)
        defender_alive = sum(1 for s in self.battle.defender_states if s.ship.is_alive)

        draw_text(
            self.screen,
            f"🔵 Atakujący: {attacker_alive}",
            WINDOW_WIDTH // 2 - 200, 55,
            (100, 150, 255),
            size=20
        )

        draw_text(
            self.screen,
            f"🔴 Obrońcy: {defender_alive}",
            WINDOW_WIDTH // 2 + 50, 55,
            (255, 100, 100),
            size=20
        )

    def _render_grid(self):
        """Renderuj siatkę bojową"""
        for x in range(self.battle.grid.width):
            for y in range(self.battle.grid.height):
                screen_x = self.grid_offset_x + x * self.tile_size
                screen_y = self.grid_offset_y + y * self.tile_size

                # Kolor tile'a (szachownica)
                if (x + y) % 2 == 0:
                    color = (30, 30, 40)
                else:
                    color = (25, 25, 35)

                tile_rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, color, tile_rect)

                # Obramowanie
                pygame.draw.rect(self.screen, (50, 50, 60), tile_rect, 1)

    def _render_highlights(self):
        """Renderuj podświetlenia (możliwe ruchy, cele)"""
        # Możliwe ruchy (zielone)
        for pos in self.highlighted_positions:
            screen_x = self.grid_offset_x + pos.x * self.tile_size
            screen_y = self.grid_offset_y + pos.y * self.tile_size
            tile_rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
            pygame.draw.rect(self.screen, (0, 255, 0), tile_rect, 3)

        # Możliwe cele (czerwone)
        for pos in self.target_positions:
            screen_x = self.grid_offset_x + pos.x * self.tile_size
            screen_y = self.grid_offset_y + pos.y * self.tile_size
            tile_rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
            pygame.draw.rect(self.screen, (255, 50, 50), tile_rect, 3)

    def _render_ships(self):
        """Renderuj statki na gridzie"""
        all_states = self.battle.attacker_states + self.battle.defender_states

        for state in all_states:
            if not state.ship.is_alive:
                continue

            screen_x = self.grid_offset_x + state.position.x * self.tile_size + self.tile_size // 2
            screen_y = self.grid_offset_y + state.position.y * self.tile_size + self.tile_size // 2

            # Kolor bazowany na imperium
            if state in self.battle.attacker_states:
                color = (100, 150, 255)  # Niebieski
            else:
                color = (255, 100, 100)  # Czerwony

            # Ikona statku (okrąg)
            ship_size = 20
            pygame.draw.circle(self.screen, color, (screen_x, screen_y), ship_size)
            pygame.draw.circle(self.screen, Colors.WHITE, (screen_x, screen_y), ship_size, 2)

            # Jeśli wybrany, podświetl
            if self.selected_ship == state:
                pygame.draw.circle(self.screen, Colors.YELLOW, (screen_x, screen_y), ship_size + 5, 3)

            # HP bar
            hp_percent = state.ship.current_hp / state.ship.max_hp
            bar_width = self.tile_size - 10
            bar_height = 5
            bar_x = self.grid_offset_x + state.position.x * self.tile_size + 5
            bar_y = self.grid_offset_y + state.position.y * self.tile_size + self.tile_size - 10

            # Tło HP bar
            pygame.draw.rect(self.screen, (60, 60, 60),
                           (bar_x, bar_y, bar_width, bar_height))

            # HP bar
            hp_color = (0, 255, 0) if hp_percent > 0.5 else ((255, 200, 0) if hp_percent > 0.25 else (255, 0, 0))
            pygame.draw.rect(self.screen, hp_color,
                           (bar_x, bar_y, int(bar_width * hp_percent), bar_height))

    def _render_bottom_panel(self):
        """Renderuj dolny panel z informacjami o statku"""
        panel_y = WINDOW_HEIGHT - 150
        panel_rect = pygame.Rect(0, panel_y, WINDOW_WIDTH, 150)
        pygame.draw.rect(self.screen, (20, 20, 30), panel_rect)
        pygame.draw.line(self.screen, Colors.WHITE, (0, panel_y), (WINDOW_WIDTH, panel_y), 2)

        # Jeśli wybrany statek, pokaż jego info
        ship_to_show = self.selected_ship or self.battle.get_current_ship()

        if ship_to_show:
            ship = ship_to_show.ship
            x_offset = 20
            y_offset = panel_y + 10

            # Nazwa/typ
            name = ship.name if ship.name else ship.ship_type.value
            draw_text(self.screen, name, x_offset, y_offset, Colors.YELLOW, size=24)

            # Stats
            y_offset += 35
            draw_text(self.screen,
                     f"HP: {int(ship.current_hp)}/{int(ship.max_hp)}",
                     x_offset, y_offset, Colors.WHITE, size=18)

            y_offset += 25
            draw_text(self.screen,
                     f"ATK: {int(ship.attack)}  DEF: {int(ship.defense)}  SPD: {ship.speed}",
                     x_offset, y_offset, Colors.WHITE, size=16)

            y_offset += 25
            draw_text(self.screen,
                     f"Zasięg: {ship_to_show.weapon_range} tiles",
                     x_offset, y_offset, Colors.WHITE, size=16)

            # Stan
            y_offset += 25
            status_parts = []
            if ship_to_show.has_moved:
                status_parts.append("Przesunięty")
            if ship_to_show.has_attacked:
                status_parts.append("Zaatakował")
            if not ship_to_show.has_moved and not ship_to_show.has_attacked:
                status_parts.append("Gotowy")

            status_text = "Status: " + ", ".join(status_parts)
            draw_text(self.screen, status_text, x_offset, y_offset, Colors.GRAY, size=14)

        # Instrukcje
        x_offset = WINDOW_WIDTH // 2
        y_offset = panel_y + 20
        draw_text(self.screen, "INSTRUKCJE:", x_offset, y_offset, Colors.WHITE, size=18)

        instructions = [
            "• Kliknij statek aby go wybrać",
            "• Zielone pola = możliwy ruch",
            "• Czerwone pola = możliwy atak",
            "• 'Zakończ turę' aby przejść dalej",
        ]

        y_offset += 25
        for instr in instructions:
            draw_text(self.screen, instr, x_offset, y_offset, Colors.GRAY, size=12)
            y_offset += 18

    def _render_battle_end(self):
        """Renderuj ekran końca bitwy"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Panel
        panel_width = 500
        panel_height = 300
        panel_x = WINDOW_WIDTH // 2 - panel_width // 2
        panel_y = WINDOW_HEIGHT // 2 - panel_height // 2

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, Colors.WHITE, panel_rect, 3)

        # Tytuł
        draw_text(
            self.screen,
            "⚔️ BITWA ZAKOŃCZONA ⚔️",
            WINDOW_WIDTH // 2, panel_y + 30,
            Colors.YELLOW,
            size=32,
            center=True
        )

        # Wyniki
        y_offset = panel_y + 80

        attacker_alive = sum(1 for s in self.battle.attacker_states if s.ship.is_alive)
        defender_alive = sum(1 for s in self.battle.defender_states if s.ship.is_alive)

        if attacker_alive > 0 and defender_alive == 0:
            result_text = "🏆 ZWYCIĘSTWO ATAKUJĄCYCH!"
            result_color = (100, 150, 255)
        elif defender_alive > 0 and attacker_alive == 0:
            result_text = "🏆 ZWYCIĘSTWO OBROŃCÓW!"
            result_color = (255, 100, 100)
        else:
            result_text = "⚔️ REMIS"
            result_color = Colors.GRAY

        draw_text(
            self.screen,
            result_text,
            WINDOW_WIDTH // 2, y_offset,
            result_color,
            size=24,
            center=True
        )

        y_offset += 50

        # Statystyki
        draw_text(
            self.screen,
            f"Rund: {self.battle.round_number}",
            WINDOW_WIDTH // 2, y_offset,
            Colors.WHITE,
            size=18,
            center=True
        )

        y_offset += 30
        draw_text(
            self.screen,
            f"Atakujący: {attacker_alive} ocalałych",
            WINDOW_WIDTH // 2, y_offset,
            (100, 150, 255),
            size=16,
            center=True
        )

        y_offset += 25
        draw_text(
            self.screen,
            f"Obrońcy: {defender_alive} ocalałych",
            WINDOW_WIDTH // 2, y_offset,
            (255, 100, 100),
            size=16,
            center=True
        )

        y_offset += 50
        draw_text(
            self.screen,
            "Naciśnij ESC lub kliknij aby kontynuować",
            WINDOW_WIDTH // 2, y_offset,
            Colors.GRAY,
            size=14,
            center=True
        )

    def _render_attack_animation(self):
        """Renderuj animację ataku (laser)"""
        if not self.attack_animation:
            return

        from_pos = self.attack_animation['from']
        to_pos = self.attack_animation['to']
        progress = self.attack_animation.get('progress', 0)

        # Konwertuj grid position na screen position
        from_x = self.grid_offset_x + from_pos.x * self.tile_size + self.tile_size // 2
        from_y = self.grid_offset_y + from_pos.y * self.tile_size + self.tile_size // 2
        to_x = self.grid_offset_x + to_pos.x * self.tile_size + self.tile_size // 2
        to_y = self.grid_offset_y + to_pos.y * self.tile_size + self.tile_size // 2

        # Rysuj laser
        pygame.draw.line(self.screen, (255, 50, 50), (from_x, from_y), (to_x, to_y), 4)
        pygame.draw.line(self.screen, (255, 200, 200), (from_x, from_y), (to_x, to_y), 2)

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """
        Obsłuż kliknięcie
        Returns: True jeśli kliknięcie było obsłużone
        """
        mouse_x, mouse_y = pos

        # Sprawdź przyciski
        if self.retreat_button.handle_click(pos):
            return True
        if self.end_turn_button.handle_click(pos):
            return True
        if self.pass_button.handle_click(pos):
            return True

        # Jeśli bitwa się skończyła, każde kliknięcie zamyka
        if self.battle.battle_ended:
            return True

        # Konwertuj screen position na grid position
        grid_pos = self._screen_to_grid(mouse_x, mouse_y)
        if not grid_pos:
            return False

        # Sprawdź czy kliknięto statek
        ship_at_pos = self.battle.get_ship_at_position(grid_pos)

        # Jeśli to tura AI, ignoruj kliknięcia
        current = self.battle.get_current_ship()
        if not current:
            return False

        is_player_turn = (
            (current in self.battle.attacker_states and
             self.battle.attacker_empire_id == self.battle.player_empire_id) or
            (current in self.battle.defender_states and
             self.battle.defender_empire_id == self.battle.player_empire_id)
        )

        if not is_player_turn:
            return False

        # Tryb wybierania
        if self.mode == "select":
            if ship_at_pos and ship_at_pos == current:
                # Wybrany aktualny statek
                self.selected_ship = ship_at_pos
                self._update_highlights()
                return True

        # Tryb ruchu - kliknięto wolne pole
        if grid_pos in self.highlighted_positions:
            if self.selected_ship:
                if self.battle.move_ship(self.selected_ship, grid_pos):
                    self._update_highlights()
                    return True

        # Tryb ataku - kliknięto wrogi statek
        if ship_at_pos and grid_pos in self.target_positions:
            if self.selected_ship:
                damage = self.battle.attack(self.selected_ship, ship_at_pos)
                if damage > 0:
                    # Uruchom animację
                    self.attack_animation = {
                        'from': self.selected_ship.position,
                        'to': ship_at_pos.position,
                        'progress': 0,
                        'duration': 0.5
                    }
                    self._update_highlights()
                return True

        return False

    def _screen_to_grid(self, screen_x: int, screen_y: int) -> Optional[GridPosition]:
        """Konwertuj pozycję ekranu na pozycję gridu"""
        grid_x = (screen_x - self.grid_offset_x) // self.tile_size
        grid_y = (screen_y - self.grid_offset_y) // self.tile_size

        pos = GridPosition(grid_x, grid_y)
        if self.battle.grid.is_valid_position(pos):
            return pos
        return None

    def _update_highlights(self):
        """Zaktualizuj podświetlenia (możliwe ruchy i cele)"""
        self.highlighted_positions = []
        self.target_positions = []

        if not self.selected_ship:
            return

        # Możliwe ruchy (zielone)
        if not self.selected_ship.has_moved:
            occupied = self.battle.get_occupied_positions()
            possible_moves = self.battle.grid.get_neighbors(
                self.selected_ship.position,
                self.selected_ship.movement_points
            )
            self.highlighted_positions = [p for p in possible_moves if p not in occupied]

        # Możliwe cele (czerwone)
        if not self.selected_ship.has_attacked:
            targets = self.battle.get_targets_in_range(self.selected_ship)
            self.target_positions = [t.position for t in targets]

    def _on_retreat(self):
        """Obsłuż kliknięcie przycisku wycofania"""
        # Tylko gracz może się wycofać
        if self.battle.is_player_involved:
            self.battle_result = self.battle.retreat()

    def _on_end_turn(self):
        """Obsłuż kliknięcie zakończenia tury"""
        self.selected_ship = None
        self.highlighted_positions = []
        self.target_positions = []
        self.battle.next_turn()

        # Jeśli teraz tura AI, wykonaj jej akcje
        self._process_ai_turns()

    def _on_pass(self):
        """Pomiń turę obecnego statku"""
        current = self.battle.get_current_ship()
        if current:
            current.has_moved = True
            current.has_attacked = True
        self._on_end_turn()

    def _process_ai_turns(self):
        """Wykonaj tury AI statków"""
        while True:
            current = self.battle.get_current_ship()
            if not current:
                break

            # Sprawdź czy to tura gracza
            is_player_turn = (
                (current in self.battle.attacker_states and
                 self.battle.attacker_empire_id == self.battle.player_empire_id) or
                (current in self.battle.defender_states and
                 self.battle.defender_empire_id == self.battle.player_empire_id)
            )

            if is_player_turn:
                # Tura gracza - stop
                self.selected_ship = current
                self._update_highlights()
                break

            # Tura AI - wykonaj akcje
            self.battle.ai_take_turn(current)
            self.battle.next_turn()

            # Sprawdź koniec bitwy
            if self.battle.battle_ended:
                self.battle_result = self.battle._create_result()
                break

    def update(self, dt: float):
        """Aktualizuj stan ekranu"""
        # Aktualizuj animacje
        if self.attack_animation:
            self.attack_animation['progress'] += dt
            if self.attack_animation['progress'] >= self.attack_animation['duration']:
                self.attack_animation = None
