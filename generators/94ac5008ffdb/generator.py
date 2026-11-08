"""Generator for arc_puzzle_bank_21_set14_bundle:hard_n04 — set-op crop on color-2/color-3 motifs.

Rule: First two components (sorted by bbox top-left). Output is a grid of
size (max(rows), max(cols)): both → 8, A only → 2, B only → 3, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: missing_color (no color-2 OR no color-3 → rule's set-op
has only one operand, undefined), identical_motifs (normalized 2-cells
== 3-cells → both/A-only/B-only collapse to a single class, no
contrast), no_overlap (motifs share no normalized cell → "both" cell
class is empty, output reduces to symmetric difference).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94ac5008ffdb"
VERSION = "1.1.1"  # add self_check
TASK_ID = "94ac5008ffdb"

SUMMARY = "Two clusters: color-2 motif + color-3 motif at separate positions."

INVARIANTS = [
    "background is 0",
    "≥3 color-2 cells (a connected motif) and ≥3 color-3 cells",
    "no other non-bg colors",
    "the two motifs do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_color", "identical_motifs", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "two_motifs",
                          "valid": "two_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥3 color-2 cells; ≥3 color-3 cells; no other non-{0,2,3} colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    n2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    n3 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    others = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 2, 3))
    if n2 < 3:
        errs.append(f"expected ≥3 color-2 cells; got {n2}")
    if n3 < 3:
        errs.append(f"expected ≥3 color-3 cells; got {n3}")
    if others:
        errs.append(f"unexpected non-{{0,2,3}} colors: {others}")
    return errs


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n_lo, n_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 14)
        n_lo, n_hi = 4, 5
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 11, 14)
        n_lo, n_hi = 3, 5
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        n_a = rng.randint(n_lo, n_hi)
        cells_a = _build_motif(rng, n_a)
        rs = [r for r, _ in cells_a]; cs = [c for _, c in cells_a]
        min_ra, min_ca = min(rs), min(cs)
        norm_a = {(r - min_ra, c - min_ca) for r, c in cells_a}
        sh_a = max(rs) - min_ra + 1; sw_a = max(cs) - min_ca + 1
        placed_a = False
        for _ in range(80):
            r0 = rng.randint(0, h - sh_a); c0 = rng.randint(0, w - sw_a)
            cells_p = [(r0 + r - min_ra, c0 + c - min_ca) for r, c in cells_a]
            if any(g[r][c] != 0 for r, c in cells_p):
                continue
            for r, c in cells_p:
                g[r][c] = 2
            placed_a = True; break
        if not placed_a:
            continue
        n_b = rng.randint(n_lo, n_hi)
        cells_b = _build_motif(rng, n_b)
        rs = [r for r, _ in cells_b]; cs = [c for _, c in cells_b]
        min_rb, min_cb = min(rs), min(cs)
        norm_b = {(r - min_rb, c - min_cb) for r, c in cells_b}
        # The declared degenerate textures are not allowed to leak into the
        # default path: the set-op crop needs a BOTH class plus A-only and
        # B-only cells, and the two normalized motifs must not be identical.
        if not (norm_a & norm_b) or not (norm_a - norm_b) or not (norm_b - norm_a):
            continue
        sh_b = max(rs) - min_rb + 1; sw_b = max(cs) - min_cb + 1
        for _ in range(80):
            r0 = rng.randint(0, h - sh_b); c0 = rng.randint(0, w - sw_b)
            cells_p = [(r0 + r - min_rb, c0 + c - min_cb) for r, c in cells_b]
            if any(g[r][c] != 0 for r, c in cells_p):
                continue
            for r, c in cells_p:
                g[r][c] = 3
            return g
    raise ValueError("could not realize set14 n04 layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "missing_color":
        # No color-3 — rule's set-op has only one operand.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 2
        return g
    if name == "identical_motifs":
        # Normalized 2-cells == 3-cells — both/A-only/B-only collapse.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][7 + dc] = 3
        return g
    if name == "no_overlap":
        # Motifs share no normalized cell — "both" class is empty,
        # output is symmetric difference only.
        # 2 = (0,0)(0,1)(1,1); 3 = (1,0)(1,1) — wait those share (1,1).
        # Use: 2 = (0,1)(1,0); 3 = (0,0)(1,1) — disjoint normalized.
        g[2][3] = 2; g[3][2] = 2
        g[5][7] = 3; g[6][8] = 3
        return g
    return g


def _color_components(grid, color):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append(cells)
    return out

def _norm_cells(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal-path invariant: color-2/color-3 motifs support a nondegenerate set-op crop."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errors = []
    bad = sorted({v for row in grid for v in row if v not in (0, 2, 3)})
    if bad:
        errors.append(f"unexpected colors {bad}")
    comps2 = _color_components(grid, 2)
    comps3 = _color_components(grid, 3)
    if len(comps2) != 1:
        errors.append(f"color 2 has {len(comps2)} components, expected 1")
    if len(comps3) != 1:
        errors.append(f"color 3 has {len(comps3)} components, expected 1")
    if len(comps2) == 1 and len(comps3) == 1:
        a = _norm_cells(comps2[0]); b = _norm_cells(comps3[0])
        if not (a & b):
            errors.append("normalized motifs have no BOTH cells")
        if not (a - b):
            errors.append("normalized motif A has no A-only cells")
        if not (b - a):
            errors.append("normalized motif B has no B-only cells")
    return errors
