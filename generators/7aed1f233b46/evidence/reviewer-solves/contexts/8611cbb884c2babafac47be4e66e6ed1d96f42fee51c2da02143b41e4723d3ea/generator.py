"""Generator for 7aed1f233b46: choose the color whose double closure is rectangular.

Each non-background color is an independent sparse candidate.  Row-close each
occupied row, then column-close the result.  Exactly one color becomes its full
bounding rectangle; crop that rectangle and recolor it cyan (8).

The public examples admit several shortcuts: choose color 2, the most populous
color, the largest bbox, the leftmost color, or the only four-cell color.  The
five-profile schedule keeps canonical-scale examples while placing explicit
counterexamples to each rival in every consecutive five-example lesson.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7aed1f233b46"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "20b242594e4b"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 24  # 4 heights x 6 widths; outputs are all-cyan rectangles.

SUMMARY = (
    "A canonical-scale zero-background grid contains three sparse colored "
    "candidates. Row-close then column-close each color independently; exactly "
    "one closure is a full rectangle. Output that rectangle as a tight cyan crop."
)

INVARIANTS = [
    "the input is one 8x12, 8x13, or 9x12 grid with background 0 and no dividers",
    "three ordinary colors form independent sparse candidates",
    "exactly one candidate's row-then-column closure equals its full bounding box",
    "the winning closure adds cells and is output as a tight all-cyan rectangle",
    "scheduled lessons include count, bbox, color, position, and four-cell shortcut counterexamples",
]

SCHEDULE_PROFILES = (
    "canonical_corners",
    "dense_decoy",
    "larger_decoy",
    "extra_winner",
    "position_decoy",
)

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "five-profile cycle keyed by sample_index",
        "valid": "|".join(SCHEDULE_PROFILES),
        "doc": "Observable shortcut-counterexample profile.",
    },
    "winner_height": {
        "type": "int",
        "default": "full-range deterministic draw",
        "valid": "3..6",
    },
    "winner_width": {
        "type": "int",
        "default": "full-range deterministic draw",
        "valid": "3..8",
    },
    "n_colors": {
        "type": "int",
        "default": "3",
        "valid": "3..4",
    },
    "winner_color": {
        "type": "int",
        "default": "profile-scheduled",
        "valid": "2..4",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
PALETTE_KINDS: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PROFILE_DIMS = {
    "canonical_corners": (8, 12),
    "dense_decoy": (8, 13),
    "larger_decoy": (9, 12),
    "extra_winner": (8, 12),
    "position_decoy": (9, 12),
}
_PROFILE_WINNER_COLOR = {
    "canonical_corners": 2,
    "dense_decoy": 3,
    "larger_decoy": 4,
    "extra_winner": 3,
    "position_decoy": 4,
}
_CANONICAL_INPUT_PROFILES = {(8, 12, 4), (8, 13, 4), (9, 12, 4)}
_ALLOWED_INPUT_COLORS = set(range(1, 8))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Deterministic five-slot lesson schedule; seed/band vary within each slot."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color {value!r} at {(row_index, col_index)}")
                return errors
    return errors


def _positions_by_color(grid: Sequence[Sequence[int]]) -> dict[int, tuple[tuple[int, int], ...]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                positions.setdefault(color, []).append((row, col))
    return {color: tuple(sorted(cells)) for color, cells in sorted(positions.items())}


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _bbox_cells(cells: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = _bbox(cells)
    return {(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)}


def _row_close(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    rows: dict[int, list[int]] = {}
    for row, col in cells:
        rows.setdefault(row, []).append(col)
    closed: set[tuple[int, int]] = set()
    for row, cols in rows.items():
        closed.update((row, col) for col in range(min(cols), max(cols) + 1))
    return closed


def _col_close(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cols: dict[int, list[int]] = {}
    for row, col in cells:
        cols.setdefault(col, []).append(row)
    closed: set[tuple[int, int]] = set()
    for col, rows in cols.items():
        closed.update((row, col) for row in range(min(rows), max(rows) + 1))
    return closed


def _double_close(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return _col_close(_row_close(cells))


def _record(color: int, cells: Sequence[tuple[int, int]]) -> dict[str, Any]:
    bbox = _bbox(cells)
    closed = _double_close(cells)
    bbox_set = _bbox_cells(cells)
    r1, c1, r2, c2 = bbox
    return {
        "color": color,
        "cells": tuple(sorted(cells)),
        "count": len(cells),
        "bbox": bbox,
        "height": r2 - r1 + 1,
        "width": c2 - c1 + 1,
        "bbox_area": len(bbox_set),
        "closed": tuple(sorted(closed)),
        "closure_count": len(closed),
        "is_rectangle": closed == bbox_set,
    }


def _classify_scene(records: Sequence[dict[str, Any]], winner: dict[str, Any] | None) -> str:
    if winner is None:
        return "unknown"
    decoys = [record for record in records if record is not winner]
    max_count = max((record["count"] for record in decoys), default=0)
    max_area = max((record["bbox_area"] for record in decoys), default=0)
    winner_count = winner["count"]
    winner_area = winner["bbox_area"]
    if winner_count == 6:
        return "extra_winner"
    if winner_count == 5 and max_count > 5 and max_area > winner_area:
        return "position_decoy"
    if winner_count == 4 and max_count == 5 and max_area <= winner_area:
        return "dense_decoy"
    if winner_count == 4 and max_count == 3 and max_area > winner_area:
        return "larger_decoy"
    return "canonical_corners"


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {
            "errors": errors,
            "height": 0,
            "width": 0,
            "palette": (),
            "records": (),
            "winners": (),
            "winner": None,
            "decoys": (),
            "scene_profile": "unknown",
        }
    height, width = len(grid), len(grid[0])
    positions = _positions_by_color(grid)
    records = tuple(_record(color, cells) for color, cells in positions.items())
    winners = tuple(record for record in records if record["is_rectangle"])
    winner = winners[0] if len(winners) == 1 else None
    decoys = tuple(record for record in records if record is not winner)
    return {
        "errors": [],
        "height": height,
        "width": width,
        "palette": tuple(positions),
        "records": records,
        "winners": winners,
        "winner": winner,
        "decoys": decoys,
        "scene_profile": _classify_scene(records, winner),
    }


def semantic_observables(grid) -> dict[str, Any]:
    """Pure structural diagnostics used by tests, gates, and future reviewers."""
    return _analysis(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful sparse-candidate grammar without mutating input."""
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    height, width = analysis["height"], analysis["width"]
    if not (6 <= height <= 12 and 8 <= width <= 18):
        errors.append(f"grid shape {height}x{width} is outside the task envelope")
    palette = set(analysis["palette"])
    if not 3 <= len(palette) <= 4:
        errors.append(f"expected three or four candidate colors, got {len(palette)}")
    illegal = sorted(palette - _ALLOWED_INPUT_COLORS)
    if illegal:
        errors.append(f"candidate colors must be in 1..7; found {illegal}")
    for record in analysis["records"]:
        if record["count"] < 3:
            errors.append(f"color {record['color']} has fewer than three evidence cells")
        if record["height"] < 2 or record["width"] < 2:
            errors.append(f"color {record['color']} must span at least two rows and columns")
    if len(analysis["winners"]) != 1:
        errors.append(
            f"expected exactly one rectangular double closure, got {len(analysis['winners'])}"
        )
    elif analysis["winner"]["closure_count"] <= analysis["winner"]["count"]:
        errors.append("winning closure adds no cells; the transformation is already explicit")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the public task's exact input shape/palette profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    profile = (
        analysis["height"],
        analysis["width"],
        len(analysis["palette"]) + 1,
    )
    if profile not in _CANONICAL_INPUT_PROFILES:
        return [f"input profile {profile} is not one of {sorted(_CANONICAL_INPUT_PROFILES)}"]
    return []


