"""Generator for ARC task 8e2edd66 / content hash 4ecf2a93671f.

Canonical rule
--------------
Let ``g`` be an ``n x n`` two-color input with background 0 and one nonzero
foreground color ``c``.  The output has shape ``n² x n²``.  An output cell has
both a *block* coordinate ``(r // n, c // n)`` and a *subcell* coordinate
``(r % n, c % n)`` back in the input.  Paint the foreground color iff BOTH of
those source cells are 0; otherwise paint 0.

Equivalently, form the binary zero-mask of the input and take its Kronecker
self-product, then color the 1s with the input foreground color.

The canonical data only establish a single nonzero color.  This generator stays
on that supported two-color grammar rather than inventing multi-color tie or
mode-selection lessons.  A four-slot size schedule puts two 3x3 canonical anchors
next to 4x4 and 5x5 generalization examples. Anchor zero counts rotate through
3, 4 and 5 over twelve draws; every three-example sliding window
therefore refutes the tempting but canonically indistinguishable "always 3x3,
always 9x9" shortcut.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "4ecf2a93671f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "a7f459196d49"

SUMMARY = (
    "For an n x n two-color grid, use 0 as the background mask and the sole "
    "nonzero color as paint. The n² x n² output is indexed by a block source "
    "cell and a subcell source cell from the input; paint exactly when BOTH "
    "source cells are 0, otherwise output 0. This is the zero-mask Kronecker "
    "self-product. Ordinary lessons schedule 3x3 canonical anchors together "
    "with 4x4 and 5x5 cases so the rule cannot collapse to a fixed 9x9 template. "
    "The twelve-draw count cycle includes all canonical zero counts 3, 4 and 5."
)

INVARIANTS = [
    "input is square with side 3..5",
    "input uses exactly background 0 plus one nonzero foreground color",
    "input contains at least three zeros and at least two foreground cells",
    "output shape is n² x n²",
    "output is foreground exactly at block-zero AND subcell-zero positions",
    "the Racket oracle is the sole output authority",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45
LESSON_SCHEDULE_PERIOD = 12

AXES = {
    "side": {
        "type": "int",
        "default": "scheduled 3,3,4,5",
        "valid": "3..5",
    },
    "fg_color": {
        "type": "color",
        "default": "rng nonzero ARC color",
        "valid": "1..9",
    },
    "bg_count": {
        "type": "int",
        "default": "scheduled 3..7",
        "valid": "3..7",
    },
}

# Every Cartesian boundary combination is constructible: side 3 still has at
# least two foreground cells at bg_count=7, and larger sides have more room.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "canonical_anchor_a",
    "canonical_anchor_b",
    "side4_generalization",
    "side5_generalization",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive draws always include a non-3x3 size witness."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int]:
    profile = schedule_profile(0, sample_index, difficulty)
    count_cycle = (sample_index // len(SCHEDULE_PROFILES)) % 3
    if profile == "canonical_anchor_a":
        return 3, 3 + count_cycle
    if profile == "canonical_anchor_b":
        return 3, 3 + (count_cycle + 1) % 3
    if profile == "side4_generalization":
        return 4, {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 5)
    return 5, {"easy": 5, "medium": 6, "hard": 7}.get(difficulty, 6)


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _foreground_color(grid) -> int:
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"expected exactly one nonzero foreground color, found {sorted(colors)}")
    return next(iter(colors))


def _zero_positions(grid) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    }


def _foreground_positions(grid) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes while accepting all canonical inputs."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if height != width:
        errors.append(f"grid must be square, got {height}x{width}")
        return errors
    if not (3 <= height <= 5):
        errors.append(f"side must be in 3..5, got {height}")

    counts = Counter(value for row in grid for value in row)
    if 0 not in counts:
        errors.append("background color 0 is absent")
    nonzero = sorted(value for value in counts if value != 0)
    if len(nonzero) != 1:
        errors.append(
            f"expected exactly one nonzero foreground color, found {nonzero}"
        )

    zero_count = counts.get(0, 0)
    fg_count = height * width - zero_count
    if zero_count < 3:
        errors.append(
            f"need at least three zero cells to expose the self-tile mask, found {zero_count}"
        )
    if fg_count < 2:
        errors.append(
            f"need at least two foreground cells to expose zero-valued branches, found {fg_count}"
        )

    zeros = _zero_positions(grid)
    foreground = _foreground_positions(grid)
    for role, cells in (("zero", zeros), ("foreground", foreground)):
        if cells and not _support_spans_two_axes(cells):
            errors.append(f"{role} support must span at least two rows and two columns")
        if _is_solid_rectangle(cells):
            errors.append(f"{role} support may not be a solid rectangle")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Empirical canonical manifold shared by all four train/test inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    if len(grid) != 3 or len(grid[0]) != 3:
        reasons.append(
            f"canonical inputs are exactly 3x3, found {len(grid)}x{len(grid[0])}"
        )
    zero_count = sum(value == 0 for row in grid for value in row)
    if not 3 <= zero_count <= 5:
        reasons.append(f"canonical zero count is 3..5, found {zero_count}")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact semantic axis from a generated grid."""
    return {
        "side": len(grid),
        "fg_color": _foreground_color(grid),
        "bg_count": sum(value == 0 for row in grid for value in row),
    }


