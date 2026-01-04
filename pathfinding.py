from collections import deque
from typing import Callable, Dict, List, Optional, Set, Tuple

Coord = Tuple[int, int]

def _reconstruct_path(
    prev: Dict[Coord, Optional[Coord]], goal: Coord, include_start: bool
) -> List[Coord]:
    path = []
    cur: Optional[Coord] = goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    if not include_start and path:
        return path[1:]
    return path


def _bfs(
    start: Coord,
    width: int,
    height: int,
    is_blocked: Callable[[Coord], bool],
) -> Tuple[Dict[Coord, Optional[Coord]], Dict[Coord, int]]:
    q = deque([start])
    prev: Dict[Coord, Optional[Coord]] = {start: None}
    dist: Dict[Coord, int] = {start: 0}

    while q:
        x, y = q.popleft()
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            nxt = (nx, ny)
            if nxt in prev:
                continue
            if is_blocked(nxt):
                continue
            prev[nxt] = (x, y)
            dist[nxt] = dist[(x, y)] + 1
            q.append(nxt)

    return prev, dist


def bfs_shortest_path(
    start: Coord,
    goal: Coord,
    width: int,
    height: int,
    is_blocked: Callable[[Coord], bool],
    allow_goal_blocked: bool = False,
    include_start: bool = False,
) -> List[Coord]:
    if start == goal:
        return [start] if include_start else []

    def wrapped_blocked(pos: Coord) -> bool:
        return is_blocked(pos) and not (allow_goal_blocked and pos == goal)

    prev, _ = _bfs(start, width, height, wrapped_blocked)
    if goal not in prev:
        return []
    return _reconstruct_path(prev, goal, include_start)


def bfs_reachable(
    start: Coord,
    width: int,
    height: int,
    is_blocked: Callable[[Coord], bool],
) -> Set[Coord]:
    prev, _ = _bfs(start, width, height, is_blocked)
    return set(prev.keys())


def bfs_farthest(
    start: Coord,
    width: int,
    height: int,
    is_blocked: Callable[[Coord], bool],
) -> Coord:
    _, dist = _bfs(start, width, height, is_blocked)
    far = start
    for pos, d in dist.items():
        if d > dist[far]:
            far = pos
    return far
