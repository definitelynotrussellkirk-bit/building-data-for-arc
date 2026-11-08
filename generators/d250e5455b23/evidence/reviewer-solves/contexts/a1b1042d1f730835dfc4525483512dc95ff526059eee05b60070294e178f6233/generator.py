"""Source-bound generator for ARC task d250e5455b23.

Every input contains two or three isolated, same-color axis-aligned dominoes.
The canonical rule grows each horizontal domino downward and each vertical
domino rightward to complete the 2x2 square for which the domino is the top or
left edge.  This module samples inputs only; the Racket authority owns labels.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "d250e5455b23"
TASK_ID = GENERATOR_ID
RULE_HASH = "9af05fcaf1f5"
VERSION = "2.0.0"
SUMMARY = (
    "Two or three isolated colored dominoes complete the 2x2 square extending "
    "downward from a horizontal domino or rightward from a vertical domino."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and every nonzero component is a two-cell same-color domino",
    "each domino is the top or left edge of an in-bounds 2x2 growth square",
    "domino colors are distinct and growth squares have a one-cell moat",
    "two to three dominoes are present; horizontal, vertical, and mixed lessons are supported",
]

ORIENTATION_MODES = ("horizontal", "vertical", "mixed")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-weighted 7..9",
        "valid": "7..9",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-weighted 7..9",
        "valid": "7..9",
    },
    "domino_count": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-weighted 2..3",
        "valid": "2..3",
    },
    "orientation_mode": {
        "type": "str",
        "default": "four-step teaching cycle: horizontal|vertical|mixed|mixed",
        "valid": "|".join(ORIENTATION_MODES),
    },
}

# Every advertised Cartesian combination is constructively realizable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# (height, width, domino count).  With one distinct color per domino these
# reproduce the four canonical (height, width, palette-size) profiles.
_CANONICAL_PROFILES = ((7, 7, 2), (8, 8, 3), (8, 9, 3), (9, 9, 3))
_ORIENTATION_SCHEDULE = ("horizontal", "vertical", "mixed", "mixed")

_BAND_OPTIONS = {
    "easy": {
        "grid_h": (7, 7, 7, 8, 8, 9),
        "grid_w": (7, 7, 7, 8, 8, 9),
        "domino_count": (2, 2, 2, 3),
    },
    "medium": {
        "grid_h": (7, 8, 8, 9),
        "grid_w": (7, 8, 8, 9),
        "domino_count": (2, 2, 3, 3),
    },
    "hard": {
        "grid_h": (7, 8, 8, 9, 9, 9),
        "grid_w": (7, 8, 8, 9, 9, 9),
        "domino_count": (2, 3, 3, 3),
    },
}


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "domino_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    value = overrides.get("orientation_mode")
    if value is not None and type(value) is not str:
        raise ValueError(
            f"orientation_mode must be a string, not {type(value).__name__}"
        )


def _growth_squares_separated(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Whether two 2x2 squares have at least one blank row or column between."""
    return abs(a[0] - b[0]) >= 3 or abs(a[1] - b[1]) >= 3


