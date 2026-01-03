import math
import pygame
from typing import List, Tuple, Dict, Set
from constants import CellType, COLORS, GRID_SIZE, FOV_RADIUS

class FogOfWar:
    def __init__(self, width, height, grid_size):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.visible = set()
        self.explored = set()

    def update(self, player_pos: Tuple[int, int]):
        px, py = player_pos
        self.visible.clear()

        for y in range(max(0, py - FOV_RADIUS), min(self.height, py + FOV_RADIUS + 1)):
            for x in range(
                max(0, px - FOV_RADIUS), min(self.width, px + FOV_RADIUS + 1)
            ):
                distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)

                if distance <= FOV_RADIUS:
                    self.visible.add((x, y))
                    self.explored.add((x, y))

    def is_visible(self, pos: Tuple[int, int]) -> bool:
        return pos in self.visible

    def is_explored(self, pos: Tuple[int, int]) -> bool:
        return pos in self.explored

    def get_cell_color(
        self, maze: List[List], pos: Tuple[int, int]
    ) -> Tuple[int, int, int]:

        x, y = pos
        cell_type = maze[y][x]

        if self.is_visible(pos):
            if cell_type == CellType.PATH:
                return COLORS["path"]

            elif cell_type == CellType.WALL:
                return COLORS["wall"]

            elif cell_type == CellType.EXIT:
                return COLORS["exit"]

            elif cell_type == CellType.TRAP:
                return COLORS["trap"]

        elif self.is_explored(pos):

            if cell_type == CellType.PATH:
                return COLORS["path_dim"]
            elif cell_type == CellType.WALL:
                return COLORS["wall_dim"]
            elif cell_type == CellType.EXIT:
                return COLORS["exit_dim"]
            elif cell_type == CellType.TRAP:
                return COLORS["trap_dim"]

        return COLORS["unknown"]

    def render(
        self,
        screen: pygame.Surface,
        maze: List[List],
        grid_size: int = GRID_SIZE,
        sprites: Dict = None,
    ):

        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * grid_size, y * grid_size, grid_size, grid_size)
                cell_type = maze[y][x]

                if self.is_visible((x, y)) or self.is_explored((x, y)):
                    if self.is_visible((x, y)):
                        if sprites:
                            if cell_type == CellType.WALL and sprites.get("wall"):
                                screen.blit(sprites["wall"], rect)

                            elif cell_type == CellType.PATH and sprites.get("path"):
                                screen.blit(sprites["path"], rect)

                            elif cell_type == CellType.EXIT and sprites.get("exit"):
                                screen.blit(sprites["exit"], rect)

                            elif cell_type == CellType.TRAP and sprites.get("trap"):
                                screen.blit(sprites["trap"], rect)
                                
                            else:
                                color = self.get_cell_color(maze, (x, y))
                                pygame.draw.rect(screen, color, rect)

                        else:
                            color = self.get_cell_color(maze, (x, y))
                            pygame.draw.rect(screen, color, rect)

                    else:
                        color = self.get_cell_color(maze, (x, y))
                        pygame.draw.rect(screen, color, rect)

                else:
                    pygame.draw.rect(screen, COLORS["unknown"], rect)
