"""Generator for arc_additional_puzzles_21_set20_bundle:H135 — panel transform analogy.

Rule: full-column color-8 dividers split the input into three equal panels.
Each panel is cropped to its nonzero content. The unique non-identity transform
that maps cropped A to cropped B is applied to cropped C.

Combinatorial axes (8): panel_n, transform, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, identity_transform, no_C.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "deb48f07adde"
VERSION = "1.3.0"
TASK_ID = "deb48f07adde"

SUMMARY = (
    "3 square-ish panels separated by full-column color-8 dividers; cropped B "
    "is a unique non-identity D4-style transform of cropped A; output is the "
    "same transform applied to cropped C."
)

INVARIANTS = [
    "background is 0",
    "two full-height color-8 divider columns split the grid into three equal panels",
    "A and B are related by one unique non-identity transform",
    "C contains a non-empty independent motif",
    "the inferred transform visibly changes C",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "identity_transform", "no_C")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_n":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "transform":      {"type": "int", "default": "rng non-id transform", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "three_panels_8dividers",
                       "valid": "three_panels_8dividers"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _mat_xform(mat, t):
    """Canonical cropped transform family used by the Racket rule.

    0=id, 1=rotate-cw, 2=rotate-180, 3=flip-lr, 4=flip-ud, 5=transpose.
    """
    h, w = len(mat), len(mat[0])
    if t == 0:
        return [row[:] for row in mat]
    if t == 1:
        return [[mat[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if t == 2:
        return [[mat[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if t == 3:
        return [[mat[r][w - 1 - c] for c in range(w)] for r in range(h)]
    if t == 4:
        return [[mat[h - 1 - r][c] for c in range(w)] for r in range(h)]
    return [[mat[r][c] for r in range(h)] for c in range(w)]


def _motif_from_cells(cells, color):
    rs = [r for r, _c in cells]
    cs = [c for _r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    mat = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
    for r, c in cells:
        mat[r - r0][c - c0] = color
    return mat


def _rand_motif(rng, max_n, color, k_lo=3, k_hi=6):
    k = rng.randint(k_lo, min(k_hi, max_n * max_n))
    cells = [(rng.randint(0, max_n - 1), rng.randint(0, max_n - 1))]
    seen = set(cells)
    attempts = 0
    while len(cells) < k and attempts < 300:
        attempts += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < max_n and 0 <= nc < max_n and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return _motif_from_cells(cells, color)


def _unique_nonidentity_code(a, b):
    matches = [t for t in range(1, 6) if _mat_xform(a, t) == b]
    return matches[0] if len(matches) == 1 else None


def _place_panel(g, mat, col0, rng):
    n = len(g)
    ph, pw = len(mat), len(mat[0])
    if ph > n or pw > n:
        return False
    r0 = rng.randint(0, n - ph)
    c0 = col0 + rng.randint(0, n - pw)
    for r in range(ph):
        for c in range(pw):
            if mat[r][c] != 0:
                g[r0 + r][c0 + c] = mat[r][c]
    return True


def _crop_panel(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v != 0]
    if not cells:
        return []
    rs = [r for r, _c in cells]
    cs = [c for _r, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    return [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]


def _split_panels(g):
    divs = [c for c in range(len(g[0])) if all(row[c] == 8 for row in g)]
    if len(divs) != 2:
        return None
    d1, d2 = divs
    if d1 == 0 or d2 <= d1 + 1 or d2 == len(g[0]) - 1:
        return None
    widths = [d1, d2 - d1 - 1, len(g[0]) - d2 - 1]
    if len(set(widths)) != 1:
        return None
    n = widths[0]
    return (
        [row[:d1] for row in g],
        [row[d1 + 1:d2] for row in g],
        [row[d2 + 1:] for row in g],
        n,
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("panel_n", 4, 4)
        t_choices = [1, 2]
    elif difficulty == "hard":
        n = ctx.draw_int("panel_n", 5, 6)
        t_choices = [3, 4, 5]
    else:
        n = ctx.draw_int("panel_n", 4, 5)
        t_choices = [1, 2, 3, 4, 5]
    rng = ctx.draw_rng("layout")
    h = n
    w = n * 3 + 2
    d1, d2 = n, 2 * n + 1
    color_a, color_c = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)
    t = rng.choice(t_choices)

    for _outer in range(240):
        a = _rand_motif(rng, n, color_a)
        b = _mat_xform(a, t)
        if _unique_nonidentity_code(a, b) != t:
            continue
        c = _rand_motif(rng, n, color_c)
        out_c = _mat_xform(c, t)
        if out_c == c:
            continue
        if len(a) > n or len(a[0]) > n or len(b) > n or len(b[0]) > n or len(c) > n or len(c[0]) > n:
            continue
        g = full_grid(h, w, 0)
        for r in range(h):
            g[r][d1] = 8
            g[r][d2] = 8
        if _place_panel(g, a, 0, rng) and _place_panel(g, b, d1 + 1, rng) and _place_panel(g, c, d2 + 1, rng):
            return g
    raise ValueError("failed to build a unique, visible transform analogy")


def _draw_from_degenerate(name, rng):
    n = 4
    h = n
    w = n * 3 + 2
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        # Panels not separated — rule cannot identify panel boundaries.
        g[0][0] = 4; g[1][1] = 4
        g[0][5] = 4; g[1][6] = 4
        g[0][10] = 5; g[1][11] = 5
        return g
    if name == "identity_transform":
        # A = B exactly — rule infers identity, output = C unchanged.
        d1, d2 = n, 2 * n + 1
        for r in range(h):
            g[r][d1] = 8; g[r][d2] = 8
        g[0][0] = 4; g[1][1] = 4
        g[0][d1 + 1] = 4; g[1][d1 + 2] = 4
        g[0][d2 + 1] = 5; g[1][d2 + 2] = 5
        return g
    if name == "no_C":
        # Panel C empty — rule has no input to transform.
        d1, d2 = n, 2 * n + 1
        for r in range(h):
            g[r][d1] = 8; g[r][d2] = 8
        g[0][0] = 4; g[1][1] = 4
        g[0][d1 + 1] = 4; g[2][d1 + 2] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    split = _split_panels(grid)
    if split is None:
        return ["expected exactly two full-height color-8 dividers producing three equal panels"]
    a_panel, b_panel, c_panel, _n = split
    a = _crop_panel(a_panel)
    b = _crop_panel(b_panel)
    c = _crop_panel(c_panel)
    if not a or not b or not c:
        errs.append("A/B/C panels must all contain nonzero content")
        return errs
    code = _unique_nonidentity_code(a, b)
    if code is None:
        errs.append("A->B does not identify one unique non-identity transform")
    elif _mat_xform(c, code) == c:
        errs.append("inferred transform leaves C unchanged")
    return errs
