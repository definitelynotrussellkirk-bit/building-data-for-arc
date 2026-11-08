"""Generator for ``arc_puzzle_bank_21_set3:S3_M7`` — pivot rotation.

The first color-6 cell in row-major order is the pivot.  Rebuild an empty
canvas, keep that pivot, and rotate every non-{0,6} input cell 90 degrees
clockwise around it.  Rotated cells outside the canvas are clipped.  Any later
color-6 cells are distractors: they are neither rotated nor repainted.

The five-slot schedule is lesson-level.  Every five consecutive generated
examples contain a canonical/plain anchor, partial clipping, multiple objects,
per-cell multicolor preservation, and a later color-6 distractor.  Together
those examples refute the strongest canonical-compatible shortcut rules.
"""
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Point = tuple[int, int]

GENERATOR_ID = "0ba6a62312d0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4a2f94aea981"

SUMMARY = (
    "Use the first color-6 cell in row-major order as the pivot. Rebuild an "
    "empty canvas, keep that pivot, and rotate every non-{0,6} cell 90 degrees "
    "clockwise around it. Clip rotated cells that leave the canvas. Later "
    "color-6 cells vanish. Every five consecutive generated examples include "
    "plain/canonical, clipping, multiple-object, multicolor, and extra-six "
    "witnesses."
)

INVARIANTS = [
    "the first row-major color-6 cell is the unique rotation pivot",
    "all non-{0,6} cells rotate clockwise with their individual colors preserved",
    "rotated cells outside the unchanged canvas are clipped cell-by-cell",
    "later isolated color-6 distractors vanish rather than rotate or survive",
    "ordinary five-example windows cover every decisive teaching profile",
    "the Racket rule is the sole output authority; rule_mirror is test-only parity logic",
]

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.15

TEXTURES = ("plain", "clip", "multi_object", "multicolor", "extra_six")
SCHEDULE_PROFILES = TEXTURES
_COLORS = (1, 2, 3, 4, 5, 7, 8, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-band draw",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-band draw",
        "valid": "6..16",
    },
    "texture": {
        "type": "str",
        "default": "five-slot schedule",
        "valid": "plain|clip|multi_object|multicolor|extra_six",
        "doc": (
            "plain is a fully visible monochrome object; clip loses some but "
            "not all rotated cells; multi_object rotates two separated objects; "
            "multicolor preserves cell colors; extra_six adds a later isolated "
            "6 that vanishes"
        ),
    },
}

# Every Cartesian combination of the declared exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Data-derived linked profiles from the three canonical inputs.  The final four
# fields are (cell_count, bbox_h, bbox_w, bbox_area_minus_cells).
_CANONICAL_LINKED_PROFILES = {
    (9, 9, 3, 2, 2, 1),
    (10, 10, 4, 2, 3, 2),
    (11, 11, 4, 3, 2, 2),
}

# Exact canonical-anchor templates.  Colors are varied, but dimensions, pivot,
# and relative morphology preserve each linked empirical profile.
_CANONICAL_TEMPLATES: tuple[tuple[int, int, Point, tuple[Point, ...]], ...] = (
    (9, 9, (4, 4), ((-2, -2), (-2, -1), (-1, -2))),
    (10, 10, (5, 4), ((-2, -2), (-1, -2), (-1, -1), (-1, 0))),
    (11, 11, (6, 5), ((-3, -1), (-2, -1), (-2, 0), (-1, -1))),
)

