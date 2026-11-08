"""Generator for arc_puzzle_bank_twentysecond21:M152 — rotate CW around 9-anchor.

Rule: 9-anchor + a single non-9 blob. Rotate the blob 90° CW around
the anchor: (r, c) → (anchor_r + (c - anchor_c), anchor_c - (r - anchor_r)).

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor, no_blob, blob_at_anchor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e07c169ac61"
VERSION = "1.2.0"
TASK_ID = "1e07c169ac61"
SUMMARY = "9-anchor + a small blob whose CW rotation lands in-bounds."

INVARIANTS = [
    "background is 0",
    "exactly one 9-cell at center",
    "blob in upper-left so rotation lands in-bounds",
    "blob is non-symmetric so rotation produces a different shape",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_blob", "blob_at_anchor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "anchor_with_upper_left_blob",
                       "valid": "anchor_with_upper_left_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rotation(grid_h, grid_w, ar, ac, cells):
    return {(ar + (c - ac), ac - (r - ar)) for r, c in cells}


def _valid_blob_positions(h, w, ar, ac):
    ok = []
    for r in range(ar):
        for c in range(ac):
            rr = ar + (c - ac)
            cc = ac - (r - ar)
            if 0 <= rr < h and 0 <= cc < w:
                ok.append((r, c))
    return ok


def _grow_connected_blob(rng, h, w, ar, ac, size):
    valid = set(_valid_blob_positions(h, w, ar, ac))
    starts = list(valid)
    for _ in range(80):
        if not starts:
            return None
        cells = {rng.choice(starts)}
        frontier = list(cells)
        guard = 0
        while len(cells) < size and frontier and guard < 80:
            guard += 1
            r, c = rng.choice(frontier)
            nbrs = []
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in valid and nb not in cells:
                    nbrs.append(nb)
            if not nbrs:
                frontier.remove((r, c))
                continue
            nb = rng.choice(nbrs)
            cells.add(nb)
            frontier.append(nb)
        if len(cells) == size and _rotation(h, w, ar, ac, cells) != cells:
            return sorted(cells)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 7, 7)
        blob_size = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        blob_size = 4
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        blob_size = 3
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    ar = h // 2; ac = w // 2
    g[ar][ac] = 9
    color = rng.choice([2, 3, 4, 5, 6, 7, 8])
    cells = _grow_connected_blob(rng, h, w, ar, ac, blob_size)
    if cells is None:
        raise ValueError("could not place connected rotatable blob")
    for r, c in cells:
        g[r][c] = color
    return g


def _components4(cells):
    cells = set(cells)
    comps = []
    while cells:
        start = cells.pop()
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells:
                    cells.remove(nb)
                    comp.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    blob = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)]
    colors = {grid[r][c] for r, c in blob}
    if anchors != [(h // 2, w // 2)]:
        errs.append(f"expected exactly one centered color-9 anchor, found {anchors}")
    if not (3 <= len(blob) <= 4):
        errs.append(f"expected 3-4 blob cells, found {len(blob)}")
    if len(colors) != 1:
        errs.append("blob must use exactly one non-9 color")
    comps = _components4(blob)
    if len(comps) != 1:
        errs.append(f"expected one 4-connected blob, found {len(comps)}")
    if anchors:
        ar, ac = anchors[0]
        if any(not (r < ar and c < ac) for r, c in blob):
            errs.append("blob cells must be strictly upper-left of the anchor")
        rot = _rotation(h, w, ar, ac, blob)
        if any(not (0 <= r < h and 0 <= c < w) for r, c in rot):
            errs.append("rotated blob leaves the grid")
        if rot == set(blob):
            errs.append("blob is invariant under the 90-degree rotation")
    return errs

def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_anchor":
        # blob without 9-anchor → no rotation pivot defined
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4
        return g
    if name == "no_blob":
        # 9-anchor alone → nothing to rotate
        g[h // 2][w // 2] = 9
        return g
    if name == "blob_at_anchor":
        # blob coincides with anchor → rotation lands at the same cell (identity)
        ar, ac = h // 2, w // 2
        g[ar][ac] = 9
        # blob symmetric under 90° around anchor (e.g., the center cell only)
        return g
    return g
