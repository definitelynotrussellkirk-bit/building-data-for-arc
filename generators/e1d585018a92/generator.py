"""Generator for arc_additional_puzzles_21_set21_bundle:M143.

Rule: cell (0, 0) names a color; the largest object of that color is
cropped to its bbox. Output = the cropped subgrid.

v1.1.0 hardcoded the 'largest target' as a 5-cell L always → output
bbox was always (3, 2) (1 bbox / 9 unique outputs across 30).
v1.2.0:
  * varies the largest target's shape (10-shape bank, sizes 4..9,
    varied bboxes 2×2..3×4)
  * varies the largest target's position
  * varies the smaller target's size (1..max(target_size-2, 1) cells)
  * varies the number of non-target distractor blobs (0..3) and their
    colors
  * adds size invariant: largest target is strictly larger than every
    other target object so 'largest' is unambiguous
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1d585018a92"
VERSION = "2.1.1"  # add executable self_check and refresh docs for random target polyominoes.
TASK_ID = "e1d585018a92"
SUMMARY = (
    "0-bg grid (h, w~9-14) "
    "with: (a) CELL (0, 0) "
    "holds the TARGET "
    "COLOR (a value in "
    "{1..9}); (b) ONE "
    "LARGEST TARGET OBJECT "
    "in the TARGET COLOR — "
    "a random connected "
    "polyomino (sizes 4-9, "
    "varied bbox) at "
    "random interior "
    "position; (c) "
    "optionally ONE "
    "SMALLER TARGET OBJECT "
    "(size 1..target_size-"
    "2) in the same "
    "color, strictly "
    "smaller; (d) 0-3 "
    "DISTRACTOR BLOBS in "
    "DISTINCT non-target "
    "colors, each strictly "
    "smaller than the "
    "target. All blobs "
    "with 1-cell padding. "
    "Output crops vary by "
    "random target shape, "
    "bbox, and color. "
    "Rule (CROP LARGEST "
    "TARGET-COLOR OBJECT "
    "TO BBOX): READ TARGET "
    "COLOR T = g[0][0]. "
    "Identify all OBJECTS "
    "in color T (excluding "
    "(0, 0)). Find the "
    "LARGEST. CROP to "
    "BBOX. EMIT the "
    "cropped subgrid. "
    "Net: (0, 0) names "
    "color; biggest object "
    "of that color is "
    "extracted."
)

# Rivals: 'crop the largest object regardless of color' refuted by ≥1
# demo where another color has a bigger object than the target. 'crop
# the marker' refuted by any demo (marker is 1 cell, target object is
# always larger). 'use marker color as output' refuted by any demo
# (output color matches target, which it always does — that's
# tautological; but the model still needs to learn marker → target
# color mapping). 'output a fixed bbox' refuted by ≥2 demos with
# different target sizes.
# 4 demos with varied target sizes + at least 1 demo where another
# color has a bigger object cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "cell (0, 0) holds the target color",
    "at least one target-colored object of size ≥ 4 elsewhere",
    "the largest target object is strictly larger than every other target object",
    "non-target distractor blobs may exist but cannot exceed the target object's size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_marker", "no_target_objects",
                       "equal_target_sizes", "distractor_bigger_than_target")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "by difficulty", "valid": "9..14"},
    "grid_w":            {"type": "int", "default": "by difficulty", "valid": "9..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "target_color":      {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "target_shape_idx":  {"type": "int", "default": "rng 0..9",
                          "valid": "0..9"},
    "smaller_size":      {"type": "int", "default": "rng 1..target_size-2",
                          "valid": "1..7"},
    "n_distractors":     {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":      {"type": "int", "default": "2..5", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "marker_top_left",
                          "valid": "marker_top_left"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|missing_marker|no_target_objects|equal_target_sizes|distractor_bigger_than_target"},
}


_TARGET_SHAPES = [
    # bbox 2×2
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    # bbox 2×3
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],
    # bbox 3×2
    [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    # bbox 3×3
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],
    # bbox 2×4
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)],
    # bbox 3×4
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 3)],
    # bbox 4×2
    [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (3, 1)],
]


def _poly(rng, k):
    """Random connected polyomino of k cells, normalized to (0,0)."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _shape_bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _difficulty_grid(difficulty):
    if difficulty == "easy":
        return 9, 11, 9, 11
    if difficulty == "hard":
        return 12, 14, 12, 14
    return 10, 12, 10, 12


