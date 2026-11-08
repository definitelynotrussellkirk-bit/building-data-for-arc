"""Generator for arc_puzzle_bank_21_set16_s:S16_H6.

Rule: the color-1 cells form a 2-cell segment and the color-2 cells a
point; the segment supplies one pair of box edges and the (first) point
the opposite edge. The rule outputs the first object (not color 1 or 2)
whose cells all lie inside that box, cropped to its bbox in color 8.

This generator builds a box from a horizontal color-1 segment + a color-2
point, places the target object strictly inside, scatters decoy objects
fully outside, and optionally transposes for the vertical case.

Combinatorial axes: grid size, the box, the target shape/color, and the
decoys.
Degenerates: no_markers, no_target, multiple_inside.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "8c3ccd709c5f"
VERSION = "2.0.1"  # diversity: random box + target + decoys + orientation + grid (was fixed ~18)
TASK_ID = "8c3ccd709c5f"
SUMMARY = (
    "0-bg grid (size varies). A color-1 2-cell segment and a color-2 point "
    "define a bounding box; one TARGET object sits inside it and DECOY "
    "objects sit outside. Rule: output the object fully inside the box, "
    "cropped to its bbox in color 8. The grid size, box, target "
    "shape/color and decoys all vary freely (was a fixed layout, ~18 "
    "distinct)."
)

INVARIANTS = [
    "color-1 is a 2-cell segment, color-2 a single point, defining a box",
    "exactly one non-{1,2} object lies fully inside the box (the target)",
    "decoy objects each have at least one cell outside the box",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_target", "multiple_inside")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "orientation":    {"type": "str", "default": "varies", "valid": "h|v"},
    "n_decoys":       {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "box_with_target", "valid": "box_with_target"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_target|multiple_inside"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-1 appears exactly twice (the 2-cell segment marker)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    n1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    n2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if n1 == 0 and n2 == 0:
        return []  # no_markers degenerate — allowed
    errs = []
    if n1 > 0 and n1 != 2:
        errs.append(f"color-1 appears {n1} times (expected exactly 2 for the segment)")
    if n2 > 0 and n2 != 1:
        errs.append(f"color-2 appears {n2} times (expected exactly 1 for the point)")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size, hmax, wmax):
    for _ in range(30):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice(_CARD)
            cells.add((r + dr, c + dc))
        nl = _norm(cells)
        if max(r for r, c in nl) + 1 <= hmax and max(c for r, c in nl) + 1 <= wmax:
            return nl
    return [(0, 0)]


def _place_cluster(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def _transpose(g):
    return [list(row) for row in zip(*g)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    orientation = (overrides.get("texture") if overrides.get("texture") in ("h", "v")
                   else None) or overrides.get("orientation") or rng.choice(["h", "v"])

    if difficulty == "easy":
        hr, wr, br, dr_ = (12, 14), (12, 15), (5, 7), (1, 2)
    elif difficulty == "hard":
        hr, wr, br, dr_ = (16, 22), (17, 24), (6, 10), (2, 3)
    else:
        hr, wr, br, dr_ = (13, 17), (14, 19), (5, 9), (1, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        bh = rng.randint(*br); bw = rng.randint(*br)
        if bh + 2 > h or bw + 2 > w:
            continue
        R0 = rng.randint(0, h - bh); C0 = rng.randint(0, w - bw)
        R1 = R0 + bh - 1; C1 = C0 + bw - 1
        if R1 - R0 < 3 or C1 - C0 < 3:
            continue
        # reserve the whole box region so decoys stay outside
        for r in range(R0, R1 + 1):
            for c in range(C0, C1 + 1):
                occ[r][c] = True

        # markers: color-1 segment on the top edge, color-2 point on bottom edge
        g[R0][C0] = 1; g[R0][C1] = 1
        g[R1][rng.randint(C0, C1)] = 2

        # target strictly inside (rows R0+1..R1-1, cols C0+1..C1-1)
        ih = (R1 - 1) - (R0 + 1) + 1; iw = (C1 - 1) - (C0 + 1) + 1
        shape = _poly(rng, rng.randint(3, max(3, (ih * iw) // 2)), ih, iw)
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
        tcolor = rng.choice([3, 4, 5, 6, 7, 8, 9])
        otop = (R0 + 1) + rng.randint(0, ih - sh)
        oleft = (C0 + 1) + rng.randint(0, iw - sw)
        paint_at(g, otop, oleft, shape, tcolor)

        # decoys fully outside the box
        for _ in range(rng.randint(*dr_)):
            ds = _poly(rng, rng.randint(2, 5), 4, 4)
            dh = max(r for r, c in ds) + 1; dw = max(c for r, c in ds) + 1
            dcolor = rng.choice([3, 4, 5, 6, 7, 8, 9])
            for _t in range(30):
                top = rng.randint(0, h - dh); left = rng.randint(0, w - dw)
                cells = [(top + r, left + c) for r, c in ds]
                if _place_cluster(occ, cells, h, w):
                    for (r, c) in cells:
                        g[r][c] = dcolor
                    break

        if orientation == "v":
            g = _transpose(g)
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_markers":
        paint_at(g, 4, 4, [(0, 0), (1, 0), (1, 1)], 3)
        return g
    if name == "no_target":
        g[2][2] = 1; g[2][8] = 1; g[8][5] = 2
        return g
    if name == "multiple_inside":
        g[1][1] = 1; g[1][9] = 1; g[9][5] = 2
        paint_at(g, 3, 3, [(0, 0), (1, 0)], 3)
        paint_at(g, 5, 6, [(0, 0), (0, 1)], 4)
        return g
    return g
