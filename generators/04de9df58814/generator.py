"""Generator for arc_additional_puzzle_bank_volume18:E123.

Rule: green(3) connected components touching the grid border get
recolored; interior greens stay.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_border, all_interior, no_green.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04de9df58814"
VERSION = "2.1.1"
TASK_ID = "04de9df58814"
SUMMARY = (
    "0-bg grid (h, w~12-18) "
    "with ≥2 GREEN(3) "
    "RECTANGULAR COMPONENTS: "
    "(a) ≥1 BORDER-TOUCHING "
    "GREEN — a solid 3-color "
    "rectangle (h~2-4, w~"
    "2-4) anchored to one of "
    "the 4 grid edges (top/"
    "bottom/left/right); "
    "(b) ≥1 INTERIOR GREEN — "
    "a solid 3-color "
    "rectangle placed in the "
    "interior (margin ≥1 "
    "from every edge) at a "
    "non-overlapping "
    "position. Rule (RECOLOR "
    "BORDER-TOUCHING GREENS, "
    "KEEP INTERIOR GREENS): "
    "Find all 4-CONNECTED "
    "COMPONENTS of color 3. "
    "For EACH component: if "
    "ANY cell is on the "
    "OUTER BORDER (row 0, "
    "row h-1, col 0, col w-1)"
    ", RECOLOR every cell "
    "of that component to a "
    "different color (puzzle-"
    "specific). Else (fully "
    "interior), keep at 3. "
    "Net: border-anchored "
    "greens get a new color; "
    "interior greens stay "
    "green."
)

# Rivals: 'recolor every green' refuted by interior greens that stay.
# 'recolor every border object' refuted by non-green border decoys
# that stay. 'only rectangles count' refuted by blob greens. 3 demos
# incl. >=1 decoy or blob board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 green component on the border AND >=1 strictly interior",
    "decoy boards: a non-green object (border or not) stays unchanged",
]

DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_green")
HELPFUL_TEXTURES = ("plain", "decoy", "blob")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":  {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|decoy|blob|all_border|all_interior|no_green",
                "doc": "decoy adds a non-green object the rule ignores; "
                       "blob uses irregular green shapes."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 green(3) component on the border AND >=1 strictly interior."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    seen: set = set()
    has_border = False
    has_interior = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 3 and (r, c) not in seen:
                stack = [(r, c)]
                comp: list = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 3
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                on_border = any(rr in (0, h - 1) or cc in (0, w - 1)
                                for rr, cc in comp)
                if on_border:
                    has_border = True
                else:
                    has_interior = True
    if not has_border:
        errs.append("no border-touching green(3) component")
    if not has_interior:
        errs.append("no strictly interior green(3) component")
    return errs


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _paint_clear(g, cells, r0, c0, color):
    h, w = len(g), len(g[0])
    spots = [(r0 + r, c0 + c) for r, c in cells]
    if any(not (0 <= r < h and 0 <= c < w) or g[r][c] != 0 for r, c in spots):
        return False
    if any(0 <= r + ar < h and 0 <= c + ac < w and g[r + ar][c + ac] != 0
           for r, c in spots for ar in (-1, 0, 1) for ac in (-1, 0, 1)):
        return False
    for r, c in spots:
        g[r][c] = color
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "decoy", "blob"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 18)
        w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 12, 18)
    rng = ctx.draw_rng("placement")

    def shape():
        if texture == "blob":
            return _grow(rng, rng.randint(3, 6))
        rh = rng.randint(2, max(2, h // 4))
        rw = rng.randint(2, max(2, w // 4))
        return [(r, c) for r in range(rh) for c in range(rw)]

    for _outer in range(60):
        g = full_grid(h, w, 0)
        # border greens
        placed_border = 0
        for _ in range(20):
            if placed_border >= rng.randint(1, 2):
                break
            cells = shape()
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            side = rng.choice(["top", "bottom", "left", "right"])
            if side == "top":
                rr, rc = 0, rng.randint(0, w - sw)
            elif side == "bottom":
                rr, rc = h - sh, rng.randint(0, w - sw)
            elif side == "left":
                rr, rc = rng.randint(0, h - sh), 0
            else:
                rr, rc = rng.randint(0, h - sh), w - sw
            # the shape must actually have a cell ON the border line
            spots = [(rr + r, rc + c) for r, c in cells]
            if not any(r in (0, h - 1) or c in (0, w - 1) for r, c in spots):
                continue
            if _paint_clear(g, cells, rr, rc, 3):
                placed_border += 1
        # strictly interior greens
        placed_interior = 0
        for _ in range(30):
            if placed_interior >= rng.randint(1, 2):
                break
            cells = shape()
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            if sh > h - 2 or sw > w - 2:
                continue
            rr = rng.randint(1, h - sh - 1)
            rc = rng.randint(1, w - sw - 1)
            if _paint_clear(g, cells, rr, rc, 3):
                placed_interior += 1
        if placed_border < 1 or placed_interior < 1:
            continue
        if texture == "decoy":
            # non-green object the rule ignores entirely
            color = rng.choice([1, 2, 5, 6, 7, 8, 9])
            cells = _grow(rng, rng.randint(2, 4))
            for _ in range(40):
                sh = max(r for r, _ in cells) + 1
                sw = max(c for _, c in cells) + 1
                rr = rng.randint(0, h - sh)
                rc = rng.randint(0, w - sw)
                if _paint_clear(g, cells, rr, rc, color):
                    break
        return g
    raise ValueError("could not realize border-green board")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    all_border   — every green touches the border: all recolor.
    all_interior — nothing touches: identity output.
    no_green     — other colors only: identity output.
    """
    rng = ctx.draw_rng("degenerate_placement")
    h = ctx.draw_int("grid_h", 12, 15)
    w = ctx.draw_int("grid_w", 12, 15)
    g = full_grid(h, w, 0)
    if name == "no_green":
        for color in rng.sample([1, 2, 4, 5, 6, 7, 8], 2):
            r0, c0 = rng.randint(1, h - 4), rng.randint(1, w - 4)
            for dr in range(2):
                for dc in range(2):
                    g[r0 + dr][c0 + dc] = color
        return g
    if name == "all_border":
        for side in rng.sample(["top", "bottom", "left", "right"], 2):
            if side == "top":
                r0, c0 = 0, rng.randint(0, w - 3)
            elif side == "bottom":
                r0, c0 = h - 2, rng.randint(0, w - 3)
            elif side == "left":
                r0, c0 = rng.randint(0, h - 3), 0
            else:
                r0, c0 = rng.randint(0, h - 3), w - 2
            for dr in range(2):
                for dc in range(2):
                    if r0 + dr < h and c0 + dc < w:
                        g[r0 + dr][c0 + dc] = 3
        return g
    # all_interior
    for _ in range(2):
        r0, c0 = rng.randint(1, h - 4), rng.randint(1, w - 4)
        for dr in range(2):
            for dc in range(2):
                g[r0 + dr][c0 + dc] = 3
    return g
