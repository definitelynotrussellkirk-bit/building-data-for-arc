"""Generator for arc_additional_puzzle_bank_volume12:H81 -- XOR of red+green into gray frame.

Rule: normalize the color-2 (red) and color-3 (green) shapes to their bbox
corners, take their symmetric difference (XOR), and stamp it in color 8 at
the top-left of the interior of the largest color-5 rectangular frame.

This generator draws a red shape, a green shape (overlapping so the XOR is
meaningful), and a color-5 frame whose interior fits the XOR.

Combinatorial axes: grid size, the red/green shapes (and their XOR), the
frame size, and positions.
Degenerates: identical_shapes, no_overlap, no_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at, draw_frame

GENERATOR_ID = "cfac60b0f321"
VERSION = "2.0.0"  # diversity: random red/green shapes + XOR-fitting frame (was fixed ~23)
TASK_ID = "cfac60b0f321"
SUMMARY = (
    "0-bg grid (size varies). A color-2 (red) shape, a color-3 (green) "
    "shape, and a color-5 rectangular FRAME. Rule: stamp the XOR (symmetric "
    "difference) of the normalized red and green shapes in color 8 at the "
    "top-left of the frame's interior. The grid size, red/green shapes "
    "(hence their XOR), frame size and positions vary freely (was a fixed "
    "setup, ~23 distinct)."
)

INVARIANTS = [
    "one red shape, one green shape, one color-5 rectangular frame",
    "the red/green XOR is non-empty and fits inside the frame interior",
    "the output stamps the XOR in color 8 inside the frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identical_shapes", "no_overlap", "no_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "varies"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "varies"},
    "shape_size":     {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "shapes_plus_frame", "valid": "shapes_plus_frame"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|identical_shapes|no_overlap|no_frame"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, g, occ, cells, color, h, w):
    cells = _norm(cells)
    sh = max(r for r, c in cells) + 1; sw = max(c for r, c in cells) + 1
    if sh > h or sw > w:
        return None
    for _t in range(50):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _reserve(occ, top, left, sh, sw, h, w):
            paint_at(g, top, left, cells, color)
            return (top, left)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, ss = (13, 16), (14, 18), (3, 4)
    elif difficulty == "hard":
        hr, wr, ss = (18, 24), (19, 26), (5, 6)
    else:
        hr, wr, ss = (15, 19), (16, 21), (3, 5)

    for _attempt in range(40):
        red = _poly(rng, rng.randint(*ss))
        green = _poly(rng, rng.randint(*ss))
        rs = set(red); gs = set(green)
        sxor = _norm(list(rs ^ gs)) if (rs ^ gs) else None
        if not sxor:
            continue
        xh = max(r for r, c in sxor) + 1; xw = max(c for r, c in sxor) + 1
        fh = xh + 2 + rng.randint(0, 2); fw = xw + 2 + rng.randint(0, 2)

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        if fh > h or fw > w:
            continue
        # frame
        ft = rng.randint(0, h - fh); fl = rng.randint(0, w - fw)
        if not _reserve(occ, ft, fl, fh, fw, h, w):
            continue
        draw_frame(g, ft, fl, ft + fh - 1, fl + fw - 1, 5)

        if _place(rng, g, occ, red, 2, h, w) is None:
            continue
        if _place(rng, g, occ, green, 3, h, w) is None:
            continue
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 15, 0)
    red = [(0, 0), (1, 0), (1, 1)]
    green = [(0, 0), (0, 1), (1, 1)]
    draw_frame(g, 1, 8, 6, 13, 5)
    if name == "no_frame":
        g2 = full_grid(13, 15, 0)
        paint_at(g2, 2, 1, red, 2); paint_at(g2, 8, 1, green, 3)
        return g2
    if name == "identical_shapes":
        paint_at(g, 8, 1, red, 2); paint_at(g, 8, 6, red, 3)
        return g
    if name == "no_overlap":
        paint_at(g, 8, 1, [(0, 0)], 2); paint_at(g, 10, 1, [(0, 0)], 3)
        return g
    paint_at(g, 8, 1, red, 2); paint_at(g, 8, 6, green, 3)
    return g

def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def _norm_cells(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    red = _components_of_color(grid, 2)
    green = _components_of_color(grid, 3)
    frame = _components_of_color(grid, 5)
    if len(red) != 1:
        errs.append(f"expected one red shape, got {len(red)}")
    if len(green) != 1:
        errs.append(f"expected one green shape, got {len(green)}")
    if not frame:
        errs.append("missing color-5 frame")
    if len(red) == 1 and len(green) == 1 and not (_norm_cells(red[0]) ^ _norm_cells(green[0])):
        errs.append("red/green XOR is empty")
    return errs
