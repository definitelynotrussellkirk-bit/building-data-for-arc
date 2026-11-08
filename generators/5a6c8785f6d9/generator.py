"""Generator for v0_original:hard_07 — upscale template by marker count.

Rule: find all 4-connected components. The multi-cell components are
"templates" (in practice, exactly one). The 1-cell components are
"markers" (singletons in any color). Rule: take the first template,
crop to its bbox, then upscale (block-scale) by N where N is the
number of marker cells. Output is the upscaled template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a6c8785f6d9"
VERSION = "1.3.0"  # template must NOT fill its bbox (a solid/line template upscales to a solid output)
TASK_ID = "5a6c8785f6d9"

SUMMARY = (
    "One multi-cell connected template shape (in some non-bg color) "
    "plus N (1-4) singleton marker cells (each in any color, but each "
    "is an isolated 1-cell component). Rule outputs the template's "
    "tight-bbox crop upscaled by factor N: each cell becomes an N×N "
    "block of the same color. Marker cells and their colors are "
    "DROPPED in the output — they only serve as a counter."
)

# Rivals: 'output is input' refuted by demos (output is template
# upscaled). 'use marker color' refuted by demos preserving template
# color. 'no scaling' refuted by demos with N≥2 producing N×N blocks.
# 'count includes template cells' refuted by demos where N != total
# non-bg count. 3 demos covering N = 1, 2, 3 cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one multi-cell (≥2) connected template in some color",
    "1..4 singleton marker cells (1-cell components) in some color",
    "template and markers don't 4-touch each other",
]

AXES = {
    "grid_h":    {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":    {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "template_size":{"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "n_markers": {"type": "int", "default": "rng 1..3", "valid": "1..4"},
}


def _grow_blob(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    minr, minc = min(rs), min(cs)
    return [(r - minr, c - minc) for r, c in cells]


def _fills_bbox(cells):
    """True if cells completely fill their bbox (a solid rectangle). Such a template
    crops to a solid block and upscales to a degenerate solid output."""
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    bb_area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
    return bb_area == len(cells)


def _grow_holey_blob(rng, k):
    """Grow a blob that does NOT fill its bbox (so its crop has >=1 bg hole)."""
    for _ in range(40):
        cells = _grow_blob(rng, k)
        if not _fills_bbox(cells):
            return cells
    return [(0, 0), (1, 0), (1, 1)]  # L-tromino fallback: bbox 2x2, one hole


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    # t_size >= 3 is required for a non-bbox-filling (holey) shape (a 2-cell domino
    # always fills its bbox -> solid output).
    if difficulty == "easy":
        h = rng.randint(5, 7); w = rng.randint(5, 8)
        t_size = rng.randint(3, 4); n_markers = rng.randint(1, 3)
    elif difficulty == "hard":
        h = rng.randint(7, 10); w = rng.randint(8, 12)
        t_size = rng.randint(4, 6); n_markers = rng.randint(2, 4)
    else:
        h = rng.randint(5, 8); w = rng.randint(6, 9)
        t_size = rng.randint(3, 5); n_markers = rng.randint(1, 4)

    g = full_grid(h, w, 0)
    template = _grow_holey_blob(rng, t_size)
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    if th > h - 1 or tw > w - 1:
        template = [(0, 0), (1, 0), (1, 1)]  # L-tromino: holey, fits small grids
        th, tw = 2, 2
    template_color = rng.choice([2, 3, 4, 5, 6, 7, 8])
    # Place template in top-left area
    for _attempt in range(60):
        tr = rng.randint(0, h - th)
        tc = rng.randint(0, w - tw)
        for dr, dc in template:
            g[tr + dr][tc + dc] = template_color
        break

    # Place markers (singletons): each must NOT 4-touch any non-bg cell
    placed = 0
    attempts = 0
    while placed < n_markers and attempts < 200:
        attempts += 1
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        # Must not 4-touch any other non-bg cell (so it stays singleton)
        if any(g[r + dr][c + dc] != 0
               for dr in [-1, 1, 0] for dc in [-1, 1, 0]
               if (dr or dc) and 0 <= r + dr < h and 0 <= c + dc < w
               and (abs(dr) + abs(dc) == 1)):
            continue
        marker_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        g[r][c] = marker_color
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one multi-cell template (not bbox-filling, so its upscaled crop is not
    solid) plus >=1 singleton marker."""
    from collections import deque
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or seen[sr][sc]:
                continue
            col = grid[sr][sc]; q = deque([(sr, sc)]); seen[sr][sc] = True; cells = []
            while q:
                r, c = q.popleft(); cells.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == col:
                        seen[nr][nc] = True; q.append((nr, nc))
            comps.append(cells)
    templates = [c for c in comps if len(c) > 1]
    markers = [c for c in comps if len(c) == 1]
    if len(templates) != 1:
        errs.append(f"expected exactly one multi-cell template, got {len(templates)}")
    elif _fills_bbox(templates[0]):
        errs.append("template fills its bbox -> upscaled output is solid")
    if not markers:
        errs.append("no singleton marker cells (upscale factor would be 0)")
    return errs