# Compact connected shapes used for generalized scenes.  D4 variants are
# derived at runtime; no literal output is stored in the generator.
_SHAPE_BANK: tuple[tuple[Point, ...], ...] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the semantic schedule slot for a sample."""
    del seed, difficulty
    return TEXTURES[int(sample_index) % len(TEXTURES)]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _positions(grid: Sequence[Sequence[int]], value: int) -> list[Point]:
    return [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, cell in enumerate(row)
        if cell == value
    ]


def _non_six_cells(grid: Sequence[Sequence[int]]) -> list[Point]:
    return [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value not in (0, 6)
    ]


def _components(grid: Sequence[Sequence[int]]) -> list[list[Point]]:
    """4-connected components of all non-{0,6} cells, ignoring their colors."""
    remaining = set(_non_six_cells(grid))
    components: list[list[Point]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue: deque[Point] = deque([start])
        component: list[Point] = []
        while queue:
            row, column = queue.popleft()
            component.append((row, column))
            for point in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    queue.append(point)
        components.append(sorted(component))
    return components


def _rotate(point: Point, pivot: Point) -> Point:
    row, column = point
    pivot_row, pivot_column = pivot
    return (
        pivot_row + (column - pivot_column),
        pivot_column - (row - pivot_row),
    )


def _in_bounds(point: Point, height: int, width: int) -> bool:
    return 0 <= point[0] < height and 0 <= point[1] < width


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; Racket remains authoritative."""
    height, width = len(grid), len(grid[0])
    sixes = _positions(grid, 6)
    if not sixes:
        raise ValueError("the Racket rule requires at least one color-6 cell")
    pivot = sixes[0]
    out = full_grid(height, width, 0)
    out[pivot[0]][pivot[1]] = 6
    for row, column in _non_six_cells(grid):
        rotated = _rotate((row, column), pivot)
        if _in_bounds(rotated, height, width):
            out[rotated[0]][rotated[1]] = int(grid[row][column])
    return out


def _shape_signature(cells: Sequence[Point]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    bbox_height = max(rows) - min(rows) + 1
    bbox_width = max(columns) - min(columns) + 1
    return (
        len(cells),
        bbox_height,
        bbox_width,
        bbox_height * bbox_width - len(cells),
    )


def _texture_of(grid: Sequence[Sequence[int]]) -> str:
    height, width = len(grid), len(grid[0])
    sixes = _positions(grid, 6)
    pivot = sixes[0]
    cells = _non_six_cells(grid)
    surviving = sum(_in_bounds(_rotate(point, pivot), height, width) for point in cells)
    if len(sixes) > 1:
        return "extra_six"
    if surviving < len(cells):
        return "clip"
    components = _components(grid)
    if len(components) > 1:
        return "multi_object"
    colors = {grid[row][column] for row, column in cells}
    if len(colors) > 1:
        return "multicolor"
    return "plain"


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "texture": _texture_of(grid),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, degenerate, ambiguous, and rule-hiding scenes."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 6 <= height <= 16:
        errors.append(f"height {height} outside declared envelope 6..16")
    if not 6 <= width <= 16:
        errors.append(f"width {width} outside declared envelope 6..16")

    sixes = _positions(grid, 6)
    if len(sixes) not in (1, 2):
        errors.append(f"expected one pivot and at most one distractor 6, found {len(sixes)}")
    if not sixes:
        return errors
    for row, column in sixes:
        if any(
            0 <= neighbor_row < height
            and 0 <= neighbor_column < width
            and grid[neighbor_row][neighbor_column] == 6
            for neighbor_row, neighbor_column in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            )
        ):
            errors.append("every color-6 marker must be a singleton")
            break

    cells = _non_six_cells(grid)
    if len(cells) < 3:
        errors.append(f"need at least three non-{{0,6}} cells, found {len(cells)}")
        return errors
    components = _components(grid)
    if len(components) > 3:
        errors.append(f"at most three non-{{0,6}} components are supported, found {len(components)}")
    if len(components) > 1 and any(len(component) < 2 for component in components):
        errors.append("multi-object scenes may not use singleton shortcut objects")

    pivot = sixes[0]
    rotated = [_rotate(point, pivot) for point in cells]
    surviving = [point for point in rotated if _in_bounds(point, height, width)]
    if not surviving:
        errors.append("all rotated object cells leave the canvas")
        return errors
    if set(surviving) == set(cells) and len(surviving) == len(cells):
        errors.append("the scene is 90-degree invariant and hides the transformation")

    clipped = len(surviving) < len(cells)
    colors = {grid[row][column] for row, column in cells}
    if clipped and (len(components) != 1 or len(colors) != 1):
        errors.append("clipping scenes must isolate clipping from multi-object and multicolor controls")
    if len(sixes) == 2:
        if clipped or len(components) != 1 or len(colors) != 1:
            errors.append("extra-six scenes must isolate the first-pivot/vanishing-marker control")
        true_output = rule_mirror(grid)
        extra = sixes[1]
        if true_output[extra[0]][extra[1]] != 0:
            errors.append("the later 6 distractor must occupy an empty true-output cell")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Strict linked empirical manifold derived from all three canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    sixes = _positions(grid, 6)
    components = _components(grid)
    cells = _non_six_cells(grid)
    colors = {grid[row][column] for row, column in cells}
    signature = _shape_signature(cells)
    linked = (height, width, *signature)
    if len(sixes) != 1:
        reasons.append("canonical inputs have exactly one color-6 pivot")
    if len(components) != 1:
        reasons.append("canonical inputs have exactly one non-pivot object")
    if len(colors) != 1:
        reasons.append("canonical inputs have a monochrome object")
    if linked not in _CANONICAL_LINKED_PROFILES:
        reasons.append(f"linked profile {linked} is not one of the three canonical profiles")
    pivot_row, pivot_column = sixes[0]
    if not all(row < pivot_row and column <= pivot_column for row, column in cells):
        reasons.append("canonical objects lie wholly north and not east of the pivot")
    if not any(column < pivot_column for _, column in cells):
        reasons.append("canonical objects extend strictly west of the pivot")
    return reasons


