import pygame
import math
import random
import time
from collections import deque

from typing import List, Tuple, Set

from base_entity import Entity

from constants import (
    COLORS,
    GRID_SIZE,
    PLAYER_MAX_HP,
    TRAP_DAMAGE,
    ENEMY_DAMAGE,
    MOVEMENT_DELAY,
    CellType,
)


class Player(Entity):

    def __init__(
        self, start_pos: Tuple[int, int], grid_size: int = GRID_SIZE, sound_manager=None
    ):

        super().__init__(
            start_pos[0],
            start_pos[1],
            COLORS["player"],
            grid_size,
            "sprites/player.png",
        )

        self.health = PLAYER_MAX_HP

        self.keys = set()

        self.collected_artifacts = 0

        self.is_alive = True

        self.last_move_time = 0
        self.has_artifact_weapon = False
        self.sound_manager = sound_manager
        self.collected_coins = 0
        self.potions = 0
        self.armor_hits = 0
        self.invuln_until = 0.0
        self.sneaking = False
        self.shield_unlocked = False
        self.shield_blocking = False
        self.shield_next_ready_ms = 0
        self.burn_ticks = 0
        self.burn_next_ms = 0

    def move(self, dx: int, dy: int, maze: List[List], elements: dict) -> bool:

        nx, ny = self.x + dx, self.y + dy

        if not (0 <= nx < len(maze[0]) and 0 <= ny < len(maze)):

            return False

        if maze[ny][nx] == CellType.WALL:

            return False

        if maze[ny][nx] == CellType.DOOR:

            for door_info in elements["doors"]:

                if door_info["pos"] == (nx, ny):

                    if door_info["is_locked"] and door_info["key_id"] not in self.keys:

                        return False

                    else:

                        door_info["is_locked"] = False

                        maze[ny][nx] = CellType.PATH

                        break

        self.x, self.y = nx, ny

        if self.sound_manager and not self.sneaking:
            self.sound_manager.play_sound("footstep")

        if (self.x, self.y) in elements.get("coins", []):

            elements["coins"].remove((self.x, self.y))

            self.collected_coins += 1

            if self.sound_manager:

                self.sound_manager.play_sound("coin_pickup")

        for key_info in elements["keys"]:

            if key_info["pos"] == (self.x, self.y):

                self.keys.add(key_info["id"])

                key_info["pos"] = None

                if self.sound_manager:

                    self.sound_manager.play_sound("collect_key")

        if (self.x, self.y) in elements["artifacts"]:

            self.collect_artifact()

            elements["artifacts"].remove((self.x, self.y))

        if maze[self.y][self.x] == CellType.TRAP:
            self.take_damage(TRAP_DAMAGE)

        return True

    def take_damage(self, damage: int):

        now = time.time()
        if now < self.invuln_until:
            return

        final_damage = damage
        if self.armor_hits > 0:
            final_damage = max(1, int(damage * 0.7))
            self.armor_hits -= 1
            self.invuln_until = now + 1.5

        self.health -= final_damage
        if self.sound_manager:
            self.sound_manager.play_sound("damage")
        if self.health <= 0:
            self.is_alive = False

    def apply_burn(self, ticks: int, now_ms: int):
        self.burn_ticks = ticks
        self.burn_next_ms = now_ms + 1000

    def tick_burn(self, now_ms: int):
        if self.burn_ticks <= 0:
            return
        if now_ms < self.burn_next_ms:
            return
        self.burn_ticks -= 1
        self.burn_next_ms += 1000
        self.health -= 1
        if self.health <= 0:
            self.is_alive = False

    def use_potion(self) -> bool:

        if self.potions <= 0:
            return False
        self.potions -= 1
        self.heal(30)
        return True

    def use_artifact_weapon(self) -> bool:

        if self.has_artifact_weapon:

            self.has_artifact_weapon = False

            self.collected_artifacts -= 1

            if self.sound_manager:

                self.sound_manager.play_sound("artifact_weapon")

            return True

        return False

    def collect_artifact(self):

        self.collected_artifacts += 1

        self.has_artifact_weapon = True

        if self.sound_manager:

            self.sound_manager.play_sound("collect_artifact")

    def heal(self, amount: int):

        self.health = min(self.health + amount, PLAYER_MAX_HP)

    def update(self, *args, **kwargs):

        pass

    def render(self, screen: pygame.Surface):

        if self.sprite:

            rect = self.get_rect()

            screen.blit(self.sprite, rect)

        else:

            pygame.draw.rect(screen, self.color, self.get_rect())


