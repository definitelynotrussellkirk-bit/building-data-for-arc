"""Generator for arc_puzzle_bank_21_set14_s:S14_M6.

Rule: the single largest non-color-1 object is the ANCHOR. Its row-profile
(cell count per row) becomes a left-aligned bar-chart histogram, stamped
in color 8 at the top-left of the color-1 MARKER on a blank grid.

This generator places one anchor (a random shape) and one color-1 marker
where the resulting histogram fits in-bounds.

Combinatorial axes: grid size, the anchor shape/color, and the marker
position.
Degenerates: no_anchor, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "1d8a1c70332a"
VERSION = "2.1.1"  # keep marker-stamped histogram footprint disjoint from the anchor
TASK_ID = "1d8a1c70332a"
SUMMARY = (
    "0-bg grid (size varies). One ANCHOR object (the largest non-color-1 "
    "shape) and one color-1 (blue) MARKER. Rule: build a left-aligned "
    "histogram of the anchor's per-row cell counts and stamp it in color 8 "
    "at the marker on a blank grid. The grid size, anchor shape/color and "
    "marker position vary freely (was a fixed layout, ~27 distinct)."
)

INVARIANTS = [
    "exactly one non-color-1 object (the anchor) and one color-1 marker",
    "the histogram (anchor-height x max-row-count) fits in-bounds at the marker",
    "the entire stamped histogram footprint is disjoint from the anchor in the input",
    "the output is the anchor's row-profile histogram in color 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "anchor_size":    {"type": "int", "default": "varies", "valid": "4..10"},
    "anchor_color":   {"type": "color", "default": "rng !{0,1}", "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "anchor_plus_marker",
                       "valid": "anchor_plus_marker"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_anchor|no_marker|full_grid"},
}

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


def _row_profile(cells):
    rows = max(r for r, c in cells) + 1
    return [sum(1 for r, c in cells if r == i) for i in range(rows)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, sr = (12, 14), (12, 15), (4, 6)
    elif difficulty == "hard":
        hr, wr, sr = (16, 22), (17, 24), (6, 10)
    else:
        hr, wr, sr = (13, 17), (14, 19), (4, 8)

    for _attempt in range(40):
        shape = _poly(rng, rng.randint(*sr))
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
        prof = _row_profile(shape)
        hist_h = len(prof); hist_w = max(1, max(prof))

        h = rng.randint(*hr); w = rng.randint(*wr)
        if sh > h or sw > w or hist_h > h or hist_w > w:
            continue
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        at = rng.randint(0, h - sh); al = rng.randint(0, w - sw)
        cells = [(at + r, al + c) for r, c in shape]
        acolor = rng.randint(2, 9)
        for (r, c) in cells:
            g[r][c] = acolor
            occ[r][c] = True

        done = False
        for _t in range(80):
            mr = rng.randint(0, h - hist_h); mc = rng.randint(0, w - hist_w)
            if not _hist_footprint_clear(occ, mr, mc, prof):
                continue
            g[mr][mc] = 1
            done = True
            break
        if done:
            return g

    return g   # fallback (rare)


def _hist_footprint_clear(occ, r0, c0, profile):
    """True iff the entire output histogram footprint avoids anchor cells.

    The previous marker placement checked only the marker/top-left cell. For
    wide row-profile bars, later cells in the stamped histogram could cover the
    anchor in the INPUT, so the demos simultaneously showed the source object
    occupying cells that the marker-command region would overwrite — hiding the
    intended "stamp a histogram at the marker on a blank grid" rule.
    """
    h = len(occ); w = len(occ[0])
    for dr, count in enumerate(profile):
        for dc in range(count):
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1 marker; at least one non-color-1 non-bg anchor cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    anchor = any(grid[r][c] not in (0, 1) for r in range(h) for c in range(w))
    if c1 != 1:
        errs.append(f"expected exactly 1 color-1 marker, found {c1}")
    if not anchor:
        errs.append("no anchor cells (non-zero, non-1)")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_anchor":
        g[5][5] = 1
        return g
    if name == "no_marker":
        paint_at(g, 2, 2, [(0, 0), (0, 1), (1, 0), (2, 0)], 3)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 3
        g[0][0] = 1
        return g
    return g
