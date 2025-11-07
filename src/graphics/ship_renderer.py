"""
Zaawansowany renderer statków z 3D-style sprites i efektami
"""
import pygame
import math
from src.config import ShipType


class ShipRenderer:
    """
    Renderer dla realistycznych statków z cieniowaniem i efektami
    """

    # Bazowe rozmiary dla różnych typów statków
    SHIP_SIZES = {
        ShipType.SCOUT: 8,
        ShipType.FIGHTER: 12,
        ShipType.CRUISER: 18,
        ShipType.BATTLESHIP: 28,
        ShipType.COLONY_SHIP: 16,
        ShipType.TRANSPORT: 14,
    }

    @staticmethod
    def draw_ship_advanced(screen: pygame.Surface, x: int, y: int,
                          ship_type: ShipType, empire_color: tuple,
                          zoom: float = 1.0, is_selected: bool = False,
                          is_moving: bool = False, rotation: float = 0.0):
        """
        Rysuj statek z zaawansowanymi efektami

        Args:
            screen: Powierzchnia pygame do rysowania
            x, y: Pozycja statku
            ship_type: Typ statku
            empire_color: Kolor imperium
            zoom: Współczynnik zoomu kamery
            is_selected: Czy statek jest zaznaczony
            is_moving: Czy statek się porusza (engine glow)
            rotation: Obrót statku w radianach (0 = góra)
        """
        size = ShipRenderer.SHIP_SIZES.get(ship_type, 10) * zoom

        # Wybierz metodę rysowania w zależności od typu
        if ship_type == ShipType.SCOUT:
            ShipRenderer._draw_scout(screen, x, y, size, empire_color, rotation)
        elif ship_type == ShipType.FIGHTER:
            ShipRenderer._draw_fighter(screen, x, y, size, empire_color, rotation)
        elif ship_type == ShipType.CRUISER:
            ShipRenderer._draw_cruiser(screen, x, y, size, empire_color, rotation)
        elif ship_type == ShipType.BATTLESHIP:
            ShipRenderer._draw_battleship(screen, x, y, size, empire_color, rotation)
        elif ship_type == ShipType.COLONY_SHIP:
            ShipRenderer._draw_colony_ship(screen, x, y, size, empire_color, rotation)
        elif ship_type == ShipType.TRANSPORT:
            ShipRenderer._draw_transport(screen, x, y, size, empire_color, rotation)

        # Efekt silników (gdy statek się porusza)
        if is_moving and size > 4:
            ShipRenderer._draw_engine_glow(screen, x, y, size, rotation)

        # Podświetlenie zaznaczenia
        if is_selected:
            ShipRenderer._draw_selection_ring(screen, x, y, size)

    @staticmethod
    def _rotate_point(x: float, y: float, angle: float) -> tuple[float, float]:
        """Obróć punkt wokół (0, 0) o dany kąt"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)

    @staticmethod
    def _draw_scout(screen: pygame.Surface, x: int, y: int, size: float,
                    color: tuple, rotation: float):
        """
        Rysuj Scout - mały, szybki, trójkątny
        """
        # Punkty trójkąta (względem środka)
        points_local = [
            (0, -size),              # Czubek (przód)
            (-size * 0.4, size * 0.5),  # Lewy tył
            (size * 0.4, size * 0.5),   # Prawy tył
        ]

        # Obróć punkty
        points = []
        for px, py in points_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            points.append((x + rx, y + ry))

        # Ciemniejszy outline (cień 3D)
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.polygon(screen, darker, points, 2)

        # Wypełnienie
        pygame.draw.polygon(screen, color, points)

        # Jasny highlight (górna część - pseudo 3D)
        if size > 4:
            brighter = tuple(min(255, c + 80) for c in color)
            highlight_points = [
                points[0],  # Czubek
                ((points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2),
                ((points[0][0] + points[2][0]) / 2, (points[0][1] + points[2][1]) / 2),
            ]
            pygame.draw.polygon(screen, brighter, highlight_points)

    @staticmethod
    def _draw_fighter(screen: pygame.Surface, x: int, y: int, size: float,
                     color: tuple, rotation: float):
        """
        Rysuj Fighter - średni, ostry kształt ze skrzydłami
        """
        # Korpus główny (wydłużony diament)
        hull_points_local = [
            (0, -size * 0.9),           # Przód
            (-size * 0.3, 0),            # Lewy bok
            (0, size * 0.5),             # Tył
            (size * 0.3, 0),             # Prawy bok
        ]

        # Skrzydła
        wing_left_local = [
            (-size * 0.3, -size * 0.2),
            (-size * 0.8, 0),
            (-size * 0.3, size * 0.2),
        ]

        wing_right_local = [
            (size * 0.3, -size * 0.2),
            (size * 0.8, 0),
            (size * 0.3, size * 0.2),
        ]

        # Obróć wszystkie punkty
        hull_points = []
        for px, py in hull_points_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            hull_points.append((x + rx, y + ry))

        wing_left = []
        for px, py in wing_left_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            wing_left.append((x + rx, y + ry))

        wing_right = []
        for px, py in wing_right_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            wing_right.append((x + rx, y + ry))

        # Rysuj skrzydła (ciemniejsze)
        wing_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.polygon(screen, wing_color, wing_left)
        pygame.draw.polygon(screen, wing_color, wing_right)

        # Rysuj korpus
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.polygon(screen, darker, hull_points, 2)
        pygame.draw.polygon(screen, color, hull_points)

        # Highlight (przednia część)
        if size > 6:
            brighter = tuple(min(255, c + 80) for c in color)
            highlight_points = [
                hull_points[0],
                ((hull_points[0][0] + hull_points[1][0]) / 2,
                 (hull_points[0][1] + hull_points[1][1]) / 2),
                ((hull_points[0][0] + hull_points[3][0]) / 2,
                 (hull_points[0][1] + hull_points[3][1]) / 2),
            ]
            pygame.draw.polygon(screen, brighter, highlight_points)

    @staticmethod
    def _draw_cruiser(screen: pygame.Surface, x: int, y: int, size: float,
                     color: tuple, rotation: float):
        """
        Rysuj Cruiser - duży statek z wieloma sekcjami
        """
        # Główny korpus (wydłużony prostokąt)
        main_hull_local = [
            (0, -size * 0.8),
            (-size * 0.35, -size * 0.3),
            (-size * 0.35, size * 0.6),
            (0, size * 0.8),
            (size * 0.35, size * 0.6),
            (size * 0.35, -size * 0.3),
        ]

        # Nadbudówki (wieże)
        tower_local = [
            (-size * 0.15, -size * 0.5),
            (-size * 0.15, -size * 0.2),
            (size * 0.15, -size * 0.2),
            (size * 0.15, -size * 0.5),
        ]

        # Obróć punkty
        main_hull = []
        for px, py in main_hull_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            main_hull.append((x + rx, y + ry))

        tower = []
        for px, py in tower_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            tower.append((x + rx, y + ry))

        # Rysuj korpus główny
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.polygon(screen, darker, main_hull, 2)
        pygame.draw.polygon(screen, color, main_hull)

        # Rysuj wieżę
        if size > 10:
            tower_color = tuple(min(255, c + 40) for c in color)
            pygame.draw.polygon(screen, tower_color, tower)
            pygame.draw.polygon(screen, darker, tower, 1)

        # Highlight (przednia sekcja)
        if size > 10:
            brighter = tuple(min(255, c + 80) for c in color)
            pygame.draw.polygon(screen, brighter, [main_hull[0], main_hull[1], main_hull[5]])

    @staticmethod
    def _draw_battleship(screen: pygame.Surface, x: int, y: int, size: float,
                        color: tuple, rotation: float):
        """
        Rysuj Battleship - ogromny statek z ciężkim uzbrojeniem
        """
        # Masywny korpus
        main_hull_local = [
            (0, -size * 0.7),
            (-size * 0.5, -size * 0.3),
            (-size * 0.5, size * 0.4),
            (-size * 0.3, size * 0.7),
            (size * 0.3, size * 0.7),
            (size * 0.5, size * 0.4),
            (size * 0.5, -size * 0.3),
        ]

        # Mostek
        bridge_local = [
            (-size * 0.2, -size * 0.4),
            (-size * 0.2, -size * 0.1),
            (size * 0.2, -size * 0.1),
            (size * 0.2, -size * 0.4),
        ]

        # Obróć punkty
        main_hull = []
        for px, py in main_hull_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            main_hull.append((x + rx, y + ry))

        bridge = []
        for px, py in bridge_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            bridge.append((x + rx, y + ry))

        # Rysuj korpus
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.polygon(screen, darker, main_hull, 3)
        pygame.draw.polygon(screen, color, main_hull)

        # Rysuj mostek
        if size > 15:
            bridge_color = tuple(min(255, c + 60) for c in color)
            pygame.draw.polygon(screen, bridge_color, bridge)
            pygame.draw.polygon(screen, darker, bridge, 2)

        # Dodatkowe szczegóły (linie pancerza)
        if size > 20:
            detail_color = tuple(max(0, c - 40) for c in color)
            for i in range(3):
                offset = -size * 0.2 + i * size * 0.2
                p1_local = (-size * 0.4, offset)
                p2_local = (size * 0.4, offset)

                p1_rx, p1_ry = ShipRenderer._rotate_point(*p1_local, rotation)
                p2_rx, p2_ry = ShipRenderer._rotate_point(*p2_local, rotation)

                pygame.draw.line(screen, detail_color,
                               (x + p1_rx, y + p1_ry),
                               (x + p2_rx, y + p2_ry), 1)

    @staticmethod
    def _draw_colony_ship(screen: pygame.Surface, x: int, y: int, size: float,
                         color: tuple, rotation: float):
        """
        Rysuj Colony Ship - okrągły statek transportowy
        """
        # Korpus cylindryczny (elipsa)
        # Rysuj jako serie elips dla efektu 3D
        darker = tuple(max(0, c - 60) for c in color)

        # Zewnętrzna elipsa (cień)
        rect = pygame.Rect(x - size * 0.6, y - size * 0.8,
                          size * 1.2, size * 1.6)
        pygame.draw.ellipse(screen, darker, rect, 2)

        # Wypełnienie
        pygame.draw.ellipse(screen, color, rect)

        # Highlight (górna część)
        if size > 8:
            brighter = tuple(min(255, c + 80) for c in color)
            highlight_rect = pygame.Rect(x - size * 0.4, y - size * 0.7,
                                        size * 0.8, size * 0.8)
            pygame.draw.ellipse(screen, brighter, highlight_rect)

        # Cargo pods (małe prostokąty)
        if size > 10:
            pod_color = tuple(max(0, c - 30) for c in color)
            for i in range(-1, 2):
                pod_y = y + i * size * 0.4
                pygame.draw.rect(screen, pod_color,
                               (x - size * 0.15, pod_y - size * 0.1,
                                size * 0.3, size * 0.2))

    @staticmethod
    def _draw_transport(screen: pygame.Surface, x: int, y: int, size: float,
                       color: tuple, rotation: float):
        """
        Rysuj Transport - prostokątny statek cargo
        """
        # Główny kontener (prostokąt)
        main_container_local = [
            (-size * 0.4, -size * 0.6),
            (-size * 0.4, size * 0.6),
            (size * 0.4, size * 0.6),
            (size * 0.4, -size * 0.6),
        ]

        # Kokpit (przód)
        cockpit_local = [
            (-size * 0.25, -size * 0.6),
            (0, -size * 0.9),
            (size * 0.25, -size * 0.6),
        ]

        # Obróć punkty
        main_container = []
        for px, py in main_container_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            main_container.append((x + rx, y + ry))

        cockpit = []
        for px, py in cockpit_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            cockpit.append((x + rx, y + ry))

        # Rysuj kontener
        darker = tuple(max(0, c - 60) for c in color)
        pygame.draw.polygon(screen, darker, main_container, 2)
        container_color = tuple(max(0, c - 20) for c in color)
        pygame.draw.polygon(screen, container_color, main_container)

        # Rysuj kokpit
        pygame.draw.polygon(screen, color, cockpit)
        pygame.draw.polygon(screen, darker, cockpit, 1)

        # Szczegóły (linie cargo)
        if size > 8:
            detail_color = tuple(max(0, c - 40) for c in color)
            for i in range(3):
                offset = -size * 0.3 + i * size * 0.3
                p1_local = (-size * 0.35, offset)
                p2_local = (size * 0.35, offset)

                p1_rx, p1_ry = ShipRenderer._rotate_point(*p1_local, rotation)
                p2_rx, p2_ry = ShipRenderer._rotate_point(*p2_local, rotation)

                pygame.draw.line(screen, detail_color,
                               (x + p1_rx, y + p1_ry),
                               (x + p2_rx, y + p2_ry), 1)

    @staticmethod
    def _draw_engine_glow(screen: pygame.Surface, x: int, y: int,
                         size: float, rotation: float):
        """
        Rysuj poświatę silników (gdy statek się porusza)
        """
        # Pozycja tyłu statku (zależy od rotacji)
        engine_offset_local = (0, size * 0.7)
        engine_x_offset, engine_y_offset = ShipRenderer._rotate_point(
            *engine_offset_local, rotation
        )

        engine_x = x + engine_x_offset
        engine_y = y + engine_y_offset

        # Poświata silnika (niebieski/cyan)
        glow_color = (100, 180, 255)

        # 3 warstwy glow
        for i in range(3, 0, -1):
            glow_radius = int((i / 3) * size * 0.4)
            alpha = int((i / 3) * 120)

            glow_surf = pygame.Surface((glow_radius * 4, glow_radius * 4),
                                      pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, alpha),
                             (glow_radius * 2, glow_radius * 2), glow_radius)

            screen.blit(glow_surf,
                       (engine_x - glow_radius * 2, engine_y - glow_radius * 2),
                       special_flags=pygame.BLEND_ALPHA_SDL2)

    @staticmethod
    def _draw_selection_ring(screen: pygame.Surface, x: int, y: int, size: float):
        """
        Rysuj pierścień zaznaczenia wokół statku
        """
        ring_radius = int(size * 1.3)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), ring_radius, 2)

        # Druga linia dla lepszej widoczności
        pygame.draw.circle(screen, (200, 200, 200), (x, y), ring_radius + 1, 1)

    @staticmethod
    def calculate_ship_rotation(current_x: float, current_y: float,
                                target_x: float, target_y: float) -> float:
        """
        Oblicz rotację statku w kierunku celu

        Args:
            current_x, current_y: Obecna pozycja statku
            target_x, target_y: Cel ruchu

        Returns:
            float: Kąt rotacji w radianach (0 = góra)
        """
        dx = target_x - current_x
        dy = target_y - current_y

        # Oblicz kąt (atan2 zwraca kąt od osi X, konwertujemy na obrót od góry)
        angle = math.atan2(dx, dy)

        return angle
