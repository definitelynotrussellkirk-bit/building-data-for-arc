"""Generator for arc_puzzle_bank_21_set11_bundle:hard_k20 — connect color-sorted markers.

Rule: take each marker's center; sort by color asc; draw an L-path
(horizontal then vertical) from each consecutive pair of centers,
painted with the smaller-colored object's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, collinear, single_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee822284e294"
VERSION = "3.0.0"  # multi-cell marker SHAPES (rule uses bbox center; canonical uses pluses) + vary count
TASK_ID = "ee822284e294"
SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) with exactly 3 SINGLE-CELL "
    "MARKERS in distinct non-zero colors. Markers are placed "
    "with Manhattan distance ≥ 3 from each other (so they "
    "don't touch and the L-paths are visible). They should "
    "not all share the same row/column (non-collinear). Rule: "
    "for each color-object, compute its bbox center (integer "
    "midpoint). Sort markers by color value ascending. For "
    "each consecutive PAIR of sorted centers (a, b): draw a "
    "HORIZONTAL segment from (r_a, c_a) to (r_a, c_b) painted "
    "with color_a, then a VERTICAL segment from (r_a, c_b) to "
    "(r_b, c_b) painted with color_a (the FIRST marker's "
    "color of the pair = smaller color). Finally re-paint each "
    "original marker on top. Net effect: L-paths connect "
    "color-sorted markers, each L colored by the smaller of "
    "the pair."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "2-4 multi-cell marker SHAPES (plus / small blob) in distinct non-zero colors",
    "marker shapes are 4-conn isolated (distinct components with clear bbox centers)",
    "shape bbox centers are not all collinear (so the connecting L-paths have corners)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "collinear", "single_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 2..4 by difficulty", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "= n_markers", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "non_collinear_marker_shapes",
                       "valid": "non_collinear_marker_shapes"},
    "n_distinct_colors": {"type": "int", "default": "= n_markers", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_markers", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_markers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15)
        n = ctx.draw_int("n_markers", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(50):
        g = full_grid(h, w, 0)
        palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        centers = []
        ok = True
        for color in palette:
            shape = _marker_shape(rng)                     # multi-cell (plus/blob)
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            done = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                # 1-ring isolation so each shape is a distinct component
                if any(g[rr][cc] != 0 for r, c in cells
                       for rr in range(max(0, r - 1), min(h, r + 2))
                       for cc in range(max(0, c - 1), min(w, c + 2))):
                    continue
                for (r, c) in cells:
                    g[r][c] = color
                cr = (min(p[0] for p in cells) + max(p[0] for p in cells)) // 2
                cc2 = (min(p[1] for p in cells) + max(p[1] for p in cells)) // 2
                centers.append((cr, cc2))
                done = True
                break
            if not done:
                ok = False; break
        # require not-all-collinear centers (so L-paths have corners)
        if ok and (n < 3 or not _collinear(centers)):
            return g
    return g  # fallback (rare)


_PLUS = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
_BLOBS = [
    _PLUS,
    [(0, 0), (0, 1), (1, 0), (1, 1)],          # 2x2
    [(0, 0), (0, 1), (0, 2), (1, 1)],          # T
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],  # plus (alias)
    [(0, 0), (1, 0), (1, 1), (2, 1)],          # S
    [(1, 0), (1, 1), (1, 2), (0, 1), (2, 1)],  # plus
]


def _marker_shape(rng):
    return rng.choice(_BLOBS)


def _collinear(pts):
    if len(pts) < 3:
        return False
    return (len({r for r, _ in pts}) == 1 or len({c for _, c in pts}) == 1)


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # Empty grid — rule has no center to L-connect.
        return g
    if name == "collinear":
        # Markers all on the same row — L-paths collapse to straight
        # segments, removing the L-corner evidence of the rule.
        g[4][2] = 1; g[4][6] = 2; g[4][10] = 3
        return g
    if name == "single_marker":
        # Just one marker — no pair to connect.
        g[4][6] = 4
        return g
    return g


def _sc_components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _sc_components_by_color(grid)
    lo, hi = (2, 3) if difficulty == "easy" else ((3, 4) if difficulty == "hard" else (3, 4))
    if not (lo <= len(comps) <= hi):
        errors.append(f"expected {lo}..{hi} marker shapes, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errors.append("marker colors must be distinct")
    centers = []
    for _color, cells in comps:
        if len(cells) < 2:
            errors.append("normal marker shapes must be multi-cell")
        cr = (min(r for r, _ in cells) + max(r for r, _ in cells)) // 2
        cc = (min(c for _, c in cells) + max(c for _, c in cells)) // 2
        centers.append((cr, cc))
    if len(centers) >= 3 and _collinear(centers):
        errors.append("marker centers must not be all collinear")
    return errors
