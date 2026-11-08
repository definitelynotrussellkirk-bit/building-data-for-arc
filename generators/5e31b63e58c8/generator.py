"""Generator for arc_additional_puzzles_21_set4:H24 — Red objects' hole counts as a row.

Rule: red(2) objects sorted left-to-right by obj-c1; output 1xN row
of (topo-count-holes + 1) per object.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_obj,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_solid, all_same_holes, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import has_neighbor, bbox_overlaps

GENERATOR_ID = "5e31b63e58c8"
VERSION = "2.1.0"  # distinct=12: output 1xN row of (holes+1) per red object, but only 3 cyclic shapers (0/1/2 holes) + N~3. Now each object gets a random hole count 0..3 (k-compartment frames) and N varies 2..6 -> 1xN row content+width vary widely.
TASK_ID = "5e31b63e58c8"
SUMMARY = "Several red objects with 0/1/2 holes laid left-to-right; output is hole-count+1 row."

INVARIANTS = [
    "between 2 and 4 red objects",
    "objects span a mix of hole counts (0, 1, 2)",
    "objects don't touch (orthogonally)",
    "objects spaced left-to-right with gaps so sort-by-c1 is unambiguous",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_solid", "all_same_holes", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 14..20", "valid": "12..28"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_obj":          {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "left_to_right",
                       "valid": "left_to_right"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _solid_rect(r1, c1, h, w):
    cells = {(r1 + dr, c1 + dc) for dr in range(h) for dc in range(w)}
    return cells, (r1, c1, r1 + h - 1, c1 + w - 1)


def _hollow_frame(r1, c1, h, w):
    cells = set()
    for c in range(c1, c1 + w):
        cells.add((r1, c)); cells.add((r1 + h - 1, c))
    for r in range(r1, r1 + h):
        cells.add((r, c1)); cells.add((r, c1 + w - 1))
    return cells, (r1, c1, r1 + h - 1, c1 + w - 1)


def _double_frame(r1, c1, h, w):
    cells = set()
    for c in range(c1, c1 + w):
        cells.add((r1, c)); cells.add((r1 + h - 1, c))
    for r in range(r1, r1 + h):
        cells.add((r, c1)); cells.add((r, c1 + w - 1))
    mid = r1 + h // 2
    for c in range(c1, c1 + w):
        cells.add((mid, c))
    return cells, (r1, c1, r1 + h - 1, c1 + w - 1)


def _shape_k_holes(rng, k):
    """A shape with EXACTLY k enclosed holes (rule emits value k+1).
    k=0 -> solid rect; k>=1 -> a frame split into k compartments by k-1
    internal full-width dividers."""
    if k == 0:
        h = rng.randint(2, 3); w = rng.randint(2, 3)
        cells = {(r, c) for r in range(h) for c in range(w)}
        return cells, (0, 0, h - 1, w - 1)
    w = rng.randint(3, 5)
    h = 2 * k + 1
    cells = set()
    for c in range(w):
        cells.add((0, c)); cells.add((h - 1, c))
    for r in range(h):
        cells.add((r, 0)); cells.add((r, w - 1))
    for i in range(1, k):                 # k-1 internal dividers -> k compartments
        for c in range(w):
            cells.add((2 * i, c))
    return cells, (0, 0, h - 1, w - 1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 14, 18)
        n_obj = ctx.draw_int("n_obj", 2, 3); kmax = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 20, 28)
        n_obj = ctx.draw_int("n_obj", 4, 6); kmax = 3
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 16, 24)
        n_obj = ctx.draw_int("n_obj", 2, 5); kmax = 3

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set(); bboxes = []

    # each object independently gets a RANDOM hole count 0..kmax (output value
    # k+1), so the 1xN row of values varies in both width (N) and content.
    cur_c = 1
    for i in range(n_obj):
        k = rng.randint(0, kmax)
        cells, bb = _shape_k_holes(rng, k)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        bh = max(rs) - min(rs) + 1
        bw = max(cs) - min(cs) + 1
        if cur_c + bw + 1 >= w: break
        rr = rng.randint(0, h - bh)
        rc = cur_c
        placed = {(rr + r - min(rs), rc + c - min(cs)) for r, c in cells}
        if any(p in used or has_neighbor(p, used, ignore=placed) for p in placed):
            cur_c += bw + 2
            continue
        used |= placed
        bboxes.append((rr, rc, rr + bh - 1, rc + bw - 1))
        for r, c in placed: g[r][c] = 2
        cur_c += bw + 2

    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 color-2 (red) cells present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(reds) < 2:
        errs.append(f"expected >=2 red(2) cells, found {len(reds)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 16
    g = full_grid(h, w, 0)
    if name == "all_solid":
        # all objects solid (0 holes) → output row is all 1s, no contrast
        for r1, c1, rh, rw in [(2, 1, 2, 2), (2, 6, 2, 3), (2, 11, 2, 2)]:
            for dr in range(rh):
                for dc in range(rw):
                    g[r1 + dr][c1 + dc] = 2
        return g
    if name == "all_same_holes":
        # all objects share same hole count → output row uniform, no signal
        for c1 in [1, 6, 11]:
            for c in range(c1, c1 + 4):
                g[1][c] = 2; g[4][c] = 2
            for r in range(1, 5):
                g[r][c1] = 2; g[r][c1 + 3] = 2
        return g
    if name == "no_objects":
        # empty grid → output row has length 0, ambiguous
        return g
    return g
