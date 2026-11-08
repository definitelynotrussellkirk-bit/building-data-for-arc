"""Generator for v0_original:hard_03 — stamp a template shape at each marker.

Rule: there is ONE multi-cell TEMPLATE component (size > 1) and several SINGLE-cell
MARKER components. On a blank canvas, for EACH marker, paste the template's
cropped shape with its top-left at the marker's position, recolored to the FIRST
marker's color. The original template and markers do not otherwise appear; cells
that fall out of bounds are clipped.

Prior generator was the WRONG TASK ("vertical gallery pack"): it produced 3-4
multi-cell blobs and NO single-cell markers, so the rule found no markers and
returned an all-blank grid (dup-outputs, uniq_out ~6%). This version produces one
template blob + 2-4 single markers of a distinct color, matching canonical.

Rule-safe diversity: grid size, template shape/size, marker count/positions, colors.
Degenerates: no_template, no_markers, single_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f3076f3858b4"
VERSION = "3.0.0"  # WRONG-TASK fix: template + single-cell markers (was 3-4 blobs, no markers -> blank output)
TASK_ID = "f3076f3858b4"

SUMMARY = (
    "0-bg grid with ONE multi-cell TEMPLATE shape (3-5 cells, color A) and 2-4 "
    "SINGLE-cell MARKERS (color B != A) at scattered isolated positions. Rule: on "
    "a blank canvas, stamp the template's shape at EACH marker (template's top-left "
    "aligned to the marker), recolored to the first marker's color; out-of-bounds "
    "cells clip. Net: the template is replicated at every marker in the marker "
    "color. (Was: 3-4 blobs, no markers -> rule returned a blank grid.)"
)

INVARIANTS = [
    "background is 0",
    "exactly one multi-cell (size>1) template component in color A",
    ">=2 single-cell markers in a distinct color B",
    "template and markers are separate 4-connected components (1-cell buffer)",
    "each marker leaves room for the template stamp to land in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_markers", "single_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":     {"type": "int", "default": "8-10 easy / 9-13 med / 12-16 hard", "valid": "6..18"},
    "grid_w":     {"type": "int", "default": "9-11 easy / 11-14 med / 13-18 hard", "valid": "6..20"},
    "n_markers":  {"type": "int", "default": "2-3 easy / 2-4 med / 3-5 hard", "valid": "1..6"},
    "template_size": {"type": "int", "default": "2-4 easy / 3-5 med / 3-6 hard", "valid": "2..7"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        n = (r + dr, c + dc)
        if n not in seen:
            cells.append(n); seen.add(n)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, mr_, tsz = (8, 10), (9, 11), (2, 3), (2, 4)
    elif difficulty == "hard":
        hr, wr, mr_, tsz = (12, 16), (13, 18), (3, 5), (3, 6)
    else:
        hr, wr, mr_, tsz = (9, 13), (11, 14), (2, 4), (3, 5)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        a, b = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)   # template / marker colors

        # template blob
        shape = _build_motif(rng, rng.randint(*tsz))
        th = max(r for r, _ in shape) + 1; tw = max(c for _, c in shape) + 1
        if th > h or tw > w:
            continue
        placed_t = False
        for _ in range(60):
            r0 = rng.randint(0, h - th); c0 = rng.randint(0, w - tw)
            if _free(g, r0, c0, r0 + th - 1, c0 + tw - 1):
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = a
                placed_t = True
                break
        if not placed_t:
            continue

        # single-cell markers in the full-stamp-fit region (top-left in-bounds)
        n_markers = rng.randint(*mr_)
        placed = 0
        for _ in range(300):
            if placed >= n_markers:
                break
            if h - th < 0 or w - tw < 0:
                break
            mr = rng.randint(0, h - th); mc = rng.randint(0, w - tw)
            if _free(g, mr, mc, mr, mc):
                g[mr][mc] = b
                placed += 1
        if placed >= 2:
            return g
    raise ValueError("could not realize template + markers layout")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the template-plus-markers stamping task."""
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    bad = sorted({v for row in grid for v in row if not isinstance(v, int) or v < 0 or v > 9})
    if bad:
        errs.append(f"colors outside 0..9: {bad}")
    comps = _components(grid)
    multi = [(color, cells) for color, cells in comps if len(cells) > 1]
    singles = [(color, cells[0]) for color, cells in comps if len(cells) == 1]
    if len(multi) != 1:
        errs.append(f"expected exactly one multi-cell template component; got {len(multi)}")
    if len(singles) < 2:
        errs.append(f"expected at least two single-cell markers; got {len(singles)}")
    if not multi or len(singles) < 2:
        return errs
    template_color, template_cells = multi[0]
    marker_colors = {color for color, _cell in singles}
    if len(marker_colors) != 1:
        errs.append(f"markers should share one color; got {sorted(marker_colors)}")
    if template_color in marker_colors:
        errs.append("marker color must differ from template color")
    r0 = min(r for r, _ in template_cells); r1 = max(r for r, _ in template_cells)
    c0 = min(c for _, c in template_cells); c1 = max(c for _, c in template_cells)
    th, tw = r1 - r0 + 1, c1 - c0 + 1
    for _color, (mr, mc) in singles:
        if mr + th > h or mc + tw > w:
            errs.append(f"marker {(mr, mc)} cannot fit the template bbox {th}x{tw} in-bounds")
            break
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_template":              # only single cells, no multi-cell template
        g[2][2] = 8; g[5][6] = 8
        return g
    if name == "no_markers":               # template but no markers -> blank output
        for r, c in [(2, 2), (2, 3), (3, 2)]:
            g[r][c] = 4
        return g
    if name == "single_marker":            # template + one marker (single stamp)
        for r, c in [(1, 1), (1, 2), (2, 1)]:
            g[r][c] = 4
        g[5][6] = 8
        return g
    return g