def _base_output(grid: Sequence[Sequence[int]], pivot: Point) -> Grid:
    out = full_grid(len(grid), len(grid[0]), 0)
    out[pivot[0]][pivot[1]] = 6
    return out


def _paint_rotated_cells(
    grid: Sequence[Sequence[int]],
    pivot: Point,
    cells: Sequence[Point],
    *,
    force_color: int | None = None,
) -> Grid:
    height, width = len(grid), len(grid[0])
    out = _base_output(grid, pivot)
    for row, column in cells:
        rotated = _rotate((row, column), pivot)
        if _in_bounds(rotated, height, width):
            out[rotated[0]][rotated[1]] = (
                force_color if force_color is not None else int(grid[row][column])
            )
    return out


def _rival_first_component_only(grid: Sequence[Sequence[int]]) -> Grid:
    pivot = _positions(grid, 6)[0]
    return _paint_rotated_cells(grid, pivot, _components(grid)[0])


def _rival_modal_color(grid: Sequence[Sequence[int]]) -> Grid:
    pivot = _positions(grid, 6)[0]
    cells = _non_six_cells(grid)
    counts = Counter(int(grid[row][column]) for row, column in cells)
    modal = min(counts, key=lambda color: (-counts[color], color))
    return _paint_rotated_cells(grid, pivot, cells, force_color=modal)


def _rival_preserve_all_sixes(grid: Sequence[Sequence[int]]) -> Grid:
    out = rule_mirror(grid)
    for row, column in _positions(grid, 6):
        out[row][column] = 6
    return out


def _rival_all_or_nothing_clip(grid: Sequence[Sequence[int]]) -> Grid:
    height, width = len(grid), len(grid[0])
    pivot = _positions(grid, 6)[0]
    out = _base_output(grid, pivot)
    for component in _components(grid):
        rotated = [_rotate(point, pivot) for point in component]
        if all(_in_bounds(point, height, width) for point in rotated):
            for source, target in zip(component, rotated, strict=True):
                out[target[0]][target[1]] = int(grid[source[0]][source[1]])
    return out