@lru_cache(maxsize=27)
def _layouts(height: int, width: int, count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    anchors = tuple(
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
    )
    layouts = tuple(
        layout
        for layout in combinations(anchors, count)
        if all(_growth_squares_separated(a, b) for a, b in combinations(layout, 2))
    )
    if not layouts:
        raise ValueError(
            f"no constructive {count}-domino layout for {height}x{width}"
        )
    return layouts


def _draw_dimensions_and_count(ctx, sample_index: int, overrides: dict):
    exact_names = ("grid_h", "grid_w", "domino_count")
    has_exact_override = any(overrides.get(name) is not None for name in exact_names)

    # Four of every five default starts replay only a canonical joint profile,
    # not a canonical grid.  Positions, orientations, and colors remain fresh.
    profile_slot = sample_index % 5
    if not has_exact_override and profile_slot < len(_CANONICAL_PROFILES):
        height, width, count = _CANONICAL_PROFILES[profile_slot]
        return (
            ctx.draw_choice("grid_h", (height,)),
            ctx.draw_choice("grid_w", (width,)),
            ctx.draw_choice("domino_count", (count,)),
        )

    band = ctx.difficulty or "medium"
    options = _BAND_OPTIONS[band]
    return (
        ctx.draw_choice("grid_h", options["grid_h"]),
        ctx.draw_choice("grid_w", options["grid_w"]),
        ctx.draw_choice("domino_count", options["domino_count"]),
    )


def _draw_orientation_mode(ctx, sample_index: int, overrides: dict) -> str:
    if overrides.get("orientation_mode") is not None:
        return ctx.draw_choice("orientation_mode", ORIENTATION_MODES)
    scheduled = _ORIENTATION_SCHEDULE[sample_index % len(_ORIENTATION_SCHEDULE)]
    return ctx.draw_choice("orientation_mode", (scheduled,))


def _orientations(mode: str, count: int, rng) -> list[str]:
    if mode == "horizontal":
        return ["horizontal"] * count
    if mode == "vertical":
        return ["vertical"] * count
    if mode != "mixed":
        raise ValueError(f"unknown orientation mode: {mode!r}")
    horizontal_count = 1 if count == 2 else rng.choice((1, 2))
    result = ["horizontal"] * horizontal_count
    result.extend(["vertical"] * (count - horizontal_count))
    rng.shuffle(result)
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, count = _draw_dimensions_and_count(ctx, sample_index, overrides)
    mode = _draw_orientation_mode(ctx, sample_index, overrides)

    layout = ctx.draw_rng("layout").choice(_layouts(height, width, count))
    orientations = _orientations(mode, count, ctx.draw_rng("orientations"))
    colors = ctx.draw_distinct_colors("colors", n=count, exclude={0})

    grid = full_grid(height, width, 0)
    for (row, col), orientation, color in zip(layout, orientations, colors):
        grid[row][col] = color
        if orientation == "horizontal":
            grid[row][col + 1] = color
        else:
            grid[row + 1][col] = color
    return grid


def _validated_components(grid) -> list[dict]:
    return components(grid, same_color=True, connectivity=4)


def _component_orientation(comp: dict) -> str | None:
    cells = comp["cells"]
    if len(cells) != 2:
        return None
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(rows) == 1 and len(cols) == 2:
        return "horizontal"
    if len(rows) == 2 and len(cols) == 1:
        return "vertical"
    return None


def _growth_anchor(comp: dict) -> tuple[int, int] | None:
    orientation = _component_orientation(comp)
    if orientation is None:
        return None
    row1, col1, _row2, _col2 = comp["bbox"]
    return row1, col1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    errors: list[str] = []
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unsupported difficulty: {difficulty!r}")
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return errors + ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return errors + ["ragged grid"]
    height = len(grid)
    if not (7 <= height <= 9 and 7 <= width <= 9):
        errors.append(f"grid {height}x{width} outside declared 7..9 envelope")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid colors must be integer values in 0..9")
        return errors

    comps = _validated_components(grid)
    if not 2 <= len(comps) <= 3:
        errors.append(f"expected 2-3 domino components, got {len(comps)}")

    colors = [comp["color"] for comp in comps]
    if len(colors) != len(set(colors)):
        errors.append("domino colors must be distinct")

    anchors: list[tuple[int, int]] = []
    for comp in comps:
        orientation = _component_orientation(comp)
        if orientation is None:
            errors.append(
                f"component of color {comp['color']} is not an axis-aligned domino"
            )
            continue
        row, col = _growth_anchor(comp)  # type: ignore[misc]
        if row + 1 >= height or col + 1 >= width:
            errors.append(
                f"domino of color {comp['color']} has out-of-bounds 2x2 growth square"
            )
            continue
        anchors.append((row, col))

    for first, second in combinations(anchors, 2):
        if not _growth_squares_separated(first, second):
            errors.append(
                f"growth squares at {first} and {second} lack a one-cell moat"
            )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors}")
    comps = _validated_components(grid)
    orientations = [_component_orientation(comp) for comp in comps]
    if all(value == "horizontal" for value in orientations):
        mode = "horizontal"
    elif all(value == "vertical" for value in orientations):
        mode = "vertical"
    else:
        mode = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "domino_count": len(comps),
        "orientation_mode": mode,
    }


def strict_canonical_like(grid):
    """Accept exactly the reviewed generator/canonical structural manifold."""
    return self_check(grid)


def _apply_growth(
    grid,
    *,
    allow: Callable[[str], bool] = lambda _orientation: True,
    fixed_color: int | None = None,
    limit: int | None = None,
):
    output = [list(row) for row in grid]
    comps = sorted(_validated_components(grid), key=lambda comp: comp["bbox"])
    grown = 0
    for comp in comps:
        orientation = _component_orientation(comp)
        if orientation is None or not allow(orientation):
            continue
        if limit is not None and grown >= limit:
            continue
        row, col = _growth_anchor(comp)  # type: ignore[misc]
        color = comp["color"] if fixed_color is None else fixed_color
        for rr in (row, row + 1):
            for cc in (col, col + 1):
                output[rr][cc] = color
        grown += 1
    return output


def rule_mirror(grid):
    """Independent Python mirror used only for tests and semantic rivals."""
    return _apply_growth(grid)


def _identity(grid):
    return [list(row) for row in grid]


def _horizontal_only(grid):
    return _apply_growth(grid, allow=lambda orientation: orientation == "horizontal")


def _vertical_only(grid):
    return _apply_growth(grid, allow=lambda orientation: orientation == "vertical")


def _fixed_color_8(grid):
    return _apply_growth(grid, fixed_color=8)


def _first_domino_only(grid):
    return _apply_growth(grid, limit=1)


SEMANTIC_RIVALS = {
    "identity": _identity,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "fixed_color_8": _fixed_color_8,
    "first_domino_only": _first_domino_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _has_orientation(grid, wanted: str) -> bool:
    return any(
        _component_orientation(comp) == wanted
        for comp in _validated_components(grid)
    )


SEMANTIC_WITNESSES = {
    "horizontal_domino": lambda grid: _has_orientation(grid, "horizontal"),
    "vertical_domino": lambda grid: _has_orientation(grid, "vertical"),
    "multiple_dominos": lambda grid: len(_validated_components(grid)) >= 2,
    "source_color_preserved": lambda grid: any(
        comp["color"] != 8 for comp in _validated_components(grid)
    ),
}
BRANCH_WITNESSES = ("horizontal_domino", "vertical_domino")
WITNESS_RIVALS = {
    "horizontal_domino": ("identity", "vertical_only"),
    "vertical_domino": ("identity", "horizontal_only"),
    "multiple_dominos": ("first_domino_only",),
    "source_color_preserved": ("fixed_color_8",),
}


def lesson_identifiable(demos, query):
    """Reject lessons where a declared wrong rule fits demos but changes query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # fail closed with an actionable reason
            reasons.append(f"rival {name} failed: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"declared rival {name} fits every demonstration but changes the query"
            )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _ORIENTATION_SCHEDULE[sample_index % len(_ORIENTATION_SCHEDULE)]


SCHEDULE_PROFILES = ORIENTATION_MODES
