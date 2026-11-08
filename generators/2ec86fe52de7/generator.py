"""Generator for b18129f611a9:H136 -- count-selected nested-frame band fill.

Rule: k = number of color-2 cells. The color-1 hollow rectangles are ranked
by area (largest first); frame k (1-indexed) is selected and its interior is
filled with 4 down to (but not including) the next-inner frame.

This generator draws one stack of concentric color-1 frames plus k color-2
markers.

Combinatorial axes: grid size, frame count, band widths, and k.
Degenerates: no_frames, no_markers, single_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ec86fe52de7"
VERSION = "3.0.1"  # diversity: concentric color-1 frames + color-2 count band fill (was ~36)
TASK_ID = "2ec86fe52de7"
SUMMARY = (
    "0-bg grid (size varies) with a stack of concentric color-1 rectangular "
    "frames and k color-2 markers. Rule: rank frames by area, select frame k, "
    "and fill its interior with 4 down to the next-inner frame. The grid size, "
    "frame count, band widths and k vary freely (was a fixed setup, ~36 "
    "distinct)."
)

INVARIANTS = [
    "concentric color-1 hollow rectangle frames, strictly decreasing area",
    "k = count of color-2 cells selects frame k (1-indexed by area rank)",
    "the band between frame k and frame k+1 is filled with 4",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_markers", "single_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..26"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..26"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "2..5"},
    "band_gap":       {"type": "int", "default": "varies", "valid": "2..3"},
    "k_count":        {"type": "int", "default": "rng 1..n-1", "valid": "1..n_frames-1"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "concentric", "valid": "concentric"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_markers|single_frame"},
}


def _frame_outline(g, top, left, bot, right, color):
    for c in range(left, right + 1):
        g[top][c] = color; g[bot][c] = color
    for r in range(top, bot + 1):
        g[r][left] = color; g[r][right] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-1 frame cells and has color-2 count marker cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    ones = sum(grid[r][c] == 1 for r in range(h) for c in range(w))
    if ones == 0:
        errs.append("no color-1 frame cells found")
    twos = sum(grid[r][c] == 2 for r in range(h) for c in range(w))
    if twos == 0:
        errs.append("no color-2 count marker cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        nfr, gapr = (2, 3), (2, 2)
    elif difficulty == "hard":
        nfr, gapr = (3, 5), (2, 3)
    else:
        nfr, gapr = (2, 4), (2, 3)

    for _attempt in range(40):
        nf = rng.randint(*nfr)
        gap = rng.randint(*gapr)
        inner_dim = rng.randint(3, 5)
        side = inner_dim + 2 * gap * (nf - 1)
        oh = side + rng.randint(0, 3); ow = side + rng.randint(0, 3)
        top0 = 2
        left0 = rng.randint(0, 4)
        h = top0 + oh + rng.randint(1, 3)
        w = left0 + ow + rng.randint(1, 4)
        if h < 12 or w < 12 or h > 30 or w > 30:
            continue

        g = full_grid(h, w, 0)
        built = 0
        for i in range(nf):
            t = top0 + i * gap; l = left0 + i * gap
            bb = top0 + oh - 1 - i * gap; r = left0 + ow - 1 - i * gap
            if bb - t < 2 or r - l < 2:
                break
            _frame_outline(g, t, l, bb, r, 1)
            built += 1
        if built < 2:
            continue

        # k in [1, built-1] so frame k and an inner frame k+1 both exist
        k = int(overrides["k_count"]) if "k_count" in overrides \
            else rng.randint(1, built - 1)
        k = max(1, min(k, built - 1))
        # k color-2 markers in the clear top strip (rows 0..1, off the frames)
        cols = rng.sample(range(w), k)
        for c in cols:
            g[0][c] = 2
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_frames":
        g[0][1] = 2
        return g
    _frame_outline(g, 2, 2, 11, 11, 1)
    if name == "single_frame":
        g[0][1] = 2
        return g
    _frame_outline(g, 4, 4, 9, 9, 1)
    if name == "no_markers":
        return g
    g[0][1] = 2
    return g
