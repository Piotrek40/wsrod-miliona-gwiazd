"""
Generator tła z gwiazdkami (starfield)
"""
import random
import pygame
from src.config import Colors
from src.graphics.nebula import NebulaGenerator


class Star:
    """Pojedyncza gwiazdka na niebie"""
    def __init__(self, x, y, size, brightness, layer):
        self.x = x
        self.y = y
        self.size = size  # 1-3
        self.brightness = brightness  # 0-255
        self.layer = layer  # 0=daleko (wolno), 1=środek, 2=blisko (szybko)
        self.twinkle_phase = random.uniform(0, 6.28)  # Dla efektu migotania
        self.twinkle_speed = random.uniform(0.5, 2.0)


class Starfield:
    """
    Generator i renderer tła z gwiazdkami
    Tworzy 3 warstwy gwiazdek dla efektu parallax
    """

    def __init__(self, width, height, num_stars=500):
        self.width = width
        self.height = height
        self.stars = []

        # Wygeneruj gwiazdki w 3 warstwach
        self._generate_stars(num_stars)

        # Generuj mgławice (ładne kolorowe chmury w tle!)
        print("Generowanie mgławic... (może chwilę potrwać)")
        self.nebula_layer = NebulaGenerator.create_nebula_layer(width, height, num_nebulae=3)
        print("✓ Mgławice wygenerowane!")

        # Cache dla surface (dla wydajności)
        self.background_surface = None
        self._regenerate_surface()

    def _generate_stars(self, num_stars):
        """Generuj losowe gwiazdki w 3 warstwach"""
        # Warstwa 0: Dalekie gwiazdki (50% wszystkich, małe, ciemne)
        for _ in range(int(num_stars * 0.5)):
            star = Star(
                x=random.randint(0, self.width),
                y=random.randint(0, self.height),
                size=1,
                brightness=random.randint(80, 150),
                layer=0
            )
            self.stars.append(star)

        # Warstwa 1: Średnie gwiazdki (30%, średnie, jaśniejsze)
        for _ in range(int(num_stars * 0.3)):
            star = Star(
                x=random.randint(0, self.width),
                y=random.randint(0, self.height),
                size=random.choice([1, 2]),
                brightness=random.randint(150, 220),
                layer=1
            )
            self.stars.append(star)

        # Warstwa 2: Bliskie gwiazdki (20%, duże, bardzo jasne)
        for _ in range(int(num_stars * 0.2)):
            star = Star(
                x=random.randint(0, self.width),
                y=random.randint(0, self.height),
                size=random.choice([2, 3]),
                brightness=random.randint(200, 255),
                layer=2
            )
            self.stars.append(star)

    def _regenerate_surface(self):
        """Przerenderuj tło do cache surface"""
        self.background_surface = pygame.Surface((self.width, self.height))
        self.background_surface.fill(Colors.BLACK)

        # Rysuj wszystkie gwiazdki
        for star in self.stars:
            color = (star.brightness, star.brightness, star.brightness)

            if star.size == 1:
                # Pojedynczy piksel
                self.background_surface.set_at((int(star.x), int(star.y)), color)
            else:
                # Większa gwiazdka (z lekkim glow)
                pygame.draw.circle(
                    self.background_surface,
                    color,
                    (int(star.x), int(star.y)),
                    star.size
                )

                # Mini-glow dla dużych gwiazdek
                if star.size >= 2:
                    glow_color = (
                        star.brightness // 3,
                        star.brightness // 3,
                        star.brightness // 3
                    )
                    pygame.draw.circle(
                        self.background_surface,
                        glow_color,
                        (int(star.x), int(star.y)),
                        star.size + 1
                    )

    def update(self, dt):
        """
        Aktualizuj gwiazdki (migotanie)
        dt: delta time w sekundach
        """
        for star in self.stars:
            # Efekt migotania (twinkle)
            star.twinkle_phase += dt * star.twinkle_speed

    def draw(self, screen, camera):
        """
        Rysuj starfield z efektem parallax
        screen: Pygame surface
        camera: Camera object (dla parallax)
        """
        # Rysuj czarne tło
        screen.fill(Colors.BLACK)

        # TODO: Parallax - gwiazdki przesuwają się wolniej niż mapa
        # Na razie proste tło statyczne
        screen.blit(self.background_surface, (0, 0))

    def draw_with_parallax(self, screen, camera):
        """
        Rysuj z efektem parallax (gwiazdki przesuwają się wolniej)

        Layer 0 (dalekie): 10% ruchu kamery
        Layer 1 (środek): 30% ruchu kamery
        Layer 2 (bliskie): 60% ruchu kamery
        """
        screen.fill(Colors.BLACK)

        # Rysuj mgławice (bardzo daleko, prawie statyczne - 5% parallax)
        nebula_offset_x = -camera.x * 0.05
        nebula_offset_y = -camera.y * 0.05
        nebula_x = int(nebula_offset_x % self.width)
        nebula_y = int(nebula_offset_y % self.height)
        screen.blit(self.nebula_layer, (nebula_x, nebula_y), special_flags=pygame.BLEND_ADD)

        parallax_factors = {0: 0.1, 1: 0.3, 2: 0.6}

        for star in self.stars:
            # Oblicz offset parallax
            factor = parallax_factors[star.layer]
            offset_x = -camera.x * factor
            offset_y = -camera.y * factor

            # Pozycja na ekranie z parallax
            screen_x = (star.x + offset_x) % self.width
            screen_y = (star.y + offset_y) % self.height

            # Migotanie (twinkle)
            import math
            twinkle = abs(math.sin(star.twinkle_phase))
            brightness = int(star.brightness * (0.7 + twinkle * 0.3))
            color = (brightness, brightness, brightness)

            # Rysuj gwiazdkę
            if star.size == 1:
                screen.set_at((int(screen_x), int(screen_y)), color)
            else:
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), star.size)
