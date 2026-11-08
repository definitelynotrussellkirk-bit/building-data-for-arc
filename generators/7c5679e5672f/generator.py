"""Generator for 7c5679e5672f — stamp the color-3 template at each coloured marker.

Rule (verified from canonical Racket): the largest color-3 object is the
TEMPLATE (normalised). Marker cells carry a rotation code by colour
(1->0, 2->1, 4->2, 5->3 quarter-turns). For every marker, the template is
rotated by its code and stamped (color 8) with its top-left at the marker, cells
outside the grid dropped.

The previous body was the generic "6 panels, find the matching pair" template,
which placed random motifs and frequently had NO color-3 object, so the rule's
`(first (sort (filter ... color 3 ...)))` returned #f and crashed (rule_smoke
3/12). This 2.2.0 rewrite CONSTRUCTS valid inputs: one clear color-3 template
plus several markers in {1,2,4,5} with room for the rotated stamps, so the rule
always has a template and the stamped output varies.

Axes: template shape, grid size, marker count/colours/positions.
Degenerates: one_marker, all_codes, big_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7c5679e5672f"
VERSION = "2.2.0"  # REWRITE: stamp template at markers (was find-pair template; crashed 3/12 on missing color-3 object)
TASK_ID = "7c5679e5672f"

SUMMARY = (
    "One color-3 template shape plus several marker cells in {1,2,4,5} (each "
    "colour = a rotation). Rule: stamp the template (rotated by each marker's "
    "colour) at every marker, in color 8. Template shape, grid size and the "
    "markers vary."
)

INVARIANTS = [
    "exactly one color-3 object (the template)",
    "marker cells use colours in {1,2,4,5}; each codes a quarter-turn rotation",
    "markers leave room for the rotated stamp inside the grid",
]

DEGENERATE_TEXTURES = ("one_marker", "all_codes", "big_template")
HELPFUL_TEXTURES = ("varied", "wide", "many_markers")

_MARKER_COLORS = (1, 2, 4, 5)

AXES = {
    "grid_h":     {"type": "int", "default": "rng 12..18", "valid": "8..24"},
    "grid_w":     {"type": "int", "default": "rng 12..18", "valid": "8..24"},
    "shape_size": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "n_markers":  {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "varied|wide|many_markers|one_marker|all_codes|big_template"},
}


def _walk(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}; tries = 0
    while len(cells) < k and tries < 40:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nc = (r + dr, c + dc)
        if nc not in seen:
            cells.append(nc); seen.add(nc)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _build(rng, h, w, k_shape, n_markers, marker_colors=None):
    g = full_grid(h, w, 0)
    shape = _walk(rng, k_shape)
    sz = max(max(r for r, _ in shape), max(c for _, c in shape)) + 1   # rotation-safe extent
    occupied = set()
    # template (color 3) near the top-left, leaving the rest for markers/stamps
    tr = rng.randint(0, max(0, min(h, w) // 3))
    tc = rng.randint(0, max(0, min(h, w) // 3))
    for (dr, dc) in shape:
        g[tr + dr][tc + dc] = 3
        occupied.add((tr + dr, tc + dc))
    # markers in {1,2,4,5} with room for an sz x sz rotated stamp
    made = 0
    for _ in range(n_markers):
        col = rng.choice(marker_colors) if marker_colors else rng.choice(_MARKER_COLORS)
        for _ in range(40):
            mr = rng.randint(0, h - sz)
            mc = rng.randint(0, w - sz)
            if (mr, mc) in occupied:
                continue
            stamp = {(mr + a, mc + b) for a in range(sz) for b in range(sz)}
            if stamp & occupied:
                continue
            g[mr][mc] = col
            occupied |= stamp
            made += 1
            break
    if made == 0:                               # guarantee >=1 marker
        for _ in range(40):
            mr = rng.randint(0, h - sz)
            mc = rng.randint(0, w - sz)
            stamp = {(mr + a, mc + b) for a in range(sz) for b in range(sz)}
            if stamp & occupied:
                continue
            g[mr][mc] = rng.choice(_MARKER_COLORS)
            occupied |= stamp
            made += 1
            break
    if made == 0:
        raise ValueError("could not place any marker with stamp clearance")
    return g


def _components4_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    bad = sorted({v for row in grid for v in row if v not in (0, 1, 2, 3, 4, 5)})
    if bad:
        errs.append(f"unexpected colors present: {bad}")
    comps3 = _components4_of_color(grid, 3)
    if len(comps3) != 1:
        errs.append("must contain exactly one 4-connected color-3 template")
        return errs
    cells = comps3[0]
    minr = min(r for r, _ in cells); minc = min(c for _, c in cells)
    shape = [(r - minr, c - minc) for r, c in cells]
    sz = max(max(r for r, _ in shape), max(c for _, c in shape)) + 1
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
               if grid[r][c] in _MARKER_COLORS]
    if not markers:
        errs.append("must contain at least one marker cell in {1,2,4,5}")
    for r, c, _ in markers:
        if r + sz > h or c + sz > w:
            errs.append("marker must leave room for the rotated template stamp")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        sz_lo, sz_hi, k_lo, k_hi, n_lo, n_hi = 10, 13, 2, 3, 2, 3
    elif difficulty == "hard":
        sz_lo, sz_hi, k_lo, k_hi, n_lo, n_hi = 15, 24, 3, 5, 3, 6
    else:
        sz_lo, sz_hi, k_lo, k_hi, n_lo, n_hi = 12, 18, 2, 4, 2, 4

    h = ctx.draw_int("grid_h", sz_lo, sz_hi)
    w = ctx.draw_int("grid_w", sz_lo, sz_hi)
    k = ctx.draw_int("shape_size", k_lo, k_hi)
    n = ctx.draw_int("n_markers", n_lo, n_hi)
    return _build(rng, h, w, k, n)


def _draw_from_degenerate(name, rng):
    if name == "one_marker":
        return _build(rng, 12, 12, 3, 1)
    if name == "all_codes":
        return _build(rng, 16, 16, 3, 4, marker_colors=[1, 2, 4, 5])
    return _build(rng, 20, 20, 5, 3)             # big_template
