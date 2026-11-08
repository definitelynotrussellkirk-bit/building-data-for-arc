"""Canonical-faithful generator for ARC task ``140c817e``.

Every input contains two to four blue (1) markers on a single-color
background.  The authoritative Racket rule processes the original markers in
row-major order.  For each marker it paints the complete row and column blue,
recolors the marker red (2), and recolors each in-bounds diagonal neighbor
green (3).

The four-draw schedule intentionally carries the complete canonical lesson
plus one rectangular recombination that breaks accidental correlations among
public axes.  It covers three observed background colors, multiple marker
counts, and both interior and boundary markers.  Public overrides are limited
to observable input properties; placement remains a private constructive detail.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7355dc4aa5e5"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6e7e8a6d6088"

SUMMARY = (
    "Place 2-4 well-separated blue markers on one legal background color. "
    "For each original marker, paint its whole row and column blue, recolor "
    "the marker red, and recolor its in-bounds diagonal neighbors green."
)

INVARIANTS = [
    "input dimensions are 7..16 by 7..16",
    "the grid contains exactly one background color plus 2..4 blue markers",
    "background is an ARC color other than the output-role colors 1, 2, and 3",
    "marker rows and columns are distinct and pairwise separated by at least two",
    "generation and all declared semantic helpers are deterministic and input-pure",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "7..16",
    },
    "n_ones": {
        "type": "int",
        "default": "scheduled 2|4|3|4",
        "valid": "2..4",
    },
    "bg_color": {
        "type": "color",
        "default": "scheduled 9|8|7|8",
        "valid": "0|4|5|6|7|8|9",
    },
}

# Every exact-axis combination is constructible for the declared ranges.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "canonical_9_bg9_n2_interior",
    "canonical_13_bg8_n4_interior",
    "canonical_11_bg7_n3_edge",
    "rectangular_bg8_n3_edge_generalization",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.75

_BACKGROUND_COLORS = (0, 4, 5, 6, 7, 8, 9)
_PROFILE_DEFAULTS = {
    SCHEDULE_PROFILES[0]: (9, 9, 2, 9, False),
    SCHEDULE_PROFILES[1]: (13, 13, 4, 8, False),
    SCHEDULE_PROFILES[2]: (11, 11, 3, 7, True),
    SCHEDULE_PROFILES[3]: (14, 9, 3, 8, True),
}
_CANONICAL_PROFILES = {
    (9, 9, 2, 9),
    (13, 13, 4, 8),
    (11, 11, 3, 7),
    (14, 14, 4, 8),
}


def _literal_nonnegative_int(value: Any, label: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer (not bool)")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative")
    return value


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the stable four-profile curriculum slot for ``sample_index``."""
    del seed, difficulty
    index = _literal_nonnegative_int(sample_index, "sample_index")
    return SCHEDULE_PROFILES[index % len(SCHEDULE_PROFILES)]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{col_index}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _analyze(grid: Any) -> tuple[int, int, int | None, list[tuple[int, int]], list[str]]:
    height, width, errors = _validate_grid(grid)
    if errors:
        return height, width, None, [], errors

    if not (7 <= height <= 16):
        errors.append(f"height {height} outside 7..16")
    if not (7 <= width <= 16):
        errors.append(f"width {width} outside 7..16")

    markers = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 1
    ]
    if not (2 <= len(markers) <= 4):
        errors.append(f"expected 2..4 color-1 markers, found {len(markers)}")

    colors = {value for row in grid for value in row}
    backgrounds = colors - {1}
    background: int | None = None
    if len(backgrounds) != 1:
        errors.append(
            "expected exactly one background color besides marker color 1, "
            f"found {sorted(backgrounds)}"
        )
    else:
        background = next(iter(backgrounds))
        if background not in _BACKGROUND_COLORS:
            errors.append(
                f"background color {background} is illegal; expected one of {_BACKGROUND_COLORS}"
            )

    marker_rows = [row for row, _col in markers]
    marker_cols = [col for _row, col in markers]
    if len(set(marker_rows)) != len(marker_rows):
        errors.append("marker rows must be distinct")
    if len(set(marker_cols)) != len(marker_cols):
        errors.append("marker columns must be distinct")
    for left_index, (left_row, left_col) in enumerate(markers):
        for right_row, right_col in markers[left_index + 1 :]:
            if abs(left_row - right_row) < 2:
                errors.append(
                    "marker rows must be pairwise separated by at least two cells"
                )
                break
            if abs(left_col - right_col) < 2:
                errors.append(
                    "marker columns must be pairwise separated by at least two cells"
                )
                break
        if errors and errors[-1].startswith("marker ") and "pairwise" in errors[-1]:
            break

    return height, width, background, markers, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete ordinary input contract without mutating ``grid``."""
    del difficulty, meta
    return list(_analyze(grid)[-1])


def strict_canonical_like(grid) -> list[str]:
    """Require one of the four exact shape/count/background canonical profiles."""
    height, width, background, markers, errors = _analyze(grid)
    reasons = list(errors)
    if reasons:
        return reasons
    profile = (height, width, len(markers), background)
    if profile not in _CANONICAL_PROFILES:
        reasons.append(
            "strict canonical profile must be one of "
            f"{sorted(_CANONICAL_PROFILES)}, found {profile}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every public exact axis from a valid generated input."""
    height, width, background, markers, errors = _analyze(grid)
    if errors:
        raise ValueError(f"cannot observe overrides on invalid grid: {errors[0]}")
    assert background is not None
    return {
        "grid_h": height,
        "grid_w": width,
        "n_ones": len(markers),
        "bg_color": background,
    }


