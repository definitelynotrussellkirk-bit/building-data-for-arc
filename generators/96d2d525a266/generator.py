"""Input sampler for drawing rectangle outlines from opposite-corner markers.

The canonical Racket rule examines each non-background color in row-major
first-occurrence order. Exactly two cells in distinct rows and columns define
opposite rectangle corners; that color paints the bounding-box outline. Every
other color is a decoy. Existing colors may be overwritten, and overlapping
outlines therefore make the first-occurrence order observable.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "96d2d525a266"
TASK_ID = GENERATOR_ID
RULE_HASH = "c060c7f67bbd"
VERSION = "4.0.0"
SUMMARY = (
    "On a 0-background grid, each color occurring exactly twice at positions "
    "in distinct rows and columns marks opposite rectangle corners. Paint that "
    "rectangle's outline in the marker color. Ignore singletons, aligned exact "
    "pairs, and colors occurring three or more times. Outlines may cross and "
    "overwrite existing cells; qualifying colors are applied in row-major "
    "first-occurrence order, matching the canonical Racket authority."
)

INVARIANTS = [
    "1..4 qualifying colors occur exactly twice in distinct rows and columns",
    "0..4 decoy colors are singletons, aligned exact pairs, or 3+ cell groups",
    "all marker cells are distinct and use colors 1..9 on background 0",
    "overlapping boxes and outline-overwrite interactions are lawful",
    "ordinary samples alternate decoy-control and interaction-control teaching slots",
]

AXES = {
    "grid_h": {"type": "int", "default": "10..20; canonical shapes favored", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "10..20; canonical shapes favored", "valid": "10..20"},
    "n_pair_colors": {
        "type": "int",
        "default": "1..4; interaction-control slots use 2..4",
        "valid": "1..4",
    },
    "n_decoy_colors": {
        "type": "int",
        "default": "1..4; exact overrides may request 0",
        "valid": "0..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_CANONICAL_SHAPES = ((10, 10), (12, 14), (13, 10), (13, 11), (10, 14))
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("decoy_controls", "interaction_controls")


def _validate_call(seed, sample_index, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(f"sample_index must be an integer, not {type(sample_index).__name__}")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _weighted_int(ctx, name, lo, hi, *, anchor=None, favored=()):
    """Draw an exact integer axis while keeping every advertised value legal."""
    options = list(range(lo, hi + 1))
    if anchor is not None:
        options.extend([anchor] * 80)
    options.extend(list(favored) * 12)
    return ctx.draw_choice(name, options)


def _scheduled_count(ctx, name, lo, hi, *, minimum, favored=()):
    """Honor exact overrides; keep ordinary lesson slots semantically complete."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    options = list(range(max(lo, minimum), hi + 1))
    options.extend(value for value in favored if value >= minimum)
    options.extend(value for value in favored if value >= minimum)
    return ctx.draw_choice(name, options)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the two-slot teaching schedule used by lesson assembly."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _positions_by_color(grid):
    result = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result[value].append((r, c))
    return dict(result)


def _colors_in_order(grid):
    result = []
    seen = set()
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def _rect_outline(a, b):
    r1, r2 = sorted((a[0], b[0]))
    c1, c2 = sorted((a[1], b[1]))
    return [
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    ]


def _bbox(a, b):
    return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


def _boxes_overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _empty_cells(grid, *, outside_box=None):
    cells = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            if outside_box is not None:
                top, left, bottom, right = outside_box
                if top <= r <= bottom and left <= c <= right:
                    continue
            cells.append((r, c))
    return cells


def _put_pair(grid, color, a, b):
    if a == b or a[0] == b[0] or a[1] == b[1]:
        raise ValueError("qualifying pair endpoints must use distinct rows and columns")
    if grid[a[0]][a[1]] != 0 or grid[b[0]][b[1]] != 0:
        raise ValueError("pair endpoint collision")
    grid[a[0]][a[1]] = color
    grid[b[0]][b[1]] = color


