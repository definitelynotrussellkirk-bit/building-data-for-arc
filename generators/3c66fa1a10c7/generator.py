"""Generator for 3c66fa1a10c7 — code-selected boolean panel overlay.

The first cell is an operation code: 1=union, 2=intersection, 3=xor.
Below it, two equal panels are separated by a vertical color-5 divider.
The target is the selected Boolean operation on panel occupancy, painted 7.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3c66fa1a10c7"
VERSION = "2.0.0"
TASK_ID = "3c66fa1a10c7"
RULE_HASH = "b75bd2704507"
SUMMARY = (
    "Operation code 1/2/3 above two equal support-mask panels separated by 5; "
    "the panels share one signal color and contain overlap plus one-sided cells."
)

INVARIANTS = [
    "top row contains only the operation code at (0,0)",
    "one color-5 divider below the top row splits equal-width panels",
    "all nonzero panel cells use one shared color",
    "panel supports include overlap and at least one one-sided cell",
]

PANEL_COLORS = (4, 6, 7, 8, 9)

# Every declared axis is independently meaningful, consumed through GenCtx,
# and recoverable from the returned grid via observe_overrides().
AXES = {
    "body_h": {
        "type": "int",
        "default": "difficulty-aware 3..7",
        "valid": "3..7",
    },
    "panel_w": {
        "type": "int",
        "default": "difficulty-aware 3..7",
        "valid": "3..7",
    },
    "code": {
        "type": "int",
        "default": "rng 1..3",
        "valid": "1..3",
    },
    "panel_color": {
        "type": "color",
        "default": "rng from 4|6|7|8|9",
        "valid": "4|6|7|8|9",
    },
    "signal_cells": {
        "type": "int",
        "default": "difficulty-aware 3..8",
        "valid": "3..8",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one lawful Boolean-overlay input grid."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Keep a substantial canonical-scale anchor in every difficulty band while
    # retaining broad lawful generalization. Any explicit override disables the
    # prior so every declared boundary remains exact-or-loud.
    canonical_prior = (
        not overrides
        and ctx.draw_rng("canonical_profile_prior").random() < 0.40
    )
    if canonical_prior:
        body_h = ctx.draw_int("body_h", 3, 3)
        panel_w = int(ctx.draw_choice("panel_w", (3, 4)))
        panel_color = int(ctx.draw_choice("panel_color", (7,)))
        signal_cells = int(ctx.draw_choice("signal_cells", (5, 6)))
    else:
        body_h = ctx.draw_int_diff("body_h", 3, 7)
        panel_w = ctx.draw_int_diff("panel_w", 3, 7)
        panel_color = int(ctx.draw_choice("panel_color", PANEL_COLORS))
        signal_cells = ctx.draw_int_diff("signal_cells", 3, 8)
    code = ctx.draw_int("code", 1, 3)

    area = body_h * panel_w
    if signal_cells > area:
        raise ValueError(
            f"signal_cells={signal_cells} exceeds panel area {area}"
        )

    divider = panel_w
    grid = full_grid(body_h + 1, panel_w * 2 + 1, 0)
    grid[0][0] = code
    for r in range(1, body_h + 1):
        grid[r][divider] = 5

    rng = ctx.draw_rng("support_layout")
    positions = rng.sample(
        [(r, c) for r in range(1, body_h + 1) for c in range(panel_w)],
        signal_cells,
    )

    # The first three witnesses prevent constant-answer and branch-collapse
    # shortcuts. Remaining support cells vary all three occupancy relations.
    relations = ["overlap", "left", "right"]
    relations.extend(
        rng.choice(("overlap", "left", "right"))
        for _ in range(signal_cells - 3)
    )
    rng.shuffle(relations)

    for (r, c), relation in zip(positions, relations):
        if relation in ("overlap", "left"):
            grid[r][c] = panel_color
        if relation in ("overlap", "right"):
            grid[r][divider + 1 + c] = panel_color
    return grid


def _structure(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    # Canonical JSONL stores compact rows as digit strings, while generated
    # instances use lists of ints. Validate both representations identically.
    if all(isinstance(row, str) for row in grid):
        if any(not row or any(ch not in "0123456789" for ch in row) for row in grid):
            return None, ["string rows must contain ARC color digits"]
        grid = [[int(ch) for ch in row] for row in grid]
    elif not all(isinstance(row, list) and row for row in grid):
        return None, ["grid rows must be nonempty lists or digit strings"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]

    h = len(grid)
    code = grid[0][0]
    errors: list[str] = []
    if code not in (1, 2, 3):
        errors.append(f"bad operation code {code!r}")
    if any(value != 0 for value in grid[0][1:]):
        errors.append("top row must be zero outside the operation code")

    divider_candidates = [
        c
        for c in range(1, width - 1)
        if grid[0][c] == 0 and all(grid[r][c] == 5 for r in range(1, h))
    ]
    if len(divider_candidates) != 1:
        errors.append(
            "expected exactly one full color-5 divider below the code row, "
            f"found {len(divider_candidates)}"
        )
        return None, errors
    divider = divider_candidates[0]
    if width != divider * 2 + 1:
        errors.append("divider must split two nonempty equal-width panels")
        return None, errors

    panel_values = [
        grid[r][c]
        for r in range(1, h)
        for c in list(range(divider)) + list(range(divider + 1, width))
    ]
    bad_values = sorted({v for v in panel_values if not isinstance(v, int) or not 0 <= v <= 9})
    if bad_values:
        errors.append(f"panel contains non-ARC values {bad_values}")
    panel_colors = {v for v in panel_values if v != 0}
    if 5 in panel_colors:
        errors.append("color 5 is reserved for the divider")
    signal_colors = panel_colors - {5}
    if len(signal_colors) != 1:
        errors.append(
            "both panels must use exactly one shared nonzero signal color; "
            f"found {sorted(signal_colors)}"
        )
        panel_color = None
    else:
        panel_color = next(iter(signal_colors))

    overlap = left_only = right_only = signal_cells = 0
    for r in range(1, h):
        for c in range(divider):
            left = grid[r][c] != 0
            right = grid[r][divider + 1 + c] != 0
            if left or right:
                signal_cells += 1
            if left and right:
                overlap += 1
            elif left:
                left_only += 1
            elif right:
                right_only += 1

    if overlap == 0:
        errors.append("panel supports need at least one overlap witness")
    if left_only + right_only == 0:
        errors.append("panel supports need at least one one-sided witness")

    return {
        "body_h": h - 1,
        "panel_w": divider,
        "code": code,
        "panel_color": panel_color,
        "signal_cells": signal_cells,
        "overlap": overlap,
        "left_only": left_only,
        "right_only": right_only,
    }, errors


def observe_overrides(grid) -> dict:
    """Recover every declared exact axis from the returned grid."""
    info, _ = _structure(grid)
    if info is None:
        return {
            "body_h": 0,
            "panel_w": 0,
            "code": None,
            "panel_color": None,
            "signal_cells": 0,
        }
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar without rejecting canonical rows."""
    _, errors = _structure(grid)
    return errors
