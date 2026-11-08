"""Generator for 12997ef3.

Rule: blue template recolored once for each singleton color dot.

Combinatorial axes (8): grid_h/w, n_dots, template_variant, orientation,
palette_kind, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_template, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f1186c4ed123"
VERSION = "1.2.0"  # random blue templates (rule crops any bbox) + honest palette_kind; drop dead anchor_corner
TASK_ID = "f1186c4ed123"
SUMMARY = (
    "A blue (color-1) template (cropped to its bbox) is replicated once per "
    "singleton color dot, each copy recolored to that dot's color. Dots all in "
    "ONE column -> vertical stack (th*n x tw); dots spread across columns -> "
    "horizontal concat (th x tw*n). Templates are both curated and randomly "
    "generated (varied shape/size, not necessarily 4-connected, as in "
    "canonical); dot count, colors (palette_kind), grid shape all vary."
)

INVARIANTS = [
    "the blue cells form one bounded template",
    "each non-blue color dot appears exactly once",
    "dots in one column request a vertical stack",
    "dots in multiple columns request horizontal concatenation",
]

ORIENTATIONS = ("vertical", "horizontal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_dots", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

TEMPLATES = [
    [[1, 0, 1], [1, 1, 1], [0, 1, 0]],
    [[1, 1, 0], [0, 1, 1]],
    [[1, 0], [1, 1], [0, 1]],
    [[1, 1, 1], [0, 1, 0], [0, 1, 0]],
]

# dot-color pools per palette_kind (exclude 0 bg and 1 blue-template)
_PALETTE_POOLS = {
    "warm":    [2, 3, 4, 6, 9],
    "cool":    [5, 7, 8, 6],
    "primary": [2, 3, 4],
    "broad":   [2, 3, 4, 5, 6, 7, 8, 9],
}

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "6..20"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..20"},
    "n_dots":         {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "template_variant":{"type": "int", "default": "rng 0..3 (else random)", "valid": "0..3"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "rng (drives dot colors)",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_template(rng):
    """Random blue template cropped to its bbox: varied size, >=2 blue and >=1
    empty cell, not necessarily 4-connected (canonical templates aren't)."""
    for _ in range(40):
        th = rng.randint(2, 5); tw = rng.randint(2, 5)
        cells = [[1 if rng.random() < 0.55 else 0 for _ in range(tw)]
                 for _ in range(th)]
        rows = [i for i in range(th) if any(cells[i])]
        cols = [j for j in range(tw) if any(cells[i][j] for i in range(th))]
        if not rows:
            continue
        cropped = [[cells[i][j] for j in cols] for i in rows]
        nblue = sum(sum(r) for r in cropped)
        nzero = sum(len(r) - sum(r) for r in cropped)
        if nblue >= 2 and nzero >= 1 and (len(cropped) >= 2 or len(cropped[0]) >= 2):
            return cropped
    return TEMPLATES[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
        nd_lo, nd_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi = 13, 20
        nd_lo, nd_hi = 4, 6
    else:
        h_lo, h_hi = 9, 13
        nd_lo, nd_hi = 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    n_dots = ctx.draw_int("n_dots", nd_lo, nd_hi)
    g = full_grid(h, w, 0)
    # template: explicit variant -> curated; otherwise ~half curated, half random
    if "template_variant" in overrides:
        tv = max(0, min(len(TEMPLATES) - 1, int(overrides["template_variant"])))
        tmpl = TEMPLATES[tv]
    elif ctx.draw_int("use_random_tmpl", 0, 1):
        tmpl = _rand_template(rng)
    else:
        tmpl = TEMPLATES[ctx.draw_int("template_variant", 0, len(TEMPLATES) - 1)]
    th, tw = len(tmpl), len(tmpl[0])
    # cap n so the replicated output fits the 30x30 canvas in either orientation
    cap = max(1, min(min(h, w) - 2, 30 // max(th, tw)))
    n_dots = max(1, min(cap, n_dots))
    tr = rng.randint(1, max(1, h - th - 3))
    tc = rng.randint(1, max(1, w - tw - 4))
    for dr, row in enumerate(tmpl):
        for dc, v in enumerate(row):
            if v:
                g[tr + dr][tc + dc] = 1
    # palette_kind selects the dot-color pool (honest axis)
    pk = (overrides.get("palette_kind")
          or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = list(_PALETTE_POOLS.get(pk, _PALETTE_POOLS["broad"]))
    if len(set(pool)) < n_dots:
        pool = list(_PALETTE_POOLS["broad"])
    rng.shuffle(pool)
    colors = pool[:n_dots]
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    if orientation == "vertical":
        c = w - 2
        rows = sorted(rng.sample(range(h), n_dots))
        for color, r in zip(colors, rows):
            g[r][c] = color
    else:
        r = h - 2
        cols = sorted(rng.sample(range(w), n_dots))
        for color, c in zip(colors, cols):
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_template":
        g[h - 2][2] = 2; g[h - 2][5] = 3
        return g
    if name == "no_dots":
        for dr, row in enumerate(TEMPLATES[0]):
            for dc, v in enumerate(row):
                if v:
                    g[2 + dr][2 + dc] = 1
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    blue = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    dots = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1)]
    if len(blue) < 2:
        msgs.append("missing bounded blue template")
    if not (1 <= len(dots) <= 6):
        msgs.append("unexpected dot count")
    dot_colors = [v for _r, _c, v in dots]
    if len(dot_colors) != len(set(dot_colors)):
        msgs.append("dot colors are not distinct singletons")
    if dots:
        rows = {r for r, _c, _v in dots}; cols = {c for _r, c, _v in dots}
        if len(rows) > 1 and len(cols) > 1:
            msgs.append("dots are neither a single row nor a single column")
        blue_set = {(r, c) for r, c in blue}
        if any((r, c) in blue_set for r, c, _v in dots):
            msgs.append("dot overlaps the blue template")
    return msgs
