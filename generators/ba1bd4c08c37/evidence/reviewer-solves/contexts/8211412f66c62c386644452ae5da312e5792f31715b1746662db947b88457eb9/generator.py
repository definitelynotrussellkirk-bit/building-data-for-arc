"""Symmetric-shape sampler for the unchanged top-left-quadrant rule.

A colored seed quadrant is mirrored across both axes to make one even-sized
foreground bounding box. The selected Racket authority returns the seed quadrant:
the top-left floor-half of that bounding box. A six-slot schedule includes three
canonical 12x12 / 8x8 profiles and three size counterexamples; any single query
holdout leaves demonstrations that refute every declared rival without locking
the two output-shape axes together.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ba1bd4c08c37"
TASK_ID = GENERATOR_ID
RULE_HASH = "5394b465fb89"
VERSION = "2.0.1"
SUMMARY = (
    "Place one horizontally and vertically symmetric colored shape on background 0. "
    "Its even bounding box is 6..10 rows by 6..10 columns; the selected rule "
    "returns the top-left quadrant, preserving its colors and internal zeros."
)

PLACEMENTS = ("top_left", "top_right", "bottom_left", "bottom_right", "center")
AXES = {
    "grid_h": {"type": "int", "default": "five-slot schedule", "valid": "12..20"},
    "grid_w": {"type": "int", "default": "five-slot schedule", "valid": "12..20"},
    "quadrant_h": {"type": "int", "default": "4,4,4,3,5 schedule", "valid": "3..5"},
    "quadrant_w": {"type": "int", "default": "4,4,4,5,3 schedule", "valid": "3..5"},
    "palette_size": {"type": "int", "default": "4,3,4,5,6 schedule", "valid": "2..6"},
    "placement": {"type": "str", "default": "five-slot schedule", "valid": "|".join(PLACEMENTS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "background is 0; canvas is a rectangular 12..20 by 12..20 integer grid",
    "one nonempty foreground bbox has even dimensions 6..10 in each direction",
    "the bbox is exactly invariant under horizontal and vertical reflection",
    "the top-left quadrant contains background and 2..6 distinct nonzero colors",
    "the quadrant is not itself horizontally or vertically symmetric",
    "every advertised override is recoverable from the returned pixels",
]

EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 6
SCHEDULE_PROFILES = (
    "canonical_center",
    "canonical_top_left",
    "canonical_bottom_right",
    "rectangular_top_right",
    "rectangular_bottom_left",
    "compact_center",
)

# name, grid_h, grid_w, quadrant_h, quadrant_w, palette_size, placement, corner mode
_PROFILE_DEFAULTS = (
    ("canonical_center", 12, 12, 4, 4, 4, "center", "open"),
    ("canonical_top_left", 12, 12, 4, 4, 3, "top_left", "filled"),
    ("canonical_bottom_right", 12, 12, 4, 4, 4, "bottom_right", "open"),
    ("rectangular_top_right", 14, 16, 3, 5, 5, "top_right", "filled"),
    ("rectangular_bottom_left", 16, 14, 5, 3, 6, "bottom_left", "open"),
    ("compact_center", 18, 18, 3, 3, 2, "center", "filled"),
)


def _validate_nonnegative_int(name, value):
    """Require an exact public integer, excluding bool and coercible scalars."""
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the public semantic profile; seed and band do not shift the schedule."""
    _validate_nonnegative_int("seed", seed)
    _validate_nonnegative_int("sample_index", sample_index)
    _validate_difficulty(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_difficulty(difficulty):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (12, 20),
        "grid_w": (12, 20),
        "quadrant_h": (3, 5),
        "quadrant_w": (3, 5),
        "palette_size": (2, 6),
    }
    for name, (low, high) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")
    placement = overrides.get("placement")
    if placement is not None:
        if not isinstance(placement, str) or placement not in PLACEMENTS:
            raise ValueError("placement must be one of " + ", ".join(PLACEMENTS))


def _draw_int_default(ctx, label, low, high, default):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, low, high)
    return ctx.draw_int_strict(label, default, default)


def _draw_choice_default(ctx, label, options, default):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _origin(placement, height, width, bbox_h, bbox_w):
    if placement == "top_left":
        return 0, 0
    if placement == "top_right":
        return 0, width - bbox_w
    if placement == "bottom_left":
        return height - bbox_h, 0
    if placement == "bottom_right":
        return height - bbox_h, width - bbox_w
    if placement == "center":
        return (height - bbox_h) // 2, (width - bbox_w) // 2
    raise ValueError(f"unsupported placement: {placement!r}")


