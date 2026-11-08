"""Constructive inputs for completing same-color rectangle corners.

The canonical Racket program is the only label authority.  This module samples
lawful inputs, exposes an exact Python mirror for review/tests, and schedules
four complementary profiles so any one held-out example still leaves evidence
against the declared canonical shortcuts.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d89b3f447c00"
TASK_ID = GENERATOR_ID
RULE_HASH = "1bf2bf24e722"
VERSION = "3.1.0"
SUMMARY = (
    "Zero-background 6..20 grids containing 1..5 distinct-colored rectangle "
    "clues.  Each color has exactly one axis-aligned rectangle with three of "
    "its four corners present; selected teaching profiles also include one "
    "same-color interior marker that shares neither clue row nor clue column. "
    "Complete every color's missing fourth corner and preserve all other cells."
)
INVARIANTS = [
    "rectangular integer ARC grid with zero background",
    "1..5 foreground colors, each with one unique three-of-four rectangle",
    "every missing corner is background and completion targets are distinct",
    "layouts are constructive: requested rectangle counts are never silently dropped",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile/band choice", "valid": "6..20"},
    "grid_w": {"type": "int", "default": "profile/band choice", "valid": "6..20"},
    "rect_count": {"type": "int", "default": "profile choice", "valid": "1..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = ("canonical", "many", "extra_marker", "minimal")
_CANONICAL_SHAPES = ((7, 8), (6, 9), (8, 8), (7, 9))


def _validate_call_arguments(seed, sample_index):
    """Reject scalar coercions before they can perturb deterministic draws."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive indices contain all teaching profiles."""
    _validate_call_arguments(seed, sample_index)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_axis(ctx, name, lo, hi, defaults):
    """Honor exact controls globally; defaults may be profile-specific."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(defaults))


def _capacity(region, cell_size):
    r0, c0, r1, c1 = region
    return ((r1 - r0 + 1) // cell_size) * ((c1 - c0 + 1) // cell_size)


def _partition(region, count, rng, cell_size):
    """Guillotine-pack ``count`` non-overlapping regions constructively."""
    if count == 1:
        if _capacity(region, cell_size) < 1:
            raise ValueError("region cannot fit a rectangle clue")
        return [region]

    r0, c0, r1, c1 = region
    choices = []
    for cut in range(r0 + cell_size, r1 - cell_size + 2):
        first = (r0, c0, cut - 1, c1)
        second = (cut, c0, r1, c1)
        for first_count in range(1, count):
            if (
                _capacity(first, cell_size) >= first_count
                and _capacity(second, cell_size) >= count - first_count
            ):
                choices.append((first, second, first_count))
    for cut in range(c0 + cell_size, c1 - cell_size + 2):
        first = (r0, c0, r1, cut - 1)
        second = (r0, cut, r1, c1)
        for first_count in range(1, count):
            if (
                _capacity(first, cell_size) >= first_count
                and _capacity(second, cell_size) >= count - first_count
            ):
                choices.append((first, second, first_count))
    if not choices:
        raise ValueError("canvas cannot fit the requested rectangle clues")
    first, second, first_count = rng.choice(choices)
    return _partition(first, first_count, rng, cell_size) + _partition(
        second, count - first_count, rng, cell_size
    )


def _touches_canvas(region, height, width):
    r0, c0, r1, c1 = region
    return r0 == 0 or c0 == 0 or r1 == height - 1 or c1 == width - 1


def _box(region, height, width, rng, *, min_size=2, minimal=False, boundary=False):
    r0, c0, r1, c1 = region
    region_h, region_w = r1 - r0 + 1, c1 - c0 + 1
    if minimal:
        box_h = box_w = 2
    else:
        box_h = rng.randint(min_size, min(region_h, 7))
        box_w = rng.randint(min_size, min(region_w, 7))
    top = rng.randint(r0, r1 - box_h + 1)
    left = rng.randint(c0, c1 - box_w + 1)

    if boundary:
        sides = []
        if r0 == 0:
            sides.append("top")
        if c0 == 0:
            sides.append("left")
        if r1 == height - 1:
            sides.append("bottom")
        if c1 == width - 1:
            sides.append("right")
        if not sides:
            raise RuntimeError("boundary profile selected a non-boundary region")
        side = rng.choice(sides)
        if side == "top":
            top = 0
        elif side == "left":
            left = 0
        elif side == "bottom":
            top = height - box_h
        else:
            left = width - box_w
    return top, left, top + box_h - 1, left + box_w - 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    profile_rng = ctx.draw_rng("profile_defaults")

    if profile == "canonical":
        default_h, default_w = profile_rng.choice(_CANONICAL_SHAPES)
        height_defaults, width_defaults, count_defaults = (default_h,), (default_w,), (2,)
    elif profile == "many":
        lo = {"easy": 10, "medium": 11, "hard": 13}.get(difficulty, 10)
        height_defaults = tuple(range(lo, 21))
        width_defaults = tuple(range(lo, 21))
        count_defaults = (4, 5)
    elif profile == "extra_marker":
        # Keep one adversarial profile on the exact canonical morphology
        # envelope: the extra same-color point, not size/palette drift, is what
        # must refute the three-markers-only shortcut.
        default_h, default_w = profile_rng.choice(_CANONICAL_SHAPES)
        height_defaults, width_defaults, count_defaults = (default_h,), (default_w,), (2,)
    else:  # minimal
        lo, hi = {"easy": (6, 10), "medium": (8, 14), "hard": (11, 20)}.get(
            difficulty, (7, 16)
        )
        height_defaults = tuple(range(lo, hi + 1))
        width_defaults = tuple(range(lo, hi + 1))
        count_defaults = (3,)

    height = _draw_axis(ctx, "grid_h", 6, 20, height_defaults)
    width = _draw_axis(ctx, "grid_w", 6, 20, width_defaults)
    rect_count = _draw_axis(ctx, "rect_count", 1, 5, count_defaults)

    wants_extra = profile in {"many", "extra_marker"}
    wants_minimal = profile in {"many", "minimal"}
    # Exact overrides can intentionally leave the scheduled profile's feasible
    # envelope.  Preserve every exact axis and degrade only the non-axis teaching
    # decoration, never the requested number of clues.
    needs_three_by_three = wants_extra or profile == "canonical"
    cell_size = (
        3
        if needs_three_by_three
        and _capacity((0, 0, height - 1, width - 1), 3) >= rect_count
        else 2
    )
    canonical_nonminimal = profile == "canonical" and cell_size == 3
    extra_index = 0 if wants_extra and cell_size == 3 else None
    if wants_minimal:
        minimal_index = 1 if extra_index == 0 and rect_count >= 2 else 0
        if minimal_index == extra_index:
            minimal_index = None
    else:
        minimal_index = None

    regions = _partition(
        (0, 0, height - 1, width - 1),
        rect_count,
        ctx.draw_rng("partition"),
        cell_size,
    )
    ctx.draw_rng("region_order").shuffle(regions)

    boundary_index = minimal_index
    if boundary_index is not None and not _touches_canvas(regions[boundary_index], height, width):
        replacement = next(
            (i for i, region in enumerate(regions) if _touches_canvas(region, height, width)),
            None,
        )
        if replacement is not None:
            regions[boundary_index], regions[replacement] = regions[replacement], regions[boundary_index]

    colors = ctx.draw_rng("palette").sample(list(range(1, 10)), rect_count)
    missing_offset = ctx.draw_rng("missing_corners").randrange(4)
    grid = full_grid(height, width, 0)

    for index, (color, region) in enumerate(zip(colors, regions)):
        add_extra = index == extra_index
        minimal = index == minimal_index
        box = _box(
            region,
            height,
            width,
            ctx.draw_rng(f"box_{index}"),
            min_size=3 if add_extra or canonical_nonminimal else 2,
            minimal=minimal,
            boundary=index == boundary_index,
        )
        top, left, bottom, right = box
        corners = [(top, left), (top, right), (bottom, left), (bottom, right)]
        missing = (missing_offset + index) % 4
        for corner_index, (row, column) in enumerate(corners):
            if corner_index != missing:
                grid[row][column] = color
        if add_extra:
            # A strictly interior point introduces a fourth same-color cell but
            # shares neither clue row nor clue column, so it creates no second
            # three-corner rectangle.
            row = ctx.draw_rng(f"extra_row_{index}").randint(top + 1, bottom - 1)
            column = ctx.draw_rng(f"extra_col_{index}").randint(left + 1, right - 1)
            if grid[row][column] != 0:
                raise RuntimeError("constructive extra marker collided")
            grid[row][column] = color
    return grid


def _points(grid):
    result = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                result.setdefault(color, []).append((row_index, column_index))
    return result


def _rectangles(cells):
    """All original-cell rectangles having exactly one missing corner."""
    cell_set = set(cells)
    rows = sorted({row for row, _ in cells})
    columns = sorted({column for _, column in cells})
    records = []
    for top, bottom in combinations(rows, 2):
        for left, right in combinations(columns, 2):
            corners = ((top, left), (top, right), (bottom, left), (bottom, right))
            occupied = [point for point in corners if point in cell_set]
            if len(occupied) == 3:
                missing = next(point for point in corners if point not in cell_set)
                records.append(
                    {
                        "top": top,
                        "left": left,
                        "bottom": bottom,
                        "right": right,
                        "missing": missing,
                    }
                )
    return records


def rule_mirror(grid):
    """Exact pure mirror of the pinned one-pass Racket authority."""
    output = [list(row) for row in grid]
    for color, cells in _points(grid).items():
        for record in _rectangles(cells):
            row, column = record["missing"]
            output[row][column] = color
    return output


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rect_count": len(_points(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    by_color = _points(grid)
    if not 1 <= len(by_color) <= 5:
        errors.append(f"expected 1..5 foreground colors, found {len(by_color)}")
    targets = []
    for color, cells in sorted(by_color.items()):
        if not 3 <= len(cells) <= 4:
            errors.append(f"color {color}: expected three clue corners plus at most one extra marker")
        records = _rectangles(cells)
        if len(records) != 1:
            errors.append(f"color {color}: expected exactly one three-corner rectangle, found {len(records)}")
            continue
        target = records[0]["missing"]
        targets.append((color, target))
        row, column = target
        if grid[row][column] != 0:
            errors.append(f"color {color}: missing corner is not background")
    if len({target for _, target in targets}) != len(targets):
        errors.append("different colors share a completion target")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    by_color = _points(grid)
    if len(by_color) != 2 or any(len(cells) != 3 for cells in by_color.values()):
        return ["strict profile requires exactly two three-corner colors"]
    if any(
        record["bottom"] - record["top"] < 2 or record["right"] - record["left"] < 2
        for cells in by_color.values()
        for record in _rectangles(cells)
    ):
        return ["strict profile requires non-minimal rectangles"]
    return []


def semantic_observables(grid):
    by_color = _points(grid)
    records = [record for cells in by_color.values() for record in _rectangles(cells)]
    more_than_two = len(by_color) > 2
    extra = any(len(cells) > 3 for cells in by_color.values())
    minimal = any(
        record["bottom"] - record["top"] == 1 or record["right"] - record["left"] == 1
        for record in records
    )
    strict = strict_canonical_like(grid) == []
    if strict:
        profile = "canonical"
    elif more_than_two and extra and minimal:
        profile = "many"
    elif extra:
        profile = "extra_marker"
    elif more_than_two and minimal:
        profile = "minimal"
    else:
        profile = "unknown"
    return {
        "profile": profile,
        "more_than_two_colors": more_than_two,
        "extra_same_color_marker": extra,
        "minimal_rectangle": minimal,
        "strict_canonical": strict,
    }


def _restricted_completion(grid, mode):
    output = [list(row) for row in grid]
    by_color = _points(grid)
    allowed_colors = set(sorted(by_color)[:2]) if mode == "two_colors_only" else set(by_color)
    for color, cells in by_color.items():
        if color not in allowed_colors:
            continue
        if mode == "three_markers_only" and len(cells) != 3:
            continue
        for record in _rectangles(cells):
            if mode == "nonminimal_only" and (
                record["bottom"] - record["top"] == 1
                or record["right"] - record["left"] == 1
            ):
                continue
            row, column = record["missing"]
            output[row][column] = color
    return output


def _two_colors_only(grid):
    return _restricted_completion(grid, "two_colors_only")


def _three_markers_only(grid):
    return _restricted_completion(grid, "three_markers_only")


def _nonminimal_only(grid):
    return _restricted_completion(grid, "nonminimal_only")


def _more_than_two_colors(grid):
    return len(_points(grid)) > 2


def _extra_same_color_marker(grid):
    return any(len(cells) > 3 for cells in _points(grid).values())


def _minimal_rectangle(grid):
    return any(
        record["bottom"] - record["top"] == 1 or record["right"] - record["left"] == 1
        for cells in _points(grid).values()
        for record in _rectangles(cells)
    )


SEMANTIC_WITNESSES = {
    "more_than_two_colors": _more_than_two_colors,
    "extra_same_color_marker": _extra_same_color_marker,
    "minimal_rectangle": _minimal_rectangle,
}
SEMANTIC_RIVALS = {
    "two_colors_only": _two_colors_only,
    "three_markers_only": _three_markers_only,
    "nonminimal_only": _nonminimal_only,
}
WITNESS_RIVALS = {
    "more_than_two_colors": ["two_colors_only"],
    "extra_same_color_marker": ["three_markers_only"],
    "minimal_rectangle": ["nonminimal_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check using demonstration labels only."""
    minimum_demos = EXAMPLES_NEEDED - 1
    if not isinstance(demos, (list, tuple)) or len(demos) < minimum_demos:
        return [f"need at least {minimum_demos} demonstrations"]
    errors = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output")
        else:
            errors.extend(f"demo {index}: {error}" for error in self_check(pair["input"]))
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query must contain an input")
    else:
        errors.extend(f"query: {error}" for error in self_check(query["input"]))
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute {name}")
    return errors
