"""Generator for arc_puzzle_bank_21_set14_s:S14_M7 -- column-profile match across panels.

Rule: split the grid into vertical panels by color-5 separator columns.
The anchor is the largest object in panel 0. The target is the first
panel-1 object (top-left order) whose column profile equals the anchor's.
Output = the target's shape rendered in color 8.

This generator puts a single anchor in panel 0 and, in panel 1, one
matching object (same column profile) plus distractors with different
column profiles.

Combinatorial axes: panel sizes, the anchor shape, the distractor
shapes/count, colors, and positions.
Degenerates: no_separator, no_left_anchor, no_right_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "63f1892d0dce"
VERSION = "2.0.1"  # diversity: random anchor + matching target + distractors across panels (was fixed ~21)
TASK_ID = "63f1892d0dce"
SUMMARY = (
    "0-bg grid (size varies) split by a color-5 column into two panels. "
    "Panel 0 holds one ANCHOR object; panel 1 holds one object with the same "
    "column profile plus distractors with different profiles. Rule: output "
    "the matching panel-1 object's shape in color 8. The panel sizes, anchor "
    "shape, distractors, colors and positions vary freely (was a fixed "
    "setup, ~21 distinct)."
)

INVARIANTS = [
    "panel 0 holds a single anchor; a color-5 column separates the panels",
    "exactly one panel-1 object has the anchor's column profile",
    "the output is that matching object's shape in color 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separator", "no_left_anchor", "no_right_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..20"},
    "panel_w":        {"type": "int", "default": "varies", "valid": "5..11"},
    "anchor_size":    {"type": "int", "default": "varies", "valid": "3..7"},
    "n_distractors":  {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "two_panels", "valid": "two_panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_separator|no_left_anchor|no_right_match"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-5 separator column; ≥1 non-{0,5} cell in left panel."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    sep_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not sep_cols:
        errs.append("no full-height color-5 separator column found")
        return errs
    div = sep_cols[0]
    left_cells = [grid[r][c] for r in range(h) for c in range(div)
                  if grid[r][c] not in (0, 5)]
    if not left_cells:
        errs.append("no non-{0,5} anchor object in left panel")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _colprof(cells):
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)
    return [sum(1 for r, c in cells if c == cc) for cc in range(c0, c1 + 1)]


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, g, occ, cells, color, h, c_lo, c_hi):
    sh = max(r for r, c in cells) + 1; sw = max(c for r, c in cells) + 1
    if sw > c_hi - c_lo + 1 or sh > h:
        return False
    for _t in range(50):
        top = rng.randint(0, h - sh); left = rng.randint(c_lo, c_hi - sw + 1)
        if _reserve(occ, top, left, sh, sw, h, len(g[0])):
            paint_at(g, top, left, cells, color)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, pw, asz, ndr = (10, 13), (5, 7), (3, 5), (1, 2)
    elif difficulty == "hard":
        hr, pw, asz, ndr = (15, 20), (7, 11), (5, 7), (2, 3)
    else:
        hr, pw, asz, ndr = (12, 16), (6, 9), (3, 6), (1, 3)

    for _attempt in range(40):
        anchor = _poly(rng, rng.randint(*asz))
        CP = _colprof(anchor)
        h = rng.randint(*hr)
        pw0 = rng.randint(*pw); pw1 = rng.randint(*pw)
        w = pw0 + 1 + pw1
        colors = [c for c in [1, 2, 3, 4, 6, 7, 8, 9]]
        rng.shuffle(colors)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        # separator column
        sepc = pw0
        for r in range(h):
            g[r][sepc] = 5
            occ[r][sepc] = True

        if not _place(rng, g, occ, anchor, colors[0], h, 0, pw0 - 1):
            continue
        # matching target in panel 1 (same shape -> same col profile)
        if not _place(rng, g, occ, anchor, colors[1], h, pw0 + 1, w - 1):
            continue
        # distractors with a DIFFERENT column profile
        ok = True
        nd = rng.randint(*ndr)
        ci = 2
        for _ in range(nd):
            dd = None
            for _t in range(40):
                cand = _poly(rng, rng.randint(3, 6))
                if _colprof(cand) != CP:
                    dd = cand; break
            if dd is None:
                continue
            col = colors[ci % len(colors)]; ci += 1
            _place(rng, g, occ, dd, col, h, pw0 + 1, w - 1)
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 11, 0)
    for r in range(10):
        g[r][5] = 5
    a = [(0, 0), (1, 0), (1, 1)]
    paint_at(g, 1, 1, a, 2)
    if name == "no_separator":
        return full_grid(10, 11, 0)
    if name == "no_left_anchor":
        g2 = full_grid(10, 11, 0)
        for r in range(10):
            g2[r][5] = 5
        paint_at(g2, 1, 7, a, 3)
        return g2
    if name == "no_right_match":
        paint_at(g, 1, 7, [(0, 0), (0, 1), (0, 2)], 3)
        return g
    paint_at(g, 1, 7, a, 3)
    return g
