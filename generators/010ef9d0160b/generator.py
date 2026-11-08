"""Generator for arc_puzzle_bank_nineteenth21:M131 (task 010ef9d0160b).

THE RULE (what a solver must learn to see):
  For each connected non-bg shape, draw the OUTLINE of its bounding
  box in the shape's color — on a FRESH canvas. The bbox interior is
  left empty, and the shape's own interior cells vanish.

  (The old docstring claimed "fill the bbox to a solid rectangle".
  That is wrong: the rule paints only the bbox border. Every shape in
  the old library had a bbox of 2x2/2x3/3x2, where frame == solid, so
  the training data could never distinguish outline from fill, and the
  vanishing-interior behavior was unreachable.)

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - >=1 shape per board has a bbox of at least 3x3 WITH an occupied
    interior cell: the output visibly hollows it (outline only) and
    the interior cell disappears — 'solid fill' is refuted in-data
  - small 2x2-bbox shapes mixed in (frame == solid there)
  - 1-3 shapes, distinct colors, bbox-separated; grown polyominoes

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_shapes    blank in, blank out
  - solid_2x2    a 2x2 solid block: frame == solid, looks like identity
  - single_cell  1x1 bboxes: outline is the cell itself
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "010ef9d0160b"
VERSION = "3.1.0"  # v3.1.0: add executable self_check for bbox-outline teaching examples.
TASK_ID = "010ef9d0160b"
SUMMARY = (
    "0-bg grid with 1-3 grown polyominoes (distinct colors, bbox-"
    "separated), at least one having a bbox >= 3x3 with an occupied "
    "interior cell; rule draws each shape's bbox OUTLINE in its color "
    "on a fresh canvas (interiors empty — not a solid fill)."
)

# Rivals: 'fill the bbox solid' refuted by >=3x3 demos whose interiors
# stay empty. 'keep the original cells' refuted by interior cells that
# vanish. 'one global bbox' refuted by multi-shape demos. 'recolor'
# refuted by color preservation. 3 demos incl. >=1 big-bbox shape.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-3 connected shapes in distinct non-bg colors, bboxes separated",
    ">=1 shape has bbox >= 3x3 with an occupied interior cell (helpful path)",
    "outputs are bbox outlines, never solid fills, on a fresh canvas",
]

DEGENERATE_TEXTURES = ("no_shapes", "solid_2x2", "single_cell")
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "grid_h":  {"type": "int", "default": "rng 6..9 (easy 5..7, hard 9..12)",
                "valid": "5..14", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 8..12 (easy 7..9, hard 12..16)",
                "valid": "6..16", "doc": "Grid width."},
    "n_objs":  {"type": "int", "default": "rng 1..2 (hard 2..3)",
                "valid": "1..3", "doc": "Shape count."},
    "texture": {"type": "str", "default": "plain",
                "valid": "plain|no_shapes|solid_2x2|single_cell",
                "doc": "Set to a degenerate name to build a rule-hiding input."},
}


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _has_interior_cell(cells):
    """True if some cell sits strictly inside the bbox."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    if r2 - r1 < 2 or c2 - c1 < 2:
        return False
    return any(r1 < r < r2 and c1 < c < c2 for r, c in cells)


def _big_shape(rng):
    """Polyomino with bbox >= 3x3 and an occupied interior cell."""
    for _ in range(60):
        cells = _grow(rng, rng.randint(6, 9))
        if _has_interior_cell(cells):
            return cells
    # plus-pentomino fallback: center is interior by construction
    return [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]


def _place(g, rng, cells, color, placed):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _ in range(80):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
        if any(not (bb[2] < p[0] or p[2] < bb[0] or bb[3] < p[1] or p[3] < bb[1])
               for p in placed):
            continue
        for r, c in cells:
            g[r0 + r][c0 + c] = color
        placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
        n = ctx.draw_int("n_objs", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_objs", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 12)
        n = ctx.draw_int("n_objs", 1, 2)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        placed = []
        palette = list(random_palette(rng, n))
        ok = True
        for i, color in enumerate(palette):
            # first shape: big bbox + occupied interior — the texture
            # that separates outline from solid fill; easy boards may
            # not fit one, so fall back to a small shape there
            cells = _big_shape(rng) if i == 0 else _grow(rng, rng.randint(3, 5))
            if not _place(g, rng, cells, color, placed):
                if i == 0 and h >= 5 and w >= 5:
                    ok = False
                break
        if ok and placed:
            return g
    # tiny-board fallback: one small hollow shape
    g = full_grid(h, w, 0)
    _place(g, rng, [(0, 0), (0, 1), (1, 0)], 4, [])
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_shapes   — blank: nothing to outline.
    solid_2x2   — frame == solid at 2x2: output equals input.
    single_cell — 1x1 bboxes: the outline IS the cell.
    """
    h = ctx.draw_int("grid_h", 6, 9)
    w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_shapes":
        return g
    palette = list(random_palette(rng, 3))
    if name == "solid_2x2":
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        for dr in range(2):
            for dc in range(2):
                g[r0 + dr][c0 + dc] = palette[0]
        return g
    # single_cell: scattered isolated singles
    placed = 0
    for _ in range(40):
        if placed >= rng.randint(2, 4):
            break
        r, c = rng.randrange(h), rng.randrange(w)
        if all(g[rr][cc] == 0
               for rr in range(max(0, r - 1), min(h, r + 2))
               for cc in range(max(0, c - 1), min(w, c + 2))):
            g[r][c] = palette[placed % len(palette)]
            placed += 1
    return g


def _components_same_color_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate bbox-outline teaching inputs with at least one interior cell."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    comps = _components_same_color_for_self_check(grid)
    expected = (2, 3) if difficulty == "hard" else ((1, 1) if difficulty == "easy" else (1, 2))
    if not (expected[0] <= len(comps) <= expected[1]):
        errs.append(f"expected {expected[0]}-{expected[1]} components, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("component colors must be distinct")
    big = False
    for _, cells in comps:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 - r1 >= 2 and c2 - c1 >= 2 and any(r1 < r < r2 and c1 < c < c2 for r, c in cells):
            big = True
    if not big:
        errs.append("at least one component must have a >=3x3 bbox with an occupied interior cell")
    return errs
