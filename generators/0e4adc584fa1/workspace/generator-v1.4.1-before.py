"""Generator for 11b:m73 — rotate source by control color.

Rule: cells with no 4-neighbor are 'isolated'; the LAST isolated
(scan-order) provides a transform code via its color. The main shape
(all other non-bg cells) is cropped to its bbox and transformed.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_control (no isolated single-cell marker → rule's
control selector returns nothing, transform undefined), no_shape
(control marker present but no multi-cell shape → rule has nothing
to transform), identity_control (control color = identity-equivalent
code → rule's transform produces no change).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0e4adc584fa1"
VERSION = "1.4.1"  # force D4-distinct main shape; strengthen self_check
TASK_ID = "0e4adc584fa1"

SUMMARY = (
    "0-bg grid with: (a) one multi-cell connected shape in some color "
    "(asymmetric); (b) one isolated single-cell marker (no 4-neighbor) "
    "in color from {1, 2, 3, 4} — encoding a transform code. Rule: "
    "find isolated cells with color in {1..4} — pick the LAST one in "
    "scan order. Use its color as the transform code (1=identity, "
    "2=rot-cw, 3=rot-180, 4=rot-ccw). Crop the shape to its bbox and "
    "apply the transform. Output is the transformed crop."
)

# Rivals: 'output is input' refuted. 'identity always' refuted by
# demos with codes 2-4. 'use shape color as code' refuted by demos
# showing marker's color = code. 'output is the marker only' refuted.
# 4 demos covering all 4 codes pin the transform table.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one isolated single-cell control marker (no 4-neighbor), color in {1, 2, 3, 4}",
    "exactly one multi-cell shape elsewhere; not 4-touching the marker",
    "shape is asymmetric (so rotations produce visibly different outputs)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_control", "no_shape", "identity_control")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":     {"type": "str", "default": "shape_plus_control_marker",
                          "valid": "shape_plus_control_marker"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_ASYM_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
]


def _norm_cells(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _d4_distinct(cells):
    cells = set(_norm_cells(cells))
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    variants = [
        cells,
        {(c, h - 1 - r) for r, c in cells},
        {(h - 1 - r, w - 1 - c) for r, c in cells},
        {(w - 1 - c, r) for r, c in cells},
    ]
    return len({_norm_cells(v) for v in variants}) == 4


def _rand_poly(rng, size):
    """Random connected polyomino of `size` cells, normalized."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify exactly one isolated code marker and one D4-distinct shape."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    seen = set()
    isolated_codes = []
    shapes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                if len(comp) == 1 and grid[comp[0][0]][comp[0][1]] in (1, 2, 3, 4):
                    isolated_codes.append(comp[0])
                elif len(comp) > 1:
                    shapes.append(comp)
                else:
                    errs.append("isolated non-code cell would confuse the control selector")
    if len(isolated_codes) != 1:
        errs.append(f"expected exactly one isolated control marker, found {len(isolated_codes)}")
    if len(shapes) != 1:
        errs.append(f"expected exactly one multi-cell shape, found {len(shapes)}")
    elif not _d4_distinct(shapes[0]):
        errs.append("main shape has duplicate rotation outputs; control code is ambiguous")
    return errs


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
        h = ctx.draw_int("grid_h", 10, 10)
        w = ctx.draw_int("grid_w", 11, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Shape colors: from {5..9} (never {1,2,3,4} so they aren't read as
    # the control code). The shape may use 1 or 2 colors (canonical
    # shapes are multi-colored).
    n_shape_colors = rng.randint(1, 2)
    shape_colors = rng.sample([5, 6, 7, 8, 9], n_shape_colors)
    # Control color = the transform code itself (must be in {1, 2, 3, 4}).
    control_code = rng.randint(1, 4)
    # Random polyomino, sized to fit the grid with room for a marker.
    max_dim = max(2, min(h - 2, w - 2, 5))
    for _shape_try in range(80):
        shape = rng.choice(_ASYM_SHAPES) if rng.random() < 0.2 else \
            _rand_poly(rng, rng.randint(3, max(3, min(7, max_dim + 2))))
        if _d4_distinct(shape):
            break
    else:
        shape = _ASYM_SHAPES[0]
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh >= h or sw >= w:
        shape = rng.choice(_ASYM_SHAPES)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
    placed = False
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = rng.choice(shape_colors)
        placed = True; break
    if not placed:
        raise ValueError("could not place main shape")
    for _ in range(60):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0 or _too_close(g, r, c):
            continue
        g[r][c] = control_code
        return g
    raise ValueError("could not place isolated control marker")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_control":
        # No isolated single-cell — rule's control selector finds nothing.
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
            g[2 + dr][2 + dc] = 4
        return g
    if name == "no_shape":
        # Control marker present but no multi-cell shape — rule has
        # nothing to transform.
        g[5][5] = 3
        return g
    if name == "identity_control":
        # Control marker color encodes identity transform — output =
        # cropped input with no transformation.
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
            g[2 + dr][2 + dc] = 4
        g[7][7] = 1   # identity-equivalent code
        return g
    return g
