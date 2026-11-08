"""Generator for arc_puzzle_bank_sixth21:H39 — color-coded rotation.

Rule: every object's bbox crop rotates by its COLOR (1 identity, 2
rotate-cw, 3 rotate-180, anything else rotate-ccw) and pastes back at
the same bbox top-left on a blank canvas. Non-square crops swap
dims; out-of-bounds cells clip; later scan-order objects overwrite
on overlap. The crop is a raw subgrid, so foreign cells inside a
bbox rotate WITH it.

Combinatorial axes: grid_h/w, colors, shapes, texture
(plain|identity_one|high_colors|nonsquare|clip).
Degenerates: no_motifs (blank), all_one (everything color 1 ->
identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0bc8ae2b1b64"
VERSION = "2.0.1"
TASK_ID = "0bc8ae2b1b64"

SUMMARY = (
    "Objects rotate per their color code (1 id / 2 cw / 3 180 / "
    "else ccw). identity_one boards include color-1 objects (frozen "
    "in place - the code was never generated before); high_colors "
    "boards use 5-9 (all ccw, refuting 'code = color mod 4'); "
    "nonsquare boards rotate tall/wide crops (dims swap at the same "
    "top-left); clip boards push a tall object's rotation off the "
    "right edge. Shapes verified rotation-asymmetric."
)

# Rivals: 'all objects rotate the same way' refuted by mixed codes.
# 'color 5+ cycles' refuted by high_colors all-ccw. 'rotation about
# the center' refuted by nonsquare top-left anchoring. 4 demos
# covering >=3 codes.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "shapes change under their color's rotation (visible effect), "
    "except identity_one objects",
    "main-path rotations stay in-bounds except clip boards",
    "objects separated enough that rotated crops don't collide",
]

DEGENERATE_TEXTURES = ("no_motifs", "all_one")
HELPFUL_TEXTURES = ("plain", "identity_one", "high_colors", "nonsquare",
                    "clip")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "grid_w":  {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|identity_one|high_colors|nonsquare|clip|"
                         "no_motifs|all_one",
                "doc": "identity_one: color-1 object frozen; "
                       "high_colors: 5-9 all rotate ccw; nonsquare: "
                       "dims swap; clip: rotated crop pokes off-grid."},
}


def _rot(crop, code):
    if code == 2:
        return [list(row) for row in zip(*crop[::-1])]
    if code == 3:
        return [row[::-1] for row in crop[::-1]]
    if code == 1:
        return [row[:] for row in crop]
    return [list(row) for row in zip(*crop)][::-1]  # ccw


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = set()
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == v:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            crop = [row[c1:c2 + 1] for row in g[r1:r2 + 1]]
            rot = _rot(crop, v if v in (1, 2, 3) else 4)
            for rr, rowv in enumerate(rot):
                for cc, vv in enumerate(rowv):
                    if vv != 0 and 0 <= r1 + rr < h and 0 <= c1 + cc < w:
                        out[r1 + rr][c1 + cc] = vv
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


def _asym(rng, k, max_h=3, max_w=3):
    for _ in range(300):
        s = _grow(rng, k, max_h, max_w)
        grid = {}
        sh = max(r for r, _ in s) + 1
        sw = max(c for _, c in s) + 1
        sub = [[1 if (r, c) in set(s) else 0 for c in range(sw)]
               for r in range(sh)]
        if _rot(sub, 2) != sub and _rot(sub, 3) != sub:
            return s
    return [(0, 0), (1, 0), (1, 1), (2, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 non-bg object with a color in {1,2,3} or higher."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    nz = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nz == 0:
        errs.append("no non-background objects: rule produces blank canvas")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "identity_one",
                                              "high_colors", "nonsquare",
                                              "clip"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 14, 15)
        n = 4
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n = 3
    rng = ctx.draw_rng("layout")

    if texture == "identity_one":
        pool = [1, 2, 3] + [rng.choice([4, 5, 6, 7, 8, 9])]
    elif texture == "high_colors":
        pool = [5, 6, 7, 8, 9]
    else:
        pool = [2, 3, 4, 5, 6, 7]
    for _attempt in range(150):
        g = full_grid(h, w, 0)
        colors = rng.sample(pool, min(n, len(pool)))
        if texture == "identity_one" and 1 not in colors:
            colors[0] = 1
        ok = True
        for i, color in enumerate(colors):
            if texture == "nonsquare":
                mh, mw = (rng.randint(3, 4), rng.randint(1, 2)) \
                    if rng.random() < 0.5 else \
                    (rng.randint(1, 2), rng.randint(3, 4))
            else:
                mh = mw = 3
            shape = _asym(rng, rng.randint(3, 5), mh, mw)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            side = max(sh, sw)
            placed = False
            for _t in range(150):
                if texture == "clip" and i == 0 and sh != sw:
                    # anchor so the rotated (dim-swapped) crop clips
                    r0 = rng.randint(0, h - sh)
                    c0 = w - sw  # right edge; rotation widens past w
                    if c0 + side <= w:
                        break
                else:
                    if h - side < 0 or w - side < 0:
                        break
                    r0 = rng.randint(0, h - side)
                    c0 = rng.randint(0, w - side)
                cells = [(r0 + r, c0 + c) for r, c in shape]
                # isolation over the SQUARE envelope so rotations never
                # collide between objects
                env = [(r0 + r, c0 + c) for r in range(side)
                       for c in range(side)
                       if 0 <= r0 + r < h and 0 <= c0 + c < w]
                if all(g[r][c] == 0 for r, c in env) and \
                   all(all(g[ar][ac] == 0
                           for ar, ac in ((r-1, c), (r+1, c),
                                          (r, c-1), (r, c+1))
                           if 0 <= ar < h and 0 <= ac < w)
                       for r, c in env):
                    for r, c in cells:
                        g[r][c] = color
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        out = _mirror(g)
        if out == g and texture != "identity_one":
            continue
        return g
    raise ValueError("could not realize rotation board")


def _draw_from_degenerate(name, ctx):
    """no_motifs — blank in, blank out. all_one — every object color
    1: identity rotation, output == input. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 9, 12)
    w = ctx.draw_int("grid_w", 11, 14)
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    for _ in range(rng.randint(2, 3)):
        shape = _grow(rng, rng.randint(3, 5), 3, 3)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _t in range(80):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            cells = [(r0 + r, c0 + c) for r, c in shape]
            if all(g[r][c] == 0 and
                   all(g[ar][ac] == 0
                       for ar, ac in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                       if 0 <= ar < h and 0 <= ac < w)
                   for r, c in cells):
                for r, c in cells:
                    g[r][c] = 1
                break
    return g