def _crop_cyan(record: dict[str, Any]):
    return full_grid(record["height"], record["width"], 8)


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket row-close/col-close rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"][0])
    if len(analysis["winners"]) != 1:
        raise ValueError(
            f"expected one winner, found {len(analysis['winners'])}"
        )
    return _crop_cyan(analysis["winner"])


def _rival_output(grid, key, *, reverse: bool = False):
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["records"]:
        raise ValueError("rival received an invalid or empty grid")
    chosen = sorted(analysis["records"], key=key, reverse=reverse)[0]
    return _crop_cyan(chosen)


def _rival_most_cells(grid):
    return _rival_output(grid, lambda record: (-record["count"], record["color"]))


def _rival_largest_bbox(grid):
    return _rival_output(grid, lambda record: (-record["bbox_area"], record["color"]))


def _rival_lowest_color(grid):
    return _rival_output(grid, lambda record: record["color"])


def _rival_leftmost(grid):
    return _rival_output(
        grid,
        lambda record: (record["bbox"][1], record["bbox"][0], record["color"]),
    )


def _rival_exactly_four(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["records"]:
        raise ValueError("rival received an invalid or empty grid")
    exact = [record for record in analysis["records"] if record["count"] == 4]
    chosen = min(exact or list(analysis["records"]), key=lambda record: record["color"])
    return _crop_cyan(chosen)


SEMANTIC_RIVALS = {
    "most_cells": _rival_most_cells,
    "largest_bbox": _rival_largest_bbox,
    "lowest_color": _rival_lowest_color,
    "leftmost": _rival_leftmost,
    "exactly_four": _rival_exactly_four,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness(name: str, grid) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "count_counterexample": lambda grid: _witness("most_cells", grid),
    "bbox_counterexample": lambda grid: _witness("largest_bbox", grid),
    "color_counterexample": lambda grid: _witness("lowest_color", grid),
    "position_counterexample": lambda grid: _witness("leftmost", grid),
    "four_cell_counterexample": lambda grid: _witness("exactly_four", grid),
}
WITNESS_RIVALS = {
    "count_counterexample": ["most_cells"],
    "bbox_counterexample": ["largest_bbox"],
    "color_counterexample": ["lowest_color"],
    "position_counterexample": ["leftmost"],
    "four_cell_counterexample": ["exactly_four"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is sufficient only when every named public-example rival loses."""
    del query
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"rival {name} still fits every demonstration")
    return reasons


def _corners(top: int, left: int, height: int, width: int) -> tuple[tuple[int, int], ...]:
    return (
        (top, left),
        (top, left + width - 1),
        (top + height - 1, left),
        (top + height - 1, left + width - 1),
    )


def _translate(local: Iterable[tuple[int, int]], top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + row, left + col) for row, col in local)


def _find_placement(
    local: Sequence[tuple[int, int]],
    bbox_height: int,
    bbox_width: int,
    grid_height: int,
    grid_width: int,
    occupied: set[tuple[int, int]],
    rng,
) -> tuple[tuple[int, int], ...]:
    for _ in range(300):
        top = rng.randint(0, grid_height - bbox_height)
        left = rng.randint(0, grid_width - bbox_width)
        cells = _translate(local, top, left)
        if occupied.isdisjoint(cells):
            return cells
    for top in range(grid_height - bbox_height + 1):
        for left in range(grid_width - bbox_width + 1):
            cells = _translate(local, top, left)
            if occupied.isdisjoint(cells):
                return cells
    raise RuntimeError("could not place a sparse candidate without cell overlap")


def _generic_decoy_local(rng) -> tuple[tuple[tuple[int, int], ...], int, int]:
    if rng.randrange(2) == 0:
        # Three corners of a 2x2 box.
        return ((0, 0), (0, 1), (1, 0)), 2, 2
    # A canonical T/L-like three-point candidate in a 2x3 box.
    return ((0, 0), (0, 2), (1, 0)), 2, 3


def _paint(grid, color: int, cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> None:
    for row, col in cells:
        if (row, col) in occupied:
            raise RuntimeError(f"cell collision at {(row, col)}")
        grid[row][col] = color
        occupied.add((row, col))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; valid axes: {', '.join(AXES)}"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    scheduled = schedule_profile(seed, sample_index, difficulty=difficulty)
    if ctx.overrides.get("scene_profile") is None:
        ctx.overrides["scene_profile"] = scheduled
    scene_profile = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    if ctx.overrides.get("n_colors") is None:
        ctx.overrides["n_colors"] = 3
    n_colors = ctx.draw_int("n_colors", 3, 4)
    if ctx.overrides.get("winner_color") is None:
        ctx.overrides["winner_color"] = _PROFILE_WINNER_COLOR[scene_profile]
    winner_color = ctx.draw_choice("winner_color", (2, 3, 4))
    winner_height = ctx.draw_int("winner_height", 3, 6)
    winner_width = ctx.draw_int("winner_width", 3, 8)

    height, width = _PROFILE_DIMS[scene_profile]
    rng = ctx.draw_rng(f"layout:{difficulty if difficulty is not None else 'none'}")
    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()

    distractor_colors = [
        color for color in (2, 3, 4, 5, 6, 7) if color != winner_color
    ][: n_colors - 1]

    if scene_profile in {"larger_decoy", "position_decoy"}:
        winner_top = height - winner_height
        winner_left = width - winner_width
    else:
        winner_top = rng.randint(0, height - winner_height)
        winner_left = rng.randint(0, width - winner_width)

    winner_cells = list(_corners(winner_top, winner_left, winner_height, winner_width))
    extra_count = 2 if scene_profile == "extra_winner" else 1 if scene_profile == "position_decoy" else 0
    if extra_count:
        available = [
            (row, col)
            for row in range(winner_top, winner_top + winner_height)
            for col in range(winner_left, winner_left + winner_width)
            if (row, col) not in winner_cells
        ]
        rng.shuffle(available)
        winner_cells.extend(available[:extra_count])

    first_decoy = distractor_colors[0]
    remaining_colors = distractor_colors[1:]

    if scene_profile == "larger_decoy":
        special = ((0, 0), (0, width - 1), (height - 1, 0))
        _paint(grid, first_decoy, special, occupied)
        _paint(grid, winner_color, winner_cells, occupied)
    elif scene_profile == "position_decoy":
        special = tuple((0, col) for col in range(width)) + tuple(
            (row, 0) for row in range(1, height)
        )
        _paint(grid, first_decoy, special, occupied)
        _paint(grid, winner_color, winner_cells, occupied)
    else:
        _paint(grid, winner_color, winner_cells, occupied)
        if scene_profile == "dense_decoy":
            local = tuple((0, col) for col in range(3)) + ((1, 0), (2, 0))
            cells = _find_placement(local, 3, 3, height, width, occupied, rng)
        else:
            local, box_h, box_w = _generic_decoy_local(rng)
            cells = _find_placement(local, box_h, box_w, height, width, occupied, rng)
        _paint(grid, first_decoy, cells, occupied)

    for color in remaining_colors:
        local, box_h, box_w = _generic_decoy_local(rng)
        cells = _find_placement(local, box_h, box_w, height, width, occupied, rng)
        _paint(grid, color, cells, occupied)

    findings = self_check(grid)
    if findings:
        raise RuntimeError(f"internal generator invariant failed: {findings}")
    return grid


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared semantic axis from the realized input."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["winner"] is None:
        raise ValueError("cannot observe axes on an invalid grid")
    winner = analysis["winner"]
    return {
        "scene_profile": analysis["scene_profile"],
        "winner_height": winner["height"],
        "winner_width": winner["width"],
        "n_colors": len(analysis["palette"]),
        "winner_color": winner["color"],
    }