def _target_count(area, palette_size, difficulty, rng, capacity):
    ranges = {
        "easy": (0.38, 0.58),
        "medium": (0.48, 0.72),
        "hard": (0.62, 0.84),
        None: (0.48, 0.72),
    }
    low, high = ranges[difficulty]
    target = round(area * rng.uniform(low, high))
    return max(palette_size, min(capacity, target))


def _seed_quadrant(ctx, height, width, palette_size, corner_mode, difficulty):
    """Construct an orientation-sensitive seed quadrant with exact palette use."""
    if corner_mode == "filled":
        forced = {(0, 0)}
        locked_zero = {(0, width - 1), (height - 1, 0)}
    else:
        forced = {(0, 1), (1, 0)}
        locked_zero = {(0, 0), (1, width - 1), (height - 1, 1)}

    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in locked_zero
    ]
    if palette_size > len(available):
        raise ValueError("quadrant is too small for the requested palette")

    shape_rng = ctx.draw_rng("quadrant_occupancy")
    count = _target_count(
        height * width,
        palette_size,
        difficulty,
        shape_rng,
        len(available),
    )
    count = max(count, len(forced))
    extras = [point for point in available if point not in forced]
    occupied = set(forced)
    occupied.update(shape_rng.sample(extras, count - len(forced)))

    palette = ctx.draw_distinct_colors("palette", n=palette_size, exclude={0})
    paint_rng = ctx.draw_rng("quadrant_colors")
    points = sorted(occupied)
    paint_rng.shuffle(points)
    colors = list(palette)
    paint_rng.shuffle(colors)
    quadrant = full_grid(height, width, 0)
    for index, (row, col) in enumerate(points):
        quadrant[row][col] = colors[index] if index < palette_size else paint_rng.choice(palette)

    # These checks protect the construction from future schedule edits.
    if quadrant == quadrant[::-1] or quadrant == [row[::-1] for row in quadrant]:
        raise RuntimeError("quadrant construction lost orientation sensitivity")
    if any(quadrant[row][col] != 0 for row, col in locked_zero):
        raise RuntimeError("locked background was painted")
    return quadrant


def _mirror_quadrant(quadrant):
    top = [row + row[::-1] for row in quadrant]
    return top + deepcopy(top[::-1])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_nonnegative_int("seed", seed)
    _validate_nonnegative_int("sample_index", sample_index)
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _PROFILE_DEFAULTS[int(sample_index) % LESSON_SCHEDULE_PERIOD]
    _, default_h, default_w, default_qh, default_qw, default_palette, default_place, corner_mode = profile
    height = _draw_int_default(ctx, "grid_h", 12, 20, default_h)
    width = _draw_int_default(ctx, "grid_w", 12, 20, default_w)
    quadrant_h = _draw_int_default(ctx, "quadrant_h", 3, 5, default_qh)
    quadrant_w = _draw_int_default(ctx, "quadrant_w", 3, 5, default_qw)
    palette_size = _draw_int_default(ctx, "palette_size", 2, 6, default_palette)
    placement = _draw_choice_default(ctx, "placement", PLACEMENTS, default_place)

    quadrant = _seed_quadrant(
        ctx, quadrant_h, quadrant_w, palette_size, corner_mode, difficulty
    )
    patch = _mirror_quadrant(quadrant)
    bbox_h, bbox_w = len(patch), len(patch[0])
    top, left = _origin(placement, height, width, bbox_h, bbox_w)
    grid = full_grid(height, width, 0)
    for row in range(bbox_h):
        for col in range(bbox_w):
            grid[top + row][left + col] = patch[row][col]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _bbox(grid):
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not points:
        raise ValueError("grid has no nonzero foreground")
    top = min(row for row, _ in points)
    bottom = max(row for row, _ in points)
    left = min(col for _, col in points)
    right = max(col for _, col in points)
    return top, left, bottom, right


