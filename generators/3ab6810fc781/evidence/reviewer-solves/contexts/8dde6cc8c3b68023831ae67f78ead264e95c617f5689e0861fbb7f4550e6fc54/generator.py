"""Semantic generator for 3ab6810fc781, crop-the-largest-object.

A zero-background scene contains at least three mutually separated
4-connected nonzero components. Exactly one component is strictly largest.
The answer is the rectangular crop of the input bounded by that component;
zeros inside its concavities are preserved, and every decoy lies outside the
selected bounding box.

The default distribution keeps positive support on all three official scenes
modulo D4 symmetry and global nonzero-color relabeling, then broadens the same
rule over sizes 8..16, varied connected shapes, colors, positions, and decoys.
"""
from __future__ import annotations

from collections import deque
from typing import Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "3ab6810fc781"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ce29890d1df1"

SUMMARY = (
    "On a zero background, identify the unique strictly largest 4-connected "
    "nonzero component, ignoring color, and crop the whole input to that "
    "component's bounding box. Preserve the component's colors and any zero "
    "concavities; smaller components are decoys outside the crop."
)

INVARIANTS = [
    "zero is the unique modal background",
    "there are at least three 4-connected nonzero components",
    "exactly one component is strictly largest and has at least five cells",
    "the selected component spans at least two rows and columns and is non-solid",
    "all smaller components lie outside the selected bounding box",
    "cropping the selected bounding box is a strict size reduction",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted draw with official-size support",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted draw with official-size support",
        "valid": "8..16",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_TEMPLATE_RATE = 0.90
_CANONICAL_TEMPLATES = (((0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 2, 3, 0, 0, 0, 0, 0, 0), (0, 2, 2, 3, 0, 0, 4, 0, 0), (0, 0, 2, 0, 0, 0, 4, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 5, 5, 0, 0, 0, 0), (0, 0, 0, 5, 5, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0)), ((0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 6, 7, 0, 0, 0, 0, 0), (0, 0, 0, 6, 6, 0, 0, 0, 0, 0), (0, 0, 0, 0, 6, 0, 0, 0, 0, 0), (0, 0, 0, 0, 6, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 4, 4, 0, 0, 0, 0, 0, 0, 0), (0, 4, 4, 0, 0, 0, 0, 0, 9, 0), (0, 0, 0, 0, 0, 0, 0, 0, 9, 0)), ((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 8, 8, 0, 0, 0, 0, 0), (0, 0, 0, 0, 8, 8, 8, 0, 0, 0, 0), (0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0), (0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0)))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not 8 <= value <= 16
        ):
            raise ValueError(f"{name} must be an integer in [8, 16]")


def _dimension_options(difficulty) -> tuple[int, ...]:
    base = list(range(8, 17))
    if difficulty == "easy":
        base += [9, 10, 11] * 5
    elif difficulty == "hard":
        base += [9, 10, 11] * 3 + [14, 15, 16] * 2
    else:
        base += [9, 10, 11] * 4 + [12, 13] * 2
    return tuple(base)


def _transform(grid: Sequence[Sequence[int]], code: int) -> list[list[int]]:
    out = [list(row) for row in grid]
    if code >= 4:
        out = [list(reversed(row)) for row in out]
    for _ in range(code % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _recolor_by_first_occurrence(grid, colors: Sequence[int]) -> list[list[int]]:
    mapping: dict[int, int] = {}
    out = []
    for row in grid:
        new_row = []
        for value in row:
            if value == 0:
                new_row.append(0)
            else:
                if value not in mapping:
                    mapping[value] = colors[len(mapping)]
                new_row.append(mapping[value])
        out.append(new_row)
    return out


def _components(grid) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] != 0
    }
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            row, column = queue.popleft()
            cells.append((row, column))
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, column + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(tuple(sorted(cells)))
    return sorted(components, key=lambda cells: cells[0])


