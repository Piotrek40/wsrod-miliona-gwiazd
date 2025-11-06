"""
Zaawansowany renderer planet z gradientami i efektami
"""
import pygame
import math
from src.config import Colors, PlanetType


class PlanetRenderer:
    """
    Renderer planet z efektami 3D (gradienty, glow, atmosfera)
    """

    @staticmethod
    def draw_planet_advanced(
        screen: pygame.Surface,
        x: int,
        y: int,
        radius: int,
        planet_type: PlanetType,
        base_color: tuple,
        has_atmosphere: bool = False,
        has_rings: bool = False
    ):
        """
        Rysuj planetę z zaawansowanymi efektami

        Args:
            screen: Pygame surface
            x, y: Pozycja centrum planety
            radius: Promień planety
            planet_type: Typ planety (dla specjalnych efektów)
            base_color: Kolor bazowy planety
            has_atmosphere: Czy ma atmosferę (niebieski halo)
            has_rings: Czy ma pierścienie (Saturn style)
        """
        if radius < 2:
            # Za mały - rysuj jak zwykle
            pygame.draw.circle(screen, base_color, (x, y), radius)
            return

        # === 1. GLOW (świecenie wokół planety) ===
        PlanetRenderer._draw_glow(screen, x, y, radius, base_color)

        # === 2. ATMOSFERA (dla ziemiopodobnych) ===
        if has_atmosphere and radius > 5:
            PlanetRenderer._draw_atmosphere(screen, x, y, radius)

        # === 3. GŁÓWNE CIAŁO PLANETY (gradient + pseudo-3D) ===
        PlanetRenderer._draw_planet_sphere(screen, x, y, radius, base_color)

        # === 4. PIERŚCIENIE (dla gazowych olbrzymów) ===
        if has_rings and radius > 8:
            PlanetRenderer._draw_rings(screen, x, y, radius, base_color)

        # === 5. HIGHLIGHT (pseudo-światło) ===
        PlanetRenderer._draw_highlight(screen, x, y, radius)

    @staticmethod
    def _draw_glow(screen, x, y, radius, color):
        """Rysuj glow effect wokół planety"""
        # 3 warstwy glow o różnej intensywności
        glow_layers = [
            (radius + 4, 15),  # Najbliżej, najjaśniejszy
            (radius + 7, 8),   # Środek
            (radius + 10, 4),  # Najdalej, najciemniejszy
        ]

        for glow_radius, alpha in glow_layers:
            if glow_radius < radius:
                continue

            # Kolor glow to przygaszony kolor planety
            glow_color = tuple(int(c * 0.6) for c in color[:3])

            # Rysuj z alpha blending (wymaga surface z alpha)
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*glow_color, alpha), (glow_radius, glow_radius), glow_radius)

            screen.blit(glow_surface, (x - glow_radius, y - glow_radius), special_flags=pygame.BLEND_ALPHA_SDL2)

    @staticmethod
    def _draw_atmosphere(screen, x, y, radius):
        """Rysuj atmosferę (niebieski halo dla ziemiopodobnych)"""
        atmo_radius = radius + 2
        atmo_color = (100, 150, 255)  # Niebieski

        # 2 warstwy atmosfery
        for offset, alpha in [(2, 30), (3, 15)]:
            atmo_surface = pygame.Surface((atmo_radius * 2 + offset, atmo_radius * 2 + offset), pygame.SRCALPHA)
            pygame.draw.circle(
                atmo_surface,
                (*atmo_color, alpha),
                (atmo_radius + offset // 2, atmo_radius + offset // 2),
                atmo_radius + offset // 2
            )
            screen.blit(atmo_surface, (x - atmo_radius - offset // 2, y - atmo_radius - offset // 2), special_flags=pygame.BLEND_ALPHA_SDL2)

    @staticmethod
    def _draw_planet_sphere(screen, x, y, radius, color):
        """
        Rysuj główne ciało planety z gradientem (pseudo-3D)
        Gradient od ciemnego (góra-lewo) do jasnego (środek) do ciemnego (dół-prawo)
        """
        # Dla małych planet - zwykłe kółko
        if radius < 5:
            pygame.draw.circle(screen, color, (x, y), radius)
            return

        # Rysuj gradient koncentryczny (symulacja kuli)
        # Od centrum (jasne) do krawędzi (ciemne)
        steps = min(radius, 20)  # Max 20 kroków dla wydajności

        for i in range(steps, 0, -1):
            # Oblicz promień tego pierścienia
            current_radius = int((i / steps) * radius)

            # Oblicz kolor z gradientem
            # Centrum: jaśniejsze (1.3x)
            # Krawędzie: ciemniejsze (0.6x)
            factor = 0.6 + (i / steps) * 0.7  # 0.6 -> 1.3

            gradient_color = tuple(min(255, int(c * factor)) for c in color[:3])

            pygame.draw.circle(screen, gradient_color, (x, y), current_radius)

    @staticmethod
    def _draw_rings(screen, x, y, radius, planet_color):
        """Rysuj pierścienie Saturn-style"""
        # Pierścienie jako elipsy (perspektywa)
        ring_color = tuple(min(255, int(c * 0.8)) for c in planet_color[:3])
        ring_color_dark = tuple(min(255, int(c * 0.5)) for c in planet_color[:3])

        # 2 pierścienie o różnej grubości
        rings = [
            (radius + 6, radius + 10, ring_color),
            (radius + 12, radius + 16, ring_color_dark),
        ]

        for inner, outer, color in rings:
            # Elipsa (płaska perspektywa)
            rect = pygame.Rect(x - outer, y - int(outer * 0.3), outer * 2, int(outer * 0.6))
            pygame.draw.ellipse(screen, color, rect, 2)

            # Cień na pierścieniach (dolna połowa ciemniejsza)
            shadow_rect = pygame.Rect(x - outer, y, outer * 2, int(outer * 0.3))
            pygame.draw.ellipse(screen, tuple(int(c * 0.6) for c in color[:3]), shadow_rect, 2)

    @staticmethod
    def _draw_highlight(screen, x, y, radius):
        """Rysuj highlight (pseudo-światło od góry-lewej)"""
        if radius < 4:
            return

        # Pozycja highlight (przesunięta w górę-lewo)
        highlight_x = x - int(radius * 0.3)
        highlight_y = y - int(radius * 0.3)
        highlight_radius = max(2, int(radius * 0.3))

        # Biały highlight z alpha
        highlight_surface = pygame.Surface((highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surface, (255, 255, 255, 80), (highlight_radius, highlight_radius), highlight_radius)

        screen.blit(highlight_surface, (highlight_x - highlight_radius, highlight_y - highlight_radius), special_flags=pygame.BLEND_ALPHA_SDL2)


def get_planet_render_flags(planet_type: PlanetType) -> tuple[bool, bool]:
    """
    Zwróć flagi renderowania dla danego typu planety

    Returns:
        (has_atmosphere, has_rings)
    """
    # Ziemiopodobne i oceaniczne mają atmosferę
    has_atmosphere = planet_type in [PlanetType.EARTH_LIKE, PlanetType.OCEAN]

    # Gazowe olbrzymy mają pierścienie
    has_rings = planet_type == PlanetType.GAS_GIANT

    return has_atmosphere, has_rings
