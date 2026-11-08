"""Generator for arc_additional_puzzle_bank_volume8:M56 — rotate template by k count, stamp at anchor.

Rule: count k = number of color-1 cells anywhere on the grid. Find
the largest color-3 4-connected blob → template shape. Normalize.
Apply transform by k: k=1 identity, k=2 rot90, k=3 rot180, k=4 flip-h.
Find the single color-7 anchor cell. Paint the transformed shape at
the anchor position with color 8 (anchor stays 7).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7788d30a256"
VERSION = "2.1.0"  # keep blue control cells out of the future cyan stamp footprint
TASK_ID = "d7788d30a256"
SUMMARY = (
    "0-bg grid (h~9-13, w~"
    "11-15) with: (a) ONE "
    "COLOR-3 (green) BLOB "
    "of 3-5 cells at a "
    "random clear position "
    "(the TEMPLATE); (b) "
    "ONE COLOR-7 (orange) "
    "ANCHOR cell at a non-"
    "adjacent position with "
    "enough room for the "
    "rotated template; (c) "
    "k COLOR-1 (blue) CELLS "
    "at scattered positions "
    "(1 ≤ k ≤ 4) — k counts "
    "the rotation. The "
    "template, anchor, and "
    "1-cells are mutually "
    "4-non-adjacent. Rule "
    "(ROTATE TEMPLATE BY k, "
    "STAMP AT ANCHOR IN "
    "COLOR 8): COUNT k = "
    "number of color-1 "
    "cells. Identify the "
    "LARGEST COLOR-3 BLOB "
    "(the TEMPLATE). "
    "NORMALIZE the template "
    "(shift to origin). "
    "APPLY transform: k=1 "
    "identity, k=2 90° CW, "
    "k=3 180°, k=4 horizontal "
    "flip. Find the COLOR-7 "
    "ANCHOR. STAMP the "
    "TRANSFORMED template "
    "at the anchor position "
    "in COLOR 8. Template, "
    "anchor, k-markers stay. "
    "Net: blue-count picks "
    "rotation, applied to "
    "green template, stamped "
    "in cyan at orange "
    "anchor."
)

# Rivals: 'output is input' refuted by demos with ≥1 stamped 8-cell.
# 'stamp without rotation' refuted by demos with k=2..4 producing
# differently-oriented stamps. 'use template color (3) for stamp'
# refuted by any demo (always 8). 'place at template, not anchor'
# refuted by demos with anchor and template far apart. 4 demos with
# k=1, k=2, k=3, k=4 cover the rotation table.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "1 ≤ k ≤ 4 color-1 cells",
    "exactly one color-3 4-connected blob (the template)",
    "exactly one color-7 anchor cell",
    "template, anchor, and 1-cells don't 4-touch each other",
]

AXES = {
    "grid_h":      {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":      {"type": "int", "default": "rng 11..15", "valid": "10..18"},
    "k":           {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "template_size":{"type": "int", "default": "rng 3..5", "valid": "3..6"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(8, 10); w = rng.randint(10, 12)
        k = rng.randint(1, 2); t_size = rng.randint(3, 4)
    elif difficulty == "hard":
        h = rng.randint(12, 16); w = rng.randint(14, 18)
        k = rng.randint(1, 4); t_size = rng.randint(4, 6)
    else:
        h = rng.randint(10, 13); w = rng.randint(12, 15)
        k = rng.randint(1, 4); t_size = rng.randint(3, 5)

    g = full_grid(h, w, 0)
    # Template at a random clear position
    template = _grow_blob(rng, t_size)
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    # Need bbox big enough to stamp the rotated shape from anchor too
    # We'll stamp from anchor with offsets within max(th,tw); ensure
    # anchor leaves enough room for any of 4 transforms.
    max_dim = max(th, tw)
    for _attempt in range(80):
        tr = rng.randint(0, h - th)
        tc = rng.randint(0, w - tw)
        # leave 1-cell buffer
        clear = True
        for dr, dc in template:
            if g[tr + dr][tc + dc] != 0:
                clear = False; break
        if not clear:
            continue
        for dr, dc in template:
            g[tr + dr][tc + dc] = 3
        break

    # Anchor: needs room to fit any of the 4 transforms (shape fits in
    # max_dim × max_dim box from anchor). Place far from template.
    for _attempt in range(80):
        ar = rng.randint(0, h - max_dim)
        ac = rng.randint(0, w - max_dim)
        # Must not collide with template or its buffer
        if any(g[ar + dr][ac + dc] != 0
               for dr in range(max_dim) for dc in range(max_dim)
               if 0 <= ar + dr < h and 0 <= ac + dc < w):
            continue
        # Must not be too close to template
        if any(abs(ar - tr) + abs(ac - tc) < max_dim + 2 for tr, tc in [(template[0][0], template[0][1])]):
            pass
        g[ar][ac] = 7
        break

    # k color-1 cells in empty spots that will remain visible after the
    # cyan stamp.  The old generator only avoided the anchor's immediate
    # neighborhood, so control cells could land inside the future transformed
    # template footprint and then be overwritten by the canonical rule.
    stamp_cells = _stamp_cells(template, k, ar, ac)
    placed = 0
    attempts = 0
    while placed < k and attempts < 300:
        attempts += 1
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] != 0 or (r, c) in stamp_cells:
            continue
        # Avoid placing 1-cells adjacent to template or anchor.
        if any(g[r + dr][c + dc] in (3, 7)
               for dr in [-1, 0, 1] for dc in [-1, 0, 1]
               if 0 <= r + dr < h and 0 <= c + dc < w):
            continue
        g[r][c] = 1
        placed += 1
    return g


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _rot90(cells):
    h = max(r for r, _ in cells) + 1
    return _normalize([(c, h - 1 - r) for r, c in cells])


def _flip_h(cells):
    w = max(c for _, c in cells) + 1
    return _normalize([(r, w - 1 - c) for r, c in cells])


def _transform(cells, k):
    cells = _normalize(cells)
    if k == 1:
        return cells
    if k == 2:
        return _rot90(cells)
    if k == 3:
        return _rot90(_rot90(cells))
    return _flip_h(cells)


def _stamp_cells(template, k, ar, ac):
    return {(ar + r, ac + c) for r, c in _transform(template, k)}


def _selfcheck_color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append(cells)
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    greens = _selfcheck_color_components(grid, 3)
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    ones = sum(v == 1 for row in grid for v in row)
    lo, hi = {"easy": (1, 2), "hard": (1, 4), None: (1, 4)}.get(difficulty, (1, 4))
    if len(greens) != 1:
        errs.append(f"expected exactly one green template component, got {len(greens)}")
    if len(anchors) != 1:
        errs.append(f"expected exactly one anchor, got {len(anchors)}")
    if not (lo <= ones <= hi):
        errs.append(f"expected {lo}..{hi} blue control cells, got {ones}")
    if len(greens) == 1 and len(anchors) == 1 and 1 <= ones <= 4:
        ar, ac = anchors[0]
        stamp = {(ar + r, ac + c) for r, c in _transform(greens[0], ones)}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in stamp):
            errs.append("future cyan stamp footprint must stay in bounds")
        elif any(grid[r][c] in (1, 3) for r, c in stamp):
            errs.append("future cyan stamp footprint should not overwrite blue controls or green template")
    return errs