def _try_place(g, cells, color, rng, *, max_tries, region=None):
    """Place a normalized cell list with 4-adj clearance from existing
    non-zero cells (excluding the (0,0) marker which is intentionally
    isolated by the surrounding rim being bg)."""
    h, w = len(g), len(g[0])
    sh, sw = _shape_bbox(cells)
    if region:
        r_lo, r_hi, c_lo, c_hi = region
    else:
        r_lo, r_hi, c_lo, c_hi = 1, h - sh, 1, w - sw
    # r0/c0 is the placement ORIGIN, so the hi bound must leave room for the
    # shape's bbox. The region path passed (2, h-1, 2, w-1) verbatim, letting
    # r0=h-1 + dr run off the grid → IndexError at the cell read below. Always
    # clamp the origin's upper bound to h-sh / w-sw.
    r_hi = min(r_hi, h - sh)
    c_hi = min(c_hi, w - sw)
    if r_hi < r_lo or c_hi < c_lo:
        return False
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
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    h_lo, h_hi, w_lo, w_hi = _difficulty_grid(difficulty)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")

    target = ctx.draw_color("target_color", exclude=[0])

    # Pick largest target shape as a RANDOM polyomino (size 4-9) for varied
    # output crops (was a fixed 10-shape bank -> dup-outputs).
    target_size = rng.randint(4, 9)
    target_shape = _poly(rng, target_size)

    g = full_grid(h, w, 0)
    g[0][0] = target  # marker — isolated by surrounding bg

    # Place the largest target object. Region excludes (0, 0)+adjacent
    # so it doesn't merge with the marker.
    if not _try_place(g, target_shape, target, rng, max_tries=80,
                       region=(2, h - 1, 2, w - 1)):
        # too tight → emit a degraded but valid grid
        for dr, dc in target_shape:
            if 2 + dr < h and 2 + dc < w:
                g[2 + dr][2 + dc] = target

    # Optional smaller target object (size 1..target_size - 2). Strictly
    # smaller so "largest target" is unambiguous.
    if target_size >= 3:
        smaller_size = rng.randint(1, target_size - 2)
        smaller_shape = [(0, c) for c in range(smaller_size)]
        _try_place(g, smaller_shape, target, rng, max_tries=40)

    # 0..3 non-target distractor blobs of various colors. Each blob
    # size capped at target_size - 1 to keep target as the largest
    # object overall (also satisfies an interpretation rivals where
    # "largest object" would otherwise pick a distractor).
    n_distractors = rng.randint(0, 3)
    distractor_colors = [c for c in range(1, 10) if c != target]
    rng.shuffle(distractor_colors)
    for i in range(min(n_distractors, len(distractor_colors))):
        dsize = rng.randint(1, max(1, target_size - 1))
        # random short connected shape
        dshape = [(0, c) for c in range(dsize)]
        _try_place(g, dshape, distractor_colors[i], rng, max_tries=40)

    return g



def _components_of_color(grid, color, *, exclude_marker=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if exclude_marker and (r0, c0) == (0, 0):
                continue
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color
                            and not (exclude_marker and (nr, nc) == (0, 0))):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def _all_nonzero_components(grid, *, ignore={(0, 0)}):
    h, w = len(grid), len(grid[0])
    seen = set(ignore)
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the target-color largest-object crop task."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    target = grid[0][0]
    if target == 0:
        errs.append("cell (0,0) must name a nonzero target color")
        return errs
    target_comps = _components_of_color(grid, target, exclude_marker=True)
    if not target_comps:
        errs.append("no target-colored object other than the marker")
        return errs
    sizes = sorted((len(cells) for cells in target_comps), reverse=True)
    if sizes[0] < 4:
        errs.append(f"largest target object too small: {sizes[0]} cells")
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        errs.append("largest target object is not unique by size")
    largest_size = sizes[0]
    for color, cells in _all_nonzero_components(grid):
        if color != target and len(cells) > largest_size:
            errs.append("non-target distractor is larger than the target object")
            break
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "missing_marker":
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]:
            g[2 + dr][2 + dc] = 4
        return g
    if name == "no_target_objects":
        g[0][0] = 5
        g[3][3] = 7; g[3][4] = 7
        return g
    if name == "equal_target_sizes":
        g[0][0] = 4
        g[2][2] = 4; g[2][3] = 4
        g[5][5] = 4; g[5][6] = 4
        g[7][7] = 4; g[7][8] = 4
        return g
    if name == "distractor_bigger_than_target":
        g[0][0] = 4
        g[2][2] = 4; g[2][3] = 4              # target: 2 cells
        for r, c in [(5, 5), (5, 6), (5, 7), (6, 5), (6, 7), (7, 5), (7, 6), (7, 7)]:
            g[r][c] = 6                       # distractor: 8 cells → bigger than target
        return g
    return g
