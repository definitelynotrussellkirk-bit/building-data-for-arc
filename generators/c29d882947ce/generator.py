"""Generator for 15b:hard_100 — build rotation equivalence matrix.

Rule: connected components sorted by (row, col). Output is NxN where
[i][j] = 1 if i==j, 2 if shape i is rotation-equivalent to shape j,
else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects (no shapes → matrix is empty); single_object
(only 1 → matrix is 1x1 with value 1, no off-diagonal contrast);
all_rotation_equivalent (all 3 shapes are rotations of each other →
matrix all 1/2, off-diagonal contrast lost).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c29d882947ce"
VERSION = "2.2.0"  # 2.1.0->2.2.0: exhaustive placement so object count never silently drops
TASK_ID = "c29d882947ce"
SUMMARY = (
    "0-bg grid with 3-6 ISOLATED 4-connected components in distinct colors. "
    "Rule: extract all 4-connected components and sort by top-left (r1, c1). "
    "Output is an N×N MATRIX: out[i][j] = 1 if i == j; = 2 if shape[i] is "
    "rotation-equivalent to shape[j] under a 90° rotation; else 0. Net: encodes "
    "the pairwise rotation-equivalence relation among the components."
)

INVARIANTS = [
    "background is 0",
    "easy has 3 isolated components; default 3-5; hard 4-6",
    "components use distinct colors and do not 8-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "all_rotation_equivalent")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..10", "valid": "7..18"},
    "grid_w":            {"type": "int", "default": "rng 13..15", "valid": "12..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "three_components_one_rotation_pair",
                          "valid": "three_components_one_rotation_pair"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    positions = [(r0, c0) for r0 in range(h - sh + 1) for c0 in range(w - sw + 1)]
    rng.shuffle(positions)
    for r0, c0 in positions:
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _rotate_cw(shape):
    rs = [r for r, _ in shape]; cs = [c for _, c in shape]
    h = max(rs) + 1
    return [(c, h - 1 - r) for r, c in shape]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output is an n x n rotation-equivalence matrix (diag=1, rot-equiv pair=2, else 0);
    # n = number of objects. Was FIXED 3 objects from a 4-shape bank -> output always 3x3
    # with few distinct matrices. Now vary n 3-6 + a pool of random rotation-classes (each
    # object a random rotation of a pool shape, so equiv pairs vary) -> matrices + dims vary.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 12, 15); n_obj = ctx.draw_int("n_obj", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 14, 20); n_obj = ctx.draw_int("n_obj", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 13, 18); n_obj = ctx.draw_int("n_obj", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], min(8, n_obj))

    def _poly(k):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
        return [(r - rmin, c - cmin) for r, c in cells]

    # pool shapes of DISTINCT sizes -> guaranteed distinct rotation-classes (rotation
    # preserves cell count), so objects span more classes -> richer equivalence matrices.
    n_classes = min(rng.randint(3, 4), n_obj)
    pool = [_poly(k) for k in rng.sample([3, 4, 5, 6, 7], n_classes)]
    for color in palette:
        sh = rng.choice(pool)
        for _ in range(rng.randint(0, 3)):
            sh = _rotate_cw(sh)
        rmin = min(r for r, _ in sh); cmin = min(c for _, c in sh)
        sh = [(r - rmin, c - cmin) for r, c in sh]
        if not _place(g, rng, sh, color):
            # Fall back to a compact triomino instead of silently dropping an
            # object and changing the matrix dimension.
            if not _place(g, rng, [(0, 0), (0, 1), (1, 0)], color):
                raise RuntimeError("could not place requested rotation-matrix object")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    if name == "single_object":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][3 + dc] = 4
        return g
    if name == "all_rotation_equivalent":
        # Three rotations of the same L-tromino.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 1
        for dr, dc in [(0, 1), (1, 0), (1, 1)]:
            g[1 + dr][6 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 1)]:
            g[5 + dr][3 + dc] = 3
        return g
    return g


def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    comps = _components_by_color(grid)
    n = len(comps)
    if difficulty == "easy":
        allowed = (3,)
    elif difficulty == "hard":
        allowed = (4, 5, 6)
    else:
        allowed = (3, 4, 5)
    if n not in allowed:
        errors.append(f"expected {allowed} isolated components, found {n}")
    colors = [color for color, _cells in comps]
    if len(colors) != len(set(colors)):
        errors.append("components must use distinct colors")
    cell_to_comp = {}
    for i, (_color, cells) in enumerate(comps):
        if not cells:
            errors.append("component must be nonempty")
            continue
        for p in cells:
            cell_to_comp[p] = i
    for i, (_color, cells) in enumerate(comps):
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    j = cell_to_comp.get((r + dr, c + dc))
                    if j is not None and j != i:
                        errors.append("components must not 8-touch")
                        return errors
    return errors
