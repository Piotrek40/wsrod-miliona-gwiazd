"""
Podstawowe komponenty UI
"""
import pygame
from dataclasses import dataclass
from typing import Optional, Callable
from src.config import Colors, PANEL_PADDING, BUTTON_HEIGHT


@dataclass
class Button:
    """Przycisk UI"""
    x: int
    y: int
    width: int
    height: int
    text: str
    callback: Optional[Callable] = None
    color: tuple = Colors.DARK_GRAY
    hover_color: tuple = Colors.UI_HIGHLIGHT
    text_color: tuple = Colors.UI_TEXT
    is_hovered: bool = False

    def update(self, mouse_pos: tuple[int, int]):
        """Sprawdź czy mysz jest nad przyciskiem"""
        mx, my = mouse_pos
        self.is_hovered = (
            self.x <= mx <= self.x + self.width and
            self.y <= my <= self.y + self.height
        )

    def handle_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Obsłuż kliknięcie, zwróć True jeśli kliknięto"""
        if self.is_hovered and self.callback:
            self.callback()
            return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Rysuj przycisk"""
        color = self.hover_color if self.is_hovered else self.color

        # Prostokąt przycisku
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, Colors.UI_BORDER, (self.x, self.y, self.width, self.height), 2)

        # Tekst
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)


@dataclass
class Panel:
    """Panel informacyjny"""
    x: int
    y: int
    width: int
    height: int
    title: str
    color: tuple = Colors.DARK_GRAY
    border_color: tuple = Colors.UI_BORDER

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Rysuj panel"""
        # Tło panelu
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.width, self.height), 2)

        # Tytuł
        if self.title:
            title_surface = font.render(self.title, True, Colors.UI_TEXT)
            screen.blit(title_surface, (self.x + PANEL_PADDING, self.y + PANEL_PADDING))

    def draw_text(self, screen: pygame.Surface, font: pygame.font.Font, text: str, y_offset: int):
        """Rysuj tekst wewnątrz panelu"""
        text_surface = font.render(text, True, Colors.UI_TEXT)
        screen.blit(text_surface, (self.x + PANEL_PADDING, self.y + y_offset))


class TextBox:
    """Prosty box do wyświetlania tekstu"""

    def __init__(self, x: int, y: int, width: int, font: pygame.font.Font):
        self.x = x
        self.y = y
        self.width = width
        self.font = font
        self.lines: list[str] = []

    def set_text(self, text: str):
        """Ustaw tekst (automatyczne łamanie linii)"""
        self.lines = text.split('\n')

    def draw(self, screen: pygame.Surface):
        """Rysuj tekst"""
        y_pos = self.y
        for line in self.lines:
            text_surface = self.font.render(line, True, Colors.UI_TEXT)
            screen.blit(text_surface, (self.x, y_pos))
            y_pos += self.font.get_height() + 2


def draw_text(screen: pygame.Surface, text: str, x: int, y: int, font: pygame.font.Font, color: tuple = Colors.UI_TEXT):
    """Pomocnicza funkcja do rysowania tekstu"""
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))
