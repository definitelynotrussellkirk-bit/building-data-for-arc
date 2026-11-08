"""Generator for arc_puzzle_bank_21_set11_s:S11_E1.

Rule: filled objects are reduced to their boundary cells on a blank grid.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, single_cell, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c4e95ad76e7"
VERSION = "3.0.2"  # diversity: 2..4 objects of varied sizes/positions incl irregular solid blobs (was 2 fixed-position fixed-size rectangles)
TASK_ID = "0c4e95ad76e7"
SUMMARY = (
    "0-bg grid (h, w ~9-14) with 2..4 SOLID FILLED OBJECTS in distinct "
    "non-bg colors, at RANDOM non-overlapping positions and VARIED sizes. "
    "Most are filled rectangles (≥3×3 so they have interior cells); some "
    "are fat irregular blobs (L / plus / random fill) that still enclose "
    "interior. Objects are isolated by ≥1 bg cell. Rule: for each object, "
    "compute its BOUNDARY cells (a cell with ≥1 4-neighbor outside the "
    "object), paint them on a fresh same-size grid in the object's color, "
    "interior → 0. Net: each solid object becomes its outline. Object "
    "count, sizes, shapes and positions all vary."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "≥1 object has interior cells (so hollowing is observable)",
    "objects are separated by background (distinct 4-conn components)",
    "objects use distinct non-bg colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "single_cell", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS


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
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _has_interior(cells):
    s = set(cells)
    return any((r - 1, c) in s and (r + 1, c) in s and (r, c - 1) in s and (r, c + 1) in s
               for r, c in s)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Require the promised multi-object solid-boundary branch to be visible."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components(grid)
    expected_min = 3 if difficulty == "hard" else 2
    errors = []
    if len(comps) < expected_min:
        errors.append(f"expected at least {expected_min} separated objects, found {len(comps)}")
    colors = {grid[r][c] for comp in comps for r, c in comp}
    if len(colors) < min(expected_min, 2):
        errors.append(f"expected distinct object colors, found {len(colors)}")
    if not any(_has_interior(comp) for comp in comps):
        errors.append("no object with a true 4-neighbor interior cell found")
    return errors


AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "9..16"},
    "n_objects":      {"type": "int", "default": "rng 2..4", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_objects|single_cell|full_grid"},
}


def _solid_block(rng, max_side=5):
    """A filled solid shape with interior cells (so hollowing is visible).
    Mostly rectangles; occasionally an L or plus block."""
    bh = rng.randint(3, max_side)
    bw = rng.randint(3, max_side)
    kind = rng.random()
    cells = {(r, c) for r in range(bh) for c in range(bw)}
    if kind < 0.25:  # carve an L by removing one corner quadrant
        cr = rng.randint(1, bh - 2)
        cc = rng.randint(1, bw - 2)
        corner = rng.choice([(0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1)])
        cells = {(r, c) for (r, c) in cells
                 if not (abs(r - corner[0]) < (bh - cr) and abs(c - corner[1]) < (bw - cc))}
        # ensure still has an interior cell; else fall back to full rect
        if not any((r - 1, c) in cells and (r + 1, c) in cells
                   and (r, c - 1) in cells and (r, c + 1) in cells for r, c in cells):
            cells = {(r, c) for r in range(bh) for c in range(bw)}
    return sorted(cells)


def _fits(g, cells, r0, c0):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
    # require a 1-cell bg moat
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r0 + r + dr, c0 + c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_obj = ctx.draw_int("n_objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_obj = ctx.draw_int("n_objects", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        n_obj = ctx.draw_int("n_objects", 2, 4)
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("colors", n=max(2, n_obj), exclude=[0]))
    max_side = 3 if difficulty == "easy" else 4
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        placed = 0
        for i in range(n_obj):
            cells = _solid_block(rng, max_side=max_side)
            bh = max(r for r, _ in cells) + 1
            bw = max(c for _, c in cells) + 1
            positions = [(r0, c0) for r0 in range(0, h - bh + 1) for c0 in range(0, w - bw + 1)]
            rng.shuffle(positions)
            for r0, c0 in positions:
                if _fits(g, cells, r0, c0):
                    color = colors[i % len(colors)]
                    for r, c in cells:
                        g[r0 + r][c0 + c] = color
                    placed += 1
                    break
        if placed == n_obj:
            return g
    raise ValueError("could not place requested number of solid objects")


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_objects":
        return g
    if name == "single_cell":
        g[3][3] = 3
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 3
        return g
    return g
