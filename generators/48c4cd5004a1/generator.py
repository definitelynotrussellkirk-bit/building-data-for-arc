"""Generator for 9ba4a9aa.

Rule: several 3x3 ICONS (uniform border color != bg, contrasting 1-cell center)
sit on the grid. Outside the icons are singleton DOTS. The most frequent dot
color touches exactly one icon; the rule outputs that icon's 3x3 signature
(border b around a center ctr).

The old generator FIXED the grid at 14x14 with 4 icons at fixed corner slots and
a constrained color assignment, so the input never varied (shape-locked-in) and
the output (b,ctr) pairs collided (distinct=61, dup 42%). Now: the grid size
varies (rule reads h,w), the icon count/positions vary, and each icon's
(border,center) is a free random pair -> far more distinct outputs.

Combinatorial axes: grid size, icon count/positions, per-icon border/center
colors, the answer icon, dot colors/counts.
Degenerates: no_icons, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "48c4cd5004a1"
RULE_HASH = "113befc8d552"  # canonical rule this generator was written against
VERSION = "2.0.1"  # shape-locked-in + distinct=61/dup 42%: gen FIXED 14x14 with 4 fixed-slot icons and constrained colours. Rule reads h,w dynamically and outputs the answer icon's (border,center). Now varied grid size + icon count/positions + free per-icon (b,ctr) pairs; majority dot colour placed adjacent to exactly one (answer) icon.
TASK_ID = "48c4cd5004a1"
SUMMARY = (
    "0-bg grid (size varies) with several 3x3 ICONS (uniform border color, "
    "contrasting 1-cell center) at separated positions, plus singleton DOTS. "
    "The MOST FREQUENT dot color is placed adjacent to exactly one (answer) "
    "icon; other dot colors are fewer. Rule: find the icon adjacent to the "
    "majority dot color and output its 3x3 signature (border around center)."
)

INVARIANTS = [
    "the background is zero",
    "several 3x3 icons have a uniform border and a contrasting center",
    "outside singleton dots are not part of any icon",
    "the most frequent dot color touches exactly one icon",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_icons", "no_dots", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_icons":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "4..9"},
    "position_bias":  {"type": "str", "default": "scattered_icons",
                       "valid": "scattered_icons"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "4..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _icon(g, r, c, border, center):
    for dr in range(3):
        for dc in range(3):
            g[r + dr][c + dc] = border
    g[r + 1][c + 1] = center


def _free(g, r0, c0, r1, c1, margin=2):
    h, w = len(g), len(g[0])
    for r in range(r0 - margin, r1 + margin + 1):
        for c in range(c0 - margin, c1 + margin + 1):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return 0 <= r0 and 0 <= c0 and r1 < h and c1 < w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  task_id=TASK_ID, version=VERSION,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 12, 14); W = ctx.draw_int("grid_w", 12, 14)
        nicons = ctx.draw_int("n_icons", 3, 3)
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 18, 24); W = ctx.draw_int("grid_w", 18, 24)
        nicons = ctx.draw_int("n_icons", 4, 5)
    else:
        H = ctx.draw_int("grid_h", 14, 18); W = ctx.draw_int("grid_w", 14, 18)
        nicons = ctx.draw_int("n_icons", 3, 4)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(H, W, 0)
        placed = []
        for _i in range(nicons):
            for _t in range(120):
                r = rng.randint(1, H - 4); c = rng.randint(1, W - 4)
                if _free(g, r, c, r + 2, c + 2):
                    b = rng.randint(1, 9)
                    ctr = rng.choice([x for x in range(1, 10) if x != b])
                    _icon(g, r, c, b, ctr)
                    placed.append((r, c, b, ctr))
                    break
        if len(placed) < 3:
            continue
        answer = rng.randrange(len(placed))
        ar, ac, _b, _ctr = placed[answer]
        # majority dot color: not an icon border (keep it a clean "dot")
        used_borders = {p[2] for p in placed}
        dotpool = [x for x in range(1, 10) if x not in used_borders] or [x for x in range(1, 10)]
        rng.shuffle(dotpool)
        mc = dotpool[0]
        # adjacent bg cells around the answer icon
        adj = []
        for dc in range(3):
            adj += [(ar - 1, ac + dc), (ar + 3, ac + dc)]
        for dr in range(3):
            adj += [(ar + dr, ac - 1), (ar + dr, ac + 3)]
        adj = [(r, c) for (r, c) in adj if 0 <= r < H and 0 <= c < W and g[r][c] == 0]
        rng.shuffle(adj)
        nmaj = max(3, min(len(adj), rng.randint(3, 5)))
        for (r, c) in adj[:nmaj]:
            g[r][c] = mc
        maj_count = min(nmaj, len(adj))
        if maj_count < 2:
            continue
        # other (minority) dots elsewhere, away from every icon, fewer than mc
        others = dotpool[1:1 + rng.randint(1, 3)]
        for oc in others:
            for _ in range(rng.randint(1, max(1, maj_count - 1))):
                for _t in range(40):
                    r = rng.randint(0, H - 1); c = rng.randint(0, W - 1)
                    if g[r][c] == 0 and _free(g, r, c, r, c, margin=2):
                        g[r][c] = oc
                        break
        return g
    raise ValueError("could not realize 48c4 layout")


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_icons":
        g[6][6] = 3
        return g
    if name == "no_dots":
        for r, c in [(1, 1), (1, 9), (9, 1), (9, 9)]:
            _icon(g, r, c, 3, 4)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=3 distinct non-0 colors (icon borders, icon centers, dot colors)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 3:
        errors.append(f"expected >=3 distinct non-0 colors (icon borders, centers, dots), found {len(colors)}")
    return errors
