"""Generator for arc_puzzle_bank_eighteenth21:M126 — dihedral analogy across 3 panels.

Rule (verified against canonical): the grid is split column-wise into 3
equal SQUARE panels (separated by single divider columns). The rule infers
the single dihedral transform T (one of id, rot90, rot180, rot270, flip-h,
flip-v, transpose, anti-transpose) such that T(panel0) == panel1 EXACTLY
(full panel, position included), then outputs T(panel2).

So panel0:panel1 :: panel2:output is a transform analogy. This generator
builds panel0 = a base motif, panel1 = T(base) for a chosen dihedral T,
and panel2 = an independent query motif; the output is derived by the rule
as T(query).

Combinatorial axes: square_size, transform, base_motif, query_motif,
base_color, query_color, divider_color.
Degenerates: no_separators, identity_only, empty_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e6362765bc86"
VERSION = "3.0.0"  # WRONG-TASK rewrite: docstring claimed 'pick odd-color panel + crop' but the rule is a dihedral analogy panel0:panel1::panel2:output (infer T s.t. T(panel0)==panel1, emit T(panel2)). Old gen placed both common panels as the SAME shape at INDEPENDENT random positions -> accidental/undesigned transform, shape-locked-out (always 4x4), wrong concept. Now: deliberate T, square panels of varied size, all 8 dihedral transforms covered.
TASK_ID = "e6362765bc86"
SUMMARY = (
    "0-bg grid of 3 SQUARE panels (each s×s, s∈3..6) separated by single "
    "DIVIDER COLUMNS (color 5) at cols s and 2s+1; total width 3s+2, height s. "
    "panel0 holds a BASE MOTIF (random asymmetric cell set in base_color). "
    "panel1 holds T(base) where T is a chosen DIHEDRAL TRANSFORM ∈ {id, rot90, "
    "rot180, rot270, flip-lr, flip-ud, transpose, anti-transpose}. panel2 holds "
    "an INDEPENDENT QUERY MOTIF (random cell set in query_color). Rule (DIHEDRAL "
    "ANALOGY): split into 3 panels; INFER the transform T such that T(panel0)=="
    "panel1 exactly; APPLY T to panel2 and EMIT it. Net: panel0:panel1 :: "
    "panel2:output is a transform analogy; output is s×s."
)

INVARIANTS = [
    "background is 0",
    "3 square panels of equal size s separated by single divider columns (color 5)",
    "panel1 is exactly a dihedral transform T of panel0 (so the rule can infer T)",
    "panel2 (query) is an independent non-empty motif so T(panel2) is non-trivial",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "identity_only", "empty_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "square_size":    {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "transform":      {"type": "str", "default": "rng dihedral",
                       "valid": "id|rot90|rot180|rot270|flip-h|flip-v|transpose|anti"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "three_square_panels",
                       "valid": "three_square_panels"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TRANSFORMS = ("id", "rot90", "rot180", "rot270",
               "flip-h", "flip-v", "transpose", "anti")


def _rot90(g):                       # rotate clockwise
    return [list(row) for row in zip(*g[::-1])]


def _apply(name, g):
    if name == "id":
        return [row[:] for row in g]
    if name == "rot90":
        return _rot90(g)
    if name == "rot180":
        return _rot90(_rot90(g))
    if name == "rot270":
        return _rot90(_rot90(_rot90(g)))
    if name == "flip-h":             # flip-lr
        return [row[::-1] for row in g]
    if name == "flip-v":             # flip-ud
        return [row[:] for row in g[::-1]]
    if name == "transpose":
        return [list(row) for row in zip(*g)]
    # anti = rot180 . transpose
    t = [list(row) for row in zip(*g)]
    return _rot90(_rot90(t))


def _rand_motif(rng, s, color, min_cells):
    """Random non-empty, non-full s×s motif in `color`."""
    grid = [[0] * s for _ in range(s)]
    while True:
        on = 0
        for r in range(s):
            for c in range(s):
                if rng.random() < 0.45:
                    grid[r][c] = color
                    on += 1
        if min_cells <= on < s * s:
            return grid
        for r in range(s):
            for c in range(s):
                grid[r][c] = 0


def _paste(g, sub, c_off):
    for r, row in enumerate(sub):
        for c, v in enumerate(row):
            if v:
                g[r][c_off + c] = v


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        s = ctx.draw_int("square_size", 3, 4)
    elif difficulty == "hard":
        s = ctx.draw_int("square_size", 5, 6)
    else:
        s = ctx.draw_int("square_size", 3, 6)
    s = int(overrides.get("square_size", s))
    rng = ctx.draw_rng("layout")

    tname = overrides.get("transform")
    if tname not in _TRANSFORMS:
        tname = rng.choice(_TRANSFORMS)
    base_color, query_color = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)

    base = _rand_motif(rng, s, base_color, min_cells=max(2, s))
    panel1 = _apply(tname, base)
    query = _rand_motif(rng, s, query_color, min_cells=1)

    div = 5
    w = 3 * s + 2
    g = full_grid(s, w, 0)
    for r in range(s):
        g[r][s] = div
        g[r][2 * s + 1] = div
    _paste(g, base, 0)
    _paste(g, panel1, s + 1)
    _paste(g, query, 2 * s + 2)
    return g


def _draw_from_degenerate(name, rng):
    s = 4
    w = 3 * s + 2
    g = full_grid(s, w, 0)
    base = [[0] * s for _ in range(s)]
    base[0][0] = base[1][0] = base[1][1] = 4   # asymmetric L
    if name == "no_separators":
        # No divider columns — the rule slices by fixed position anyway,
        # but the panels run together so the analogy is undefined.
        _paste(g, base, 0)
        _paste(g, _apply("rot90", base), 4)
        _paste(g, base, 8)
        return g
    for r in range(s):
        g[r][s] = 5
        g[r][2 * s + 1] = 5
    if name == "identity_only":
        # panel1 == panel0 -> rule infers id -> output == query unchanged
        # (transform discriminator collapses to identity).
        _paste(g, base, 0)
        _paste(g, base, s + 1)
        _paste(g, base, 2 * s + 2)
        return g
    if name == "empty_panels":
        # panels empty -> id matches trivially, output empty.
        return g
    return g
