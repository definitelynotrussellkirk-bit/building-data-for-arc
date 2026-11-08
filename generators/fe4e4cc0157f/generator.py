"""Generator for arc_additional_puzzles_21_set16_bundle:M110 — pick the object with the most interior holes.

Rule: count interior holes per object (using bbox padded by 1; holes
are bg components not touching the padded border). Pick the object
with the most holes (tiebreakers: size DESC, then top-row, then
left-col). Output is its bbox crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects (no shapes → rule has nothing to pick);
all_solid (every object has 0 holes → primary key collapses, rule
falls through to size/position tiebreakers); single_object (only 1
→ trivial pick, no contrast in selection).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "fe4e4cc0157f"
VERSION = "2.1.0"  # procedural punched-rect shapes with controlled distinct hole counts (was 3 fixed winner shapes -> out_shapes 3); more objects/colors/sizes
TASK_ID = "fe4e4cc0157f"
SUMMARY = (
    "0-bg grid with 2-5 4-connected non-bg objects, each a "
    "distinct color and a DISTINCT number of interior holes "
    "(so the most-holes pick is unambiguous). Objects are "
    "solid rectangles of varied size with k single-cell "
    "interior holes punched (each hole fully enclosed and "
    "separated so it is its own bg component). Objects are "
    "non-touching. Rule: count each object's interior holes "
    "(bg components inside the bbox padded by 1 that don't "
    "touch the padded border); pick the object with the MOST "
    "holes (tiebreak size DESC, then top-row, then left-col) "
    "and OUTPUT its bbox crop."
)

INVARIANTS = [
    "background is 0",
    "2-5 4-connected non-bg objects, each a distinct color",
    "each object has a DISTINCT number of interior holes (so max is unambiguous)",
    "objects are non-touching (1-cell padded separation)",
    "every punched hole is a fully-enclosed single-cell bg component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "all_solid", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "9-12 easy / 11-16 med / 14-22 hard", "valid": "8..26"},
    "grid_w":            {"type": "int", "default": "12-16 easy / 14-20 med / 18-26 hard", "valid": "12..28"},
    "n_objs":            {"type": "int", "default": "2 easy / 2-3 med / 3-5 hard", "valid": "2..5"},
    "hole_counts":       {"type": "int", "default": "distinct k per object", "valid": "0..7"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "= n_objs", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "objects_with_distinct_holes",
                          "valid": "objects_with_distinct_holes"},
    "n_distinct_colors": {"type": "int", "default": "= n_objs", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _count_holes(cells):
    """Python mirror of the rule's hole-count: enclosed bg components inside the bbox
    padded by 1. Used to GATE each generated shape so its actual count matches intent."""
    norm = sorted((r, c) for r, c in cells)
    maxr = max(r for r, _ in norm); maxc = max(c for _, c in norm)
    H, W = maxr + 3, maxc + 3
    occ = {(r + 1, c + 1) for r, c in norm}
    seen = set()
    holes = 0
    for sr in range(H):
        for sc in range(W):
            if (sr, sc) in occ or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]; seen.add((sr, sc)); region = []
            touch = False
            while stack:
                r, c = stack.pop(); region.append((r, c))
                if r in (0, H - 1) or c in (0, W - 1):
                    touch = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in occ and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            if not touch:
                holes += 1
    return holes


def _punched_rect(rng, R, C, k, tries=80):
    """Solid R x C rectangle with k single-cell interior holes punched (pairwise
    non-4-adjacent so each is its own enclosed bg component). Returns normalized cells
    or None if k holes can't be placed. Verified by _count_holes at the call site."""
    if k == 0:
        return [(r, c) for r in range(R) for c in range(C)]
    interior = [(r, c) for r in range(1, R - 1) for c in range(1, C - 1)]
    for _ in range(tries):
        rng.shuffle(interior)
        chosen = []
        for cell in interior:
            if all(abs(cell[0] - x[0]) + abs(cell[1] - x[1]) > 1 for x in chosen):
                chosen.append(cell)
            if len(chosen) == k:
                break
        if len(chosen) == k:
            holes = set(chosen)
            return [(r, c) for r in range(R) for c in range(C) if (r, c) not in holes]
    return None


