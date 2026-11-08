"""Generator for arc_puzzle_bank_21_set14_bundle:medium_n01 — output crop of the marker-color object.

Rule: the top-left cell holds a target color marker. The output is
the bbox crop of the larger object that shares that color (the
marker itself is excluded as it's a single cell).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (cell (0,0) is bg → rule's marker selector
returns nothing, no target chosen), no_match (marker present but no
multi-cell object shares its color → rule's selector finds nothing
to crop), tied_match (≥2 multi-cell objects share marker color →
"the larger object" is ambiguous, tie-break decides which is cropped).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "b95c3395eaf5"
VERSION = "1.4.0"  # 1.2.0->1.3.0: target object is a RANDOM polyomino (4-8
# cells, varied non-square bbox) instead of a fixed 12-shape bank -> the output
# crop varies far more (out_shapes 5 -> higher). Distractors stay smaller so the
# target remains the unique largest match for its color.
TASK_ID = "b95c3395eaf5"
SUMMARY = "Marker at (0,0) is the target color; rule outputs the cropped bbox of the LARGEST multi-cell object with that color (excluding the singleton marker)."

# Rivals: 'crop the largest object regardless of marker' refuted by ≥2
# demos where the marker color picks a non-largest object. 'use the
# marker color verbatim as output' refuted by any demo (output is a
# crop, not the marker). 'ignore distractors' is implicit but pinned by
# any demo with distractors of different colors. 3 demos with varied
# marker colors and varied target object positions suffice.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "(0, 0) holds the target marker color",
    "exactly one object of the marker's color elsewhere with ≥3 cells",
    "1-2 distractor objects in other colors",
    "objects don't touch each other or (0, 0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_match", "tied_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":            {"type": "int", "default": "rng 10..14", "valid": "9..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "marker_plus_target_plus_distractors",
                          "valid": "marker_plus_target_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TARGET_SHAPES = [
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 2)],
    [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)],
    [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3)],
]
_DISTRACT_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (1, 1)],
]


def _poly(rng, size):
    """Random connected polyomino of `size` cells (BFS grow), normalized."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size:
        if not frontier:
            frontier = list(cells)
        base = rng.choice(frontier)
        nbrs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        rng.shuffle(nbrs)
        grew = False
        for dr, dc in nbrs:
            cand = (base[0] + dr, base[1] + dc)
            if cand not in cells:
                cells.add(cand)
                frontier.append(cand)
                grew = True
                break
        if not grew:
            frontier.remove(base)
    minr = min(r for r, c in cells)
    minc = min(c for r, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n_distractors = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_distractors = rng.randint(3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        n_distractors = rng.randint(2, 3)
    g = full_grid(h, w, 0)
    palette = list(random_palette(rng, n_distractors + 1))
    target = palette[0]
    g[0][0] = target
    placed: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)]
    # Target object: random polyomino (4-8 cells) -> varied non-square crops.
    for _shape_try in range(80):
        target_shape = _poly(rng, rng.randint(4, 8))
        sh = max(c[0] for c in target_shape) + 1
        sw = max(c[1] for c in target_shape) + 1
        if sh <= h - 3 and sw <= w - 3:
            break
    else:
        target_shape = [(0, 0), (0, 1), (1, 0), (1, 1)]
        sh = sw = 2
    placed_target = False
    for _ in range(80):
        r0 = rng.randint(2, h - sh - 1)
        c0 = rng.randint(2, w - sw - 1)
        bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
        if any(bbox_overlaps(bb, p) for p in placed):
            continue
        paint_at(g, r0, c0, target_shape, target)
        placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
        placed_target = True
        break
    if not placed_target:
        r0, c0 = 2, 2
        paint_at(g, r0, c0, target_shape, target)
        placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
    for color in palette[1:]:
        ds = rng.choice(_DISTRACT_SHAPES)
        dh = max(c[0] for c in ds) + 1
        dw = max(c[1] for c in ds) + 1
        if dh > h - 3 or dw > w - 3:
            ds = [(0, 0)]; dh = dw = 1
        placed_distractor = False
        for _ in range(80):
            r0 = rng.randint(2, h - dh - 1)
            c0 = rng.randint(2, w - dw - 1)
            bb = (r0 - 1, c0 - 1, r0 + dh, c0 + dw)
            if any(bbox_overlaps(bb, p) for p in placed):
                continue
            paint_at(g, r0, c0, ds, color)
            placed.append((r0, c0, r0 + dh - 1, c0 + dw - 1))
            placed_distractor = True
            break
        if not placed_distractor:
            for r0 in range(2, h - dh):
                if placed_distractor:
                    break
                for c0 in range(2, w - dw):
                    bb = (r0 - 1, c0 - 1, r0 + dh, c0 + dw)
                    if any(bbox_overlaps(bb, p) for p in placed):
                        continue
                    paint_at(g, r0, c0, ds, color)
                    placed.append((r0, c0, r0 + dh - 1, c0 + dw - 1))
                    placed_distractor = True
                    break
    if self_check(g, difficulty=difficulty):
        # Very crowded easy layouts could still leave the marked target missing
        # or fail to place any distractor. Use a compact constructive fallback.
        g = full_grid(h, w, 0)
        g[0][0] = target
        target_shape = [(0, 0), (0, 1), (1, 0), (2, 0)]
        paint_at(g, 2, 2, target_shape, target)
        slots = [(2, max(5, w - 4)), (max(5, h - 4), 2), (max(5, h - 4), max(5, w - 4))]
        for color, (r0, c0) in zip(palette[1:], slots):
            if r0 + 1 < h - 1 and c0 + 1 < w - 1:
                paint_at(g, r0, c0, [(0, 0), (0, 1), (1, 1)], color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # (0,0) is bg — rule's marker selector returns nothing.
        for dr, dc in [(0, 0), (0, 1), (1, 1)]:
            g[3 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (1, 0)]:
            g[6 + dr][7 + dc] = 6
        return g
    if name == "no_match":
        # Marker present but no multi-cell object shares its color.
        g[0][0] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 6
        for dr, dc in [(0, 0), (1, 0)]:
            g[6 + dr][7 + dc] = 8
        return g
    if name == "tied_match":
        # Two multi-cell objects share marker color — "the larger
        # object" is ambiguous; tie-break decides.
        g[0][0] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[6 + dr][7 + dc] = 4
        return g
    return g

def _self_components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]:
        return ["empty grid"]
    msgs = []
    marker = grid[0][0]
    if marker == 0:
        msgs.append("top-left marker must be nonzero")
    comps = [(v, cells) for v, cells in _self_components(grid)
             if not (len(cells) == 1 and cells[0] == (0, 0))]
    target_comps = [cells for v, cells in comps if v == marker and len(cells) >= 3]
    if len(target_comps) != 1:
        msgs.append(f"expected exactly one multi-cell target object in marker color, got {len(target_comps)}")
    if not any(v != marker for v, _ in comps):
        msgs.append("expected at least one distractor object in another color")
    return msgs
