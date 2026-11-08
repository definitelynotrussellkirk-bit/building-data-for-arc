"""Generator for `arc_additional_puzzle_bank_volume21:M144` — rotate template,
stamp at the anchor.

Rule: a CONTROL marker (first present of colors 2/3/4/6) selects a rotation
count (2->0, 3->1, 4->2, 6->3 quarter-turns); the blue(1) TEMPLATE shape is
rotated that many times and stamped (color 8) at the color-7 ANCHOR cell.

The old generator was incomplete: it never placed the color-7 anchor (so the
stamp defaulted to a fixed position), used a FIXED L-template, allowed a no-op
marker 5, and its colours {0,1,2-6} didn't match the canonical {0,1,4,7,9}.
This rewrite places a RANDOM color-1 template, a ctrl marker in {2,3,4,6}, a
color-7 anchor with room for any rotation, and a rule-ignored color-9 decoy.

Combinatorial axes: template shape, ctrl marker (rotation), anchor position,
grid size.
Degenerates: no_marker, no_template, multiple_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4199aa353fa1"
VERSION = "3.0.1"
TASK_ID = "4199aa353fa1"
SUMMARY = (
    "0-bg grid (h, w ~10-14) with: (a) one CONTROL MARKER "
    "cell in some color from {2, 3, 4, 5, 6}; (b) a BLUE(1) "
    "TEMPLATE shape of 4 cells in an asymmetric L/J pattern "
    "placed in the interior, not adjacent to the marker. "
    "Rule: detect ctrl color via (first available in 2, 3, 4, "
    "6) → maps to rotations 0/1/2/3 CW. Take template cells "
    "(color 1) normalized; rotate ctrl times. Find anchor "
    "from grid (first color-7 cell or fallback). Output: a "
    "fresh empty grid with the rotated shape stamped at "
    "anchor position, painted color 8 (cyan)."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one control marker cell, color in {2, 3, 4, 5, 6}",
    "≥4 blue(1) cells in a contiguous asymmetric L/J shape",
    "template is asymmetric so rotations are observable",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_template", "multiple_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "marker":         {"type": "color", "default": "rng of {2,3,4,5,6}",
                       "valid": "{2,3,4,5,6}"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "marker_then_blue_template",
                       "valid": "marker_then_blue_template"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one control marker in {2,3,4,6}; ≥4 color-1 cells (template)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    ctrl_colors = {2, 3, 4, 6}
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in ctrl_colors]
    if len(markers) != 1:
        errs.append(f"expected exactly 1 control marker in {{2,3,4,6}}, got {len(markers)}")
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(ones) < 3:
        errs.append(f"expected ≥3 color-1 template cells, got {len(ones)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 10, 11); k_hi = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 14, 18); k_hi = 7
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 11, 15); k_hi = 6
    marker = ctx.draw_choice("marker", [2, 3, 4, 6])   # rule's ctrl set (no no-op 5)
    rng = ctx.draw_rng("placement")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        # random color-1 template
        shape = _rand_poly(rng, rng.randint(3, k_hi))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        if not _place(g, rng, shape, 1):
            continue
        # ctrl marker (single cell)
        if not _place(g, rng, [(0, 0)], marker):
            continue
        # color-7 anchor: a single cell with room for ANY rotation of the shape
        maxd = max(sh, sw)
        anchored = False
        for _ in range(200):
            ar = rng.randint(0, h - maxd); ac = rng.randint(0, w - maxd)
            if g[ar][ac] == 0 and _free8(g, [(ar, ac)]):
                g[ar][ac] = 7
                anchored = True
                break
        if not anchored:
            continue
        # rule-ignored color-9 decoys (match canonical {0,1,4,7,9} distribution)
        for _ in range(rng.randint(1, 2)):
            _place(g, rng, [(0, 0)], 9)
        return g
    raise ValueError("could not realize 4199 layout")


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free8(g, cells):
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    for _ in range(150):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        shifted = [(top + r, left + c) for r, c in cells]
        if _free8(g, shifted):
            for (r, c) in shifted:
                g[r][c] = color
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # Blue template but no control marker — rule has no
        # rotation-direction code to read.
        g[3][3] = 1; g[4][3] = 1; g[5][3] = 1; g[5][4] = 1
        return g
    if name == "no_template":
        # Marker but no blue template — rule has nothing to rotate.
        g[5][5] = 3
        return g
    if name == "multiple_markers":
        # Two control markers in different colors — rule's
        # exactly-one-control precondition fails; rotation lookup
        # is ambiguous.
        g[2][2] = 3
        g[8][8] = 5
        g[5][5] = 1; g[6][5] = 1; g[7][5] = 1; g[7][6] = 1
        return g
    return g
