from typing import List, Tuple, Dict, Set
from collections import deque
from constants import CellType

class LevelValidator:
    @staticmethod
    def validate_level(
        maze: List[List],
        elements: Dict,
        start_pos: Tuple[int, int],
        exit_pos: Tuple[int, int],
    ) -> bool:

        visited_states = set()
        queue = deque()
        start_state = (start_pos[0], start_pos[1], frozenset())
        queue.append(start_state)
        visited_states.add(start_state)
        all_key_ids = {key["id"] for key in elements.get("keys", [])}

        while queue:
            x, y, keys = queue.popleft()
            
            if (x, y) == exit_pos:
                return True

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy

                if not (0 <= nx < len(maze[0]) and 0 <= ny < len(maze)):
                    continue

                if maze[ny][nx] == CellType.WALL:
                    continue

                can_enter = True

                for door in elements.get("doors", []):
                    if door["pos"] == (nx, ny):
                        if door["is_locked"] and door["key_id"] not in keys:
                            can_enter = False
                            
                        break

                if not can_enter:
                    continue

                new_keys = set(keys)

                for key in elements.get("keys", []):
                    if key["pos"] == (nx, ny):
                        new_keys.add(key["id"])

                new_keys = frozenset(new_keys)
                new_state = (nx, ny, new_keys)

                if new_state not in visited_states:
                    visited_states.add(new_state)
                    queue.append(new_state)

        return False
