"""Semantic generator for ARC task ae148d180b74.

Treat gray (5) cells as walls.  Compute distances through every non-wall cell
from the first red (2) start and first green (3) goal.  Recolor a black (0)
cell cyan (8) exactly when it belongs to at least one shortest 4-neighbor path
between the markers.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "ae148d180b74"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "4fb01d27e94e"
SUMMARY = "Mark every black cell lying on any shortest non-wall path between red and green."
INVARIANTS = [
    "color 5 is the only wall color",
    "exactly one red start and one green goal are calibrated",
    "movement is 4-connected through every non-wall cell",
    "only black cells on the union of all shortest paths become cyan",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "unique_straight",
    "unique_one_turn",
    "unique_winding",
    "unique_with_decoys",
    "multi_open",
    "multi_with_decoys",
    "multi_detour",
    "multi_detour_decoys",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and eight observable shortest-path topologies",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_train_1": "20000000000/00005000000/00005000500/00005000500/00005000000/00000000500/00000000500/00005000500/00005000500/00005000503/00000000000",
    "public_train_2": "00000000000/00005500000/00005500003/00005500000/05555555550/20000500000/00005500000/00005000000/05505505550/00005500000/00000000000",
    "public_train_3": "000000000000/000005050000/000005050000/000000000000/000000050000/000005050000/000005050000/000005050000/200005050003/000000000000",
    "public_train_4": "00000000000/00005050500/00005050503/00005050500/00005000000/00000050500/20000050500/00005050500/00000000000",
    "public_test_1": "00000000000/20055000000/00055000003/00555555550/00050000000/00055000000/00055000000/00055000000/00555550550/00055000000/00000000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _distances(grid, start):
    height, width = len(grid), len(grid[0])
    distance = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = row + dr, col + dc
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and grid[neighbor[0]][neighbor[1]] != 5
                and neighbor not in distance
            ):
                distance[neighbor] = distance[(row, col)] + 1
                queue.append(neighbor)
    return distance


def _path_count(grid, start, goal, distance):
    ways = {start: 1}
    for cell in sorted(distance, key=lambda p: distance[p]):
        row, col = cell
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = row + dr, col + dc
            if distance.get(neighbor) == distance[cell] + 1:
                ways[neighbor] = min(2, ways.get(neighbor, 0) + ways[cell])
    return ways.get(goal, 0)


def _unique_turns(union, start, goal):
    previous = None
    current = start
    directions = []
    while current != goal:
        options = [
            cell
            for cell in ((current[0] - 1, current[1]), (current[0] + 1, current[1]), (current[0], current[1] - 1), (current[0], current[1] + 1))
            if cell in union and cell != previous
        ]
        if len(options) != 1:
            return None
        nxt = options[0]
        directions.append((nxt[0] - current[0], nxt[1] - current[1]))
        previous, current = current, nxt
    return sum(first != second for first, second in zip(directions, directions[1:]))


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    starts, goals = _positions(grid, 2), _positions(grid, 3)
    if not starts or not goals:
        raise ValueError("grid requires red and green markers")
    start, goal = starts[0], goals[0]
    ds, dt = _distances(grid, start), _distances(grid, goal)
    output = [list(row) for row in grid]
    if goal not in ds:
        return output
    target = ds[goal]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            cell = row, col
            if grid[row][col] == 0 and cell in ds and cell in dt and ds[cell] + dt[cell] == target:
                output[row][col] = 8
    return output


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    unexpected = sorted({value for row in grid for value in row} - {0, 2, 3, 5})
    if unexpected:
        errors.append(f"unexpected colors: {unexpected}")
    starts, goals = _positions(grid, 2), _positions(grid, 3)
    if len(starts) != 1:
        errors.append(f"expected exactly one red start, found {len(starts)}")
    if len(goals) != 1:
        errors.append(f"expected exactly one green goal, found {len(goals)}")
    if len(starts) != 1 or len(goals) != 1:
        return result
    start, goal = starts[0], goals[0]
    ds, dt = _distances(grid, start), _distances(grid, goal)
    if goal not in ds:
        errors.append("start and goal must be connected")
        return result
    target = ds[goal]
    union = {cell for cell in ds if cell in dt and ds[cell] + dt[cell] == target}
    passable = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 5}
    decoys = set(ds) - union
    disconnected = passable - set(ds)
    path_count = _path_count(grid, start, goal, ds)
    turns = _unique_turns(union, start, goal) if path_count == 1 else None
    manhattan = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    if path_count == 1 and not decoys and turns == 0:
        general = "unique_straight"
    elif path_count == 1 and not decoys and turns == 1 and target == manhattan:
        general = "unique_one_turn"
    elif path_count == 1 and not decoys and turns is not None and turns >= 2:
        general = "unique_winding"
    elif path_count == 1 and decoys:
        general = "unique_with_decoys"
    elif path_count > 1 and target == manhattan and not decoys:
        general = "multi_open"
    elif path_count > 1 and target == manhattan and decoys:
        general = "multi_with_decoys"
    elif path_count > 1 and target > manhattan and not decoys:
        general = "multi_detour"
    elif path_count > 1 and target > manhattan and decoys:
        general = "multi_detour_decoys"
    else:
        general = None
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or general
    if profile not in SCENE_PROFILES:
        errors.append("shortest-path topology does not match a declared profile")
    output = rule_mirror(grid)
    result.update(
        {
            "start": start,
            "goal": goal,
            "distance": target,
            "manhattan": manhattan,
            "path_count_class": path_count,
            "shortest_union": union,
            "marked_cells": {cell for cell in union if grid[cell[0]][cell[1]] == 0},
            "decoy_cells": decoys,
            "disconnected_cells": disconnected,
            "turns": turns,
            "wall_count": sum(value == 5 for row in grid for value in row),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _pattern(rng, profile, band):
    spans = {"easy": (4, 8), "medium": (5, 8), "hard": (7, 11)}
    low, high = spans[band]
    width = rng.randint(low, high)
    if profile == "unique_straight":
        cells = {(0, col) for col in range(width)}
        start, goal = (0, 0), (0, width - 1)
    elif profile == "unique_one_turn":
        height = rng.randint(3, max(3, width - 1))
        cells = {(0, col) for col in range(width)} | {(row, width - 1) for row in range(1, height)}
        start, goal = (0, 0), (height - 1, width - 1)
    elif profile in ("unique_winding", "unique_with_decoys"):
        cells = {(0, col) for col in range(width)} | {(1, width - 1)} | {(2, col) for col in range(width)} | {(3, 0)} | {(4, col) for col in range(width)}
        start, goal = (0, 0), (4, width - 1)
        if profile == "unique_with_decoys":
            cells |= {(5, width // 2), (6, width // 2)}
            cells.add((4, width // 2))
    elif profile in ("multi_open", "multi_with_decoys"):
        height = rng.randint(3, min(6, high))
        cells = {(row, col) for row in range(height) for col in range(width)}
        start, goal = (0, 0), (height - 1, width - 1)
        if profile == "multi_with_decoys":
            cells |= {(height, width // 2), (height + 1, width // 2)}
    else:
        height = 5
        cells = {(2, 0), (2, width - 1)}
        cells |= {(row, 0) for row in range(5)} | {(row, width - 1) for row in range(5)}
        cells |= {(0, col) for col in range(width)} | {(4, col) for col in range(width)}
        start, goal = (2, 0), (2, width - 1)
        if profile == "multi_detour_decoys":
            cells |= {(-1, width // 2), (-2, width // 2)}
            # The outward branch attaches to the upper shortest route and is
            # separated from both markers, so it cannot create a third route.
    return cells, start, goal


def _transform(cells, start, goal, turns, reflect):
    all_cells = set(cells)
    s, g = start, goal
    for _ in range(turns):
        all_cells = {(col, -row) for row, col in all_cells}
        s, g = (s[1], -s[0]), (g[1], -g[0])
    if reflect:
        all_cells = {(row, -col) for row, col in all_cells}
        s, g = (s[0], -s[1]), (g[0], -g[1])
    min_row = min(row for row, _ in all_cells)
    min_col = min(col for _, col in all_cells)
    shifted = {(row - min_row, col - min_col) for row, col in all_cells}
    return shifted, (s[0] - min_row, s[1] - min_col), (g[0] - min_row, g[1] - min_col)


def _general(rng, profile, band):
    cells, start, goal = _pattern(rng, profile, band)
    cells, start, goal = _transform(cells, start, goal, rng.randrange(4), bool(rng.randrange(2)))
    local_h = max(row for row, _ in cells) + 1
    local_w = max(col for _, col in cells) + 1
    margins = {"easy": (2, 4), "medium": (2, 4), "hard": (2, 5)}
    low, high = margins[band]
    top, bottom = rng.randint(low, high), rng.randint(low, high)
    left, right = rng.randint(low, high), rng.randint(low, high)
    height = top + local_h + 2 + bottom
    width = left + local_w + 2 + right
    grid = [[0] * width for _ in range(height)]
    for row in range(top, top + local_h + 2):
        for col in range(left, left + local_w + 2):
            grid[row][col] = 5
    for row, col in cells:
        grid[top + 1 + row][left + 1 + col] = 0
    grid[top + 1 + start[0]][left + 1 + start[1]] = 2
    grid[top + 1 + goal[0]][left + 1 + goal[1]] = 3
    for row, col in ((0, 0), (0, width - 1), (height - 1, 0)):
        grid[row][col] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    profile = requested or ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)])
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
