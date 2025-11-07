"""
Główna logika gry
"""
import pygame
import random
from typing import Optional
from src.models.galaxy import Galaxy, StarSystem
from src.models.empire import Empire
from src.models.ship import Ship, ShipType
from src.models.planet import Planet, Building
from src.ui.renderer import Renderer
from src.ui.widgets import Panel, Button, draw_text
from src.ui.screens.planet_screen import PlanetScreen
from src.ui.screens.research_screen import ResearchScreen
from src.ui.screens.battle_screen import BattleScreen
from src.combat import CombatManager, CombatEffectsManager, TacticalBattle
from src.ai import AIController
from src.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, WINDOW_TITLE,
    Colors, NUM_AI_EMPIRES, STARTING_SHIPS, PANEL_WIDTH,
    PANEL_PADDING, COLONIZABLE_PLANET_TYPES,
    POPULATION_FOOD_UPKEEP, POPULATION_ENERGY_UPKEEP,
    DEFICIT_EFFECTS, TECHNOLOGIES, BUILDINGS
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

        # Combat system
        self.combat_manager = CombatManager()
        self.combat_effects = CombatEffectsManager()
        self.last_turn_battles = []  # Bitwy z ostatniej tury (do wyświetlenia)

        # Tactical combat
        self.tactical_battle: Optional[TacticalBattle] = None
        self.battle_screen: Optional[BattleScreen] = None

        # AI system
        self.ai_controllers: dict[int, AIController] = {}  # empire_id -> AIController

        # UI
        self.selected_system: Optional[StarSystem] = None
        self.selected_ships: list[Ship] = []  # Wybrane statki
        self.selected_planet = None  # Wybrana planeta (dla ekranu szczegółów)
        self.planet_screen: Optional[PlanetScreen] = None  # Ekran szczegółów planety
        self.research_screen: Optional[ResearchScreen] = None  # Ekran badań
        self.info_panel: Optional[Panel] = None
        self.show_help = False  # Czy pokazywać pełną pomoc (toggle H)
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

                # Skolonizuj pierwszą ODPOWIEDNIĄ planetę (NIE gazowy olbrzym!)
                # Znajdź pierwszą planetę która nadaje się do kolonizacji
                colonizable_planets = [p for p in home_system.planets
                                       if p.planet_type in COLONIZABLE_PLANET_TYPES]

                if colonizable_planets:
                    home_planet = colonizable_planets[0]
                    home_planet.colonize(empire.id, initial_population=50.0)
                    if empire.is_player:
                        print(f"✓ Start: {home_planet.name} ({home_planet.planet_type.value})")
                elif home_system.planets:
                    # Ostatnia deska ratunku - weź pierwszą planetę i zmień jej typ
                    home_planet = home_system.planets[0]
                    from src.config import PlanetType
                    home_planet.planet_type = PlanetType.EARTH_LIKE  # Wymuś ziemiopodobną
                    home_planet.colonize(empire.id, initial_population=50.0)
                    if empire.is_player:
                        print(f"⚠️ System macierzysty nie miał dobrych planet - przekształcono pierwszą")

                # Stwórz początkowe statki
                self._create_starting_ships(empire, home_system)

        # Wycentruj kamerę na systemie gracza
        if self.player_empire.home_system_id is not None:
            home_system = self.galaxy.find_system_by_id(self.player_empire.home_system_id)
            if home_system:
                self.renderer.camera.center_on(home_system.x, home_system.y)

        # Ustaw relacje dyplomatyczne (wszyscy w stanie wojny)
        print("Ustawianie relacji dyplomatycznych...")
        for i, emp1 in enumerate(self.empires):
            for j, emp2 in enumerate(self.empires):
                if i != j:
                    emp1.set_relation(emp2.id, "war")

        # Inicjalizuj AI controllery
        print("Inicjalizacja AI...")
        for empire in self.empires:
            if not empire.is_player:
                self.ai_controllers[empire.id] = AIController(empire, self.galaxy)
                print(f"  AI {empire.name} ({empire.ai_personality})")

        # TESTOWE: Dodaj pirackiego bossa i statek bojowy dla gracza
        self._create_test_combat_scenario()

        print("Gra gotowa!")

    def _create_test_combat_scenario(self):
        """
        TESTOWE: Stwórz scenariusz testowy do sprawdzenia combat
        - Piracki Cruiser w pobliżu systemu gracza
        - Bojowy Cruiser dla gracza
        """
        if not self.player_empire:
            print("⚠️ UWAGA: Nie można stworzyć test scenario - brak player_empire")
            return

        if self.player_empire.home_system_id is None:
            print("⚠️ UWAGA: Nie można stworzyć test scenario - brak home_system_id")
            return

        player_home = self.galaxy.find_system_by_id(self.player_empire.home_system_id)
        if not player_home:
            print("⚠️ UWAGA: Nie można stworzyć test scenario - nie znaleziono home system")
            return

        print("\n" + "="*60)
        print("🏴‍☠️ TESTOWY SCENARIUSZ COMBAT - POCZĄTEK")
        print("="*60)

        # 1. Stwórz pirackie imperium (bez AI controllera, więc piraci stoją w miejscu)
        from src.models.empire import Empire
        pirate_empire = Empire(
            id=999,  # Specjalne ID dla piratów
            name="🏴‍☠️ Piraci",
            color=(80, 80, 80),
            is_player=False
        )
        self.empires.append(pirate_empire)

        # Ustaw piratów w stanie wojny z graczem
        pirate_empire.set_relation(self.player_empire.id, "war")
        self.player_empire.set_relation(pirate_empire.id, "war")

        # 2. Stwórz pirackiego Cruisera BLISKO systemu gracza (dystans ~70 jednostek)
        # Zmniejszony z 150 na 70 żeby był widoczny
        pirate_x = player_home.x + 60
        pirate_y = player_home.y + 40

        pirate_cruiser = Ship.create_ship(
            ship_id=self.next_ship_id,
            ship_type=ShipType.CRUISER,
            owner_id=pirate_empire.id,
            x=pirate_x,
            y=pirate_y
        )
        pirate_cruiser.name = "🏴‍☠️ Piracki Boss"
        self.ships.append(pirate_cruiser)
        self.next_ship_id += 1

        print(f"  • Piracki Cruiser ({pirate_cruiser.name}) @ ({int(pirate_x)}, {int(pirate_y)})")
        print(f"    HP: {pirate_cruiser.max_hp}, ATK: {pirate_cruiser.attack}, DEF: {pirate_cruiser.defense}")

        # Oblicz rzeczywisty dystans
        dist = ((pirate_x - player_home.x)**2 + (pirate_y - player_home.y)**2)**0.5
        print(f"    Dystans od Twojego systemu: {int(dist)} jednostek")

        # 3. Dodaj bojowy Cruiser dla gracza w jego systemie
        player_cruiser = Ship.create_ship(
            ship_id=self.next_ship_id,
            ship_type=ShipType.CRUISER,
            owner_id=self.player_empire.id,
            x=player_home.x,
            y=player_home.y
        )
        player_cruiser.name = "⚔️ Obrońca"
        self.ships.append(player_cruiser)
        self.next_ship_id += 1

        print(f"  • Twój Cruiser ({player_cruiser.name}) @ ({int(player_home.x)}, {int(player_home.y)})")
        print(f"    HP: {player_cruiser.max_hp}, ATK: {player_cruiser.attack}, DEF: {player_cruiser.defense}")
        print(f"\n  💡 INSTRUKCJA:")
        print(f"     1. Znajdź swojego Cruisera '⚔️ Obrońca' w swoim systemie domowym")
        print(f"     2. Kliknij PPM aby wysłać go do pozycji pirata: (~{int(pirate_x)}, ~{int(pirate_y)})")
        print(f"     3. Gdy będą w zasięgu 100 jednostek, bitwa rozpocznie się automatycznie!")
        print(f"     4. Zobaczysz efekty lasery i eksplozje podczas walki!")
        print("="*60)
        print("🏴‍☠️ TESTOWY SCENARIUSZ COMBAT - KONIEC")
        print("="*60 + "\n")

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
            self.render(dt)  # Przekaż dt do renderera (dla animacji)

        pygame.quit()

    def handle_events(self):
        """Obsługa zdarzeń"""
        mouse_pos = pygame.mouse.get_pos()

        # Jeśli w tactical combat, obsługuj tylko battle screen
        if self.battle_screen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Zakończ bitwę (wycofanie)
                        if self.tactical_battle and not self.tactical_battle.battle_ended:
                            self.battle_screen._on_retreat()
                        # Jeśli bitwa się skończyła, zamknij ekran
                        if self.tactical_battle and self.tactical_battle.battle_ended:
                            self._end_tactical_battle()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # LPM
                        self.battle_screen.handle_click(mouse_pos)

                        # Sprawdź czy bitwa się skończyła
                        if self.tactical_battle.battle_ended:
                            self._end_tactical_battle()
            return

        # Aktualizuj stan przycisków
        self.end_turn_button.update(mouse_pos)

        # Aktualizuj ekran planety jeśli jest otwarty
        if self.planet_screen:
            self.planet_screen.update(mouse_pos)

        # Aktualizuj ekran badań jeśli jest otwarty
        if self.research_screen:
            self.research_screen.update(mouse_pos)

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

        # C - kolonizuj planetę (jeśli wybrano statek kolonistów)
        elif key == pygame.K_c:
            self._handle_colonize_command()

        # H - toggle pomoc/instrukcje
        elif key == pygame.K_h:
            self.show_help = not self.show_help

        # R - otwórz ekran badań
        elif key == pygame.K_r:
            if not self.research_screen and not self.planet_screen:
                self.research_screen = ResearchScreen(
                    empire=self.player_empire,
                    on_close=lambda: setattr(self, 'research_screen', None)
                )

        # Escape - wyjście lub zamknij ekrany
        elif key == pygame.K_ESCAPE:
            if self.planet_screen:
                self.planet_screen = None
            elif self.research_screen:
                self.research_screen = None
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
            empire=self.player_empire,
            on_close=lambda: setattr(self, 'planet_screen', None)
        )

    def _handle_left_click(self, mouse_pos):
        """Obsługa lewego kliknięcia myszy"""
        # Jeśli ekran planety jest otwarty, przekaż do niego kliknięcie
        if self.planet_screen:
            self.planet_screen.handle_click(mouse_pos)
            return

        # Jeśli ekran badań jest otwarty, przekaż do niego kliknięcie
        if self.research_screen:
            self.research_screen.handle_click(mouse_pos)
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

        # Znajdź KOLONIZOWALNE planety (filtrowane po typie - NIE gazowe olbrzymy!)
        colonizable_planets = target_system.get_colonizable_planets(COLONIZABLE_PLANET_TYPES)

        if not colonizable_planets:
            # Sprawdź czy są jakieś wolne planety (dla komunikatu)
            free_planets = target_system.get_free_planets()
            if free_planets:
                planet_types = ", ".join([p.planet_type.value for p in free_planets])
                print(f"⚠ {target_system.name}: Brak planet nadających się do kolonizacji!")
                print(f"  Dostępne planety: {planet_types}")
                print(f"  (Wymagana technologia do kolonizacji tych typów)")
            else:
                print(f"⚠ {target_system.name}: Wszystkie planety już skolonizowane")

            colony_ship.target_system_id = None  # Wyczyść cel
            return False

        # Skolonizuj pierwszą NADAJĄCĄ SIĘ planetę
        planet = colonizable_planets[0]
        planet.colonize(colony_ship.owner_id, initial_population=10.0)

        print(f"✓ {planet.name} ({planet.planet_type.value}) skolonizowana przez {self.empires[colony_ship.owner_id].name}!")

        # Zwróć True - statek zostanie usunięty przez wywołującego
        return True

    def _handle_colonize_command(self):
        """Obsługa komendy kolonizacji (klawisz C)"""
        # Sprawdź czy wybrano dokładnie jeden statek
        if len(self.selected_ships) != 1:
            print("⚠ Wybierz dokładnie jeden statek kolonistów aby kolonizować")
            return

        colony_ship = self.selected_ships[0]

        # Sprawdź czy to statek kolonistów
        if colony_ship.ship_type != ShipType.COLONY_SHIP:
            print(f"⚠ {colony_ship.ship_type.value} nie może kolonizować planet!")
            print("  Wybierz statek kolonistów.")
            return

        # Sprawdź czy statek jest w systemie
        if colony_ship.target_system_id is None:
            print("⚠ Statek kolonistów nie jest w żadnym systemie!")
            print("  Wyślij go do systemu który chcesz skolonizować (PPM na system)")
            return

        # Znajdź system w którym jest statek
        target_system = self.galaxy.find_system_by_id(colony_ship.target_system_id)
        if not target_system:
            print("⚠ Nie można znaleźć systemu docelowego")
            return

        # Sprawdź czy statek dotarł do celu (nie jest w ruchu)
        if colony_ship.is_moving:
            print(f"⚠ Statek kolonistów jest w drodze do {target_system.name}")
            print("  Poczekaj aż dotrze na miejsce")
            return

        # Spróbuj skolonizować
        print(f"\n🌍 Próba kolonizacji w systemie {target_system.name}...")
        result = self._try_colonize(colony_ship)

        if result:
            # Kolonizacja udana - usuń statek
            self.ships.remove(colony_ship)
            self.selected_ships.remove(colony_ship)
            print("  Statek kolonistów został wykorzystany do kolonizacji")

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

        # Jeśli w tactical combat, aktualizuj battle screen
        if self.battle_screen:
            self.battle_screen.update(dt)
            return

        # Aktualizuj efekty walki (animacje)
        self.combat_effects.update(dt)

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

                # Auto-kolonizacja dla AI (gracz musi nacisnąć 'C')
                if ship.ship_type == ShipType.COLONY_SHIP and ship.owner_id != self.player_empire.id:
                    # AI colony ship - próbuj skolonizować automatycznie
                    colonized = self._try_colonize(ship)
                    if colonized:
                        ships_to_remove.append(ship)  # Usuń statek kolonistów po kolonizacji
                # Dla statków innych niż kolonizacyjne wyczyść cel po dotarciu
                elif ship.ship_type != ShipType.COLONY_SHIP:
                    ship.target_system_id = None

        # Usuń statki po iteracji
        for ship in ships_to_remove:
            self.ships.remove(ship)
            if ship in self.selected_ships:
                self.selected_ships.remove(ship)

        # 1.5. Przetwarzanie bitew (combat system)
        # NOWA LOGIKA: Wykrywaj bitwy i sprawdź czy gracz jest zaangażowany
        player_battle = self._detect_player_battles()

        if player_battle:
            # Gracz jest w bitwie - uruchom tactical combat!
            print("⚔️ BITWA! Przygotuj się do walki taktycznej...")
            self._start_tactical_battle(player_battle)
            # Przerwij end_turn - zostanie wznowiony po zakończeniu bitwy
            return

        # Jeśli gracz nie jest w bitwie, przetwórz wszystkie bitwy normalnie (AI vs AI)
        combat_stats = self.combat_manager.process_combat_turn(self.ships, self.empires)

        # Zapisz bitwy dla UI
        self.last_turn_battles = combat_stats['results']

        # Wyświetl informacje o bitwach
        if combat_stats['battles_resolved'] > 0:
            print(f"⚔️ Rozwiązano {combat_stats['battles_resolved']} bitew!")
            print(f"   Zniszczono {combat_stats['total_ships_destroyed']} statków")

            # Generuj efekty wizualne dla każdej bitwy
            for result in combat_stats['results']:
                # Dodaj eksplozje dla zniszczonych statków
                # (używamy pozycji ocalałych statków jako aproksymacji pola bitwy)
                all_survivors = result.attacker_survivors + result.defender_survivors

                if all_survivors:
                    # Pozycja bitwy (średnia pozycja ocalałych)
                    avg_x = sum(s.x for s in all_survivors) / len(all_survivors)
                    avg_y = sum(s.y for s in all_survivors) / len(all_survivors)
                else:
                    # Jeśli wszyscy zginęli, użyj pozycji z pierwszego atakującego
                    # (nie mamy już dostępu do statków, więc używamy domyślnej)
                    avg_x = 0
                    avg_y = 0

                # Dodaj eksplozje dla zniszczonych statków
                total_destroyed = result.attacker_ships_destroyed + result.defender_ships_destroyed
                for i in range(total_destroyed):
                    # Losowa pozycja wokół centrum bitwy
                    offset_x = random.uniform(-50, 50)
                    offset_y = random.uniform(-50, 50)
                    self.combat_effects.add_explosion(avg_x + offset_x, avg_y + offset_y, size=40)

                # Dodaj lasery między statkami (symulacja ataków)
                # Połącz atakujących z obrońcami
                attackers = result.attacker_survivors[:3]  # Max 3 dla wydajności
                defenders = result.defender_survivors[:3]

                for attacker in attackers:
                    if defenders:
                        target = random.choice(defenders)
                        # Kolor lasera zależy od imperium
                        laser_color = next((e.color for e in self.empires if e.id == attacker.owner_id), (100, 200, 255))
                        self.combat_effects.add_laser_beam(
                            attacker.x, attacker.y,
                            target.x, target.y,
                            color=laser_color
                        )

            # Wyświetl szczegóły bitew dla gracza
            for result in combat_stats['results']:
                if result.attacker_empire_id == self.player_empire.id or result.defender_empire_id == self.player_empire.id:
                    attacker_name = next((e.name for e in self.empires if e.id == result.attacker_empire_id), "Nieznany")
                    defender_name = next((e.name for e in self.empires if e.id == result.defender_empire_id), "Nieznany")

                    if result.attacker_won:
                        winner = attacker_name
                        loser = defender_name
                    else:
                        winner = defender_name
                        loser = attacker_name

                    print(f"   🏆 {winner} pokonał {loser} ({result.rounds} rund)")
                    print(f"      Straty: {result.attacker_ships_destroyed} vs {result.defender_ships_destroyed}")

        # 1.7. AI podejmuje decyzje
        for empire_id, ai_controller in self.ai_controllers.items():
            ai_controller.make_turn_decisions(self.ships)

        # 2. Aktualizacja zasobów imperii (przed wzrostem populacji!)
        self._update_empire_resources()

        # 3. Aplikuj efekty deficytu (głód, blackout)
        self._apply_deficit_effects()

        # 4. Przetwarzanie badań
        for empire in self.empires:
            if empire.current_research and empire.total_science > 0:
                completed = empire.add_research_points(empire.total_science)
                if completed:
                    tech_id = list(empire.researched_technologies)[-1]  # Ostatnio odkryta
                    tech = TECHNOLOGIES.get(tech_id)
                    if tech and empire.is_player:
                        print(f"🔬 Odkryto technologię: {tech.name}!")
                        print(f"   {tech.description}")
                        if tech.unlocks_buildings:
                            buildings_names = [BUILDINGS[bid].name for bid in tech.unlocks_buildings]
                            print(f"   Odblokowane budynki: {', '.join(buildings_names)}")
                        if tech.unlocks_planet_types:
                            types_names = [pt for pt in tech.unlocks_planet_types]
                            print(f"   Odblokowane typy planet: {', '.join(types_names)}")

        # 5. Wzrost populacji i produkcja na planetach
        for system in self.galaxy.systems:
            for planet in system.planets:
                if planet.is_colonized:
                    planet.grow_population()

                    # Przetwórz produkcję
                    completed_item = planet.process_production()
                    if completed_item:
                        if completed_item.item_type == "ship" and completed_item.ship_type:
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

                        elif completed_item.item_type == "building" and completed_item.building_id:
                            # Stwórz nowy budynek
                            building_def = BUILDINGS.get(completed_item.building_id)
                            if building_def:
                                new_building = Building(
                                    building_id=building_def.id,
                                    name=building_def.name,
                                    production_bonus=building_def.production_bonus,
                                    science_bonus=building_def.science_bonus,
                                    food_bonus=building_def.food_bonus,
                                    energy_bonus=building_def.energy_bonus,
                                    production_flat=building_def.production_flat,
                                    science_flat=building_def.science_flat,
                                    food_flat=building_def.food_flat,
                                    energy_flat=building_def.energy_flat,
                                    upkeep_energy=building_def.upkeep_energy,
                                )
                                planet.add_building(new_building)
                                print(f"🏗️ {building_def.name} zbudowany na {planet.name}!")

    def _update_empire_resources(self):
        """Aktualizuj całkowite zasoby wszystkich imperiów"""
        for empire in self.empires:
            total_prod = 0.0
            total_sci = 0.0
            total_food = 0.0
            total_energy = 0.0
            total_population = 0.0

            # Sumuj z wszystkich planet
            for system in self.galaxy.systems:
                for planet in system.planets:
                    if planet.owner_id == empire.id:
                        total_prod += planet.calculate_production()
                        total_sci += planet.calculate_science()
                        total_food += planet.calculate_food()
                        total_energy += planet.calculate_energy()
                        total_population += planet.population

            # Oblicz zużycie zasobów
            food_upkeep = total_population * POPULATION_FOOD_UPKEEP
            energy_upkeep = total_population * POPULATION_ENERGY_UPKEEP

            # Dodaj zużycie energii przez budynki
            building_energy_upkeep = 0.0
            for system in self.galaxy.systems:
                for planet in system.planets:
                    if planet.owner_id == empire.id:
                        for building in planet.buildings:
                            building_energy_upkeep += building.upkeep_energy
            energy_upkeep += building_energy_upkeep
            # TODO: Dodać zużycie energii przez statki

            # Oblicz bilans (produkcja - zużycie)
            food_balance = total_food - food_upkeep
            energy_balance = total_energy - energy_upkeep

            # Zapisz do imperium
            empire.total_production = total_prod
            empire.total_science = total_sci
            empire.total_food = total_food
            empire.total_energy = total_energy
            empire.food_upkeep = food_upkeep
            empire.energy_upkeep = energy_upkeep
            empire.food_balance = food_balance
            empire.energy_balance = energy_balance

            # Sprawdź deficyty
            empire.has_starvation = food_balance < 0
            empire.has_blackout = energy_balance < 0

    def _apply_deficit_effects(self):
        """Aplikuj efekty deficytu zasobów (jak w Stellaris)"""
        for empire in self.empires:
            empire_name = empire.name if not empire.is_player else "Twoje imperium"

            # EFEKT 1: Głód (brak żywności)
            if empire.has_starvation:
                penalty_rate = DEFICIT_EFFECTS['food']['penalty_per_turn']
                planets_affected = []

                # Populacja umiera na wszystkich planetach
                for system in self.galaxy.systems:
                    for planet in system.planets:
                        if planet.owner_id == empire.id and planet.population > 0:
                            # Spadek populacji o 5% co turę
                            population_loss = planet.population * penalty_rate
                            planet.population = max(1.0, planet.population - population_loss)
                            planets_affected.append(planet.name)

                if empire.is_player:
                    print(f"⚠️ GŁÓD! Brak żywności ({empire.food_balance:.1f})")
                    print(f"   Populacja wymiera na {len(planets_affected)} planetach!")
                    print(f"   Straty: {penalty_rate*100:.0f}% populacji co turę")

            # EFEKT 2: Blackout (brak energii)
            if empire.has_blackout:
                # Kary do produkcji i nauki
                penalty_prod = DEFICIT_EFFECTS['energy']['penalty_production']
                penalty_sci = DEFICIT_EFFECTS['energy']['penalty_science']

                # Kary są aplikowane automatycznie w następnej turze
                # (bo _update_empire_resources() jest wywoływane przed produkcją)

                if empire.is_player:
                    print(f"⚠️ BLACKOUT! Brak energii ({empire.energy_balance:.1f})")
                    print(f"   Produkcja: -{penalty_prod*100:.0f}%, Nauka: -{penalty_sci*100:.0f}%")
                    print(f"   Buduj elektrownie lub zmniejsz populację!")

    def _detect_player_battles(self):
        """
        Wykryj bitwy z udziałem gracza
        Returns: dict z info o bitwie lub None
        """
        from src.combat.battle import Battle

        # Zbuduj słownik relacji
        relations = {}
        for i, emp1 in enumerate(self.empires):
            for j, emp2 in enumerate(self.empires):
                if i != j:
                    relation_key = (min(emp1.id, emp2.id), max(emp1.id, emp2.id))
                    relations[relation_key] = emp1.get_relation(emp2.id)

        # Wykryj wszystkie bitwy
        detected_battles = Battle.detect_battles(self.ships, relations)

        # Znajdź pierwszą bitwę gracza
        for battle in detected_battles:
            if (battle.attacker_empire_id == self.player_empire.id or
                battle.defender_empire_id == self.player_empire.id):
                # Znaleźliśmy bitwę gracza!
                return {
                    'attacker_empire_id': battle.attacker_empire_id,
                    'defender_empire_id': battle.defender_empire_id,
                    'attacker_ships': battle.attacker_ships,
                    'defender_ships': battle.defender_ships,
                    'location': battle.location
                }

        return None

    def _start_tactical_battle(self, battle_info):
        """Uruchom tactical combat dla gracza"""
        # Stwórz tactical battle
        self.tactical_battle = TacticalBattle(
            attacker_empire_id=battle_info['attacker_empire_id'],
            defender_empire_id=battle_info['defender_empire_id'],
            attacker_ships=battle_info['attacker_ships'],
            defender_ships=battle_info['defender_ships'],
            location=battle_info['location'],
            player_empire_id=self.player_empire.id
        )

        # Stwórz battle screen
        self.battle_screen = BattleScreen(self.screen, self.tactical_battle)

        # Rozpocznij tury AI jeśli to konieczne
        self.battle_screen._process_ai_turns()

    def _end_tactical_battle(self):
        """Zakończ tactical combat i kontynuuj end_turn"""
        if not self.battle_screen or not self.tactical_battle:
            return

        # Pobierz wynik
        result = self.battle_screen.battle_result or self.tactical_battle._create_result()

        # Zastosuj wynik bitwy - usuń zniszczone statki
        for ship in result.attacker_survivors + result.defender_survivors:
            if not ship.is_alive:
                if ship in self.ships:
                    self.ships.remove(ship)
                if ship in self.selected_ships:
                    self.selected_ships.remove(ship)

        # Dodaj do historii bitew
        self.last_turn_battles = [result]

        # Wyświetl wynik
        if result.attacker_won:
            winner_name = next((e.name for e in self.empires if e.id == result.attacker_empire_id), "Nieznany")
            loser_name = next((e.name for e in self.empires if e.id == result.defender_empire_id), "Nieznany")
        else:
            winner_name = next((e.name for e in self.empires if e.id == result.defender_empire_id), "Nieznany")
            loser_name = next((e.name for e in self.empires if e.id == result.attacker_empire_id), "Nieznany")

        print(f"   🏆 {winner_name} pokonał {loser_name} ({result.rounds} rund)")
        print(f"      Straty: {result.attacker_ships_destroyed} vs {result.defender_ships_destroyed}")

        # Wyczyść tactical combat state
        self.tactical_battle = None
        self.battle_screen = None

        # Kontynuuj resztę end_turn - przetwórz pozostałe bitwy AI vs AI
        self._continue_end_turn_after_battle()

    def _continue_end_turn_after_battle(self):
        """Kontynuuj end_turn po zakończeniu tactical combat"""
        # Przetwórz pozostałe bitwy (AI vs AI) - bez gracza
        combat_stats = self.combat_manager.process_combat_turn(self.ships, self.empires)

        if combat_stats['battles_resolved'] > 0:
            print(f"⚔️ Rozwiązano {combat_stats['battles_resolved']} dodatkowych bitew AI!")

        # Kontynuuj z AI, wzrostem populacji etc.
        # (kod skopiowany z oryginalnego end_turn - linie ~736+)

        # 1.7. AI podejmuje decyzje
        for empire_id, ai_controller in self.ai_controllers.items():
            ai_controller.make_turn_decisions(self.ships)

        # 2. Aktualizacja zasobów imperii
        self._update_empire_resources()

        # 3. Aplikuj efekty deficytu
        self._apply_deficit_effects()

        # 4. Przetwarzanie badań
        for empire in self.empires:
            if empire.current_research and empire.total_science > 0:
                completed = empire.add_research_points(empire.total_science)
                if completed:
                    tech_id = list(empire.researched_technologies)[-1]
                    tech = TECHNOLOGIES.get(tech_id)
                    if tech and empire.is_player:
                        print(f"🔬 Odkryto technologię: {tech.name}!")

        # 5. Wzrost populacji i produkcja
        self._process_planet_production()

    def _process_planet_production(self):
        """Przetwórz produkcję na wszystkich planetach (wydzielone z end_turn)"""
        for system in self.galaxy.systems:
            for planet in system.planets:
                if planet.is_colonized:
                    planet.grow_population()

                    # Przetwórz produkcję
                    completed_item = planet.process_production()
                    if completed_item:
                        if completed_item.item_type == "ship" and completed_item.ship_type:
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

                            empire = next((e for e in self.empires if e.id == planet.owner_id), None)
                            if empire and empire.is_player:
                                print(f"✓ {completed_item.ship_type.value} #{new_ship.id} wyprodukowany w systemie {system.name}!")
                        elif completed_item.item_type == "building" and completed_item.building_id:
                            # Dodaj budynek do planety
                            building_def = BUILDINGS.get(completed_item.building_id)
                            if building_def:
                                from src.models.planet import Building
                                new_building = Building(
                                    building_id=building_def.id,
                                    name=building_def.name,
                                    production_bonus=building_def.production_bonus,
                                    science_bonus=building_def.science_bonus,
                                    food_bonus=building_def.food_bonus,
                                    energy_bonus=building_def.energy_bonus,
                                    upkeep_energy=building_def.upkeep_energy
                                )
                                planet.add_building(new_building)

                                empire = next((e for e in self.empires if e.id == planet.owner_id), None)
                                if empire and empire.is_player:
                                    print(f"🏗️ {building_def.name} zbudowany na {planet.name}!")

    def render(self, dt=0.016):
        """Renderuj grę"""
        # Jeśli w tactical combat, renderuj tylko battle screen
        if self.battle_screen:
            self.battle_screen.render()
            pygame.display.flip()
            return

        self.renderer.clear()
        self.renderer.draw_background(dt)

        # Przygotuj kolory imperiów
        empire_colors = {empire.id: empire.color for empire in self.empires}

        # Rysuj galaktykę
        if self.galaxy:
            self.renderer.draw_galaxy(self.galaxy, self.player_empire.id, empire_colors)

        # Rysuj statki
        self.renderer.draw_ships(self.ships, empire_colors, self.selected_ships)

        # Rysuj efekty walki (lasery, eksplozje)
        self.combat_effects.draw(self.screen, self.renderer.camera)

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

        # Rysuj ekran badań na wierzchu (jeśli otwarty)
        if self.research_screen:
            self.research_screen.draw(self.screen)

        pygame.display.flip()

    def _render_ui(self):
        """Rysuj interfejs użytkownika"""
        # Panel informacyjny
        self.info_panel.draw(self.screen, self.renderer.font_medium)

        # === SEKCJA 1: HEADER (Tura, Imperium) ===
        y_header = 50
        draw_text(self.screen, f"Tura: {self.current_turn}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_header,
                 self.renderer.font_small, Colors.UI_TEXT)

        draw_text(self.screen, f"Imperium: {self.player_empire.name}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_header + 20,
                 self.renderer.font_small, Colors.UI_TEXT)

        # === SEKCJA 2: ZASOBY IMPERIUM ===
        y_resources = 100
        draw_text(self.screen, "═══ Zasoby ═══",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_resources,
                 self.renderer.font_small, Colors.UI_HIGHLIGHT)

        # Produkcja (minerały)
        draw_text(self.screen, f"🔨 Produkcja: {self.player_empire.total_production:.1f}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_resources + 22,
                 self.renderer.font_small, Colors.UI_TEXT)

        # Nauka
        draw_text(self.screen, f"🔬 Nauka: {self.player_empire.total_science:.1f}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_resources + 42,
                 self.renderer.font_small, Colors.UI_TEXT)

        # Żywność (z bilansem)
        food_color = Colors.UI_TEXT
        if self.player_empire.has_starvation:
            food_color = (255, 100, 100)  # Czerwony przy głodzie
        elif self.player_empire.food_balance < 5:
            food_color = (255, 200, 100)  # Pomarańczowy przy niskim bilansie

        food_text = f"🌾 Żywność: {self.player_empire.food_balance:+.1f}"
        if self.player_empire.has_starvation:
            food_text += " ⚠️GŁÓD"
        draw_text(self.screen, food_text,
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_resources + 62,
                 self.renderer.font_small, food_color)

        # Energia (z bilansem)
        energy_color = Colors.UI_TEXT
        if self.player_empire.has_blackout:
            energy_color = (255, 100, 100)  # Czerwony przy blackoucie
        elif self.player_empire.energy_balance < 5:
            energy_color = (255, 200, 100)  # Pomarańczowy przy niskim bilansie

        energy_text = f"⚡ Energia: {self.player_empire.energy_balance:+.1f}"
        if self.player_empire.has_blackout:
            energy_text += " ⚠️BRAK"
        draw_text(self.screen, energy_text,
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_resources + 82,
                 self.renderer.font_small, energy_color)

        # === SEKCJA 3: BADANIA I EKSPLORACJA ===
        y_research = 210
        if self.player_empire.current_research:
            current_tech = TECHNOLOGIES.get(self.player_empire.current_research)
            if current_tech:
                draw_text(self.screen, "═══ Badania ═══",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research,
                         self.renderer.font_small, Colors.UI_HIGHLIGHT)

                tech_name = current_tech.name[:25]  # Obetnij długie nazwy
                draw_text(self.screen, f"🔬 {tech_name}",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research + 20,
                         self.renderer.font_small, Colors.UI_TEXT)

                # Mini progress bar
                progress = self.player_empire.research_progress / current_tech.cost
                bar_width = PANEL_WIDTH - 2 * PANEL_PADDING
                bar_height = 12
                bar_x = WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING
                bar_y = y_research + 38

                # Tło
                pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
                # Wypełnienie
                fill_width = int(bar_width * progress)
                pygame.draw.rect(self.screen, Colors.UI_HIGHLIGHT, (bar_x, bar_y, fill_width, bar_height))
                # Obramowanie
                pygame.draw.rect(self.screen, Colors.LIGHT_GRAY, (bar_x, bar_y, bar_width, bar_height), 1)

                progress_text = f"  {progress*100:.0f}% ({self.player_empire.research_progress:.0f}/{current_tech.cost})"
                draw_text(self.screen, progress_text,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research + 53,
                         self.renderer.font_small, Colors.LIGHT_GRAY)
        else:
            draw_text(self.screen, "R - badania",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research,
                     self.renderer.font_small, Colors.LIGHT_GRAY)

        # Statystyki eksploracji
        explored_count = len(self.player_empire.explored_systems)
        total_systems = len(self.galaxy.systems)
        unexplored = total_systems - explored_count
        draw_text(self.screen, f"Systemy: {explored_count}/{total_systems}",
                 WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research + 80,
                 self.renderer.font_small, Colors.LIGHT_GRAY)

        # Hint o nieodkrytych systemach (na początku gry)
        if self.current_turn < 3 and unexplored > 0:
            hint_color = (100, 150, 200)  # Niebieski hint
            draw_text(self.screen, f"💡 {unexplored} szare kropki",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research + 100,
                     self.renderer.font_small, hint_color)
            draw_text(self.screen, "   to nieodkryte systemy!",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_research + 118,
                     self.renderer.font_small, hint_color)

        # === SEKCJA 3.5: BITWY (jeśli były) ===
        y_battles = 280
        if self.last_turn_battles:
            draw_text(self.screen, "═══ Bitwy ═══",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_battles,
                     self.renderer.font_small, Colors.UI_HIGHLIGHT)

            y_battle_item = y_battles + 20
            for result in self.last_turn_battles[:2]:  # Max 2 bitwy (żeby się zmieściło)
                # Sprawdź czy gracz uczestniczył
                player_involved = (result.attacker_empire_id == self.player_empire.id or
                                 result.defender_empire_id == self.player_empire.id)

                if player_involved:
                    # Nazwy imperiów
                    attacker_name = next((e.name for e in self.empires if e.id == result.attacker_empire_id), "?")
                    defender_name = next((e.name for e in self.empires if e.id == result.defender_empire_id), "?")

                    # Skróć nazwy
                    attacker_short = attacker_name[:10]
                    defender_short = defender_name[:10]

                    # Kto wygrał
                    if result.attacker_won:
                        winner_short = attacker_short
                        battle_color = Colors.UI_TEXT if result.attacker_empire_id == self.player_empire.id else (255, 100, 100)
                    else:
                        winner_short = defender_short
                        battle_color = Colors.UI_TEXT if result.defender_empire_id == self.player_empire.id else (255, 100, 100)

                    # Rysuj
                    battle_text = f"⚔️ {attacker_short} vs {defender_short}"
                    draw_text(self.screen, battle_text,
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_battle_item,
                             self.renderer.font_small, battle_color)

                    result_text = f"   🏆 {winner_short} (-{result.attacker_ships_destroyed}/{result.defender_ships_destroyed})"
                    draw_text(self.screen, result_text,
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_battle_item + 15,
                             self.renderer.font_small, Colors.LIGHT_GRAY)

                    y_battle_item += 40

        # === SEKCJA 4: GŁÓWNA (Statki/Systemy) - największa sekcja ===
        y_main = 380  # Przesunięte w dół o 30px dla sekcji bitew

        # Informacje o wybranych statkach
        if self.selected_ships:
            draw_text(self.screen, f"Wybrane statki: {len(self.selected_ships)}",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_main,
                     self.renderer.font_small, Colors.UI_HIGHLIGHT)

            y_ship = y_main + 25
            for ship in self.selected_ships[:5]:  # Pokaż max 5 statków
                ship_info = f"  {ship.ship_type.value}"
                if ship.is_moving:
                    ship_info += " (w ruchu)"
                draw_text(self.screen, ship_info,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship,
                         self.renderer.font_small, Colors.UI_TEXT)
                y_ship += 25

            if len(self.selected_ships) > 5:
                draw_text(self.screen, f"  ...i {len(self.selected_ships) - 5} więcej",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship,
                         self.renderer.font_small, Colors.LIGHT_GRAY)
                y_ship += 25

            # Hint dla statku kolonistów
            if len(self.selected_ships) == 1 and self.selected_ships[0].ship_type == ShipType.COLONY_SHIP:
                colony_ship = self.selected_ships[0]
                y_ship += 5

                if colony_ship.is_moving:
                    # Statek w ruchu
                    draw_text(self.screen, "⏳ W drodze do kolonizacji...",
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship,
                             self.renderer.font_small, Colors.LIGHT_GRAY)
                elif colony_ship.target_system_id is not None:
                    # Statek dotarł do systemu
                    target_system = self.galaxy.find_system_by_id(colony_ship.target_system_id)
                    if target_system:
                        colonizable = target_system.get_colonizable_planets(COLONIZABLE_PLANET_TYPES)
                        if colonizable:
                            draw_text(self.screen, "C - kolonizuj planetę",
                                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship,
                                     self.renderer.font_small, Colors.UI_HIGHLIGHT)
                            draw_text(self.screen, f"  ({len(colonizable)} planet dostępnych)",
                                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship + 20,
                                     self.renderer.font_small, Colors.LIGHT_GRAY)
                        else:
                            draw_text(self.screen, "⚠ Brak planet do kolonizacji",
                                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship,
                                     self.renderer.font_small, (200, 100, 100))
                else:
                    # Statek nie wysłany nigdzie
                    draw_text(self.screen, "PPM na system - wyślij",
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_ship,
                             self.renderer.font_small, Colors.LIGHT_GRAY)

        # Informacje o wybranym systemie
        elif self.selected_system:
            draw_text(self.screen, "Wybrany system:",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_main,
                     self.renderer.font_small, Colors.UI_HIGHLIGHT)

            draw_text(self.screen, self.selected_system.name,
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_main + 25,
                     self.renderer.font_small, Colors.WHITE)

            draw_text(self.screen, f"Typ: {self.selected_system.star_type.value}",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_main + 45,
                     self.renderer.font_small, Colors.UI_TEXT)

            draw_text(self.screen, f"Planet: {len(self.selected_system.planets)}",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_main + 65,
                     self.renderer.font_small, Colors.UI_TEXT)

            # Lista planet (max 4 żeby zmieścić)
            y_planet = y_main + 85
            for i, planet in enumerate(self.selected_system.planets[:4]):
                # Ikona planety (kolorowe kółko)
                planet_icon_x = WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 5
                planet_icon_y = y_planet + 7
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
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 15, y_planet,
                         self.renderer.font_small, text_color)
                y_planet += 20

            # Podpowiedź o zarządzaniu planetami
            player_planets = self.selected_system.get_colonized_planets(self.player_empire.id)
            if player_planets:
                y_planet += 5
                hint = f"P lub 1-{len(player_planets)} - zarządzaj planetą"
                draw_text(self.screen, hint,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_planet,
                         self.renderer.font_small, Colors.LIGHT_GRAY)
                y_planet += 20

            # Lista statków gracza w tym systemie (max 3)
            system_ships = [s for s in self.ships if s.owner_id == self.player_empire.id and
                           abs(s.x - self.selected_system.x) < 50 and
                           abs(s.y - self.selected_system.y) < 50]

            if system_ships:
                y_planet += 5
                draw_text(self.screen, f"Twoje statki ({len(system_ships)}):",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_planet,
                         self.renderer.font_small, Colors.UI_HIGHLIGHT)
                y_planet += 20

                for i, ship in enumerate(system_ships[:3]):  # Max 3 żeby zmieścić
                    # Ikona statku (trójkąt)
                    ship_icon_x = WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 5
                    ship_icon_y = y_planet + 7
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
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 15, y_planet,
                             self.renderer.font_small, text_color)
                    y_planet += 20

                if len(system_ships) > 3:
                    draw_text(self.screen, f"  ...i {len(system_ships) - 3} więcej",
                             WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_planet,
                             self.renderer.font_small, Colors.LIGHT_GRAY)
                    y_planet += 18

                # Podpowiedź
                draw_text(self.screen, "Shift+LPM - wybierz następny",
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_planet,
                         self.renderer.font_small, Colors.LIGHT_GRAY)

        # Przycisk zakończenia tury
        self.end_turn_button.draw(self.screen, self.renderer.font_medium)

        # === SEKCJA 5: INSTRUKCJE (na samym dole) ===
        y_bottom = WINDOW_HEIGHT - 80

        if self.show_help:
            # Pełna lista instrukcji (gdy gracz nacisnął H)
            separator_y = y_bottom - 15
            pygame.draw.line(self.screen, Colors.UI_BORDER,
                           (WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, separator_y),
                           (WINDOW_WIDTH - PANEL_PADDING, separator_y), 1)

            y_help = y_bottom - 145
            draw_text(self.screen, "═══ STEROWANIE ═══",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_help,
                     self.renderer.font_small, Colors.UI_HIGHLIGHT)

            instructions = [
                ("WSAD/Strzałki", "ruch kamery"),
                ("PPM przeciągnij", "ruch mapy"),
                ("Scroll", "zoom"),
                ("LPM", "wybierz statek/system"),
                ("Shift+LPM", "dodaj do wyboru"),
                ("PPM klik", "rozkaz ruchu"),
                ("C", "kolonizuj planetę"),
                ("P", "zarządzaj planetą"),
                ("R", "badania"),
                ("Spacja", "zakończ turę"),
                ("H", "ukryj pomoc"),
            ]

            y_help += 20
            for key, desc in instructions:
                text = f"{key:14} - {desc}"
                draw_text(self.screen, text,
                         WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING + 5, y_help,
                         self.renderer.font_small, Colors.LIGHT_GRAY)
                y_help += 15
        else:
            # Tylko krótka podpowiedź
            draw_text(self.screen, "H - pokaż pomoc • Spacja - następna tura",
                     WINDOW_WIDTH - PANEL_WIDTH + PANEL_PADDING, y_bottom,
                     self.renderer.font_small, Colors.LIGHT_GRAY)
