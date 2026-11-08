"""Generator for arc_puzzle_bank_21_set18_bundle:medium_p02 — column height summary.

Rule: take the single non-bg blob, crop to its bbox, and output a column-density
histogram: width = blob bbox width, height = the max per-column cell count, and
column c is filled from the bottom with `count_c` cells of the blob's color.

The old generator used only THREE fixed stair patterns -> 3 shapes x 9 colors =
27 distinct, with a fixed output size. Now: a RANDOM connected polyomino of
varied width and varied per-column counts -> the output width AND height (and
the bar pattern) vary widely.

Combinatorial axes: blob shape (column-count profile -> output dims + pattern),
blob color, grid size, position.
Degenerates: no_blob, single_column, full_block.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "557968cd6205"
VERSION = "3.0.2"  # reject rectangular/flat histograms; strengthen executable self_check
TASK_ID = "557968cd6205"
SUMMARY = (
    "0-bg grid (size varies) with ONE connected non-bg blob (a random "
    "polyomino, varied bbox 2-7 wide x 2-6 tall, in one color). Rule: crop the "
    "blob to its bbox; for each column count the blob's cells; output a grid of "
    "width = bbox width and height = max column count, where column c is filled "
    "from the bottom with count_c cells of the color (a column-density bar "
    "chart). Output dims and the bar pattern both track the blob's shape."
)

INVARIANTS = [
    "background is 0",
    "exactly one connected non-background blob",
    "the blob has varied per-column cell counts (non-trivial histogram)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blob", "single_column", "full_block")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "blob_cells":     {"type": "int", "default": "rng 4..12", "valid": "4..14"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "single_blob", "valid": "single_blob"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_blob|single_column|full_block"},
}


def _poly(rng, n, mh, mw):
    cells = {(rng.randint(0, mh - 1), rng.randint(0, mw - 1))}
    guard = 0
    while len(cells) < n and guard < 300:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < mh and 0 <= nc < mw:
            cells.add((nr, nc))
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def _bbox_counts(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    counts = [sum(1 for r, c in cells if c == cc) for cc in range(c0, c1 + 1)]
    return r0, r1, c0, c1, counts


def _nontrivial_histogram(cells) -> bool:
    r0, r1, c0, c1, counts = _bbox_counts(cells)
    bh = r1 - r0 + 1
    bw = c1 - c0 + 1
    return bw >= 2 and len(set(counts)) >= 2 and len(cells) < bh * bw


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the single-blob input produces a non-flat column-count histogram."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        return errors  # degenerate (no_blob) — allowed by explicit override only
    colors = {grid[r][c] for r, c in non_bg}
    if len(colors) > 1:
        errors.append(f"expected single blob color, found {len(colors)} colors: {sorted(colors)}")

    seen = {non_bg[0]}
    q = [non_bg[0]]
    for r, c in q:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if 0 <= nb[0] < h and 0 <= nb[1] < w and grid[nb[0]][nb[1]] != 0 and nb not in seen:
                seen.add(nb); q.append(nb)
    if len(seen) != len(non_bg):
        errors.append("non-background cells are not one 4-connected blob")
    if not _nontrivial_histogram(non_bg):
        errors.append("blob has a flat/rectangular column histogram")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        mh, mw = rng.randint(2, 4), rng.randint(2, 4); n = rng.randint(4, 7)
    elif difficulty == "hard":
        mh, mw = rng.randint(4, 6), rng.randint(4, 7); n = rng.randint(8, 14)
    else:
        mh, mw = rng.randint(3, 5), rng.randint(3, 6); n = rng.randint(5, 11)

    cells = None
    for _shape_attempt in range(120):
        cand = _poly(rng, min(n, mh * mw), mh, mw)
        if _nontrivial_histogram(cand):
            cells = cand
            break
    if cells is None:
        # Last-resort L/step shape: still connected and explicitly non-flat.
        cells = [(0, 0), (1, 0), (1, 1)] if mh >= 2 and mw >= 2 else [(0, 0)]
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    h = ctx.draw_int("grid_h", bh + 3, bh + 7)
    w = ctx.draw_int("grid_w", bw + 4, bw + 8)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    g = full_grid(h, w, 0)
    r0 = rng.randint(0, h - bh)
    c0 = rng.randint(0, w - bw)
    for r, c in cells:
        g[r0 + r][c0 + c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 9, 0)
    if name == "no_blob":
        return g
    if name == "single_column":
        for r in range(2, 6):
            g[r][3] = 4
        return g
    if name == "full_block":
        for r in range(2, 5):
            for c in range(3, 6):
                g[r][c] = 6
        return g
    return g
