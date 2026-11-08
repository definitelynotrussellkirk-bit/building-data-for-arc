"""Generator for arc_additional_puzzle_bank_volume13:H90.

Rule: among the blue(1) objects, any whose translation-normalized shape
occurs an ODD number of times is recolored to 2 (red); shapes occurring
an even number of times stay blue.

This generator places several DISTINCT blue shapes, each stamped a chosen
number of times (same orientation), with a forced mix of odd and even
counts so the output shows both red and blue.

Combinatorial axes: grid size, the shapes, and each shape's instance
count (odd or even) and positions.
Degenerates: all_even, all_odd, single_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "529337742c5c"
VERSION = "2.0.1"
TASK_ID = "529337742c5c"
SUMMARY = (
    "0-bg grid (size varies). Several DISTINCT blue(1) shapes, each stamped "
    "a chosen number of times (same orientation), placed apart, with a mix "
    "of odd and even counts. Rule: recolor every instance of an "
    "odd-count shape to red(2); even-count shapes stay blue. The grid size, "
    "the shapes and each shape's count/positions vary freely (was a fixed "
    "layout, ~16 distinct)."
)

INVARIANTS = [
    "all objects are blue(1), separated, in identical orientation per shape",
    "shapes are pairwise distinct (so each shape's count is well-defined)",
    "at least one shape has an odd count and at least one has an even count",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_even", "all_odd", "single_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..24"},
    "n_shapes":       {"type": "int", "default": "varies", "valid": "2..4"},
    "count":          {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "shapes_apart", "valid": "shapes_apart"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_even|all_odd|single_shape"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; all non-bg cells are color-1."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        return errors  # degenerate — allowed
    wrong_colors = [grid[r][c] for r, c in non_bg if grid[r][c] != 1]
    if wrong_colors:
        errors.append(f"expected all non-bg cells to be color 1, found: {set(wrong_colors)}")
    return errors


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
        counts = [rng.randint(1, 4) for _ in shapes]
        # force a mix: >=1 odd and >=1 even
        if all(c % 2 == 1 for c in counts):
            counts[0] = counts[0] + 1 if counts[0] < 4 else counts[0] - 1
        if all(c % 2 == 0 for c in counts):
            counts[0] = counts[0] - 1 if counts[0] > 1 else counts[0] + 1

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
    if name == "all_even":
        for (top, left) in [(1, 1), (1, 6), (6, 1), (6, 6)]:
            paint_at(g, top, left, s1, 1)
        return g
    if name == "all_odd":
        for (top, left) in [(1, 1), (1, 6), (6, 1)]:
            paint_at(g, top, left, s1, 1)
        return g
    if name == "single_shape":
        paint_at(g, 1, 1, s2, 1)
        return g
    return g
