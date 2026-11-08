"""Generator for ARC task dcfb4c64c914 — row-profile difference histogram.

A full-height gray divider separates two panels.  Each panel contains one
monochrome connected object.  Count cells on each row of each object's own
bounding box, pad the shorter profile with zeros, take elementwise absolute
differences, and render the result as a left-justified cyan histogram.

The public examples happen to place both objects on the same canvas rows.  The
default curriculum deliberately includes vertically staggered objects, so the
plausible but wrong shortcut "compare absolute canvas rows" is falsified.
Likewise, gapped rows distinguish cell counts from horizontal spans.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dcfb4c64c914"
TASK_ID = "dcfb4c64c914"
VERSION = "3.0.0"
RULE_HASH = "53fe6f709bdc"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A centered full-height gray divider separates two independently placed "
    "monochrome connected objects.  Count object cells per row in each "
    "object's own bounding box, zero-pad the shorter row profile, take "
    "elementwise absolute differences, and draw that list as a left-justified "
    "cyan histogram."
)

INVARIANTS = [
    "the grid has exactly one centered full-height gray(5) divider",
    "each panel contains exactly one monochrome 4-connected object",
    "the two objects use distinct nonzero colors other than gray(5) and cyan(8)",
    "row profiles count cells in object-local bounding-box rows, not spans or canvas rows",
    "the two object-local profiles have a nonzero absolute difference",
    "all declared override axes are exact and recoverable from the returned grid",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

_LAYOUT_DIMS = {
    "canonical_8x15": (8, 15),
    "canonical_9x15": (9, 15),
    "canonical_9x17": (9, 17),
    "wide_10x19": (10, 19),
}
LAYOUTS = tuple(_LAYOUT_DIMS)
PROFILE_CASES = (
    "equal_mixed",
    "equal_left_dominant",
    "equal_right_dominant",
    "left_taller_mixed",
    "right_taller_mixed",
)
GEOMETRY_MODES = ("contiguous", "gapped")
PLACEMENT_MODES = ("aligned", "staggered")
COLOR_PAIRS = ("2-4", "4-2", "1-7", "3-9")

AXES = {
    "layout": {
        "type": "enum",
        "default": "four-slot teaching schedule",
        "valid": "canonical_8x15|canonical_9x15|canonical_9x17|wide_10x19",
        "doc": "Exact observable grid dimensions.",
    },
    "profile_case": {
        "type": "enum",
        "default": "four-slot teaching schedule",
        "valid": "equal_mixed|equal_left_dominant|equal_right_dominant|left_taller_mixed|right_taller_mixed",
        "doc": "Exact relation between the two zero-padded object-local row profiles.",
    },
    "geometry_mode": {
        "type": "enum",
        "default": "alternates contiguous and internally gapped rows",
        "valid": "contiguous|gapped",
        "doc": "Whether every occupied object row is contiguous or at least one row has an internal gap.",
    },
    "placement_mode": {
        "type": "enum",
        "default": "alternates aligned and staggered object tops",
        "valid": "aligned|staggered",
        "doc": "Whether the two object bounding boxes start on the same canvas row.",
    },
    "color_pair": {
        "type": "enum",
        "default": "four-slot teaching schedule",
        "valid": "2-4|4-2|1-7|3-9",
        "doc": "Exact ordered left-right object color pair.",
    },
}

# Four consecutive generated pairs form a complete teaching window.  Any one
# may be held out as the query: the remaining three still contain a staggered
# example, a gapped-row example, an unequal-height example, and both signs of
# profile comparison.
SCHEDULE_PROFILES = (
    ("canonical_8x15", "left_taller_mixed", "gapped", "staggered", "2-4"),
    ("canonical_9x15", "equal_left_dominant", "contiguous", "aligned", "4-2"),
    ("canonical_9x17", "equal_right_dominant", "gapped", "staggered", "1-7"),
    ("wide_10x19", "right_taller_mixed", "contiguous", "aligned", "3-9"),
)

# Every left profile has a 3+-cell row followed by a 2-cell row.  In gapped
# mode that second row becomes {0, 2}; the row above keeps the whole object
# connected while making cell-count and row-span interpretations disagree.
# Profile values themselves are generated constructively rather than drawn
# from a small fixed bank, so the output curriculum remains broad.

def _draw_profiles(
    rng, profile_case: str, difficulty: str | None
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    # Difficulty changes latent numerical complexity while leaving every
    # declared observable axis exact.  Easy uses short 1..4 profiles; hard
    # always uses the maximum five-row extent and the full 1..5 range.
    band = "medium" if difficulty is None else difficulty
    max_count = 4 if band == "easy" else 5
    if profile_case.startswith("equal_"):
        if band == "easy":
            left_height = right_height = 3
        elif band == "hard":
            left_height = right_height = 5
        else:
            left_height = right_height = rng.randint(3, 5)
    elif profile_case == "left_taller_mixed":
        if band == "easy":
            left_height, right_height = 4, 3
        elif band == "hard":
            left_height, right_height = 5, rng.randint(2, 4)
        else:
            left_height = rng.randint(4, 5)
            right_height = rng.randint(2, left_height - 1)
    elif profile_case == "right_taller_mixed":
        if band == "easy":
            left_height, right_height = 3, 4
        elif band == "hard":
            left_height, right_height = rng.randint(3, 4), 5
        else:
            right_height = rng.randint(4, 5)
            left_height = rng.randint(3, right_height - 1)
    else:
        raise ValueError(f"unknown profile case: {profile_case!r}")

    left = [rng.randint(1, max_count) for _ in range(left_height)]
    left[0] = rng.randint(3, max_count)
    left[1] = 2

    if profile_case == "equal_mixed":
        right = [rng.randint(1, max_count) for _ in range(right_height)]
        right[0] = rng.randint(1, left[0] - 1)  # left > right
        right[1] = rng.randint(3, max_count)    # right > left
    elif profile_case == "equal_left_dominant":
        right = [rng.randint(1, left[index]) for index in range(right_height)]
        right[0] = rng.randint(1, left[0] - 1)  # guarantee a strict row
    elif profile_case == "equal_right_dominant":
        right = [
            rng.randint(left[index], max_count) for index in range(right_height)
        ]
        right[1] = rng.randint(3, max_count)    # guarantee a strict row
    elif profile_case == "left_taller_mixed":
        right = [rng.randint(1, max_count) for _ in range(right_height)]
        right[1] = rng.randint(3, max_count)    # overlap has right > left
        # The positive left-only tail supplies the opposite sign.
    else:  # right_taller_mixed
        right = [rng.randint(1, max_count) for _ in range(right_height)]
        right[0] = rng.randint(1, left[0] - 1)  # overlap has left > right
        # The positive right-only tail supplies the opposite sign.

    pair = (tuple(left), tuple(right))
    if _profile_case(*pair) != profile_case:
        raise AssertionError(f"constructed profile relation drifted: {pair!r}")
    return pair

Cell = tuple[int, int]
Grid = list[list[int]]


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    """Return the deterministic four-slot curriculum profile."""
    del seed
    _validate_difficulty(difficulty)
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise TypeError("sample_index must be an integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    domains = {
        "layout": LAYOUTS,
        "profile_case": PROFILE_CASES,
        "geometry_mode": GEOMETRY_MODES,
        "placement_mode": PLACEMENT_MODES,
        "color_pair": COLOR_PAIRS,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} override must be a string")
        if value not in domains[name]:
            raise ValueError(
                f"{name} override {value!r} is not one of {domains[name]!r}"
            )


def _draw_axis(ctx, name: str, domain: tuple[str, ...], scheduled: str) -> str:
    options = domain if ctx.overrides.get(name) is not None else (scheduled,)
    return ctx.draw_choice(name, options)


def _shape_from_profile(
    profile: tuple[int, ...], geometry_mode: str, *, reflect: bool
) -> tuple[Cell, ...]:
    rows: list[list[int]] = [list(range(count)) for count in profile]
    if geometry_mode == "gapped":
        # All profile templates deliberately satisfy this constructive witness.
        gap_row = next(
            (
                index
                for index in range(1, len(profile))
                if profile[index] == 2 and profile[index - 1] >= 3
            ),
            None,
        )
        if gap_row is None:
            raise AssertionError("gapped profile lacks a supported 3+-then-2 witness")
        rows[gap_row] = [0, 2]

    width = max(max(cols) for cols in rows) + 1
    cells = [
        (row, width - 1 - col if reflect else col)
        for row, cols in enumerate(rows)
        for col in cols
    ]
    min_col = min(col for _, col in cells)
    return tuple(sorted((row, col - min_col) for row, col in cells))


def _shape_dims(shape: Iterable[Cell]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _paint_shape(
    grid: Grid, shape: Iterable[Cell], top: int, left: int, color: int
) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _choose_tops(
    rng, grid_h: int, left_h: int, right_h: int, placement_mode: str
) -> tuple[int, int]:
    left_options = tuple(range(1, grid_h - left_h))
    right_options = tuple(range(1, grid_h - right_h))
    if not left_options or not right_options:
        raise AssertionError("layout cannot provide one-row vertical margins")
    if placement_mode == "aligned":
        common = tuple(sorted(set(left_options) & set(right_options)))
        if not common:
            raise AssertionError("no aligned placement exists")
        top = rng.choice(common)
        return top, top
    pairs = tuple(
        (left_top, right_top)
        for left_top in left_options
        for right_top in right_options
        if left_top != right_top
        and max(left_top + left_h, right_top + right_h)
        - min(left_top, right_top)
        > max(left_h, right_h)
    )
    if not pairs:
        raise AssertionError("no staggered placement exists")
    return rng.choice(pairs)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout = _draw_axis(ctx, "layout", LAYOUTS, scheduled[0])
    profile_case = _draw_axis(ctx, "profile_case", PROFILE_CASES, scheduled[1])
    geometry_mode = _draw_axis(ctx, "geometry_mode", GEOMETRY_MODES, scheduled[2])
    placement_mode = _draw_axis(ctx, "placement_mode", PLACEMENT_MODES, scheduled[3])
    color_pair = _draw_axis(ctx, "color_pair", COLOR_PAIRS, scheduled[4])

    profile_rng = ctx.draw_rng("profile_values")
    left_profile, right_profile = _draw_profiles(profile_rng, profile_case, difficulty)
    shape_rng = ctx.draw_rng("shape_orientation")
    left_shape = _shape_from_profile(
        left_profile, geometry_mode, reflect=bool(shape_rng.randrange(2))
    )
    # Keep the right object contiguous in gapped examples.  One explicit gap is
    # enough to distinguish cell counts from row spans without cancellation.
    right_shape = _shape_from_profile(
        right_profile, "contiguous", reflect=bool(shape_rng.randrange(2))
    )

    height, width = _LAYOUT_DIMS[layout]
    divider = width // 2
    panel_width = divider
    left_h, left_w = _shape_dims(left_shape)
    right_h, right_w = _shape_dims(right_shape)
    if left_w + 2 > panel_width or right_w + 2 > panel_width:
        raise AssertionError("profile shape does not fit the selected panel with margins")

    placement_rng = ctx.draw_rng("object_placement")
    left_top, right_top = _choose_tops(
        placement_rng, height, left_h, right_h, placement_mode
    )
    left_col = placement_rng.choice(tuple(range(1, panel_width - left_w)))
    right_local_col = placement_rng.choice(tuple(range(1, panel_width - right_w)))
    right_col = divider + 1 + right_local_col

    left_color, right_color = (int(part) for part in color_pair.split("-"))
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 5
    _paint_shape(grid, left_shape, left_top, left_col, left_color)
    _paint_shape(grid, right_shape, right_top, right_col, right_color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    expected = {
        "layout": layout,
        "profile_case": profile_case,
        "geometry_mode": geometry_mode,
        "placement_mode": placement_mode,
        "color_pair": color_pair,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and executable rule mirror
# ---------------------------------------------------------------------------


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty sequence of rows"
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return "every row must be a sequence"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return "grid values must be integer ARC colors in 0..9"
    return None


def _panel_object(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
    col_lo: int,
    col_hi: int,
    side: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(col_lo, col_hi + 1)
        if grid[row][col] != 0
    ]
    if not cells:
        return None, [f"{side} panel needs a non-background object"]
    colors = {grid[row][col] for row, col in cells}
    errors: list[str] = []
    if len(colors) != 1:
        errors.append(
            f"{side} panel object must be monochrome, found colors {sorted(colors)}"
        )
        return None, errors
    color = next(iter(colors))
    remaining = set(cells)
    start = next(iter(remaining))
    queue = deque([start])
    seen: set[Cell] = set()
    while queue:
        row, col = queue.popleft()
        if (row, col) in seen:
            continue
        seen.add((row, col))
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in remaining and neighbor not in seen:
                queue.append(neighbor)
    if seen != remaining:
        errors.append(f"{side} panel object must be one 4-connected component")
        return None, errors

    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    profile = tuple(
        sum(row == target for row, _ in cells)
        for target in range(top, bottom + 1)
    )
    shape = tuple(sorted((row - top, col - left) for row, col in cells))
    return (
        {
            "color": color,
            "cells": tuple(sorted(cells)),
            "global_cells": tuple(sorted(cells)),
            "shape": shape,
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right,
            "height": bottom - top + 1,
            "width": right - left + 1,
            "profile": profile,
        },
        errors,
    )


def _padded_profiles(
    left: Iterable[int], right: Iterable[int]
) -> tuple[list[int], list[int]]:
    a = list(left)
    b = list(right)
    length = max(len(a), len(b))
    a.extend([0] * (length - len(a)))
    b.extend([0] * (length - len(b)))
    return a, b


def _profile_case(left: Iterable[int], right: Iterable[int]) -> str | None:
    raw_left = tuple(left)
    raw_right = tuple(right)
    a, b = _padded_profiles(raw_left, raw_right)
    signs = {1 if x > y else -1 if x < y else 0 for x, y in zip(a, b)}
    has_left = 1 in signs
    has_right = -1 in signs
    if len(raw_left) == len(raw_right):
        if has_left and has_right:
            return "equal_mixed"
        if has_left and not has_right:
            return "equal_left_dominant"
        if has_right and not has_left:
            return "equal_right_dominant"
        return None
    if len(raw_left) > len(raw_right) and has_left and has_right:
        return "left_taller_mixed"
    if len(raw_right) > len(raw_left) and has_left and has_right:
        return "right_taller_mixed"
    return None


def _has_internal_row_gap(obj: dict[str, Any]) -> bool:
    by_row: dict[int, list[int]] = {}
    for row, col in obj["global_cells"]:
        by_row.setdefault(row, []).append(col)
    return any(
        len(cols) != max(cols) - min(cols) + 1 for cols in by_row.values()
    )


def _analyze(grid: Any) -> dict[str, Any]:
    shape_error = _grid_error(grid)
    result: dict[str, Any] = {"errors": []}
    if shape_error:
        result["errors"] = [shape_error]
        return result

    height = len(grid)
    width = len(grid[0])
    errors: list[str] = []
    layout = next(
        (name for name, dims in _LAYOUT_DIMS.items() if dims == (height, width)),
        None,
    )
    if layout is None:
        errors.append(
            f"grid dimensions {(height, width)} are outside declared layouts"
        )

    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    result.update({"height": height, "width": width, "layout": layout, "dividers": dividers})
    if len(dividers) != 1:
        errors.append(
            f"expected exactly one full-height gray divider, found {len(dividers)}"
        )
        result["errors"] = errors
        return result
    divider = dividers[0]
    result["divider"] = divider
    if divider == 0 or divider == width - 1 or divider != (width - 1) // 2:
        errors.append("divider must split two nonempty equal-width panels")
    if any(
        grid[row][col] == 5
        for row in range(height)
        for col in range(width)
        if col != divider
    ):
        errors.append("gray(5) may occur only in the divider column")
    if any(value == 8 for row in grid for value in row):
        errors.append("input must not contain output color cyan(8)")

    left_obj, left_errors = _panel_object(grid, 0, divider - 1, "left")
    right_obj, right_errors = _panel_object(grid, divider + 1, width - 1, "right")
    errors.extend(left_errors)
    errors.extend(right_errors)
    result.update({"left": left_obj, "right": right_obj})
    if left_obj is None or right_obj is None:
        result["errors"] = sorted(set(errors))
        return result
    if left_obj["color"] in (0, 5, 8) or right_obj["color"] in (0, 5, 8):
        errors.append("object colors must exclude background(0), gray(5), and cyan(8)")
    if left_obj["color"] == right_obj["color"]:
        errors.append("left and right objects must use distinct colors")

    case = _profile_case(left_obj["profile"], right_obj["profile"])
    result["profile_case"] = case
    if case is None:
        a, b = _padded_profiles(left_obj["profile"], right_obj["profile"])
        if all(x == y for x, y in zip(a, b)):
            errors.append("object-local row-profile absolute difference must be nonempty")
        else:
            errors.append("profile relation is outside the declared teaching cases")

    geometry_mode = (
        "gapped"
        if _has_internal_row_gap(left_obj) or _has_internal_row_gap(right_obj)
        else "contiguous"
    )
    placement_mode = (
        "aligned" if left_obj["top"] == right_obj["top"] else "staggered"
    )
    result.update(
        {
            "geometry_mode": geometry_mode,
            "placement_mode": placement_mode,
            "color_pair": f"{left_obj['color']}-{right_obj['color']}",
        }
    )
    result["errors"] = sorted(set(errors))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    try:
        _validate_difficulty(difficulty)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _histogram(profile: Iterable[int], color: int = 8) -> Grid:
    values = list(profile)
    if not values:
        return []
    width = max(1, max(values))
    return [
        [color if col < value else 0 for col in range(width)] for value in values
    ]


def rule_mirror(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    left, right = _padded_profiles(
        analysis["left"]["profile"], analysis["right"]["profile"]
    )
    return _histogram(abs(a - b) for a, b in zip(left, right))


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    values = {
        "layout": analysis["layout"],
        "profile_case": analysis["profile_case"],
        "geometry_mode": analysis["geometry_mode"],
        "placement_mode": analysis["placement_mode"],
        "color_pair": analysis["color_pair"],
    }
    for name, domain in (
        ("layout", LAYOUTS),
        ("profile_case", PROFILE_CASES),
        ("geometry_mode", GEOMETRY_MODES),
        ("placement_mode", PLACEMENT_MODES),
        ("color_pair", COLOR_PAIRS),
    ):
        if values[name] not in domain:
            raise ValueError(f"observed {name}={values[name]!r} outside {domain!r}")
    return values


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    left, right = _padded_profiles(
        analysis["left"]["profile"], analysis["right"]["profile"]
    )
    return {
        **observe_overrides(grid),
        "left_profile": analysis["left"]["profile"],
        "right_profile": analysis["right"]["profile"],
        "difference_profile": tuple(abs(a - b) for a, b in zip(left, right)),
    }


# ---------------------------------------------------------------------------
# Plausible wrong rules and executable teaching witnesses
# ---------------------------------------------------------------------------


def _with_analysis(grid: Any, fn: Callable[[dict[str, Any]], Grid]) -> Grid | None:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return fn(analysis)


def _canvas_row_alignment(grid: Any) -> Grid | None:
    def solve(analysis: dict[str, Any]) -> Grid:
        left_obj = analysis["left"]
        right_obj = analysis["right"]
        start = min(left_obj["top"], right_obj["top"])
        stop = max(left_obj["bottom"], right_obj["bottom"])
        left_counts = {row: 0 for row in range(start, stop + 1)}
        right_counts = {row: 0 for row in range(start, stop + 1)}
        for row, _ in left_obj["global_cells"]:
            left_counts[row] += 1
        for row, _ in right_obj["global_cells"]:
            right_counts[row] += 1
        return _histogram(
            abs(left_counts[row] - right_counts[row])
            for row in range(start, stop + 1)
        )

    return _with_analysis(grid, solve)


def _bbox_span_profile(grid: Any) -> Grid | None:
    def spans(obj: dict[str, Any]) -> list[int]:
        by_row: dict[int, list[int]] = {}
        for row, col in obj["global_cells"]:
            by_row.setdefault(row, []).append(col)
        return [
            max(by_row[row]) - min(by_row[row]) + 1
            for row in range(obj["top"], obj["bottom"] + 1)
        ]

    def solve(analysis: dict[str, Any]) -> Grid:
        left, right = _padded_profiles(spans(analysis["left"]), spans(analysis["right"]))
        return _histogram(abs(a - b) for a, b in zip(left, right))

    return _with_analysis(grid, solve)


def _left_minus_clamped(grid: Any) -> Grid | None:
    def solve(analysis: dict[str, Any]) -> Grid:
        left, right = _padded_profiles(
            analysis["left"]["profile"], analysis["right"]["profile"]
        )
        return _histogram(max(0, a - b) for a, b in zip(left, right))

    return _with_analysis(grid, solve)


def _right_minus_clamped(grid: Any) -> Grid | None:
    def solve(analysis: dict[str, Any]) -> Grid:
        left, right = _padded_profiles(
            analysis["left"]["profile"], analysis["right"]["profile"]
        )
        return _histogram(max(0, b - a) for a, b in zip(left, right))

    return _with_analysis(grid, solve)


def _truncate_shorter(grid: Any) -> Grid | None:
    def solve(analysis: dict[str, Any]) -> Grid:
        left = analysis["left"]["profile"]
        right = analysis["right"]["profile"]
        return _histogram(abs(a - b) for a, b in zip(left, right))

    return _with_analysis(grid, solve)


def _sum_profiles(grid: Any) -> Grid | None:
    def solve(analysis: dict[str, Any]) -> Grid:
        left, right = _padded_profiles(
            analysis["left"]["profile"], analysis["right"]["profile"]
        )
        return _histogram(a + b for a, b in zip(left, right))

    return _with_analysis(grid, solve)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid | None]] = {
    "canvas_row_alignment": _canvas_row_alignment,
    "bbox_span_profile": _bbox_span_profile,
    "left_minus_clamped": _left_minus_clamped,
    "right_minus_clamped": _right_minus_clamped,
    "truncate_shorter": _truncate_shorter,
    "sum_profiles": _sum_profiles,
}

# This shortcut reproduces every canonical pair because the retained objects
# all share a top row.  The staggered witness below supplies its counterexample.
CANONICAL_SHORTCUTS = {"canvas_row_alignment": _canvas_row_alignment}


def _lawful_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _rival_witness(
    grid: Any, *, structural: Callable[[dict[str, Any]], bool], rivals: tuple[str, ...]
) -> bool:
    analysis = _lawful_analysis(grid)
    if analysis is None or not structural(analysis):
        return False
    authority = rule_mirror(grid)
    return all(SEMANTIC_RIVALS[name](grid) != authority for name in rivals)


def _mixed_signs(analysis: dict[str, Any]) -> bool:
    left, right = _padded_profiles(
        analysis["left"]["profile"], analysis["right"]["profile"]
    )
    return any(a > b for a, b in zip(left, right)) and any(
        a < b for a, b in zip(left, right)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "staggered_alignment": lambda grid: _rival_witness(
        grid,
        structural=lambda analysis: analysis["placement_mode"] == "staggered",
        rivals=("canvas_row_alignment",),
    ),
    "internal_gap_cell_counting": lambda grid: _rival_witness(
        grid,
        structural=lambda analysis: analysis["geometry_mode"] == "gapped",
        rivals=("bbox_span_profile",),
    ),
    "mixed_sign_absolute_value": lambda grid: _rival_witness(
        grid,
        structural=_mixed_signs,
        rivals=("left_minus_clamped", "right_minus_clamped"),
    ),
    "unequal_height_zero_padding": lambda grid: _rival_witness(
        grid,
        structural=lambda analysis: analysis["left"]["height"]
        != analysis["right"]["height"],
        rivals=("truncate_shorter",),
    ),
    "difference_not_sum": lambda grid: _rival_witness(
        grid,
        structural=lambda analysis: True,
        rivals=("sum_profiles",),
    ),
}

WITNESS_RIVALS = {
    "staggered_alignment": ["canvas_row_alignment"],
    "internal_gap_cell_counting": ["bbox_span_profile"],
    "mixed_sign_absolute_value": ["left_minus_clamped", "right_minus_clamped"],
    "unequal_height_zero_padding": ["truncate_shorter"],
    "difference_not_sum": ["sum_profiles"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the row-profile grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(
                f"demo {index} output disagrees with object-local absolute row-profile difference"
            )

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the row-profile grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append(
            "query output disagrees with object-local absolute row-profile difference"
        )
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Task-local malformed inputs for generic defect probes."""
    blank = full_grid(8, 15, 0)

    missing_right = full_grid(8, 15, 0)
    for row in range(8):
        missing_right[row][7] = 5
    missing_right[2][2] = missing_right[3][2] = 2

    identical = generate(932, 1, profile_case="equal_left_dominant")
    analysis = _analyze(identical)
    identical = [list(row) for row in identical]
    for row, col in analysis["right"]["global_cells"]:
        identical[row][col] = 0
    right_left = analysis["divider"] + 2
    right_top = analysis["right"]["top"]
    for dr, dc in analysis["left"]["shape"]:
        identical[right_top + dr][right_left + dc] = analysis["right"]["color"]

    return [
        ("blank_without_divider", blank),
        ("missing_right_object", missing_right),
        ("identical_profiles", identical),
    ]
