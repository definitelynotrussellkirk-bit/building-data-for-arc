"""Generator for arc_puzzle_bank_21_set24_s:S24_M3.

Rule: a connected solid shape produces a one-row histogram of onion
depths.

Combinatorial axes (8): grid_h, grid_w, palette_kind, radius,
palette_size, position_bias, n_distinct_colors, shape_kind, texture.
Degenerates: empty_grid, two_shapes, hollow_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12ace26107fd"
VERSION = "3.0.2"  # diversity: random connected solid polyominoes (varied size/shape/color) instead of only radius-1/2 diamonds; depth histogram now spans many distinct outputs (was 2)
TASK_ID = "12ace26107fd"
SUMMARY = (
    "0-bg grid with ONE CONNECTED SOLID shape (a random polyomino of "
    "varied size/shape, single non-0/non-9 color). The rule onion-"
    "peels the shape's binary mask: layer L holds the count of cells "
    "still present after eroding L Manhattan steps from the boundary; "
    "output is a ONE-ROW (1 x K) grid of those layer counts. Varying "
    "the shape (compactness controls peel depth, size controls the "
    "layer-1 count) spreads the histogram across many distinct outputs "
    "(was a radius-1/2 diamond yielding only 2 histograms)."
)

INVARIANTS = [
    "the input contains one nonzero connected shape",
    "background is zero",
    "the output is a one-row count per erosion layer",
]

PALETTE_KINDS = ("default", "small", "medium", "large")
DEGENERATE_TEXTURES = ("empty_grid", "two_shapes", "hollow_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|small|medium|large"},
    "shape_size":     {"type": "int", "default": "rng 5..9", "valid": "3..9"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "shape_kind":     {"type": "str", "default": "random_polyomino",
                       "valid": "random_polyomino"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|small|medium|large|empty_grid|two_shapes|hollow_shape"},
}

# Color 9 is excluded (the rule treats 9 like background).
_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)


def _grow_solid(rng, target, h, w):
    """Grow a connected polyomino of ~`target` cells, biased toward
    compactness (BFS frontier weighted by # of already-filled
    neighbours) so the onion-depth histogram has multiple layers."""
    cells = {(0, 0)}
    for _ in range(target * 12):
        if len(cells) >= target:
            break
        # frontier: empty neighbours of current cells
        frontier = {}
        for (r, c) in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in cells:
                    continue
                nb = sum(1 for ddr, ddc in
                         ((-1, 0), (1, 0), (0, -1), (0, 1))
                         if (p[0] + ddr, p[1] + ddc) in cells)
                frontier[p] = nb
        if not frontier:
            break
        # pick weighted toward higher neighbour count (fills concavities)
        items = list(frontier.items())
        weights = [n * n + 1 for _, n in items]
        choice = rng.choices([p for p, _ in items], weights=weights)[0]
        cells.add(choice)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    norm = [(r - mr, c - mc) for r, c in cells]
    sh = max(r for r, _ in norm) + 1
    sw = max(c for _, c in norm) + 1
    if sh > h or sw > w:
        return None
    return norm


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one connected nonzero shape (except degenerate two_shapes)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return errors  # degenerate (empty_grid) — allowed
    # BFS to count connected components
    visited = set()
    components = 0
    for start in nonzero:
        if start in visited:
            continue
        components += 1
        stack = [start]
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in visited:
                    stack.append((nr, nc))
    if components > 2:
        errors.append(f"found {components} components, expected 1 or 2")
    if len(nonzero) > 9:
        errors.append(f"shape has {len(nonzero)} cells; onion histogram layer counts can exceed digit range 0..9")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        size = ctx.draw_int("shape_size", 5, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        size = ctx.draw_int("shape_size", 7, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        size = ctx.draw_int("shape_size", 5, 9)
    color = int(overrides.get("color", rng.choice(_COLORS)))

    for _attempt in range(60):
        shape = _grow_solid(rng, size, h, w)
        if shape is None:
            continue
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        g = full_grid(h, w, 0)
        for r, c in shape:
            g[top + r][left + c] = color
        return g
    raise ValueError("could not realize onion shape")


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no shape — onion depth histogram is empty
        return g
    if name == "two_shapes":
        # two separate components → predicate "one connected shape" fails
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][5 + dc] = 2
        return g
    if name == "hollow_shape":
        # shape with a hole → erosion layer counts mis-represent "solid" depth
        for r, c in [(2, 2), (2, 3), (2, 4), (3, 2), (3, 4), (4, 2), (4, 3), (4, 4)]:
            g[r][c] = 2
        return g
    return g

LAWFUL_MINIMAL_PROBES = {'solid_2x2': {'justification': 'The selected onion rule accepts connected solid shapes; four cells form one nonempty shell and produce a single count of four.', 'rule_hash': '3e24db6285e1', 'expected_output': [[4]]}, 'short_line': {'justification': 'The selected onion rule accepts connected solid shapes; four cells form one nonempty shell and produce a single count of four.', 'rule_hash': '3e24db6285e1', 'expected_output': [[4]]}}
