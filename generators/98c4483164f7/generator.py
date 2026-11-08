"""Semantic generator for ARC task 98c4483164f7.

A single nonzero 2x2 motif sits on a literal color-0 background.  Color 2 is a
set of direction markers: each red motif cell activates the diagonal quadrant
that contains it.  The remaining motif color is the payload color.  The rule
recolors the complete motif to that payload and projects a two-cell-wide
family of diagonal rays from *all four motif cells* in every active direction.

The default four-step curriculum deliberately teaches the difficult branches:
one marker, an opposite pair, three markers, and an adjacent pair.  Every
third sample independently uses the official 9x9 geometry, while the four-step
marker schedule continues to cover all teaching branches.
Only exact, observable controls are advertised; retired boilerplate axes are
rejected as unknown instead of being silently ignored.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from numbers import Real
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "98c4483164f7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "18ad2f5cfd8b"

SUMMARY = (
    "A 2x2 motif uses red (2) cells as diagonal direction markers; recolor the "
    "motif to its other color and launch that color from all four motif cells "
    "toward every marked quadrant."
)

INVARIANTS = [
    "the background is literal color 0",
    "exactly four nonzero cells form one filled 2x2 motif",
    "the motif contains one to three red (2) direction markers",
    "all remaining motif cells share one nonzero, non-red payload color",
    "generated motifs retain two background cells of clearance on every side",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "9 every third sample; otherwise difficulty-scaled",
        "valid": "6..30",
        "doc": "Exact returned grid height; every declared value is legal in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "9 every third sample; otherwise difficulty-scaled",
        "valid": "6..30",
        "doc": "Exact returned grid width; every declared value is legal in every band.",
    },
    "n_red_cells": {
        "type": "int",
        "default": "four-step lesson cycle 1,2,3,2",
        "valid": "1..3",
        "doc": "Exact number of red direction markers in the 2x2 motif.",
    },
    "main_color": {
        "type": "color",
        "default": "keyed draw from all nonzero colors except red (2)",
        "valid": "1|3|4|5|6|7|8|9",
        "doc": "Exact payload/ray color; 0 and the marker color 2 are illegal.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_AXIS_BOUNDS = {
    "grid_h": (6, 30),
    "grid_w": (6, 30),
    "n_red_cells": (1, 3),
}
_MAIN_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)

# The first profile anchors the official geometry.  The remaining profiles are
# named for the red-mask relation they teach, not just for superficial shape.
SCHEDULE_PROFILES = (
    "single_marker",
    "opposite_pair",
    "triple",
    "adjacent_pair",
)
_PROFILE_RED_COUNTS = {
    "single_marker": 1,
    "opposite_pair": 2,
    "triple": 3,
    "adjacent_pair": 2,
}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

_CELLS = ((0, 0), (0, 1), (1, 0), (1, 1))
_ALL_DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_OPPOSITE_MASKS = (
    frozenset(((0, 0), (1, 1))),
    frozenset(((0, 1), (1, 0))),
)
_ADJACENT_MASKS = (
    frozenset(((0, 0), (0, 1))),
    frozenset(((1, 0), (1, 1))),
    frozenset(((0, 0), (1, 0))),
    frozenset(((0, 1), (1, 1))),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared four-step curriculum branch for one draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty in (None, "easy", "medium", "hard"):
        return
    if isinstance(difficulty, Real) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if 0.0 <= value <= 1.0:
            return
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "n_red_cells"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool), got {value!r}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    if "main_color" in overrides and overrides["main_color"] is not None:
        value = overrides["main_color"]
        if type(value) is not int:
            raise TypeError(
                f"main_color override must be an integer ARC color (not bool), got {value!r}"
            )
        if value not in _MAIN_COLORS:
            raise ValueError(
                f"main_color override {value!r} must be one of {_MAIN_COLORS}"
            )


def _broad_bounds(axis: str, difficulty: Any) -> tuple[int, int]:
    if isinstance(difficulty, Real) and not isinstance(difficulty, bool):
        return _AXIS_BOUNDS[axis]
    band = "medium" if difficulty is None else difficulty
    table = {
        "grid_h": {"easy": (6, 12), "medium": (8, 20), "hard": (14, 30)},
        "grid_w": {"easy": (6, 12), "medium": (8, 20), "hard": (14, 30)},
    }
    return table[axis][band]


def _draw_dimension(
    ctx,
    overrides: dict[str, Any],
    axis: str,
    *,
    preferred: int | None,
) -> int:
    lo, hi = _AXIS_BOUNDS[axis]
    if overrides.get(axis) is not None:
        # Exact overrides use the complete advertised domain in every band.
        return ctx.draw_int_strict(axis, lo, hi)
    if preferred is not None:
        # Fixed bounds still record honest keyed provenance for the axis.
        return ctx.draw_int_strict(axis, preferred, preferred)
    broad_lo, broad_hi = _broad_bounds(axis, ctx.difficulty)
    return ctx.draw_int_diff(axis, broad_lo, broad_hi)


def _draw_red_count(
    ctx,
    overrides: dict[str, Any],
    profile: str,
) -> int:
    lo, hi = _AXIS_BOUNDS["n_red_cells"]
    if overrides.get("n_red_cells") is not None:
        return ctx.draw_int_strict("n_red_cells", lo, hi)
    preferred = _PROFILE_RED_COUNTS[profile]
    return ctx.draw_int_strict("n_red_cells", preferred, preferred)


def _mask_options(profile: str, n_red: int) -> tuple[frozenset[tuple[int, int]], ...]:
    if profile == "opposite_pair" and n_red == 2:
        return _OPPOSITE_MASKS
    if profile == "adjacent_pair" and n_red == 2:
        return _ADJACENT_MASKS
    return tuple(frozenset(mask) for mask in combinations(_CELLS, n_red))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, lawful task input.

    Overrides are exact-or-loud.  Difficulty affects only default broad draws;
    it never narrows the legal override domain.
    """
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
    profile = schedule_profile(seed, sample_index, difficulty)
    # Keep canonical geometry on an independent period.  The pinned census
    # aliases slightly against period four (14/60); period three clears the
    # required 25% floor without disturbing the four-step marker lesson.
    preferred_dimension = 9 if int(sample_index) % 3 == 0 else None
    height = _draw_dimension(
        ctx, overrides, "grid_h", preferred=preferred_dimension
    )
    width = _draw_dimension(
        ctx, overrides, "grid_w", preferred=preferred_dimension
    )
    n_red = _draw_red_count(ctx, overrides, profile)
    main_color = ctx.draw_color("main_color", exclude=(0, 2))

    placement_rng = ctx.draw_rng("motif_placement")
    # Two cells of clearance make every active direction and long-ray branch
    # directly observable, including on the smallest 6x6 generated canvas.
    top = placement_rng.randint(2, height - 4)
    left = placement_rng.randint(2, width - 4)

    mask_rng = ctx.draw_rng("red_mask")
    red_mask = mask_rng.choice(_mask_options(profile, n_red))

    grid = full_grid(height, width, 0)
    for dr, dc in _CELLS:
        grid[top + dr][left + dc] = 2 if (dr, dc) in red_mask else main_color
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= 9:
                return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 2 <= height <= 30:
        errors.append(f"grid height must be in 2..30, found {height}")
    if not 2 <= width <= 30:
        errors.append(f"grid width must be in 2..30, found {width}")

    nonzero = [
        (row, column, grid[row][column])
        for row in range(height)
        for column in range(width)
        if grid[row][column] != 0
    ]
    if len(nonzero) != 4:
        errors.append(f"expected exactly four nonzero motif cells, found {len(nonzero)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "nonzero": nonzero,
        }

    rows = [row for row, _, _ in nonzero]
    columns = [column for _, column, _ in nonzero]
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)
    if bottom - top != 1 or right - left != 1:
        errors.append("the four nonzero cells must form one filled 2x2 motif")

    expected_cells = {
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    }
    actual_cells = {(row, column) for row, column, _ in nonzero}
    if actual_cells != expected_cells:
        errors.append("the motif bounding box must contain all four nonzero cells")

    red_cells = sorted(
        (row, column) for row, column, value in nonzero if value == 2
    )
    if not 1 <= len(red_cells) <= 3:
        errors.append(
            f"motif must contain one to three red direction markers, found {len(red_cells)}"
        )

    main_colors = {value for _, _, value in nonzero if value != 2}
    if len(main_colors) != 1:
        errors.append(
            "all non-red motif cells must share exactly one payload color; "
            f"found {sorted(main_colors)}"
        )
    main_color = next(iter(main_colors)) if len(main_colors) == 1 else None
    if main_color in (None, 0, 2):
        if main_color is not None:
            errors.append("payload color must be nonzero and different from red (2)")

    block_cells = sorted(actual_cells)
    active_directions = sorted(
        {
            (-1 if row == top else 1, -1 if column == left else 1)
            for row, column in red_cells
        }
    )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "block_cells": block_cells,
        "red_cells": red_cells,
        "red_count": len(red_cells),
        "main_color": main_color,
        "active_directions": active_directions,
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the canonical input grammar; malformed values never raise."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept lawful inputs on the official 9x9 shape/palette profile."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if (analysis["height"], analysis["width"]) != (9, 9):
        return [
            "strict canonical profile requires a 9x9 grid, found "
            f"{analysis['height']}x{analysis['width']}"
        ]
    return []


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every advertised exact axis from a returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_red_cells": analysis["red_count"],
        "main_color": analysis["main_color"],
    }


