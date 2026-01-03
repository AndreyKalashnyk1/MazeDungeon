import os
import sys
import pygame
from enum import Enum


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


GRID_SIZE = 32
MAZE_WIDTH = 25
MAZE_HEIGHT = 25

WINDOW_WIDTH = MAZE_WIDTH * GRID_SIZE
WINDOW_HEIGHT = MAZE_HEIGHT * GRID_SIZE


class CellType(Enum):
    WALL = 0
    PATH = 1
    EXIT = 2
    TRAP = 3
    ARTIFACT = 4
    DOOR = 5


COLORS = {
    "wall": (50, 50, 50),
    "path": (20, 20, 20),
    "player": (0, 200, 0),
    "enemy": (200, 0, 0),
    "exit": (0, 150, 200),
    "pig": (255, 170, 190),
    "text": (200, 200, 200),
    "highlight": (0, 255, 150),
    "hint": (140, 140, 140),
    "menu_bg": (18, 14, 10),
    "menu_text": (230, 215, 170),
    "menu_highlight": (255, 200, 90),
    "menu_hint": (160, 145, 120),
    "menu_shadow": (5, 5, 5),
    "menu_inactive": (150, 150, 150),
    "menu_info": (100, 100, 100),
    "ui_bg": (20, 20, 30),
    "ui_panel_bg": (10, 10, 20),
    "text_dim": (180, 180, 180),
    "danger": (200, 80, 80),
    "hud_low": (255, 100, 100),
    "armor_bar": (120, 180, 255),
    "armor_bar_bg": (40, 40, 50),
    "key": (255, 215, 0),
    "artifact": (255, 100, 255),
    "door": (139, 69, 19),
    "coin": (255, 215, 0),
    "unknown": (0, 0, 0),
    "path_dim": (20, 40, 80),
    "wall_dim": (30, 30, 30),
    "exit_dim": (20, 100, 20),
    "trap_dim": (100, 20, 20),
}


FOV_RADIUS = 6
ENEMY_SPEED = 0.5


MOVEMENT_DELAY = 200
CLICK_MOVE = True


PLAYER_MAX_HP = 100
ENEMY_DAMAGE = 10
TRAP_DAMAGE = 25
ARTIFACT_HP_HEAL = 20

FPS = 60

EXIT_ARTIFACT_REQUIREMENT = 0

ENEMY_KILL_DAMAGE = 100


NUM_TRAPS = 5
NUM_ARTIFACTS = 3
NUM_KEYS = 3
NUM_DOORS = 2


DIRECTIONS = [
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
]
