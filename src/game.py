"""
Główna logika gry
"""
import pygame
from typing import Optional
from src.models.galaxy import Galaxy, StarSystem
from src.models.empire import Empire
from src.models.ship import Ship, ShipType
from src.ui.renderer import Renderer
from src.ui.widgets import Panel, Button, draw_text
from src.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, WINDOW_TITLE,
    Colors, NUM_AI_EMPIRES, STARTING_SHIPS, PANEL_WIDTH,
    PANEL_PADDING
)


class Game:
    """
    Główna klasa gry - zarządza stanem gry i pętlą główną
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = False

        # Renderer
        self.renderer = Renderer(self.screen)

        # Stan gry
        self.galaxy: Optional[Galaxy] = None
        self.empires: list[Empire] = []
        self.player_empire: Optional[Empire] = None
        self.ships: list[Ship] = []
        self.current_turn = 1
        self.next_ship_id = 0

        # UI
        self.selected_system: Optional[StarSystem] = None
        self.info_panel: Optional[Panel] = None
        self.setup_ui()

        # Input
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)

    def setup_ui(self):
        """Przygotuj UI"""
        # Panel informacyjny po prawej stronie
        self.info_panel = Panel(
            x=WINDOW_WIDTH - PANEL_WIDTH,
            y=0,
            width=PANEL_WIDTH,
            height=WINDOW_HEIGHT,
            title="Informacje"
        )

        # Przycisk zakończenia tury
        self.end_turn_button = Button(
            x=WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING,
            y=WINDOW_HEIGHT - 60,
            width=PANEL_WIDTH - 2 * PANEL_PADDING,
            height=40,
            text="Zakończ turę",
            callback=self.end_turn
        )

    def initialize_new_game(self):
        """Rozpocznij nową grę"""
        print("Generowanie galaktyki...")
        self.galaxy = Galaxy.generate()

        print("Tworzenie imperiów...")
        # Stwórz gracza
        self.player_empire = Empire.create_player("Ziemia")
        self.empires.append(self.player_empire)

        # Stwórz AI
        for i in range(NUM_AI_EMPIRES):
            ai_empire = Empire.create_ai(i + 1)
            self.empires.append(ai_empire)

        print("Przydzielanie systemów macierzystych...")
        # Przydziel systemy macierzyste
        for i, empire in enumerate(self.empires):
            if i < len(self.galaxy.systems):
                home_system = self.galaxy.systems[i]
                empire.home_system_id = home_system.id
                empire.explore_system(home_system.id)
                home_system.explore(empire.id)

                # Skolonizuj pierwszą planetę
                if home_system.planets:
                    home_planet = home_system.planets[0]
                    home_planet.colonize(empire.id, initial_population=50.0)

                # Stwórz początkowe statki
                self._create_starting_ships(empire, home_system)

        # Wycentruj kamerę na systemie gracza
        if self.player_empire.home_system_id is not None:
            home_system = self.galaxy.find_system_by_id(self.player_empire.home_system_id)
            if home_system:
                self.renderer.camera.center_on(home_system.x, home_system.y)

        print("Gra gotowa!")

    def _create_starting_ships(self, empire: Empire, system: StarSystem):
        """Stwórz początkowe statki dla imperium"""
        for ship_type, count in STARTING_SHIPS.items():
            for _ in range(count):
                ship = Ship.create_ship(
                    ship_id=self.next_ship_id,
                    ship_type=ship_type,
                    owner_id=empire.id,
                    x=system.x,
                    y=system.y
                )
                self.ships.append(ship)
                self.next_ship_id += 1

    def run(self):
        """Główna pętla gry"""
        self.running = True
        self.initialize_new_game()

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time w sekundach
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()

    def handle_events(self):
        """Obsługa zdarzeń"""
        mouse_pos = pygame.mouse.get_pos()

        # Aktualizuj stan przycisków
        self.end_turn_button.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Lewy przycisk myszy
                    self._handle_left_click(mouse_pos)
                elif event.button == 3:  # Prawy przycisk myszy
                    self.mouse_dragging = True
                    self.last_mouse_pos = mouse_pos
                elif event.button == 4:  # Scroll w górę (zoom in)
                    self.renderer.camera.zoom_in()
                elif event.button == 5:  # Scroll w dół (zoom out)
                    self.renderer.camera.zoom_out()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    self.mouse_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    dx = self.last_mouse_pos[0] - mouse_pos[0]
                    dy = self.last_mouse_pos[1] - mouse_pos[1]
                    self.renderer.camera.move(dx, dy)
                    self.last_mouse_pos = mouse_pos

    def _handle_keyboard(self, key):
        """Obsługa klawiatury"""
        # Strzałki - ruch kamery
        if key == pygame.K_LEFT or key == pygame.K_a:
            self.renderer.camera.move(-20, 0)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.renderer.camera.move(20, 0)
        elif key == pygame.K_UP or key == pygame.K_w:
            self.renderer.camera.move(0, -20)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.renderer.camera.move(0, 20)

        # Zoom
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            self.renderer.camera.zoom_in()
        elif key == pygame.K_MINUS:
            self.renderer.camera.zoom_out()

        # Spacja - zakończ turę
        elif key == pygame.K_SPACE:
            self.end_turn()

        # Escape - wyjście
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _handle_left_click(self, mouse_pos):
        """Obsługa lewego kliknięcia myszy"""
        # Sprawdź czy kliknięto w przycisk
        if self.end_turn_button.handle_click(mouse_pos):
            return

        # Sprawdź czy kliknięto w panel UI
        if mouse_pos[0] >= WINDOW_WIDTH - PANEL_WIDTH:
            return

        # Kliknięcie w mapę - sprawdź czy kliknięto system
        world_x, world_y = self.renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        system = self.galaxy.get_system_at(world_x, world_y, tolerance=30/self.renderer.camera.zoom)

        if system and system.is_explored_by(self.player_empire.id):
            self.selected_system = system
        else:
            self.selected_system = None

    def update(self, dt: float):
        """Aktualizuj stan gry"""
        # Aktualizuj ruch statków
        for ship in self.ships:
            ship.update_movement(dt)

    def end_turn(self):
        """Zakończ turę"""
        self.current_turn += 1
        print(f"Tura {self.current_turn}")

        # Wzrost populacji na planetach
        for system in self.galaxy.systems:
            for planet in system.planets:
                if planet.is_colonized:
                    planet.grow_population()

    def render(self):
        """Renderuj grę"""
        self.renderer.clear()
        self.renderer.draw_background()

        # Rysuj galaktykę
        if self.galaxy:
            self.renderer.draw_galaxy(self.galaxy, self.player_empire.id)

        # Rysuj statki
        empire_colors = {empire.id: empire.color for empire in self.empires}
        self.renderer.draw_ships(self.ships, empire_colors)

        # Podświetl wybrany system
        if self.selected_system:
            self.renderer.highlight_system(self.selected_system)

        # Rysuj UI
        self._render_ui()

        # FPS
        self.renderer.draw_fps(self.clock.get_fps())

        pygame.display.flip()

    def _render_ui(self):
        """Rysuj interfejs użytkownika"""
        # Panel informacyjny
        self.info_panel.draw(self.screen, self.renderer.font_medium)

        # Informacje o turze
        y_offset = 50
        draw_text(self.screen, f"Tura: {self.current_turn}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                 self.renderer.font_small, Colors.UI_TEXT)

        y_offset += 30
        draw_text(self.screen, f"Imperium: {self.player_empire.name}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                 self.renderer.font_small, Colors.UI_TEXT)

        # Informacje o wybranym systemie
        if self.selected_system:
            y_offset += 50
            draw_text(self.screen, "Wybrany system:",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, Colors.UI_HIGHLIGHT)

            y_offset += 25
            draw_text(self.screen, self.selected_system.name,
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, Colors.WHITE)

            y_offset += 25
            draw_text(self.screen, f"Typ: {self.selected_system.star_type.value}",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, Colors.UI_TEXT)

            y_offset += 25
            draw_text(self.screen, f"Planet: {len(self.selected_system.planets)}",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, Colors.UI_TEXT)

            # Lista planet
            for i, planet in enumerate(self.selected_system.planets):
                y_offset += 25
                planet_info = f"  {planet.name}"
                if planet.is_colonized:
                    planet_info += f" (Pop: {int(planet.population)})"
                draw_text(self.screen, planet_info,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                         self.renderer.font_small, Colors.UI_TEXT)

        # Przycisk zakończenia tury
        self.end_turn_button.draw(self.screen, self.renderer.font_medium)

        # Instrukcje
        y_bottom = WINDOW_HEIGHT - 100
        draw_text(self.screen, "Sterowanie:",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 100,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "WSAD/Strzałki - ruch",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 75,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "PPM - przeciągnij mapę",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 60,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "Scroll - zoom",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 45,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "LPM - wybierz system",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 30,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "Spacja - zakończ turę",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 15,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
