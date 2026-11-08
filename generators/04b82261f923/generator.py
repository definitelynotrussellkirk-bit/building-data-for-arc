"""Generator for 11e1fe23.

Rule: three colored dots imply a gray midpoint and one-step colored
spokes.

Combinatorial axes (8): grid_h/w, radius, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_dots, single_dot, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04b82261f923"
VERSION = "2.1.1"
TASK_ID = "04b82261f923"
SUMMARY = (
    "Exactly three colored dots: a strictly-farthest pair (either "
    "diagonal, vertical, or horizontal — even deltas, integer "
    "midpoint) plus a third dot anywhere nearer to both endpoints. "
    "Rule paints the farthest pair's midpoint gray(5) and one-step "
    "colored spokes from it toward each dot. (Old layout was always "
    "the same NW-SE pair + west dot.)"
)

INVARIANTS = [
    "exactly three nonzero dots are present",
    "the farthest pair is STRICTLY farthest and has an integer "
    "midpoint (both coordinate deltas even)",
    "the third dot sits >=2 from the midpoint (spokes never overwrite it)",
    "pair orientations vary: both diagonals, vertical, horizontal",
]

DEGENERATE_TEXTURES = ("collinear", "full_grid")
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "grid_h":  {"type": "int", "default": "rng 10..14 (hard 14..18)",
                "valid": "7..20", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 10..14 (hard 14..18)",
                "valid": "7..20", "doc": "Grid width."},
    "radius":  {"type": "int", "default": "rng 2..4 (hard 3..5)",
                "valid": "2..7", "doc": "Half-distance of the farthest pair."},
    "texture": {"type": "str", "default": "plain",
                "valid": "plain|collinear|full_grid",
                "doc": "collinear: 3 dots on a line (midpoint = center dot "
                       "area); full_grid: everything non-zero."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if difficulty == "easy":
        h_lo, h_hi, r_lo, r_hi = 10, 12, 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, r_lo, r_hi = 14, 18, 3, 5
    else:
        h_lo, h_hi, r_lo, r_hi = 10, 14, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    max_radius = min(r_hi, (h - 3) // 2, (w - 3) // 2)
    radius = min(ctx.draw_int("radius", r_lo, r_hi), max_radius)
    colors = ctx.draw_distinct_colors("dot_colors", n=3, exclude={0, 5})
    g = full_grid(h, w, 0)

    cr = rng.randint(radius + 1, h - radius - 2)
    cc = rng.randint(radius + 1, w - radius - 2)
    # farthest pair: EVEN deltas through the midpoint, varied orientation
    orient = rng.choice(("diag_main", "diag_anti", "vertical", "horizontal"))
    if orient == "diag_main":
        a = (cr - radius, cc - radius)
        b = (cr + radius, cc + radius)
    elif orient == "diag_anti":
        a = (cr - radius, cc + radius)
        b = (cr + radius, cc - radius)
    elif orient == "vertical":
        a = (cr - radius, cc)
        b = (cr + radius, cc)
    else:
        a = (cr, cc - radius)
        b = (cr, cc + radius)
    pair_dist = abs(a[0] - b[0]) + abs(a[1] - b[1])

    # third dot: strictly closer to both endpoints than the pair span,
    # >=2 from the midpoint, anywhere around the center
    third = None
    for _try in range(200):
        tr = rng.randint(max(0, cr - radius), min(h - 1, cr + radius))
        tc = rng.randint(max(0, cc - radius), min(w - 1, cc + radius))
        if (tr, tc) in (a, b) or (abs(tr - cr) + abs(tc - cc)) < 2:
            continue
        da = abs(tr - a[0]) + abs(tc - a[1])
        db = abs(tr - b[0]) + abs(tc - b[1])
        if da < pair_dist and db < pair_dist:
            third = (tr, tc)
            break
    if third is None:
        third = (cr, cc - radius) if orient != "horizontal" else (cr - radius, cc)

    g[a[0]][a[1]] = colors[0]
    g[b[0]][b[1]] = colors[1]
    g[third[0]][third[1]] = colors[2]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: exactly 3 nonzero dots; farthest pair (by L2 squared) is
    strictly farthest and has even coordinate deltas (integer midpoint)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    dots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(dots) != 3:
        msgs.append(f"expected exactly 3 nonzero dots, got {len(dots)}")
        return msgs
    pairs = [(dots[0], dots[1]), (dots[0], dots[2]), (dots[1], dots[2])]
    # Use L2-squared to identify farthest pair (avoids float issues)
    dists2 = [(b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 for a, b in pairs]
    max_d2 = max(dists2)
    tied = sum(1 for d in dists2 if d == max_d2)
    if tied > 1:
        msgs.append(
            f"farthest pair not unique by L2 (dist² {max_d2} shared by {tied} pairs)"
        )
    idx = dists2.index(max_d2)
    a, b = pairs[idx]
    if (b[0] - a[0]) % 2 != 0 or (b[1] - a[1]) % 2 != 0:
        msgs.append(
            f"farthest pair {a}↔{b} has odd coordinate deltas "
            f"({b[0]-a[0]}, {b[1]-a[1]}); midpoint would not be integer"
        )
    return msgs


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (3+ dots always; the
    old no_dots/single_dot degenerates crashed at (second dots)).

    collinear — 3 dots on one line: midpoint of the endpoints.
    full_grid — everything non-zero: the first three scan cells decide.
    """
    rng = ctx.draw_rng("degenerate_layout")
    n = ctx.draw_int("grid_h", 10, 13)
    g = full_grid(n, n, 0)
    if name == "full_grid":
        color = rng.randint(1, 4)
        for r in range(n):
            for c in range(n):
                g[r][c] = color
        return g
    # collinear: three dots on a row, even end separation
    r = rng.randint(1, n - 2)
    c0 = rng.randint(0, n - 7)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    g[r][c0] = colors[0]
    g[r][c0 + 3] = colors[2]
    g[r][c0 + 6] = colors[1]
    return g
