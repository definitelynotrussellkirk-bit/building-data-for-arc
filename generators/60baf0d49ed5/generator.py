"""Generator for 60baf0d49ed5: infer A->B transform, apply to C.

The grid contains three square panels separated by full-height color-9 columns.
Panel B is a uniquely identifiable transform of panel A.  The output is the same
transform applied to panel C.

Version 3 repairs two retained defects from the source review:
* advertised palette/count controls now change the generated colors exactly;
* an episode's consecutive samples cycle through distinct transforms, while the
  query motif is asymmetric, so a fixed-transform shortcut cannot fit a lesson.
"""
from __future__ import annotations

import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "60baf0d49ed5"
VERSION = "3.0.0"
TASK_ID = GENERATOR_ID

SUMMARY = (
    "Three square panels separated by full-height color-9 columns. Panel B is "
    "a uniquely identifiable rotation/reflection of panel A; infer that operation "
    "and apply it to the asymmetric motif in panel C. Consecutive lesson samples "
    "cycle operations so a fixed-transform shortcut is visibly false."
)

INVARIANTS = [
    "background is 0; exactly three equal square panels use full-height color-9 dividers",
    "panel B is exactly one searched transform of panel A",
    "panels A and C are asymmetric under all searched transforms",
    "the requested 1..3 motif colors all occur and exclude 0 and divider color 9",
]

_OPS = ("rot90", "rot270", "rot180", "flip-h", "flip-v")
PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8),
    "warm": (1, 2, 4, 7),
    "cool": (3, 5, 6, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_side": {"type": "int", "default": "by difficulty", "valid": "3..8"},
    "transform": {"type": "enum", "default": "episode-cycle", "valid": "|".join(_OPS)},
    "palette_kind": {"type": "str", "default": "rng", "valid": "|".join(PALETTE_KINDS)},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "1..3"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _apply(grid, op):
    n = len(grid)
    if op == "rot90":
        return [[grid[n - 1 - j][i] for j in range(n)] for i in range(n)]
    if op == "rot270":
        return [[grid[j][n - 1 - i] for j in range(n)] for i in range(n)]
    if op == "rot180":
        return [[grid[n - 1 - i][n - 1 - j] for j in range(n)] for i in range(n)]
    if op == "flip-h":
        return [list(reversed(row)) for row in grid]
    if op == "flip-v":
        return [row[:] for row in reversed(grid)]
    raise ValueError(f"unknown transform: {op!r}")


def _all_images(grid):
    return [grid] + [_apply(grid, op) for op in _OPS]


def _connected_shape(rng, side, *, min_cells, max_cells):
    cells = {(rng.randrange(side), rng.randrange(side))}
    target = rng.randint(min_cells, max_cells)
    for _ in range(side * side * 40):
        if len(cells) >= target:
            break
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        nr, nc = r + dr, c + dc
        if 0 <= nr < side and 0 <= nc < side:
            cells.add((nr, nc))
    return sorted(cells)


def _paint_shape(rng, side, cells, colors):
    grid = [[0] * side for _ in range(side)]
    order = list(cells)
    rng.shuffle(order)
    for index, (r, c) in enumerate(order):
        color = colors[index] if index < len(colors) else rng.choice(colors)
        grid[r][c] = color
    return grid


def _fallback_panel(side, colors):
    grid = [[0] * side for _ in range(side)]
    cells = [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]
    if side >= 4:
        cells += [(3, 1), (3, 2)]
    for index, (r, c) in enumerate(cells):
        grid[r][c] = colors[index % len(colors)]
    return grid


def _rand_panel(rng, side, colors, *, dense=False):
    minimum = max(5, len(colors))
    maximum = min(side * side - 1, max(minimum, side * (3 if dense else 2)))
    for _ in range(300):
        cells = _connected_shape(rng, side, min_cells=minimum, max_cells=maximum)
        panel = _paint_shape(rng, side, cells, colors)
        if len({tuple(tuple(row) for row in image) for image in _all_images(panel)}) == 6:
            return panel
    panel = _fallback_panel(side, colors)
    if len({tuple(tuple(row) for row in image) for image in _all_images(panel)}) != 6:
        raise RuntimeError("failed to construct an asymmetric panel")
    return panel


def _scheduled_operation(seed, sample_index):
    payload = f"{TASK_ID}|{VERSION}|{seed}|operation-cycle".encode()
    offset = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % len(_OPS)
    return _OPS[(offset + int(sample_index)) % len(_OPS)]


def split_panels(grid):
    height = len(grid)
    width = len(grid[0]) if grid else 0
    dividers = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    if len(dividers) != 2:
        raise ValueError("expected exactly two full-height color-9 dividers")
    starts = (0, dividers[0] + 1, dividers[1] + 1)
    panels = [[row[start : start + height] for row in grid] for start in starts]
    if any(len(row) != height for panel in panels for row in panel):
        raise ValueError("dividers do not form three square panels")
    return panels


def infer_operation(grid):
    a, b, _ = split_panels(grid)
    matches = [op for op in _OPS if _apply(a, op) == b]
    if len(matches) != 1:
        raise ValueError(f"expected one transform mapping A to B, got {matches}")
    return matches[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES + DEGENERATE_TEXTURES))
        if texture in DEGENERATE_TEXTURES:
            return _draw_from_degenerate(texture, None)
        palette_kind = texture
    else:
        palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))

    if difficulty == "easy":
        side = ctx.draw_int_strict("panel_side", 3, 4)
    elif difficulty == "hard":
        side = ctx.draw_int_strict("panel_side", 6, 8)
    elif difficulty == "medium":
        side = ctx.draw_int_strict("panel_side", 4, 7)
    else:
        side = ctx.draw_int_strict("panel_side", 3, 6)

    if overrides.get("transform") is not None:
        operation = ctx.draw_choice("transform", list(_OPS))
    else:
        operation = _scheduled_operation(seed, sample_index)

    count = ctx.draw_int_strict("n_distinct_colors", 1, 3)
    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(list(PALETTES[palette_kind]), count)
    layout_rng = ctx.draw_rng("layout")

    a = _rand_panel(layout_rng, side, colors)
    b = _apply(a, operation)
    c = _rand_panel(layout_rng, side, colors)

    width = 3 * side + 2
    grid = full_grid(side, width, 0)
    for col in (side, 2 * side + 1):
        for r in range(side):
            grid[r][col] = 9
    for index, panel in enumerate((a, b, c)):
        left = index * (side + 1)
        for r in range(side):
            for col in range(side):
                grid[r][left + col] = panel[r][col]
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    try:
        panels = split_panels(grid)
    except ValueError as exc:
        return [str(exc)]
    for name, panel in zip(("A", "B", "C"), panels):
        if not any(cell not in (0, 9) for row in panel for cell in row):
            errors.append(f"panel {name} is empty")
    for name, panel in (("A", panels[0]), ("C", panels[2])):
        if len({tuple(tuple(row) for row in image) for image in _all_images(panel)}) != 6:
            errors.append(f"panel {name} is ambiguous under searched transforms")
    try:
        infer_operation(grid)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _draw_from_degenerate(name, rng):
    side = 4
    width = 3 * side + 2
    grid = full_grid(side, width, 0)
    if name == "no_dividers":
        grid[1][1] = 4
        grid[1][6] = 6
        grid[2][11] = 7
        return grid
    for col in (side, 2 * side + 1):
        for r in range(side):
            grid[r][col] = 9
    if name == "empty_panels":
        return grid
    if name == "single_panel":
        grid[0][0] = 4
        grid[1][1] = 4
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")
