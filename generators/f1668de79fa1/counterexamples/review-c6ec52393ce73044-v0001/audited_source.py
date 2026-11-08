"""Generator for arc_puzzle_bank_21_set15:S15_E3.

Rule: a color-2 template is horizontally mirrored and stamped at a
single color-1 marker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template (no color-2 shape → rule has no source);
no_marker (template present but no color-1 → rule has no
destination); lr_symmetric_template (template invariant under
hmirror → mirrored stamp identical to original, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f1668de79fa1"
VERSION = "1.4.0"  # random LR-asymmetric polyominoes + bigger grids (was 12 curated shapes, 8-13 grid)
TASK_ID = "f1668de79fa1"
SUMMARY = (
    "0-bg grid with one connected color-2 template (3-6 cells, "
    "asymmetric under horizontal mirror) and exactly one color-1 "
    "marker cell. Rule: compute the template's cell offsets relative "
    "to its bbox top-left, apply HORIZONTAL MIRROR (flip-lr) to those "
    "offsets, then on a FRESH 0-grid paint color 8 at every "
    "(marker_r + dr, marker_c + dc) for transformed offset (dr, dc). "
    "Cells outside the grid are silently dropped. Output is a fresh "
    "grid containing only the mirrored stamp; original template and "
    "marker do NOT appear in the output."
)

# Rivals: 'output is input' refuted by demos (output has only 8s).
# 'identity stamp (no mirror)' refuted by demos with an LR-asymmetric
# template — the mirrored shape is visibly distinct from the original.
# 'rotation instead of mirror' refuted by demos where the stamp is
# specifically the LR mirror (different from rot-cw/ccw). 'flip-ud
# instead of flip-lr' refuted by demos. 'preserve template color (2)'
# refuted by demos showing stamp is 8. 'stamp at template position,
# not marker' refuted by demos with marker far from template.
# 4 demos with varied asymmetric shapes pin flip-lr.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one connected color-2 template (3-6 cells)",
    "template is NOT LR-symmetric (so flip-lr is distinguishable from identity)",
    "template is NOT UD-symmetric (so flip-lr is distinguishable from flip-ud)",
    "exactly one color-1 marker cell, NOT overlapping the template",
    "the mirrored stamp has ≥1 cell that lands in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_marker", "lr_symmetric_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":            {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "template_with_marker",
                          "valid": "template_with_marker"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],                       # L-tetromino
    [(0, 0), (0, 1), (1, 1), (2, 1)],                       # mirrored L
    [(0, 0), (1, 0), (1, 1), (1, 2)],                       # T-rotated
    [(0, 1), (1, 1), (2, 0), (2, 1)],                       # J-tetromino
    [(0, 0), (1, 0), (1, 1), (2, 1)],                       # S-tetromino
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],               # P-5 left
    [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],               # zigzag-5
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],               # corner-5
    [(0, 0), (0, 1), (0, 2), (1, 0)],                       # J-tetromino flat
    [(0, 0), (0, 1), (0, 2), (1, 2)],                       # L-tetromino flat
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],               # L-5 tall
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],               # T-down-tall
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rand_asym(rng, k):
    """A random connected polyomino of k cells that is LR-asymmetric (its
    horizontal mirror differs from itself), so the flip-lr stamp is visible."""
    for _ in range(40):
        cells = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        if _hmirror(norm) != norm and _vmirror(norm) != norm:
            return norm
    candidates = [shape for shape in _SHAPES if _hmirror(shape) != shape and _vmirror(shape) != shape]
    return rng.choice(candidates)


def _hmirror(shape):
    _, sw = _size(shape)
    return sorted((r, sw - 1 - c) for r, c in shape)


def _vmirror(shape):
    sh, _ = _size(shape)
    return sorted((sh - 1 - r, c) for r, c in shape)


def _components_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen and grid[ny][nx] == color:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            comps.append(comp)
    return comps


def _normalize_abs(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(markers) != 1:
        errors.append(f"expected exactly one color-1 marker, found {len(markers)}")
    comps = _components_color(grid, 2)
    if len(comps) != 1:
        errors.append(f"expected exactly one connected color-2 template, found {len(comps)}")
        return errors
    template = _normalize_abs(comps[0])
    if not (3 <= len(template) <= 7):
        errors.append(f"template size should be 3..7, found {len(template)}")
    if _hmirror(template) == template:
        errors.append("template is LR-symmetric; mirrored stamp may look like identity")
    if _vmirror(template) == template:
        errors.append("template is UD-symmetric; flip-lr and flip-ud are ambiguous")
    if markers:
        mr, mc = markers[0]
        for dr, dc in _hmirror(template):
            if not (0 <= mr + dr < h and 0 <= mc + dc < w):
                errors.append("mirrored stamp would land out of bounds")
                break
    return errors


def _free_box(g, r0, c0, sh, sw, pad=1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _paint(g, r0, c0, shape, color):
    for dr, dc in shape:
        g[r0 + dr][c0 + dc] = color


def _place_shape(g, rng, shape, color):
    sh, sw = _size(shape)
    h, w = len(g), len(g[0])
    for _ in range(80):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free_box(g, r0, c0, sh, sw):
            _paint(g, r0, c0, shape, color)
            return
    raise ValueError("could not place template")


def _place_marker(g, rng, stamp_shape):
    sh, sw = _size(stamp_shape)
    h, w = len(g), len(g[0])
    for _ in range(120):
        r = rng.randint(0, h - sh)
        c = rng.randint(0, w - sw)
        if g[r][c] == 0 and _free_box(g, r, c, 1, 1):
            g[r][c] = 1
            return
    raise ValueError("could not place marker")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 8, 10)
        w = ctx.draw_int("width", 10, 12)
        ksz = (4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 11, 15)
        w = ctx.draw_int("width", 13, 18)
        ksz = (4, 7)
    else:
        h = ctx.draw_int("height", 9, 12)
        w = ctx.draw_int("width", 11, 14)
        ksz = (4, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shape = _rand_asym(rng, rng.randint(*ksz))
    _place_shape(g, rng, shape, 2)
    _place_marker(g, rng, _hmirror(shape))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-2 template — rule has no source.
        g[5][5] = 1
        return g
    if name == "no_marker":
        # Template present but no color-1 marker — no destination.
        for dr, dc in [(0, 0), (1, 0), (2, 0), (2, 1)]:
            g[1 + dr][1 + dc] = 2
        return g
    if name == "lr_symmetric_template":
        # T-shape symmetric under h-mirror — mirrored stamp identical.
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1)]:
            g[1 + dr][1 + dc] = 2
        g[5][7] = 1
        return g
    return g
