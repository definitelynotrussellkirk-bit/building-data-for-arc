"""Generator for arc_puzzle_bank_21_set20_s:S20_H5 — panel dihedral-equivalence matrix.

Rule: split the grid into N panels at full-height color-9 divider columns and crop each
to its non-zero content. Output an N×N matrix where cell (r,c) is 8 if panel r and panel c
have the same shape under some dihedral transform (rotation/flip), else 0 — i.e. the
pairwise dihedral-equivalence table of the panel motifs. (The "each has a small motif"
header was the copy-paste panel-family template; the SUMMARY below is authoritative.)

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "10b95b5e7d1c"
VERSION = "1.4.1"  # +self_check
TASK_ID = "10b95b5e7d1c"

SUMMARY = ("N panels separated by full-height color-9 divider columns, each holding a small "
           "motif. Rule crops each panel and outputs an NxN matrix with 8 at (r,c) when panel r "
           "and panel c are dihedral-equivalent (same shape under rotation/flip), else 0.")

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns (1 col wide)",
    "each panel has a motif (1..6 cells) in a non-{0,9} color at a random in-panel position",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..6", "valid": "3..6"},
    "panel_w":        {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "n_panels":       {"type": "int", "default": "rng 4..6", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "horizontal_panels_9divs",
                       "valid": "horizontal_panels_9divs"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_dividers|empty_panels|single_panel"},
}


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


# Motif FAMILIES that are pairwise DIHEDRALLY DISTINCT (verified). Repeating a
# family across panels (with an independent random dihedral transform) creates
# equivalence pairs -> the N x N matrix block structure varies with the chosen
# partition, instead of collapsing to all-8 / identity.
_MOTIF_FAMILIES = [
    [(0, 0)],                                        # dot
    [(0, 0), (0, 1)],                                # domino
    [(0, 0), (0, 1), (1, 0)],                        # L tromino
    [(0, 0), (0, 1), (0, 2)],                        # I tromino
    [(0, 0), (0, 1), (1, 0), (1, 1)],                # square
    [(0, 0), (0, 1), (0, 2), (1, 1)],                # T tetromino
    [(0, 0), (1, 0), (1, 1), (2, 1)],                # S tetromino
    [(0, 0), (1, 0), (2, 0), (2, 1)],                # L tetromino
    [(0, 0), (0, 1), (0, 2), (0, 3)],                # I tetromino
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],        # P pentomino
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],        # plus pentomino
]


def _norm(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    mr, mc = min(rs), min(cs)
    return [(r - mr, c - mc) for r, c in cells]


def _rotcw(cells):
    rs = [r for r, _ in cells]; mx = max(rs)
    return _norm([(c, mx - r) for r, c in cells])


def _fliplr(cells):
    cs = [c for _, c in cells]; mx = max(cs)
    return _norm([(r, mx - c) for r, c in cells])


def _rand_dihedral(cells, rng):
    out = _norm(cells)
    for _ in range(rng.randint(0, 3)):
        out = _rotcw(out)
    if rng.random() < 0.5:
        out = _fliplr(out)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 4, 4)
        n = ctx.draw_int("n_panels", 3, 4)
        panel_w = 4
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 6)
        n = ctx.draw_int("n_panels", 5, 6)
        panel_w = ctx.draw_int("panel_w", 4, 5)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 6)
        n = ctx.draw_int("n_panels", 4, 6)
        panel_w = ctx.draw_int("panel_w", 4, 5)
    rng = ctx.draw_rng("layout")

    # w = (panel_w+1)*n - 1 must fit the 30-col ARC canvas.
    while (panel_w + 1) * n - 1 > 30:
        n -= 1
    n = max(2, n)
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h): g[r][c] = 9
    # Choose a random PARTITION of the n panels over a set of dihedrally-distinct
    # families. Repeats -> dihedral-equivalent panels (8s off-diagonal);
    # distinct -> 0s. This makes the N x N matrix block structure vary widely.
    fams = [f for f in _MOTIF_FAMILIES
            if (max(r for r, _ in f) + 1) <= h
            and (max(c for _, c in f) + 1) <= panel_w]
    rng.shuffle(fams)
    n_distinct = rng.randint(1, min(n, len(fams)))
    base = fams[:n_distinct]
    assignment = [rng.choice(base) for _ in range(n)]
    rng.shuffle(assignment)
    for k in range(n):
        c0 = k * (panel_w + 1)
        cells = _rand_dihedral(assignment[k], rng)
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) + 1; sw = max(cs) + 1
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        top = rng.randint(0, h - sh); left = rng.randint(0, panel_w - sw)
        for r, c in cells:
            g[top + r][c0 + left + c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Full color-9 separator columns present; non-{0,9} motif cells present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not sep_cols:
        errors.append("no full-height color-9 divider columns found")
    has_motif = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if not has_motif:
        errors.append("no non-{0,9} motif cells found in any panel")
    return errors


def _draw_from_degenerate(name, rng):
    panel_h, n, panel_w = 4, 5, 4
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        for k in range(n):
            c0 = k * panel_w
            g[1][c0 + 1] = [4, 6, 7, 4, 6][k]
        return g
    if name == "empty_panels":
        for k in range(1, n):
            c = panel_w * k + (k - 1)
            for r in range(h): g[r][c] = 9
        return g
    if name == "single_panel":
        g[1][1] = 4
        return g
    return g
