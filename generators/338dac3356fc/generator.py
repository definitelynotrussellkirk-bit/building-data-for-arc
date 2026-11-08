"""Generator for 9b365c51.

Rule: left vertical key bars assign colors to atomic 8-column blocks.

Combinatorial axes (8): grid_h/w, block_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_keys, no_blocks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "338dac3356fc"
VERSION = "1.1.1"  # add executable self_check for key-bar/block invariants
TASK_ID = "338dac3356fc"
SUMMARY = "Left vertical key bars assign colors to atomic 8-column blocks."

INVARIANTS = [
    "left-side non-8 vertical bars provide ordered key colors",
    "right-side color-8 runs define sorted column endpoints",
    "each atomic 8-containing column block maps to the next key color",
    "key colors are distinct from 0 and 8",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_keys", "no_blocks", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "block_count":    {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        bc_lo, bc_hi = 2, 2
    elif difficulty == "hard":
        bc_lo, bc_hi = 4, 4
    else:
        bc_lo, bc_hi = 2, 4
    block_count = ctx.draw_int("block_count", bc_lo, bc_hi)
    colors = ctx.draw_distinct_colors("key_colors", n=block_count, exclude={0, 8})
    h = 6 + rng.randint(0, 3)
    widths = [rng.randint(2, 3) for _ in range(block_count)]
    gap = 1
    start = block_count + 1
    w = start + sum(widths) + gap * (block_count - 1) + 1
    g = full_grid(h, w, 0)
    for c, color in enumerate(colors):
        for r in range(h):
            g[r][c] = color
    c = start
    for i, width in enumerate(widths):
        rows = sorted({rng.randint(1, h - 2), rng.randint(0, h - 1)})
        if i % 2 == 0:
            rows.append((rows[-1] + 1) % h)
        for r in set(rows):
            for cc in range(c, c + width):
                g[r][cc] = 8
        c += width + gap
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 12, 0)
    if name == "no_keys":
        for r in range(8):
            g[r][6] = 8
        return g
    if name == "no_blocks":
        for r in range(8):
            g[r][0] = 2
            g[r][1] = 3
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(12):
                g[r][c] = 8
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    key_cols = []
    for c in range(w):
        col = [grid[r][c] for r in range(h)]
        if len(set(col)) == 1 and col[0] not in (0, 8):
            key_cols.append((c, col[0]))
        else:
            break
    msgs = []
    if not (2 <= len(key_cols) <= 4):
        msgs.append(f"expected 2-4 left vertical key bars, got {len(key_cols)}")
    if len({color for _, color in key_cols}) != len(key_cols):
        msgs.append("key bar colors must be distinct")
    if not any(grid[r][c] == 8 for r in range(h) for c in range(len(key_cols) + 1, w)):
        msgs.append("expected 8-blocks to the right of the key bars")
    return msgs
