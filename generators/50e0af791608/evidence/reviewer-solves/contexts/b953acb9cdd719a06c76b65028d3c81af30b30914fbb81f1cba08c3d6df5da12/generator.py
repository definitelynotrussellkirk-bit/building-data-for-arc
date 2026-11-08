"""Semantic generator for ARC task 50e0af791608.

Gray cells are impassable maze walls, red is the unique start, green is the
unique goal, and zero cells are traversable.  Recolor every zero cell lying
on at least one shortest cardinal path cyan.  A cell belongs to that union
exactly when its start distance plus goal distance equals the optimum.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "50e0af791608"
TASK_ID = "50e0af791608"
VERSION = "3.0.0"
RULE_HASH = "f0c150157293"
SUMMARY = "Highlight the union of every shortest red-to-green path through a gray-walled maze."
INVARIANTS = [
    "there is exactly one red start and one green goal",
    "gray cells are impassable and all other input cells are traversable",
    "a zero cell is cyan exactly when its two endpoint distances sum to the optimal distance",
    "the output contains the union of all tied shortest paths rather than one selected route",
    "markers, walls, and zero cells outside the shortest-path union remain unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "horizontal_corridor_pocket",
    "vertical_corridor_pocket",
    "open_room",
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
        "default": "five exact-public and ten recoverable gray-maze lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|horizontal_corridor_pocket|vertical_corridor_pocket|open_room|symmetric_block_horizontal|top_shorter_block|bottom_shorter_block|symmetric_block_vertical|left_shorter_block|right_shorter_block|twin_gates",
    }
}

_PUBLIC_ROWS = (
    "55555555555/52000500005/50000000505/50000000055/50000005005/55000050055/50050500055/50005000035/55555555555",
    "55555555555/52000555005/50050050555/50550055505/55000005055/50550000055/50005500005/50500550035/55555555555",
    "55555555555/52000005005/50005000005/55000005005/55005050055/50050550005/50000505505/55000000535/55555555555",
    "55555555555/52500050055/50050005055/50000000505/55500550005/50000000005/50005000055/50050050035/55555555555",
    "55555555555/52550550005/50505555005/50050000055/50005050005/50000000005/55005500005/50050505035/55555555555",
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
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["input dimensions must be between 7 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2, 3, 5) for row in grid for value in row):
        return ["input cells must be literal 0, 2, 3, or 5"]
    return []


def _distances(grid, origin):
    height, width = len(grid), len(grid[0])
    result = {origin: 0}
    queue = deque([origin])
    while queue:
        row, col = queue.popleft()
        for drow, dcol in _DELTAS:
            neighbor = row + drow, col + dcol
            if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width and grid[neighbor[0]][neighbor[1]] != 5 and neighbor not in result:
                result[neighbor] = result[(row, col)] + 1
                queue.append(neighbor)
    return result


def _bbox(cells):
    return min(row for row, _ in cells), min(col for _, col in cells), max(row for row, _ in cells), max(col for _, col in cells)


def _extract_facts(grid):
    starts = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 2)
    goals = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 3)
    if len(starts) != 1 or len(goals) != 1:
        return {"errors": [f"expected exactly one red start and green goal, got {len(starts)} and {len(goals)}"]}
    start, goal = starts[0], goals[0]
    from_start, from_goal = _distances(grid, start), _distances(grid, goal)
    optimal = from_start.get(goal)
    union = tuple(sorted(cell for cell, distance in from_start.items() if grid[cell[0]][cell[1]] == 0 and cell in from_goal and optimal is not None and distance + from_goal[cell] == optimal))
    output = [list(row) for row in grid]
    for row, col in union:
        output[row][col] = 8
    reachable_zeros = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 0 and (row, col) in from_start}
    off_shortest = tuple(sorted(reachable_zeros - set(union)))
    return {
        "errors": [], "height": len(grid), "width": len(grid[0]), "start": start, "goal": goal,
        "from_start": from_start, "from_goal": from_goal, "optimal_distance": optimal,
        "union": union, "off_shortest": off_shortest, "output": output,
    }


def rule_mirror(grid):
    """Exact Python mirror of the canonical Racket distance-sum rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _boundary_is_walled(grid):
    return all(value == 5 for value in grid[0] + grid[-1]) and all(row[0] == row[-1] == 5 for row in grid)


