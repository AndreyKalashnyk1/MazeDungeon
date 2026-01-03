import pygame
from save_manager import SaveManager
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, COLORS, FPS, resource_path
from ui_theme import get_font

def load_font(size: int):
    try:
        return get_font("body_l", size)

    except:
        return get_font("body_l", size)

def draw_menu_background(screen):
    try:
        img = pygame.image.load(resource_path("sprites/background.png")).convert()
        img = pygame.transform.scale(img, (WINDOW_WIDTH, WINDOW_HEIGHT))

        screen.blit(img, (0, 0))

    except:
        screen.fill(COLORS["menu_bg"])

class Menu:
    def __init__(self):
        self.screen = None

        self.clock = pygame.time.Clock()

        self.running = True

        self.selected = 0

        self.active_save = None

        self.font = get_font("body_l")

        self.font_title = get_font("title_xl")

        self.font_hint = get_font("hint")

    def set_screen(self, screen: pygame.Surface):
        self.screen = screen

    def set_save(self, save_data):
        self.active_save = save_data

    def handle_input(self) -> str:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected - 1) % 3

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected + 1) % 3

                elif event.key == pygame.K_ESCAPE:
                    return "back"

                elif event.key == pygame.K_RETURN:
                    if self.selected == 0:
                        return "play"

                    elif self.selected == 1:
                        return "history"

                    else:
                        return "shop"

        return ""

    def render(self):
        if self.screen is None:
            return

        draw_menu_background(self.screen)

        title_font = self.font_title

        subtitle_font = self.font

        button_font = self.font

        info_font = self.font_hint

        title = title_font.render("MAZE DUNGEON", True, COLORS["menu_text"])

        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 110))

        self.screen.blit(title, title_rect)

        subtitle = subtitle_font.render("QUEST", True, COLORS["menu_highlight"])

        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 180))

        self.screen.blit(subtitle, subtitle_rect)

        if hasattr(self, "active_save") and self.active_save:
            inv = self.active_save.get("inventory", {})

            artifact_count = inv.get("artifact", 0)

            max_level = self.active_save.get("max_level", 1)

            coins_text = f"Coins: {self.active_save['coins']} | Lvl {max_level}"

            coins_surface = self.font.render(coins_text, True, COLORS["menu_text"])

            self.screen.blit(
                coins_surface, (WINDOW_WIDTH // 2 - coins_surface.get_width() // 2, 210)
            )

            name_text = f"Save: {self.active_save.get('name', '')}"

            name_surface = self.font.render(name_text, True, COLORS["menu_text"])

            self.screen.blit(
                name_surface, (WINDOW_WIDTH // 2 - name_surface.get_width() // 2, 240)
            )

        options = ["Play", "Legend", "Shop"]

        start_y = 320

        for i, label in enumerate(options):
            prefix = "> " if self.selected == i else "  "

            color = (
                COLORS["menu_highlight"]
                if self.selected == i
                else COLORS["menu_inactive"]
            )

            text = prefix + label

            surface = button_font.render(text, True, color)

            rect = surface.get_rect(center=(WINDOW_WIDTH // 2, start_y + i * 70))

            self.screen.blit(surface, rect)

        info_text = "Up/Down or W/S - select | Enter - confirm | Esc - back"

        info_surface = info_font.render(info_text, True, COLORS["menu_info"])

        info_rect = info_surface.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50)
        )

        self.screen.blit(info_surface, info_rect)

        pygame.display.flip()

    def show(self) -> str:
        while self.running:
            action = self.handle_input()

            if action in ["play", "history", "shop", "quit", "back"]:
                return action

            self.render()

            self.clock.tick(FPS)

        return "quit"

SHOP_ITEMS = [
    {
        "id": "potion",
        "name": "Health Potion",
        "cost": 5,
        "desc": "Use with F to heal +30 HP",
    },
    {
        "id": "armor",
        "name": "Wood Armor (Lvl 1)",
        "cost": 20,
        "desc": "5 hits, -30% damage, 1.5s shield",
    },
    {
        "id": "shield",
        "name": "Shield",
        "cost": 30,
        "desc": "RMB block vs skeleton (2s cooldown)",
    },
    {
        "id": "pig",
        "name": "Piglet",
        "cost": 100,
        "desc": "Fetch visible coins (G) and return",
    },
]

class ShopScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        self.clock = pygame.time.Clock()

        self.selected = 0

        self.font_title = get_font("title_l")

        self.font_item = get_font("body_l")

        self.font_desc = get_font("body_s")

        self.font_hint = get_font("hint")

        self.item_icons = {}

        self._load_icons()

    def _load_icons(self):
        icons = {
            "potion": "sprites/health_potion.png",
            "armor": "sprites/wood_armor.png",
            "shield": "sprites/shield.png",
            "pig": "sprites/pig.png",
        }
        for item_id, path in icons.items():
            try:
                img = pygame.image.load(resource_path(path)).convert_alpha()
                self.item_icons[item_id] = pygame.transform.scale(img, (24, 24))
            except Exception:
                self.item_icons[item_id] = None

    def _ensure_inventory(self, save_data: dict) -> dict:
        inv = save_data.setdefault("inventory", {})

        inv.setdefault("potion", 0)

        inv.setdefault("artifact", 0)

        inv.setdefault("armor", 0)

        inv.setdefault("armor_hits", 0)

        inv.setdefault("pig", 0)

        inv.setdefault("shield", 0)

        return inv

    def show(self, save_data: dict):
        if save_data is None:
            return None

        inv = self._ensure_inventory(save_data)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return save_data

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected = (self.selected - 1) % len(SHOP_ITEMS)

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected = (self.selected + 1) % len(SHOP_ITEMS)

                    elif event.key == pygame.K_ESCAPE:
                        return save_data

                    elif event.key == pygame.K_RETURN:
                        item = SHOP_ITEMS[self.selected]

                        if save_data.get("coins", 0) >= item["cost"]:
                            if item["id"] == "armor":
                                save_data["coins"] -= item["cost"]

                                inv["armor"] = 1

                                inv["armor_hits"] = 5

                            elif item["id"] == "shield":
                                save_data["coins"] -= item["cost"]

                                inv["shield"] = 1

                            else:
                                save_data["coins"] -= item["cost"]

                                inv[item["id"]] = inv.get(item["id"], 0) + 1

                            SaveManager().save(save_data)

                    elif event.key == pygame.K_r:
                        if inv.get("armor", 0) > 0 and inv.get("armor_hits", 0) > 0:
                            if save_data.get("coins", 0) >= 1:
                                save_data["coins"] -= 1

                                inv["armor_hits"] = 5

                                SaveManager().save(save_data)

            self.render(save_data, inv)

            self.clock.tick(30)

    def render(self, save_data: dict, inv: dict):
        self.screen.fill(COLORS["ui_bg"])

        title = self.font_title.render("Shop", True, COLORS["menu_highlight"])

        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 40))

        coins = self.font_item.render(
            f"Coins: {save_data.get('coins', 0)}", True, COLORS["menu_text"]
        )

        self.screen.blit(coins, (WINDOW_WIDTH // 2 - coins.get_width() // 2, 105))

        start_y = 160

        for i, item in enumerate(SHOP_ITEMS):
            prefix = "> " if i == self.selected else "  "

            color = (
                COLORS["menu_highlight"]
                if i == self.selected
                else COLORS["menu_inactive"]
            )

            owned = inv.get(item["id"], 0)

            line = f"{prefix}{item['name']} - {item['cost']} coins (owned: {owned})"

            surface = self.font_item.render(line, True, color)

            self.screen.blit(surface, (60, start_y + i * 70))

            icon = self.item_icons.get(item["id"])

            if icon:
                self.screen.blit(icon, (30, start_y + i * 70))

            desc = self.font_desc.render(item["desc"], True, COLORS["text_dim"])

            self.screen.blit(desc, (90, start_y + i * 70 + 30))

        hint = self.font_hint.render(
            "Up/Down or W/S - select | Enter - buy | Esc - back | R - repair armor",
            True,
            COLORS["hint"],
        )

        self.screen.blit(
            hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 40)
        )

        armor_hits = inv.get("armor_hits", 0)

        armor_owned = inv.get("armor", 0) > 0

        armor_status = (
            f"Armor durability: {armor_hits}/5"
            if armor_owned
            else "Armor durability: -"
        )

        armor_line = self.font_desc.render(armor_status, True, COLORS["text_dim"])

        self.screen.blit(armor_line, (60, WINDOW_HEIGHT - 80))

        if armor_owned and armor_hits > 0:
            repair_text = "Press R to repair armor for 1 coin"

        else:
            repair_text = "Repair available only if armor not broken"

        repair_line = self.font_desc.render(repair_text, True, COLORS["text_dim"])

        self.screen.blit(repair_line, (60, WINDOW_HEIGHT - 60))

        pygame.display.flip()

class HistoryScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.scroll_offset = 0
        self.max_scroll = 0
        self.line_height = 28

    def render(self):
        self.screen.fill(COLORS["ui_bg"])

        title_font = get_font("title_m")

        title = title_font.render("LEGEND", True, COLORS["menu_highlight"])

        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))

        self.screen.blit(title, title_rect)

        text_font = get_font("body_m")

        info_font = get_font("body_s")

        texts = [
            "Legend of the Crypt Maze",
            "",
            "Lore:",
            "> Beneath the old cathedral lies a shifting crypt",
            "> A lost relic binds the dead to the maze",
            "> Break the curse and reach the exit",
            "",
            "Objective:",
            "> Find the key and reach the exit",
            "> The artifact empowers you, but is optional",
            "",
            "Controls:",
            "> Arrows/WASD - move",
            "> Hold = repeat with 200ms delay",
            "> Hold Shift - sneak (quiet, detect within 2 tiles)",
            "> E - use artifact weapon",
            "> F - use health potion",
            "> G - command pig to fetch visible coin",
            "> RMB - shield block (cooldown)",
            "> R - restart level",
            "",
            "Enemies:",
            "> Skeletons patrol and chase if close",
            "> Witch casts fireballs and thorns",
            "",
            "Shop Items:",
            "> Potions, wood armor, shield, piglet",
            "",
            "Press ESC to return to menu",
        ]

        visible_height = WINDOW_HEIGHT - 160
        total_height = len(texts) * self.line_height
        self.max_scroll = max(0, total_height - visible_height)

        y_offset = 120 - self.scroll_offset
        for text in texts:
            if (
                text.startswith("Game:")
                or text.startswith("Description:")
                or text.startswith("Game Goal:")
                or text.startswith("Controls:")
                or text.startswith("Mechanics:")
            ):
                surface = text_font.render(text, True, COLORS["menu_highlight"])

            else:
                surface = info_font.render(text, True, COLORS["text_dim"])

            self.screen.blit(surface, (60, y_offset))

            y_offset += self.line_height

        pygame.display.flip()

    def show(self) -> str:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset -= event.y * self.line_height
                    if self.scroll_offset < 0:
                        self.scroll_offset = 0
                    if self.scroll_offset > self.max_scroll:
                        self.scroll_offset = self.max_scroll

            self.render()
            self.clock.tick(60)

class LevelSelectScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        self.clock = pygame.time.Clock()

        self.selected = 0

        self.font_title = get_font("title_l")

        self.font_item = get_font("body_l")

        self.font_hint = get_font("hint")

        self.level_img = None

        self.blocked_img = None

        self._load_icons()

    def _load_icons(self):
        try:
            img = pygame.image.load(resource_path("sprites/level.png")).convert_alpha()
            self.level_img = pygame.transform.scale(img, (64, 64))
        except Exception:
            self.level_img = None
        try:
            img = pygame.image.load(
                resource_path("sprites/blocked_level.png")
            ).convert_alpha()
            self.blocked_img = pygame.transform.scale(img, (64, 64))
        except Exception:
            self.blocked_img = None

    def show(self, max_level: int):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.selected = (self.selected - 1) % 3

                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.selected = (self.selected + 1) % 3

                    elif event.key == pygame.K_ESCAPE:
                        return None

                    elif event.key == pygame.K_RETURN:
                        chosen = self.selected + 1

                        if chosen <= max_level:
                            return chosen

            self.render(max_level)

            self.clock.tick(30)

    def render(self, max_level: int):
        self.screen.fill(COLORS["ui_bg"])

        title = self.font_title.render("Select Level", True, COLORS["menu_highlight"])

        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 40))

        item_width = 180

        block_width = item_width * 3

        start_x = (WINDOW_WIDTH - block_width) // 2

        y = 160

        for i in range(3):
            level_num = i + 1

            unlocked = level_num <= max_level

            x = start_x + i * item_width

            if unlocked:
                img = self.level_img

            else:
                img = self.blocked_img

            if img:
                self.screen.blit(img, (x + 40, y))

            else:
                rect = pygame.Rect(x + 40, y, 64, 64)

                color = (
                    COLORS["menu_highlight"] if unlocked else COLORS["menu_inactive"]
                )

                pygame.draw.rect(self.screen, color, rect, 2)

            prefix = "> " if self.selected == i else "  "

            label = f"{prefix}Level {level_num}"

            color = (
                COLORS["menu_highlight"]
                if (self.selected == i and unlocked)
                else COLORS["menu_inactive"]
            )

            text = self.font_item.render(label, True, color)

            self.screen.blit(text, (x + 20, y + 80))

        hint = self.font_hint.render(
            "A/D or Left/Right - select | Enter - start | Esc - back",
            True,
            COLORS["hint"],
        )

        self.screen.blit(
            hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 40)
        )

        pygame.display.flip()

class GameOverScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        self.clock = pygame.time.Clock()

        self.font = get_font("body_l")

        self.font_title = get_font("title_xl")

    def show_victory(self, stats: dict) -> str:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        return "restart"

                    elif event.key == pygame.K_n:
                        return "next"

                    elif event.key == pygame.K_ESCAPE:
                        return "menu"

            self.screen.fill(COLORS["ui_bg"])

            title_font = self.font_title

            text_font = self.font

            info_font = get_font("body_s")

            title = title_font.render("VICTORY!", True, COLORS["menu_highlight"])

            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))

            self.screen.blit(title, title_rect)

            stats_text = [
                f"HP: {stats.get('health', 100)}/100",
                f"Artifacts: {stats.get('artifacts', 0)}",
                f"Keys: {stats.get('keys', 0)}",
                f"Coins: +{stats['coins']}",
                f"Total coins: {stats['total_coins']}",
            ]

            y_offset = 250

            for text in stats_text:
                surface = text_font.render(text, True, COLORS["text"])

                self.screen.blit(surface, (WINDOW_WIDTH // 2 - 200, y_offset))

                y_offset += 50

            info1 = info_font.render("Enter - restart level", True, COLORS["text_dim"])

            info2 = info_font.render(
                "N - next level | ESC - return to menu", True, COLORS["text_dim"]
            )

            self.screen.blit(info1, (WINDOW_WIDTH // 2 - 200, 500))

            self.screen.blit(info2, (WINDOW_WIDTH // 2 - 200, 530))

            pygame.display.flip()

            self.clock.tick(60)

    def show_defeat(self, stats: dict) -> str:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        return "restart"

            self.screen.fill(COLORS["ui_bg"])

            title_font = self.font_title

            text_font = self.font

            info_font = get_font("body_s")

            title = title_font.render("DEFEAT", True, COLORS["danger"])

            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))

            self.screen.blit(title, title_rect)

            stats_text = [
                f"HP: 0/100",
                f"Artifacts: {stats.get('artifacts', 0)}",
                f"Keys: {stats.get('keys', 0)}",
                f"Coins: {stats.get('coins', 0)}",
            ]

            y_offset = 250

            for text in stats_text:
                surface = text_font.render(text, True, COLORS["text"])

                self.screen.blit(surface, (WINDOW_WIDTH // 2 - 200, y_offset))

                y_offset += 50

            info1 = info_font.render("Enter — restart level", True, COLORS["text_dim"])

            info2 = info_font.render("Only restart available", True, COLORS["text_dim"])

            self.screen.blit(info1, (WINDOW_WIDTH // 2 - 200, 500))

            self.screen.blit(info2, (WINDOW_WIDTH // 2 - 200, 530))

            pygame.display.flip()

            self.clock.tick(60)

class SaveSelectScreen:
    def __init__(self, screen):
        self.screen = screen

        self.save_manager = SaveManager()

        self.saves = []

        self.selected = 0

        self.mode = "select"

        self.input_text = ""

        self.font_title = get_font("title_l")

        self.font_item = get_font("body_l")

        self.font_hint = get_font("hint")

        self.reload_saves()

    def reload_saves(self):
        self.saves = []

        for name in self.save_manager.list_saves():
            data = self.save_manager.load_save(name)

            self.saves.append(data)

        self.saves.append({"name": "+ Create a new save", "coins": None})

        if self.selected >= len(self.saves):
            self.selected = 0

    def show(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                if event.type == pygame.KEYDOWN:
                    if self.mode == "select":
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.selected = (self.selected - 1) % len(self.saves)

                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.selected = (self.selected + 1) % len(self.saves)

                        elif event.key == pygame.K_RETURN:
                            chosen = self.saves[self.selected]

                            if chosen["coins"] is None:
                                self.mode = "create"

                                self.input_text = ""

                            else:
                                return chosen

                        elif event.key == pygame.K_ESCAPE:
                            return None

                    elif self.mode == "create":
                        if event.key == pygame.K_RETURN and self.input_text.strip():
                            save = self.save_manager.create_save(
                                self.input_text.strip()
                            )

                            self.reload_saves()

                            return save

                        elif event.key == pygame.K_ESCAPE:
                            self.mode = "select"

                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]

                        else:
                            if (
                                len(self.input_text) < 20
                                and event.unicode.isprintable()
                            ):
                                self.input_text += event.unicode

            self.render()

            clock.tick(30)

    def render(self):
        self.screen.fill(COLORS["ui_panel_bg"])

        title = self.font_title.render("Save selection", True, COLORS["text"])

        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 60))

        if self.mode == "select":
            y = 160

            for i, save in enumerate(self.saves):
                if save["coins"] is None:
                    text = save["name"]

                else:
                    level = save.get("max_level", 1)

                    text = f"{save['name']}   Lvl {level}"

                color = COLORS["highlight"] if i == self.selected else COLORS["text"]

                surface = self.font_item.render(text, True, color)

                self.screen.blit(
                    surface, (WINDOW_WIDTH // 2 - surface.get_width() // 2, y)
                )

                y += 40

            hint = self.font_hint.render(
                "↑↓ or W/S — choise | Enter — confirm | Esc — exit",
                True,
                COLORS["hint"],
            )

            self.screen.blit(
                hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 40)
            )

        elif self.mode == "create":
            prompt = self.font_item.render("Enter save name:", True, COLORS["text"])

            self.screen.blit(prompt, (WINDOW_WIDTH // 2 - prompt.get_width() // 2, 220))

            input_surface = self.font_item.render(
                self.input_text + "|", True, COLORS["highlight"]
            )

            self.screen.blit(
                input_surface, (WINDOW_WIDTH // 2 - input_surface.get_width() // 2, 270)
            )

            hint = self.font_hint.render(
                "Enter — create | Esc — back", True, COLORS["hint"]
            )

            self.screen.blit(
                hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 40)
            )

        pygame.display.flip()
