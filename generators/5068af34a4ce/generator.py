"""Generator for b9630600.

Rule: build the minimum-gap spanning tree over the rectangles and, for
each tree edge, draw a color-3 corridor across the gap (two parallel
walls at the overlap-interior boundary rows/cols) and punch a doorway
(set to 0) through each rectangle's facing edge.

This generator emits an aligned CHAIN of rectangles (all sharing the
same perpendicular band) so every consecutive pair is a valid edge and
no rectangle blocks another -- the MST is exactly the chain, giving a
clean string of corridors.

Combinatorial axes: orientation (h/v), the rectangle count, each
rectangle's size, the gaps, the band position, the grid size, the color.
Degenerates: no_rects, single_rect, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "5068af34a4ce"
RULE_HASH = "8c30bd1916c0"  # canonical rule this generator was written against
VERSION = "2.2.0"  # restore canonical 30x30 hollow color-3 rectangle distribution
TASK_ID = "5068af34a4ce"
SUMMARY = (
    "30x30 zero-background grid with 5-7 separated hollow rectangles, all "
    "drawn in color 3.  Rectangles are arranged as a horizontal or vertical "
    "chain with small gaps and a shared perpendicular band, matching the "
    "canonical task's large fixed canvas and hollow color-3 object style. "
    "Rule: connect rectangles along the minimum-gap spanning tree by drawing "
    "color-3 corridors and punching doorways through facing rectangle walls."
)

INVARIANTS = [
    "the grid is the canonical 30x30 canvas",
    "the background is zero and every object pixel is color 3",
    "objects are separated hollow rectangles, not solid rectangles",
    "the rectangles form an aligned chain with >=1 cell gaps",
]

ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_rects", "single_rect", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "30", "valid": "30"},
    "grid_w":         {"type": "int", "default": "30", "valid": "30"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "horizontal|vertical"},
    "n_rects":        {"type": "int", "default": "rng 5..7", "valid": "2..7"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "aligned_chain", "valid": "aligned_chain"},
    "color":          {"type": "color", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "horizontal|vertical|no_rects|single_rect|full_grid"},
}


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _component_bboxes(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = [[False] * w for _ in range(h)]
    boxes = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            boxes.append((color, min(rs), min(cs), max(rs), max(cs), set(cells)))
    return boxes


def _is_hollow_rect_component(grid, box) -> bool:
    color, r0, c0, r1, c1, cells = box
    if color != 3 or r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return False
    expected = set()
    for c in range(c0, c1 + 1):
        expected.add((r0, c)); expected.add((r1, c))
    for r in range(r0, r1 + 1):
        expected.add((r, c0)); expected.add((r, c1))
    return cells == expected


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the canonical-style 30x30 field of separated hollow color-3 rectangles."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if (h, w) != (30, 30):
        errs.append(f"expected canonical 30x30 canvas, got {h}x{w}")
    colors = {v for row in grid for v in row}
    if not colors <= {0, 3}:
        errs.append(f"expected only colors 0 and 3, got {sorted(colors)}")
    boxes = _component_bboxes(grid)
    if len(boxes) < 2:
        errs.append(f"expected >=2 hollow rectangles, found {len(boxes)}")
    if len(boxes) > 7:
        errs.append(f"expected <=7 hollow rectangles, found {len(boxes)}")
    bad = [box for box in boxes if not _is_hollow_rect_component(grid, box)]
    if bad:
        errs.append(f"expected separated hollow rectangles; malformed components={len(bad)}")
    return errs

def _draw_hollow_rect(g, r, c, h, w, color=3):
    for cc in range(c, c + w):
        g[r][cc] = color
        g[r + h - 1][cc] = color
    for rr in range(r, r + h):
        g[rr][c] = color
        g[rr][c + w - 1] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS
                   else None) or overrides.get("orientation") or \
        rng.choice(list(ORIENTATIONS))

    # Canonical examples are fixed 30x30 fields of hollow color-3 rectangles.
    # Keep the intentionally simple aligned-chain teaching distribution, but
    # restore the fixed canvas, hollow objects, color, and object count.
    g = full_grid(30, 30, 0)
    if difficulty == "easy":
        n = 5
        rect_h_r = (4, 6)
    elif difficulty == "hard":
        n = 6
        rect_h_r = (5, 8)
    else:
        n = rng.randint(5, 6)
        rect_h_r = (4, 7)
    rect_w_r = (3, 4) if n >= 6 else (3, 5)
    gap_r = (1, 1) if n >= 6 else (1, 2)

    for _attempt in range(200):
        heights = [rng.randint(*rect_h_r) for _ in range(n)]
        widths = [rng.randint(*rect_w_r) for _ in range(n)]
        gaps = [rng.randint(*gap_r) for _ in range(n - 1)]
        span_w = sum(widths) + sum(gaps)
        max_h = max(heights)
        if span_w <= 28 and max_h <= 28:
            left = rng.randint(0, 30 - span_w)
            top = rng.randint(0, 30 - max_h)
            cur = left
            for hh, ww, gap in zip(heights, widths, gaps + [0]):
                # Align vertical centers so adjacent rectangles share a band,
                # but vary heights like the canonical examples.
                rr = top + (max_h - hh) // 2
                _draw_hollow_rect(g, rr, cur, hh, ww, 3)
                cur += ww + gap
            if orientation == "vertical":
                g = _transpose(g)
            return g
    raise ValueError("could not fit hollow rectangle chain on 30x30 canvas")

def _draw_from_degenerate(name, rng):
    g = full_grid(30, 30, 0)
    if name == "no_rects":
        return g
    if name == "single_rect":
        _draw_hollow_rect(g, 10, 10, 6, 6, 3)
        return g
    if name == "full_grid":
        for r in range(30):
            for c in range(30):
                g[r][c] = 3
        return g
    return g
