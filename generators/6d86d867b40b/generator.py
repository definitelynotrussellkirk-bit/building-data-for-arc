"""Generator for arc_puzzle_bank_21_more:medium_b06 — Crop quadrant by corner marker.

Rule: body = grid[1..h-2, 1..w-2] (the interior, border stripped). Find
which grid CORNER holds a non-zero marker (scanning TL, TR, BL, BR) and
output the matching QUADRANT of the body (split at bh//2, bw//2).

Combinatorial axes: grid size, which corner is marked, the marker color,
the four quadrant base colors, and the scattered accent cells.
Degenerates: no_marker, multiple_corners, blank_body.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d86d867b40b"
VERSION = "2.1.0"  # shrink toward canonical 6x6 (fix area drift ~156->~50) + force a contrasting accent into the MARKED quadrant (was solid-quadrant output)
TASK_ID = "6d86d867b40b"
SUMMARY = (
    "0-bg grid (size varies) with a 1-cell border. ONE grid CORNER holds a "
    "non-zero marker; the interior BODY (border stripped) is painted as "
    "four distinct-colored QUADRANTS (split at the body's midlines) plus a "
    "few scattered accent cells. Rule: read which corner is marked (TL/TR/"
    "BL/BR) and output that quadrant of the body. The grid size, the marked "
    "corner, the marker color, the four quadrant colors and the accents all "
    "vary freely (was a fixed deterministic counter body, ~13 distinct)."
)

INVARIANTS = [
    "exactly one grid corner cell is non-zero (the marker)",
    "the other three corners are 0",
    "the interior body has four visually distinct quadrants",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "multiple_corners", "blank_body")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "corner":         {"type": "int", "default": "varies", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "5..9"},
    "position_bias":  {"type": "str", "default": "frame_with_corner",
                       "valid": "frame_with_corner"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "5..9"},
    "density":        {"type": "str", "default": "dense", "valid": "dense"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "no_marker|multiple_corners|blank_body"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # Sizes kept close to the canonical 6x6 (output quadrant = (h-2)//2 squared).
    if difficulty == "easy":
        hr, wr, ar = (6, 7), (6, 7), (1, 3)
    elif difficulty == "hard":
        hr, wr, ar = (9, 12), (9, 12), (3, 6)
    else:
        hr, wr, ar = (6, 9), (6, 9), (2, 4)

    h = rng.randint(*hr); w = rng.randint(*wr)
    g = full_grid(h, w, 0)
    bh = h - 2; bw = w - 2
    hh = bh // 2; hw = bw // 2

    # four distinct quadrant base colors
    q_tl, q_tr, q_bl, q_br = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)

    def paint(r0, r1, c0, c1, color):
        for r in range(r0, r1):
            for c in range(c0, c1):
                g[1 + r][1 + c] = color

    paint(0, hh, 0, hw, q_tl)          # body TL  rows 0..hh-1, cols 0..hw-1
    paint(0, hh, hw, bw, q_tr)         # body TR  rows 0..hh-1, cols hw..bw-1
    paint(hh, bh, 0, hw, q_bl)         # body BL  rows hh..bh-1, cols 0..hw-1
    paint(hh, bh, hw, bw, q_br)        # body BR  rows hh..bh-1, cols hw..bw-1

    # scatter a few accent cells (different color from the local quadrant)
    for _ in range(rng.randint(*ar)):
        br = rng.randint(0, bh - 1); bc = rng.randint(0, bw - 1)
        cur = g[1 + br][1 + bc]
        accent = rng.choice([x for x in range(1, 10) if x != cur])
        g[1 + br][1 + bc] = accent

    # one corner marker — choose the corner FIRST so we can guarantee its quadrant
    # (the one that becomes the OUTPUT) is non-uniform: a solid quadrant -> solid output.
    corner_idx = rng.randint(0, 3)
    # body-coordinate bounds of the selected quadrant
    rr = (0, hh) if corner_idx in (0, 1) else (hh, bh)
    cc_ = (0, hw) if corner_idx in (0, 2) else (hw, bw)
    qcells = [(r, c) for r in range(rr[0], rr[1]) for c in range(cc_[0], cc_[1])]
    if len(qcells) >= 2:
        # force TWO distinct colors into the marked quadrant so the extracted output
        # is never solid (setting a single 'accent != current value' could coincide
        # with the quadrant base after a prior scatter and stay uniform).
        rng.shuffle(qcells)
        a, b = rng.sample(range(1, 10), 2)
        (r0, c0), (r1, c1) = qcells[0], qcells[1]
        g[1 + r0][1 + c0] = a
        g[1 + r1][1 + c1] = b
    cr, cc = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)][corner_idx]
    g[cr][cc] = rng.randint(1, 9)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one non-zero grid corner (the marker), and the body quadrant that
    corner selects must be non-uniform so the extracted output is not solid."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    marked = [i for i, (r, c) in enumerate(corners) if grid[r][c] != 0]
    if len(marked) != 1:
        errs.append(f"expected exactly one marked corner, got {len(marked)}")
        return errs
    ci = marked[0]
    bh = h - 2; bw = w - 2
    hh = bh // 2; hw = bw // 2
    rr = (0, hh) if ci in (0, 1) else (hh, bh)
    cc = (0, hw) if ci in (0, 2) else (hw, bw)
    vals = {grid[1 + r][1 + c] for r in range(rr[0], rr[1]) for c in range(cc[0], cc[1])}
    if len(vals) < 2:
        errs.append("marked quadrant is uniform -> extracted output would be solid")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    for r in range(h - 2):
        for c in range(w - 2):
            g[1 + r][1 + c] = ((r * (w - 2) + c) % 8) + 1
    if name == "no_marker":
        return g                       # body present, no corner marker
    if name == "multiple_corners":
        g[0][0] = 9; g[h - 1][w - 1] = 9
        return g
    if name == "blank_body":
        blank = full_grid(h, w, 0)     # marker only, blank body
        blank[0][0] = 9
        return blank
    return g
