"""Generator for arc_puzzle_bank_nineteenth21:M130 — stamp the template at every 1-anchor.

Rule: remove color 1; the largest connected non-zero, non-1 component is the
TEMPLATE. Every color-1 cell is an ANCHOR. Output stamps the template at each
anchor on a blank grid, with the anchor as the template's top-left corner.

This default generator is deliberately kept close to the canonical examples:
5 rows by 7/8 columns, one 3-cell L-template, and exactly two anchors.
Degenerates remain caller-opt-in.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5ccc2b4c650"
VERSION = "2.1.0"  # restore canonical 5x7/8, 3-cell L-template default distribution
TASK_ID = "f5ccc2b4c650"
SUMMARY = (
    "Canonical M130-style grid: 5 rows by 7 or 8 columns, one 3-cell "
    "non-1 L-template, and two color-1 anchors. Rule: take the largest "
    "non-1 component as the template and stamp it at each anchor on a blank "
    "grid. The generator keeps default samples close to the original train "
    "distribution instead of emitting large free-form motif galleries."
)

INVARIANTS = [
    "background is 0; anchors are color 1",
    "exactly one connected non-1 component (the template), colored from non-1 colors",
    "exactly two color-1 anchor cells, off the template",
    "output stamps the template at each anchor (top-left), OOB clipped",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_anchors", "anchor_oob")
HELPFUL_TEXTURES = PALETTE_KINDS
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NON1 = (2, 3, 4, 5, 6, 7, 8, 9)

AXES = {
    "grid_h":   {"type": "int", "default": "fixed 5", "valid": "5"},
    "grid_w":   {"type": "int", "default": "rng 7..8", "valid": "7..8"},
    "tpl_cells":{"type": "int", "default": "fixed 3-cell L", "valid": "3"},
    "tpl_colors":{"type": "int", "default": "one canonical non-1 color", "valid": "1"},
    "n_anchors":{"type": "int", "default": "fixed 2", "valid": "2"},
    "n_distinct_colors": {"type": "int", "default": "template color + 1", "valid": "2"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "default|warm|cool|varied|no_template|no_anchors|anchor_oob"},
}


def _poly(rng, n):
    cells = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(tuple(cells)); dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _non1_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (0, 1) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, 1) and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable input invariants for the canonical template-at-anchor task."""
    errors: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != 5 or w not in (7, 8):
        errors.append(f"expected canonical 5×7/8 grid, got {h}×{w}")
    flat = [v for row in grid for v in row]
    bad = sorted({v for v in flat if not isinstance(v, int) or v < 0 or v > 9})
    if bad:
        errors.append(f"out-of-palette values: {bad[:5]}")
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(anchors) != 2:
        errors.append(f"expected exactly two color-1 anchors, found {len(anchors)}")
    comps = _non1_components(grid)
    if len(comps) != 1:
        errors.append(f"expected exactly one connected non-1 template component, found {len(comps)}")
    else:
        comp = comps[0]
        if len(comp) != 3:
            errors.append(f"template size {len(comp)} outside canonical 3-cell L")
        rr = {r for r, _ in comp}; cc = {c for _, c in comp}
        if len(rr) != 2 or len(cc) != 2:
            errors.append("template is not a 2×2 L-triomino footprint")
        colors = {grid[r][c] for r, c in comp}
        if 1 in colors or 0 in colors:
            errors.append("template component contains bg/anchor color")
        if not colors <= set(_NON1):
            errors.append("template uses colors outside the non-1 palette")
    return errors


def _canonical_l(orientation):
    shapes = [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 1), (1, 0), (1, 1)],
    ]
    return shapes[orientation % len(shapes)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    h = int(overrides.get("grid_h", 5))
    w = int(overrides.get("grid_w", rng.choice([7, 8])))
    if h != 5 or w not in (7, 8):
        raise ValueError("f5ccc2b4c650 default family is canonical 5×7/8")
    g = full_grid(h, w, 0)
    color = int(overrides.get("tpl_color", rng.choice([4, 6])))
    tpl = _canonical_l(rng.randrange(4))
    sh = max(r for r, _ in tpl) + 1
    sw = max(c for _, c in tpl) + 1

    # Keep the template in the left half, matching canonical examples and
    # leaving the right half available for anchor-triggered copies.
    tr0 = rng.randint(0, h - sh)
    tc0 = rng.randint(0, max(0, min(3, w - sw)))
    tpl_cells = set()
    for dr, dc in tpl:
        g[tr0 + dr][tc0 + dc] = color
        tpl_cells.add((tr0 + dr, tc0 + dc))

    preferred = [(1, 4), (1, 5), (2, w - 2), (2, w - 1), (3, 5)]
    free = [(r, c) for r, c in preferred if 0 <= r < h and 0 <= c < w and (r, c) not in tpl_cells]
    free += [(r, c) for r in range(h) for c in range(w)
             if (r, c) not in tpl_cells and g[r][c] == 0 and (r, c) not in free]
    rng.shuffle(free)
    if len(free) < 2:
        raise ValueError("not enough room for two anchors")
    for r, c in free[:2]:
        g[r][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_template":
        g[2][5] = 1; g[4][7] = 1
        return g
    if name == "no_anchors":
        for r, c in [(1, 1), (1, 2), (2, 1)]:
            g[r][c] = 4
        return g
    if name == "anchor_oob":
        for r, c in [(1, 1), (1, 2), (2, 1)]:
            g[r][c] = 4
        g[4][w - 1] = 1
        return g
    return g
