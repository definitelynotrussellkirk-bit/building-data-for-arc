"""Generator for 33c1de6c4310 — copy a right-hand colour field through a left mask.

A full color-9 column separates two equal panels.  Every nonzero cell in the
left panel is a stencil position; the answer copies the value at the same
position from the right panel and writes 0 everywhere else.

The generator deliberately varies mask color, connected-component count,
shape bias, panel size, and source palette.  In particular, ordinary draws now
include the canonical task's disconnected-mask branch instead of teaching only
one connected blob.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "33c1de6c4310"
TASK_ID = "33c1de6c4310"
VERSION = "3.0.0"
RULE_HASH = "de709e7ff7b8"

SUMMARY = (
    "A full color-9 column separates equal left and right panels. The left "
    "panel contains one to four nonzero mask components; the right panel is a "
    "nonzero multicolor source. Copy each right-panel value through positions "
    "where the left panel is nonzero, and output 0 elsewhere."
)

INVARIANTS = [
    "exactly one full color-9 column separates two equal-size panels",
    "the left panel contains both background 0 and one to four nonzero mask components",
    "the right panel contains no 0 or 9 and uses two to eight colors",
    "masked and unmasked source positions both carry multiple colors, so both panels are needed",
    "at least one copied value differs from its mask color, refuting mask-color echo",
    "the mask is neither a row-major prefix nor suffix, refuting fixed-position count-only copying",
]

HELPFUL_TEXTURES = ("varied", "wide", "tall")
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over 5..16",
        "valid": "5..16",
    },
    "panel_w": {
        "type": "int",
        "default": "difficulty-aware draw over 4..14",
        "valid": "4..14",
    },
    "mask_components": {
        "type": "int",
        "default": "difficulty-aware draw over 1..4",
        "valid": "1..4",
    },
    "src_colors": {
        "type": "int",
        "default": "difficulty-aware draw over 2..8",
        "valid": "2..8",
    },
    "texture": {
        "type": "str",
        "default": "rng helpful mask-shape bias",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _coerce_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    out = []
    for row in grid:
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row]
            except ValueError as exc:
                raise ValueError("row strings must contain only digits") from exc
        elif isinstance(row, list):
            values = list(row)
        else:
            raise ValueError("grid rows must be lists or digit strings")
        if not values:
            raise ValueError("grid rows must be non-empty")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for value in values
        ):
            raise ValueError("grid values must be integer colors in 0..9")
        out.append(values)
    width = len(out[0])
    if any(len(row) != width for row in out):
        raise ValueError("grid must be rectangular")
    return out


def _is_fixed_traversal_mask(cells, h, w):
    """Reject masks determined only by their cell count and a fixed scan order."""
    indices = sorted(r * w + c for r, c in cells)
    count = len(indices)
    return indices == list(range(count)) or indices == list(range(h * w - count, h * w))


def _components(cells):
    remaining = set(cells)
    found = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        found.append(component)
    return found


def _scene_facts(grid):
    g = _coerce_grid(grid)
    h, width = len(g), len(g[0])
    dividers = [
        c for c in range(width)
        if all(g[r][c] == 9 for r in range(h))
    ]
    if len(dividers) != 1:
        raise ValueError(
            f"expected exactly one full color-9 divider column; found {len(dividers)}"
        )
    divider = dividers[0]
    left = [row[:divider] for row in g]
    right = [row[divider + 1:] for row in g]
    if divider == 0 or any(len(row) != divider for row in right):
        raise ValueError("divider must split the grid into equal non-empty panels")

    mask = {
        (r, c)
        for r in range(h)
        for c in range(divider)
        if left[r][c] != 0
    }
    background = {
        (r, c)
        for r in range(h)
        for c in range(divider)
        if left[r][c] == 0
    }
    return {
        "grid": g,
        "height": h,
        "panel_w": divider,
        "left": left,
        "right": right,
        "mask": mask,
        "background": background,
        "components": _components(mask) if mask else [],
        "mask_palette": {left[r][c] for r, c in mask},
        "source_palette": {value for row in right for value in row},
        "masked_source_palette": {right[r][c] for r, c in mask},
        "unmasked_source_palette": {right[r][c] for r, c in background},
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone mask/source lessons."""
    del difficulty, meta
    try:
        facts = _scene_facts(grid)
    except ValueError as exc:
        return [str(exc)]

    errors = []
    h = facts["height"]
    panel_w = facts["panel_w"]
    left = facts["left"]
    right = facts["right"]
    mask = facts["mask"]
    background = facts["background"]
    components = facts["components"]

    if not 5 <= h <= 16:
        errors.append(f"grid height must be in 5..16; got {h}")
    if not 4 <= panel_w <= 14:
        errors.append(f"panel width must be in 4..14; got {panel_w}")
    if any(value == 9 for row in left + right for value in row):
        errors.append("color 9 may appear only in the separator column")
    if len(mask) < 2:
        errors.append("mask must contain at least two nonzero cells")
    if len(background) < 2:
        errors.append("mask must leave at least two background cells")
    if not 1 <= len(components) <= 4:
        errors.append(
            f"mask must contain 1..4 four-connected components; found {len(components)}"
        )
    if _is_fixed_traversal_mask(mask, h, panel_w):
        errors.append(
            "mask must not be a row-major prefix or suffix determined only by cell count"
        )
    if not 1 <= len(facts["mask_palette"]) <= 3:
        errors.append("mask must use one to three nonzero colors")

    source_values = [value for row in right for value in row]
    if any(value in (0, 9) for value in source_values):
        errors.append("right source panel must contain only colors 1..8")
    if not 2 <= len(facts["source_palette"]) <= 8:
        errors.append("right source panel must use two to eight colors")
    if len(facts["masked_source_palette"]) < 2:
        errors.append("masked source positions must contain at least two colors")
    if len(facts["unmasked_source_palette"]) < 2:
        errors.append("unmasked source positions must contain at least two colors")
    if not facts["masked_source_palette"] & facts["unmasked_source_palette"]:
        errors.append(
            "at least one source color must occur both inside and outside the mask"
        )
    if mask and not any(
        left[r][c] != right[r][c]
        for r, c in mask
    ):
        errors.append("copied values must not merely echo every mask color")
    return errors


