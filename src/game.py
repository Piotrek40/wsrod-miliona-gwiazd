"""
Główna logika gry
"""
import pygame
from typing import Optional
from src.models.galaxy import Galaxy, StarSystem
from src.models.empire import Empire
from src.models.ship import Ship, ShipType
from src.models.planet import Planet
from src.ui.renderer import Renderer
from src.ui.widgets import Panel, Button, draw_text
from src.ui.screens.planet_screen import PlanetScreen
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
        self.selected_ships: list[Ship] = []  # Wybrane statki
        self.selected_planet = None  # Wybrana planeta (dla ekranu szczegółów)
        self.planet_screen: Optional[PlanetScreen] = None  # Ekran szczegółów planety
        self.info_panel: Optional[Panel] = None
        self.setup_ui()

        # Input
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)
        self.right_click_start_pos = None  # Pozycja początku prawego kliknięcia

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

        # Aktualizuj ekran planety jeśli jest otwarty
        if self.planet_screen:
            self.planet_screen.update(mouse_pos)

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
                    self.right_click_start_pos = mouse_pos
                elif event.button == 4:  # Scroll w górę (zoom in)
                    self.renderer.camera.zoom_in()
                elif event.button == 5:  # Scroll w dół (zoom out)
                    self.renderer.camera.zoom_out()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    # Sprawdź czy to było przeciąganie czy kliknięcie
                    if self.right_click_start_pos:
                        import math
                        dx = mouse_pos[0] - self.right_click_start_pos[0]
                        dy = mouse_pos[1] - self.right_click_start_pos[1]
                        distance = math.sqrt(dx*dx + dy*dy)

                        if distance < 5:  # To było kliknięcie, nie przeciąganie
                            self._handle_right_click(mouse_pos)

                    self.mouse_dragging = False
                    self.right_click_start_pos = None

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

        # P - otwórz ekran planety
        elif key == pygame.K_p:
            self._open_planet_screen()

        # Escape - wyjście lub zamknij ekran planety
        elif key == pygame.K_ESCAPE:
            if self.planet_screen:
                self.planet_screen = None
            else:
                self.running = False

    def _open_planet_screen(self):
        """Otwórz ekran szczegółów planety"""
        if not self.selected_system:
            print("Najpierw wybierz system!")
            return

        # Znajdź skolonizowane planety gracza w systemie
        player_planets = self.selected_system.get_colonized_planets(self.player_empire.id)

        if not player_planets:
            print("Brak twoich planet w tym systemie!")
            return

        # Otwórz ekran pierwszej planety
        planet = player_planets[0]
        self.planet_screen = PlanetScreen(
            planet=planet,
            system_name=self.selected_system.name,
            on_close=lambda: setattr(self, 'planet_screen', None)
        )

    def _handle_left_click(self, mouse_pos):
        """Obsługa lewego kliknięcia myszy"""
        # Jeśli ekran planety jest otwarty, przekaż do niego kliknięcie
        if self.planet_screen:
            self.planet_screen.handle_click(mouse_pos)
            return

        # Sprawdź czy kliknięto w przycisk
        if self.end_turn_button.handle_click(mouse_pos):
            return

        # Sprawdź czy kliknięto w panel UI
        if mouse_pos[0] >= WINDOW_WIDTH - PANEL_WIDTH:
            return

        # Kliknięcie w mapę
        world_x, world_y = self.renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])

        # Najpierw sprawdź czy kliknięto statek gracza
        clicked_ship = self._find_ship_at(world_x, world_y, self.player_empire.id)
        if clicked_ship:
            # Sprawdź czy shift jest wciśnięty (wielokrotny wybór)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                if clicked_ship in self.selected_ships:
                    self.selected_ships.remove(clicked_ship)
                else:
                    self.selected_ships.append(clicked_ship)
            else:
                self.selected_ships = [clicked_ship]
            return

        # Jeśli nie kliknięto statku, sprawdź systemy
        system = self.galaxy.get_system_at(world_x, world_y, tolerance=30/self.renderer.camera.zoom)

        if system and system.is_explored_by(self.player_empire.id):
            self.selected_system = system
            self.selected_ships = []  # Odznacz statki
        else:
            self.selected_system = None
            self.selected_ships = []

    def _find_ship_at(self, world_x: float, world_y: float, empire_id: int, tolerance: float = 15) -> Optional[Ship]:
        """Znajdź statek w danej pozycji"""
        import math
        for ship in self.ships:
            if ship.owner_id != empire_id:
                continue
            distance = math.sqrt((ship.x - world_x)**2 + (ship.y - world_y)**2)
            if distance <= tolerance / self.renderer.camera.zoom:
                return ship
        return None

    def _try_colonize(self, colony_ship: Ship):
        """Spróbuj skolonizować planetę statkiem kolonistów"""
        # Znajdź system docelowy
        target_system = self.galaxy.find_system_by_id(colony_ship.target_system_id)
        if not target_system:
            return

        # Sprawdź czy system jest odkryty
        if not target_system.is_explored_by(colony_ship.owner_id):
            target_system.explore(colony_ship.owner_id)

        # Znajdź pierwszą nieskolonizowaną planetę
        free_planets = target_system.get_free_planets()
        if not free_planets:
            print(f"Brak wolnych planet w systemie {target_system.name}")
            return

        # Skolonizuj pierwszą wolną planetę
        planet = free_planets[0]
        planet.colonize(colony_ship.owner_id, initial_population=10.0)

        print(f"✓ {planet.name} skolonizowana przez {self.empires[colony_ship.owner_id].name}!")

        # Usuń statek kolonistów (zużyty podczas kolonizacji)
        self.ships.remove(colony_ship)
        if colony_ship in self.selected_ships:
            self.selected_ships.remove(colony_ship)

    def _handle_right_click(self, mouse_pos):
        """Obsługa prawego kliknięcia - wydawanie rozkazów"""
        # Sprawdź czy są wybrane statki
        if not self.selected_ships:
            return

        # Sprawdź czy kliknięto w panel UI
        if mouse_pos[0] >= WINDOW_WIDTH - PANEL_WIDTH:
            return

        # Kliknięcie w mapę - wyślij statki
        world_x, world_y = self.renderer.camera.screen_to_world(mouse_pos[0], mouse_pos[1])

        # Sprawdź czy kliknięto w system
        system = self.galaxy.get_system_at(world_x, world_y, tolerance=30/self.renderer.camera.zoom)

        if system:
            # Wyślij statki do systemu
            for ship in self.selected_ships:
                ship.move_to(system.x, system.y, system.id)
                print(f"{ship.name} wysłany do {system.name}")
        else:
            # Wyślij statki do punktu w przestrzeni
            for ship in self.selected_ships:
                ship.move_to(world_x, world_y)
                print(f"{ship.name} wysłany do pozycji ({int(world_x)}, {int(world_y)})")

    def update(self, dt: float):
        """Aktualizuj stan gry"""
        # Aktualizuj ruch statków
        for ship in self.ships:
            ship.update_movement(dt)

            # Sprawdź eksplorację systemów
            if not ship.is_moving and ship.target_system_id is not None:
                target_system = self.galaxy.find_system_by_id(ship.target_system_id)
                if target_system and not target_system.is_explored_by(ship.owner_id):
                    target_system.explore(ship.owner_id)
                    empire = next((e for e in self.empires if e.id == ship.owner_id), None)
                    if empire:
                        empire.explore_system(ship.target_system_id)
                    print(f"✓ {target_system.name} odkryty!")

            # Sprawdź kolonizację
            if not ship.is_moving and ship.ship_type == ShipType.COLONY_SHIP and ship.target_system_id is not None:
                self._try_colonize(ship)

    def end_turn(self):
        """Zakończ turę"""
        self.current_turn += 1
        print(f"Tura {self.current_turn}")

        # Wzrost populacji i produkcja na planetach
        for system in self.galaxy.systems:
            for planet in system.planets:
                if planet.is_colonized:
                    planet.grow_population()

                    # Przetwórz produkcję
                    completed_item = planet.process_production()
                    if completed_item and completed_item.ship_type:
                        # Stwórz nowy statek
                        new_ship = Ship.create_ship(
                            ship_id=self.next_ship_id,
                            ship_type=completed_item.ship_type,
                            owner_id=planet.owner_id,
                            x=system.x,
                            y=system.y
                        )
                        self.ships.append(new_ship)
                        self.next_ship_id += 1
                        print(f"✓ {new_ship.name} wyprodukowany w systemie {system.name}!")

    def render(self):
        """Renderuj grę"""
        self.renderer.clear()
        self.renderer.draw_background()

        # Rysuj galaktykę
        if self.galaxy:
            self.renderer.draw_galaxy(self.galaxy, self.player_empire.id)

        # Rysuj statki
        empire_colors = {empire.id: empire.color for empire in self.empires}
        self.renderer.draw_ships(self.ships, empire_colors, self.selected_ships)

        # Podświetl wybrany system
        if self.selected_system:
            self.renderer.highlight_system(self.selected_system)

        # Rysuj UI
        self._render_ui()

        # FPS
        self.renderer.draw_fps(self.clock.get_fps())

        # Rysuj ekran planety na wierzchu (jeśli otwarty)
        if self.planet_screen:
            self.planet_screen.draw(self.screen)

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

        # Informacje o wybranych statkach
        if self.selected_ships:
            y_offset += 50
            draw_text(self.screen, f"Wybrane statki: {len(self.selected_ships)}",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, Colors.UI_HIGHLIGHT)

            for ship in self.selected_ships[:5]:  # Pokaż max 5 statków
                y_offset += 25
                ship_info = f"  {ship.ship_type.value}"
                if ship.is_moving:
                    ship_info += " (w ruchu)"
                draw_text(self.screen, ship_info,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                         self.renderer.font_small, Colors.UI_TEXT)

            if len(self.selected_ships) > 5:
                y_offset += 25
                draw_text(self.screen, f"  ...i {len(self.selected_ships) - 5} więcej",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                         self.renderer.font_small, Colors.LIGHT_GRAY)

        # Informacje o wybranym systemie
        elif self.selected_system:
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
        y_bottom = WINDOW_HEIGHT - 135
        draw_text(self.screen, "Sterowanie:",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 130,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "WSAD/Strzałki - ruch",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 115,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "PPM przeciągnij - ruch mapy",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 100,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "Scroll - zoom",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 85,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "LPM - wybierz statek/system",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 70,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "Shift+LPM - dodaj do wyboru",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 55,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "PPM klik - rozkaz ruchu",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 40,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "P - zarządzaj planetą",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 25,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
        draw_text(self.screen, "Spacja - zakończ turę",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom - 10,
                 self.renderer.font_small, Colors.LIGHT_GRAY)
