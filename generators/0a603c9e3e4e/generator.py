"""Generator for arc_additional_puzzles_21_set19_bundle:E130 —
flipped bbox-crop of the shape across a 5-divider.

Rule: first full 5-row (else full 5-col) is the guide. Non-0/5 cells
reflect across it; output = bbox crop of the reflected cells, painted
ENTIRELY in the first (scan-order) shape cell's color. Net: the crop
is the shape flipped (UD for a row guide, LR for a col guide).
no_shape CRASHES ((first '())) — never generated. A missing/broken
divider degrades via #f-coercion to a flip about row/col 0 (still a
valid flipped crop) — kept as documented degenerates.

Combinatorial axes: grid_h/w, divider position, side, blob shapes,
texture (plain|multicolor|both_guides).
Degenerates: no_divider, broken_divider (degraded but valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a603c9e3e4e"
VERSION = "3.1.1"  # + self_check
TASK_ID = "0a603c9e3e4e"
SUMMARY = (
    "A full 5-line mirrors the shape; output is the flipped bbox crop "
    "in the FIRST cell's color - multicolor boards collapse to one "
    "color (bridge-verified). Divider position and shape side are "
    "free (was: centered divider, 5 fixed shapes, top/left side "
    "only). both_guides boards have a full row AND column of 5s "
    "(the row wins: rule checks guide-col #f via the row-first "
    "reflection branch)."
)

# Rivals: 'output keeps per-cell colors' refuted by multicolor
# collapse. 'shape sits left/above only' refuted by free sides.
# 'crop is unflipped' refuted by asymmetric shapes. 3 demos with
# both orientations + >=1 asymmetric shape.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 non-0/5 cell ALWAYS (none crashes the rule)",
    "main-path boards: exactly one full 5-line; shape clear of it",
    "shapes are asymmetric often enough that the flip is visible",
]

DEGENERATE_TEXTURES = ("no_divider", "broken_divider")
HELPFUL_TEXTURES = ("plain", "multicolor", "both_guides")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..12", "valid": "5..14"},
    "grid_w":  {"type": "int", "default": "rng 7..12", "valid": "5..14"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|multicolor|both_guides|no_divider|"
                         "broken_divider",
                "doc": "multicolor: shape colors collapse to the first "
                       "scan cell's; both_guides: full 5-row AND 5-col "
                       "(row reflection wins via the col branch)."},
}

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _grow(rng, k, max_h, max_w):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(300):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mirror(g):
    h, w = len(g), len(g[0])
    grow_ = next((r for r in range(h) if all(v == 5 for v in g[r])), None)
    gcol = next((c for c in range(w) if all(g[r][c] == 5 for r in range(h))),
                None)
    cells = [(r, c) for r in range(h) for c in range(w)
             if g[r][c] not in (0, 5)]
    if not cells:
        return None
    color = g[cells[0][0]][cells[0][1]]
    if gcol is None:
        gr = grow_ if grow_ is not None else 0
        refl = [(2 * gr - r, c) for r, c in cells]
    else:
        refl = [(r, 2 * gcol - c) for r, c in cells]
    r1 = min(r for r, _ in refl)
    c1 = min(c for _, c in refl)
    out = [[0] * (max(c for _, c in refl) - c1 + 1)
           for _ in range(max(r for r, _ in refl) - r1 + 1)]
    for r, c in refl:
        out[r - r1][c - c1] = color
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 non-0/5 cell; >=1 color-5 cell (the guide divider)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    shape_cells = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] != 0 and grid[r][c] != 5]
    guide_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not shape_cells:
        errs.append("no non-0/5 cells: rule crashes (first of empty list)")
    if not guide_cells:
        errs.append("no color-5 guide cells: degraded mode (flip about row/col 0)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "multicolor", "both_guides"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        k = (3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        k = (5, 7)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        k = (3, 8)
    rng = ctx.draw_rng("layout")

    horiz = rng.random() < 0.5  # full 5-ROW guide
    g = full_grid(h, w, 0)
    if texture == "both_guides":
        gr = rng.randint(2, h - 3)
        gc = rng.randint(2, w - 3)
        for c in range(w):
            g[gr][c] = 5
        for r in range(h):
            g[r][gc] = 5
        # rule reflects across the COLUMN when one exists
        side = rng.choice([-1, 1])
        lo, hi = (0, gc - 1) if side < 0 else (gc + 1, w - 1)
        band_w = hi - lo + 1
        shape = _grow(rng, rng.randint(*k), max(1, h - 2), band_w)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.choice([r for r in range(0, h - sh + 1)
                         if r + sh <= gr or r > gr] or [0])
        c0 = rng.randint(lo, hi - sw + 1)
        # avoid the 5-row: nudge shape fully above or below it
        rows_used = range(r0, r0 + sh)
        if gr in rows_used:
            r0 = gr + 1 if gr + 1 + sh <= h else max(0, gr - sh)
        for r, c in shape:
            g[r0 + r][c0 + c] = rng.choice(_COLORS)
    elif horiz:
        gr = rng.randint(2, h - 3)
        for c in range(w):
            g[gr][c] = 5
        side = rng.choice([-1, 1])
        lo, hi = (0, gr - 1) if side < 0 else (gr + 1, h - 1)
        shape = _grow(rng, rng.randint(*k), hi - lo + 1, w)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.randint(lo, hi - sh + 1)
        c0 = rng.randint(0, w - sw)
        for r, c in shape:
            g[r0 + r][c0 + c] = rng.choice(_COLORS)
    else:
        gc = rng.randint(2, w - 3)
        for r in range(h):
            g[r][gc] = 5
        side = rng.choice([-1, 1])
        lo, hi = (0, gc - 1) if side < 0 else (gc + 1, w - 1)
        shape = _grow(rng, rng.randint(*k), h, hi - lo + 1)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(lo, hi - sw + 1)
        for r, c in shape:
            g[r0 + r][c0 + c] = rng.choice(_COLORS)

    if texture != "multicolor":
        color = rng.choice(_COLORS)
        for r in range(h):
            for c in range(w):
                if g[r][c] not in (0, 5):
                    g[r][c] = color
    else:
        # ensure >=2 colors actually present
        cells = [(r, c) for r in range(h) for c in range(w)
                 if g[r][c] not in (0, 5)]
        if len({g[r][c] for r, c in cells}) < 2 and len(cells) >= 2:
            ca, cb = rng.sample(_COLORS, 2)
            g[cells[0][0]][cells[0][1]] = ca
            g[cells[1][0]][cells[1][1]] = cb
    return g


def _draw_from_degenerate(name, ctx):
    """no_divider — shape, zero 5s: guide arithmetic degrades to a
    flip about row 0 (valid flipped crop, bridge-verified).
    broken_divider — a 5-line with one shape cell punched in it: no
    full line remains, same degradation; the punched cell joins the
    shape. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    color = rng.choice(_COLORS)
    shape = _grow(rng, rng.randint(3, 5), h - 2, w - 2)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    r0 = rng.randint(0, h - sh - 1)
    c0 = rng.randint(0, w - sw)
    for r, c in shape:
        g[r0 + r][c0 + c] = color
    if name == "broken_divider":
        gr = h - 2 if r0 + sh < h - 2 else h - 1
        for c in range(w):
            g[gr][c] = 5
        g[gr][rng.randint(0, w - 1)] = color
    return g
