"""Generator for 14b:hard_93 — build dihedral equivalence matrix.

Rule: 4 panels at fixed cols [0..4, 6..10, 12..16, 18..22], each 5
wide. Output is a 4x4 matrix: 8 on diagonal, 2 if rotation-equivalent,
6 if dihedrally-equivalent (mirror), 0 otherwise.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_cell_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_panel, all_identical, all_unique.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "feaa89c467a0"
VERSION = "3.0.0"  # widen: arbitrary per-panel colors (rule is color-blind), in-panel position jitter (rule crops to bbox), taller grids, wider asymmetric cell counts.
TASK_ID = "feaa89c467a0"
SUMMARY = (
    "4 PANELS in fixed 5-wide column windows [0..4], "
    "[6..10], [12..16], [18..22] of a 23-col grid (5-7 "
    "rows). Each panel holds ONE asymmetric shape (3-9 "
    "cells, all 8 dihedral images distinct) jittered to a "
    "random position inside its window, in an arbitrary "
    "color (the rule is COLOR-BLIND — it works on the "
    "binary crop). Panels are assigned to 1-4 shape CLASSES "
    "(each class a distinct cell-count so classes are "
    "pairwise dihedrally-inequivalent); each panel applies "
    "one of 8 dihedral transforms to its class base. Rule: "
    "binary-crop each panel; emit a 4x4 matrix where cell "
    "(r,c) is 8 on the diagonal, 2 if shape c is a ROTATION "
    "of panel r, 6 if it is a REFLECTION (dihedral, "
    "non-rotation) of panel r, else 0."
)

INVARIANTS = [
    "background is 0",
    "grid is 23 cols wide, 5-7 rows tall",
    "4 panels in 5-wide windows at cols [0..4], [6..10], [12..16], [18..22]",
    "each panel holds one asymmetric shape (3-9 cells) within its window",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_panel", "all_identical", "all_unique")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "5..7"},
    "grid_w":         {"type": "int", "default": "23 (rule-fixed geometry)", "valid": "23"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_classes":      {"type": "int", "default": "rng 1..4 dihedral classes", "valid": "1..4"},
    "panel_cells":    {"type": "int", "default": "3..6 easy / 3..8 med / 4..9 hard", "valid": "3..9"},
    "palette_size":   {"type": "int", "default": "rng per-panel (repeats ok)", "valid": "1..9"},
    "n_distinct_colors": {"type": "int", "default": "1..4 (color-blind rule)", "valid": "1..9"},
    "density":        {"type": "str", "default": "panels", "valid": "panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty_panel|all_identical|all_unique"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _asym_motif(rng, k, s=5):
    for _ in range(200):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice(_CARD)
            nr, nc = r + dr, c + dc
            if 0 <= nr < s and 0 <= nc < s and (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        base = _norm(cells)
        if len({tuple(_dihedral(base, t)) for t in range(8)}) == 8:
            return base
    return _norm([(0, 0), (0, 1), (1, 0), (2, 0)])


def _dihedral(cells, t):
    out = []
    for (r, c) in cells:
        if t == 0:   out.append((r, c))
        elif t == 1: out.append((c, -r))
        elif t == 2: out.append((-r, -c))
        elif t == 3: out.append((-c, r))
        elif t == 4: out.append((r, -c))
        elif t == 5: out.append((-c, -r))
        elif t == 6: out.append((-r, c))
        else:        out.append((c, r))
    return _norm(out)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    n_classes = ctx.draw_int("n_classes", 1, 4)
    if difficulty == "easy":
        cell_lo, cell_hi = 3, 6
    elif difficulty == "hard":
        cell_lo, cell_hi = 4, 9
    else:
        cell_lo, cell_hi = 3, 8
    rng = ctx.draw_rng("layout")
    h = ctx.draw_int("grid_h", 5, 7); w = 23
    starts = [0, 6, 12, 18]

    # Per-panel colors are ARBITRARY (the rule binary-crops, so it never reads color):
    # draw each independently from 1..9 with repeats allowed -> more input variety.
    colors = [rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]) for _ in range(4)]

    # DISTINCT cell-counts per class => bases are automatically pairwise
    # dihedrally-inequivalent (different cell counts can't be dihedral images),
    # so off-diagonal 0s are genuine "different class" entries.
    counts = rng.sample(range(cell_lo, cell_hi + 1), n_classes)
    bases = [_asym_motif(rng, k) for k in counts]
    assign = list(range(n_classes)) + [rng.randint(0, n_classes - 1)
                                       for _ in range(4 - n_classes)]
    rng.shuffle(assign)
    tforms = [rng.randint(0, 7) for _ in range(4)]   # 0-3 rotations, 4-7 reflections

    g = full_grid(h, w, 0)
    for c0, color, cls, t in zip(starts, colors, assign, tforms):
        cells = _dihedral(bases[cls], t)   # _norm'd: min row/col = 0, within 5x5
        sh = max(dr for dr, _ in cells) + 1
        sw = max(dc for _, dc in cells) + 1
        # Jitter the shape's position inside its (h rows x 5 cols) window. The rule
        # crops each panel to its non-bg bbox, so position is irrelevant to the
        # output matrix -- pure rule-safe input diversity.
        top = rng.randint(0, h - sh) if h > sh else 0
        left = rng.randint(0, 5 - sw) if sw < 5 else 0
        for dr, dc in cells:
            rr, cc = top + dr, left + dc
            if 0 <= rr < h and 0 <= cc < 5:
                g[rr][c0 + cc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 23
    g = full_grid(h, w, 0)
    if name == "empty_panel":
        # 1 of 4 panels is blank → its row/col in the matrix is degenerate
        for r, c in [(0, 0), (1, 1), (2, 2)]:
            g[r][c] = 1
        for r, c in [(0, 12), (1, 13), (2, 14)]:
            g[r][c] = 3
        for r, c in [(0, 18), (1, 19), (2, 20), (3, 21)]:
            g[r][c] = 5
        return g
    if name == "all_identical":
        # all 4 panels are the same shape and same color → matrix saturates
        shape = [(0, 0), (1, 0), (2, 0), (1, 1)]
        for c0 in [0, 6, 12, 18]:
            for r, dc in shape:
                g[r][c0 + dc] = 4
        return g
    if name == "all_unique":
        # all 4 pairwise inequivalent → off-diagonal = all 0
        for r, c in [(0, 0), (0, 1), (0, 2)]:
            g[r][c] = 1
        for r, c in [(0, 6), (1, 6), (2, 6)]:
            g[r][c] = 3
        for r, c in [(0, 12), (1, 13), (2, 14), (3, 15)]:
            g[r][c] = 5
        for r, c in [(0, 18), (4, 18), (0, 22), (4, 22), (2, 20)]:
            g[r][c] = 7
        return g
    return g
