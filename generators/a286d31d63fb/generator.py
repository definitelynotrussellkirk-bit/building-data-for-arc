"""Constructive sampler for task a286d31d63fb: recolor flat row profiles.

The unchanged canonical rule treats each monochromatic 4-connected nonzero
component independently.  A component is recolored to cyan(8) exactly when
every occupied row contains the same number of cells.

Ordinary lessons always contain both qualifying and non-qualifying components,
use a distinct source color per component, and include at least one qualifying
non-rectangle.  That last witness separates the selected rule from the tempting
shortcut "recolor solid rectangles" that fits every canonical demonstration.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a286d31d63fb"
TASK_ID = GENERATOR_ID
RULE_HASH = "bc2002d0a0d4"
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background grid contains distinctly colored 4-connected components. "
    "For each component, count its cells in every occupied row. Components with "
    "a constant per-row count are recolored to cyan(8); components whose row "
    "counts vary keep their source color. Generated lessons contain both classes "
    "and at least one constant-row-profile shape that is not a solid rectangle."
)

INVARIANTS = [
    "background is 0 and cyan(8) is reserved for the output",
    "each nonzero source color belongs to exactly one 4-connected component",
    "there is at least one constant-row-profile component",
    "there is at least one varying-row-profile component",
    "every generated lesson contains a non-rectangular constant-row-profile component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTES = {
    "default": (1, 2, 3, 4, 5),
    "warm": (1, 2, 4, 6, 7),
    "cool": (1, 3, 5, 6, 9),
    "varied": (2, 3, 4, 7, 9),
}

AXES = {
    "height": {
        "type": "int",
        "default": "difficulty schedule with canonical 9/10-row anchors",
        "valid": "8..16",
        "doc": "Input-grid height; exact overrides work in every difficulty band.",
    },
    "width": {
        "type": "int",
        "default": "difficulty schedule with canonical 15/16-column anchors",
        "valid": "11..18",
        "doc": "Input-grid width; exact overrides work in every difficulty band.",
    },
    "flat_component_count": {
        "type": "int",
        "default": "scheduled 1..3 with canonical count 2 represented in every band",
        "valid": "1..3",
        "doc": "Number of constant-row-profile components.",
    },
    "nonflat_component_count": {
        "type": "int",
        "default": "scheduled 1..2 with canonical count 1 represented in every band",
        "valid": "1..2",
        "doc": "Number of varying-row-profile components.",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled palette",
        "valid": "default|warm|cool|varied",
        "doc": "Five-color source palette from which distinct component colors are drawn.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Grid = list[list[int]]

# Solid rectangles and lines teach that ordinary rectangles qualify.
_FLAT_RECTANGLES: tuple[Shape, ...] = (
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
)

# These are connected and have profiles [2,2] / [2,2,2], but leave holes in
# their bounding rectangles.  Every generated lesson includes one of them.
_FLAT_NONRECTANGLES: tuple[Shape, ...] = (
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
)
_FLAT_ALL = _FLAT_RECTANGLES + _FLAT_NONRECTANGLES

# Canonical-like profiles [1,2,3], [2,3,2], [3,2,3] plus compact T/L lessons.
_NON_FLAT: tuple[Shape, ...] = (
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
)

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Each band contains both canonical dimension profiles and broader support.
_DIMENSION_PROFILES = {
    None: ((9, 15), (10, 16), (8, 11), (11, 14), (12, 17), (14, 16), (16, 18), (10, 13)),
    "easy": ((9, 15), (10, 16), (8, 11), (9, 14), (10, 15), (11, 16)),
    "medium": ((9, 15), (10, 16), (11, 14), (12, 17), (13, 15), (14, 18)),
    "hard": ((9, 15), (10, 16), (12, 17), (14, 16), (15, 18), (16, 18)),
}
_COUNT_PROFILES = {
    None: ((2, 1), (1, 2), (3, 1), (2, 2), (1, 1), (3, 2)),
    "easy": ((2, 1), (1, 1), (2, 1), (1, 2)),
    "medium": ((2, 1), (1, 2), (3, 1), (2, 2)),
    "hard": ((2, 1), (2, 2), (3, 1), (3, 2)),
}
_PALETTE_SCHEDULE = {
    None: PALETTE_KINDS,
    "easy": ("default", "varied", "cool", "warm"),
    "medium": ("varied", "default", "warm", "cool"),
    "hard": ("cool", "warm", "varied", "default"),
}


def _shape_size(shape: Sequence[Cell]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _reflect(shape: Shape, *, horizontal: bool, vertical: bool) -> Shape:
    height, width = _shape_size(shape)
    transformed = []
    for row, col in shape:
        if vertical:
            row = height - 1 - row
        if horizontal:
            col = width - 1 - col
        transformed.append((row, col))
    return tuple(sorted(transformed))


def _row_profile(cells: Iterable[Cell]) -> tuple[int, ...]:
    counts = Counter(row for row, _ in cells)
    return tuple(counts[row] for row in sorted(counts))


def _is_flat(cells: Iterable[Cell]) -> bool:
    profile = _row_profile(cells)
    return bool(profile) and len(set(profile)) == 1


def _fills_bbox(cells: Iterable[Cell]) -> bool:
    cells = tuple(cells)
    if not cells:
        return False
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _components_4conn(grid: Grid) -> list[tuple[int, set[Cell]]]:
    """Return monochromatic 4-connected nonzero components."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[tuple[int, set[Cell]]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            cells = {(start_row, start_col)}
            seen.add((start_row, start_col))
            stack = [(start_row, start_col)]
            while stack:
                row, col = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (row + dr, col + dc)
                    if point in seen:
                        continue
                    rr, cc = point
                    if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == color:
                        seen.add(point)
                        cells.add(point)
                        stack.append(point)
            result.append((color, cells))
    return result


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    for name in ("height", "width", "flat_component_count", "nonflat_component_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    palette = overrides.get("palette_kind")
    if palette is not None and type(palette) is not str:
        raise TypeError("palette_kind must be a string")


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Record a scheduled default while preserving the full override domain."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _scheduled_choice(ctx, name: str, options: tuple[str, ...], default: str) -> str:
    available = options if ctx.overrides.get(name) is not None else (default,)
    return str(ctx.draw_choice(name, available))


def _distribute(slack: int, buckets: int, rng) -> list[int]:
    result = [0] * buckets
    for _ in range(slack):
        result[rng.randrange(buckets)] += 1
    return result


def _pack_lane(
    grid: Grid,
    lane: Sequence[tuple[Shape, int]],
    *,
    top: int,
    lane_height: int,
    rng,
) -> None:
    width = len(grid[0])
    widths = [_shape_size(shape)[1] for shape, _ in lane]
    occupied = sum(widths) + max(0, len(lane) - 1)
    if occupied > width:
        raise ValueError(f"lane requires width {occupied}, grid width is {width}")
    margins = _distribute(width - occupied, len(lane) + 1, rng)
    col = margins[0]
    for index, (shape, color) in enumerate(lane):
        shape_height, shape_width = _shape_size(shape)
        row = top + rng.randint(0, lane_height - shape_height)
        for dr, dc in shape:
            grid[row + dr][col + dc] = color
        col += shape_width
        if index + 1 < len(lane):
            col += 1 + margins[index + 1]


def _pack_components(
    height: int,
    width: int,
    components: list[tuple[Shape, int]],
    rng,
) -> Grid:
    """Pack 2..5 components in two separated lanes without retries."""
    shuffled = list(components)
    rng.shuffle(shuffled)
    top_count = (len(shuffled) + 1) // 2
    top_lane = shuffled[:top_count]
    bottom_lane = shuffled[top_count:]
    top_height = max(_shape_size(shape)[0] for shape, _ in top_lane)
    bottom_height = max(_shape_size(shape)[0] for shape, _ in bottom_lane)
    occupied = top_height + 1 + bottom_height
    if occupied > height:
        raise ValueError(f"two lanes require height {occupied}, grid height is {height}")
    vertical = _distribute(height - occupied, 3, rng)
    top = vertical[0]
    bottom = top + top_height + 1 + vertical[1]

    grid = full_grid(height, width, 0)
    _pack_lane(grid, top_lane, top=top, lane_height=top_height, rng=rng)
    _pack_lane(grid, bottom_lane, top=bottom, lane_height=bottom_height, rng=rng)
    return grid


def _choose_shapes(ctx, flat_count: int, nonflat_count: int) -> list[Shape]:
    rng = ctx.draw_rng("shapes")
    flat = [rng.choice(_FLAT_NONRECTANGLES)]
    flat.extend(rng.choice(_FLAT_ALL) for _ in range(flat_count - 1))
    nonflat = [rng.choice(_NON_FLAT) for _ in range(nonflat_count)]
    shapes = flat + nonflat
    return [
        _reflect(
            shape,
            horizontal=bool(rng.randrange(2)),
            vertical=bool(rng.randrange(2)),
        )
        for shape in shapes
    ]


def _source_colors(ctx, palette_kind: str, count: int) -> list[int]:
    colors = list(PALETTES[palette_kind])
    rng = ctx.draw_rng("component_colors")
    rng.shuffle(colors)
    return colors[:count]


def row_profile_output(grid: Grid) -> Grid:
    output = [list(row) for row in grid]
    for _, cells in _components_4conn(grid):
        if _is_flat(cells):
            for row, col in cells:
                output[row][col] = 8
    return output


def rectangle_only_output(grid: Grid) -> Grid:
    output = [list(row) for row in grid]
    for _, cells in _components_4conn(grid):
        if _fills_bbox(cells):
            for row, col in cells:
                output[row][col] = 8
    return output


def observe_overrides(grid: Grid) -> dict[str, int]:
    """Recover the exact semantic count axes from a returned grid."""
    components = _components_4conn(grid)
    return {
        "flat_component_count": sum(
            1 for _, cells in components if _is_flat(cells)
        ),
        "nonflat_component_count": sum(
            1 for _, cells in components if not _is_flat(cells)
        ),
    }


def _nonrectangular_flat_profile(grid: Grid) -> bool:
    try:
        if self_check(grid):
            return False
        return any(
            _is_flat(cells) and not _fills_bbox(cells)
            for _, cells in _components_4conn(grid)
        ) and row_profile_output(grid) != rectangle_only_output(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_RIVALS = {"rectangle_only": rectangle_only_output}
SEMANTIC_WITNESSES = {"nonrectangular_flat_profile": _nonrectangular_flat_profile}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    "nonrectangular_flat_profile": ["rectangle_only"],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural diagnostics; accept canonical and generated inputs."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["each row must be a list"]
    if not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (8 <= len(grid) <= 16):
        errors.append("height outside supported 8..16 domain")
    if not (11 <= width <= 18):
        errors.append("width outside supported 11..18 domain")

    bad_values = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not (0 <= value <= 9)
    ]
    if bad_values:
        errors.append("grid cells must be integer ARC colors 0..9 (not bool)")
        return errors
    if all(value == 0 for row in grid for value in row):
        errors.append("grid has no nonzero components")
        return errors
    if any(value == 8 for row in grid for value in row):
        errors.append("input uses reserved output color 8")

    components = _components_4conn(grid)
    colors = [color for color, _ in components]
    if len(colors) != len(set(colors)):
        errors.append("a source color appears in more than one disconnected component")
    if not any(_is_flat(cells) for _, cells in components):
        errors.append("no constant-row-profile component found")
    if not any(not _is_flat(cells) for _, cells in components):
        errors.append("no varying-row-profile component found")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, lawful, shortcut-refuting input grid."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    dimensions = _DIMENSION_PROFILES[difficulty]
    default_height, default_width = dimensions[sample_index % len(dimensions)]
    count_profiles = _COUNT_PROFILES[difficulty]
    default_flat, default_nonflat = count_profiles[sample_index % len(count_profiles)]
    palette_schedule = _PALETTE_SCHEDULE[difficulty]
    default_palette = palette_schedule[sample_index % len(palette_schedule)]

    height = _scheduled_int(ctx, "height", 8, 16, default_height)
    width = _scheduled_int(ctx, "width", 11, 18, default_width)
    flat_count = _scheduled_int(ctx, "flat_component_count", 1, 3, default_flat)
    nonflat_count = _scheduled_int(
        ctx, "nonflat_component_count", 1, 2, default_nonflat
    )
    palette_kind = _scheduled_choice(
        ctx, "palette_kind", PALETTE_KINDS, default_palette
    )

    shapes = _choose_shapes(ctx, flat_count, nonflat_count)
    colors = _source_colors(ctx, palette_kind, len(shapes))
    grid = _pack_components(
        height,
        width,
        list(zip(shapes, colors, strict=True)),
        ctx.draw_rng("layout"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    if not _nonrectangular_flat_profile(grid):
        raise RuntimeError("constructed lesson does not refute rectangle-only shortcut")
    return grid
