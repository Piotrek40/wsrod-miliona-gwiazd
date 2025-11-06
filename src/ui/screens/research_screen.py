"""
Ekran badań technologii
"""
import pygame
from typing import Optional, Callable
from src.models.empire import Empire
from src.config import (
    Colors, WINDOW_WIDTH, WINDOW_HEIGHT,
    TECHNOLOGIES, Technology
)
from src.ui.widgets import Button, draw_text


class ResearchScreen:
    """Ekran badań technologii"""

    def __init__(self, empire: Empire, on_close: Callable):
        self.empire = empire
        self.on_close = on_close

        # UI
        self.panel_width = 700
        self.panel_height = 600
        self.panel_x = (WINDOW_WIDTH - self.panel_width) // 2
        self.panel_y = (WINDOW_HEIGHT - self.panel_height) // 2

        self.font_large = pygame.font.Font(None, 28)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Przyciski technologii
        self.tech_buttons = []
        self._create_tech_buttons()

        # Przycisk zamknięcia
        self.close_button = Button(
            x=self.panel_x + self.panel_width - 110,
            y=self.panel_y + self.panel_height - 50,
            width=100,
            height=40,
            text="Zamknij",
            callback=self.on_close
        )

    def _create_tech_buttons(self):
        """Stwórz przyciski dla dostępnych technologii"""
        # Pobierz dostępne technologie
        available_tech_ids = self.empire.get_available_technologies()

        button_y = self.panel_y + 150
        button_x = self.panel_x + 20

        for i, tech_id in enumerate(available_tech_ids[:8]):  # Max 8 na ekranie
            tech = TECHNOLOGIES.get(tech_id)
            if not tech:
                continue

            # Sprawdź czy można badać
            can_research = self.empire.can_research(tech_id)

            button = Button(
                x=button_x,
                y=button_y + i * 50,
                width=660,
                height=45,
                text=f"{tech.name} (koszt: {tech.cost})",
                callback=lambda tid=tech_id: self._start_research(tid),
                enabled=can_research and self.empire.current_research is None
            )
            self.tech_buttons.append((button, tech))

    def _start_research(self, tech_id: str):
        """Rozpocznij badanie technologii"""
        if self.empire.current_research is None:
            self.empire.start_research(tech_id)
            tech = TECHNOLOGIES.get(tech_id)
            print(f"🔬 Rozpoczęto badanie: {tech.name}")
            print(f"   Koszt: {tech.cost} punktów nauki")
            # Odśwież przyciski
            self.tech_buttons.clear()
            self._create_tech_buttons()

    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Obsłuż kliknięcie. Zwróć True jeśli kliknięto w ekran."""
        mx, my = mouse_pos
        if not (self.panel_x <= mx <= self.panel_x + self.panel_width and
                self.panel_y <= my <= self.panel_y + self.panel_height):
            return False

        # Sprawdź przyciski
        if self.close_button.handle_click(mouse_pos):
            return True

        for button, tech in self.tech_buttons:
            if button.handle_click(mouse_pos):
                return True

        return True

    def update(self, mouse_pos: tuple[int, int]):
        """Aktualizuj stan przycisków"""
        self.close_button.update(mouse_pos)
        for button, tech in self.tech_buttons:
            button.update(mouse_pos)

    def draw(self, screen: pygame.Surface):
        """Rysuj ekran badań"""
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
        title_text = f"Badania Naukowe - {self.empire.name}"
        title_surface = self.font_large.render(title_text, True, Colors.WHITE)
        screen.blit(title_surface, (self.panel_x + 20, self.panel_y + 20))

        # Obecne badanie
        y = self.panel_y + 60
        if self.empire.current_research:
            current_tech = TECHNOLOGIES.get(self.empire.current_research)
            if current_tech:
                # Nazwa badania
                current_text = f"🔬 Badane: {current_tech.name}"
                text_surface = self.font_medium.render(current_text, True, Colors.UI_HIGHLIGHT)
                screen.blit(text_surface, (self.panel_x + 20, y))

                y += 30

                # Progress bar
                progress = self.empire.research_progress / current_tech.cost
                bar_width = 660
                bar_height = 25
                bar_x = self.panel_x + 20
                bar_y = y

                # Tło progress bara
                pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))

                # Wypełnienie
                fill_width = int(bar_width * progress)
                pygame.draw.rect(screen, Colors.UI_HIGHLIGHT, (bar_x, bar_y, fill_width, bar_height))

                # Obramowanie
                pygame.draw.rect(screen, Colors.UI_BORDER, (bar_x, bar_y, bar_width, bar_height), 2)

                # Tekst progress
                progress_text = f"{self.empire.research_progress:.0f} / {current_tech.cost} ({progress*100:.0f}%)"
                text_surface = self.font_small.render(progress_text, True, Colors.WHITE)
                text_rect = text_surface.get_rect(center=(bar_x + bar_width//2, bar_y + bar_height//2))
                screen.blit(text_surface, text_rect)

                y += 35
        else:
            no_research_text = "Nie badasz żadnej technologii"
            text_surface = self.font_medium.render(no_research_text, True, Colors.LIGHT_GRAY)
            screen.blit(text_surface, (self.panel_x + 20, y))
            y += 40

        # Separator
        y += 10
        pygame.draw.line(screen, Colors.LIGHT_GRAY,
                        (self.panel_x + 20, y),
                        (self.panel_x + self.panel_width - 20, y), 2)
        y += 15

        # Tytuł dostępnych technologii
        available_title = "Dostępne technologie:"
        text_surface = self.font_medium.render(available_title, True, Colors.UI_HIGHLIGHT)
        screen.blit(text_surface, (self.panel_x + 20, y))

        # Przyciski technologii
        for button, tech in self.tech_buttons:
            button.draw(screen, self.font_small)

            # Opis technologii obok przycisku
            desc_y = button.y + 25
            desc_text = f"  {tech.description}"
            text_surface = self.font_small.render(desc_text, True, Colors.LIGHT_GRAY)
            screen.blit(text_surface, (button.x + 10, desc_y))

        # Hint jeśli nic nie ma
        if not self.tech_buttons:
            hint_y = self.panel_y + 170
            if self.empire.current_research:
                hint_text = "Wszystkie dostępne technologie zostały zbadane lub są w trakcie badania"
            else:
                hint_text = "Zbadaj podstawowe technologie aby odblokować nowe!"
            text_surface = self.font_small.render(hint_text, True, Colors.LIGHT_GRAY)
            screen.blit(text_surface, (self.panel_x + 40, hint_y))

        # Przycisk zamknięcia
        self.close_button.draw(screen, self.font_medium)

        # Legenda na dole
        legend_y = self.panel_y + self.panel_height - 90
        legend_texts = [
            "Kategorie: Biotechnologia, Fizyka, Konstrukcja, Komputery, Chemia",
            "Niektóre technologie wymagają innych (prerequisites)",
            "Punkty nauki/turę: " + f"{self.empire.total_science:.1f}"
        ]
        for i, text in enumerate(legend_texts):
            text_surface = self.font_small.render(text, True, Colors.LIGHT_GRAY)
            screen.blit(text_surface, (self.panel_x + 20, legend_y + i * 20))
