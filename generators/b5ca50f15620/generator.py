"""Generator for arc_additional_puzzles_21_set5:H34.

Rule: the 3x3 TEMPLATE is the upper-left subgrid (0,0)-(2,2). For each
non-zero ANCHOR cell outside the template region, stamp the template
centered on the anchor — each template 9-cell becomes the anchor's
color, other non-zero template cells keep their value, and only empty
(0) target cells are painted. Anchors and the template stay.

Combinatorial axes: grid size, the template pattern, and the anchors'
count / positions / colors.
Degenerates: no_template, no_anchors, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b5ca50f15620"
VERSION = "3.0.1"
TASK_ID = "b5ca50f15620"
SUMMARY = (
    "0-bg grid (size varies) with a 3x3 TEMPLATE in the upper-left "
    "(values 0/7/9, center 0) and 1-4 ANCHOR cells elsewhere (distinct "
    "colors from {1..6,8}), each with a clear 3x3 footprint. Rule: for "
    "each anchor, stamp the template centered on it — template 9-cells "
    "become the anchor's color, 7-cells stay 7, only empty cells are "
    "painted. The grid size, the template pattern, and the anchors' "
    "count/positions/colors all vary freely (was a fixed X-template + 2 "
    "fixed anchors, ~9 distinct)."
)

INVARIANTS = [
    "a 3x3 template (values 0/7/9, center 0) sits at the upper-left",
    "1-4 anchor cells outside the template region, distinct non-{0,7,9} colors",
    "each anchor's 3x3 stamp footprint is clear (no overlap with template/others)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_anchors", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_ANCHOR_COLORS = (1, 2, 3, 4, 5, 6, 8)

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "true", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "3..5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_template|no_anchors|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; when a template exists, upper-left 3x3 has values in {0,7,9} with center=0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h < 3 or w < 3:
        return []
    tpl_vals = {grid[r][c] for r in range(3) for c in range(3)}
    # full_grid degenerate: uniform single non-zero value → skip template checks
    if len(tpl_vals) == 1 and 0 not in tpl_vals:
        return []
    if tpl_vals & {7, 9}:
        if grid[1][1] != 0:
            return [f"template center (1,1)={grid[1][1]}, expected 0"]
        bad = [grid[r][c] for r in range(3) for c in range(3) if grid[r][c] not in (0, 7, 9)]
        if bad:
            return [f"template region has non-{{0,7,9}} values: {bad}"]
    return []


def _make_template(rng):
    """3x3 of {0,7,9}, center 0, with >=3 non-zero cells (a real stencil)."""
    positions = [(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)]
    for _ in range(40):
        tpl = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for (r, c) in positions:
            tpl[r][c] = rng.choice([0, 7, 9])
        nonzero = sum(1 for r, c in positions if tpl[r][c])
        has9 = any(tpl[r][c] == 9 for r, c in positions)
        if nonzero >= 3 and has9:   # >=3 marks and >=1 anchor-colored mark
            return tpl
    return [[7, 9, 7], [9, 0, 9], [7, 9, 7]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nar = (9, 11), (11, 13), (1, 2)
    elif difficulty == "hard":
        hr, wr, nar = (12, 16), (13, 18), (3, 4)
    else:
        hr, wr, nar = (10, 14), (12, 16), (2, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        tpl = _make_template(rng)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        # draw template + reserve its region (incl a 1-cell margin)
        for r in range(3):
            for c in range(3):
                if tpl[r][c]:
                    g[r][c] = tpl[r][c]
        for r in range(0, 4):
            for c in range(0, 4):
                if r < h and c < w:
                    occ[r][c] = True

        n_anchor = rng.randint(*nar)
        colors = rng.sample(_ANCHOR_COLORS, min(n_anchor, len(_ANCHOR_COLORS)))
        placed = 0
        for k in colors:
            for _t in range(40):
                ar = rng.randint(1, h - 2); ac = rng.randint(1, w - 2)
                # 3x3 footprint clear (anchor + its stamp), with 1-cell margin
                foot = [(ar + dr, ac + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
                ok = True
                for (fr, fc) in foot:
                    for mr in (-1, 0, 1):
                        for mc in (-1, 0, 1):
                            rr, cc = fr + mr, fc + mc
                            if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                                ok = False
                if not ok:
                    continue
                g[ar][ac] = k
                for (fr, fc) in foot:
                    occ[fr][fc] = True
                placed += 1
                break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_template":
        g[5][5] = 2
        g[7][8] = 4
        return g
    if name == "no_anchors":
        g[0][0] = 7; g[0][1] = 9; g[0][2] = 7
        g[1][0] = 9; g[1][2] = 9
        g[2][0] = 7; g[2][1] = 9; g[2][2] = 7
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 7
        return g
    return g
