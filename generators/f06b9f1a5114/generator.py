"""Generator for next_b:m08 — complete rectangle borders from diagonal corners.

Rule: each pair of same-color diagonal corner cells defines a
rectangle. Each rectangle's outline (border only) is drawn in the
corner color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_corners, single_corner, collinear_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f06b9f1a5114"
VERSION = "2.2.0"  # robust positive-rectangle packing + self_check
TASK_ID = "f06b9f1a5114"
SUMMARY = (
    "0-bg grid with 2-4 POSITIVE diagonal-corner pairs (each a distinct color, "
    "rect >=3 in each dim so its outline differs from the 2-corner input) plus "
    "0-2 NEGATIVE colors (collinear pair / single cell) the rule leaves "
    "unchanged. Rule: for each color with EXACTLY 2 cells at diagonal corners "
    "(different row AND col), draw the rectangle border in that color. Rect "
    "count, sizes, colors, positions and grid shape all vary."
)

INVARIANTS = [
    "background is 0",
    "each POSITIVE color has exactly 2 same-color cells at diagonal-corner positions",
    "positive rectangles do not overlap (full bbox reserved)",
    "each positive rectangle is >=3 in each dim so its outline differs from the input",
    "NEGATIVE colors (collinear pair / single cell) exercise the len==2 & diagonal "
    "filter and are left unchanged",
    "all colors distinct (so find-color groups stay per-rectangle)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corners", "single_corner", "collinear_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "n_neg":          {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "diagonal_corner_pairs",
                       "valid": "diagonal_corner_pairs"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 13)
        n_rects = ctx.draw_int("n_rects", 2, 2); n_neg = ctx.draw_int("n_neg", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20)
        n_rects = ctx.draw_int("n_rects", 3, 4); n_neg = ctx.draw_int("n_neg", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 12, 16)
        n_rects = ctx.draw_int("n_rects", 2, 3); n_neg = ctx.draw_int("n_neg", 0, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(colors)
    ci = 0
    used_cells: set[tuple[int, int]] = set()

    # --- positives: diagonal-corner pairs the rule outlines (rect >=3 each dim) ---
    placed = 0
    candidates = _rect_candidates(rng, h, w)
    while placed < n_rects and ci < len(colors):
        color = colors[ci]
        for r1, c1, r2, c2 in candidates:
            cells = _rect_cells(r1, c1, r2, c2)
            if cells & used_cells:
                continue
            if rng.random() < 0.5:
                g[r1][c1] = color; g[r2][c2] = color
            else:
                g[r1][c2] = color; g[r2][c1] = color
            used_cells |= cells
            placed += 1
            ci += 1
            break
        else:
            break
    if placed < n_rects:
        raise ValueError(f"could not place {n_rects} disjoint positive rectangles; placed {placed}")

    # --- negatives: configs the (len==2 & diagonal) filter rejects -> unchanged ---
    neg = 0
    while neg < n_neg and ci < len(colors):
        color = colors[ci]
        cells = _negative_cells(rng, h, w, used_cells)
        if cells:
            for (r, c) in cells:
                g[r][c] = color
            used_cells |= set(cells)
            neg += 1
        ci += 1
    return g


def _rect_cells(r1, c1, r2, c2):
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def _rect_candidates(rng, h, w):
    """Randomized small/medium rectangles, with a deterministic scan fallback.

    The old rejection sampler sometimes spent all colors on oversized boxes and
    returned only one positive diagonal pair.  Enumerating feasible boxes first
    makes the requested positive count realizable even on the narrow easy grids.
    """
    out = []
    for rh in range(3, min(7, h) + 1):
        for rw in range(3, min(7, w) + 1):
            for r1 in range(0, h - rh + 1):
                for c1 in range(0, w - rw + 1):
                    out.append((r1, c1, r1 + rh - 1, c1 + rw - 1))
    rng.shuffle(out)
    # Prefer smaller boxes late as a packing fallback.
    out.sort(key=lambda rc: ((rc[2] - rc[0] + 1) * (rc[3] - rc[1] + 1), rng.random()))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Check that positive colors really encode diagonal rectangle corners."""
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid is empty or not a 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    by_color = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    errs = []
    positives = []
    for color, pts in by_color.items():
        if len(pts) == 2:
            (r1, c1), (r2, c2) = pts
            if r1 != r2 and c1 != c2:
                if abs(r1 - r2) < 2 or abs(c1 - c2) < 2:
                    errs.append(f"color {color} diagonal pair is too small to form a nontrivial outline")
                positives.append((color, pts))
        elif len(pts) > 2:
            errs.append(f"color {color} has {len(pts)} input cells; expected a pair or singleton negative")
    if len(positives) < 2:
        errs.append(f"expected at least 2 diagonal-corner pairs, found {len(positives)}")
    # Positive rectangle bboxes are reserved by construction; overlapping boxes
    # would make the generated outlines ambiguous for the direct-grid target.
    boxes = []
    for color, ((r1, c1), (r2, c2)) in positives:
        box = (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2), color)
        for ar1, ac1, ar2, ac2, acolor in boxes:
            if not (box[2] < ar1 or ar2 < box[0] or box[3] < ac1 or ac2 < box[1]):
                errs.append(f"positive rectangles for colors {acolor} and {color} overlap")
        boxes.append(box)
    return errs


def _negative_cells(rng, h, w, used):
    """A color the rule leaves unchanged: collinear pair (same row/col) or a
    single cell. Cells must be free (not in used)."""
    kind = rng.choice(["row", "col", "single"])
    for _ in range(80):
        if kind == "single":
            cells = [(rng.randint(0, h - 1), rng.randint(0, w - 1))]
        elif kind == "row":
            r = rng.randint(0, h - 1)
            cs = rng.sample(range(w), 2)
            cells = [(r, cs[0]), (r, cs[1])]
        else:
            c = rng.randint(0, w - 1)
            rs = rng.sample(range(h), 2)
            cells = [(rs[0], c), (rs[1], c)]
        if not (set(cells) & used):
            return cells
    return []


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "no_corners":
        # Empty grid — no diagonal corner pair to expand.
        return g
    if name == "single_corner":
        # Only one cell of each color — no pair, so no rectangle is
        # implied and the rule has nothing to outline.
        g[2][2] = 4
        g[7][8] = 6
        return g
    if name == "collinear_corners":
        # Same-color cells on the same row (not diagonal) — no rectangle
        # is defined, just a line, so the rule's outline is degenerate.
        g[2][1] = 4; g[2][6] = 4
        g[7][2] = 6; g[7][8] = 6
        return g
    return g
