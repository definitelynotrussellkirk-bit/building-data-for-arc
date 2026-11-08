"""Sparse red/green bounding boxes with an independently chosen overlap.

The selected Racket rule is the sole label authority. Normal draws alternate a
wide, reversed-boundary teaching example with a broad geometry example. Canvas
and point-count overrides are exact in every difficulty band.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c68b56303c10"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "42cdb52c8cce"
SUMMARY = (
    "On background 0, take the bounding boxes of all color-2 cells and all "
    "color-3 cells. Emit a solid color-8 rectangle with the height and width "
    "of their nonempty intersection. Sparse points, relative box ownership, "
    "overlap aspect ratio, containment and canvas scale vary."
)
INVARIANTS = [
    "rectangular integer grid with background 0 and colors 2 and 3",
    "2..8 points of each color, with exact requested counts and no collisions",
    "both bounding boxes have a nonempty intersection",
    "canonical canvas sizes and small overlaps remain supported in every band",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..18; favors canonical heights 8..11", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "8..22; favors canonical widths 10..13", "valid": "8..22"},
    "n_red": {"type": "int", "default": "2..8; difficulty changes weights only", "valid": "2..8"},
    "n_green": {"type": "int", "default": "2..8; difficulty changes weights only", "valid": "2..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("separator", "coverage")
SOLID_OUTPUT_JUSTIFICATION = (
    "The unchanged canonical Racket program calls empty-grid with color 8 "
    "and the exact intersection dimensions; every lawful output is solid, "
    "while its height and width carry the entire task answer."
)


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _draw_weighted_int(ctx, name, lo, hi, favored):
    # Full global support is recorded even when a band favors a smaller subset.
    return ctx.draw_choice(name, list(range(lo, hi + 1)) + list(favored))


@lru_cache(maxsize=256)
def _axis_pairs(length, overlap, separator, column):
    """Finite immutable interval pairs, each interval at least two cells long."""
    intervals = [(a, b) for a in range(length) for b in range(a + 1, length)]
    pairs = []
    for red0, red1 in intervals:
        for green0, green1 in intervals:
            if min(red1, green1) - max(red0, green0) + 1 != overlap:
                continue
            if separator and not (green0 < red0 <= green1 < red1):
                continue
            if separator and column and green1 - green0 + 1 - overlap == 3:
                continue
            pairs.append((red0, red1, green0, green1))
    return tuple(pairs)


def _box_cells(box):
    r0, c0, r1, c1 = box
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def _covers(box, count, rng):
    """Extremal supports: varied edge points, then two guaranteed diagonals."""
    r0, c0, r1, c1 = box
    result = []
    for _ in range(4):
        if count >= 4:
            points = {(r0, rng.randint(c0, c1)), (r1, rng.randint(c0, c1)),
                      (rng.randint(r0, r1), c0), (rng.randint(r0, r1), c1)}
            result.append(points)
        elif count == 3:
            top, left = rng.choice((False, True)), rng.choice((False, True))
            row, opposite_row = (r0, r1) if top else (r1, r0)
            col, opposite_col = (c0, c1) if left else (c1, c0)
            result.append({(row, col), (opposite_row, rng.randint(c0, c1)),
                           (rng.randint(r0, r1), opposite_col)})
    diagonals = [{(r0, c0), (r1, c1)}, {(r0, c1), (r1, c0)}]
    rng.shuffle(diagonals)
    return result + diagonals


def _place_points(red_box, green_box, n_red, n_green, rng):
    """Allocate exclusive/shared cells without overwrites or shortened counts."""
    red_area, green_area = _box_cells(red_box), _box_cells(green_box)
    if (len(red_area) < n_red or len(green_area) < n_green
            or len(red_area | green_area) < n_red + n_green):
        return None
    for red in _covers(red_box, n_red, rng):
        for green in _covers(green_box, n_green, rng):
            if red & green:
                continue
            needed_red, needed_green = n_red - len(red), n_green - len(green)
            occupied = red | green
            red_only = sorted(red_area - green_area - occupied)
            green_only = sorted(green_area - red_area - occupied)
            shared = sorted((red_area & green_area) - occupied)
            low = max(0, needed_red - len(red_only))
            high = min(needed_red, len(shared) - max(0, needed_green - len(green_only)))
            if low > high:
                continue
            shared_red_count = rng.randint(low, high)
            shared_red = set(rng.sample(shared, shared_red_count))
            remaining_shared = sorted(set(shared) - shared_red)
            green_low = max(0, needed_green - len(green_only))
            green_high = min(needed_green, len(remaining_shared))
            if green_low > green_high:
                continue
            shared_green_count = rng.randint(green_low, green_high)
            placed_red = red | shared_red | set(rng.sample(red_only, needed_red - shared_red_count))
            placed_green = green | set(rng.sample(remaining_shared, shared_green_count))
            placed_green |= set(rng.sample(green_only, needed_green - shared_green_count))
            return placed_red, placed_green
    return None


def _fallback_boxes(height, width, ih, iw, separator):
    # Balanced proper crossings fit all four integer-axis joint domains: at the
    # smallest 7x8 canvas, each box has ample capacity for eight colored cells.
    top = (height - ih) // 2
    left_choices = list(range(1, width - iw))
    if separator:
        left_choices = [value for value in left_choices if value != 3]
    left = min(left_choices, key=lambda value: abs(2 * value - (width - iw)))
    return (top, left, height - 1, width - 1), (0, 0, top + ih - 1, left + iw - 1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed and sample_index must be integers; sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    anchor_h, anchor_w = ctx.draw_choice("canvas_anchor", ((8, 10), (9, 11), (10, 12), (11, 13)))
    height = _draw_weighted_int(ctx, "grid_h", 7, 18, [anchor_h] * 50)
    width = _draw_weighted_int(ctx, "grid_w", 8, 22, [anchor_w] * 50)
    favored = (2, 3, 4) if difficulty == "easy" else ((4, 5, 6, 7, 8) if difficulty == "hard" else (3, 4, 5))
    count_weights = list(favored) * 5 + [3] * 20
    n_red = _draw_weighted_int(ctx, "n_red", 2, 8, count_weights)
    n_green = _draw_weighted_int(ctx, "n_green", 2, 8, count_weights)
    separator = schedule_profile(seed, sample_index, difficulty) == "separator"
    if separator:
        # Each such example refutes ALL declared alternatives. Two in every
        # four consecutive draws support any three-demo/one-query rotation.
        shapes = [(h, w) for h in range(1, height - 1)
                  for w in range(max(4, h + 1), width - 1)
                  if (h, w) != (n_red, n_green)]
    else:
        shapes = [(h, w) for h in range(1, height - 1)
                  for w in range(1, width - 1)]
        shapes += [(2, 2), (4, 3), (5, 3)] * 30
    ih, iw = ctx.draw_choice("overlap_shape", shapes)
    row_pairs = _axis_pairs(height, ih, separator, False)
    column_pairs = _axis_pairs(width, iw, separator, True)
    rng = ctx.draw_rng("bbox_geometry")
    placed = None
    for _ in range(32):
        r0, r1, g0, g1 = rng.choice(row_pairs)
        c0, c1, q0, q1 = rng.choice(column_pairs)
        placed = _place_points((r0, c0, r1, c1), (g0, q0, g1, q1), n_red, n_green, rng)
        if placed is not None:
            break
    if placed is None:
        red_box, green_box = _fallback_boxes(height, width, ih, iw, separator)
        placed = _place_points(red_box, green_box, n_red, n_green, rng)
    if placed is None:
        raise RuntimeError("constructive fallback failed; refusing a shortened or relabeled draw")
    grid = full_grid(height, width, 0)
    for color, points in zip((2, 3), placed):
        for row, col in points:
            grid[row][col] = color
    return grid


def _bounds(grid, color):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not points:
        raise ValueError(f"missing color-{color} cells")
    rows, cols = zip(*points)
    return min(rows), min(cols), max(rows), max(cols)


def _geometry(grid):
    red, green = _bounds(grid, 2), _bounds(grid, 3)
    height = min(red[2], green[2]) - max(red[0], green[0]) + 1
    width = min(red[3], green[3]) - max(red[1], green[1]) + 1
    return red, green, height, width


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_red": sum(value == 2 for row in grid for value in row),
            "n_green": sum(value == 3 for row in grid for value in row)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    height, width = len(grid), len(grid[0])
    if not (1 <= height <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 2, 3) for row in grid for value in row):
        return ["cells must be literal integer colors 0, 2, or 3"]
    try:
        _red, _green, height, width = _geometry(grid)
    except ValueError as exc:
        return [str(exc)]
    if height <= 0 or width <= 0:
        return ["red and green bounding boxes must intersect"]
    return []


def strict_canonical_like(grid):
    """The lawful sparse-color manifold, independent of a difficulty label."""
    return self_check(grid)


def _solid(height, width):
    # Rival output only; production labels always come from canonical Racket.
    return [[8] * max(1, width) for _ in range(max(1, height))]


def _directed_corners(grid):
    red, green, _height, _width = _geometry(grid)
    return _solid(red[2] - green[0] + 1, red[3] - green[1] + 1)


def _sorted_dimensions(grid):
    _red, _green, height, width = _geometry(grid)
    return _solid(max(height, width), min(height, width))


def _width_cap_three(grid):
    _red, _green, height, width = _geometry(grid)
    return _solid(height, min(width, 3))


def _fixed_green_protrusion(grid):
    _red, green, height, _width = _geometry(grid)
    return _solid(height, green[3] - green[1] + 1 - 3)


def _red_box_only(grid):
    red = _bounds(grid, 2)
    return _solid(red[2] - red[0] + 1, red[3] - red[1] + 1)


def _green_box_only(grid):
    green = _bounds(grid, 3)
    return _solid(green[2] - green[0] + 1, green[3] - green[1] + 1)


def _union_box(grid):
    red, green, _height, _width = _geometry(grid)
    return _solid(max(red[2], green[2]) - min(red[0], green[0]) + 1,
                  max(red[3], green[3]) - min(red[1], green[1]) + 1)


def _minimum_box_spans(grid):
    red, green, _height, _width = _geometry(grid)
    return _solid(min(red[2] - red[0], green[2] - green[0]) + 1,
                  min(red[3] - red[1], green[3] - green[1]) + 1)


def _point_counts(grid):
    observed = observe_overrides(grid)
    return _solid(observed["n_red"], observed["n_green"])


def _wide_overlap(grid):
    _red, _green, height, width = _geometry(grid)
    return width > height


def _wide_over_three(grid):
    return _geometry(grid)[3] > 3


def _reversed_boundary(grid):
    red, green, _height, _width = _geometry(grid)
    return green[0] < red[0] <= green[2] < red[2] and green[1] < red[1] <= green[3] < red[3]


def _variable_protrusion(grid):
    _red, green, _height, width = _geometry(grid)
    return max(1, green[3] - green[1] + 1 - 3) != width


CANONICAL_SHORTCUTS = {
    "directed_corners": _directed_corners,
    "sorted_dimensions": _sorted_dimensions,
    "width_cap_three": _width_cap_three,
    "fixed_green_protrusion": _fixed_green_protrusion,
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "red_box_only": _red_box_only,
    "green_box_only": _green_box_only,
    "union_box": _union_box,
    "minimum_box_spans": _minimum_box_spans,
    "point_counts": _point_counts,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    "reversed_boundary": _reversed_boundary,
    "wide_overlap": _wide_overlap,
    "wide_over_three": _wide_over_three,
    "variable_protrusion": _variable_protrusion,
}
WITNESS_RIVALS = {
    "reversed_boundary": ["directed_corners"],
    "wide_overlap": ["sorted_dimensions"],
    "wide_over_three": ["width_cap_three"],
    "variable_protrusion": ["fixed_green_protrusion"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a claim of unique induction."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
