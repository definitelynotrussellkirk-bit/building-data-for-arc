"""Generator for arc_puzzle_bank_21_set21_bundle:medium_p03 — translate obj by 1→2 vector.

Rule: a color-1 marker and a color-2 marker define vector (p2 - p1). The
largest non-{1, 2} obj is doubled: original cells stay, plus translated
copy at the vector offset.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: zero_vector (1 and 2 markers coincide → vector is (0,0);
rule's translated copy lands on original, no visible doubling),
missing_marker (only 1 OR only 2 → vector undefined, no translation),
no_obj (no non-{1,2} object → rule has nothing to translate, output
keeps only markers).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c6e1b7fd77a"
VERSION = "1.3.0"  # v1.1 occasionally sampled a 5-cell-tall motif in the lower half, making randint's placement range empty.
TASK_ID = "5c6e1b7fd77a"

SUMMARY = "1 color-1 marker + 1 color-2 marker (vector) + 1 motif in some other color."

INVARIANTS = [
    "background is 0",
    "exactly one color-1 marker and one color-2 marker at distinct positions",
    "exactly one connected motif (3-5 cells) in some non-{0, 1, 2} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("zero_vector", "missing_marker", "no_obj")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":            {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "vector_plus_motif",
                          "valid": "vector_plus_motif"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|zero_vector|missing_marker|no_obj"},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _in_bounds(cells, h, w):
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 10, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        r1 = rng.randint(0, 1); c1 = rng.randint(w - 3, w - 1)
        r2 = rng.randint(2, 3); c2 = rng.randint(w - 3, w - 1)
        if (r1, c1) == (r2, c2): continue
        g[r1][c1] = 1
        g[r2][c2] = 2
        color = rng.choice([3, 4, 5, 6, 7, 8, 9])
        cells = _build_motif(rng, rng.randint(3, 5))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        dr, dc = r2 - r1, c2 - c1
        norm = [(r - min(rs), c - min(cs)) for r, c in cells]
        for _ in range(120):
            # Sample from the full legal original bbox, then validate both the
            # input motif and its translated copy. This avoids empty ranges for
            # tall motifs while preserving the intended bottom-left tendency.
            r0_min, r0_max = 0, h - sh
            if r0_min > r0_max:
                continue
            c0_min, c0_max = 0, max(0, w // 2 - sw)
            if c0_min > c0_max:
                continue
            r0 = rng.randint(r0_min, r0_max)
            if rng.random() < 0.75 and h // 2 <= r0_max:
                r0 = rng.randint(h // 2, r0_max)
            c0 = rng.randint(c0_min, c0_max)
            cells_p = [(r0 + r, c0 + c) for r, c in norm]
            cells_t = [(r + dr, c + dc) for r, c in cells_p]
            if not _in_bounds(cells_p, h, w) or not _in_bounds(cells_t, h, w):
                continue
            if set(cells_p) & set(cells_t):
                continue
            if any(g[r][c] != 0 for r, c in cells_p):
                continue
            if any(g[r][c] != 0 for r, c in cells_t):
                continue
            for r, c in cells_p:
                g[r][c] = color
            return g
    raise ValueError("could not realize layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-1 cell, exactly one color-2 cell, >=3 other cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    motif = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1, 2)]
    if len(ones) != 1:
        errs.append(f"expected exactly 1 color-1 marker, found {len(ones)}")
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 marker, found {len(twos)}")
    if len(motif) < 1:
        errs.append("no motif cells found (non-{0,1,2} colors)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "zero_vector":
        # 1 and 2 markers at near-coincident positions (vector ≈ 0) —
        # rule's translated copy lands near original, no visible doubling.
        g[1][7] = 1
        g[1][7] = 2  # overwrite — they're at same cell conceptually
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][2 + dc] = 4
        return g
    if name == "missing_marker":
        # Only color-1 marker present; no color-2 — vector undefined.
        g[1][7] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][2 + dc] = 4
        return g
    if name == "no_obj":
        # No non-{1,2} object — rule has nothing to translate.
        g[1][7] = 1
        g[3][7] = 2
        return g
    return g
