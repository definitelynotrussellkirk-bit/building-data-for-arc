"""Generator for arc_additional_puzzle_bank_volume6:H40.

Rule: row 0 holds a selector color in 2..7; find the frame of that color,
take its interior empty (hole) cells, normalize them, and stamp them in
color 8 with the shape's top-left at the color-9 anchor (on a blank grid).

Combinatorial axes: grid size, selector color, the frame's interior hole
shape, the anchor position, and the decoy frame(s).
Degenerates: no_selector, no_matching_frame, no_anchor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, fill_box, full_grid
from puzzle_generators.helpers.selfcheck import components, interior_cells

GENERATOR_ID = "67b26807f98e"
VERSION = "3.1.0"  # respect selector_color override; fail closed; self_check verifies matching frame hole
TASK_ID = "67b26807f98e"
SUMMARY = (
    "0-bg grid (size varies). ROW 0 holds a SELECTOR color in 2..7. A "
    "FRAME of that color (a rectangular border) encloses a HOLE SHAPE "
    "(its interior empty cells; the rest of the interior is filled with "
    "the frame color). A color-9 ANCHOR sits where the stamp fits, plus "
    "1-2 DECOY frames of other colors. Rule: read the selector, find the "
    "matching frame, take its interior hole cells (normalized), and stamp "
    "them in COLOR 8 (cyan) with the shape's top-left at the anchor, on a "
    "blank grid. The grid size, selector color, the hole shape, the "
    "anchor and the decoys all vary freely, so the output (the stamped "
    "hole shape) varies too (was a fixed layout)."
)

INVARIANTS = [
    "row 0 has a selector color in 2..7",
    "the matching frame encloses a non-empty hole shape",
    "a color-9 anchor where the stamp fits in-bounds",
    "decoy frames are other colors",
]

PALETTE_KINDS = ("default", "selector_2", "selector_3", "selector_mid")
DEGENERATE_TEXTURES = ("no_selector", "no_matching_frame", "no_anchor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "13..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|selector_2|selector_3|selector_mid"},
    "selector_color": {"type": "int", "default": "rng 2..7", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "frame_kind":     {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|selector_2|selector_3|selector_mid|no_selector|no_matching_frame|no_anchor"},
}


def _hole_shape(rng, ih, iw):
    """A connected polyomino within an ih x iw interior, leaving >=1 cell
    filled (so it's a hole, not the whole interior)."""
    interior = [(r, c) for r in range(ih) for c in range(iw)]
    size = rng.randint(1, max(1, ih * iw - 1))
    for _ in range(60):
        cells = {rng.choice(interior)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            nb = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= r + dr < ih and 0 <= c + dc < iw]
            cells.add(rng.choice(nb))
        if len(cells) < ih * iw:
            return list(cells)
    return [(0, 0)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify selector, matching frame-with-hole, and an in-bounds anchor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    selector_cells = [(0, c, grid[0][c]) for c in range(w) if 2 <= grid[0][c] <= 7]
    if len(selector_cells) != 1:
        errs.append(f"row 0 should contain exactly one selector color 2..7, got {len(selector_cells)}")
        return errs
    selector = selector_cells[0][2]
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        errs.append(f"expected exactly one color-9 anchor, got {len(anchors)}")
    frame_comps = []
    for comp in components(grid, colors={selector}, same_color=True):
        # Ignore the selector strip singleton; the matching frame/fill component
        # has a >=4x4 bbox and at least one empty interior hole cell.
        r1, c1, r2, c2 = comp["bbox"]
        if r1 == 0:
            continue
        if r2 - r1 + 1 >= 4 and c2 - c1 + 1 >= 4:
            holes = [(r, c) for r, c in interior_cells(comp["bbox"]) if grid[r][c] == 0]
            if holes:
                frame_comps.append((comp, holes))
    if len(frame_comps) != 1:
        errs.append(f"expected exactly one matching selector-colored frame with a hole, got {len(frame_comps)}")
    elif anchors:
        holes = frame_comps[0][1]
        mr = min(r for r, _ in holes); mc = min(c for _, c in holes)
        sh = max(r - mr for r, _ in holes) + 1
        sw = max(c - mc for _, c in holes) + 1
        ar, ac = anchors[0]
        if ar + sh > h or ac + sw > w:
            errs.append("anchor lacks room for normalized hole stamp")
    return errs


def _reserve(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def _draw_frame_with_hole(g, top, left, fh, fw, color, hole):
    draw_frame(g, top, left, top + fh - 1, left + fw - 1, color)
    holeset = set(hole)
    for r in range(fh - 2):
        for c in range(fw - 2):
            if (r, c) not in holeset:
                g[top + 1 + r][left + 1 + c] = color   # fill non-hole interior


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nd, fmax = (11, 13), (13, 15), 1, 5
    elif difficulty == "hard":
        hr, wr, nd, fmax = (15, 20), (16, 20), 2, 6
    else:
        hr, wr, nd, fmax = (12, 15), (14, 17), rng.randint(1, 2), 6

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        for c in range(w):
            occ[0][c] = True                  # reserve row 0 (selector strip)
        g = full_grid(h, w, 0)

        if "selector_color" in overrides:
            sel = max(2, min(7, int(overrides["selector_color"])))
            decoy_pool = [c for c in range(2, 8) if c != sel]
            rng.shuffle(decoy_pool)
            cols = [sel] + decoy_pool[:nd]
        else:
            cols = rng.sample(range(2, 8), nd + 1)
            sel = cols[0]
        # selector cell in row 0
        g[0][rng.randint(0, w - 1)] = sel

        # matching frame with a hole shape
        fh = rng.randint(4, min(fmax, h - 1)); fw = rng.randint(4, min(fmax, w))
        hole = _hole_shape(rng, fh - 2, fw - 2)
        placed = False
        for _t in range(40):
            top = rng.randint(1, h - fh); left = rng.randint(0, w - fw)
            if _reserve(occ, top, left, fh, fw, h, w):
                _draw_frame_with_hole(g, top, left, fh, fw, sel, hole)
                placed = True
                break
        if not placed:
            continue
        # normalized hole shape (for anchor placement)
        mr = min(r for r, c in hole); mc = min(c for r, c in hole)
        shape = [(r - mr, c - mc) for r, c in hole]
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1

        # decoy frames (other colors)
        for dcol in cols[1:]:
            dfh = rng.randint(4, min(fmax, h - 1)); dfw = rng.randint(4, min(fmax, w))
            for _t in range(20):
                dt = rng.randint(1, h - dfh); dl = rng.randint(0, w - dfw)
                if _reserve(occ, dt, dl, dfh, dfw, h, w):
                    _draw_frame_with_hole(g, dt, dl, dfh, dfw, dcol,
                                          _hole_shape(rng, dfh - 2, dfw - 2))
                    break

        # anchor (color 9) where the stamp fits in-bounds, on a free cell.
        anchor_ok = False
        for _t in range(60):
            ar = rng.randint(0, h - sh); ac = rng.randint(0, w - sw)
            if not occ[ar][ac]:
                g[ar][ac] = 9
                anchor_ok = True
                break
        if not anchor_ok:
            continue
        return g

    raise ValueError("could not realize selector-frame/anchor layout")


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_selector":
        draw_frame(g, 2, 1, 5, 4, 2); fill_box(g, h - 4, 3, h - 2, 5, 4); g[8][12] = 9
        return g
    if name == "no_matching_frame":
        g[0][1] = 2; fill_box(g, 2, 1, 6, 4, 2); draw_frame(g, h - 5, 6, h - 2, 9, 4); g[8][12] = 9
        return g
    if name == "no_anchor":
        g[0][1] = 2; draw_frame(g, 2, 1, 5, 4, 2); fill_box(g, h - 4, 3, h - 2, 5, 4)
        return g
    return g
