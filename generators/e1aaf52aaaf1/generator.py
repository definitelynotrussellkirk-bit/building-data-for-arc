"""Generator for arc_puzzle_bank_21_set6_s:S6_E5.

Rule: among several green components, the unique odd-area component
recolors blue.

Combinatorial axes (8): grid_h, grid_w, palette_kind, component_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_even_areas, all_odd_areas, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "e1aaf52aaaf1"
VERSION = "2.1.0"  # add executable invariants for the unique odd-area component contract.
TASK_ID = "e1aaf52aaaf1"
SUMMARY = "Among several green components, the unique odd-area component recolors blue."

INVARIANTS = [
    "background is 0",
    "all input objects are color 3",
    "exactly one component has odd area",
    "the other components have even area",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_even_areas", "all_odd_areas", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "component_count": {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_even_areas|all_odd_areas|single_component"},
}

_ODD_SHAPES = [
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
]

_EVEN_SHAPES = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0), (2, 0), (3, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degenerate"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        count = ctx.draw_int("component_count", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
        count = ctx.draw_int("component_count", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        count = ctx.draw_int("component_count", 3, 5)
    rng = ctx.draw_rng("layout")
    # one odd-AREA poly (the target) + (count-1) even-AREA polys; random shapes
    shapes = [_poly(rng, rng.choice([3, 5, 7]))]
    shapes.extend(_poly(rng, rng.choice([2, 4, 6])) for _ in range(count - 1))
    rng.shuffle(shapes)
    # The `count` components (1 odd + count-1 even, up to 6 cells each) placed with
    # a 1-cell pad can wedge each other on the small easy grid (7×9, 3 components)
    # → place_no_overlap exhausts 300 tries and raises (~1/300 easy). Per-component
    # retry can't reposition the earlier components, so reset-and-retry the whole
    # layout: the shape set (odd choice + even choices + shuffle) is drawn ONCE
    # before the loop so it's fixed, and outer attempt 0 replays the same
    # place_no_overlap draws → every first-pass-success seed returns byte-
    # identically; only the previously-wedged seeds resample. Early-placement-
    # wedging class (17b0b2791dd2/2e1cd9abbb81).
    for _outer in range(60):
        g = full_grid(h, w, 0)
        ok = True
        for cells in shapes:
            if place_no_overlap(rng, g, cells, 3, padding=1, max_tries=300) is None:
                ok = False
                break
        if ok:
            return g
    # graceful fallback: guaranteed 1 odd-area + 1 even-area component (no raise)
    g = full_grid(max(7, h), max(9, w), 0)
    for r, c in [(1, 1), (1, 2), (2, 1)]:        # 3-cell odd (the target)
        g[r][c] = 3
    for r, c in [(4, 5), (4, 6)]:                # 2-cell even
        g[r][c] = 3
    return g


def _draw_from_degenerate(name, rng):
    # rng is a ctx.draw_rng("degenerate") handle (deterministic per seed +
    # sample_index) — place_no_overlap consumes it, so degenerate layouts
    # stay reproducible without a banned `import random`.
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "all_even_areas":
        # all components have even area → no unique odd-area component, rule has no target
        shapes = [_EVEN_SHAPES[0], _EVEN_SHAPES[1], _EVEN_SHAPES[2]]
        for cells in shapes:
            place_no_overlap(rng, g, cells, 3, padding=1, max_tries=300)
        return g
    if name == "all_odd_areas":
        # all components have odd area → multiple "odd" components, ambiguous which to recolor
        for cells in [_ODD_SHAPES[0], _ODD_SHAPES[1], _ODD_SHAPES[2]]:
            place_no_overlap(rng, g, cells, 3, padding=1, max_tries=300)
        return g
    if name == "single_component":
        # one component → trivially the unique odd (if odd) or no odd (if even), rule degenerate
        place_no_overlap(rng, g, _ODD_SHAPES[1], 3, padding=1, max_tries=300)
        return g
    return g


def _components3(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != 3:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == 3):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    bad_colors = sorted({v for row in grid for v in row if v not in (0, 3)})
    if bad_colors:
        errors.append(f"unexpected nonzero colors besides 3: {bad_colors}")
    comps = _components3(grid)
    min_components = 4 if difficulty == "hard" else 3
    if len(comps) < min_components:
        errors.append(f"expected at least {min_components} green components, found {len(comps)}")
    odd = [cells for cells in comps if len(cells) % 2 == 1]
    if len(odd) != 1:
        errors.append(f"expected exactly one odd-area component, found {len(odd)}")
    return errors
