"""Generator for arc_additional_puzzles_21_set21_bundle:H143 -- Recolor objects by bbox-area rank.

Rule: sort the non-0 objects (4-connected same-color components) by
bounding-box area descending and recolor them on a blank grid -- largest
2, next 3, next 4, ...

This generator scatters K connected blobs (any colors) with DISTINCT bbox
areas so the rank is unambiguous.

Combinatorial axes: grid size, blob count, the blob shapes/sizes/colors,
and positions.
Degenerates: single_blob, no_blob, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "eb92fce9b549"
VERSION = "2.2.0"  # add executable ranked-component self_check and fail-closed fallback
TASK_ID = "eb92fce9b549"
SUMMARY = (
    "0-bg grid (size varies). Two input styles, both ranked-recolored by "
    "bbox area: (a) NESTED CONCENTRIC RINGS -- a mono-color set of nested "
    "rectangular frames each separated by a 1-cell gap (the canonical look); "
    "(b) SCATTERED BLOBS -- K (2-8) connected blobs of distinct bbox areas. "
    "Rule: rank the 4-connected objects by bbox area DESC and recolor on a "
    "blank grid -- largest 2, next 3, next 4, ... For rings this yields "
    "concentric color bands; for blobs, size-ranked recolor."
)

INVARIANTS = [
    "every blob is a connected same-color component, separated from the others",
    "all blobs have distinct bounding-box areas (the rank is unambiguous)",
    "the output recolors each blob by descending-area rank starting at 2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_blob", "no_blob", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_blobs":        {"type": "int", "default": "varies", "valid": "2..8"},
    "blob_size":      {"type": "int", "default": "varies", "valid": "2..12"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|single_blob|no_blob|full_grid"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _bbox_area(shape):
    return (max(r for r, c in shape) + 1) * (max(c for r, c in shape) + 1)


def _reserve(occ, top, left, sh, sw, h, w):
    for r in range(top - 1, top + sh + 1):
        for c in range(left - 1, left + sw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _cells_bbox_area(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal samples: at least two 4-connected components with unique bbox areas for unambiguous rank recolor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    comps = _components(grid)
    if len(comps) < 2:
        errors.append(f"expected at least 2 rankable components, found {len(comps)}")
    areas = [_cells_bbox_area(cells) for _, cells in comps]
    if len(areas) != len(set(areas)):
        errors.append(f"component bbox areas are not unique: {sorted(areas)}")
    for color, cells in comps:
        if not cells:
            errors.append(f"empty component for color {color}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, nr, sr = (12, 14), (12, 15), (2, 3), (2, 6)
    elif difficulty == "hard":
        hr, wr, nr, sr = (17, 22), (18, 24), (5, 8), (3, 12)
    else:
        hr, wr, nr, sr = (14, 18), (14, 19), (3, 5), (2, 9)

    # NESTED CONCENTRIC RINGS = the canonical structure (bias toward it);
    # scattered blobs kept for diversity.
    mode = overrides.get("mode") or rng.choice(["rings", "rings", "scattered"])
    if mode == "rings":
        rings = _nested_rings(rng, hr, wr)
        if rings is not None:
            return rings

    for _attempt in range(40):
        K = rng.randint(*nr)
        shapes = []; areas = set()
        for _t in range(200):
            sp = _poly(rng, rng.randint(*sr))
            a = _bbox_area(sp)
            if a in areas:
                continue
            areas.add(a); shapes.append(sp)
            if len(shapes) == K:
                break
        if len(shapes) < K:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for sp in shapes:
            sh = max(r for r, c in sp) + 1; sw = max(c for r, c in sp) + 1
            if sh > h or sw > w:
                continue
            for _p in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                if _reserve(occ, top, left, sh, sw, h, w):
                    paint_at(g, top, left, sp, rng.randint(1, 9))
                    placed += 1
                    break
        if placed >= 2:
            return g

    return _fallback_rank_components(rng, hr, wr)


def _nested_rings(rng, hr, wr):
    """Concentric rectangular frames, each a separate 4-connected component
    (1-cell gap between consecutive frames), mono-color -> the canonical
    structure. Bbox areas strictly decrease inward -> unambiguous rank."""
    h = rng.randint(*hr); w = rng.randint(*wr)
    # outer frame size; need room for >=2 frames (each frame steps inset by 2)
    H = rng.randint(7, h); W = rng.randint(7, w)
    top = rng.randint(0, h - H); left = rng.randint(0, w - W)
    color = rng.randint(1, 9)
    g = full_grid(h, w, 0)
    n = 0
    k = 0
    while True:
        r0 = top + k; r1 = top + H - 1 - k
        c0 = left + k; c1 = left + W - 1 - k
        if r1 < r0 or c1 < c0:
            break
        if r1 == r0 or c1 == c0:           # degenerate inner -> single line/dot
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    g[r][c] = color
            n += 1
            break
        for c in range(c0, c1 + 1):        # rectangular outline (one frame)
            g[r0][c] = color; g[r1][c] = color
        for r in range(r0, r1 + 1):
            g[r][c0] = color; g[r][c1] = color
        n += 1
        k += 2                              # next frame inset by 2 -> 1-cell gap
    return g if n >= 2 else None


def _fallback_rank_components(rng, hr, wr):
    """Small deterministic valid board if random placement wedges: three separated
    components with distinct bbox areas, so the rank order is still defined."""
    h = max(12, min(hr[1], 14))
    w = max(12, min(wr[1], 16))
    g = full_grid(h, w, 0)
    paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 2)          # bbox area 4
    paint_at(g, 1, 7, [(0, 0), (0, 1), (0, 2), (1, 1)], 5) # bbox area 6
    paint_at(g, 7, 3, [(0, 0), (0, 1), (0, 2),
                       (1, 0), (2, 0)], 8)                 # bbox area 9
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "single_blob":
        paint_at(g, 4, 4, [(0, 0), (0, 1), (1, 0), (1, 1)], 4)
        return g
    if name == "no_blob":
        return g
    if name == "full_grid":
        return full_grid(12, 12, 3)
    paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 4)
    paint_at(g, 6, 6, [(0, 0), (0, 1), (0, 2), (1, 1)], 7)
    return g