def _bbox(cells) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [column for _, column in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    return top, left, bottom - top + 1, right - left + 1


def _analysis(grid) -> dict:
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty list or tuple"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists or tuples"]}
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid cells must be integer ARC colors 0..9"]}

    height = len(grid)
    if not 8 <= height <= 16:
        errors.append(f"grid height must be in 8..16, got {height}")
    if not 8 <= width <= 16:
        errors.append(f"grid width must be in 8..16, got {width}")
    if errors:
        return {"errors": errors}

    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    if 0 not in counts:
        errors.append("zero background is required")
    elif counts[0] <= max((n for color, n in counts.items() if color != 0), default=0):
        errors.append("zero must be the unique modal color")

    components = _components(grid)
    sizes = sorted((len(cells) for cells in components), reverse=True)
    if len(components) < 3:
        errors.append(f"need at least three nonzero components, got {len(components)}")
    if not sizes:
        errors.append("need a nonzero component")
        return {"errors": errors, "components": components}
    if sizes[0] < 5:
        errors.append(f"largest component must contain at least five cells, got {sizes[0]}")
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        errors.append("largest nonzero component must be unique by cell count")

    largest = max(components, key=len)
    top, left, box_h, box_w = _bbox(largest)
    if box_h < 2 or box_w < 2:
        errors.append("largest component must span at least two rows and columns")
    if box_h * box_w <= len(largest):
        errors.append("largest component crop must contain at least one zero concavity")
    if box_h == height and box_w == width:
        errors.append("largest component crop must reduce the canvas size")

    largest_set = set(largest)
    for index, cells in enumerate(components):
        if set(cells) == largest_set:
            continue
        if any(
            top <= row < top + box_h and left <= column < left + box_w
            for row, column in cells
        ):
            errors.append(f"decoy component {index} enters the selected bounding box")

    return {
        "errors": errors,
        "components": components,
        "component_sizes": sizes,
        "largest": largest,
        "bbox": (top, left, box_h, box_w),
        "palette": tuple(sorted(counts)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analysis(grid)["errors"])


def rule_mirror(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    top, left, box_h, box_w = analysis["bbox"]
    return [list(row[left:left + box_w]) for row in grid[top:top + box_h]]


def observe_overrides(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _normalized_color_pattern(grid) -> tuple[tuple[int, ...], ...]:
    mapping: dict[int, int] = {}
    next_color = 1
    out = []
    for row in grid:
        normalized = []
        for value in row:
            if value == 0:
                normalized.append(0)
            else:
                if value not in mapping:
                    mapping[value] = next_color
                    next_color += 1
                normalized.append(mapping[value])
        out.append(tuple(normalized))
    return tuple(out)


def canonical_profile_signature(grid) -> tuple[tuple[int, ...], ...]:
    return min(_normalized_color_pattern(_transform(grid, code)) for code in range(8))


_CANONICAL_SIGNATURES = tuple(
    sorted({canonical_profile_signature(template) for template in _CANONICAL_TEMPLATES})
)


def _random_connected_shape(rng, size: int, max_h: int, max_w: int):
    for _ in range(240):
        cells = {(0, 0)}
        while len(cells) < size:
            row, column = rng.choice(sorted(cells))
            dr, dc = rng.choice(_CARDINAL)
            cells.add((row + dr, column + dc))
        min_row = min(row for row, _ in cells)
        min_col = min(column for _, column in cells)
        normalized = tuple(sorted((row - min_row, column - min_col) for row, column in cells))
        box_h = max(row for row, _ in normalized) + 1
        box_w = max(column for _, column in normalized) + 1
        if (
            2 <= box_h <= max_h
            and 2 <= box_w <= max_w
            and box_h * box_w > len(normalized)
        ):
            return normalized
    raise RuntimeError("could not draw a connected non-solid shape")


def _sprawling_l_shape(size: int) -> tuple[tuple[int, int], ...]:
    """Connected size-n decoy with deliberately large bounding-box area."""
    height = size // 2 + 1
    width = size - height + 1
    return tuple(
        [(0, column) for column in range(width)]
        + [(row, 0) for row in range(1, height)]
    )


def _placement_is_free(occupied, shape, top, left, height, width) -> bool:
    for row, column in shape:
        rr, cc = top + row, left + column
        if not (0 <= rr < height and 0 <= cc < width):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < height and 0 <= nc < width and occupied[nr][nc]:
                    return False
    return True


def _paint_shape(grid, occupied, shape, top, left, palette, rng) -> None:
    assignments = [rng.choice(palette) for _ in shape]
    for index, color in enumerate(palette):
        if index < len(assignments):
            assignments[index] = color
    rng.shuffle(assignments)
    for (row, column), color in zip(shape, assignments):
        rr, cc = top + row, left + column
        grid[rr][cc] = color
        occupied[rr][cc] = True


def _draw_generalized(height: int, width: int, difficulty, ctx) -> list[list[int]]:
    layout_rng = ctx.draw_rng("generalized_layout")
    color_rng = ctx.draw_rng("generalized_colors")
    if difficulty == "easy":
        target_range, decoy_range = (5, 7), (2, 3)
    elif difficulty == "hard":
        target_range, decoy_range = (8, 12), (3, 5)
    else:
        target_range, decoy_range = (6, 10), (2, 4)

    for attempt in range(240):
        rng = ctx.draw_rng(f"generalized_attempt_{attempt}")
        grid = [[0 for _ in range(width)] for _ in range(height)]
        occupied = [[False for _ in range(width)] for _ in range(height)]
        upper = min(target_range[1], max(5, (height * width) // 5))
        lower = min(target_range[0], upper)
        target_size = rng.randint(lower, upper)
        target = _random_connected_shape(
            rng,
            target_size,
            max_h=min(5, height - 2),
            max_w=min(5, width - 2),
        )
        target_h = max(row for row, _ in target) + 1
        target_w = max(column for _, column in target) + 1
        top = rng.randint(0, height - target_h)
        left = rng.randint(0, width - target_w)

        target_color_count = 1 if color_rng.random() < 0.35 else color_rng.randint(2, min(3, target_size))
        all_colors = color_rng.sample(range(1, 10), min(6, target_color_count + decoy_range[1]))
        _paint_shape(
            grid,
            occupied,
            target,
            top,
            left,
            all_colors[:target_color_count],
            color_rng,
        )

        # Reserve the full crop rectangle and a one-cell halo so no decoy can
        # leak into the output or connect to the target.
        for row in range(top - 1, top + target_h + 1):
            for column in range(left - 1, left + target_w + 1):
                if 0 <= row < height and 0 <= column < width:
                    occupied[row][column] = True

        decoy_count = rng.randint(*decoy_range)
        placed = 0
        for decoy_index in range(decoy_count):
            if decoy_index == 0 and rng.random() < 0.70:
                decoy_size = min(target_size - 1, 7)
                decoy = _sprawling_l_shape(decoy_size)
            else:
                max_decoy = min(target_size - 1, 5 + (difficulty == "hard"))
                decoy_size = rng.randint(2, max(2, max_decoy))
                try:
                    decoy = _random_connected_shape(
                        rng,
                        decoy_size,
                        max_h=min(4, height),
                        max_w=min(4, width),
                    )
                except RuntimeError:
                    continue
            decoy_h = max(row for row, _ in decoy) + 1
            decoy_w = max(column for _, column in decoy) + 1
            for _ in range(120):
                decoy_top = rng.randint(0, height - decoy_h)
                decoy_left = rng.randint(0, width - decoy_w)
                if not _placement_is_free(
                    occupied, decoy, decoy_top, decoy_left, height, width
                ):
                    continue
                decoy_palette = (rng.choice(all_colors),)
                _paint_shape(
                    grid,
                    occupied,
                    decoy,
                    decoy_top,
                    decoy_left,
                    decoy_palette,
                    color_rng,
                )
                placed += 1
                break
        if placed >= 2 and not self_check(grid, difficulty=difficulty):
            return grid
    raise RuntimeError("unable to construct a valid largest-object scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    options = _dimension_options(difficulty)
    height = ctx.draw_choice("grid_h", options)
    width = ctx.draw_choice("grid_w", options)

    canonical_by_shape = {
        (len(template), len(template[0])): template
        for template in _CANONICAL_TEMPLATES
    }
    template = canonical_by_shape.get((height, width))
    prior_rng = ctx.draw_rng("canonical_profile_prior")
    if template is not None and prior_rng.random() < _CANONICAL_TEMPLATE_RATE:
        transformed = _transform(template, prior_rng.randrange(8))
        palette_count = len({value for row in transformed for value in row if value})
        colors = prior_rng.sample(range(1, 10), palette_count)
        return _recolor_by_first_occurrence(transformed, colors)

    return _draw_generalized(height, width, difficulty, ctx)
