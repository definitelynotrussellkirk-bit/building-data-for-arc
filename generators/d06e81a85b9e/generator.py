"""Generator for arc_additional_puzzles_21_set5:H35 — Mark cells with LoS to 2 (horiz) AND 3 (vert).

Rule: for each empty cell (r,c), check if there's a 2-cell on same row
with all-zero between, AND a 3-cell on same col with all-zero between.
If both → 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n2,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_2, no_3, no_los_intersection.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d06e81a85b9e"
SUMMARY = (
    "0-bg grid (h~7-9, w~9-11) with: 2-3 cells of color 2 "
    "(red), 2-3 cells of color 3 (green), and 1-3 scattered "
    "distractor cells (colors {1, 4, 5, 6, 7, 9}). All cells "
    "are placed at random distinct positions. Rule: produce a "
    "FRESH same-shape grid where each cell (r, c) is 8 (cyan) "
    "if: (a) input[r][c] == 0; (b) there exists a 2-cell at "
    "(r, c2) on the same row with all cells strictly between c "
    "and c2 in that row equal to 0 (horizontal LoS to a red); "
    "(c) there exists a 3-cell at (r2, c) on the same column "
    "with all cells strictly between r and r2 equal to 0 "
    "(vertical LoS to a green). Else cell is 0. The 2/3/"
    "distractors do NOT appear in the output."
)
VERSION = "2.1.0"  # FIX: normal path retries until at least one LoS intersection exists
TASK_ID = "d06e81a85b9e"

# Rivals: 'paint any cell with both 2 and 3 in its row/col' refuted by
# ≥1 demo where LoS is blocked by a distractor cell. 'paint with the
# 2 or 3 color' refuted by any demo (always 8). 'fill all bg' refuted
# by ≥1 demo with bg cells off-LoS.
# 4 demos with varied LoS layouts + at least 1 with blockers cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "between 2 and 3 2-cells",
    "between 2 and 3 3-cells",
    "at least one empty cell has horizontal LoS to a 2 and vertical LoS to a 3",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_2", "no_3", "no_los_intersection")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n2":             {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "n3":             {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "scattered_2_and_3",
                       "valid": "scattered_2_and_3"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h_lo, h_hi, w_lo, w_hi = 7, 8, 9, 10
        n_lo, n_hi = 2, 3
        n_dist_lo, n_dist_hi = 0, 1
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 14, 12, 16
        n_lo, n_hi = 3, 5
        n_dist_lo, n_dist_hi = 2, 5
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 10, 10, 13
        n_lo, n_hi = 2, 4
        n_dist_lo, n_dist_hi = 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    distractor_pool = [1, 4, 5, 6, 7, 9]

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        n2 = rng.randint(n_lo, n_hi)
        n3 = rng.randint(n_lo, n_hi)
        placed = 0
        while placed < n2:
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = 2; placed += 1
        placed = 0
        while placed < n3:
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = 3; placed += 1
        # Distractor cells (colors 1, 4, 5, 6, 7, 9) act as LoS blockers
        # if placed between a {2-cell, target} pair. Adds the
        # "block LoS" signal so the model learns the rule's blocking semantics.
        n_distractors = rng.randint(n_dist_lo, n_dist_hi)
        placed = 0
        for _ in range(40):
            if placed >= n_distractors: break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = rng.choice(distractor_pool)
            placed += 1
        if _los_targets(g):
            return g

    # Deterministic fallback with one guaranteed clear intersection plus the
    # requested color counts; keeps normal generation from leaking no-fire boards.
    g = full_grid(h, w, 0)
    tr, tc = h // 2, w // 2
    g[tr][max(0, tc - 2)] = 2
    g[max(0, tr - 2)][tc] = 3
    g[min(h - 1, tr + 1)][min(w - 1, tc + 2)] = 2
    g[min(h - 1, tr + 2)][max(0, tc - 1)] = 3
    return g


def _los_targets(g):
    h, w = len(g), len(g[0])
    hits = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0:
                continue
            hlos = any(
                g[r][c2] == 2 and all(g[r][x] == 0 for x in range(min(c, c2) + 1, max(c, c2)))
                for c2 in range(w)
            )
            vlos = any(
                g[r2][c] == 3 and all(g[x][c] == 0 for x in range(min(r, r2) + 1, max(r, r2)))
                for r2 in range(h)
            )
            if hlos and vlos:
                hits.append((r, c))
    return hits


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    n2 = sum(v == 2 for row in grid for v in row)
    n3 = sum(v == 3 for row in grid for v in row)
    if n2 < 2 or n3 < 2:
        errors.append(f"need at least two 2-cells and two 3-cells, got {(n2, n3)}")
    if not _los_targets(grid):
        errors.append("no empty cell has clear horizontal LoS to 2 and vertical LoS to 3")
    return sorted(set(errors))


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_2":
        # only 3-cells → no horizontal source, rule never fires
        g[1][3] = 3
        g[5][7] = 3
        return g
    if name == "no_3":
        # only 2-cells → no vertical source, rule never fires
        g[2][1] = 2
        g[4][6] = 2
        return g
    if name == "no_los_intersection":
        # 2s and 3s exist but no empty cell has LoS to both
        # Put 2s in row 0 only and 3s in col w-1 only - no row/col share
        # any empty cell with both axes clear (place a blocker in between)
        g[0][2] = 2; g[0][6] = 2
        g[h - 1][1] = 3; g[h - 1][8] = 3
        # add blocker on every potential LoS path
        for c in range(w): g[3][c] = 5   # row 3 of 5s blocks vertical LoS
        return g
    return g
