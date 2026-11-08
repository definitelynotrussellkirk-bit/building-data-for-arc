"""Generator for b3010fe075b7.

Rule: a small template panel and a board panel are separated by one full
color-9 column. The board contains several recolored copies of the template;
the canonical rule marks every board location that matches the template under a
one-to-one color bijection.

Combinatorial axes: template size/cells, board size, copy count, copy
positions, color bijections, difficulty.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b3010fe075b7"
VERSION = "2.0.1"  # cap template cells to available colors; require at least two real board matches; add executable invariants.
TASK_ID = "b3010fe075b7"

SUMMARY = "Template panel and board panel separated by a full color-9 column; board contains recolored template copies."

INVARIANTS = [
    "background is 0",
    "exactly one full color-9 divider column separates template and board",
    "template has 2-7 nonzero cells, enough for a one-to-one color bijection",
    "board contains at least two recolored template matches",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "n_panels":       {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 1..3", "valid": "1..4"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # Rule: split on full color-9 columns. panel[0] = a small TEMPLATE (its
    # nonzero crop); panel[1] = a BOARD; find every place the template matches
    # the board under a COLOR BIJECTION; output board-size with 8 at each match
    # center. v1.x made N independent tiny motifs with no template/copy
    # relationship -> matches were accidental -> distinct 20. Now: build a real
    # template + a board containing K recolored copies of it.
    if difficulty == "easy":
        bw_lo, bw_hi, k_lo, k_hi = 8, 11, 2, 3
    elif difficulty == "hard":
        bw_lo, bw_hi, k_lo, k_hi = 14, 20, 4, 6
    else:
        bw_lo, bw_hi, k_lo, k_hi = 10, 16, 2, 5
    rng = ctx.draw_rng("layout")

    # --- template + board.  The rule uses a one-to-one color bijection, so a
    # template cannot have more distinct-colored cells than the seven available
    # non-{0,9} colors.  v2.0.0 sampled up to 3x3=9 cells and crashed about 11%
    # of default seed/sample_index pairs with ValueError from random.sample().
    for _layout_attempt in range(80):
        tH = rng.randint(2, 3)
        tW = rng.randint(2, 3)
        allcells = [(r, c) for r in range(tH) for c in range(tW)]
        k = rng.randint(2, min(len(allcells), 7))
        tcells = rng.sample(allcells, k)
        rmin = min(r for r, _ in tcells); cmin = min(c for _, c in tcells)
        tcells = [(r - rmin, c - cmin) for r, c in tcells]
        tH = max(r for r, _ in tcells) + 1
        tW = max(c for _, c in tcells) + 1
        base_colors = rng.sample([2, 3, 4, 5, 6, 7, 8], len(tcells))
        tmpl = {cell: col for cell, col in zip(tcells, base_colors)}

        bw = rng.randint(bw_lo, bw_hi)
        h = rng.randint(max(tH + 1, 7), 14)
        w = tW + 1 + bw
        g = full_grid(h, w, 0)

        # panel 0: the template, placed at a random row in its own tW-wide column
        tr = rng.randint(0, h - tH)
        for (r, c), col in tmpl.items():
            g[tr + r][c] = col
        sep = tW
        for r in range(h):
            g[r][sep] = 9                               # full-9 divider

        # panel 1 (board): recolored copies of the template, well separated.
        board0 = sep + 1
        n_copies = rng.randint(k_lo, k_hi)
        placed = []
        for _ in range(n_copies * 35):
            if len(placed) >= n_copies:
                break
            br = rng.randint(0, h - tH)
            bc = rng.randint(0, bw - tW)
            if any(abs(br - pr) < tH + 1 and abs(bc - pc) < tW + 1 for pr, pc in placed):
                continue
            perm = rng.sample([2, 3, 4, 5, 6, 7, 8], len(tcells))
            cmap = {col: perm[i] for i, col in enumerate(base_colors)}
            for (r, c), col in tmpl.items():
                g[br + r][board0 + bc + c] = cmap[col]
            placed.append((br, bc))
        if len(placed) >= 2:
            return g

    # Non-crashing fallback that still teaches the intended template-match rule.
    h, w, tW = 7, 10, 2
    g = full_grid(h, w, 0)
    g[2][0] = 2; g[2][1] = 3
    sep = tW
    for r in range(h):
        g[r][sep] = 9
    board0 = sep + 1
    for br, bc, cols in [(1, 0, (4, 5)), (4, 4, (6, 7))]:
        g[br][board0 + bc] = cols[0]
        g[br][board0 + bc + 1] = cols[1]
    return g


def _split_on_full_9_cols(grid):
    h, w = len(grid), len(grid[0])
    full9 = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not full9:
        return [], []
    panels = []
    start = 0
    for c in full9:
        if start < c:
            panels.append([row[start:c] for row in grid])
        start = c + 1
    if start < w:
        panels.append([row[start:] for row in grid])
    return panels, full9


def _crop_nonzero_non9(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    if not cells:
        return []
    r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _pattern_ok(board, template, r0, c0):
    fwd = {}
    rev = {}
    for r, row in enumerate(template):
        for c, tv in enumerate(row):
            bv = board[r0 + r][c0 + c]
            if tv == 0:
                if bv != 0:
                    return False
                continue
            if bv == 0:
                return False
            if tv in fwd and fwd[tv] != bv:
                return False
            if bv in rev and rev[bv] != tv:
                return False
            fwd[tv] = bv
            rev[bv] = tv
    return True


def _match_count(board, template):
    if not board or not template:
        return 0
    bh, bw = len(board), len(board[0])
    th, tw = len(template), len(template[0])
    if th > bh or tw > bw:
        return 0
    return sum(1 for r in range(bh - th + 1) for c in range(bw - tw + 1)
               if _pattern_ok(board, template, r, c))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    vals = {v for row in grid for v in row}
    if not vals <= set(range(10)):
        errors.append(f"unexpected colors: {sorted(vals - set(range(10)))}")
    panels, full9 = _split_on_full_9_cols(grid)
    if len(full9) != 1 or len(panels) != 2:
        errors.append(f"expected exactly one full-9 divider and two panels, got dividers={full9} panels={len(panels)}")
        return errors
    template = _crop_nonzero_non9(panels[0])
    if not template:
        errors.append("missing nonzero template cells in the first panel")
        return errors
    tcolors = [v for row in template for v in row if v != 0]
    if not (2 <= len(tcolors) <= 7):
        errors.append(f"template should have 2..7 colored cells, found {len(tcolors)}")
    if len(tcolors) != len(set(tcolors)):
        errors.append("template colors must be distinct so the color bijection is unambiguous")
    matches = _match_count(panels[1], template)
    if matches < 2:
        errors.append(f"board should contain at least two recolored template matches, found {matches}")
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
