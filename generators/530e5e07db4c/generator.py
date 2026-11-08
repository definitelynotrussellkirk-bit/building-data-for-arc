"""Generator for 468bcf25.

Rule: BFS from 2-seed through cells {2,3,5}; if 3-seed is in component,
recolor reached 5-cells to 4.

Combinatorial axes (8): grid_h/w, path_orientation, n_isolated_stubs,
seed_2_position, seed_3_position, palette_kind, anchor_corner,
asymmetry_force.
Degenerates: no_path, no_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "530e5e07db4c"
VERSION = "2.1.0"
TASK_ID = "530e5e07db4c"
SUMMARY = (
    "0-bg grid (h~6-8, w~9-11) with: (a) one RED(2) SEED; "
    "(b) one BLUE(3) SEED; (c) a connected PATH of GRAY(5) "
    "cells linking them (4-connected through cells with value "
    "∈ {2, 3, 5}); (d) 1-2 ISOLATED GRAY(5) STUB cells "
    "elsewhere, not connected to the path. Path orientations "
    "vary (horizontal, vertical, L, diagonal-by-stair). Rule: "
    "BFS from the 2-seed through cells with value in {2, 3, "
    "5} (4-connectivity). If the BFS reaches the 3-seed → "
    "for every 5-cell in the reachable component, recolor it "
    "to YELLOW(4). Else output unchanged. Isolated 5-stubs "
    "stay as 5 (not reachable, not recolored)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one 2-seed and one 3-seed",
    "5-cells form a connected path between them",
    "1-2 isolated 5-cells off-path",
    "path orientations vary across train pairs (h/v/L/diagonal)",
]

PATH_ORIENTATIONS = ("horizontal", "vertical", "L_shape", "diagonal")
DEGENERATE_TEXTURES = ("no_path", "no_seeds", "full_grid")
HELPFUL_TEXTURES = PATH_ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "path_orientation":{"type": "str", "default": "rng helpful",
                       "valid": "horizontal|vertical|L_shape|diagonal"},
    "n_isolated_stubs":{"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "seed_2_position":{"type": "str", "default": "rng",
                       "valid": "tl|tr|bl|br|left|right"},
    "seed_3_position":{"type": "str", "default": "rng",
                       "valid": "tl|tr|bl|br|left|right"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for path_orientation",
                       "valid": "horizontal|vertical|L_shape|diagonal|no_path|no_seeds|full_grid"},
}


def _component_through_path(grid, start):
    h, w = len(grid), len(grid[0])
    stack = [start]
    seen = {start}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                    and grid[nr][nc] in (2, 3, 5)):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


def _is_cardinally_isolated(grid, r, c):
    h, w = len(grid), len(grid[0])
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] in (2, 3, 5):
            return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify default examples actually fire the reachability rule."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(twos) != 1:
        errors.append(f"expected exactly one color-2 seed, found {len(twos)}")
    if len(threes) != 1:
        errors.append(f"expected exactly one color-3 seed, found {len(threes)}")
    if not fives:
        errors.append("no color-5 path cells found")
    if errors:
        return errors

    main = _component_through_path(grid, twos[0])
    if threes[0] not in main:
        errors.append("2-seed and 3-seed are not 4-connected through {2,3,5}")
    reached_fives = [p for p in fives if p in main]
    off_path_fives = [p for p in fives if p not in main]
    if not reached_fives:
        errors.append("no color-5 cells are reachable from the 2-seed")
    if not (1 <= len(off_path_fives) <= 4):
        errors.append(f"expected 1-4 isolated off-path 5-cells, found {len(off_path_fives)}")
    for r, c in off_path_fives:
        if not _is_cardinally_isolated(grid, r, c):
            errors.append("off-path 5-cells must be cardinally isolated from seeds/path/stubs")
            break
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 6, 7, 9
        ns_lo, ns_hi = 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 14, 12, 14
        ns_lo, ns_hi = 2, 4
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 8, 9, 11
        ns_lo, ns_hi = 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    orient = (overrides.get("texture") or
              overrides.get("path_orientation")
              or ctx.draw_choice("path_orientation",
                                 list(PATH_ORIENTATIONS)))
    if orient == "horizontal":
        r = rng.randint(1, h - 2)
        g[r][1] = 2
        for c in range(2, w - 2):
            g[r][c] = 5
        g[r][w - 2] = 3
    elif orient == "vertical":
        c = rng.randint(1, w - 2)
        g[1][c] = 2
        for r in range(2, h - 2):
            g[r][c] = 5
        g[h - 2][c] = 3
    elif orient == "L_shape":
        r1 = 1; r2 = h - 2; c1 = 1; c2 = w - 2
        g[r1][c1] = 2
        for c in range(c1 + 1, c2):
            g[r1][c] = 5
        for r in range(r1, r2):
            g[r][c2] = 5
        g[r2][c2] = 3
    else:
        # A visually diagonal path still must be 4-connected for the canonical
        # BFS rule.  Build a stair-step route from the red seed to the blue
        # seed instead of placing disconnected diagonal cells.
        r1 = 1; c1 = 1
        r2 = h - 2; c2 = w - 2
        g[r1][c1] = 2
        cr, cc = r1, c1
        prefer_row = bool(rng.getrandbits(1))
        while (cr, cc) != (r2, c2):
            can_down = cr < r2
            can_right = cc < c2
            if can_down and can_right:
                if prefer_row:
                    cr += 1
                else:
                    cc += 1
                prefer_row = not prefer_row
            elif can_down:
                cr += 1
            else:
                cc += 1
            if (cr, cc) == (r2, c2):
                g[cr][cc] = 3
            else:
                g[cr][cc] = 5
    n_stubs = int(overrides.get("n_isolated_stubs",
                                ctx.draw_int("n_isolated_stubs",
                                             ns_lo, ns_hi)))
    n_stubs = max(0, min(4, n_stubs))
    placed = 0
    tries = 0
    while placed < n_stubs and tries < 200:
        tries += 1
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0 and _is_cardinally_isolated(g, r, c):
            g[r][c] = 5
            placed += 1
    if placed < n_stubs:
        # Deterministic fallback: keep the rule-firing main path and place as
        # many truly isolated distractors as the grid can support.
        for r in range(h):
            for c in range(w):
                if placed >= n_stubs:
                    break
                if g[r][c] == 0 and _is_cardinally_isolated(g, r, c):
                    g[r][c] = 5
                    placed += 1
            if placed >= n_stubs:
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_path":
        g[1][1] = 2
        g[1][w - 2] = 3
        return g
    if name == "no_seeds":
        for c in range(2, w - 2):
            g[3][c] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
