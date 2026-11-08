"""Generator for arc_puzzle_bank_21_set3:S3_H2.

Rule: k = number of color-1 cells in row 0. Among the color-3 objects
(entirely below row 0), find the first with exactly k enclosed holes,
clear the row-0 markers, and recolor that object to 2.

This generator draws color-3 rectangles with distinct hole counts (one
with exactly k) and k markers in row 0.

Combinatorial axes: grid size, k, the target/distractor shapes, and
positions.
Degenerates: no_markers, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d6ff77830f1"
VERSION = "2.0.1"  # diversity: k markers + color-3 rects with distinct hole counts (was fixed ~27)
TASK_ID = "9d6ff77830f1"
SUMMARY = (
    "0-bg grid (size varies). Row 0 holds k color-1 markers; below are "
    "color-3 rectangles with distinct hole counts. Rule: recolor the "
    "rectangle with exactly k holes to 2 and clear the markers. The grid "
    "size, k, target/distractor shapes and positions vary freely (was a "
    "fixed setup, ~27 distinct)."
)

INVARIANTS = [
    "row 0 has k color-1 markers; one color-3 shape has exactly k holes",
    "shapes are color-3 rectangles with distinct hole counts, below row 0",
    "the output recolors the k-hole shape to 2 and clears the markers",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "k_holes":        {"type": "int", "default": "rng 1..3", "valid": "1|2|3"},
    "n_distractors":  {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "shapes_below_markers",
                       "valid": "shapes_below_markers"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_shapes|full_grid"},
}


def _holed_rect(rng, n_holes):
    """solid color-3 rect (cells) with n_holes non-adjacent interior 0-holes."""
    # interior big enough for n_holes non-adjacent cells
    iw = max(3, 2 * n_holes + 1); ih = 3
    rh = ih + 2; rw = iw + 2
    interior = [(r, c) for r in range(1, rh - 1) for c in range(1, rw - 1)]
    holes = set()
    rng.shuffle(interior)
    for (r, c) in interior:
        if len(holes) >= n_holes:
            break
        if all((r + dr, c + dc) not in holes for dr, dc in _CARD):
            holes.add((r, c))
    if len(holes) < n_holes:
        return None, 0, 0
    cells = [(r, c) for r in range(rh) for c in range(rw) if (r, c) not in holes]
    return cells, rh, rw


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, ndr = (12, 15), (14, 18), (1, 2)
    elif difficulty == "hard":
        hr, wr, ndr = (16, 22), (18, 24), (2, 3)
    else:
        hr, wr, ndr = (13, 18), (15, 20), (1, 3)

    k = int(overrides["k_holes"]) if "k_holes" in overrides else rng.randint(1, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        for c in range(w):
            occ[0][c] = True   # reserve row 0 for markers

        # hole counts: target k + distinct distractors
        nd = rng.randint(*ndr)
        others = [j for j in (0, 1, 2, 3) if j != k]
        rng.shuffle(others)
        counts = [k] + others[:nd]
        ok = True
        for n in counts:
            cells, rh, rw = _holed_rect(rng, n)
            if cells is None:
                ok = False; break
            placed = False
            for _t in range(40):
                top = rng.randint(1, h - rh); left = rng.randint(0, w - rw)
                if _reserve(occ, top, left, rh, rw, h, w):
                    for (r, c) in cells:
                        g[top + r][left + c] = 3
                    placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue

        # k markers in row 0
        cols = rng.sample(range(w), k)
        for c in cols:
            g[0][c] = 1
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 14, 0)
    for r in range(2, 5):
        for c in range(2, 7):
            g[r][c] = 3
    g[3][4] = 0
    g[0][1] = 1
    if name == "no_markers":
        g[0][1] = 0
        return g
    if name == "no_shapes":
        g2 = full_grid(13, 14, 0); g2[0][1] = 1
        return g2
    if name == "full_grid":
        return full_grid(13, 14, 3)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: color-1 cells exist in row 0; color-3 shape cells exist below row 0."""
    msgs = []
    h, w = len(grid), len(grid[0])
    markers = [c for c in range(w) if grid[0][c] == 1]
    shapes = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 3]
    if not markers:
        msgs.append("no color-1 marker cells in row 0")
    if not shapes:
        msgs.append("no color-3 shape cells below row 0")
    return msgs
