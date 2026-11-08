"""Generator for arc_additional_puzzles_21_set12_bundle:M83 — sort objects by interior-hole count.

Rule: count "holes" (non-border-touching bg components) inside each
object's bbox crop. Sort objects ascending by hole count (with
tiebreakers), then stack their crops vertically at column 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, all_zero_holes, equal_holes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "edb34dd65185"
VERSION = "1.4.0"  # keep every emitted crop stack within the authority output height
TASK_ID = "edb34dd65185"
SUMMARY = "2-3 distinct-color, non-skinny shapes with distinct interior-hole counts (0/1/2); verified full placement."


def _hole_count(cells):
    """Interior 0-holes of a normalized cell set, matching the rule's
    crop-and-count-non-border-touching-bg-components."""
    s = set(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    seen = set(); holes = 0
    for r in range(h):
        for c in range(w):
            if (r, c) in s or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); border = False
            while stack:
                y, x = stack.pop()
                if y in (0, h - 1) or x in (0, w - 1):
                    border = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in s and (ny, nx) not in seen:
                        seen.add((ny, nx)); stack.append((ny, nx))
            if not border:
                holes += 1
    return holes


def _ring(R, C):
    return [(r, c) for r in range(R) for c in range(C)
            if r in (0, R - 1) or c in (0, C - 1)]


def _double_ring(R, C):
    # outline + a full middle divider row -> two stacked holes
    mid = R // 2
    return [(r, c) for r in range(R) for c in range(C)
            if r in (0, R - 1, mid) or c in (0, C - 1)]


def _solid(R, C):
    return [(r, c) for r in range(R) for c in range(C)]

INVARIANTS = [
    "background is 0",
    "2-3 4-connected non-bg objects, each a distinct color",
    "each object has a distinct number of interior holes (0, 1, or 2)",
    "objects are non-touching (≥1 bg gap between bboxes)",
    "default rows never silently under-place objects",
]


PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "all_zero_holes", "equal_holes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_distinct_holes",
                       "valid": "scattered_distinct_holes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def _entry(cells):
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    return (cells, _hole_count(cells), sh, sw)


# hole-0: small solid blobs + solid rectangles
_RAW0 = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
] + [_solid(R, C) for R in (2, 3) for C in (2, 3, 4)]
# hole-1: rectangular rings of varied sizes
_RAW1 = [_ring(R, C) for R in (3, 4, 5) for C in (3, 4, 5, 6)]
# hole-2: double-rings (outline + middle divider) of varied sizes
_RAW2 = [_double_ring(R, C) for R in (5, 6, 7) for C in (3, 4, 5)]

_SHAPES_0 = [_entry(c) for c in _RAW0 if _hole_count(c) == 0]
_SHAPES_1 = [_entry(c) for c in _RAW1 if _hole_count(c) == 1]
_SHAPES_2 = [_entry(c) for c in _RAW2 if _hole_count(c) == 2]

_SHAPE_BUCKETS = [_SHAPES_0, _SHAPES_1, _SHAPES_2]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 14, 15)
        n = ctx.draw_int("n_objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 20)
        w = ctx.draw_int("grid_w", 16, 19)
        n = ctx.draw_int("n_objects", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_objects", 2, 3)
    rng = ctx.draw_rng("layout")
    colors = list(random_palette(rng, n))

    # v1.2.0 gave each object 60 local placement tries and then silently
    # continued when a large ring could not be placed.  Rare easy seeds
    # therefore emitted one-object rows, hiding the intended sort-by-hole-count
    # rule while still looking superficially well-formed.  Retry the whole
    # layout until every planned object is present; the final deterministic
    # corner fallback is sized for the declared 14+ canvases.
    bucket_idxs = list(range(3))
    rng.shuffle(bucket_idxs)
    chosen = bucket_idxs[:n]
    # The authority packs crops into an output with the input height and silently
    # clips overflow.  Sample only combinations whose complete vertical stack
    # (including one separator row between crops) fits that fixed canvas.
    for _shape_attempt in range(256):
        chosen_shapes = [rng.choice(_SHAPE_BUCKETS[b]) for b in chosen]
        if sum(shape[2] for shape in chosen_shapes) + n - 1 <= h:
            break
    else:  # Every selected bucket has a small representative, so this is defensive.
        raise RuntimeError("edb34dd65185 could not sample a packable shape set")

    for _layout_attempt in range(20):
        g = full_grid(h, w, 0)
        placed_bboxes: list[tuple[int, int, int, int]] = []
        ok = True
        for color, (cells, _holes, sh, sw) in zip(colors, chosen_shapes):
            placed = False
            for _ in range(160):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
                if any(bbox_overlaps(bb, p) for p in placed_bboxes):
                    continue
                paint_at(g, r0, c0, cells, color)
                placed_bboxes.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g

    # Deterministic fallback: top-left, top-right, bottom-left.  These positions
    # maintain a one-cell bbox gap for the maximum declared shapes on 14x14+.
    g = full_grid(h, w, 0)
    corners = [(1, 1), (1, None), (None, 1)]
    placed_bboxes = []
    for color, (cells, _holes, sh, sw), (rr, cc) in zip(colors, chosen_shapes, corners):
        r0 = h - sh - 1 if rr is None else rr
        c0 = w - sw - 1 if cc is None else cc
        bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
        if any(bbox_overlaps(bb, p) for p in placed_bboxes):
            raise RuntimeError("edb34dd65185 fallback placement unexpectedly overlapped")
        paint_at(g, r0, c0, cells, color)
        placed_bboxes.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] == 0:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    if any(v == 0 for row in grid for v in row) is False:
        errors.append("background color 0 must be present")
    comps = _components(grid)
    if not (2 <= len(comps) <= 3):
        errors.append(f"expected 2-3 colored objects, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errors.append("objects must have distinct colors")
    holes = []
    crop_heights = []
    bboxes = []
    for _color, cells in comps:
        r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
        if (r1 - r0 + 1) < 2 or (c1 - c0 + 1) < 2:
            errors.append("default objects should not be skinny one-cell-wide crops")
        norm = [(r - r0, c - c0) for r, c in cells]
        holes.append(_hole_count(norm))
        crop_heights.append(r1 - r0 + 1)
        bboxes.append((r0, c0, r1, c1))
    if len(holes) != len(set(holes)):
        errors.append(f"hole counts must be distinct, found {holes}")
    if any(h not in (0, 1, 2) for h in holes):
        errors.append(f"hole counts must be in {{0,1,2}}, found {holes}")
    packed_height = sum(crop_heights) + max(0, len(crop_heights) - 1)
    if packed_height > len(grid):
        errors.append(
            f"vertical pack needs {packed_height} rows but the fixed output has {len(grid)}"
        )
    for i, a in enumerate(bboxes):
        for b in bboxes[i + 1:]:
            padded = (a[0] - 1, a[1] - 1, a[2] + 1, a[3] + 1)
            if bbox_overlaps(padded, b):
                errors.append("object bboxes must have at least one background-cell gap")
                break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 16, 16
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    if name == "all_zero_holes":
        # All solid shapes — sort by hole-count is degenerate (all 0).
        paint_at(g, 1, 1, _SHAPES_0[0][0], 4)
        paint_at(g, 5, 1, _SHAPES_0[1][0], 5)
        paint_at(g, 9, 1, _SHAPES_0[2][0], 6)
        return g
    if name == "equal_holes":
        # All shapes have same hole count — sort tie-break ambiguous.
        paint_at(g, 1, 1, _SHAPES_1[0][0], 4)
        paint_at(g, 5, 1, _SHAPES_1[0][0], 5)
        paint_at(g, 9, 1, _SHAPES_1[0][0], 6)
        return g
    return g
