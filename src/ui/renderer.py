"""
System renderowania grafiki
"""
import pygame
import random
from typing import Optional
from src.models.galaxy import Galaxy, StarSystem
from src.models.ship import Ship
from src.ui.camera import Camera
from src.config import Colors, WINDOW_WIDTH, WINDOW_HEIGHT, BACKGROUND_STARS


class Renderer:
    """
    Renderer gry - rysuje wszystkie elementy
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.camera = Camera()

        # Generuj tło z gwiazdami
        self.background_stars = self._generate_background_stars()

        # Czcionki
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)

    def _generate_background_stars(self) -> list[tuple[int, int, int]]:
        """Generuj małe gwiazdki w tle dla efektu"""
        stars = []
        for _ in range(BACKGROUND_STARS):
            x = random.randint(0, WINDOW_WIDTH)
            y = random.randint(0, WINDOW_HEIGHT)
            brightness = random.randint(100, 255)
            stars.append((x, y, brightness))
        return stars

    def clear(self):
        """Wyczyść ekran"""
        self.screen.fill(Colors.BLACK)

    def draw_background(self):
        """Rysuj tło z gwiazdkami"""
        for x, y, brightness in self.background_stars:
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color, (x, y), 1)

    def draw_galaxy(self, galaxy: Galaxy, player_empire_id: int, empire_colors: dict[int, tuple]):
        """Rysuj całą galaktykę"""
        for system in galaxy.systems:
            # Sprawdź czy system jest odkryty przez gracza
            if system.is_explored_by(player_empire_id):
                self.draw_star_system(system, empire_colors)
            else:
                # Rysuj jako nieodkryty (mgła wojny)
                self.draw_unexplored_system(system)

    def draw_star_system(self, system: StarSystem, empire_colors: dict[int, tuple]):
        """Rysuj system gwiezdny"""
        # Przekształć współrzędne świata na ekran
        screen_x, screen_y = self.camera.world_to_screen(system.x, system.y)

        # Sprawdź czy system jest widoczny na ekranie
        if not self._is_visible(screen_x, screen_y):
            return

        # Rysuj gwiazdę
        star_radius = int(system.star_size * self.camera.zoom)
        if star_radius < 1:
            star_radius = 1

        pygame.draw.circle(self.screen, system.color, (int(screen_x), int(screen_y)), star_radius)

        # Rysuj nazwę systemu (jeśli zoom wystarczający)
        if self.camera.zoom > 0.7:
            name_surface = self.font_small.render(system.name, True, Colors.WHITE)
            name_rect = name_surface.get_rect(center=(int(screen_x), int(screen_y) + star_radius + 10))
            self.screen.blit(name_surface, name_rect)

        # Rysuj planety ZAWSZE (ale większe przy zoomie)
        self.draw_planets(system, screen_x, screen_y, empire_colors)

    def draw_planets(self, system: StarSystem, center_x: float, center_y: float, empire_colors: dict[int, tuple]):
        """Rysuj planety w systemie - WIDOCZNE ZAWSZE"""
        for planet in system.planets:
            # Pozycja planety względem gwiazdy (mniejsza orbita dla lepszej widoczności)
            orbit_scale = 0.4 if self.camera.zoom < 1.0 else 1.0
            planet_screen_x = center_x + planet.x * self.camera.zoom * orbit_scale
            planet_screen_y = center_y + planet.y * self.camera.zoom * orbit_scale

            # Rozmiar planety (minimalnie 3px żeby było widać)
            base_size = 4 if self.camera.zoom < 1.0 else planet.size
            planet_radius = max(3, int(base_size * self.camera.zoom / 2))

            # Rysuj planetę
            pygame.draw.circle(self.screen, planet.color, (int(planet_screen_x), int(planet_screen_y)), planet_radius)

            # Jeśli skolonizowana, rysuj obramowanie kolorem właściciela
            if planet.is_colonized:
                owner_color = empire_colors.get(planet.owner_id, Colors.WHITE)
                pygame.draw.circle(self.screen, owner_color, (int(planet_screen_x), int(planet_screen_y)), planet_radius + 2, 2)

    def draw_unexplored_system(self, system: StarSystem):
        """Rysuj nieodkryty system (mgła wojny)"""
        screen_x, screen_y = self.camera.world_to_screen(system.x, system.y)

        if not self._is_visible(screen_x, screen_y):
            return

        # Rysuj jako szary punkt
        pygame.draw.circle(self.screen, Colors.FOG_OF_WAR, (int(screen_x), int(screen_y)), 2)

    def draw_ship(self, ship: Ship, empire_color: tuple, is_selected: bool = False):
        """Rysuj statek"""
        screen_x, screen_y = self.camera.world_to_screen(ship.x, ship.y)

        if not self._is_visible(screen_x, screen_y):
            return

        # Rysuj statek jako trójkąt
        size = 8 * self.camera.zoom
        points = [
            (screen_x, screen_y - size),  # Góra
            (screen_x - size/2, screen_y + size/2),  # Lewy dół
            (screen_x + size/2, screen_y + size/2),  # Prawy dół
        ]
        pygame.draw.polygon(self.screen, empire_color, points)

        # Jeśli wybrany, rysuj obramowanie
        if is_selected:
            pygame.draw.circle(self.screen, Colors.WHITE, (int(screen_x), int(screen_y)), int(size * 1.5), 2)

        # Jeśli statek się porusza, rysuj linię do celu
        if ship.is_moving and ship.target_x and ship.target_y:
            target_screen_x, target_screen_y = self.camera.world_to_screen(ship.target_x, ship.target_y)
            pygame.draw.line(self.screen, empire_color, (screen_x, screen_y), (target_screen_x, target_screen_y), 1)

    def draw_ships(self, ships: list[Ship], empires: dict[int, tuple], selected_ships: list[Ship] = None):
        """Rysuj wszystkie statki"""
        if selected_ships is None:
            selected_ships = []

        for ship in ships:
            empire_color = empires.get(ship.owner_id, Colors.WHITE)
            is_selected = ship in selected_ships
            self.draw_ship(ship, empire_color, is_selected)

    def highlight_system(self, system: StarSystem):
        """Podświetl wybrany system"""
        screen_x, screen_y = self.camera.world_to_screen(system.x, system.y)

        if not self._is_visible(screen_x, screen_y):
            return

        radius = int((system.star_size + 5) * self.camera.zoom)
        pygame.draw.circle(self.screen, Colors.UI_HIGHLIGHT, (int(screen_x), int(screen_y)), radius, 2)

    def _is_visible(self, screen_x: float, screen_y: float, margin: float = 50) -> bool:
        """Sprawdź czy punkt jest widoczny na ekranie"""
        return (
            -margin <= screen_x <= WINDOW_WIDTH + margin and
            -margin <= screen_y <= WINDOW_HEIGHT + margin
        )

    def draw_text(self, text: str, x: int, y: int, color: tuple = Colors.UI_TEXT, size: str = "medium"):
        """Rysuj tekst na ekranie"""
        font = self.font_medium
        if size == "small":
            font = self.font_small
        elif size == "large":
            font = self.font_large

        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_fps(self, fps: float):
        """Rysuj FPS w rogu ekranu"""
        fps_text = f"FPS: {int(fps)}"
        self.draw_text(fps_text, 10, 10, Colors.WHITE, "small")
