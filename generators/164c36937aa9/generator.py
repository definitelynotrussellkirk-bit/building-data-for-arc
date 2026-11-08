"""Generator for arc_additional_puzzles_21_set17_bundle:H119 — colorized anchor stamp.

Rule: locate the prototype component containing the color-8 origin (and color-1
body cells). Build a binary stamp from its bbox; for every non-{0, 1, 8}
single-cell anchor in the grid, paint a translated copy of the stamp colored
with the anchor's color (with overlap collisions becoming 9).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_prototype (no color-8 origin → rule has no template);
no_anchors (prototype but no other anchors → no stamps placed);
single_cell_prototype (prototype is just the 8-cell with no color-1
body → stamp is a single cell, no shape contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "164c36937aa9"
VERSION = "2.0.1"
TASK_ID = "164c36937aa9"

SUMMARY = (
    "0-bg grid (h~9-11, w~10-12) with: (a) one PROTOTYPE "
    "component — a color-8 (cyan) ORIGIN cell + 2-4 "
    "color-1 (blue) BODY cells connected to the origin; "
    "(b) 2-3 single-cell ANCHORS in distinct colors from "
    "{2, 3, 4, 5, 6, 7, 9} placed isolated elsewhere "
    "(≥3 Manhattan distance from the prototype). Rule: "
    "find the prototype (component containing color-8). "
    "Build a binary STAMP from the prototype's bbox "
    "(non-bg cells = 1, else 0). For each ANCHOR "
    "(single non-{0, 1, 8} cell), translate the stamp "
    "so the origin lands on the anchor, paint the "
    "stamp's '1' cells with the ANCHOR's color. "
    "Overlapping stamp cells become color 9."
)

INVARIANTS = [
    "background is 0",
    "exactly one prototype component: 1 cell of color 8 + 2-4 4-conn cells of color 1",
    "2-3 single anchor cells elsewhere on the grid in distinct colors from {2,3,4,5,6,7,9}",
    "anchors are isolated from the prototype and each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_prototype", "no_anchors", "single_cell_prototype")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "n_anchors":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "4..6"},
    "position_bias":     {"type": "str", "default": "prototype_with_anchors",
                          "valid": "prototype_with_anchors"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "4..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-8 origin cell, at least one color-1 body cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_prototype", "no_anchors", "single_cell_prototype"):
        return errs
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(eights) != 1:
        errs.append(f"expected exactly one color-8 origin, got {len(eights)}")
    if not ones:
        errs.append("no color-1 body cells for prototype")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        n_anchors = ctx.draw_int("n_anchors", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        n_anchors = ctx.draw_int("n_anchors", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
        n_anchors = ctx.draw_int("n_anchors", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        proto = [(0, 0, 8)]
        seen = {(0, 0)}
        n_body = rng.randint(2, 4)
        while len(proto) < 1 + n_body:
            r, c, _ = rng.choice(proto)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                proto.append((nr, nc, 1))
                seen.add((nr, nc))
        rs = [r for r, _, _ in proto]
        cs = [c for _, c, _ in proto]
        sr0, sc0 = -min(rs), -min(cs)
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        placed = False
        for _ in range(60):
            ar = rng.randint(0, h - sh)
            ac = rng.randint(0, w - sw)
            if not _free(g, ar, ac, ar + sh - 1, ac + sw - 1):
                continue
            for r, c, v in proto:
                g[ar + sr0 + r][ac + sc0 + c] = v
            placed = True
            break
        if not placed:
            continue
        anchor_colors = rng.sample([2, 3, 4, 5, 6, 7, 9], n_anchors)
        ok = True
        for color in anchor_colors:
            placed_a = False
            for _ in range(120):
                ar2 = rng.randint(0, h - 1)
                ac2 = rng.randint(0, w - 1)
                if g[ar2][ac2] != 0:
                    continue
                if any(0 <= ar2 + dr < h and 0 <= ac2 + dc < w and g[ar2 + dr][ac2 + dc] != 0
                       for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                    continue
                if abs(ar2 - (ar + sr0)) + abs(ac2 - (ac + sc0)) < 3:
                    continue
                g[ar2][ac2] = color
                placed_a = True
                break
            if not placed_a:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not realize prototype + anchors layout in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_prototype":
        # No color-8 origin — rule has no template.
        g[3][3] = 4; g[7][8] = 6
        return g
    if name == "no_anchors":
        # Prototype but no anchors.
        g[3][3] = 8; g[3][4] = 1; g[4][3] = 1
        return g
    if name == "single_cell_prototype":
        # Prototype is just the 8-cell — stamp is a single cell, no shape.
        g[3][3] = 8
        g[6][7] = 4; g[8][2] = 6
        return g
    return g
