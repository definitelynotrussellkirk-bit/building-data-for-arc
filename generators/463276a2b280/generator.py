"""Generator for arc_puzzle_bank_21_set14_bundle:medium_n05 — draw bbox frames.

Rule: for every nonzero connected component, draw the border of that component's
bounding box in the component color on a 0 background.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_isolated, all_touching, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "463276a2b280"
VERSION = "1.2.0"
TASK_ID = "463276a2b280"

SUMMARY = "3-5 isolated non-rectangular components; rule draws each component's same-color bounding-box frame."

INVARIANTS = [
    "background is 0",
    "3-5 isolated 4-conn components in distinct colors",
    "each component is missing at least one cell from its bbox border so the frame-draw rule is demonstrated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_isolated", "all_touching", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "n_components":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_components",
                       "valid": "scattered_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 12, 12)
        n = ctx.draw_int("n_components", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 17)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            shape = rng.choice([
                [(0, 0), (0, 1), (1, 0)],
                [(0, 0), (1, 0), (1, 1)],
                [(0, 0), (0, 1), (1, 1)],
                [(0, 0), (0, 1), (1, 0), (2, 0)],
                [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],
            ])
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place {0} components".format(n))


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "all_isolated":
        # All components Manhattan-far from each other → all degree
        # 0; rule maps everything to color 2.
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 1
        for r, c in [(1, 10), (1, 11)]: g[r][c] = 3
        for r, c in [(8, 1), (8, 2)]: g[r][c] = 4
        for r, c in [(8, 10), (8, 11)]: g[r][c] = 5
        return g
    if name == "all_touching":
        # All components within Manhattan-2 of every other → uniform
        # high degree; rule's discrimination collapses.
        for r, c in [(2, 4), (2, 5)]: g[r][c] = 1
        for r, c in [(4, 4), (4, 5)]: g[r][c] = 3
        for r, c in [(2, 7), (2, 8)]: g[r][c] = 4
        for r, c in [(4, 7), (4, 8)]: g[r][c] = 5
        return g
    if name == "single_component":
        # Only one component — trivially degree 0; no contrast.
        for r, c in [(4, 5), (4, 6), (5, 6)]: g[r][c] = 6
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def _bbox_border(cells):
    r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; 3-5 distinct-color components that will expand to bbox frames."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    comps = _components(grid)
    if not (3 <= len(comps) <= 5):
        errors.append(f"expected 3-5 nonzero components, found {len(comps)}")
    colors = [color for color, _cells in comps]
    if len(colors) != len(set(colors)):
        errors.append("component colors should be distinct")
    for color, cells in comps:
        border = _bbox_border(cells)
        cellset = set(cells)
        if not cellset <= border:
            errors.append(f"component color {color} has cells inside, not on, its bbox border")
        if not (border - cellset):
            errors.append(f"component color {color} already equals its bbox frame; output would not change for it")
    return errors