def _rival_last_six_pivot(grid: Sequence[Sequence[int]]) -> Grid:
    pivot = _positions(grid, 6)[-1]
    return _paint_rotated_cells(grid, pivot, _non_six_cells(grid))


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "rotate_only_first_non6_component": _rival_first_component_only,
    "collapse_object_to_modal_color": _rival_modal_color,
    "preserve_every_color6_marker": _rival_preserve_all_sixes,
    "discard_whole_component_when_any_cell_clips": _rival_all_or_nothing_clip,
    "use_last_color6_as_pivot": _rival_last_six_pivot,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_texture(grid: Any, texture: str) -> bool:
    return not self_check(grid) and _texture_of(grid) == texture


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    if self_check(grid):
        return False
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "partial_cellwise_clipping": lambda grid: _valid_and_refutes(
        grid, "discard_whole_component_when_any_cell_clips"
    ),
    "all_non6_components_rotate": lambda grid: _valid_and_refutes(
        grid, "rotate_only_first_non6_component"
    ),
    "per_cell_colors_are_preserved": lambda grid: _valid_and_refutes(
        grid, "collapse_object_to_modal_color"
    ),
    "first_six_pivot_later_six_vanishes": lambda grid: (
        _valid_texture(grid, "extra_six")
        and _valid_and_refutes(grid, "preserve_every_color6_marker")
        and _valid_and_refutes(grid, "use_last_color6_as_pivot")
    ),
}

WITNESS_RIVALS = {
    "partial_cellwise_clipping": [
        "discard_whole_component_when_any_cell_clips"
    ],
    "all_non6_components_rotate": ["rotate_only_first_non6_component"],
    "per_cell_colors_are_preserved": ["collapse_object_to_modal_color"],
    "first_six_pivot_later_six_vanishes": [
        "preserve_every_color6_marker",
        "use_last_color6_as_pivot",
    ],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require five exact demos that expose all profiles and kill every rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    seen_textures: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_grid = pair["input"]
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        seen_textures.add(_texture_of(input_grid))
        if rule_mirror(input_grid) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")

    missing = sorted(set(TEXTURES) - seen_textures)
    if missing:
        reasons.append(f"demonstrations miss teaching profile(s): {missing}")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def _normalize_shape(shape: Sequence[Point]) -> tuple[Point, ...]:
    min_row = min(row for row, _ in shape)
    min_column = min(column for _, column in shape)
    return tuple(sorted((row - min_row, column - min_column) for row, column in shape))


def _shape_variants(shape: Sequence[Point]) -> tuple[tuple[Point, ...], ...]:
    variants: set[tuple[Point, ...]] = set()
    current = list(shape)
    for _ in range(4):
        variants.add(_normalize_shape(current))
        variants.add(_normalize_shape([(row, -column) for row, column in current]))
        current = [(column, -row) for row, column in current]
    return tuple(sorted(variants))


def _central_pivot(point: Point, height: int, width: int) -> bool:
    return abs(2 * point[0] - (height - 1)) <= 1 and abs(
        2 * point[1] - (width - 1)
    ) <= 1


def _single_candidates(
    height: int,
    width: int,
    shape: Sequence[Point],
    *,
    clip: bool,
    prefer_off_center: bool,
    require_later_empty: bool = False,
) -> list[tuple[Point, tuple[Point, ...]]]:
    candidates: list[tuple[Point, tuple[Point, ...]]] = []
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(column for _, column in shape) + 1
    for pivot_row in range(height):
        for pivot_column in range(width):
            pivot = (pivot_row, pivot_column)
            if prefer_off_center and _central_pivot(pivot, height, width):
                continue
            for row0 in range(height - shape_height + 1):
                for column0 in range(width - shape_width + 1):
                    cells = tuple(
                        (row0 + row, column0 + column) for row, column in shape
                    )
                    if pivot in cells:
                        continue
                    rotated = tuple(_rotate(point, pivot) for point in cells)
                    survivors = tuple(
                        point for point in rotated if _in_bounds(point, height, width)
                    )
                    if clip:
                        if not 0 < len(survivors) < len(cells):
                            continue
                    elif len(survivors) != len(cells):
                        continue
                    if len(survivors) == len(cells) and set(survivors) == set(cells):
                        continue
                    if require_later_empty:
                        occupied = set(cells) | set(survivors) | {pivot}
                        has_later_empty = any(
                            (row, column) > pivot
                            and (row, column) not in occupied
                            and abs(row - pivot[0]) + abs(column - pivot[1]) > 1
                            for row in range(height)
                            for column in range(width)
                        )
                        if not has_later_empty:
                            continue
                    candidates.append((pivot, cells))
    return candidates


def _choose_single_scene(
    height: int,
    width: int,
    rng: Any,
    *,
    clip: bool = False,
    minimum_cells: int = 3,
    require_later_empty: bool = False,
) -> tuple[Point, tuple[Point, ...]]:
    banks = [shape for shape in _SHAPE_BANK if len(shape) >= minimum_cells]
    rng.shuffle(banks)
    for prefer_off_center in (True, False):
        for base_shape in banks:
            variants = list(_shape_variants(base_shape))
            rng.shuffle(variants)
            for shape in variants:
                candidates = _single_candidates(
                    height,
                    width,
                    shape,
                    clip=clip,
                    prefer_off_center=prefer_off_center,
                    require_later_empty=require_later_empty,
                )
                if candidates:
                    return candidates[rng.randrange(len(candidates))]
    raise ValueError(f"could not place {'clipped' if clip else 'visible'} object")


def _nonadjacent(first: Sequence[Point], second: Sequence[Point]) -> bool:
    first_set = set(first)
    for row, column in second:
        if (row, column) in first_set:
            return False
        if any(
            point in first_set
            for point in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            )
        ):
            return False
    return True


