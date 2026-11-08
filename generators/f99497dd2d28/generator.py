"""Generator for da2b0fe3.

Rule: take the mode non-bg color, crop to its bbox. If the crop is LR-symmetric
AND (not UD-symmetric OR the crop has odd height), draw a full HORIZONTAL middle
row of color 3 (at row floor((h-1)/2)); otherwise draw a full VERTICAL middle
column of color 3 (at col floor((w-1)/2)). The original shape is preserved.

v2.0.0 used a FIXED 10x10 grid (in_shapes = out_shapes = 1). The rule is fully
size-dynamic (it uses (rows g)/(cols g)), so v3.0.0 varies the grid size and
builds shapes that deterministically exercise BOTH branches:
 * LR-symmetric, ODD-height shapes  -> the ROW branch
 * asymmetric (non-LR) shapes        -> the COLUMN branch
A Python symmetry mirror guarantees each shape lands in its intended branch.

Combinatorial axes: grid size, shape color, branch (row vs col) + shape, position.
Degenerates: empty_grid, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f99497dd2d28"
VERSION = "3.1.0"  # vary grid size (was fixed 10x10, in_shapes=1) + deterministically hit row & col branches
TASK_ID = "f99497dd2d28"
SUMMARY = (
    "0-bg grid (size varies) with one SHAPE in a single non-zero color (not 3). "
    "Half the time the shape is LR-symmetric with ODD bbox height; half the time "
    "it is asymmetric. Rule: find the mode non-bg color, crop to its bbox; if the "
    "crop is LR-symmetric AND (not UD-symmetric OR odd height) draw a full "
    "HORIZONTAL middle row of color 3 across the grid, otherwise draw a full "
    "VERTICAL middle column of color 3. The shape is preserved. So LR-symmetric "
    "odd-height shapes yield a horizontal 3-line; asymmetric shapes yield a "
    "vertical 3-line; the line sits at the grid's middle (which moves with the "
    "grid size). (Was a fixed 10x10 grid -> a single in/out shape.)"
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one non-zero color present (the mode), >=5 cells, color != 3",
    "no color-3 cells in the input (the rule writes 3)",
    "the shape is either LR-symmetric with odd bbox height, or clearly asymmetric",
    "grid size varies so the middle row/column line position varies",
]

SHAPE_SIZE_KINDS = ("small", "medium", "large", "wide", "tall")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "single_cell")
HELPFUL_TEXTURES = SHAPE_SIZE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "8-11 easy / 11-15 med / 14-20 hard", "valid": "6..22"},
    "grid_w":            {"type": "int", "default": "8-11 easy / 11-15 med / 14-20 hard", "valid": "6..22"},
    "color":             {"type": "color", "default": "rng (!=0,3)", "valid": "1..9 (!=3)"},
    "branch":            {"type": "str", "default": "rng row|col", "valid": "row|col"},
    "shape_size_kind":   {"type": "str", "default": "rng helpful", "valid": "small|medium|large|wide|tall"},
    "position_bias":     {"type": "str", "default": "rng spread|center|edge", "valid": "spread|center|edge"},
    "palette_kind":      {"type": "str", "default": "rng helpful", "valid": "warm|cool|broad|small"},
    "texture":           {"type": "str", "default": "alias for shape_size_kind",
                          "valid": "small|medium|large|wide|tall|empty_grid|full_grid|single_cell"},
}

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _lr_sym(cells):
    w = max(c for _, c in cells) + 1
    s = set(cells)
    return all((r, w - 1 - c) in s for r, c in cells)


def _lr_shape(rng, ph, pw):
    """LR-symmetric shape with bbox exactly ph x pw (ph odd), >=5 cells."""
    cells = {(0, 0), (0, pw - 1), (ph - 1, 0), (ph - 1, pw - 1)}   # symmetric corners -> bbox + lr-sym
    half = (pw + 1) // 2
    for r in range(ph):
        for c in range(half):
            if rng.random() < 0.5:
                cells.add((r, c)); cells.add((r, pw - 1 - c))
    return sorted(cells)


def _asym_shape(rng, ph, pw):
    """Connected blob with bbox ph x pw that is NOT LR-symmetric."""
    for _ in range(40):
        cells = {(0, 0)}; frontier = [(0, 0)]
        while len(cells) < ph * pw and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in _CARD
                    if 0 <= cr + dr < ph and 0 <= cc + dc < pw and (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc)); continue
            if rng.random() < 0.55:
                nc = rng.choice(opts); cells.add(nc); frontier.append(nc)
            else:
                frontier.remove((cr, cc))
            if len(cells) >= max(6, ph * pw // 2):
                break
        # force full bbox extents
        cells |= {(0, 0), (ph - 1, pw - 1)}
        if max(r for r, _ in cells) + 1 == ph and max(c for _, c in cells) + 1 == pw \
                and len(cells) >= 5 and not _lr_sym(cells):
            return sorted(cells)
    # guaranteed-asymmetric fallback (an L)
    return [(0, 0), (1, 0), (2, 0), (2, 1)] if ph >= 3 and pw >= 2 else [(0, 0), (0, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], 10, 10, rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 11, 15)

    color = int(overrides.get("color", rng.choice([1, 2, 4, 5, 6, 7, 8, 9])))
    if color in (0, 3):
        color = rng.choice([1, 2, 4, 5, 6, 7, 8, 9])
    branch = overrides.get("branch", rng.choice(["row", "col"]))

    if branch == "row":
        ph = rng.choice([3, 5, 7]); pw = rng.randint(3, 7)
        shape = _lr_shape(rng, ph, min(pw, w - 1))
    else:
        ph = rng.randint(3, 7); pw = rng.randint(3, 7)
        shape = _asym_shape(rng, min(ph, h - 1), min(pw, w - 1))
    sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
    sh = min(sh, h); sw = min(sw, w)

    bias = overrides.get("position_bias", rng.choice(["spread", "center", "edge"]))
    if bias == "center":
        pr = max(0, (h - sh) // 2); pc = max(0, (w - sw) // 2)
    elif bias == "edge":
        pr = pc = 0
    else:
        pr = rng.randint(0, h - sh); pc = rng.randint(0, w - sw)

    g = full_grid(h, w, 0)
    for dr, dc in shape:
        if pr + dr < h and pc + dc < w:
            g[pr + dr][pc + dc] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the input has one non-3 shape that selects a row/column branch."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h = len(grid)
    errs = []
    if h > 22 or w > 22:
        errs.append(f"grid too large: {h}x{w}")
    colors = sorted({v for row in grid for v in row if v != 0})
    if 3 in colors:
        errs.append("input already contains color 3, which the rule is supposed to write")
    shape_colors = [c for c in colors if c != 3]
    if len(shape_colors) != 1:
        errs.append(f"expected exactly one nonzero shape color other than 3; got {shape_colors}")
        return errs
    color = shape_colors[0]
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
    if len(cells) < 5:
        errs.append(f"shape too small: expected >=5 cells, got {len(cells)}")
        return errs
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    norm = sorted((r - r0, c - c0) for r, c in cells)
    bbox_h = max(r for r, _ in norm) + 1
    if not (_lr_sym(norm) and bbox_h % 2 == 1) and _lr_sym(norm):
        errs.append("LR-symmetric shape should have odd bbox height to trigger the horizontal branch")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 4, 5, 6, 7, 8, 9])
    if name == "empty_grid":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_cell":
        g[h // 2][w // 2] = color
        return g
    return g
