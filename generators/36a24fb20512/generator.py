"""Generator for 3b4c2228.

Rule: count solid 2×2 sub-blocks of color 3 (overlapping). Output is
3×3 with cells (r,r) for r<count set to 1, else 0.

Combinatorial axes (8): grid_h/w, n_three_blocks, n_decoy_blocks,
decoy_palette_size, position_bias, block_clustering, decoration_density,
asymmetry_force.
Degenerates: zero_three_blocks, all_three_blocks, single_decoy.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "36a24fb20512"
# 1.7.0: defect-lint low_output_diversity — 3 of 4 helpful textures OVERRODE the
# count to 1-2 (n=3 nearly unreachable, a third of the codomain starved) and a
# partial placement silently lowered the real count. Textures now vary decoys
# only; placement is verified (loud raise); the finite-codomain exemption is
# declared under the attribute name the gates actually read.
# (1.6.0: forced count>=1 — n=0 is off-distribution.)
VERSION = "1.7.0"
TASK_ID = "36a24fb20512"
INTRINSIC_OUTPUT_VARIANTS = 3  # canonical count-diagonal rule has exactly 3 non-empty outputs
# The attribute the lint/smoke gates actually read for the finite-codomain
# exemption (INTRINSIC_OUTPUT_VARIANTS above was a name the tools never look at).
EXPECTED_OUTPUT_CODOMAIN = 3
SUMMARY = (
    "Grid with 1-3 solid 2×2 color-3 blocks and 1-3 solid 2×2 blocks "
    "of OTHER colors as decoys. Rule: count the number of (overlapping) "
    "solid 2×2 sub-blocks of color 3 (sliding 2×2 window). Output is "
    "a fresh 3×3 grid: cell (r, r) = 1 for r in 0..count-1, all other "
    "cells = 0. So the output is a diagonal of 1s of length = count."
)

# Rivals: 'output is input' refuted by demos (output is 3×3).
# 'count any color block' refuted by demos with decoy blocks not
# counted. 'count cells (not 2x2 blocks)' refuted by demos where
# count = number of distinct 2×2 blocks, not cells/4. 'fill the
# whole output with count copies' refuted by demos showing diagonal
# placement. 'use color 3 in output' refuted by demos showing color
# 1. 'output is N×N (not always 3×3)' refuted by demos showing fixed
# 3×3 dim. 3 demos with 0, 1, 2, 3 counts pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "count of solid 2×2 3-blocks ∈ 0..3 (rule's diag has at most 3 cells)",
    "≥1 solid block of OTHER color (so input isn't trivially empty)",
    "blocks separated by ≥3 cells (so they're distinct, no merging)",
]

DEGENERATE_TEXTURES = ("zero_three_blocks", "all_three_blocks", "single_decoy")
HELPFUL_TEXTURES = ("balanced", "many_decoys", "edge_clustered", "spread")

AXES = {
    "grid_h":             {"type": "int", "default": "rng 6..10", "valid": "5..12"},
    "grid_w":             {"type": "int", "default": "rng 6..10", "valid": "5..12"},
    "n_three_blocks":     {"type": "int", "default": "rng 1..3", "valid": "0..4"},
    "n_decoy_blocks":     {"type": "int", "default": "rng 1..3", "valid": "0..5"},
    "decoy_palette_size": {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":      {"type": "str", "default": "rng spread|center|edge",
                           "valid": "spread|center|edge"},
    "block_separation":   {"type": "int", "default": "3", "valid": "2..4"},
    "decoration_density": {"type": "float", "default": "0",
                           "valid": "0..0.05"},
    "texture":            {"type": "str", "default": "rng helpful",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # output = 3x3 diagonal encoding n = count of green 2x2 blocks. The
    # canonical task only ever shows n in {1,2,3} (never the all-zero n=0
    # output), so n3_lo>=1 keeps every instance on-distribution.
    if difficulty == "easy":
        h_lo, h_hi, n3_lo, n3_hi = 5, 7, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, n3_lo, n3_hi = 9, 12, 2, 3
    else:
        h_lo, h_hi, n3_lo, n3_hi = 6, 10, 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    # Textures vary DECOYS/POSITIONS only — they must not override the count
    # (that skewed n away from 3 and starved a third of the output codomain).
    n_3 = int(overrides.get("n_three_blocks",
                            ctx.draw_int("n_three_blocks", n3_lo, n3_hi)))
    if texture == "many_decoys":
        n_decoy = 4
    elif texture == "edge_clustered":
        n_decoy = 2
    elif texture == "spread":
        n_decoy = 1
    else:
        n_decoy = int(overrides.get("n_decoy_blocks",
                                    ctx.draw_int("n_decoy_blocks", 1, 3)))
    n_3 = max(1, min(3, n_3))   # >=1: never emit the off-distribution empty output
    n_decoy = max(1, min(5, n_decoy))
    n_decoy_palette = int(overrides.get("decoy_palette_size",
                                        ctx.draw_int("decoy_palette_size", 2, 4)))
    sep = int(overrides.get("block_separation", 3))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    g = full_grid(h, w, 0)
    placed = []
    for _ in range(120):
        if len(placed) >= n_3:
            break
        r, c = _pick_pos(bias, h, w, rng)
        if all(abs(r - pr) >= sep or abs(c - pc) >= sep for pr, pc in placed):
            draw_rect(g, r, c, 2, 2, 3)
            placed.append((r, c))
    if len(placed) < n_3:
        # bias sampling starved — exhaustive scan; a silent short count would
        # change the rule's answer, so failing quietly is not an option.
        for r in range(h - 1):
            for c in range(w - 1):
                if len(placed) >= n_3:
                    break
                if all(abs(r - pr) >= sep or abs(c - pc) >= sep for pr, pc in placed):
                    draw_rect(g, r, c, 2, 2, 3)
                    placed.append((r, c))
        if len(placed) < n_3:
            raise ValueError(f"could not place {n_3} separated 3-blocks on {h}x{w}")
    decoy_pool = [c for c in range(1, 10) if c != 3]
    rng.shuffle(decoy_pool)
    decoy_palette = decoy_pool[:max(1, n_decoy_palette)]
    decoy_placed = []
    for _ in range(80):
        if len(decoy_placed) >= n_decoy:
            break
        color = rng.choice(decoy_palette)
        r, c = _pick_pos(bias, h, w, rng)
        ok = True
        for dr in range(2):
            for dc in range(2):
                if g[r + dr][c + dc] != 0:
                    ok = False
        if ok:
            draw_rect(g, r, c, 2, 2, color)
            decoy_placed.append((r, c))
    if not decoy_placed:
        placed_decoy = False
        for r in range(h - 1):
            for c in range(w - 1):
                if all(g[r + dr][c + dc] == 0 for dr in (0, 1) for dc in (0, 1)):
                    draw_rect(g, r, c, 2, 2, decoy_palette[0])
                    placed_decoy = True
                    break
            if placed_decoy:
                break
        if not placed_decoy:
            raise ValueError("could not place a non-3 decoy block")
    return g


def _pick_pos(bias, h, w, rng):
    if bias == "center":
        cr, cc = h // 2 - 1, w // 2 - 1
        return (max(0, cr + rng.randint(-1, 1)),
                max(0, cc + rng.randint(-1, 1)))
    if bias == "edge":
        edges = [(0, rng.randint(0, w - 2)),
                 (h - 2, rng.randint(0, w - 2)),
                 (rng.randint(0, h - 2), 0),
                 (rng.randint(0, h - 2), w - 2)]
        return rng.choice(edges)
    return (rng.randint(0, h - 2), rng.randint(0, w - 2))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    decoy_pool = [c for c in range(1, 10) if c != 3]
    rng.shuffle(decoy_pool)
    if name == "zero_three_blocks":
        draw_rect(g, 1, 1, 2, 2, decoy_pool[0])
        draw_rect(g, 1, w - 3, 2, 2, decoy_pool[1])
        return g
    if name == "all_three_blocks":
        positions = [(0, 0), (0, 4), (4, 0)]
        for r, c in positions:
            if r + 2 <= h and c + 2 <= w:
                draw_rect(g, r, c, 2, 2, 3)
        return g
    if name == "single_decoy":
        draw_rect(g, h // 2 - 1, w // 2 - 1, 2, 2, decoy_pool[0])
        return g
    return g

def _count_green_blocks(grid):
    return sum(1 for r in range(len(grid) - 1) for c in range(len(grid[0]) - 1)
               if all(grid[r + dr][c + dc] == 3 for dr in (0, 1) for dc in (0, 1)))


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    n = _count_green_blocks(grid)
    if not (1 <= n <= 3):
        msgs.append(f"solid 2x2 green-block count {n} outside 1..3 "
                    "(n=0 emits an off-distribution all-zero output)")
    if not any(v not in (0, 3) for row in grid for v in row):
        msgs.append("no non-3 decoy block")
    return msgs
