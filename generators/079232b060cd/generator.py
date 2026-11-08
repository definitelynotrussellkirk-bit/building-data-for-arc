"""Generator for arc_puzzle_bank_21_set20_bundle:easy_p05 — same-color border seeds beam inward.

Rule: each border seed fires a beam of its color inward, stopping at
optional 8-walls.

Combinatorial axes: grid_h, grid_w, seed_count, texture
(plain|crossing|pass_through|corner_seed|near_wall).
Degenerates: no_seeds, all_walls (both identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "079232b060cd"
VERSION = "2.0.0"
TASK_ID = "079232b060cd"
SUMMARY = (
    "Every non-{0,8} border cell fires an inward beam of ITS OWN "
    "color (top/bottom borders beam vertically incl. corners, side "
    "borders horizontally). Beams stop only at 8-walls, pass THROUGH "
    "colored cells without overwriting, and the first writer wins at "
    "crossings (vertical seeds trace before horizontal). (Was: all "
    "seeds one color, no crossings/pass-throughs/corners exercised.)"
)

# Rivals: 'beams share one color' refuted by per-seed colors. 'any
# nonzero blocks' refuted by pass_through (beam continues past a
# colored cell, which stays). 'later beams overwrite' refuted by
# crossing boards (the vertical beam keeps the shared cell). 'corners
# do nothing' refuted by corner seeds beaming vertically. 3-4 demos.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0; walls are color 8",
    "seeds sit on the border, never color 0 or 8",
    ">=1 beam paints >=1 cell on main-path boards",
]

DEGENERATE_TEXTURES = ("no_seeds", "all_walls")
HELPFUL_TEXTURES = ("plain", "crossing", "pass_through", "corner_seed",
                    "near_wall")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "grid_w":     {"type": "int", "default": "rng 8..13", "valid": "5..16"},
    "seed_count": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "plain|crossing|pass_through|corner_seed|"
                            "near_wall|no_seeds|all_walls",
                   "doc": "crossing: guaranteed beam intersection (vertical "
                          "wins); pass_through: interior colored cell on a "
                          "beam path (beam continues, cell stays); "
                          "corner_seed: a corner beams vertically; "
                          "near_wall: wall adjacent to a seed (empty beam)."},
}

_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _dir_of(h, w, r, c):
    if r == 0:
        return 1, 0
    if r == h - 1:
        return -1, 0
    if c == 0:
        return 0, 1
    return 0, -1


def _mirror(g):
    """Exact rule emulation: seed order = per-column top,bottom then
    per-row (1..h-2) left,right; paint only onto zeros; stop at 8."""
    h, w = len(g), len(g[0])
    seeds = []
    for c in range(w):
        if g[0][c] not in (0, 8):
            seeds.append((0, c, 1, 0, g[0][c]))
        if g[h - 1][c] not in (0, 8):
            seeds.append((h - 1, c, -1, 0, g[h - 1][c]))
    for r in range(1, h - 1):
        if g[r][0] not in (0, 8):
            seeds.append((r, 0, 0, 1, g[r][0]))
        if g[r][w - 1] not in (0, 8):
            seeds.append((r, w - 1, 0, -1, g[r][w - 1]))
    out = [row[:] for row in g]
    for sr, sc, dr, dc, v in seeds:
        r, c = sr + dr, sc + dc
        while 0 <= r < h and 0 <= c < w and g[r][c] != 8:
            if out[r][c] == 0:
                out[r][c] = v
            r += dr
            c += dc
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "crossing", "pass_through",
                        "corner_seed", "near_wall"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        seed_count = ctx.draw_int("seed_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        seed_count = ctx.draw_int("seed_count", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 8, 13)
        seed_count = ctx.draw_int("seed_count", 2, 5)
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        placed = []
        if texture == "crossing":
            # a top seed and a side seed whose beams must intersect
            ct = rng.randint(1, w - 2)
            rs = rng.randint(1, h - 2)
            g[0][ct] = rng.choice(_SEED_COLORS)
            side = rng.choice((0, w - 1))
            g[rs][side] = rng.choice(_SEED_COLORS)
            placed += [(0, ct), (rs, side)]
        elif texture == "corner_seed":
            corner = rng.choice(((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)))
            g[corner[0]][corner[1]] = rng.choice(_SEED_COLORS)
            placed.append(corner)

        border = ([(0, c) for c in range(1, w - 1)]
                  + [(h - 1, c) for c in range(1, w - 1)]
                  + [(r, 0) for r in range(1, h - 1)]
                  + [(r, w - 1) for r in range(1, h - 1)])
        rng.shuffle(border)
        for r, c in border:
            if len(placed) >= seed_count:
                break
            if g[r][c] != 0:
                continue
            g[r][c] = rng.choice(_SEED_COLORS)
            placed.append((r, c))

        # optional walls on some beam paths
        for i, (r, c) in enumerate(placed):
            dr, dc = _dir_of(h, w, r, c)
            path = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                path.append((rr, cc))
                rr += dr
                cc += dc
            if not path:
                continue
            if texture == "near_wall" and i == 0:
                g[path[0][0]][path[0][1]] = 8  # beam paints nothing
            elif texture == "pass_through" and i == 0 and len(path) >= 3:
                # interior colored cell ON the path: not 8, so the
                # beam continues past it and the cell survives
                pr, pc = path[rng.randint(1, len(path) - 2)]
                if g[pr][pc] == 0:
                    g[pr][pc] = rng.choice(_SEED_COLORS)
            elif rng.random() < 0.45 and len(path) >= 3:
                wr, wc = path[rng.randint(1, len(path) - 1)]
                if g[wr][wc] == 0:
                    g[wr][wc] = 8

        out = _mirror(g)
        if out == g:
            continue  # every beam blocked — boring board
        if texture == "crossing":
            # verify the beams genuinely share a painted cell
            ct_col = placed[0][1]
            rs_row = placed[1][0]
            if out[rs_row][ct_col] == 0 or g[rs_row][ct_col] != 0:
                continue
        return g
    raise ValueError("could not realize beam board")


def _draw_from_degenerate(name, ctx):
    """no_seeds — blank: identity. all_walls — interior full of 8s:
    every beam stops immediately, identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 8, 12)
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        return g
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            g[r][c] = 8
    for _ in range(rng.randint(1, 3)):
        c = rng.randint(1, w - 2)
        g[rng.choice((0, h - 1))][c] = rng.choice(_SEED_COLORS)
    return g


