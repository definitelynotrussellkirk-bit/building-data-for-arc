"""Generator for ARC task 4522001f / content hash 0ab4fcb302d2.

A lawful input is a 3x3 mini-grid with one empty row, one empty column,
one red marker, and three cells of one shared fill color.  Removing the empty
row and column leaves a 2x2 code: a red marker on that code's main diagonal
selects main-diagonal 4x4 output blocks; an off-diagonal marker selects the
anti-diagonal blocks.  The empty row and column determine the one-cell output
gutters.

The default four-draw schedule crosses main/anti marker positions with
same/different gap-index parity.  Each phase uses a different marker corner,
so all four inputs stay distinct under the production sampler.  The parity
assignment flips across seeds, preventing a corner-to-gap correlation while
any three pairs still refute gap parity, inverse gap parity, always-main, and
always-anti.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "0ab4fcb302d2"
TASK_ID = GENERATOR_ID
RULE_HASH = "39724c7d06e2"
VERSION = "3.2.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 3x3 mini-grid has one empty row and column; the red marker's position "
    "in the remaining 2x2 code selects main- versus anti-diagonal 4x4 blocks."
)

INVARIANTS = [
    "input is a rectangular 3x3 ARC-color grid",
    "exactly one row and exactly one column are all background",
    "the four non-gap intersections are nonzero",
    "exactly one non-gap cell is red(2)",
    "the other three non-gap cells share one nonzero non-red color",
]

AXES = {
    "gap_row": {
        "type": "int",
        "default": "difficulty-weighted full support",
        "valid": "0..2",
    },
    "gap_col": {
        "type": "int",
        "default": "four-draw semantic schedule with full support",
        "valid": "0..2",
    },
    "marker_corner": {
        "type": "int",
        "default": "row-major corner in the non-gap 2x2 code",
        "valid": "0..3",
    },
    "block_color": {
        "type": "color",
        "default": "difficulty-weighted full support excluding 0 and 2",
        "valid": "1|3|4|5|6|7|8|9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
_DIFFICULTIES = (None, "easy", "medium", "hard")
_GAP_ROW_OPTIONS = {
    None: (0, 1, 2),
    "easy": (0, 0, 0, 2, 2, 1),
    "medium": (0, 1, 1, 1, 2),
    "hard": (0, 1, 2, 2, 2, 1),
}
_COLOR_OPTIONS = {
    None: _COLORS,
    "easy": (1, 3, 3, 3, 4, 5, 6, 7, 8, 9),
    "medium": (1, 3, 4, 4, 5, 5, 6, 7, 8, 9),
    "hard": (1, 3, 4, 5, 6, 7, 8, 8, 9, 9),
}

# The four phases are the complete truth table for intended diagonal versus
# gap-index parity.  Distinct fixed marker corners make a four-pair window
# duplicate-proof; every one-query rotation leaves both output orientations
# and both parity agreement classes among the three demonstrations.
_SCHEDULE = (
    "anti_corner_1",
    "main_corner_0",
    "main_corner_3",
    "anti_corner_2",
)
SCHEDULE_PROFILES = _SCHEDULE


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic profile for one default draw."""
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name in ("gap_row", "gap_col", "marker_corner", "block_color"):
        if name in overrides and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer, not {type(overrides[name]).__name__}")

    for name in ("gap_row", "gap_col"):
        if name in overrides and not 0 <= overrides[name] <= 2:
            raise ValueError(f"{name}={overrides[name]} outside 0..2")
    if "marker_corner" in overrides and not 0 <= overrides["marker_corner"] <= 3:
        raise ValueError(
            f"marker_corner={overrides['marker_corner']} outside 0..3"
        )
    if "block_color" in overrides and overrides["block_color"] not in _COLORS:
        raise ValueError(
            f"block_color={overrides['block_color']} not in {_COLORS}"
        )


