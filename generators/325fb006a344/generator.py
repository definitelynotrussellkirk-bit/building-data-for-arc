"""Generator for arc_puzzle_bank_21_set7_s:S7_H5 — consensus shape from shifted copies.

Rule (verified from canonical Racket): take every colour-3 OBJECT, normalize each
to its own top-left, and keep the cells that occur in AT LEAST TWO of the
normalized copies. Output that consensus shape (cropped to its bbox), coloured 3.

The previous body was the generic scatter template, which uses each colour at most
once — so colour-3 appears in a single object, no normalized cell reaches count 2,
and the rule returns [[0]] every time (distinct_out=1). This rewrite CONSTRUCTS
several colour-3 objects that share a common BASE shape (each with a few extra
cells), so the base is the consensus and the output varies with the base.

Axes: grid size, base shape, copy count, per-copy extra cells.
Degenerates: single_copy, identical_copies, disjoint_copies.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "325fb006a344"
VERSION = "2.1.1"  # FIX: scatter template used colour-3 once -> no cell in >=2 copies -> output always [[0]] (distinct=1). Now several colour-3 objects sharing a base shape, so the base is the consensus.
TASK_ID = "325fb006a344"

SUMMARY = ("Several colour-3 objects share a common base shape (each with a few extra cells); "
           "the rule keeps the cells present in >=2 normalized copies and outputs that "
           "consensus shape, coloured 3. Base shape, copy count and extras vary.")

INVARIANTS = [
    "2+ separate colour-3 objects (distinct connected components)",
    "all copies contain a shared base shape (the consensus)",
    "per-copy extra cells differ so only the base reaches count >=2",
]

DEGENERATE_TEXTURES = ("single_copy", "identical_copies", "disjoint_copies")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":     {"type": "int", "default": "rng 11..15", "valid": "9..20"},
    "base_k":     {"type": "int", "default": "rng 3..5 (base cells)", "valid": "2..9"},
    "n_copies":   {"type": "int", "default": "2-3 easy / 3-4 hard", "valid": "2..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|single_copy|identical_copies|disjoint_copies"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return seen


def _with_extras(base, rng, n_extra):
    """base shape plus n_extra cells adjacent to it (keeps it connected)."""
    cells = set(base)
    for _ in range(n_extra):
        frontier = [(r + dr, c + dc) for (r, c) in cells for dr, dc in _CARD
                    if (r + dr, c + dc) not in cells]
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return cells


def _free(g, cells, r0, c0):
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r0 + r + dr, c0 + c + dc
                if not (0 <= rr < h and 0 <= cc < w):
                    if (dr, dc) == (0, 0):
                        return False
                    continue
                if g[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """≥2 separate color-3 connected components (copies) sharing a base shape."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Count color-3 connected components
    visited = [[False] * w for _ in range(h)]
    comps = 0
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] == 3:
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= h or cc < 0 or cc >= w:
                        continue
                    if visited[cr][cc] or grid[cr][cc] != 3:
                        continue
                    visited[cr][cc] = True
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        stack.append((cr+dr, cc+dc))
                comps += 1
    if comps < 2:
        errs.append(f"only {comps} color-3 object(s) found (need >=2 copies)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = the consensus base shape (cells shared across copies), so a
    # bigger/varied base gives more distinct outputs (was base_k 3..5 -> distinct=83).
    # palette is intrinsic: the rule hardcodes color 3 (canonical is [0,3] only).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 14)
        base_k = ctx.draw_int("base_k", 3, 5); n_copies = ctx.draw_int("n_copies", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 15, 19)
        base_k = ctx.draw_int("base_k", 6, 9); n_copies = ctx.draw_int("n_copies", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 17)
        base_k = ctx.draw_int("base_k", 3, 8); n_copies = ctx.draw_int("n_copies", 2, 4)
    rng = ctx.draw_rng("layout")

    base = _build_motif(rng, base_k)
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(n_copies * 60):
        if placed >= n_copies:
            break
        # each copy = the shared base + a couple distinct extra cells
        copy = _with_extras(base, rng, rng.randint(0, 2))
        rs = [r for r, _ in copy]; cs = [c for _, c in copy]
        rmin, cmin = min(rs), min(cs)
        norm = [(r - rmin, c - cmin) for r, c in copy]
        sh = max(r for r, _ in norm) + 1; sw = max(c for _, c in norm) + 1
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, norm, r0, c0):
            continue
        for (r, c) in norm:
            g[r0 + r][c0 + c] = 3
        placed += 1
    if placed < 2:                       # guarantee >=2 copies for a real consensus
        return _draw_from_degenerate("identical_copies", None)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    base = [(0, 0), (0, 1), (1, 0)]      # L-tromino
    if name == "single_copy":
        # only one colour-3 object -> no consensus -> output [[0]]
        for r, c in base:
            g[2 + r][2 + c] = 3
        return g
    if name == "disjoint_copies":
        # two copies that share no normalized cell -> empty consensus
        for r, c in [(0, 0), (1, 0), (2, 0)]:        # vertical bar
            g[1 + r][1 + c] = 3
        for r, c in [(0, 0), (0, 1), (0, 2)]:        # horizontal bar
            g[6 + r][6 + c] = 3
        return g
    # identical_copies -> two identical L's -> consensus is the whole L
    for r, c in base:
        g[1 + r][1 + c] = 3
    for r, c in base:
        g[6 + r][6 + c] = 3
    return g
