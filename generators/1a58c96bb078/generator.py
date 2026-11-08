"""Generator for ARC task 1a58c96bb078: column legend painter.

The top row is a per-column legend.  In body rows, a cyan cell (colour 8)
is replaced by the non-zero legend colour at the top of its column.  Cyan
cells below an empty header and every non-cyan body cell are preserved.

The curriculum deliberately contains both observations that the original
sampler omitted:

* unrelated coloured body cells that must survive unchanged; and
* scheduled cyan cells below empty headers that must remain cyan.

Together they refute a destructive "clear the body then paint" shortcut and
the canonical-fitting "drop unmapped cyan" shortcut.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1a58c96bb078"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "341c4a414d7c"

SUMMARY = (
    "Use row 0 as a column legend. Replace each body colour-8 cell with its "
    "column's non-zero header colour; leave colour-8 cells below empty headers "
    "and all other cells unchanged."
)

INVARIANTS = [
    "the grid is 7..14 rows by 7..16 columns",
    "row 0 contains 1..5 distinct non-zero, non-cyan legend colours",
    "each legend column contains the same 1..4 cyan markers",
    "0..3 cyan markers occur below empty header columns and remain cyan",
    "1..4 cells of one non-legend colour occur below empty headers and remain unchanged",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_LEGEND_AND_DISTRACTOR_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_ANCHORS = (
    {
        "grid_h": 7,
        "grid_w": 7,
        "n_legend_cols": 2,
        "markers_per_col": 2,
        "n_preserved": 1,
        "n_inert_eights": 0,
        "distractor_color": 6,
    },
    {
        "grid_h": 8,
        "grid_w": 8,
        "n_legend_cols": 2,
        "markers_per_col": 2,
        "n_preserved": 1,
        "n_inert_eights": 0,
        "distractor_color": 5,
    },
    {
        "grid_h": 9,
        "grid_w": 9,
        "n_legend_cols": 3,
        "markers_per_col": 2,
        "n_preserved": 1,
        "n_inert_eights": 0,
        "distractor_color": 4,
    },
)
_PROFILE_NAMES = (
    "canonical_anchor",
    "one_inert_eight",
    "two_inert_eights",
    "three_inert_eights",
)
SCHEDULE_PROFILES = _PROFILE_NAMES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "7..16",
    },
    "n_legend_cols": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "1..5",
    },
    "markers_per_col": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "1..4",
    },
    "n_preserved": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "1..4",
    },
    "n_inert_eights": {
        "type": "int",
        "default": "four-sample semantic schedule",
        "valid": "0..3",
    },
    "distractor_color": {
        "type": "color",
        "default": "canonical-profile schedule plus keyed choice",
        "valid": "1|2|3|4|5|6|7|9",
    },
}


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the deterministic four-sample semantic schedule branch."""
    del seed
    _validate_difficulty(difficulty)
    return _PROFILE_NAMES[int(sample_index) % 4]


