"""Generator for arc_additional_puzzle_bank_volume11:H75 — most-frequent-shape scaled.

Rule (re-derived):
  1. Find all objects (any color, 4-connected).
  2. Group by normalized shape (color-blind, exact orientation — same-shape?
     is exact-normalized, NOT dihedral).
  3. Pick the most-frequent shape class (tie-break: top-most then left-most).
     Let K = its frequency.
  4. Output = the shape scaled K× (each cell -> K×K block), painted entirely
     color 8 on a black background. Output bbox is (shape_h*K, shape_w*K).

v2.0.0 drew the frequent shape from a fixed 9-entry bank, so the output
(determined entirely by (shape, K)) had only ~9×4 possibilities -> uniq_out
~0.075 (heavy duplication). v3.0.0 generates RANDOM polyomino shapes for both
the frequent shape and the distractors, exploding the (shape, K) output space.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "fb7c915894d6"
# 3.1.0: all_background fix. The output is the frequent shape upscaled K x in
# colour 8. When that shape was a SOLID rectangle (filled its bbox, e.g. a 2x2
# or 2x3 block), the upscaled output was a single solid 8 block -- a degenerate
# single-colour output. Now the frequent shape is forced NON-bbox-filling so the
# upscaled output always shows shape-vs-background structure.
VERSION = "3.1.0"
TASK_ID = "fb7c915894d6"
SUMMARY = (
    "0-bg grid (size varies) with: (a) K (2-5) COPIES of a FREQUENT random "
    "polyomino SHAPE (4-7 cells); (b) 1-4 DISTRACTOR shapes, each a random "
    "polyomino with a DIFFERENT normalized shape (and distinct from each "
    "other), each appearing exactly ONCE. Every blob is painted a DISTINCT "
    "non-0 color drawn without replacement from {1..9} (the rule is "
    "COLOR-BLIND). Blobs are placed with 4-adjacent buffer separation. Rule "
    "(FIND THE MOST-FREQUENT NORMALIZED SHAPE, COUNT ITS FREQUENCY K, OUTPUT "
    "THAT SHAPE SCALED K× IN COLOR 8): GROUP all blobs by NORMALIZED SHAPE "
    "(color-blind, exact orientation). FIND the most-frequent class "
    "(tie-break top-most, left-most). Let K = its frequency. UPSCALE that "
    "shape by K (each cell -> K×K block) and PAINT every block color 8 on a "
    "bg-0 canvas of size (sh*K, sw*K). Input colors are DROPPED. Net: the "
    "dominant shape's mass × frequency yields a cyan-8 scaled output. (Was a "
    "fixed 9-shape bank; now shapes are generated randomly.)"
)

# Rivals: 'always emit X×X output' refuted by >=2 demos with different output
# bboxes. 'pick the largest object' refuted by >=1 demo where the frequent
# shape is smaller than a distractor. 'output uses input color' refuted by any
# demo (always color 8). 'scale by total object count' refuted by >=1 demo
# where K != total. 'scale by 3' refuted by >=1 demo with K != 3.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    ">=2 distinct normalized shape classes; one (the 'frequent') appears K times, K >= 2",
    "every other shape class appears exactly once",
    "blobs are placed with 4-adjacent clearance from each other",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = (
    "no_frequent",         # all shapes appear once → no majority
    "all_same_shape",      # only one shape class → K = total objects, no distractors
    "single_blob",         # only one object → K = 1, output equals shape
    "tied_frequency",      # two shape classes tied for most-frequent → tie-break by position only
)
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "by difficulty", "valid": "10..24"},
    "grid_w":            {"type": "int", "default": "by difficulty", "valid": "12..26"},
    "palette_kind":      {"type": "str", "default": "default", "valid": "default"},
    "shape_size":        {"type": "int", "default": "frequent rng 4..7 / distractor rng 2..6 cells", "valid": "2..7"},
    "K":                 {"type": "int", "default": "by difficulty", "valid": "2..5"},
    "n_distractors":     {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":      {"type": "int", "default": "K + n_distractors", "valid": "3..9"},
    "position_bias":     {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..9", "valid": "3..9"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "default",
                          "valid": "default|no_frequent|all_same_shape|single_blob|tied_frequency"},
}

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _normalized(cells):
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return tuple(sorted((r - minr, c - minc) for r, c in cells))


def _shape_bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _rand_poly(rng, size, maxdim=5):
    for _ in range(40):
        cells = {(0, 0)}
        frontier = [(0, 0)]
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in _CARD
                    if (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc)
            frontier.append(nc)
        norm = list(_normalized(cells))
        if (len(norm) == size and max(r for r, _ in norm) + 1 <= maxdim
                and max(c for _, c in norm) + 1 <= maxdim):
            return norm
    return [(0, 0), (0, 1), (1, 0)]


def _distinct_shape(rng, used, size):
    """A random polyomino whose normalized form is not already used."""
    for _ in range(40):
        s = _rand_poly(rng, size)
        if _normalized(s) not in used:
            return s
    return None


def _difficulty_K_range(difficulty):
    if difficulty == "easy":
        return 2, 3
    if difficulty == "hard":
        return 3, 5
    return 2, 4


def _difficulty_grid(difficulty):
    if difficulty == "easy":
        return 11, 14, 13, 16
    if difficulty == "hard":
        return 17, 22, 19, 24
    return 14, 18, 16, 20


def _try_place(g, shape, color, rng, *, max_tries):
    """Place shape so no cell is 4-adjacent to any existing non-zero cell."""
    h, w = len(g), len(g[0])
    sh, sw = _shape_bbox(shape)
    for _ in range(max_tries):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        ok = True
        for dr, dc in shape:
            r, c = r0 + dr, c0 + dc
            if g[r][c] != 0:
                ok = False
                break
            for ar, ac in _CARD:
                nr, nc = r + ar, c + ac
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            for dr, dc in shape:
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
    K_lo, K_hi = _difficulty_K_range(difficulty)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        # Frequent shape + frequency K (output bbox sh*K, sw*K stays <= 30 since
        # maxdim 5 and K <= 5 -> 25). Force the shape NON-bbox-filling so the
        # upscaled colour-8 output isn't a single solid block.
        freq_shape = _rand_poly(rng, rng.randint(4, 7))
        for _ in range(40):
            fh, fw = _shape_bbox(freq_shape)
            if fh * fw > len(freq_shape):      # bbox has >=1 empty cell
                break
            freq_shape = _rand_poly(rng, rng.randint(4, 7))
        K = rng.randint(K_lo, K_hi)
        used = {_normalized(freq_shape)}

        # Distractors: each a distinct normalized shape, appearing once.
        n_distractors = rng.randint(1, 4)
        distractors = []
        for _ in range(n_distractors):
            d = _distinct_shape(rng, used, rng.randint(2, 6))
            if d is None:
                continue
            used.add(_normalized(d))
            distractors.append(d)
        if not distractors:
            continue

        palette = list(range(1, 10))
        rng.shuffle(palette)
        needed = K + len(distractors)
        colors = palette[:needed]

        g = full_grid(h, w, 0)
        ok = True
        for i in range(K):
            if not _try_place(g, freq_shape, colors[i], rng, max_tries=120):
                ok = False
                break
        if not ok:
            continue
        for i, cells in enumerate(distractors):
            if not _try_place(g, cells, colors[K + i], rng, max_tries=120):
                ok = False
                break
        if ok:
            return g

    raise ValueError("could not realize most-frequent-shape layout")


def self_check(grid, *, difficulty=None, meta=None):
    """The most-frequent normalized shape (the one upscaled to the colour-8
    output) must NOT fill its bbox, else the output is a single solid 8 block."""
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in seen:
                comp = []; stack = [(r, c)]; seen.add((r, c))
                while stack:
                    cr, cc = stack.pop(); comp.append((cr, cc))
                    for dr, dc in _CARD:
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                                and (nr, nc) not in seen):
                            seen.add((nr, nc)); stack.append((nr, nc))
                comps.append(comp)
    if not comps:
        return ["no blobs -> empty output"]
    from collections import Counter
    freq = Counter(_normalized(c) for c in comps)
    shape, count = freq.most_common(1)[0]
    if count < 2:
        return ["no shape class repeats (no frequency K>=2 majority)"]
    sh, sw = _shape_bbox(list(shape))
    if sh * sw <= len(shape):
        return ["the frequent shape fills its bbox -> upscaled output is a "
                "single solid 8 block (degenerate)"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = full_grid(h, w, 0)
    L = [(0, 0), (1, 0), (1, 1)]
    O = [(0, 0), (0, 1), (1, 0), (1, 1)]
    I3 = [(0, 0), (0, 1), (0, 2)]
    if name == "no_frequent":
        paint_at(g, 1, 1, L, 2)
        paint_at(g, 1, w - 4, O, 3)
        paint_at(g, h - 4, 2, I3, 4)
        return g
    if name == "all_same_shape":
        paint_at(g, 1, 1, L, 2)
        paint_at(g, 1, w - 4, L, 3)
        paint_at(g, h - 4, 2, L, 4)
        paint_at(g, h - 4, w - 4, L, 5)
        return g
    if name == "single_blob":
        paint_at(g, h // 2, w // 2, L, 4)
        return g
    if name == "tied_frequency":
        # Two classes each appearing twice → tie on count, broken by position.
        paint_at(g, 1, 1, L, 2)
        paint_at(g, 1, w - 4, L, 3)
        paint_at(g, h - 4, 2, O, 4)
        paint_at(g, h - 4, w - 4, O, 5)
        return g
    return g
