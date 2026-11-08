"""Deterministic matched-input lessons for the b87dcd3011b1 portal family."""
from __future__ import annotations

from collections import deque
from functools import lru_cache
import hashlib
import math
import random
from typing import Callable

Grid = list[list[int]]
Cell = tuple[int, int]
Pair = tuple[Cell, Cell]
PORTAL_COLORS = (4, 5, 6)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
POLICIES = ("all_pairs", "widest_pair_only")


def _rng(seed: int, role: str, index: int, salt: str = "scene") -> random.Random:
    raw = hashlib.sha256(f"{seed}|{role}|{index}|{salt}|v2".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _copy(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _grid_tuple(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _validate_grid(grid: Grid) -> None:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers 0..9")


def portal_pairs(grid: Grid) -> dict[int, Pair]:
    _validate_grid(grid)
    result: dict[int, Pair] = {}
    for color in PORTAL_COLORS:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) == 2:
            result[color] = (cells[0], cells[1])
        elif cells:
            raise ValueError(f"portal color {color} must occur exactly twice")
    if not result:
        raise ValueError("at least one portal pair is required")
    return result


def _manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _start_goal(grid: Grid) -> tuple[Cell, Cell]:
    starts = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    goals = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if len(starts) != 1 or len(goals) != 1:
        raise ValueError("exactly one start and one goal are required")
    return starts[0], goals[0]


def widest_portal_color(grid: Grid) -> int:
    pairs = portal_pairs(grid)
    return max(sorted(pairs), key=lambda color: _manhattan(*pairs[color]))


def _selector_key(grid: Grid, selector: str, color: int) -> tuple[float, int]:
    pairs = portal_pairs(grid)
    start, goal = _start_goal(grid)
    a, b = pairs[color]
    if selector == "widest_manhattan":
        value = _manhattan(a, b)
    elif selector == "narrowest_manhattan":
        value = -_manhattan(a, b)
    elif selector == "widest_euclidean":
        value = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    elif selector == "max_vertical":
        value = abs(a[0] - b[0])
    elif selector == "max_horizontal":
        value = abs(a[1] - b[1])
    elif selector == "nearest_start":
        value = -min(_manhattan(start, a), _manhattan(start, b))
    elif selector == "nearest_goal":
        value = -min(_manhattan(goal, a), _manhattan(goal, b))
    elif selector == "fastest_single":
        value = -min(_manhattan(start, a) + _manhattan(b, goal),
                     _manhattan(start, b) + _manhattan(a, goal))
    elif selector == "first_scan":
        value = -min(a, b)[0] * 100 - min(a, b)[1]
    elif selector == "last_scan":
        value = max(a, b)[0] * 100 + max(a, b)[1]
    else:
        raise ValueError(f"unknown selector {selector!r}")
    # max() plus -color gives deterministic lower-color tie breaking.
    return float(value), -color


def selected_portal_color(grid: Grid, selector: str) -> int:
    pairs = portal_pairs(grid)
    if selector == "lowest_color":
        return min(pairs)
    if selector == "highest_color":
        return max(pairs)
    return max(pairs, key=lambda color: _selector_key(grid, selector, color))


def _path(grid: Grid, active_colors: set[int]) -> list[Cell] | None:
    _validate_grid(grid)
    start, goal = _start_goal(grid)
    pairs = portal_pairs(grid)
    exits: dict[Cell, Cell] = {}
    for color, (a, b) in pairs.items():
        if color in active_colors:
            exits[a] = b
            exits[b] = a
    h, w = len(grid), len(grid[0])
    queue: deque[Cell] = deque([start])
    previous: dict[Cell, Cell | None] = {start: None}
    while queue and goal not in previous:
        row, col = queue.popleft()
        for dr, dc in CARDINAL:
            nr, nc = row + dr, col + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            nxt = exits.get((nr, nc), (nr, nc))
            if nxt not in previous:
                previous[nxt] = (row, col)
                queue.append(nxt)
    if goal not in previous:
        return None
    result: list[Cell] = []
    current: Cell | None = goal
    while current is not None:
        result.append(current)
        current = previous[current]
    result.reverse()
    return result


def _paint(grid: Grid, path: list[Cell] | None) -> Grid:
    output = _copy(grid)
    if path is None:
        return output
    for row, col in path:
        if output[row][col] == 0:
            output[row][col] = 7
    return output


def apply_policy(grid: Grid, policy: str) -> Grid:
    if policy == "all_pairs":
        active = set(portal_pairs(grid))
    elif policy == "widest_pair_only":
        active = {widest_portal_color(grid)}
    else:
        raise ValueError(f"unknown portal policy {policy!r}")
    return _paint(grid, _path(grid, active))


def apply_fixed_portal_color(grid: Grid, color: int) -> Grid:
    if type(color) is not int or color not in PORTAL_COLORS:
        raise ValueError("fixed portal color must be 4, 5, or 6")
    return _paint(grid, _path(grid, {color}))


def apply_selector(grid: Grid, selector: str) -> Grid:
    if selector == "no_portals":
        return _paint(grid, _path(grid, set()))
    if selector.startswith("fixed_"):
        return apply_fixed_portal_color(grid, int(selector[-1]))
    return apply_fixed_portal_color(grid, selected_portal_color(grid, selector))


def _transform(grid: Grid, code: int) -> Grid:
    result = _copy(grid)
    if code >= 4:
        result = [list(reversed(row)) for row in result]
        code -= 4
    for _ in range(code):
        result = [list(row) for row in zip(*reversed(result))]
    return result


def _chain_scene(seed: int) -> Grid:
    """Two barriers require two distinct portals; one-pair shortcuts fail."""
    h, w = 12, 18
    grid = [[0] * w for _ in range(h)]
    for row in range(h):
        grid[row][6] = 8
        grid[row][12] = 8
    grid[1][1] = 2
    grid[1][16] = 3
    # Color 4 is the widest pair and crosses the first barrier.
    for row, col in ((10, 1), (1, 11)):
        grid[row][col] = 4
    # Color 5 crosses the second barrier; both 4 and 5 are needed.
    for row, col in ((2, 8), (2, 15)):
        grid[row][col] = 5
    # Color 6 is a same-zone distractor.
    for row, col in ((9, 8), (9, 10)):
        grid[row][col] = 6
    base_all = apply_policy(grid, "all_pairs")
    base_wide = apply_policy(grid, "widest_pair_only")
    if base_all == base_wide or _path(grid, {4, 5, 6}) is None or _path(grid, {4}) is not None:
        raise AssertionError("invalid chained portal template")
    rng = _rng(seed, "demo", 0, "chain-transform")
    transformed = _transform(grid, rng.randrange(8))
    # Add one harmless wall keyed by seed to avoid repeated visible scenes.
    path_cells = set(_path(transformed, set(portal_pairs(transformed))) or [])
    path_cells |= set(_path(transformed, {widest_portal_color(transformed)}) or [])
    candidates = [(r, c) for r, row in enumerate(transformed) for c, value in enumerate(row)
                  if value == 0 and (r, c) not in path_cells]
    if candidates:
        r, c = rng.choice(candidates)
        trial = _copy(transformed)
        trial[r][c] = 8
        if (apply_policy(trial, "all_pairs") == apply_policy(transformed, "all_pairs")
                and apply_policy(trial, "widest_pair_only") == apply_policy(transformed, "widest_pair_only")):
            transformed = trial
    return transformed


def _profile(role: str, index: int) -> tuple[int, int, str, bool]:
    if role == "demo":
        profiles = [
            (13, 17, "vertical", False),
            (14, 16, "horizontal", False),
            (12, 19, "vertical", True),
            (15, 18, "horizontal", False),
            (16, 20, "vertical", False),
            (14, 21, "horizontal", True),
        ]
        return profiles[index % len(profiles)]
    if role == "query":
        profiles = [
            (8, 18, "vertical", True),
            (15, 14, "horizontal", True),
            (18, 20, "vertical", False),
            (30, 30, "horizontal", True),
        ]
        return profiles[index % len(profiles)]
    raise ValueError("role must be 'demo' or 'query'")


def _single_barrier_scene(seed: int, role: str, index: int) -> Grid:
    height, width, orientation, boundary = _profile(role, index)
    rng = _rng(seed, role, index)
    if orientation == "vertical":
        barrier = width // 2 + rng.choice((-1, 0, 1))
        low = [(r, c) for r in range(height) for c in range(barrier)]
        high = [(r, c) for r in range(height) for c in range(barrier + 1, width)]
        start = (rng.randrange(height), 0 if boundary else 1)
        goal = (rng.randrange(height), width - 1 if boundary else width - 2)
    else:
        barrier = height // 2 + rng.choice((-1, 0, 1))
        low = [(r, c) for r in range(barrier) for c in range(width)]
        high = [(r, c) for r in range(barrier + 1, height) for c in range(width)]
        start = (0 if boundary else 1, rng.randrange(width))
        goal = (height - 1 if boundary else height - 2, rng.randrange(width))
    low = [p for p in low if p not in {start, goal}]
    high = [p for p in high if p not in {start, goal}]

    target_widest = PORTAL_COLORS[index % 3] if role == "demo" else PORTAL_COLORS[(index + seed) % 3]
    target_fast = PORTAL_COLORS[(PORTAL_COLORS.index(target_widest) + 1) % 3]
    remaining_color = next(color for color in PORTAL_COLORS if color not in {target_widest, target_fast})

    for attempt in range(20000):
        left = rng.sample(low, 3)
        right = rng.sample(high, 3)
        rng.shuffle(right)
        raw_pairs = list(zip(left, right))
        spans = [_manhattan(a, b) for a, b in raw_pairs]
        if len(set(spans)) != 3:
            continue
        costs = [min(_manhattan(start, a) + _manhattan(b, goal),
                     _manhattan(start, b) + _manhattan(a, goal)) for a, b in raw_pairs]
        widest_i = max(range(3), key=lambda i: spans[i])
        fast_i = min(range(3), key=lambda i: costs[i])
        if widest_i == fast_i or costs[widest_i] < costs[fast_i] + 3:
            continue
        other_i = next(i for i in range(3) if i not in {widest_i, fast_i})
        assigned = {
            target_widest: raw_pairs[widest_i],
            target_fast: raw_pairs[fast_i],
            remaining_color: raw_pairs[other_i],
        }
        grid = [[0] * width for _ in range(height)]
        if orientation == "vertical":
            for row in range(height):
                grid[row][barrier] = 8
        else:
            for col in range(width):
                grid[barrier][col] = 8
        grid[start[0]][start[1]] = 2
        grid[goal[0]][goal[1]] = 3
        for color, pair in assigned.items():
            for row, col in pair:
                grid[row][col] = color
        if widest_portal_color(grid) != target_widest:
            continue
        all_output = apply_policy(grid, "all_pairs")
        wide_output = apply_policy(grid, "widest_pair_only")
        if all_output == wide_output or _path(grid, set(PORTAL_COLORS)) is None or _path(grid, {target_widest}) is None:
            continue
        used = {grid[r][c] for r, c in (_path(grid, set(PORTAL_COLORS)) or []) if grid[r][c] in PORTAL_COLORS}
        if target_fast not in used:
            continue
        # The first three demos deliberately cross different nuisance selectors.
        if role == "demo" and index % 3 == 1:
            # Cross metric, start/goal proximity, scan order and axis-only
            # shortcuts while keeping the true Manhattan selector unchanged.
            for rival_selector in (
                "widest_euclidean",
                "max_horizontal",
                "nearest_start",
                "nearest_goal",
                "last_scan",
            ):
                if selected_portal_color(grid, rival_selector) == target_widest:
                    break
            else:
                rival_selector = None
            if rival_selector is not None:
                continue
        if role == "demo" and index % 3 == 2:
            if selected_portal_color(grid, "max_vertical") == target_widest:
                continue
            if selected_portal_color(grid, "first_scan") == target_widest:
                continue

        # Add bounded distractor walls outside both selected paths; preserve labels.
        protected = set(_path(grid, set(PORTAL_COLORS)) or []) | set(_path(grid, {target_widest}) or [])
        candidates = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                      if value == 0 and (r, c) not in protected]
        count = min(len(candidates), 1 + ((seed + index) % 4))
        if count:
            trial = _copy(grid)
            for row, col in rng.sample(candidates, count):
                trial[row][col] = 8
            if (apply_policy(trial, "all_pairs") == all_output
                    and apply_policy(trial, "widest_pair_only") == wide_output
                    and widest_portal_color(trial) == target_widest):
                grid = trial
        return grid
    raise ValueError(f"could not construct {role} scene {index} for seed {seed}")


@lru_cache(maxsize=1024)
def _build_cached(seed: int, role: str, index: int) -> tuple[tuple[int, ...], ...]:
    if type(seed) is not int or seed < 0 or type(index) is not int or index < 0:
        raise TypeError("seed and index must be nonnegative exact integers")
    if role == "demo" and index == 0:
        grid = _chain_scene(seed)
    else:
        grid = _single_barrier_scene(seed, role, index)
    _validate_grid(grid)
    return _grid_tuple(grid)


def build_scene(seed: int, role: str, index: int) -> Grid:
    return [list(row) for row in _build_cached(seed, role, index)]