def _one_component(cells):
    """True if `cells` form a single 4-connected component."""
    cs = set(cells)
    if not cs:
        return False
    start = next(iter(cs)); seen = {start}; stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if nb in cs and nb not in seen:
                seen.add(nb); stack.append(nb)
    return len(seen) == len(cs)


def _make_shape(rng, k):
    """A punched rectangle whose ACTUAL hole count equals k AND that stays a SINGLE
    4-connected component (dense punching can otherwise isolate an object cell and
    split the shape into spurious extra same-color objects). Sized generously for k."""
    for _ in range(60):
        side = 3 + int(k * 0.6)
        R = rng.randint(max(3, side), max(3, side) + 3)
        C = rng.randint(max(3, side), max(3, side) + 4)
        cells = _punched_rect(rng, R, C, k)
        if cells is not None and _one_component(cells) and _count_holes(cells) == k:
            return cells, R, C
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_objs", 2, 2)
        hole_pool = [0, 1, 2, 3]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 22)
        w = ctx.draw_int("grid_w", 18, 26)
        n = ctx.draw_int("n_objs", 3, 5)
        hole_pool = [0, 1, 2, 3, 4, 5, 6, 7]
    else:
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 14, 20)
        n = ctx.draw_int("n_objs", 2, 3)
        hole_pool = [0, 1, 2, 3, 4, 5]
    rng = ctx.draw_rng("layout")

    # DISTINCT hole counts per object so the most-holes winner is unambiguous; each
    # object is a procedurally punched rectangle.  The old one-pass placer returned
    # partially filled grids when a late object could not be placed.  Retry the whole
    # layout instead: either all intended distinct-hole objects are present or the
    # generator fails closed.
    for _layout in range(300):
        g = full_grid(h, w, 0)
        hole_counts = rng.sample(hole_pool, min(n, len(hole_pool)))
        palette = list(random_palette(rng, len(hole_counts)))
        placed: list[tuple[int, int, int, int]] = []
        ok = True
        for color, k in zip(palette, hole_counts):
            made = _make_shape(rng, k)
            if made is None:
                ok = False
                break
            cells, sh, sw = made
            if sh > h or sw > w:
                ok = False
                break
            placed_one = False
            for _ in range(300):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                bb_pad = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
                if any(bbox_overlaps(bb_pad, p) for p in placed):
                    continue
                paint_at(g, r0, c0, cells, color)
                placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
                placed_one = True
                break
            if not placed_one:
                ok = False
                break
        if ok and len(placed) == len(hole_counts):
            return g
    raise ValueError("could not realize all distinct-hole objects")


def _draw_from_degenerate(name, rng):
    h, w = 11, 15
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    if name == "all_solid":
        # Every object has 0 holes — primary key collapses.
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 1
        for r in range(2):
            for c in range(3):
                g[1 + r][6 + c] = 2
        for r in range(3):
            g[5 + r][3] = 3
        return g
    if name == "single_object":
        # Only 1 object — trivial pick. A 3x5 rect with 2 interior holes.
        cells = [(r, c) for r in range(3) for c in range(5)
                 if (r, c) not in {(1, 1), (1, 3)}]
        paint_at(g, 2, 4, cells, 4)
        return g
    return g

def _components_for_self_check(grid, colors=None):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (colors is not None and color not in colors) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components_for_self_check(grid)
    if not (2 <= len(comps) <= 5):
        msgs.append(f"expected 2-5 isolated objects, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(set(colors)) != len(colors):
        msgs.append("object colors must be distinct")
    hole_counts = [_count_holes(cells) for _, cells in comps]
    if len(set(hole_counts)) != len(hole_counts):
        msgs.append(f"object hole counts must be distinct, got {hole_counts}")
    if hole_counts and max(hole_counts) == 0:
        msgs.append("at least one object must have an interior hole so the primary selection key fires")
    return msgs
