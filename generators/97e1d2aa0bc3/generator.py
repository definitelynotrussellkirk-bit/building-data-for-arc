"""Generator for ARC task 2de01db2.

Each row has one uniquely most-frequent color after colors 0 and 7 are
ignored.  Call that row color ``mc``.  The output replaces ``mc`` cells with
0 and replaces every other cell (0, 7, and arbitrary noise colors) with
``mc``.

The canonical test is important: color 3 is an ordinary distractor, so 7 is
not the only possible noise color.  Generated rows therefore always include
an arbitrary non-{0,7,mc} distractor, while a deterministic sample-index
schedule varies whether 7 is present and how the target cells are arranged.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "97e1d2aa0bc3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "aaa71b99c62e"

SUMMARY = (
    "For each row, ignore colors 0 and 7 and find the uniquely most-frequent "
    "remaining color mc. Replace cells equal to mc with 0; replace every "
    "other cell, including 0, 7, and arbitrary colored noise, with mc."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "grid height is 3..4 and width is 10..11 (including canonical 3x10)",
    "every row has a unique most-frequent color among values other than 0 and 7",
    "row target colors are distinct across rows",
    "every row contains both target and non-target cells",
    "generated rows include an arbitrary non-{0,7,target} distractor",
    "sample_index cycles a 7-dominant shortcut rebuttal, ordinary 7 noise, and no-7 rows",
    "sample_index also cycles scattered, alternating, and contiguous target layouts",
]

# Keep the override surface small and exact.  Other variation is a documented
# deterministic sample-index schedule or a label-keyed local RNG decision.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 3..4", "valid": "3..4"},
    "grid_w": {"type": "int", "default": "difficulty-aware 10..11", "valid": "10..11"},
}

_TARGET_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_LAYOUTS = ("scattered", "alternating", "contiguous")


def _row_target(row: list[int]) -> tuple[int | None, int, bool]:
    """Return (target, count, unique_top) under the canonical non-{0,7} rule."""
    counts = Counter(value for value in row if value not in (0, 7))
    if not counts:
        return None, 0, False
    top_count = max(counts.values())
    top_colors = [color for color, count in counts.items() if count == top_count]
    return top_colors[0], top_count, len(top_colors) == 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the row-wise inversion grammar, including canonical inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    height = len(grid)
    errors: list[str] = []
    if not (3 <= height <= 4):
        errors.append(f"height {height} outside 3..4")
    if not (10 <= width <= 11):
        errors.append(f"width {width} outside 10..11")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color")
        return errors

    targets: list[int] = []
    for row_index, row in enumerate(grid):
        target, target_count, unique_top = _row_target(row)
        if target is None:
            errors.append(f"row {row_index} has no color outside {{0,7}}")
            continue
        if not unique_top:
            errors.append(f"row {row_index} has a tied non-{{0,7}} mode")
        if target_count < 3:
            errors.append(
                f"row {row_index} target appears only {target_count} times; expected at least 3"
            )
        if target_count == width:
            errors.append(f"row {row_index} is monochrome, so inversion is hidden")
        targets.append(target)

    if len(targets) == height and len(set(targets)) != height:
        errors.append("row target colors must be distinct")
    if not any(value == 0 for row in grid for value in row):
        errors.append("grid must contain at least one 0 distractor/background cell")
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests only; Racket remains authoritative."""
    output: list[list[int]] = []
    for row in grid:
        target, _, unique_top = _row_target(row)
        if target is None or not unique_top:
            raise ValueError("row has no unique non-{0,7} target")
        output.append([0 if value == target else target for value in row])
    return output


def observe_overrides(grid) -> dict[str, int]:
    """Expose the exact declared dimensions from the returned grid."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md, v1)
# ---------------------------------------------------------------------------

def strict_canonical_like(grid) -> list[str]:
    """[] when grid is a lawful instance of THIS task's canonical manifold.

    Structural grammar (self_check) plus the task-linked palette budget: the
    non-{0,7} palette is exactly the h distinct row targets, optionally plus
    ONE shared distractor colour (canonical train_0 uses colour 2, the
    canonical test uses colour 3; train_1/train_2 use none).
    """
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height = len(grid)
    non07 = {value for row in grid for value in row if value not in (0, 7)}
    if not (height <= len(non07) <= height + 1):
        reasons.append(
            f"non-{{0,7}} palette has {len(non07)} colours; canonical-like "
            f"grids carry exactly the {height} row targets plus at most one "
            "distractor colour"
        )
    return reasons


def _witness_seven_dominant_row(grid) -> bool:
    """Schedule branch 0: a row where 7 outnumbers the true target, so
    'pick the most frequent nonzero colour' gives the WRONG answer."""
    for row in grid:
        target, count, unique_top = _row_target(row)
        if target is None or not unique_top:
            continue
        if row.count(7) > count:
            return True
    return False


def _witness_seven_sparse_noise(grid) -> bool:
    """Schedule branch 1: 7 present as ordinary noise only, never
    outnumbering any row's target."""
    has_seven = any(7 in row for row in grid)
    return has_seven and not _witness_seven_dominant_row(grid)


def _witness_no_seven(grid) -> bool:
    """Schedule branch 2: no 7 anywhere — the rule must not require 7's
    presence, only its exclusion from the mode count."""
    return all(7 not in row for row in grid)


