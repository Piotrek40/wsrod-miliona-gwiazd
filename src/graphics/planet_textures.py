"""
Generator proceduralnych tekstur planet
Tworzy realistyczne tekstury dla różnych typów planet
"""
import numpy as np
import pygame
from src.config import PlanetType
from src.graphics.nebula import NebulaGenerator  # Użyjemy Perlin noise


class PlanetTextureGenerator:
    """
    Generator realistycznych tekstur planet
    """

    # Cache wygenerowanych tekstur (żeby nie generować za każdym razem)
    _texture_cache = {}

    @staticmethod
    def get_or_generate_texture(planet_id: str, planet_type: PlanetType, size: int, seed: int) -> pygame.Surface:
        """
        Pobierz teksturę z cache lub wygeneruj nową

        Args:
            planet_id: Unikalny ID planety
            planet_type: Typ planety
            size: Rozmiar tekstury (diameter w pikselach)
            seed: Seed dla generatora (dla powtarzalności)

        Returns:
            pygame.Surface z teksturą planety
        """
        cache_key = f"{planet_id}_{size}"

        if cache_key not in PlanetTextureGenerator._texture_cache:
            # Generuj nową teksturę
            texture = PlanetTextureGenerator._generate_texture(planet_type, size, seed)
            PlanetTextureGenerator._texture_cache[cache_key] = texture

        return PlanetTextureGenerator._texture_cache[cache_key]

    @staticmethod
    def _generate_texture(planet_type: PlanetType, size: int, seed: int) -> pygame.Surface:
        """Generuj teksturę planety według typu"""
        if size < 16:
            # Za mała - zwróć prosty gradient
            return PlanetTextureGenerator._simple_gradient(size, planet_type)

        # Wybierz generator według typu planety
        if planet_type == PlanetType.EARTH_LIKE:
            return PlanetTextureGenerator._generate_earth_like(size, seed)
        elif planet_type == PlanetType.OCEAN:
            return PlanetTextureGenerator._generate_ocean(size, seed)
        elif planet_type == PlanetType.DESERT:
            return PlanetTextureGenerator._generate_desert(size, seed)
        elif planet_type == PlanetType.ICE:
            return PlanetTextureGenerator._generate_ice(size, seed)
        elif planet_type == PlanetType.ROCK:
            return PlanetTextureGenerator._generate_rock(size, seed)
        elif planet_type == PlanetType.GAS_GIANT:
            return PlanetTextureGenerator._generate_gas_giant(size, seed)
        else:
            return PlanetTextureGenerator._simple_gradient(size, planet_type)

    @staticmethod
    def _simple_gradient(size: int, planet_type: PlanetType) -> pygame.Surface:
        """Prosty gradient dla małych planet"""
        colors = {
            PlanetType.EARTH_LIKE: (60, 120, 180),
            PlanetType.OCEAN: (40, 80, 180),
            PlanetType.DESERT: (200, 150, 80),
            PlanetType.ICE: (200, 220, 255),
            PlanetType.ROCK: (120, 100, 90),
            PlanetType.GAS_GIANT: (180, 150, 120),
        }
        base_color = colors.get(planet_type, (128, 128, 128))

        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        for r in range(size // 2, 0, -1):
            factor = r / (size // 2)
            color = tuple(int(c * factor) for c in base_color)
            pygame.draw.circle(surface, color, (center, center), r)

        return surface

    @staticmethod
    def _generate_earth_like(size: int, seed: int) -> pygame.Surface:
        """
        Generuj ziemiopodobną planetę (kontynenty + oceany + chmury)
        """
        # Kontynenty (Perlin noise)
        continents = NebulaGenerator.perlin_noise_2d((size, size), (6, 6), seed)
        continents = (continents - continents.min()) / (continents.max() - continents.min())

        # Dodatkowy detail (małe wyspy, góry)
        detail = NebulaGenerator.perlin_noise_2d((size, size), (16, 16), seed + 100)
        detail = (detail - detail.min()) / (detail.max() - detail.min())
        continents = continents * 0.8 + detail * 0.2

        # Chmury (osobny layer)
        clouds = NebulaGenerator.perlin_noise_2d((size, size), (12, 12), seed + 200)
        clouds = (clouds - clouds.min()) / (clouds.max() - clouds.min())
        clouds = np.maximum(0, clouds - 0.6)  # Tylko jasne obszary
        clouds = clouds / (clouds.max() + 0.001) if clouds.max() > 0 else clouds

        # Kolory
        water_color = np.array([40, 80, 160])  # Niebieski
        land_color = np.array([80, 140, 60])   # Zielony
        mountain_color = np.array([120, 110, 90])  # Szary
        cloud_color = np.array([255, 255, 255])  # Biały

        # Twórz obraz
        texture = np.zeros((size, size, 4), dtype=np.uint8)

        # Maska kuli (tylko wewnątrz koła)
        y, x = np.ogrid[:size, :size]
        center = size / 2
        mask = (x - center) ** 2 + (y - center) ** 2 <= (size / 2) ** 2

        # Sphere mapping - gradient oświetlenia
        distance = np.sqrt((x - center) ** 2 + (y - center) ** 2)
        # Światło z lewej-góry
        light_x = x - center + size * 0.3
        light_y = y - center + size * 0.3
        light_dist = np.sqrt(light_x ** 2 + light_y ** 2)
        lighting = 1.0 - np.clip(light_dist / (size * 0.7), 0, 1)
        lighting = lighting ** 0.5  # Smooth falloff

        for i in range(size):
            for j in range(size):
                if not mask[i, j]:
                    continue  # Poza kulą

                # Określ typ terenu
                height = continents[i, j]

                if height < 0.35:
                    # Woda (głęboka)
                    color = water_color * 0.7
                elif height < 0.4:
                    # Woda (płytka)
                    color = water_color * 0.9
                elif height < 0.5:
                    # Ląd (niziny)
                    color = land_color
                elif height < 0.7:
                    # Ląd (wyżyny)
                    color = land_color * 1.1
                else:
                    # Góry
                    color = mountain_color

                # Dodaj chmury
                if clouds[i, j] > 0.3:
                    cloud_alpha = clouds[i, j]
                    color = color * (1 - cloud_alpha) + cloud_color * cloud_alpha

                # Aplikuj oświetlenie
                color = color * (0.4 + lighting[i, j] * 0.6)

                texture[i, j, :3] = np.clip(color, 0, 255).astype(np.uint8)
                texture[i, j, 3] = 255  # Pełna nieprzezroczystość

        # Convert to Pygame surface
        texture_transposed = np.transpose(texture, (1, 0, 2))
        surface = pygame.surfarray.make_surface(texture_transposed[:, :, :3])
        surface = surface.convert_alpha()

        return surface

    @staticmethod
    def _generate_ocean(size: int, seed: int) -> pygame.Surface:
        """Generuj oceaniczną planetę (95% woda, małe wyspy)"""
        # Podobnie jak ziemiopodobna, ale więcej wody
        continents = NebulaGenerator.perlin_noise_2d((size, size), (6, 6), seed)
        continents = (continents - continents.min()) / (continents.max() - continents.min())

        # Threshold wyższy = mniej lądu
        continents = continents * 0.6 + 0.2

        texture = np.zeros((size, size, 4), dtype=np.uint8)

        y, x = np.ogrid[:size, :size]
        center = size / 2
        mask = (x - center) ** 2 + (y - center) ** 2 <= (size / 2) ** 2

        # Oświetlenie
        distance = np.sqrt((x - center) ** 2 + (y - center) ** 2)
        light_x = x - center + size * 0.3
        light_y = y - center + size * 0.3
        light_dist = np.sqrt(light_x ** 2 + light_y ** 2)
        lighting = 1.0 - np.clip(light_dist / (size * 0.7), 0, 1)
        lighting = lighting ** 0.5

        water_deep = np.array([20, 60, 140])
        water_shallow = np.array([40, 100, 180])
        land_color = np.array([80, 120, 70])

        for i in range(size):
            for j in range(size):
                if not mask[i, j]:
                    continue

                height = continents[i, j]

                if height < 0.7:
                    # Głęboka woda
                    color = water_deep
                elif height < 0.75:
                    # Płytka woda
                    color = water_shallow
                else:
                    # Małe wyspy
                    color = land_color

                color = color * (0.4 + lighting[i, j] * 0.6)
                texture[i, j, :3] = np.clip(color, 0, 255).astype(np.uint8)
                texture[i, j, 3] = 255

        texture_transposed = np.transpose(texture, (1, 0, 2))
        surface = pygame.surfarray.make_surface(texture_transposed[:, :, :3])
        return surface.convert_alpha()

    @staticmethod
    def _generate_desert(size: int, seed: int) -> pygame.Surface:
        """Generuj pustynną planetę (wydmy, piasek)"""
        # Wydmy (Perlin noise z dużymi formami)
        dunes = NebulaGenerator.perlin_noise_2d((size, size), (4, 4), seed)
        dunes = (dunes - dunes.min()) / (dunes.max() - dunes.min())

        detail = NebulaGenerator.perlin_noise_2d((size, size), (12, 12), seed + 50)
        detail = (detail - detail.min()) / (detail.max() - detail.min())

        texture = np.zeros((size, size, 4), dtype=np.uint8)

        y, x = np.ogrid[:size, :size]
        center = size / 2
        mask = (x - center) ** 2 + (y - center) ** 2 <= (size / 2) ** 2

        light_x = x - center + size * 0.3
        light_y = y - center + size * 0.3
        light_dist = np.sqrt(light_x ** 2 + light_y ** 2)
        lighting = 1.0 - np.clip(light_dist / (size * 0.7), 0, 1)
        lighting = lighting ** 0.5

        sand_dark = np.array([180, 130, 70])
        sand_light = np.array([220, 180, 100])

        for i in range(size):
            for j in range(size):
                if not mask[i, j]:
                    continue

                height = dunes[i, j] * 0.7 + detail[i, j] * 0.3

                # Interpoluj między ciemnym a jasnym piaskiem
                color = sand_dark * (1 - height) + sand_light * height

                color = color * (0.4 + lighting[i, j] * 0.6)
                texture[i, j, :3] = np.clip(color, 0, 255).astype(np.uint8)
                texture[i, j, 3] = 255

        texture_transposed = np.transpose(texture, (1, 0, 2))
        surface = pygame.surfarray.make_surface(texture_transposed[:, :, :3])
        return surface.convert_alpha()

    @staticmethod
    def _generate_ice(size: int, seed: int) -> pygame.Surface:
        """Generuj lodową planetę (lód, pęknięcia)"""
        # Podobnie jak desert ale w niebieskich tonach
        ice_texture = NebulaGenerator.perlin_noise_2d((size, size), (8, 8), seed)
        ice_texture = (ice_texture - ice_texture.min()) / (ice_texture.max() - ice_texture.min())

        cracks = NebulaGenerator.perlin_noise_2d((size, size), (20, 20), seed + 100)
        cracks = (cracks - cracks.min()) / (cracks.max() - cracks.min())

        texture = np.zeros((size, size, 4), dtype=np.uint8)

        y, x = np.ogrid[:size, :size]
        center = size / 2
        mask = (x - center) ** 2 + (y - center) ** 2 <= (size / 2) ** 2

        light_x = x - center + size * 0.3
        light_y = y - center + size * 0.3
        light_dist = np.sqrt(light_x ** 2 + light_y ** 2)
        lighting = 1.0 - np.clip(light_dist / (size * 0.7), 0, 1)
        lighting = lighting ** 0.5

        ice_dark = np.array([180, 200, 230])
        ice_light = np.array([240, 250, 255])

        for i in range(size):
            for j in range(size):
                if not mask[i, j]:
                    continue

                value = ice_texture[i, j]

                color = ice_dark * (1 - value) + ice_light * value

                # Dodaj ciemne pęknięcia
                if cracks[i, j] < 0.2:
                    color = color * 0.6

                color = color * (0.5 + lighting[i, j] * 0.5)
                texture[i, j, :3] = np.clip(color, 0, 255).astype(np.uint8)
                texture[i, j, 3] = 255

        texture_transposed = np.transpose(texture, (1, 0, 2))
        surface = pygame.surfarray.make_surface(texture_transposed[:, :, :3])
        return surface.convert_alpha()

    @staticmethod
    def _generate_rock(size: int, seed: int) -> pygame.Surface:
        """Generuj skalistą planetę (kratery, skały)"""
        surface_noise = NebulaGenerator.perlin_noise_2d((size, size), (10, 10), seed)
        surface_noise = (surface_noise - surface_noise.min()) / (surface_noise.max() - surface_noise.min())

        texture = np.zeros((size, size, 4), dtype=np.uint8)

        y, x = np.ogrid[:size, :size]
        center = size / 2
        mask = (x - center) ** 2 + (y - center) ** 2 <= (size / 2) ** 2

        light_x = x - center + size * 0.3
        light_y = y - center + size * 0.3
        light_dist = np.sqrt(light_x ** 2 + light_y ** 2)
        lighting = 1.0 - np.clip(light_dist / (size * 0.7), 0, 1)
        lighting = lighting ** 0.5

        rock_dark = np.array([80, 70, 60])
        rock_light = np.array([140, 120, 100])

        for i in range(size):
            for j in range(size):
                if not mask[i, j]:
                    continue

                value = surface_noise[i, j]
                color = rock_dark * (1 - value) + rock_light * value

                color = color * (0.3 + lighting[i, j] * 0.7)
                texture[i, j, :3] = np.clip(color, 0, 255).astype(np.uint8)
                texture[i, j, 3] = 255

        texture_transposed = np.transpose(texture, (1, 0, 2))
        surface = pygame.surfarray.make_surface(texture_transposed[:, :, :3])
        return surface.convert_alpha()

    @staticmethod
    def _generate_gas_giant(size: int, seed: int) -> pygame.Surface:
        """Generuj gazowego olbrzyma (pasma gazowe, wiry)"""
        # Poziome pasma (jak Jupiter)
        bands = np.zeros((size, size))
        for i in range(size):
            # Sinusoida dla pasów
            band_value = np.sin(i / size * np.pi * 12 + seed * 0.01) * 0.5 + 0.5
            bands[i, :] = band_value

        # Dodaj turbulencję
        turb = NebulaGenerator.perlin_noise_2d((size, size), (8, 8), seed)
        turb = (turb - turb.min()) / (turb.max() - turb.min())

        combined = bands * 0.7 + turb * 0.3

        texture = np.zeros((size, size, 4), dtype=np.uint8)

        y, x = np.ogrid[:size, :size]
        center = size / 2
        mask = (x - center) ** 2 + (y - center) ** 2 <= (size / 2) ** 2

        light_x = x - center + size * 0.3
        light_y = y - center + size * 0.3
        light_dist = np.sqrt(light_x ** 2 + light_y ** 2)
        lighting = 1.0 - np.clip(light_dist / (size * 0.7), 0, 1)
        lighting = lighting ** 0.5

        gas_dark = np.array([160, 120, 80])   # Brązowy
        gas_light = np.array([220, 180, 120])  # Jasny brązowy

        for i in range(size):
            for j in range(size):
                if not mask[i, j]:
                    continue

                value = combined[i, j]
                color = gas_dark * (1 - value) + gas_light * value

                color = color * (0.4 + lighting[i, j] * 0.6)
                texture[i, j, :3] = np.clip(color, 0, 255).astype(np.uint8)
                texture[i, j, 3] = 255

        texture_transposed = np.transpose(texture, (1, 0, 2))
        surface = pygame.surfarray.make_surface(texture_transposed[:, :, :3])
        return surface.convert_alpha()