def _choose_multi_scene(
    height: int, width: int, rng: Any
) -> tuple[Point, tuple[Point, ...], tuple[Point, ...]]:
    shapes = (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0), (1, 1)),
    )
    pivots = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if not _central_pivot((row, column), height, width)
    ]
    rng.shuffle(pivots)
    for pivot in pivots:
        placement_sets: list[list[tuple[Point, ...]]] = []
        for shape in shapes:
            placements: list[tuple[Point, ...]] = []
            for variant in _shape_variants(shape):
                shape_height = max(row for row, _ in variant) + 1
                shape_width = max(column for _, column in variant) + 1
                for row0 in range(height - shape_height + 1):
                    for column0 in range(width - shape_width + 1):
                        cells = tuple(
                            (row0 + row, column0 + column) for row, column in variant
                        )
                        if pivot in cells:
                            continue
                        rotated = [_rotate(point, pivot) for point in cells]
                        if all(_in_bounds(point, height, width) for point in rotated):
                            placements.append(cells)
            rng.shuffle(placements)
            placement_sets.append(placements)
        for first in placement_sets[0]:
            for second in placement_sets[1]:
                if _nonadjacent(first, second):
                    all_cells = tuple(first) + tuple(second)
                    rotated = {_rotate(point, pivot) for point in all_cells}
                    if rotated != set(all_cells):
                        return pivot, tuple(first), tuple(second)
    raise ValueError("could not place two separated rotating objects")


def _draw_dimensions(ctx: Any, difficulty: Any) -> tuple[int, int]:
    if difficulty == "easy":
        bounds = (6, 9)
    elif difficulty == "hard":
        bounds = (11, 16)
    else:
        bounds = (8, 12)
    height = ctx.draw_int(
        "grid_h", 6, 16
    ) if ctx.overrides.get("grid_h") is not None else ctx.draw_int(
        "grid_h", *bounds
    )
    width = ctx.draw_int(
        "grid_w", 6, 16
    ) if ctx.overrides.get("grid_w") is not None else ctx.draw_int(
        "grid_w", *bounds
    )
    return height, width


