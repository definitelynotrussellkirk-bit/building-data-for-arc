"""Generator for ARC task f0afb749 / content hash 827c34fc8e04.

The authoritative rule doubles every input cell to a 2x2 block, then paints
color 1 on every still-background cell of each marked cell's full NW-SE
output diagonal.  The lesson schedule deliberately cycles through a northwest anchor, a southeast anchor, and two redundant
off-axis multi-anchor scenes so any three of four consecutive demonstrations refute one-sided and fixed-diagonal shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "827c34fc8e04"
TASK_ID = "827c34fc8e04"
VERSION = "3.1.0"
RULE_HASH = "ec4ecd14d47d"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Create a 2..6 by 2..6 zero-background grid with 1..3 colored marker "
    "cells, using ARC colors 2..9 and never input color 1. The output doubles "
    "every input cell to a 2x2 block. For each marker at (r,c), paint color 1 "
    "on every remaining background cell of the complete NW-SE output diagonal "
    "R-C = 2(r-c); preserve all doubled non-background blocks. Consecutive "
    "lesson samples rotate through northwest-only extension, southeast-only "
    "extension, and two off-main-diagonal multi-anchor cases so every three-of-four "
    "window exposes direction, anchor dependence, and use of every marker."
)

INVARIANTS = [
    "rectangular 2..6 by 2..6 input grid",
    "exactly 1..3 non-background marker cells",
    "marker colors are 2..9; color 1 is reserved for output trails",
    "at least one marker diagonal has visible trail cells outside its 2x2 block",
    "two or more markers never collapse into one contiguous horizontal bar",
]

# All declared axes are exact and recoverable from the returned input grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed keyed draw",
        "valid": "2..6",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed keyed draw",
        "valid": "2..6",
    },
    "n_marks": {
        "type": "int",
        "default": "keyed draw; profile 2 defaults to 2..3",
        "valid": "1..3",
    },
    "palette_size": {
        "type": "int",
        "default": "keyed draw not exceeding n_marks",
        "valid": "1..3",
    },
}

# Every requested palette color must occur, so palette_size cannot exceed the
# requested number of markers. These are the complete impossible tuples over
# the finite domains above.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_marks": 1, "palette_size": 2},
    {"n_marks": 1, "palette_size": 3},
    {"n_marks": 2, "palette_size": 3},
]


_ALLOWED_OVERRIDES = set(AXES)


def _exact_int(value: Any, name: str, lo: int, hi: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if value < lo or hi is not None and value > hi:
        bound = f"{lo}..{hi}" if hi is not None else f">={lo}"
        raise ValueError(f"{name} must be in {bound}")
    return value


def _validated_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _exact_int(seed, "seed", 0)
    _exact_int(sample_index, "sample_index", 0)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", 2, 6),
        ("grid_w", 2, 6),
        ("n_marks", 1, 3),
        ("palette_size", 1, 3),
    ):
        if name in overrides and overrides[name] is not None:
            _exact_int(overrides[name], name, lo, hi)

SCHEDULE_PROFILES = (
    "northwest_anchor",
    "southeast_anchor",
    "off_axis_multi_anchor_a",
    "off_axis_multi_anchor_b",
)


def _is_off_axis_profile(profile: str) -> bool:
    return profile.startswith("off_axis_multi_anchor")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic teaching profile for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _marks(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _trail_cells_for_mark(
    h: int, w: int, sr: int, sc: int
) -> list[tuple[int, int]]:
    """Blank output cells on one marker's full doubled NW-SE diagonal."""
    difference = 2 * (sr - sc)
    block = {
        (r, c)
        for r in (2 * sr, 2 * sr + 1)
        for c in (2 * sc, 2 * sc + 1)
    }
    return [
        (r, c)
        for r in range(2 * h)
        for c in range(2 * w)
        if r - c == difference and (r, c) not in block
    ]


def _visible_sides(
    h: int, w: int, sr: int, sc: int
) -> tuple[bool, bool]:
    trails = _trail_cells_for_mark(h, w, sr, sc)
    northwest = any(r < 2 * sr and c < 2 * sc for r, c in trails)
    southeast = any(r > 2 * sr + 1 and c > 2 * sc + 1 for r, c in trails)
    return northwest, southeast


