"""Input generator for ``ad9405621c3d``.

The selected authority paints the U,D,L,R BFS path between the only two matching
non-wall endpoints.  This sampler builds connected gray-wall mazes with four
scheduled topology profiles.  One profile deliberately looks like the public
edge-hugging examples; the other three put the selected path in the interior,
so a solver cannot succeed by treating the maze interior as decoration.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad9405621c3d"
TASK_ID = GENERATOR_ID
RULE_HASH = "f19a9c2c6081"
VERSION = "3.0.0"
SUMMARY = (
    "Generate color-5 wall mazes containing exactly two matching colored "
    "endpoints.  Four consecutive samples cover an edge-hugging route, a deep "
    "serpentine detour, an interior endpoint pair, and a multiple-shortest-path "
    "case.  The authority paints the first U,D,L,R BFS shortest path through "
    "zero cells with the endpoint color."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the grid is 6..9 by 7..9 and uses exactly background 0, wall 5, and one endpoint color",
    "the non-{0,5} endpoint color appears exactly twice",
    "the two endpoints are connected through zero cells",
    "every four consecutive sample indices contain all four topology profiles",
    "interior-route profiles refute the outer-two-ring-only shortcut that fits every canonical pair",
]

_ENDPOINT_COLORS = (2, 3, 4, 6, 7, 8, 9)
_CANONICAL_SHAPES = ((6, 7), (7, 7), (8, 8), (9, 9))
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "one of the four canonical profiles",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "one of the four canonical profiles",
        "valid": "7..9",
    },
    "endpoint_color": {
        "type": "color",
        "default": "uniform from 2|3|4|6|7|8|9",
        "valid": "2|3|4|6|7|8|9",
    },
}

# Every boundary combination above is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = ("edge_hugger", "deep_detour", "interior_pair", "tie_break")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared curriculum profile for this draw.

    The seed and difficulty are intentionally irrelevant: ``run_one`` consumes
    consecutive sample indices, so every four-demo lesson receives every
    profile regardless of its starting residue.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 6, 9), ("grid_w", 7, 9)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    color = overrides.get("endpoint_color")
    if color is not None:
        if type(color) is not int:
            raise ValueError("endpoint_color must be an integer ARC color")
        if color not in _ENDPOINT_COLORS:
            raise ValueError(
                "endpoint_color must be one of "
                + ", ".join(map(str, _ENDPOINT_COLORS))
            )


def _line(start, goal):
    """Inclusive straight orthogonal segment."""
    r1, c1 = start
    r2, c2 = goal
    if r1 != r2 and c1 != c2:
        raise ValueError("line endpoints must share a row or column")
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    out = [(r1, c1)]
    while out[-1] != (r2, c2):
        r, c = out[-1]
        out.append((r + dr, c + dc))
    return out


def _joined_segments(points):
    path = []
    for start, goal in zip(points, points[1:]):
        segment = _line(start, goal)
        path.extend(segment if not path else segment[1:])
    if len(path) != len(set(path)):
        raise RuntimeError("profile backbone self-intersects")
    return path


def _base_geometry(profile, h, w):
    """Return (open cells, endpoint pair) before symmetry and branch growth."""
    if profile == "edge_hugger":
        # A simple boundary L: the public outer-ring shortcut is correct here.
        path = _joined_segments(((0, 0), (h - 1, 0), (h - 1, w - 1)))
        return set(path), (path[0], path[-1])

    if profile == "deep_detour":
        # Parallel tracks are separated by at least one wall column, making the
        # backbone an induced path whose only endpoint route reaches depth >=2.
        path = _joined_segments(
            (
                (0, 0),
                (h - 1, 0),
                (h - 1, 2),
                (2, 2),
                (2, w - 1),
                (h - 1, w - 1),
            )
        )
        return set(path), (path[0], path[-1])

    if profile == "interior_pair":
        start = (2, 2)
        goal = (h - 3, w - 3)
        # Ensure a nontrivial path even on 6x7, where the points are close.
        path = _joined_segments((start, (start[0], goal[1]), goal))
        return set(path), (path[0], path[-1])

    if profile == "tie_break":
        # The inner rectangular perimeter contains at least two equal shortest
        # routes.  On the minimum 6x7 canvas it becomes a 2x3 ladder, which is
        # still a lawful multi-route case and keeps both endpoints at depth 2.
        top, bottom = 2, h - 3
        left, right = 2, w - 3
        cells = set(_line((top, left), (top, right)))
        cells.update(_line((bottom, left), (bottom, right)))
        cells.update(_line((top, left), (bottom, left)))
        cells.update(_line((top, right), (bottom, right)))
        return cells, ((top, left), (bottom, right))

    raise ValueError(f"unknown schedule profile {profile!r}")


def _transform_point(point, h, w, symmetry):
    r, c = point
    if symmetry & 1:
        r = h - 1 - r
    if symmetry & 2:
        c = w - 1 - c
    return r, c


def _transform_geometry(cells, endpoints, h, w, symmetry):
    transformed = {_transform_point(point, h, w, symmetry) for point in cells}
    return transformed, tuple(
        _transform_point(point, h, w, symmetry) for point in endpoints
    )


def _neighbors(point, h, w):
    r, c = point
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _grow_branches(open_cells, h, w, target_count, rng):
    """Grow leaves onto an existing connected graph without adding cycles."""
    opened = set(open_cells)
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    while len(opened) < target_count:
        candidates = [
            point
            for point in all_cells
            if point not in opened
            and sum(neighbor in opened for neighbor in _neighbors(point, h, w)) == 1
        ]
        if not candidates:
            break
        opened.add(rng.choice(candidates))
    return opened


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    shape = ctx.draw_rng("canonical_shape").choice(_CANONICAL_SHAPES)
    h = (
        ctx.draw_int("grid_h", 6, 9)
        if overrides.get("grid_h") is not None
        else ctx.draw_int("grid_h", shape[0], shape[0])
    )
    w = (
        ctx.draw_int("grid_w", 7, 9)
        if overrides.get("grid_w") is not None
        else ctx.draw_int("grid_w", shape[1], shape[1])
    )
    color = ctx.draw_choice("endpoint_color", _ENDPOINT_COLORS)

    profile = schedule_profile(seed, sample_index, difficulty)
    open_cells, endpoints = _base_geometry(profile, h, w)
    symmetry = ctx.draw_rng("symmetry").randrange(4)
    open_cells, endpoints = _transform_geometry(
        open_cells, endpoints, h, w, symmetry
    )

    open_fraction = {
        "easy": 0.64,
        "medium": 0.57,
        "hard": 0.50,
    }.get(difficulty, 0.57)
    jitter = ctx.draw_rng("open_count").choice((-2, -1, 0, 1, 2))
    target_count = max(
        len(open_cells),
        min(h * w - 1, round(h * w * open_fraction) + jitter),
    )
    open_cells = _grow_branches(
        open_cells, h, w, target_count, ctx.draw_rng("branch_growth")
    )

    grid = full_grid(h, w, 5)
    for r, c in open_cells:
        grid[r][c] = 0
    for r, c in endpoints:
        grid[r][c] = color
    return grid


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence"]
    rows = []
    for row in grid:
        if isinstance(row, str):
            if not row or not all(char.isdigit() for char in row):
                return None, ["string rows must contain ARC digits"]
            rows.append([int(char) for char in row])
        elif isinstance(row, (list, tuple)) and row:
            rows.append(list(row))
        else:
            return None, ["rows must be non-empty sequences or digit strings"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return rows, ["grid must be rectangular"]
    return rows, []


def _shortest_path(grid, start, goal, *, max_boundary_depth=None):
    """Selected authority's row-major endpoint, U,D,L,R BFS behavior."""
    h, w = len(grid), len(grid[0])
    parent = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbor in _neighbors(current, h, w):
            if neighbor in parent:
                continue
            nr, nc = neighbor
            if max_boundary_depth is not None and neighbor not in (start, goal):
                depth = min(nr, h - 1 - nr, nc, w - 1 - nc)
                if depth > max_boundary_depth:
                    continue
            if neighbor != goal and grid[nr][nc] != 0:
                continue
            parent[neighbor] = current
            queue.append(neighbor)
    if goal not in parent:
        return []
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return path[::-1]