def _canonical_template_for_difficulty(ctx: Any, difficulty: Any):
    if difficulty == "easy":
        return _CANONICAL_TEMPLATES[0]
    if difficulty == "hard":
        return _CANONICAL_TEMPLATES[2]
    if difficulty == "medium":
        return _CANONICAL_TEMPLATES[1]
    return ctx.draw_choice("canonical_template_internal", _CANONICAL_TEMPLATES)


def _paint_scene(
    height: int,
    width: int,
    pivot: Point,
    paint_groups: Sequence[tuple[Sequence[Point], Sequence[int]]],
    *,
    extra_six: Point | None = None,
) -> Grid:
    grid = full_grid(height, width, 0)
    grid[pivot[0]][pivot[1]] = 6
    for cells, colors in paint_groups:
        for point, color in zip(cells, colors, strict=True):
            grid[point[0]][point[1]] = int(color)
    if extra_six is not None:
        grid[extra_six[0]][extra_six[1]] = 6
    return grid


def _extra_six_candidate(
    grid: Sequence[Sequence[int]], pivot: Point, true_output: Sequence[Sequence[int]]
) -> list[Point]:
    height, width = len(grid), len(grid[0])
    return [
        (row, column)
        for row in range(height)
        for column in range(width)
        if (row, column) > pivot
        and grid[row][column] == 0
        and true_output[row][column] == 0
        and abs(row - pivot[0]) + abs(column - pivot[1]) > 1
    ]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    texture_options = TEXTURES if overrides.get("texture") is not None else (scheduled,)
    texture = str(ctx.draw_choice("texture", texture_options))
    rng = ctx.draw_rng("layout")

    use_canonical_anchor = (
        texture == "plain"
        and overrides.get("grid_h") is None
        and overrides.get("grid_w") is None
    )
    if use_canonical_anchor:
        height, width, pivot, relative_cells = _canonical_template_for_difficulty(
            ctx, difficulty
        )
        height = ctx.draw_int("grid_h", height, height)
        width = ctx.draw_int("grid_w", width, width)
        cells = tuple(
            (pivot[0] + row_delta, pivot[1] + column_delta)
            for row_delta, column_delta in relative_cells
        )
        color = rng.choice(_COLORS)
        grid = _paint_scene(
            height,
            width,
            pivot,
            ((cells, (color,) * len(cells)),),
        )
    else:
        height, width = _draw_dimensions(ctx, difficulty)
        if texture == "multi_object":
            pivot, first, second = _choose_multi_scene(height, width, rng)
            colors = rng.sample(list(_COLORS), 2)
            grid = _paint_scene(
                height,
                width,
                pivot,
                (
                    (first, (colors[0],) * len(first)),
                    (second, (colors[1],) * len(second)),
                ),
            )
        else:
            pivot, cells = _choose_single_scene(
                height,
                width,
                rng,
                clip=texture == "clip",
                minimum_cells=4 if texture == "multicolor" else 3,
                require_later_empty=texture == "extra_six",
            )
            if texture == "multicolor":
                colors = rng.sample(list(_COLORS), 2)
                painted_colors = [colors[index % 2] for index in range(len(cells))]
                rng.shuffle(painted_colors)
                # Guarantee both colors even after the shuffle.
                painted_colors[0], painted_colors[1] = colors
            else:
                color = rng.choice(_COLORS)
                painted_colors = [color] * len(cells)
            grid = _paint_scene(
                height,
                width,
                pivot,
                ((cells, tuple(painted_colors)),),
            )
            if texture == "extra_six":
                true_output = rule_mirror(grid)
                candidates = _extra_six_candidate(grid, pivot, true_output)
                if not candidates:
                    raise ValueError("could not place an observable later color-6 distractor")
                extra = candidates[rng.randrange(len(candidates))]
                grid[extra[0]][extra[1]] = 6

    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid {texture!r} scene: {errors}")
    observed = observe_overrides(grid)
    expected = {"grid_h": len(grid), "grid_w": len(grid[0]), "texture": texture}
    if observed != expected:
        raise ValueError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid
