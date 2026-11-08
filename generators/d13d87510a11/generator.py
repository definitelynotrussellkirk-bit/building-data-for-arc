"""Generator for arc_puzzle_bank_21_set7_s:S7_M4 — translate by anchor vector.

Rule: 1-cell = src anchor, 2-cell = dst anchor, 3-blob = template.
Output: empty grid + the 3-blob translated by (dst-src) painted in 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_src, no_dst, no_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "d13d87510a11"
VERSION = "2.1.1"  # dup 44%: src forced top-left / dst bottom-right -> large vector clips translated blob OOB -> truncated dup outputs; the "fits in bounds" invariant was claimed but NOT enforced. Now derive (dr,dc) from blob bbox so the translated blob always fits, place src/dst freely, widen blob size 2-6 + grid 6-14.
TASK_ID = "d13d87510a11"
SUMMARY = (
    "0-bg grid with: (a) ONE color-1 (blue) SRC anchor cell; (b) ONE "
    "color-2 (red) DST anchor cell at a different position; (c) one "
    "TEMPLATE blob of 2-5 cells in color 3, placed adjacent to or "
    "around the src anchor. Rule: compute translation vector (dr, dc) "
    "= (dst.r - src.r, dst.c - src.c). Translate the 3-blob by (dr, "
    "dc). On a fresh 0-canvas, paint the translated blob in color 2. "
    "Anchors are removed in output. Blob's translated position fits "
    "in-bounds."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-1 src anchor",
    "exactly one color-2 dst anchor",
    "≥1 connected color-3 blob (template)",
    "blob translated by (dst-src) fits within grid bounds",
    "(dst - src) is non-zero (translation is meaningful)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_src", "no_dst", "no_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "src_dst_template",
                       "valid": "src_dst_template"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1 src, one color-2 dst, ≥1 color-3 template cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    counts = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            counts[v] = counts.get(v, 0) + 1
    if counts.get(1, 0) != 1:
        errs.append(f"expected exactly 1 color-1 src anchor; found {counts.get(1,0)}")
    if counts.get(2, 0) != 1:
        errs.append(f"expected exactly 1 color-2 dst anchor; found {counts.get(2,0)}")
    if counts.get(3, 0) < 1:
        errs.append(f"expected ≥1 color-3 template cell; found {counts.get(3,0)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 7, 9)
        b_lo, b_hi = 2, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
        b_lo, b_hi = 3, 6
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 9, 13)
        b_lo, b_hi = 2, 5
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    # blob first (template color 3); its bbox bounds the legal translation so the
    # translated copy ALWAYS fits in-bounds (was claimed invariant, never enforced).
    blob = grow_blob(rng, h, w, used, rng.randint(b_lo, min(b_hi, h * w // 3)),
                     max_attempts=120)
    if blob is None:
        return g
    minr = min(r for r, _ in blob); maxr = max(r for r, _ in blob)
    minc = min(c for _, c in blob); maxc = max(c for _, c in blob)
    # legal vector keeps the translated bbox on the canvas
    dr_lo, dr_hi = -minr, (h - 1) - maxr
    dc_lo, dc_hi = -minc, (w - 1) - maxc
    dr, dc = 0, 0
    for _ in range(40):
        dr = rng.randint(dr_lo, dr_hi); dc = rng.randint(dc_lo, dc_hi)
        if (dr, dc) != (0, 0):
            break
    if (dr, dc) == (0, 0):           # degenerate canvas; force a 1-step shift if room
        if dc_hi > 0:
            dc = 1
        elif dr_hi > 0:
            dr = 1
    for r, c in blob:
        g[r][c] = 3
        used.add((r, c))
    # src anywhere free; dst = src + (dr,dc), also in bounds and free
    sr_lo, sr_hi = max(0, -dr), min(h - 1, (h - 1) - dr)
    sc_lo, sc_hi = max(0, -dc), min(w - 1, (w - 1) - dc)
    src = dst = None
    for _ in range(200):
        sr = rng.randint(sr_lo, sr_hi); sc = rng.randint(sc_lo, sc_hi)
        s = (sr, sc); d = (sr + dr, sc + dc)
        if s in used or d in used or s == d:
            continue
        src, dst = s, d
        break
    if src is None:
        return g
    g[src[0]][src[1]] = 1
    g[dst[0]][dst[1]] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_src":
        # missing 1-cell src anchor → no anchor for translation vector
        g[5][6] = 2  # dst
        g[3][3] = 3; g[3][4] = 3  # blob
        return g
    if name == "no_dst":
        # missing 2-cell dst anchor → no destination for translation
        g[1][1] = 1  # src
        g[3][3] = 3; g[3][4] = 3  # blob
        return g
    if name == "no_template":
        # src + dst but no 3-blob → nothing to translate
        g[1][1] = 1
        g[5][6] = 2
        return g
    return g
