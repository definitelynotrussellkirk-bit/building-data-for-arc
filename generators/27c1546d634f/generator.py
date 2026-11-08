"""Generator for arc_puzzle_bank_21_set12_bundle:medium_l10 — Crop the obj with 1 hole.

Rule: find the first object whose topo-count-holes == 1 and crop the
grid to its bbox. If none, output [[0]].

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_solids,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, multiple_frames, only_solids.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob, has_neighbor

GENERATOR_ID = "27c1546d634f"
VERSION = "2.0.1"
TASK_ID = "27c1546d634f"
SUMMARY = "Mix of solid blob and hollow frame; output crops the frame."

INVARIANTS = [
    "exactly one closed-frame object (hollow rectangle) of size >= 3x3",
    "1..2 solid blobs (no holes)",
    "objects don't touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "multiple_frames", "only_solids")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_solids":       {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one hollow-rectangle frame (border cells of a rect are all non-zero, interior has bg)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_frame", "multiple_frames", "only_solids"):
        return []
    errs = []
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero == 0:
        errs.append("no non-bg cells")
    return errs


def _place_frame(rng, h, w, used):
    for _ in range(20):
        rh = rng.randint(3, min(7, h - 2))
        rw = rng.randint(3, min(7, w - 2))
        if rh < 3 or rw < 3: continue
        if rh > h - 2 or rw > w - 2: continue
        r1 = rng.randint(1, h - rh - 1)
        c1 = rng.randint(1, w - rw - 1)
        r2 = r1 + rh - 1
        c2 = c1 + rw - 1
        cells = set()
        for r in range(r1, r2 + 1):
            cells.add((r, c1)); cells.add((r, c2))
        for c in range(c1, c2 + 1):
            cells.add((r1, c)); cells.add((r2, c))
        if any(p in used or has_neighbor(p, used, ignore=cells) for p in cells):
            continue
        return cells, (r1, c1, r2, c2)
    return None, None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degenerate"))
    # output = the bbox crop of the (unique) 1-hole rectangle frame. Was 3-5 x 3-5
    # (out=9, dup48%) -> widened frame dims to 3-7 and grids for more output sizes.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 11, 16)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    colors = list(range(1, 10)); rng.shuffle(colors)

    used = set()
    frame, bb = _place_frame(rng, h, w, used)
    if frame is not None:
        used |= frame
        for r, c in frame: g[r][c] = colors[0]

    n_solids = rng.randint(1, 2)
    for i in range(n_solids):
        size = rng.randint(2, 4)
        blob = grow_blob(rng, h, w, used, size)
        if blob is None: continue
        used |= blob
        for r, c in blob: g[r][c] = colors[(i + 1) % len(colors)]

    return g


def _draw_from_degenerate(name, rng):
    # rng is a ctx.draw_rng("degenerate") handle (deterministic per seed +
    # sample_index) — grow_blob consumes it, so degenerate layouts stay
    # reproducible without a banned `import random`.
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # only solid blobs → no object has a hole, rule outputs [[0]]
        used = set()
        for color in (3, 5):
            blob = grow_blob(rng, h, w, used, 4)
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = color
        return g
    if name == "multiple_frames":
        # two hollow rectangles → ambiguous which to crop to
        for r in range(1, 5):
            g[r][1] = 4; g[r][4] = 4
        for c in range(1, 5):
            g[1][c] = 4; g[4][c] = 4
        for r in range(5, 9):
            g[r][7] = 6; g[r][10] = 6
        for c in range(7, 11):
            g[5][c] = 6; g[8][c] = 6
        return g
    if name == "only_solids":
        # only solid blobs of various sizes (no frame) → no hole, output [[0]]
        for r, c in [(2, 2), (2, 3), (3, 2)]:
            g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 6), (6, 7)]:
            g[r][c] = 6
        return g
    return g
