"""Generator for hard_137_build_rotation_relation_matrix.

Rule: 4 fixed 5×5 panels at columns [0, 6, 12, 18]. Output 4×4 matrix:
8 on diagonal; 1 if normalized panels equal; 2 if rotation-equivalent;
0 otherwise.

Combinatorial axes (8): grid_h/w, palette_kind, num_panels, panel_density,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: all_panels_equivalent, all_panels_unique, empty_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e56158e4892"
VERSION = "2.2.0"  # diversity++ : n_classes was drawn 1..4 uniformly, but n_classes==4 makes every panel a distinct class -> the OUTPUT is always the boring identity matrix (diag 8, rest 0). That single matrix swamped the smoke window (distinct_out=4 -> flagged). Draw n_classes 1..3 so panels OVERLAP and the off-diagonal exercises both rel=1 (equal) and rel=2 (rotation-equiv), giving far more distinct matrices. + self_check.
TASK_ID = "1e56158e4892"
SUMMARY = (
    "Fixed 5×23 0-bg grid with 4 PANELS at "
    "FIXED cols [0..4], [6..10], [12..16], "
    "[18..22] (each 5×5, separated by empty "
    "divider cols). Each panel contains 3-7 "
    "cells of a single distinct non-zero color "
    "at random positions. Rule: SPLIT into 4 "
    "panels. BINARIZE each. COMPUTE the "
    "ROTATION-EQUIVALENCE class of each panel "
    "under the 4 rotations (0°, 90°, 180°, "
    "270°). Build a 4×4 OUTPUT MATRIX: cell "
    "(i, j) = 8 if i == j (diagonal); else 1 "
    "if normalized binaries of panel i and "
    "panel j are EXACTLY EQUAL (identical "
    "shape); else 2 if rotation-equivalent "
    "(same rotation orbit but different "
    "orientation); else 0. Net: 4×4 matrix "
    "encoding panel rotation-relations."
)

INVARIANTS = [
    "background is 0",
    "grid is 5 rows tall and 23 cols wide",
    "4 panels each holding 3-7 non-bg cells in a single color",
]

PALETTE_KINDS = ("default", "sparse_panels", "dense_panels", "varied")
DEGENERATE_TEXTURES = ("all_panels_equivalent", "all_panels_unique", "empty_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5"},
    "grid_w":         {"type": "int", "default": "23", "valid": "23"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse_panels|dense_panels|varied"},
    "num_panels":     {"type": "int", "default": "4", "valid": "4"},
    "n_classes":      {"type": "int", "default": "rng 1..4 rotation classes", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse_panels|dense_panels|varied|all_panels_equivalent|all_panels_unique|empty_panels"},
}

_STARTS = [0, 6, 12, 18]
_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _motif(rng, k, s=5):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < s and 0 <= nc < s and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return _norm(cells)


def _rot90(cells):
    maxr = max(r for r, _ in cells)
    return _norm([(c, maxr - r) for r, c in cells])


def _rot(cells, k):
    for _ in range(k % 4):
        cells = _rot90(cells)
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # 1..3 classes (never 4): with 4 distinct classes every off-diagonal cell
    # is 0 and the output collapses to the single identity matrix. Overlapping
    # classes are what make the relation matrix vary.
    n_classes = ctx.draw_int("n_classes", 1, 3)
    rng = ctx.draw_rng("layout")
    h = 5; w = 23
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)

    # one base per rotation class (distinct cell counts -> classes never rot-equiv).
    counts = rng.sample(range(3, 8), n_classes)
    bases = [_motif(rng, k) for k in counts]
    assign = list(range(n_classes)) + [rng.randint(0, n_classes - 1)
                                       for _ in range(4 - n_classes)]
    rng.shuffle(assign)
    # per panel a rotation index: same class+rot -> equal(1); same class diff rot -> rot-equiv(2)
    rots = [rng.randint(0, 3) for _ in range(4)]

    g = full_grid(h, w, 0)
    for c0, color, cls, rk in zip(_STARTS, palette, assign, rots):
        cells = _rot(bases[cls], rk)
        for dr, dc in cells:
            if dr < 5 and dc < 5:
                g[dr][c0 + dc] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """5x23 grid; each of the 4 fixed 5x5 panels (cols 0,6,12,18) holds 3-7
    non-bg cells in a single color; and the panels must NOT all be in distinct
    rotation classes (else the output collapses to the identity matrix).
    Returns a list of violation strings (empty == pass)."""
    msgs = []
    if len(grid) != 5 or len(grid[0]) != 23:
        msgs.append(f"grid must be 5x23, got {len(grid)}x{len(grid[0])}")
        return msgs
    classes = []
    for c0 in _STARTS:
        cells = [(r, c - c0) for r in range(5) for c in range(c0, c0 + 5)
                 if grid[r][c] != 0]
        cols = {grid[r][c0 + dc] for (r, dc) in cells}
        if not (3 <= len(cells) <= 7):
            msgs.append(f"panel@{c0} has {len(cells)} cells (want 3-7)")
        if len(cols) > 1:
            msgs.append(f"panel@{c0} not single-colored: {cols}")
        # rotation-equivalence class = min over 4 rotations of normalized shape
        norm = _norm(cells)
        orbit = [norm]
        for _ in range(3):
            norm = _rot90(norm); orbit.append(norm)
        classes.append(min(tuple(map(tuple, o)) for o in orbit))
    if len(set(classes)) == 4:
        msgs.append("all 4 panels in distinct rotation classes "
                    "-> output is the trivial identity matrix")
    return msgs


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 23, 0)
    palette = [3, 4, 5, 6]
    base_pattern = [(0, 0), (0, 1), (1, 0), (2, 2), (4, 4)]
    if name == "all_panels_equivalent":
        # all panels are exact rotations of one shape — relation matrix is mostly 1s/2s
        for c0, color in zip(_STARTS, palette):
            for dr, dc in base_pattern:
                g[dr][c0 + dc] = color
        return g
    if name == "all_panels_unique":
        # all panels distinct under rotation — diagonal-only matrix
        patterns = [
            [(0, 0), (1, 0), (2, 0)],
            [(0, 0), (0, 1), (0, 2), (0, 3)],
            [(0, 0), (0, 1), (1, 0), (1, 1)],
            [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
        ]
        for c0, color, pat in zip(_STARTS, palette, patterns):
            for dr, dc in pat:
                g[dr][c0 + dc] = color
        return g
    if name == "empty_panels":
        return g
    return g
