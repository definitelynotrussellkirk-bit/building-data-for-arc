"""Generator for 8b:m54 — checker-fill each bbox.

Rule: each blob → fill its bbox with a checker pattern in same color
(every other cell starting from top-left).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_cell_blobs, no_blobs, all_solid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "67d6bf21f48a"
VERSION = "2.0.0"
TASK_ID = "67d6bf21f48a"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with 2-3 "
    "BLOBS — each a 2-4 cell 4-connected "
    "blob grown via grow_blob, painted in "
    "a DISTINCT non-0 color drawn from "
    "{1..9}. Blobs are placed at non-"
    "touching positions with non-"
    "overlapping bboxes (tracked in "
    "used set). Each blob has bbox ≥ "
    "2×2 (size ≥ 2 ensures the checker "
    "pattern is visible). Rule (FILL "
    "EACH BLOB'S BBOX WITH A CHECKER "
    "PATTERN IN THE BLOB'S COLOR): for "
    "EACH 4-CONNECTED non-bg blob of "
    "color C: COMPUTE its bbox (r1, "
    "c1, r2, c2). For EACH cell (r, c) "
    "in the bbox: PAINT (r, c) with "
    "COLOR C if (r + c) parity matches "
    "the bbox's top-left parity "
    "(checker pattern starting with C "
    "at (r1, c1)); ELSE leave as bg-0. "
    "The original blob cells are "
    "absorbed into the checker fill. "
    "Net: each irregular blob inflates "
    "into a checker pattern within "
    "its bbox, in its color."
)

INVARIANTS = [
    "background is 0",
    "blobs of size >= 2 with bbox >= 2x2",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_cell_blobs", "no_blobs", "all_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    for color in palette:
        cells = None
        for _ in range(60):
            cand = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=80)
            if cand is None:
                continue
            bh = max(r for r, _ in cand) - min(r for r, _ in cand) + 1
            bw = max(c for _, c in cand) - min(c for _, c in cand) + 1
            if bh >= 2 and bw >= 2:
                cells = cand
                break
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]; cells = []; stack = [(r, c)]; seen.add((r, c))
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components(grid)
    if len(comps) < 2:
        errors.append("expected at least two blobs")
    for color, cells in comps:
        if len(cells) < 3:
            errors.append(f"color {color} blob must have at least three cells")
        bh = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if bh < 2 or bw < 2:
            errors.append(f"color {color} blob bbox must be at least 2x2")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "single_cell_blobs":
        # 1x1 bbox blobs → checker fill is just the single cell, no pattern visible
        g[2][2] = 3; g[5][7] = 6
        return g
    if name == "no_blobs":
        # empty grid → nothing to fill
        return g
    if name == "all_solid":
        # blobs already fill their bboxes solidly → checker fill removes half
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 4
        for r in range(5, 8):
            for c in range(5, 8): g[r][c] = 6
        return g
    return g
