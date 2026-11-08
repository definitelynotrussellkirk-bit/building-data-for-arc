"""Generator for arc_puzzle_bank_21_set15_bundle:hard_o02 — orthogonal lasers from color-3 sources.

Rule: each color-3 cell emits lasers in 4 cardinal directions through 0-cells
(stops at any non-0). Cells hit by horizontal laser → 2; vertical laser → 3;
both → 4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_emitters,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, all_blocked, only_distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c3c0b9938f3"
VERSION = "1.2.0"
TASK_ID = "5c3c0b9938f3"

SUMMARY = "2-4 color-3 emitter cells + 0-3 distractors (2 or 6) blocking the lasers."

INVARIANTS = [
    "background is 0",
    "2-4 single-cell color-3 emitters at distinct positions",
    "0-3 distractor cells (color 2 or 6) acting as laser blockers",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_emitters", "all_blocked", "only_distractors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_emitters":     {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "3emitters_with_blockers",
                       "valid": "3emitters_with_blockers"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n_emitters = ctx.draw_int("n_emitters", 2, 2)
        n_distract = ctx.draw_int("n_distract", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        n_emitters = ctx.draw_int("n_emitters", 3, 4)
        n_distract = ctx.draw_int("n_distract", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n_emitters = ctx.draw_int("n_emitters", 2, 4)
        n_distract = ctx.draw_int("n_distract", 0, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for _ in range(n_emitters):
        for _t in range(60):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = 3
            break
    for _ in range(n_distract):
        for _t in range(60):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = rng.choice([2, 6])
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=1 color-3 emitter cell, only 0/2/3/6 values present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    emitters = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not emitters:
        errs.append("no color-3 emitter cells found")
    bad = {grid[r][c] for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 2, 3, 6)}
    if bad:
        errs.append(f"unexpected cell colors (expected only 0/2/3/6): {bad}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        # only blockers, no color-3 emitters → no lasers fired
        g[3][3] = 2; g[5][6] = 6
        return g
    if name == "all_blocked":
        # emitter immediately surrounded by blockers → laser stops at distance 0
        g[4][4] = 3
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[4 + dr][4 + dc] = 2
        return g
    if name == "only_distractors":
        # only non-emitter cells → no lasers in any direction
        g[2][2] = 2; g[3][5] = 6; g[6][3] = 2
        return g
    return g