def _place_random_pair(grid, color, rng, *, avoid_box=None):
    cells = _empty_cells(grid)
    for _ in range(512):
        a, b = rng.sample(cells, 2)
        if a[0] == b[0] or a[1] == b[1]:
            continue
        if avoid_box is not None and _boxes_overlap(_bbox(a, b), avoid_box):
            continue
        _put_pair(grid, color, a, b)
        return (a, b)
    for i, a in enumerate(cells):
        for b in cells[i + 1 :]:
            if a[0] == b[0] or a[1] == b[1]:
                continue
            if avoid_box is not None and _boxes_overlap(_bbox(a, b), avoid_box):
                continue
            _put_pair(grid, color, a, b)
            return (a, b)
    raise RuntimeError("could not place a qualifying pair constructively")


def _place_singleton(grid, color, rng, *, outside_box=None, preferred=()):
    for r, c in preferred:
        if grid[r][c] == 0:
            grid[r][c] = color
            return [(r, c)]
    cells = _empty_cells(grid, outside_box=outside_box)
    if not cells:
        raise RuntimeError("no empty cell for singleton decoy")
    r, c = rng.choice(cells)
    grid[r][c] = color
    return [(r, c)]


def _place_aligned_pair(grid, color, rng, *, outside_box=None):
    h, w = len(grid), len(grid[0])
    for _ in range(512):
        horizontal = bool(rng.randrange(2))
        if horizontal:
            r = rng.randrange(h)
            c1, c2 = sorted(rng.sample(range(w), 2))
            if c2 - c1 < 2:
                continue
            points = ((r, c1), (r, c2))
        else:
            c = rng.randrange(w)
            r1, r2 = sorted(rng.sample(range(h), 2))
            if r2 - r1 < 2:
                continue
            points = ((r1, c), (r2, c))
        if outside_box is not None and any(
            outside_box[0] <= r <= outside_box[2] and outside_box[1] <= c <= outside_box[3]
            for r, c in points
        ):
            continue
        if all(grid[r][c] == 0 for r, c in points):
            for r, c in points:
                grid[r][c] = color
            return list(points)
    raise RuntimeError("could not place aligned-pair decoy constructively")


def _place_multi_decoy(grid, color, rng, *, outside_box=None):
    """Place a 3-cell non-collinear group whose bbox rival adds new pixels."""
    h, w = len(grid), len(grid[0])
    for _ in range(512):
        top = rng.randrange(h - 2)
        left = rng.randrange(w - 2)
        variants = (
            ((top, left), (top + 2, left + 2), (top + 1, left)),
            ((top, left + 2), (top + 2, left), (top + 1, left + 2)),
            ((top, left), (top, left + 2), (top + 2, left + 1)),
        )
        points = rng.choice(variants)
        if outside_box is not None and any(
            outside_box[0] <= r <= outside_box[2] and outside_box[1] <= c <= outside_box[3]
            for r, c in points
        ):
            continue
        if all(grid[r][c] == 0 for r, c in points):
            for r, c in points:
                grid[r][c] = color
            return list(points)
    cells = _empty_cells(grid, outside_box=outside_box)
    for _ in range(512):
        points = rng.sample(cells, 3)
        rows = {r for r, _ in points}
        cols = {c for _, c in points}
        if len(rows) >= 2 and len(cols) >= 2:
            for r, c in points:
                grid[r][c] = color
            return list(points)
    raise RuntimeError("could not place multi-cell decoy constructively")


def _special_decoy_controls(grid, colors, rng):
    """Place aligned-pair and 3-cell decoys in a protected 4x4 corner.

    Qualifying rectangles are subsequently kept outside this box, so both
    wrong shortcuts remain observably wrong after every later overwrite.
    """
    if len(colors) < 2:
        raise ValueError("decoy-control profile needs two colors")
    h, w = len(grid), len(grid[0])
    top = 0 if rng.randrange(2) == 0 else h - 4
    left = 0 if rng.randrange(2) == 0 else w - 4
    flip_r = bool(rng.randrange(2))
    flip_c = bool(rng.randrange(2))

    def point(dr, dc):
        return (
            top + (3 - dr if flip_r else dr),
            left + (3 - dc if flip_c else dc),
        )

    aligned = (point(0, 0), point(0, 3))
    multi = (point(1, 0), point(1, 2), point(3, 1))
    if any(grid[r][c] != 0 for r, c in (*aligned, *multi)):
        raise ValueError("reserved decoy-control box is not empty")
    for r, c in aligned:
        grid[r][c] = colors[0]
    for r, c in multi:
        grid[r][c] = colors[1]
    return (top, left, top + 3, left + 3)


