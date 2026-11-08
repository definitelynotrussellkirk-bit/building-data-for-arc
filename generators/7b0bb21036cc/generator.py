"""Generator for arc_puzzle_bank_thirteenth21:M86 — command-coded shape transform.

The canonical rule (re-derived): cell (0,0) holds a COMMAND CODE; the rest of the
grid holds a single shape. The rule zeroes (0,0), crops the shape to its bbox,
and applies the transform the code selects: 1 = flip-lr, 2 = rotate-cw,
3 = rotate-180, anything else = identity. Output = the transformed crop.

The previous body was a MISLABELLED "6 panels / find pair" generator (full
color-9 divider columns), which the rule read as: command = g[0][0] (usually a
0/bg panel cell -> identity transform), shape = the whole panel block -> the
output frequently equalled the input. This version builds inputs that MATCH the
rule: a command in {1,2,3} at (0,0) and one asymmetric shape placed in the
interior, so the transform is always visible.

Degenerates: code_zero (identity transform), no_shape, full_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7b0bb21036cc"
VERSION = "2.0.0"  # rewrite: was a mislabelled panel/find-pair generator whose g[0][0] command was usually bg -> identity transform -> output==input. Now command{1,2,3} at (0,0) + one asymmetric interior shape -> transform always visible.
TASK_ID = "7b0bb21036cc"

SUMMARY = (
    "Square-ish 0-bg grid with a COMMAND CODE in {1,2,3} at cell (0,0) and one "
    "connected asymmetric shape (3-6 cells, a non-0 colour) placed in the "
    "interior (rows/cols >=1, clear of (0,0)). Rule: zero (0,0), crop the shape "
    "to its bbox, and apply the code's transform (1=flip-lr, 2=rotate-cw, "
    "3=rotate-180). Output = the transformed cropped shape."
)

INVARIANTS = [
    "cell (0,0) is a command code in {1,2,3}",
    "exactly one shape (the non-0 cells other than (0,0)), placed clear of (0,0)",
    "the shape is asymmetric under the chosen transform so the output changes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("code_zero", "no_shape", "full_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "cmd":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "shape_size":     {"type": "int", "default": "rng 3..6", "valid": "2..7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|code_zero|no_shape|full_shape"},
}


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _transform(cells, code):
    """Match the canonical t13-transform on a normalized cell set."""
    if code == 1:                                  # flip-lr
        cs = [c for _, c in cells]; mx = max(cs)
        out = [(r, mx - c) for r, c in cells]
    elif code == 2:                                # rotate-cw
        rs = [r for r, _ in cells]; mx = max(rs)
        out = [(c, mx - r) for r, c in cells]
    elif code == 3:                                # rotate-180
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        out = [(max(rs) - r, max(cs) - c) for r, c in cells]
    else:
        out = list(cells)
    mr = min(r for r, _ in out); mc = min(c for _, c in out)
    return frozenset((r - mr, c - mc) for r, c in out)


def _visible(cells, code):
    """True if the transform changes the shape (so the output differs visibly)."""
    base = _transform(cells, 0)
    return _transform(cells, code) != base


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 6, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 11, 16)
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 8, 12)
    cmd = ctx.draw_int("cmd", 1, 3)
    rng = ctx.draw_rng("layout")

    # asymmetric shape under the chosen transform so the output visibly changes
    shape = _build_motif(rng, rng.randint(3, 6))
    for _ in range(40):
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        if sh < h and sw < w and _visible(shape, cmd):
            break
        shape = _build_motif(rng, rng.randint(3, 6))
    sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1

    g = full_grid(h, w, 0)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    # place the shape clear of row 0 and col 0 (so (0,0) is the only cell there)
    r0 = rng.randint(1, h - sh); c0 = rng.randint(1, w - sw)
    for r, c in shape:
        g[r0 + r][c0 + c] = color
    g[0][0] = cmd
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    L = [(2, 2), (3, 2), (3, 3), (4, 3)]   # asymmetric
    if name == "code_zero":
        # command 0 -> identity transform -> output == cropped shape (no change)
        for r, c in L:
            g[r][c] = 4
        return g
    if name == "no_shape":
        # only the command cell -> nothing to transform
        g[0][0] = 2
        return g
    if name == "full_shape":
        # shape fills the grid -> crop == grid, transform of a full block
        for r in range(8):
            for c in range(8):
                g[r][c] = 5
        g[0][0] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Command in {1,2,3} at (0,0), one shape clear of row 0 / col 0, and the
    shape is asymmetric under that command's transform (so the output changes)."""
    h, w = len(grid), len(grid[0])
    cmd = grid[0][0]
    if cmd not in (1, 2, 3):
        return [f"cell (0,0) = {cmd} is not a transform command in {{1,2,3}}"]
    shape = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] != 0 and (r, c) != (0, 0)]
    if not shape:
        return ["no shape besides the command cell -> nothing to transform"]
    if any(r == 0 or c == 0 for r, c in shape):
        return ["shape touches row 0 / col 0 -> overlaps the command cell region"]
    mr = min(r for r, _ in shape); mc = min(c for _, c in shape)
    norm = [(r - mr, c - mc) for r, c in shape]
    if not _visible(norm, cmd):
        return [f"shape is symmetric under command {cmd} -> transform not visible"]
    return []
