"""Generator for arc_puzzle_bank_21_set10_e:easy_j01.

Rule: for each non-bg cell at (r0, c0, color), set out[r][c] = color
for all (r, c) with |r - r0| + |c - c0| ≤ 2 (in bounds).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, overlapping_diamonds, seed_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04204350555e"
VERSION = "2.1.0"
TASK_ID = "04204350555e"
SUMMARY = (
    "0-bg grid (h ∈ 5-7, w ∈ 7-9) with: "
    "N ∈ 1-2 ISOLATED NON-BG SEED "
    "CELLS, each in a color drawn at "
    "random from {2..9}, placed at "
    "random positions with MANHATTAN-"
    "DISTANCE >4 between any pair (so "
    "their radius-2 diamonds don't "
    "overlap). Rule (FOR EACH NON-BG "
    "SEED CELL AT (R0, C0) WITH "
    "COLOR k, PAINT EVERY CELL (R, "
    "C) WITHIN MANHATTAN DISTANCE 2 "
    "WITH COLOR k — A 13-CELL "
    "DIAMOND): For EACH non-bg cell "
    "at (r0, c0) with color k: For "
    "EVERY (r, c) WHERE |r-r0| + "
    "|c-c0| ≤ 2 (in-bounds): PAINT "
    "g[r][c] = k. The seed cell "
    "itself stays k; the 4 cells "
    "at distance 1 (cardinal "
    "neighbors) get k; the 8 "
    "cells at distance 2 (longer "
    "diagonals + outer cardinals) "
    "get k. Out-of-bounds cells "
    "drop. Net: each seed becomes "
    "a 13-cell colored diamond "
    "(rhombus); the rest of the "
    "grid stays 0."
)

# Rivals: 'diamonds never collide' refuted by overlap boards where the
# later scan-order seed overwrites the shared cells. 'diamonds always
# fit' refuted by edge/corner seeds with clipped diamonds. 'radius
# scales with something' refuted (always 2). 3 demos incl. >=1
# overlap or clipped board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "1-3 non-bg seed cells",
    "plain boards: seeds > 4 apart (disjoint diamonds); overlap "
    "boards: two seeds 3-4 apart (later scan-order seed wins)",
]

DEGENERATE_TEXTURES = ("no_seeds", "seed_at_corner")
HELPFUL_TEXTURES = ("plain", "overlap")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 5..7 (hard 6..9)",
                "valid": "4..10", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 7..9 (hard 8..12)",
                "valid": "6..12", "doc": "Grid width."},
    "n_seeds": {"type": "int", "default": "rng 1..3", "valid": "1..3",
                "doc": "Diamond centers."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|overlap|no_seeds|seed_at_corner",
                "doc": "overlap: two diamonds collide (scan order wins)."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain", "overlap"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 12)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    n = int(overrides.get("n_seeds", ctx.draw_int("n_seeds", 1, 3)))
    placed = []
    for _ in range(60):
        if len(placed) >= n:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if texture == "overlap" and len(placed) == 1:
            # second seed 3-4 away: diamonds collide, later scan-order
            # seed overwrites the shared cells (previously unreachable)
            d = abs(r - placed[0][0]) + abs(c - placed[0][1])
            if not 3 <= d <= 4:
                continue
        elif any(abs(r - pr) + abs(c - pc) <= 4 for pr, pc in placed):
            continue
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice(palette)
        placed.append((r, c))
    if not placed:
        g[h // 2][w // 2] = rng.choice(palette)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not (1 <= len(seeds) <= 3):
        errs.append("expected 1-3 seed cells")
    if difficulty != "overlap":
        for i, (r1, c1, _v1) in enumerate(seeds):
            for r2, c2, _v2 in seeds[i + 1:]:
                if abs(r1 - r2) + abs(c1 - c2) <= 2:
                    errs.append("seed cells should not be immediately adjacent")
                    return errs
    return errs



def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_seeds       — blank: identity output.
    seed_at_corner — most diamond cells clip off-board.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 5, 7)
    w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        return g
    corner = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))[rng.randrange(4)]
    g[corner[0]][corner[1]] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    return g
