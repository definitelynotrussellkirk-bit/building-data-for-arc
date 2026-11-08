"""Generator for arc_additional_puzzle_bank_volume8:H52.

Rule: take the largest color-2 component and the largest color-1
component, normalize each to its bbox, and output their XOR (cells in
exactly one of the two normalized sets), bbox-cropped, painted color 8.

Combinatorial axes: grid size, the two single-component shapes (which
set the XOR output) and their positions.
Degenerates: no_shapes, identical_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "b045d042edd7"
VERSION = "3.0.2"  # reviewer fix: fail-closed via _fallback_valid() when placement exhausted
TASK_ID = "b045d042edd7"
SUMMARY = (
    "0-bg grid (size varies). ONE color-2 (red) SHAPE and ONE color-1 "
    "(blue) SHAPE (random single-component polyominoes whose normalized "
    "forms share >=1 cell and differ in >=1 cell), placed apart. Rule: "
    "take the largest blob of each color, normalize both to their bbox, "
    "and output their XOR (cells in EXACTLY ONE of the two normalized "
    "sets) bbox-cropped, painted COLOR 8 (cyan). The grid size, the two "
    "shapes (which set the XOR) and their positions all vary freely (was "
    "2 fixed shapes whose XOR was always the same 4-cell pattern)."
)

INVARIANTS = [
    "exactly one color-2 blob and one color-1 blob (each its own largest)",
    "each shape is a single connected component",
    "their normalized cell sets share >=1 cell (some cancel) and differ "
    "in >=1 cell (XOR is non-empty)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "identical_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|"
                                "no_shapes|identical_shapes|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the two single-component normalized shapes really teach XOR."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h = len(grid)
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    extra = colors - {1, 2}
    if extra:
        errs.append(f"unexpected non-bg colors {sorted(extra)}")
    def components(color):
        seen = set()
        out = []
        for r in range(h):
            for c in range(w):
                if grid[r][c] != color or (r, c) in seen:
                    continue
                stack = [(r, c)]
                seen.add((r, c))
                cells = set()
                while stack:
                    cr, cc = stack.pop()
                    cells.add((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and
                                grid[nr][nc] == color and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                out.append(cells)
        return out
    by_color = {color: components(color) for color in (1, 2)}
    for color in (1, 2):
        if len(by_color[color]) != 1:
            errs.append(f"expected exactly one color-{color} component, got {len(by_color[color])}")
    if len(by_color[1]) == 1 and len(by_color[2]) == 1:
        a = set(map(tuple, _norm(by_color[2][0])))
        b = set(map(tuple, _norm(by_color[1][0])))
        if not (a & b):
            errs.append("normalized color-2 and color-1 shapes do not overlap")
        if not (a ^ b):
            errs.append("normalized shapes are identical, so XOR would be empty")
    return errs


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _conn_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr, md = (9, 11), (11, 13), (3, 4), 3
    elif difficulty == "hard":
        hr, wr, szr, md = (11, 16), (12, 16), (4, 7), 5
    else:
        hr, wr, szr, md = (9, 13), (11, 14), (4, 6), 4

    for _attempt in range(50):
        s2 = _norm(_conn_poly(rng, rng.randint(*szr), md))
        s1 = _norm(_conn_poly(rng, rng.randint(*szr), md))
        A = set(map(tuple, s2)); B = set(map(tuple, s1))
        if not (A & B):          # must share >=1 cell (some cancel)
            continue
        if not (A ^ B):          # must differ (XOR non-empty)
            continue
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells, color):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, cells, top, left, h, w):
                    for r, c in cells:
                        g[top + r][left + c] = color; occ[top + r][left + c] = True
                    return True
            return False

        if _place(s2, 2) and _place(s1, 1):
            return g

    return _fallback_valid()   # fail closed to a known-valid XOR instance


def _fallback_valid():
    g = full_grid(10, 12, 0)
    # Normalized shapes share two cells and differ in one cell each.
    paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 2)
    paint_at(g, 6, 7, [(0, 0), (0, 1), (1, 1)], 1)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_shapes":
        return g
    if name == "identical_shapes":
        s = [(0, 0), (1, 0), (1, 1)]
        paint_at(g, 1, 1, s, 2)
        paint_at(g, 6, 7, s, 1)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
