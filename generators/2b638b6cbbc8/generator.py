"""Generator for arc_puzzle_bank_21_set5_e:medium_e04 — extract odd-one-out shape.

Rule: N+1 blobs total, N of them share normalized shape, exactly one
has a unique shape. Output: that unique blob, cropped.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, all_unique, all_same.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import (
    L_TROMINO_NE, L_TROMINO_SE, T_TETROMINO, SQUARE_2X2,
)

GENERATOR_ID = "2b638b6cbbc8"
VERSION = "2.0.0"  # distinct=9/out=1: the UNIQUE shape was ALWAYS T_TETROMINO, so the output crop never varied. Now random unique + common polyominoes (varied shape/size incl. non-square) so the odd-one-out crop varies; 2-4 duplicate copies.
TASK_ID = "2b638b6cbbc8"
SUMMARY = "K (2-4) same-shape blobs + 1 unique-shape blob (random polyominoes), distinct colors; rule crops the unique one."

INVARIANTS = [
    "background is 0",
    "K>=2 blobs share an identical bbox-crop shape + exactly 1 unique shape",
    "all blobs distinct colors, separated by >=1 gap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "all_unique", "all_same")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_same_one_unique",
                       "valid": "two_same_one_unique"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blobs|all_unique|all_same"},
}


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) + 1, max(cs) + 1


def _free(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 8, 10); k = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 16); k = rng_k(ctx, 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 11); w = ctx.draw_int("grid_w", 9, 13); k = rng_k(ctx, 2, 3)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        # common shape (K copies, same orientation -> identical bbox crops) + ONE
        # unique shape whose bbox-crop binary differs -> it's the rule's odd-one-out.
        common = _rand_poly(rng, rng.randint(3, 5))
        unique = _rand_poly(rng, rng.randint(2, 6))
        if _binary(unique) == _binary(common):
            continue
        palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k + 1)
        placements = [(common, palette[i]) for i in range(k)]
        placements.append((unique, palette[k]))
        rng.shuffle(placements)
        ok = True
        for shape, color in placements:
            sh, sw = _bbox(shape)
            if sh > h or sw > w:
                ok = False; break
            placed = False
            for _ in range(60):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if _free(g, r0, c0, shape):
                    paint_at(g, r0, c0, shape, color)
                    placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place odd-one-out layout")


def rng_k(ctx, lo, hi):
    return ctx.draw_int("n_common", lo, hi)


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _binary(cells):
    return tuple(sorted(cells))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _norm_shape(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components(grid)
    if len(comps) < 3:
        errors.append(f"expected at least 3 foreground blobs, found {len(comps)}")
        return errors
    colors = []
    shapes = []
    for cells in comps:
        comp_colors = {grid[r][c] for r, c in cells}
        if len(comp_colors) != 1:
            errors.append("each blob must be single-color")
        colors.append(next(iter(comp_colors)))
        shapes.append(_norm_shape(cells))
    if len(colors) != len(set(colors)):
        errors.append("blob colors must be distinct")
    counts = {sh: shapes.count(sh) for sh in set(shapes)}
    singleton_shapes = [sh for sh, n in counts.items() if n == 1]
    repeated_shapes = [sh for sh, n in counts.items() if n >= 2]
    if len(singleton_shapes) != 1 or len(repeated_shapes) != 1:
        errors.append("expected exactly one unique shape and one repeated majority shape")
    # The generator promises a one-cell moat around each blob. Check 8-neighbor
    # separation, not just 4-connected component separation.
    owner = {}
    for i, cells in enumerate(comps):
        for cell in cells:
            owner[cell] = i
    for (r, c), i in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                j = owner.get((r + dr, c + dc))
                if j is not None and j != i:
                    errors.append("blobs must be separated by at least a one-cell gap")
                    return errors
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no candidates to compare.
        return g
    if name == "all_unique":
        # All three blobs have distinct shapes — rule's "majority
        # share a shape" precondition fails; odd-one-out undefined.
        paint_at(g, 1, 1, L_TROMINO_NE, 4)
        paint_at(g, 1, 5, T_TETROMINO, 6)
        paint_at(g, 4, 1, SQUARE_2X2, 7)
        return g
    if name == "all_same":
        # All three blobs share the same shape — rule's "exactly
        # one unique" finds none.
        paint_at(g, 1, 1, L_TROMINO_NE, 4)
        paint_at(g, 1, 5, L_TROMINO_NE, 6)
        paint_at(g, 4, 1, L_TROMINO_NE, 7)
        return g
    return g