def _apply_markers(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
    markers: Iterable[tuple[int, int]],
    *,
    include_diagonals: bool,
) -> list[list[int]]:
    result = [list(row) for row in grid]
    height, width = len(result), len(result[0])
    for row, col in markers:
        for col_index in range(width):
            result[row][col_index] = 1
        for row_index in range(height):
            result[row_index][col] = 1
        result[row][col] = 2
        if include_diagonals:
            for row_delta, col_delta in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                diagonal_row = row + row_delta
                diagonal_col = col + col_delta
                if 0 <= diagonal_row < height and 0 <= diagonal_col < width:
                    result[diagonal_row][diagonal_col] = 3
    return result


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket rule for test evidence."""
    _height, _width, _background, markers, errors = _analyze(grid)
    if errors:
        raise ValueError(f"rule_mirror requires a valid input: {errors[0]}")
    return _apply_markers(grid, markers, include_diagonals=True)


def _first_marker_only(grid) -> list[list[int]]:
    _height, _width, _background, markers, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return _apply_markers(grid, markers[:1], include_diagonals=True)


def _cross_without_diagonals(grid) -> list[list[int]]:
    _height, _width, _background, markers, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return _apply_markers(grid, markers, include_diagonals=False)


def _background9_only(grid) -> list[list[int]]:
    _height, _width, background, _markers, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return rule_mirror(grid) if background == 9 else deepcopy(grid)


def _skip_edge_markers(grid) -> list[list[int]]:
    height, width, _background, markers, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    interior = [
        (row, col)
        for row, col in markers
        if 0 < row < height - 1 and 0 < col < width - 1
    ]
    return _apply_markers(grid, interior, include_diagonals=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "first_marker_only": _first_marker_only,
    "cross_without_diagonals": _cross_without_diagonals,
    "background9_only": _background9_only,
    "skip_edge_markers": _skip_edge_markers,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid: Any):
    height, width, background, markers, errors = _analyze(grid)
    if errors:
        return None
    return height, width, background, markers


def _witness_multiple_markers(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis[3]) >= 2)


def _witness_diagonal_stamp(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and _cross_without_diagonals(grid) != rule_mirror(grid))


def _witness_non_nine_background(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis[2] != 9)


def _witness_edge_marker(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    height, width, _background, markers = analysis
    return any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in markers
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "multiple_markers": _witness_multiple_markers,
    "diagonal_stamp": _witness_diagonal_stamp,
    "non_nine_background": _witness_non_nine_background,
    "edge_marker": _witness_edge_marker,
}
WITNESS_RIVALS = {
    "multiple_markers": ["first_marker_only"],
    "diagonal_stamp": ["cross_without_diagonals"],
    "non_nine_background": ["background9_only"],
    "edge_marker": ["skip_edge_markers"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check exact demonstrations and reject every named shortcut at query time."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
        return reasons
    expected_query = rule_mirror(query["input"])
    if "output" in query and query["output"] != expected_query:
        reasons.append("query output does not match the pinned rule")

    normalized_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        intended = rule_mirror(demo["input"])
        if demo["output"] != intended:
            reasons.append(f"demo {index} output does not match the pinned rule")
            continue
        normalized_demos.append(demo)

    if reasons:
        return reasons

    for name, rival in SEMANTIC_RIVALS.items():
        fits_all_demos = all(rival(demo["input"]) == demo["output"] for demo in normalized_demos)
        if fits_all_demos and rival(query["input"]) != expected_query:
            reasons.append(f"rival {name} fits every demo but disagrees with query")
    return reasons


def _scheduled_int(ctx, overrides: dict[str, Any], label: str, default: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, 7 if label != "n_ones" else 2,
                                   16 if label != "n_ones" else 4)
    return ctx.draw_choice(label, (default,))


def _scheduled_background(ctx, overrides: dict[str, Any], default: int) -> int:
    if "bg_color" in overrides and overrides["bg_color"] is not None:
        color = ctx.draw_color_strict("bg_color", exclude={1, 2, 3})
        if color not in _BACKGROUND_COLORS:
            raise ValueError(
                f"bg_color override {color} is illegal; expected one of {_BACKGROUND_COLORS}"
            )
        return color
    return ctx.draw_choice("bg_color", (default,))


def _spaced_combinations(size: int, count: int) -> list[tuple[int, ...]]:
    return [
        candidate
        for candidate in combinations(range(size), count)
        if all(right - left >= 2 for left, right in zip(candidate, candidate[1:]))
    ]


def _choose_coordinates(size: int, count: int, *, prefer_edge: bool, rng) -> tuple[int, ...]:
    candidates = _spaced_combinations(size, count)
    if prefer_edge:
        preferred = [
            candidate for candidate in candidates
            if candidate[0] == 0 or candidate[-1] == size - 1
        ]
    else:
        preferred = [
            candidate for candidate in candidates
            if candidate[0] > 0 and candidate[-1] < size - 1
        ]
    return rng.choice(preferred or candidates)


def _pick_markers(
    height: int,
    width: int,
    count: int,
    *,
    prefer_edge: bool,
    rng,
) -> list[tuple[int, int]]:
    rows = list(_choose_coordinates(height, count, prefer_edge=prefer_edge, rng=rng))
    cols = list(_choose_coordinates(width, count, prefer_edge=prefer_edge, rng=rng))

    if prefer_edge:
        edge_rows = [row for row in rows if row in (0, height - 1)]
        edge_cols = [col for col in cols if col in (0, width - 1)]
        if edge_rows and edge_cols:
            edge_row = rng.choice(edge_rows)
            edge_col = rng.choice(edge_cols)
            rows.remove(edge_row)
            cols.remove(edge_col)
            rng.shuffle(rows)
            rng.shuffle(cols)
            markers = [(edge_row, edge_col), *zip(rows, cols)]
        else:
            rng.shuffle(cols)
            markers = list(zip(rows, cols))
    else:
        rng.shuffle(cols)
        markers = list(zip(rows, cols))

    rng.shuffle(markers)
    return markers


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic ordinary input honoring every declared override."""
    index = _literal_nonnegative_int(sample_index, "sample_index")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    profile = schedule_profile(seed, index, difficulty)
    default_h, default_w, default_count, default_background, prefer_edge = _PROFILE_DEFAULTS[profile]

    ctx = gen_ctx(
        seed=seed,
        sample_index=index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, overrides, "grid_h", default_h)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w)
    count = _scheduled_int(ctx, overrides, "n_ones", default_count)
    background = _scheduled_background(ctx, overrides, default_background)
    rng = ctx.draw_rng(f"marker_layout:{difficulty or 'default'}")

    markers = _pick_markers(
        height,
        width,
        count,
        prefer_edge=prefer_edge,
        rng=rng,
    )
    grid = full_grid(height, width, background)
    for row, col in markers:
        grid[row][col] = 1

    errors = self_check(grid)
    if errors:  # Constructive generation should make this unreachable.
        raise RuntimeError(f"internal generator contract violation: {errors[0]}")
    return grid
