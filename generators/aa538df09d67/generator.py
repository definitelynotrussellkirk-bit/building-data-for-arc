"""Generator for arc_puzzle_bank_next21:M9 — paint each obj bbox border.

Rule: each connected component's bbox border (4 edges) is painted with the
component's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_cell, motifs_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa538df09d67"
VERSION = "2.1.0"  # FIX all_background (blank) + identity_demo: motifs with a degenerate (<2x2) bbox were silently skipped -> sometimes zero motifs -> blank output; and a motif already covering its full bbox border is reproduced unchanged -> when all motifs were like that, output==input. Now every motif has bbox>=2x2 (retry build), and >=1 motif is missing a border cell so the rule always adds something. + self_check.
TASK_ID = "aa538df09d67"

SUMMARY = (
    "0-bg grid (h ∈ 6-10, w ∈ 8-12, by "
    "difficulty) with: N ∈ 2-4 "
    "CONNECTED MOTIFS, each a 3-5 "
    "cell connected motif built via "
    "_build_motif random adjacent-step "
    "walk, painted in a DISTINCT non-"
    "bg color drawn from {1..9}. Each "
    "motif's bbox is ≥2×2 (single-row "
    "or single-col motifs filtered "
    "out). Motifs placed at non-"
    "overlapping positions via _free "
    "check with 1-cell padding. Rule "
    "(FOR EACH 4-CONNECTED NON-BG "
    "COMPONENT, PAINT THE 4 EDGES "
    "OF ITS BBOX (TOP, BOTTOM, LEFT, "
    "RIGHT) WITH THE COMPONENT'S "
    "COLOR — TURNING THE BBOX INTO "
    "A HOLLOW RECTANGULAR OUTLINE; "
    "INTERIOR REMAINS PARTLY PAINTED "
    "FROM THE ORIGINAL MOTIF): For "
    "EACH component with color c "
    "and bbox (rmin, cmin, rmax, "
    "cmax): PAINT all cells (rmin, "
    "c) and (rmax, c) for c in "
    "cmin..cmax, and (r, cmin) "
    "and (r, cmax) for r in "
    "rmin..rmax with COLOR c. "
    "Interior cells keep their "
    "original (motif or bg) "
    "values. Net: each motif gets "
    "wrapped in its color's "
    "rectangular bbox outline."
)

INVARIANTS = [
    "background is 0",
    "2-3 motifs in distinct non-zero colors with bbox ≥2x2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_cell", "motifs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_isolated_motifs",
                       "valid": "scattered_isolated_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        n_placed = 0
        any_missing_border = False
        for color in colors:
            # Build a motif with a non-degenerate (>=2x2) bbox; retry instead
            # of silently skipping (a skip could leave zero motifs -> blank).
            cells = None
            for _ in range(30):
                cand = _build_motif(rng, rng.randint(3, 5))
                rs = [r for r, _ in cand]; cs = [c for _, c in cand]
                if max(rs) - min(rs) + 1 >= 2 and max(cs) - min(cs) + 1 >= 2:
                    cells = cand
                    break
            if cells is None:
                ok = False; break
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True
                n_placed += 1
                if _misses_border(cells):
                    any_missing_border = True
                break
            if not placed:
                ok = False; break
        # The rule only ADDS bbox-border cells; require >=1 motif that is
        # missing a border cell so the output differs from the input.
        if ok and n_placed >= 1 and any_missing_border:
            return g
    raise ValueError("could not realize a layout where the border-paint is visible")


def _misses_border(cells):
    """True if the motif does NOT already cover its full bbox border (so the
    rule's border-paint will add at least one new cell -> visible change)."""
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    have = set(cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r == r0 or r == r1 or c == c0 or c == c1) and (r, c) not in have:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None):
    """>=1 motif and at least one component is missing a bbox-border cell, so
    the rule's border-paint visibly changes the grid. Returns a list of
    violations (empty == pass)."""
    h, w = len(grid), len(grid[0])
    seen = set(); n_obj = 0; any_missing = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            n_obj += 1
            if _misses_border(cells):
                any_missing = True
    msgs = []
    if n_obj < 1:
        msgs.append("no motifs -> blank output")
    if not any_missing:
        msgs.append("every motif already covers its bbox border -> identity")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no bbox borders to paint.
        return g
    if name == "single_cell":
        # 1x1 cells — bbox border is just the cell, rule is no-op.
        g[2][2] = 4; g[5][6] = 5
        return g
    if name == "motifs_touching":
        # Two motifs touching — connected components merge, bbox spans both.
        g[1][1] = 4; g[1][2] = 4; g[2][2] = 4
        g[2][3] = 5; g[3][3] = 5
        return g
    return g
