from functools import lru_cache
import pygame
from constants import resource_path

FONT_PATH = resource_path("fonts/medieval.ttf")

FONT_SIZES = {
    "title_xl": 72,
    "title_l": 64,
    "title_m": 48,
    "button": 40,
    "body_l": 32,
    "body_m": 28,
    "body_s": 24,
    "hint": 20,
    "hud": 24,
}


def _load_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.Font(None, size)


@lru_cache(maxsize=None)
def get_font(role: str, size: int = None) -> pygame.font.Font:
    if size is None:
        size = FONT_SIZES.get(role, 24)
    return _load_font(size)
