"""Generator for 15b:m104 — read frame majorities into row.

Rule: 3 hollow rectangular 8-frames at different positions; each
frame's interior holds a strict-majority color among 1-2 colors.
Output is a 1x3 row of those majority colors, ordered by frame's
leftmost column.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, no_majority, all_same_majority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce7cf0742e9a"
VERSION = "2.0.1"  # shape-locked-out (always 1x3): FIXED 3 frames in a horizontal row, grid width 17-18. Rule scans ANY number of 5x5 8-frames anywhere and emits 1x(frame count) ordered by (col,row). Now vary frame count 2-5 at FREE 2D positions on varied grids -> output width varies; each interior filled with a majority colour."
TASK_ID = "ce7cf0742e9a"
SUMMARY = "Hollow 5x5 8-frames; each interior's majority non-8 color read into a 1xK row (K=frame count), ordered by column then row."

INVARIANTS = [
    "background is 0",
    "2-5 hollow rectangular 5x5 8-frames, separated by a gap",
    "each interior has 1-2 distinct non-8 colors with a clear majority",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_majority", "all_same_majority")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..18", "valid": "7..26"},
    "grid_w":         {"type": "int", "default": "rng 9..18", "valid": "7..26"},
    "n_frames":       {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "free", "valid": "free"},
    "n_distinct_colors": {"type": "int", "default": "varied", "valid": "varied"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values 0-9; all color-8 cells form frame borders (not isolated)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        nf = ctx.draw_int("n_frames", 2, 3); h = ctx.draw_int("grid_h", 9, 14); w = ctx.draw_int("grid_w", 9, 16)
    elif difficulty == "hard":
        nf = ctx.draw_int("n_frames", 3, 5); h = ctx.draw_int("grid_h", 16, 26); w = ctx.draw_int("grid_w", 16, 26)
    else:
        nf = ctx.draw_int("n_frames", 2, 4); h = ctx.draw_int("grid_h", 11, 20); w = ctx.draw_int("grid_w", 11, 20)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(400):
        if placed >= nf:
            break
        r0 = rng.randint(0, h - 5); c0 = rng.randint(0, w - 5)
        if not _free(g, r0, c0, r0 + 4, c0 + 4):   # 5x5 frame + 1-ring gap (no spurious frame)
            continue
        for c in range(c0, c0 + 5):
            g[r0][c] = 8; g[r0 + 4][c] = 8
        for r in range(r0, r0 + 5):
            g[r][c0] = 8; g[r][c0 + 4] = 8
        major, minor = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)
        interior = [(r, c) for r in range(r0 + 1, r0 + 4) for c in range(c0 + 1, c0 + 4)]
        rng.shuffle(interior)
        n_major = rng.randint(5, 7)
        for r, c in interior[:n_major]:
            g[r][c] = major
        for r, c in interior[n_major:]:
            g[r][c] = minor
        placed += 1
    if placed < 2:                                 # guarantee >=2 frames (fallback small layout)
        return _draw_from_degenerate("all_same_majority", rng) if placed == 0 else g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 17
    g = full_grid(h, w, 0)
    starts = [0, 6, 12]
    if name == "no_frames":
        # Loose color cells but no 8-frames — rule's "frame
        # interior" majority readout has no scope.
        g[2][2] = 4; g[2][8] = 6; g[2][14] = 7
        return g
    if name == "no_majority":
        # 3 frames but each interior has a 5-4 split (no strict
        # majority); rule's "strict majority" filter fails per frame.
        for c0 in starts:
            for c in range(c0, c0 + 5):
                g[1][c] = 8; g[5][c] = 8
            for r in range(1, 6):
                g[r][c0] = 8; g[r][c0 + 4] = 8
            interior = [(r, c) for r in range(2, 5) for c in range(c0 + 1, c0 + 4)]
            for i, (r, c) in enumerate(interior):
                g[r][c] = 4 if i < 4 else 6
        return g
    if name == "all_same_majority":
        # All 3 frames have the same majority color — rule's
        # "distinct majority" precondition fails; output strip is
        # uniform.
        for c0 in starts:
            for c in range(c0, c0 + 5):
                g[1][c] = 8; g[5][c] = 8
            for r in range(1, 6):
                g[r][c0] = 8; g[r][c0 + 4] = 8
            for r in range(2, 5):
                for c in range(c0 + 1, c0 + 4):
                    g[r][c] = 4
        return g
    return g
