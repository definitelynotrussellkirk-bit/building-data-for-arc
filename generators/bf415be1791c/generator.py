"""Generator for arc_additional_puzzle_bank_volume23:E158.

A full-height gray (5) column is the mirror axis. Every magenta (6) cell
left of it is copied to the reflected empty cell and painted cyan (8).
All source cells, the divider, background, and unrelated colored distractors
remain unchanged.

The canonical demonstrations contain one connected magenta object of four to
six cells, so they also fit component-selection shortcuts such as "mirror only
the largest component", "ignore components smaller than two/three/four cells",
or "ignore components larger than six cells". Ordinary lessons therefore
alternate mixed-size sources containing 7-, 2-, and 1-cell components with
canonical-scale sources. Left-side distractors with empty mirrors separately
rebut "reflect every colored cell".
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf415be1791c"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "7d82bc36a98b"

SUMMARY = (
    "A full-height gray divider separates a magenta source from empty mirror "
    "destinations. Copy every magenta cell across the divider as cyan while "
    "preserving all source cells and unrelated colored distractors. Generated "
    "lessons include singleton, two-cell, and oversized magenta components in "
    "the same inputs plus a left distractor whose mirror remains blank, "
    "refuting canonical-fitting component-size and reflect-all shortcuts."
)

INVARIANTS = [
    "background is 0 and cyan 8 is absent from the input",
    "exactly one full-height gray 5 divider exists and no other gray cells occur",
    "all magenta 6 source cells lie left of the divider",
    "every magenta reflection is in bounds and initially background",
    "ordinary draws contain 2..4 distractor colors and preserve an empty mirror for a left distractor",
    "every four-profile window has two mixed 7/2/1 component witnesses",
    "the eight-profile schedule also includes canonical-scale one- and multi-component sources",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "9..13",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "12..16",
    },
    "divider_col": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "5..8",
    },
    "n_magenta": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "4..10",
    },
    "n_components": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "1..3",
    },
    "n_distractor_cells": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "4..10",
    },
    "n_distractor_colors": {
        "type": "int",
        "default": "eight-profile schedule",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))

_AXIS_RANGES = {
    "grid_h": (9, 13),
    "grid_w": (12, 16),
    "divider_col": (5, 8),
    "n_magenta": (4, 10),
    "n_components": (1, 3),
    "n_distractor_cells": (4, 10),
    "n_distractor_colors": (2, 4),
}

# These profiles retain canonical dimensions/palettes while exercising all
# public extrema. The alternating W,N pattern makes each W input contain
# component sizes 7, 2, and 1. Any four consecutive draws therefore contain two
# mixed-size witnesses; after any query holdout, a demonstration still rebuts
# lower- and upper-size threshold shortcuts at once.
_PROFILES = (
    {
        "grid_h": 10,
        "grid_w": 12,
        "divider_col": 6,
        "n_magenta": 10,
        "n_components": 3,
        "component_sizes": (7, 2, 1),
        "n_distractor_cells": 4,
        "n_distractor_colors": 2,
    },
    {
        "grid_h": 10,
        "grid_w": 15,
        "divider_col": 6,
        "n_magenta": 5,
        "n_components": 2,
        "n_distractor_cells": 5,
        "n_distractor_colors": 2,
    },
    {
        "grid_h": 9,
        "grid_w": 14,
        "divider_col": 8,
        "n_magenta": 10,
        "n_components": 3,
        "component_sizes": (7, 2, 1),
        "n_distractor_cells": 4,
        "n_distractor_colors": 2,
    },
    {
        "grid_h": 9,
        "grid_w": 12,
        "divider_col": 5,
        "n_magenta": 4,
        "n_components": 1,
        "n_distractor_cells": 4,
        "n_distractor_colors": 2,
    },
    {
        "grid_h": 13,
        "grid_w": 16,
        "divider_col": 8,
        "n_magenta": 10,
        "n_components": 3,
        "component_sizes": (7, 2, 1),
        "n_distractor_cells": 10,
        "n_distractor_colors": 4,
    },
    {
        "grid_h": 11,
        "grid_w": 14,
        "divider_col": 7,
        "n_magenta": 8,
        "n_components": 2,
        "n_distractor_cells": 8,
        "n_distractor_colors": 3,
    },
    {
        "grid_h": 12,
        "grid_w": 16,
        "divider_col": 7,
        "n_magenta": 10,
        "n_components": 3,
        "component_sizes": (7, 2, 1),
        "n_distractor_cells": 6,
        "n_distractor_colors": 3,
    },
    {
        "grid_h": 10,
        "grid_w": 13,
        "divider_col": 5,
        "n_magenta": 6,
        "n_components": 2,
        "n_distractor_cells": 6,
        "n_distractor_colors": 2,
    },
)

_DISTRACTOR_COLORS = (1, 2, 3, 4, 7, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the finite semantic schedule residue for review tooling."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return sample_index % LESSON_SCHEDULE_PERIOD


def _validate_controls(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(
                f"override {name!r}={value!r} outside [{lo}, {hi}]"
            )


def _draw_axis(ctx, overrides: dict[str, Any], name: str, scheduled: int) -> int:
    lo, hi = _AXIS_RANGES[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # Record scheduled defaults through the same typed provenance API without
    # allowing keyed randomness to erase the finite curriculum ordering.
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _balanced_sizes(total: int, parts: int, rng) -> list[int]:
    base, remainder = divmod(total, parts)
    sizes = [base + (index < remainder) for index in range(parts)]
    rng.shuffle(sizes)
    return sizes


def _snake(size: int, width: int) -> tuple[tuple[int, int], ...]:
    """A connected exact-size row snake rooted at (0, 0)."""
    cells = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        cells.append((row, col))
    return tuple(cells)


def _source_cells(
    *,
    height: int,
    width: int,
    divider: int,
    n_magenta: int,
    n_components: int,
    component_sizes: tuple[int, ...] | None,
    rng,
) -> set[tuple[int, int]]:
    """Construct exact disconnected, connected components in mirrorable space."""
    left_min = max(0, 2 * divider - (width - 1))
    span = divider - left_min
    if span <= 0:
        raise ValueError("divider leaves no mirrorable source columns")

    if component_sizes is None:
        sizes = _balanced_sizes(n_magenta, n_components, rng)
    else:
        sizes = list(component_sizes)
        if (
            len(sizes) != n_components
            or sum(sizes) != n_magenta
            or any(type(size) is not int or size <= 0 for size in sizes)
        ):
            raise ValueError("scheduled component sizes contradict public counts")
        rng.shuffle(sizes)

    shapes: list[tuple[tuple[int, int], ...]] = []
    heights: list[int] = []
    for size in sizes:
        shape_width = min(span, size)
        shape = _snake(size, shape_width)
        shapes.append(shape)
        heights.append(max(row for row, _ in shape) + 1)

    required_height = sum(heights) + (n_components - 1)
    if required_height > height:
        raise ValueError(
            "requested source component geometry does not fit the grid height"
        )

    top = rng.randrange(height - required_height + 1)
    cells: set[tuple[int, int]] = set()
    row_cursor = top
    for shape, shape_height in zip(shapes, heights):
        shape_width = max(col for _, col in shape) + 1
        col_offset = left_min + rng.randrange(span - shape_width + 1)
        placed = {
            (row_cursor + row, col_offset + col) for row, col in shape
        }
        cells.update(placed)
        row_cursor += shape_height + 1

    if len(cells) != n_magenta:
        raise RuntimeError("internal source constructor lost cells")
    return cells


def _distractor_positions(
    *,
    height: int,
    width: int,
    divider: int,
    source: set[tuple[int, int]],
    mirror_targets: set[tuple[int, int]],
    count: int,
    rng,
) -> tuple[list[tuple[int, int]], tuple[int, int]]:
    """Choose exact positions and reserve one blank mirror as a teaching cue."""
    occupied = set(source) | set(mirror_targets)
    occupied.update((row, divider) for row in range(height))

    left_min = max(0, 2 * divider - (width - 1))
    left_candidates = [
        (row, col)
        for row in range(height)
        for col in range(left_min, divider)
        if (row, col) not in occupied
        and (row, 2 * divider - col) not in occupied
    ]
    if not left_candidates:
        raise RuntimeError("no legal left distractor witness position")
    left_anchor = rng.choice(left_candidates)
    protected_mirror = (left_anchor[0], 2 * divider - left_anchor[1])

    right_candidates = [
        (row, col)
        for row in range(height)
        for col in range(divider + 1, width)
        if (row, col) not in occupied and (row, col) != protected_mirror
    ]
    if not right_candidates:
        raise RuntimeError("no legal right distractor position")
    right_anchor = rng.choice(right_candidates)

    chosen = [left_anchor, right_anchor]
    forbidden = occupied | {left_anchor, right_anchor, protected_mirror}
    remaining = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in forbidden
    ]
    needed = count - len(chosen)
    if needed < 0 or needed > len(remaining):
        raise ValueError("requested distractor count does not fit the grid")
    chosen.extend(rng.sample(remaining, needed))
    rng.shuffle(chosen)
    return chosen, left_anchor


def _paint_distractors(
    grid: list[list[int]],
    *,
    positions: list[tuple[int, int]],
    n_colors: int,
    palette_rng,
    assignment_rng,
) -> None:
    palette = list(palette_rng.sample(_DISTRACTOR_COLORS, n_colors))
    colors = list(palette)
    while len(colors) < len(positions):
        colors.append(assignment_rng.choice(palette))
    assignment_rng.shuffle(colors)
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color


def _shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _DIR4:
                point = row + drow, col + dcol
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return sorted(result, key=lambda part: (min(part), len(part)))


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "grid_h": None,
        "grid_w": None,
        "divider_col": None,
        "magenta": set(),
        "components": [],
        "distractors": [],
        "distractor_colors": set(),
        "left_distractor_empty_mirrors": [],
    }
    shape = _shape(grid)
    if shape is None:
        result["errors"].append("grid must be a nonempty rectangular list of rows")
        return result
    height, width = shape
    result["grid_h"] = height
    result["grid_w"] = width

    invalid_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid_cells:
        row, col, value = invalid_cells[0]
        result["errors"].append(
            f"cell ({row},{col})={value!r} is not an ARC integer color 0..9"
        )
        return result

    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(dividers) != 1:
        result["errors"].append(
            f"expected exactly one full-height gray divider, found {len(dividers)}"
        )
        return result
    divider = dividers[0]
    result["divider_col"] = divider

    if any(
        value == 5 and col != divider
        for row in range(height)
        for col, value in enumerate(grid[row])
    ):
        result["errors"].append("gray 5 may occur only in the divider column")
    if not any(value == 0 for row in grid for value in row):
        result["errors"].append("background color 0 must be present")
    if any(value == 8 for row in grid for value in row):
        result["errors"].append("cyan 8 is reserved for the output and absent from input")

    magenta = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    }
    result["magenta"] = magenta
    result["components"] = _components(magenta)
    if not magenta:
        result["errors"].append("at least one magenta source cell is required")
    for row, col in sorted(magenta):
        if col >= divider:
            result["errors"].append("all magenta source cells must lie left of divider")
            break
        mirror_col = 2 * divider - col
        if not 0 <= mirror_col < width:
            result["errors"].append("every magenta reflection must remain in bounds")
            break
        if grid[row][mirror_col] != 0:
            result["errors"].append(
                "every magenta reflection target must initially be background"
            )
            break

    distractors = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5, 6, 8)
    ]
    result["distractors"] = distractors
    result["distractor_colors"] = {value for _, _, value in distractors}
    if not distractors:
        result["errors"].append("at least one unrelated colored distractor is required")

    witnesses = []
    for row, col, value in distractors:
        if col >= divider:
            continue
        mirror_col = 2 * divider - col
        if 0 <= mirror_col < width and grid[row][mirror_col] == 0:
            witnesses.append((row, col, mirror_col, value))
    result["left_distractor_empty_mirrors"] = witnesses
    return result


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Expose rule-relevant facts using only the visible grid."""
    facts = _analysis(grid)
    return {
        "errors": list(facts["errors"]),
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "divider_col": facts["divider_col"],
        "n_magenta": len(facts["magenta"]),
        "n_components": len(facts["components"]),
        "component_sizes": sorted(len(part) for part in facts["components"]),
        "n_distractor_cells": len(facts["distractors"]),
        "n_distractor_colors": len(facts["distractor_colors"]),
        "left_distractor_has_empty_mirror": bool(
            facts["left_distractor_empty_mirrors"]
        ),
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    facts = semantic_observables(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {name: int(facts[name]) for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if name in AXES and expected is not None and observed[name] != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical grammar and the declared constructive extension."""
    facts = semantic_observables(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    strict_ranges = {
        "grid_h": (9, 13),
        "grid_w": (12, 16),
        "divider_col": (5, 8),
        "n_magenta": (4, 10),
        "n_components": (1, 3),
        # Canonical examples include one distractor color and as few as two
        # distractor cells; ordinary generated inputs intentionally use more.
        "n_distractor_cells": (1, 10),
        "n_distractor_colors": (1, 4),
    }
    for name, (lo, hi) in strict_ranges.items():
        value = facts[name]
        if not lo <= value <= hi:
            errors.append(f"{name}={value} outside strict range {lo}..{hi}")
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    divider = int(facts["divider_col"])
    output = deepcopy(grid)
    for row, col in facts["magenta"]:
        mirror_col = 2 * divider - col
        if output[row][mirror_col] == 0:
            output[row][mirror_col] = 8
    return output


def _largest_magenta_component_only(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    components = facts["components"]
    selected = sorted(components, key=lambda cells: (-len(cells), min(cells)))[0]
    divider = int(facts["divider_col"])
    output = deepcopy(grid)
    for row, col in selected:
        mirror_col = 2 * divider - col
        if output[row][mirror_col] == 0:
            output[row][mirror_col] = 8
    return output


def _components_of_size_at_least(
    grid: Any, minimum_size: int
) -> list[list[int]]:
    """Wrong canonical-fitting rule that drops smaller source components."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    divider = int(facts["divider_col"])
    output = deepcopy(grid)
    for component in facts["components"]:
        if len(component) < minimum_size:
            continue
        for row, col in component:
            mirror_col = 2 * divider - col
            if output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def _components_of_size_at_least_two(grid: Any) -> list[list[int]]:
    return _components_of_size_at_least(grid, 2)


def _components_of_size_at_least_three(grid: Any) -> list[list[int]]:
    return _components_of_size_at_least(grid, 3)


def _components_of_size_at_least_four(grid: Any) -> list[list[int]]:
    return _components_of_size_at_least(grid, 4)


def _components_of_size_at_most(
    grid: Any, maximum_size: int
) -> list[list[int]]:
    """Wrong canonical-fitting rule that drops oversized source components."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    divider = int(facts["divider_col"])
    output = deepcopy(grid)
    for component in facts["components"]:
        if len(component) > maximum_size:
            continue
        for row, col in component:
            mirror_col = 2 * divider - col
            if output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def _components_of_size_at_most_six(grid: Any) -> list[list[int]]:
    return _components_of_size_at_most(grid, 6)


def _reflect_every_colored_left_cell(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    divider = int(facts["divider_col"])
    width = int(facts["grid_w"])
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col in range(divider):
            if values[col] == 0:
                continue
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < width and output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def _move_magenta_instead_of_copying(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    divider = int(facts["divider_col"])
    output = deepcopy(grid)
    for row, col in facts["magenta"]:
        output[row][col] = 0
        mirror_col = 2 * divider - col
        if output[row][mirror_col] == 0:
            output[row][mirror_col] = 8
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "largest_magenta_component_only": _largest_magenta_component_only,
    "components_of_size_at_least_two": _components_of_size_at_least_two,
    "components_of_size_at_least_three": _components_of_size_at_least_three,
    "components_of_size_at_least_four": _components_of_size_at_least_four,
    "components_of_size_at_most_six": _components_of_size_at_most_six,
    "reflect_every_colored_left_cell": _reflect_every_colored_left_cell,
    "move_magenta_instead_of_copying": _move_magenta_instead_of_copying,
}
CANONICAL_SHORTCUTS = {
    "largest_magenta_component_only": _largest_magenta_component_only,
    "components_of_size_at_least_two": _components_of_size_at_least_two,
    "components_of_size_at_least_three": _components_of_size_at_least_three,
    "components_of_size_at_least_four": _components_of_size_at_least_four,
    "components_of_size_at_most_six": _components_of_size_at_most_six,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_fact(grid: Any, key: str, default: Any = None) -> Any:
    facts = semantic_observables(grid)
    if facts["errors"]:
        return default
    return facts.get(key, default)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "multiple_magenta_components": lambda grid: _valid_fact(
        grid, "n_components", 0
    ) > 1,
    "singleton_magenta_component": lambda grid: 1
    in _valid_fact(grid, "component_sizes", []),
    "two_cell_magenta_component": lambda grid: 2
    in _valid_fact(grid, "component_sizes", []),
    "oversized_magenta_component": lambda grid: any(
        size > 6 for size in _valid_fact(grid, "component_sizes", [])
    ),
    "left_distractor_has_empty_mirror": lambda grid: bool(
        _valid_fact(grid, "left_distractor_has_empty_mirror", False)
    ),
    "source_is_preserved": lambda grid: _valid_fact(grid, "n_magenta", 0) > 0,
}
WITNESS_RIVALS = {
    "multiple_magenta_components": ["largest_magenta_component_only"],
    "singleton_magenta_component": [
        "components_of_size_at_least_two",
        "components_of_size_at_least_three",
        "components_of_size_at_least_four",
    ],
    "two_cell_magenta_component": [
        "components_of_size_at_least_three",
        "components_of_size_at_least_four",
    ],
    "oversized_magenta_component": ["components_of_size_at_most_six"],
    "left_distractor_has_empty_mirror": ["reflect_every_colored_left_cell"],
    "source_is_preserved": ["move_magenta_instead_of_copying"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    input_errors = self_check(pair["input"])
    if input_errors:
        return [f"{label} input invalid: {input_errors[0]}"]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} rule evaluation failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output does not follow the selected rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared rival can still alter the query answer."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and rival(query["input"]) != query["output"]:
            errors.append(f"surviving lesson shortcut: {name}")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local invalid near-misses for generic validator probes."""
    grid = generate(991, 0, difficulty="easy")
    divider = observe_overrides(grid)["divider_col"]

    broken_divider = deepcopy(grid)
    broken_divider[0][divider] = 0

    occupied_target = deepcopy(grid)
    row, col = min(_analysis(grid)["magenta"])
    occupied_target[row][2 * divider - col] = 2

    cyan_input = deepcopy(grid)
    for row, values in enumerate(cyan_input):
        for col, value in enumerate(values):
            if value == 0:
                cyan_input[row][col] = 8
                break
        else:
            continue
        break

    return [
        ("broken_divider", broken_divider),
        ("occupied_mirror_target", occupied_target),
        ("cyan_in_input", cyan_input),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful, deterministic input with exact public controls."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    profile = _PROFILES[schedule_profile(seed, sample_index, difficulty)]
    band = difficulty or "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    values = {
        name: _draw_axis(ctx, overrides, name, int(profile[name]))
        for name in AXES
    }
    height = values["grid_h"]
    width = values["grid_w"]
    divider = values["divider_col"]

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 5

    source = _source_cells(
        height=height,
        width=width,
        divider=divider,
        n_magenta=values["n_magenta"],
        n_components=values["n_components"],
        component_sizes=(
            None
            if overrides.get("n_magenta") is not None
            or overrides.get("n_components") is not None
            else profile.get("component_sizes")
        ),
        rng=ctx.draw_rng(f"source_layout:{band}"),
    )
    for row, col in source:
        grid[row][col] = 6

    mirror_targets = {(row, 2 * divider - col) for row, col in source}
    positions, left_anchor = _distractor_positions(
        height=height,
        width=width,
        divider=divider,
        source=source,
        mirror_targets=mirror_targets,
        count=values["n_distractor_cells"],
        rng=ctx.draw_rng(f"distractor_positions:{band}"),
    )
    _paint_distractors(
        grid,
        positions=positions,
        n_colors=values["n_distractor_colors"],
        palette_rng=ctx.draw_rng(f"distractor_palette:{band}"),
        assignment_rng=ctx.draw_rng(f"distractor_assignment:{band}"),
    )

    # Guard the constructive proof in executable form. These checks should be
    # unreachable for validated controls, but turn future refactors into loud
    # failures rather than silently dishonest overrides.
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": values})
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors[0]}")
    observed = observe_overrides(grid)
    if observed != values:
        raise RuntimeError(
            f"internal override mismatch: requested {values!r}, observed {observed!r}"
        )
    mirror_col = 2 * divider - left_anchor[1]
    if grid[left_anchor[0]][mirror_col] != 0:
        raise RuntimeError("left distractor witness mirror was not preserved")
    return grid