def _scene_analysis(grid):
    rows, errors = _coerce_grid(grid)
    if errors:
        return rows, None, errors
    h, w = len(rows), len(rows[0])
    errors = []
    if not 6 <= h <= 9:
        errors.append("grid height must be in 6..9")
    if not 7 <= w <= 9:
        errors.append("grid width must be in 7..9")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in rows
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return rows, None, errors

    nonstructural = sorted({value for row in rows for value in row if value not in (0, 5)})
    if len(nonstructural) != 1:
        errors.append("exactly one endpoint color outside {0,5} is required")
        return rows, None, errors
    color = nonstructural[0]
    if color not in _ENDPOINT_COLORS:
        errors.append("endpoint color must exclude 0, 1, and wall color 5")
    points = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == color
    ]
    if len(points) != 2:
        errors.append(f"endpoint color {color} must appear exactly twice")
    if not any(value == 0 for row in rows for value in row):
        errors.append("at least one zero corridor cell is required")
    if not any(value == 5 for row in rows for value in row):
        errors.append("at least one color-5 wall cell is required")
    unexpected = sorted({value for row in rows for value in row} - {0, 5, color})
    if unexpected:
        errors.append(f"unexpected colors: {unexpected}")
    if errors:
        return rows, None, errors

    start, goal = points
    path = _shortest_path(rows, start, goal)
    if not path:
        errors.append("matching endpoints are disconnected")
        return rows, None, errors
    features = {
        "grid_h": h,
        "grid_w": w,
        "endpoint_color": color,
        "start": start,
        "goal": goal,
        "path": path,
    }
    return rows, features, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _rows, _features, errors = _scene_analysis(grid)
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    _rows, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "endpoint_color": features["endpoint_color"],
    }


