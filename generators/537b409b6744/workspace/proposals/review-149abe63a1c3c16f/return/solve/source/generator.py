"""Generator for 537b409b6744 — pass the nearest mover through its wall.

A modal background contains three differently colored parts.  A small solid
mover faces a wider/taller solid wall.  A farther distractor faces the same wall
and makes the rule's nearest-candidate ranking observable.  The output moves the
nearest object through the wall, cuts its channel, and grows the wall one cell
outward on both transverse sides.

The public axes describe only facts recoverable from returned pixels.  Default
sampling deliberately revisits the canonical 10x10/four-color profile while
varying background, orientation, dimensions, gap, palette, and distractor
solidity.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "537b409b6744"
TASK_ID = GENERATOR_ID
RULE_HASH = "7b81cecb3b71"
VERSION = "4.1.0"
SUMMARY = (
    "A modal background contains a solid mover, a larger solid facing wall, "
    "and a farther same-side distractor. The nearest qualifying mover passes "
    "through the wall; its channel is erased from the wall, and the wall grows "
    "transversely around that channel. Output dimensions are unchanged."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "exactly four colors: one unique modal background and three object colors",
    "exactly three same-color 4-connected parts",
    "the selected mover and wall are solid rectangles",
    "the wall is wider/taller than the mover and faces it along one axis",
    "generated helpful scenes contain a farther qualifying distractor",
    "the nearest candidate is unique and changing to the farther candidate changes the output",
]

DIRECTIONS = ("down", "up", "right", "left")
DISTRACTOR_KINDS = ("solid", "ragged")
AXES = {
    "grid_h": {
        "type": "int", "default": "10x10 canonical-profile schedule", "valid": "10..14",
    },
    "grid_w": {
        "type": "int", "default": "10x10 canonical-profile schedule", "valid": "10..14",
    },
    "direction": {
        "type": "str", "default": "four-way schedule", "valid": "down|up|right|left",
    },
    "mover_span": {
        "type": "int", "default": "varies", "valid": "1..2",
    },
    "mover_depth": {
        "type": "int", "default": "varies", "valid": "1..2",
    },
    "wall_extra": {
        "type": "int", "default": "varies", "valid": "2..3",
    },
    "wall_depth": {
        "type": "int", "default": "varies", "valid": "2..3",
    },
    "gap": {
        "type": "int", "default": "varies", "valid": "0..2",
    },
    "distractor_kind": {
        "type": "str", "default": "solid/ragged schedule", "valid": "solid|ragged",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


# ---------------------------------------------------------------------------
# Structural oracle shared by validation, override observation, and rivals.
# It mirrors the selected Racket program but is independently expressed in
# Python so generation can reject malformed scenes before they reach training.
# ---------------------------------------------------------------------------

def _mode_color(grid: list[list[int]]) -> int:
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    first = {value: flat.index(value) for value in counts}
    return max(counts, key=lambda value: (counts[value], -first[value]))


def _components(grid: list[list[int]], background: int | None = None) -> list[dict]:
    if background is None:
        background = _mode_color(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    parts: list[dict] = []
    for row in range(height):
        for column in range(width):
            if (row, column) in seen or grid[row][column] == background:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(columns), max(columns)
            obj = {
                "index": len(parts),
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "r1": r1,
                "r2": r2,
                "c1": c1,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            }
            obj["solid"] = obj["size"] == obj["h"] * obj["w"]
            parts.append(obj)
    return parts


def _overlap(a1: int, a2: int, b1: int, b2: int) -> bool:
    return a1 <= b2 and b1 <= a2


def _ranked_candidates(grid: list[list[int]]) -> list[dict]:
    parts = _components(grid, _mode_color(grid))
    candidates: list[dict] = []
    for mover in parts:
        for wall in parts:
            if mover is wall or not wall["solid"]:
                continue
            direction = None
            gap = None
            if (
                wall["r1"] > mover["r2"]
                and _overlap(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "down"
                gap = wall["r1"] - mover["r2"] - 1
            elif (
                mover["r1"] > wall["r2"]
                and _overlap(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "up"
                gap = mover["r1"] - wall["r2"] - 1
            elif (
                wall["c1"] > mover["c2"]
                and _overlap(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "right"
                gap = wall["c1"] - mover["c2"] - 1
            elif (
                mover["c1"] > wall["c2"]
                and _overlap(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "left"
                gap = mover["c1"] - wall["c2"] - 1
            if direction is not None:
                candidates.append(
                    {
                        "enumeration_index": len(candidates),
                        "gap": gap,
                        "wall_size": wall["size"],
                        "direction": direction,
                        "mover": mover,
                        "wall": wall,
                    }
                )
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["gap"],
            -candidate["wall_size"],
            candidate["enumeration_index"],
        ),
    )


def _put(grid: list[list[int]], row: int, column: int, value: int) -> None:
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        grid[row][column] = value


def _apply_candidate(
    grid: list[list[int]], candidate: dict, *, grow_wall: bool = True
) -> list[list[int]]:
    background = _mode_color(grid)
    mover = candidate["mover"]
    wall = candidate["wall"]
    direction = candidate["direction"]
    output = deepcopy(grid)
    mover_cells = [
        (row, column, grid[row][column]) for row, column in mover["cells"]
    ]
    for row, column, _ in mover_cells:
        output[row][column] = background

    if direction in ("down", "up"):
        for row in range(wall["r1"], wall["r2"] + 1):
            for column in range(mover["c1"], mover["c2"] + 1):
                _put(output, row, column, background)
        if grow_wall:
            padding = max(1, mover["w"] // 2)
            for row in range(wall["r1"], wall["r2"] + 1):
                for distance in range(1, padding + 1):
                    _put(output, row, wall["c1"] - distance, wall["color"])
                    _put(output, row, wall["c2"] + distance, wall["color"])
        destination_row = (
            max(0, wall["r1"] - mover["h"])
            if direction == "up"
            else (
                wall["r2"] - mover["h"] + 1
                if wall["r2"] == len(grid) - 1
                else wall["r2"] + 1
            )
        )
        destination_column = mover["c1"]
    else:
        for row in range(mover["r1"], mover["r2"] + 1):
            for column in range(wall["c1"], wall["c2"] + 1):
                _put(output, row, column, background)
        if grow_wall:
            padding = max(1, mover["h"] // 2)
            for column in range(wall["c1"], wall["c2"] + 1):
                for distance in range(1, padding + 1):
                    _put(output, wall["r1"] - distance, column, wall["color"])
                    _put(output, wall["r2"] + distance, column, wall["color"])
        destination_column = (
            max(0, wall["c1"] - mover["w"])
            if direction == "left"
            else (
                wall["c2"] - mover["w"] + 1
                if wall["c2"] == len(grid[0]) - 1
                else wall["c2"] + 1
            )
        )
        destination_row = mover["r1"]

    for row, column, value in mover_cells:
        _put(
            output,
            destination_row + row - mover["r1"],
            destination_column + column - mover["c1"],
            value,
        )
    return output


def _rule_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = _ranked_candidates(grid)
    return deepcopy(grid) if not candidates else _apply_candidate(grid, candidates[0])


def _farthest_candidate_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = _ranked_candidates(grid)
    return deepcopy(grid) if not candidates else _apply_candidate(grid, candidates[-1])


def _no_growth_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = _ranked_candidates(grid)
    return (
        deepcopy(grid)
        if not candidates
        else _apply_candidate(grid, candidates[0], grow_wall=False)
    )


def _smallest_mover_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical shortcut: move the smallest qualifying object."""
    candidates = _ranked_candidates(grid)
    if not candidates:
        return deepcopy(grid)
    selected = min(
        candidates,
        key=lambda candidate: (
            candidate["mover"]["size"],
            candidate["gap"],
            -candidate["wall_size"],
            candidate["enumeration_index"],
        ),
    )
    return _apply_candidate(grid, selected)


