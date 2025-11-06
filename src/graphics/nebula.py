"""
Generator proceduralnych mgławic (nebulae) używając Perlin noise
"""
import numpy as np
import pygame


class NebulaGenerator:
    """Generator kolorowych mgławic w tle"""

    @staticmethod
    def perlin_noise_2d(shape, res, seed=None):
        """
        Generuj Perlin noise 2D

        Args:
            shape: (width, height) - rozmiar tekstury
            res: (res_x, res_y) - rozdzielczość grid
            seed: Random seed dla powtarzalności

        Returns:
            numpy array z wartościami 0-1
        """
        if seed is not None:
            np.random.seed(seed)

        def f(t):
            """Smoothstep interpolation"""
            return 6 * t ** 5 - 15 * t ** 4 + 10 * t ** 3

        # POPRAWKA: Używaj linspace zamiast mgrid dla dokładnych rozmiarów
        delta = (res[0] / shape[0], res[1] / shape[1])

        # Stwórz grid z dokładnymi wymiarami
        x = np.linspace(0, res[0], shape[0], endpoint=False)
        y = np.linspace(0, res[1], shape[1], endpoint=False)
        grid_x, grid_y = np.meshgrid(x, y, indexing='ij')

        # Zapamiętaj pozycję w gridzie (0-1 w każdej komórce)
        grid_x_frac = grid_x % 1
        grid_y_frac = grid_y % 1
        grid = np.dstack((grid_x_frac, grid_y_frac))

        # Indeksy grid
        grid_x_int = grid_x.astype(int)
        grid_y_int = grid_y.astype(int)

        # Random gradients
        angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
        gradients = np.dstack((np.cos(angles), np.sin(angles)))

        # Pobierz gradienty dla 4 rogów każdej komórki
        g00 = gradients[grid_x_int, grid_y_int]
        g10 = gradients[grid_x_int + 1, grid_y_int]
        g01 = gradients[grid_x_int, grid_y_int + 1]
        g11 = gradients[grid_x_int + 1, grid_y_int + 1]

        # Wektory od rogów do punktu
        n00 = np.sum(grid * g00, 2)
        n10 = np.sum((grid - [1, 0]) * g10, 2)
        n01 = np.sum((grid - [0, 1]) * g01, 2)
        n11 = np.sum((grid - [1, 1]) * g11, 2)

        # Interpolation z smoothstep
        t = f(grid)
        n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
        n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11

        return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)

    @staticmethod
    def generate_nebula_texture(width, height, color, seed=None, density=0.5):
        """
        Generuj teksturę mgławicy

        Args:
            width, height: Rozmiar tekstury
            color: (R, G, B) - kolor mgławicy
            seed: Random seed
            density: Gęstość mgławicy (0-1)

        Returns:
            pygame.Surface z mgławicą
        """
        # Multi-octave Perlin noise (różne skale detali)
        noise1 = NebulaGenerator.perlin_noise_2d((width, height), (4, 4), seed)
        noise2 = NebulaGenerator.perlin_noise_2d((width, height), (8, 8), seed)
        noise3 = NebulaGenerator.perlin_noise_2d((width, height), (16, 16), seed)

        # Combine octaves (różne wagi dla różnych skal)
        combined = noise1 * 0.5 + noise2 * 0.3 + noise3 * 0.2

        # Normalizuj do 0-1
        combined = (combined - combined.min()) / (combined.max() - combined.min())

        # Threshold dla gęstości
        combined = np.maximum(0, combined - (1 - density))
        if combined.max() > 0:
            combined = combined / combined.max()

        # Maska radialna (ciemniej na krawędziach)
        y, x = np.ogrid[:height, :width]
        center_x, center_y = width / 2, height / 2
        radius = min(width, height) / 2
        distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        radial_mask = 1 - np.clip(distance / radius, 0, 1)
        radial_mask = radial_mask ** 2  # Smooth falloff

        # Aplikuj maskę
        combined *= radial_mask

        # Twórz RGBA texture
        nebula = np.zeros((height, width, 4), dtype=np.uint8)

        # Kolor RGB
        for i in range(3):
            nebula[:, :, i] = (combined * color[i]).astype(np.uint8)

        # Alpha (transparencja) - ZWIĘKSZONA dla lepszej widoczności
        nebula[:, :, 3] = (combined * 180).astype(np.uint8)  # Bardziej widoczne

        # Convert to Pygame surface
        # NumPy array jest (height, width, channels), ale Pygame potrzebuje (width, height)
        nebula_transposed = np.transpose(nebula, (1, 0, 2))
        surface = pygame.surfarray.make_surface(nebula_transposed[:, :, :3])  # RGB
        surface.set_alpha(None)  # Wyłącz per-surface alpha

        # Dodaj per-pixel alpha
        surface_with_alpha = surface.convert_alpha()
        alpha_array = pygame.surfarray.pixels_alpha(surface_with_alpha)
        alpha_array[:] = nebula_transposed[:, :, 3]
        del alpha_array  # Release lock

        return surface_with_alpha

    @staticmethod
    def create_nebula_layer(width, height, num_nebulae=3):
        """
        Stwórz warstwę z kilkoma mgławicami

        Returns:
            pygame.Surface z kompozycją mgławic
        """
        layer = pygame.Surface((width, height), pygame.SRCALPHA)
        layer.fill((0, 0, 0, 0))  # Transparent

        # Większe mgławice dla lepszej widoczności
        # (color, position, size, density)
        nebulae_configs = [
            ((255, 100, 180), (width * 0.2, height * 0.3), (800, 800), 0.5),  # Różowa - większa i gęstsza
            ((100, 150, 255), (width * 0.7, height * 0.5), (900, 900), 0.45),  # Niebieska - większa
            ((180, 100, 255), (width * 0.5, height * 0.7), (700, 700), 0.4),  # Fioletowa - większa
        ]

        for i, (color, pos, size, density) in enumerate(nebulae_configs[:num_nebulae]):
            # Generuj mgławicę
            nebula = NebulaGenerator.generate_nebula_texture(
                size[0], size[1],
                color,
                seed=i * 1000,
                density=density
            )

            # Pozycja (wycentrowana)
            x = int(pos[0] - size[0] / 2)
            y = int(pos[1] - size[1] / 2)

            # Rysuj z blendingiem
            layer.blit(nebula, (x, y), special_flags=pygame.BLEND_ALPHA_SDL2)

        return layer
