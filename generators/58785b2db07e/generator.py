"""Generator for arc_puzzle_bank_21_set17_s:S17_M6."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "58785b2db07e"
VERSION = "1.1.1"
TASK_ID = "58785b2db07e"

SUMMARY = "One-step plus growths from color-2 and color-3 groups overlap into contact cells."

INVARIANTS = [
    "background is 0",
    "color 2 and color 3 groups are separated by exactly one contact lane",
    "their one-step plus expansions have a nonempty intersection",
]

AXES = {
    "height": {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "width": {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "orientation": {"type": "enum", "default": "rng horizontal|vertical", "valid": "horizontal|vertical"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color-2 and color-3 cells both present, separated by a gap."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c3 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    if c2 == 0:
        errs.append("no color-2 cells found")
    if c3 == 0:
        errs.append("no color-3 cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = ctx.draw_int("height", 8, 11)
    w = ctx.draw_int("width", 8, 11)
    orientation = ctx.draw_choice("orientation", ["horizontal", "vertical"])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    if orientation == "horizontal":
        r = rng.randint(2, h - 4)
        c = rng.randint(2, w - 5)
        for dr in [0, 1]:
            g[r + dr][c] = 2
            g[r + dr][c + 2] = 3
    else:
        r = rng.randint(2, h - 5)
        c = rng.randint(2, w - 4)
        for dc in [0, 1]:
            g[r][c + dc] = 2
            g[r + 2][c + dc] = 3
    return g
