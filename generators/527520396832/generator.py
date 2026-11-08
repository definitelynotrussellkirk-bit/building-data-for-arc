"""Generator for 4c177718.

Rule: a full color-5 row divides the grid. The TOP region holds a color-2 "T"
(a bar + a perpendicular stem) and an "other"-colored shape; the BOTTOM region
holds a "bottom"-colored shape. The T's stem direction (bar at top -> stem down,
bar at bottom -> stem up) decides whether the other shape is stacked BELOW or
ABOVE the bottom shape (column-aligned to the bottom shape) in the output, which
is the bottom region with the other shape added.

The old generator hardcoded a 13x11 grid with FIXED T / bottom / other shapes
(only the two colors + direction varied; canonical is 15x15) -> shape-locked in
and out, 48% dup. Now: vary the grid size, the divider row, the T position, the
bottom and other shapes (random polyominoes), and positions.

Combinatorial axes: grid size, divider row, T position + direction, the bottom
and other shapes, colors.
Degenerates: no_divider, no_t, no_bottom.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect, paint_at

GENERATOR_ID = "527520396832"
RULE_HASH = "507432e727ff"  # canonical rule this generator was written against
VERSION = "2.1.0"  # v2.1.0: add executable self_check for divider/T/shape stacking inputs.
TASK_ID = "527520396832"
SUMMARY = (
    "0-bg grid (size varies). A full COLOR-5 ROW divides it. TOP region: a "
    "COLOR-2 T (a 3-cell bar + a 2-cell perpendicular stem; stem points down "
    "when the bar is on top, up when the bar is on the bottom) plus an "
    "'other'-colored random shape. BOTTOM region: a 'bottom'-colored random "
    "shape. Rule: output = the bottom region with the other shape stacked "
    "directly BELOW (stem down) or ABOVE (stem up) the bottom shape, "
    "column-aligned to it. Output dims = bottom-region dims."
)

INVARIANTS = [
    "a full color-5 row divides the grid",
    "the top region has a color-2 T (bar + stem) and one other-colored shape",
    "the bottom region has one bottom-colored shape",
    "the T stem direction selects above/below stacking of the other shape",
]

DIRECTIONS = ("down", "up")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_divider", "no_t", "no_bottom")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..17"},
    "t_direction":    {"type": "str", "default": "rng", "valid": "|".join(DIRECTIONS)},
    "divider_row":    {"type": "int", "default": "rng 4..6", "valid": "4..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "t_over_divider", "valid": "t_over_divider"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for t_direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, lo, hi, md):
    n = rng.randint(lo, hi)
    cells = {(rng.randint(0, md - 1), rng.randint(0, md - 1))}
    guard = 0
    while len(cells) < n and guard < 200:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < md and 0 <= nc < md:
            cells.add((nr, nc))
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def _occupied(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w) or g[rr][cc] != 0:
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    direction = (overrides.get("texture") if overrides.get("texture") in DIRECTIONS else None) or \
                overrides.get("t_direction") or rng.choice(list(DIRECTIONS))
    other_color, bottom_color = ctx.draw_distinct_colors("colors", n=2, exclude={0, 2, 5})

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13); w = ctx.draw_int("grid_w", 11, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 18); w = ctx.draw_int("grid_w", 14, 17)
    else:
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 12, 15)
    dv = ctx.draw_int("divider_row", 4, 6)

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        for c in range(w):
            g[dv][c] = 5
        out_h = h - dv - 1

        bottom = _poly(rng, 2, 4, 3)
        other = _poly(rng, 2, 4, 3)
        bh = max(r for r, _ in bottom) + 1
        bw = max(c for _, c in bottom) + 1
        oh = max(r for r, _ in other) + 1
        ow = max(c for _, c in other) + 1
        if bh + oh > out_h or max(bw, ow) >= w:
            continue
        # bottom shape position (in output/bottom-region coords) with room for the
        # other shape adjacent (below for 'down', above for 'up').
        if direction == "down":
            nbr = rng.randint(0, out_h - bh - oh)
        else:
            nbr = rng.randint(oh, out_h - bh)
        bc = rng.randint(0, w - max(bw, ow))
        for dr, dc in bottom:
            g[dv + 1 + nbr + dr][bc + dc] = bottom_color

        # T (bar + stem) in the top region (rows 0..dv-1)
        if dv - 3 < 0:
            continue
        tr = rng.randint(0, dv - 3)
        tc = rng.randint(0, w - 3)
        if direction == "down":          # bar on top, stem down
            for c in range(tc, tc + 3):
                g[tr][c] = 2
            g[tr + 1][tc + 1] = 2
            g[tr + 2][tc + 1] = 2
        else:                            # stem up, bar on bottom
            g[tr][tc + 1] = 2
            g[tr + 1][tc + 1] = 2
            for c in range(tc, tc + 3):
                g[tr + 2][c] = 2

        # other shape somewhere free in the top region (position irrelevant to
        # the rule, which re-places it relative to the bottom shape)
        placed = False
        for _ in range(80):
            otr = rng.randint(0, dv - oh)
            otc = rng.randint(0, w - ow)
            if not _occupied(g, otr, otc, other):
                for dr, dc in other:
                    g[otr + dr][otc + dc] = other_color
                placed = True
                break
        if placed:
            return g
    # fallback: minimal valid config
    g = full_grid(13, 11, 0)
    for c in range(11):
        g[5][c] = 5
    for c in range(3, 6):
        g[1][c] = 2
    g[2][4] = 2; g[3][4] = 2
    draw_rect(g, 7, 3, 2, 3, bottom_color)
    paint_at(g, 1, 7, [(0, 0), (1, 0), (1, 1)], other_color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 11, 0)
    if name == "no_divider":
        for c in range(3, 6):
            g[1][c] = 2
        g[2][4] = 2; g[3][4] = 2
        draw_rect(g, 7, 3, 2, 3, 3)
        return g
    for c in range(11):
        g[5][c] = 5
    if name == "no_t":
        draw_rect(g, 7, 3, 2, 3, 3)
        paint_at(g, 1, 7, [(0, 0), (1, 0)], 4)
        return g
    if name == "no_bottom":
        for c in range(3, 6):
            g[1][c] = 2
        g[2][4] = 2; g[3][4] = 2
        paint_at(g, 1, 7, [(0, 0), (1, 0)], 4)
        return g
    return g


def _components_excluding_for_self_check(grid, rows, exclude):
    h, w = len(grid), len(grid[0])
    rowset = set(rows)
    seen = set(); out = []
    for r in rows:
        for c in range(w):
            if grid[r][c] in exclude or (r, c) in seen:
                continue
            color = grid[r][c]
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if nr in rowset and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate divider row, T marker, and top/bottom colored shapes."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    divs = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    if len(divs) != 1:
        return [f"expected exactly one full color-5 divider row, got {len(divs)}"]
    dv = divs[0]
    t_cells = [(r, c) for r in range(dv) for c in range(w) if grid[r][c] == 2]
    if len(t_cells) != 5:
        errs.append(f"expected a 5-cell color-2 T, got {len(t_cells)} cells")
    top_shapes = _components_excluding_for_self_check(grid, range(0, dv), {0, 2, 5})
    bottom_shapes = _components_excluding_for_self_check(grid, range(dv + 1, h), {0, 2, 5})
    if len(top_shapes) != 1:
        errs.append(f"expected one other-colored top shape, got {len(top_shapes)}")
    if len(bottom_shapes) != 1:
        errs.append(f"expected one bottom-region shape, got {len(bottom_shapes)}")
    if top_shapes and bottom_shapes and top_shapes[0][0] == bottom_shapes[0][0]:
        errs.append("top and bottom shapes should have distinct colors")
    return errs
