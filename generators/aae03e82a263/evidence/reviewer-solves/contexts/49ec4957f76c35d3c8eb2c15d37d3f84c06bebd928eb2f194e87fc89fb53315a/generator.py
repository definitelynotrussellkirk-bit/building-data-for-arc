"""Generator for ARC task aae03e82a263 — transpose the median-area object.

The input is a zero-background grid with three or five separated color-6
objects whose cell areas are distinct.  Sort the objects by cell area, select
the middle one, normalize its cells, transpose the normalized coordinates, and
return the tight color-6 crop.

The five-slot curriculum retains canonical 12/13-square anchors while varying
object count and the selected cell area.  It also orders and shapes objects so
that reading order, bounding-box area, a fixed five-cell choice, and the
canonical-only "second-smallest" shortcut are all contradicted redundantly.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aae03e82a263"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "69eaaa031800"

SUMMARY = (
    "Place three or five isolated color-6 objects with distinct cell areas. "
    "Select the median-area object, transpose its normalized shape, and return "
    "the tight color-6 crop. A five-slot schedule varies count, median area, "
    "reading order, shape, position, and dimensions while retaining canonical "
    "12x12/13x13 anchors."
)

INVARIANTS = [
    "the grid contains exactly three or five mutually separated color-6 objects",
    "object cell areas are pairwise distinct, so the odd-count median is unique",
    "the output is the tight crop of the normalized median object after swapping row and column coordinates",
]

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
MIN_STRICT_FRAC = 0.15

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-skewed 12..18",
        "valid": "12|13|18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-skewed 12..18",
        "valid": "12|13|18",
    },
    "n_objects": {
        "type": "int",
        "default": "five-slot schedule",
        "valid": "3|5",
    },
    "median_size": {
        "type": "int",
        "default": "five-slot schedule",
        "valid": "4..6",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_DIMS = ((12, 12), (13, 13))
DIMENSION_VALUES = (12, 13, 18)
_SCHEDULE = (
    # n_objects, median_size, reading-order profile
    (3, 5, "ascending"),
    (5, 4, "target_last"),
    (5, 6, "target_first"),
    (3, 4, "target_last"),
    (5, 5, "target_second"),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _transpose_shape(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return _normalize((col, row) for row, col in cells)


def _shape_dimensions(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _bbox_area(shape: Sequence[tuple[int, int]]) -> int:
    height, width = _shape_dimensions(shape)
    return height * width


def _enumerate_shape_pools() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """Enumerate normalized fixed polyominoes up to eight cells in a 4x4 box."""
    pools: dict[int, set[tuple[tuple[int, int], ...]]] = {1: {((0, 0),)}}
    for size in range(2, 9):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in pools[size - 1]:
            occupied = set(shape)
            for row, col in shape:
                for drow, dcol in _CARDINAL:
                    candidate = (row + drow, col + dcol)
                    if candidate in occupied:
                        continue
                    normalized = _normalize((*shape, candidate))
                    height, width = _shape_dimensions(normalized)
                    if height <= 4 and width <= 4:
                        expanded.add(normalized)
        if not expanded:
            raise RuntimeError(f"no bounded connected shapes of size {size}")
        pools[size] = expanded
    return {size: tuple(sorted(shapes)) for size, shapes in pools.items()}


_SHAPE_POOLS = _enumerate_shape_pools()
_TARGET_POOLS = {
    size: tuple(
        shape
        for shape in _SHAPE_POOLS[size]
        if _transpose_shape(shape) != shape
        and _bbox_area(shape)
        == max(
            _bbox_area(candidate)
            for candidate in _SHAPE_POOLS[size]
            if _transpose_shape(candidate) != candidate
        )
    )
    for size in range(4, 7)
}
_COMPACT_POOLS = {
    size: tuple(
        shape
        for shape in _SHAPE_POOLS[size]
        if _bbox_area(shape) == min(_bbox_area(candidate) for candidate in _SHAPE_POOLS[size])
    )
    for size in range(2, 9)
}
if any(not pool for pool in _TARGET_POOLS.values()):
    raise RuntimeError("asymmetric target shape pool construction failed")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _components(grid: Any) -> list[dict[str, Any]]:
    """Return color-6 4-components in reading order."""
    if _validate_grid(grid):
        return []
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 6 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for drow, dcol in _CARDINAL:
                    neighbor = (current[0] + drow, current[1] + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == 6
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            cells.sort()
            row0 = min(r for r, _ in cells)
            row1 = max(r for r, _ in cells)
            col0 = min(c for _, c in cells)
            col1 = max(c for _, c in cells)
            components.append(
                {
                    "cells": tuple(cells),
                    "size": len(cells),
                    "first": cells[0],
                    "bbox": (row0, col0, row1, col1),
                    "bbox_area": (row1 - row0 + 1) * (col1 - col0 + 1),
                    "shape": _normalize(cells),
                }
            )
    components.sort(key=lambda component: component["first"])
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors, "components": []}

    height, width = len(grid), len(grid[0])
    values = {value for row in grid for value in row}
    components = _components(grid)
    sizes = [component["size"] for component in components]

    if not (12 <= height <= 18 and 12 <= width <= 18):
        errors.append(f"dims {height}x{width} outside declared envelope 12..18")
    if not values <= {0, 6}:
        errors.append(f"only colors 0 and 6 are allowed, found {sorted(values - {0, 6})}")
    if len(components) not in (3, 5):
        errors.append(f"need exactly 3 or 5 color-6 objects, found {len(components)}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"object cell areas must be distinct, got {sizes}")
    if sum(value == 0 for row in grid for value in row) <= height * width // 2:
        errors.append("zero must remain the majority background")

    owner = {
        cell: index
        for index, component in enumerate(components)
        for cell in component["cells"]
    }
    diagonal_touch = False
    for (row, col), index in owner.items():
        for drow, dcol in _NEIGHBORS_8:
            neighbor = (row + drow, col + dcol)
            if neighbor in owner and owner[neighbor] != index:
                diagonal_touch = True
                break
        if diagonal_touch:
            break
    if diagonal_touch:
        errors.append("distinct objects must have an eight-neighbor background gap")

    selected = None
    if components and len(set(sizes)) == len(sizes):
        ranked = sorted(components, key=lambda component: (component["size"], component["first"]))
        selected = ranked[len(ranked) // 2]

    reading_middle = components[len(components) // 2] if components else None
    bbox_middle = (
        sorted(components, key=lambda component: (component["bbox_area"], component["first"]))[
            len(components) // 2
        ]
        if components
        else None
    )
    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "components": components,
        "n_objects": len(components),
        "sizes": sizes,
        "selected": selected,
        "median_size": selected["size"] if selected else None,
        "median_not_reading_middle": bool(selected and reading_middle is not selected),
        "median_not_bbox_middle": bool(selected and bbox_middle is not selected),
        "selected_is_asymmetric": bool(
            selected and _transpose_shape(selected["shape"]) != selected["shape"]
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and every advertised degenerate input."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical dimensions/count/size/palette profile."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("canonical dimensions are 12x12 or 13x13")
    if analysis["n_objects"] != 3:
        reasons.append("canonical profile has exactly three objects")
    if sorted(analysis["sizes"]) != [4, 5, 6]:
        reasons.append("canonical object areas are 4, 5, and 6")
    return reasons


def canonical_profile_signature(grid) -> str | None:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    dims = (analysis["grid_h"], analysis["grid_w"])
    if dims in _CANONICAL_DIMS and analysis["n_objects"] == 3 and sorted(analysis["sizes"]) == [4, 5, 6]:
        return f"{dims[0]}x{dims[1]}-palette2-objects3-sizes4,5,6"
    return None


def observe_overrides(grid) -> dict[str, int]:
    """Recover all exact axes from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_objects": analysis["n_objects"],
        "median_size": analysis["median_size"],
    }


