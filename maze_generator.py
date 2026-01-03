import random
from typing import List, Tuple, Dict, Set, Optional
from collections import deque
from constants import CellType, MAZE_WIDTH, MAZE_HEIGHT

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
        self, maze: List[List[CellType]], start_pos: Coord, blocked: Set[Coord] = set()
    ) -> Set[Coord]:

        visited: Set[Coord] = set()
        q = deque([start_pos])
        visited.add(start_pos)

        while q:
            x, y = q.popleft()

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy

                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                if (nx, ny) in visited or (nx, ny) in blocked:
                    continue

                if maze[ny][nx] == CellType.WALL:
                    continue

                visited.add((nx, ny))
                q.append((nx, ny))

        return visited

    def _bfs_shortest_path(
        self,
        maze: List[List[CellType]],
        start: Coord,
        goal: Coord,
        blocked: Set[Coord] = set(),
    ) -> List[Coord]:

        q = deque([start])
        prev: Dict[Coord, Optional[Coord]] = {start: None}

        while q:
            cur = q.popleft()

            if cur == goal:
                break

            x, y = cur

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                nxt = (nx, ny)

                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                if nxt in prev or nxt in blocked:
                    continue

                if maze[ny][nx] == CellType.WALL:
                    continue

                prev[nxt] = cur
                
                q.append(nxt)

        if goal not in prev:
            return []

        path = []
        cur: Optional[Coord] = goal

        while cur is not None:
            path.append(cur)
            cur = prev[cur]

        path.reverse()

        return path

    def _farthest_cell(self, maze: List[List[CellType]], start: Coord) -> Coord:
        q = deque([start])
        dist = {start: 0}
        far = start

        while q:
            cur = q.popleft()

            if dist[cur] > dist[far]:
                far = cur

            x, y = cur

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy

                nxt = (nx, ny)

                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                if nxt in dist:
                    continue

                if maze[ny][nx] == CellType.WALL:
                    continue

                dist[nxt] = dist[cur] + 1

                q.append(nxt)

        return far

    def place_special_elements(self) -> Tuple[Coord, Dict]:

        if self.maze is None:
            self.generate()

        maze = self.maze

        assert maze is not None

        path_cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if maze[y][x] == CellType.PATH
        ]

        if len(path_cells) < 30:

            raise ValueError("Лабіринт занадто малий для розміщення елементів")

        start_pos = random.choice(path_cells)
        exit_pos = self._farthest_cell(maze, start_pos)
        main_path = self._bfs_shortest_path(maze, start_pos, exit_pos)

        if len(main_path) < 8:

            for _ in range(10):
                start_pos = random.choice(path_cells)
                exit_pos = self._farthest_cell(maze, start_pos)
                main_path = self._bfs_shortest_path(maze, start_pos, exit_pos)

                if len(main_path) >= 8:

                    break

        if len(main_path) < 8:
            raise ValueError("Не вдалося побудувати достатньо довгий шлях Start->Exit")

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

        if not key_candidates:
            raise ValueError("Не знайшлось місце для ключа до дверей")

        key_pos = random.choice(key_candidates)
        all_reachable = self._get_reachable_cells(maze, start_pos)
        
        post_candidates = [
            c for c in all_reachable if c not in pre_door_reachable and c != exit_pos
        ]

        pre_candidates = [
            c for c in pre_door_reachable if c not in (start_pos, key_pos)
        ]

        if post_candidates and random.random() < 0.6:
            artifact_pos = random.choice(post_candidates)

        elif pre_candidates:
            artifact_pos = random.choice(pre_candidates)

        else:
            artifact_pos = None

        forbidden = {start_pos, exit_pos, door_pos, key_pos}

        if artifact_pos:
            forbidden.add(artifact_pos)

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

        elements = {
            "doors": [{"pos": door_pos, "key_id": 0, "is_locked": True}],
            "keys": [{"id": 0, "pos": key_pos}],
            "traps": trap_cells,
            "artifacts": [artifact_pos] if artifact_pos else [],
            "exit_pos": exit_pos,
            "coins": coins,
        }

        return start_pos, elements
