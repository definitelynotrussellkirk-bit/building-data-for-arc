"""Generator for arc_puzzle_bank_eighth21:M55 — remove border-touching blobs.

Rule: for each 4-connected non-0 component, if any of its cells lie on a grid
border (row 0, row h-1, col 0, col w-1) erase it; else keep it. Output is a blank
grid with only the fully-interior blobs preserved.

Prior generator placed a SINGLE border blob (always a top-edge L-tromino) plus 2
interior blobs. Canonical has MULTIPLE border blobs touching VARIOUS edges (top,
bottom, left, right) and multiple interior blobs. This version places 1-4 border
blobs across random edges (varied connected shapes) and 1-3 interior blobs.

Rule-safe diversity: grid size, border/interior blob counts, edges, shapes, colors.
Degenerates: no_border_blobs, no_interior_blobs, all_border.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f3672f3f540b"
VERSION = "3.0.0"  # multi-edge varied border blobs (was single top-edge L-tromino)
TASK_ID = "f3672f3f540b"
SUMMARY = (
    "0-bg grid with 1-4 BORDER-TOUCHING blobs across random edges (top/bottom/"
    "left/right, varied connected shapes) and 1-3 fully-INTERIOR blobs, all in "
    "distinct colors and separated by a 1-cell ring. Rule: erase any 4-connected "
    "component whose bbox touches a grid border; keep interior components on a "
    "blank canvas. (Was: a single top-edge L-tromino border blob.)"
)

INVARIANTS = [
    "background is 0",
    ">=1 blob touches some grid border (gets erased)",
    ">=1 blob is fully interior (no cell on any border)",
    "all blobs are separate 4-connected components (1-cell ring apart)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_border_blobs", "no_interior_blobs", "all_border")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":     {"type": "int", "default": "8-10 easy / 9-13 med / 11-15 hard", "valid": "8..16"},
    "grid_w":     {"type": "int", "default": "9-11 easy / 10-13 med / 12-16 hard", "valid": "9..18"},
    "n_border":   {"type": "int", "default": "1-2 easy / 2-3 med / 2-4 hard", "valid": "1..5"},
    "n_interior": {"type": "int", "default": "1-2 easy / 2-3 med / 2-3 hard", "valid": "1..4"},
    "blob_size":  {"type": "int", "default": "2-5", "valid": "1..6"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _clear(cells, used, h, w):
    for (r, c) in cells:
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if (rr, cc) in used:
                    return False
    return True


def _place_border(g, rng, used, color, size):
    h, w = len(g), len(g[0])
    for _ in range(60):
        shape = _rand_poly(rng, size)
        bh = max(r for r, _ in shape) + 1; bw = max(c for _, c in shape) + 1
        if bh > h or bw > w:
            continue
        edge = rng.choice(("top", "bottom", "left", "right"))
        if edge == "top":
            r0, c0 = 0, rng.randint(0, w - bw)
        elif edge == "bottom":
            r0, c0 = h - bh, rng.randint(0, w - bw)
        elif edge == "left":
            r0, c0 = rng.randint(0, h - bh), 0
        else:
            r0, c0 = rng.randint(0, h - bh), w - bw
        cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
        if _clear(cells, used, h, w):
            for r, c in cells:
                g[r][c] = color
            used |= cells
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, nbr, nir = (8, 10), (9, 11), (1, 2), (1, 2)
    elif difficulty == "hard":
        hr, wr, nbr, nir = (11, 15), (12, 16), (2, 4), (2, 3)
    else:
        hr, wr, nbr, nir = (9, 13), (10, 13), (2, 3), (2, 3)
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 9)
    ci = 0
    used: set[tuple[int, int]] = set()

    # border-touching blobs across random edges
    nb = rng.randint(*nbr)
    placed_border = 0
    for _ in range(nb):
        if _place_border(g, rng, used, colors[ci % 9], rng.randint(2, 5)):
            placed_border += 1; ci += 1
    if placed_border == 0:                         # guarantee >=1 border blob
        g[0][1] = colors[ci % 9]; g[0][2] = colors[ci % 9]; g[1][1] = colors[ci % 9]
        used |= {(0, 1), (0, 2), (1, 1)}; ci += 1

    # interior blobs (grow_blob excludes the border ring + existing blobs)
    interior_block = set(used)
    for r in range(h):
        interior_block.add((r, 0)); interior_block.add((r, w - 1))
    for c in range(w):
        interior_block.add((0, c)); interior_block.add((h - 1, c))
    placed_interior = 0
    for _ in range(rng.randint(*nir)):
        cells = grow_blob(rng, h, w, interior_block, rng.randint(2, 5), max_attempts=80)
        if cells:
            for r, c in cells:
                g[r][c] = colors[ci % 9]
            interior_block |= cells; ci += 1; placed_interior += 1
    if placed_interior == 0:                       # guarantee >=1 interior blob
        rr = h // 2; cc = w // 2
        g[rr][cc] = colors[ci % 9]; g[rr][cc + 1] = colors[ci % 9]
    return g


def _components_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop(); cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangular 2D list"]
    h, w = len(grid), len(grid[0])
    comps = _components_for_self_check(grid)
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("normal blobs should use distinct colors")
    border = sum(any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
                 for _, cells in comps)
    interior = len(comps) - border
    if border < 1:
        errs.append("expected at least one border-touching blob")
    if interior < 1:
        errs.append("expected at least one fully interior blob")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_border_blobs":
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        for (r, c) in [(5, 6), (6, 6), (6, 7)]: g[r][c] = 6
        return g
    if name == "no_interior_blobs":
        for (r, c) in [(0, 1), (0, 2), (1, 1)]: g[r][c] = 4
        for (r, c) in [(h - 1, 5), (h - 1, 6), (h - 2, 5)]: g[r][c] = 6
        return g
    if name == "all_border":
        for (r, c) in [(0, 2), (1, 2)]: g[r][c] = 4
        for (r, c) in [(0, 8), (0, 9)]: g[r][c] = 6
        for (r, c) in [(h - 1, 4), (h - 1, 5)]: g[r][c] = 3
        return g
    return g
