"""Generator for e9cd770abc01 — recolor the center-closest color-3 object to 7.

Rule (verified from canonical Racket): among all color-3 objects, pick the one
whose bbox center is closest to the grid center (ties broken by bbox order) and
repaint it color 7.

The previous body was the generic "6 panels, find the matching pair" template,
which placed random motifs and frequently had no color-3 object at all, so the
rule's `(first (sort (objs-color g 3) ...))` returned #f / crashed (rule_smoke
8/15). This 2.2.0 rewrite CONSTRUCTS valid inputs: several separated color-3
objects at varying distances from the grid center, plus a few non-{3,7}
distractor objects, so the "closest to center" choice is well-defined and
varies.

Axes: grid size, number of color-3 objects, distractor count, shapes, positions.
Degenerates: single_three, dense_three, no_distractor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e9cd770abc01"
VERSION = "2.2.0"  # REWRITE: center-closest color-3 -> 7 (was find-pair template; crashed 8/15 on missing color-3 objects)
TASK_ID = "e9cd770abc01"

SUMMARY = (
    "Several separated color-3 objects (plus non-{3,7} distractors). Rule: "
    "repaint the color-3 object whose bbox center is closest to the grid center "
    "as color 7. Grid size, object count, shapes and positions vary."
)

INVARIANTS = [
    "background is 0",
    ">=1 connected color-3 object (each separated by >=1 bg cell)",
    "distractor objects use non-{0,3,7} colors",
    "objects do not touch, so each is a distinct connected component",
]

DEGENERATE_TEXTURES = ("single_three", "dense_three", "no_distractor")
HELPFUL_TEXTURES = ("balanced", "spread", "compact")

_DISTRACTOR = (1, 2, 4, 5, 6, 8, 9)        # non-0, non-3, non-7

AXES = {
    "grid_h":      {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "grid_w":      {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "n_three":     {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "n_distract":  {"type": "int", "default": "rng 1..3", "valid": "0..5"},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "balanced|spread|compact|single_three|dense_three|no_distractor"},
}


def _walk(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}; tries = 0
    while len(cells) < k and tries < 40:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nc = (r + dr, c + dc)
        if nc not in seen:
            cells.append(nc); seen.add(nc)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _place(g, h, w, rng, color, k, occupied):
    shape = _walk(rng, k)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        cells = {(top + r, left + c) for r, c in shape}
        halo = {(r + dr, c + dc) for (r, c) in cells
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if halo & occupied:
            continue
        for (r, c) in cells:
            g[r][c] = color
        occupied |= halo
        return True
    return False


def _build(rng, h, w, n_three, n_distract):
    g = full_grid(h, w, 0)
    occupied = set()
    placed = 0
    for _ in range(n_three):
        if _place(g, h, w, rng, 3, rng.randint(2, 5), occupied):
            placed += 1
    if placed == 0:                       # guarantee at least one color-3 object
        _place(g, h, w, rng, 3, 3, occupied)
    for _ in range(n_distract):
        _place(g, h, w, rng, rng.choice(_DISTRACTOR), rng.randint(2, 5), occupied)
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        sz_lo, sz_hi, t_lo, t_hi, d_lo, d_hi = 10, 12, 2, 3, 1, 2
    elif difficulty == "hard":
        sz_lo, sz_hi, t_lo, t_hi, d_lo, d_hi = 14, 18, 3, 6, 2, 4
    else:
        sz_lo, sz_hi, t_lo, t_hi, d_lo, d_hi = 11, 15, 2, 4, 1, 3

    h = ctx.draw_int("grid_h", sz_lo, sz_hi)
    w = ctx.draw_int("grid_w", sz_lo, sz_hi)
    n_three = ctx.draw_int("n_three", t_lo, t_hi)
    n_distract = ctx.draw_int("n_distract", d_lo, d_hi)
    return _build(rng, h, w, n_three, n_distract)


def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in q:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the center-closest color-3-object task."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    flat = [v for row in grid for v in row]
    if 7 in flat:
        errs.append("input already contains output color 7")
    if any(v < 0 or v > 9 for v in flat):
        errs.append("grid contains colors outside 0..9")
    comps = _components_of_color(grid, 3)
    if not comps:
        errs.append("no color-3 object for the rule to select")
        return errs
    if len(comps) < 2 and difficulty != "easy":
        errs.append("fewer than two color-3 objects; closest-to-center choice is not visible")
    comp_index = {}
    for i, cells in enumerate(comps):
        for rc in cells:
            comp_index[rc] = i
    for i, cells in enumerate(comps):
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    j = comp_index.get((r + dr, c + dc))
                    if j is not None and j != i:
                        errs.append("distinct color-3 objects touch diagonally/orthogonally")
                        return errs
    return errs


def _draw_from_degenerate(name, rng):
    if name == "single_three":
        return _build(rng, 11, 11, 1, 2)
    if name == "dense_three":
        return _build(rng, 15, 15, 6, 0)
    return _build(rng, 12, 12, 3, 0)      # no_distractor
