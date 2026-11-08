"""Generator for ARC task 6fc2f51cfbb2.

The walkable cells form either (a) one loop that creates exactly two equal
shortest routes, or (b) a branched tree with one shortest route.  The output
marks only zero-cells used by every shortest route from red(2) to green(3).
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6fc2f51cfbb2"
TASK_ID = "6fc2f51cfbb2"
VERSION = "3.1.0"
RULE_HASH = "d2ecbd1c9b9e"

SUMMARY = (
    "A gray(5) field contains one connected network of walkable zero-cells, "
    "one red(2) start, and one green(3) goal.  Some scenes contain a single "
    "cycle that supplies exactly two equal-length shortest routes; others "
    "contain a unique elbow route plus dead-end branches.  Treat gray cells "
    "as walls.  Of all shortest 4-connected start-to-goal paths, recolor with "
    "cyan(8) exactly the zero-cells present on every shortest path.  Preserve "
    "the red and green endpoints, alternative shortest-route cells, dead-end "
    "branches, and walls."
)

EXAMPLES_NEEDED = 4
INVARIANTS = [
    "gray(5) cells are blocked and every non-gray cell belongs to one network",
    "there is exactly one red(2) start and exactly one green(3) goal",
    "loop scenes have exactly two equal shortest paths with shared bottlenecks",
    "tree scenes have one shortest path and dead-end zero-cell distractors",
    "only zero-cells common to every shortest path become cyan(8)",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PROFILES = ("equal_loop_h", "equal_loop_v", "elbow_branches")
_VARIANTS = ("compact", "extended")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 11..18",
        "valid": "11..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 11..18",
        "valid": "11..18",
    },
    "profile": {
        "type": "enum",
        "default": "seed-phased three-sample teaching cycle",
        "valid": "equal_loop_h|equal_loop_v|elbow_branches",
    },
    "variant": {
        "type": "enum",
        "default": "keyed choice",
        "valid": "compact|extended",
    },
}

_WALKABLE = frozenset((0, 2, 3))
_ALLOWED_INPUT_COLORS = frozenset((0, 2, 3, 5))
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard") and not isinstance(
        difficulty, (int, float)
    ):
        raise ValueError(
            "difficulty must be None, easy, medium, hard, or a numeric value"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _coerce_grid(grid: Any) -> list[list[Any]]:
    if not isinstance(grid, (list, tuple)):
        return []
    coerced: list[list[Any]] = []
    for row in grid:
        if isinstance(row, str):
            coerced.append([int(value) if value.isdigit() else value for value in row])
        elif isinstance(row, (list, tuple)):
            coerced.append(
                [
                    int(value)
                    if isinstance(value, str) and value.isdigit()
                    else value
                    for value in row
                ]
            )
        else:
            return []
    return coerced


def _neighbors(cell: tuple[int, int], cells: set[tuple[int, int]]):
    row, col = cell
    for d_row, d_col in _DIRECTIONS:
        other = (row + d_row, col + d_col)
        if other in cells:
            yield other


def _distances_and_counts(
    origin: tuple[int, int], cells: set[tuple[int, int]]
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    distances = {origin: 0}
    counts = {origin: 1}
    queue = deque([origin])
    while queue:
        cell = queue.popleft()
        next_distance = distances[cell] + 1
        for neighbor in _neighbors(cell, cells):
            if neighbor not in distances:
                distances[neighbor] = next_distance
                counts[neighbor] = counts[cell]
                queue.append(neighbor)
            elif distances[neighbor] == next_distance:
                counts[neighbor] += counts[cell]
    return distances, counts


def _scene_analysis(grid: Any):
    coerced = _coerce_grid(grid)
    errors: list[str] = []
    if not coerced or not coerced[0]:
        return coerced, None, ["grid must be non-empty"]
    width = len(coerced[0])
    if any(not row or len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]
    height = len(coerced)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be between 1 and 30")
    if any(
        type(value) is not int or value not in _ALLOWED_INPUT_COLORS
        for row in coerced
        for value in row
    ):
        errors.append("input cells must use only integer colors 0, 2, 3, and 5")
        return coerced, None, errors

    starts = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 2
    ]
    goals = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 3
    ]
    zeroes = {
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 0
    }
    walls = sum(value == 5 for row in coerced for value in row)
    if len(starts) != 1:
        errors.append(f"expected exactly one red(2) start, found {len(starts)}")
    if len(goals) != 1:
        errors.append(f"expected exactly one green(3) goal, found {len(goals)}")
    if not zeroes:
        errors.append("scene must contain walkable zero-cells")
    if not walls:
        errors.append("scene must contain gray(5) walls")
    if errors:
        return coerced, None, errors

    start, goal = starts[0], goals[0]
    cells = set(zeroes) | {start, goal}
    distances_from_start, counts_from_start = _distances_and_counts(start, cells)
    if len(distances_from_start) != len(cells):
        errors.append("all walkable cells must form one connected component")
        return coerced, None, errors
    distances_from_goal, counts_from_goal = _distances_and_counts(goal, cells)
    shortest_distance = distances_from_start[goal]
    shortest_path_count = counts_from_start[goal]

    edge_count = sum(1 for cell in cells for _ in _neighbors(cell, cells)) // 2
    cycle_rank = edge_count - len(cells) + 1
    degrees = {cell: sum(1 for _ in _neighbors(cell, cells)) for cell in cells}
    leaf_cells = {cell for cell, degree in degrees.items() if degree == 1}
    branch_leaves = leaf_cells - {start, goal}

    some_shortest: set[tuple[int, int]] = set()
    every_shortest: set[tuple[int, int]] = set()
    for cell in cells:
        if (
            distances_from_start[cell] + distances_from_goal[cell]
            != shortest_distance
        ):
            continue
        some_shortest.add(cell)
        if (
            counts_from_start[cell] * counts_from_goal[cell]
            == shortest_path_count
        ):
            every_shortest.add(cell)

    unavoidable_zeroes = every_shortest & zeroes
    alternative_shortest_zeroes = (some_shortest - every_shortest) & zeroes
    off_shortest_zeroes = zeroes - some_shortest
    active_rows = [row for row, _ in cells]
    active_cols = [col for _, col in cells]
    features = {
        "height": height,
        "width": width,
        "start": start,
        "goal": goal,
        "cells": cells,
        "zeroes": zeroes,
        "walkable_count": len(cells),
        "edge_count": edge_count,
        "cycle_rank": cycle_rank,
        "degrees": degrees,
        "leaf_count": len(leaf_cells),
        "branch_leaf_count": len(branch_leaves),
        "shortest_distance": shortest_distance,
        "shortest_path_count": shortest_path_count,
        "some_shortest": some_shortest,
        "every_shortest": every_shortest,
        "unavoidable_zeroes": unavoidable_zeroes,
        "alternative_shortest_zeroes": alternative_shortest_zeroes,
        "off_shortest_zeroes": off_shortest_zeroes,
        "unavoidable_zero_count": len(unavoidable_zeroes),
        "alternative_shortest_zero_count": len(alternative_shortest_zeroes),
        "off_shortest_zero_count": len(off_shortest_zeroes),
        "active_bbox": (
            min(active_rows),
            min(active_cols),
            max(active_rows),
            max(active_cols),
        ),
    }
    return coerced, features, []


def _linked_profile(features: dict[str, Any]) -> tuple[str, str] | None:
    """Return the strict task-linked family/variant for a valid scene."""
    start = features["start"]
    goal = features["goal"]
    if features["cycle_rank"] == 1:
        if features["shortest_path_count"] != 2:
            return None
        if start[0] == goal[0]:
            profile = "equal_loop_h"
        elif start[1] == goal[1]:
            profile = "equal_loop_v"
        else:
            return None
        if not (
            19 <= features["walkable_count"] <= 25
            and 12 <= features["shortest_distance"] <= 15
            and 5 <= features["unavoidable_zero_count"] <= 7
            and 12 <= features["alternative_shortest_zero_count"] <= 18
            and features["off_shortest_zero_count"] in (0, 2)
            and features["branch_leaf_count"] in (0, 1)
        ):
            return None
        variant = (
            "extended"
            if features["off_shortest_zero_count"] == 2
            else "compact"
        )
        return profile, variant

    if features["cycle_rank"] == 0:
        if not (
            features["shortest_path_count"] == 1
            and 17 <= features["walkable_count"] <= 21
            and 10 <= features["shortest_distance"] <= 12
            and features["unavoidable_zero_count"]
            == features["shortest_distance"] - 1
            and features["alternative_shortest_zero_count"] == 0
            and 6 <= features["off_shortest_zero_count"] <= 8
            and features["branch_leaf_count"] == 2
        ):
            return None
        variant = (
            "extended" if features["shortest_distance"] == 12 else "compact"
        )
        return "elbow_branches", variant
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the canonical all-shortest-path teaching grammar."""
    del difficulty, meta
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return errors
    assert features is not None
    if features["degrees"][features["start"]] != 1:
        errors.append("red start must be a degree-one endpoint")
    if features["degrees"][features["goal"]] != 1:
        errors.append("green goal must be a degree-one endpoint")
    if any(degree > 3 for degree in features["degrees"].values()):
        errors.append("walkable network may not contain degree-four junctions")
    if _linked_profile(features) is None:
        errors.append(
            "scene must be a linked equal-route loop or the branched elbow profile"
        )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    assert features is not None
    linked = _linked_profile(features)
    if linked is None:
        raise ValueError("cannot observe overrides: scene is outside linked profiles")
    profile, variant = linked
    return {
        "grid_h": features["height"],
        "grid_w": features["width"],
        "profile": profile,
        "variant": variant,
    }


