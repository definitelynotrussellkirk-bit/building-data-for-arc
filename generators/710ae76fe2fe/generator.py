"""Generator for ARC task 710ae76fe2fe — intersect two Ferrers signatures.

The first column stores left-justified row-length caps and the first row stores
top-justified column-height caps.  The canonical Racket rule paints cyan (8)
inside the body exactly where both caps admit the cell.

Most canonical examples use two mutually consistent signatures of one Ferrers
shape, while one has a deliberately looser row cap.  Ordinary lessons preserve
those empirical branches and add symmetric column-loose cases.  Half of the
schedule uses two monotone Ferrers cap profiles that cross,
so the intersection differs from either one-header reconstruction.  Those
controlled counterexamples refute the plausible "read only the first row" and
"read only the first column" shortcuts without reverting to arbitrary noisy
headers or non-Ferrers outputs.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "710ae76fe2fe"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "68e3bc631fba"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Read row-length caps from column 0 and column-height caps from row 0. "
    "Remove those headers and paint a body cell cyan (8) exactly when it lies "
    "inside both the row cap and the column cap."
)

INVARIANTS = [
    "the top-left corner is 0 and the body interior is all 0",
    "row-header values are positive, nonincreasing lengths within the body width",
    "column-header values are positive, nonincreasing heights within the body height",
    "the output is a top-left Ferrers staircase with at least three row and column levels",
    "canonical scenes include both mutually consistent caps and a looser row cap",
    "one-sided scenes expose either row or column as the binding cap",
    "crossing scenes make both headers independently decisive under intersection",
]

SCENE_PROFILES = ("consistent", "row_loose", "column_loose", "crossing")
SCHEDULE_PROFILES = SCENE_PROFILES
# Every three-demo sliding window contains a crossing witness, while ordinary
# draws also cover the canonical consistent and row-loose branches plus the
# symmetric column-loose generalization.
_PROFILE_SCHEDULE = (
    "consistent", "crossing", "crossing",
    "row_loose", "crossing", "column_loose",
)
_CANONICAL_GRID_PROFILES = ((4, 5), (5, 6), (5, 4), (6, 7))

# Header cells are ARC colors, so the largest representable count is 9.  A
# 10x10 input has a 9x9 body and is therefore the largest lawful canvas.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 4..6 anchors plus difficulty-skewed 4..10 variation",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 4..7 anchors plus difficulty-skewed 4..10 variation",
        "valid": "4..10",
    },
    "scene_profile": {
        "type": "str",
        "default": "six-step schedule covering consistent, both one-sided, and crossing caps",
        "valid": "consistent|row_loose|column_loose|crossing",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def _dimension_options(difficulty: str | None, *, width: bool) -> list[int]:
    """Retain every exact override while softly varying ordinary scale."""
    if difficulty == "easy":
        weighted = [4, 4, 4, 5, 5, 5, 6, 6, 7, 8, 9, 10]
    elif difficulty == "hard":
        weighted = [4, 5, 6, 7, 7, 8, 8, 9, 9, 9, 10, 10, 10]
    else:
        weighted = [4, 4, 5, 5, 6, 6, 7, 7, 8, 9, 10]
    # Width 7 is a canonical extreme and receives one extra ordinary draw.
    return weighted + ([7] if width else [])


def _scheduled_dimensions(seed: int, sample_index: int) -> tuple[int, int]:
    index = (int(seed) + int(sample_index) // 4) % len(_CANONICAL_GRID_PROFILES)
    return _CANONICAL_GRID_PROFILES[index]


def _random_partition(height: int, width: int, rng, *, force_three_levels: bool) -> list[int]:
    """Positive nonincreasing row lengths spanning the full body width."""
    if height < 3 or width < 3:
        raise ValueError("Ferrers profiles require a body of at least 3x3")
    values = [width]
    if force_three_levels:
        values.append(rng.randint(2, width - 1))
        remaining = height - 3
        values.extend(rng.randint(1, width) for _ in range(remaining))
        values.append(1)
    else:
        values.extend(rng.randint(1, width) for _ in range(height - 1))
    values.sort(reverse=True)
    return values


def _conjugate(row_lengths: list[int], width: int) -> list[int]:
    return [sum(length > column for length in row_lengths) for column in range(width)]


def _row_shape_from_lengths(row_lengths: list[int], width: int) -> list[list[int]]:
    return [
        [8 if column < row_lengths[row] else 0 for column in range(width)]
        for row in range(len(row_lengths))
    ]


def _col_shape_from_heights(col_heights: list[int], height: int) -> list[list[int]]:
    return [
        [8 if row < col_heights[column] else 0 for column in range(len(col_heights))]
        for row in range(height)
    ]


def _intersection_from_headers(
    row_lengths: list[int], col_heights: list[int]
) -> list[list[int]]:
    return [
        [
            8 if column < row_lengths[row] and row < col_heights[column] else 0
            for column in range(len(col_heights))
        ]
        for row in range(len(row_lengths))
    ]



def _loosen_partition(target: list[int], width: int, rng) -> list[int]:
    """Increase one cap without changing the target intersection shape."""
    candidates = [
        index
        for index in range(1, len(target))
        if target[index] < min(width, target[index - 1])
    ]
    if not candidates:
        raise ValueError("target partition has no monotone cap that can be loosened")
    index = rng.choice(candidates)
    loose = list(target)
    loose[index] += 1
    return loose

def _crossing_profiles(height: int, width: int, rng) -> tuple[list[int], list[int]]:
    """Return two monotone row profiles whose pointwise minimum uses both."""
    for _ in range(512):
        left = _random_partition(height, width, rng, force_three_levels=False)
        top = _random_partition(height, width, rng, force_three_levels=False)
        if not any(a > b for a, b in zip(left, top)):
            continue
        if not any(a < b for a, b in zip(left, top)):
            continue
        target = [min(a, b) for a, b in zip(left, top)]
        if len(set(target)) < 3:
            continue
        if len(set(_conjugate(target, width))) < 3:
            continue
        return left, top

    # Small bodies (including the 3x3 minimum) have this exact crossing pair:
    # row 1 is constrained by the top profile, row 2 by the left profile.
    left = [width, width, 1] + [1] * (height - 3)
    top = [width, width - 1, 2] + [1] * (height - 3)
    return left, top


def _grid_from_headers(row_lengths: list[int], col_heights: list[int]) -> list[list[int]]:
    grid = full_grid(len(row_lengths) + 1, len(col_heights) + 1, 0)
    for row, length in enumerate(row_lengths, start=1):
        grid[row][0] = length
    for column, height in enumerate(col_heights, start=1):
        grid[0][column] = height
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)

    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    # Half of ordinary draws use exact canonical dimension pairs.  Caller
    # overrides remain authoritative axis-by-axis.
    if int(sample_index) % 6 in (0, 3):
        height, width = _scheduled_dimensions(seed, sample_index)
        effective_overrides.setdefault("grid_h", height)
        effective_overrides.setdefault("grid_w", width)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    grid_h = ctx.draw_choice("grid_h", _dimension_options(difficulty, width=False))
    grid_w = ctx.draw_choice("grid_w", _dimension_options(difficulty, width=True))
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("ferrers_profiles")

    body_h, body_w = grid_h - 1, grid_w - 1
    if scene_profile == "consistent":
        target = _random_partition(body_h, body_w, rng, force_three_levels=True)
        row_lengths = target
        col_heights = _conjugate(target, body_w)
    elif scene_profile == "row_loose":
        target = _random_partition(body_h, body_w, rng, force_three_levels=True)
        row_lengths = _loosen_partition(target, body_w, rng)
        col_heights = _conjugate(target, body_w)
    elif scene_profile == "column_loose":
        target = _random_partition(body_h, body_w, rng, force_three_levels=True)
        row_lengths = target
        col_heights = _conjugate(_loosen_partition(target, body_w, rng), body_w)
    else:
        row_lengths, second_row_profile = _crossing_profiles(body_h, body_w, rng)
        col_heights = _conjugate(second_row_profile, body_w)

    grid = _grid_from_headers(row_lengths, col_heights)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid Ferrers-signature scene: " + "; ".join(errors))

    observed = observe_overrides(grid)
    expected = {name: ctx.axis_value(name) for name in AXES}
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost keyed axis values: expected {expected}, observed {observed}"
        )
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    result: dict[str, Any] = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    grid_h, grid_w = len(grid), len(grid[0])
    body_h, body_w = grid_h - 1, grid_w - 1
    if not 4 <= grid_h <= 10:
        errors.append(f"grid height must be in 4..10, got {grid_h}")
    if not 4 <= grid_w <= 10:
        errors.append(f"grid width must be in 4..10, got {grid_w}")
    if grid[0][0] != 0:
        errors.append("top-left header corner must be 0")
    if any(grid[row][column] != 0 for row in range(1, grid_h) for column in range(1, grid_w)):
        errors.append("body interior must be all 0; only the two headers carry data")

    row_lengths = [grid[row][0] for row in range(1, grid_h)]
    col_heights = [grid[0][column] for column in range(1, grid_w)]
    if any(not 1 <= value <= body_w for value in row_lengths):
        errors.append("every row-header length must lie in 1..body_width")
    if any(not 1 <= value <= body_h for value in col_heights):
        errors.append("every column-header height must lie in 1..body_height")
    if row_lengths and row_lengths[0] != body_w:
        errors.append("row headers must span the full body width in the first row")
    if col_heights and col_heights[0] != body_h:
        errors.append("column headers must span the full body height in the first column")
    if any(left < right for left, right in zip(row_lengths, row_lengths[1:])):
        errors.append("row-header lengths must be nonincreasing")
    if any(top < bottom for top, bottom in zip(col_heights, col_heights[1:])):
        errors.append("column-header heights must be nonincreasing")

    row_shape = _row_shape_from_lengths(row_lengths, body_w)
    col_shape = _col_shape_from_heights(col_heights, body_h)
    output = _intersection_from_headers(row_lengths, col_heights)
    output_row_lengths = [sum(value == 8 for value in row) for row in output]
    output_col_heights = [
        sum(output[row][column] == 8 for row in range(body_h))
        for column in range(body_w)
    ]

    if output and (not any(8 in row for row in output) or not any(0 in row for row in output)):
        errors.append("the output must contain both cyan and background cells")
    if len(set(output_row_lengths)) < 3:
        errors.append("the output must expose at least three distinct row lengths")
    if len(set(output_col_heights)) < 3:
        errors.append("the output must expose at least three distinct column heights")

    if row_shape == col_shape:
        scene_profile = "consistent"
    elif output == col_shape and output != row_shape:
        scene_profile = "row_loose"
    elif output == row_shape and output != col_shape:
        scene_profile = "column_loose"
    else:
        scene_profile = "crossing"

    result.update(
        {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "row_lengths": row_lengths,
            "col_heights": col_heights,
            "row_shape": row_shape,
            "col_shape": col_shape,
            "output": output,
            "output_row_lengths": output_row_lengths,
            "output_col_heights": output_col_heights,
            "scene_profile": scene_profile,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority-valid grammar and reject rule-hiding scenes."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Empirical manifold: both headers are conjugate signatures of one shape."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if not errors and analysis["scene_profile"] not in {"consistent", "row_loose"}:
        errors.append(
            "canonical examples use consistent signatures or a looser row cap"
        )
    return errors


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "scene_profile": analysis["scene_profile"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; the canonical Racket rule is authoritative."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    row_lengths = [grid[row][0] for row in range(1, len(grid))]
    col_heights = [grid[0][column] for column in range(1, len(grid[0]))]
    return _intersection_from_headers(row_lengths, col_heights)


def _row_headers_only(grid: list[list[int]]) -> list[list[int]]:
    row_lengths = [grid[row][0] for row in range(1, len(grid))]
    return _row_shape_from_lengths(row_lengths, len(grid[0]) - 1)


def _column_headers_only(grid: list[list[int]]) -> list[list[int]]:
    col_heights = [grid[0][column] for column in range(1, len(grid[0]))]
    return _col_shape_from_heights(col_heights, len(grid) - 1)


def _union_of_headers(grid: list[list[int]]) -> list[list[int]]:
    row_shape = _row_headers_only(grid)
    col_shape = _column_headers_only(grid)
    return [
        [8 if row_shape[row][column] or col_shape[row][column] else 0 for column in range(len(row_shape[0]))]
        for row in range(len(row_shape))
    ]


def _full_inner_canvas(grid: list[list[int]]) -> list[list[int]]:
    return [[8] * (len(grid[0]) - 1) for _ in range(len(grid) - 1)]


def _empty_inner_canvas(grid: list[list[int]]) -> list[list[int]]:
    return [[0] * (len(grid[0]) - 1) for _ in range(len(grid) - 1)]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "row_headers_only": _row_headers_only,
    "column_headers_only": _column_headers_only,
    "union_of_headers": _union_of_headers,
    "full_inner_canvas": _full_inner_canvas,
    "empty_inner_canvas": _empty_inner_canvas,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "column_headers_only": SEMANTIC_RIVALS["column_headers_only"],
}


def _both_headers_decisive(grid: list[list[int]]) -> bool:
    return _analysis(grid)["scene_profile"] == "crossing"


def _mixed_staircase(grid: list[list[int]]) -> bool:
    output = rule_mirror(grid)
    values = {value for row in output for value in row}
    return values == {0, 8}


def _three_level_ferrers(grid: list[list[int]]) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and len(set(analysis["output_row_lengths"])) >= 3
        and len(set(analysis["output_col_heights"])) >= 3
    )


SEMANTIC_WITNESSES = {
    "both_headers_decisive": _both_headers_decisive,
    "mixed_staircase": _mixed_staircase,
    "three_level_ferrers": _three_level_ferrers,
}
WITNESS_RIVALS = {
    "both_headers_decisive": [
        "row_headers_only",
        "column_headers_only",
        "union_of_headers",
    ],
    "mixed_staircase": ["full_inner_canvas", "empty_inner_canvas"],
    "three_level_ferrers": ["full_inner_canvas", "empty_inner_canvas"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits every demo but not the query."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        errors = self_check(pair.get("input"))
        if errors:
            reasons.append(f"{role} input is outside the teaching grammar: {errors[0]}")
            continue
        if pair.get("output") != rule_mirror(pair["input"]):
            reasons.append(f"{role} output does not match header intersection")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Targeted malformed scenes that the structural checker must reject."""
    base = _grid_from_headers([3, 2, 1], [3, 2, 1])

    interior = [row[:] for row in base]
    interior[2][2] = 7

    nonmonotone_rows = [row[:] for row in base]
    nonmonotone_rows[2][0], nonmonotone_rows[3][0] = 1, 2

    nonmonotone_cols = [row[:] for row in base]
    nonmonotone_cols[0][2], nonmonotone_cols[0][3] = 1, 2

    full_rectangle = _grid_from_headers([3, 3, 3], [3, 3, 3])

    bad_corner = [row[:] for row in base]
    bad_corner[0][0] = 9

    out_of_range = [row[:] for row in base]
    out_of_range[1][0] = 4

    return [
        ("interior_contamination", interior),
        ("nonmonotone_row_headers", nonmonotone_rows),
        ("nonmonotone_column_headers", nonmonotone_cols),
        ("full_rectangle_no_staircase", full_rectangle),
        ("nonzero_top_left_corner", bad_corner),
        ("row_header_out_of_range", out_of_range),
    ]
