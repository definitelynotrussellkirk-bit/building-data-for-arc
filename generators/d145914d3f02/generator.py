"""Generator for arc_additional_puzzles_21_set18_bundle:M120 — rotated 7-template stamps at anchors.

Rule: a 9-cell defines the origin; nearby 7-cells form the template
(by offset). Each anchor cell with value in {2,3,4,5} stamps 7s at the
template's offsets rotated by the anchor's transform (2=0°, 3=90°,
4=180°, 5=270°).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchors (no stamps to apply → output equals input),
symmetric_template (template invariant under 90° rotations → all 4
anchor codes produce identical stamps), single_anchor (only one
anchor → no rotation contrast across stamps).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d145914d3f02"
VERSION = "2.1.0"  # 2.1.0: constructively place all requested anchors and add self-check.
TASK_ID = "d145914d3f02"
SUMMARY = (
    "0-bg grid (h~11-14, w~12-15) with: (a) "
    "ONE COLOR-9 (maroon) ORIGIN cell at "
    "interior position (nine_r, nine_c) "
    "(within rows 2-4, cols 2-4); (b) 2-3 "
    "COLOR-7 (orange) CELLS placed at fixed "
    "OFFSETS from the origin (one of 4 "
    "templates: small L-shapes / corners). "
    "These define the TEMPLATE; (c) 1-3 single "
    "ANCHOR cells with values from {2, 3, 4, 5} "
    "(the rotation codes: 2=0°, 3=90°, 4=180°, "
    "5=270°), placed at scattered interior "
    "positions with sufficient margin from the "
    "origin and each other so rotated stamps "
    "stay in-bounds. Rule: extract the "
    "TEMPLATE as the color-7 offsets relative "
    "to the COLOR-9 origin. For EACH ANCHOR "
    "cell with rotation code v, ROTATE the "
    "template's offsets by v's rotation "
    "(2=0°, 3=cw90°, 4=180°, 5=ccw90°), then "
    "STAMP COLOR-7 cells at "
    "(anchor + rotated_offset) positions. The "
    "anchor stays, the origin stays, and "
    "original templates stay. Net: each "
    "rotation anchor pulls a rotated copy of "
    "the template into its position in orange."
)

INVARIANTS = [
    "background is 0",
    "exactly one 9-cell (the origin)",
    "2-3 7-cells form a small template adjacent to the 9",
    "1-4 anchor cells with distinct values from {2, 3, 4, 5}",
    "anchors leave room for the rotated template to land in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchors", "symmetric_template", "single_anchor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "n_anchors":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "origin_template_anchors",
                       "valid": "origin_template_anchors"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "3..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TEMPLATES = [
    [(-1, 0), (0, -1)],
    [(-1, 0), (0, -1), (1, 0)],
    [(-1, 0), (0, 1), (1, 0)],
    [(0, 1), (1, 0)],
]


def _rotate_offset(dr, dc, code):
    if code == 2:      # 0 degrees
        return dr, dc
    if code == 3:      # 90 degrees clockwise
        return dc, -dr
    if code == 4:      # 180 degrees
        return -dr, -dc
    if code == 5:      # 270 degrees clockwise / ccw90
        return -dc, dr
    raise ValueError(f"unknown rotation code {code}")


def _stamp_positions(ar, ac, code, template):
    return [(ar + rr, ac + cc) for rr, cc in (_rotate_offset(dr, dc, code) for dr, dc in template)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
        n_anchors = ctx.draw_int("n_anchors", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        w = ctx.draw_int("grid_w", 14, 17)
        n_anchors = ctx.draw_int("n_anchors", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 15)
        n_anchors = ctx.draw_int("n_anchors", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    template = rng.choice(_TEMPLATES)
    nine_r = rng.randint(2, 4)
    nine_c = rng.randint(2, 4)
    g[nine_r][nine_c] = 9
    for dr, dc in template:
        rr = nine_r + dr; cc = nine_c + dc
        if 0 <= rr < h and 0 <= cc < w:
            g[rr][cc] = 7
    anchors = rng.sample([2, 3, 4, 5], n_anchors)
    placed_anchors: list[tuple[int, int]] = []
    for v in anchors:
        candidates = []
        for ar in range(2, h - 2):
            for ac in range(2, w - 2):
                if g[ar][ac] != 0:
                    continue
                if max(abs(ar - nine_r), abs(ac - nine_c)) < 4:
                    continue
                if any(max(abs(ar - pr), abs(ac - pc)) < 3 for pr, pc in placed_anchors):
                    continue
                if all(0 <= rr < h and 0 <= cc < w for rr, cc in _stamp_positions(ar, ac, v, template)):
                    candidates.append((ar, ac))
        if not candidates:
            raise ValueError("could not place requested rotation anchors")
        ar, ac = rng.choice(candidates)
        g[ar][ac] = v
        placed_anchors.append((ar, ac))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    g[3][3] = 9
    for dr, dc in _TEMPLATES[1]:
        g[3 + dr][3 + dc] = 7
    if name == "no_anchors":
        # No anchors — rule's stamp loop is empty; output equals
        # input (just the origin + template).
        return g
    if name == "symmetric_template":
        # Use a 4-fold symmetric template (the 4 cardinal neighbors)
        # so all rotations produce identical output; rule's
        # rotation-by-anchor branch yields no contrast.
        g = full_grid(h, w, 0)
        g[3][3] = 9
        for dr, dc in [(-1, 0), (0, -1), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 7
        g[7][7] = 2
        g[10][3] = 4
        return g
    if name == "single_anchor":
        # Only one anchor — rule applies just one rotation; no
        # cross-anchor contrast in output.
        g[8][8] = 3
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h = len(grid); w = len(grid[0]) if h else 0
    origins = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(origins) != 1:
        return [f"expected exactly one origin 9-cell, got {len(origins)}"]
    nr, nc = origins[0]
    template = [(r - nr, c - nc) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if not (2 <= len(template) <= 3):
        msgs.append(f"template should contain 2..3 orange cells, got {len(template)}")
    if any(max(abs(dr), abs(dc)) != 1 for dr, dc in template):
        msgs.append("template cells should be adjacent offsets around the origin")
    anchors = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] in {2, 3, 4, 5}]
    lo, hi = (1, 1) if difficulty == "easy" else ((3, 4) if difficulty == "hard" else (1, 3))
    if not (lo <= len(anchors) <= hi):
        msgs.append(f"expected {lo}..{hi} rotation anchors, got {len(anchors)}")
    vals = [v for _, _, v in anchors]
    if len(vals) != len(set(vals)):
        msgs.append("anchor rotation codes must be distinct")
    for ar, ac, code in anchors:
        for rr, cc in _stamp_positions(ar, ac, code, template):
            if not (0 <= rr < h and 0 <= cc < w):
                msgs.append("rotated template stamp would leave the grid")
                break
    return msgs
