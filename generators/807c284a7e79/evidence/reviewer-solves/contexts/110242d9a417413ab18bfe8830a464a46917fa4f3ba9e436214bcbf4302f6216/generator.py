"""Generator for ARC task 807c284a7e79 (fill a chamber by BFS parity).

A color-2 seed starts a four-neighbor flood through every non-8 cell in its
connected component.  Reached cells are recolored 3 at even shortest-path
distance and 4 at odd distance; color-8 walls and unreachable cells remain
unchanged.

The teaching grammar deliberately alternates three semantic profiles:

* ``connected`` — one passable chamber, matching the public examples;
* ``split_seed_small`` — two chambers with the seed in the smaller one;
* ``split_seed_large`` — two chambers with the seed in the larger one.

Every consecutive three-example lesson contains all three profiles.  This
refutes both public-data shortcuts ("paint every non-wall cell" and "paint the
largest chamber") while keeping every public override exact and recoverable
from returned pixels.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "807c284a7e79"
TASK_ID = "807c284a7e79"
VERSION = "3.0.0"
RULE_HASH = "229d8e0a7e30"

SUMMARY = (
    "A complete color-8 border encloses a zero-valued chamber containing one "
    "color-2 seed and one straight interior color-8 wall. The wall is vertical "
    "or horizontal and either has a two-cell opening (one connected chamber) "
    "or spans the chamber (two disconnected chambers). From the seed, flood "
    "through four-connected non-8 cells; recolor reached even-distance cells "
    "3 and reached odd-distance cells 4. Walls and unreachable zeros stay "
    "unchanged. A three-sample schedule cycles connected, seed-in-smaller, and "
    "seed-in-larger scenes so lessons expose reachability rather than merely a "
    "global checkerboard or largest-component shortcut."
)

INVARIANTS = [
    "outer border is entirely color 8",
    "exactly one interior color-2 seed",
    "at least one interior color-8 wall cell",
    "only colors 0, 2, and 8 occur in inputs",
    "the seed reaches a nontrivial component",
]

SCENE_PROFILES = ("connected", "split_seed_small", "split_seed_large")
WALL_ORIENTATIONS = ("vertical", "horizontal")
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 3

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/rng 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "scheduled/rng 10..14", "valid": "10..14"},
    "scene_profile": {
        "type": "str",
        "default": "sample_index mod 3",
        "valid": "|".join(SCENE_PROFILES),
    },
    "wall_orientation": {
        "type": "str",
        "default": "sample_index mod 2",
        "valid": "|".join(WALL_ORIENTATIONS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_SHAPES = ((9, 11), (10, 10), (9, 12), (8, 10), (9, 11))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Public deterministic semantic schedule; ``seed``/``difficulty`` do not alias it."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    for name in ("grid_h", "grid_w"):
        if name not in overrides:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")
    if "grid_h" in overrides and not 8 <= overrides["grid_h"] <= 12:
        raise ValueError("grid_h override must be in 8..12")
    if "grid_w" in overrides and not 10 <= overrides["grid_w"] <= 14:
        raise ValueError("grid_w override must be in 10..14")

    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if not isinstance(value, str) or value not in SCENE_PROFILES:
            raise ValueError(f"scene_profile override must be one of {SCENE_PROFILES}")
    if "wall_orientation" in overrides:
        value = overrides["wall_orientation"]
        if not isinstance(value, str) or value not in WALL_ORIENTATIONS:
            raise ValueError(f"wall_orientation override must be one of {WALL_ORIENTATIONS}")


def _scheduled_overrides(sample_index: int, overrides: dict[str, Any]) -> dict[str, Any]:
    """Pin lesson semantics and public-size anchors, then honor caller values."""
    index = int(sample_index)
    scheduled: dict[str, Any] = {
        "scene_profile": SCENE_PROFILES[index % len(SCENE_PROFILES)],
        "wall_orientation": WALL_ORIENTATIONS[index % len(WALL_ORIENTATIONS)],
    }
    shape_slot = index % 10
    if shape_slot < len(_CANONICAL_SHAPES):
        scheduled["grid_h"], scheduled["grid_w"] = _CANONICAL_SHAPES[shape_slot]
    scheduled.update(overrides)
    return scheduled


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return all four-connected non-wall components, including the seed cell."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8 or (r, c) in seen:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def _seed_points(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]


def _reachable_distances(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    seeds = _seed_points(grid)
    if len(seeds) != 1:
        return {}
    h, w = len(grid), len(grid[0])
    distance = {seeds[0]: 0}
    queue = deque(seeds)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            point = (nr, nc)
            if (
                0 <= nr < h
                and 0 <= nc < w
                and grid[nr][nc] != 8
                and point not in distance
            ):
                distance[point] = distance[(r, c)] + 1
                queue.append(point)
    return distance


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "errors": errors,
        "height": 0,
        "width": 0,
        "seeds": [],
        "components": [],
        "seed_component": [],
        "distances": {},
        "interior_walls": [],
    }
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a nonempty list of rows")
        return result
    if any(not isinstance(row, (list, tuple)) for row in grid):
        errors.append("every row must be a list or tuple")
        return result
    if not grid[0]:
        errors.append("grid rows must be nonempty")
        return result
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result

    height = len(grid)
    result["height"], result["width"] = height, width
    if not 8 <= height <= 12:
        errors.append(f"height {height} is outside 8..12")
    if not 10 <= width <= 14:
        errors.append(f"width {width} is outside 10..14")

    bad_types = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if isinstance(value, bool) or not isinstance(value, int)
    ]
    if bad_types:
        r, c, value = bad_types[0]
        errors.append(f"cell ({r},{c}) has non-integer value {value!r}")
        return result
    bad_values = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2, 8)
    ]
    if bad_values:
        r, c, value = bad_values[0]
        errors.append(f"cell ({r},{c}) has unsupported color {value}")

    if height >= 2 and width >= 2:
        border_ok = (
            all(grid[0][c] == 8 and grid[height - 1][c] == 8 for c in range(width))
            and all(grid[r][0] == 8 and grid[r][width - 1] == 8 for r in range(height))
        )
        if not border_ok:
            errors.append("outer color-8 border is incomplete")

    seeds = _seed_points(grid)
    result["seeds"] = seeds
    if len(seeds) != 1:
        errors.append(f"expected exactly one seed-2, got {len(seeds)}")
    elif not (1 <= seeds[0][0] < height - 1 and 1 <= seeds[0][1] < width - 1):
        errors.append("seed-2 must be inside the border")

    interior_walls = [
        (r, c)
        for r in range(1, max(1, height - 1))
        for c in range(1, max(1, width - 1))
        if grid[r][c] == 8
    ]
    result["interior_walls"] = interior_walls
    if not interior_walls:
        errors.append("at least one interior wall-8 cell is required")

    if bad_values or len(seeds) != 1:
        return result

    comps = _components(grid)
    result["components"] = comps
    if not 1 <= len(comps) <= 2:
        errors.append(f"expected one or two passable components, got {len(comps)}")
    seed_component = next((cells for cells in comps if seeds[0] in cells), [])
    result["seed_component"] = seed_component
    distances = _reachable_distances(grid)
    result["distances"] = distances
    if len(distances) < 8:
        errors.append(f"seed reaches too few cells: {len(distances)}")
    if distances and not ({d % 2 for d in distances.values()} == {0, 1}):
        errors.append("reachable chamber does not expose both distance parities")
    if len(comps) == 2:
        sizes = sorted(map(len, comps))
        if sizes[0] < 6:
            errors.append(f"smaller disconnected chamber is too small: {sizes[0]}")
        if sizes[0] == sizes[1]:
            errors.append("disconnected chambers must have unequal size")
    return result


def _draw_wall(
    grid: list[list[int]],
    profile: str,
    orientation: str,
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    split = profile != "connected"
    if orientation == "vertical":
        if split:
            candidates = [
                c for c in range(3, w - 3)
                if c - 1 != (w - 2) - c
            ]
            column = rng.choice(candidates)
            for r in range(1, h - 1):
                grid[r][column] = 8
        else:
            column = rng.randint(2, w - 3)
            gap_start = rng.randint(2, h - 4)
            for r in range(1, h - 1):
                if r not in (gap_start, gap_start + 1):
                    grid[r][column] = 8
    else:
        if split:
            candidates = [
                r for r in range(3, h - 3)
                if r - 1 != (h - 2) - r
            ]
            row = rng.choice(candidates)
            for c in range(1, w - 1):
                grid[row][c] = 8
        else:
            row = rng.randint(2, h - 3)
            gap_start = rng.randint(2, w - 4)
            for c in range(1, w - 1):
                if c not in (gap_start, gap_start + 1):
                    grid[row][c] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled = _scheduled_overrides(sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=scheduled,
    )
    # Difficulty changes only the default size distribution. Explicit boundary
    # overrides remain legal in every band because draw_int_diff validates them
    # against the same full domains.
    height = ctx.draw_int_diff("grid_h", 8, 12)
    width = ctx.draw_int_diff("grid_w", 10, 14)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    orientation = ctx.draw_choice("wall_orientation", WALL_ORIENTATIONS)
    rng = ctx.draw_rng("layout")

    grid = full_grid(height, width, 0)
    for c in range(width):
        grid[0][c] = 8
        grid[height - 1][c] = 8
    for r in range(height):
        grid[r][0] = 8
        grid[r][width - 1] = 8

    _draw_wall(grid, profile, orientation, rng)
    comps = _components(grid)
    if profile == "connected":
        if len(comps) != 1:
            raise AssertionError(f"connected profile produced {len(comps)} components")
        target = comps[0]
    else:
        if len(comps) != 2:
            raise AssertionError(f"split profile produced {len(comps)} components")
        ordered = sorted(comps, key=lambda cells: (len(cells), cells))
        target = ordered[0] if profile == "split_seed_small" else ordered[-1]

    desired_parity = int(sample_index) % 2
    candidates = sorted((r, c) for r, c in target if (r + c) % 2 == desired_parity)
    if not candidates:
        raise AssertionError("target chamber has no cell with scheduled seed parity")
    sr, sc = rng.choice(candidates)
    grid[sr][sc] = 2

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
        "wall_orientation": orientation,
    }
    actual = observe_overrides(grid)
    if actual != expected:
        raise AssertionError(f"axis realization mismatch: expected {expected}, observed {actual}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Accept the broad task grammar, including all five public examples."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    walls = analysis["interior_walls"]
    rows = {r for r, _ in walls}
    cols = {c for _, c in walls}
    if len(cols) == 1:
        orientation = "vertical"
    elif len(rows) == 1:
        orientation = "horizontal"
    else:
        orientation = "mixed"

    comps = analysis["components"]
    if len(comps) == 1:
        profile = "connected"
    else:
        seed_size = len(analysis["seed_component"])
        profile = (
            "split_seed_large"
            if seed_size == max(map(len, comps))
            else "split_seed_small"
        )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_profile": profile,
        "wall_orientation": orientation,
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    seed = analysis["seeds"][0]
    return {
        **observe_overrides(grid),
        "component_count": len(analysis["components"]),
        "component_sizes": sorted(map(len, analysis["components"])),
        "seed_component_size": len(analysis["seed_component"]),
        "seed_checkerboard_parity": (seed[0] + seed[1]) % 2,
        "reachable_cells": len(analysis["distances"]),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python test mirror; the selected Racket source remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = deepcopy(grid)
    for (r, c), distance in analysis["distances"].items():
        output[r][c] = 3 if distance % 2 == 0 else 4
    return output


def _paint_by_seed_parity(
    grid: list[list[int]], cells: list[tuple[int, int]]
) -> list[list[int]]:
    seed = _seed_points(grid)[0]
    output = deepcopy(grid)
    for r, c in cells:
        output[r][c] = 3 if (abs(r - seed[0]) + abs(c - seed[1])) % 2 == 0 else 4
    return output


def _rival_all_non_walls(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    cells = [cell for component in analysis["components"] for cell in component]
    return _paint_by_seed_parity(grid, cells)


def _rival_largest_component(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    largest = max(analysis["components"], key=len)
    return _paint_by_seed_parity(grid, largest)


def _rival_leave_seed_unchanged(grid):
    output = rule_mirror(grid)
    r, c = _seed_points(grid)[0]
    output[r][c] = 2
    return output


def _rival_absolute_origin_parity(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = deepcopy(grid)
    for r, c in analysis["distances"]:
        output[r][c] = 3 if (r + c) % 2 == 0 else 4
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "paint_all_non_walls": _rival_all_non_walls,
    "paint_largest_component": _rival_largest_component,
    "leave_seed_unchanged": _rival_leave_seed_unchanged,
    "absolute_origin_checkerboard": _rival_absolute_origin_parity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "paint_all_non_walls": _rival_all_non_walls,
    "paint_largest_component": _rival_largest_component,
}


def _lawful_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _rival_differs(grid, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "unreachable_component_preserved": lambda grid: bool(
        (analysis := _lawful_analysis(grid)) is not None
        and len(analysis["components"]) == 2
        and _rival_differs(grid, "paint_all_non_walls")
    ),
    "seed_in_smaller_component": lambda grid: bool(
        (analysis := _lawful_analysis(grid)) is not None
        and len(analysis["components"]) == 2
        and len(analysis["seed_component"]) < max(map(len, analysis["components"]))
        and _rival_differs(grid, "paint_largest_component")
    ),
    "seed_recolored_at_distance_zero": lambda grid: bool(
        _lawful_analysis(grid) is not None
        and _rival_differs(grid, "leave_seed_unchanged")
    ),
    "odd_seed_parity_refutes_fixed_origin": lambda grid: bool(
        (analysis := _lawful_analysis(grid)) is not None
        and sum(analysis["seeds"][0]) % 2 == 1
        and _rival_differs(grid, "absolute_origin_checkerboard")
    ),
}
WITNESS_RIVALS = {
    "unreachable_component_preserved": ["paint_all_non_walls"],
    "seed_in_smaller_component": ["paint_largest_component"],
    "seed_recolored_at_distance_zero": ["leave_seed_unchanged"],
    "odd_seed_parity_refutes_fixed_origin": ["absolute_origin_checkerboard"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """A valid three-demo lesson must falsify every declared rival program."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(demo["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with BFS parity")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        try:
            expected_query = rule_mirror(query["input"])
            if query.get("output") is not None and query["output"] != expected_query:
                reasons.append("query output disagrees with BFS parity")
        except (TypeError, ValueError) as exc:
            reasons.append(f"query is outside the task grammar: {exc}")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"competitor {name!r} fits every demonstration")
        except Exception as exc:
            reasons.append(f"competitor {name!r} errored: {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed scenes used by structural and reviewer tests."""
    valid = generate(99173, 1, difficulty="medium")
    fixtures: list[tuple[str, list[list[int]]]] = []

    no_seed = deepcopy(valid)
    r, c = _seed_points(no_seed)[0]
    no_seed[r][c] = 0
    fixtures.append(("missing_seed", no_seed))

    broken_border = deepcopy(valid)
    broken_border[0][1] = 0
    fixtures.append(("broken_border", broken_border))

    unknown_color = deepcopy(valid)
    unknown_color[1][1] = 9
    fixtures.append(("unknown_color", unknown_color))

    no_wall = deepcopy(valid)
    for r in range(1, len(no_wall) - 1):
        for c in range(1, len(no_wall[0]) - 1):
            if no_wall[r][c] == 8:
                no_wall[r][c] = 0
    fixtures.append(("missing_interior_wall", no_wall))

    isolated = generate(99173, 0, difficulty="medium")
    r, c = _seed_points(isolated)[0]
    for dr, dc in _CARDINAL:
        isolated[r + dr][c + dc] = 8
    fixtures.append(("isolated_seed", isolated))
    return fixtures
