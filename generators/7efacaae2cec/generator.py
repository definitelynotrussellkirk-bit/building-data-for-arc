"""Generator for 256b0a75 — 4-L frame + cross with marker rays.

Rule (per the canonical Racket): the input has exactly 4 L-shaped 3-cell
components marking the corners of a rectangle.  Three Ls share a "frame"
color, one L is the "cross" color.  Outside the frame:
  * cells in the row-band (frame's row range, columns outside frame) extend
    rays in the cross color, with any single-cell markers in the band
    contributing their own color out to the grid edge in the away-from-frame
    direction;
  * cells in the col-band behave symmetrically;
  * cells in neither band stay as input.

This generator produces diverse instances by varying the grid size, frame
position, frame and cross colors, and the scattered marker positions /
colors / counts.  The frame interior is always empty (per the canonical
constraint).  The output of the puzzle is computed by the existing rule
in `solvers/grounded_rules.py`, so the generator only emits the input grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, set_cell

GENERATOR_ID = "7efacaae2cec"
VERSION = "2.1.0"
TASK_ID = "7efacaae2cec"
SUMMARY = (
    "Random frame bbox + 3 L-corners in frame color + 1 L-corner in cross "
    "color, scattered colored markers in the cross bands and corners. "
    "Output is derived by the canonical 4-L frame + cross rule."
)

INVARIANTS = [
    "background is 0",
    "exactly 4 L-shaped 3-cell components in the input",
    "3 of the 4 Ls share a 'frame' color, 1 is the 'cross' color",
    "the 4 Ls mark exactly the 4 corners of one axis-aligned rectangle",
    "the rectangle interior is empty",
    "no other 3-cell components exist (so the L-detection is unambiguous)",
]

AXES = {
    "grid_size": {"type": "int", "default": "rng 18..26", "valid": "14..30"},
    "frame_h":   {"type": "int", "default": "rng 6..10",  "valid": "4..(grid-4)"},
    "frame_w":   {"type": "int", "default": "rng 6..10",  "valid": "4..(grid-4)"},
}

# 4 L-shape stamps, one for each corner.  Each L occupies the corner plus
# two cells extending inward (one along the frame's top/bottom edge, one
# along the side edge).  Cells are listed as (dr, dc) offsets from the
# corner cell of the frame's bbox.
_L_OFFSETS = {
    "tl": [(0, 0), (0, 1), (1, 0)],
    "tr": [(0, 0), (0, -1), (1, 0)],
    "bl": [(0, 0), (0, 1), (-1, 0)],
    "br": [(0, 0), (0, -1), (-1, 0)],
}


def _stamp_l(g, anchor_r, anchor_c, kind, color):
    for dr, dc in _L_OFFSETS[kind]:
        set_cell(g, anchor_r + dr, anchor_c + dc, color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")

    H = ctx.draw_int("grid_size", 18, 26)
    W = H + rng.randint(-2, 2)
    W = max(14, min(30, W))

    fh = ctx.draw_int("frame_h", 6, min(10, H - 4))
    fw = ctx.draw_int("frame_w", 6, min(10, W - 4))

    rmin = rng.randint(2, H - fh - 2)
    cmin = rng.randint(2, W - fw - 2)
    rmax = rmin + fh - 1
    cmax = cmin + fw - 1

    palette = list(range(1, 10))
    rng.shuffle(palette)
    frame_color = palette[0]
    cross_color = palette[1]

    g = full_grid(H, W, 0)

    corners = ["tl", "tr", "bl", "br"]
    rng.shuffle(corners)
    cross_corner = corners[0]
    corner_anchors = {
        "tl": (rmin, cmin),
        "tr": (rmin, cmax),
        "bl": (rmax, cmin),
        "br": (rmax, cmax),
    }
    for corner, anchor in corner_anchors.items():
        col = cross_color if corner == cross_corner else frame_color
        _stamp_l(g, anchor[0], anchor[1], corner, col)

    # Marker palette excludes frame color (would be misread as part of frame
    # if it landed in the cross bands and got picked up as a 3-cell
    # component if multiple landed adjacent).  Cross color is allowed but
    # rare so the unique-3-cell-per-color invariant is preserved.
    marker_palette = [c for c in range(1, 10) if c not in {frame_color, cross_color}]

    forbidden = {(r, c) for r in range(H) for c in range(W) if g[r][c] != 0}
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            forbidden.add((r, c))

    def pool_above():
        return [(r, c) for r in range(0, rmin)
                for c in range(cmin, cmax + 1) if (r, c) not in forbidden]

    def pool_below():
        return [(r, c) for r in range(rmax + 1, H)
                for c in range(cmin, cmax + 1) if (r, c) not in forbidden]

    def pool_left():
        return [(r, c) for r in range(rmin, rmax + 1)
                for c in range(0, cmin) if (r, c) not in forbidden]

    def pool_right():
        return [(r, c) for r in range(rmin, rmax + 1)
                for c in range(cmax + 1, W) if (r, c) not in forbidden]

    def pool_corner():
        return [(r, c) for r in range(H) for c in range(W)
                if not (rmin <= r <= rmax) and not (cmin <= c <= cmax)
                and (r, c) not in forbidden]

    def marker_clear(cell):
        r0, c0 = cell
        if cell in forbidden or g[r0][c0] != 0:
            return False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r0 + dr, c0 + dc
            if 0 <= rr < H and 0 <= cc < W and g[rr][cc] != 0:
                return False
        return True

    n_band_max = rng.randint(3, 8)
    for region_pool in (pool_above(), pool_below(), pool_left(),
                        pool_right(), pool_corner()):
        n = rng.randint(0, n_band_max)
        # Keep markers as true singletons globally.  The pools are materialized
        # before the loop, so re-filter before every pick against the current
        # grid/forbidden set; otherwise a later region can place next to an
        # earlier marker or next to an L-corner and corrupt L detection.
        for _ in range(n):
            region_pool[:] = [p for p in region_pool if marker_clear(p)]
            if not region_pool:
                break
            pick = rng.choice(region_pool)
            color = rng.choice(marker_palette)
            set_cell(g, pick[0], pick[1], color)
            r0, c0 = pick
            forbidden.update({pick, (r0 - 1, c0), (r0 + 1, c0),
                              (r0, c0 - 1), (r0, c0 + 1)})
            region_pool[:] = [p for p in region_pool if p not in forbidden]

    return g



def _components4(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[tuple[int, list[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _norm_cells(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


_L_PATTERNS = []
for _offs in _L_OFFSETS.values():
    _r0 = min(r for r, _ in _offs)
    _c0 = min(c for _, c in _offs)
    _L_PATTERNS.append({(r - _r0, c - _c0) for r, c in _offs})


def _is_l3(cells):
    return len(cells) == 3 and _norm_cells(cells) in _L_PATTERNS


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the 4-L frame + marker-ray input."""
    errors: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any((not isinstance(v, int) or not 0 <= v <= 9) for row in grid for v in row):
        errors.append("grid values must be ARC digits 0..9")
    comps = _components4(grid)
    l_comps = [(color, cells) for color, cells in comps if _is_l3(cells)]
    if len(l_comps) != 4:
        errors.append(f"expected exactly 4 L-shaped 3-cell components, found {len(l_comps)}")
    counts: dict[int, int] = {}
    for color, _ in l_comps:
        counts[color] = counts.get(color, 0) + 1
    if sorted(counts.values()) != [1, 3]:
        errors.append("L colors must split as three frame-color Ls plus one cross-color L")
    for _, cells in comps:
        if not _is_l3(cells) and len(cells) != 1:
            errors.append("non-L markers must remain singleton components")
    if len(l_comps) == 4:
        bbs = [_bbox(cells) for _, cells in l_comps]
        row_extrema = sorted({v for r1, _, r2, _ in bbs for v in (r1, r2)})
        col_extrema = sorted({v for _, c1, _, c2 in bbs for v in (c1, c2)})
        if len(row_extrema) < 2 or len(col_extrema) < 2:
            errors.append("the four Ls must define a nontrivial rectangle")
    return sorted(set(errors))