# ---------------------------------------------------------------------------
# Generator and observable public contract.
# ---------------------------------------------------------------------------

def _axis_int(ctx, overrides, name: str, lo: int, hi: int, default: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _axis_choice(ctx, overrides, name: str, options: tuple[str, ...], default: str) -> str:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _default_int(ctx, label: str, lo: int, hi: int) -> int:
    return ctx.draw_rng(label).randint(lo, hi)


def _draw_ragged_l(grid: list[list[int]], row: int, column: int, color: int) -> None:
    # Connected, 2x2 bounding box, exactly one missing corner.
    for dr, dc in ((0, 0), (1, 0), (1, 1)):
        grid[row + dr][column + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Every fourth default is exactly the canonical 10x10 profile.  Other
    # defaults cover the full advertised dimension range; explicit overrides
    # always retain the full domain in every difficulty band.
    core_profile = int(sample_index) % 4 == 0
    default_h = 10 if core_profile else _default_int(ctx, "grid_h_default", 10, 14)
    default_w = 10 if core_profile else _default_int(ctx, "grid_w_default", 10, 14)
    h = _axis_int(ctx, overrides, "grid_h", 10, 14, default_h)
    w = _axis_int(ctx, overrides, "grid_w", 10, 14, default_w)

    direction_default = DIRECTIONS[int(sample_index) % len(DIRECTIONS)]
    distractor_default = DISTRACTOR_KINDS[int(sample_index) % len(DISTRACTOR_KINDS)]
    direction = _axis_choice(ctx, overrides, "direction", DIRECTIONS, direction_default)
    mover_span = _axis_int(
        ctx, overrides, "mover_span", 1, 2,
        _default_int(ctx, "mover_span_default", 1, 2),
    )
    # Even default indices deliberately make the nearer mover larger than the
    # farther solid distractor.  This supplies a visible counterexample to the
    # canonical-fitting "move the smallest candidate" shortcut in every four-pair
    # episode and in every one-query rotation.  Explicit overrides remain exact.
    mover_depth_default = 2 if sample_index % 2 == 0 else 1
    mover_depth = _axis_int(
        ctx, overrides, "mover_depth", 1, 2, mover_depth_default,
    )
    wall_extra = _axis_int(
        ctx, overrides, "wall_extra", 2, 3,
        _default_int(ctx, "wall_extra_default", 2, 3),
    )
    wall_depth = _axis_int(
        ctx, overrides, "wall_depth", 2, 3,
        _default_int(ctx, "wall_depth_default", 2, 3),
    )
    band_gap = {"easy": 0, "medium": 1, "hard": 2}.get(
        difficulty, _default_int(ctx, "gap_default", 0, 2)
    )
    gap = _axis_int(ctx, overrides, "gap", 0, 2, band_gap)
    distractor_kind = _axis_choice(
        ctx, overrides, "distractor_kind", DISTRACTOR_KINDS, distractor_default,
    )

    # Background is a role, not color 0.  The core schedule deliberately emits
    # canonical background 7; the broad branch explores all ARC colors.
    background = 7 if core_profile else ctx.draw_rng("background").randrange(10)
    mover_color, wall_color, distractor_color = ctx.draw_distinct_colors(
        "role_colors", n=3, exclude={background}
    )
    grid = full_grid(h, w, background)
    wall_span = mover_span + wall_extra
    layout_rng = ctx.draw_rng("layout")
    distractor_depth = 1 if distractor_kind == "solid" else 2
    distractor_span = mover_span if distractor_kind == "solid" else 2

    if direction in ("down", "up"):
        wall_column = layout_rng.randint(1, w - wall_span - 1)
        mover_column = layout_rng.randint(
            wall_column, wall_column + wall_span - mover_span
        )
        distractor_column = layout_rng.randint(
            wall_column, wall_column + wall_span - distractor_span
        )
        if direction == "down":
            wall_row = h - wall_depth
            mover_row = wall_row - gap - mover_depth
            distractor_row = mover_row - distractor_depth
        else:
            wall_row = 0
            mover_row = wall_depth + gap
            distractor_row = mover_row + mover_depth

        draw_rect(grid, wall_row, wall_column, wall_depth, wall_span, wall_color)
        draw_rect(grid, mover_row, mover_column, mover_depth, mover_span, mover_color)
        if distractor_kind == "solid":
            draw_rect(
                grid,
                distractor_row,
                distractor_column,
                distractor_depth,
                distractor_span,
                distractor_color,
            )
        else:
            _draw_ragged_l(grid, distractor_row, distractor_column, distractor_color)
    else:
        wall_row = layout_rng.randint(1, h - wall_span - 1)
        mover_row = layout_rng.randint(wall_row, wall_row + wall_span - mover_span)
        distractor_row = layout_rng.randint(
            wall_row, wall_row + wall_span - distractor_span
        )
        if direction == "right":
            wall_column = w - wall_depth
            mover_column = wall_column - gap - mover_depth
            distractor_column = mover_column - distractor_depth
        else:
            wall_column = 0
            mover_column = wall_depth + gap
            distractor_column = mover_column + mover_depth

        draw_rect(grid, wall_row, wall_column, wall_span, wall_depth, wall_color)
        draw_rect(grid, mover_row, mover_column, mover_span, mover_depth, mover_color)
        if distractor_kind == "solid":
            draw_rect(
                grid,
                distractor_row,
                distractor_column,
                distractor_span,
                distractor_depth,
                distractor_color,
            )
        else:
            _draw_ragged_l(grid, distractor_row, distractor_column, distractor_color)

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid 537b409b6744 scene: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact public axis from returned pixels."""
    candidates = _ranked_candidates(grid)
    if not candidates:
        raise ValueError("grid has no qualifying mover/wall candidate")
    selected = candidates[0]
    mover, wall = selected["mover"], selected["wall"]
    parts = _components(grid, _mode_color(grid))
    distractors = [
        obj
        for obj in parts
        if obj["index"] not in (mover["index"], wall["index"])
    ]
    if len(distractors) != 1:
        raise ValueError(f"expected one distractor, found {len(distractors)}")
    distractor = distractors[0]
    vertical = selected["direction"] in ("down", "up")
    mover_span = mover["w"] if vertical else mover["h"]
    mover_depth = mover["h"] if vertical else mover["w"]
    wall_span = wall["w"] if vertical else wall["h"]
    wall_depth = wall["h"] if vertical else wall["w"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "direction": selected["direction"],
        "mover_span": mover_span,
        "mover_depth": mover_depth,
        "wall_extra": wall_span - mover_span,
        "wall_depth": wall_depth,
        "gap": selected["gap"],
        "distractor_kind": "solid" if distractor["solid"] else "ragged",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical scene grammar and reject structural corruption."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors: list[str] = []
    height = len(grid)
    if height < 6 or width < 6:
        errors.append(f"grid {height}x{width} is too small for the rule")
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 4:
        errors.append(f"expected exactly four colors, found {len(counts)}")
    if counts:
        largest = max(counts.values())
        modes = [color for color, count in counts.items() if count == largest]
        if len(modes) != 1:
            errors.append("background must be the unique modal color")
    background = _mode_color(grid)
    parts = _components(grid, background)
    if len(parts) != 3:
        errors.append(f"expected exactly three non-background parts, found {len(parts)}")

    candidates = _ranked_candidates(grid)
    if not candidates:
        errors.append("no qualifying mover/wall pair")
        return errors
    selected = candidates[0]
    mover, wall = selected["mover"], selected["wall"]
    if not mover["solid"]:
        errors.append("selected mover must be a solid rectangle")
    if not wall["solid"]:
        errors.append("selected wall must be a solid rectangle")
    if len(candidates) > 1:
        first_key = (candidates[0]["gap"], -candidates[0]["wall_size"])
        second_key = (candidates[1]["gap"], -candidates[1]["wall_size"])
        if first_key == second_key:
            errors.append("nearest candidate must be unique before enumeration tie-break")

    output = _rule_output(grid)
    if output == [list(row) for row in grid]:
        errors.append("selected rule must change the grid")
    input_mover_count = counts[mover["color"]]
    output_mover_count = sum(value == mover["color"] for row in output for value in row)
    if output_mover_count != input_mover_count:
        errors.append("rule must preserve the selected mover color count")
    if len(output) != height or any(len(row) != width for row in output):
        errors.append("rule must preserve grid dimensions")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


# ---------------------------------------------------------------------------
# Explicit wrong hypotheses for lesson and semantic gates.
# ---------------------------------------------------------------------------

def _witness_nearest_pair(grid) -> bool:
    candidates = _ranked_candidates(grid)
    return (
        len(candidates) >= 2
        and candidates[0]["gap"] < candidates[-1]["gap"]
        and _rule_output(grid) != _farthest_candidate_output(grid)
    )


def _witness_wall_growth(grid) -> bool:
    return bool(_ranked_candidates(grid)) and _rule_output(grid) != _no_growth_output(grid)


def _witness_smallest_mover(grid) -> bool:
    return bool(_ranked_candidates(grid)) and _rule_output(grid) != _smallest_mover_output(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "nearest_pair": _witness_nearest_pair,
    "wall_growth": _witness_wall_growth,
    "smallest_mover": _witness_smallest_mover,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "farthest_pair": _farthest_candidate_output,
    "no_wall_growth": _no_growth_output,
    "smallest_mover": _smallest_mover_output,
}
WITNESS_RIVALS = {
    "nearest_pair": ["farthest_pair"],
    "wall_growth": ["no_wall_growth"],
    "smallest_mover": ["smallest_mover"],
}
# Every labeled canonical pair selects the smallest qualifying mover, so this
# alternative cannot be rejected from canonical data alone.  The generated
# schedule includes larger-near/smaller-far counterexamples in every lesson.
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "smallest_mover": _smallest_mover_output,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    del query
    survivors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    if survivors:
        return [
            "demos do not refute declared competitor(s): "
            + ", ".join(sorted(survivors))
        ]
    return []
