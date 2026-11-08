"""Generator for arc_additional_puzzle_bank_volume9:H60.

Rule: a top-left control rotates the blue template; the rotated mask is
intersected with the red mask, output is the cropped cyan intersection.

Combinatorial axes (8): grid_h/w, palette_kind, control_color,
palette_size, position_bias, n_distinct_colors, mask_overlap, texture.
Degenerates: no_control, no_blue, no_red.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "67851a16ff1a"
VERSION = "2.0.1"  # distinct=4: rule intersects NORMALIZED rotated-blue with NORMALIZED red, so output depends ONLY on (blue shape, rotation, red shape) -- generator used FIXED blue+red, so only the 4 control rotations varied. Now random blue + red polyominoes with a guaranteed normalized-overlap -> output shape varies widely.
TASK_ID = "67851a16ff1a"
SUMMARY = "A top-left control rotates the blue template before intersecting it with a normalized red shape."

INVARIANTS = [
    "top-left control is 3, 4, 5, or 6",
    "one blue template and one red template are present",
    "the rotated blue mask overlaps the red mask",
    "the output is the cropped cyan intersection",
]

PALETTE_KINDS = ("default", "control_3", "control_4", "control_5_6")
DEGENERATE_TEXTURES = ("no_control", "no_blue", "no_red")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "control_color":  {"type": "int", "default": "rng",
                       "valid": "3|4|5|6"},
    "mask_overlap":   {"type": "str", "default": "partial",
                       "valid": "partial"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rot90(cells):
    h = max(r for r, _ in cells) + 1
    return _norm([(c, h - 1 - r) for r, c in cells])


def _rotate(cells, k):
    cur = _norm(cells)
    for _ in range(k % 4):
        cur = _rot90(cur)
    return cur


def _rand_poly(rng, maxh, maxw, target):
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(300):
        if len(cells) >= target:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen and 0 <= nr < maxh and 0 <= nc < maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    return _norm(cells)


def _free(g, cells, r0, c0):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < h and 0 <= c < w):
            return False
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if _free(g, cells, r0, c0):
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 control cell (3/4/5/6 at top-left region); ≥1 blue (1); ≥1 red (2)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_ctrl = grid[0][0] in (3, 4, 5, 6)
    has_blue = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    has_red = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_ctrl:
        errs.append(f"no control cell (3/4/5/6) at (0,0); found {grid[0][0]}")
    if not has_blue:
        errs.append("no color-1 (blue template) cells found")
    if not has_red:
        errs.append("no color-2 (red mask) cells found")
    return errs


_CTRL_ROT = {3: 0, 4: 1, 5: 2, 6: 3}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 22)
    else:
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 12, 19)
    rng = ctx.draw_rng("layout")
    ctrl = rng.choice([3, 4, 5, 6])
    rot = _CTRL_ROT[ctrl]
    # Random blue (template) + red (mask) polyominoes whose NORMALIZED rotated
    # blue overlaps the NORMALIZED red in >=2 cells (so output is non-trivial).
    blue = red = inter = None
    for _ in range(400):
        b = _rand_poly(rng, rng.randint(3, 5), rng.randint(3, 5), rng.randint(5, 10))
        r = _rand_poly(rng, rng.randint(3, 5), rng.randint(3, 5), rng.randint(5, 10))
        a = _rotate(b, rot)
        nr = _norm(r)
        it = [p for p in a if p in set(nr)]
        if len(it) >= 3:
            blue, red, inter = b, nr, it
            break
    if blue is None:  # fallback: guaranteed 2-cell overlap
        blue = [(0, 0), (0, 1), (1, 0)]
        red = [(0, 0), (0, 1), (1, 1)]
    g = full_grid(h, w, 0)
    g[0][0] = ctrl
    if not _place(g, rng, blue, 1) or not _place(g, rng, red, 2):
        # extremely unlikely; retry on a roomier blank grid
        g = full_grid(h, w, 0)
        g[0][0] = ctrl
        _place(g, rng, blue, 1)
        _place(g, rng, red, 2)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    blue = [(0, 0), (1, 0), (2, 0), (2, 1)]
    red = [(0, 0), (0, 1), (1, 0), (1, 1)]
    if name == "no_control":
        # blue + red but no control — rotation amount undefined
        paint_at(g, 1, 2, blue, 1)
        paint_at(g, h - 5, w - 5, red, 2)
        return g
    if name == "no_blue":
        # control + red but no blue template to rotate
        g[0][0] = 4
        paint_at(g, h - 5, w - 5, red, 2)
        return g
    if name == "no_red":
        # control + blue but no red mask to intersect with
        g[0][0] = 4
        paint_at(g, 1, 2, blue, 1)
        return g
    return g
