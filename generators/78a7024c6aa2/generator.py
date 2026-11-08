"""Generator for e14e4b5836bc:H92 -- infer a dihedral transform, apply to C.

Rule: a color-9 cross splits the grid into quadrants A (top-left), B
(top-right), C (bottom-left) and an empty answer quadrant. Find the first
transform T in (cw, 180, ccw, lr, ud) with T(A)=B, then paste T(C) into the
answer quadrant. (Analogy A:B :: C:?.)

This generator builds square quadrants A and C with a random pattern, sets
B = T(A) for a chosen transform, and leaves the answer quadrant empty.

Combinatorial axes: quadrant size, the transform, the A/C patterns and colors.
Degenerates: identity_like, sparse, tiny.

NOTE: the output is T(C), a small quadrant, so OUTPUTS are bounded; distinct
INPUTS are large.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78a7024c6aa2"
VERSION = "2.1.0"  # diversity: random A/C + chosen dihedral transform (was ~31)
TASK_ID = "78a7024c6aa2"
SUMMARY = (
    "Grid split by a color-9 cross into square quadrants. A->B demonstrates a "
    "dihedral transform (cw/180/ccw/lr/ud); the rule applies it to C in the "
    "answer quadrant. The quadrant size, transform, A/C patterns and colors "
    "vary freely (was a fixed setup, ~31 distinct). Output is T(C), so "
    "bounded; inputs are large."
)

INVARIANTS = [
    "a color-9 cross splits the grid into 4 square quadrants",
    "B = T(A) for one dihedral transform T; the answer quadrant is empty",
    "the output is T(C) in the answer quadrant",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_like", "sparse", "tiny")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = [1, 2, 3, 4, 5, 6, 7, 8]   # quadrant content colors (not 9, the divider)

AXES = {
    "quad_size":      {"type": "int", "default": "varies", "valid": "3..7"},
    "transform":      {"type": "str", "default": "rng", "valid": "cw|180|ccw|lr|ud"},
    "fill_frac":      {"type": "float", "default": "varies", "valid": "0.4..0.8"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "quadrants", "valid": "quadrants"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|identity_like|sparse|tiny"},
}


def _rot_cw(a):
    n = len(a); mm = len(a[0])
    return [[a[n - 1 - j][i] for j in range(n)] for i in range(mm)]


def _rot_ccw(a):
    n = len(a); mm = len(a[0])
    return [[a[j][mm - 1 - i] for j in range(n)] for i in range(mm)]


def _rot_180(a):
    return [row[::-1] for row in a[::-1]]


def _flip_lr(a):
    return [row[::-1] for row in a]


def _flip_ud(a):
    return [row[:] for row in a[::-1]]


_TRANSFORMS = {"cw": _rot_cw, "180": _rot_180, "ccw": _rot_ccw,
               "lr": _flip_lr, "ud": _flip_ud}


def _rand_quad(rng, Q, colors, frac):
    """One connected, single-color panel motif.

    The old Bernoulli texture created dozens of tiny components, while the
    canonical examples are a few coherent panel shapes separated by the 9-cross.
    A connected polyomino keeps the analogy structure visible and brings the
    object-count distribution back toward the task.
    """
    target = max(2, min(Q * Q - 1, int(round(Q * Q * frac * 0.55))))
    cells = {(rng.randrange(Q), rng.randrange(Q))}
    frontier = list(cells)
    while len(cells) < target:
        r, c = rng.choice(frontier)
        nbrs = [(r + dr, c + dc) for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if 0 <= r + dr < Q and 0 <= c + dc < Q]
        rng.shuffle(nbrs)
        for n in nbrs:
            if n not in cells:
                cells.add(n); frontier.append(n); break
        else:
            frontier.remove((r, c))
            if not frontier:
                frontier = list(cells)
    color = rng.choice(colors)
    return [[color if (r, c) in cells else 0 for c in range(Q)] for r in range(Q)]


def _assemble(a, b, c, Q):
    n = 2 * Q + 1
    g = full_grid(n, n, 0)
    for r in range(Q):
        for col in range(Q):
            g[r][col] = a[r][col]
            g[r][Q + 1 + col] = b[r][col]
            g[Q + 1 + r][col] = c[r][col]
    for col in range(n):
        g[Q][col] = 9
    for r in range(n):
        g[r][Q] = 9
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        qr, fr = (3, 4), (0.4, 0.7)
    elif difficulty == "hard":
        qr, fr = (5, 7), (0.4, 0.8)
    else:
        qr, fr = (4, 6), (0.4, 0.8)

    tname = overrides.get("transform") or rng.choice(list(_TRANSFORMS))
    T = _TRANSFORMS[tname]

    for _attempt in range(40):
        Q = rng.randint(*qr)
        f = rng.uniform(*fr)
        ncol = rng.randint(2, 4)
        colors = rng.sample(_COLORS, ncol)
        a = _rand_quad(rng, Q, colors, f)
        c = _rand_quad(rng, Q, colors, f)
        if all(v == 0 for row in a for v in row):
            continue
        b = T(a)
        return _assemble(a, b, c, Q)

    return _draw_from_degenerate("tiny", rng)   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None):
    """Verify cross, panel analogy, connected motifs, and empty answer quadrant."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if 9 not in flat:
        errs.append("color 9 (cross separator) not present")
        return errs
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    div_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    if len(div_cols) != 1:
        errs.append(f"expected one full-height color-9 column, found {div_cols}")
    if len(div_rows) != 1:
        errs.append(f"expected one full-width color-9 row, found {div_rows}")
    if errs:
        return errs
    sr, sc = div_rows[0], div_cols[0]
    if sr != sc or sr * 2 + 1 != h or sc * 2 + 1 != w:
        errs.append("separator does not split into four equal square quadrants")
        return errs
    Q = sr
    A = [row[:Q] for row in grid[:Q]]
    B = [row[Q + 1:] for row in grid[:Q]]
    C = [row[:Q] for row in grid[Q + 1:]]
    D = [row[Q + 1:] for row in grid[Q + 1:]]
    if any(v != 0 for row in D for v in row):
        errs.append("answer quadrant is not empty")
    if not any(v not in (0, 9) for row in A for v in row):
        errs.append("A quadrant is empty")
    if not any(v not in (0, 9) for row in C for v in row):
        errs.append("C/query quadrant is empty")
    if not any(T(A) == B for T in _TRANSFORMS.values()):
        errs.append("B is not a dihedral transform of A")
    for name, panel in [("A", A), ("B", B), ("C", C)]:
        colors = {v for row in panel for v in row if v not in (0, 9)}
        if len(colors) > 1:
            errs.append(f"{name} panel has multiple content colors {sorted(colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    Q = 4
    colors = [2, 3]
    a = _rand_quad(rng, Q, colors, 0.5 if name != "sparse" else 0.2)
    if all(v == 0 for row in a for v in row):
        a[0][0] = 2
    c = _rand_quad(rng, Q, colors, 0.5)
    b = _rot_cw(a) if name != "identity_like" else [row[:] for row in a]
    return _assemble(a, b, c, Q)
