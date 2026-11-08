"""Generator for 11b:m74 (task 00f0de29a65c) — smallest shape, scaled + recolored.

THE RULE (what a solver must learn to see):
  A single-cell marker provides the target color. Among the multi-cell
  shapes, take the SMALLEST — ties broken by topmost, then leftmost
  bbox corner. Crop it, upscale 2x, recolor every cell to the marker
  color.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - random grown polyominoes (sizes 3-8), not a fixed 12-shape library
  - size_tie boards: two shapes SHARE the minimum size and the
    topmost-leftmost one wins — the tie-break half of the rule was
    previously only in a frozen degenerate, never in training data
  - marker is placed FIRST so it always exists (the rule CRASHES on a
    missing marker: (last (filter ...)) over an empty list)
  - marker color distinct from every shape color; shapes pairwise
    distinct colors, halo-separated

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - multiple_markers  several singles: the rule picks the LAST in scan
                      order — position, not semantics, decides
  - tied_smallest     min-size tie decided purely by the tie-break
  - single_shape      one multi-cell shape: no size contrast at all
  (no_marker is NOT offered — the rule errors out on it)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00f0de29a65c"
VERSION = "2.1.0"
TASK_ID = "00f0de29a65c"
SUMMARY = (
    "0-bg grid with one single-cell marker plus 2-4 halo-separated "
    "grown polyominoes (3-8 cells, distinct colors, sizes sometimes "
    "tied at the minimum); rule crops the smallest shape (topmost-"
    "leftmost on ties), upscales 2x, recolors to the marker color."
)

# Rivals: 'crop the LARGEST' refuted by every demo. 'keep the shape's
# own color' refuted (output is marker-colored). 'output at 1x' refuted
# by 2x dims. 'pick by color not size' refuted by varied palettes.
# 'any of the tied smallest' refuted by tie demos where only the
# topmost-leftmost matches. 4 demos incl. >=1 size tie.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0; exactly one single-cell marker (helpful path)",
    "2-4 multi-cell shapes, distinct colors, halo-separated",
    "marker color distinct from all shape colors",
    "size_tie boards: exactly two shapes share the min size",
    "marker placed first — it always exists (missing marker crashes the rule)",
]

DEGENERATE_TEXTURES = ("multiple_markers", "tied_smallest", "single_shape")
HELPFUL_TEXTURES = ("plain", "size_tie")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 11..14 (easy 10..12, hard 13..18)",
                 "valid": "10..18", "doc": "Grid height."},
    "grid_w":   {"type": "int", "default": "rng 12..15 (easy 11..13, hard 14..18)",
                 "valid": "11..18", "doc": "Grid width."},
    "n_shapes": {"type": "int", "default": "rng 2..3 (hard 3..4)",
                 "valid": "2..4", "doc": "Multi-cell shapes."},
    "size_tie": {"type": "bool", "default": "rng ~40%", "valid": "0|1",
                 "doc": "Two shapes share the min size; the topmost-"
                        "leftmost one is the rule's target."},
    "texture":  {"type": "str", "default": "rng helpful",
                 "valid": "plain|size_tie|multiple_markers|tied_smallest|single_shape",
                 "doc": "Set to a degenerate name to build a rule-hiding input."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _grow_shape(rng, k):
    """Random connected polyomino of k cells, normalized to (0,0).

    For k>=3 the result is forced to be NON-bbox-filling (not a solid
    line/rectangle): a solid shape upscales+recolors to a single solid
    color, making the OUTPUT a degenerate all-one-color block that hides
    the crop+recolor transform. A non-rectangular shape keeps both the
    marker color and the 0-background visible in the output.
    """
    for _ in range(40):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < k:
            r, c = cells[rng.randrange(len(cells))]
            dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc))
                seen.add((r + dr, c + dc))
        mr = min(r for r, _ in cells)
        mc = min(c for _, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        bh = max(r for r, _ in norm) + 1
        bw = max(c for _, c in norm) + 1
        if k < 3 or bh * bw > k:   # bbox has at least one empty cell
            return norm
    return norm


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(50):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        n_shapes = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n_shapes = ctx.draw_int("n_shapes", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 15)
        n_shapes = ctx.draw_int("n_shapes", 2, 3)
    tie = texture == "size_tie" or bool(int(overrides.get(
        "size_tie", 1 if ctx.draw_int("size_tie", 0, 9) < 4 else 0)))
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    palette = list(rng.sample(_COLORS, n_shapes + 1))
    marker_color, shape_colors = palette[0], palette[1:]

    # marker FIRST: guaranteed to exist (rule crashes without one);
    # halo placement of shapes keeps it an isolated single
    g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = marker_color

    if tie:
        small = rng.randint(3, 5)
        sizes = [small, small] + list(rng.sample(range(small + 1, 9),
                                                 max(0, n_shapes - 2)))
    else:
        sizes = list(rng.sample(range(3, 9), n_shapes))
    placed = 0
    for size, color in zip(sizes, shape_colors):
        if _place(g, rng, _grow_shape(rng, size), color):
            placed += 1
    if placed < 2:
        # crowded board: guarantee size contrast with two tiny shapes
        for size, color in ((3, shape_colors[0]), (4, shape_colors[-1])):
            _place(g, rng, _grow_shape(rng, size), color)
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, always rule-safe (marker exists).

    multiple_markers — several singles; the rule picks the LAST in
                       component scan order, not 'the' marker.
    tied_smallest    — two shapes share min size; tie-break decides.
    single_shape     — one multi-cell shape, no size contrast.
    """
    h = ctx.draw_int("grid_h", 11, 14)
    w = ctx.draw_int("grid_w", 12, 15)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    palette = list(rng.sample(_COLORS, 4))
    if name == "multiple_markers":
        _place(g, rng, _grow_shape(rng, rng.randint(3, 5)), palette[0])
        for color in palette[1:]:
            for _ in range(30):
                r, c = rng.randrange(h), rng.randrange(w)
                if _free(g, r, c, r, c):
                    g[r][c] = color
                    break
        return g
    if name == "tied_smallest":
        size = rng.randint(3, 5)
        _place(g, rng, _grow_shape(rng, size), palette[0])
        _place(g, rng, _grow_shape(rng, size), palette[1])
        for _ in range(30):
            r, c = rng.randrange(h), rng.randrange(w)
            if _free(g, r, c, r, c):
                g[r][c] = palette[2]
                break
        return g
    # single_shape
    _place(g, rng, _grow_shape(rng, rng.randint(4, 7)), palette[0])
    for _ in range(30):
        r, c = rng.randrange(h), rng.randrange(w)
        if _free(g, r, c, r, c):
            g[r][c] = palette[1]
            break
    return g


def _components(g):
    """4-connected non-zero components → list of cell-lists."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] == g[cr][cc]):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """The crop+upscale+recolor output must be non-degenerate.

    Requires: >=1 single-cell marker (rule crashes without one) and at
    least one multi-cell shape; and EVERY multi-cell shape is
    non-bbox-filling (bbox area > cell count). The last guarantee means
    whichever shape the rule crops, the upscaled output retains the
    0-background → it is never a single solid color.
    """
    msgs = []
    comps = _components(grid)
    singles = [cs for cs in comps if len(cs) == 1]
    multi = [cs for cs in comps if len(cs) >= 2]
    if not singles:
        msgs.append("no single-cell marker (rule crashes without one)")
    if not multi:
        msgs.append("no multi-cell shape to crop")
    for cs in multi:
        rs = [r for r, _ in cs]; csx = [c for _, c in cs]
        bbox = (max(rs) - min(rs) + 1) * (max(csx) - min(csx) + 1)
        if bbox <= len(cs):
            msgs.append("bbox-filling shape → output would be a single "
                        "solid color (degenerate)")
            break
    return msgs
