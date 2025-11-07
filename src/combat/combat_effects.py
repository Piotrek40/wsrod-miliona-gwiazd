"""
Efekty wizualne dla systemu walki
"""
import pygame
import math
import random
from typing import Optional
from dataclasses import dataclass


@dataclass
class LaserBeam:
    """Wiązka lasera podczas ataku"""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    color: tuple
    lifetime: float  # Czas życia w sekundach
    age: float = 0.0  # Wiek w sekundach

    def update(self, dt: float) -> bool:
        """
        Aktualizuj laser

        Args:
            dt: Delta time

        Returns:
            bool: True jeśli laser nadal żyje
        """
        self.age += dt
        return self.age < self.lifetime

    def draw(self, screen: pygame.Surface, camera):
        """Rysuj laser"""
        if self.age >= self.lifetime:
            return

        # Przekształć współrzędne świata na ekran
        screen_start_x, screen_start_y = camera.world_to_screen(self.start_x, self.start_y)
        screen_end_x, screen_end_y = camera.world_to_screen(self.end_x, self.end_y)

        # Oblicz alpha (zanika z czasem)
        alpha = int(255 * (1 - self.age / self.lifetime))

        # Stwórz surface z alpha
        # Rysuj grubszą linię dla efektu
        thickness = 3

        # Rysuj poświatę (grubsza, przezroczysta)
        glow_color = (*self.color, max(0, alpha // 2))
        glow_surf = pygame.Surface((abs(int(screen_end_x - screen_start_x)) + 20,
                                    abs(int(screen_end_y - screen_start_y)) + 20),
                                   pygame.SRCALPHA)

        # Pozycja względna na surface
        offset_x = 10
        offset_y = 10
        local_start = (offset_x, offset_y)
        local_end = (int(screen_end_x - screen_start_x) + offset_x,
                     int(screen_end_y - screen_start_y) + offset_y)

        # Rysuj poświatę (grubsza)
        pygame.draw.line(glow_surf, glow_color, local_start, local_end, thickness + 4)

        # Blit na ekran
        screen.blit(glow_surf,
                   (int(screen_start_x) - 10, int(screen_start_y) - 10),
                   special_flags=pygame.BLEND_ALPHA_SDL2)

        # Rysuj główną linię (jasną)
        main_color = (*self.color, alpha)
        main_surf = pygame.Surface((abs(int(screen_end_x - screen_start_x)) + 20,
                                    abs(int(screen_end_y - screen_start_y)) + 20),
                                   pygame.SRCALPHA)

        pygame.draw.line(main_surf, main_color, local_start, local_end, thickness)

        screen.blit(main_surf,
                   (int(screen_start_x) - 10, int(screen_start_y) - 10),
                   special_flags=pygame.BLEND_ALPHA_SDL2)


@dataclass
class Explosion:
    """Eksplozja zniszczonego statku"""
    x: float
    y: float
    max_radius: float
    lifetime: float
    age: float = 0.0
    particles: list = None

    def __post_init__(self):
        """Inicjalizuj cząsteczki eksplozji"""
        if self.particles is None:
            self.particles = []
            # Stwórz 20-30 cząsteczek
            num_particles = random.randint(20, 30)
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(20, 60)  # Prędkość w jednostkach/s
                self.particles.append({
                    'x': self.x,
                    'y': self.y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'color': random.choice([
                        (255, 150, 50),   # Pomarańczowy
                        (255, 100, 50),   # Czerwono-pomarańczowy
                        (255, 200, 100),  # Jasny pomarańczowy
                        (200, 200, 200),  # Szary dym
                    ]),
                    'size': random.randint(2, 5)
                })

    def update(self, dt: float) -> bool:
        """
        Aktualizuj eksplozję

        Args:
            dt: Delta time

        Returns:
            bool: True jeśli eksplozja nadal trwa
        """
        self.age += dt

        # Aktualizuj cząsteczki
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt

            # Spowalniaj cząsteczki (friction)
            particle['vx'] *= 0.98
            particle['vy'] *= 0.98

        return self.age < self.lifetime

    def draw(self, screen: pygame.Surface, camera):
        """Rysuj eksplozję"""
        if self.age >= self.lifetime:
            return

        # Progress eksplozji (0.0 - 1.0)
        progress = self.age / self.lifetime

        # Rysuj cząsteczki
        for particle in self.particles:
            screen_x, screen_y = camera.world_to_screen(particle['x'], particle['y'])

            # Oblicz alpha (zanika z czasem)
            alpha = int(255 * (1 - progress))

            # Rysuj cząsteczkę
            color_with_alpha = (*particle['color'], alpha)

            # Rozmiar maleje z czasem
            size = max(1, int(particle['size'] * (1 - progress * 0.5)))

            # Rysuj małe kółko
            if size > 0:
                particle_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color_with_alpha,
                                 (size * 2, size * 2), size)

                screen.blit(particle_surf,
                           (int(screen_x) - size * 2, int(screen_y) - size * 2),
                           special_flags=pygame.BLEND_ALPHA_SDL2)

        # Dodaj główną falę uderzeniową (pierścień)
        if progress < 0.5:  # Tylko w pierwszej połowie eksplozji
            screen_x, screen_y = camera.world_to_screen(self.x, self.y)

            # Promień rośnie z czasem
            radius = int(self.max_radius * progress * 2)  # *2 bo tylko pierwsza połowa
            alpha = int(255 * (1 - progress * 2))

            if radius > 0 and alpha > 0:
                shockwave_color = (255, 200, 100, alpha)

                shockwave_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(shockwave_surf, shockwave_color,
                                 (radius + 5, radius + 5), radius, 3)

                screen.blit(shockwave_surf,
                           (int(screen_x) - radius - 5, int(screen_y) - radius - 5),
                           special_flags=pygame.BLEND_ALPHA_SDL2)


class CombatEffectsManager:
    """Manager efektów wizualnych dla combat"""

    def __init__(self):
        self.laser_beams: list[LaserBeam] = []
        self.explosions: list[Explosion] = []

    def add_laser_beam(self, start_x: float, start_y: float,
                      end_x: float, end_y: float,
                      color: tuple = (100, 200, 255)):
        """
        Dodaj wiązkę lasera

        Args:
            start_x, start_y: Początek (statek atakujący)
            end_x, end_y: Koniec (statek atakowany)
            color: Kolor lasera
        """
        beam = LaserBeam(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            color=color,
            lifetime=0.3  # 300ms
        )
        self.laser_beams.append(beam)

    def add_explosion(self, x: float, y: float, size: float = 30.0):
        """
        Dodaj eksplozję

        Args:
            x, y: Pozycja eksplozji
            size: Maksymalny promień
        """
        explosion = Explosion(
            x=x,
            y=y,
            max_radius=size,
            lifetime=1.0  # 1 sekunda
        )
        self.explosions.append(explosion)

    def update(self, dt: float):
        """
        Aktualizuj wszystkie efekty

        Args:
            dt: Delta time
        """
        # Aktualizuj lasery
        self.laser_beams = [beam for beam in self.laser_beams if beam.update(dt)]

        # Aktualizuj eksplozje
        self.explosions = [exp for exp in self.explosions if exp.update(dt)]

    def draw(self, screen: pygame.Surface, camera):
        """
        Rysuj wszystkie efekty

        Args:
            screen: Powierzchnia pygame
            camera: Kamera
        """
        # Rysuj lasery
        for beam in self.laser_beams:
            beam.draw(screen, camera)

        # Rysuj eksplozje
        for explosion in self.explosions:
            explosion.draw(screen, camera)

    def clear(self):
        """Wyczyść wszystkie efekty"""
        self.laser_beams.clear()
        self.explosions.clear()
