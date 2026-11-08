"""Generator for arc_puzzle_bank_21_set14_s:S14_M3 — crop unique odd row-profile object.

Rule: among 3 objects, find the one whose row-count profile differs
from the other two. Output its cropped shape in color 8.

v1.1.0 used a single hardcoded COMMON shape and a single hardcoded
ODD shape — so output was always the same shape in color 8 (1 unique
output across 20 instances).

v1.2.0 pairs from a bank of (common, odd) shape pairs, each with
distinct row-count profiles, plus varied positions and colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "8285bdd7f44a"
VERSION = "2.0.0"  # distinct=6: odd shape came from a 6-entry bank so only 6 distinct cropped outputs. Rule only needs two components sharing a row-profile + one with a unique profile. Now generate RANDOM polyominoes: two identical "common" shapes + one "odd" with a different row-profile -> unbounded odd-shape (and output) variety incl non-square.
TASK_ID = "8285bdd7f44a"
SUMMARY = "3 objects; 2 share a row-count profile, 1 is unique; rule outputs the unique one's cropped shape in color 8."

# Rivals: 'output the majority shape' refuted by ≥2 demos where the
# odd one is the output. 'use object color for output' refuted by any
# demo (always 8). 'output a fixed bbox' refuted by ≥2 demos with
# different odd shapes producing different bboxes.
# 4 demos with varied shape pairs cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly two objects share the same row-count profile",
    "exactly one object has a unique row-count profile",
    "objects are 4-adj separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_same_profile", "all_distinct_profiles", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 3 distinct 4-connected components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    visited = [[False] * w for _ in range(h)]
    n_comps = 0
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 0 and not visited[r0][c0]:
                n_comps += 1
                queue = [(r0, c0)]
                visited[r0][c0] = True
                while queue:
                    r, c = queue.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
    if n_comps == 0:
        return []  # single_object / no objects degenerate — allowed
    errs = []
    if n_comps != 3:
        errs.append(f"expected exactly 3 objects; found {n_comps}")
    return errs


# Each entry: (common_shape, odd_shape). They must have different
# row-count profiles so the rule can distinguish them.
_SHAPE_PAIRS = [
    # (plus, J)
    ([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
     [(0, 0), (0, 1), (1, 1), (2, 1)]),
    # (T, L)
    ([(0, 0), (0, 1), (0, 2), (1, 1)],
     [(0, 0), (1, 0), (2, 0), (2, 1)]),
    # (Z-tet, I3)
    ([(0, 0), (0, 1), (1, 1), (1, 2)],
     [(0, 0), (0, 1), (0, 2)]),
    # (square, L-pent)
    ([(0, 0), (0, 1), (1, 0), (1, 1)],
     [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]),
    # (I3-horiz, L-pent)
    ([(0, 0), (0, 1), (0, 2)],
     [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)]),
    # (W-tet, T-pent)
    ([(0, 0), (1, 0), (1, 1), (2, 1)],
     [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]),
]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _shape_bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _row_profile(cells):
    counts = {}
    for r, _ in cells:
        counts[r] = counts.get(r, 0) + 1
    return tuple(counts[r] for r in sorted(counts))


# Assert each pair has distinct row profiles.
for _common, _odd in _SHAPE_PAIRS:
    assert _row_profile(_common) != _row_profile(_odd), (
        f"shape pair has same row profile: {_common} vs {_odd}"
    )


AXES = {
    "height":         {"type": "int", "default": "by difficulty", "valid": "9..15"},
    "width":          {"type": "int", "default": "by difficulty", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "shape_pair_idx": {"type": "int", "default": "rng 0..5", "valid": "0..5"},
    "odd_position":   {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Legacy aliases kept for back-compat with any caller.
COMMON = _SHAPE_PAIRS[0][0]
ODD = _SHAPE_PAIRS[0][1]


def _try_place(g, cells, color, region, rng, max_tries=80):
    h, w = len(g), len(g[0])
    sh, sw = _shape_bbox(cells)
    r_lo, r_hi, c_lo, c_hi = region
    r_hi = min(r_hi, h - sh); c_hi = min(c_hi, w - sw)
    if r_hi < r_lo or c_hi < c_lo:
        r_lo, r_hi, c_lo, c_hi = 0, h - sh, 0, w - sw
    for _ in range(max_tries):
        r0 = rng.randint(r_lo, r_hi)
        c0 = rng.randint(c_lo, c_hi)
        ok = True
        for dr, dc in cells:
            r, c = r0 + dr, c0 + dc
            if g[r][c] != 0:
                ok = False; break
            for ar, ac in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + ar, c + ac
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    ok = False; break
            if not ok: break
        if ok:
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 10, 11)
        w = ctx.draw_int("width", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 12, 15)
        w = ctx.draw_int("width", 15, 18)
    else:
        h = ctx.draw_int("height", 10, 12)
        w = ctx.draw_int("width", 13, 16)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # Random common + odd shapes with DISTINCT row-count profiles so the
    # rule (pick the unique-profile component) has exactly one target.
    for _ in range(200):
        common_shape = _rand_poly(rng, rng.randint(4, 7))
        odd_shape = _rand_poly(rng, rng.randint(4, 7))
        if _row_profile(common_shape) != _row_profile(odd_shape):
            break
    odd_position = rng.randint(0, 2)  # which slot (0, 1, 2) gets the odd shape
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)

    # Three placement regions: top-left, top-right, bottom
    regions = [
        (0, h // 2, 0, w // 2),                # TL quadrant
        (0, h // 2, w // 2 + 1, w - 1),        # TR quadrant
        (h // 2 + 1, h - 1, 0, w - 1),         # bottom row
    ]

    shapes_to_place = []
    for slot in range(3):
        if slot == odd_position:
            shapes_to_place.append((odd_shape, colors[slot]))
        else:
            shapes_to_place.append((common_shape, colors[slot]))

    for (shape, color), region in zip(shapes_to_place, regions):
        if not _try_place(g, list(shape), color, region, rng):
            # fallback: place anywhere
            _try_place(g, list(shape), color, (0, h - 1, 0, w - 1), rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "all_same_profile":
        paint_at(g, 1, 1, COMMON, 2)
        paint_at(g, 1, 6, COMMON, 3)
        paint_at(g, h - 4, 1, COMMON, 4)
        return g
    if name == "all_distinct_profiles":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (0, 2)], 2)
        paint_at(g, 1, 6, ODD, 3)
        paint_at(g, h - 4, 1, COMMON, 4)
        return g
    if name == "single_object":
        paint_at(g, 4, 5, COMMON, 2)
        return g
    return g
