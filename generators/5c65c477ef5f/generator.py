"""Generator for arc_puzzle_bank_21_set13_s:S13_E6 — smallest asymmetric → 8.

The smallest object with no horizontal or vertical symmetry is cropped and
recolored to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_symmetric (no asymmetric components → rule's selector
finds nothing, output equals input), tied_smallest_asym (≥2 asymmetric
components share min size → "smallest" tie-break decides), single_asym
(only one asymmetric component → trivially selected, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c65c477ef5f"
VERSION = "3.0.0"  # distinct=1: output is the smallest-asymmetric object cropped+recoloured 8, but the TARGET was a fixed L-tromino -> constant. Now a RANDOM asymmetric target (3-6 cells, uniquely smallest) + strictly-larger asymmetric distractors + a symmetric decoy -> distinct 1->66 (residual dup intrinsic to small-asym-shape output).
TASK_ID = "5c65c477ef5f"
SUMMARY = (
    "0-bg grid (h~10-13, w~12-15) with 3-5 "
    "SEPARATED CONNECTED OBJECTS at scattered "
    "positions, each in a distinct color from "
    "{2..5}: (a) ONE small 3-cell L-shape "
    "TARGET object (strictly asymmetric — no "
    "lr/ud symmetry); (b) 1-3 LARGER "
    "asymmetric distractor blobs (4-5 cells, "
    "also no lr/ud symmetry); (c) ONE smaller "
    "or larger SYMMETRIC distractor (2×2 "
    "square, plus-shape, etc.). Objects don't "
    "touch each other. Rule: for EVERY "
    "connected object, check if it has NO "
    "horizontal AND NO vertical symmetry (i.e., "
    "is fully asymmetric). Among all "
    "ASYMMETRIC objects, find the SMALLEST one "
    "(strict minimum by cell count). CROP it "
    "to its bbox and RECOLOR every cell to "
    "color 8 (cyan). Output is just that "
    "cropped, recolored small subgrid. Net: "
    "input has several mixed-symmetry objects; "
    "output is the tiniest asymmetric one, "
    "alone, painted cyan."
)

INVARIANTS = [
    "background is 0",
    "there is one strictly smallest asymmetric component",
    "larger asymmetric components and symmetric distractors may also appear",
    "the selected asymmetric crop is recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_symmetric", "tied_smallest_asym", "single_asym")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "asym_distractors": {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "asym_target_plus_distractors",
                       "valid": "asym_target_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TARGET = [(0, 0), (1, 0), (1, 1)]
_ASYM_BIG = [
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 1), (3, 1)],
]
_SYMMETRIC = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return
    raise ValueError("could not place object")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 10, 11)
        w = ctx.draw_int("width", 12, 13)
        asym_count = ctx.draw_int("asym_distractors", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 16)
        w = ctx.draw_int("width", 15, 18)
        asym_count = ctx.draw_int("asym_distractors", 2, 3)
    else:
        h = ctx.draw_int("height", 10, 13)
        w = ctx.draw_int("width", 12, 15)
        asym_count = ctx.draw_int("asym_distractors", 1, 2)
    rng = ctx.draw_rng("layout")
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2 + asym_count)
    # TARGET: a RANDOM asymmetric polyomino, the UNIQUELY-smallest asymmetric
    # object (output = it cropped + recoloured 8). Asymmetric distractors are
    # strictly larger; one symmetric shape is ignored by the rule.
    st = rng.randint(3, 6)
    # Placing several padded polyominoes (hard band: up to 4 objects, distractors
    # ~10 cells) congests a tight board for a rare seed -> _place raises. The rule
    # is board-size-agnostic, so retry on a board grown by 1 each round.
    for _attempt in range(40):
        g = full_grid(h + _attempt, w + _attempt, 0)
        try:
            _place(g, rng, _rand_asym(rng, st), colors[0])
            for i in range(asym_count):
                _place(g, rng, _rand_asym(rng, rng.randint(st + 2, st + 4)),
                       colors[1 + i])
            _place(g, rng, rng.choice(_SYMMETRIC), colors[-1])
            return g
        except ValueError:
            continue
    raise ValueError("could not place object")


def _norm_cells(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return sorted((r - r0, c - c0) for r, c in cells)


def _is_asym(cells):
    n = _norm_cells(cells)
    maxr = max(r for r, _ in n); maxc = max(c for _, c in n)
    lr = sorted((r, maxc - c) for r, c in n)
    ud = sorted((maxr - r, c) for r, c in n)
    return n != lr and n != ud


def _rand_asym(rng, k):
    """A random connected k-cell polyomino with NO lr/ud mirror symmetry."""
    for _ in range(80):
        cells = [(0, 0)]; seen = {(0, 0)}
        for _ in range(200):
            if len(cells) >= k:
                break
            br, bc = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = br + dr, bc + dc
            if (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        cells = _norm_cells(cells)
        if len(cells) >= 3 and _is_asym(cells):
            return cells
    return [(0, 0), (1, 0), (1, 1)]    # L-tromino fallback (asymmetric)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            color = grid[r][c]
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None):
    problems = []
    comps = _components(grid)
    if len(comps) < 3:
        problems.append(f"expected target, asymmetric distractor, and symmetric distractor; found {len(comps)} components")
    asym = [cells for cells in comps if _is_asym(cells)]
    sym = [cells for cells in comps if not _is_asym(cells)]
    if len(asym) < 2:
        problems.append(f"expected at least two asymmetric components, found {len(asym)}")
    if not sym:
        problems.append("missing symmetric distractor component")
    if asym:
        sizes = [len(cells) for cells in asym]
        if sizes.count(min(sizes)) != 1:
            problems.append(f"asymmetric target is not uniquely smallest: sizes={sizes}")
        if min(sizes) < 3:
            problems.append("smallest asymmetric component is too small to exercise shape reasoning")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "all_symmetric":
        # No asymmetric components — rule's "smallest asymmetric"
        # selector finds nothing; output equals input.
        for dr, dc in _SYMMETRIC[0]:
            g[1 + dr][2 + dc] = 2
        for dr, dc in _SYMMETRIC[1]:
            g[6 + dr][8 + dc] = 4
        return g
    if name == "tied_smallest_asym":
        # Two asymmetric components share min size → "smallest"
        # is ambiguous; tie-break decides.
        for dr, dc in _TARGET:
            g[2 + dr][2 + dc] = 2
        for dr, dc in _TARGET:
            g[2 + dr][8 + dc] = 3
        for dr, dc in _ASYM_BIG[0]:
            g[7 + dr][3 + dc] = 4
        return g
    if name == "single_asym":
        # Only one asymmetric component — trivially selected; no
        # cross-candidate contrast.
        for dr, dc in _TARGET:
            g[3 + dr][4 + dc] = 6
        for dr, dc in _SYMMETRIC[0]:
            g[7 + dr][8 + dc] = 5
        return g
    return g