def _witness_non_seven_distractor(grid) -> bool:
    """Canonical-test branch: some row carries a nonzero, non-7 colour that is
    not that row's target (colour 3 in the canonical test), proving 7 is not
    the only possible noise colour."""
    for row in grid:
        target, _, unique_top = _row_target(row)
        if target is None or not unique_top:
            continue
        if any(value not in (0, 7, target) for value in row):
            return True
    return False


SEMANTIC_WITNESSES = {
    "seven_dominant_row_rebuttal": _witness_seven_dominant_row,
    "seven_sparse_noise": _witness_seven_sparse_noise,
    "no_seven_rows": _witness_no_seven,
    "non_seven_distractor": _witness_non_seven_distractor,
}


def _competitor_row_mode_over_nonzero(grid):
    """Competing rule: ignore ONLY 0 (not 7) — the per-row nonzero mode is mc.

    Falsified by the seven-dominant scheduled row, where the nonzero mode is
    7 but the canonical target is the non-{0,7} mode. Returns None when the
    competitor is inapplicable (tie / all-zero row)."""
    output = []
    for row in grid:
        counts = Counter(value for value in row if value != 0)
        if not counts:
            return None
        top_count = max(counts.values())
        top_colors = [color for color, count in counts.items() if count == top_count]
        if len(top_colors) != 1:
            return None
        mode_color = top_colors[0]
        output.append([0 if value == mode_color else mode_color for value in row])
    return output


def _competitor_whole_grid_mode(grid):
    """Competing rule: one GLOBAL non-{0,7} mode for the whole grid instead of
    per-row modes. Falsified by any grid with distinct row targets (all
    canonical and generated grids). Ties break to the smallest colour."""
    counts = Counter(value for row in grid for value in row if value not in (0, 7))
    if not counts:
        return None
    top_count = max(counts.values())
    mode_color = min(color for color, count in counts.items() if count == top_count)
    return [
        [0 if value == mode_color else mode_color for value in row] for row in grid
    ]


_LESSON_COMPETITORS = {
    "row mode over nonzero colours (7 eligible as mc)":
        _competitor_row_mode_over_nonzero,
    "whole-grid mc instead of per-row":
        _competitor_whole_grid_mode,
}


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos uniquely determine the query answer.

    A competing rule that is consistent with EVERY demo yet answers the query
    differently makes the lesson ambiguous. Pure: no mutation, no RNG."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} input is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(
                f"demo {index} output does not match the canonical "
                "row-inversion rule"
            )
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query input is outside the rule domain: {exc}")
        return reasons
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' is consistent with every demo but "
                "answers the query differently"
            )
    return reasons


def _target_columns(layout: str, width: int, count: int, rng, row_index: int) -> list[int]:
    columns = list(range(width))
    if layout == "alternating":
        parity = row_index % 2
        preferred = [c for c in columns if c % 2 == parity]
        remainder = [c for c in columns if c % 2 != parity]
        return (preferred + remainder)[:count]
    if layout == "contiguous":
        start = rng.randint(0, width - count)
        return list(range(start, start + count))
    rng.shuffle(columns)
    return columns[:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Full declared bounds are used in every band, so every exact boundary
    # override remains valid; draw_int_diff supplies the curriculum skew.
    height = ctx.draw_int_diff("grid_h", 3, 4)
    width = ctx.draw_int_diff("grid_w", 10, 11)
    rng = ctx.draw_rng("row-layout-and-colors")

    targets = list(rng.sample(_TARGET_COLORS, height))
    noise_candidates = [color for color in _TARGET_COLORS if color not in targets]
    noise_color = rng.choice(noise_candidates)

    layout = _LAYOUTS[sample_index % len(_LAYOUTS)]
    schedule_branch = sample_index % 3
    include_seven = schedule_branch != 2
    if difficulty == "easy":
        ordinary_target_count = width // 2 + 1
    elif difficulty == "hard":
        ordinary_target_count = max(4, width // 2 - 1)
    else:
        ordinary_target_count = width // 2

    grid = full_grid(height, width, 0)
    for row_index, target in enumerate(targets):
        # In branch 0, row 0 makes color 7 the overall row mode while the
        # canonical target remains the unique mode after {0,7} are ignored.
        # This falsifies the tempting shortcut "choose the most frequent
        # nonzero color".  Branch 1 has ordinary sparse 7 noise; branch 2
        # omits 7 entirely.
        seven_dominant = schedule_branch == 0 and row_index == 0
        target_count = 4 if seven_dominant else ordinary_target_count
        target_columns = set(
            _target_columns(layout, width, target_count, rng, row_index)
        )
        remaining = [column for column in range(width) if column not in target_columns]
        rng.shuffle(remaining)

        for column in target_columns:
            grid[row_index][column] = target

        # An arbitrary colored distractor is mandatory.  This specifically
        # covers the canonical test branch where color 3, not 7, is noise.
        grid[row_index][remaining.pop()] = noise_color
        if seven_dominant:
            for column in remaining:
                grid[row_index][column] = 7
        elif include_seven:
            grid[row_index][remaining.pop()] = 7
        # All unassigned cells stay 0.  Across rows, 0 is ordinarily the
        # global modal/background color even though each row has its own mc.

    return grid