def _border_cells(grid):
    h, w = len(grid), len(grid[0])
    cells = []
    for c in range(w):
        cells.append((0, c))
        cells.append((h - 1, c))
    for r in range(1, h - 1):
        cells.append((r, 0))
        cells.append((r, w - 1))
    return cells


def self_check(grid, *, difficulty=None, meta=None):
    problems = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a nonempty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows are ragged"]
    if h < 5 or w < 5:
        problems.append("beam boards should be at least 5x5")
    bad_vals = [v for row in grid for v in row if v not in range(10)]
    if bad_vals:
        problems.append("grid contains values outside 0..9")
    border = set(_border_cells(grid))
    seeds = [(r, c, grid[r][c]) for r, c in border if grid[r][c] not in (0, 8)]
    interior_colored = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                        if grid[r][c] not in (0, 8)]
    if not seeds and not interior_colored:
        problems.append("default path should include at least one colored seed or pass-through marker")
    for r, c, v in seeds:
        if v not in _SEED_COLORS:
            problems.append("border seed uses a non-beam color")
            break
        dr, dc = _dir_of(h, w, r, c)
        if (r, c) in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)) and dc != 0:
            problems.append("corner seeds should use the vertical top/bottom direction")
            break
    mirrored = _mirror(grid)
    if mirrored == grid:
        problems.append("default path emitted an identity/no-fired-beam board")
    if any(mirrored[r][c] not in range(10) for r in range(h) for c in range(w)):
        problems.append("mirror emulation produced invalid colors")
    return problems
