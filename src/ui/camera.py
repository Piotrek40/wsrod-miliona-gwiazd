"""
System kamery do przewijania i zbliżania mapy
"""
from dataclasses import dataclass
from src.config import (
    CAMERA_MOVE_SPEED, CAMERA_ZOOM_MIN, CAMERA_ZOOM_MAX,
    WINDOW_WIDTH, WINDOW_HEIGHT
)


@dataclass
class Camera:
    """
    Kamera do poruszania się po mapie galaktyki
    """
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0

    def move(self, dx: float, dy: float):
        """Przesuń kamerę"""
        self.x += dx * CAMERA_MOVE_SPEED / self.zoom
        self.y += dy * CAMERA_MOVE_SPEED / self.zoom

    def zoom_in(self):
        """Przybliż"""
        self.zoom = min(self.zoom + 0.1, CAMERA_ZOOM_MAX)

    def zoom_out(self):
        """Oddal"""
        self.zoom = max(self.zoom - 0.1, CAMERA_ZOOM_MIN)

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        """
        Przekształć współrzędne świata na współrzędne ekranu
        """
        screen_x = (world_x - self.x) * self.zoom + WINDOW_WIDTH / 2
        screen_y = (world_y - self.y) * self.zoom + WINDOW_HEIGHT / 2
        return screen_x, screen_y

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """
        Przekształć współrzędne ekranu na współrzędne świata
        """
        world_x = (screen_x - WINDOW_WIDTH / 2) / self.zoom + self.x
        world_y = (screen_y - WINDOW_HEIGHT / 2) / self.zoom + self.y
        return world_x, world_y

    def center_on(self, world_x: float, world_y: float):
        """Wycentruj kamerę na danym punkcie"""
        self.x = world_x
        self.y = world_y