def observe_overrides(grid):
    """Expose exact semantic axes recoverable from a returned grid."""
    facts = _scene_facts(grid)
    return {
        "panel_w": facts["panel_w"],
        "mask_components": len(facts["components"]),
        "src_colors": len(facts["source_palette"]),
    }


def rule_mirror(grid):
    """Input-pure audit mirror; the canonical Racket program remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid mask/source scene: " + "; ".join(errors))
    facts = _scene_facts(grid)
    return [
        [
            facts["right"][r][c] if facts["left"][r][c] != 0 else 0
            for c in range(facts["panel_w"])
        ]
        for r in range(facts["height"])
    ]


def _partition_sizes(rng, total, count):
    sizes = [1] * count
    remaining = total - count
    while remaining:
        sizes[rng.randrange(count)] += 1
        remaining -= 1
    rng.shuffle(sizes)
    return sizes


def _weighted_choice(rng, candidates, texture):
    weighted = []
    for cell, dr, dc in candidates:
        weight = 1
        if texture == "wide" and dc:
            weight = 6
        elif texture == "tall" and dr:
            weight = 6
        elif texture == "varied" and dr and dc == 0:
            weight = 2
        weighted.extend([cell] * weight)
    return rng.choice(weighted)


def _choose_seeds(rng, h, w, count):
    cells = [(r, c) for r in range(h) for c in range(w)]
    for _ in range(300):
        rng.shuffle(cells)
        seeds = []
        for candidate in cells:
            if all(
                abs(candidate[0] - other[0]) + abs(candidate[1] - other[1]) >= 3
                for other in seeds
            ):
                seeds.append(candidate)
                if len(seeds) == count:
                    return seeds
    # The 5x4 minimum still admits four well-separated corner seeds.
    fallback = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    return fallback[:count]


def _mask_cells(rng, h, w, component_count, target, texture):
    sizes = _partition_sizes(rng, target, component_count)
    for _ in range(500):
        seeds = _choose_seeds(rng, h, w, component_count)
        components = [{seed} for seed in seeds]
        occupied = {seed: index for index, seed in enumerate(seeds)}
        failed = False
        while any(len(component) < sizes[index] for index, component in enumerate(components)):
            progress = False
            order = list(range(component_count))
            rng.shuffle(order)
            for index in order:
                component = components[index]
                if len(component) >= sizes[index]:
                    continue
                candidates = []
                seen = set()
                for r, c in component:
                    for dr, dc in _DIRS4:
                        cell = (r + dr, c + dc)
                        if cell in seen:
                            continue
                        seen.add(cell)
                        nr, nc = cell
                        if not (0 <= nr < h and 0 <= nc < w) or cell in occupied:
                            continue
                        # Keep a zero moat between distinct components.
                        if any(
                            neighbor in occupied and occupied[neighbor] != index
                            for ddr, ddc in _DIRS4
                            for neighbor in [(nr + ddr, nc + ddc)]
                        ):
                            continue
                        candidates.append((cell, dr, dc))
                if not candidates:
                    failed = True
                    break
                chosen = _weighted_choice(rng, candidates, texture)
                component.add(chosen)
                occupied[chosen] = index
                progress = True
            if failed or not progress:
                failed = True
                break
        if not failed:
            cells = set().union(*components)
            if (
                len(cells) == target
                and len(_components(cells)) == component_count
                and not _is_fixed_traversal_mask(cells, h, w)
            ):
                return cells
    raise ValueError(
        f"could not construct {component_count} separated mask components "
        f"with {target} cells in {h}x{w}"
    )


def _target_mask_cells(rng, h, w, component_count, difficulty, texture):
    bands = {
        "easy": (20, 32),
        "medium": (23, 38),
        "hard": (27, 44),
    }
    lo, hi = bands.get(difficulty, (21, 41))
    if texture == "wide":
        lo, hi = lo + 1, hi + 1
    elif texture == "tall":
        lo, hi = max(18, lo - 1), max(24, hi - 1)
    area = h * w
    target = round(area * rng.randint(lo, hi) / 100)
    target = max(target, max(3, 2 * component_count))
    return min(target, area - 2)


def _paint_mask(rng, grid, cells, difficulty):
    max_colors = 1 if difficulty == "easy" else 2 if difficulty == "medium" else 3
    color_count = rng.randint(1, min(max_colors, len(cells)))
    palette = rng.sample(list(range(1, 9)), color_count)
    positions = list(cells)
    rng.shuffle(positions)
    for index, (r, c) in enumerate(positions):
        grid[r][c] = palette[index % color_count]
    return palette


def _build_source(rng, h, w, palette, mask, left):
    positions = [(r, c) for r in range(h) for c in range(w)]
    source = [[rng.choice(palette) for _ in range(w)] for _ in range(h)]

    protected = set()
    mask_positions = list(mask)
    background_positions = [position for position in positions if position not in mask]
    rng.shuffle(mask_positions)
    rng.shuffle(background_positions)
    for cells in (mask_positions, background_positions):
        source[cells[0][0]][cells[0][1]] = palette[0]
        source[cells[1][0]][cells[1][1]] = palette[1]
        protected.update(cells[:2])

    # Guarantee every requested source color is present after the branch witnesses.
    counts = {color: 0 for color in palette}
    for row in source:
        for value in row:
            counts[value] += 1
    free = [position for position in positions if position not in protected]
    rng.shuffle(free)
    for color in palette:
        if counts[color]:
            continue
        r, c = free.pop()
        counts[source[r][c]] -= 1
        source[r][c] = color
        counts[color] += 1

    # A mask-color echo must be impossible as a complete shortcut.
    if all(source[r][c] == left[r][c] for r, c in mask):
        r, c = mask_positions[0]
        source[r][c] = next(color for color in palette if color != left[r][c])

    # The anti-echo rewrite above may replace the sole occurrence of a color.
    # Re-establish the exact requested palette without disturbing the two
    # inside/outside branch witnesses.  Choose donors with multiplicity > 1 so
    # restoring one color cannot erase another.
    counts = {color: 0 for color in palette}
    for row in source:
        for value in row:
            counts[value] += 1
    for color in palette:
        if counts[color]:
            continue
        donors = [
            position for position in free
            if counts[source[position[0]][position[1]]] > 1
        ]
        if not donors:
            raise ValueError("could not preserve the requested source palette")
        r, c = donors.pop()
        counts[source[r][c]] -= 1
        source[r][c] = color
        counts[color] += 1
    return source


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 5, 16)
    panel_w = ctx.draw_int_diff("panel_w", 4, 14)
    component_count = ctx.draw_int_diff("mask_components", 1, 4)
    source_color_count = ctx.draw_int_diff("src_colors", 2, 8)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    mask_rng = ctx.draw_rng("mask-layout")
    density_rng = ctx.draw_rng("mask-density")
    mask_color_rng = ctx.draw_rng("mask-colors")
    source_rng = ctx.draw_rng("source")

    target = _target_mask_cells(
        density_rng,
        h,
        panel_w,
        component_count,
        difficulty,
        texture,
    )
    mask = _mask_cells(
        mask_rng,
        h,
        panel_w,
        component_count,
        target,
        texture,
    )

    left = full_grid(h, panel_w, 0)
    _paint_mask(mask_color_rng, left, mask, difficulty)
    source_palette = source_rng.sample(list(range(1, 9)), source_color_count)
    right = _build_source(source_rng, h, panel_w, source_palette, mask, left)

    grid = full_grid(h, panel_w * 2 + 1, 0)
    for r in range(h):
        grid[r][:panel_w] = left[r]
        grid[r][panel_w] = 9
        grid[r][panel_w + 1:] = right[r]
    return grid
