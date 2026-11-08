"""Generator for arc_puzzle_bank_21_set5_s:S5_M5 — count-selected holed-7-object.

Rule: row 0 has k color-1 markers. Among the color-7 objects on the
grid, exactly one has k enclosed (topological) holes. Rule outputs
that object's tight bbox crop (with holes as interior 0 cells).
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49a0b77dcc7f"
VERSION = "3.0.1"  # distinct=12: selected object was a FIXED lattice SQUARE (3x3/5x5), so output dims depended only on k and hole arrangements were few. Now each holed-7 object is a VARIED-size rect (3..6 x 3..7, non-square) with n holes punched at random SAME-PARITY interior cells (pairwise non-4-adjacent -> each its own enclosed region == exactly n holes). Output = the k-object's bbox crop, now varied in dims AND pattern.
TASK_ID = "49a0b77dcc7f"
SUMMARY = (
    "Row 0 holds k color-1 markers (the count). The grid contains "
    "several color-7 4-connected objects, each with a DIFFERENT "
    "number of enclosed holes. Rule selects the 7-object whose hole "
    "count equals k, then outputs that object's tight bounding-box "
    "crop (holes appear as interior 0s)."
)

# Rivals: 'output is input' refuted by any demo (output is small
# crop). 'pick largest 7-object' refuted by ≥1 demo where size and
# hole count disagree. 'recolor while cropping' refuted by any demo
# (7 stays 7, 0 stays 0). 'ignore markers' refuted by demos that
# differ only in marker count. 3 demos with ≥2 distinct k values
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "row 0 contains k color-1 markers (1 ≤ k ≤ 4)",
    "grid contains color-7 objects with strictly distinct hole counts, one of them = k",
    "the selected object has exactly k enclosed holes",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 12..16 (auto-grown to fit)", "valid": "10..26"},
    "grid_w":   {"type": "int", "default": "rng 16..22 (auto-grown to fit)", "valid": "14..28"},
    "k_count":  {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "n_objects":{"type": "int", "default": "rng 3..4", "valid": "2..5"},
}


def _make_holed_rect(n_holes, rng):
    """Solid color-7 rect with EXACTLY n_holes enclosed 0-holes, with VARIED
    (often non-square) dimensions and varied hole positions.

    Holes are punched at random SAME-PARITY interior cells. Same-parity cells
    are never 4-adjacent (4-neighbors flip parity), so each hole is a single
    0-cell fully surrounded by 7 -> topo-count-holes == n_holes exactly. The
    rect is grown until its interior has enough same-parity cells.
    """
    for _ in range(60):
        rh = rng.randint(3, 6); rw = rng.randint(3, 7)
        interior = [(r, c) for r in range(1, rh - 1) for c in range(1, rw - 1)]
        par = rng.randint(0, 1)
        cand = [(r, c) for (r, c) in interior if (r + c) % 2 == par]
        if len(cand) >= n_holes:
            break
    else:
        # fallback: square lattice big enough (guaranteed to fit)
        cnt = max(1, math.ceil(math.sqrt(n_holes)))
        rh = rw = 2 * cnt + 1
        cand = [(r, c) for r in range(1, rh - 1, 2) for c in range(1, rw - 1, 2)]
    g = [[7] * rw for _ in range(rh)]
    for (r, c) in rng.sample(cand, n_holes):
        g[r][c] = 0
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        wlo, whi, hlo, hhi = 14, 18, 11, 14
        max_k = 2; n_objects = rng.randint(2, 3)
    elif difficulty == "hard":
        wlo, whi, hlo, hhi = 20, 26, 15, 20
        max_k = 4; n_objects = rng.randint(4, 5)
    else:
        wlo, whi, hlo, hhi = 17, 22, 13, 17
        max_k = 3; n_objects = rng.randint(3, 4)

    # Distinct hole counts from 1..max_k+1; k (the selected count) is one of them.
    hole_counts_pool = list(range(1, max_k + 2))
    rng.shuffle(hole_counts_pool)
    hole_counts = hole_counts_pool[:n_objects]
    k = rng.choice(hole_counts)

    # Build one holed-7 rect per (distinct) hole count — each has EXACTLY
    # that many enclosed holes, so the k-object always exists.
    shapes = [_make_holed_rect(n, rng) for n in hole_counts]

    gap = 1
    # Width: difficulty draw, but at least wide enough for the widest object.
    w = max(rng.randint(wlo, whi), max(len(s[0]) for s in shapes) + 2)

    # Deterministic band-pack: lay shapes left-to-right, wrap to a new band
    # when the next won't fit the row. Guarantees every object is placed and
    # all are separated by ≥1 cell (distinct 4-connected components).
    bands = []; cur = []; cur_w = 0
    for sh in shapes:
        sw = len(sh[0])
        if cur and cur_w + gap + sw > w - 2:
            bands.append(cur); cur = [sh]; cur_w = sw
        else:
            cur_w += (gap if cur else 0) + sw; cur.append(sh)
    if cur:
        bands.append(cur)
    band_heights = [max(len(s) for s in b) for b in bands]

    top = 2  # leave row 0 for markers + row 1 buffer
    need_h = top + sum(band_heights) + gap * (len(bands) - 1) + 1
    h = max(rng.randint(hlo, hhi), need_h)

    g = full_grid(h, w, 0)
    # k color-1 markers in row 0.
    for c in rng.sample(range(w), k):
        g[0][c] = 1

    y = top
    for bi, b in enumerate(bands):
        x = 1
        for sh in b:
            for dr in range(len(sh)):
                for dc in range(len(sh[0])):
                    g[y + dr][x + dc] = sh[dr][dc]
            x += len(sh[0]) + gap
        y += band_heights[bi] + gap
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """row 0 has >=1 color-1 marker; rows below have >=1 color-7 object cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h < 2:
        return ["grid too short; need >=2 rows"]
    errors = []
    markers = [c for c in range(w) if grid[0][c] == 1]
    if not markers:
        errors.append("no color-1 marker cells in row 0 (k undefined)")
    object_cells = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 7]
    if not object_cells:
        errors.append("no color-7 cells in rows below row 0 (no holed objects)")
    return errors