def _positions_form_horizontal_bar(positions: list[tuple[int, int]]) -> bool:
    if len(positions) < 2:
        return False
    rows = {r for r, _c in positions}
    columns = sorted(c for _r, c in positions)
    return len(rows) == 1 and columns == list(range(columns[0], columns[0] + len(columns)))


def _ordered_positions(
    h: int,
    w: int,
    n_marks: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    """Choose exact marker count while making the scheduled cue observable."""
    cells = [(r, c) for r in range(h) for c in range(w)]

    if profile == "northwest_anchor":
        primary = (0, 0)  # its visible trail extends southeast
    elif profile == "southeast_anchor":
        primary = (h - 1, w - 1)  # its visible trail extends northwest
    else:
        # Prefer an off-main-diagonal anchor with trail on both sides.  The
        # default dimension schedule avoids 2x2 for this profile, so at least
        # a one-sided off-axis choice always exists.
        off_axis = [
            cell
            for cell in cells
            if cell[0] != cell[1]
            and _trail_cells_for_mark(h, w, cell[0], cell[1])
        ]
        both_sides = [
            cell
            for cell in off_axis
            if all(_visible_sides(h, w, cell[0], cell[1]))
        ]
        choices = both_sides or off_axis
        primary = choices[rng.randrange(len(choices))] if choices else (0, 0)

    selected = [primary]
    remaining = [cell for cell in cells if cell != primary]
    rng.shuffle(remaining)

    if n_marks >= 2:
        primary_diag = primary[0] - primary[1]
        if _is_off_axis_profile(profile):
            # A second visible, different diagonal proves that every marker,
            # not just a distinguished first marker, contributes a trail.
            preferred = [
                cell
                for cell in remaining
                if cell[0] - cell[1] != primary_diag
                and _trail_cells_for_mark(h, w, cell[0], cell[1])
            ]
        elif (rng.randrange(2) == 0):
            # Sometimes repeat a diagonal to cover the union/idempotence branch.
            preferred = [
                cell
                for cell in remaining
                if cell[0] - cell[1] == primary_diag
            ]
        else:
            preferred = [
                cell
                for cell in remaining
                if cell[0] - cell[1] != primary_diag
            ]
        second = preferred[0] if preferred else remaining[0]
        selected.append(second)
        remaining.remove(second)

    while len(selected) < n_marks:
        # Favor a new diagonal, then fall back to any remaining cell.
        used_diagonals = {r - c for r, c in selected}
        preferred = [
            cell for cell in remaining if cell[0] - cell[1] not in used_diagonals
        ]
        cell = preferred[0] if preferred else remaining[0]
        selected.append(cell)
        remaining.remove(cell)

    # A short same-row bar is a recurring generic impostor, not a canonical
    # marker arrangement. If random placement formed one, replace the final
    # marker while preserving the scheduled multi-anchor cue.
    if _positions_form_horizontal_bar(selected):
        for preserve_profile in (True, False):
            for replacement in remaining:
                candidate = selected[:-1] + [replacement]
                if _positions_form_horizontal_bar(candidate):
                    continue
                if preserve_profile and _is_off_axis_profile(profile):
                    primary_diag = candidate[0][0] - candidate[0][1]
                    if not any(
                        r - c != primary_diag
                        and _trail_cells_for_mark(h, w, r, c)
                        for r, c in candidate[1:]
                    ):
                        continue
                selected = candidate
                break
            if not _positions_form_horizontal_bar(selected):
                break
    return selected


def _draw_dimensions(ctx, profile: str, overrides: dict[str, Any]) -> tuple[int, int]:
    """Draw exact dimensions; default off-axis profiles are robust 4..6 scenes."""
    h_explicit = "grid_h" in overrides and overrides["grid_h"] is not None
    w_explicit = "grid_w" in overrides and overrides["grid_w"] is not None

    if h_explicit:
        h = ctx.draw_int("grid_h", 2, 6)
    elif _is_off_axis_profile(profile):
        h = ctx.draw_int_diff("grid_h", 4, 6)
    else:
        h = ctx.draw_int_diff("grid_h", 2, 6)

    if w_explicit:
        w = ctx.draw_int("grid_w", 2, 6)
    elif _is_off_axis_profile(profile):
        w = ctx.draw_int_diff("grid_w", 4, 6)
    else:
        w = ctx.draw_int_diff("grid_w", 2, 6)
    return h, w


def _draw_counts(ctx, profile: str, overrides: dict[str, Any]) -> tuple[int, int]:
    """Draw exact, compatible n_marks and palette_size values."""
    n_explicit = "n_marks" in overrides and overrides["n_marks"] is not None
    p_explicit = "palette_size" in overrides and overrides["palette_size"] is not None

    if n_explicit and p_explicit:
        n_marks = ctx.draw_int("n_marks", 1, 3)
        palette_size = ctx.draw_int("palette_size", 1, 3)
        if palette_size > n_marks:
            raise ValueError(
                "incompatible overrides: palette_size cannot exceed n_marks"
            )
        return n_marks, palette_size

    if n_explicit:
        n_marks = ctx.draw_int("n_marks", 1, 3)
        palette_size = ctx.draw_int("palette_size", 1, n_marks)
        return n_marks, palette_size

    if p_explicit:
        palette_size = ctx.draw_int("palette_size", 1, 3)
        minimum = max(palette_size, 2 if _is_off_axis_profile(profile) else 1)
        n_marks = ctx.draw_int_diff("n_marks", minimum, 3)
        return n_marks, palette_size

    minimum = 2 if _is_off_axis_profile(profile) else 1
    n_marks = ctx.draw_int_diff("n_marks", minimum, 3)
    palette_size = ctx.draw_int("palette_size", 1, n_marks)
    return n_marks, palette_size


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validated_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    h, w = _draw_dimensions(ctx, profile, overrides)
    n_marks, palette_size = _draw_counts(ctx, profile, overrides)

    placement_rng = ctx.draw_rng("placement")
    positions = _ordered_positions(h, w, n_marks, profile, placement_rng)

    color_rng = ctx.draw_rng("palette")
    palette = list(range(2, 10))
    color_rng.shuffle(palette)
    palette = palette[:palette_size]

    grid = full_grid(h, w, 0)
    for index, (r, c) in enumerate(positions):
        # The first palette_size markers realize every requested color exactly.
        color = palette[index] if index < palette_size else color_rng.choice(palette)
        grid[r][c] = color
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from the returned input grid."""
    marks = _marks(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_marks": len(marks),
        "palette_size": len({value for _r, _c, value in marks}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding inputs, not merely ordinary draws."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be non-empty and rectangular"]

    errors: list[str] = []
    h, w = len(grid), width
    if not (2 <= h <= 6 and 2 <= w <= 6):
        errors.append(f"expected dimensions 2..6 by 2..6, got {h}x{w}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    marks = _marks(grid)
    if any(value == 1 for _r, _c, value in marks):
        errors.append("input color 1 is reserved for output trails")
    if not (1 <= len(marks) <= 3):
        errors.append(f"expected 1..3 marker cells, got {len(marks)}")
    if len({value for _r, _c, value in marks}) > len(marks):
        errors.append("marker palette cannot exceed marker count")
    if marks and not any(
        _trail_cells_for_mark(h, w, r, c) for r, c, _value in marks
    ):
        errors.append("all marker diagonals are hidden inside their 2x2 blocks")
    if _positions_form_horizontal_bar([(r, c) for r, c, _value in marks]):
        errors.append("markers may not form one contiguous horizontal bar")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This generator is intentionally pinned to the canonical input grammar."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror; the Racket rule remains the output authority."""
    h, w = len(grid), len(grid[0])
    output = full_grid(2 * h, 2 * w, 0)
    marks = _marks(grid)
    for r in range(2 * h):
        for c in range(2 * w):
            source = grid[r // 2][c // 2]
            if source != 0:
                output[r][c] = source
            elif any(r - c == 2 * (sr - sc) for sr, sc, _value in marks):
                output[r][c] = 1
    return output


def _scale_only(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    return [
        [grid[r // 2][c // 2] for c in range(2 * w)]
        for r in range(2 * h)
    ]


def _one_sided(grid: list[list[int]], *, northwest: bool) -> list[list[int]]:
    output = _scale_only(grid)
    h, w = len(grid), len(grid[0])
    for sr, sc, _value in _marks(grid):
        for r, c in _trail_cells_for_mark(h, w, sr, sc):
            is_northwest = r < 2 * sr and c < 2 * sc
            is_southeast = r > 2 * sr + 1 and c > 2 * sc + 1
            if (northwest and is_northwest) or (not northwest and is_southeast):
                output[r][c] = 1
    return output


def _northwest_only(grid: list[list[int]]) -> list[list[int]]:
    return _one_sided(grid, northwest=True)


def _southeast_only(grid: list[list[int]]) -> list[list[int]]:
    return _one_sided(grid, northwest=False)


def _main_diagonal_only(grid: list[list[int]]) -> list[list[int]]:
    output = _scale_only(grid)
    for index in range(min(len(output), len(output[0]))):
        if output[index][index] == 0:
            output[index][index] = 1
    return output


def _first_anchor_only(grid: list[list[int]]) -> list[list[int]]:
    output = _scale_only(grid)
    marks = _marks(grid)
    if not marks:
        return output
    h, w = len(grid), len(grid[0])
    sr, sc, _value = marks[0]
    for r, c in _trail_cells_for_mark(h, w, sr, sc):
        if output[r][c] == 0:
            output[r][c] = 1
    return output


def _marker_colored_trails(grid: list[list[int]]) -> list[list[int]]:
    output = _scale_only(grid)
    h, w = len(grid), len(grid[0])
    for sr, sc, value in _marks(grid):
        for r, c in _trail_cells_for_mark(h, w, sr, sc):
            if output[r][c] == 0:
                output[r][c] = value
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "scale_only": _scale_only,
    "northwest_only": _northwest_only,
    "southeast_only": _southeast_only,
    "main_diagonal_only": _main_diagonal_only,
    "first_anchor_only": _first_anchor_only,
    "marker_colored_trails": _marker_colored_trails,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# These are intentionally partial rivals used to test lesson identifiability,
# not alternate implementations of the canonical rule.
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def _has_visible_trail(grid) -> bool:
    return any(value == 1 for row in rule_mirror(grid) for value in row)


def _has_northwest_extension(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(_visible_sides(h, w, r, c)[0] for r, c, _value in _marks(grid))


def _has_southeast_extension(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(_visible_sides(h, w, r, c)[1] for r, c, _value in _marks(grid))


def _has_off_main_visible_trail(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(
        r != c and bool(_trail_cells_for_mark(h, w, r, c))
        for r, c, _value in _marks(grid)
    )


def _has_second_distinct_visible_anchor(grid) -> bool:
    marks = _marks(grid)
    if len(marks) < 2:
        return False
    h, w = len(grid), len(grid[0])
    first_r, first_c, _value = marks[0]
    first_diag = first_r - first_c
    return any(
        r - c != first_diag and bool(_trail_cells_for_mark(h, w, r, c))
        for r, c, _value in marks[1:]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "visible_color1_trail": _has_visible_trail,
    "northwest_extension": _has_northwest_extension,
    "southeast_extension": _has_southeast_extension,
    "off_main_diagonal_trail": _has_off_main_visible_trail,
    "second_distinct_anchor_contributes": _has_second_distinct_visible_anchor,
}

WITNESS_RIVALS = {
    "visible_color1_trail": ["scale_only", "marker_colored_trails"],
    "northwest_extension": ["southeast_only"],
    "southeast_extension": ["northwest_only"],
    "off_main_diagonal_trail": ["main_diagonal_only"],
    "second_distinct_anchor_contributes": ["first_anchor_only"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    input_grid = pair["input"]
    reasons = self_check(input_grid)
    if reasons:
        return [f"{label}: {reason}" for reason in reasons]
    if pair["output"] != rule_mirror(input_grid):
        return [f"{label} output does not match the full doubled-diagonal rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons in which a named plausible rival survives the demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"named rival {name!r} survives every demonstration")

    demo_inputs = [pair["input"] for pair in demos]
    if not any(_has_northwest_extension(grid) for grid in demo_inputs):
        reasons.append("no demonstration requires a northwest trail extension")
    if not any(_has_southeast_extension(grid) for grid in demo_inputs):
        reasons.append("no demonstration requires a southeast trail extension")
    if not any(_has_off_main_visible_trail(grid) for grid in demo_inputs):
        reasons.append("no demonstration ties a trail to an off-main-diagonal marker")
    if not any(_has_second_distinct_visible_anchor(grid) for grid in demo_inputs):
        reasons.append("no demonstration proves that a second distinct marker contributes")
    return reasons
