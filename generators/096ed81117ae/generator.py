"""Generator for arc_additional_puzzle_bank_volume17:H119.

Rule: control color (first present of 1=identity, 4=reflect-v,
7=rot180, 9=reflect-h) transforms the normalized color-6 shape; the
result stamps in color 8 at shape-bbox-min + (p3 - p2), where p2/p3
are the first color-2/color-3 cells. Stamps paint ONLY onto 0-cells
(existing content is preserved); out-of-bounds cells clip.

Combinatorial axes: grid_h/w, control, texture (plain|clip|collide).
Degenerates (bridge-verified degradations): no_control (cond falls to
reflect-h), no_markers (vector degrades to 0: stamp lands on the
shape, mostly skipped), full_grid (no zeros, identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "096ed81117ae"
VERSION = "2.0.1"
TASK_ID = "096ed81117ae"
SUMMARY = (
    "Color-6 shape + control (1 identity / 4 reflect-v / 7 rot180 / "
    "9 reflect-h) + markers 2,3 defining the vector; the transformed "
    "shape stamps in 8 onto EMPTY cells only. collide boards overlap "
    "the stamp with existing content that survives (no overwrite); "
    "clip boards spill off-grid. (Was: fixed shape/control/markers - "
    "the vector was always (3,3) and unique_in=20.)"
)

# Rivals: 'stamp overwrites' refuted by collide boards (non-zero cells
# survive inside the stamp footprint). 'vector is fixed/diagonal'
# refuted by free vectors. 'control does nothing' refuted by
# pairwise-distinct transforms. 4 demos covering >=3 controls.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one 6-shape, one control cell (1/4/7/9), one 2, one 3",
    "the shape's identity/reflect-v/rot180/reflect-h are pairwise distinct",
    "main-path stamps land fully in-bounds on empty cells",
]

DEGENERATE_TEXTURES = ("no_control", "no_markers", "full_grid")
HELPFUL_TEXTURES = ("plain", "clip", "collide")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 10..14", "valid": "8..20"},
    "grid_w":  {"type": "int", "default": "rng 12..17", "valid": "10..22"},
    "control": {"type": "int", "default": "rng 1|4|7|9", "valid": "1|4|7|9"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|clip|collide|no_control|no_markers|full_grid",
                "doc": "clip: stamp partially off-grid; collide: the stamp "
                       "footprint crosses existing cells, which the "
                       "only-onto-zeros rule preserves."},
}


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _transform(cells, control):
    n = _norm(cells)
    h = max(r for r, _ in n) + 1
    w = max(c for _, c in n) + 1
    if control == 1:
        return n
    if control == 4:
        return _norm([(r, w - 1 - c) for r, c in n])
    if control == 7:
        return _norm([(h - 1 - r, w - 1 - c) for r, c in n])
    return _norm([(h - 1 - r, c) for r, c in n])  # 9 / fallback


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    return _norm(cells)


def _asym(rng):
    for _ in range(300):
        s = _grow(rng, rng.randint(4, 6))
        if len({tuple(_transform(s, k)) for k in (1, 4, 7, 9)}) == 4:
            return s
    return [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]


def _mirror(g):
    h, w = len(g), len(g[0])
    shape = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 6]
    if not shape:
        return None

    def first_of(color):
        for r in range(h):
            for c in range(w):
                if g[r][c] == color:
                    return (r, c)
        return None

    p2, p3 = first_of(2), first_of(3)
    control = next((k for k in (1, 4, 7, 9) if first_of(k)), None)
    trans = _transform(shape, control if control else 9)
    bb = (min(r for r, _ in shape), min(c for _, c in shape))
    dr = (p3[0] - p2[0]) if p2 and p3 else 0
    dc = (p3[1] - p2[1]) if p2 and p3 else 0
    out = [row[:] for row in g]
    for r, c in trans:
        rr, cc = bb[0] + dr + r, bb[1] + dc + c
        if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
            out[rr][cc] = 8
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "clip", "collide"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 15, 17)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 17)
    control = int(overrides.get("control") or
                  ctx.draw_choice("control", (1, 4, 7, 9)))
    rng = ctx.draw_rng("layout")

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        shape = _asym(rng)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        tr = rng.randint(0, h - sh)
        tc = rng.randint(0, w - sw)
        for r, c in shape:
            g[tr + r][tc + c] = 6
        occupied = {(tr + r, tc + c) for r, c in shape}

        t = _transform(shape, control)
        th = max(r for r, _ in t) + 1
        tw = max(c for _, c in t) + 1
        ok = False
        for _try in range(150):
            dr = rng.randint(-tr - th + 1, h - tr - 1) if texture == "clip" \
                else rng.randint(-tr, h - th - tr)
            dc = rng.randint(-tc - tw + 1, w - tc - 1) if texture == "clip" \
                else rng.randint(-tc, w - tw - tc)
            if dr == 0 and dc == 0:
                continue
            stamp = [(tr + dr + r, tc + dc + c) for r, c in t]
            inb = [(r, c) for r, c in stamp if 0 <= r < h and 0 <= c < w]
            if texture == "clip":
                if len(inb) == len(stamp) or not inb:
                    continue
            elif len(inb) != len(stamp):
                continue
            hits = [p for p in inb if p in occupied]
            if texture == "collide":
                # the footprint must cross the source: those cells stay 6
                if not hits or len(hits) == len(inb):
                    continue
            elif hits:
                continue
            # markers: p2 free, p3 = p2 + (dr, dc) free
            placed = False
            for _mtry in range(150):
                r1 = rng.randint(0, h - 1)
                c1 = rng.randint(0, w - 1)
                r2_, c2_ = r1 + dr, c1 + dc
                if not (0 <= r2_ < h and 0 <= c2_ < w):
                    continue
                pts = {(r1, c1), (r2_, c2_)}
                if len(pts) != 2 or any(p in occupied or p in set(inb)
                                        for p in pts):
                    continue
                if g[r1][c1] != 0 or g[r2_][c2_] != 0:
                    continue
                g[r1][c1] = 2
                g[r2_][c2_] = 3
                placed = True
                break
            if placed:
                occupied |= set(inb) | pts
                ok = True
                break
        if not ok:
            continue
        for _ctry in range(200):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0 and (r, c) not in occupied:
                g[r][c] = control
                return g
    raise ValueError("could not realize transform-stamp board")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: exactly one 6-shape component; exactly one control cell
    (value in {1,4,7,9}); exactly one color-2 and one color-3 cell."""
    msgs = []
    h, w = len(grid), len(grid[0])
    seen = set()
    six_comps = 0
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] != 6:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 6:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            six_comps += 1
    if six_comps != 1:
        msgs.append(f"expected exactly 1 color-6 shape, found {six_comps}")
    controls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 4, 7, 9)]
    if len(controls) != 1:
        msgs.append(f"expected exactly 1 control cell (1/4/7/9), found {len(controls)}")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(twos) != 1:
        msgs.append(f"expected exactly 1 color-2 marker, found {len(twos)}")
    if len(threes) != 1:
        msgs.append(f"expected exactly 1 color-3 marker, found {len(threes)}")
    return msgs


def _draw_from_degenerate(name, ctx):
    """Bridge-verified degradations, rng-varied:
    no_control — cond falls through to reflect-h.
    no_markers — vector degrades to 0 (stamp lands on the shape and
                 only paints surrounding zeros).
    full_grid  — no zeros anywhere: nothing stamps, identity.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 12, 15)
    if name == "full_grid":
        return full_grid(h, w, 6)
    g = full_grid(h, w, 0)
    shape = _asym(rng)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    tr = rng.randint(1, h - sh - 1)
    tc = rng.randint(1, w - sw - 1)
    for r, c in shape:
        g[tr + r][tc + c] = 6
    if name == "no_control":
        g[0][rng.randint(0, w // 2)] = 2
        g[rng.randint(h // 2, h - 1)][rng.randint(0, w - 1)] = 3
    else:  # no_markers
        g[0][rng.randint(0, w - 1)] = rng.choice([1, 4, 7, 9])
    return g
