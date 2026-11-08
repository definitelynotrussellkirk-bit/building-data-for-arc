"""Generator for 228f6490 — shape-keyed hole filling.

Rule: each 5-object's bbox holes (0-cells inside) are keyed by
normalized shape. Every color forming EXACTLY ONE component whose
shape equals a hole's shape teleports into that hole (painted there,
original cleared). Colors with 2+ components stay (the original
task's 6s). Single-component colors with no matching hole stay.

Combinatorial axes: grid_h/w, hole shapes, texture
(plain|two_containers|multi_decoy|wrong_shape).
Degenerates: no_hole, no_object, full_grid (all identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b53f4dfc446"
VERSION = "2.0.1"
TASK_ID = "0b53f4dfc446"
SUMMARY = (
    "Blob-shaped holes in 5-containers pull in the single-component "
    "color of matching shape. multi_decoy boards add a color with TWO "
    "components (one even matching the hole shape) that STAYS - only "
    "single-component colors are mobile; wrong_shape boards add a "
    "mover whose shape matches nothing (stays); two_containers boards "
    "run two distinct hole shapes with two movers. (Was: 1x1/1x2 "
    "holes only, one container, no near-misses.)"
)

# Rivals: 'any matching shape moves' refuted by multi_decoy (2-comp
# colors frozen). 'all loose objects vanish' refuted by wrong_shape.
# 'holes are rectangles' refuted by blob holes. 3-4 demos incl. >=1
# multi_decoy.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "hole shapes are distinct per board; mover shapes match uniquely",
    "multi_decoy boards: a color with exactly two components",
    "containers' 5-cells fill the bbox except the hole",
]

DEGENERATE_TEXTURES = ("no_hole", "no_object", "full_grid")
HELPFUL_TEXTURES = ("plain", "two_containers", "multi_decoy",
                    "wrong_shape")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 10..14", "valid": "9..18"},
    "grid_w":  {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|two_containers|multi_decoy|wrong_shape|"
                         "no_hole|no_object|full_grid",
                "doc": "multi_decoy: 2-component color stays even if a "
                       "piece matches the hole; wrong_shape: unmatched "
                       "single-component color stays."},
}

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 color-5 cell (container walls); >=1 non-{0,5} cell (movers)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    has_5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has_5:
        errors.append("no color-5 cells (container missing)")
    has_mover = any(grid[r][c] not in (0, 5) for r in range(h) for c in range(w))
    if not has_mover:
        errors.append("no non-{0,5} cells (no movers)")
    return errors


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


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _components_of(g, pred):
    h, w = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if not pred(g[r][c]) or (r, c) in seen:
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
                            and (nr, nc) not in seen and pred(g[nr][nc]):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _mirror(g):
    h, w = len(g), len(g[0])
    gobjs = _components_of(g, lambda v: v == 5)
    holes = []
    for cells in gobjs:
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        hl = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
              if g[r][c] == 0]
        if hl:
            holes.append(hl)
    order = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v not in (0, 5) and v not in order:
                order.append(v)
    moves = []
    for col in order:
        comps = _components_of(g, lambda v, col=col: v == col)
        if len(comps) != 1:
            continue
        cells = comps[0]
        ns = _norm(cells)
        hole = next((hl for hl in holes if _norm(hl) == ns), None)
        if hole:
            moves.append((cells, hole, col,
                          min(r for r, _ in cells),
                          min(c for _, c in cells),
                          min(r for r, _ in hole),
                          min(c for _, c in hole)))
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            fill = next((mv for mv in moves
                         if any(mv[5] + (pr - mv[3]) == r and
                                mv[6] + (pc - mv[4]) == c
                                for pr, pc in mv[0])), None)
            clear = next((mv for mv in moves
                          if (r, c) in set(map(tuple, mv[0]))), None)
            if fill:
                out[r][c] = fill[2]
            elif clear:
                out[r][c] = 0
    return out


def _place_container(g, rng, hole_shape):
    """5-filled bbox with the blob hole punched out."""
    h, w = len(g), len(g[0])
    hh = max(r for r, _ in hole_shape) + 1
    hw = max(c for _, c in hole_shape) + 1
    fh, fw = hh + 2, hw + 2
    for _t in range(150):
        r0 = rng.randint(0, h - fh)
        c0 = rng.randint(0, w - fw)
        if not all(g[r][c] == 0
                   for r in range(max(0, r0 - 1), min(h, r0 + fh + 1))
                   for c in range(max(0, c0 - 1), min(w, c0 + fw + 1))):
            continue
        for r in range(fh):
            for c in range(fw):
                g[r0 + r][c0 + c] = 5
        for r, c in hole_shape:
            g[r0 + 1 + r][c0 + 1 + c] = 0
        return True
    return False


def _place_loose(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _t in range(150):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = [(r0 + r, c0 + c) for r, c in shape]
        if all(g[r][c] == 0 and
               all(g[ar][ac] == 0
                   for ar, ac in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                   if 0 <= ar < h and 0 <= ac < w)
               for r, c in cells):
            for r, c in cells:
                g[r][c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "two_containers",
                                              "multi_decoy", "wrong_shape"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 15, 16)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 16)
    rng = ctx.draw_rng("layout")

    for _attempt in range(120):
        g = full_grid(h, w, 0)
        n_cont = 2 if texture == "two_containers" else 1
        shapes = []
        ok = True
        for _ in range(n_cont):
            for _t in range(60):
                sh = _grow(rng, rng.randint(2, 4), 2, 3)
                if all(_norm(sh) != _norm(s) for s in shapes):
                    shapes.append(sh)
                    break
            else:
                ok = False
        if not ok or not all(_place_container(g, rng, s) for s in shapes):
            continue
        colors = rng.sample(_COLORS, 4)
        ci = 0
        for s in shapes:
            if not _place_loose(g, rng, s, colors[ci]):
                ok = False
                break
            ci += 1
        if not ok:
            continue
        if texture == "multi_decoy":
            # one color, TWO components; one piece even matches the
            # hole shape - the color is not mobile, both stay
            dc = colors[ci]
            ci += 1
            if not (_place_loose(g, rng, shapes[0], dc) and
                    _place_loose(g, rng, _grow(rng, 2, 2, 2), dc)):
                continue
        elif texture == "wrong_shape":
            dc = colors[ci]
            ci += 1
            for _t in range(60):
                sh = _grow(rng, rng.randint(2, 5), 3, 3)
                if all(_norm(sh) != _norm(s) for s in shapes):
                    break
            else:
                continue
            if not _place_loose(g, rng, sh, dc):
                continue
        out = _mirror(g)
        if out == g:
            continue
        return g
    raise ValueError("could not realize hole-fill board")


def _draw_from_degenerate(name, ctx):
    """no_hole — solid 5-block + loose object: no holes, identity.
    no_object — container with hole, nothing mobile: identity.
    full_grid — all 5: bbox has no 0-cells, identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 12, 15)
    if name == "full_grid":
        return full_grid(h, w, 5)
    g = full_grid(h, w, 0)
    if name == "no_hole":
        for r in range(2, 6):
            for c in range(2, 7):
                g[r][c] = 5
        _place_loose(g, rng, _grow(rng, 3, 2, 2), rng.choice(_COLORS))
        return g
    _place_container(g, rng, _grow(rng, rng.randint(2, 4), 2, 3))
    return g
