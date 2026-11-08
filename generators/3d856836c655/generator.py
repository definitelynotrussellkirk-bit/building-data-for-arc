"""Generator for fe9bb13a9b18:S14_M1 -- match a shape by its row-count profile.

Rule: the first color-1 object is the ANCHOR. Among the non-1 objects, find
the first (top-left order) whose row-profile (the list of per-row cell counts
over its bbox) equals the anchor's. Crop that target to its bbox and recolor
it to 8.

This generator draws a color-1 anchor, one non-1 target congruent to it (so
the row-profiles match), and distractor shapes with different row-profiles.

Combinatorial axes: grid size, the anchor/target shape, the distractors,
colors and positions.
Degenerates: anchor_only, two_shapes, single_cell.

NOTE: the output is the cropped target, so its size is bounded; distinct
INPUTS are large and outputs track the target-shape variety.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3d856836c655"
VERSION = "2.2.0"  # exclude target color 8 so recolor branch is visible; avoid solid-bbox target crops; keeps row-profile rule nontrivial
TASK_ID = "3d856836c655"
SUMMARY = (
    "0-bg grid (size varies) with a color-1 anchor, one non-1 target "
    "congruent to it, and distractor shapes with different row-profiles. "
    "Rule: find the non-1 object whose per-row cell-count profile matches the "
    "anchor, crop it, recolor to 8. The grid size, shapes, colors and "
    "positions vary freely (was a fixed setup, ~27 distinct)."
)

INVARIANTS = [
    "exactly one color-1 anchor; exactly one non-1 target shares its row-profile",
    "distractor shapes have row-profiles different from the anchor",
    "the output is the target cropped to its bbox, recolored 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("anchor_only", "two_shapes", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_COLORS = [3, 4, 5, 6, 7, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "13..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "13..24"},
    "shape_size":     {"type": "int", "default": "varies", "valid": "4..9"},
    "n_distract":     {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|anchor_only|two_shapes|single_cell"},
}


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



def _has_bbox_background(cells):
    """True iff the cropped object bbox contains at least one background cell.

    If the chosen anchor/target shape fills its whole bounding box (a line,
    rectangle, or other solid crop), the canonical rule's output becomes a
    single-color field of 8s. Those examples pass parity but teach a degenerate
    crop/recolor shortcut. Keep only shapes with at least one empty bbox cell so
    the answer retains spatial structure.
    """
    h = max(r for r, c in cells) + 1
    w = max(c for r, c in cells) + 1
    return len(set(cells)) < h * w

def _profile(cells):
    rows = {}
    for r, c in cells:
        rows[r] = rows.get(r, 0) + 1
    return tuple(rows[r] for r in range(min(rows), max(rows) + 1))


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, g, occ, shape, color, h, w):
    sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
    if sh > h or sw > w:
        return False
    for _t in range(30):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _reserve(occ, top, left, sh, sw, h, w):
            for (r, c) in shape:
                g[top + r][left + c] = color
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
        hr, wr, dr_, sr = (13, 16), (13, 17), (1, 2), (5, 8)
    elif difficulty == "hard":
        hr, wr, dr_, sr = (18, 24), (18, 24), (3, 4), (7, 11)
    else:
        hr, wr, dr_, sr = (15, 20), (15, 21), (2, 3), (6, 9)

    for _attempt in range(40):
        anchor_shape = _poly(rng, rng.randint(*sr))
        if not _has_bbox_background(anchor_shape):
            continue
        prof = _profile(anchor_shape)
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        if not _place(rng, g, occ, anchor_shape, 1, h, w):
            continue
        # target: same shape (so profile matches), non-1 color
        if not _place(rng, g, occ, anchor_shape, rng.choice(_COLORS), h, w):
            continue
        # distractors with a DIFFERENT row-profile
        nd = rng.randint(*dr_)
        ok = True
        for _ in range(nd):
            placed = False
            for _t in range(20):
                d = _poly(rng, rng.randint(*sr))
                if _profile(d) != prof:
                    if _place(rng, g, occ, d, rng.choice(_COLORS), h, w):
                        placed = True
                    break
            if not placed:
                ok = False; break
        if not ok:
            continue
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = full_grid(h, w, 0)
    anchor = [(0, 0), (1, 0), (1, 1), (2, 1)]
    for (r, c) in anchor:
        g[2 + r][2 + c] = 1
    if name == "anchor_only":
        return g
    for (r, c) in anchor:
        g[7 + r][8 + c] = 4
    if name == "single_cell":
        g[5][12] = 6
    return g



def _same_color_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    comps = _same_color_components(grid)
    anchors = [cells for color, cells in comps if color == 1]
    if len(anchors) != 1:
        errs.append(f"expected exactly one color-1 anchor, saw {len(anchors)}")
        return errs
    anchor_prof = _profile(anchors[0])
    matches = [(color, cells) for color, cells in comps if color != 1 and _profile(cells) == anchor_prof]
    if len(matches) != 1:
        errs.append(f"expected exactly one non-1 target sharing anchor row-profile, saw {len(matches)}")
    elif matches[0][0] == 8:
        errs.append("target already uses output color 8, hiding the recolor branch")
    for color, cells in comps:
        if color != 1 and _profile(cells) != anchor_prof and _profile(cells) == anchor_prof:
            errs.append("unreachable duplicate profile check")
    return errs
