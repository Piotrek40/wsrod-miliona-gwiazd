"""
Zaawansowany renderer statków z realistycznymi detalami i efektami
"""
import pygame
import math
import random
from src.config import ShipType


class ShipRenderer:
    """
    Renderer dla realistycznych statków z wieloma detalami
    """

    # Bazowe rozmiary dla różnych typów statków
    SHIP_SIZES = {
        ShipType.SCOUT: 10,
        ShipType.FIGHTER: 14,
        ShipType.CRUISER: 22,
        ShipType.BATTLESHIP: 32,
        ShipType.COLONY_SHIP: 18,
        ShipType.TRANSPORT: 16,
    }

    @staticmethod
    def draw_ship_advanced(screen: pygame.Surface, x: int, y: int,
                          ship_type: ShipType, empire_color: tuple,
                          zoom: float = 1.0, is_selected: bool = False,
                          is_moving: bool = False, rotation: float = 0.0):
        """
        Rysuj statek z zaawansowanymi efektami i detalami

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
            ShipRenderer._draw_scout(screen, x, y, size, empire_color, rotation, is_moving)
        elif ship_type == ShipType.FIGHTER:
            ShipRenderer._draw_fighter(screen, x, y, size, empire_color, rotation, is_moving)
        elif ship_type == ShipType.CRUISER:
            ShipRenderer._draw_cruiser(screen, x, y, size, empire_color, rotation, is_moving)
        elif ship_type == ShipType.BATTLESHIP:
            ShipRenderer._draw_battleship(screen, x, y, size, empire_color, rotation, is_moving)
        elif ship_type == ShipType.COLONY_SHIP:
            ShipRenderer._draw_colony_ship(screen, x, y, size, empire_color, rotation, is_moving)
        elif ship_type == ShipType.TRANSPORT:
            ShipRenderer._draw_transport(screen, x, y, size, empire_color, rotation, is_moving)

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
    def _draw_detail_rect(screen: pygame.Surface, center_x: int, center_y: int,
                         local_x: float, local_y: float, width: float, height: float,
                         color: tuple, rotation: float, outline: bool = False):
        """Pomocnicza funkcja do rysowania małych prostokątów (detale)"""
        # Rogi prostokąta (lokalnie)
        corners_local = [
            (local_x - width/2, local_y - height/2),
            (local_x + width/2, local_y - height/2),
            (local_x + width/2, local_y + height/2),
            (local_x - width/2, local_y + height/2),
        ]

        # Obróć i przenieś do pozycji świata
        corners = []
        for cx, cy in corners_local:
            rx, ry = ShipRenderer._rotate_point(cx, cy, rotation)
            corners.append((center_x + rx, center_y + ry))

        if outline:
            pygame.draw.polygon(screen, color, corners, 1)
        else:
            pygame.draw.polygon(screen, color, corners)

    @staticmethod
    def _draw_scout(screen: pygame.Surface, x: int, y: int, size: float,
                    color: tuple, rotation: float, is_moving: bool):
        """
        Scout - mały, szybki, opływowy statek zwiadowczy
        """
        # KORPUS GŁÓWNY - wydłużony kształt strzałki
        hull_points_local = [
            (0, -size * 0.9),              # Ostry nos
            (-size * 0.25, -size * 0.4),   # Górna lewa
            (-size * 0.35, size * 0.1),    # Środek lewa
            (-size * 0.2, size * 0.6),     # Tył lewa
            (0, size * 0.5),               # Tył środek
            (size * 0.2, size * 0.6),      # Tył prawa
            (size * 0.35, size * 0.1),     # Środek prawa
            (size * 0.25, -size * 0.4),    # Górna prawa
        ]

        hull_points = []
        for px, py in hull_points_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            hull_points.append((x + rx, y + ry))

        # Ciemny outline
        darker = tuple(max(0, c - 80) for c in color)
        pygame.draw.polygon(screen, darker, hull_points, 2)

        # Wypełnienie
        pygame.draw.polygon(screen, color, hull_points)

        if size > 6:
            # KOKPIT (jasny)
            brighter = tuple(min(255, c + 100) for c in color)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.6,
                                          size * 0.15, size * 0.2, brighter, rotation)

            # SILNIKI (2 małe)
            engine_color = (100, 100, 120)
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.15, size * 0.45,
                                          size * 0.12, size * 0.15, engine_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.15, size * 0.45,
                                          size * 0.12, size * 0.15, engine_color, rotation)

            # Engine glow (gdy się porusza)
            if is_moving:
                ShipRenderer._draw_engine_glow_dual(screen, x, y, size, rotation,
                                                   -size * 0.15, size * 0.15, size * 0.52)

            # SENSORY (małe kropki)
            if size > 8:
                sensor_color = (150, 200, 255)
                for sensor_y in [-size * 0.3, 0, size * 0.3]:
                    sx_local, sy_local = ShipRenderer._rotate_point(size * 0.3, sensor_y, rotation)
                    pygame.draw.circle(screen, sensor_color, (int(x + sx_local), int(y + sy_local)), 1)

    @staticmethod
    def _draw_fighter(screen: pygame.Surface, x: int, y: int, size: float,
                     color: tuple, rotation: float, is_moving: bool):
        """
        Fighter - zwrotny statek bojowy ze skrzydłami i uzbrojeniem
        """
        # KORPUS CENTRALNY
        hull_points_local = [
            (0, -size * 0.85),             # Nos
            (-size * 0.2, -size * 0.3),    # Górny lewy
            (-size * 0.25, size * 0.3),    # Środek lewy
            (0, size * 0.5),               # Tył
            (size * 0.25, size * 0.3),     # Środek prawy
            (size * 0.2, -size * 0.3),     # Górny prawy
        ]

        # SKRZYDŁA - asymetryczne, bardziej realistyczne
        wing_left_local = [
            (-size * 0.25, -size * 0.25),
            (-size * 0.7, -size * 0.05),
            (-size * 0.75, size * 0.1),
            (-size * 0.25, size * 0.25),
        ]

        wing_right_local = [
            (size * 0.25, -size * 0.25),
            (size * 0.7, -size * 0.05),
            (size * 0.75, size * 0.1),
            (size * 0.25, size * 0.25),
        ]

        # Obróć punkty
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
        wing_color = tuple(max(0, c - 50) for c in color)
        darker = tuple(max(0, c - 80) for c in color)

        pygame.draw.polygon(screen, wing_color, wing_left)
        pygame.draw.polygon(screen, darker, wing_left, 1)
        pygame.draw.polygon(screen, wing_color, wing_right)
        pygame.draw.polygon(screen, darker, wing_right, 1)

        # Rysuj korpus
        pygame.draw.polygon(screen, darker, hull_points, 2)
        pygame.draw.polygon(screen, color, hull_points)

        if size > 8:
            # KOKPIT (jasny)
            brighter = tuple(min(255, c + 110) for c in color)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.55,
                                          size * 0.2, size * 0.25, brighter, rotation)

            # DZIAŁA (na skrzydłach)
            weapon_color = (120, 120, 140)
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.65, 0,
                                          size * 0.08, size * 0.15, weapon_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.65, 0,
                                          size * 0.08, size * 0.15, weapon_color, rotation)

            # PANELE na skrzydle
            panel_color = tuple(max(0, c - 30) for c in color)
            for i in range(2):
                y_offset = -size * 0.15 + i * size * 0.2
                ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.5, y_offset,
                                              size * 0.12, size * 0.08, panel_color, rotation)
                ShipRenderer._draw_detail_rect(screen, x, y, size * 0.5, y_offset,
                                              size * 0.12, size * 0.08, panel_color, rotation)

            # SILNIK (centralny)
            engine_color = (90, 90, 110)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, size * 0.35,
                                          size * 0.25, size * 0.2, engine_color, rotation)

            if is_moving:
                ShipRenderer._draw_engine_glow(screen, x, y, size, rotation, size * 0.45)

            # ŚWIATŁA nawigacyjne
            if size > 10:
                light_positions = [(-size * 0.7, 0), (size * 0.7, 0)]
                for lx, ly in light_positions:
                    lx_r, ly_r = ShipRenderer._rotate_point(lx, ly, rotation)
                    pygame.draw.circle(screen, (255, 100, 100), (int(x + lx_r), int(y + ly_r)), 2)

    @staticmethod
    def _draw_cruiser(screen: pygame.Surface, x: int, y: int, size: float,
                     color: tuple, rotation: float, is_moving: bool):
        """
        Cruiser - duży statek z wieloma sekcjami i uzbrojeniem
        """
        # GŁÓWNY KORPUS (wydłużony sześciokąt)
        main_hull_local = [
            (0, -size * 0.75),
            (-size * 0.3, -size * 0.35),
            (-size * 0.35, size * 0.2),
            (-size * 0.25, size * 0.65),
            (size * 0.25, size * 0.65),
            (size * 0.35, size * 0.2),
            (size * 0.3, -size * 0.35),
        ]

        main_hull = []
        for px, py in main_hull_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            main_hull.append((x + rx, y + ry))

        # Rysuj korpus
        darker = tuple(max(0, c - 80) for c in color)
        pygame.draw.polygon(screen, darker, main_hull, 2)
        pygame.draw.polygon(screen, color, main_hull)

        if size > 12:
            # MOSTEK DOWODZENIA (wysoka wieża)
            bridge_color = tuple(min(255, c + 60) for c in color)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.45,
                                          size * 0.25, size * 0.35, bridge_color, rotation)

            # OKNA mostka
            window_color = (150, 200, 255)
            for i in range(3):
                wx = -size * 0.08 + i * size * 0.08
                ShipRenderer._draw_detail_rect(screen, x, y, wx, -size * 0.45,
                                              size * 0.04, size * 0.06, window_color, rotation)

            # WIEŻE OBRONNE (2 po bokach)
            turret_color = tuple(max(0, c - 40) for c in color)
            # Lewa
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.28, -size * 0.15,
                                          size * 0.15, size * 0.2, turret_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.28, -size * 0.05,
                                          size * 0.08, size * 0.12, darker, rotation)
            # Prawa
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.28, -size * 0.15,
                                          size * 0.15, size * 0.2, turret_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.28, -size * 0.05,
                                          size * 0.08, size * 0.12, darker, rotation)

            # PANELE PANCERZA (linie)
            panel_color = tuple(max(0, c - 35) for c in color)
            for i in range(4):
                y_offset = -size * 0.25 + i * size * 0.25
                ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.25, y_offset,
                                              size * 0.45, size * 0.08, panel_color, rotation, outline=True)

            # SILNIKI (2 duże)
            engine_color = (80, 80, 100)
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.15, size * 0.55,
                                          size * 0.2, size * 0.25, engine_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.15, size * 0.55,
                                          size * 0.2, size * 0.25, engine_color, rotation)

            if is_moving:
                ShipRenderer._draw_engine_glow_dual(screen, x, y, size, rotation,
                                                   -size * 0.15, size * 0.15, size * 0.67)

            # ANTENY / SENSORY
            if size > 18:
                antenna_color = (120, 140, 160)
                for ax in [-size * 0.2, size * 0.2]:
                    ax_r, ay_r = ShipRenderer._rotate_point(ax, -size * 0.7, rotation)
                    pygame.draw.circle(screen, antenna_color, (int(x + ax_r), int(y + ay_r)), 2)

    @staticmethod
    def _draw_battleship(screen: pygame.Surface, x: int, y: int, size: float,
                        color: tuple, rotation: float, is_moving: bool):
        """
        Battleship - masywny okręt wojenny z ciężkim pancerzem
        """
        # MASYWNY KORPUS
        main_hull_local = [
            (0, -size * 0.7),
            (-size * 0.35, -size * 0.35),
            (-size * 0.45, 0),
            (-size * 0.4, size * 0.4),
            (-size * 0.2, size * 0.65),
            (size * 0.2, size * 0.65),
            (size * 0.4, size * 0.4),
            (size * 0.45, 0),
            (size * 0.35, -size * 0.35),
        ]

        main_hull = []
        for px, py in main_hull_local:
            rx, ry = ShipRenderer._rotate_point(px, py, rotation)
            main_hull.append((x + rx, y + ry))

        # Rysuj korpus
        darker = tuple(max(0, c - 80) for c in color)
        pygame.draw.polygon(screen, darker, main_hull, 3)
        pygame.draw.polygon(screen, color, main_hull)

        if size > 16:
            # MOSTEK GŁÓWNY (potężna wieża)
            bridge_color = tuple(min(255, c + 70) for c in color)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.4,
                                          size * 0.35, size * 0.4, bridge_color, rotation)
            # Górna część mostka
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.5,
                                          size * 0.25, size * 0.15, tuple(min(255, c + 90) for c in color), rotation)

            # GŁÓWNE BATERIE (4 wieże działowe)
            turret_color = tuple(max(0, c - 50) for c in color)
            gun_color = (100, 100, 120)

            # Przednie baterie
            for tx in [-size * 0.25, size * 0.25]:
                ShipRenderer._draw_detail_rect(screen, x, y, tx, -size * 0.15,
                                              size * 0.18, size * 0.22, turret_color, rotation)
                # Lufa
                ShipRenderer._draw_detail_rect(screen, x, y, tx, -size * 0.28,
                                              size * 0.08, size * 0.15, gun_color, rotation)

            # Tylne baterie
            for tx in [-size * 0.3, size * 0.3]:
                ShipRenderer._draw_detail_rect(screen, x, y, tx, size * 0.2,
                                              size * 0.16, size * 0.2, turret_color, rotation)
                # Lufa
                ShipRenderer._draw_detail_rect(screen, x, y, tx, size * 0.08,
                                              size * 0.07, size * 0.12, gun_color, rotation)

            # PANELE PANCERZA (masywne płyty)
            armor_color = tuple(max(0, c - 40) for c in color)
            for i in range(5):
                y_offset = -size * 0.3 + i * size * 0.25
                # Lewy panel
                ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.35, y_offset,
                                              size * 0.15, size * 0.12, armor_color, rotation)
                # Prawy panel
                ShipRenderer._draw_detail_rect(screen, x, y, size * 0.35, y_offset,
                                              size * 0.15, size * 0.12, armor_color, rotation)

            # SILNIKI (4 potężne)
            engine_color = (70, 70, 90)
            for ex in [-size * 0.25, -size * 0.08, size * 0.08, size * 0.25]:
                ShipRenderer._draw_detail_rect(screen, x, y, ex, size * 0.55,
                                              size * 0.12, size * 0.22, engine_color, rotation)

            if is_moving:
                # 4 engine glows
                for ex in [-size * 0.25, -size * 0.08, size * 0.08, size * 0.25]:
                    ex_r, ey_r = ShipRenderer._rotate_point(ex, size * 0.66, rotation)
                    ShipRenderer._draw_single_engine_glow(screen, int(x + ex_r), int(y + ey_r), size * 0.08)

            # ANTENY I SENSORY
            if size > 24:
                sensor_color = (140, 160, 200)
                # Anteny na mostku
                for ax in [-size * 0.12, size * 0.12]:
                    ax_r, ay_r = ShipRenderer._rotate_point(ax, -size * 0.6, rotation)
                    pygame.draw.circle(screen, sensor_color, (int(x + ax_r), int(y + ay_r)), 2)

                # Radar dishes
                dish_color = (180, 180, 200)
                for dx in [-size * 0.35, size * 0.35]:
                    dx_r, dy_r = ShipRenderer._rotate_point(dx, -size * 0.2, rotation)
                    pygame.draw.circle(screen, dish_color, (int(x + dx_r), int(y + dy_r)), 3, 1)

    @staticmethod
    def _draw_colony_ship(screen: pygame.Surface, x: int, y: int, size: float,
                         color: tuple, rotation: float, is_moving: bool):
        """
        Colony Ship - duży statek transportowy z modułami kolonizacyjnymi
        """
        # GŁÓWNY KONTENER (cylindryczny)
        # Użyj prostokątów do stworzenia efektu cylindra
        darker = tuple(max(0, c - 80) for c in color)

        # Główny cylinder (3 sekcje dla głębi)
        mid_color = tuple(max(0, c - 30) for c in color)
        light_color = tuple(min(255, c + 40) for c in color)

        # Ciemna strona (lewa)
        ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.2, 0,
                                      size * 0.35, size * 1.3, darker, rotation)
        # Środek
        ShipRenderer._draw_detail_rect(screen, x, y, 0, 0,
                                      size * 0.35, size * 1.3, mid_color, rotation)
        # Jasna strona (prawa)
        ShipRenderer._draw_detail_rect(screen, x, y, size * 0.2, 0,
                                      size * 0.35, size * 1.3, light_color, rotation)

        if size > 10:
            # MODUŁY KOLONIZACYJNE (cargo pods)
            pod_color = tuple(max(0, c - 50) for c in color)
            pod_positions = [
                (-size * 0.35, -size * 0.4), (size * 0.35, -size * 0.4),
                (-size * 0.35, 0), (size * 0.35, 0),
                (-size * 0.35, size * 0.4), (size * 0.35, size * 0.4),
            ]

            for px, py in pod_positions:
                ShipRenderer._draw_detail_rect(screen, x, y, px, py,
                                              size * 0.2, size * 0.25, pod_color, rotation)
                # Okna/panele na podach
                window_color = (100, 150, 200)
                ShipRenderer._draw_detail_rect(screen, x, y, px, py,
                                              size * 0.12, size * 0.08, window_color, rotation)

            # KOKPIT (przód)
            cockpit_color = tuple(min(255, c + 80) for c in color)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.75,
                                          size * 0.3, size * 0.25, cockpit_color, rotation)
            # Okna kokpitu
            window_color = (150, 200, 255)
            for wx in [-size * 0.1, 0, size * 0.1]:
                ShipRenderer._draw_detail_rect(screen, x, y, wx, -size * 0.75,
                                              size * 0.05, size * 0.08, window_color, rotation)

            # SILNIKI (tylne, 2 duże)
            engine_color = (80, 80, 100)
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.2, size * 0.6,
                                          size * 0.25, size * 0.3, engine_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.2, size * 0.6,
                                          size * 0.25, size * 0.3, engine_color, rotation)

            if is_moving:
                ShipRenderer._draw_engine_glow_dual(screen, x, y, size, rotation,
                                                   -size * 0.2, size * 0.2, size * 0.75)

            # LINIE KONSTRUKCYJNE
            if size > 14:
                line_color = tuple(max(0, c - 60) for c in color)
                for ly in [-size * 0.5, -size * 0.15, size * 0.15, size * 0.5]:
                    for lx_offset in range(-1, 2):
                        lx = lx_offset * size * 0.15
                        lx1_r, ly1_r = ShipRenderer._rotate_point(lx - size * 0.5, ly, rotation)
                        lx2_r, ly2_r = ShipRenderer._rotate_point(lx + size * 0.5, ly, rotation)
                        pygame.draw.line(screen, line_color,
                                       (int(x + lx1_r), int(y + ly1_r)),
                                       (int(x + lx2_r), int(y + ly2_r)), 1)

    @staticmethod
    def _draw_transport(screen: pygame.Surface, x: int, y: int, size: float,
                       color: tuple, rotation: float, is_moving: bool):
        """
        Transport - prostokątny statek cargo z kontenerami
        """
        # GŁÓWNY KONTENER (prostokątny)
        darker = tuple(max(0, c - 80) for c in color)
        container_color = tuple(max(0, c - 30) for c in color)

        ShipRenderer._draw_detail_rect(screen, x, y, 0, 0,
                                      size * 0.7, size * 1.1, container_color, rotation)
        ShipRenderer._draw_detail_rect(screen, x, y, 0, 0,
                                      size * 0.7, size * 1.1, darker, rotation, outline=True)

        if size > 10:
            # KONTENERY CARGO (segmenty)
            cargo_color = tuple(max(0, c - 40) for c in color)
            cargo_positions = [
                (-size * 0.25, -size * 0.35), (size * 0.25, -size * 0.35),
                (-size * 0.25, -size * 0.05), (size * 0.25, -size * 0.05),
                (-size * 0.25, size * 0.25), (size * 0.25, size * 0.25),
            ]

            for cx, cy in cargo_positions:
                ShipRenderer._draw_detail_rect(screen, x, y, cx, cy,
                                              size * 0.25, size * 0.22, cargo_color, rotation)
                # Oznaczenia na kontenerach
                mark_color = tuple(min(255, c + 60) for c in color)
                ShipRenderer._draw_detail_rect(screen, x, y, cx, cy,
                                              size * 0.08, size * 0.05, mark_color, rotation)

            # KOKPIT (mały z przodu)
            cockpit_color = tuple(min(255, c + 70) for c in color)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.7,
                                          size * 0.25, size * 0.3, cockpit_color, rotation)
            # Okna
            window_color = (140, 180, 220)
            ShipRenderer._draw_detail_rect(screen, x, y, 0, -size * 0.7,
                                          size * 0.15, size * 0.12, window_color, rotation)

            # SILNIKI (2 po bokach)
            engine_color = (75, 75, 95)
            ShipRenderer._draw_detail_rect(screen, x, y, -size * 0.3, size * 0.5,
                                          size * 0.15, size * 0.25, engine_color, rotation)
            ShipRenderer._draw_detail_rect(screen, x, y, size * 0.3, size * 0.5,
                                          size * 0.15, size * 0.25, engine_color, rotation)

            if is_moving:
                ShipRenderer._draw_engine_glow_dual(screen, x, y, size, rotation,
                                                   -size * 0.3, size * 0.3, size * 0.62)

            # LINIE STRUKTURALNE
            if size > 12:
                struct_color = tuple(max(0, c - 50) for c in color)
                # Poziome linie
                for ly in [-size * 0.45, -size * 0.15, size * 0.15, size * 0.45]:
                    lx1_r, ly1_r = ShipRenderer._rotate_point(-size * 0.35, ly, rotation)
                    lx2_r, ly2_r = ShipRenderer._rotate_point(size * 0.35, ly, rotation)
                    pygame.draw.line(screen, struct_color,
                                   (int(x + lx1_r), int(y + ly1_r)),
                                   (int(x + lx2_r), int(y + ly2_r)), 1)
                # Pionowe linie
                for lx in [-size * 0.3, 0, size * 0.3]:
                    lx1_r, ly1_r = ShipRenderer._rotate_point(lx, -size * 0.55, rotation)
                    lx2_r, ly2_r = ShipRenderer._rotate_point(lx, size * 0.55, rotation)
                    pygame.draw.line(screen, struct_color,
                                   (int(x + lx1_r), int(y + ly1_r)),
                                   (int(x + lx2_r), int(y + ly2_r)), 1)

    @staticmethod
    def _draw_engine_glow(screen: pygame.Surface, x: int, y: int,
                         size: float, rotation: float, offset_y: float):
        """Pojedyncza poświata silnika (centralny)"""
        engine_x_offset, engine_y_offset = ShipRenderer._rotate_point(0, offset_y, rotation)
        engine_x = x + engine_x_offset
        engine_y = y + engine_y_offset

        ShipRenderer._draw_single_engine_glow(screen, int(engine_x), int(engine_y), size * 0.15)

    @staticmethod
    def _draw_engine_glow_dual(screen: pygame.Surface, x: int, y: int,
                               size: float, rotation: float,
                               left_x: float, right_x: float, offset_y: float):
        """Podwójna poświata silników (2 silniki)"""
        for ex in [left_x, right_x]:
            ex_r, ey_r = ShipRenderer._rotate_point(ex, offset_y, rotation)
            ShipRenderer._draw_single_engine_glow(screen, int(x + ex_r), int(y + ey_r), size * 0.12)

    @staticmethod
    def _draw_single_engine_glow(screen: pygame.Surface, ex: int, ey: int, radius: float):
        """Pojedyncza poświata (używana wielokrotnie)"""
        glow_color = (100, 180, 255)

        for i in range(3, 0, -1):
            glow_radius = int((i / 3) * radius * 3)
            if glow_radius < 1:
                continue
            alpha = int((i / 3) * 140)

            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, alpha),
                             (glow_radius, glow_radius), glow_radius)

            screen.blit(glow_surf,
                       (ex - glow_radius, ey - glow_radius),
                       special_flags=pygame.BLEND_ALPHA_SDL2)

    @staticmethod
    def _draw_selection_ring(screen: pygame.Surface, x: int, y: int, size: float):
        """Pierścień zaznaczenia wokół statku"""
        ring_radius = int(size * 1.4)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), ring_radius, 2)
        pygame.draw.circle(screen, (200, 200, 200), (x, y), ring_radius + 1, 1)

    @staticmethod
    def calculate_ship_rotation(current_x: float, current_y: float,
                                target_x: float, target_y: float) -> float:
        """
        Oblicz rotację statku w kierunku celu
        """
        dx = target_x - current_x
        dy = target_y - current_y
        angle = math.atan2(dx, dy)
        return angle
