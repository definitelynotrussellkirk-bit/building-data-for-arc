"""Generator for puzzle d2abd087.

Rule: for each non-bg 4-connected object: size == 6 → 2 (red); else → 1 (blue).

Combinatorial axes (8):
  * grid_h / grid_w     — outer canvas size
  * input_color         — color of input objects (≠ 0, ≠ 1, ≠ 2)
  * n_size6             — count of size-6 objects (will become 2)
  * n_other             — count of other-size objects (will become 1)
  * size6_kind          — shape of size-6: rect_2x3 / rect_1x6 / L_shape /
                          T_shape / Z_shape / blob_6 / cross_6
  * other_size_dist     — small_only / mixed / large_only (sizes for "other")
  * placement           — random / corners / row / column / grid
  * input_palette_mode  — same_color / per_size_group / all_distinct
  * caller-opt-in degenerates: only_size6, only_other, touching_objects
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "d8d37830884c"
VERSION = "1.2.0"  # fix object separation padding; add executable invariant self_check
TASK_ID = "d8d37830884c"
SUMMARY = "Components of various sizes; rule colors size-6 → 2(red), else → 1(blue)."

INVARIANTS = [
    "background is 0",
    "≥1 size-6 component (→ red)",
    "≥1 component of size ≠ 6 (→ blue)",
    "components 4-connected, non-overlapping with margin ≥ 1",
]

SIZE6_KINDS = ("rect_2x3", "rect_1x6", "L_shape", "T_shape", "Z_shape",
               "blob_6", "cross_6")
OTHER_SIZE_DISTS = ("small_only", "mixed", "large_only")
PLACEMENTS = ("random", "corners", "row", "column", "grid")
PALETTE_MODES = ("same_color", "all_distinct")
DEGENERATE_TEXTURES = ("only_size6", "only_other", "touching_objects")
HELPFUL_TEXTURES = SIZE6_KINDS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":             {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "input_color":        {"type": "color", "default": "rng (≠0,1,2)", "valid": "3..9"},
    "n_size6":            {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_other":            {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "size6_kind":         {"type": "str", "default": "rng helpful",
                           "valid": "|".join(SIZE6_KINDS)},
    "other_size_dist":    {"type": "str", "default": "rng helpful",
                           "valid": "|".join(OTHER_SIZE_DISTS)},
    "placement":          {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PLACEMENTS)},
    "input_palette_mode": {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PALETTE_MODES)},
    "texture":            {"type": "str", "default": "alias for size6_kind",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n6_lo, n6_hi, no_lo, no_hi = 12, 14, 1, 1, 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, n6_lo, n6_hi, no_lo, no_hi = 16, 18, 2, 3, 3, 4
    else:
        h_lo, h_hi, n6_lo, n6_hi, no_lo, no_hi = 12, 18, 1, 3, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    color = int(overrides.get("input_color",
                              ctx.draw_color("input_color", exclude={0, 1, 2})))
    n6 = int(overrides.get("n_size6", ctx.draw_int("n_size6", n6_lo, n6_hi)))
    no = int(overrides.get("n_other", ctx.draw_int("n_other", no_lo, no_hi)))
    size6_kind = (overrides.get("texture") or overrides.get("size6_kind")
                  or ctx.draw_choice("size6_kind", list(SIZE6_KINDS)))
    other_dist = overrides.get("other_size_dist",
                               ctx.draw_choice("other_size_dist", list(OTHER_SIZE_DISTS)))
    palette_mode = overrides.get("input_palette_mode",
                                 ctx.draw_choice("input_palette_mode", list(PALETTE_MODES)))
    palette_extra = list(ctx.draw_distinct_colors("palette_extra", n=4, exclude={0, 1, 2, color}))

    g = full_grid(h, w, 0)
    placed_six = 0; placed_other = 0
    for i in range(n6):
        cells = _size6_cells(size6_kind, rng)
        c = color if palette_mode == "same_color" else (
            palette_extra[i % len(palette_extra)] if palette_extra else color)
        if place_no_overlap(rng, g, cells, c, bg=0, margin=1, padding=1, max_tries=120):
            placed_six += 1
    for i in range(no):
        size = _pick_other_size(other_dist, rng)
        cells = _shape_for_size(size, rng)
        c = color if palette_mode == "same_color" else (
            palette_extra[(i + 1) % len(palette_extra)] if palette_extra else color)
        if place_no_overlap(rng, g, cells, c, bg=0, margin=1, padding=1, max_tries=120):
            placed_other += 1
    if placed_six < 1 or placed_other < 1:
        return _valid_fallback(h, w, color)
    return g


def _valid_fallback(h, w, color):
    """Fail closed to a tiny but valid teaching instance instead of [[0]]."""
    g = full_grid(h, w, 0)
    # One size-6 2x3 rectangle near the top-left.
    for r in range(1, 3):
        for c in range(1, 4):
            g[r][c] = color
    # One non-size-6 component with a padding moat near the bottom-right.
    for r, c in [(h - 4, w - 4), (h - 4, w - 3), (h - 3, w - 4)]:
        g[r][c] = color
    return g


def _size6_cells(kind, rng):
    if kind == "rect_2x3":
        return normalize(rect_cells(2, 3))
    if kind == "rect_1x6":
        return normalize(rng.choice([rect_cells(1, 6), rect_cells(6, 1)]))
    if kind == "L_shape":
        return normalize([(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)])
    if kind == "T_shape":
        return normalize([(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1)])
    if kind == "Z_shape":
        return normalize([(0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (1, 4)])
    if kind == "blob_6":
        return normalize([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)])
    if kind == "cross_6":
        return normalize([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)])
    return normalize(rect_cells(2, 3))


def _pick_other_size(dist, rng):
    if dist == "small_only":
        return rng.choice([1, 2, 3, 4])
    if dist == "large_only":
        return rng.choice([7, 8, 9, 10])
    return rng.choice([1, 2, 3, 4, 5, 7, 8])


def _shape_for_size(size, rng):
    if size == 1:
        return [(0, 0)]
    if size == 2:
        return normalize(rect_cells(*rng.choice([(1, 2), (2, 1)])))
    if size == 3:
        return normalize(rect_cells(*rng.choice([(1, 3), (3, 1)])))
    if size == 4:
        return normalize(rect_cells(*rng.choice([(2, 2), (1, 4), (4, 1)])))
    if size == 5:
        return normalize([(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)])
    if size == 7:
        return normalize([(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)])
    if size == 8:
        return normalize(rect_cells(*rng.choice([(2, 4), (4, 2)])))
    if size == 9:
        return normalize(rect_cells(3, 3))
    return normalize(rect_cells(2, 5))


def _draw_from_degenerate(name, h, w, rng):
    color = rng.choice([3, 4, 5, 6, 7, 8, 9])
    g = full_grid(h, w, 0)
    if name == "only_size6":
        for _ in range(4):
            place_no_overlap(rng, g, _size6_cells("rect_2x3", rng), color,
                             bg=0, margin=1, max_tries=20)
        return g
    if name == "only_other":
        for s in [1, 2, 3, 4, 5]:
            place_no_overlap(rng, g, _shape_for_size(s, rng), color,
                             bg=0, margin=1, max_tries=20)
        return g
    if name == "touching_objects":
        # Touching shapes 4-conn merge into one big object — rule sees it as size 12.
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = color
        for r in range(2, 5):
            for c in range(5, 8):
                g[r][c] = color
        return g
    return g

def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop(); comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if len(grid) == 1 and len(grid[0]) == 1:
        return ["fallback scalar grid emitted instead of teaching components"]
    vals = {v for row in grid for v in row if v != 0}
    if vals & {1, 2}:
        errs.append("input object colors must not be output label colors 1 or 2")
    comps = _nonzero_components(grid)
    sizes = [len(c) for c in comps]
    if 6 not in sizes:
        errs.append("no size-6 component present")
    if not any(s != 6 for s in sizes):
        errs.append("no non-size-6 component present")
    for i, comp_a in enumerate(comps):
        a = set(comp_a)
        for comp_b in comps[i + 1:]:
            for r, c in a:
                if any(max(abs(r - rr), abs(c - cc)) <= 1 for rr, cc in comp_b):
                    errs.append("separate components touch within padding-1 moat")
                    return sorted(set(errs))
    return sorted(set(errs))