def _corridor_profile(grid, facts):
    height, width = facts["height"], facts["width"]
    traversable = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 5}
    start, goal = facts["start"], facts["goal"]
    if start[0] == goal[0] and {col for row, col in traversable if row == start[0]} == set(range(1, width - 1)):
        extras = traversable - {(start[0], col) for col in range(1, width - 1)}
        if extras and len({col for _, col in extras}) == 1:
            col = next(iter({col for _, col in extras}))
            rows = sorted(row for row, _ in extras)
            if rows == list(range(min(rows), max(rows) + 1)) and (min(rows) == start[0] + 1 or max(rows) == start[0] - 1):
                return "horizontal_corridor_pocket"
    if start[1] == goal[1] and {row for row, col in traversable if col == start[1]} == set(range(1, height - 1)):
        extras = traversable - {(row, start[1]) for row in range(1, height - 1)}
        if extras and len({row for row, _ in extras}) == 1:
            row = next(iter({row for row, _ in extras}))
            cols = sorted(col for _, col in extras)
            if cols == list(range(min(cols), max(cols) + 1)) and (min(cols) == start[1] + 1 or max(cols) == start[1] - 1):
                return "vertical_corridor_pocket"
    return None


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    corridor = _corridor_profile(grid, facts)
    if corridor:
        return corridor
    height, width = facts["height"], facts["width"]
    inner_walls = {(row, col) for row in range(1, height - 1) for col in range(1, width - 1) if grid[row][col] == 5}
    if not inner_walls:
        return "open_room"
    start, goal = facts["start"], facts["goal"]
    row0, col0, row1, col1 = _bbox(inner_walls)
    solid = len(inner_walls) == (row1 - row0 + 1) * (col1 - col0 + 1)
    if solid:
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
    barrier_cols = {col for _, col in inner_walls}
    if len(barrier_cols) == 1 and start[0] == goal[0] and start[1] < next(iter(barrier_cols)) < goal[1]:
        barrier = next(iter(barrier_cols))
        gaps = {row for row in range(1, height - 1) if grid[row][barrier] == 0}
        if len(gaps) == 2 and all(grid[row][col] != 5 for row in range(1, height - 1) for col in range(1, width - 1) if col != barrier):
            return "twin_gates"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    if not _boundary_is_walled(grid):
        errors.append("the complete outer boundary must be gray wall")
    if facts["optimal_distance"] is None:
        errors.append("green goal must be reachable from red start")
    if not facts["union"]:
        errors.append("at least one zero cell must lie on a shortest path")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared gray-maze profile")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
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
        None: ((9, 15), (11, 17)),
        "easy": ((9, 11), (11, 13)),
        "medium": ((11, 14), (13, 16)),
        "hard": ((14, 18), (16, 20)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    return rng.randint(h0, h1), rng.randint(w0, w1)


def _walls(height, width):
    return [[5 for _ in range(width)] for _ in range(height)]


def _open_interior(height, width):
    grid = _walls(height, width)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            grid[row][col] = 0
    return grid


def _corridor_scene(difficulty, profile, rng):
    height, width = _dimensions(difficulty, rng)
    if profile == "vertical_corridor_pocket" and height < width:
        height, width = width, height
    grid = _walls(height, width)
    if profile == "horizontal_corridor_pocket":
        row = height // 2
        for col in range(1, width - 1):
            grid[row][col] = 0
        branch_col = rng.randint(3, width - 4)
        direction = rng.choice((-1, 1))
        length = rng.randint(2, max(2, min(4, height // 2 - 1)))
        for step in range(1, length + 1):
            grid[row + direction * step][branch_col] = 0
        start, goal = (row, 1), (row, width - 2)
    else:
        col = width // 2
        for row in range(1, height - 1):
            grid[row][col] = 0
        branch_row = rng.randint(3, height - 4)
        direction = rng.choice((-1, 1))
        length = rng.randint(2, max(2, min(4, width // 2 - 1)))
        for step in range(1, length + 1):
            grid[branch_row][col + direction * step] = 0
        start, goal = (1, col), (height - 2, col)
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    return grid


def _open_room(difficulty, rng):
    height, width = _dimensions(difficulty, rng)
    grid = _open_interior(height, width)
    if rng.random() < 0.5:
        start, goal = (1, 1), (height - 2, width - 2)
    else:
        start, goal = (1, width - 2), (height - 2, 1)
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    return grid


def _block_scene(difficulty, profile, rng):
    height, width = _dimensions(difficulty, rng)
    grid = _open_interior(height, width)
    horizontal = profile in {"symmetric_block_horizontal", "top_shorter_block", "bottom_shorter_block"}
    if horizontal:
        wall_h = 3 if height < 14 else rng.choice((3, 5))
        wall_w = rng.randint(2, min(4, width - 7))
    else:
        wall_h = rng.randint(2, min(4, height - 7))
        wall_w = 3 if width < 14 else rng.choice((3, 5))
    row0 = rng.randint(3, height - wall_h - 3)
    col0 = rng.randint(3, width - wall_w - 3)
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
    grid[start[0]][start[1]], grid[goal[0]][goal[1]] = 2, 3
    return grid


def _twin_gates(difficulty, rng):
    height, width = _dimensions(difficulty, rng)
    if height % 2 == 0:
        height += 1
    grid = _open_interior(height, width)
    center, barrier = height // 2, width // 2
    gaps = {center - 2, center + 2}
    for row in range(1, height - 1):
        if row not in gaps:
            grid[row][barrier] = 5
    grid[center][1], grid[center][width - 2] = 2, 3
    return grid


def _general_scene(difficulty, profile, rng):
    for _ in range(100):
        if profile in {"horizontal_corridor_pocket", "vertical_corridor_pocket"}:
            grid = _corridor_scene(difficulty, profile, rng)
        elif profile == "open_room":
            grid = _open_room(difficulty, rng)
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
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 6)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
