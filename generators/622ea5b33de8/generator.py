"""Generator for arc_puzzle_bank_21_set17_bundle:hard_p03 — adjacency matrix via dilation overlap.

Rule: connected components sorted top-left. Output N×N: diagonal = component
color, off-diagonal = 8 if their dilated (1-cell halo) cells overlap, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_far (no pair within 1 cell → output diagonal-only,
hides the off-diagonal "8" branch); all_close (every pair within 1
cell → output is full off-diagonal 8s, hides far branch);
single_component (rule's N×N output is just a 1×1 diagonal — no
adjacency information visible).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "622ea5b33de8"
VERSION = "2.0.1"
TASK_ID = "622ea5b33de8"

SUMMARY = (
    "0-bg grid (h~9-14, w~12-18) containing "
    "3-5 small CONNECTED COMPONENTS, each in a "
    "DISTINCT non-zero color. Each component "
    "is 1-3 cells from a small shape bank "
    "(singletons, dominos, corners). "
    "Components are 4-conn isolated. SOME "
    "pairs are placed CLOSE (1-cell apart, "
    "so their 1-cell DILATED HALOES OVERLAP); "
    "others are FAR apart (no halo overlap). "
    "Rule: SORT the N components in TOP-LEFT "
    "scan order. Build an N×N ADJACENCY "
    "MATRIX: diagonal[i][i] = component i's "
    "COLOR; off-diagonal[i][j] = 8 if i and j's "
    "1-cell DILATED HALOES OVERLAP (1-cell "
    "apart or closer), else 0. Net: input is "
    "scattered colored components; output is "
    "a small N×N matrix encoding pairwise "
    "dilation-adjacency."
)

INVARIANTS = [
    "background is 0",
    "3-4 isolated 4-conn components in distinct colors",
    "some components are 1-cell apart (dilation overlap), others are far apart",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_far", "all_close", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "n_components":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "mixed_near_far",
                       "valid": "mixed_near_far"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
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
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            shape = rng.choice([
                [(0, 0), (0, 1)],
                [(0, 0), (1, 0)],
                [(0, 0), (0, 1), (1, 0)],
                [(0, 0), (0, 1), (1, 1)],
                [(0, 0)],
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=3 isolated nonzero components in distinct colors."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    visited = [[False] * w for _ in range(h)]
    comp_colors = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 and not visited[sr][sc]:
                q = [(sr, sc)]
                visited[sr][sc] = True
                colors_in = set()
                while q:
                    r, c = q.pop()
                    colors_in.add(grid[r][c])
                    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr, nc))
                comp_colors.append(frozenset(colors_in))
    if len(comp_colors) < 3:
        errors.append(f"expected >=3 isolated components, found {len(comp_colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 14
    g = full_grid(h, w, 0)
    if name == "all_far":
        # Three components each ≥3 cells apart on every side → no
        # dilation halos overlap; output's off-diagonal is all 0,
        # hiding the "8" branch.
        for cells, color, base in [([(0, 0), (0, 1)], 1, (1, 1)),
                                   ([(0, 0), (0, 1)], 2, (5, 8)),
                                   ([(0, 0), (1, 0)], 3, (8, 2))]:
            for dr, dc in cells:
                g[base[0] + dr][base[1] + dc] = color
        return g
    if name == "all_close":
        # Three components packed so every pair has 1-cell halo
        # overlap → output is N×N with 8 everywhere off-diagonal,
        # hiding the "no overlap → 0" branch.
        for cells, color, base in [([(0, 0)], 1, (3, 3)),
                                   ([(0, 0)], 2, (3, 5)),
                                   ([(0, 0)], 3, (3, 7))]:
            for dr, dc in cells:
                g[base[0] + dr][base[1] + dc] = color
        return g
    if name == "single_component":
        # Only one component → rule's N×N output is 1×1 (just the
        # diagonal); no adjacency information to convey.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][6 + dc] = 4
        return g
    return g
