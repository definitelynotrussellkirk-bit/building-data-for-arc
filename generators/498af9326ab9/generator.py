"""Semantic generator for ARC task 498af9326ab9.

Gray cells are walls, blue is the start, red is the goal, and zero cells are
walkable.  Every zero cell lying on at least one shortest cardinal path from
start to goal becomes cyan.  Equivalently, a reachable zero cell is marked
when its distance from the start plus its distance from the goal equals the
start-to-goal distance.  Markers and walls remain unchanged.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "498af9326ab9"
TASK_ID = "498af9326ab9"
VERSION = "3.0.0"
RULE_HASH = "067c9281e33e"
SUMMARY = "Mark the union of all shortest start-to-goal paths through zero cells while preserving markers and gray walls."
INVARIANTS = [
    "there is exactly one blue start and one red goal",
    "gray cells are impassable and all other input cells are traversable",
    "a zero cell is cyan exactly when start-distance plus goal-distance equals the optimal distance",
    "the output is the union of all shortest paths, not an arbitrary single path",
    "start, goal, walls, and zero cells outside the shortest-path union remain unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "horizontal_line",
    "vertical_line",
    "open_rectangle",
    "symmetric_block_horizontal",
    "top_shorter_block",
    "bottom_shorter_block",
    "symmetric_block_vertical",
    "left_shorter_block",
    "right_shorter_block",
    "twin_gates",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten recoverable shortest-path-union lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|horizontal_line|vertical_line|open_rectangle|symmetric_block_horizontal|top_shorter_block|bottom_shorter_block|symmetric_block_vertical|left_shorter_block|right_shorter_block|twin_gates",
    }
}

_PUBLIC_ROWS = (
    "000000000/000000000/000555000/010555020/000555000/000000000/000000000",
    "000000000/000050000/000050000/000050000/010000020/000050000/000050000/000050000/000000000",
    "000010000/000000000/005555500/005000500/005000500/005555500/000000000/000020000",
    "000000000/000010000/000000000/005555500/005555500/005555500/000000000/000020000/000000000",
    "0000000000/0000000000/0000550000/0000550000/0100550020/0000550000/0000000000/0000000000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return ["input dimensions must be between 5 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1, 2, 5) for row in grid for value in row):
        return ["input cells must be literal 0, 1, 2, or 5"]
    return []


def _distances(grid, origin):
    height, width = len(grid), len(grid[0])
    distances = {origin: 0}
    queue = deque((origin,))
    while queue:
        row, col = queue.popleft()
        for drow, dcol in _DELTAS:
            neighbor = row + drow, col + dcol
            if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width and grid[neighbor[0]][neighbor[1]] != 5 and neighbor not in distances:
                distances[neighbor] = distances[(row, col)] + 1
                queue.append(neighbor)
    return distances


def _bbox(cells):
    return min(row for row, _ in cells), min(col for _, col in cells), max(row for row, _ in cells), max(col for _, col in cells)


def _extract_facts(grid):
    starts = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 1)
    goals = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 2)
    if len(starts) != 1 or len(goals) != 1:
        return {"errors": [f"expected exactly one start and goal, got {len(starts)} and {len(goals)}"]}
    start, goal = starts[0], goals[0]
    from_start, from_goal = _distances(grid, start), _distances(grid, goal)
    optimal = from_start.get(goal)
    union = tuple(
        sorted(
            cell
            for cell, distance in from_start.items()
            if grid[cell[0]][cell[1]] == 0 and cell in from_goal and optimal is not None and distance + from_goal[cell] == optimal
        )
    )
    output = [list(row) for row in grid]
    for row, col in union:
        output[row][col] = 8
    walls = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 5)
    wall_bbox = _bbox(walls) if walls else None
    solid_wall = bool(walls and len(walls) == (wall_bbox[2] - wall_bbox[0] + 1) * (wall_bbox[3] - wall_bbox[1] + 1))
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "start": start,
        "goal": goal,
        "walls": walls,
        "wall_bbox": wall_bbox,
        "solid_wall": solid_wall,
        "from_start": from_start,
        "from_goal": from_goal,
        "optimal_distance": optimal,
        "union": union,
        "output": output,
    }


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    start, goal = facts["start"], facts["goal"]
    if not facts["walls"]:
        if start[0] == goal[0]:
            return "horizontal_line"
        if start[1] == goal[1]:
            return "vertical_line"
        return "open_rectangle"
    if not facts["solid_wall"]:
        return "twin_gates"
    row0, col0, row1, col1 = facts["wall_bbox"]
    if start[0] == goal[0] and start[1] < col0 <= col1 < goal[1]:
        if start[0] == (row0 + row1) // 2:
            return "symmetric_block_horizontal"
        if start[0] == row0:
            return "top_shorter_block"
        if start[0] == row1:
            return "bottom_shorter_block"
    if start[1] == goal[1] and start[0] < row0 <= row1 < goal[0]:
        if start[1] == (col0 + col1) // 2:
            return "symmetric_block_vertical"
        if start[1] == col0:
            return "left_shorter_block"
        if start[1] == col1:
            return "right_shorter_block"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    if facts["optimal_distance"] is None:
        errors.append("start and goal must be reachable")
    if not facts["union"]:
        errors.append("at least one zero cell must lie on a shortest path")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared shortest-path profile")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    if any(facts["output"][row][col] != grid[row][col] for row, col in facts["walls"] + (facts["start"], facts["goal"])):
        errors.append("walls and markers must remain unchanged")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimensions(difficulty, rng):
    bands = {
        None: ((7, 14), (8, 15)),
        "easy": ((7, 9), (8, 10)),
        "medium": ((9, 12), (10, 13)),
        "hard": ((12, 16), (13, 16)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    return rng.randint(h0, h1), rng.randint(w0, w1)


def _empty_scene(difficulty, rng):
    height, width = _dimensions(difficulty, rng)
    return [[0 for _ in range(width)] for _ in range(height)]


def _open_scene(difficulty, profile, rng):
    grid = _empty_scene(difficulty, rng)
    height, width = len(grid), len(grid[0])
    if profile == "horizontal_line":
        row = rng.randint(1, height - 2)
        start, goal = (row, 1), (row, width - 2)
    elif profile == "vertical_line":
        col = rng.randint(1, width - 2)
        start, goal = (1, col), (height - 2, col)
    else:
        start = rng.randint(1, max(1, height // 3)), rng.randint(1, max(1, width // 3))
        goal = rng.randint(max(start[0] + 2, 2 * height // 3), height - 2), rng.randint(max(start[1] + 3, 2 * width // 3), width - 2)
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 1, 2
    return grid


def _block_scene(difficulty, profile, rng):
    grid = _empty_scene(difficulty, rng)
    if len(grid) < 8:
        grid.extend([[0 for _ in grid[0]] for _ in range(8 - len(grid))])
    if len(grid[0]) < 8:
        for row in grid:
            row.extend([0] * (8 - len(row)))
    height, width = len(grid), len(grid[0])
    horizontal = profile in {"symmetric_block_horizontal", "top_shorter_block", "bottom_shorter_block"}
    if horizontal:
        wall_h = 3 if height < 12 else rng.choice((3, 5))
        wall_w = rng.randint(2, min(4, width - 6))
    else:
        wall_h = rng.randint(2, min(4, height - 6))
        wall_w = 3 if width < 12 else rng.choice((3, 5))
    row0 = rng.randint(2, height - wall_h - 2)
    col0 = rng.randint(2, width - wall_w - 2)
    row1, col1 = row0 + wall_h - 1, col0 + wall_w - 1
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            grid[row][col] = 5
    if horizontal:
        marker_row = (row0 + row1) // 2 if profile == "symmetric_block_horizontal" else row0 if profile == "top_shorter_block" else row1
        start, goal = (marker_row, 1), (marker_row, width - 2)
    else:
        marker_col = (col0 + col1) // 2 if profile == "symmetric_block_vertical" else col0 if profile == "left_shorter_block" else col1
        start, goal = (1, marker_col), (height - 2, marker_col)
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 1, 2
    return grid


def _twin_gates(difficulty, rng):
    grid = _empty_scene(difficulty, rng)
    if len(grid) < 9:
        grid.extend([[0 for _ in grid[0]] for _ in range(9 - len(grid))])
    if len(grid) % 2 == 0:
        grid.append([0 for _ in grid[0]])
    height, width = len(grid), len(grid[0])
    center, barrier = height // 2, width // 2
    gaps = {center - 2, center + 2}
    for row in range(height):
        if row not in gaps:
            grid[row][barrier] = 5
    grid[center][1], grid[center][width - 2] = 1, 2
    return grid


def _general_scene(difficulty, profile, rng):
    for _ in range(100):
        if profile in ("horizontal_line", "vertical_line", "open_rectangle"):
            grid = _open_scene(difficulty, profile, rng)
        elif profile == "twin_gates":
            grid = _twin_gates(difficulty, rng)
        else:
            grid = _block_scene(difficulty, profile, rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    weighted = PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 6
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