def rule_mirror(grid):
    """Independent Python mirror for evidence; canonical Racket remains authority."""
    n = len(grid)
    color = _foreground_color(grid)
    return [
        [
            color
            if grid[r // n][c // n] == 0 and grid[r % n][c % n] == 0
            else 0
            for c in range(n * n)
        ]
        for r in range(n * n)
    ]


def _block_zero_only(grid):
    n = len(grid)
    color = _foreground_color(grid)
    return [
        [color if grid[r // n][c // n] == 0 else 0 for c in range(n * n)]
        for r in range(n * n)
    ]


def _subcell_zero_only(grid):
    n = len(grid)
    color = _foreground_color(grid)
    return [
        [color if grid[r % n][c % n] == 0 else 0 for c in range(n * n)]
        for r in range(n * n)
    ]


def _either_zero_or(grid):
    n = len(grid)
    color = _foreground_color(grid)
    return [
        [
            color
            if grid[r // n][c // n] == 0 or grid[r % n][c % n] == 0
            else 0
            for c in range(n * n)
        ]
        for r in range(n * n)
    ]


def _foreground_self_tile(grid):
    n = len(grid)
    color = _foreground_color(grid)
    return [
        [
            color
            if grid[r // n][c // n] != 0 and grid[r % n][c % n] != 0
            else 0
            for c in range(n * n)
        ]
        for r in range(n * n)
    ]


def _zero_count_only(grid):
    """Wrong shortcut: preserve only the number of painted output cells."""
    n = len(grid)
    color = _foreground_color(grid)
    zero_count = sum(value == 0 for row in grid for value in row)
    painted = zero_count * zero_count
    out = [[0 for _ in range(n * n)] for _ in range(n * n)]
    for index in range(painted):
        out[index // (n * n)][index % (n * n)] = color
    return out


def _fixed_side3(grid):
    """Wrong shortcut that is answer-equivalent on every canonical example."""
    expected = rule_mirror(grid)
    if len(grid) == 3:
        return expected
    return [row[:9] for row in expected[:9]]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "block_zero_only": _block_zero_only,
    "subcell_zero_only": _subcell_zero_only,
    "either_zero_or": _either_zero_or,
    "foreground_self_tile": _foreground_self_tile,
    "zero_count_only": _zero_count_only,
    "fixed_side3_output": _fixed_side3,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_side3_output": _fixed_side3}


def _valid(grid) -> bool:
    return not self_check(grid)


def _witness_block_condition(grid) -> bool:
    return _valid(grid)


def _witness_subcell_condition(grid) -> bool:
    return _valid(grid)


def _witness_and_not_or(grid) -> bool:
    return _valid(grid)


def _witness_zero_role(grid) -> bool:
    return _valid(grid)


def _witness_spatial_arrangement(grid) -> bool:
    return _valid(grid) and _zero_count_only(grid) != rule_mirror(grid)


def _witness_scaled_size(grid) -> bool:
    return _valid(grid) and len(grid) != 3


SEMANTIC_WITNESSES = {
    "block_condition_matters": _witness_block_condition,
    "subcell_condition_matters": _witness_subcell_condition,
    "and_not_or": _witness_and_not_or,
    "zero_role_not_foreground_role": _witness_zero_role,
    "spatial_arrangement_not_count_only": _witness_spatial_arrangement,
    "output_size_scales_with_input": _witness_scaled_size,
}

WITNESS_RIVALS = {
    "block_condition_matters": ["subcell_zero_only"],
    "subcell_condition_matters": ["block_zero_only"],
    "and_not_or": ["either_zero_or"],
    "zero_role_not_foreground_role": ["foreground_self_tile"],
    "spatial_arrangement_not_count_only": ["zero_count_only"],
    "output_size_scales_with_input": ["fixed_side3_output"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a fitting named rival only when it changes this query's answer."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        return [f"query input is invalid: {query_errors[0]}"]

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact zero-mask self-tile")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    expected_query = rule_mirror(query["input"])
    for name, was_refuted in refuted.items():
        if not was_refuted and SEMANTIC_RIVALS[name](query["input"]) != expected_query:
            reasons.append(f"demonstrations do not refute query-disagreeing rival {name}")
    return reasons


def _support_spans_two_axes(cells: set[tuple[int, int]]) -> bool:
    return len({r for r, _ in cells}) >= 2 and len({c for _, c in cells}) >= 2


def _is_solid_rectangle(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return area == len(cells)


def _candidate_grid(side: int, fg_color: int, bg_count: int, rng):
    positions = [(r, c) for r in range(side) for c in range(side)]
    rng.shuffle(positions)
    zeros = set(positions[:bg_count])
    return [
        [0 if (r, c) in zeros else fg_color for c in range(side)]
        for r in range(side)
    ]


def _teaching_checks(grid) -> list[str]:
    """Curriculum-only checks; intentionally separate from authority grammar."""
    reasons: list[str] = []
    expected = rule_mirror(grid)
    for name, rival in SEMANTIC_RIVALS.items():
        if name == "fixed_side3_output" and len(grid) == 3:
            # This deliberate canonical shortcut is killed by the schedule,
            # not by an impossible per-3x3 witness.
            continue
        if rival(grid) == expected:
            reasons.append(f"scene fails to refute rival {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty is not None and (
        type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a literal integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_side, default_bg_count = _profile_defaults(sample_index, difficulty)
    side = _scheduled_int(ctx, overrides, "side", default_side, 3, 5)
    fg_color = ctx.draw_color("fg_color", exclude={0})
    bg_count = _scheduled_int(ctx, overrides, "bg_count", default_bg_count, 3, 7)
    rng = ctx.draw_rng("mask_layout")

    # Deterministic rejection sampling is used only for pedagogical shape
    # quality. Every accepted grid still realizes the requested exact axes.
    for _ in range(256):
        grid = _candidate_grid(side, fg_color, bg_count, rng)
        if self_check(grid):
            continue
        if _teaching_checks(grid):
            continue
        return grid
    raise RuntimeError(
        "could not construct a shortcut-disambiguating mask after 256 deterministic attempts"
    )
