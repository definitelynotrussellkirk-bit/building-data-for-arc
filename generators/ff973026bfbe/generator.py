"""Generator for ARC task ff973026bfbe: paint marked row/column intersections.

The authoritative Racket rule reads two independent marker sets:

* every row containing colour 1 is active, regardless of the marker column;
* every column whose row-0 cell is colour 2 is active;
* each active-row/active-column intersection is painted colour 3.

Colour-2 cells below row 0 and one unrelated colour are inert distractors.  The
curriculum deliberately varies both conditions that the canonical examples
leave ambiguous: colour-1 markers need not be on the left border, and colour-2
cells below row 0 do not activate their columns.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ff973026bfbe"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0f7e32eb6ec7"

SUMMARY = (
    "On a colour-0 background, rows containing colour 1 are active and columns "
    "with colour 2 in row 0 are active. Paint their Cartesian-product "
    "intersections colour 3. Colour-2 cells below row 0 and a separate neutral "
    "colour are distractors and remain unchanged."
)

INVARIANTS = [
    "the grid is 7..14 rows by 8..14 columns",
    "there are 1..5 colour-1 cells in distinct non-top rows",
    "colour-1 markers are either all on column 0 or all strictly off it",
    "there are 1..5 colour-2 cells in row 0 at distinct columns",
    "there are 0..2 colour-2 distractors below row 0 in non-active columns",
    "there are 1..3 cells of exactly one neutral colour 4..9 on inactive rows",
    "colour 3 never occurs in an input",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_ROW_MARKER_MODES = ("border", "scattered")
_DISTRACTOR_COLORS = (4, 5, 6, 7, 8, 9)
_CANONICAL_PROFILES = ((8, 9), (7, 10), (9, 8), (8, 11), (7, 9))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "8..14",
    },
    "n_row_marks": {
        "type": "int",
        "default": "difficulty draw",
        "valid": "1..5",
    },
    "n_col_marks": {
        "type": "int",
        "default": "difficulty draw",
        "valid": "1..5",
    },
    "n_red_decoys": {
        "type": "int",
        "default": "semantic schedule",
        "valid": "0..2",
    },
    "n_neutral": {
        "type": "int",
        "default": "difficulty draw",
        "valid": "1..3",
    },
    "row_marker_mode": {
        "type": "str",
        "default": "semantic schedule",
        "valid": "border|scattered",
    },
    "distractor_color": {
        "type": "color",
        "default": "keyed choice",
        "valid": "4|5|6|7|8|9",
    },
}

# Any three demonstrations retained from any four consecutive generated pairs
# contain both shortcut refutations.  Profile 2 carries both witnesses, while
# profiles 0 and 1 keep each condition independently observable.
_PROFILES = (
    {"name": "border_red_decoy", "row_marker_mode": "border", "n_red_decoys": 1},
    {"name": "scattered_no_red_decoy", "row_marker_mode": "scattered", "n_red_decoys": 0},
    {"name": "scattered_red_decoy", "row_marker_mode": "scattered", "n_red_decoys": 1},
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic semantic curriculum profile."""
    del seed
    _validate_difficulty(difficulty)
    return _PROFILES[int(sample_index) % len(_PROFILES)]["name"]


def _profile_for(sample_index: int) -> dict[str, Any]:
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    integer_ranges = {
        "grid_h": (7, 14),
        "grid_w": (8, 14),
        "n_row_marks": (1, 5),
        "n_col_marks": (1, 5),
        "n_red_decoys": (0, 2),
        "n_neutral": (1, 3),
    }
    for name, (lo, hi) in integer_ranges.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"override {name} must be an integer in {lo}..{hi}")

    if (
        "row_marker_mode" in overrides
        and overrides["row_marker_mode"] is not None
        and overrides["row_marker_mode"] not in _ROW_MARKER_MODES
    ):
        raise ValueError(
            f"override row_marker_mode must be one of {_ROW_MARKER_MODES}"
        )
    if (
        "distractor_color" in overrides
        and overrides["distractor_color"] is not None
        and (
            type(overrides["distractor_color"]) is not int
            or overrides["distractor_color"] not in _DISTRACTOR_COLORS
        )
    ):
        raise ValueError(
            f"override distractor_color must be one of {_DISTRACTOR_COLORS}"
        )


