"""Generator for 3b:m15 — outline filled rectangles.

Rule: each solid rect blob → replace with its bbox-outline (only border).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rects, all_2x2, already_outline.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99a1cb372ca4"
VERSION = "2.1.0"  # retry/fallback placement so the promised rectangle count is never silently underfilled.
TASK_ID = "99a1cb372ca4"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with 2-3 "
    "SOLID FILLED RECTANGLES of size rh × "
    "rw (3..4 each, so each rect has a "
    "strict INTERIOR), each painted entirely "
    "in a DISTINCT non-0 color drawn from a "
    "shuffled palette {1..9}. Rectangles are "
    "placed at non-touching positions with "
    "1-cell padding via _free (no two "
    "rectangles share cells or 4-edges). "
    "Rule (REPLACE EACH SOLID FILLED "
    "RECTANGLE WITH ITS BBOX-OUTLINE — "
    "KEEPING THE BORDER, ERASING THE "
    "INTERIOR): for EACH solid rectangular "
    "blob of color C: identify its bbox "
    "(r1, c1, r2, c2). KEEP the BORDER "
    "CELLS (top row r1, bottom row r2, "
    "left col c1, right col c2 of the "
    "bbox) in color C. CLEAR the INTERIOR "
    "(cells (r1+1..r2-1, c1+1..c2-1)) to "
    "bg-0. Other rectangles outside the "
    "current blob's bbox stay unchanged. "
    "Net: solid filled rectangles become "
    "hollow outlines of the same color "
    "and size; interiors become bg-0."
)

INVARIANTS = [
    "background is 0",
    "every blob is a solid filled rect ≥3×3 (so outline differs from fill)",
    "blobs don't 4-touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rects", "all_2x2", "already_outline")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "solid_filled_rectangles",
                       "valid": "solid_filled_rectangles"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n_rects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_rects", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_rects", 2, 3)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for _outer in range(80):
        g = full_grid(h, w, 0)
        placed_count = 0
        for color in palette:
            placed = False
            for _ in range(80):
                rh = rng.randint(3, 4); rw = rng.randint(3, 4)
                r1 = rng.randint(0, h - rh); c1 = rng.randint(0, w - rw)
                r2 = r1 + rh - 1; c2 = c1 + rw - 1
                if _free(g, r1, c1, r2, c2):
                    _paint_rect(g, r1, c1, r2, c2, color)
                    placed = True
                    placed_count += 1
                    break
            if not placed:
                break
        if placed_count == n:
            return g
    return _fallback_rects(h, w, palette)


def _paint_rect(g, r1, c1, r2, c2, color):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g[r][c] = color


def _fallback_rects(h, w, palette):
    g = full_grid(h, w, 0)
    for color in palette:
        placed = False
        for rh, rw in ((3, 3), (3, 4), (4, 3), (4, 4)):
            for r1 in range(0, h - rh + 1):
                for c1 in range(0, w - rw + 1):
                    r2 = r1 + rh - 1; c2 = c1 + rw - 1
                    if _free(g, r1, c1, r2, c2):
                        _paint_rect(g, r1, c1, r2, c2, color)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            raise ValueError("could not realize solid-rectangle layout")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_rects":
        # blank → no rectangles to outline
        return g
    if name == "all_2x2":
        # 2x2 rects → outline equals interior (no interior cells), rule is identity
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 4
                g[5 + r][6 + c] = 6
        return g
    if name == "already_outline":
        # already-hollow outlines → "outline" rule has no work
        for c in range(2, 7): g[2][c] = 3; g[6][c] = 3
        for r in range(2, 7): g[r][2] = 3; g[r][6] = 3
        return g
    return g


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    comps = _components(grid)
    min_rects = 3 if difficulty == "hard" else 2
    if len(comps) < min_rects:
        errors.append(f"expected at least {min_rects} solid rectangles, found {len(comps)}")
    for color, cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        rh = max(rs) - min(rs) + 1
        rw = max(cs) - min(cs) + 1
        if rh < 3 or rw < 3:
            errors.append(f"color {color} rectangle bbox is {rh}x{rw}, expected >=3x3")
        if len(cells) != rh * rw:
            errors.append(f"color {color} component is not a solid filled rectangle")
    return errors
