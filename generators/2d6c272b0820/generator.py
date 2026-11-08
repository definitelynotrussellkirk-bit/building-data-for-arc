"""Generator for arc_puzzle_bank_21_set10_e:medium_j08.

Rule: rank the blobs by edge-perimeter (descending) and recolor each by
its rank using the palette [2,3,4,6,8,9,1,5,7].

Combinatorial axes: grid size, the number of blobs, their shapes (which
set the perimeters), positions and input colors.
Degenerates: tied_perimeters, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import PLUS_5

GENERATOR_ID = "2d6c272b0820"
VERSION = "3.1.0"  # diversity: random N blobs (distinct perimeters) + positions + grid (was 3 fixed blobs)
TASK_ID = "2d6c272b0820"
SUMMARY = (
    "0-bg grid (size varies). 3-5 BLOBS (random polyominoes with DISTINCT "
    "edge-perimeters, distinct input colors), placed apart. Rule: compute "
    "each blob's edge-perimeter, sort the distinct perimeters descending, "
    "and recolor every blob by its perimeter rank using the palette "
    "[2,3,4,6,8,9,1,5,7] (largest perimeter -> palette[0], etc.). The grid "
    "size, the number of blobs, their shapes/perimeters, positions and "
    "input colors all vary freely, so the rank recolor (the output) "
    "varies too (was 3 fixed blobs + grid padding)."
)

INVARIANTS = [
    "3-5 non-touching blobs",
    "all distinct edge-perimeters (so the rank order is unambiguous)",
    "blobs are separated so each is its own component",
    "input blob colors differ from their rank-output colors",
]

PALETTE_KINDS = ("default", "small_blobs", "mixed_blobs", "large_blobs")
DEGENERATE_TEXTURES = ("tied_perimeters", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|small_blobs|mixed_blobs|large_blobs"},
    "n_blobs":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..5"},
    "perimeter_spread": {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|small_blobs|mixed_blobs|large_blobs|tied_perimeters|single_blob|no_blobs"},
}


def _perim(cells):
    s = set(cells)
    return sum(1 for (r, c) in s
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if (r + dr, c + dc) not in s)


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in norm) < maxd and max(c for r, c in norm) < maxd:
            return norm
    return [(0, 0), (1, 0), (1, 1)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify distinct-perimeter blobs whose input colors visibly change."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    comps = _components(grid)
    if len(comps) < 3:
        errs.append(f"expected >=3 non-bg blob components, got {len(comps)}")
        return errs
    perims = [_perim(cells) for _color, cells in comps]
    if len(set(perims)) != len(perims):
        errs.append("blob edge-perimeters are not all distinct")
    palette = [2, 3, 4, 6, 8, 9, 1, 5, 7]
    ranked = sorted(set(perims), reverse=True)
    for color, cells in comps:
        target = palette[ranked.index(_perim(cells))]
        if color == target:
            errs.append("a blob input color already equals its rank-output color")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nbl = (8, 10), (11, 13), 3
    elif difficulty == "hard":
        hr, wr, nbl = (12, 16), (12, 16), rng.randint(4, 5)
    else:
        hr, wr, nbl = (9, 12), (11, 14), rng.randint(3, 4)

    for _attempt in range(40):
        # N blobs with DISTINCT perimeters.
        blobs = []; perims = set()
        for _ in range(nbl):
            for _t in range(30):
                b = _random_poly(rng, rng.randint(2, 6), 4)
                pm = _perim(b)
                if pm not in perims:
                    perims.add(pm); blobs.append(b); break
        if len(blobs) < nbl:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        palette = [2, 3, 4, 6, 8, 9, 1, 5, 7]
        ranked = sorted(perims, reverse=True)
        target_colors = [palette[ranked.index(_perim(b))] for b in blobs]
        colors = None
        for _t in range(100):
            cand = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], nbl)
            if all(c != target_colors[i] for i, c in enumerate(cand)):
                colors = cand
                break
        if colors is None:
            continue
        ok = True
        for i, b in enumerate(blobs):
            bh = max(r for r, c in b) + 1; bw = max(c for r, c in b) + 1
            placed = False
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, b, top, left, h, w):
                    for r, c in b:
                        g[top + r][left + c] = colors[i]; occ[top + r][left + c] = True
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if ok:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "tied_perimeters":
        sq = [(0, 0), (0, 1), (1, 0), (1, 1)]
        paint_at(g, 1, 1, sq, 2); paint_at(g, 1, w - 4, sq, 4); paint_at(g, h - 3, 1, sq, 7)
        return g
    if name == "single_blob":
        paint_at(g, 1, 2, PLUS_5, 2)
        return g
    if name == "no_blobs":
        return g
    return g
