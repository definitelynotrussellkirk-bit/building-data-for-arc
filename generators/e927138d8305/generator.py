"""Generator for arc_additional_puzzles_21_set8:M56.

Rule: locate the solid rectangle and the non-rectangular shape; output
the cropped shape recolored using the rectangle's color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "e927138d8305"
VERSION = "3.2.0"  # output = recoloured shape crop -> scale shape size by difficulty (4-10 cells) for bigger/more-varied output bboxes (was fixed 4-6)
# (3.0.0 was the rewrite from a 4-disconnected hardcoded "shape" that left the rule's non-rect list empty -> [[0]].)
TASK_ID = "e927138d8305"
SUMMARY = (
    "0-bg grid (h~9-12, w~10-14) with: (a) a SOLID RECTANGLE (random "
    "2x2..3x4) in rect_color; (b) a CONNECTED NON-RECTANGULAR polyomino "
    "(random, 4-6 cells, does not fill its bbox) in shape_color, "
    "separated from the rect. Rule: locate the solid-rectangle component "
    "and the non-rectangular component, crop the shape to its bbox, "
    "recolor its cells with the rect's color, output that crop. Varied "
    "shape forms + rect colours make the recolored crop differ per sample."
)

INVARIANTS = [
    "exactly one solid rectangle and one connected non-rectangular shape",
    "the non-rectangular shape is 4-connected (one component) and separated from the rect",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("no_rect", "no_shape", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|rainbow"},
    "num_rects":      {"type": "int", "default": "1", "valid": "1"},
    "num_shapes":     {"type": "int", "default": "1", "valid": "1"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|rainbow|no_rect|no_shape|all_same_color"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NONBG = [1, 2, 3, 4, 5, 6, 7, 8, 9]


def _poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _non_rect_poly(rng, n):
    """A connected n-cell polyomino that does NOT fill its bbox (not a rect)."""
    for _ in range(30):
        cells = _poly(rng, n)
        bh = max(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) + 1
        if len(cells) < bh * bw:          # has a gap in bbox -> not a solid rect
            return cells
    return [(0, 0), (0, 1), (1, 0)]       # L-tromino fallback (non-rect)


def _place(g, cells, color, rng, occ):
    h, w = len(g), len(g[0])
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    if bh > h or bw > w:
        return False
    for _ in range(150):
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        ac = [(r0 + r, c0 + c) for r, c in cells]
        if any((r + dr, c + dc) in occ
               for r, c in ac for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for r, c in ac:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occ.add((r + dr, c + dc))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 10, 12)
        sz_lo, sz_hi = 4, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 13, 18)
        sz_lo, sz_hi = 6, 10
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 11, 15)
        sz_lo, sz_hi = 4, 7
    shape_size = ctx.draw_int("shape_size", sz_lo, sz_hi)

    # Placement failure used to be silently ignored, yielding one-component
    # examples where the canonical rule has no template to crop.  Retry the
    # whole scene with a new keyed RNG and fail loudly if the invariant cannot
    # be satisfied.
    last = None
    for attempt in range(64):
        rng = ctx.draw_rng("layout" if attempt == 0 else f"layout_retry_{attempt}")
        rect_color, shape_color = rng.sample(_NONBG, 2)

        # Solid rectangle (varied size) as a flat list of cells.
        rh = rng.randint(2, 3); rw = rng.randint(2, 4)
        rect = [(r, c) for r in range(rh) for c in range(rw)]
        # Connected, non-rectangular shape (so it is the unique non-rect component);
        # size scales with difficulty so the recoloured output crop varies more.
        shape = _non_rect_poly(rng, shape_size)

        g = full_grid(h, w, 0)
        occ = set()
        if not _place(g, rect, rect_color, rng, occ):
            last = g
            continue
        if not _place(g, shape, shape_color, rng, occ):
            last = g
            continue
        last = g
        if not self_check(g, difficulty=difficulty):
            return g
    raise ValueError(f"could not place separated rectangle+template scene; last={self_check(last)}")


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_solid_rect(cells):
    r0, c0, r1, c1 = _bbox(cells)
    return len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)


def _touch_or_diagonal(a, b):
    return any(max(abs(r - rr), abs(c - cc)) <= 1 for r, c in a for rr, cc in b)


def self_check(grid, *, difficulty=None, meta=None):
    """Executable normal-path invariants for colorized template transfer."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    components = _components(grid)
    rects = [cells for cells in components if _is_solid_rect(cells)]
    shapes = [cells for cells in components if not _is_solid_rect(cells)]
    if len(components) != 2:
        errors.append("normal sample must contain exactly two nonzero components")
    if len(rects) != 1:
        errors.append("normal sample must contain exactly one solid rectangle")
    if len(shapes) != 1:
        errors.append("normal sample must contain exactly one non-rectangular template")
    if len(rects) == 1 and len(shapes) == 1:
        rect_colors = {grid[r][c] for r, c in rects[0]}
        shape_colors = {grid[r][c] for r, c in shapes[0]}
        if len(rect_colors) != 1:
            errors.append("rectangle must be solid-color")
        if len(shape_colors) != 1:
            errors.append("template must be single-color")
        if rect_colors == shape_colors:
            errors.append("rectangle color must differ from template color")
        if _touch_or_diagonal(rects[0], shapes[0]):
            errors.append("rectangle and template must have a one-cell moat")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_rect":
        # only the non-rectangular shape — no source color to recolor with
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 1)]:
            g[h - 4 + dr][w - 5 + dc] = 5
        return g
    if name == "no_shape":
        # only a rectangle — nothing to recolor
        draw_rect(g, 1, 1, 2, 3, 4)
        return g
    if name == "all_same_color":
        # rect and shape share a color — recoloring is a no-op
        draw_rect(g, 1, 1, 2, 3, 5)
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 1)]:
            g[h - 4 + dr][w - 5 + dc] = 5
        return g
    return g
