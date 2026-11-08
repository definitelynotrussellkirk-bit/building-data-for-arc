"""Generator for arc_additional_puzzle_bank_volume12:M78.

Rule: vector dr/dc = (1-marker - 2-marker); for each color-3 cell, paint
color 8 at that cell translated by the vector (a translated copy of the
green blob; the original stays).

Combinatorial axes: grid size, the marker vector, the color-3 blob
(shape/position) and the decoration.
Degenerates: no_anchors, no_shape, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e9218327512"
VERSION = "2.1.0"  # ensure translated copy lands on empty cells, not on the source blob
TASK_ID = "7e9218327512"
SUMMARY = (
    "0-bg grid (size varies). A color-2 and a color-1 MARKER define a "
    "VECTOR (1-marker minus 2-marker). A color-3 (green) BLOB (random "
    "shape) sits in the grid, plus a color-7 DECORATION block the rule "
    "ignores. Rule: for each green cell, paint COLOR 8 (cyan) at that "
    "cell translated by the vector; the green blob, markers and "
    "decoration stay. The translated copy always lands in-bounds on "
    "empty cells. The grid size, the vector, the blob shape/position and "
    "the decoration all vary freely (was a fixed marker+blob layout)."
)

INVARIANTS = [
    "exactly one color-2 marker and one color-1 marker",
    "one color-3 blob; its translated copy lands in-bounds on empty cells",
    "a non-{1,2,3} decoration sits outside",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_anchors", "no_shape", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_anchors|no_shape|full_grid"},
}


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in norm) < maxd and max(c for r, c in norm) < maxd:
            return norm
    return [(0, 0), (0, 1), (1, 0)]


def _free(occ, cells, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
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
        hr, wr, szr = (9, 11), (11, 13), (3, 4)
    elif difficulty == "hard":
        hr, wr, szr = (12, 16), (12, 16), (4, 6)
    else:
        hr, wr, szr = (10, 13), (11, 14), (3, 5)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        dr = rng.randint(-5, 5); dc = rng.randint(-5, 5)
        if dr == 0 and dc == 0:
            continue
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        placed_m = False
        for _t in range(40):
            mr = rng.randint(0, h - 1); mc = rng.randint(0, w - 1)
            ar, ac = mr + dr, mc + dc
            if 0 <= ar < h and 0 <= ac < w and not occ[mr][mc] and not occ[ar][ac] and (mr, mc) != (ar, ac):
                g[mr][mc] = 2; g[ar][ac] = 1
                occ[mr][mc] = True; occ[ar][ac] = True
                placed_m = True
                break
        if not placed_m:
            continue

        blob = _random_poly(rng, rng.randint(*szr), 4)
        bh = max(r for r, c in blob) + 1; bw = max(c for r, c in blob) + 1
        placed_b = False
        for _t in range(60):
            top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
            cells = [(top + r, left + c) for r, c in blob]
            tcells = [(r + dr, c + dc) for r, c in cells]
            if not all(0 <= r < h and 0 <= c < w for r, c in tcells):
                continue
            # The rule paints color 8 at translated green cells.  If the
            # translated copy overlaps the source blob, those green cells are
            # overwritten and the advertised "original stays + copy on empty
            # cells" invariant is false.
            if set(tcells) & set(cells):
                continue
            if not _free(occ, cells, h, w) or any(occ[r][c] for r, c in tcells):
                continue
            for r, c in cells:
                g[r][c] = 3; occ[r][c] = True
            for r, c in tcells:
                occ[r][c] = True
            placed_b = True
            break
        if not placed_b:
            continue

        # color-7 decoration (rule ignores it).
        for _t in range(30):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if not occ[r][c]:
                g[r][c] = 7
                break
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 13, 0)
    if name == "no_anchors":
        g[1][1] = 3; g[2][1] = 3; g[3][1] = 3
        return g
    if name == "no_shape":
        g[0][0] = 2; g[4][6] = 1
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(13):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    ones = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    greens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    decor = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    if len(ones) != 1 or len(twos) != 1:
        errors.append("expected exactly one color-1 and one color-2 marker")
        return errors
    if len(greens) < 3:
        errors.append("green source blob is too small or missing")
    if not decor:
        errors.append("missing ignored color-7 decoration")
    dr = ones[0][0] - twos[0][0]
    dc = ones[0][1] - twos[0][1]
    if dr == 0 and dc == 0:
        errors.append("zero marker vector")
    green_set = set(greens)
    translated = {(r + dr, c + dc) for r, c in greens}
    if translated & green_set:
        errors.append("translated copy overlaps the source green blob")
    for r, c in translated:
        if not (0 <= r < h and 0 <= c < w):
            errors.append("translated copy goes out of bounds")
            break
        if grid[r][c] != 0:
            errors.append("translated copy does not land on empty cells")
            break
    return errors
