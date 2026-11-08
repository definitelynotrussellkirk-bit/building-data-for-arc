"""Canonical-linked generator for ARC task 2c00ca6ac44b.

Each non-background color forms one straight segment: a down-right diagonal, a
down-left diagonal, or (for one demonstrated profile) a horizontal segment on
the bottom row.  The answer is a 5x3 table whose non-background rows are the
segment colors sorted by each segment's topmost-leftmost start; unused rows are
background and appear first.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c00ca6ac44b"
TASK_ID = "2c00ca6ac44b"
VERSION = "3.0.0"
RULE_HASH = "f361d92f41e6"

BACKGROUND = 7
OUTPUT_HEIGHT = 5
OUTPUT_WIDTH = 3
ORIENT_DOWN_RIGHT = "down_right"
ORIENT_DOWN_LEFT = "down_left"
ORIENT_HORIZONTAL = "horizontal"
SCENE_PROFILES = ("diagonal_only", "with_horizontal")

SUMMARY = (
    "Create a background-7 grid containing 3-5 distinct colored straight "
    "segments. Every scene contains both down-right and down-left diagonals; "
    "the with_horizontal profile additionally contains exactly one contiguous "
    "horizontal segment on the bottom row. Segment starts have distinct rows. "
    "The 5x3 output is background-padded at the top, then repeats each segment "
    "color across one row in ascending order of that segment's topmost-leftmost "
    "start coordinate."
)

INVARIANTS = [
    "the cell at (0,0) and all unpainted cells are background color 7",
    "there are exactly 3-5 distinct non-background colors",
    "each foreground color forms exactly one contiguous straight segment of length at least 3",
    "allowed segment directions are down-right, down-left, and bottom-row horizontal",
    "both diagonal slopes occur and at most one horizontal segment occurs",
    "segment start rows are distinct, so the answer order is unambiguous",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-keyed draw over 12..24",
        "valid": "12..24",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-keyed draw over 12..24",
        "valid": "12..24",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-keyed draw over 3..5",
        "valid": "3..5",
    },
    "scene_profile": {
        "type": "str",
        "default": "keyed choice",
        "valid": "diagonal_only|with_horizontal",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh canonical-linked input grid."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 12, 24)
    width = ctx.draw_int_diff("grid_w", 12, 24)
    n_colors = ctx.draw_int_diff("n_colors", 3, 5)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    scene_rng = ctx.draw_rng("segment_layout")
    orientations = _orientation_schedule(n_colors, profile, scene_rng)
    segments = _place_segments(height, width, orientations, scene_rng)

    palette_rng = ctx.draw_rng("foreground_palette")
    colors = palette_rng.sample(
        [color for color in range(10) if color != BACKGROUND],
        n_colors,
    )
    # Decouple color identity from direction and start order, preventing a
    # direction-only or fixed-position shortcut from predicting the table.
    palette_rng.shuffle(colors)

    grid = full_grid(height, width, BACKGROUND)
    for color, segment in zip(colors, segments):
        for row, col in segment:
            grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # construction failure is a bug, never a silent fallback
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return [list(row) for row in grid]


def _orientation_schedule(n_colors: int, profile: str, rng) -> list[str]:
    if profile == "with_horizontal":
        orientations = [
            ORIENT_HORIZONTAL,
            ORIENT_DOWN_RIGHT,
            ORIENT_DOWN_LEFT,
        ]
        orientations.extend(
            rng.choice((ORIENT_DOWN_RIGHT, ORIENT_DOWN_LEFT))
            for _ in range(n_colors - 3)
        )
        # Place the constrained bottom row first, then vary diagonal order.
        diagonals = orientations[1:]
        rng.shuffle(diagonals)
        return [ORIENT_HORIZONTAL, *diagonals]

    orientations = [ORIENT_DOWN_RIGHT, ORIENT_DOWN_LEFT]
    orientations.extend(
        rng.choice((ORIENT_DOWN_RIGHT, ORIENT_DOWN_LEFT))
        for _ in range(n_colors - 2)
    )
    rng.shuffle(orientations)
    return orientations


def _place_segments(
    height: int,
    width: int,
    orientations: list[str],
    rng,
) -> list[list[tuple[int, int]]]:
    """Backtrack over straight-segment candidates until all fit exactly."""
    candidate_lists: list[list[list[tuple[int, int]]]] = []
    for orientation in orientations:
        candidates = _segment_candidates(height, width, orientation)
        slot_rng = rng
        # Prefer longer, canonical-like rays while retaining broad placement
        # support. Random jitter dominates ties and varies starts/lengths.
        candidates.sort(
            key=lambda cells: (
                slot_rng.random() + 0.28 * len(cells) / max(height, width)
            ),
            reverse=True,
        )
        candidate_lists.append(candidates)

    chosen: list[list[tuple[int, int]]] = []
    occupied: set[tuple[int, int]] = set()
    start_rows: set[int] = set()

    def search(index: int) -> bool:
        if index == len(orientations):
            return True
        # A generous deterministic cap keeps pathological searches bounded;
        # 12x12 boundary cases still have hundreds of legal choices per slot.
        for cells in candidate_lists[index][:1800]:
            start_row = cells[0][0]
            if start_row in start_rows or any(cell in occupied for cell in cells):
                continue
            chosen.append(cells)
            start_rows.add(start_row)
            occupied.update(cells)
            if search(index + 1):
                return True
            chosen.pop()
            start_rows.remove(start_row)
            occupied.difference_update(cells)
        return False

    if not search(0):
        raise RuntimeError(
            f"could not place {len(orientations)} canonical segments in "
            f"{height}x{width}"
        )
    return [list(cells) for cells in chosen]


def _segment_candidates(
    height: int,
    width: int,
    orientation: str,
) -> list[list[tuple[int, int]]]:
    candidates: list[list[tuple[int, int]]] = []
    if orientation == ORIENT_HORIZONTAL:
        row = height - 1
        for start_col in range(1, width - 2):
            for length in range(3, width - start_col + 1):
                candidates.append(
                    [(row, start_col + offset) for offset in range(length)]
                )
        return candidates

    for start_row in range(1, height - 2):
        if orientation == ORIENT_DOWN_RIGHT:
            columns = range(1, width - 2)
            step_col = 1
        elif orientation == ORIENT_DOWN_LEFT:
            columns = range(2, width - 1)
            step_col = -1
        else:
            raise ValueError(f"unknown segment orientation: {orientation!r}")
        for start_col in columns:
            vertical_room = height - start_row
            horizontal_room = (
                width - start_col if step_col == 1 else start_col + 1
            )
            max_length = min(vertical_room, horizontal_room)
            for length in range(3, max_length + 1):
                candidates.append(
                    [
                        (start_row + offset, start_col + step_col * offset)
                        for offset in range(length)
                    ]
                )
    return candidates


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Recover the full linked line grammar from a returned or canonical grid."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid is empty or not a list of rows"], "facts": {}}
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid rows are empty or non-rectangular"], "facts": {}}
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color value")
    if grid[0][0] != BACKGROUND:
        errors.append("background sentinel (0,0) is not color 7")

    colors = sorted(
        {value for row in grid for value in row if value != BACKGROUND}
    )
    if not 3 <= len(colors) <= 5:
        errors.append(
            f"expected 3..5 non-background colors, found {len(colors)}"
        )

    lines: list[dict[str, Any]] = []
    for color in colors:
        cells = sorted(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        )
        orientation = _classify_segment(cells)
        if len(cells) < 3:
            errors.append(f"color {color} has a segment shorter than 3 cells")
        if orientation is None:
            errors.append(
                f"color {color} does not form one contiguous allowed straight segment"
            )
        lines.append(
            {
                "color": color,
                "cells": tuple(cells),
                "start": cells[0] if cells else None,
                "length": len(cells),
                "orientation": orientation,
            }
        )

    starts = [line["start"] for line in lines if line["start"] is not None]
    if len({row for row, _ in starts}) != len(starts):
        errors.append("two segment starts share a row, making the lesson non-canonical")

    counts = Counter(line["orientation"] for line in lines)
    if counts[ORIENT_DOWN_RIGHT] < 1 or counts[ORIENT_DOWN_LEFT] < 1:
        errors.append("both diagonal slopes must occur")
    horizontal_lines = [
        line for line in lines if line["orientation"] == ORIENT_HORIZONTAL
    ]
    if len(horizontal_lines) > 1:
        errors.append("at most one horizontal segment is allowed")
    if horizontal_lines and horizontal_lines[0]["start"][0] != height - 1:
        errors.append("the horizontal segment must lie on the bottom row")

    if not horizontal_lines:
        profile = "diagonal_only"
    elif len(horizontal_lines) == 1:
        profile = "with_horizontal"
    else:
        profile = None

    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared canonical profile")

    ordered = sorted(
        lines,
        key=lambda line: line["start"] if line["start"] is not None else (999, 999),
    )
    facts = {
        "height": height,
        "width": width,
        "background": BACKGROUND,
        "colors": tuple(colors),
        "n_colors": len(colors),
        "lines": tuple(lines),
        "ordered_lines": tuple(ordered),
        "orientation_counts": dict(counts),
        "scene_profile": profile,
    }
    return {"errors": errors, "facts": facts}


def _classify_segment(cells: list[tuple[int, int]]) -> str | None:
    if len(cells) < 2:
        return None
    if all(row == cells[0][0] for row, _ in cells):
        columns = [col for _, col in cells]
        if columns == list(range(columns[0], columns[0] + len(columns))):
            return ORIENT_HORIZONTAL
        return None
    rows = [row for row, _ in cells]
    columns = [col for _, col in cells]
    if rows != list(range(rows[0], rows[0] + len(rows))):
        return None
    deltas = [right - left for left, right in zip(columns, columns[1:])]
    if deltas and all(delta == 1 for delta in deltas):
        return ORIENT_DOWN_RIGHT
    if deltas and all(delta == -1 for delta in deltas):
        return ORIENT_DOWN_LEFT
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, and shortcut-prone line scenes."""
    del difficulty, meta
    return list(analyze_scene(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact semantic axis from the returned grid."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_colors": facts["n_colors"],
        "scene_profile": facts["scene_profile"],
    }


def canonical_profile_signature(grid) -> str | None:
    """Return the demonstrated linked profile, or None for a near miss."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return None
    return analysis["facts"]["scene_profile"]


def semantic_signature(grid) -> tuple[Any, ...] | None:
    """Count-backed linked signature used by the review census."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts["scene_profile"],
        facts["n_colors"],
        tuple(sorted(facts["orientation_counts"].items())),
        tuple(line["orientation"] for line in facts["ordered_lines"]),
        tuple(line["length"] for line in facts["ordered_lines"]),
    )


def solve_python(grid) -> list[list[int]]:
    """Test-only mirror of the canonical Racket rule; never an oracle fallback."""
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    background = grid[0][0]
    colors = {
        value for row in grid for value in row if value != background
    }
    info = []
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        start = min(cells)
        info.append((start[0], start[1], color))
    info.sort()
    ordered_colors = [color for _, _, color in info]
    rows = [[background] * OUTPUT_WIDTH for _ in range(OUTPUT_HEIGHT - len(info))]
    rows.extend([[color] * OUTPUT_WIDTH for color in ordered_colors])
    return rows
