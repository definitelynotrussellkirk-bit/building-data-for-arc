"""Generator for 9772c176.

Rule: 8-trapezoid (narrower at top and bottom, wider in middle) gets
diamond apex extensions added above and below.

Combinatorial axes (8): grid_h/w, body_h, top_w, position_bias,
anchor_corner, asymmetry_force, palette_size, body_w_delta.
Degenerates: no_trapezoid, full_grid, single_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd24427a4ff0"
VERSION = "2.0.1"  # +self_check for trapezoid-shape invariants
TASK_ID = "fd24427a4ff0"
SUMMARY = (
    "0-bg grid with 1-4 color-8 TRAPEZOIDS (narrower top/bottom "
    "row, wider middle body), each in varied size and position, "
    "mutually isolated. Rule: for EACH color-8 object, compute a "
    "DIAMOND from its top-row width, bottom-row width and top-row "
    "center (apex top-width//2 above the top row, bottom-width//2 "
    "below the bottom row) and paint that diamond in color 4 on "
    "the background 0-cells (the 8-shape is preserved). Net: each "
    "trapezoid gains color-4 apex extensions above and below."
)

INVARIANTS = [
    "1-4 color-8 trapezoids (wider in the middle than the top/bottom row)",
    "each trapezoid has >= 3 rows so top, body, bottom are distinct",
    "trapezoids are mutually isolated (each is its own color-8 object)",
]

POSITION_BIASES = ("center", "top_left", "top_right", "bottom_left", "bottom_right")
DEGENERATE_TEXTURES = ("no_trapezoid", "full_grid", "single_row")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "16-20 easy / 18-24 med / 22-28 hard", "valid": "14..30"},
    "grid_w":         {"type": "int", "default": "16-20 easy / 18-24 med / 22-28 hard", "valid": "14..30"},
    "n_shapes":       {"type": "int", "default": "1-2 easy / 2-3 med / 2-4 hard", "valid": "1..4"},
    "body_h":         {"type": "int", "default": "rng 2..6 per trapezoid", "valid": "2..8"},
    "top_w":          {"type": "int", "default": "rng 3..7 per trapezoid", "valid": "3..9"},
    "position_bias":  {"type": "str", "default": "random scattered",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_size":   {"type": "int", "default": "1 (color 8; rule adds 4)", "valid": "1"},
    "body_w_delta":   {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_trapezoid(g, occ, cr, cc, top_w, body_w, body_h):
    """Paint one color-8 trapezoid at top-left (cr, cc); mark occupancy. Caller has
    already confirmed the bbox + 1-cell halo is clear."""
    off = (body_w - top_w) // 2
    h = len(g); w = len(g[0])
    cells = [(cr, cc + off + i) for i in range(top_w)]
    for r in range(cr + 1, cr + 1 + body_h):
        cells += [(r, cc + i) for i in range(body_w)]
    cells += [(cr + 1 + body_h, cc + off + i) for i in range(top_w)]
    for r, c in cells:
        g[r][c] = 8
        occ[r][c] = True


def _components(grid, color=8):
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify each color-8 component is a real top/bottom-narrow trapezoid."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    colors = {v for row in grid for v in row}
    if not colors <= {0, 8}:
        return [f"unexpected colors in input: {sorted(colors - {0, 8})}"]
    comps = _components(grid, 8)
    if not comps:
        return ["no color-8 trapezoid found"]
    if len(comps) > 4:
        return [f"expected at most four trapezoids, found {len(comps)}"]
    for cells in comps:
        by_row: dict[int, list[int]] = {}
        for r, c in cells:
            by_row.setdefault(r, []).append(c)
        rows = sorted(by_row)
        if len(rows) < 3:
            return ["trapezoid component has fewer than three rows"]
        widths = []
        for r in rows:
            cs = sorted(by_row[r])
            if cs != list(range(cs[0], cs[-1] + 1)):
                return ["trapezoid row is not contiguous"]
            widths.append(len(cs))
        top_w, bot_w = widths[0], widths[-1]
        mid_max = max(widths[1:-1])
        if top_w != bot_w:
            return ["trapezoid top and bottom widths differ"]
        if mid_max <= top_w:
            return ["trapezoid middle is not wider than top/bottom"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 16, 20)
        n_shapes = ctx.draw_int("n_shapes", 1, 2)
        b_lo, b_hi = 2, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 22, 28)
        n_shapes = ctx.draw_int("n_shapes", 2, 4)
        b_lo, b_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 18, 24)
        n_shapes = ctx.draw_int("n_shapes", 2, 3)
        b_lo, b_hi = 3, 6
    w = ctx.draw_int("grid_w", h - 2, h + 2)
    w = max(14, min(30, w))
    g = full_grid(h, w, 0)
    occ = [[False] * w for _ in range(h)]

    placed = 0
    for _ in range(n_shapes * 30):
        if placed >= n_shapes:
            break
        top_w = rng.randint(3, 7)
        body_w = top_w + rng.randint(1, 3)
        body_h = rng.randint(b_lo, b_hi)
        sh = body_h + 2
        if sh > h - 2 or body_w > w - 2:
            continue
        cr = rng.randint(1, h - 1 - sh)
        cc = rng.randint(1, w - 1 - body_w)
        # require the bbox + 1-cell halo clear so each trapezoid is its own 8-object
        halo_ok = True
        for r in range(cr - 1, cr + sh + 1):
            for c in range(cc - 1, cc + body_w + 1):
                if 0 <= r < h and 0 <= c < w and occ[r][c]:
                    halo_ok = False
                    break
            if not halo_ok:
                break
        if not halo_ok:
            continue
        _draw_trapezoid(g, occ, cr, cc, top_w, body_w, body_h)
        placed += 1
    if placed == 0:                       # guarantee >=1 trapezoid
        _draw_trapezoid(g, occ, 2, 3, 4, 6, 3)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(20, 20, 0)
    if name == "no_trapezoid":
        return g
    if name == "single_row":
        for c in range(5, 12):
            g[10][c] = 8
        return g
    if name == "full_grid":
        for r in range(20):
            for c in range(20):
                g[r][c] = 8
        return g
    return g
