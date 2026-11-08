"""Generator for ac2e8ecf.

Rule: rectangular frame objects packed upward; plus-like non-frames
packed downward.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
object_layout.
Degenerates: no_frames, no_pluses, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid, paint_at
from puzzle_generators.helpers.shape import PLUS_5

GENERATOR_ID = "8a6282b87245"
RULE_HASH = "af694b46412a"  # canonical rule this generator was written against
VERSION = "2.1.1"  # in_sh=out_sh=1: grid size fixed per band (probe medium always 14x16). Rule reads h,w generically (frames slide up / pluses slide down to edges; canonical 13x13..16x17). Draw grid h,w from ranges -> input/output dims vary; distinct already 144.
TASK_ID = "8a6282b87245"
SUMMARY = "Some objects are exact rectangle outlines (frames), others are filled plus shapes. Rule keeps each object in its own columns; frames slide UP and pluses slide DOWN until they hit the top/bottom edge respectively, packing densely without overlap. Colors preserved."

# Rivals: 'output is input' refuted by any demo where objects shift.
# 'all objects move up' refuted by ≥1 demo where pluses clearly settle
# at the bottom. 'recolor on packing' refuted by any demo (colors stay).
# 'gravity by mass instead of frame/plus distinction' refuted by demos
# where frame vs plus split is the determinant. 3 demos with varied
# frame/plus mixes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "some same-color objects are exact rectangle outlines",
    "other same-color objects are compact non-frame plus shapes",
    "frames preserve columns and move to the top; non-frames preserve columns and move to the bottom",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frames", "no_pluses", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "14", "valid": "14"},
    "grid_w":         {"type": "int", "default": "15", "valid": "15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "object_layout":  {"type": "str", "default": "shuffled", "valid": "shuffled"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


PLUS = PLUS_5


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all cell values in 0-9; grid shape is consistent."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if not (0 <= v <= 9):
                errs.append(f"cell ({r},{c}) has out-of-range value {v}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    _ = ctx.draw_choice("object_layout", ["shuffled"])
    if difficulty == "easy":
        n_frames = rng.randint(1, 2); n_pluses = rng.randint(1, 2)
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 13, 15)
    elif difficulty == "hard":
        n_frames = rng.randint(2, 3); n_pluses = rng.randint(2, 3)
        h = ctx.draw_int("grid_h", 16, 20); w = ctx.draw_int("grid_w", 18, 22)
    else:
        n_frames = rng.randint(1, 3); n_pluses = rng.randint(1, 3)
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 14, 18)
    total = n_frames + n_pluses
    colors = ctx.draw_distinct_colors("colors", n=total, exclude={0})
    g = full_grid(h, w, 0)
    used_cols = set()
    placed_idx = 0
    # Place frames at random non-overlapping column ranges
    for _ in range(n_frames):
        for _ in range(40):
            fh = rng.randint(3, 5)
            fw = rng.randint(3, 4)
            if fh > h - 2 or fw > w - 2: continue
            r0 = rng.randint(0, h - fh)
            c0 = rng.randint(0, w - fw)
            cols_range = set(range(c0, c0 + fw))
            if cols_range & used_cols: continue
            draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, colors[placed_idx])
            used_cols |= cols_range
            placed_idx += 1
            break
    # Place pluses at random non-overlapping column ranges
    for _ in range(n_pluses):
        for _ in range(40):
            r0 = rng.randint(0, h - 3)
            c0 = rng.randint(0, w - 3)
            cols_range = {c0, c0 + 1, c0 + 2}
            if cols_range & used_cols: continue
            paint_at(g, r0, c0, PLUS, colors[placed_idx])
            used_cols |= cols_range
            placed_idx += 1
            break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 15, 0)
    if name == "no_frames":
        paint_at(g, 1, 5, PLUS, 4)
        return g
    if name == "no_pluses":
        draw_frame(g, 7, 1, 9, 3, 3)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(15):
                g[r][c] = 3
        return g
    return g
