import pygame
from abc import ABC, abstractmethod
from constants import GRID_SIZE, COLORS, resource_path


class Entity(ABC):
    def __init__(
        self,
        x: int,
        y: int,
        color: tuple,
        grid_size: int = GRID_SIZE,
        sprite_path: str = None,
    ):
        self.x = x
        self.y = y
        self.color = color
        self.grid_size = grid_size
        self.sprite = None

        if sprite_path:
            try:
                sprite_file = resource_path(sprite_path)
                self.sprite = pygame.image.load(sprite_file).convert_alpha()
                self.sprite = pygame.transform.scale(
                    self.sprite, (grid_size - 4, grid_size - 4)
                )
            except Exception:
                pass

    @abstractmethod
    def update(self, *args, **kwargs):
        pass

    @abstractmethod
    def render(self, screen: pygame.Surface):
        pass

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x * self.grid_size + 2,
            self.y * self.grid_size + 2,
            self.grid_size - 4,
            self.grid_size - 4,
        )

    def get_position(self) -> tuple:
        return (self.x, self.y)

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y