def _special_overlap_pairs(grid, colors, rng, *, order_sensitive):
    """Place two interacting boxes in a corner, reserving a 7x5 zone."""
    h, w = len(grid), len(grid[0])
    top = 0 if rng.randrange(2) == 0 else h - 7
    left = 0 if rng.randrange(2) == 0 else w - 5
    flip = bool(rng.randrange(2))

    def col(offset):
        return left + (4 - offset if flip else offset)

    a1, a2 = (top, col(0)), (top + 3, col(3))
    b1, b2 = (top + 3, col(1)), (top + 6, col(4))
    first, second = colors[:2]
    if order_sensitive and first < second:
        first, second = second, first
    _put_pair(grid, first, a1, a2)
    _put_pair(grid, second, b1, b2)
    return [(first, (a1, a2)), (second, (b1, b2))], (top, left, top + 6, left + 4)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_h, canonical_w = _CANONICAL_SHAPES[sample_index % len(_CANONICAL_SHAPES)]
    profile = schedule_profile(seed, sample_index, difficulty)
    if difficulty == "easy":
        pair_favored, decoy_favored = (1, 2), (1, 2)
    elif difficulty == "hard":
        pair_favored, decoy_favored = (3, 4, 4), (2, 3, 4)
    else:
        pair_favored, decoy_favored = (2, 3), (1, 2, 3)

    h = _weighted_int(ctx, "grid_h", 10, 20, anchor=canonical_h)
    w = _weighted_int(ctx, "grid_w", 10, 20, anchor=canonical_w)
    n_pairs = _scheduled_count(
        ctx,
        "n_pair_colors",
        1,
        4,
        minimum=2 if profile == "interaction_controls" else 1,
        favored=pair_favored,
    )
    n_decoys = _scheduled_count(
        ctx,
        "n_decoy_colors",
        0,
        4,
        minimum=2 if profile == "decoy_controls" else 1,
        favored=decoy_favored,
    )

    total_colors = n_pairs + n_decoys
    palette = ctx.draw_rng("palette").sample(range(1, 10), total_colors)
    pair_colors = palette[:n_pairs]
    decoy_colors = palette[n_pairs:]
    if profile == "interaction_controls" and n_pairs >= 2:
        high = max(pair_colors)
        low = min(pair_colors)
        middle = [color for color in pair_colors if color not in (high, low)]
        pair_colors = [high, low] + middle

    grid = full_grid(h, w, 0)
    pair_records = []
    reserved_box = None
    pair_rng = ctx.draw_rng("pair_layout")
    decoy_rng = ctx.draw_rng("decoy_layout")
    preplaced_decoys = 0

    if profile == "decoy_controls" and n_decoys >= 2:
        reserved_box = _special_decoy_controls(grid, decoy_colors[:2], decoy_rng)
        preplaced_decoys = 2

    if profile == "interaction_controls" and n_pairs >= 2:
        placed, reserved_box = _special_overlap_pairs(
            grid, pair_colors, pair_rng, order_sensitive=True
        )
        pair_records.extend(placed)
        remaining_colors = pair_colors[2:]
    else:
        remaining_colors = pair_colors

    for color in remaining_colors:
        points = _place_random_pair(
            grid,
            color,
            pair_rng,
            avoid_box=reserved_box,
        )
        pair_records.append((color, points))

    remaining_decoys = decoy_colors[preplaced_decoys:]
    styles = []
    if remaining_decoys:
        if profile == "interaction_controls" and pair_records:
            styles.append("overwrite")
        else:
            styles.append(("single", "aligned", "multi")[sample_index % 3])
        cycle = ("single", "aligned", "multi")
        styles.extend(
            cycle[(sample_index + i) % len(cycle)]
            for i in range(len(remaining_decoys) - 1)
        )

    for color, style in zip(remaining_decoys, styles):
        if style == "overwrite":
            _, endpoints = pair_records[0]
            candidates = [
                point
                for point in _rect_outline(*endpoints)
                if point not in endpoints and grid[point[0]][point[1]] == 0
            ]
            if candidates:
                _place_singleton(grid, color, decoy_rng, preferred=(decoy_rng.choice(candidates),))
            else:
                _place_singleton(grid, color, decoy_rng, outside_box=reserved_box)
        elif style == "aligned":
            _place_aligned_pair(grid, color, decoy_rng, outside_box=reserved_box)
        elif style == "multi":
            _place_multi_decoy(grid, color, decoy_rng, outside_box=reserved_box)
        else:
            _place_singleton(grid, color, decoy_rng, outside_box=reserved_box)

    return grid


