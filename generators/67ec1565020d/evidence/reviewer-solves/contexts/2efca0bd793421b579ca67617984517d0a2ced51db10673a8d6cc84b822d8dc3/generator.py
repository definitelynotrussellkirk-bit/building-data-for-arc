"""Inputs for component-wise bounding-box-aspect recoloring.

The unchanged Racket rule supplies every label.  Default inputs include an
irregular connected object and repeat one input color across different aspect
classes, refuting the two strongest shortcuts that fit the canonical pairs:
filling entire bounding boxes and assigning one output per input color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67ec1565020d"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b45100a04df9"
SUMMARY = (
    "Recolor each monochrome 4-component by bounding-box aspect: wide->2, "
    "tall->3, square->4. Varied connected shapes, repeated colors across "
    "aspects, 8..14 by 9..14 canvases, and 3..6 objects."
)
INVARIANTS = [
    "8..14 by 9..14 rectangular integer-color grid with zero background",
    "3..6 monochrome 4-connected objects and at least one wide, tall, and square bbox",
    "default inputs contain a nonrectangle and repeat a color across aspect classes",
    "explicit dimensions, object count, and foreground-color count are exact",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..14; core favors 10", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "9..14; core favors 10", "valid": "9..14"},
    "n_blobs": {"type": "int", "default": "3..6; band-weighted", "valid": "3..6"},
    "n_distinct_colors": {
        "type": "int",
        "default": "1..n_blobs-1; core favors 3",
        "valid": "1..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("n_blobs", "n_distinct_colors")]
MIN_STRICT_FRAC = 1.0

_FOUR = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple(
    (row_delta, column_delta)
    for row_delta in (-1, 0, 1)
    for column_delta in (-1, 0, 1)
    if (row_delta, column_delta) != (0, 0)
)


class IncompatibleControls(ValueError):
    incompatible_axes = ("n_blobs", "n_distinct_colors")


def _components(grid):
    """Return monochrome 4-connected non-background components."""
    seen = set()
    groups = []
    height, width = len(grid), len(grid[0])
    for start_row in range(height):
        for start_column in range(width):
            color = grid[start_row][start_column]
            if color == 0 or (start_row, start_column) in seen:
                continue
            queue = [(start_row, start_column)]
            seen.add((start_row, start_column))
            for row, column in queue:
                for row_delta, column_delta in _FOUR:
                    neighbor_row = row + row_delta
                    neighbor_column = column + column_delta
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_column < width
                        and (neighbor_row, neighbor_column) not in seen
                        and grid[neighbor_row][neighbor_column] == color
                    ):
                        seen.add((neighbor_row, neighbor_column))
                        queue.append((neighbor_row, neighbor_column))
            groups.append((color, queue))
    return groups


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(column for _, column in cells),
        max(row for row, _ in cells),
        max(column for _, column in cells),
    )


def _orientation(cells):
    row_min, column_min, row_max, column_max = _bbox(cells)
    height = row_max - row_min + 1
    width = column_max - column_min + 1
    return "tall" if height > width else "wide" if width > height else "square"


def _shape(rng, orientation, max_height, max_width, *, nonrectangle=False):
    sizes = [
        (height, width)
        for height in range(1, min(6, max_height) + 1)
        for width in range(1, min(6, max_width) + 1)
        if ("tall" if height > width else "wide" if width > height else "square")
        == orientation
        and (not nonrectangle or min(height, width) >= 2)
    ]
    height, width = rng.choice(sizes)
    whole = {(row, column) for row in range(height) for column in range(width)}
    if min(height, width) == 1 or (not nonrectangle and rng.randrange(3) == 0):
        cells = whole
    else:
        # A bbox-spanning L is connected and has the requested dimensions. Grow
        # from its cardinal frontier while retaining at least one missing cell
        # when this object is the required anti-bounding-box witness.
        cells = {(row, 0) for row in range(height)} | {(0, column) for column in range(width)}
        limit = height * width - (1 if nonrectangle else 0)
        target_size = rng.randint(len(cells), limit)
        while len(cells) < target_size:
            frontier = sorted(
                {
                    (row + row_delta, column + column_delta)
                    for row, column in cells
                    for row_delta, column_delta in _FOUR
                }
                & (whole - cells)
            )
            cells.add(rng.choice(frontier))

    if rng.randrange(2):
        cells = {(height - 1 - row, column) for row, column in cells}
    if rng.randrange(2):
        cells = {(row, width - 1 - column) for row, column in cells}
    return cells


def _place_shape(rng, height, width, used, shape):
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(column for _, column in shape) + 1
    for _ in range(48):
        row_offset = rng.randint(0, height - shape_height)
        column_offset = rng.randint(0, width - shape_width)
        cells = {
            (row + row_offset, column + column_offset)
            for row, column in shape
        }
        if cells & used:
            continue
        if any(
            (row + row_delta, column + column_delta) in used
            for row, column in cells
            for row_delta, column_delta in _EIGHT
        ):
            continue
        return cells
    return None


def _slot_intervals(length, count, rng):
    """Partition an axis into ``count`` bands of >=2 cells with separators."""
    sizes = [2] * count
    for _ in range(length - (count - 1) - 2 * count):
        sizes[rng.randrange(count)] += 1
    result = []
    start = 0
    for size in sizes:
        result.append((start, size))
        start += size + 1
    return result


def _constructive_layout(rng, height, width, plan):
    """Crowded-grid fallback that preserves all requested objects exactly."""
    row_count, column_count = (2, 2) if len(plan) <= 4 else rng.choice(((2, 3), (3, 2)))
    rows = _slot_intervals(height, row_count, rng)
    columns = _slot_intervals(width, column_count, rng)
    slots = [
        (row, column, slot_height, slot_width)
        for row, slot_height in rows
        for column, slot_width in columns
    ]
    rng.shuffle(slots)
    placed = []
    for (orientation, color, nonrectangle), (
        row_offset,
        column_offset,
        slot_height,
        slot_width,
    ) in zip(plan, slots):
        shape = _shape(
            rng,
            orientation,
            slot_height,
            slot_width,
            nonrectangle=nonrectangle,
        )
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(column for _, column in shape) + 1
        row_offset += rng.randint(0, slot_height - shape_height)
        column_offset += rng.randint(0, slot_width - shape_width)
        placed.append(
            (
                color,
                {
                    (row + row_offset, column + column_offset)
                    for row, column in shape
                },
            )
        )
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or removed override axes: {sorted(unknown)}")

    bounds = {
        "grid_h": (8, 14),
        "grid_w": (9, 14),
        "n_blobs": (3, 6),
        "n_distinct_colors": (1, 6),
    }
    for name, value in overrides.items():
        if value is not None and (
            type(value) is not int or not bounds[name][0] <= value <= bounds[name][1]
        ):
            raise ValueError(f"{name} must be an integer in {bounds[name]}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    core = ctx.draw_choice("profile", ("core", "core", "core", "broad", "broad")) == "core"
    height = ctx.draw_choice(
        "grid_h",
        list(range(8, 15)) + ([10] * 200 if core else []),
    )
    width = ctx.draw_choice(
        "grid_w",
        list(range(9, 15)) + ([10] * 200 if core else []),
    )

    requested_colors = overrides.get("n_distinct_colors")
    minimum_objects = max(3, requested_colors or 1) if overrides.get("n_blobs") is None else 3
    favored_objects = 6 if difficulty == "hard" else 4
    object_options = list(range(minimum_objects, 7))
    n_blobs = ctx.draw_choice(
        "n_blobs",
        object_options + ([favored_objects] * 12 if favored_objects in object_options else []),
    )

    color_options = list(range(1, 7)) if requested_colors is not None else list(range(1, n_blobs))
    if requested_colors is None and 3 in color_options:
        color_options += [3] * (200 if core else 4)
    n_colors = ctx.draw_choice("n_distinct_colors", color_options)
    if n_colors > n_blobs:
        raise IncompatibleControls("n_distinct_colors cannot exceed n_blobs")

    rng = ctx.draw_rng("layout")
    palette = rng.sample(range(1, 10), n_colors)
    orientations = ["wide", "tall", "square"] + rng.choices(
        ("wide", "tall", "square"),
        k=n_blobs - 3,
    )
    if n_colors < n_blobs:
        # The same input color occurs on wide and tall objects, so assigning one
        # output color globally per input color cannot explain default lessons.
        colors = [palette[0], palette[0]] + palette[1:]
        colors += [rng.choice(palette) for _ in range(n_blobs - len(colors))]
    else:
        colors = palette[:]

    # The required nonrectangle is initially the square-class object.  Shuffling
    # removes fixed role/position correlations while preserving the witness.
    plan = [
        (orientation, color, index == 2)
        for index, (orientation, color) in enumerate(zip(orientations, colors))
    ]
    rng.shuffle(plan)

    placed = None
    for _ in range(10):
        used = set()
        trial = []
        for orientation, color, nonrectangle in plan:
            shape = _shape(
                rng,
                orientation,
                height,
                width,
                nonrectangle=nonrectangle,
            )
            cells = _place_shape(rng, height, width, used, shape)
            if cells is None:
                break
            used.update(cells)
            trial.append((color, cells))
        if len(trial) == n_blobs:
            placed = trial
            break
    if placed is None:
        placed = _constructive_layout(rng, height, width, plan)

    grid = full_grid(height, width, 0)
    for color, cells in placed:
        for row, column in cells:
            grid[row][column] = color
    return grid


def observe_overrides(grid):
    groups = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(groups),
        "n_distinct_colors": len({color for color, _ in groups}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, list)
        or not grid
        or not all(isinstance(row, list) and row for row in grid)
    ):
        return ["grid must be a nonempty list of nonempty rows"]
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["colors must be integers 0..9 (not bool)"]
    if not (8 <= height <= 14 and 9 <= width <= 14):
        return ["grid dimensions must be 8..14 by 9..14"]

    groups = _components(grid)
    errors = []
    if not 3 <= len(groups) <= 6:
        errors.append(f"expected 3..6 components, got {len(groups)}")
    missing = {"wide", "tall", "square"} - {
        _orientation(cells) for _, cells in groups
    }
    if missing:
        errors.append(f"missing aspect classes: {sorted(missing)}")
    return errors


def strict_canonical_like(grid):
    """Task-domain validity, not exact canonical rectangle/palette matching."""
    return self_check(grid)


def _output_color(cells):
    return {"wide": 2, "tall": 3, "square": 4}[_orientation(cells)]


def _group_by_color(grid):
    """Rival: merge disconnected components that share an input color."""
    merged = {}
    for color, cells in _components(grid):
        merged.setdefault(color, []).extend(cells)
    out = full_grid(len(grid), len(grid[0]), 0)
    for cells in merged.values():
        value = _output_color(cells)
        for row, column in cells:
            out[row][column] = value
    return out


def _fill_bounding_boxes(grid):
    """Rival: classify correctly but paint every cell in each bounding box."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for _, cells in _components(grid):
        row_min, column_min, row_max, column_max = _bbox(cells)
        value = _output_color(cells)
        for row in range(row_min, row_max + 1):
            for column in range(column_min, column_max + 1):
                out[row][column] = value
    return out


def _color_spans_aspects(grid):
    aspects = {}
    for color, cells in _components(grid):
        aspects.setdefault(color, set()).add(_orientation(cells))
    return any(len(values) > 1 for values in aspects.values())


def _nonrectangle(grid):
    for _, cells in _components(grid):
        row_min, column_min, row_max, column_max = _bbox(cells)
        if len(cells) < (row_max - row_min + 1) * (column_max - column_min + 1):
            return True
    return False


SEMANTIC_WITNESSES = {
    "color_spans_aspects": _color_spans_aspects,
    "nonrectangle": _nonrectangle,
}
SEMANTIC_RIVALS = {
    "group_by_color": _group_by_color,
    "fill_bounding_boxes": _fill_bounding_boxes,
}
WITNESS_RIVALS = {
    "color_spans_aspects": ["group_by_color"],
    "nonrectangle": ["fill_bounding_boxes"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