def profile_signature(grid) -> dict[str, Any] | None:
    """Structured semantic signature used by the task-linked census."""
    _coerced, features, errors = _scene_analysis(grid)
    if errors or features is None:
        return None
    linked = _linked_profile(features)
    if linked is None:
        return None
    profile, variant = linked
    return {
        "profile": profile,
        "variant": variant,
        "walkable_count": features["walkable_count"],
        "edge_count": features["edge_count"],
        "cycle_rank": features["cycle_rank"],
        "shortest_distance": features["shortest_distance"],
        "shortest_path_count": features["shortest_path_count"],
        "unavoidable_zero_count": features["unavoidable_zero_count"],
        "alternative_shortest_zero_count": features[
            "alternative_shortest_zero_count"
        ],
        "off_shortest_zero_count": features["off_shortest_zero_count"],
        "branch_leaf_count": features["branch_leaf_count"],
        "active_bbox_shape": (
            features["active_bbox"][2] - features["active_bbox"][0] + 1,
            features["active_bbox"][3] - features["active_bbox"][1] + 1,
        ),
    }


def canonical_profile_signature(grid) -> dict[str, Any] | None:
    return profile_signature(grid)


def is_canonical_profile(grid) -> bool:
    return canonical_profile_signature(grid) is not None


def rule_mirror(grid):
    """Python test mirror; production outputs remain authoritative Racket results."""
    coerced, features, errors = _scene_analysis(grid)
    if errors or features is None:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [row[:] for row in coerced]
    for row, col in features["unavoidable_zeroes"]:
        output[row][col] = 8
    return output


