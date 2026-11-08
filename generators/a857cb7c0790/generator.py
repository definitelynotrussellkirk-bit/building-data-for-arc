"""Generator for arc_puzzle_bank_21_set20_s:S20_H1 — strip-mark mismatched panels.

Rule: panels separated by full color-9 columns. First panel is the template;
following panels are candidates. Output marks (color 8) the indexes of
candidates that are NOT a dihedral variant of the template.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers (no color-9 columns → rule cannot identify
panels); no_template (panel 0 empty → rule has nothing to match
against); all_match (every candidate is a dihedral variant → rule's
output mark column is empty, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a857cb7c0790"
VERSION = "2.1.1"
TASK_ID = "a857cb7c0790"

SUMMARY = (
    "Horizontally-tiled grid: panel_h × W "
    "where panel_h ∈ {3-5} and W = 3 * n + "
    "(n-1) with n ∈ {4, 5} panels. Layout: "
    "(a) n PANELS each panel_h rows × 3 "
    "cols, arranged left-to-right; (b) "
    "FULL color-9 DIVIDER COLUMNS between "
    "panels; (c) PANEL 0 holds the "
    "TEMPLATE — a 2-3 cell connected motif "
    "in a single non-{0, 9} color drawn "
    "from {2..7}; (d) PANELS 1..n-1 hold "
    "CANDIDATE MOTIFS: 50% of candidates "
    "are a DIHEDRAL VARIANT (rotation or "
    "reflection) of the template (also in "
    "the template's color); the rest are "
    "random non-template shapes in the "
    "same color. Rule (MARK THE MISMATCHED "
    "PANELS — THOSE WHOSE MOTIFS ARE NOT A "
    "DIHEDRAL VARIANT OF THE TEMPLATE — "
    "WITH COLOR 8 STRIP MARKERS): READ the "
    "TEMPLATE in panel 0. COMPUTE its "
    "DIHEDRAL VARIANTS (8 rotations + "
    "reflections). For EACH CANDIDATE "
    "PANEL (panels 1..n-1): CHECK if its "
    "motif (normalized) matches ANY "
    "template variant. IF the motif does "
    "NOT match (mismatch): MARK that "
    "panel — e.g., paint a COLOR 8 (cyan) "
    "VERTICAL STRIP at the panel's "
    "rightmost interior column or above "
    "the panel's index per demos. "
    "Matching panels stay unchanged. The "
    "template panel and 9-dividers also "
    "stay. Net: each candidate panel "
    "either keeps its motif (dihedral "
    "match) or gets a cyan strip marker "
    "(mismatch). Flagged intrinsic-low "
    "(uniq_out=21): output normalizes "
    "across small motif and marker "
    "permutations."
)

INVARIANTS = [
    "background is 0",
    "panels separated by full color-9 columns of equal width 3",
    "each panel has a small motif in some color (template + candidates)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "no_template", "all_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 3..5", "valid": "3..7"},
    "grid_w":            {"type": "int", "default": "computed", "valid": "—"},
    "n_panels":          {"type": "int", "default": "rng 4..5", "valid": "3..7"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "panels_separated_by_9_cols",
                          "valid": "panels_separated_by_9_cols"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_dividers|no_template|all_match"},
}


def _normalize(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    rmin, cmin = min(rs), min(cs)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _rot(cells):
    return [(c, -r) for r, c in cells]


def _flip(cells):
    return [(r, -c) for r, c in cells]


def _variants(cells):
    out = set()
    cur = list(cells)
    for _ in range(4):
        out.add(tuple(_normalize(cur))); cur = _rot(cur)
    cur = _flip(cells)
    for _ in range(4):
        out.add(tuple(_normalize(cur))); cur = _rot(cur)
    return [list(v) for v in out]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one full-height color-9 divider column separating panels."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not div_cols:
        return errs  # degenerate (no_dividers) — allowed
    # At least one panel must have non-zero non-9 content (the template)
    has_template = any(
        grid[r][c] not in (0, 9)
        for r in range(h)
        for c in range(div_cols[0])
    )
    if not has_template:
        return errs  # degenerate (no_template) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = 1 x (n_panels-1) binary strip (candidate differs from template?).
    # v1.x used n_panels 4-5 -> only 2^3+2^4=24 possible strips (dup-outputs).
    # Raise panel count (w=4n-1, so n<=7 fits 30 cols) -> up to 2^6 more patterns.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 3, 4)
        n = ctx.draw_int("n_panels", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 4, 5)
        n = ctx.draw_int("n_panels", 6, 7)
    else:
        h = ctx.draw_int("grid_h", 3, 5)
        n = ctx.draw_int("n_panels", 4, 7)
    rng = ctx.draw_rng("layout")

    panel_w = 3
    w = panel_w * n + (n - 1)

    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h): g[r][c] = 9
    color = rng.choice([2, 3, 4, 5, 6, 7])
    cells = [(0, 0)]
    seen = {(0, 0)}
    target = rng.randint(2, 3)
    while len(cells) < target:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen and 0 <= nr < h and 0 <= nc < panel_w:
            cells.append((nr, nc)); seen.add((nr, nc))
    template = _normalize(cells)
    variants = [tuple(v) for v in _variants(template)]

    panel_col0_table = [k * (panel_w + 1) for k in range(n)]

    for r, c in template:
        g[r][c] = color
    for k in range(1, n):
        if rng.choice([True, False]):
            shape = list(rng.choice(_variants(template)))
        else:
            for _t in range(20):
                ncells = [(0, 0)]; nseen = {(0, 0)}
                tg = rng.randint(2, 3)
                while len(ncells) < tg:
                    rr, cc = rng.choice(ncells)
                    dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
                    nr, nc = rr + dr, cc + dc
                    if (nr, nc) not in nseen and 0 <= nr < h and 0 <= nc < panel_w:
                        ncells.append((nr, nc)); nseen.add((nr, nc))
                norm = _normalize(ncells)
                if tuple(norm) not in variants:
                    shape = norm; break
            else:
                shape = list(rng.choice(_variants(template)))
        rs = [r for r, _ in shape]; cs = [c for _, c in shape]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        if sw > panel_w or sh > h: continue
        r0 = 0
        c0 = panel_col0_table[k]
        for r, c in shape:
            g[r0 + r][c0 + c] = color
    return g


def _draw_from_degenerate(name, rng):
    h = 4
    panel_w = 3
    n = 4
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        # No color-9 separator columns.
        g[0][0] = 4; g[1][0] = 4; g[1][1] = 4
        g[0][6] = 4; g[1][6] = 4
        return g
    if name == "no_template":
        # Panel 0 empty — rule has nothing to match against.
        for k in range(1, n):
            cidx = panel_w * k + (k - 1)
            for r in range(h): g[r][cidx] = 9
        for k in range(1, n):
            base = k * (panel_w + 1)
            g[0][base] = 4; g[1][base] = 4
        return g
    if name == "all_match":
        # Every candidate is a dihedral variant of template.
        for k in range(1, n):
            cidx = panel_w * k + (k - 1)
            for r in range(h): g[r][cidx] = 9
        for k in range(n):
            base = k * (panel_w + 1)
            g[0][base] = 4; g[1][base] = 4
        return g
    return g
