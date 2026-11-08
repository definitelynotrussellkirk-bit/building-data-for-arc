"""Generator for 20b:m134 — select largest legend-color blob, crop, flip-lr.

Rule: legend color L = g[0][0]. Clear (0,0). Among objects of color L pick the
LARGEST, crop it to its bbox, and flip it left-right. That flipped crop is the
output — so the OUTPUT SHAPE is the target blob's bbox.

FLAGGED: prior version made the legend blob only 3-4 cells, so the output was a
tiny near-fixed shape (uniq_out ~0.24, out_shapes 2). The fix is to make the
target blob large and varied — that is the sole driver of output diversity here.

Rule-safe diversity: grid size, legend blob SIZE and SHAPE (the output bbox),
legend color, distractor colors/shapes, and smaller same-color decoys (the rule
still picks the largest). The legend blob is kept LR-asymmetric so the flip is
visible.
Rule-LOCKED: g[0][0] is the legend color (cleared before object detection); the
chosen object must be the strictly-largest of the legend color.
Degenerates: no_legend, no_legend_blob, lr_symmetric_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f7aca7ec2012"
VERSION = "3.1.0"  # canonical-scale object count: fewer distractors, still varied asymmetric legend crop
TASK_ID = "f7aca7ec2012"
SUMMARY = (
    "0-bg grid (size varies). (a) LEGEND color at (0,0) from {1..9}. (b) ONE big "
    "BODY BLOB in the legend color (5-25 cells, LR-asymmetric so the flip is "
    "visible), away from the corner. (c) Optional smaller SAME-COLOR decoy blobs "
    "(strictly smaller, so the rule's 'largest' pick is unambiguous). (d) Several "
    "DISTRACTOR blobs in other colors. Rule: read legend L=g[0][0], clear (0,0), "
    "take the largest color-L object, crop to bbox, flip left-right; emit the "
    "flipped crop. Net: the legend color's body blob is extracted and horizontally "
    "mirrored. (Was: 3-4 cell body blob -> tiny fixed output.)"
)

INVARIANTS = [
    "background is 0",
    "(0,0) holds the legend color",
    "exactly one strictly-largest blob of the legend color (the target), away from the corner",
    "the target blob is LR-asymmetric so flip-lr changes it",
    "distractor / decoy blobs never exceed the target size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_legend_blob", "lr_symmetric_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9-12 easy / 12-16 med / 16-22 hard", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 12-18 med / 16-24 hard", "valid": "8..26"},
    "legend_size":    {"type": "int", "default": "5-9 easy / 8-16 med / 12-25 hard", "valid": "4..28"},
    "n_decoy_legend": {"type": "int", "default": "0 easy / 0-1 med / 0-2 hard", "valid": "0..3"},
    "n_distractor":   {"type": "int", "default": "1-2 easy / 2-3 med / 2-4 hard", "valid": "0..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distinct_colors": {"type": "int", "default": "up to 5", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _asymmetric_lr(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    rmin, cmin, cmax = min(rs), min(cs), max(cs)
    norm = {(r - rmin, c - cmin) for r, c in cells}
    flipped = {(r, (cmax - cmin) - c) for r, c in norm}
    return norm != flipped


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, ls, dl, nd = (9, 11), (10, 14), (4, 7), (0, 0), (1, 1)
    elif difficulty == "hard":
        hr, wr, ls, dl, nd = (10, 14), (12, 18), (6, 12), (0, 1), (1, 2)
    else:
        hr, wr, ls, dl, nd = (10, 13), (12, 16), (5, 9), (0, 1), (1, 1)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(4, 1 + nd[1] + 2))
        legend = colors[0]
        g[0][0] = legend
        used = {(0, 0)}

        # main legend blob: large, LR-asymmetric, away from the corner
        main_size = rng.randint(*ls)
        main = None
        for _ in range(30):
            cand = grow_blob(rng, h, w, used, main_size, max_attempts=25)
            if cand and _asymmetric_lr(cand):
                main = cand; break
        if main is None:
            continue
        for r, c in main:
            g[r][c] = legend
        used |= main

        # smaller same-color decoys (rule picks largest -> still the main blob)
        for _ in range(rng.randint(*dl)):
            ds = rng.randint(2, max(2, main_size - 1))
            b = grow_blob(rng, h, w, used, ds, max_attempts=25)
            if b:
                for r, c in b:
                    g[r][c] = legend
                used |= b

        # distractor blobs in other colors (also < main size)
        for color in colors[1:]:
            for _ in range(rng.randint(*nd)):
                ds = rng.randint(2, max(2, min(6, main_size - 1)))
                b = grow_blob(rng, h, w, used, ds, max_attempts=25)
                if b:
                    for r, c in b:
                        g[r][c] = color
                    used |= b
        return g

    # deterministic fallback: one asymmetric legend blob
    g = full_grid(9, 11, 0)
    g[0][0] = 4
    for r, c in [(3, 3), (3, 4), (3, 5), (4, 3), (5, 3)]:
        g[r][c] = 4
    for r, c in [(6, 7), (7, 7)]:
        g[r][c] = 6
    return g


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] != color:
                continue
            q = [(sr, sc)]; seen.add((sr, sc)); cells = []
            while q:
                r, c = q.pop(); cells.append((r, c))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Verify legend-color + unique largest asymmetric blob invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    legend_color = grid[0][0]
    if legend_color == 0:
        errs.append("(0,0) is 0 — expected a non-zero legend color")
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if flat.count(0) == 0:
        errs.append("no background (0) cells")
    comps = [c for c in _components(grid, legend_color) if (0, 0) not in c]
    if not comps:
        errs.append(f"no body blob of legend color {legend_color}")
        return errs
    sizes = sorted((len(c) for c in comps), reverse=True)
    if len(sizes) > 1 and sizes[0] <= sizes[1]:
        errs.append("legend target is not strictly larger than same-color decoys")
    target = max(comps, key=len)
    if len(target) < 4:
        errs.append("legend target blob too small")
    if not _asymmetric_lr(target):
        errs.append("legend target blob is LR-symmetric; flip would be invisible")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Blobs but (0,0) is empty — rule's "color at (0,0)" lookup finds no legend.
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 4
        for r, c in [(6, 6), (6, 7)]: g[r][c] = 6
        return g
    if name == "no_legend_blob":
        # Legend present but no body blob of that color — rule finds no target.
        g[0][0] = 4
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        for r, c in [(6, 6), (6, 7)]: g[r][c] = 7
        return g
    if name == "lr_symmetric_blob":
        # Legend blob is LR-symmetric — flip-lr is identity, rule's effect invisible.
        g[0][0] = 4
        for r, c in [(3, 3), (3, 4), (3, 5), (4, 4)]: g[r][c] = 4
        for r, c in [(6, 6), (6, 7)]: g[r][c] = 6
        return g
    return g
