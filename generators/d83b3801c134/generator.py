"""Generator for arc_puzzle_bank_seventh21:M46 — marker-vector translation.

Rule: 1-cell = src marker, 2-cell = dst marker. Translate every 3-cell
by (dst-src). Output: empty grid + translated 3s.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_blob, src_equals_dst.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "d83b3801c134"
VERSION = "1.3.1"  # add executable self_check for marker/vector/in-bounds invariants
TASK_ID = "d83b3801c134"
SUMMARY = "1-marker (src) + 2-marker (dst) + a 3-blob; translation lands in-bounds."

INVARIANTS = [
    "background is 0",
    "exactly one 1-cell, exactly one 2-cell, ≥2 3-cells in one or more connected blobs",
    "translated cells are in-bounds (so output is non-empty)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_blob", "src_equals_dst")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "blob_size":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "src_dst_with_blob",
                       "valid": "src_dst_with_blob"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_blob|src_equals_dst"},
}


def _choose_inbounds_vector_and_markers(rng, h, w, blob_cells, occupied):
    """Pick src/dst markers whose (1->2) vector keeps every color-3 cell in-bounds."""
    min_r = min(r for r, _ in blob_cells); max_r = max(r for r, _ in blob_cells)
    min_c = min(c for _, c in blob_cells); max_c = max(c for _, c in blob_cells)
    drs = list(range(-min_r, h - max_r))
    dcs = list(range(-min_c, w - max_c))
    vectors = [(dr, dc) for dr in drs for dc in dcs if (dr, dc) != (0, 0)]
    rng.shuffle(vectors)
    free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in occupied]
    free_set = set(free)
    for dr, dc in vectors:
        candidates = [(r, c) for (r, c) in free
                      if (r + dr, c + dc) in free_set and (r + dr, c + dc) != (r, c)]
        if candidates:
            src = rng.choice(candidates)
            dst = (src[0] + dr, src[1] + dc)
            return src, dst
    return None, None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # rule = vector (color1 -> color2) applied to ALL color-3 cells. Old gen had
    # ONE small 3-blob + constrained src/dst -> dup 47%. Widen grids, place 1-3
    # color-3 blobs, and let src/dst be any distinct cells (free vector).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 8, 10)
        n_blobs = ctx.draw_int("n_blobs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 15)
        n_blobs = ctx.draw_int("n_blobs", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 13)
        n_blobs = ctx.draw_int("n_blobs", 1, 3)
    rng = ctx.draw_rng("layout")
    # Choose the (1->2) vector only AFTER placing the 3-blobs, so every translated
    # color-3 cell lands in-bounds. The old gen picked a free src/dst vector first,
    # which translated at least one 3-cell off the board in 804/1000 seeds —
    # violating the generator's own in-bounds invariant.
    for _attempt in range(40):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        blob_cells: set[tuple[int, int]] = set()
        for _ in range(n_blobs):
            blob = grow_blob(rng, h, w, used, rng.randint(2, 5), max_attempts=100)
            if blob is None:
                continue
            blob_cells |= blob
            for r, c in blob:
                g[r][c] = 3
                for hr in (-1, 0, 1):
                    for hc in (-1, 0, 1):
                        used.add((r + hr, c + hc))
        if len(blob_cells) < 2:
            continue
        src, dst = _choose_inbounds_vector_and_markers(rng, h, w, blob_cells, used)
        if src is None:
            continue
        g[src[0]][src[1]] = 1
        g[dst[0]][dst[1]] = 2
        return g

    # deterministic fallback: a 2-cell blob and a down-right vector that stays
    # in-bounds, preserving the rule-firing invariant rather than dropping rows.
    g = full_grid(max(h, 7), max(w, 8), 0)
    g[1][1] = 1; g[2][2] = 2
    g[4][4] = 3; g[4][5] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for marker-vector translation instances."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]

    p1 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    p2 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    cells3 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    bad_values = sorted({v for row in grid for v in row if v not in (0, 1, 2, 3)})
    if bad_values:
        errs.append(f"unexpected colors outside {{0,1,2,3}}: {bad_values}")
    if len(p1) != 1:
        errs.append(f"expected exactly one color-1 src marker, got {len(p1)}")
    if len(p2) != 1:
        errs.append(f"expected exactly one color-2 dst marker, got {len(p2)}")
    if len(cells3) < 2:
        errs.append(f"expected at least two color-3 cells, got {len(cells3)}")
    if len(p1) == 1 and len(p2) == 1 and cells3:
        dr = p2[0][0] - p1[0][0]
        dc = p2[0][1] - p1[0][1]
        if (dr, dc) == (0, 0):
            errs.append("src and dst markers produce a zero translation vector")
        oob = [(r, c) for r, c in cells3 if not (0 <= r + dr < h and 0 <= c + dc < w)]
        if oob:
            sample = oob[:5]
            errs.append(f"translated color-3 cells leave the grid: {sample}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # blob only, no 1/2 markers → no translation vector
        g[3][3] = 3; g[3][4] = 3; g[4][3] = 3
        return g
    if name == "no_blob":
        # markers but no 3-blob → nothing to translate
        g[1][1] = 1
        g[5][6] = 2
        return g
    if name == "src_equals_dst":
        # both markers at same cell → vector zero, rule identity
        g[3][3] = 1
        g[3][3] = 2   # overwrites src
        g[5][5] = 3; g[5][6] = 3; g[6][5] = 3
        return g
    return g
