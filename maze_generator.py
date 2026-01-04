import random
from typing import Dict, List, Optional, Set, Tuple
from constants import CellType, MAZE_WIDTH, MAZE_HEIGHT
from pathfinding import bfs_farthest, bfs_reachable, bfs_shortest_path

Coord = Tuple[int, int]

class MazeGenerator:
    def __init__(self, width: int = MAZE_WIDTH, height: int = MAZE_HEIGHT):
        self.width = width
        self.height = height
        
        if self.width % 2 == 0:
            self.width += 1

        if self.height % 2 == 0:
            self.height += 1

        self.maze: Optional[List[List[CellType]]] = None

    def generate(self) -> List[List[CellType]]:
        self.maze = [
            [CellType.WALL for _ in range(self.width)] for _ in range(self.height)
        ]

        start_x, start_y = 1, 1
        
        self.maze[start_y][start_x] = CellType.PATH
        
        stack = [(start_x, start_y)]

        visited = {(start_x, start_y)}

        while stack:
            x, y = stack[-1]
            neighbors = []

            for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                nx, ny = x + dx, y + dy

                if (
                    1 <= nx < self.width - 1
                    and 1 <= ny < self.height - 1
                    and (nx, ny) not in visited
                ):
                    
                    neighbors.append((nx, ny, dx // 2, dy // 2))

            if neighbors:
                nx, ny, wx, wy = random.choice(neighbors)

                self.maze[y + wy][x + wx] = CellType.PATH
                self.maze[ny][nx] = CellType.PATH
                visited.add((nx, ny))
                stack.append((nx, ny))

            else:
                stack.pop()

        self._remove_isolated_cells()

        return self.maze

    def _remove_isolated_cells(self):
        if not self.maze:
            return

        start_pos = (1, 1)
        visited = self._get_reachable_cells(self.maze, start_pos)

        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y][x] == CellType.PATH and (x, y) not in visited:
                    self.maze[y][x] = CellType.WALL

    def _get_reachable_cells(
        self,
        maze: List[List[CellType]],
        start_pos: Coord,
        blocked: Optional[Set[Coord]] = None,
    ) -> Set[Coord]:
        if blocked is None:
            blocked = set()

        def is_blocked(pos: Coord) -> bool:
            x, y = pos
            return pos in blocked or maze[y][x] == CellType.WALL

        return bfs_reachable(start_pos, self.width, self.height, is_blocked)

    def _path_cells(self, maze: List[List[CellType]]) -> List[Coord]:
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if maze[y][x] == CellType.PATH
        ]

    def _make_is_blocked(self, maze: List[List[CellType]]):
        def is_blocked(pos: Coord) -> bool:
            x, y = pos
            return maze[y][x] == CellType.WALL

        return is_blocked

    def _pick_main_path(
        self, path_cells: List[Coord], is_blocked
    ) -> Tuple[Coord, Coord, List[Coord]]:
        start_pos = random.choice(path_cells)
        exit_pos = bfs_farthest(start_pos, self.width, self.height, is_blocked)
        main_path = bfs_shortest_path(
            start_pos,
            exit_pos,
            self.width,
            self.height,
            is_blocked,
            include_start=True,
        )

        if len(main_path) >= 8:
            return start_pos, exit_pos, main_path

        for _ in range(10):
            start_pos = random.choice(path_cells)
            exit_pos = bfs_farthest(start_pos, self.width, self.height, is_blocked)
            main_path = bfs_shortest_path(
                start_pos,
                exit_pos,
                self.width,
                self.height,
                is_blocked,
                include_start=True,
            )
            if len(main_path) >= 8:
                break

        return start_pos, exit_pos, main_path

    def _place_door_and_key(
        self, maze: List[List[CellType]], start_pos: Coord, main_path: List[Coord]
    ) -> Tuple[Coord, Coord, Set[Coord]]:
        door_index = random.randint(
            max(3, len(main_path) // 3),
            min(len(main_path) - 4, 2 * len(main_path) // 3),
        )
        door_pos = main_path[door_index]
        dx, dy = door_pos
        maze[dy][dx] = CellType.DOOR

        pre_door_reachable = self._get_reachable_cells(
            maze, start_pos, blocked={door_pos}
        )
        key_candidates = [c for c in pre_door_reachable if c != start_pos]
        raise_no_key = "Не знайшлось місце для ключа до дверей"
        if not key_candidates:
            raise ValueError(raise_no_key)
        key_pos = random.choice(key_candidates)
        return door_pos, key_pos, pre_door_reachable

    def _pick_artifact_pos(
        self,
        all_reachable: Set[Coord],
        pre_door_reachable: Set[Coord],
        start_pos: Coord,
        key_pos: Coord,
        exit_pos: Coord,
    ) -> Optional[Coord]:
        post_candidates = [
            c for c in all_reachable if c not in pre_door_reachable and c != exit_pos
        ]
        pre_candidates = [
            c for c in pre_door_reachable if c not in (start_pos, key_pos)
        ]

        if post_candidates and random.random() < 0.6:
            return random.choice(post_candidates)
        if pre_candidates:
            return random.choice(pre_candidates)
        return None

    def _place_traps_and_coins(
        self,
        maze: List[List[CellType]],
        all_reachable: Set[Coord],
        forbidden: Set[Coord],
        exit_pos: Coord,
    ) -> Tuple[List[Coord], List[Coord]]:
        trap_candidates = [c for c in all_reachable if c not in forbidden]
        random.shuffle(trap_candidates)
        trap_cells = trap_candidates[:2]

        ex, ey = exit_pos
        maze[ey][ex] = CellType.EXIT
        for tx, ty in trap_cells:
            maze[ty][tx] = CellType.TRAP

        coin_count = random.randint(7, 9)
        coin_candidates = [
            c for c in all_reachable if c not in forbidden and c not in trap_cells
        ]
        random.shuffle(coin_candidates)
        coins = coin_candidates[:coin_count]
        return trap_cells, coins

    def place_special_elements(self) -> Tuple[Coord, Dict]:
        if self.maze is None:
            self.generate()

        maze = self.maze
        assert maze is not None

        path_cells = self._path_cells(maze)
        raise_small = "Лабіринт занадто малий для розміщення елементів"
        if len(path_cells) < 30:
            raise ValueError(raise_small)

        is_blocked = self._make_is_blocked(maze)
        start_pos, exit_pos, main_path = self._pick_main_path(
            path_cells, is_blocked
        )
        raise_short = "Не вдалося побудувати достатньо довгий шлях Start->Exit"
        if len(main_path) < 8:
            raise ValueError(raise_short)

        door_pos, key_pos, pre_door_reachable = self._place_door_and_key(
            maze, start_pos, main_path
        )
        all_reachable = self._get_reachable_cells(maze, start_pos)
        artifact_pos = self._pick_artifact_pos(
            all_reachable, pre_door_reachable, start_pos, key_pos, exit_pos
        )

        forbidden = {start_pos, exit_pos, door_pos, key_pos}
        if artifact_pos:
            forbidden.add(artifact_pos)

        trap_cells, coins = self._place_traps_and_coins(
            maze, all_reachable, forbidden, exit_pos
        )

        elements = {
            "doors": [{"pos": door_pos, "key_id": 0, "is_locked": True}],
            "keys": [{"id": 0, "pos": key_pos}],
            "traps": trap_cells,
            "artifacts": [artifact_pos] if artifact_pos else [],
            "exit_pos": exit_pos,
            "coins": coins,
        }

        return start_pos, elements
