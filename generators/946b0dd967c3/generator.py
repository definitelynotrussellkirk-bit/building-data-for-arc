"""Generator for arc_additional_puzzles_21_set13_bundle:M89.

Rule: objects sorted by increasing size are repainted with rank colors
starting at 2 (smallest=2, next=3, ...).

Combinatorial axes (8): grid_h/w, palette_kind, n_objects, palette_size,
position_bias, n_distinct_colors, size_diversity, texture.
Degenerates: tied_sizes, single_object, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import L_TROMINO_SE, SQUARE_2X2

GENERATOR_ID = "946b0dd967c3"
VERSION = "3.0.0"  # distinct=16: 4 FIXED shapes at FIXED positions -> rank-recolored output (input colors are irrelevant, only shapes/positions matter) was nearly constant. Use N (3..6) random polyominoes of DISTINCT sizes at random positions -> output shapes/positions/count vary.
TASK_ID = "946b0dd967c3"
SUMMARY = (
    "0-bg grid with N (3..6) connected objects of STRICTLY DISTINCT sizes "
    "(random polyominoes) at random separated positions. Rule: sort objects by "
    "ascending size and repaint each with a rank color (smallest=2, next=3, "
    "...). The output colors are rank-derived (input colors irrelevant), so "
    "diversity comes from the shapes, positions, and object count."
)

INVARIANTS = [
    "objects are separated by background (4-conn isolated)",
    "object sizes are strictly distinct to make rank order unambiguous",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("tied_sizes", "single_object", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "4", "valid": "4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "size_diversity": {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, r0, c0, sh, sw):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 10, 11)
        N = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 13, 16)
        N = ctx.draw_int("n_objects", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
        N = ctx.draw_int("n_objects", 3, 5)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        sizes = rng.sample(range(1, 9), N)   # strictly distinct sizes
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], N)
        ok = True
        for size, color in zip(sizes, colors):
            shape = _rand_poly(rng, size)
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if _free(g, r0, c0, sh, sw):
                    for dr, dc in shape:
                        g[r0 + dr][c0 + dc] = color
                    placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize rank-recolor layout")


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # multiple objects of equal size → rank order ambiguous
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, 1, w - 3, [(0, 0), (0, 1)], 6)
        paint_at(g, h - 3, 1, [(0, 0), (0, 1)], 7)
        return g
    if name == "single_object":
        # only 1 object — rank trivially 2
        paint_at(g, 3, 3, SQUARE_2X2, 5)
        return g
    if name == "no_objects":
        # empty grid — nothing to rank
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components, components_have_clearance
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    comps = components(grid)
    if len(comps) < 3:
        errors.append(f"expected at least three rankable objects, got {len(comps)}")
    sizes = [len(comp["cells"]) for comp in comps]
    if len(set(sizes)) != len(sizes):
        errors.append(f"object sizes are not strictly distinct: {sizes}")
    if not components_have_clearance(grid, comps, diagonal=True):
        errors.append("objects should have a one-cell moat so 4-connected components are unambiguous")
    return errors