def _valid_analysis(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    return analysis


def _render(
    grid: Any,
    *,
    directions: Sequence[tuple[int, int]] | None = None,
    origins: Sequence[tuple[int, int]] | None = None,
    max_steps: int | None = None,
    paint_color: int | None = None,
) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    output = deepcopy([list(row) for row in grid])
    color = analysis["main_color"] if paint_color is None else paint_color
    ray_directions = (
        tuple(analysis["active_directions"])
        if directions is None
        else tuple(directions)
    )
    ray_origins = (
        tuple(analysis["block_cells"]) if origins is None else tuple(origins)
    )

    for row, column in analysis["block_cells"]:
        output[row][column] = color

    limit = max(analysis["height"], analysis["width"]) - 1
    if max_steps is not None:
        limit = min(limit, max_steps)
    for row, column in ray_origins:
        for dr, dc in ray_directions:
            for step in range(1, limit + 1):
                nr, nc = row + step * dr, column + step * dc
                if not (0 <= nr < analysis["height"] and 0 <= nc < analysis["width"]):
                    break
                output[nr][nc] = color
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror; the selected canonical Racket rule is authority."""
    return _render(grid)


# Alias used by several task-local test conventions.
oracle_output = rule_mirror


def _rival_no_rays(grid: Any) -> list[list[int]]:
    return _render(grid, directions=())


def _rival_all_directions(grid: Any) -> list[list[int]]:
    return _render(grid, directions=_ALL_DIRECTIONS)


def _rival_red_origins_only(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    return _render(grid, origins=analysis["red_cells"])


def _rival_opposite_directions(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    opposite = tuple((-dr, -dc) for dr, dc in analysis["active_directions"])
    return _render(grid, directions=opposite)


def _rival_first_marker_only(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    row, column = analysis["red_cells"][0]
    direction = (
        -1 if row == analysis["top"] else 1,
        -1 if column == analysis["left"] else 1,
    )
    return _render(grid, directions=(direction,))


def _rival_one_step_rays(grid: Any) -> list[list[int]]:
    return _render(grid, max_steps=1)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "no_rays": _rival_no_rays,
    "all_directions": _rival_all_directions,
    "red_origins_only": _rival_red_origins_only,
    "opposite_directions": _rival_opposite_directions,
    "first_marker_only": _rival_first_marker_only,
    "one_step_rays": _rival_one_step_rays,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def _valid_and_disagrees(
    grid: Any,
    rival: Callable[[Any], list[list[int]]],
) -> bool:
    return self_check(grid) == [] and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "projection_beyond_motif": lambda grid: _valid_and_disagrees(grid, _rival_no_rays),
    "inactive_quadrants_stay_empty": lambda grid: _valid_and_disagrees(
        grid, _rival_all_directions
    ),
    "all_four_motif_cells_launch": lambda grid: _valid_and_disagrees(
        grid, _rival_red_origins_only
    ),
    "marker_quadrants_not_opposites": lambda grid: _valid_and_disagrees(
        grid, _rival_opposite_directions
    ),
    "multiple_markers_form_a_union": lambda grid: (
        not self_check(grid)
        and _analysis(grid)["red_count"] > 1
        and _rival_first_marker_only(grid) != rule_mirror(grid)
    ),
    "rays_continue_to_the_boundary": lambda grid: _valid_and_disagrees(
        grid, _rival_one_step_rays
    ),
}
WITNESS_RIVALS = {
    "projection_beyond_motif": ["no_rays"],
    "inactive_quadrants_stay_empty": ["all_directions"],
    "all_four_motif_cells_launch": ["red_origins_only"],
    "marker_quadrants_not_opposites": ["opposite_directions"],
    "multiple_markers_form_a_union": ["first_marker_only"],
    "rays_continue_to_the_boundary": ["one_step_rays"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson in which a named plausible wrong rule fits all demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} input is outside the 2x2 marker grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{label} output disagrees with the diagonal-ray rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor survives every demonstration: {name}")
    return reasons
