"""Generator for arc_additional_puzzles_21_set7:M44.

A hollow rectangular frame contains two differently colored cells on one row.
The left cell names the color at the frame interior's top-left corner; the
right cell names the alternating color.  The Racket authority fills the strict
interior as a checkerboard and preserves the frame.

The three-slot teaching schedule deliberately includes the canonical top-left
adjacent pair, an adjacent pair shifted away from the corner, and a separated
left/right pair.  Every seed lies on the checkerboard parity matching its
color, so generated "seeds" are never relabeled by the output.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "78cc0b96bc87"
TASK_ID = "78cc0b96bc87"
VERSION = "2.1.0"
# sha256[:12] of the whitespace-normalized selected canonical Racket rule.
RULE_HASH = "5ed55d63a700"

SUMMARY = (
    "One hollow rectangular frame on a zero background contains exactly two "
    "distinct seed colors on one row. The left seed anchors the top-left "
    "interior color, the right seed is the alternating color, and both seeds "
    "already agree with the checkerboard parity they demonstrate."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input is a rectangular ARC grid with background color 0",
    "exactly one non-zero object is a complete rectangular frame at least 4x4",
    "there are no non-zero cells outside that frame",
    "the strict interior contains exactly two cells of distinct non-frame colors",
    "the two seeds share a row; the left seed has even interior parity and the right seed has odd parity",
]

SEED_LAYOUTS = ("canonical_pair", "shifted_pair", "spaced_pair")
SCHEDULE_PROFILES = SEED_LAYOUTS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 8..10",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 10..12",
        "valid": "10..12",
    },
    "frame_h": {
        "type": "int",
        "default": "difficulty-weighted 6..8",
        "valid": "6..8",
    },
    "frame_w": {
        "type": "int",
        "default": "difficulty-weighted 6..9",
        "valid": "6..9",
    },
    "seed_layout": {
        "type": "enum",
        "default": "scheduled canonical_pair,shifted_pair,spaced_pair",
        "valid": "canonical_pair|shifted_pair|spaced_pair",
    },
}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return difficulty


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name, lo, hi in (
        ("grid_h", 8, 10),
        ("grid_w", 10, 12),
        ("frame_h", 6, 8),
        ("frame_w", 6, 9),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name} must be an integer, got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"override {name} must be in {lo}..{hi}, got {value}")

    if "seed_layout" in overrides and overrides["seed_layout"] is not None:
        value = overrides["seed_layout"]
        if value not in SEED_LAYOUTS:
            raise ValueError(
                f"override seed_layout must be one of {SEED_LAYOUTS}, got {value!r}"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the three-slot schedule used by every sliding demo window."""
    del seed, difficulty
    return SEED_LAYOUTS[sample_index % len(SEED_LAYOUTS)]


def _scheduled_layout(ctx, sample_index: int) -> str:
    if "seed_layout" in ctx.overrides and ctx.overrides["seed_layout"] is not None:
        return ctx.draw_choice("seed_layout", SEED_LAYOUTS)
    scheduled = schedule_profile(ctx.seed, sample_index, ctx.difficulty)
    return ctx.draw_choice("seed_layout", (scheduled,))