def expected_output(grid):
    rows, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = deepcopy(rows)
    for r, c in features["path"]:
        output[r][c] = features["endpoint_color"]
    return output


def _outer_two_ring_only(grid):
    """Rival: the interior maze is decorative; solve only boundary depth <=1."""
    rows, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    path = _shortest_path(
        rows,
        features["start"],
        features["goal"],
        max_boundary_depth=1,
    )
    output = deepcopy(rows)
    for r, c in path:
        output[r][c] = features["endpoint_color"]
    return output


def _interior_route_witness(grid):
    rows, features, errors = _scene_analysis(grid)
    if errors:
        return False
    h, w = len(rows), len(rows[0])
    reaches_interior = any(
        min(r, h - 1 - r, c, w - 1 - c) >= 2
        for r, c in features["path"]
    )
    return reaches_interior and _outer_two_ring_only(rows) != expected_output(rows)


SEMANTIC_WITNESSES = {"interior_route": _interior_route_witness}
SEMANTIC_RIVALS = {"outer_two_ring_only": _outer_two_ring_only}
WITNESS_RIVALS = {"interior_route": ["outer_two_ring_only"]}
CANONICAL_SHORTCUTS = {"outer_two_ring_only": _outer_two_ring_only}
LESSON_COMPETITORS = {"outer_two_ring_only": _outer_two_ring_only}


def lesson_identifiable(demos, query):
    """A lesson is sufficient exactly when every declared rival is refuted."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:  # keep hook failures diagnostic, not silent
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"rival {name!r} fits every demonstration")
    return reasons
