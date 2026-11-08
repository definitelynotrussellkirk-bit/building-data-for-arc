"""Generator for bank task H34 / ec5fd031b9e1.

Color 8 forms a bordered maze. Every other used color appears at exactly two
endpoints. The rule finds that pair's shortest zero-cell path in the original
grid and paints the entire path with the endpoint color.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ec5fd031b9e1"
VERSION = "3.0.0"
TASK_ID = "ec5fd031b9e1"
RULE_HASH = "1fb88c73c536"

SUMMARY = (
    "Build a color-8 bordered maze with interior wall dividers and one to "
    "three pairs of colored endpoints. Each pair remains connected when all "
    "walls and other endpoints are treated as blockers. The output paints "
    "the canonical shortest path for each color on the original maze."
)

INVARIANTS = [
    "the input is a 7..16 by 8..18 rectangular ARC grid",
    "the complete outer border and at least one interior cell are color 8",
    "one to three nonzero non-8 colors each appear at exactly two endpoints",
    "every endpoint is interior and each pair has Manhattan distance at least 3",
    "every pair has a path through zeros when other endpoints are blocked",
    "the canonical shortest paths for distinct colors do not overlap",
    "the output preserves dimensions and paints paths in ascending color order",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 7..16",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 8..18",
        "valid": "8..18",
    },
    "n_pairs": {
        "type": "int",
        "default": "difficulty-aware rng 1..3",
        "valid": "1..3",
    },
}

_VALID_H = (7, 16)
_VALID_W = (8, 18)
_VALID_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)
_PROFILE_PRIOR = 0.25
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BAND_BOUNDS = {
    "easy": ((7, 10), (8, 12), (1, 2), (1, 2)),
    "medium": ((9, 13), (10, 15), (2, 2), (2, 4)),
    "hard": ((12, 16), (14, 18), (2, 3), (3, 5)),
}

# Five public input profiles. Compact digit rows keep the embedded prior
# inspectable without importing the canonical dataset at generation time.
_PROFILE_ROWS = (
    (
        "88888888888",
        "81008000028",
        "80008000008",
        "80008000008",
        "80008888808",
        "80008000008",
        "80008000008",
        "80010000028",
        "88888888888",
    ),
    (
        "8888888888",
        "8100000028",
        "8000000008",
        "8888088808",
        "8000008008",
        "8000008028",
        "8000000008",
        "8000008008",
        "8000108008",
        "8888888888",
    ),
    (
        "888888888888",
        "803008000028",
        "800008000008",
        "800000000008",
        "800008000008",
        "800008880888",
        "800000000008",
        "800030000028",
        "888888888888",
    ),
    (
        "88888888888",
        "84000000008",
        "80088888808",
        "80080000008",
        "80080000028",
        "80080000008",
        "80080000008",
        "84080002008",
        "88888888888",
    ),
    (
        "888888888888",
        "810008000028",
        "800000000008",
        "800008000008",
        "800008000008",
        "800008808808",
        "800000000008",
        "800100000028",
        "888888888888",
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, bounds in (
        ("grid_h", _VALID_H),
        ("grid_w", _VALID_W),
        ("n_pairs", (1, 3)),
    ):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if not bounds[0] <= value <= bounds[1]:
            raise ValueError(
                f"{label} must be in {bounds[0]}..{bounds[1]}"
            )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _colored_points(grid):
    colors = sorted({
        value
        for row in grid
        for value in row
        if value not in (0, 8)
    })
    return {
        color: [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        for color in colors
    }


def _shortest_path(grid, start, goal, extra_blocked=()):
    """Canonical BFS: up, down, left, right through zero or the goal."""
    height = len(grid)
    width = len(grid[0])
    blocked = set(extra_blocked)
    blocked.discard(start)
    blocked.discard(goal)
    parent = {start: None}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for dr, dc in _DELTAS:
            neighbor = row + dr, col + dc
            if (
                not 0 <= neighbor[0] < height
                or not 0 <= neighbor[1] < width
                or neighbor in parent
                or neighbor in blocked
            ):
                continue
            value = grid[neighbor[0]][neighbor[1]]
            if value == 0 or neighbor == goal:
                parent[neighbor] = (row, col)
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
    if not isinstance(grid, list) or not grid:
        return None, None, ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return None, None, [
            "grid rows must be non-empty lists or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]

    height = len(coerced)
    errors = []
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append("grid height must be in 7..16")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append("grid width must be in 8..18")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return coerced, None, errors

    border = (
        coerced[0]
        + coerced[-1]
        + [coerced[row][0] for row in range(1, height - 1)]
        + [coerced[row][-1] for row in range(1, height - 1)]
    )
    if any(value != 8 for value in border):
        errors.append("the complete outer border must be color 8")
    interior_walls = sum(
        coerced[row][col] == 8
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    )
    if interior_walls < 1:
        errors.append("at least one interior color-8 wall cell is required")
    points = _colored_points(coerced)
    if not 1 <= len(points) <= 3:
        errors.append("the grid must contain one to three endpoint colors")
    if any(color not in _VALID_PALETTE for color in points):
        errors.append("endpoint colors must exclude 0 and wall color 8")
    if any(len(cells) != 2 for cells in points.values()):
        errors.append("every endpoint color must appear exactly twice")
    if errors:
        return coerced, None, errors

    paths = {}
    occupied_path_cells = set()
    for color, cells in points.items():
        start, goal = cells
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        ):
            errors.append("all colored endpoints must be interior")
        distance = (
            abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        )
        if distance < 3:
            errors.append(
                f"color {color} endpoints must have Manhattan distance >= 3"
            )
        path = _shortest_path(coerced, start, goal)
        if not path:
            errors.append(
                f"color {color} endpoints must connect through zero cells"
            )
        elif occupied_path_cells.intersection(path):
            errors.append(
                "canonical shortest paths for endpoint colors must not overlap"
            )
        occupied_path_cells.update(path)
        paths[color] = path
    if errors:
        return coerced, None, errors

    features = {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": len(points),
        "interior_walls": interior_walls,
        "points": points,
        "paths": paths,
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "n_pairs": features["n_pairs"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [row[:] for row in coerced]
    for color in sorted(features["points"]):
        start, goal = features["points"][color]
        for row, col in _shortest_path(coerced, start, goal):
            output[row][col] = color
    return output


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform_grid(grid, transform):
    result = [row[:] for row in grid]
    if transform >= 4:
        result = [row[::-1] for row in result]
    for _ in range(transform % 4):
        result = _rotate(result)
    return result


def _profile_feature(grid):
    variants = []
    for transform in range(8):
        candidate = _transform_grid(grid, transform)
        height = len(candidate)
        width = len(candidate[0])
        walls = tuple(
            (row, col)
            for row in range(height)
            for col in range(width)
            if candidate[row][col] == 8
        )
        groups = tuple(sorted(
            tuple(cells)
            for cells in _colored_points(candidate).values()
        ))
        variants.append((height, width, walls, groups))
    return min(variants)


def _decode_rows(rows):
    return [[int(value) for value in row] for row in rows]


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_feature(_decode_rows(rows)) for rows in _PROFILE_ROWS
)


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    signature = _profile_feature(_coerce_grid(grid))
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def _draw_profile(rows, transform, colors):
    grid = _decode_rows(rows)
    source_colors = sorted(_colored_points(grid))
    mapping = dict(zip(source_colors, colors))
    recolored = [
        [mapping.get(value, value) for value in row]
        for row in grid
    ]
    result = _transform_grid(recolored, transform)
    if canonical_profile_signature(result) not in (
        _CANONICAL_PROFILE_SIGNATURES
    ):
        raise AssertionError("constructed public profile drifted")
    return result


def _blank_maze(height, width):
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][0] = 8
        grid[row][width - 1] = 8
    for col in range(width):
        grid[0][col] = 8
        grid[height - 1][col] = 8
    return grid


def _paint_dividers(grid, count, band, rng):
    height = len(grid)
    width = len(grid[0])
    for _ in range(count):
        if rng.random() < 0.5:
            col = rng.randint(2, width - 3)
            for row in range(1, height - 1):
                grid[row][col] = 8
            candidates = list(range(2, height - 2))
            max_gaps = {"easy": 1, "medium": 2, "hard": 3}[band]
            gap_count = rng.randint(1, min(max_gaps, len(candidates)))
            for row in rng.sample(candidates, gap_count):
                grid[row][col] = 0
        else:
            row = rng.randint(2, height - 3)
            for col in range(1, width - 1):
                grid[row][col] = 8
            candidates = list(range(2, width - 2))
            max_gaps = {"easy": 1, "medium": 2, "hard": 3}[band]
            gap_count = rng.randint(1, min(max_gaps, len(candidates)))
            for col in rng.sample(candidates, gap_count):
                grid[row][col] = 0


def _zero_cells(grid):
    return [
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] == 0
    ]


def _place_pairs(grid, colors, rng):
    endpoints = set()
    reserved = set()
    pairs = []
    for color in colors:
        placed = None
        candidates = [
            cell
            for cell in _zero_cells(grid)
            if cell not in endpoints and cell not in reserved
        ]
        for _ in range(240):
            if len(candidates) < 2:
                break
            start = rng.choice(candidates)
            goals = [
                cell
                for cell in candidates
                if (
                    cell != start
                    and abs(cell[0] - start[0])
                    + abs(cell[1] - start[1])
                    >= 3
                )
            ]
            if not goals:
                continue
            goal = rng.choice(goals)
            path = _shortest_path(
                grid,
                start,
                goal,
                endpoints | reserved,
            )
            if path:
                placed = start, goal, path
                break
        if placed is None:
            return None
        start, goal, path = placed
        endpoints.update((start, goal))
        reserved.update(path)
        pairs.append((color, start, goal))

    for color, start, goal in pairs:
        grid[start[0]][start[1]] = color
        grid[goal[0]][goal[1]] = color
    return grid


def _fallback_scene(height, width, colors):
    """Construct a guaranteed valid small-canvas scene without clamping."""
    grid = _blank_maze(height, width)
    wall_row = 1
    for col in range(2, width - 2):
        grid[wall_row][col] = 8
    pair_rows = list(range(2, 2 + len(colors)))
    for color, row in zip(colors, pair_rows):
        grid[row][1] = color
        grid[row][width - 2] = color
    return grid


def _draw_general(height, width, n_pairs, band, rng):
    colors = rng.sample(list(_VALID_PALETTE), n_pairs)
    _height_bounds, _width_bounds, _pair_bounds, wall_bounds = (
        _BAND_BOUNDS[band]
    )
    interior_area = (height - 2) * (width - 2)
    wall_cap = max(1, min(wall_bounds[1], interior_area // 35))
    wall_lo = min(wall_bounds[0], wall_cap)

    for _ in range(128):
        grid = _blank_maze(height, width)
        wall_count = rng.randint(wall_lo, wall_cap)
        _paint_dividers(grid, wall_count, band, rng)
        result = _place_pairs(grid, colors, rng)
        if result is not None and not self_check(result):
            return result

    fallback = _fallback_scene(height, width, colors)
    errors = self_check(fallback)
    if errors:
        raise AssertionError(
            "constructive fallback invalid: " + "; ".join(errors)
        )
    return fallback


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
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_ROWS))),
            )

    if profile_index is not None:
        profile_rng = ctx.draw_rng("profile_layout")
        transform = profile_rng.randrange(8)
        colors = profile_rng.sample(list(_VALID_PALETTE), 2)
        grid = _draw_profile(
            _PROFILE_ROWS[profile_index],
            transform,
            colors,
        )
        ctx.draw_int("grid_h", len(grid), len(grid))
        ctx.draw_int("grid_w", len(grid[0]), len(grid[0]))
        ctx.draw_int("n_pairs", 2, 2)
    else:
        height_bounds, width_bounds, pair_bounds, _wall_bounds = (
            _BAND_BOUNDS[band]
        )
        if overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", *_VALID_H)
        else:
            height = ctx.draw_int("grid_h", *height_bounds)
        if overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", *_VALID_W)
        else:
            width = ctx.draw_int("grid_w", *width_bounds)
        if overrides.get("n_pairs") is not None:
            n_pairs = ctx.draw_int("n_pairs", 1, 3)
        else:
            n_pairs = ctx.draw_int("n_pairs", *pair_bounds)
        grid = _draw_general(
            height,
            width,
            n_pairs,
            band,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
