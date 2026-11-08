"""Generator for arc_additional_puzzles_21_set12_bundle:H83.

Rule: sort objects by (color, r1, c1); n×n matrix: 1 if size[r] < size[c],
2 if equal, 3 if greater.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, size_spread, texture.
Degenerates: equal_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "bdba622b3265"
# 1.2.0: was 4 FIXED-shape blobs at FIXED positions (sizes always
# [3,4,2,4]) -> output matrix nearly constant (uniq_out 8%, shape-locked
# to 4x4). Now: 3-6 distinct-color random polyomino blobs of varied sizes
# placed in a coarse cell grid (guaranteed separation). n varies -> output
# dims vary; sizes vary -> the size-comparison matrix varies.
VERSION = "1.2.2"  # strengthen executable self_check
TASK_ID = "bdba622b3265"
SUMMARY = "3-6 distinct-color non-touching blobs of varied sizes."

INVARIANTS = [
    "between 3 and 6 non-touching distinct-color blobs",
    "at least 2 distinct sizes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("equal_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "9..22"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "= n_blobs", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "cell_grid", "valid": "cell_grid"},
    "n_distinct_colors": {"type": "int", "default": "= n_blobs", "valid": "3..6"},
    "size_spread":    {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, size, max_h, max_w):
    """BFS-grow a connected polyomino of `size` cells within max_h x max_w."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        opts = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        rng.shuffle(opts)
        grown = False
        for nr, nc in opts:
            if (nr, nc) in cells:
                continue
            rs = [x for x, _ in cells] + [nr]
            cs = [y for _, y in cells] + [nc]
            if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
                continue
            cells.add((nr, nc))
            frontier.append((nr, nc))
            grown = True
            break
        if not grown:
            frontier.remove((r, c))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen:
                        if grid[nr][nc] != 0:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify default scenes contain 3-6 separated mono-color blobs with varied sizes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    comps = _nonzero_components(grid)
    if not (3 <= len(comps) <= 6):
        errs.append(f"expected 3..6 blobs, got {len(comps)}")
    colors = []
    sizes = []
    for i, cells in enumerate(comps):
        vals = {grid[r][c] for r, c in cells}
        if len(vals) != 1:
            errs.append(f"component {i} is not monochrome: {sorted(vals)}")
        else:
            colors.append(next(iter(vals)))
        sizes.append(len(cells))
    if len(colors) != len(set(colors)):
        errs.append("blob colors are not distinct")
    if sizes and len(set(sizes)) < 2:
        errs.append("all blob sizes are equal")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n = ctx.draw_int("n_blobs", 3, 4)
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        n = ctx.draw_int("n_blobs", 5, 6)
        h = ctx.draw_int("grid_h", 16, 20)
        w = ctx.draw_int("grid_w", 16, 20)
    else:
        n = ctx.draw_int("n_blobs", 3, 6)
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
    g = full_grid(h, w, 0)
    colors = list(range(1, 10)); rng.shuffle(colors)
    colors = colors[:n]

    # Coarse cell grid so blobs never touch: choose a layout with >= n cells.
    cols_cells = 1
    while cols_cells * cols_cells < n:
        cols_cells += 1
    rows_cells = (n + cols_cells - 1) // cols_cells
    cell_h = h // rows_cells
    cell_w = w // cols_cells
    slots = [(rc, cc) for rc in range(rows_cells) for cc in range(cols_cells)]
    rng.shuffle(slots)

    bh_cap = max(1, cell_h - 2)
    bw_cap = max(1, cell_w - 2)
    size_cap = min(6, max(1, bh_cap * bw_cap))
    # pre-pick sizes; if they're all equal, perturb one so >=2 distinct sizes
    sizes_used = [rng.randint(1, size_cap) for _ in range(n)]
    if size_cap >= 2 and len(set(sizes_used)) < 2:
        sizes_used[0] = 1 if sizes_used[0] != 1 else min(2, size_cap)
    for i in range(n):
        rc, cc = slots[i]
        # leave a 1-cell margin inside each cell so neighbouring blobs don't touch
        bh = bh_cap
        bw = bw_cap
        size = sizes_used[i]
        shape = _poly(rng, size, bh, bw)
        # place at a random offset within the cell's inner area
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        base_r = rc * cell_h + 1
        base_c = cc * cell_w + 1
        max_dr = max(0, (cell_h - 2) - sh)
        max_dc = max(0, (cell_w - 2) - sw)
        r0 = base_r + rng.randint(0, max_dr)
        c0 = base_c + rng.randint(0, max_dc)
        paint_at(g, r0, c0, shape, colors[i])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "equal_sizes":
        # all blobs share one size → matrix is uniformly 2 (equal everywhere)
        single = [(0, 0), (0, 1), (1, 0)]
        paint_at(g, 1, 1, single, 2)
        paint_at(g, 1, w - 4, single, 3)
        paint_at(g, h - 4, 1, single, 4)
        paint_at(g, h - 4, w - 4, single, 5)
        return g
    if name == "single_blob":
        # only 1 blob → matrix is 1×1 (just self-comparison)
        paint_at(g, h // 2, w // 2, [(0, 0), (0, 1), (1, 0), (1, 1)], 5)
        return g
    if name == "no_blobs":
        # empty grid → matrix is 0×0, no comparisons to make
        return g
    return g