def _correct_crop(grid):
    top, left, bottom, right = _bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[left:left + half_w] for row in grid[top:top + half_h]]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]

    errors = []
    height = len(grid)
    if not (12 <= height <= 20 and 12 <= width <= 20):
        errors.append("canvas must be 12..20 rows by 12..20 columns")
    try:
        top, left, bottom, right = _bbox(grid)
    except ValueError as exc:
        return errors + [str(exc)]

    bbox_h, bbox_w = bottom - top + 1, right - left + 1
    if bbox_h % 2 or bbox_w % 2 or not (6 <= bbox_h <= 10 and 6 <= bbox_w <= 10):
        errors.append("foreground bbox must have even dimensions 6..10")
    patch = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    if patch != patch[::-1]:
        errors.append("foreground bbox must be vertically symmetric")
    if patch != [row[::-1] for row in patch]:
        errors.append("foreground bbox must be horizontally symmetric")

    if bbox_h >= 2 and bbox_w >= 2:
        quadrant = [row[:bbox_w // 2] for row in patch[:bbox_h // 2]]
        values = {value for row in quadrant for value in row}
        palette = values - {0}
        if not 2 <= len(palette) <= 6:
            errors.append(f"quadrant must use 2..6 nonzero colors; found {len(palette)}")
        if 0 not in values:
            errors.append("quadrant must preserve at least one internal background cell")
        if quadrant == quadrant[::-1]:
            errors.append("quadrant must distinguish top from bottom")
        if quadrant == [row[::-1] for row in quadrant]:
            errors.append("quadrant must distinguish left from right")
    return errors


def strict_canonical_like(grid):
    """Accept the declared symmetric-shape manifold, including all canonical rows."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every exact public control from the returned pixels."""
    top, left, bottom, right = _bbox(grid)
    height, width = len(grid), len(grid[0])
    bbox_h, bbox_w = bottom - top + 1, right - left + 1
    candidates = {
        (0, 0): "top_left",
        (0, width - bbox_w): "top_right",
        (height - bbox_h, 0): "bottom_left",
        (height - bbox_h, width - bbox_w): "bottom_right",
        ((height - bbox_h) // 2, (width - bbox_w) // 2): "center",
    }
    if (top, left) not in candidates:
        raise ValueError(f"bbox origin {(top, left)} is not an advertised placement")
    return {
        "grid_h": height,
        "grid_w": width,
        "quadrant_h": bbox_h // 2,
        "quadrant_w": bbox_w // 2,
        "palette_size": len({value for row in grid for value in row if value != 0}),
        "placement": candidates[(top, left)],
    }


# Pure wrong rules used only for diagnostics; labels still come from Racket.
def _fixed_four(grid):
    top, left, _, _ = _bbox(grid)
    return [row[left:left + 4] for row in grid[top:top + 4]]


def _fixed_height_four(grid):
    top, left, _, right = _bbox(grid)
    half_w = (right - left + 1) // 2
    return [row[left:left + half_w] for row in grid[top:top + 4]]


def _fixed_width_four(grid):
    top, left, bottom, _ = _bbox(grid)
    half_h = (bottom - top + 1) // 2
    return [row[left:left + 4] for row in grid[top:top + half_h]]


def _grid_origin(grid):
    top, left, bottom, right = _bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[:half_w] for row in grid[:half_h]]


def _raw_top_right(grid):
    top, left, bottom, right = _bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[right - half_w + 1:right + 1] for row in grid[top:top + half_h]]


def _raw_bottom_left(grid):
    top, left, bottom, right = _bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[left:left + half_w] for row in grid[bottom - half_h + 1:bottom + 1]]


def _raw_bottom_right(grid):
    top, left, bottom, right = _bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [
        row[right - half_w + 1:right + 1]
        for row in grid[bottom - half_h + 1:bottom + 1]
    ]


def _whole_bbox(grid):
    top, left, bottom, right = _bbox(grid)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


SEMANTIC_RIVALS = {
    "fixed_four": _fixed_four,
    "fixed_height_four": _fixed_height_four,
    "fixed_width_four": _fixed_width_four,
    "grid_origin": _grid_origin,
    "raw_top_right": _raw_top_right,
    "raw_bottom_left": _raw_bottom_left,
    "raw_bottom_right": _raw_bottom_right,
    "whole_bbox": _whole_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("fixed_four", "fixed_height_four", "fixed_width_four")
}


def _refutes(name, grid):
    return SEMANTIC_RIVALS[name](grid) != _correct_crop(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, name=name: _refutes(name, grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Report finite ambiguity against every declared competitor."""
    return [
        f"{name} fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
