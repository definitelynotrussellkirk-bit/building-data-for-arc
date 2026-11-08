"""Generator for arc_puzzle_bank_twelfth21:H78 — rotate panel 3 into panel 4.

Rule (verified): the grid is several SQUARE panels separated by full color-9
columns. The rule takes the 3rd panel (index 2), rotates it CW, and overlays it
onto the 4th panel (index 3); everything else is unchanged. Panels MUST be
square so the CW rotation fits the target slot cleanly (canonical uses 5x5).

Combinatorial axes: panel side (square), n_panels, motif content, colors.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e80a3d8b2591"
VERSION = "2.1.0"  # panels were panel_w=4 x panel_h(4-5) -> NON-SQUARE when h=5 -> CW rotation (4x5) clipped in the 4-wide target slot. Rule rotates panel3 into panel4 -> panels MUST be square. Now square panels; doc fixed (was 'find pair')
TASK_ID = "e80a3d8b2591"

SUMMARY = (
    ">=4 SQUARE panels (side s) separated by single full color-9 columns, each "
    "with a small motif in a non-{0,9} color. Rule: rotate the 3rd panel CW and "
    "overlay it onto the 4th panel; the rest is unchanged. Panels are square so "
    "the rotation fits the target cleanly. Panel side, count, motifs and colors vary."
)

INVARIANTS = [
    "background is 0",
    "panels are SQUARE (side == panel height) so CW rotation fits the target slot",
    ">=4 panels separated by single full color-9 columns",
    "the 3rd panel has a motif (so the rotation/overlay is non-trivial)",
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
    if difficulty == "easy":
        side = ctx.draw_int("panel_side", 3, 4)
        n_req = ctx.draw_int("n_panels", 4, 5)
    elif difficulty == "hard":
        side = ctx.draw_int("panel_side", 5, 6)
        n_req = ctx.draw_int("n_panels", 4, 6)
    else:
        side = ctx.draw_int("panel_side", 4, 5)
        n_req = ctx.draw_int("n_panels", 4, 5)
    rng = ctx.draw_rng("layout")

    panel_w = h = side                       # SQUARE panels -> CW rotation fits
    max_n = (30 + 1) // (side + 1)           # total width = side*n + (n-1) <= 30
    n = max(4, min(n_req, max_n))            # rule needs >=4 panels (uses panels 2 & 3)
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = k * (panel_w + 1) - 1
        for r in range(h):
            g[r][c] = 9
    for k in range(n):
        c0 = k * (panel_w + 1)
        cells = _build_motif(rng, rng.randint(1, min(4, side * side - 1)))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        if sh > h or sw > panel_w:
            continue
        color = rng.choice([2, 3, 4, 5, 6, 7])
        for r, c in cells:
            g[r - min(rs)][c0 + c - min(cs)] = color
    third_c0 = 2 * (panel_w + 1)
    if not any(g[r][c] not in (0, 9) for r in range(h) for c in range(third_c0, third_c0 + panel_w)):
        # The rule specifically rotates panel index 2 into panel index 3; if
        # random motif placement skipped panel 3, the example becomes a no-op.
        g[0][third_c0] = rng.choice([2, 3, 4, 5, 6, 7])
    return g


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


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the square panel/divider structure for e80a3d8b2591."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    divider_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not divider_cols:
        errs.append("no full color-9 divider columns")
        return errs
    for a, b in zip(divider_cols, divider_cols[1:]):
        if b == a + 1:
            errs.append("adjacent divider columns merge panel separators")

    starts = [0] + [c + 1 for c in divider_cols]
    stops = divider_cols + [w]
    panel_widths = [b - a for a, b in zip(starts, stops)]
    if len(panel_widths) < 4:
        errs.append(f"expected at least 4 panels, got {len(panel_widths)}")
    if any(width <= 0 for width in panel_widths):
        errs.append(f"empty panel width in {panel_widths}")
    if len(set(panel_widths)) != 1:
        errs.append(f"panel widths differ: {panel_widths}")
    elif panel_widths[0] != h:
        errs.append(f"panels must be square: height {h}, width {panel_widths[0]}")

    for a, b in zip(starts, stops):
        for r in range(h):
            for c in range(a, b):
                if grid[r][c] == 9:
                    errs.append("color 9 appears inside a panel body")
                    return errs
    if len(panel_widths) >= 4 and len(set(panel_widths)) == 1:
        side = panel_widths[0]
        third_c0 = starts[2]
        if not any(grid[r][c] not in (0, 9) for r in range(h) for c in range(third_c0, third_c0 + side)):
            errs.append("third panel is empty; rotate-into-fourth branch is hidden")
    return errs
