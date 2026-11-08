"""Generator for arc_puzzle_bank_21_set13_bundle:hard_m01.

Rule: find color-2 target shape (cropped to bbox). Among other
components (non-{0,2}), find the FIRST whose cropped object-grid is
dihedrally equivalent (any of 8 rotations/reflections) to the target.
Output that candidate's cropped object-grid in its color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_distractors,
shape_size, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_target, no_match, tied_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a079fac95996"
VERSION = "2.0.0"
TASK_ID = "a079fac95996"

SUMMARY = "Color-2 target shape + several distractor shapes; rule outputs the FIRST distractor whose shape is dihedrally equivalent to the target, in the distractor's own color."

# Rivals: 'output the target' refuted by ≥2 demos where output color
# is the matching distractor's, not 2. 'output ALL components'
# refuted by any demo (output is one cropped shape). 'output the
# distractor with matching color' refuted by ≥1 demo where color is
# orthogonal. 'identity match only (no dihedral)' refuted by ≥2
# demos where match is a rotation/reflection of target.
# 4 demos with varied targets + distractor counts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-2 target component",
    "≥1 distractor whose shape (under 8 dihedrals) matches the target",
    "all components are isolated by ≥1 bg cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_target", "no_match", "tied_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distractors":  {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "shape_size":     {"type": "int", "default": "rng 3..6", "valid": "3..9"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "3..7"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "3..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_BANK = [
    [(0, 0), (0, 1), (1, 0)],                       # L-tro
    [(0, 0), (1, 0), (1, 1), (2, 1)],               # S-tet
    [(0, 0), (0, 1), (0, 2), (1, 1)],               # T-tet
    [(0, 0), (0, 1), (1, 0), (1, 1)],               # square
    [(0, 0), (0, 1), (0, 2), (1, 0)],               # J-tet
    [(0, 0), (1, 0), (1, 1), (1, 2)],               # L-tet
    [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],       # zigzag-pent
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],       # L-pent
    [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],       # L-pent rotated
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],       # P-pent
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],       # plus
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],       # U-pent
    [(0, 0), (1, 0), (1, 1), (2, 0)],               # T-rot
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],       # U
]


def _normalize(cells):
    if not cells:
        return []
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells):
    if not cells:
        return ()
    rs = [r for r, _ in cells]
    h = max(rs) + 1
    return _normalize([(c, h - 1 - r) for r, c in cells])


def _flip_lr(cells):
    if not cells:
        return ()
    cs = [c for _, c in cells]
    w = max(cs) + 1
    return _normalize([(r, w - 1 - c) for r, c in cells])


def _dihedral_variants(cells):
    cur = _normalize(cells)
    variants = {cur}
    for _ in range(3):
        cur = _rotate_cw(cur)
        variants.add(cur)
    cur = _flip_lr(_normalize(cells))
    variants.add(cur)
    for _ in range(3):
        cur = _rotate_cw(cur)
        variants.add(cur)
    return variants


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _try_place(g, cells, color, rng):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    h, w = len(g), len(g[0])
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in cells:
            g[r0 + r - min(rs)][c0 + c - min(cs)] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        n_distractors = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 22)
        n_distractors = rng.randint(3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n_distractors = rng.randint(2, 4)

    # Pick target shape from bank
    target = list(_normalize(rng.choice(_BANK)))
    target_variants = _dihedral_variants(target)

    # Pick the MATCHING distractor as a non-identity variant of target
    # (rotation or reflection that differs from target itself).
    other_variants = [v for v in target_variants if v != _normalize(target)]
    if other_variants:
        match_cells = list(rng.choice(other_variants))
    else:
        # Symmetric shape — match = same shape
        match_cells = list(target)

    # Distractors: shapes whose dihedral variants do NOT include target.
    non_match_shapes = []
    for shape in _BANK:
        norm = _normalize(shape)
        variants = _dihedral_variants(norm)
        if not (variants & target_variants):
            non_match_shapes.append(list(shape))

    g = full_grid(h, w, 0)
    color_pool = [1, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(color_pool)
    # Place target FIRST (color 2)
    if not _try_place(g, target, 2, rng):
        return g
    # Place match (in some color)
    match_color = color_pool[0]
    if not _try_place(g, match_cells, match_color, rng):
        return g
    # Place additional distractors
    for i in range(n_distractors):
        if not non_match_shapes or i + 1 >= len(color_pool):
            break
        d_shape = rng.choice(non_match_shapes)
        d_color = color_pool[i + 1]
        _try_place(g, d_shape, d_color, rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_target":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]: g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]: g[6 + dr][8 + dc] = 6
        return g
    if name == "no_match":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]: g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (0, 2)]: g[5 + dr][6 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1), (1, 2)]: g[7 + dr][2 + dc] = 6
        return g
    if name == "tied_match":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]: g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 1)]: g[5 + dr][6 + dc] = 4
        for dr, dc in [(0, 1), (1, 0), (1, 1)]: g[7 + dr][2 + dc] = 6
        return g
    return g

def _selfcheck_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]; seen.add((sr, sc)); cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid must be non-empty and rectangular"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid rows must have equal width"]
    comps = _selfcheck_components(grid)
    targets = [cells for color, cells in comps if color == 2]
    if len(targets) != 1:
        errs.append(f"expected exactly one color-2 target component, found {len(targets)}")
        return errs
    target_variants = _dihedral_variants(_normalize(targets[0]))
    matches = []
    for color, cells in comps:
        if color in (0, 2):
            continue
        if _dihedral_variants(_normalize(cells)) & target_variants:
            matches.append(color)
    if len(matches) < 1:
        errs.append("expected at least one non-color-2 distractor dihedrally matching the target")
    # One-cell moat between distinct objects keeps the first-match scan unambiguous.
    owner = {}
    for i, (_color, cells) in enumerate(comps):
        for cell in cells:
            owner[cell] = i
    h, w = len(grid), len(grid[0])
    for (r, c), i in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if not (dr or dc):
                    continue
                nb = (r + dr, c + dc)
                if 0 <= nb[0] < h and 0 <= nb[1] < w and nb in owner and owner[nb] != i:
                    errs.append("components should be separated by a one-cell background moat")
                    return errs
    return errs
