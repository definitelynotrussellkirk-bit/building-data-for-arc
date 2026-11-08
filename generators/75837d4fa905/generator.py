"""Generator for ARC task ``75837d4fa905`` (Square Corner Bloom).

Every nonzero object is a solid monochrome 2x2 square.  The output keeps the
squares and copies each square's colour to its four diagonal corner cells,
dropping corners outside the grid.  When two blooms target the same empty
cell, the first square encountered in row-major order wins, matching the
canonical Racket program.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75837d4fa905"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e56cca9b3b6c"

SUMMARY = (
    "Find every distinct-colour solid 2x2 square. Keep each square unchanged "
    "and paint its colour into the four diagonal corner cells one step beyond "
    "the square. Ignore corners outside the grid. If blooms overlap, the first "
    "square in row-major order owns a cell that was still background."
)

INVARIANTS = [
    "background is colour 0",
    "there are two to four distinct-colour solid monochrome 2x2 squares",
    "all in-bounds diagonal bloom targets are background in the input",
    "boundary squares are lawful and out-of-bounds bloom cells are clipped",
    "overlapping bloom targets are lawful; first row-major writer wins",
]

EXAMPLES_NEEDED = 3

# Every public axis is exact and recoverable from the returned grid through
# observe_overrides().  The full finite boundary matrix is constructible.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled/profile-aware", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "scheduled/profile-aware", "valid": "8..18"},
    "n_squares": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# (height, width, nonzero square count).  These reproduce every canonical
# input profile (palette size is n_squares + background).
_CANONICAL_PROFILES = (
    (8, 10, 2),
    (9, 9, 2),
    (10, 10, 3),
    (10, 11, 3),
)
_PROFILE_PERIOD = 6
_DIAGONALS = ((-1, -1), (-1, 2), (2, -1), (2, 2))


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if not isinstance(row, (list, tuple)):
            raise ValueError("every grid row must be a sequence")
        values = list(row)
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        for value in values:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("grid colours must be integers in 0..9")
            if value < 0 or value > 9:
                raise ValueError("grid colours must be integers in 0..9")
        rows.append(values)
    return rows


def _square_cells(row: int, col: int) -> set[tuple[int, int]]:
    return {
        (row, col),
        (row, col + 1),
        (row + 1, col),
        (row + 1, col + 1),
    }


def _targets(row: int, col: int) -> tuple[tuple[int, int], ...]:
    return tuple((row + dr, col + dc) for dr, dc in _DIAGONALS)


def _in_bounds(row: int, col: int, height: int, width: int) -> bool:
    return 0 <= row < height and 0 <= col < width


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    height, width = len(values), len(values[0])
    errors: list[str] = []
    if height < 7 or width < 8:
        errors.append(f"grid {height}x{width} is smaller than the 7x8 teaching domain")
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")

    by_colour: dict[int, list[tuple[int, int]]] = {}
    for row, values_row in enumerate(values):
        for col, colour in enumerate(values_row):
            if colour:
                by_colour.setdefault(colour, []).append((row, col))

    if len(by_colour) < 2:
        errors.append(f"found {len(by_colour)} nonzero colours, expected at least 2 squares")
    if len(by_colour) > 4:
        errors.append(f"found {len(by_colour)} nonzero colours, expected at most 4")

    squares: list[dict[str, Any]] = []
    for colour, cells_list in sorted(by_colour.items()):
        cells = set(cells_list)
        if len(cells) != 4:
            errors.append(
                f"colour {colour} has {len(cells)} cells, expected exactly one solid 2x2 square"
            )
            continue
        rows = sorted({row for row, _ in cells})
        cols = sorted({col for _, col in cells})
        if (
            len(rows) != 2
            or rows[1] != rows[0] + 1
            or len(cols) != 2
            or cols[1] != cols[0] + 1
            or cells != _square_cells(rows[0], cols[0])
        ):
            errors.append(f"colour {colour} does not form one solid 2x2 square")
            continue
        squares.append(
            {
                "row": rows[0],
                "col": cols[0],
                "colour": colour,
                "cells": cells,
            }
        )

    squares.sort(key=lambda square: (square["row"], square["col"]))
    for square in squares:
        row, col = square["row"], square["col"]
        for target_row, target_col in _targets(row, col):
            if (
                _in_bounds(target_row, target_col, height, width)
                and values[target_row][target_col] != 0
            ):
                errors.append(
                    "diagonal bloom target "
                    f"({target_row}, {target_col}) for square at ({row}, {col}) "
                    "is nonzero in the input"
                )

    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "squares": squares,
        "n_squares": len(squares),
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors

    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = observe_overrides(grid)
    for axis, value in requested.items():
        if axis in observed and observed[axis] != value:
            errors.append(f"meta {axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_squares": analysis["n_squares"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    profile = (analysis["height"], analysis["width"], analysis["n_squares"])
    if profile not in _CANONICAL_PROFILES:
        return [
            "profile is not one of the four canonical "
            f"(height, width, square-count) profiles: {profile}"
        ]
    return []


def _apply_bloom(analysis: dict[str, Any], *, interior_only: bool) -> list[list[int]]:
    output = [row[:] for row in analysis["grid"]]
    height, width = analysis["height"], analysis["width"]
    for square in analysis["squares"]:
        targets = _targets(square["row"], square["col"])
        if interior_only and not all(
            _in_bounds(row, col, height, width) for row, col in targets
        ):
            continue
        for row, col in targets:
            if _in_bounds(row, col, height, width) and output[row][col] == 0:
                output[row][col] = square["colour"]
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    return _apply_bloom(_analysis_or_raise(grid), interior_only=False)


def _rival_interior_only(grid) -> list[list[int]]:
    """Plausible canonical shortcut: skip any square whose bloom is clipped."""
    return _apply_bloom(_analysis_or_raise(grid), interior_only=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "interior_only": _rival_interior_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _clipped_boundary_bloom(grid) -> bool:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return False
    height, width = analysis["height"], analysis["width"]
    clipped = any(
        any(not _in_bounds(row, col, height, width) for row, col in _targets(square["row"], square["col"]))
        for square in analysis["squares"]
    )
    return clipped and _apply_bloom(analysis, interior_only=False) != _apply_bloom(
        analysis, interior_only=True
    )


SEMANTIC_WITNESSES = {
    "clipped_boundary_bloom": _clipped_boundary_bloom,
}
WITNESS_RIVALS = {
    "clipped_boundary_bloom": ["interior_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when the labeled demonstrations leave a rival alive."""
    reasons: list[str] = []
    if not isinstance(demos, list):
        return ["demos must be a list of input/output pairs"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]

    normalized_demos: list[tuple[Any, list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} input violates teaching grammar: {structural[0]}")
            continue
        try:
            output = _coerce_grid(pair["output"])
        except ValueError as exc:
            reasons.append(f"demo {index} output is invalid: {exc}")
            continue
        if rule_mirror(pair["input"]) != output:
            reasons.append(f"demo {index} output disagrees with the corner-bloom rule")
            continue
        normalized_demos.append((pair["input"], output))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input violates teaching grammar: {query_errors[0]}")
        query_expected: list[list[int]] | None = None
    else:
        query_expected = rule_mirror(query["input"])
        if "output" in query:
            try:
                supplied = _coerce_grid(query["output"])
            except ValueError as exc:
                reasons.append(f"query output is invalid: {exc}")
            else:
                if supplied != query_expected:
                    reasons.append("query output disagrees with the corner-bloom rule")
                query_expected = supplied

    if reasons or query_expected is None:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(grid) == output for grid, output in normalized_demos)
        if survives and competitor(query["input"]) != query_expected:
            reasons.append(
                f"competing rule {name!r} fits every demo but answers the query differently"
            )
    return reasons


