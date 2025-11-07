"""
Zaawansowany renderer gwiazd z efektami corona, flares i glow
"""
import pygame
import math
import random
from src.config import StarType


class StarRenderer:
    """
    Renderer dla realistycznych gwiazd z efektami świetlnymi
    """

    # Paleta kolorów dla różnych typów gwiazd
    STAR_PALETTES = {
        StarType.YELLOW: {
            'core': (255, 255, 200),      # Jasne żółte jądro
            'corona': (255, 200, 100),    # Pomarańczowa corona
            'flare': (255, 220, 150),     # Jasne flary
        },
        StarType.WHITE: {
            'core': (255, 255, 255),      # Białe jądro
            'corona': (200, 220, 255),    # Niebiesko-biała corona
            'flare': (220, 230, 255),     # Jasne białe flary
        },
        StarType.RED: {
            'core': (255, 150, 100),      # Czerwone jądro
            'corona': (255, 100, 80),     # Czerwona corona
            'flare': (255, 120, 100),     # Czerwone flary
        },
        StarType.BLUE: {
            'core': (150, 200, 255),      # Niebieskie jądro
            'corona': (100, 150, 255),    # Niebieska corona
            'flare': (180, 200, 255),     # Niebieskie flary
        },
    }

    @staticmethod
    def draw_star_advanced(screen: pygame.Surface, x: int, y: int,
                          radius: int, star_type: StarType,
                          pulse_factor: float = 1.0):
        """
        Rysuj gwiazdę z zaawansowanymi efektami

        Args:
            screen: Powierzchnia pygame do rysowania
            x, y: Pozycja środka gwiazdy
            radius: Promień gwiazdy
            star_type: Typ gwiazdy (określa kolory)
            pulse_factor: Współczynnik pulsowania (0.95 - 1.05)
        """
        palette = StarRenderer.STAR_PALETTES.get(star_type,
                                                 StarRenderer.STAR_PALETTES[StarType.YELLOW])

        # Zastosuj pulsowanie
        effective_radius = int(radius * pulse_factor)

        # 1. CORONA (wielowarstwowa poświata)
        StarRenderer._draw_corona(screen, x, y, effective_radius, palette['corona'])

        # 2. CORE (jasne jądro z gradientem)
        StarRenderer._draw_core(screen, x, y, effective_radius, palette['core'])

        # 3. FLARES (rozbłyski - tylko dla większych gwiazd)
        if radius > 8:
            StarRenderer._draw_flares(screen, x, y, effective_radius, palette['flare'])

        # 4. BRIGHT CENTER (bardzo jasny środek)
        StarRenderer._draw_bright_center(screen, x, y, effective_radius)

    @staticmethod
    def _draw_corona(screen: pygame.Surface, x: int, y: int, radius: int, color: tuple):
        """
        Rysuj wielowarstwową coronę (poświatę wokół gwiazdy)
        """
        # 6 warstw corony o malejącej intensywności
        layers = [
            (radius * 3.0, 15),   # Zewnętrzna - bardzo delikatna
            (radius * 2.5, 25),
            (radius * 2.0, 40),
            (radius * 1.6, 60),
            (radius * 1.3, 80),
            (radius * 1.1, 100),  # Wewnętrzna - najjaśniejsza
        ]

        # Utwórz powierzchnię z alpha dla każdej warstwy
        for layer_radius, alpha in layers:
            if layer_radius < 1:
                continue

            size = int(layer_radius * 2) + 2
            corona_surf = pygame.Surface((size, size), pygame.SRCALPHA)

            # Gradient radialny
            steps = 20
            for i in range(steps, 0, -1):
                step_radius = int((i / steps) * layer_radius)
                step_alpha = int((i / steps) * alpha)

                # Kolor z alpha
                corona_color = (*color, step_alpha)
                pygame.draw.circle(corona_surf, corona_color,
                                 (size // 2, size // 2), step_radius)

            # Rysuj na ekranie
            screen.blit(corona_surf,
                       (x - size // 2, y - size // 2),
                       special_flags=pygame.BLEND_ALPHA_SDL2)

    @staticmethod
    def _draw_core(screen: pygame.Surface, x: int, y: int, radius: int, color: tuple):
        """
        Rysuj jądro gwiazdy z gradientem (jasny środek -> krawędzie)
        """
        # Gradient koncentryczny - 15 warstw
        steps = 15
        for i in range(steps, 0, -1):
            current_radius = int((i / steps) * radius)
            if current_radius < 1:
                current_radius = 1

            # Jasność rośnie do środka (0.5 -> 1.2)
            brightness = 0.5 + (i / steps) * 0.7

            gradient_color = tuple(min(255, int(c * brightness)) for c in color)
            pygame.draw.circle(screen, gradient_color, (x, y), current_radius)

    @staticmethod
    def _draw_flares(screen: pygame.Surface, x: int, y: int, radius: int, color: tuple):
        """
        Rysuj małe rozbłyski (flares) wokół gwiazdy
        """
        # 4-8 flar w losowych pozycjach (ale deterministyczne dla danej pozycji)
        random.seed(hash((x, y)) % 10000)  # Seed bazujący na pozycji
        num_flares = 6

        for i in range(num_flares):
            # Pozycja flary (na krawędzi gwiazdy)
            angle = (i / num_flares) * 2 * math.pi + random.uniform(-0.3, 0.3)
            flare_distance = radius * random.uniform(0.8, 1.2)

            flare_x = x + int(math.cos(angle) * flare_distance)
            flare_y = y + int(math.sin(angle) * flare_distance)

            # Rozmiar flary
            flare_radius = max(2, int(radius * 0.15))

            # Rysuj flarę jako małą poświatę
            flare_surf = pygame.Surface((flare_radius * 4, flare_radius * 4), pygame.SRCALPHA)

            # Gradient radialny dla flary
            for j in range(5, 0, -1):
                step_radius = int((j / 5) * flare_radius * 2)
                step_alpha = int((j / 5) * 80)

                flare_color = (*color, step_alpha)
                pygame.draw.circle(flare_surf, flare_color,
                                 (flare_radius * 2, flare_radius * 2), step_radius)

            screen.blit(flare_surf,
                       (flare_x - flare_radius * 2, flare_y - flare_radius * 2),
                       special_flags=pygame.BLEND_ALPHA_SDL2)

        random.seed()  # Reset seed

    @staticmethod
    def _draw_bright_center(screen: pygame.Surface, x: int, y: int, radius: int):
        """
        Rysuj bardzo jasny środek gwiazdy (efekt bloom)
        """
        # Mały, bardzo jasny punkt w środku
        center_radius = max(1, int(radius * 0.3))

        # Biały bloom
        bloom_surf = pygame.Surface((center_radius * 6, center_radius * 6), pygame.SRCALPHA)

        # 3 warstwy białego bloom
        layers = [
            (center_radius * 2.5, 120),
            (center_radius * 1.5, 180),
            (center_radius * 0.8, 255),
        ]

        for layer_radius, alpha in layers:
            pygame.draw.circle(bloom_surf, (255, 255, 255, alpha),
                             (center_radius * 3, center_radius * 3),
                             int(layer_radius))

        screen.blit(bloom_surf,
                   (x - center_radius * 3, y - center_radius * 3),
                   special_flags=pygame.BLEND_ALPHA_SDL2)

    @staticmethod
    def calculate_pulse_factor(time: float, star_id: int) -> float:
        """
        Oblicz współczynnik pulsowania dla gwiazdy

        Args:
            time: Czas w sekundach (akumulowany)
            star_id: ID gwiazdy (dla unikalnej fazy pulsowania)

        Returns:
            float: Współczynnik w zakresie 0.97 - 1.03
        """
        # Każda gwiazda ma unikalną fazę i częstotliwość pulsowania
        phase_offset = (star_id * 0.7) % (2 * math.pi)
        frequency = 0.5 + (star_id % 10) * 0.05  # 0.5 - 1.0 Hz

        pulse = math.sin(time * frequency + phase_offset)

        # Mapuj na zakres 0.97 - 1.03 (bardzo subtelne pulsowanie)
        return 1.0 + pulse * 0.03
