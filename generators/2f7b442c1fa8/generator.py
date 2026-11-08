"""Generator for 2f7b442c1fa8 — positional recolor by reading order.

Rule: extract all 4-connected components of non-zero cells. Sort by bbox
reading order (row, col). Recolor with palette [2, 3, 4, 5, 6, 7, 8, 9,
1] in order — first component → 2, second → 3, etc.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f7b442c1fa8"
VERSION = "2.0.1"
TASK_ID = "2f7b442c1fa8"
SUMMARY = (
    "0-bg grid with N (3-5) isolated 4-connected components, each in a "
    "distinct color (sampled freely from {1..9}). The components are "
    "scattered so no two 4-touch each other and no two share an 8-edge. "
    "Rule: collect all components, sort by their bbox top-left in "
    "reading order (row then column). Recolor in order with the palette "
    "[2, 3, 4, 5, 6, 7, 8, 9, 1]: first → 2, second → 3, third → 4, etc. "
    "Output places the recolored cells on a fresh 0-bg grid (positions "
    "preserved, only colors changed)."
)

# Rivals: 'output is input' refuted by demos where ≥1 component gets a
# new color. 'recolor by component size' refuted by demos where size
# rank != reading-order rank. 'recolor by sort top→bottom then color'
# refuted by demos with same-row components going left→right. 'recolor
# by left→right only (ignoring row)' refuted by demos with a smaller-col
# component lower-row coming AFTER a higher-row component. 'palette
# starts at 1 instead of 2' refuted by demos where first object → 2.
# 3-4 demos with mixed input colors and varied row/col mixes pin it.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "3-5 isolated 4-connected components in distinct non-zero colors",
    "components don't 4-touch and don't share an 8-edge",
    "input colors are NOT the same as the recolor palette (so rule changes ≥1 cell)",
    "components are placed at varied row/col offsets so reading-order != trivial",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h":       {"type": "int", "default": "rng 9..11", "valid": "8..15",
                     "doc": "Grid height (easy 8..9, medium 9..11, hard 12..15)."},
    "grid_w":       {"type": "int", "default": "rng 12..14", "valid": "11..18",
                     "doc": "Grid width (easy 11..12, medium 12..14, hard 14..18)."},
    "n_components": {"type": "int", "default": "rng 3..4", "valid": "3..5",
                     "doc": "Number of components to recolor (easy 3, hard 4..5)."},
}

_SHAPES = (
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (1, 1)],
)


def _free_with_buffer(g, r1, c1, r2, c2):
    """Check rect [r1..r2, c1..c2] plus 1-cell buffer is all 0."""
    h, w = len(g), len(g[0])
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


_PALETTE_OUTPUT = [2, 3, 4, 5, 6, 7, 8, 9, 1]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """3-5 isolated 4-connected components in distinct non-zero colors; bg=0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # BFS to find 4-connected components
    visited = [[False] * w for _ in range(h)]
    components = []
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] != 0:
                comp = []
                stack = [(r, c)]
                color = grid[r][c]
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= h or cc < 0 or cc >= w:
                        continue
                    if visited[cr][cc] or grid[cr][cc] != color:
                        continue
                    visited[cr][cc] = True
                    comp.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((cr + dr, cc + dc))
                components.append((color, comp))
    if not (3 <= len(components) <= 5):
        errs.append(f"expected 3-5 components, found {len(components)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_components", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")
    # Pick distinct INPUT colors that don't match the trivial output positions
    # (so output != input for at least one component).
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    # If exactly equal to first n of output palette, swap one to force change
    output_prefix = _PALETTE_OUTPUT[:n]
    if palette == output_prefix:
        i = rng.randint(0, n - 1)
        j = (i + 1) % n
        palette[i], palette[j] = palette[j], palette[i]

    for outer in range(60):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            shape = rng.choice(_SHAPES)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            if sh > h or sw > w:
                ok = False
                break
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                if not _free_with_buffer(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place {0} components".format(n))
