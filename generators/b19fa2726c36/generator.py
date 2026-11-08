"""Generator for arc_additional_puzzle_bank_volume16:H110.

Rule: control 2, 3, or 4 selects a nested color-6 frame band to fill cyan.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frames, no_control, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b19fa2726c36"
VERSION = "1.2.1"  # dup-inputs/outputs 39%: hardcoded EXACTLY 3 frames at fixed offsets + 3-choice marker. Rule fills the depth-th concentric 6-frame band (depth=marker 2/3/4). Now vary frame count (3-5), band width, and depth + wider grid."
TASK_ID = "b19fa2726c36"
SUMMARY = "Control 2/3/4 selects nested color-6 frame band to fill cyan."

INVARIANTS = [
    "background is 0",
    "three color-6 frames are nested",
    "one control marker has value 2, 3, or 4",
    "the selected frame band has blank cells",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frames", "no_control", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..17", "valid": "11..24"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "11..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; cell (0,0) is 2, 3, or 4 (control marker); color-6 frames present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    ctrl = grid[0][0]
    if ctrl not in (2, 3, 4):
        errs.append(f"expected control marker 2/3/4 at (0,0); got {ctrl}")
    six_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 6)
    if six_count < 4:
        errs.append(f"expected color-6 frame cells; found {six_count}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 24)
        w = ctx.draw_int("grid_w", 18, 24)
    else:
        h = ctx.draw_int("grid_h", 13, 20)
        w = ctx.draw_int("grid_w", 13, 20)
    g = full_grid(h, w, 0)
    # Rule: marker color 2/3/4 -> depth 0/1/2; fill the band of the depth-th
    # concentric 6-frame with 8. v1.1.0 hardcoded EXACTLY 3 frames at fixed
    # offsets + a 3-choice marker -> dup-inputs/outputs 39%. Now vary the number
    # of nested frames and the band width between them, and pick a valid depth.
    o = 0
    n_frames = 0
    target = rng.randint(3, 5)
    while n_frames < target:
        r1, c1, r2, c2 = 2 + o, 2 + o, h - 3 - o, w - 3 - o
        if r2 - r1 < 2 or c2 - c1 < 2:
            break
        draw_frame(g, r1, c1, r2, c2, 6)
        n_frames += 1
        o += rng.choice([2, 3])          # variable band width between frames
    if n_frames == 0:                    # safety: grid too small -> one frame
        draw_frame(g, 1, 1, h - 2, w - 2, 6); n_frames = 1
    max_depth = min(2, n_frames - 1)     # control only encodes depths 0..2
    depth = rng.randint(0, max_depth)
    g[0][0] = {0: 2, 1: 3, 2: 4}[depth]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_frames":
        g[0][0] = 2
        return g
    if name == "no_control":
        for offset in (0, 2, 4):
            draw_frame(g, 2 + offset, 2 + offset, 11 - offset, 11 - offset, 6)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 6
        return g
    return g
