"""Generator for 50aad11f.

Rule: color-6 shapes are recolored by their nearest singleton marker;
the output concatenates the recolored shapes in spatial order.

Canonical scene: small grids (9..18) with 2-3 color-6 polyominoes
(6..10 cells, bbox <= 4x4) and an equal number of singleton markers in
distinct non-{0,6} colors placed near their shapes.

Combinatorial axes (5): grid_h/w, shape_count, palette_kind,
marker_gap, texture. Degenerates: no_shapes, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b650a355848c"
VERSION = "4.0.0"
TASK_ID = "b650a355848c"
RULE_HASH = "2cb975ac778f"
SUMMARY = (
    "0-bg grid (9..18) with 2-3 color-6 polyominoes (6..10 cells, bbox "
    "<= 4x4) and equally many distinct-color singleton markers near "
    "their shapes. Rule: recolor each shape by its nearest marker."
)

INVARIANTS = [
    "background is color 0",
    "all source shapes use color 6 (4-connected components, 6..10 cells)",
    "singleton marker count equals shape count",
    "marker colors are distinct from each other and from 0 and 6",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":      {"type": "int", "default": "band rng 9..18",
                    "valid": "9..30"},
    "grid_w":      {"type": "int", "default": "band rng 9..18",
                    "valid": "9..30"},
    "shape_count": {"type": "int", "default": "band 2..3",
                    "valid": "1..5"},
    "palette_kind":{"type": "str", "default": "rng helpful",
                    "valid": "|".join(PALETTE_KINDS)},
    "texture":     {"type": "str", "default": "alias for palette_kind",
                    "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_POOLS = {
    "warm":    [2, 3, 4, 9, 7, 1],
    "cool":    [1, 5, 8, 2, 3, 9],
    "broad":   [1, 2, 3, 4, 5, 7, 8, 9],
    "primary": [1, 2, 3, 4, 5, 8],
}

# Official (h, w, n_shapes) tuples.
_CANONICAL_FORMS = ((12, 14, 2), (12, 9, 2), (12, 18, 3), (18, 13, 3))

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], set()
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != 0):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all canonical pairs
    satisfy them): rectangular grid inside the declared 9..30 envelope,
    background 0; every color-6 component is a polyomino of 6..10 cells
    with bbox <= 4x4; singleton markers (non-{0,6}) equal the shape count
    with distinct colors. no_shapes (no 6 cells), no_markers (shapes but
    no singletons), and full_grid are declared degenerates."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
        return errs
    if not (9 <= h <= 30 and 9 <= w <= 30):
        errs.append(f"dims {h}x{w} outside the declared 9..30 envelope")
        return errs
    flat = [v for row in grid for v in row]
    if len(set(flat)) == 1:
        if flat[0] != 6:
            errs.append(f"single-color grid of {flat[0]} is not a lawful "
                        "input (the declared full_grid form is all-6)")
        return errs  # all-0 (no_shapes) and all-6 (full_grid) are declared
    comps = _components(grid)
    shapes = []
    markers = []
    for cells in comps:
        v = grid[next(iter(cells))[0]][next(iter(cells))[1]]
        if v == 6:
            shapes.append(cells)
        elif len(cells) == 1:
            markers.append((v, next(iter(cells))))
    if not shapes:
        return errs  # no_shapes degenerate (declared)
    for cells in shapes:
        if not 6 <= len(cells) <= 10:
            errs.append(f"color-6 shape of {len(cells)} cells outside 6..10")
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        if (max(rs) - min(rs) + 1 > 4) or (max(cs) - min(cs) + 1 > 4):
            errs.append("color-6 shape bbox larger than 4x4")
    if not markers:
        return errs  # no_markers degenerate (declared)
    if len(markers) != len(shapes):
        errs.append(f"{len(shapes)} shapes but {len(markers)} markers "
                    "(equal counts required)")
    mcols = [v for v, _ in markers]
    if len(set(mcols)) != len(mcols):
        errs.append("marker colors are not distinct")
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): shape_count and marker_count."""
    comps = _components(grid)
    shapes = sum(1 for cells in comps
                 if grid[next(iter(cells))[0]][next(iter(cells))[1]] == 6)
    markers = sum(1 for cells in comps
                  if len(cells) == 1
                  and grid[next(iter(cells))[0]][next(iter(cells))[1]] not in (0, 6))
    return {"shape_count": shapes, "marker_count": markers}