def _horizontal_loop(variant: str) -> tuple[dict[tuple[int, int], int], str]:
    if variant == "compact":
        length, left, right, depth = 8, 2, 5, 2
        branch_length = 0
    else:
        length, left, right, depth = 10, 2, 6, 2
        branch_length = 2

    cells: dict[tuple[int, int], int] = {}
    for col in range(0, left + 1):
        cells[(0, col)] = 0
    for col in range(right, length + 1):
        cells[(0, col)] = 0
    for sign in (-1, 1):
        row = sign * depth
        for col in range(left, right + 1):
            cells[(row, col)] = 0
        for offset in range(1, depth):
            cells[(sign * offset, left)] = 0
            cells[(sign * offset, right)] = 0
    if branch_length:
        attach_col = length - 1
        for offset in range(1, branch_length + 1):
            cells[(-offset, attach_col)] = 0
    cells[(0, 0)] = 2
    cells[(0, length)] = 3
    return cells, "equal_loop_h"


def _compact_elbow() -> dict[tuple[int, int], int]:
    main = (
        (0, 2),
        (1, 2),
        (2, 2),
        (2, 3),
        (2, 4),
        (2, 5),
        (3, 5),
        (4, 5),
        (5, 5),
        (6, 5),
        (7, 5),
    )
    branches = (
        (2, 1),
        (2, 0),
        (5, 4),
        (5, 3),
        (5, 2),
        (6, 2),
    )
    cells = {cell: 0 for cell in main + branches}
    cells[main[0]] = 2
    cells[main[-1]] = 3
    return cells


