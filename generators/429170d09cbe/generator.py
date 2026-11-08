"""Generator for 0607ce86.

Rule: noisy repeated tile is reconstructed by periodic majority vote.

Combinatorial axes (8): row_period, col_period, palette_kind,
anchor_corner, asymmetry_force, palette_size, row_repeats,
col_repeats.
Degenerates: no_noise, all_noise, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "429170d09cbe"
VERSION = "1.2.1"
TASK_ID = "429170d09cbe"
SUMMARY = "A tile (row period 4-8, col period 5-10) is repeated 2-3× along each axis starting at row offset 0-2. Some cells are noised. Rule infers the best tile via periodic majority vote and outputs the clean tiled grid (noise cells replaced by majority for their residue position)."

# Rivals: 'output is input' refuted by any demo with noise cells.
# 'output the first period only' refuted by any demo (output is full).
# 'use bg as fill' refuted by any demo (noise replaced by majority).
# 'majority over rows only' refuted by ≥1 demo where col period > 1.
# 3 demos with varied periods + noise cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the active region starts at row offset 0, 1, or 2",
    "the hidden tile has row period 4 to 8 and column period 5 to 10",
    "the tile repeats at least twice along both axes",
    "noise leaves every periodic slot majority-supported",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_noise", "all_noise", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "row_period":     {"type": "int", "default": "rng 4..8", "valid": "4..8"},
    "col_period":     {"type": "int", "default": "rng 5..9", "valid": "5..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "row_repeats":    {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "col_repeats":    {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _make_tile(pr, pc, palette):
    tile = []
    for r in range(pr):
        row = []
        for c in range(pc):
            idx = (r * 3 + c * 5 + (r * c)) % len(palette)
            row.append(palette[idx])
        tile.append(row)
    for r in range(pr):
        tile[r][0] = palette[(r + 1) % len(palette)]
    for c in range(pc):
        tile[pr - 1][c] = palette[(c + 2) % len(palette)]
    return tile


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has ≥2 distinct non-bg colors (the periodic tile uses ≥2 colors)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w)) - {0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-bg tile colors, got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("noise")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        pr_lo, pr_hi, pc_lo, pc_hi = 4, 5, 5, 6
    elif difficulty == "hard":
        pr_lo, pr_hi, pc_lo, pc_hi = 7, 8, 8, 9
    else:
        pr_lo, pr_hi, pc_lo, pc_hi = 4, 8, 5, 9
    r0 = ctx.draw_int("row_offset", 0, 2)
    pr = ctx.draw_int("row_period", pr_lo, pr_hi)
    pc = ctx.draw_int("col_period", pc_lo, pc_hi)
    rr = ctx.draw_int("row_repeats", 2, 3)
    cc = ctx.draw_int("col_repeats", 2, 3)
    palette = ctx.draw_distinct_colors("palette", n=4, exclude=set())
    h = r0 + pr * rr
    w = pc * cc
    g = full_grid(h, w, 0)
    tile = _make_tile(pr, pc, palette)
    for kr in range(rr):
        for kc in range(cc):
            for r in range(pr):
                for c in range(pc):
                    g[r0 + kr * pr + r][kc * pc + c] = tile[r][c]
    noise_count = rng.randint(2, min(6, pr * pc))
    used_slots = set()
    for _ in range(noise_count):
        for _attempt in range(50):
            rr0 = rng.randrange(pr)
            cc0 = rng.randrange(pc)
            if (rr0, cc0) not in used_slots:
                used_slots.add((rr0, cc0))
                break
        kr = rng.randrange(rr)
        kc = rng.randrange(cc)
        r = r0 + kr * pr + rr0
        c = kc * pc + cc0
        choices = [v for v in range(10) if v != g[r][c]]
        g[r][c] = rng.choice(choices)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_noise":
        for r in range(h):
            for c in range(w):
                g[r][c] = (r * 3 + c * 5) % 4
        return g
    if name == "all_noise":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.randint(0, 9)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