def _scheduled_defaults(sample_index: int) -> dict[str, int]:
    residue = int(sample_index) % 4
    if residue == 0:
        return dict(_CANONICAL_ANCHORS[(int(sample_index) // 4) % len(_CANONICAL_ANCHORS)])
    return {"n_inert_eights": residue}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    integer_ranges = {
        "grid_h": (7, 14),
        "grid_w": (7, 16),
        "n_legend_cols": (1, 5),
        "markers_per_col": (1, 4),
        "n_preserved": (1, 4),
        "n_inert_eights": (0, 3),
    }
    for name, (lo, hi) in integer_ranges.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"override {name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"override {name} must be in {lo}..{hi}")

    if "distractor_color" in overrides and overrides["distractor_color"] is not None:
        value = overrides["distractor_color"]
        if type(value) is not int:
            raise TypeError("override distractor_color must be an integer colour")
        if value not in _LEGEND_AND_DISTRACTOR_COLORS:
            raise ValueError(
                "override distractor_color must be one of "
                f"{_LEGEND_AND_DISTRACTOR_COLORS}"
            )


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    defaults: dict[str, int],
    name: str,
    lo: int,
    hi: int,
) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if name in defaults:
        return ctx.draw_choice(name, (defaults[name],))
    return ctx.draw_int_diff(name, lo, hi)


def _draw_color_axis(
    ctx,
    overrides: dict[str, Any],
    defaults: dict[str, int],
) -> int:
    if "distractor_color" in overrides and overrides["distractor_color"] is not None:
        return ctx.draw_choice("distractor_color", _LEGEND_AND_DISTRACTOR_COLORS)
    if "distractor_color" in defaults:
        return ctx.draw_choice("distractor_color", (defaults["distractor_color"],))
    return ctx.draw_choice("distractor_color", _LEGEND_AND_DISTRACTOR_COLORS)


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
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 14:
        errors.append(f"height must be in 7..14, found {height}")
    if not 7 <= width <= 16:
        errors.append(f"width must be in 7..16, found {width}")

    header = list(grid[0])
    if any(value == 8 for value in header):
        errors.append("row 0 may not use cyan (colour 8) as a legend")
    if any(value not in (0, *_LEGEND_AND_DISTRACTOR_COLORS) for value in header):
        errors.append("row 0 may contain only zero or non-cyan ARC colours")

    legend_cols = [col for col, value in enumerate(header) if value != 0]
    legend_colors = [header[col] for col in legend_cols]
    if not 1 <= len(legend_cols) <= 5:
        errors.append(f"expected 1..5 legend columns, found {len(legend_cols)}")
    if len(set(legend_colors)) != len(legend_colors):
        errors.append("legend colours must be distinct")

    marker_counts = [
        sum(grid[row][col] == 8 for row in range(1, height))
        for col in legend_cols
    ]
    markers_per_col = marker_counts[0] if marker_counts else None
    if marker_counts and len(set(marker_counts)) != 1:
        errors.append(f"legend columns must have equal cyan counts, found {marker_counts}")
    if markers_per_col is None or not 1 <= markers_per_col <= 4:
        errors.append(
            "each legend column must contain 1..4 cyan markers"
            + ("" if markers_per_col is None else f", found {markers_per_col}")
        )

    active = set(legend_cols)
    inert_eights = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] == 8 and col not in active
    ]
    if not 0 <= len(inert_eights) <= 3:
        errors.append(f"expected 0..3 cyan cells below empty headers, found {len(inert_eights)}")

    preserved = [
        (row, col, grid[row][col])
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    preserved_colors = {value for _, _, value in preserved}
    if len(preserved_colors) != 1:
        errors.append(
            "expected exactly one preserved body colour, found "
            f"{sorted(preserved_colors)}"
        )
    if not 1 <= len(preserved) <= 4:
        errors.append(f"expected 1..4 preserved body cells, found {len(preserved)}")
    if preserved_colors & set(legend_colors):
        errors.append("preserved body colour must differ from every legend colour")
    if any(col in active for _, col, _ in preserved):
        errors.append("preserved body cells must lie below empty header columns")

    distractor_color = next(iter(preserved_colors)) if len(preserved_colors) == 1 else None
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "legend_cols": legend_cols,
        "legend_colors": legend_colors,
        "markers_per_col": markers_per_col,
        "inert_eights": inert_eights,
        "preserved": preserved,
        "distractor_color": distractor_color,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact axis from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_legend_cols": len(analysis["legend_cols"]),
        "markers_per_col": analysis["markers_per_col"],
        "n_preserved": len(analysis["preserved"]),
        "n_inert_eights": len(analysis["inert_eights"]),
        "distractor_color": analysis["distractor_color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or off-contract input scenes."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar and all canonical inputs share this contract."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror for diagnostics; canonical Racket is authority."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            header = grid[0][col]
            if value == 8 and header != 0:
                output[row][col] = header
    return output


def _clear_body_then_paint(grid):
    """Rival: erase all body content, then redraw only mapped cyan markers."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = full_grid(len(grid), len(grid[0]), 0)
    output[0] = list(grid[0])
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 8 and grid[0][col] != 0:
                output[row][col] = grid[0][col]
    return output


def _drop_unmapped_eights(grid):
    """Rival: apply the rule but incorrectly erase cyan below empty headers."""
    output = rule_mirror(grid)
    for row in range(1, len(output)):
        for col, value in enumerate(output[row]):
            if value == 8:
                output[row][col] = 0
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "clear_body_then_paint": _clear_body_then_paint,
    "drop_unmapped_eights": _drop_unmapped_eights,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# Only this rival fits every canonical label; the destructive clearing rival is
# already refuted by each canonical preserved body cell.
CANONICAL_SHORTCUTS = {"drop_unmapped_eights": _drop_unmapped_eights}


def _lawful(grid) -> bool:
    return not _analysis(grid)["errors"]


def _has_preserved_foreign_body(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["preserved"])


def _has_inert_eight_outside_legend(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["inert_eights"])


SEMANTIC_WITNESSES = {
    "preserved_foreign_body": _has_preserved_foreign_body,
    "inert_eight_outside_legend": _has_inert_eight_outside_legend,
}
WITNESS_RIVALS = {
    "preserved_foreign_body": ["clear_body_then_paint"],
    "inert_eight_outside_legend": ["drop_unmapped_eights"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute both executable shortcut rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output does not match the column-legend rule")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        intended = rule_mirror(demo["input"])
        if demo["output"] != intended:
            reasons.append(f"demo {index} output does not match the column-legend rule")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] |= rival(demo["input"]) != intended

    if not refuted["clear_body_then_paint"]:
        reasons.append("demonstrations do not prove unrelated body cells are preserved")
    if not refuted["drop_unmapped_eights"]:
        reasons.append("demonstrations do not prove cyan below empty headers is preserved")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; canonical Racket owns the output."""
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    defaults = _scheduled_defaults(int(sample_index))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = _draw_int_axis(ctx, overrides, defaults, "grid_h", 7, 14)
    width = _draw_int_axis(ctx, overrides, defaults, "grid_w", 7, 16)
    n_legend = _draw_int_axis(ctx, overrides, defaults, "n_legend_cols", 1, 5)
    markers_per_col = _draw_int_axis(ctx, overrides, defaults, "markers_per_col", 1, 4)
    n_preserved = _draw_int_axis(ctx, overrides, defaults, "n_preserved", 1, 4)
    n_inert = _draw_int_axis(ctx, overrides, defaults, "n_inert_eights", 0, 3)
    distractor_color = _draw_color_axis(ctx, overrides, defaults)

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    grid = full_grid(height, width, 0)

    legend_cols = layout_rng.sample(range(width), n_legend)
    legend_palette = [
        color for color in _LEGEND_AND_DISTRACTOR_COLORS
        if color != distractor_color
    ]
    legend_colors = layout_rng.sample(legend_palette, n_legend)
    for col, color in zip(legend_cols, legend_colors):
        grid[0][col] = color
        for row in layout_rng.sample(range(1, height), markers_per_col):
            grid[row][col] = 8

    inactive_cols = [col for col in range(width) if col not in set(legend_cols)]
    inactive_cells = [
        (row, col)
        for row in range(1, height)
        for col in inactive_cols
    ]
    chosen = layout_rng.sample(inactive_cells, n_inert + n_preserved)
    for row, col in chosen[:n_inert]:
        grid[row][col] = 8
    for row, col in chosen[n_inert:]:
        grid[row][col] = distractor_color

    return grid
