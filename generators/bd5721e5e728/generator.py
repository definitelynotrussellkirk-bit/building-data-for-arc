"""Generator for arc_additional_puzzle_bank_volume9:H63.

Rule: for each blue(1) object, count the blue objects with the same
translation-normalized shape. If it is UNIQUE (frequency 1) recolor it to
8 (cyan); otherwise (duplicated) recolor it to 2 (red).

This generator places several DISTINCT blue shapes, each stamped a chosen
number of times (same orientation), with a forced mix of unique and
duplicated shapes so the output shows both 8 and 2.

Combinatorial axes: grid size, the shapes, and each shape's instance
count (1 vs >=2) and positions.
Degenerates: all_unique, all_duplicated, single_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "bd5721e5e728"
VERSION = "2.0.0"  # diversity: random distinct shapes + unique/duplicated counts + positions + grid (was fixed ~16)
TASK_ID = "bd5721e5e728"
SUMMARY = (
    "0-bg grid (size varies). Several DISTINCT blue(1) shapes, each stamped "
    "once (unique) or several times (duplicated, same orientation), placed "
    "apart, with a mix of both. Rule: recolor every UNIQUE shape to 8 "
    "(cyan) and every DUPLICATED shape to 2 (red). The grid size, the "
    "shapes and each shape's count/positions vary freely (was a fixed "
    "layout, ~16 distinct)."
)

INVARIANTS = [
    "all objects are blue(1), separated, identical orientation per shape",
    "shapes are pairwise distinct (so each shape's frequency is well-defined)",
    "at least one shape is unique (freq 1) and at least one is duplicated (freq >=2)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_unique", "all_duplicated", "single_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..24"},
    "n_shapes":       {"type": "int", "default": "varies", "valid": "2..4"},
    "count":          {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "shapes_apart", "valid": "shapes_apart"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_unique|all_duplicated|single_shape"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


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

    if difficulty == "easy":
        hr, wr, nr, sr = (11, 13), (11, 14), (2, 2), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr, sr = (16, 22), (17, 24), (3, 4), (4, 6)
    else:
        hr, wr, nr, sr = (13, 17), (14, 19), (2, 3), (3, 5)

    for _attempt in range(40):
        n = rng.randint(*nr)
        shapes = []
        for _ in range(n):
            for _t in range(20):
                cand = _poly(rng, rng.randint(*sr))
                if cand not in shapes:
                    shapes.append(cand)
                    break
        if len(shapes) < 2:
            continue
        counts = [rng.randint(1, 3) for _ in shapes]
        # force >=1 unique (freq 1) and >=1 duplicated (freq >=2)
        if all(c >= 2 for c in counts):
            counts[0] = 1
        if all(c == 1 for c in counts):
            counts[0] = 2

        objs = []
        for shape, cnt in zip(shapes, counts):
            for _ in range(cnt):
                objs.append(shape)
        rng.shuffle(objs)

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        ok = True
        for shape in objs:
            sl = sorted(shape)
            sh = max(r for r, c in sl) + 1; sw = max(c for r, c in sl) + 1
            done = False
            for _t in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                cells = [(top + r, left + c) for r, c in sl]
                if _place_cluster(occ, cells, h, w):
                    paint_at(g, top, left, sl, 1)
                    done = True
                    break
            if not done:
                ok = False
                break
        if ok:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    s1 = [(0, 0), (1, 0), (1, 1)]
    s2 = [(0, 0), (0, 1)]
    if name == "all_unique":
        paint_at(g, 1, 1, s1, 1)
        paint_at(g, 1, 6, s2, 1)
        return g
    if name == "all_duplicated":
        for (top, left) in [(1, 1), (1, 6), (6, 1), (6, 6)]:
            paint_at(g, top, left, s1, 1)
        return g
    if name == "single_shape":
        paint_at(g, 1, 1, s2, 1)
        return g
    return g


def _blue_components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for recoloring objects by normalized-shape frequency."""
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    non_blue = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1)]
    if non_blue:
        errs.append("input may contain only background 0 and blue object cells 1")
    comps = _blue_components(grid)
    if len(comps) < 2:
        errs.append("expected at least two separated blue objects")
        return errs

    # Components must be visually separated even diagonally; otherwise object extraction can merge/ambiguate them.
    label = {}
    for idx, comp in enumerate(comps):
        for cell in comp:
            label[cell] = idx
    for (r, c), idx in label.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nb = (r + dr, c + dc)
                if nb in label and label[nb] != idx:
                    errs.append("blue objects must be separated by at least one background cell")
                    return errs

    counts = {}
    for comp in comps:
        shape = _norm(comp)
        counts[shape] = counts.get(shape, 0) + 1
    if not any(freq == 1 for freq in counts.values()):
        errs.append("expected at least one unique normalized shape")
    if not any(freq >= 2 for freq in counts.values()):
        errs.append("expected at least one duplicated normalized shape")
    return errs