def observe_overrides(grid):
    """Recover every advertised exact axis from returned input pixels."""
    by_color = _positions_by_color(grid)
    pairs = sum(
        len(cells) == 2
        and cells[0][0] != cells[1][0]
        and cells[0][1] != cells[1][1]
        for cells in by_color.values()
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pair_colors": pairs,
        "n_decoy_colors": len(by_color) - pairs,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the actual canonical rule domain, not only this sampler's subset."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["ARC grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    by_color = _positions_by_color(grid)
    if not any(
        len(cells) == 2
        and cells[0][0] != cells[1][0]
        and cells[0][1] != cells[1][1]
        for cells in by_color.values()
    ):
        return ["expected at least one exact diagonal corner-pair color"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _reference_output(grid, *, order=None, background_only=False):
    source = deepcopy(grid)
    out = deepcopy(grid)
    by_color = _positions_by_color(source)
    colors = _colors_in_order(source) if order is None else list(order)
    for color in colors:
        cells = by_color[color]
        if (
            len(cells) != 2
            or cells[0][0] == cells[1][0]
            or cells[0][1] == cells[1][1]
        ):
            continue
        for r, c in _rect_outline(cells[0], cells[1]):
            if not background_only or out[r][c] in (0, color):
                out[r][c] = color
    return out


def _aligned_pairs_also_expand(grid):
    source = deepcopy(grid)
    out = deepcopy(grid)
    by_color = _positions_by_color(source)
    for color in _colors_in_order(source):
        cells = by_color[color]
        if len(cells) == 2:
            for r, c in _rect_outline(cells[0], cells[1]):
                out[r][c] = color
    return out


def _multi_bbox_also_expands(grid):
    source = deepcopy(grid)
    out = deepcopy(grid)
    by_color = _positions_by_color(source)
    for color in _colors_in_order(source):
        cells = by_color[color]
        if len(cells) < 2:
            continue
        rows = [point[0] for point in cells]
        cols = [point[1] for point in cells]
        if min(rows) == max(rows) or min(cols) == max(cols):
            continue
        for r, c in _rect_outline((min(rows), min(cols)), (max(rows), max(cols))):
            out[r][c] = color
    return out


def _background_only_outlines(grid):
    return _reference_output(grid, background_only=True)


def _numeric_color_order(grid):
    return _reference_output(grid, order=sorted(_positions_by_color(grid)))


def _differs(rival):
    return lambda grid: _reference_output(grid) != rival(grid)


SEMANTIC_RIVALS = {
    "aligned_pairs_also_expand": _aligned_pairs_also_expand,
    "multi_bbox_also_expands": _multi_bbox_also_expands,
    "background_only_outlines": _background_only_outlines,
    "numeric_color_order": _numeric_color_order,
}
SEMANTIC_WITNESSES = {
    "aligned_pair_exclusion": _differs(_aligned_pairs_also_expand),
    "exact_two_count": _differs(_multi_bbox_also_expands),
    "overwrite_existing_cells": _differs(_background_only_outlines),
    "first_occurrence_order": _differs(_numeric_color_order),
}
WITNESS_RIVALS = {
    "aligned_pair_exclusion": ["aligned_pairs_also_expand"],
    "exact_two_count": ["multi_bbox_also_expands"],
    "overwrite_existing_cells": ["background_only_outlines"],
    "first_occurrence_order": ["numeric_color_order"],
}
CANONICAL_SHORTCUTS = {
    "aligned_pairs_also_expand": _aligned_pairs_also_expand,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
