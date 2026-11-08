"""Generator for ARC task 2072aba6.

Rule: `(rule! (lambda (g) (stamp-grid g (grid (list (list 1 2) (list 2 1))))))`.
At every foreground cell (color 5 in canonical), stamp the 2 × 2
checker `[[1,2],[2,1]]`.

Combinatorial axes:
  * grid_size           — input side (canonical 3; here exposed)
  * trigger_count       — how many cells are color 5 (1..8)
  * trigger_layout      — random/cluster/border/row/column/corners/cross/diagonal
  * filler_pattern      — non-trigger fill: zero / sparse_decoy / mixed_decoy
  * filler_palette_size — colors used for non-trigger cells
  * caller-opt-in degenerates: no_triggers, all_triggers, single_trigger
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f7ed198556e"
VERSION = "3.0.0"  # shape-locked in/out: rule stamps a 2x2 checker at each COLOR-5 cell (output = 2x input; size-generic). Old gen fixed a 3x3 input (-> always 6x6) + decoy colours the rule IGNORES (canonical has only 5s). Now vary grid size n (3-6) with a random color-5 pattern -> output dims + pattern vary.
TASK_ID = "4f7ed198556e"
SUMMARY = (
    "FIXED 3×3 input grid "
    "with 1-8 COLOR-5 "
    "TRIGGER cells at "
    "positions chosen by one "
    "of 8 LAYOUTS (random/"
    "cluster/border/row/"
    "column/corners/cross/"
    "diagonal). Non-trigger "
    "cells filled by FILLER "
    "PATTERN (zero/sparse_"
    "decoy at 30%/mixed_"
    "decoy at 60%) using "
    "decoy colors from {3, "
    "4, 6, 7, 8, 9} "
    "(excluding {0, 1, 2, "
    "5}). Rule (STAMP 2×2 "
    "[[1, 2], [2, 1]] "
    "CHECKER AT EACH "
    "COLOR-5 TRIGGER): "
    "EMIT a 6×6 OUTPUT GRID "
    "(input doubled). For "
    "EACH cell (r, c) in the "
    "3×3 input where "
    "g[r][c] == 5: STAMP "
    "the 2×2 CHECKER "
    "[[1, 2], [2, 1]] at "
    "output position "
    "(2r, 2c). Non-5 input "
    "cells produce 0 in the "
    "output 2×2 block. Net: "
    "each color-5 cell "
    "expands to a 2×2 "
    "checker; output is 6×6."
)

# Bbox fixed: 3×3 → 6×6 by rule. Diversity comes from trigger count +
# trigger position + filler decoy colors.
#
# Rivals: 'stamp at every cell regardless of color' refuted by ≥1
# demo with filler cells that don't get stamped. 'stamp a different
# 2×2' refuted by any demo (output always shows [[1,2],[2,1]]).
# 'output equals input' refuted by any demo (output is bigger).
# 4 demos with varied trigger counts + decoys cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "input is 3 × 3 (canonical)",
    "foreground trigger color is 5",
    "≥1 foreground cell so the rule has visible effect",
]

TRIGGER_LAYOUTS = (
    "random", "cluster", "border", "row", "column",
    "corners", "cross", "diagonal",
)
FILLER_PATTERNS = ("zero", "sparse_decoy", "mixed_decoy")
DEGENERATE_TEXTURES = ("no_triggers", "all_triggers", "single_trigger")
HELPFUL_TEXTURES = TRIGGER_LAYOUTS

AXES = {
    "grid_size":          {"type": "int", "default": "3", "valid": "3..3"},
    "trigger_count":      {"type": "int", "default": "rng 2..6", "valid": "1..9"},
    "trigger_layout":     {"type": "str", "default": "rng helpful",
                           "valid": "|".join(TRIGGER_LAYOUTS)},
    "filler_pattern":     {"type": "str", "default": "rng zero|sparse_decoy|mixed_decoy",
                           "valid": "|".join(FILLER_PATTERNS)},
    "filler_palette_size": {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "texture":            {"type": "str", "default": "alias for trigger_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # the rule stamps the 2x2 checker at each COLOR-5 cell -> output = 2x the
    # input. The old gen fixed a 3x3 input (shape-locked) + added decoy colours
    # the rule IGNORES (canonical has only 5s). Now vary the grid size n (the
    # rule is size-generic) with a RANDOM color-5 pattern -> output dims (2n)
    # and the stamp pattern both vary.
    if difficulty == "easy":
        n = ctx.draw_int("grid_n", 3, 3)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_n", 4, 6)
    else:
        n = ctx.draw_int("grid_n", 3, 5)

    g = full_grid(n, n, 0)
    cells = [(r, c) for r in range(n) for c in range(n)]
    n_trigger = rng.randint(1, max(1, n * n - 1))
    for r, c in rng.sample(cells, n_trigger):
        g[r][c] = 5
    return g


def _trigger_layout(layout, n, rng):
    if layout == "cluster":
        center = (rng.randint(0, 2), rng.randint(0, 2))
        cells = [(r, c) for r in range(3) for c in range(3)]
        cells.sort(key=lambda rc: abs(rc[0] - center[0]) + abs(rc[1] - center[1]))
    elif layout == "border":
        cells = [(r, c) for r in range(3) for c in range(3)
                 if r in {0, 2} or c in {0, 2}]
        rng.shuffle(cells)
    elif layout == "row":
        r = rng.randint(0, 2)
        cells = [(r, c) for c in range(3)]
    elif layout == "column":
        c = rng.randint(0, 2)
        cells = [(r, c) for r in range(3)]
    elif layout == "corners":
        cells = [(0, 0), (0, 2), (2, 0), (2, 2)]
        rng.shuffle(cells)
    elif layout == "cross":
        cells = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
        rng.shuffle(cells)
    elif layout == "diagonal":
        cells = [(0, 0), (1, 1), (2, 2)] if rng.random() < 0.5 \
            else [(0, 2), (1, 1), (2, 0)]
    else:
        cells = [(r, c) for r in range(3) for c in range(3)]
        rng.shuffle(cells)
    return cells[:max(1, min(n, len(cells)))]


def _draw_from_degenerate(name, rng):
    """Edge-case where the stamp signal collapses.

    no_triggers     — no 5s in input; rule is no-op (output == input).
    all_triggers    — every cell is 5; output is a uniform big checker.
    single_trigger  — single 5; minimal rule signal.
    """
    g = full_grid(3, 3, 0)
    if name == "no_triggers":
        for r in range(3):
            for c in range(3):
                g[r][c] = 0 if rng.random() < 0.4 else 4
        return g
    if name == "all_triggers":
        for r in range(3):
            for c in range(3):
                g[r][c] = 5
        return g
    if name == "single_trigger":
        r = rng.randint(0, 2); c = rng.randint(0, 2)
        g[r][c] = 5
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h = len(grid)
    w = len(grid[0]) if grid else 0
    if h != w or not (3 <= h <= 6):
        errs.append(f"expected square input size 3..6, got {h}x{w}")
    vals = {v for row in grid for v in row}
    if vals - {0, 5}:
        errs.append(f"default input should contain only 0 and trigger color 5, got {sorted(vals)}")
    triggers = sum(v == 5 for row in grid for v in row)
    if triggers < 1:
        errs.append("expected at least one color-5 trigger")
    if triggers == h * w:
        errs.append("all cells are triggers; non-trigger branch is hidden")
    return errs