def _frame_candidate(grid: Sequence[Sequence[int]], color: int):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    if not cells:
        return None
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    frame_h, frame_w = bottom - top + 1, right - left + 1
    if frame_h < 4 or frame_w < 4:
        return None
    border = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    if cells != border:
        return None
    return {
        "color": color,
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "cells": border,
    }


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return {}, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions must be in 1..30, got {len(grid)}x{width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {}, errors + ["grid values must be integer ARC colors 0..9"]

    candidates = [
        candidate
        for color in range(1, 10)
        if (candidate := _frame_candidate(grid, color)) is not None
    ]
    if len(candidates) != 1:
        errors.append(f"expected exactly one complete rectangular frame, got {len(candidates)}")
        return {}, errors

    frame = candidates[0]
    top, left = frame["top"], frame["left"]
    bottom, right = frame["bottom"], frame["right"]

    outside = [
        (row, col, grid[row][col])
        for row in range(len(grid))
        for col in range(width)
        if grid[row][col] != 0
        and not (top <= row <= bottom and left <= col <= right)
    ]
    if outside:
        errors.append(f"found {len(outside)} non-zero cell(s) outside the frame")

    seeds = [
        (row, col, grid[row][col])
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if grid[row][col] != 0
    ]
    seeds.sort()
    if len(seeds) != 2:
        errors.append(f"strict interior must contain exactly two seed cells, got {len(seeds)}")
        return {}, errors

    first, second = seeds
    first_row, first_col, first_color = first
    second_row, second_col, second_color = second
    if first_color == second_color:
        errors.append("the two seed colors must be distinct")
    if frame["color"] in (first_color, second_color):
        errors.append("seed colors must differ from the frame color")
    if first_row != second_row:
        errors.append("the two seeds must share one row so left/right order is visible")
    if first_col >= second_col:
        errors.append("the first seed must be strictly left of the second seed")

    first_parity = ((first_row - (top + 1)) + (first_col - (left + 1))) % 2
    second_parity = ((second_row - (top + 1)) + (second_col - (left + 1))) % 2
    if first_parity != 0:
        errors.append("the left seed must lie on even parity from the interior top-left")
    if second_parity != 1:
        errors.append("the right seed must lie on odd parity from the interior top-left")

    rel_first = (first_row - (top + 1), first_col - (left + 1))
    rel_second = (second_row - (top + 1), second_col - (left + 1))
    gap = second_col - first_col
    if rel_first == (0, 0) and rel_second == (0, 1):
        seed_layout = "canonical_pair"
    elif gap == 1:
        seed_layout = "shifted_pair"
    elif gap >= 3 and gap % 2 == 1:
        seed_layout = "spaced_pair"
    else:
        errors.append(
            "seed pair must be adjacent or separated by a positive odd horizontal gap"
        )
        seed_layout = "invalid"

    facts = {
        "height": len(grid),
        "width": width,
        "frame": frame,
        "frame_color": frame["color"],
        "frame_h": frame["frame_h"],
        "frame_w": frame["frame_w"],
        "seeds": tuple(seeds),
        "left_seed": first,
        "right_seed": second,
        "left_color": first_color,
        "right_color": second_color,
        "seed_layout": seed_layout,
        "seed_gap": gap,
        "outside_nonzero": tuple(outside),
    }
    return facts, errors


def _checkerboard_output(
    grid: Sequence[Sequence[int]], *, top_left_color: int, alternate_color: int
) -> list[list[int]]:
    facts, errors = _analyze([list(row) for row in grid])
    if errors:
        raise ValueError("; ".join(errors))
    frame = facts["frame"]
    output = full_grid(facts["height"], facts["width"], 0)
    draw_frame(
        output,
        frame["top"],
        frame["left"],
        frame["bottom"],
        frame["right"],
        frame["color"],
    )
    for row in range(frame["top"] + 1, frame["bottom"]):
        for col in range(frame["left"] + 1, frame["right"]):
            parity = (
                row - (frame["top"] + 1) + col - (frame["left"] + 1)
            ) % 2
            output[row][col] = top_left_color if parity == 0 else alternate_color
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    facts, errors = _analyze([list(row) for row in grid])
    if errors:
        raise ValueError("; ".join(errors))
    return _checkerboard_output(
        grid,
        top_left_color=facts["left_color"],
        alternate_color=facts["right_color"],
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed frames, ambiguous seed cues, and parity-inconsistent seeds."""
    del difficulty, meta
    _facts, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical frame/checkerboard teaching manifold."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if not (8 <= facts["height"] <= 10 and 10 <= facts["width"] <= 12):
        reasons.append(
            f"canonical canvas envelope is 8..10 by 10..12, got "
            f"{facts['height']}x{facts['width']}"
        )
    if not 6 <= facts["frame_h"] <= 8:
        reasons.append(f"canonical frame height support is 6..8, got {facts['frame_h']}")
    if not 6 <= facts["frame_w"] <= 9:
        reasons.append(f"canonical frame width support is 6..9, got {facts['frame_w']}")
    return reasons


def observe_overrides(grid) -> dict[str, int | str | None]:
    """Recover every declared exact axis from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        return {name: None for name in AXES}
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "frame_h": facts["frame_h"],
        "frame_w": facts["frame_w"],
        "seed_layout": facts["seed_layout"],
    }


def _seed_positions(
    layout: str, interior_h: int, interior_w: int, rng
) -> tuple[tuple[int, int], tuple[int, int]]:
    if layout == "canonical_pair":
        return (0, 0), (0, 1)

    if layout == "shifted_pair":
        candidates = [
            ((row, col), (row, col + 1))
            for row in range(interior_h)
            for col in range(interior_w - 1)
            if (row + col) % 2 == 0 and (row, col) != (0, 0)
        ]
    elif layout == "spaced_pair":
        candidates = [
            ((row, left), (row, right))
            for row in range(interior_h)
            for left in range(interior_w)
            for right in range(left + 3, interior_w, 2)
            if (row + left) % 2 == 0
        ]
    else:  # guarded by _validate_overrides / scheduled domain
        raise ValueError(f"unsupported seed layout: {layout!r}")

    if not candidates:
        raise RuntimeError(
            f"no legal {layout} placement in {interior_h}x{interior_w} interior"
        )
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    height = ctx.draw_int_diff("grid_h", 8, 10)
    width = ctx.draw_int_diff("grid_w", 10, 12)
    frame_h = ctx.draw_int_diff("frame_h", 6, 8)
    frame_w = ctx.draw_int_diff("frame_w", 6, 9)
    layout = _scheduled_layout(ctx, sample_index)

    slot = sample_index % len(SEED_LAYOUTS)
    row_slack = height - frame_h
    col_slack = width - frame_w
    frame_top = (0, row_slack // 2, row_slack)[slot]
    frame_left = (0, col_slack // 2, col_slack)[slot]
    frame_bottom = frame_top + frame_h - 1
    frame_right = frame_left + frame_w - 1

    palette_rng = ctx.draw_rng("palette")
    frame_color, seed_a, seed_b = palette_rng.sample(list(range(1, 10)), 3)
    if slot == 0:
        left_color, right_color = sorted((seed_a, seed_b))
    elif slot == 1:
        left_color, right_color = sorted((seed_a, seed_b), reverse=True)
    else:
        left_color, right_color = seed_a, seed_b

    grid = full_grid(height, width, 0)
    draw_frame(
        grid,
        frame_top,
        frame_left,
        frame_bottom,
        frame_right,
        frame_color,
    )
    seed_rng = ctx.draw_rng("seed_positions")
    (left_row, left_col), (right_row, right_col) = _seed_positions(
        layout, frame_h - 2, frame_w - 2, seed_rng
    )
    grid[frame_top + 1 + left_row][frame_left + 1 + left_col] = left_color
    grid[frame_top + 1 + right_row][frame_left + 1 + right_col] = right_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid checkerboard lesson: " + "; ".join(errors))
    return grid


def _rival_right_seed_phase(grid):
    facts, errors = _analyze(grid)
    if errors:
        return [list(row) for row in grid]
    return _checkerboard_output(
        grid,
        top_left_color=facts["right_color"],
        alternate_color=facts["left_color"],
    )


def _rival_solid_left_color(grid):
    facts, errors = _analyze(grid)
    if errors:
        return [list(row) for row in grid]
    frame = facts["frame"]
    output = full_grid(facts["height"], facts["width"], 0)
    draw_frame(
        output,
        frame["top"],
        frame["left"],
        frame["bottom"],
        frame["right"],
        frame["color"],
    )
    for row in range(frame["top"] + 1, frame["bottom"]):
        for col in range(frame["left"] + 1, frame["right"]):
            output[row][col] = facts["left_color"]
    return output


def _rival_keep_sparse_seeds(grid):
    return [list(row) for row in grid]


def _rival_numeric_min_phase(grid):
    facts, errors = _analyze(grid)
    if errors:
        return [list(row) for row in grid]
    low, high = sorted((facts["left_color"], facts["right_color"]))
    return _checkerboard_output(grid, top_left_color=low, alternate_color=high)


def _rival_top_left_cell_is_key(grid):
    """Canonical-fitting shortcut: use the literal top-left cell, else min color."""
    facts, errors = _analyze(grid)
    if errors:
        return [list(row) for row in grid]
    frame = facts["frame"]
    value = grid[frame["top"] + 1][frame["left"] + 1]
    colors = {facts["left_color"], facts["right_color"]}
    top_left_color = value if value in colors else min(colors)
    alternate_color = next(color for color in colors if color != top_left_color)
    return _checkerboard_output(
        grid,
        top_left_color=top_left_color,
        alternate_color=alternate_color,
    )


def _rival_adjacent_pair_only(grid):
    """Canonical-fitting shortcut: fill only when the two seeds are adjacent."""
    facts, errors = _analyze(grid)
    if errors:
        return [list(row) for row in grid]
    if facts["seed_gap"] == 1:
        return rule_mirror(grid)
    return [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "right_seed_phase": _rival_right_seed_phase,
    "solid_left_color": _rival_solid_left_color,
    "keep_sparse_seeds": _rival_keep_sparse_seeds,
    "numeric_min_phase": _rival_numeric_min_phase,
    "top_left_cell_is_key": _rival_top_left_cell_is_key,
    "adjacent_pair_only": _rival_adjacent_pair_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "top_left_cell_is_key": _rival_top_left_cell_is_key,
    "adjacent_pair_only": _rival_adjacent_pair_only,
}


def _facts_or_none(grid):
    facts, errors = _analyze(grid)
    return None if errors else facts


def _differs_from(name: str):
    return lambda grid: rule_mirror(grid) != SEMANTIC_RIVALS[name](grid)


def _layout_refutes(layout: str, rival: str):
    return lambda grid: (
        (facts := _facts_or_none(grid)) is not None
        and facts["seed_layout"] == layout
        and rule_mirror(grid) != SEMANTIC_RIVALS[rival](grid)
    )


SEMANTIC_WITNESSES = {
    "right_phase_changes_answer": _differs_from("right_seed_phase"),
    "sparse_seeds_require_full_fill": _differs_from("keep_sparse_seeds"),
    "both_colors_are_required": _differs_from("solid_left_color"),
    "left_color_can_exceed_right": lambda grid: (
        (facts := _facts_or_none(grid)) is not None
        and facts["left_color"] > facts["right_color"]
        and rule_mirror(grid) != SEMANTIC_RIVALS["numeric_min_phase"](grid)
    ),
    "shifted_pair_refutes_top_left_key": _layout_refutes(
        "shifted_pair", "top_left_cell_is_key"
    ),
    "spaced_pair_refutes_adjacent_only": _layout_refutes(
        "spaced_pair", "adjacent_pair_only"
    ),
}

WITNESS_RIVALS = {
    "right_phase_changes_answer": ["right_seed_phase"],
    "sparse_seeds_require_full_fill": ["keep_sparse_seeds"],
    "both_colors_are_required": ["solid_left_color"],
    "left_color_can_exceed_right": ["numeric_min_phase"],
    "shifted_pair_refutes_top_left_key": ["top_left_cell_is_key"],
    "spaced_pair_refutes_adjacent_only": ["adjacent_pair_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo window to refute the named wrong rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    facts_rows: list[dict[str, Any]] = []
    frame_positions: set[tuple[int, int]] = set()

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} must contain input and output")
            continue
        facts, errors = _analyze(pair["input"])
        if errors:
            reasons.append(f"demonstration {index} violates the grammar: {'; '.join(errors)}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demonstration {index} output disagrees with the checkerboard rule")
        facts_rows.append(facts)
        frame_positions.add((facts["frame"]["top"], facts["frame"]["left"]))

    if reasons:
        return reasons
    if {facts["seed_layout"] for facts in facts_rows} != set(SEED_LAYOUTS):
        reasons.append("demonstrations must cover canonical, shifted, and spaced seed layouts")
    if not any(facts["left_color"] < facts["right_color"] for facts in facts_rows):
        reasons.append("demonstrations lack a left-color-below-right-color example")
    if not any(facts["left_color"] > facts["right_color"] for facts in facts_rows):
        reasons.append("demonstrations lack a left-color-above-right-color example")
    if len(frame_positions) < 2:
        reasons.append("demonstrations do not vary frame position")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and oracle output")
    else:
        query_facts, query_errors = _analyze(query["input"])
        del query_facts
        if query_errors:
            reasons.append("query violates the teaching grammar: " + "; ".join(query_errors))
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the checkerboard rule")
    return reasons
