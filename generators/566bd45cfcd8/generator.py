"""Generator for arc_puzzle_bank_seventh_21_bundle:hard_43_local_marked_rowcol_crossings_in_frames.

Rule: for each color-5 rectangular FRAME, read the KEY color from the cell just
above the frame; inside the frame find the interior rows whose two inner side
cells are both 2 (row markers) and the interior cols whose two inner top/bottom
cells are both 3 (col markers); paint every (marked-row x marked-col) crossing
with that frame's key. The rule discovers frames dynamically, so it is fully
size- and count-generic.

The old generator hardcoded an 8x14 grid with exactly two fixed 6x6 frames
(shape-locked in AND out; canonical is 14x18+ with varied frames). Now: vary
the grid size, the NUMBER of frames (2-4), each frame's SIZE and POSITION, the
keys, and the row/col marker subsets.

Combinatorial axes: grid size, frame count/sizes/positions, per-frame key,
per-frame row/col marker subsets.
Degenerates: no_frames, no_keys, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "566bd45cfcd8"
VERSION = "3.0.1"  # shape-locked in/out: gen hardcoded 8x14 + two fixed 6x6 frames. Rule discovers color-5 frames dynamically (size/count-generic; canonical 14x18+). Now vary grid size + frame count(2-4)/sizes/positions + keys + row/col marker subsets.
TASK_ID = "566bd45cfcd8"
SUMMARY = (
    "0-bg grid (size varies) holding 2-4 color-5 RECTANGULAR FRAMES of varied "
    "size/position. Each frame has a single KEY color cell in the row just "
    "above it; inside, some interior ROWS carry color-2 markers on both inner "
    "side columns and some interior COLS carry color-3 markers on both inner "
    "top/bottom rows. Rule: per frame, paint each (marked-row x marked-col) "
    "crossing inside the frame with that frame's key color."
)

INVARIANTS = [
    "color-5 rectangular frames contain local row endpoint markers in color 2",
    "the same interiors contain local column endpoint markers in color 3",
    "a nonzero key marker above each frame gives the crossing fill color",
    "only local row/column crossings inside each frame are filled",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_keys", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "14..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "frame_count":    {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "scattered_keyed_frames",
                       "valid": "scattered_keyed_frames"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_keys|no_markers"},
}

_KEYS = [1, 4, 6, 7, 8, 9]


def _add_frame(g, top, left, fh, fw, key, rrows, ccols):
    draw_frame(g, top, left, top + fh - 1, left + fw - 1, 5)
    g[top - 1][left + fw // 2] = key
    ir0, ic0 = top + 1, left + 1
    ir1, ic1 = top + fh - 2, left + fw - 2
    for r in rrows:                       # row markers on both inner side cols
        g[r][ic0] = 2
        g[r][ic1] = 2
    for c in ccols:                       # col markers on both inner top/bot rows
        g[ir0][c] = 3
        g[ir1][c] = 3


def _overlaps(rect, occ):
    r0, c0, r1, c1 = rect
    for (a0, b0, a1, b1) in occ:
        if not (r1 < a0 - 1 or r0 > a1 + 1 or c1 < b0 - 1 or c0 > b1 + 1):
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 14, 18)
        target = rng.randint(2, 2); lo, hi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 17, 22); w = ctx.draw_int("grid_w", 20, 26)
        target = rng.randint(3, 4); lo, hi = 2, 3
    else:
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 16, 22)
        target = rng.randint(2, 3); lo, hi = 1, 3

    g = full_grid(h, w, 0)
    occ = []
    placed = 0
    for _ in range(400):
        if placed >= target:
            break
        fh = rng.randint(6, 8)
        fw = rng.randint(6, 8)
        if fh > h - 1 or fw > w:
            continue
        top = rng.randint(1, h - fh)
        left = rng.randint(0, w - fw)
        rect = (top - 1, left, top + fh - 1, left + fw - 1)
        if _overlaps(rect, occ):
            continue
        # inner-inner index ranges (exclude the rows/cols used by the other axis)
        inner_rows = list(range(top + 2, top + fh - 2))
        inner_cols = list(range(left + 2, left + fw - 2))
        if not inner_rows or not inner_cols:
            continue
        nr = min(len(inner_rows), rng.randint(lo, hi))
        nc = min(len(inner_cols), rng.randint(lo, hi))
        rrows = sorted(rng.sample(inner_rows, nr))
        ccols = sorted(rng.sample(inner_cols, nc))
        _add_frame(g, top, left, fh, fw, rng.choice(_KEYS), rrows, ccols)
        occ.append(rect)
        placed += 1

    if placed < 2:                        # roomy fallback guarantees >=2 frames
        g = full_grid(18, 22, 0)
        _add_frame(g, 1, 1, 7, 7, 4, [3, 4], [3, 4])
        _add_frame(g, 1, 12, 7, 7, 6, [3], [3, 4])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-5 frame cells present, plus color-2 and color-3 markers inside."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    has5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    has2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    has3 = any(grid[r][c] == 3 for r in range(h) for c in range(w))
    if not has5:
        errs.append("no color-5 frame cells found")
    if not has2:
        errs.append("no color-2 row markers found")
    if not has3:
        errs.append("no color-3 col markers found")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 14, 0)
    if name == "no_frames":
        g[0][3] = 4; g[0][10] = 6
        g[3][1] = 2; g[3][8] = 2
        g[1][3] = 3; g[1][10] = 3
        return g
    if name == "no_keys":
        draw_frame(g, 1, 1, 6, 6, 5)
        draw_frame(g, 1, 8, 6, 13, 5)
        for r in [3]:
            g[r][2] = 2; g[r][5] = 2
        for c in [3]:
            g[2][c] = 3; g[5][c] = 3
        return g
    if name == "no_markers":
        draw_frame(g, 1, 1, 6, 6, 5)
        draw_frame(g, 1, 8, 6, 13, 5)
        g[0][3] = 4; g[0][10] = 6
        return g
    return g
