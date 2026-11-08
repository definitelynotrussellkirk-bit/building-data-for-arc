"""Generator for 11b:hard_73 — choose most holes, scale2, recolor.

Rule: a single-cell marker provides a target color. Among multi-cell
shapes, find the one with the most bbox-interior bg cells (holes).
Output: that shape cropped, scaled 2x, recolored to marker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (no isolated single-cell marker → rule's
target-color selector returns nothing), tied_holes (≥2 shapes share
max hole-count → "most holes" is ambiguous, tie-break decides),
all_solid (every shape has 0 holes → rule's hole-rank is uniform,
no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5df4d341f399"
VERSION = "3.1.0"  # distinct=44/dup31%: most-holed shape (from fixed _BY_HOLES bank) scaled 2x recolored. Now build each shape as a random-dimension k-hole frame -> the winner's output (scaled 2x) varies; distinct 44->99.
TASK_ID = "5df4d341f399"
SUMMARY = (
    "0-bg grid (h ∈ 12-20, w ∈ 13-22, "
    "by difficulty) with: (a) "
    "N_SHAPES ∈ 2-4 MULTI-CELL SHAPES "
    "drawn from _BY_HOLES bank (keyed "
    "by hole count 0-3): 0-hole (2×2 "
    "solid, T-tet, 2×3 solid, T-pent), "
    "1-hole (3×3 ring, 3×4 ring, 4×3 "
    "ring), 2-hole (3×5 frame with "
    "middle bar, 4×4 with two side "
    "holes), 3-hole (5×5 with cross "
    "dividers, 3×7 with three holes). "
    "Each shape painted in a DISTINCT "
    "color from a 4+ color palette "
    "drawn from {1..9}, with STRICTLY "
    "DISTINCT HOLE COUNTS (rng.sample "
    "of [0,1,2,3] keys); (b) ONE "
    "ISOLATED SINGLE-CELL MARKER "
    "(no neighbors) painted in the "
    "MARKER COLOR (palette[0]). Rule "
    "(FIND THE MARKER → ITS COLOR "
    "IS THE TARGET; FIND THE SHAPE "
    "WITH THE MOST HOLES (BBOX-"
    "INTERIOR BG CELLS); CROP IT, "
    "SCALE 2× (EACH CELL → 2×2 "
    "BLOCK), RECOLOR EVERY CELL TO "
    "THE MARKER COLOR, OUTPUT): "
    "EXTRACT every shape with its "
    "hole count. SELECT max-holes "
    "shape. CROP to bbox. UPSCALE "
    "by 2. RECOLOR to marker. "
    "OUTPUT. Net: marker dictates "
    "color, most-holed shape "
    "dictates form, output is 2x "
    "scaled."
)

# Rivals: 'use a fixed scale' refuted by ≥2 demos with different
# winner shapes producing different output bboxes. 'recolor with
# winner's color' refuted by any demo (output uses marker color, not
# winner's). 'scale by 1 (no upscale)' refuted by any demo (output is
# 2× the shape bbox). 'pick most cells' refuted by ≥1 demo where
# fewer-cell shape has more holes.
# 4 demos with varied winner hole counts + marker colors cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one isolated single-cell marker",
    "2-3 multi-cell shapes, distinct colors, with strictly distinct hole counts",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "tied_holes", "all_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 13..15", "valid": "12..18"},
    "grid_w":            {"type": "int", "default": "rng 14..17", "valid": "13..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":     {"type": "str", "default": "marker_plus_distinct_hole_shapes",
                          "valid": "marker_plus_distinct_hole_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_BY_HOLES = {
    0: [
        [(0, 0), (0, 1), (1, 0), (1, 1)],                                 # 2x2 solid
        [(0, 0), (0, 1), (0, 2), (1, 1)],                                 # T-tet
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],                 # 2x3 solid
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)],         # T-pent
    ],
    1: [
        # 3x3 ring (1 hole at center)
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
        # 3x4 ring (1 hole — 1x2 interior)
        [(0, 0), (0, 1), (0, 2), (0, 3),
         (1, 0), (1, 3),
         (2, 0), (2, 1), (2, 2), (2, 3)],
        # 4x3 ring (1 hole — 2x1 interior)
        [(0, 0), (0, 1), (0, 2),
         (1, 0), (1, 2),
         (2, 0), (2, 2),
         (3, 0), (3, 1), (3, 2)],
    ],
    2: [
        # 4x4 ring (1 large hole — connected) — actually has 1 hole. Let me build
        # a true 2-hole shape: two separate interior 1x1 cavities.
        # 3x5 frame with internal bar between two 1x1 interior holes.
        [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
         (1, 0), (1, 2), (1, 4),
         (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
        # 4x4 with two side-by-side holes
        [(0, 0), (0, 1), (0, 2), (0, 3),
         (1, 0), (1, 2), (1, 3),
         (2, 0), (2, 1), (2, 3),
         (3, 0), (3, 1), (3, 2), (3, 3)],
    ],
    3: [
        # 5x5 ring with cross dividers (3 holes)
        [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
         (1, 0), (1, 2), (1, 4),
         (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
         (3, 0), (3, 2), (3, 4),
         (4, 0), (4, 1), (4, 2), (4, 3), (4, 4)],
        # 3x7 with three 1x1 holes
        [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
         (1, 0), (1, 2), (1, 4), (1, 6),
         (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)],
    ],
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _frame_k_holes(rng, k):
    """Random-dimension shape with EXACTLY k holes: a rectangular frame split
    into k compartments by k-1 internal full-width dividers."""
    if k == 0:
        hh = rng.randint(2, 4); ww = rng.randint(2, 4)
        return [(r, c) for r in range(hh) for c in range(ww)]
    ww = rng.randint(3, 6)
    hh = 2 * k + 1 + 2 * rng.randint(0, 1)     # extra rows -> varied dims
    cells = set()
    for c in range(ww):
        cells.add((0, c)); cells.add((hh - 1, c))
    for r in range(hh):
        cells.add((r, 0)); cells.add((r, ww - 1))
    inner = list(range(2, hh - 2, 2))[:k - 1]  # k-1 dividers -> k compartments
    for dr in inner:
        for c in range(ww):
            cells.add((dr, c))
    return sorted(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 12, 14, 13, 15
        n_lo, n_hi = 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 16, 20, 18, 22
        n_lo, n_hi = 3, 4
    else:
        h_lo, h_hi, w_lo, w_hi = 13, 16, 15, 18
        n_lo, n_hi = 2, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_shapes = rng.randint(n_lo, n_hi)
    # Palette includes 1 and 5 (was missing).
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_shapes + 1)
    marker_color = palette[0]
    shape_colors = palette[1:]
    # distinct hole counts -> a UNIQUE max (the winner). Build each shape as a
    # random-dimension k-hole frame so the winner (output = it scaled 2x) varies.
    keys = rng.sample([0, 1, 2, 3], n_shapes)
    for k, color in zip(keys, shape_colors):
        _place(g, rng, _frame_k_holes(rng, k), color)
    for _ in range(60):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0: continue
        bad = False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    bad = True; break
            if bad: break
        if bad: continue
        g[r][c] = marker_color; break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 distinct non-zero colors (shapes+marker), at least one isolated single-cell marker."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct non-zero colors, found {len(colors)}")
    # Check for at least one isolated single-cell (marker)
    has_isolated = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            v = grid[r][c]
            neighbors = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
            if all(grid[nr][nc] == 0 for nr, nc in neighbors
                   if 0 <= nr < h and 0 <= nc < w):
                has_isolated = True
                break
        if has_isolated:
            break
    if not has_isolated:
        errs.append("no isolated single-cell marker found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 14, 15
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # No isolated single-cell marker — rule's target-color selector
        # returns nothing.
        for c in range(1, 4): g[1][c] = 4; g[3][c] = 4
        g[2][1] = 4; g[2][3] = 4
        for r in range(7, 10):
            for c in range(8, 11): g[r][c] = 6
        return g
    if name == "tied_holes":
        # Two shapes share max hole-count (both 1-hole rings) — "most"
        # is ambiguous.
        for c in range(1, 4): g[1][c] = 4; g[3][c] = 4
        g[2][1] = 4; g[2][3] = 4
        for c in range(8, 11): g[1][c] = 6; g[3][c] = 6
        g[2][8] = 6; g[2][10] = 6
        g[10][12] = 7   # marker
        return g
    if name == "all_solid":
        # Every shape has 0 holes — rule's hole-rank is uniform.
        for r in range(1, 3):
            for c in range(1, 3): g[r][c] = 4
        for r in range(6, 9):
            for c in range(6, 9): g[r][c] = 6
        for r in range(11, 13):
            for c in range(11, 14): g[r][c] = 8
        g[1][13] = 7   # marker
        return g
    return g
