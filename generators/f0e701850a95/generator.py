"""Generator for 4acc7107.

Rule: two colors with 2 pieces each; rule stacks each color's pieces at
bottom in two columns.

Combinatorial axes (8): grid_h/w, palette_kind, position_bias, halo,
anchor_corner, asymmetry_force, palette_size, attempts.
Degenerates: same_color, no_objects, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f0e701850a95"
VERSION = "1.3.0"  # add executable two-colors/two-components-per-color self_check
TASK_ID = "f0e701850a95"
SUMMARY = (
    "0-bg grid with exactly 2 non-bg colors, each having exactly 2 separated "
    "4-connected pieces (curated + random shapes, bbox <=3x3, halo-separated). "
    "Rule: per color, stack its two pieces bottom-anchored in one column "
    "(originally-leftmost piece on the bottom, rightmost on top, 1-row gap); "
    "the color owning the overall-leftmost piece stacks in column 0, the other "
    "offset right by left-width+1. Colors (palette_kind), shapes, sizes vary."
)

INVARIANTS = [
    "background is 0",
    "exactly 2 non-bg colors",
    "each color has exactly 2 4-connected components",
    "components separated by bg margin >= halo (>=1)",
    "never returns a blank/no-op grid (retries layout, then a guaranteed fallback)",
]

SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
]
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
# dot/shape color pools per palette_kind (2 distinct picked); exclude 0 bg
_PALETTE_POOLS = {
    "warm":    [2, 3, 4, 6, 9],
    "cool":    [5, 7, 8, 6],
    "primary": [1, 2, 3, 4],
    "broad":   [1, 2, 3, 4, 5, 6, 7, 8, 9],
}
DEGENERATE_TEXTURES = ("same_color", "no_objects", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..20", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 10..20", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng (drives the 2 colors)",
                       "valid": "|".join(PALETTE_KINDS)},
    "halo":           {"type": "int", "default": "1", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "2 (rule needs exactly 2 colors)", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_shape(rng):
    """Random connected polyomino (3-5 cells) within a 3x3 bbox so the rule's
    two-column bottom-stack always fits a 10+ wide/tall grid."""
    k = rng.randint(3, 5)
    cells = {(0, 0)}
    tries = 0
    while len(cells) < k and tries < 40:
        tries += 1
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        nr, nc = r + dr, c + dc
        cand = cells | {(nr, nc)}
        mr = min(x for x, _ in cand); mc = min(y for _, y in cand)
        bh = max(x - mr for x, _ in cand) + 1
        bw = max(y - mc for _, y in cand) + 1
        if bh <= 3 and bw <= 3:
            cells = cand
    mr = min(x for x, _ in cells); mc = min(y for _, y in cells)
    return sorted((x - mr, y - mc) for x, y in cells)


def _dims(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return max(rs) + 1, max(cs) + 1


def _try_place(g, cells, color, rng, h, w, halo=1, attempts=30):
    sh, sw = _dims(cells)
    for _ in range(attempts):
        rr = rng.randint(0, h - sh)
        rc = rng.randint(0, w - sw)
        ok = True
        for r in range(max(0, rr - halo), min(h, rr + sh + halo)):
            for c in range(max(0, rc - halo), min(w, rc + sw + halo)):
                if g[r][c] != 0:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        for dr, dc in cells:
            g[rr + dr][rc + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
    else:
        h_lo, h_hi = 12, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    pk = (overrides.get("palette_kind")
          or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = list(_PALETTE_POOLS.get(pk, _PALETTE_POOLS["broad"]))
    if len(set(pool)) < 2:
        pool = list(_PALETTE_POOLS["broad"])
    halo = max(1, min(2, int(overrides.get("halo", 1))))

    # retry the whole layout; never emit a blank no-op
    for _ in range(25):
        palette = rng.sample(pool, 2)
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            placed = 0
            for _i in range(2):
                shape = (rng.choice(SHAPES) if rng.random() < 0.4
                         else _rand_shape(rng))
                if _try_place(g, shape, color, rng, h, w, halo):
                    placed += 1
            if placed != 2:
                ok = False
                break
        if ok:
            return g

    # guaranteed-fit fallback: 4 well-separated single cells (2 per color)
    palette = rng.sample(pool, 2)
    g = full_grid(h, w, 0)
    for (r, c), color in zip([(1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)],
                             [palette[0], palette[0], palette[1], palette[1]]):
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "same_color":
        for dr, dc in SHAPES[0]:
            g[2 + dr][2 + dc] = 2
        for dr, dc in SHAPES[1]:
            g[7 + dr][8 + dc] = 2
        return g
    if name == "no_objects":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components
    if not grid or not grid[0]:
        return ["empty grid"]
    comps = components(grid, same_color=True)
    colors = sorted({comp["color"] for comp in comps})
    errs = []
    if len(colors) != 2:
        errs.append(f"expected exactly two non-bg colors, found {colors}")
    for color in colors:
        count = sum(1 for comp in comps if comp["color"] == color)
        if count != 2:
            errs.append(f"color {color} has {count} components, expected exactly 2")
    return errs
