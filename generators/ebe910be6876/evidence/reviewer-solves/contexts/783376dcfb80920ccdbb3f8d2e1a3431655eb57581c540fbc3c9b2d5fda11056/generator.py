"""Generator for ARC task 46f33fce / ebe910be6876.

Each sparse marker sits at an odd row and odd column. The rule doubles the
canvas and expands every marker into its aligned 4x4 color tile.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ebe910be6876"
VERSION = "3.0.0"
TASK_ID = "ebe910be6876"
RULE_HASH = "74026dfb3e5c"

SUMMARY = (
    "Build a sparse odd-coordinate marker lattice on a zero background. "
    "In the doubled output, a marker at (r,c) becomes a clipped 4x4 tile "
    "whose top-left is (2r-2,2c-2). Odd-coordinate markers therefore map "
    "to non-overlapping 4x4 cells on an aligned logical grid. A controlled "
    "prior covers all four linked public marker/color profiles."
)

INVARIANTS = [
    "the input is a 6..15 by 6..15 zero-background grid",
    "there are 4..14 nonzero single-cell markers using at least two colors",
    "every marker lies at an odd row and an odd column",
    "distinct markers map to disjoint aligned 4x4 output tiles",
    "the output is exactly twice the input height and width",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 6..15",
        "valid": "6..15",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 6..15",
        "valid": "6..15",
    },
}

_VALID_H = (6, 15)
_VALID_W = (6, 15)
_PROFILE_PRIOR = 0.30
_BAND_BOUNDS = {
    "easy": ((8, 10), (8, 10)),
    "medium": ((9, 12), (9, 12)),
    "hard": ((11, 15), (11, 15)),
}
_COUNT_BOUNDS = {
    "easy": (4, 6),
    "medium": (5, 9),
    "hard": (7, 14),
}
_PALETTE_BOUNDS = {
    "easy": (2, 4),
    "medium": (3, 6),
    "hard": (4, 8),
}
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _points(*cells):
    return tuple(sorted(cells))


_PROFILE_SPECS = (
    {
        "points": _points(
            (0, 0), (0, 1), (1, 1), (3, 4), (4, 3), (4, 4)
        ),
        "multiplicities": (2, 1, 1, 1, 1),
    },
    {
        "points": _points(
            (0, 0), (1, 0), (1, 1), (2, 2), (3, 3), (4, 4)
        ),
        "multiplicities": (2, 2, 1, 1),
    },
    {
        "points": _points((0, 0), (0, 1), (4, 0), (4, 1), (4, 4)),
        "multiplicities": (2, 1, 1, 1),
    },
    {
        "points": _points((1, 1), (2, 2), (3, 1), (3, 3), (4, 0)),
        "multiplicities": (1, 1, 1, 1, 1),
    },
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


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


def _logical_component_sizes(points):
    points = set(points)
    seen = set()
    sizes = []
    for start in sorted(points):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        size = 0
        while queue:
            row, col = queue.popleft()
            size += 1
            for dr, dc in _DELTAS:
                neighbor = row + dr, col + dc
                if neighbor in points and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return tuple(sorted(sizes))


def _canonical_d4_points(points, size):
    variants = []
    for transform in range(8):
        transformed = []
        for point in points:
            row, col = point
            for _ in range(transform % 4):
                row, col = col, size - 1 - row
            if transform >= 4:
                col = size - 1 - col
            transformed.append((row, col))
        variants.append(tuple(sorted(transformed)))
    return min(variants)


def _profile_feature(points, colors, *, height=10, width=10):
    points = tuple(sorted(points))
    rows = [row for row, _col in points]
    cols = [col for _row, col in points]
    row_counts = tuple(sorted(Counter(rows).values()))
    col_counts = tuple(sorted(Counter(cols).values()))
    axis_counts = tuple(sorted((row_counts, col_counts)))
    bbox_shape = tuple(sorted((
        max(rows) - min(rows) + 1,
        max(cols) - min(cols) + 1,
    )))
    logical_height = height // 2
    logical_width = width // 2
    boundary = sum(
        row in (0, logical_height - 1)
        or col in (0, logical_width - 1)
        for row, col in points
    )
    corner = sum(
        row in (0, logical_height - 1)
        and col in (0, logical_width - 1)
        for row, col in points
    )
    multiplicities = tuple(sorted(Counter(colors).values()))
    return (
        height,
        width,
        len(points),
        multiplicities,
        _canonical_d4_points(points, height // 2),
        bbox_shape,
        axis_counts,
        _logical_component_sizes(points),
        boundary,
        corner,
    )


for _index, _spec in enumerate(_PROFILE_SPECS):
    _colors = []
    for _color, _count in enumerate(_spec["multiplicities"], start=1):
        _colors.extend([_color] * _count)
    _spec["signature"] = _profile_feature(_spec["points"], _colors)
    _spec["index"] = _index

_CANONICAL_PROFILE_SIGNATURES = frozenset(
    spec["signature"] for spec in _PROFILE_SPECS
)


def _markers(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    height = len(coerced)
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append("grid height must be in 6..15")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append("grid width must be in 6..15")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    markers = _markers(coerced)
    if not 4 <= len(markers) <= 14:
        errors.append("the grid must contain 4..14 nonzero markers")
    if any(row % 2 != 1 or col % 2 != 1
           for row, col, _value in markers):
        errors.append("every marker must lie at an odd row and odd column")
    distinct_colors = {value for _row, _col, value in markers}
    if len(distinct_colors) < 2:
        errors.append("at least two nonzero marker colors are required")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    coerced = _coerce_grid(grid)
    height = len(coerced)
    width = len(coerced[0])
    out_height = height * 2
    out_width = width * 2
    output = full_grid(out_height, out_width, 0)
    for row, col, color in _markers(coerced):
        start_row = 2 * row - 2
        start_col = 2 * col - 2
        for out_row in range(start_row, start_row + 4):
            for out_col in range(start_col, start_col + 4):
                if 0 <= out_row < out_height and 0 <= out_col < out_width:
                    output[out_row][out_col] = color
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    coerced = _coerce_grid(grid)
    if len(coerced) != 10 or len(coerced[0]) != 10:
        return None
    markers = _markers(coerced)
    points = tuple(sorted((row // 2, col // 2)
                          for row, col, _value in markers))
    colors = [value for _row, _col, value in markers]
    signature = _profile_feature(points, colors)
    return signature if signature in _CANONICAL_PROFILE_SIGNATURES else None


def is_canonical_profile(grid):
    return (
        canonical_profile_signature(grid)
        in _CANONICAL_PROFILE_SIGNATURES
    )


def _transform_point(point, transform, size=5):
    row, col = point
    rotations = transform % 4
    for _ in range(rotations):
        row, col = col, size - 1 - row
    if transform >= 4:
        col = size - 1 - col
    return row, col


def _profile_colors(multiplicities, rng):
    palette = rng.sample(
        list(range(1, 10)),
        k=len(multiplicities),
    )
    counts = list(multiplicities)
    rng.shuffle(counts)
    colors = []
    for color, count in zip(palette, counts):
        colors.extend([color] * count)
    rng.shuffle(colors)
    return colors


def _paint_logical(height, width, points, colors):
    grid = full_grid(height, width, 0)
    for (logical_row, logical_col), color in zip(points, colors):
        grid[2 * logical_row + 1][2 * logical_col + 1] = color
    return grid


def _draw_profile(spec, rng):
    transform = rng.randrange(8)
    points = tuple(sorted(
        _transform_point(point, transform)
        for point in spec["points"]
    ))
    colors = _profile_colors(spec["multiplicities"], rng)
    grid = _paint_logical(10, 10, points, colors)
    if canonical_profile_signature(grid) != spec["signature"]:
        raise AssertionError("constructed public profile drifted")
    return grid


def _draw_general(height, width, band, rng):
    logical_points = [
        (row, col)
        for row in range(height // 2)
        for col in range(width // 2)
    ]
    count_lo, count_hi = _COUNT_BOUNDS[band]
    count_hi = min(count_hi, len(logical_points))
    count_lo = min(count_lo, count_hi)
    marker_count = rng.randint(count_lo, count_hi)
    points = rng.sample(logical_points, marker_count)

    palette_lo, palette_hi = _PALETTE_BOUNDS[band]
    palette_hi = min(palette_hi, marker_count, 9)
    palette_lo = min(palette_lo, palette_hi)
    palette_size = rng.randint(palette_lo, palette_hi)
    palette = rng.sample(list(range(1, 10)), palette_size)
    colors = palette[:]
    colors.extend(
        rng.choice(palette)
        for _ in range(marker_count - palette_size)
    )
    rng.shuffle(colors)
    return _paint_logical(height, width, points, colors)


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
                tuple(range(len(_PROFILE_SPECS))),
            )

    if profile_index is not None:
        height = ctx.draw_int("grid_h", 10, 10)
        width = ctx.draw_int("grid_w", 10, 10)
        grid = _draw_profile(
            _PROFILE_SPECS[profile_index],
            ctx.draw_rng("layout"),
        )
    else:
        height_bounds, width_bounds = _BAND_BOUNDS[band]
        if overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", *_VALID_H)
        else:
            height = ctx.draw_int("grid_h", *height_bounds)
        if overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", *_VALID_W)
        else:
            width = ctx.draw_int("grid_w", *width_bounds)
        grid = _draw_general(
            height,
            width,
            band,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