class Enemy(Entity):

    def __init__(self, start_pos: Tuple[int, int], grid_size: int = GRID_SIZE):
        super().__init__(
            start_pos[0], start_pos[1], COLORS["enemy"], grid_size, "sprites/enemy.png"
        )
        self.spawn_pos = (start_pos[0], start_pos[1])
        self.path: List[Tuple[int, int]] = []
        self.idle_counter = 0
        self.health = 100
        self.attack_cooldown = 0
        self.retreat_steps = 0
        self.state = "PATROL"
        self.alert_timer = 0
        self.stun_until_ms = 0
        self.last_heard_pos = None
        self.alert_until_ms = 0
        self.return_at_ms = 0
        self.hear_radius = 6
        self.last_move_ms = 0
        self.move_delay_patrol = 260
        self.move_delay_alert = 220
        self.move_delay_chase = 180
        self.patrol_path = []
        self.patrol_index = 0

    def _locked_doors_as_blocked(self, elements: dict) -> Set[Tuple[int, int]]:
        blocked = set()
        for door in elements.get("doors", []):
            if door.get("is_locked", False):
                blocked.add(tuple(door["pos"]))
        return blocked

    def _can_move(self, delay_ms: int) -> bool:
        now = pygame.time.get_ticks()
        if now - self.last_move_ms < delay_ms:
            return False
        self.last_move_ms = now
        return True

    def _build_patrol_path(self, maze: List[List]):
        cx, cy = self.spawn_pos
        radius = 2
        path = []

        for x in range(cx - radius, cx + radius + 1):
            path.append((x, cy - radius))
        for y in range(cy - radius + 1, cy + radius + 1):
            path.append((cx + radius, y))
        for x in range(cx + radius - 1, cx - radius - 1, -1):
            path.append((x, cy + radius))
        for y in range(cy + radius - 1, cy - radius, -1):
            path.append((cx - radius, y))

        valid = []
        w = len(maze[0])
        h = len(maze)
        for x, y in path:
            if 0 <= x < w and 0 <= y < h and maze[y][x] == CellType.PATH:
                valid.append((x, y))

        if not valid:
            valid = [self.spawn_pos]

        self.patrol_path = valid
        self.patrol_index = 0

    def _find_path_to_target(
        self, target: Tuple[int, int], maze: List[List], elements: dict
    ) -> List[Tuple[int, int]]:
        blocked = self._locked_doors_as_blocked(elements)
        visited = set()
        queue = deque([(self.x, self.y, [])])
        visited.add((self.x, self.y))

        while queue:
            x, y, path = queue.popleft()
            if (x, y) == target:
                return path

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < len(maze[0]) and 0 <= ny < len(maze)):
                    continue
                if (nx, ny) in visited:
                    continue
                if (nx, ny) in blocked:
                    continue
                if maze[ny][nx] == CellType.WALL:
                    continue

                visited.add((nx, ny))
                queue.append((nx, ny, path + [(nx, ny)]))

        return []

    def _step_toward(
        self, target: Tuple[int, int], maze: List[List], elements: dict
    ) -> bool:
        path = self._find_path_to_target(target, maze, elements)
        if path:
            nx, ny = path.pop(0)
            if (nx, ny) != (self.x, self.y):
                self.x, self.y = nx, ny
                return True
        return False

    def has_line_of_sight(self, player, maze) -> bool:

        if self.x == player.x:

            step = 1 if player.y > self.y else -1

            for y in range(self.y + step, player.y, step):

                if maze[y][self.x] == CellType.WALL:

                    return False

            return True

        if self.y == player.y:

            step = 1 if player.x > self.x else -1

            for x in range(self.x + step, player.x, step):

                if maze[self.y][x] == CellType.WALL:

                    return False

            return True

        return False

    def find_path_to_player(
        self, player: "Player", maze: List[List], elements: dict
    ) -> List[Tuple[int, int]]:

        blocked = self._locked_doors_as_blocked(elements)

        visited = set()

        queue = deque([(self.x, self.y, [])])

        visited.add((self.x, self.y))

        while queue:

            x, y, path = queue.popleft()

            if abs(x - player.x) + abs(y - player.y) == 1:

                return path

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:

                nx, ny = x + dx, y + dy

                if not (0 <= nx < len(maze[0]) and 0 <= ny < len(maze)):

                    continue

                if (nx, ny) in visited:

                    continue

                if (nx, ny) in blocked:

                    continue

                if maze[ny][nx] == CellType.WALL:

                    continue

                visited.add((nx, ny))

                queue.append((nx, ny, path + [(nx, ny)]))

        return []

    def update(self, player, maze, elements, sneaking: bool = False):
        if self.health <= 0:
            return

        now = pygame.time.get_ticks()
        if now < self.stun_until_ms:
            return

        if self.retreat_steps > 0:

            self.retreat_steps -= 1

            return

        dist = abs(self.x - player.x) + abs(self.y - player.y)
        sees_player = self.has_line_of_sight(player, maze)
        chase_condition = sees_player and dist <= 3
        alert_condition = (not sneaking) and (dist <= 5) and (not sees_player)
        now = pygame.time.get_ticks()

        if self.state == "PATROL":
            if chase_condition:
                self.state = "CHASE"
                return

            if alert_condition:
                self.state = "ALERT"
                self.last_heard_pos = (player.x, player.y)
                self.alert_until_ms = now + 4000
                return

            if not self.patrol_path:
                self._build_patrol_path(maze)

            if self._can_move(self.move_delay_patrol):
                target = self.patrol_path[self.patrol_index]
                if (self.x, self.y) == target:
                    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_path)
                    target = self.patrol_path[self.patrol_index]
                moved = self._step_toward(target, maze, elements)
                if not moved:
                    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_path)
            return

        if self.state == "ALERT":
            if chase_condition:
                self.state = "CHASE"
                return

            if alert_condition:
                self.last_heard_pos = (player.x, player.y)
                self.alert_until_ms = now + 4000

            if now > self.alert_until_ms:
                self.state = "COOLDOWN"
                self.return_at_ms = now + 10000
                return

            if self.last_heard_pos and self._can_move(self.move_delay_alert):
                self._step_toward(self.last_heard_pos, maze, elements)
            return

        if self.state == "COOLDOWN":
            if now >= self.return_at_ms:
                self.state = "RETURN"
            return

        if self.state == "RETURN":
            if (self.x, self.y) == self.spawn_pos:
                self.state = "PATROL"
                self.patrol_path = []
                return
            if self._can_move(self.move_delay_patrol):
                self._step_toward(self.spawn_pos, maze, elements)
            return

        if self.state == "CHASE":
            if not chase_condition:
                if alert_condition:
                    self.state = "ALERT"
                    self.last_heard_pos = (player.x, player.y)
                    self.alert_until_ms = now + 4000
                else:
                    self.state = "COOLDOWN"
                    self.return_at_ms = now + 10000
                return

            if dist == 1:
                self.retreat_steps = random.randint(5, 10)
                self.state = "PATROL"
                return

            if self._can_move(self.move_delay_chase):
                self.path = self.find_path_to_player(player, maze, elements)
                if self.path:
                    nx, ny = self.path.pop(0)
                    if (nx, ny) != (player.x, player.y):
                        self.x, self.y = nx, ny

    def render(self, screen: pygame.Surface):
        if self.sprite:
            screen.blit(self.sprite, (self.x * self.grid_size, self.y * self.grid_size))
        else:
            rect = pygame.Rect(
                self.x * self.grid_size,
                self.y * self.grid_size,
                self.grid_size,
                self.grid_size,
            )
            pygame.draw.rect(screen, self.color, rect)

    def stun(self, duration_ms: int):
        self.stun_until_ms = pygame.time.get_ticks() + duration_ms