def _validate_overrides(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")
    bounds = {
        "grid_h": (7, 16),
        "grid_w": (8, 18),
        "n_squares": (2, 4),
    }
    for axis, value in overrides.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {axis} must be an integer")
        low, high = bounds[axis]
        if not low <= value <= high:
            raise ValueError(f"override {axis}={value} is outside {low}..{high}")


def _default_axes(ctx, sample_index: int, difficulty: str | None, overrides: dict[str, Any]):
    profile_index = sample_index % _PROFILE_PERIOD
    profile = _CANONICAL_PROFILES[profile_index] if profile_index < len(_CANONICAL_PROFILES) else None

    if "grid_h" in overrides:
        height = ctx.draw_int("grid_h", 7, 16)
    elif profile is not None:
        height = ctx.draw_choice("grid_h", (profile[0],))
    else:
        low, high = {
            "easy": (7, 10),
            "medium": (9, 13),
            "hard": (12, 16),
            None: (9, 13),
        }[difficulty]
        height = ctx.draw_int("grid_h", low, high)

    if "grid_w" in overrides:
        width = ctx.draw_int("grid_w", 8, 18)
    elif profile is not None:
        width = ctx.draw_choice("grid_w", (profile[1],))
    else:
        low, high = {
            "easy": (8, 12),
            "medium": (10, 15),
            "hard": (14, 18),
            None: (10, 15),
        }[difficulty]
        width = ctx.draw_int("grid_w", low, high)

    if "n_squares" in overrides:
        count = ctx.draw_int("n_squares", 2, 4)
    elif profile is not None:
        count = ctx.draw_choice("n_squares", (profile[2],))
    else:
        low, high = {
            "easy": (2, 2),
            "medium": (2, 3),
            "hard": (3, 4),
            None: (2, 3),
        }[difficulty]
        count = ctx.draw_int("n_squares", low, high)

    return height, width, count


def _anchor_support(row: int, col: int, height: int, width: int) -> set[tuple[int, int]]:
    support = _square_cells(row, col)
    support.update(
        (target_row, target_col)
        for target_row, target_col in _targets(row, col)
        if _in_bounds(target_row, target_col, height, width)
    )
    return support


def _touches_boundary(row: int, col: int, height: int, width: int) -> bool:
    return row == 0 or col == 0 or row + 1 == height - 1 or col + 1 == width - 1


def _construct_anchors(height: int, width: int, count: int, mode: str, rng) -> list[tuple[int, int]]:
    candidates = [(row, col) for row in range(height - 1) for col in range(width - 1)]
    edges = [
        anchor for anchor in candidates if _touches_boundary(anchor[0], anchor[1], height, width)
    ]
    edge_set = set(edges)
    interiors = [anchor for anchor in candidates if anchor not in edge_set]
    rng.shuffle(edges)
    rng.shuffle(interiors)

    require_edge = mode == "edge"
    if mode == "interior":
        ordered = interiors + edges
    elif mode == "edge":
        ordered = edges + interiors
    else:
        ordered = candidates[:]
        rng.shuffle(ordered)

    # Randomized greedy restarts are fast for these tiny counts and dimensions.
    for _ in range(160):
        trial = ordered[:]
        rng.shuffle(trial)
        if mode == "edge":
            trial.sort(key=lambda anchor: not _touches_boundary(anchor[0], anchor[1], height, width))
        elif mode == "interior":
            trial.sort(key=lambda anchor: _touches_boundary(anchor[0], anchor[1], height, width))
        selected: list[tuple[int, int]] = []
        occupied: set[tuple[int, int]] = set()
        has_edge = False
        for row, col in trial:
            support = _anchor_support(row, col, height, width)
            if support & occupied:
                continue
            selected.append((row, col))
            occupied.update(support)
            has_edge = has_edge or _touches_boundary(row, col, height, width)
            if len(selected) == count:
                if not require_edge or has_edge:
                    return sorted(selected)
                break

    # Four corner squares are support-disjoint throughout the public domain and
    # provide a constructive total fallback for every advertised boundary.
    corners = [(0, 0), (0, width - 2), (height - 2, 0), (height - 2, width - 2)]
    fallback = corners[:count]
    occupied: set[tuple[int, int]] = set()
    for row, col in fallback:
        support = _anchor_support(row, col, height, width)
        if support & occupied:
            raise AssertionError("corner fallback unexpectedly overlaps")
        occupied.update(support)
    return sorted(fallback)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, count = _default_axes(ctx, sample_index, difficulty, overrides)
    layout_rng = ctx.draw_rng("layout")
    # Every four-pair lesson contains two guaranteed clipped-boundary witnesses,
    # so holding out any one pair still leaves the canonical-only interior rival refuted.
    mode = "edge" if sample_index % 2 == 0 else "interior"
    anchors = _construct_anchors(height, width, count, mode, layout_rng)
    colours = list(ctx.draw_distinct_colors("square_colours", n=count, exclude=(0,)))

    grid = full_grid(height, width, 0)
    for (row, col), colour in zip(anchors, colours):
        for square_row, square_col in _square_cells(row, col):
            grid[square_row][square_col] = colour

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator produced invalid task grid: " + "; ".join(errors))
    return grid