def _draw_scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use a scheduled default while keeping every documented override exact."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _draw_scheduled_choice(ctx, overrides, label: str, default: Any, options: tuple[Any, ...]):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _draw_dimensions(ctx, overrides, sample_index: int) -> tuple[int, int]:
    # A linked canonical profile every fourth sample gives the profile-floor
    # checker exact support without making every generated size canonical.
    if (
        sample_index % 4 == 0
        and not any(name in overrides and overrides[name] is not None for name in ("grid_h", "grid_w"))
    ):
        height, width = _CANONICAL_PROFILES[(sample_index // 4) % len(_CANONICAL_PROFILES)]
        return (
            ctx.draw_choice("grid_h", (height,)),
            ctx.draw_choice("grid_w", (width,)),
        )
    return (
        ctx.draw_int_diff("grid_h", 7, 14),
        ctx.draw_int_diff("grid_w", 8, 14),
    )


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 14:
        errors.append(f"height must be in 7..14, found {height}")
    if not 8 <= width <= 14:
        errors.append(f"width must be in 8..14, found {width}")

    cells_by_color: dict[int, list[tuple[int, int]]] = {color: [] for color in range(10)}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            cells_by_color[value].append((row, col))

    if cells_by_color[3]:
        errors.append("colour 3 is output-only and must not occur in an input")

    illegal = [color for color in range(10) if color not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9) and cells_by_color[color]]
    if illegal:  # Defensive; literal ARC validation above currently makes this unreachable.
        errors.append(f"illegal colours: {illegal}")

    blue = cells_by_color[1]
    if not 1 <= len(blue) <= 5:
        errors.append(f"expected 1..5 colour-1 markers, found {len(blue)}")
    blue_rows = [row for row, _ in blue]
    if any(row == 0 for row in blue):
        errors.append("colour-1 markers must be below row 0")
    if len(set(blue_rows)) != len(blue_rows):
        errors.append("colour-1 markers must occupy distinct rows")
    row_marker_mode = None
    if blue and all(col == 0 for _, col in blue):
        row_marker_mode = "border"
    elif blue and all(col > 0 for _, col in blue):
        row_marker_mode = "scattered"
    elif blue:
        errors.append("colour-1 markers must be uniformly border or scattered")

    red = cells_by_color[2]
    top_red = [(row, col) for row, col in red if row == 0]
    red_decoys = [(row, col) for row, col in red if row != 0]
    if not 1 <= len(top_red) <= 5:
        errors.append(f"expected 1..5 top-row colour-2 markers, found {len(top_red)}")
    if not 0 <= len(red_decoys) <= 2:
        errors.append(f"expected 0..2 off-top colour-2 distractors, found {len(red_decoys)}")
    active_cols = {col for _, col in top_red}
    bad_decoys = [(row, col) for row, col in red_decoys if col in active_cols]
    if bad_decoys:
        errors.append(f"off-top red distractors must use inactive columns: {bad_decoys}")
    if len({col for _, col in red_decoys}) != len(red_decoys):
        errors.append("off-top red distractors must use distinct columns")

    neutral = [
        (row, col, color)
        for color in _DISTRACTOR_COLORS
        for row, col in cells_by_color[color]
    ]
    neutral_colors = {color for _, _, color in neutral}
    if len(neutral_colors) != 1:
        errors.append(
            f"expected exactly one neutral colour from 4..9, found {sorted(neutral_colors)}"
        )
    if not 1 <= len(neutral) <= 3:
        errors.append(f"expected 1..3 neutral cells, found {len(neutral)}")
    active_rows = set(blue_rows)
    bad_neutral = [
        (row, col, color)
        for row, col, color in neutral
        if row == 0 or row in active_rows
    ]
    if bad_neutral:
        errors.append(f"neutral cells must lie on inactive non-top rows: {bad_neutral}")

    # Inputs intentionally use exactly four colours: background, the two marker
    # colours, and one neutral distractor.  This matches the canonical palette.
    present = {value for row in grid for value in row}
    if len(present) != 4 or not {0, 1, 2}.issubset(present):
        errors.append(f"input palette must be 0,1,2 plus one neutral colour; found {sorted(present)}")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "blue": blue,
        "top_red": top_red,
        "red_decoys": red_decoys,
        "neutral": neutral,
        "row_marker_mode": row_marker_mode,
        "distractor_color": next(iter(neutral_colors)) if len(neutral_colors) == 1 else None,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_row_marks": len(analysis["blue"]),
        "n_col_marks": len(analysis["top_red"]),
        "n_red_decoys": len(analysis["red_decoys"]),
        "n_neutral": len(analysis["neutral"]),
        "row_marker_mode": analysis["row_marker_mode"],
        "distractor_color": analysis["distractor_color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or off-contract generated scenes."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar and canonical examples share one strict contract."""
    return self_check(grid)


def _paint(grid, rows: set[int], cols: set[int]):
    output = [list(row) for row in grid]
    for row in rows:
        for col in cols:
            output[row][col] = 3
    return output


def rule_mirror(grid):
    """Independent Python mirror for diagnostics; canonical Racket is authority."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    rows = {row for row, values in enumerate(grid) if 1 in values}
    cols = {col for col, value in enumerate(grid[0]) if value == 2}
    return _paint(grid, rows, cols)


def _left_border_rows_only(grid):
    rows = {row for row, values in enumerate(grid) if values[0] == 1}
    cols = {col for col, value in enumerate(grid[0]) if value == 2}
    return _paint(grid, rows, cols)


def _all_red_columns(grid):
    rows = {row for row, values in enumerate(grid) if 1 in values}
    cols = {
        col
        for values in grid
        for col, value in enumerate(values)
        if value == 2
    }
    return _paint(grid, rows, cols)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "left_border_rows_only": _left_border_rows_only,
    "all_red_columns": _all_red_columns,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _lawful(grid) -> bool:
    return not _analysis(grid)["errors"]


def _has_off_border_row_marker(grid) -> bool:
    return _lawful(grid) and any(
        value == 1 and col > 0
        for values in grid
        for col, value in enumerate(values)
    )


def _has_off_top_red_decoy(grid) -> bool:
    return _lawful(grid) and any(
        value == 2 and row > 0
        for row, values in enumerate(grid)
        for value in values
    )


SEMANTIC_WITNESSES = {
    "off_border_row_marker": _has_off_border_row_marker,
    "off_top_red_decoy": _has_off_top_red_decoy,
}
WITNESS_RIVALS = {
    "off_border_row_marker": ["left_border_rows_only"],
    "off_top_red_decoy": ["all_red_columns"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute both canonical-fitting shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    saw_off_border = False
    saw_off_top_red = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match the intersection rule")
        saw_off_border |= _has_off_border_row_marker(demo["input"])
        saw_off_top_red |= _has_off_top_red_decoy(demo["input"])

    if not saw_off_border:
        reasons.append("demonstrations do not refute the left-border-only row shortcut")
    if not saw_off_top_red:
        reasons.append("demonstrations do not refute the all-red-columns shortcut")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket owns output."""
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    profile = _profile_for(sample_index)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width = _draw_dimensions(ctx, overrides, int(sample_index))
    n_row = ctx.draw_int_diff("n_row_marks", 1, 5)
    n_col = ctx.draw_int_diff("n_col_marks", 1, 5)
    n_red_decoys = _draw_scheduled_int(
        ctx,
        overrides,
        "n_red_decoys",
        int(profile["n_red_decoys"]),
        0,
        2,
    )
    n_neutral = ctx.draw_int_diff("n_neutral", 1, 3)
    row_marker_mode = _draw_scheduled_choice(
        ctx,
        overrides,
        "row_marker_mode",
        profile["row_marker_mode"],
        _ROW_MARKER_MODES,
    )
    distractor_color = ctx.draw_choice("distractor_color", _DISTRACTOR_COLORS)

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    grid = full_grid(height, width, 0)

    rows = list(range(1, height))
    layout_rng.shuffle(rows)
    active_rows = rows[:n_row]
    if row_marker_mode == "border":
        blue_cells = [(row, 0) for row in active_rows]
    else:
        blue_cells = [
            (row, layout_rng.randint(1, width - 1))
            for row in active_rows
        ]
    for row, col in blue_cells:
        grid[row][col] = 1

    columns = list(range(width))
    layout_rng.shuffle(columns)
    active_cols = columns[:n_col]
    for col in active_cols:
        grid[0][col] = 2

    # Off-top reds use distinct inactive columns, so they visibly disagree with
    # the all-red-columns rival while remaining untouched by the intended rule.
    decoy_cols = [col for col in range(width) if col not in set(active_cols)]
    layout_rng.shuffle(decoy_cols)
    for col in decoy_cols[:n_red_decoys]:
        candidates = [
            row
            for row in range(1, height)
            if grid[row][col] == 0
        ]
        if not candidates:
            raise ValueError(f"no legal row for red distractor in column {col}")
        row = layout_rng.choice(candidates)
        grid[row][col] = 2

    inactive_rows = [row for row in range(1, height) if row not in set(active_rows)]
    neutral_candidates = [
        (row, col)
        for row in inactive_rows
        for col in range(width)
        if grid[row][col] == 0
    ]
    layout_rng.shuffle(neutral_candidates)
    if len(neutral_candidates) < n_neutral:
        raise ValueError(
            f"need {n_neutral} neutral cells but only {len(neutral_candidates)} fit"
        )
    for row, col in neutral_candidates[:n_neutral]:
        grid[row][col] = distractor_color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