def _draw_axis(ctx, overrides, name, full_domain, scheduled_domain):
    options = full_domain if name in overrides else scheduled_domain
    return ctx.draw_choice(name, options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a lawful mini-grid with exact, pixel-observable overrides."""
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of {_DIFFICULTIES}, got {difficulty!r}"
        )
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
    phase = sample_index % len(_SCHEDULE)
    gap_row = ctx.draw_choice("gap_row", _GAP_ROW_OPTIONS[difficulty])

    del profile
    marker_by_phase = (1, 0, 3, 2)
    scheduled_corners = (marker_by_phase[phase],)
    base_same = phase in (0, 2)
    same_gaps = base_same if int(seed) % 2 == 0 else not base_same
    scheduled_cols = (
        (gap_row,)
        if same_gaps
        else tuple(col for col in range(3) if col != gap_row)
    )

    gap_col = _draw_axis(
        ctx, overrides, "gap_col", (0, 1, 2), scheduled_cols
    )
    marker_corner = _draw_axis(
        ctx, overrides, "marker_corner", (0, 1, 2, 3), scheduled_corners
    )
    block_color = ctx.draw_choice("block_color", _COLOR_OPTIONS[difficulty])

    grid = [[0] * 3 for _ in range(3)]
    rows = [row for row in range(3) if row != gap_row]
    cols = [col for col in range(3) if col != gap_col]
    for index, (row, col) in enumerate((r, c) for r in rows for c in cols):
        grid[row][col] = 2 if index == marker_corner else block_color
    return grid


def _parse(grid: Any) -> dict[str, int]:
    if not isinstance(grid, list) or len(grid) != 3:
        raise ValueError("grid must contain exactly three list rows")
    if any(not isinstance(row, list) or len(row) != 3 for row in grid):
        raise ValueError("grid must be rectangular 3x3")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")

    gap_rows = [
        row for row in range(3) if all(grid[row][col] == 0 for col in range(3))
    ]
    gap_cols = [
        col for col in range(3) if all(grid[row][col] == 0 for row in range(3))
    ]
    if len(gap_rows) != 1:
        raise ValueError(
            f"expected exactly one all-zero row, found {len(gap_rows)}"
        )
    if len(gap_cols) != 1:
        raise ValueError(
            f"expected exactly one all-zero column, found {len(gap_cols)}"
        )

    gap_row, gap_col = gap_rows[0], gap_cols[0]
    rows = [row for row in range(3) if row != gap_row]
    cols = [col for col in range(3) if col != gap_col]
    cells = [(row, col) for row in rows for col in cols]
    values = [grid[row][col] for row, col in cells]
    if any(value == 0 for value in values):
        raise ValueError("every non-gap intersection must be nonzero")

    marker_indices = [index for index, value in enumerate(values) if value == 2]
    if len(marker_indices) != 1:
        raise ValueError(
            f"expected exactly one red(2) marker, found {len(marker_indices)}"
        )
    fills = [value for value in values if value != 2]
    if len(fills) != 3 or len(set(fills)) != 1:
        raise ValueError(
            "the three non-marker quadrant cells must share one fill color"
        )
    block_color = fills[0]
    if block_color not in _COLORS:
        raise ValueError(
            f"fill color must be one of {_COLORS}, found {block_color}"
        )
    return {
        "gap_row": gap_row,
        "gap_col": gap_col,
        "marker_corner": marker_indices[0],
        "block_color": block_color,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural diagnostics without mutating or raising on bad grids."""
    del difficulty, meta
    try:
        _parse(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared axis from rendered pixels."""
    return dict(_parse(grid))


def _output_for_diagonal(grid, *, main_diagonal: bool) -> list[list[int]]:
    info = _parse(grid)
    top_row = 1 if info["gap_row"] == 0 else 0
    bottom_row = 4 if info["gap_row"] == 2 else 5
    left_col = 1 if info["gap_col"] == 0 else 0
    right_col = 4 if info["gap_col"] == 2 else 5
    blocks = (
        ((top_row, left_col), (bottom_row, right_col))
        if main_diagonal
        else ((top_row, right_col), (bottom_row, left_col))
    )
    output = [[0] * 9 for _ in range(9)]
    for row0, col0 in blocks:
        for row in range(row0, row0 + 4):
            for col in range(col0, col0 + 4):
                output[row][col] = info["block_color"]
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the pinned canonical Racket rule."""
    info = _parse(grid)
    return _output_for_diagonal(
        grid, main_diagonal=info["marker_corner"] in (0, 3)
    )


def gap_parity_output(grid) -> list[list[int]]:
    """Plausible wrong rule: derive diagonal from gap parity, ignore red."""
    info = _parse(grid)
    return _output_for_diagonal(
        grid, main_diagonal=info["gap_row"] == info["gap_col"]
    )


def inverse_gap_parity_output(grid) -> list[list[int]]:
    """Wrong rule: invert gap parity while still ignoring the red marker."""
    info = _parse(grid)
    return _output_for_diagonal(
        grid, main_diagonal=info["gap_row"] != info["gap_col"]
    )


def always_main_output(grid) -> list[list[int]]:
    """Weaker rival that ignores the red marker and always uses main diagonal."""
    return _output_for_diagonal(grid, main_diagonal=True)


def always_anti_output(grid) -> list[list[int]]:
    """Weaker rival that always uses the anti-diagonal blocks."""
    return _output_for_diagonal(grid, main_diagonal=False)


def _anti_marker_same_gaps(grid) -> bool:
    info = _parse(grid)
    return (
        info["marker_corner"] in (1, 2)
        and info["gap_row"] == info["gap_col"]
    )


def _main_marker_different_gaps(grid) -> bool:
    info = _parse(grid)
    return (
        info["marker_corner"] in (0, 3)
        and info["gap_row"] != info["gap_col"]
    )


def _main_marker_same_gaps(grid) -> bool:
    info = _parse(grid)
    return (
        info["marker_corner"] in (0, 3)
        and info["gap_row"] == info["gap_col"]
    )


def _anti_marker_different_gaps(grid) -> bool:
    info = _parse(grid)
    return (
        info["marker_corner"] in (1, 2)
        and info["gap_row"] != info["gap_col"]
    )


SEMANTIC_WITNESSES = {
    "anti_marker_same_gaps": _anti_marker_same_gaps,
    "main_marker_different_gaps": _main_marker_different_gaps,
    "main_marker_same_gaps": _main_marker_same_gaps,
    "anti_marker_different_gaps": _anti_marker_different_gaps,
}
SEMANTIC_RIVALS = {
    "gap_parity": gap_parity_output,
    "inverse_gap_parity": inverse_gap_parity_output,
    "always_main": always_main_output,
    "always_anti": always_anti_output,
}
WITNESS_RIVALS = {
    "anti_marker_same_gaps": ["gap_parity", "always_main"],
    "main_marker_different_gaps": ["gap_parity", "always_anti"],
    "main_marker_same_gaps": ["inverse_gap_parity", "always_anti"],
    "anti_marker_different_gaps": ["inverse_gap_parity", "always_main"],
}
CANONICAL_SHORTCUTS = {"gap_parity": gap_parity_output}
LESSON_COMPETITORS = {
    "gap_parity": gap_parity_output,
    "inverse_gap_parity": inverse_gap_parity_output,
    "always_main": always_main_output,
    "always_anti": always_anti_output,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check whether declared rivals surviving demos can change the query."""
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < 2:
        return ["lesson requires at least two demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    try:
        expected_query = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        return [f"invalid query input: {exc}"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        try:
            expected = rule_mirror(demo["input"])
        except (TypeError, ValueError) as exc:
            errors.append(f"invalid demo {index} input: {exc}")
            continue
        if expected != demo["output"]:
            errors.append(f"demo {index} output disagrees with the pinned rule")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = rival(query["input"]) != expected_query
        except (TypeError, ValueError) as exc:
            errors.append(f"competitor {name!r} failed: {exc}")
            continue
        if survives and changes_query:
            errors.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return errors
