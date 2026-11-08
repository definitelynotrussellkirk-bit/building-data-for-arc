"""Generator for 0c2ab7de69d1 — one-way fold across a 5-divider.

Rule: the FIRST full 5-row is the fold line d. Every non-0/5 cell
ABOVE it paints 8 at (2d-r, c) if that target is in-bounds AND still
0. Below-divider content never reflects upward, and it BLOCKS
incoming 8s. No divider -> identity (explicit branch).

Combinatorial axes: grid_h/w, divider position, texture
(plain|below_blocker|clip|five_decoy|two_dividers).
Degenerates: no_divider, empty_above (identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c2ab7de69d1"
VERSION = "2.1.0"  # add executable self_check coverage for fold-line invariants
TASK_ID = "0c2ab7de69d1"
SUMMARY = (
    "Above-divider shapes fold below as 8s. below_blocker boards put "
    "content under the line: it does NOT reflect upward and BLOCKS "
    "incoming 8s (was a frozen degenerate); clip boards push the "
    "divider low so reflections fall off-grid; five_decoy boards put "
    "a loose 5-cell above (not reflected - 5s are excluded sources); "
    "two_dividers boards have a second full 5-row (the FIRST wins, "
    "the second behaves as blocking content)."
)

# Rivals: 'fold is symmetric both ways' refuted by below content
# staying. 'reflections overwrite' refuted by blockers. 'every non-0
# reflects' refuted by five_decoy. 3-4 demos incl. >=1 blocker.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 above-divider source whose reflection lands visibly",
    "below_blocker: >=1 reflection target occupied (skipped)",
    "clip: >=1 reflection out of bounds, >=1 visible",
]

DEGENERATE_TEXTURES = ("no_divider", "empty_above")
HELPFUL_TEXTURES = ("plain", "below_blocker", "clip", "five_decoy",
                    "two_dividers")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..15", "valid": "7..20"},
    "grid_w":  {"type": "int", "default": "rng 7..13", "valid": "5..16"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|below_blocker|clip|five_decoy|"
                         "two_dividers|no_divider|empty_above",
                "doc": "below_blocker: under-line content blocks and "
                       "never reflects; clip: low divider, OOB "
                       "reflections; two_dividers: first wins."},
}

_COLORS = (1, 2, 3, 4, 6, 7, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    d = next((r for r in range(h) if all(v == 5 for v in g[r])), None)
    if d is None:
        return [row[:] for row in g]
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            rr = 2 * d - r
            if r < d and v not in (0, 5) and 0 <= rr < h \
                    and g[rr][c] == 0:
                out[rr][c] = 8
    return out


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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "below_blocker", "clip",
                                              "five_decoy",
                                              "two_dividers"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 15)
        w = ctx.draw_int("grid_w", 7, 13)
    rng = ctx.draw_rng("layout")

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        if texture == "clip":
            d = h - rng.randint(2, 3)  # low divider: little room below
        else:
            d = rng.randint(3, h - 4)
        for c in range(w):
            g[d][c] = 5
        if texture == "two_dividers" and d + 2 < h:
            d2 = rng.randint(d + 2, h - 1)
            for c in range(w):
                g[d2][c] = 5
        # above shape
        shape = _grow(rng, rng.randint(3, 6), d, w)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.randint(max(0, d - sh - 2), d - sh)
        c0 = rng.randint(0, w - sw)
        color = rng.choice(_COLORS)
        for r, c in shape:
            g[r0 + r][c0 + c] = color
        if texture == "five_decoy":
            # loose 5 above (excluded source); keep its row not full-5
            for _t in range(60):
                r = rng.randint(0, d - 1)
                c = rng.randrange(w)
                if g[r][c] == 0:
                    g[r][c] = 5
                    break
        if texture == "below_blocker":
            # blocker at >=1 reflection target + extra below content
            tr = [(2 * d - (r0 + r), c0 + c) for r, c in shape]
            inb = [(r, c) for r, c in tr if 0 <= r < h]
            if not inb:
                continue
            br, bc = inb[rng.randrange(len(inb))]
            g[br][bc] = rng.choice(_COLORS)
            for _t in range(40):
                r = rng.randint(d + 1, h - 1)
                c = rng.randrange(w)
                if g[r][c] == 0 and (r, c) not in inb:
                    g[r][c] = rng.choice(_COLORS)
                    break
        out = _mirror(g)
        if out == g:
            continue
        if texture == "clip":
            tr = [(2 * d - (r0 + r), c0 + c) for r, c in shape]
            if all(0 <= r < h for r, _ in tr):
                continue  # nothing clipped: re-roll
        return g
    raise ValueError("could not realize fold board")


def _draw_from_degenerate(name, ctx):
    """no_divider — shape, no full 5-row: explicit identity branch.
    empty_above — divider with nothing above: identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 9, 13)
    w = ctx.draw_int("grid_w", 7, 11)
    g = full_grid(h, w, 0)
    if name == "no_divider":
        shape = _grow(rng, rng.randint(3, 5), h - 2, w - 2)
        color = rng.choice(_COLORS)
        for r, c in shape:
            g[r + 1][c + 1] = color
        return g
    d = rng.randint(2, h - 3)
    for c in range(w):
        g[d][c] = 5
    # content only BELOW (never reflects)
    for _ in range(rng.randint(0, 3)):
        r = rng.randint(d + 1, h - 1)
        g[r][rng.randrange(w)] = rng.choice(_COLORS)
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    dividers = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    if not dividers:
        errs.append("default fold board should contain a full color-5 divider row")
        return errs
    d = dividers[0]
    above = [(r, c) for r in range(d) for c in range(w) if grid[r][c] not in (0, 5)]
    if not above:
        errs.append("default fold board should have at least one above-divider source cell")
    visible = [(2 * d - r, c) for r, c in above
               if 0 <= 2 * d - r < h and grid[2 * d - r][c] == 0]
    if not visible:
        errs.append("at least one above source should fold to a visible empty target")
    return errs