def _poly(rng, size):
    """Random 4-connected polyomino of `size` cells, bbox <= 4x4."""
    cells = {(0, 0)}
    tries = 0
    while len(cells) < size and tries < 300:
        tries += 1
        r, c = list(cells)[rng.randrange(len(cells))]
        dr, dc = _DIRS4[rng.randrange(4)]
        nxt = (r + dr, c + dc)
        cand = cells | {nxt}
        rs = [x for x, _ in cand]
        cs = [y for _, y in cand]
        if (max(rs) - min(rs) + 1 > 4) or (max(cs) - min(cs) + 1 > 4):
            continue
        cells = cand
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    tex = overrides.get("texture")
    if tex in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items()
                       if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                f"degenerate texture {tex!r} is a fixed diagnostic layout; "
                f"it takes no other overrides, got {extra}")
        return _draw_from_degenerate(tex, ctx.draw_rng("layout"))
    if tex is not None and tex not in PALETTE_KINDS:
        raise ValueError(f"unknown texture {tex!r}; valid: "
                         f"{PALETTE_KINDS + DEGENERATE_TEXTURES}")
    if tex is not None and overrides.get("palette_kind") is not None and \
            overrides["palette_kind"] != tex:
        raise ValueError(
            f"texture={tex!r} is itself a palette alias and "
            f"palette_kind={overrides['palette_kind']!r} disagrees; drop one")
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        hr = (9, 12)
    elif difficulty == "hard":
        hr = (14, 18)
    else:
        hr = (11, 15)

    # Canonical-form prior (KRF-0003): ~30% of fully-unoverridden draws pin
    # one official (h, w, n_shapes) tuple.
    if not any(k in overrides for k in ("grid_h", "grid_w", "shape_count")):
        if ctx.draw_rng("canonical_prior").random() < 0.30:
            ch, cw, cn = ctx.draw_choice("canonical_form", _CANONICAL_FORMS)
            for label, value in (("grid_h", ch), ("grid_w", cw),
                                 ("shape_count", cn)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)

    h = ctx.draw_int("grid_h", *( (9, 30) if overrides.get("grid_h") is not None
                                  else hr))
    w = ctx.draw_int("grid_w", *( (9, 30) if overrides.get("grid_w") is not None
                                  else hr))
    n = ctx.draw_int("shape_count", *( (1, 5) if overrides.get("shape_count") is not None
                                       else (2, 3)))
    palette_kind = (tex or overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = list(_POOLS[palette_kind])
    rng.shuffle(pool)
    marker_colors = pool[:n]

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        used = set()
        ok = True
        spots = []
        for i in range(n):
            shape = _poly(rng, rng.randint(6, 10))
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _try in range(200):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
                if any((r + dr, c + dc) in used
                       for r, c in cells for dr, dc in _DIRS4):
                    continue
                for r, c in cells:
                    g[r][c] = 6
                used |= cells
                rs = [r for r, _ in cells]
                cs = [c for _, c in cells]
                spots.append((min(rs), min(cs), max(rs), max(cs)))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        # markers near their shapes (within Chebyshev 4 of the bbox, free)
        for i, (r1, c1, r2, c2) in enumerate(spots):
            placed = False
            for _try in range(200):
                mr = rng.randint(max(0, r1 - 4), min(h - 1, r2 + 4))
                mc = rng.randint(max(0, c1 - 4), min(w - 1, c2 + 4))
                if (mr, mc) in used:
                    continue
                if any((mr + dr, mc + dc) in used
                       for dr, dc in _DIRS4):
                    continue
                g[mr][mc] = marker_colors[i]
                used.add((mr, mc))
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            errs = self_check(g)
            if not errs:
                return g
    raise ValueError(
        f"cannot place {n} shapes with distinct near markers on {h}x{w}")


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_shapes":
        g[3][3] = 2
        return g
    if name == "no_markers":
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]:
            g[2 + dr][5 + dc] = 6
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 6
        return g
    return g
