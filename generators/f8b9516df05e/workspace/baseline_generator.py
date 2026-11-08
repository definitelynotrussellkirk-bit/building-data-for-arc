"""Generator for arc_puzzle_bank_sixteenth_21_bundle:easy_112_cast_rightward_rays_until_blockers.

Rule: each row has a colored emitter; rays extend right in emitter color
until they hit a gray (8) blocker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rays,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocker, blocker_left_of_emitter, no_emitter.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f8b9516df05e"
VERSION = "3.1.0"  # bigger grids + more rays + post-blocker decoy cells (rule preserves beyond the first blocker)
TASK_ID = "f8b9516df05e"
SUMMARY = (
    "0-bg grid (h~7-10, w~9-13) with 3-5 "
    "ACTIVE ROWS, each containing exactly two "
    "marker cells: (a) a single EMITTER cell "
    "in some non-{0, 8} color at column c0; "
    "(b) a single COLOR-8 (gray) BLOCKER cell "
    "at column c1 > c0 with c1 - c0 ≥ 2 (so "
    "there's a gap between emitter and "
    "blocker). Cells between emitter and "
    "blocker, and cells outside the (c0, c1) "
    "span are initially 0; cells beyond "
    "the first blocker may contain decoys "
    "that must stay unchanged. Other rows "
    "entirely 0. Rule: for each ACTIVE ROW, "
    "FIND the emitter and blocker. CAST a RAY "
    "from the emitter to the RIGHT in the "
    "emitter's color: fill every cell from "
    "c0+1 through c1-1 (inclusive) with the "
    "emitter's color. The emitter cell stays; "
    "the blocker (color 8) stays; cells "
    "beyond the blocker stay as they were. Net: each "
    "active row gets a colored ray from "
    "emitter rightward until it hits the gray "
    "blocker."
)

INVARIANTS = [
    "background is 0",
    "blocker color is 8",
    "active rows have one non-8 emitter left of one blocker",
    "cells between emitter and first blocker are initially empty",
    "at least one active row has post-blocker decoy cells preserved by the rule",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocker", "blocker_left_of_emitter", "no_emitter")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 10-14 med / 13-20 hard", "valid": "3..22"},
    "grid_w":         {"type": "int", "default": "9-13 easy / 12-17 med / 15-24 hard", "valid": "5..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "rays":           {"type": "int", "default": "3-4 easy / 4-7 med / 6-12 hard", "valid": "1..18"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "emitter_then_blocker",
                       "valid": "emitter_then_blocker"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "density":        {"type": "str", "default": "row_pairs", "valid": "row_pairs"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blocker|blocker_left_of_emitter|no_emitter"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 9, 13)
        target = min(ctx.draw_int("rays", 3, 4), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 20); w = ctx.draw_int("grid_w", 15, 24)
        target = min(ctx.draw_int("rays", 6, 12), h)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 12, 17)
        target = min(ctx.draw_int("rays", 4, 7), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    for i, r in enumerate(rows):
        c0 = rng.randint(0, w - 4)
        c1_hi = w - 2 if i == 0 else w - 1
        c1 = rng.randint(c0 + 2, c1_hi)
        g[r][c0] = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        g[r][c1] = 8
        # decoy cells BEYOND the first blocker (any non-0 color incl 8); the rule
        # fills only up to the first blocker, so these are preserved untouched.
        if i == 0:
            g[r][c1 + 1] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for c in range(c1 + 1, w):
            if g[r][c] == 0 and rng.random() < 0.25:
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    w = len(grid[0])
    active = 0
    decoy_after = 0
    for row in grid:
        emitters = [c for c, v in enumerate(row) if v not in (0, 8)]
        blockers = [c for c, v in enumerate(row) if v == 8]
        if not emitters or not blockers:
            continue
        emit = emitters[0]
        right_blockers = [c for c in blockers if c > emit]
        if not right_blockers:
            continue
        active += 1
        blocker = min(right_blockers)
        if blocker - emit < 2:
            errs.append("emitter and blocker should leave a visible gap")
        if any(row[c] != 0 for c in range(emit + 1, blocker)):
            errs.append("ray path before first blocker should be empty")
        if any(row[c] != 0 for c in range(blocker + 1, w)):
            decoy_after += 1
    if active < 3:
        errs.append("expected at least three active ray rows")
    if decoy_after == 0:
        errs.append("expected at least one post-blocker decoy")
    return errs



def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_blocker":
        # emitter without rightward 8-blocker → ray would extend off the grid
        g[2][1] = 3
        g[5][2] = 6
        return g
    if name == "blocker_left_of_emitter":
        # 8-blocker left of emitter → ray fired right has no blocker to stop at
        g[2][1] = 8; g[2][5] = 4
        g[5][2] = 8; g[5][6] = 6
        return g
    if name == "no_emitter":
        # blockers but no emitters → no rays to cast
        g[2][5] = 8
        g[5][6] = 8
        return g
    return g
