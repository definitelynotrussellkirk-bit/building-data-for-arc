"""Generator for arc_additional_puzzle_bank_volume3:E19 — Recolor 1-cell to 4 if it has 3 cardinal 1-neighbors.

Rule: cell (r,c) with value 1 and exactly 3 cardinal neighbors of
value 1 → becomes 4 (a T-shape center).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_Ts,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_T_centers, only_lines, full_plus.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "ae1648cd669b"
VERSION = "2.1.0"  # enforce non-touching T-shapes plus a true non-T distractor bar; strengthen self_check.
TASK_ID = "ae1648cd669b"
SUMMARY = (
    "0-bg grid (h~7-9, w~9-11) containing color-1 "
    "(blue) cells arranged as: (a) 2 T-SHAPES "
    "(each = a 4-cell T: 3-cell horizontal or "
    "vertical bar + 1 stem cell, where the stem "
    "cell has exactly 3 cardinal blue neighbors); "
    "T-shapes vary in orientation (up, down, "
    "left, right T's); (b) at least 1 "
    "DISTRACTOR — a straight 3-cell BAR of "
    "color 1 (no cell has 3 neighbors). All "
    "1-shapes are non-touching with their "
    "neighborhoods. Rule: for every cell (r, c) "
    "with VALUE 1, COUNT its CARDINAL "
    "neighbors that are also 1. If the count is "
    "EXACTLY 3, RECOLOR that cell to color 4 "
    "(yellow). Otherwise leave it as 1. Net: "
    "T-shape CENTERS become yellow (one cell "
    "per T), arms stay blue, distractor bars "
    "stay fully blue."
)

INVARIANTS = [
    "≥2 T-shaped 1-shapes (center has 3 cardinal 1-neighbors)",
    "≥1 distractor 1-blob that is not a T (e.g. straight line)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_T_centers", "only_lines", "full_plus")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_Ts":           {"type": "int", "default": "2", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread",
                       "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 1 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _t_center_count(grid):
    h, w = len(grid), len(grid[0])
    n = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1:
                continue
            deg = sum(
                1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 1
            )
            if deg == 3:
                n += 1
    return n


def _has_nont_distractor(grid):
    for cells in _components(grid):
        cell_set = set(cells)
        has_t = False
        for r, c in cells:
            deg = sum(
                1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if (r + dr, c + dc) in cell_set
            )
            if deg == 3:
                has_t = True
                break
        if not has_t and len(cells) >= 3:
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify two real T centers plus a visible non-T distractor component."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    t_centers = _t_center_count(grid)
    if t_centers < 2:
        errs.append(f"expected at least two T-centers, found {t_centers}")
    if not _has_nont_distractor(grid):
        errs.append("expected a separate non-T distractor component; found none")
    if any(v not in (0, 1) for row in grid for v in row):
        errs.append("input should contain only 0 and 1")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    Ts = [
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (0, 1)],
    ]
    bar = [(0, 0), (0, 1), (0, 2)]

    def bbox(shape):
        rs = [r for r, _ in shape]
        cs = [c for _, c in shape]
        return min(rs), min(cs), max(rs), max(cs)

    def can_place(g, top, left, shape):
        mr, mc, xr, xc = bbox(shape)
        # one-cell moat: components must not merge through accidental touching.
        for r in range(top + mr - 1, top + xr + 2):
            for c in range(left + mc - 1, left + xc + 2):
                if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                    return False
        return True

    def place_shape(g, shape, *, band):
        mr, mc, xr, xc = bbox(shape)
        sh = xr - mr + 1
        sw = xc - mc + 1
        if band == "top":
            row_choices = list(range(0, max(1, h // 3 - sh + 1)))
            col_choices = list(range(0, max(1, w // 2 - sw + 1)))
        elif band == "bottom_right":
            row_choices = list(range(max(0, h - sh - h // 3), h - sh + 1))
            col_choices = list(range(max(0, w - sw - w // 2), w - sw + 1))
        else:  # bottom-left distractor band
            row_choices = list(range(max(0, h - sh - 1), h - sh + 1))
            col_choices = list(range(0, max(1, w - sw + 1)))
        rng.shuffle(row_choices)
        rng.shuffle(col_choices)
        for top0 in row_choices:
            for left0 in col_choices:
                top = top0 - mr
                left = left0 - mc
                if top + mr < 0 or left + mc < 0 or top + xr >= h or left + xc >= w:
                    continue
                if can_place(g, top, left, shape):
                    paint_at(g, top, left, shape, 1)
                    return True
        return False

    # The old coordinate recipe let the bar touch/merge with a T in ~36% of
    # default samples, deleting the required non-T contrast.  Re-draw whole
    # layouts until the executable invariant is actually true.
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        shapes = [rng.choice(Ts), rng.choice(Ts)]
        rng.shuffle(shapes)
        if (place_shape(g, shapes[0], band="top")
                and place_shape(g, shapes[1], band="bottom_right")
                and place_shape(g, bar, band="bottom_left")
                and not self_check(g)):
            return g
    raise ValueError("could not realize two isolated T-shapes plus a non-T bar")


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_T_centers":
        # only color-1 cells with ≤2 cardinal 1-neighbors → no T-center exists, rule fires zero times
        # singletons + a 2-cell pair
        g[2][2] = 1
        g[5][7] = 1
        g[6][2] = 1; g[6][3] = 1
        return g
    if name == "only_lines":
        # straight 4-cell lines → endpoints have 1 neighbor, middles have 2; never 3
        for c in range(1, 5): g[2][c] = 1
        for r in range(3, 7): g[r][8] = 1
        return g
    if name == "full_plus":
        # +-shape (5 cells: center + 4 arms) → center has 4 neighbors (not 3) → predicate fails
        cr, cc = 4, 5
        g[cr][cc] = 1
        g[cr - 1][cc] = 1; g[cr + 1][cc] = 1
        g[cr][cc - 1] = 1; g[cr][cc + 1] = 1
        return g
    return g
