import pygame
import sys
import time
from typing import List, Tuple, Dict

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    GRID_SIZE,
    MAZE_WIDTH,
    MAZE_HEIGHT,
    CellType,
    COLORS,
    MOVEMENT_DELAY,
    ENEMY_DAMAGE,
    EXIT_ARTIFACT_REQUIREMENT,
    ARTIFACT_HP_HEAL,
    resource_path,
)
from maze_generator import MazeGenerator
from game_entities import Player, Enemy, Pig, Witch
from fog_of_war import FogOfWar
from level_validator import LevelValidator
from menu import (
    Menu,
    HistoryScreen,
    GameOverScreen,
    SaveSelectScreen,
    ShopScreen,
    LevelSelectScreen,
)
from save_manager import SaveManager
from sound_manager import SoundManager
from ui_theme import get_font


class GameManager:

    def __init__(self):

        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Maze Dungeon Quest")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_running = False

        self.maze = None
        self.elements = None
        self.player = None
        self.enemies = []
        self.witches = []
        self.fireballs = []
        self.thorns = []
        self.last_player_pos = None
        self.fog_of_war = None

        self.keys_pressed = {}
        self.last_movement_time = {}

        self.enemy_contact_time = {}
        self.enemy_contact_damage = {}
        self.contact_cooldown = 3

        self.sprites = self._load_sprites()

        self.sound_manager = SoundManager()

        self.menu = Menu()
        self.menu.set_screen(self.screen)
        self.history_screen = HistoryScreen(self.screen)
        self.game_over_screen = GameOverScreen(self.screen)

        self.active_save = None
        self.current_level = 1
        self.pig = None
        self.pig_coin_summons_remaining = 3
        self.prev_player_pos = None
        self.toast_text = ""
        self.toast_until = 0
        self.is_sneaking = False
        self.exit_to_menu = False
        self.exit_to_save_select = False
        self.ui_shield_icon = None
        try:
            icon = pygame.image.load(
                resource_path("sprites/shield.png")
            ).convert_alpha()
            self.ui_shield_icon = pygame.transform.scale(icon, (20, 20))
        except Exception:
            self.ui_shield_icon = None

    def _load_sprites(self) -> Dict:

        sprites = {}
        sprite_files = {
            "key": "sprites/key.png",
            "artifact": "sprites/artifact.png",
            "exit": "sprites/exit.png",
            "trap": "sprites/trap.png",
            "door": "sprites/door.png",
            "wall": "sprites/wall.png",
            "path": "sprites/path.png",
            "coin": "sprites/coin.png",
            "witch": "sprites/witch.png",
            "fireball": "sprites/fireball.png",
            "thorns": "sprites/thorns.png",
        }

        for name, path in sprite_files.items():
            try:
                img = pygame.image.load(resource_path(path)).convert_alpha()
                sprites[name] = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
            except Exception as e:
                sprites[name] = None

        return sprites

    def show_main_menu(self) -> bool:

        self.sound_manager.play_music("menu_music", loops=-1)

        while True:
            action = self.menu.handle_input()

            if action == "quit":
                self.sound_manager.stop_music()
                return False
            elif action == "play":
                return True
            elif action == "history":
                history_action = self.history_screen.show()
                if history_action == "quit":
                    self.sound_manager.stop_music()
                    return False

            elif action == "shop":
                shop_screen = ShopScreen(self.screen)
                updated_save = shop_screen.show(self.active_save)
                if updated_save is not None:
                    self.active_save = updated_save
                    self.menu.set_save(self.active_save)
            elif action == "back":
                self.exit_to_save_select = True
                return False

            self.menu.render()
            self.clock.tick(FPS)

    def _apply_shop_items(self):
        if not self.active_save or self.player is None:
            return
        inv = self.active_save.setdefault("inventory", {})
        inv.setdefault("potion", 0)
        inv.setdefault("artifact", 0)
        inv.setdefault("armor", 0)
        inv.setdefault("armor_hits", 0)
        inv.setdefault("pig", 0)
        inv.setdefault("shield", 0)

        self.player.potions = inv.get("potion", 0)
        self.player.shield_unlocked = inv.get("shield", 0) > 0

        if inv.get("armor", 0) > 0:
            self.player.armor_hits = max(0, int(inv.get("armor_hits", 0)))

        if inv.get("artifact", 0) > 0:
            self.player.collected_artifacts = max(
                self.player.collected_artifacts, inv.get("artifact", 1)
            )
            self.player.has_artifact_weapon = True

        if inv.get("pig", 0) > 0 and self.pig is None:
            self._spawn_pig()

        SaveManager().save(self.active_save)

    def _persist_armor_state(self):
        if not self.active_save or not self.player:
            return
        inv = self.active_save.setdefault("inventory", {})
        inv.setdefault("armor", 0)
        inv["armor_hits"] = max(0, int(self.player.armor_hits))
        SaveManager().save(self.active_save)

    def _spawn_pig(self):
        if not self.player or not self.maze:
            return
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = self.player.x + dx, self.player.y + dy
            if 0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT:
                if self.maze[ny][nx] not in (
                    CellType.WALL,
                    CellType.DOOR,
                    CellType.TRAP,
                ):
                    self.pig = Pig((nx, ny))
                    return

    def _pig_command_fetch(self):
        if not self.pig or self.pig_coin_summons_remaining <= 0:
            self._show_toast("No pig fetches left")
            return
        if not self.fog_of_war:
            return
        visible_coins = [
            c for c in self.elements.get("coins", []) if c in self.fog_of_war.visible
        ]
        if not visible_coins:
            self._show_toast("No visible coins")
            return
        if self.pig.command_fetch(visible_coins):
            self.pig_coin_summons_remaining -= 1
        else:
            self._show_toast("Pig is busy")

    def _show_toast(self, text: str, duration_ms: int = 2000):
        self.toast_text = text
        self.toast_until = pygame.time.get_ticks() + duration_ms

    def _collect_forbidden_positions(
        self, player_pos: Tuple[int, int], enemy_positions: List[Tuple[int, int]]
    ):
        forbidden = {
            player_pos,
            self.elements.get("exit_pos"),
        }
        for pos in enemy_positions:
            forbidden.add(pos)
        for coin in self.elements.get("coins", []):
            forbidden.add(coin)
        for trap in self.elements.get("traps", []):
            forbidden.add(trap)
        for key_info in self.elements.get("keys", []):
            if key_info.get("pos"):
                forbidden.add(tuple(key_info["pos"]))
        for art in self.elements.get("artifacts", []):
            forbidden.add(art)
        for door_info in self.elements.get("doors", []):
            if door_info.get("pos"):
                forbidden.add(tuple(door_info["pos"]))
        return forbidden

    def _spawn_witches(
        self,
        count: int,
        player_pos: Tuple[int, int],
        enemy_positions: List[Tuple[int, int]],
    ):
        self.witches = []
        if self.maze is None or count <= 0:
            return
        forbidden = self._collect_forbidden_positions(player_pos, enemy_positions)
        candidates = []
        for y in range(MAZE_HEIGHT):
            for x in range(MAZE_WIDTH):
                if self.maze[y][x] != CellType.PATH:
                    continue
                if (x, y) in forbidden:
                    continue
                candidates.append((x, y))

        if not candidates:
            return

        import random

        random.shuffle(candidates)
        for pos in candidates:
            if len(self.witches) >= count:
                break
            self.witches.append(Witch(pos))
            forbidden.add(pos)

    def _update_witch_attacks(self, now_ms: int):
        if not self.witches:
            return
        for witch in self.witches:
            direction = witch.try_fireball(
                self.player, self.maze, now_ms, self.is_sneaking
            )
            if direction != (0, 0):
                fx = witch.x + direction[0]
                fy = witch.y + direction[1]
                if not (0 <= fx < MAZE_WIDTH and 0 <= fy < MAZE_HEIGHT):
                    continue
                if self.maze[fy][fx] in (CellType.WALL, CellType.DOOR):
                    continue
                self.fireballs.append(
                    {
                        "x": fx,
                        "y": fy,
                        "dx": direction[0],
                        "dy": direction[1],
                        "next_ms": now_ms + 120,
                    }
                )
                self.sound_manager.play_sound("fire")

            if witch.try_thorns(self.player, now_ms, self.is_sneaking):
                positions = []
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = witch.x + dx, witch.y + dy
                    if 0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT:
                        if self.maze[ny][nx] == CellType.PATH:
                            positions.append((nx, ny))
                expire = now_ms + 1000
                for pos in positions:
                    self.thorns.append({"pos": pos, "expires": expire})

    def _update_fireballs(self, now_ms: int):
        if not self.fireballs:
            return
        active = []
        for fb in self.fireballs:
            if now_ms < fb["next_ms"]:
                active.append(fb)
                continue
            nx = fb["x"] + fb["dx"]
            ny = fb["y"] + fb["dy"]
            if not (0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT):
                continue
            if self.maze[ny][nx] in (CellType.WALL, CellType.DOOR):
                continue
            if (nx, ny) == self.player.get_position():
                self.player.take_damage(15)
                self.player.apply_burn(5, now_ms)
                continue
            fb["x"] = nx
            fb["y"] = ny
            fb["next_ms"] = now_ms + 120
            active.append(fb)
        self.fireballs = active

    def _update_thorns(self, now_ms: int):
        if not self.thorns:
            return
        self.thorns = [t for t in self.thorns if t["expires"] > now_ms]
        current_pos = self.player.get_position()
        if self.last_player_pos != current_pos:
            for t in self.thorns:
                if t["pos"] == current_pos:
                    self.player.take_damage(10)
                    break
        self.last_player_pos = current_pos

    def _init_level(self):

        max_attempts = 30

        for _ in range(max_attempts):
            generator = MazeGenerator(MAZE_WIDTH, MAZE_HEIGHT)
            self.maze = generator.generate()
            start_pos, self.elements = generator.place_special_elements()

            exit_pos = self.elements["exit_pos"]
            if LevelValidator.validate_level(
                self.maze, self.elements, start_pos, exit_pos
            ):
                break
        else:
            raise RuntimeError("Не вдалося згенерувати коректний рівень за ліміт спроб")

        self.player = Player(start_pos, GRID_SIZE, self.sound_manager)
        self.pig = None
        self.prev_player_pos = self.player.get_position()
        self.last_player_pos = self.player.get_position()
        self.pig_coin_summons_remaining = 3
        self.exit_to_menu = False
        self._apply_shop_items()

        import random

        skeleton_count = 1
        witch_count = 1
        desired_coins = None
        if self.current_level == 2:
            skeleton_count = 2
            witch_count = 3
            desired_coins = 15
        elif self.current_level == 3:
            skeleton_count = 3
            witch_count = 5
            desired_coins = 25

        if desired_coins is not None:
            forbidden = self._collect_forbidden_positions(start_pos, [])
            candidates = []
            for y in range(MAZE_HEIGHT):
                for x in range(MAZE_WIDTH):
                    if self.maze[y][x] != CellType.PATH:
                        continue
                    if (x, y) in forbidden:
                        continue
                    if (x, y) in self.elements.get("traps", []):
                        continue
                    candidates.append((x, y))
            random.shuffle(candidates)
            self.elements["coins"] = candidates[:desired_coins]

        enemy_positions = []
        tries = 0
        while len(enemy_positions) < skeleton_count and tries < 400:
            tries += 1
            x = random.randint(1, MAZE_WIDTH - 2)
            y = random.randint(1, MAZE_HEIGHT - 2)
            pos = (x, y)
            if self.maze[y][x] != CellType.PATH:
                continue
            if abs(x - self.player.x) + abs(y - self.player.y) <= 10:
                continue
            if pos in enemy_positions:
                continue
            if pos in self.elements.get("traps", []):
                continue
            if pos in self.elements.get("coins", []):
                continue
            enemy_positions.append(pos)

        self.enemies = [Enemy(pos) for pos in enemy_positions]
        self._spawn_witches(witch_count, start_pos, enemy_positions)

        self.fog_of_war = FogOfWar(MAZE_WIDTH, MAZE_HEIGHT, GRID_SIZE)
        self.fog_of_war.update(self.player.get_position())

    def handle_input(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.game_running = False
            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    self.game_running = False
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.exit_to_menu = True
                    self.game_running = False
                    return

                elif event.key == pygame.K_e:
                    if self.player.use_artifact_weapon() and self.enemies:

                        self.enemies[0].health = 0
                        self.player.heal(ARTIFACT_HP_HEAL)
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.is_sneaking = True
                elif event.key == pygame.K_f:
                    if self.player.use_potion():
                        if self.active_save:
                            inv = self.active_save.setdefault("inventory", {})
                            inv["potion"] = self.player.potions
                            SaveManager().save(self.active_save)
                elif event.key == pygame.K_g:
                    self._pig_command_fetch()
                else:
                    self.keys_pressed[event.key] = time.time()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3 and self.player.shield_unlocked:
                    self.player.shield_blocking = True
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    del self.keys_pressed[event.key]
                if event.key in self.last_movement_time:
                    del self.last_movement_time[event.key]
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.is_sneaking = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    self.player.shield_blocking = False

        current_time = time.time()
        key_to_dir = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0),
        }

        self.player.sneaking = self.is_sneaking
        delay_ms = int(MOVEMENT_DELAY * (1.5 if self.is_sneaking else 1.0))
        for key, direction in key_to_dir.items():
            if key in self.keys_pressed:

                if key not in self.last_movement_time:
                    old_pos = self.player.get_position()
                    if self.player.move(
                        direction[0], direction[1], self.maze, self.elements
                    ):
                        self.prev_player_pos = old_pos
                    self.last_movement_time[key] = current_time

                elif (current_time - self.last_movement_time[key]) * 1000 >= delay_ms:
                    old_pos = self.player.get_position()
                    if self.player.move(
                        direction[0], direction[1], self.maze, self.elements
                    ):
                        self.prev_player_pos = old_pos
                    self.last_movement_time[key] = current_time

    def update(self):
        if not self.player.is_alive:
            return "defeat"

        if (
            self.player.x == self.elements["exit_pos"][0]
            and self.player.y == self.elements["exit_pos"][1]
            and len(self.player.keys) >= EXIT_ARTIFACT_REQUIREMENT
        ):
            return "victory"

        self.fog_of_war.update(self.player.get_position())

        alive_enemies = []
        for i, enemy in enumerate(self.enemies):
            if enemy.health <= 0:
                continue

            enemy.update(self.player, self.maze, self.elements, self.is_sneaking)

            if abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y) == 1:
                self._handle_enemy_contact(i, enemy)

            alive_enemies.append(enemy)

        self.enemies = alive_enemies

        now_ms = pygame.time.get_ticks()
        self._update_witch_attacks(now_ms)
        self._update_fireballs(now_ms)
        self._update_thorns(now_ms)
        self.player.tick_burn(now_ms)

        if self.pig:
            current_pos = self.player.get_position()
            follow_pos = (
                self.prev_player_pos
                if self.prev_player_pos and self.prev_player_pos != current_pos
                else None
            )
            self.pig.set_follow_target(follow_pos)
            pig_status = self.pig.update(self.player, self.maze, self.elements)
            if pig_status == "delivered":
                self.player.collected_coins += 1
                if self.sound_manager:
                    self.sound_manager.play_sound("coin_pickup")
            elif pig_status == "no_path":
                self._show_toast("Coin not found")

    def _handle_enemy_contact(self, enemy_id: int, enemy):

        current_time = time.time()
        now_ms = pygame.time.get_ticks()

        if (
            self.player.shield_unlocked
            and self.player.shield_blocking
            and now_ms >= self.player.shield_next_ready_ms
        ):
            self.player.shield_next_ready_ms = now_ms + 5000
            self.enemy_contact_time[enemy_id] = current_time
            self.enemy_contact_damage[enemy_id] = 0
            import random

            if random.random() < 0.3:
                enemy.stun(1500)
            return

        if enemy_id not in self.enemy_contact_damage:
            self.enemy_contact_damage[enemy_id] = 0
            self.enemy_contact_time[enemy_id] = current_time
            self.player.take_damage(10)
            self.sound_manager.play_sound("enemy_attack")
            return

        if current_time - self.enemy_contact_time[enemy_id] >= self.contact_cooldown:
            self.player.take_damage(30)
            self.enemy_contact_time[enemy_id] = current_time
            self.enemy_contact_damage[enemy_id] += 1
            self.sound_manager.play_sound("enemy_attack")

        return "continue"

    def render(self):

        self.screen.fill(COLORS["unknown"])

        self.fog_of_war.render(self.screen, self.maze, GRID_SIZE, self.sprites)

        for enemy in self.enemies:
            enemy.render(self.screen)

        for witch in self.witches:
            witch.render(self.screen)

        self.player.render(self.screen)

        if self.pig:
            self.pig.render(self.screen)

        for key_info in self.elements.get("keys", []):
            if key_info["pos"] and self.fog_of_war.is_visible(key_info["pos"]):
                x, y = key_info["pos"]
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if self.sprites.get("key"):
                    self.screen.blit(self.sprites["key"], rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["key"], rect)

        for artifact_pos in self.elements.get("artifacts", []):
            if self.fog_of_war.is_visible(artifact_pos):
                x, y = artifact_pos
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if self.sprites.get("artifact"):
                    self.screen.blit(self.sprites["artifact"], rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["artifact"], rect)

        for door_info in self.elements.get("doors", []):
            pos = door_info["pos"]
            if pos and self.fog_of_war.is_visible(pos):
                x, y = pos
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if self.sprites.get("door"):
                    self.screen.blit(self.sprites["door"], rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["door"], rect)

        for coin_pos in self.elements.get("coins", []):
            if self.fog_of_war.is_visible(coin_pos):
                x, y = coin_pos
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)

                if self.sprites.get("coin"):
                    self.screen.blit(self.sprites["coin"], rect)
                else:

                    pygame.draw.circle(
                        self.screen, COLORS["coin"], rect.center, GRID_SIZE // 3
                    )

        for fb in self.fireballs:
            if self.fog_of_war.is_visible((fb["x"], fb["y"])):
                rect = pygame.Rect(
                    fb["x"] * GRID_SIZE, fb["y"] * GRID_SIZE, GRID_SIZE, GRID_SIZE
                )
                if self.sprites.get("fireball"):
                    self.screen.blit(self.sprites["fireball"], rect)
                else:
                    pygame.draw.circle(
                        self.screen, COLORS["enemy"], rect.center, GRID_SIZE // 4
                    )

        for thorn in self.thorns:
            pos = thorn["pos"]
            if self.fog_of_war.is_visible(pos):
                rect = pygame.Rect(
                    pos[0] * GRID_SIZE, pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE
                )
                if self.sprites.get("thorns"):
                    self.screen.blit(self.sprites["thorns"], rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["danger"], rect, 2)

        self._render_hud()

        pygame.display.flip()

    def _render_hud(self):

        font = get_font("hud")

        health_text = f"HP: {max(0, self.player.health)}/100"
        keys_text = f"Keys: {len(self.player.keys)}"
        artifact_text = f"Artifacts: {self.player.collected_artifacts}"
        coins_text = f"Coins: {self.player.collected_coins}"
        weapon_text = (
            f"Weapon (E): {'Yes' if self.player.has_artifact_weapon else 'No'}"
        )
        potions_text = f"Potions (F): {self.player.potions}"
        pig_text = f"Pig fetches (G): {self.pig_coin_summons_remaining}/3"
        restart_text = "R - restart | ESC - menu"

        texts = [
            health_text,
            keys_text,
            artifact_text,
            coins_text,
            weapon_text,
            potions_text,
            pig_text,
            "",
            restart_text,
        ]
        for i, text in enumerate(texts):
            if text == "":
                continue
            color = COLORS["text"]
            if "HP" in text and self.player.health < 30:
                color = COLORS["hud_low"]
            surface = font.render(text, True, color)
            self.screen.blit(surface, (10, 10 + i * 25))

        if self.player.armor_hits > 0:
            bar_w = 90
            bar_h = 8
            bar_x = 180
            bar_y = 14
            pygame.draw.rect(
                self.screen, COLORS["armor_bar_bg"], (bar_x, bar_y, bar_w, bar_h)
            )
            fill_w = int(bar_w * (self.player.armor_hits / 5))
            pygame.draw.rect(
                self.screen, COLORS["armor_bar"], (bar_x, bar_y, fill_w, bar_h)
            )
            armor_label = font.render(
                f"Armor: {self.player.armor_hits}/5", True, COLORS["text"]
            )
            self.screen.blit(armor_label, (bar_x + bar_w + 8, 6))

        if self.player.shield_unlocked and self.player.shield_blocking:
            now_ms = pygame.time.get_ticks()
            if self.ui_shield_icon:
                self.screen.blit(self.ui_shield_icon, (WINDOW_WIDTH - 140, 8))
            if now_ms < self.player.shield_next_ready_ms:
                remaining = max(
                    0, int((self.player.shield_next_ready_ms - now_ms) / 1000)
                )
                status_text = f"CD {remaining}s"
            else:
                status_text = "Blocking"
            status_surface = font.render(status_text, True, COLORS["menu_highlight"])
            self.screen.blit(status_surface, (WINDOW_WIDTH - 110, 8))

        now = pygame.time.get_ticks()
        if self.toast_text and now < self.toast_until:
            toast = font.render(self.toast_text, True, COLORS["menu_highlight"])
            rect = toast.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 20))
            self.screen.blit(toast, rect)

    def run_game_loop(self):

        self._init_level()
        self.game_running = True

        while self.running and self.game_running:
            self.handle_input()

            if not self.game_running:
                break

            status = self.update()

            if status == "defeat":
                self._persist_armor_state()
                stats = {
                    "health": 0,
                    "keys": len(self.player.keys),
                    "artifacts": self.player.collected_artifacts,
                    "coins": self.player.collected_coins,
                }

                action = self.game_over_screen.show_defeat(stats)

                if action == "restart":
                    return "restart"
                elif action == "menu":
                    return "menu"
                else:
                    return "quit"

            if status == "victory":
                self._persist_armor_state()
                if self.active_save:
                    max_level = self.active_save.get("max_level", 1)
                    if self.current_level < 3 and self.current_level + 1 > max_level:
                        self.active_save["max_level"] = self.current_level + 1
                        SaveManager().save(self.active_save)

                if self.active_save is not None:
                    self.active_save["coins"] += self.player.collected_coins
                    from save_manager import SaveManager

                    SaveManager().save(self.active_save)

                self.sound_manager.play_sound("victory")

                stats = {
                    "health": max(0, self.player.health),
                    "keys": len(self.player.keys),
                    "artifacts": self.player.collected_artifacts,
                    "coins": self.player.collected_coins,
                    "total_coins": self.active_save["coins"] if self.active_save else 0,
                }

                action = self.game_over_screen.show_victory(stats)

                if action == "restart":
                    return "restart"
                elif action == "next":
                    return "next"
                elif action == "menu":
                    return "menu"
                else:
                    return "quit"

            self.render()
            self.clock.tick(FPS)

        if self.running and not self.game_running:
            if self.exit_to_menu:
                return "menu"
            return "restart"

        return "quit"

    def run(self):

        while self.running:

            save_screen = SaveSelectScreen(self.screen)
            self.active_save = save_screen.show()

            if self.active_save is None:
                break

            self.menu.set_save(self.active_save)

            if not self.show_main_menu():
                if self.exit_to_save_select:
                    self.exit_to_save_select = False
                    continue
                break

            level_screen = LevelSelectScreen(self.screen)
            chosen_level = level_screen.show(self.active_save.get("max_level", 1))
            if chosen_level is None:
                continue
            self.current_level = chosen_level
            self.sound_manager.stop_music()

            while self.running:
                action = self.run_game_loop()

                if action == "restart":
                    continue
                elif action == "next":
                    if self.current_level < 3:
                        self.current_level += 1
                        max_level = self.active_save.get("max_level", 1)
                        if self.current_level > max_level:
                            self.active_save["max_level"] = self.current_level
                            SaveManager().save(self.active_save)
                        continue
                    else:
                        break

                elif action == "menu":
                    break

                elif action == "defeat":

                    stats = {
                        "health": 0,
                        "keys": len(self.player.keys),
                        "artifacts": self.player.collected_artifacts,
                        "coins": self.player.collected_coins,
                    }

                    choice = self.game_over_screen.show_defeat(stats)

                    if choice == "restart":
                        continue
                    elif choice == "menu":
                        break
                    else:
                        self.running = False
                        break

                else:
                    self.running = False
                    break

        pygame.quit()
        sys.exit()
