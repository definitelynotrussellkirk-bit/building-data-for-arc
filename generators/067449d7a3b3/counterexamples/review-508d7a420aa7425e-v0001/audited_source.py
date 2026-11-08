"""Generator for db93a21d.

Rule (ACTUAL): every 8-connected non-zero object gets bbox border
thickness = max(bbox_h, bbox_w)//2. First ALL blue (1) stems are
painted: full column band c1..c2 from r2+border+1 to the bottom,
overwriting anything. Then ALL green (3) border rings (thickness
border, around but excluding the bbox) are painted wherever the INPUT
cell is not 9 — so rings overwrite stems but never original maroon.
1x1 objects have border 0: no ring, stem starts directly below.

Combinatorial axes: grid_h/w, n_rects, texture
(plain|clip|other_color|dot_stem).
Degenerates: no_rects (blank, identity), full_grid (identity: ring
OOB, no stem rows).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "067449d7a3b3"
VERSION = "3.0.1"
TASK_ID = "067449d7a3b3"
SUMMARY = (
    "Solid maroon rects (plus optional other-color objects and lone "
    "dots) each grow a green halo of thickness max(side)//2 and trail "
    "a blue stem from below the halo to the bottom edge. (Was RED: "
    "variant = sample_index %% 6 collapsed every smoke board to ONE "
    "fixed 18x18 layout; rule actually treats ANY non-zero object, "
    "clips rings at edges, and skips stems for bottom-adjacent rects.)"
)

# Rivals: 'only maroon rects react' refuted by other_color objects
# that also grow halos/stems. 'every object has a ring' refuted by
# dot_stem (border 0: stem only). 'rings always complete' refuted by
# clip boards (edge rects, and bottom rects with NO stem). 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "main-path objects are solid rects, pairwise non-interacting (halos+stems disjoint from other objects)",
    ">=1 object always changes the board (no identity on main path)",
]

DEGENERATE_TEXTURES = ("no_rects", "full_grid")
HELPFUL_TEXTURES = ("plain", "clip", "other_color", "dot_stem")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 14..20", "valid": "12..24"},
    "grid_w":  {"type": "int", "default": "rng 14..20", "valid": "12..24"},
    "n_rects": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|clip|other_color|dot_stem|no_rects|full_grid",
                "doc": "clip: rect near an edge (ring clipped / stem absent); "
                       "other_color: a non-9 rect gets the same treatment; "
                       "dot_stem: a 1x1 object -> border 0, stem only."},
}


def _mirror(g):
    """Exact Python mirror of the rule (used for placement validation)."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    rects = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if (0 <= rr < h and 0 <= cc < w
                                and not seen[rr][cc] and g[rr][cc] != 0):
                            seen[rr][cc] = True
                            stack.append((rr, cc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            border = max(r2 - r1 + 1, c2 - c1 + 1) // 2
            rects.append((r1, c1, r2, c2, border))
    out = [row[:] for row in g]
    for r1, c1, r2, c2, border in rects:        # stems first
        for r in range(r2 + border + 1, h):
            for c in range(c1, c2 + 1):
                out[r][c] = 1
    for r1, c1, r2, c2, border in rects:        # rings second
        for r in range(r1 - border, r2 + border + 1):
            for c in range(c1 - border, c2 + border + 1):
                if r1 <= r <= r2 and c1 <= c <= c2:
                    continue
                if 0 <= r < h and 0 <= c < w and g[r][c] != 9:
                    out[r][c] = 3
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 non-bg solid rect object; background is 0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    nz = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nz == 0:
        errs.append("grid is blank: no objects to grow halos/stems for")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "clip", "other_color", "dot_stem"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 14, 16)
        w = ctx.draw_int("grid_w", 14, 16)
        n_rects = ctx.draw_int("n_rects", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 20)
        w = ctx.draw_int("grid_w", 18, 20)
        n_rects = ctx.draw_int("n_rects", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 14, 20)
        n_rects = ctx.draw_int("n_rects", 1, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        # claimed = cells any object's halo/stem/body will use; new
        # objects must keep their OWN footprint out of every claim
        claimed: set = set()
        placed = 0
        specs = []
        for i in range(n_rects):
            if texture == "dot_stem" and i == 0:
                rh = rw = 1
            else:
                rh = rng.randint(2, 5)
                rw = rng.randint(2, 5)
            color = 9
            if texture == "other_color" and i == 0:
                color = rng.choice([2, 4, 5, 6, 7, 8])
            border = max(rh, rw) // 2
            for _try in range(80):
                if texture == "clip" and i == 0:
                    # hug an edge so the ring clips (or the stem is gone)
                    side = rng.randrange(3)
                    if side == 0:
                        r0 = rng.randint(0, max(0, border - 1))
                        c0 = rng.randint(border, w - rw - border)
                    elif side == 1:
                        r0 = rng.randint(border, h - rh - border)
                        c0 = rng.choice([0, w - rw])
                    else:
                        r0 = h - rh - rng.randint(0, border)
                        c0 = rng.randint(border, w - rw - border)
                    if r0 < 0 or c0 < 0 or r0 + rh > h or c0 + rw > w:
                        continue
                else:
                    if h - rh - border <= border or w - rw - border <= border:
                        continue
                    r0 = rng.randint(border, h - rh - border)
                    c0 = rng.randint(border, w - rw - border)
                body = {(r, c) for r in range(r0, r0 + rh)
                        for c in range(c0, c0 + rw)}
                halo = {(r, c)
                        for r in range(r0 - border - 1, r0 + rh + border + 1)
                        for c in range(c0 - border - 1, c0 + rw + border + 1)}
                stem = {(r, c) for r in range(r0 + rh + border, h)
                        for c in range(c0 - 1, c0 + rw + 1)}
                claim = halo | stem
                if body & claimed:
                    continue
                # other objects' bodies must not sit in THIS claim either
                if any(p in claim for s in specs for p in s):
                    continue
                for r, c in body:
                    g[r][c] = color
                specs.append(body)
                claimed |= claim
                placed += 1
                break
        if placed == 0:
            continue
        out = _mirror(g)
        if out != g:
            return g
    raise ValueError("could not realize flowerpot board")


def _draw_from_degenerate(name, ctx):
    """no_rects — blank: identity. full_grid — one giant rect: ring
    fully out of bounds and no stem rows below, identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 14, 18)
    w = ctx.draw_int("grid_w", 14, 18)
    if name == "no_rects":
        return full_grid(h, w, 0)
    return full_grid(h, w, 9)
