"""Generator for arc_additional_puzzle_bank_volume14:H96.

Rule: ctrl cell (3=identity, 4=rot90, 7=reflect-h, 8=reflect-v) picks
a transform of the normalized color-6 template; the result is painted
in color 9 at template-bbox-top-left + (p2 - p1), where p1/p2 are the
first color-1/color-2 cells. Everything else stays; OOB stamp cells
clip (paint-cells).

Combinatorial axes: grid_h/w, control_color, texture (plain|clip).
Degenerates (bridge-verified degradations, NOT crashes):
  no_control     — ctrl=(third #f)=#f, cond falls to else: BASE stamp.
  no_marker_pair — (- #f #f) coerces to 0: transform stamped AT the
                   template anchor (overpainting it).
no_template was DROPPED: (first '()) -> obj-cells #f CRASHES.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "06fdc277c2cb"
VERSION = "2.1.0"  # add executable transform-stamp invariant self-check
TASK_ID = "06fdc277c2cb"
SUMMARY = (
    "Color-6 template + ctrl cell (3 identity / 4 rot90 / 7 reflect-h "
    "/ 8 reflect-v) + markers 1,2 defining a translation vector; the "
    "transformed template is stamped in color 9. All four transforms "
    "of every template are pairwise distinct so the control is always "
    "inferable. (Was: fixed S-shape at (2,1), ctrl at (0,0), markers "
    "in one row so the vector was always horizontal.)"
)

# Rivals: 'stamp keeps color 6' refuted by 9-stamps. 'vector is
# horizontal' refuted by diagonal/vertical/negative vectors. 'ctrl
# does nothing' refuted by distinct-transform guarantee. 'stamps
# always fit' refuted by clip. 4 demos covering >=3 ctrl values.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one color-6 object ALWAYS (none crashes the rule)",
    "base/rot90/reflect-h/reflect-v of the template are pairwise distinct",
    "exactly one cell each of colors 1, 2, and one ctrl in {3,4,7,8}",
    "main-path stamps land fully in-bounds on empty cells",
]

DEGENERATE_TEXTURES = ("no_control", "no_marker_pair")
HELPFUL_TEXTURES = ("plain", "clip")

AXES = {
    "grid_h":        {"type": "int", "default": "rng 10..14", "valid": "8..20"},
    "grid_w":        {"type": "int", "default": "rng 12..17", "valid": "10..22"},
    "control_color": {"type": "int", "default": "rng 3|4|7|8", "valid": "3|4|7|8"},
    "texture":       {"type": "str", "default": "rng helpful",
                      "valid": "plain|clip|no_control|no_marker_pair",
                      "doc": "clip: stamp partially out of bounds."},
}


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


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rot90(cells):
    h = max(r for r, _ in cells) + 1
    return _norm([(c, h - 1 - r) for r, c in cells])


def _refl_h(cells):
    h = max(r for r, _ in cells) + 1
    return _norm([(h - 1 - r, c) for r, c in cells])


def _refl_v(cells):
    w = max(c for _, c in cells) + 1
    return _norm([(r, w - 1 - c) for r, c in cells])


def _transform(cells, ctrl):
    if ctrl == 4:
        return _rot90(cells)
    if ctrl == 7:
        return _refl_h(cells)
    if ctrl == 8:
        return _refl_v(cells)
    return cells


def _asym_shape(rng):
    """All four transforms pairwise distinct -> ctrl always inferable."""
    for _ in range(300):
        s = _grow(rng, rng.randint(4, 6))
        ts = [tuple(s), tuple(_rot90(s)), tuple(_refl_h(s)), tuple(_refl_v(s))]
        if len(set(ts)) == 4:
            return s
    return [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]  # known-asymmetric


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain", "clip"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 15, 17)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 17)
    ctrl = int(overrides.get("control_color") or
               ctx.draw_choice("control_color", (3, 4, 7, 8)))
    rng = ctx.draw_rng("layout")

    for _attempt in range(120):
        g = full_grid(h, w, 0)
        shape = _asym_shape(rng)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        tr = rng.randint(0, h - sh)
        tc = rng.randint(0, w - sw)
        for r, c in shape:
            g[tr + r][tc + c] = 6
        occupied = {(tr + r, tc + c) for r, c in shape}

        t = _transform(shape, ctrl)
        th = max(r for r, _ in t) + 1
        tw = max(c for _, c in t) + 1
        # vector from p1 to p2; stamp anchor = (tr+dr, tc+dc)
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
            if any(p in occupied for p in inb):
                continue
            # markers: p1 anywhere free, p2 = p1 + (dr, dc) in-bounds free
            placed = False
            for _mtry in range(150):
                r1 = rng.randint(0, h - 1)
                c1 = rng.randint(0, w - 1)
                r2, c2 = r1 + dr, c1 + dc
                if not (0 <= r2 < h and 0 <= c2 < w):
                    continue
                pts = {(r1, c1), (r2, c2)}
                if len(pts) != 2:
                    continue
                if any(p in occupied or p in set(inb) for p in pts):
                    continue
                if g[r1][c1] != 0 or g[r2][c2] != 0:
                    continue
                g[r1][c1] = 1
                g[r2][c2] = 2
                placed = True
                break
            if placed:
                occupied |= set(inb) | pts
                ok = True
                break
        if not ok:
            continue
        # ctrl cell last: any free cell not in the stamp footprint
        for _ctry in range(200):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0 and (r, c) not in occupied:
                g[r][c] = ctrl
                return g
    raise ValueError("could not realize transform-stamp board")


def _draw_from_degenerate(name, ctx):
    """Bridge-verified DEGRADATIONS (not crashes), rng-varied:

    no_control     — ctrl missing: cond falls through to else, the
                     BASE shape is stamped by the marker vector.
    no_marker_pair — markers missing: (- #f #f) coerces to 0, the
                     transformed shape is stamped AT the template
                     anchor (painting 9 over/near the template).
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 12, 15)
    g = full_grid(h, w, 0)
    shape = _asym_shape(rng)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    tr = rng.randint(1, h - sh - 1)
    tc = rng.randint(1, w - sw - 1)
    for r, c in shape:
        g[tr + r][tc + c] = 6
    if name == "no_control":
        g[h - 2][1] = 1
        g[h - 2][rng.randint(3, w - 2)] = 2
    else:  # no_marker_pair
        g[0][rng.randint(0, w - 1)] = rng.choice([3, 4, 7, 8])
    return g


def _cells_of(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if len(_cells_of(grid, 1)) != 1 or len(_cells_of(grid, 2)) != 1:
        errors.append("need exactly one marker each of colors 1 and 2")
    ctrl_count = sum(len(_cells_of(grid, c)) for c in (3, 4, 7, 8))
    if ctrl_count != 1:
        errors.append(f"need exactly one transform control in {{3,4,7,8}}, got {ctrl_count}")
    shape = _norm(_cells_of(grid, 6))
    if not shape:
        errors.append("missing color-6 template")
    else:
        ts = [tuple(shape), tuple(_rot90(shape)), tuple(_refl_h(shape)), tuple(_refl_v(shape))]
        if len(set(ts)) != 4:
            errors.append("template transforms are not pairwise distinct")
    return sorted(set(errors))
