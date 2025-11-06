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

        # Inicjalizuj zasoby na starcie
        self._update_empire_resources()

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

        # P lub 1-9 - otwórz ekran planety
        elif key == pygame.K_p:
            self._open_planet_screen(0)  # Pierwsza planeta
        elif pygame.K_1 <= key <= pygame.K_9:
            # Klawsze 1-9 otwierają konkretną planetę
            planet_index = key - pygame.K_1
            self._open_planet_screen(planet_index)

        # Escape - wyjście lub zamknij ekran planety
        elif key == pygame.K_ESCAPE:
            if self.planet_screen:
                self.planet_screen = None
            else:
                self.running = False

    def _open_planet_screen(self, planet_index: int = 0):
        """Otwórz ekran szczegółów planety"""
        if not self.selected_system:
            print("Najpierw wybierz system!")
            return

        # Znajdź skolonizowane planety gracza w systemie
        player_planets = self.selected_system.get_colonized_planets(self.player_empire.id)

        if not player_planets:
            print("Brak twoich planet w tym systemie!")
            return

        # Sprawdź czy indeks jest w zakresie
        if planet_index >= len(player_planets):
            print(f"Brak planety #{planet_index + 1} w tym systemie (masz {len(player_planets)})")
            return

        # Otwórz ekran wybranej planety
        planet = player_planets[planet_index]
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
        ships_at_location = self._find_all_ships_at(world_x, world_y, self.player_empire.id)

        if ships_at_location:
            keys = pygame.key.get_pressed()

            # Shift+Click = cykliczny wybór z nakładających się statków
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                # Jeśli mamy wiele statków w tym miejscu, wybierz następny
                if len(ships_at_location) > 1:
                    # Znajdź który statek jest obecnie wybrany (jeśli jakiś)
                    current_index = -1
                    for i, ship in enumerate(ships_at_location):
                        if ship in self.selected_ships:
                            current_index = i
                            break

                    # Wybierz następny (cyklicznie)
                    next_index = (current_index + 1) % len(ships_at_location)
                    clicked_ship = ships_at_location[next_index]

                    # Toggle: jeśli był wybrany, odznacz; jeśli nie, zaznacz
                    if clicked_ship in self.selected_ships:
                        self.selected_ships.remove(clicked_ship)
                    else:
                        self.selected_ships = [clicked_ship]
                else:
                    # Tylko jeden statek - normalny toggle
                    clicked_ship = ships_at_location[0]
                    if clicked_ship in self.selected_ships:
                        self.selected_ships.remove(clicked_ship)
                    else:
                        self.selected_ships.append(clicked_ship)
            else:
                # Normalny click - wybierz pierwszy statek
                self.selected_ships = [ships_at_location[0]]
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

    def _find_all_ships_at(self, world_x: float, world_y: float, empire_id: int, tolerance: float = 15) -> list[Ship]:
        """Znajdź WSZYSTKIE statki w danej pozycji (dla nakładających się)"""
        import math
        found_ships = []
        for ship in self.ships:
            if ship.owner_id != empire_id:
                continue
            distance = math.sqrt((ship.x - world_x)**2 + (ship.y - world_y)**2)
            if distance <= tolerance / self.renderer.camera.zoom:
                found_ships.append(ship)
        return found_ships

    def _try_colonize(self, colony_ship: Ship) -> bool:
        """Spróbuj skolonizować planetę statkiem kolonistów. Zwraca True jeśli się powiodło."""
        # Znajdź system docelowy
        target_system = self.galaxy.find_system_by_id(colony_ship.target_system_id)
        if not target_system:
            return False

        # Sprawdź czy system jest odkryty
        if not target_system.is_explored_by(colony_ship.owner_id):
            target_system.explore(colony_ship.owner_id)

        # Znajdź pierwszą nieskolonizowaną planetę
        free_planets = target_system.get_free_planets()
        if not free_planets:
            print(f"Brak wolnych planet w systemie {target_system.name}")
            colony_ship.target_system_id = None  # Wyczyść cel
            return False

        # Skolonizuj pierwszą wolną planetę
        planet = free_planets[0]
        planet.colonize(colony_ship.owner_id, initial_population=10.0)

        print(f"✓ {planet.name} skolonizowana przez {self.empires[colony_ship.owner_id].name}!")

        # Zwróć True - statek zostanie usunięty przez wywołującego
        return True

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
        """Aktualizuj stan gry (teraz tylko wizualizacja)"""
        # W trybie turowym update() nie przesuwa statków
        # Ruch odbywa się tylko podczas end_turn()
        pass

    def end_turn(self):
        """Zakończ turę"""
        self.current_turn += 1
        print(f"\n=== TURA {self.current_turn} ===")

        # 1. Ruch statków (turowy)
        ships_to_remove = []
        explored_systems = set()

        for ship in self.ships:
            arrived = ship.move_one_turn()

            # Sprawdź eksplorację systemów (tylko jeśli dotarł)
            if arrived and ship.target_system_id is not None:
                if ship.target_system_id not in explored_systems:
                    target_system = self.galaxy.find_system_by_id(ship.target_system_id)
                    if target_system and not target_system.is_explored_by(ship.owner_id):
                        target_system.explore(ship.owner_id)
                        empire = next((e for e in self.empires if e.id == ship.owner_id), None)
                        if empire:
                            empire.explore_system(ship.target_system_id)
                        explored_systems.add(ship.target_system_id)
                        print(f"✓ {target_system.name} odkryty!")

                # Sprawdź kolonizację (tylko dla statków kolonistów)
                if ship.ship_type == ShipType.COLONY_SHIP:
                    result = self._try_colonize(ship)
                    if result:  # Jeśli kolonizacja się powiodła
                        ships_to_remove.append(ship)
                else:
                    # Dla innych statków wyczyść cel po dotarciu
                    ship.target_system_id = None

        # Usuń statki po iteracji
        for ship in ships_to_remove:
            self.ships.remove(ship)
            if ship in self.selected_ships:
                self.selected_ships.remove(ship)

        # 2. Wzrost populacji i produkcja na planetach
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

        # 3. Aktualizacja zasobów imperii
        self._update_empire_resources()

    def _update_empire_resources(self):
        """Aktualizuj całkowite zasoby wszystkich imperiów"""
        for empire in self.empires:
            total_prod = 0.0
            total_sci = 0.0

            # Sumuj z wszystkich planet
            for system in self.galaxy.systems:
                for planet in system.planets:
                    if planet.owner_id == empire.id:
                        total_prod += planet.calculate_production()
                        total_sci += planet.calculate_science()

            empire.total_production = total_prod
            empire.total_science = total_sci

    def render(self):
        """Renderuj grę"""
        self.renderer.clear()
        self.renderer.draw_background()

        # Przygotuj kolory imperiów
        empire_colors = {empire.id: empire.color for empire in self.empires}

        # Rysuj galaktykę
        if self.galaxy:
            self.renderer.draw_galaxy(self.galaxy, self.player_empire.id, empire_colors)

        # Rysuj statki
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

        # Zasoby imperium
        y_offset += 25
        draw_text(self.screen, f"Produkcja: {self.player_empire.total_production:.1f}/tura",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                 self.renderer.font_small, Colors.UI_TEXT)

        y_offset += 20
        draw_text(self.screen, f"Nauka: {self.player_empire.total_science:.1f}/tura",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                 self.renderer.font_small, Colors.UI_TEXT)

        # Statystyki eksploracji
        explored_count = len(self.player_empire.explored_systems)
        total_systems = len(self.galaxy.systems)
        unexplored = total_systems - explored_count
        y_offset += 25
        draw_text(self.screen, f"Systemy: {explored_count}/{total_systems}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                 self.renderer.font_small, Colors.LIGHT_GRAY)

        # Hint o nieodkrytych systemach (na początku gry)
        if self.current_turn < 3 and unexplored > 0:
            y_offset += 20
            hint_color = (100, 150, 200)  # Niebieski hint
            draw_text(self.screen, f"💡 {unexplored} szare kropki",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, hint_color)
            y_offset += 18
            draw_text(self.screen, "   to nieodkryte systemy!",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                     self.renderer.font_small, hint_color)

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
            y_offset += 10
            for i, planet in enumerate(self.selected_system.planets):
                y_offset += 22

                # Ikona planety (kolorowe kółko)
                planet_icon_x = WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 5
                planet_icon_y = y_offset + 7
                pygame.draw.circle(self.screen, planet.color, (planet_icon_x, planet_icon_y), 4)

                # Informacje o planecie
                planet_info = f"{chr(65 + i)}: {planet.planet_type.value[:3]}"  # A: Zie (skrót)

                if planet.is_colonized:
                    if planet.owner_id == self.player_empire.id:
                        planet_info += f" | Twoja"
                    else:
                        owner = next((e for e in self.empires if e.id == planet.owner_id), None)
                        if owner:
                            planet_info += f" | {owner.name[:10]}"
                    planet_info += f" (Pop:{int(planet.population)})"
                else:
                    planet_info += f" | Wolna"

                # Kolor tekstu
                text_color = Colors.UI_TEXT
                if planet.is_colonized and planet.owner_id == self.player_empire.id:
                    text_color = Colors.PLAYER

                draw_text(self.screen, planet_info,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 15, y_offset,
                         self.renderer.font_small, text_color)

            # Podpowiedź o zarządzaniu planetami
            player_planets = self.selected_system.get_colonized_planets(self.player_empire.id)
            if player_planets:
                y_offset += 30
                hint = f"P lub 1-{len(player_planets)} - zarządzaj planetą"
                draw_text(self.screen, hint,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                         self.renderer.font_small, Colors.LIGHT_GRAY)

            # Lista statków gracza w tym systemie
            y_offset += 30
            system_ships = [s for s in self.ships if s.owner_id == self.player_empire.id and
                           abs(s.x - self.selected_system.x) < 50 and
                           abs(s.y - self.selected_system.y) < 50]

            if system_ships:
                draw_text(self.screen, f"Twoje statki ({len(system_ships)}):",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                         self.renderer.font_small, Colors.UI_HIGHLIGHT)

                for i, ship in enumerate(system_ships[:5]):  # Max 5
                    y_offset += 22

                    # Ikona statku (trójkąt)
                    ship_icon_x = WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 5
                    ship_icon_y = y_offset + 7
                    points = [
                        (ship_icon_x, ship_icon_y - 4),
                        (ship_icon_x - 3, ship_icon_y + 3),
                        (ship_icon_x + 3, ship_icon_y + 3)
                    ]
                    pygame.draw.polygon(self.screen, Colors.PLAYER, points)

                    # Info
                    ship_info = f"{i+1}: {ship.ship_type.value[:10]}"
                    if ship.is_moving:
                        ship_info += " →"

                    # Kolor (biały jeśli wybrany)
                    text_color = Colors.WHITE if ship in self.selected_ships else Colors.UI_TEXT

                    draw_text(self.screen, ship_info,
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 15, y_offset,
                             self.renderer.font_small, text_color)

                if len(system_ships) > 5:
                    y_offset += 20
                    draw_text(self.screen, f"  ...i {len(system_ships) - 5} więcej",
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                             self.renderer.font_small, Colors.LIGHT_GRAY)

                # Podpowiedź
                y_offset += 25
                draw_text(self.screen, "Shift+LPM - wybierz następny",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_offset,
                         self.renderer.font_small, Colors.LIGHT_GRAY)

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
