"""Generator for the per-color layer-flip task ``89a9a629c544``.

For every non-background color, the selected Racket rule flips that color's
cells top-to-bottom inside its own bounding box.  Because the rule applies the
layers sequentially, a generated scene is valid only when one layer's flipped
mask cannot overwrite another layer before its turn.  Ordinary scenes are
therefore assembled inside disjoint transform-closed tiles.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "89a9a629c544"
VERSION = "1.2.0"
TASK_ID = "89a9a629c544"
SUMMARY = (
    "Multi-color grid; each non-background color layer is flipped vertically "
    "inside its own bounding box without cross-layer overwrite."
)

INVARIANTS = [
    "background is 0",
    "at least two non-background colors so the rule is informative",
    "at least one color layer is UD-asymmetric within its bounding box",
    "independently flipped color masks are disjoint and equal sequential Racket semantics",
]

COLOR_LAYOUTS = ("scattered", "blob_per_color", "stripes", "diagonal", "row_per_color")
DEGENERATE_TEXTURES = ("monochrome", "all_layers_ud_symmetric", "single_color")
HELPFUL_TEXTURES = COLOR_LAYOUTS

AXES = {
    "grid_h": {"type": "int", "default": "rng 5..14", "valid": "3..18"},
    "grid_w": {"type": "int", "default": "rng 5..14", "valid": "3..18"},
    "n_colors": {"type": "int", "default": "rng 2..5", "valid": "2..7"},
    "color_layout": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(COLOR_LAYOUTS),
    },
    "layer_density": {
        "type": "float",
        "default": "rng 0.15..0.4",
        "valid": "0.05..0.7",
    },
    "texture": {
        "type": "str",
        "default": "alias for color_layout",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _grid_colors(grid):
    seen = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.append(value)
    return seen


def _layer_mask(grid, color):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _flip_mask(mask, axis="ud"):
    if not mask:
        return set()
    rows = [r for r, _ in mask]
    cols = [c for _, c in mask]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    if axis == "ud":
        return {(r1 + r2 - r, c) for r, c in mask}
    if axis == "lr":
        return {(r, c1 + c2 - c) for r, c in mask}
    raise ValueError("axis must be 'ud' or 'lr'")


def _is_asymmetric(mask, axis="ud"):
    return bool(mask) and _flip_mask(mask, axis) != mask


def rule_mirror(grid, axis="ud"):
    """Exact sequential Python mirror used only for tests and validation."""
    result = deepcopy(grid)
    for color in _grid_colors(grid):
        current = _layer_mask(result, color)
        if not current:
            continue
        target = _flip_mask(current, axis)
        for r, row in enumerate(result):
            for c, value in enumerate(row):
                if value == color:
                    result[r][c] = 0
        for r, c in target:
            result[r][c] = color
    return result


def _independent_result(grid, axis="ud"):
    result = full_grid(len(grid), len(grid[0]), 0)
    occupied = set()
    for color in _grid_colors(grid):
        target = _flip_mask(_layer_mask(grid, color), axis)
        overlap = occupied & target
        if overlap:
            return None, overlap
        occupied |= target
        for r, c in target:
            result[r][c] = color
    return result, set()


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the actual semantic domain of the selected sequential rule."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty 2D list"]
    if any(not isinstance(row, list) for row in grid):
        return ["grid rows must be lists"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid integer color {value!r}")
    if errors:
        return errors

    colors = _grid_colors(grid)
    if len(colors) < 2:
        errors.append("need at least two non-background colors")
    masks = {color: _layer_mask(grid, color) for color in colors}
    if colors and not any(_is_asymmetric(mask, "ud") for mask in masks.values()):
        errors.append("need at least one UD-asymmetric color layer")

    expected, overlap = _independent_result(grid, "ud")
    if overlap:
        errors.append(
            "independent flipped layer collision at "
            + ", ".join(map(str, sorted(overlap)[:4]))
        )
    elif expected is not None:
        actual = rule_mirror(grid, "ud")
        if actual != expected:
            errors.append("sequential layer application differs from independent flips")
        before = Counter(value for row in grid for value in row if value)
        after = Counter(value for row in actual for value in row if value)
        if before != after:
            errors.append("sequential layer application does not preserve color counts")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 5, 7, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 11, 14, 4, 5
    elif difficulty in (None, "medium"):
        h_lo, h_hi, n_lo, n_hi = 5, 14, 2, 5
    else:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w, ctx, rng)
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")

    n = int(overrides.get("n_colors", ctx.draw_int("n_colors", n_lo, n_hi)))
    if not 2 <= n <= 7:
        raise ValueError("n_colors must be in 2..7")
    palette = list(ctx.draw_distinct_colors("palette", n=n, exclude={0}))
    layout = texture or overrides.get("color_layout") or ctx.draw_choice(
        "color_layout", list(COLOR_LAYOUTS)
    )
    if layout not in COLOR_LAYOUTS:
        raise ValueError(f"unknown color_layout {layout!r}")
    density = float(
        overrides.get("layer_density", ctx.draw_rng("layer_density").uniform(0.15, 0.4))
    )
    if not 0.05 <= density <= 0.7:
        raise ValueError("layer_density must be in 0.05..0.7")

    grid = _construct_safe_scene(h, w, palette, layout, density, rng)
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructive sampler violated its contract: " + "; ".join(errors))
    return grid


def _partition(length, parts):
    base, remainder = divmod(length, parts)
    sizes = [base + (1 if index < remainder else 0) for index in range(parts)]
    starts = []
    cursor = 0
    for size in sizes:
        starts.append((cursor, cursor + size))
        cursor += size
    return starts


def _tile_plan(h, w, count, layout):
    candidates = []
    for row_parts in range(1, min(h, count) + 1):
        col_parts = math.ceil(count / row_parts)
        if col_parts > w:
            continue
        rows = _partition(h, row_parts)
        cols = _partition(w, col_parts)
        tiles = [(r0, r1, c0, c1) for r0, r1 in rows for c0, c1 in cols]
        has_anchor = any(r1 - r0 >= 2 and c1 - c0 >= 2 for r0, r1, c0, c1 in tiles)
        if not has_anchor:
            continue
        waste = len(tiles) - count
        if layout in ("row_per_color", "stripes"):
            orientation_penalty = col_parts * 3 - row_parts
        elif layout == "diagonal":
            orientation_penalty = abs(row_parts - col_parts)
        else:
            orientation_penalty = abs((h / row_parts) - (w / col_parts))
        largest = max((r1 - r0) * (c1 - c0) for r0, r1, c0, c1 in tiles)
        candidates.append(((waste, orientation_penalty, -largest), tiles))
    if not candidates:
        return None
    tiles = min(candidates, key=lambda item: item[0])[1]
    if layout == "diagonal":
        tiles.sort(key=lambda tile: (tile[0] + tile[2], tile[0], tile[2]))
    elif layout in ("row_per_color", "stripes"):
        tiles.sort(key=lambda tile: (tile[0], tile[2]))
    return tiles[:count]


def _random_mask(tile, density, rng, *, force_asymmetric=False):
    r0, r1, c0, c1 = tile
    positions = [(r, c) for r in range(r0, r1) for c in range(c0, c1)]
    if force_asymmetric:
        if r1 - r0 < 2 or c1 - c0 < 2:
            raise ValueError("asymmetric anchor tile must be at least 2x2")
        for _ in range(64):
            br = rng.randint(r0 + 1, r1 - 1)
            bc = rng.randint(c0 + 1, c1 - 1)
            tr = rng.randint(r0, br - 1)
            lc = rng.randint(c0, bc - 1)
            corners = [(tr, lc), (tr, bc), (br, lc), (br, bc)]
            missing = rng.randrange(4)
            mask = {cell for index, cell in enumerate(corners) if index != missing}
            desired = max(3, min(len(positions) - 1, round(len(positions) * density)))
            extras = [cell for cell in positions if cell not in mask]
            rng.shuffle(extras)
            for cell in extras[: max(0, desired - len(mask))]:
                mask.add(cell)
            if _is_asymmetric(mask, "ud"):
                return mask
        raise RuntimeError("failed to construct an asymmetric anchor mask")

    desired = max(1, min(len(positions), round(len(positions) * density)))
    rng.shuffle(positions)
    return set(positions[:desired])


def _construct_safe_scene(h, w, palette, layout, density, rng):
    """Place each color in a disjoint tile closed under bbox reflections."""
    tiles = _tile_plan(h, w, len(palette), layout)
    if tiles is None:
        return _small_safe_scene(h, w, palette, rng)

    anchor_choices = [
        index
        for index, (r0, r1, c0, c1) in enumerate(tiles)
        if r1 - r0 >= 2 and c1 - c0 >= 2
    ]
    anchor_index = rng.choice(anchor_choices)
    if layout == "scattered":
        rng.shuffle(tiles)
        anchor_index = next(
            index
            for index, (r0, r1, c0, c1) in enumerate(tiles)
            if r1 - r0 >= 2 and c1 - c0 >= 2
        )

    grid = full_grid(h, w, 0)
    for index, (color, tile) in enumerate(zip(palette, tiles)):
        mask = _random_mask(tile, density, rng, force_asymmetric=index == anchor_index)
        for r, c in mask:
            grid[r][c] = color
    return grid


def _small_safe_scene(h, w, palette, rng):
    """Maximal lawful fallback for cramped explicit overrides.

    A 2x2 L occupies one transform-closed block.  Remaining colors use fixed
    points outside that block.  Extremely cramped requests may expose fewer
    palette entries because seven informative collision-free layers do not fit
    in every 3x3 grid.
    """
    if h < 2 or w < 2:
        raise ValueError("an informative layer flip needs at least a 2x2 grid")
    r0 = rng.randrange(h - 1)
    c0 = rng.randrange(w - 1)
    block = {(r0, c0), (r0 + 1, c0), (r0, c0 + 1), (r0 + 1, c0 + 1)}
    grid = full_grid(h, w, 0)
    missing = rng.choice(tuple(block))
    for r, c in block - {missing}:
        grid[r][c] = palette[0]
    free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in block]
    rng.shuffle(free)
    for color, (r, c) in zip(palette[1:], free):
        grid[r][c] = color
    return grid


def _draw_from_degenerate(name, h, w, ctx, rng):
    palette = list(ctx.draw_distinct_colors("palette", n=4, exclude={0}))
    grid = full_grid(h, w, 0)
    if name == "monochrome":
        color = palette[0]
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.4:
                    grid[r][c] = color
        grid[0][0] = color
        return grid
    if name == "all_layers_ud_symmetric":
        # Separate full rows are individually UD-symmetric in one-row bboxes.
        for index, color in enumerate(palette[: min(3, h)]):
            row = (2 * index) % h
            for c in range(w):
                if rng.random() < 0.55:
                    grid[row][c] = color
            grid[row][index % w] = color
        return grid
    if name == "single_color":
        color = palette[0]
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.3:
                    grid[r][c] = color
        grid[0][0] = color
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")