def _extended_elbow() -> dict[tuple[int, int], int]:
    main = (
        (0, 2),
        (1, 2),
        (2, 2),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (3, 6),
        (4, 6),
        (5, 6),
        (6, 6),
        (7, 6),
        (8, 6),
    )
    branches = (
        (2, 1),
        (2, 0),
        (6, 5),
        (6, 4),
        (6, 3),
        (6, 2),
        (7, 2),
        (8, 2),
    )
    cells = {cell: 0 for cell in main + branches}
    cells[main[0]] = 2
    cells[main[-1]] = 3
    return cells


def _normalize_cells(
    cells: dict[tuple[int, int], int]
) -> dict[tuple[int, int], int]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return {
        (row - min_row, col - min_col): value
        for (row, col), value in cells.items()
    }


def _transform_cells(
    cells: dict[tuple[int, int], int], operation: int
) -> dict[tuple[int, int], int]:
    transformed: dict[tuple[int, int], int] = {}
    for (row, col), value in cells.items():
        if operation == 0:
            point = (row, col)
        elif operation == 1:
            point = (row, -col)
        elif operation == 2:
            point = (-row, col)
        elif operation == 3:
            point = (-row, -col)
        elif operation == 4:
            point = (col, -row)
        elif operation == 5:
            point = (-col, -row)
        elif operation == 6:
            point = (col, row)
        else:
            point = (-col, row)
        transformed[point] = value
    return _normalize_cells(transformed)


def _place_cells(
    cells: dict[tuple[int, int], int],
    height: int,
    width: int,
    rng,
) -> list[list[int]]:
    normalized = _normalize_cells(cells)
    active_height = max(row for row, _ in normalized) + 1
    active_width = max(col for _, col in normalized) + 1
    if active_height > height or active_width > width:
        raise ValueError(
            f"profile requires at least {active_height}x{active_width}, "
            f"received {height}x{width}"
        )
    top = rng.randint(0, height - active_height)
    left = rng.randint(0, width - active_width)
    grid = full_grid(height, width, 5)
    for (row, col), value in normalized.items():
        grid[top + row][left + col] = value
    return grid


def _draw_profile(profile: str, variant: str, rng):
    if profile in ("equal_loop_h", "equal_loop_v"):
        cells, _ = _horizontal_loop(variant)
        if profile == "equal_loop_h":
            operation = rng.choice((0, 1, 2, 3))
        else:
            operation = rng.choice((4, 5, 6, 7))
        return _transform_cells(cells, operation)
    cells = _compact_elbow() if variant == "compact" else _extended_elbow()
    return _transform_cells(cells, rng.randrange(8))


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
    height = ctx.draw_int_diff("grid_h", 11, 18)
    width = ctx.draw_int_diff("grid_w", 11, 18)
    if overrides.get("profile") is not None:
        profile = ctx.draw_choice("profile", _PROFILES)
    else:
        # A generated ARC lesson consumes sequential sample indices.  Rotate the
        # three linked topologies with a seed-keyed phase so every three
        # consecutive default examples include both equal-route evidence and
        # the unique-route/dead-end contrast.  This prevents answer-equivalent
        # all-unique lessons while keeping episode queries seed-diverse.
        phase = int(seed) % len(_PROFILES)
        scheduled = _PROFILES[(sample_index + phase) % len(_PROFILES)]
        profile = ctx.draw_choice("profile", (scheduled,))
    variant = ctx.draw_choice("variant", _VARIANTS)
    placement_rng = ctx.draw_rng("placement")
    cells = _draw_profile(profile, variant, placement_rng)
    grid = _place_cells(cells, height, width, placement_rng)
    observed = observe_overrides(grid)
    if observed["profile"] != profile or observed["variant"] != variant:
        raise AssertionError(
            f"constructed profile drifted: requested {(profile, variant)}, "
            f"observed {(observed['profile'], observed['variant'])}"
        )
    return grid
