"""Generator for arc_additional_puzzles_21_set2:M11.

Rule: marker = first non-zero cell in row 0 (leftmost). Among all
connected components with color == marker AND size > 1, take the
TOPMOST (by r1, then c1) and output its bbox crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, marker_color,
n_other_marker_blobs, n_distractors, shape_size, position_bias.
Degenerates: no_marker, no_matching_blob, all_singletons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5dbe4bcb101c"
VERSION = "2.1.0"
TASK_ID = "5dbe4bcb101c"
SUMMARY = (
    "0-bg grid (h~7-12, w~10-15) with: "
    "(a) ONE COLOR MARKER CELL in row 0 "
    "at random col mc — color drawn from "
    "2..9 (the 'marker color'); (b) "
    "1-2 MARKER-COLOR BLOBS of size "
    "2-5 placed at row r ≥ 2 (avoiding "
    "marker row); (c) 1-3 DISTRACTOR "
    "BLOBS in different colors at "
    "rows ≥ 2; (d) optionally 1-3 "
    "MARKER-COLOR SINGLETONS scattered "
    "(rule ignores these). Rule "
    "(MARKER-COLOR TOPMOST CROP): READ "
    "row 0 to find the MARKER COLOR "
    "(first non-zero cell's value). "
    "Among ALL CONNECTED COMPONENTS in "
    "the body (rows ≥ 1) with COLOR == "
    "MARKER AND SIZE > 1, pick the "
    "TOPMOST one (min r1, then min c1 "
    "as tiebreaker). EMIT the BBOX "
    "CROP of that component as the "
    "output (a small subgrid with the "
    "blob in place, bbox padded with "
    "0 if applicable). Singletons "
    "ignored. Net: row-0 marker color "
    "picks the topmost matching blob; "
    "output is its bbox crop."
)

# Rivals: 'output a distractor color blob' refuted by ≥2 demos where
# output color matches marker. 'output marker color singletons too'
# refuted by ≥1 demo with size-1 marker cells ignored. 'output
# largest blob' refuted by ≥2 demos where a smaller-but-topmost wins.
# 'output entire grid' refuted by any demo (output is small crop).
# 'output bottommost marker-color blob' refuted by ≥2 demos where
# topmost wins.
# 4 demos with varied marker positions + shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "row 0 has ≥1 non-zero cell (the marker)",
    "≥1 marker-color component with size > 1",
    "≥1 distractor component in a different color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_matching_blob", "all_singletons")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "8..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "marker_color":   {"type": "color", "default": "rng 2..9", "valid": "2..9"},
    "n_marker_blobs": {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_distractors":  {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "shape_size":     {"type": "int", "default": "rng 2..5", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "marker_plus_blobs",
                       "valid": "marker_plus_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_marker|no_matching_blob|all_singletons"},
}


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _try_place(g, cells, color, rng, r_min=0):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    h, w = len(g), len(g[0])
    for _ in range(80):
        r0 = rng.randint(r_min, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in cells:
            g[r0 + r - min(rs)][c0 + c - min(cs)] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 9, 12)
        n_marker_blobs = 1
        n_distractors = rng.randint(1, 2)
        size_lo, size_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 20)
        n_marker_blobs = rng.randint(2, 3)
        n_distractors = rng.randint(3, 5)
        size_lo, size_hi = 3, 6
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 15)
        n_marker_blobs = rng.randint(1, 2)
        n_distractors = rng.randint(2, 3)
        size_lo, size_hi = 2, 5
    g = full_grid(h, w, 0)
    marker = rng.randint(2, 9)
    # Place marker in row 0 at random column.
    mc = rng.randint(0, w - 1)
    g[0][mc] = marker
    # Place marker-color blob(s) of size ≥2 in body (rows ≥2 to avoid
    # collision with marker row).
    sizes = sorted([rng.randint(size_lo, size_hi)
                    for _ in range(n_marker_blobs)])
    for size in sizes:
        cells = _build_motif(rng, size)
        _try_place(g, cells, marker, rng, r_min=2)
    # Place distractor blobs in colors != marker.
    distractor_pool = [c for c in range(1, 10) if c != marker]
    rng.shuffle(distractor_pool)
    for i in range(n_distractors):
        if i >= len(distractor_pool):
            break
        size = rng.randint(size_lo, size_hi)
        cells = _build_motif(rng, size)
        _try_place(g, cells, distractor_pool[i], rng, r_min=2)
    # Optionally add some marker-color singletons (rule ignores them).
    if rng.random() < 0.5:
        for _ in range(rng.randint(1, 3)):
            for _attempt in range(30):
                sr = rng.randint(2, h - 1); sc = rng.randint(0, w - 1)
                if g[sr][sc] == 0:
                    # Ensure singleton isn't adjacent to marker-color blob
                    ok = True
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = sr + dr, sc + dc
                        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == marker:
                            ok = False; break
                    if ok:
                        g[sr][sc] = marker
                        break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, row 0 has >=1 non-zero marker, body has >=1 multi-cell blob."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    # Row 0 must have at least one non-zero cell (marker)
    row0_nz = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not row0_nz:
        errs.append("row 0 has no non-zero cells (marker missing)")
    # Body (rows 1..h-1) must have at least one non-zero cell
    body_nz = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if not body_nz:
        errs.append("no non-zero cells in body (rows 1..h-1)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_marker":
        g[2][2] = 4; g[2][3] = 4; g[5][7] = 6; g[5][8] = 6
        return g
    if name == "no_matching_blob":
        g[0][0] = 4
        g[2][8] = 6; g[2][9] = 6; g[3][8] = 6
        return g
    if name == "all_singletons":
        g[0][0] = 4
        g[2][3] = 4; g[5][7] = 4  # singletons
        g[4][1] = 6; g[4][2] = 6
        return g
    return g