def _render_component(component: dict[str, Any], *, transpose: bool) -> list[list[int]]:
    shape = component["shape"]
    if transpose:
        shape = _transpose_shape(shape)
    height, width = _shape_dimensions(shape)
    output = full_grid(height, width, 0)
    for row, col in shape:
        output[row][col] = 6
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid median-transpose input: " + "; ".join(analysis["errors"]))
    return _render_component(analysis["selected"], transpose=True)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_objects", "median_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _scheduled_choice(ctx, label: str, domain: Sequence[int], scheduled: int) -> int:
    options = tuple(domain) if label in ctx.overrides and ctx.overrides[label] is not None else (scheduled,)
    return int(ctx.draw_choice(label, options))


def _draw_dimension(ctx, label: str, *, anchor: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return int(ctx.draw_choice(label, DIMENSION_VALUES))
    if anchor is not None:
        return int(ctx.draw_choice(label, (anchor,)))
    options = {
        "easy": (12, 13),
        "medium": DIMENSION_VALUES,
        "hard": (13, 18),
    }[ctx.difficulty]
    return int(ctx.draw_choice(label, options))


def _sizes(n_objects: int, median_size: int) -> list[int]:
    radius = n_objects // 2
    return list(range(median_size - radius, median_size + radius + 1))


def _reading_order(sizes: list[int], profile: str) -> list[int]:
    ascending = sorted(sizes)
    target = ascending[len(ascending) // 2]
    others = [size for size in ascending if size != target]
    if profile == "ascending":
        return ascending
    if profile == "target_last":
        return [*others, target]
    if profile == "target_first":
        result = [target]
        while others:
            result.append(others.pop(0))
            if others:
                result.append(others.pop(-1))
        return result
    if profile == "target_second":
        return [others.pop(-1), target, *others]
    raise ValueError(f"unknown reading-order profile: {profile}")


def _choose_shapes(ctx, ordered_sizes: Sequence[int], median_size: int):
    rng = ctx.draw_rng("shapes")
    result = []
    for index, size in enumerate(ordered_sizes):
        pool = _TARGET_POOLS[size] if size == median_size else _COMPACT_POOLS[size]
        # Keyed randomness varies orientation/shape without changing cell area or
        # the deliberate compact-vs-sparse bbox teaching contrast.
        local = list(pool)
        rng.shuffle(local)
        result.append(local[0])
    return result


def _candidate_placements(
    shape: Sequence[tuple[int, int]], height: int, width: int
) -> list[tuple[tuple[int, int], ...]]:
    shape_h, shape_w = _shape_dimensions(shape)
    return [
        tuple((top + row, left + col) for row, col in shape)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
    ]


def _touches(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for row, col in cells:
        if (row, col) in occupied:
            return True
        if any((row + drow, col + dcol) in occupied for drow, dcol in _NEIGHBORS_8):
            return True
    return False


def _place_shapes(
    *,
    height: int,
    width: int,
    shapes: Sequence[Sequence[tuple[int, int]]],
    rng,
) -> list[tuple[tuple[int, int], ...]]:
    """Place shapes by randomized backtracking while preserving reading order."""
    for _restart in range(24):
        candidate_lists = []
        for shape in shapes:
            candidates = _candidate_placements(shape, height, width)
            rng.shuffle(candidates)
            candidate_lists.append(candidates)

        placed: list[tuple[tuple[int, int], ...]] = []
        occupied: set[tuple[int, int]] = set()
        node_budget = 80000

        def search(index: int, previous_first: tuple[int, int]) -> bool:
            nonlocal node_budget
            if index == len(candidate_lists):
                return True
            for cells in candidate_lists[index]:
                node_budget -= 1
                if node_budget <= 0:
                    return False
                first = min(cells)
                if first <= previous_first or _touches(cells, occupied):
                    continue
                placed.append(cells)
                occupied.update(cells)
                if search(index + 1, first):
                    return True
                for cell in cells:
                    occupied.remove(cell)
                placed.pop()
            return False

        if search(0, (-1, -1)):
            return list(placed)
        rng.random()
    raise ValueError(f"cannot place {len(shapes)} separated objects in {height}x{width}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    n_objects, median_size, order = _SCHEDULE[int(sample_index) % LESSON_SCHEDULE_PERIOD]
    return f"n{n_objects}-median{median_size}-{order}"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    slot = int(sample_index) % LESSON_SCHEDULE_PERIOD
    scheduled_n, scheduled_median, order_profile = _SCHEDULE[slot]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    n_objects = _scheduled_choice(ctx, "n_objects", (3, 5), scheduled_n)
    median_size = _scheduled_choice(ctx, "median_size", (4, 5, 6), scheduled_median)

    anchor_dims = None
    if slot == 0 and not ({"grid_h", "grid_w"} & {key for key, value in overrides.items() if value is not None}):
        anchor_dims = _CANONICAL_DIMS[(int(sample_index) // LESSON_SCHEDULE_PERIOD) % len(_CANONICAL_DIMS)]
    height = _draw_dimension(ctx, "grid_h", anchor=anchor_dims[0] if anchor_dims else None)
    width = _draw_dimension(ctx, "grid_w", anchor=anchor_dims[1] if anchor_dims else None)

    sizes = _sizes(n_objects, median_size)
    ordered_sizes = _reading_order(sizes, order_profile)
    shapes = _choose_shapes(ctx, ordered_sizes, median_size)
    placements = _place_shapes(
        height=height,
        width=width,
        shapes=shapes,
        rng=ctx.draw_rng("layout"),
    )

    grid = full_grid(height, width, 0)
    for cells in placements:
        for row, col in cells:
            grid[row][col] = 6

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid median-transpose lesson: " + "; ".join(errors))

    # Defaults, unlike arbitrary overrides, must carry the advertised semantic
    # contrast. Fail closed instead of silently emitting a weak lesson.
    if not overrides:
        analysis = _analysis(grid)
        if not analysis["selected_is_asymmetric"]:
            raise AssertionError("scheduled target must visibly require transposition")
        if slot != 0 and not analysis["median_not_reading_middle"]:
            raise AssertionError("scheduled lesson failed to refute reading-order selection")
        if not analysis["median_not_bbox_middle"]:
            raise AssertionError("scheduled lesson failed to refute bbox-area selection")
    return grid


def _ranked_component(grid: Any, key: Callable[[dict[str, Any]], Any], rank: int):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    ranked = sorted(analysis["components"], key=lambda component: (key(component), component["first"]))
    return ranked[rank]


def _smallest(grid):
    return _render_component(_ranked_component(grid, lambda component: component["size"], 0), transpose=True)


def _largest(grid):
    return _render_component(_ranked_component(grid, lambda component: component["size"], -1), transpose=True)


def _second_smallest(grid):
    return _render_component(_ranked_component(grid, lambda component: component["size"], 1), transpose=True)


def _reading_middle(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_component(analysis["components"][len(analysis["components"]) // 2], transpose=True)


def _bbox_middle(grid):
    return _render_component(_ranked_component(grid, lambda component: component["bbox_area"], len(_components(grid)) // 2), transpose=True)


def _fixed_size_five(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    match = next((component for component in analysis["components"] if component["size"] == 5), None)
    return [[0]] if match is None else _render_component(match, transpose=True)


def _median_untransposed(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_component(analysis["selected"], transpose=False)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "smallest": _smallest,
    "largest": _largest,
    "second_smallest": _second_smallest,
    "reading_order_middle": _reading_middle,
    "bbox_area_middle": _bbox_middle,
    "fixed_size_five": _fixed_size_five,
    "median_without_transpose": _median_untransposed,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "second_smallest": _second_smallest,
    "fixed_size_five": _fixed_size_five,
}


def _differs(grid, rival: Callable[[Any], list[list[int]]]) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (IndexError, TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    f"refutes_{name}": (lambda grid, competitor=rival: _differs(grid, competitor))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {
    f"refutes_{name}": [name]
    for name in SEMANTIC_RIVALS
}


def lesson_identifiable(demos: Sequence[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons whose demonstrations leave a declared shortcut viable."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
            actual = pair["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is malformed: {type(exc).__name__}: {exc}")
            continue
        if actual != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")

    try:
        query_expected = rule_mirror(query["input"])
        if "output" in query and query["output"] != query_expected:
            reasons.append("query output disagrees with the selected rule")
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is malformed: {type(exc).__name__}: {exc}")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if demos and all(rival(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"competitor {name!r} still fits every demonstration")
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} could not be scored: {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Minimal invalid scenes used by the shared mutation-sensitivity probe."""
    base = generate(8081, 1, difficulty="medium")

    empty = full_grid(12, 12, 0)

    single = full_grid(12, 12, 0)
    for row, col in ((1, 1), (1, 2), (2, 1)):
        single[row][col] = 6

    tied = full_grid(12, 12, 0)
    for top, left in ((1, 1), (1, 6), (7, 1)):
        tied[top][left] = tied[top][left + 1] = 6

    wrong_color = [list(row) for row in base]
    row, col = next(
        (r, c)
        for r, values in enumerate(wrong_color)
        for c, value in enumerate(values)
        if value == 6
    )
    wrong_color[row][col] = 7

    return [
        ("no_objects", empty),
        ("single_object", single),
        ("tied_sizes", tied),
        ("wrong_color", wrong_color),
    ]