class Witch(Entity):

    def __init__(self, start_pos: Tuple[int, int], grid_size: int = GRID_SIZE):
        super().__init__(
            start_pos[0], start_pos[1], COLORS["enemy"], grid_size, "sprites/witch.png"
        )
        self.last_fire_ms = 0
        self.last_thorns_ms = 0
        self.fire_cooldown_ms = 5000
        self.thorns_cooldown_ms = 3000
        self.thorns_duration_ms = 1000

    def update(self, *args, **kwargs):

        pass

    def _line_of_fire(self, player: Player, maze: List[List]) -> Tuple[int, int]:
        if self.x == player.x:
            step = 1 if player.y > self.y else -1
            for y in range(self.y + step, player.y, step):
                if maze[y][self.x] == CellType.WALL:
                    return (0, 0)
            return (0, step)
        if self.y == player.y:
            step = 1 if player.x > self.x else -1
            for x in range(self.x + step, player.x, step):
                if maze[self.y][x] == CellType.WALL:
                    return (0, 0)
            return (step, 0)
        return (0, 0)

    def try_fireball(
        self, player: Player, maze: List[List], now_ms: int, sneaking: bool
    ) -> Tuple[int, int]:
        if now_ms - self.last_fire_ms < self.fire_cooldown_ms:
            return (0, 0)
        dist = abs(self.x - player.x) + abs(self.y - player.y)
        if dist <= 3:
            return (0, 0)
        if sneaking and dist > 2:
            return (0, 0)
        direction = self._line_of_fire(player, maze)
        if direction != (0, 0):
            self.last_fire_ms = now_ms
        return direction

    def try_thorns(self, player: Player, now_ms: int, sneaking: bool) -> bool:
        if now_ms - self.last_thorns_ms < self.thorns_cooldown_ms:
            return False
        dist = abs(self.x - player.x) + abs(self.y - player.y)
        if dist >= 3:
            return False
        if sneaking and dist > 2:
            return False
        self.last_thorns_ms = now_ms
        return True

    def render(self, screen):

        if self.sprite:

            screen.blit(self.sprite, (self.x * self.grid_size, self.y * self.grid_size))

        else:

            rect = pygame.Rect(
                self.x * self.grid_size,
                self.y * self.grid_size,
                self.grid_size,
                self.grid_size,
            )

            pygame.draw.rect(screen, self.color, rect)


class Pig(Entity):

    def __init__(self, start_pos: Tuple[int, int], grid_size: int = GRID_SIZE):
        super().__init__(
            start_pos[0], start_pos[1], COLORS["pig"], grid_size, "sprites/pig.png"
        )
        self.state = "follow"
        self.follow_target = start_pos
        self.target_coin = None
        self.last_move_time = 0
        self.move_delay = 200
        self.last_status = None

    def set_follow_target(self, pos: Tuple[int, int]):
        self.follow_target = pos

    def command_fetch(self, coin_positions: List[Tuple[int, int]]) -> bool:
        if self.state != "follow":
            return False
        if not coin_positions:
            return False
        best = min(
            coin_positions, key=lambda p: abs(p[0] - self.x) + abs(p[1] - self.y)
        )
        self.target_coin = best
        self.state = "fetch"
        return True

    def _next_step(self, maze: List[List], target: Tuple[int, int]) -> Tuple[int, int]:
        blocked = {CellType.WALL, CellType.DOOR}
        w = len(maze[0])
        h = len(maze)
        queue = deque([(self.x, self.y, [])])
        visited = {(self.x, self.y)}

        while queue:
            x, y, path = queue.popleft()
            if (x, y) == target:
                if path:
                    return path[0]
                return (x, y)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if (nx, ny) in visited:
                    continue
                if maze[ny][nx] in blocked and (nx, ny) != target:
                    continue
                visited.add((nx, ny))
                queue.append((nx, ny, path + [(nx, ny)]))

        return (self.x, self.y)

    def update(self, player: Player, maze: List[List], elements: dict):
        now = pygame.time.get_ticks()
        if now - self.last_move_time < self.move_delay:
            return None

        self.last_move_time = now
        self.last_status = None

        if self.state == "follow":
            target = self.follow_target
        elif self.state == "fetch":
            target = self.target_coin
        else:
            target = (player.x, player.y)

        if not target:
            return None

        if self.state == "fetch" and (self.x, self.y) == self.target_coin:
            if self.target_coin in elements.get("coins", []):
                elements["coins"].remove(self.target_coin)
            self.state = "return"
            return None

        if self.state == "return" and (self.x, self.y) == (player.x, player.y):
            self.state = "follow"
            self.target_coin = None
            self.last_status = "delivered"

        if self.state in ("follow", "fetch", "return") and (self.x, self.y) != target:
            nx, ny = self._next_step(maze, target)
            if (nx, ny) == (self.x, self.y) and self.state == "fetch":
                self.state = "follow"
                self.target_coin = None
                self.last_status = "no_path"
                return self.last_status
            self.x, self.y = nx, ny

        return self.last_status

    def render(self, screen: pygame.Surface):
        if self.sprite:
            screen.blit(self.sprite, (self.x * self.grid_size, self.y * self.grid_size))
        else:
            rect = pygame.Rect(
                self.x * self.grid_size,
                self.y * self.grid_size,
                self.grid_size,
                self.grid_size,
            )
            pygame.draw.circle(screen, COLORS["pig"], rect.center, self.grid_size // 3)
