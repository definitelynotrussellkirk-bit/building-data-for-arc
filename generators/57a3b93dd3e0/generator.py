"""Generator for arc_puzzle_bank_21_set9_s:S9_H2 — rotate stencil by corner marker, stamp at anchor.

Rule: a color-1 marker in the top-left 2x2 encodes a rotation k ((0,0)->0,
(0,1)->1, (1,1)->2, else->3). Take the color-2 object, rotate its normalized
cells by k, and paint them (color 8) onto a fresh blank grid at the position of
the single color-4 anchor cell.

The old docstring called this a "multi-motif gallery pack" and the generator
added n-2 SUPPLEMENTARY motifs (colors 3/5/6/7/8/9) the rule never reads, and
drew the color-4 anchor as a multi-cell blob (canonical anchor is a single
cell). Now: exactly the marker + one color-2 stencil + one single color-4
anchor, no decoys; the anchor is placed so the rotated stamp lands in-bounds.

Combinatorial axes: marker position (-> rotation), the color-2 stencil
shape/size, the anchor position, grid size.
Degenerates: no_marker, no_stencil, no_anchor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57a3b93dd3e0"
VERSION = "3.0.0"  # WRONG-TASK docstring + decoys: rule reads only the 1-marker (rotation), the color-2 stencil, and a SINGLE color-4 anchor. Old gen added n-2 supplementary motifs the rule ignores + drew the anchor as a multi-cell blob. Now exactly marker + 1 stencil + 1 single anchor (placed so the rotated stamp fits), no decoys; vary marker/shape/anchor/grid.
TASK_ID = "57a3b93dd3e0"

SUMMARY = (
    "0-bg grid (size varies) with: (a) a color-1 MARKER in the top-left 2x2 "
    "(its position encodes a rotation k: (0,0)->0, (0,1)->1, (1,1)->2, "
    "(1,0)->3); (b) one connected color-2 STENCIL (3-6 cells); (c) one SINGLE "
    "color-4 ANCHOR cell. Rule: rotate the stencil's normalized cells by k and "
    "paint them in color 8 onto a fresh blank grid at the anchor position. "
    "Output dims = input dims; only the rotated stamp (color 8) is drawn."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-1 marker inside the top-left 2x2",
    "exactly one connected color-2 stencil",
    "exactly one single color-4 anchor cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_stencil", "no_anchor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "9..18"},
    "marker_pos":     {"type": "int", "default": "rng 0..3 (rotation)", "valid": "0..3"},
    "stencil_cells":  {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "marker_stencil_anchor",
                       "valid": "marker_stencil_anchor"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for (r, c) in cells)


def _rot(cells, k):
    """Match the rule's rotate-norm-cells: (r,c) -> (c, maxr - r), k times."""
    pts = _norm(cells)
    for _ in range(k % 4):
        maxr = max(r for r, _ in pts)
        pts = _norm([(c, maxr - r) for (r, c) in pts])
    return pts


def _build_stencil(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    return _norm(cells)


def _free(g, cells):
    """All cells in-bounds, empty, and with an empty 8-neighborhood.

    The previous version allowed an occupied cell if that cell was part of
    `cells`, so a stencil could overwrite the top-left rotation marker.
    """
    h, w = len(g), len(g[0])
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cset and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    rng = ctx.draw_rng("layout")
    marker_k = ctx.draw_int("marker_pos", 0, 3)
    marker_xy = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 0)}[marker_k]

    for _outer in range(60):
        g = full_grid(h, w, 0)
        g[marker_xy[0]][marker_xy[1]] = 1
        stencil = _build_stencil(rng, rng.randint(3, 6))
        # the OUTPUT stamps the rotated stencil at the anchor -> pick an anchor
        # so the rotated stamp fits in-bounds (output quality).
        rot = _rot(stencil, marker_k)
        rh = max(r for r, _ in rot) + 1
        rw = max(c for _, c in rot) + 1
        if rh > h or rw > w:
            continue
        ar = rng.randint(0, h - rh)
        ac = rng.randint(0, w - rw)
        # place the color-2 stencil somewhere clear (its grid position is
        # irrelevant to the rule, which normalizes it).
        sh = max(r for r, _ in stencil) + 1
        sw = max(c for _, c in stencil) + 1
        placed = False
        for _ in range(80):
            sr = rng.randint(0, h - sh)
            sc = rng.randint(0, w - sw)
            scells = [(sr + r, sc + c) for r, c in stencil]
            if _free(g, scells):
                for r, c in scells:
                    g[r][c] = 2
                placed = True
                break
        if not placed:
            continue
        if g[ar][ac] == 0 and _free(g, [(ar, ac)]):
            g[ar][ac] = 4
            return g
    raise ValueError("could not realize 57a3 layout")


def _components_of(grid, color):
    h, w = len(grid), len(grid[0])
    targets = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    out = []
    while targets:
        start = targets.pop(); cells = [start]; stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in targets:
                    targets.remove(p); stack.append(p); cells.append(p)
        out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    allowed = {0, 1, 2, 4}
    if any(v not in allowed for row in grid for v in row):
        errors.append("only colors 1(marker), 2(stencil), and 4(anchor) should appear")
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(markers) != 1 or not (markers and markers[0][0] < 2 and markers[0][1] < 2):
        errors.append("expected exactly one color-1 marker inside the top-left 2x2")
    stencils = _components_of(grid, 2)
    if len(stencils) != 1:
        errors.append(f"expected exactly one connected color-2 stencil, found {len(stencils)}")
    elif not (3 <= len(stencils[0]) <= 6):
        errors.append("stencil should contain 3..6 cells")
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4]
    if len(anchors) != 1:
        errors.append("expected exactly one single-cell color-4 anchor")
    if len(markers) == 1 and len(stencils) == 1 and len(anchors) == 1:
        marker_k = {(0, 0): 0, (0, 1): 1, (1, 1): 2, (1, 0): 3}.get(markers[0])
        rot = _rot(stencils[0], marker_k)
        ar, ac = anchors[0]
        if ar + max(r for r, _ in rot) >= len(grid) or ac + max(c for _, c in rot) >= len(grid[0]):
            errors.append("rotated stencil must fit in-bounds at the anchor")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    g[0][0] = 1
    if name == "no_marker":
        g[0][0] = 0
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 2
        g[6][8] = 4
        return g
    if name == "no_stencil":
        g[6][8] = 4
        return g
    if name == "no_anchor":
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 2
        return g
    return g
