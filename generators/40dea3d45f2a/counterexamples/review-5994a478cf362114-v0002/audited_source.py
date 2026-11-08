"""Generator for arc_puzzle_bank_twelfth_21_bundle:hard_79_dihedral_equivalence_matrix_ignoring_color.

Rule: 4 panels at 2x2 positions [(0,0), (0,5), (5,0), (5,5)] (4 wide
× 4 tall each). Output 4x4: 8 if panels j and i are dihedrally
equivalent, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_cell_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_panels, all_equivalent, all_distinct.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40dea3d45f2a"
VERSION = "2.1.0"  # all-8 / low-diversity fix: n_classes==1 made all panels equivalent -> solid-8 matrix. Draw n_classes from 2..4 so the matrix always has off-diagonal 0s and more distinct outputs.
TASK_ID = "40dea3d45f2a"
SUMMARY = "4 panels at fixed 2x2 positions, each a dihedral image of one of a few class bases."

INVARIANTS = [
    "background is 0",
    "grid is 9 rows tall and 9 cols wide",
    "4 panels at top-lefts [(0,0), (0,5), (5,0), (5,5)] each 4x4",
    "each panel holds 3-7 non-bg cells in any non-bg color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_panels", "all_equivalent", "all_distinct")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9", "valid": "9"},
    "grid_w":         {"type": "int", "default": "9", "valid": "9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_classes":      {"type": "int", "default": "rng 1..4 dihedral classes", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty_panels|all_equivalent|all_distinct"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _restricted_growth_strings(n):
    """All set partitions of n labeled elements as restricted-growth strings."""
    out = []

    def rec(i, cur, mx):
        if i == n:
            out.append(cur[:]); return
        for b in range(mx + 2):
            cur.append(b); rec(i + 1, cur, max(mx, b)); cur.pop()
    rec(0, [], -1)
    return out


# the 14 non-trivial partitions of the 4 panels (the single-block one — all panels
# equivalent -> solid-8 matrix — is excluded).
_PANEL_PARTITIONS = [p for p in _restricted_growth_strings(4) if len(set(p)) >= 2]


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _motif(rng, k, s=4):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < s and 0 <= nc < s and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return _norm(cells)


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
    rng = ctx.draw_rng("layout")
    h = 9; w = 9
    g = full_grid(h, w, 0)
    starts = [(0, 0), (0, 5), (5, 0), (5, 5)]
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)

    # The output is the 4x4 equivalence matrix of the panels, so distinct outputs
    # == distinct PARTITIONS of the 4 panels. Draw a partition UNIFORMLY from all
    # 14 non-trivial partitions (the all-same one is excluded -> never a solid-8
    # matrix, and uniform coverage maximizes output diversity). An explicit
    # n_classes override restricts to partitions with that many blocks.
    parts = _PANEL_PARTITIONS
    nc_override = overrides.get("n_classes")
    if nc_override is not None:
        nc = max(2, min(4, int(nc_override)))
        parts = [p for p in parts if len(set(p)) == nc] or parts
    assign = rng.choice(parts)
    n_classes = len(set(assign))

    # one base per dihedral class (distinct cell counts -> classes never equivalent);
    # same-class panels are dihedral images of the base.
    counts = rng.sample(range(3, 8), n_classes)
    bases = [_motif(rng, k) for k in counts]
    for (r0, c0), color, cls in zip(starts, palette, assign):
        cells = _dihedral(bases[cls], rng.randint(0, 7))
        # clamp into the 4x4 panel
        cells = [(r, c) for (r, c) in cells if r < 4 and c < 4]
        for dr, dc in cells:
            g[r0 + dr][c0 + dc] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The 4 panels must NOT all be dihedrally equivalent (>=2 distinct non-zero
    cell counts among them), so the output matrix is never a solid-8 block."""
    if not grid or len(grid) != 9 or any(len(row) != 9 for row in grid):
        return ["grid must be 9x9"]
    starts = [(0, 0), (0, 5), (5, 0), (5, 5)]
    counts = []
    for (r0, c0) in starts:
        n = sum(1 for dr in range(4) for dc in range(4) if grid[r0 + dr][c0 + dc] != 0)
        counts.append(n)
    if len([c for c in counts if c > 0]) < 4:
        return ["a panel is empty"]
    if len(set(counts)) < 2:
        return ["all panels share a cell count: output may be solid-8"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    starts = [(0, 0), (0, 5), (5, 0), (5, 5)]
    g = full_grid(h, w, 0)
    if name == "empty_panels":
        # all panels empty → every pair is trivially equivalent (uniform 8)
        return g
    if name == "all_equivalent":
        # all panels share one shape → matrix is all-8 with 4 different colors
        shape = [(0, 0), (1, 1), (2, 2), (3, 3)]
        for (r0, c0), color in zip(starts, [1, 2, 3, 4]):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
        return g
    if name == "all_distinct":
        # every panel has a different (non-equivalent) shape → matrix is identity (only diag is 8)
        shapes = [
            [(0, 0), (0, 1), (1, 0)],
            [(0, 0), (1, 0), (2, 0), (3, 0)],
            [(0, 0), (0, 1), (0, 2), (1, 1)],
            [(0, 0), (0, 1), (1, 0), (2, 1), (3, 3)],
        ]
        for (r0, c0), color, shape in zip(starts, [1, 2, 3, 4], shapes):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
        return g
    return g
