"""Sample gray containers with cyan contents for canonical task b0c4d837.

The unchanged Racket rule counts wholly empty interior rows, then paints that
count along a clockwise 3x3 spiral (saturating at nine). Generation returns only
inputs. Python output functions below are declared rivals/contract diagnostics,
never a replacement for authoritative Racket labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c1ae510562f9"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "7a7c1a560527"
SUMMARY = "Count wholly empty rows inside a gray U-shaped container; paint a 3x3 clockwise cyan spiral."

INVARIANTS = [
    "one upright gray (5) U-shaped container on a zero background",
    "interior cells are zero or cyan (8); at least one interior row contains cyan",
    "the floor is excluded from the row count; any cyan cell makes its row nonempty",
    "ordinary lessons mix solid bottom fill with separated and partially occupied rows",
    "exact controls are observed from pixels; impossible explicit combinations raise ValueError",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles or 5..16", "valid": "5..16"},
    "grid_w": {"type": "int", "default": "canonical profiles or 6..16", "valid": "6..16"},
    "interior_h": {"type": "int", "default": "feasible 2..12", "valid": "2..12"},
    "interior_w": {"type": "int", "default": "feasible 1..10", "valid": "1..10"},
    "empty_rows": {"type": "int", "default": "scheduled 0..10", "valid": "0..10"},
}
_LIMITS = {"grid_h": (5, 16), "grid_w": (6, 16), "interior_h": (2, 12),
           "interior_w": (1, 10), "empty_rows": (0, 10)}
# Rejections identify the actual conflicting pins on the ValueError itself.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_CANONICAL_SHAPES = ((5, 6), (6, 6), (7, 7), (9, 9))
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "contrast_one", "edge", "contrast_two")
MIN_STRICT_FRAC = 0.20
EXPECTED_OUTPUT_CODOMAIN = 10
SOLID_OUTPUT_JUSTIFICATION = (
    "The unchanged Racket count-to-spiral rule has ten possible outputs: zero "
    "empty rows yields a zero 3x3 grid, and nine or more yields a solid cyan "
    "3x3 grid. These are lawful endpoint counts inside a validated container."
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Every five-draw window contains both partial-row contrast families."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _conflict(*axes):
    error = ValueError("incompatible explicit overrides: " + ", ".join(axes))
    error.incompatible_axes = axes
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    pins = {name: value for name, value in overrides.items() if value is not None}
    for name, value in pins.items():
        lo, hi = _LIMITS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if {"grid_h", "interior_h"} <= pins.keys() and pins["grid_h"] < pins["interior_h"] + 2:
        _conflict("grid_h", "interior_h")
    if {"grid_w", "interior_w"} <= pins.keys() and pins["grid_w"] < pins["interior_w"] + 2:
        _conflict("grid_w", "interior_w")
    if {"interior_h", "empty_rows"} <= pins.keys() and pins["interior_h"] <= pins["empty_rows"]:
        _conflict("interior_h", "empty_rows")
    if {"grid_h", "empty_rows"} <= pins.keys() and pins["grid_h"] < pins["empty_rows"] + 3:
        _conflict("grid_h", "empty_rows")
    return pins


def _draw(ctx, name, lo, hi, preferred=()):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    choices = tuple(value for value in preferred if lo <= value <= hi)
    return ctx.draw_choice(name, choices) if choices else ctx.draw_int_strict(name, lo, hi)


def _band_choices(lo, hi, difficulty):
    """Bias size, preserving every feasible value and every explicit override."""
    values = list(range(lo, hi + 1))
    span = max(1, len(values) // 3)
    if difficulty == "easy":
        favored = values[:span]
    elif difficulty == "hard":
        favored = values[-span:]
    else:
        start = (len(values) - span) // 2
        favored = values[start:start + span]
    return values + favored * 6


def generate(seed, sample_index, *, difficulty=None, **overrides):
    pins = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    contrast = profile.startswith("contrast_")
    depth_cap = min(12, pins.get("grid_h", 16) - 2)
    empty_cap = min(10, pins.get("interior_h", depth_cap) - 1)
    favored = {"canonical": (1, 2, 3, 4), "contrast_one": (5, 6, 7, 8),
               "contrast_two": (5, 6, 7, 8),
               "edge": (0, 9, 10)}[profile]
    empty = _draw(ctx, "empty_rows", 0, empty_cap, favored)
    depth_min = max(2, empty + 1)
    partial_pairs = 2 if profile == "contrast_two" else 1 if contrast else 0
    while partial_pairs and empty + 2 * partial_pairs > pins.get("interior_h", depth_cap):
        partial_pairs -= 1
    if partial_pairs:
        depth_min = max(depth_min, empty + 2 * partial_pairs)
    height_min = max(5, pins.get("interior_h", depth_min) + 2)
    width_min = max(6, pins.get("interior_w", 1) + 2)
    # Every canonical slot has an exact canonical canvas profile when unpinned.
    shapes = [shape for shape in _CANONICAL_SHAPES
              if shape[0] >= height_min and shape[1] >= width_min
              and ("grid_h" not in pins or pins["grid_h"] == shape[0])
              and ("grid_w" not in pins or pins["grid_w"] == shape[1])]
    shape = None
    if profile == "canonical" and shapes:
        favored_shape = shapes[0] if difficulty == "easy" else shapes[-1] if difficulty == "hard" else shapes[len(shapes) // 2]
        shape = ctx.draw_rng("canonical_canvas").choice(shapes + [favored_shape] * 4)
    h = _draw(ctx, "grid_h", height_min, 16, (shape[0],) if shape else _band_choices(height_min, 16, difficulty))
    w = _draw(ctx, "grid_w", width_min, 16, (shape[1],) if shape else _band_choices(width_min, 16, difficulty))
    depth = _draw(ctx, "interior_h", depth_min, min(12, h - 2))
    width_choices = range(2, min(10, w - 2) + 1) if contrast else ()
    width = _draw(ctx, "interior_w", 1, min(10, w - 2), width_choices)
    top = ctx.draw_rng("vertical_position").randint(0, h - depth - 1)
    left = ctx.draw_rng("horizontal_position").randint(0, w - width - 2)
    floor, right = top + depth, left + width + 1
    grid = full_grid(h, w, 0)
    for r in range(top, floor + 1):
        grid[r][left] = grid[r][right] = 5
    for c in range(left, right + 1):
        grid[floor][c] = 5
    if partial_pairs and width >= 2 and empty > 0:
        # Complementary partial rows make every single-column and area-count
        # shortcut wrong, while occupied top/bottom rows refute top headroom.
        rng = ctx.draw_rng("interior_row_masks")
        # One or two complementary pairs give different per-column/area
        # deficits; a fixed '-1' or '-2' correction cannot solve both families.
        partial_rows = [0, depth - 1]
        partial_rows += rng.sample(range(1, depth - 1), 2 * (partial_pairs - 1))
        masks = {}
        for first, second in zip(partial_rows[::2], partial_rows[1::2]):
            mask = set(rng.sample(range(width), rng.randint(1, width - 1)))
            masks[first] = mask
            masks[second] = set(range(width)) - mask
        empty_indices = set(rng.sample([r for r in range(depth) if r not in masks], empty))
        for r in range(depth):
            if r in empty_indices:
                continue
            for c in masks.get(r, range(width)):
                grid[top + r][left + 1 + c] = 8
    else:
        for r in range(empty, depth):
            for c in range(width):
                grid[top + r][left + 1 + c] = 8
    return grid


def _bounds(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    return min(r for r, _ in points), max(r for r, _ in points), min(c for _, c in points), max(c for _, c in points)


def _interior(grid):
    top, floor, left, right = _bounds(grid)
    return [row[left + 1:right] for row in grid[top:floor]]


def observe_overrides(grid):
    top, floor, left, right = _bounds(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "interior_h": floor - top, "interior_w": right - left - 1,
            "empty_rows": sum(not any(row) for row in _interior(grid))}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["expected nonempty integer row lists"]
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        return ["empty or ragged grid"]
    if len(grid) > 30 or width > 30:
        return ["grid exceeds ARC's 30x30 bound"]
    if any(type(value) is not int or value not in (0, 5, 8) for row in grid for value in row):
        return ["expected integer colors 0, 5 and 8"]
    gray = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    if not gray:
        return ["missing gray container"]
    top, floor, left, right = _bounds(grid)
    if floor <= top or right - left < 2:
        return ["container needs an interior row and column"]
    expected = {(r, c) for r in range(top, floor + 1) for c in (left, right)}
    expected.update((floor, c) for c in range(left, right + 1))
    errors = []
    if gray != expected:
        errors.append("gray cells must form exactly one closed-bottom U")
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cyan:
        errors.append("container needs at least one occupied cyan row")
    if any(not (top <= r < floor and left < c < right) for r, c in cyan):
        errors.append("cyan must stay inside the container")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    seen_fill = False
    for row in _interior(grid):
        if not any(row):
            if seen_fill:
                return ["empty row below cyan fill"]
        elif all(value == 8 for value in row):
            seen_fill = True
        else:
            return ["partial occupied row"]
    return []


_SPIRAL = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (1, 1))
_SNAKE = ((0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0), (2, 0), (2, 1), (2, 2))


def _paint(count, order=_SPIRAL):
    output = [[0] * 3 for _ in range(3)]
    for r, c in order[:max(0, min(9, count))]:
        output[r][c] = 8
    return output


def _empty_count(grid):
    return sum(not any(row) for row in _interior(grid))


def _alternating_rows(grid):
    return _paint(_empty_count(grid), _SNAKE)


def _top_empty_prefix(grid):
    count = 0
    for row in _interior(grid):
        if any(row):
            break
        count += 1
    return _paint(count)


def _empty_area(grid):
    rows = _interior(grid)
    return _paint(sum(value == 0 for row in rows for value in row) // len(rows[0]))


def _column_only(grid, index):
    rows = _interior(grid)
    return _paint(sum(row[index] == 0 for row in rows))


def _left_column(grid):
    return _column_only(grid, 0)


def _middle_column(grid):
    return _column_only(grid, len(_interior(grid)[0]) // 2)


def _right_column(grid):
    return _column_only(grid, -1)


def _any_zero(grid):
    return _paint(sum(0 in row for row in _interior(grid)))


def _cap_at_four(grid):
    return _paint(min(4, _empty_count(grid)))


def _span_only(grid):
    return _paint(len(_interior(grid)))


def _row_major(grid):
    return _paint(_empty_count(grid), tuple((r, c) for r in range(3) for c in range(3)))


def _whole_grid_empty_rows(grid):
    return _paint(sum(not any(row) for row in grid))


def _offset_column(grid, index, correction):
    return _paint(sum(row[index] == 0 for row in _interior(grid)) - correction)


def _left_minus_one(grid):
    return _offset_column(grid, 0, 1)


def _left_minus_two(grid):
    return _offset_column(grid, 0, 2)


def _middle_minus_one(grid):
    return _offset_column(grid, len(_interior(grid)[0]) // 2, 1)


def _middle_minus_two(grid):
    return _offset_column(grid, len(_interior(grid)[0]) // 2, 2)


def _right_minus_one(grid):
    return _offset_column(grid, -1, 1)


def _right_minus_two(grid):
    return _offset_column(grid, -1, 2)


def _area_minus_one(grid):
    rows = _interior(grid)
    return _paint(sum(value == 0 for row in rows for value in row) // len(rows[0]) - 1)


def _area_minus_two(grid):
    rows = _interior(grid)
    return _paint(sum(value == 0 for row in rows for value in row) // len(rows[0]) - 2)


CANONICAL_SHORTCUTS = {
    "alternating_rows": _alternating_rows,
    "top_empty_prefix": _top_empty_prefix,
    "empty_area_divided_by_width": _empty_area,
    "left_column_only": _left_column,
    "middle_column_only": _middle_column,
    "right_column_only": _right_column,
    "any_zero_in_row": _any_zero,
    "cap_at_four": _cap_at_four,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "span_only": _span_only,
                      "plain_row_major": _row_major,
                      "whole_grid_empty_rows": _whole_grid_empty_rows,
                      "left_minus_1": _left_minus_one, "left_minus_2": _left_minus_two,
                      "middle_minus_1": _middle_minus_one, "middle_minus_2": _middle_minus_two,
                      "right_minus_1": _right_minus_one, "right_minus_2": _right_minus_two,
                      "area_minus_1": _area_minus_one, "area_minus_2": _area_minus_two}


def _combined_witness(grid):
    count = _empty_count(grid)
    return 5 <= count <= 8 and all(solve(grid) != _paint(count) for solve in CANONICAL_SHORTCUTS.values())


SEMANTIC_WITNESSES = {"combined_shortcut_breaker": _combined_witness}
WITNESS_RIVALS = {"combined_shortcut_breaker": tuple(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query):
    """Finite declared-rival check using the supplied authoritative labels."""
    return [f"{name} fits demonstrations but changes the query"
            for name, solve in LESSON_COMPETITORS.items()
            if all(solve(pair["input"]) == pair["output"] for pair in demos)
            and solve(query["input"]) != query["output"]]
