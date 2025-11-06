"""
Ekran szczegółów planety
"""
import pygame
from typing import Optional, Callable
from src.models.planet import Planet
from src.config import (
    Colors, WINDOW_WIDTH, WINDOW_HEIGHT, PANEL_WIDTH,
    PANEL_PADDING, ShipType, SHIP_COST
)
from src.ui.widgets import Button, Panel, draw_text


class PlanetScreen:
    """Ekran szczegółów planety z produkcją"""

    def __init__(self, planet: Planet, system_name: str, on_close: Callable):
        self.planet = planet
        self.system_name = system_name
        self.on_close = on_close

        # UI
        self.panel_width = 600
        self.panel_height = 500
        self.panel_x = (WINDOW_WIDTH - self.panel_width) // 2
        self.panel_y = (WINDOW_HEIGHT - self.panel_height) // 2

        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Przyciski budowy statków
        self.ship_buttons = []
        self._create_ship_buttons()

        # Przycisk zamknięcia
        self.close_button = Button(
            x=self.panel_x + self.panel_width - 110,
            y=self.panel_y + self.panel_height - 50,
            width=100,
            height=40,
            text="Zamknij",
            callback=self.on_close
        )

    def _create_ship_buttons(self):
        """Stwórz przyciski budowy statków"""
        button_y = self.panel_y + 250
        button_x = self.panel_x + 20

        ship_types = [
            ShipType.SCOUT,
            ShipType.COLONY_SHIP,
            ShipType.FIGHTER,
        ]

        for i, ship_type in enumerate(ship_types):
            cost = SHIP_COST.get(ship_type, 100)
            button = Button(
                x=button_x + (i % 2) * 280,
                y=button_y + (i // 2) * 50,
                width=260,
                height=40,
                text=f"{ship_type.value} ({cost})",
                callback=lambda st=ship_type: self._build_ship(st)
            )
            self.ship_buttons.append(button)

    def _build_ship(self, ship_type: ShipType):
        """Dodaj statek do kolejki produkcji"""
        self.planet.add_ship_to_queue(ship_type)
        print(f"Dodano {ship_type.value} do kolejki produkcji")

    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Obsłuż kliknięcie. Zwróć True jeśli kliknięto w ekran."""
        # Sprawdź czy kliknięto poza ekranem
        mx, my = mouse_pos
        if not (self.panel_x <= mx <= self.panel_x + self.panel_width and
                self.panel_y <= my <= self.panel_y + self.panel_height):
            return False

        # Sprawdź przyciski
        if self.close_button.handle_click(mouse_pos):
            return True

        for button in self.ship_buttons:
            if button.handle_click(mouse_pos):
                return True

        return True

    def update(self, mouse_pos: tuple[int, int]):
        """Aktualizuj stan przycisków"""
        self.close_button.update(mouse_pos)
        for button in self.ship_buttons:
            button.update(mouse_pos)

    def draw(self, screen: pygame.Surface):
        """Rysuj ekran planety"""
        # Tło (przyciemnione)
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(Colors.BLACK)
        screen.blit(overlay, (0, 0))

        # Panel główny
        pygame.draw.rect(screen, Colors.DARK_GRAY,
                        (self.panel_x, self.panel_y, self.panel_width, self.panel_height))
        pygame.draw.rect(screen, Colors.UI_BORDER,
                        (self.panel_x, self.panel_y, self.panel_width, self.panel_height), 3)

        # Tytuł
        title_text = f"{self.planet.name} ({self.system_name})"
        title_surface = self.font_medium.render(title_text, True, Colors.WHITE)
        screen.blit(title_surface, (self.panel_x + 20, self.panel_y + 20))

        # Informacje o planecie
        y = self.panel_y + 60

        # Specjalne zasoby
        special_resources = []
        if self.planet.has_rare_metals:
            special_resources.append("💎 Metale Rzadkie")
        if self.planet.has_crystals:
            special_resources.append("🔮 Kryształy")

        info_lines = [
            f"Typ: {self.planet.planet_type.value}",
            f"Rozmiar: {self.planet.size}",
            f"Bogactwo minerałów: {self.planet.mineral_richness:.2f}x",
        ]

        if special_resources:
            info_lines.append(f"Zasoby: {', '.join(special_resources)}")

        info_lines.extend([
            "",
            f"Populacja: {int(self.planet.population)} / {int(self.planet.max_population)}",
            "",
            "═ Produkcja zasobów/turę ═",
            f"  🔨 Produkcja: {self.planet.calculate_production():.1f}",
            f"  🔬 Nauka: {self.planet.calculate_science():.1f}",
            f"  🌾 Żywność: {self.planet.calculate_food():.1f}",
            f"  ⚡ Energia: {self.planet.calculate_energy():.1f}",
        ])

        for line in info_lines:
            text_surface = self.font_small.render(line, True, Colors.UI_TEXT)
            screen.blit(text_surface, (self.panel_x + 20, y))
            y += 22

        # Kolejka produkcji
        y += 10
        queue_title = self.font_medium.render("Kolejka produkcji:", True, Colors.UI_HIGHLIGHT)
        screen.blit(queue_title, (self.panel_x + 20, y))
        y += 30

        if self.planet.production_queue:
            for item in self.planet.production_queue[:3]:  # Pokaż max 3
                if item.ship_type:
                    text = f"  {item.ship_type.value}: {item.progress_percent:.0f}%"
                    text_surface = self.font_small.render(text, True, Colors.UI_TEXT)
                    screen.blit(text_surface, (self.panel_x + 20, y))
                    y += 20
        else:
            text_surface = self.font_small.render("  (pusta)", True, Colors.LIGHT_GRAY)
            screen.blit(text_surface, (self.panel_x + 20, y))

        # Sekcja budowy statków
        y = self.panel_y + 220
        build_title = self.font_medium.render("Buduj statek:", True, Colors.UI_HIGHLIGHT)
        screen.blit(build_title, (self.panel_x + 20, y))

        # Przyciski budowy
        for button in self.ship_buttons:
            button.draw(screen, self.font_small)

        # Przycisk zamknięcia
        self.close_button.draw(screen, self.font_medium)
