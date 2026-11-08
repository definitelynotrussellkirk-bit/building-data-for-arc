"""Generator for arc_additional_puzzle_bank_volume16:H112.

Rule: normalize the cells of colors 1, 2 and 3 each to its own bbox
origin; output (cropped, in color 8) the cells present in ALL THREE
normalized shapes. (Empty intersection -> a 1x1 zero grid.)

This generator builds the three shapes around a shared CORE (each shape
= core + its own disjoint extra cells, all anchored at the origin) so
the 3-way intersection is exactly the core -- a clean, non-trivial
output.

Combinatorial axes: grid size, the shared core shape, and each color's
extra cells.
Degenerates: no_shapes, single_shape, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "3f4b934203b8"
VERSION = "3.0.1"  # distinct=27: output = the CORE (intersection of the 3 colour shapes) but core was only 2-4 cells -> few distinct shapes. Enlarged core to 3-8 cells (varied) -> many more distinct intersection outputs.
TASK_ID = "3f4b934203b8"
SUMMARY = (
    "0-bg grid (size varies). Three connected shapes in colors 1, 2 and 3, "
    "placed apart. Each shares a common CORE (anchored at the bbox origin) "
    "plus its own disjoint extra cells. Rule: normalize each color's shape "
    "and output the cells common to all three (the core) cropped in color 8. "
    "The grid size, the core shape and each color's extras all vary freely "
    "(was a fixed layout, ~13 distinct)."
)

INVARIANTS = [
    "each of colors 1,2,3 forms one connected shape, all separated",
    "the three normalized shapes share a common core (non-empty intersection)",
    "each shape has >=1 cell the others lack (extras are disjoint across colors)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "single_shape", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "core_size":      {"type": "int", "default": "varies", "valid": "2..4"},
    "extras":         {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "three_shapes_apart",
                       "valid": "three_shapes_apart"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shapes|single_shape|full_grid"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: colors 1, 2, and 3 each have >=1 cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    for color in (1, 2, 3):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if not cells:
            errs.append(f"color-{color} shape missing")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return set(_norm(cells))


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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # core = the INTERSECTION of the 3 shapes = the OUTPUT, so a bigger/varied
    # core gives many more distinct output shapes (was 2-4 cells -> distinct=27).
    if difficulty == "easy":
        hr, wr, kr, er = (10, 13), (11, 14), (3, 4), (1, 2)
    elif difficulty == "hard":
        hr, wr, kr, er = (16, 22), (17, 24), (5, 8), (2, 3)
    else:
        hr, wr, kr, er = (13, 18), (14, 20), (3, 6), (1, 3)

    for _attempt in range(40):
        core = _poly(rng, rng.randint(*kr))
        used = set(core)            # cells claimed by core or any shape's extras
        shapes = []
        ok = True
        for _ci in range(3):
            shape = set(core)
            for _ in range(rng.randint(*er)):
                cands = []
                for (r, c) in shape:
                    for dr, dc in _CARD:
                        nr, nc = r + dr, c + dc
                        if nr >= 0 and nc >= 0 and (nr, nc) not in shape and (nr, nc) not in used:
                            cands.append((nr, nc))
                if not cands:
                    break
                cell = rng.choice(cands)
                shape.add(cell); used.add(cell)
            if shape == core:        # got no unique extra -> shapes indistinguishable
                ok = False
                break
            shapes.append(shape)
        if not ok:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = True
        for color, shape in zip((1, 2, 3), shapes):
            sl = _norm(shape)
            sh = max(r for r, c in sl) + 1; sw = max(c for r, c in sl) + 1
            done = False
            for _t in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                cells = [(top + r, left + c) for r, c in sl]
                if _place_cluster(occ, cells, h, w):
                    paint_at(g, top, left, sl, color)
                    done = True
                    break
            if not done:
                placed = False
                break
        if placed:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    core = [(0, 0), (1, 0), (1, 1)]
    if name == "no_shapes":
        return g
    if name == "single_shape":
        paint_at(g, 1, 1, core, 1)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 1
        return g
    return g
