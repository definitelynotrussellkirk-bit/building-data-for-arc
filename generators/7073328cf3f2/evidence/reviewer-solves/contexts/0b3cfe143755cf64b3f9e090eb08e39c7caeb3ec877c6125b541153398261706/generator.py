"""Semantic generator for custom ARC task 7073328cf3f2.

The input is a zero-background corridor graph containing one red(2) seed, one
blue(1) seed, and gray(5) corridor cells.  The selected Racket authority finds
all gray cells on a shortest red-to-blue path and colors them yellow(4).  It
then colors an off-path gray region red or blue only when that region enters
from the corresponding seed end (directly from the seed when such a region
exists, otherwise from the seed-adjacent path cell).  All remaining off-path
gray regions become yellow.

Every ordinary scene contains all three answer-bearing region roles: red-only,
blue-only, and neutral/both-side yellow.  A four-slot schedule alternates
straight and two-turn backbones plus direct, fallback, and mixed end branches,
so every four consecutive demonstrations refute the main shortcut rules.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7073328cf3f2"
TASK_ID = "7073328cf3f2"
VERSION = "4.0.0"
# sha256(" ".join(selected task-local target_code.split()))[:12]
RULE_HASH = "1047ef160c66"

SUMMARY = (
    "On a zero background, red(2) and blue(1) seeds are joined by a gray(5) "
    "corridor tree. Gray cells on the red-to-blue shortest path become "
    "yellow(4). Off-path corridor regions entering from the red end become "
    "red, regions entering from the blue end become blue, and interior "
    "off-path regions become yellow."
)

INVARIANTS = [
    "the only input colors are 0, 1, 2, and 5, with exactly one red and one blue seed",
    "all nonzero cells form one acyclic 4-connected corridor graph",
    "the red-to-blue path contains at least three gray cells",
    "every scene has nonempty red-only, blue-only, and neutral gray regions",
    "ordinary lessons schedule straight/two-turn paths and direct/fallback/mixed seed ends",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.30

ORIENTATIONS = ("horizontal", "vertical")
PATH_SHAPES = ("straight", "two_turn")
SIDE_MODES = ("direct", "fallback", "red_direct", "blue_direct")
PROFILE_SCHEDULE = (
    "straight_direct",
    "straight_fallback",
    "two_turn_red_direct",
    "two_turn_blue_direct",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchors in slots 0-1; difficulty-aware otherwise",
        "valid": "7..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile anchors in slots 0-1; difficulty-aware otherwise",
        "valid": "7..17",
    },
    "orientation": {
        "type": "enum",
        "default": "keyed horizontal|vertical",
        "valid": "horizontal|vertical",
    },
    "path_shape": {
        "type": "enum",
        "default": "four-slot straight|two_turn schedule",
        "valid": "straight|two_turn",
    },
    "side_mode": {
        "type": "enum",
        "default": "four-slot direct|fallback|red_direct|blue_direct schedule",
        "valid": "direct|fallback|red_direct|blue_direct",
    },
}

# Opt into strict override validation. Every declared cross-product is supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Grid = list[list[int]]
Cell = tuple[int, int]
_DIR4: tuple[Cell, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TRAVERSABLE = {1, 2, 5}
_CANONICAL_DIMS = {(7, 9), (8, 9), (8, 10), (9, 9)}
_ANCHOR_DIMS = {
    "easy": ((7, 9), (8, 9)),
    "medium": ((8, 9), (8, 10)),
    "hard": ((9, 9), (8, 10)),
}
_GENERAL_DIMS = {
    "easy": ((7, 8, 9), (9, 10, 11)),
    "medium": ((9, 10, 11, 12), (11, 12, 13, 14)),
    "hard": ((12, 13, 14, 15), (14, 15, 16, 17)),
}


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _neighbors(cell: Cell) -> tuple[Cell, ...]:
    row, col = cell
    return tuple((row + dr, col + dc) for dr, dc in _DIR4)


def _in_bounds(cell: Cell, height: int, width: int) -> bool:
    row, col = cell
    return 0 <= row < height and 0 <= col < width


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed the ARC 30x30 limit"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _distances(cells: set[Cell], start: Cell) -> dict[Cell, int]:
    distances = {start: 0}
    queue: deque[Cell] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in _neighbors(current):
            if neighbor in cells and neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances


def _ordered_path(cells: set[Cell], start: Cell, goal: Cell) -> list[Cell]:
    parent: dict[Cell, Cell | None] = {start: None}
    queue: deque[Cell] = deque([start])
    while queue and goal not in parent:
        current = queue.popleft()
        for neighbor in _neighbors(current):
            if neighbor in cells and neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)
    if goal not in parent:
        return []
    path: list[Cell] = []
    current: Cell | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))


def _flood(starts: Iterable[Cell], allowed: set[Cell]) -> set[Cell]:
    seen = {cell for cell in starts if cell in allowed}
    queue: deque[Cell] = deque(seen)
    while queue:
        current = queue.popleft()
        for neighbor in _neighbors(current):
            if neighbor in allowed and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _turn_count(path: list[Cell]) -> int:
    directions = [
        (b[0] - a[0], b[1] - a[1])
        for a, b in zip(path, path[1:])
    ]
    return sum(first != second for first, second in zip(directions, directions[1:]))


def _components(cells: set[Cell]) -> list[set[Cell]]:
    remaining = set(cells)
    result: list[set[Cell]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = [start]
        while queue:
            current = queue.pop()
            for neighbor in _neighbors(current):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _analyze(grid: Grid) -> dict[str, Any]:
    height = len(grid)
    width = len(grid[0])
    red_cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2]
    blue_cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1]
    red = red_cells[0] if len(red_cells) == 1 else None
    blue = blue_cells[0] if len(blue_cells) == 1 else None
    traversable = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] in _TRAVERSABLE
    }
    gray = {(r, c) for r, c in traversable if grid[r][c] == 5}
    if red is None or blue is None:
        return {
            "red": red,
            "blue": blue,
            "traversable": traversable,
            "gray": gray,
            "reachable": False,
        }

    red_dist = _distances(traversable, red)
    blue_dist = _distances(traversable, blue)
    reachable = blue in red_dist
    path_length = red_dist.get(blue)
    ordered_path = _ordered_path(traversable, red, blue) if reachable else []
    path_gray = {
        cell
        for cell in gray
        if path_length is not None
        and red_dist.get(cell, 10**9) + blue_dist.get(cell, 10**9) == path_length
    }
    off_path = gray - path_gray

    def side_region(seed: Cell, seed_dist: dict[Cell, int]) -> tuple[set[Cell], set[Cell], set[Cell]]:
        direct = {
            cell
            for cell in off_path
            if any(neighbor == seed for neighbor in _neighbors(cell))
        }
        fallback = {
            cell
            for cell in off_path
            if any(
                neighbor in path_gray and seed_dist.get(neighbor, 10**9) <= 1
                for neighbor in _neighbors(cell)
            )
        }
        starts = direct if direct else fallback
        return _flood(starts, off_path), direct, fallback

    red_side, red_direct, red_fallback = side_region(red, red_dist)
    blue_side, blue_direct, blue_fallback = side_region(blue, blue_dist)
    neutral = off_path - red_side - blue_side

    turns = _turn_count(ordered_path)
    path_rows = [row for row, _ in ordered_path]
    path_cols = [col for _, col in ordered_path]
    row_span = max(path_rows) - min(path_rows) if path_rows else 0
    col_span = max(path_cols) - min(path_cols) if path_cols else 0
    if col_span > row_span:
        orientation = "horizontal"
    elif row_span > col_span:
        orientation = "vertical"
    else:
        orientation = "ambiguous"
    path_shape = "straight" if turns == 0 else ("two_turn" if turns == 2 else f"turns_{turns}")
    if red_direct and blue_direct:
        side_mode = "direct"
    elif not red_direct and not blue_direct:
        side_mode = "fallback"
    elif red_direct and not blue_direct:
        side_mode = "red_direct"
    else:
        side_mode = "blue_direct"

    edges = sum(
        neighbor in traversable
        for cell in traversable
        for neighbor in _neighbors(cell)
    ) // 2
    neutral_components = _components(neutral)
    unequal_neutral = {
        cell for cell in neutral if red_dist.get(cell) != blue_dist.get(cell)
    }
    return {
        "red": red,
        "blue": blue,
        "traversable": traversable,
        "gray": gray,
        "red_dist": red_dist,
        "blue_dist": blue_dist,
        "reachable": reachable,
        "path_length": path_length,
        "ordered_path": ordered_path,
        "path_gray": path_gray,
        "off_path": off_path,
        "red_side": red_side,
        "blue_side": blue_side,
        "neutral": neutral,
        "red_direct": red_direct,
        "blue_direct": blue_direct,
        "red_fallback": red_fallback,
        "blue_fallback": blue_fallback,
        "turns": turns,
        "orientation": orientation,
        "path_shape": path_shape,
        "side_mode": side_mode,
        "edges": edges,
        "neutral_components": neutral_components,
        "unequal_neutral": unequal_neutral,
    }


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python audit mirror of the selected Racket authority."""
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    for row, col in analysis.get("gray", set()):
        if (row, col) in analysis.get("path_gray", set()):
            output[row][col] = 4
        elif (row, col) in analysis.get("red_side", set()):
            output[row][col] = 2
        elif (row, col) in analysis.get("blue_side", set()):
            output[row][col] = 1
        else:
            output[row][col] = 4
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the corridor-tree grammar while accepting every canonical input."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    height = len(grid)
    width = len(grid[0])
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 2, 5}:
        errors.append(f"input palette {sorted(palette)} is not a subset of {{0,1,2,5}}")
    if 0 not in palette:
        errors.append("background color 0 is absent")
    red_count = sum(value == 2 for row in grid for value in row)
    blue_count = sum(value == 1 for row in grid for value in row)
    if red_count != 1:
        errors.append(f"expected exactly one red(2) seed, found {red_count}")
    if blue_count != 1:
        errors.append(f"expected exactly one blue(1) seed, found {blue_count}")
    if errors:
        return errors

    analysis = _analyze(grid)
    traversable = analysis["traversable"]
    if not analysis["gray"]:
        errors.append("at least one gray(5) corridor cell is required")
    if not analysis["reachable"]:
        errors.append("red and blue seeds are not connected through colors {1,2,5}")
        return errors
    reachable_from_red = set(analysis["red_dist"])
    if reachable_from_red != traversable:
        errors.append("all nonzero corridor cells must belong to one connected component")
    if analysis["edges"] != len(traversable) - 1:
        errors.append("the nonzero corridor graph must be acyclic")
    if len(analysis["path_gray"]) < 3:
        errors.append("the red-to-blue path needs at least three gray cells")
    max_degree = max(
        (sum(neighbor in traversable for neighbor in _neighbors(cell)) for cell in traversable),
        default=0,
    )
    if max_degree > 4:
        errors.append(f"corridor junction degree exceeds 4 (found {max_degree})")
    if analysis["red_side"] & analysis["blue_side"]:
        errors.append("red-only and blue-only regions overlap")
    if not analysis["red_side"]:
        errors.append("scene lacks a red-only off-path region")
    if not analysis["blue_side"]:
        errors.append("scene lacks a blue-only off-path region")
    if not analysis["neutral"]:
        errors.append("scene lacks an interior neutral off-path region")
    if analysis["path_shape"] not in PATH_SHAPES:
        errors.append(
            f"path must be straight or have exactly two turns; observed {analysis['path_shape']}"
        )
    if analysis["orientation"] not in ORIENTATIONS:
        errors.append("path orientation is ambiguous")
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append(f"corridor canvas {height}x{width} is outside the supported grammar")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Executable strict empirical-manifold predicate for all four canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analyze(grid)
    dims = (len(grid), len(grid[0]))
    if dims not in _CANONICAL_DIMS:
        reasons.append(f"dimensions {dims} are outside canonical profiles {sorted(_CANONICAL_DIMS)}")
    palette = {value for row in grid for value in row}
    if palette != {0, 1, 2, 5}:
        reasons.append(f"canonical input palette must be exactly {{0,1,2,5}}, found {sorted(palette)}")
    if len(analysis["path_gray"]) not in {5, 6}:
        reasons.append("canonical red-blue paths contain exactly five or six gray cells")
    if len(analysis["gray"]) not in {11, 12, 13}:
        reasons.append("canonical inputs contain 11..13 gray cells")
    if analysis["side_mode"] not in {"direct", "fallback"}:
        reasons.append("canonical inputs use both-direct or both-fallback seed ends")
    if not 1 <= len(analysis["red_side"]) <= 2:
        reasons.append("canonical red-only support has one or two cells")
    if not 2 <= len(analysis["blue_side"]) <= 3:
        reasons.append("canonical blue-only support has two or three cells")
    if not 2 <= len(analysis["neutral"]) <= 3:
        reasons.append("canonical neutral support has two or three cells")
    return reasons


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact declared semantic axis from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    analysis = _analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "orientation": analysis["orientation"],
        "path_shape": analysis["path_shape"],
        "side_mode": analysis["side_mode"],
    }


def _rival_identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _rival_all_gray_yellow(grid: Grid) -> Grid:
    return [[4 if value == 5 else value for value in row] for row in grid]


def _rival_path_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    for row, col in analysis.get("path_gray", set()):
        output[row][col] = 4
    return output


def _rival_nearest_seed(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    for row, col in analysis.get("gray", set()):
        red_distance = analysis["red_dist"].get((row, col), 10**9)
        blue_distance = analysis["blue_dist"].get((row, col), 10**9)
        output[row][col] = 2 if red_distance < blue_distance else (1 if blue_distance < red_distance else 4)
    return output


def _output_with_side_start_policy(grid: Grid, policy: str) -> Grid:
    analysis = _analyze(grid)
    off_path = set(analysis.get("off_path", set()))
    if policy == "direct":
        red_starts = analysis.get("red_direct", set())
        blue_starts = analysis.get("blue_direct", set())
    else:
        red_starts = analysis.get("red_fallback", set())
        blue_starts = analysis.get("blue_fallback", set())
    red_side = _flood(red_starts, off_path)
    blue_side = _flood(blue_starts, off_path)
    output = _copy_grid(grid)
    for row, col in analysis.get("gray", set()):
        if (row, col) in analysis.get("path_gray", set()):
            output[row][col] = 4
        elif (row, col) in red_side:
            output[row][col] = 2
        elif (row, col) in blue_side:
            output[row][col] = 1
        else:
            output[row][col] = 4
    return output


def _rival_direct_only(grid: Grid) -> Grid:
    return _output_with_side_start_policy(grid, "direct")


def _rival_fallback_only(grid: Grid) -> Grid:
    return _output_with_side_start_policy(grid, "fallback")


def _rival_straight_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    return rule_mirror(grid) if analysis.get("turns") == 0 else _rival_all_gray_yellow(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _rival_identity,
    "all_gray_yellow": _rival_all_gray_yellow,
    "path_only": _rival_path_only,
    "nearest_seed_voronoi": _rival_nearest_seed,
    "direct_starts_only": _rival_direct_only,
    "fallback_starts_only": _rival_fallback_only,
    "straight_paths_only": _rival_straight_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _lawful_analysis(grid: Grid) -> dict[str, Any] | None:
    return None if self_check(grid) else _analyze(grid)


def _witness_red_side(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["red_side"])


def _witness_blue_side(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["blue_side"])


def _witness_neutral(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["neutral"])


def _witness_direct(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["side_mode"] == "direct")


def _witness_fallback(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["side_mode"] == "fallback")


def _witness_mixed(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["side_mode"] in {"red_direct", "blue_direct"})


def _witness_two_turn(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["path_shape"] == "two_turn")


def _witness_nearest_conflict(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["unequal_neutral"])


SEMANTIC_WITNESSES = {
    "red_only_region": _witness_red_side,
    "blue_only_region": _witness_blue_side,
    "neutral_region": _witness_neutral,
    "direct_seed_ends": _witness_direct,
    "fallback_seed_ends": _witness_fallback,
    "mixed_seed_ends": _witness_mixed,
    "two_turn_path": _witness_two_turn,
    "neutral_not_nearest_seed": _witness_nearest_conflict,
}

WITNESS_RIVALS = {
    "red_only_region": ["identity", "all_gray_yellow", "path_only"],
    "blue_only_region": ["identity", "all_gray_yellow", "path_only"],
    "neutral_region": ["nearest_seed_voronoi"],
    "direct_seed_ends": ["fallback_starts_only"],
    "fallback_seed_ends": ["direct_starts_only"],
    "mixed_seed_ends": ["direct_starts_only", "fallback_starts_only"],
    "two_turn_path": ["straight_paths_only"],
    "neutral_not_nearest_seed": ["nearest_seed_voronoi"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival fits all demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    candidates: dict[str, Callable[[Grid], Grid]] = {
        "true": rule_mirror,
        **SEMANTIC_RIVALS,
    }
    survivors = set(candidates)
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        grid = demo.get("input")
        official = demo.get("output")
        grammar_errors = self_check(grid)
        if grammar_errors:
            reasons.append(f"demo {index} input is outside the declared grammar: {grammar_errors[0]}")
            continue
        outputs = {name: fn(_copy_grid(grid)) for name, fn in candidates.items()}
        if outputs["true"] != official:
            reasons.append(f"demo {index} output disagrees with the Python audit mirror")
            continue
        survivors &= {name for name, output in outputs.items() if output == official}

    query_grid = query.get("input")
    query_answer = query.get("output")
    grammar_errors = self_check(query_grid)
    if grammar_errors:
        reasons.append(f"query input is outside the declared grammar: {grammar_errors[0]}")
        return reasons
    query_outputs = {name: fn(_copy_grid(query_grid)) for name, fn in candidates.items()}
    if query_outputs["true"] != query_answer:
        reasons.append("query output disagrees with the Python audit mirror")
        return reasons
    for name in sorted(survivors - {"true"}):
        if query_outputs[name] != query_answer:
            reasons.append(
                f"competitor {name!r} fits every demo but gives a different query answer"
            )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return PROFILE_SCHEDULE[int(sample_index) % EXAMPLES_NEEDED]


def _draw_int_axis(ctx, overrides: dict[str, Any], label: str, scheduled: Iterable[int], lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, tuple(scheduled)))


def _draw_choice_axis(ctx, overrides: dict[str, Any], label: str, scheduled: Iterable[str], legal: Iterable[str]) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, tuple(legal)))
    return str(ctx.draw_choice(label, tuple(scheduled)))


def _make_path(height: int, width: int, path_shape: str, rng) -> list[Cell]:
    if path_shape == "straight":
        row = rng.randint(2, height - 3)
        return [(row, col) for col in range(1, width - 1)]

    upper = rng.randint(2, height - 5) if height >= 8 else 2
    direction = 1 if upper + 2 <= height - 3 else -1
    lower = upper + 2 * direction
    turn_col = max(3, min(width - 4, width // 2))
    path: list[Cell] = [(upper, col) for col in range(1, turn_col + 1)]
    step = 1 if lower > upper else -1
    path.extend((row, turn_col) for row in range(upper + step, lower + step, step))
    path.extend((lower, col) for col in range(turn_col + 1, width - 1))
    return path


def _branch_candidates(
    attach: Cell,
    occupied: set[Cell],
    height: int,
    width: int,
    desired_length: int,
    rng,
) -> list[list[Cell]]:
    directions = list(_DIR4)
    rng.shuffle(directions)
    candidates: list[list[Cell]] = []
    for length in range(desired_length, 0, -1):
        for dr, dc in directions:
            branch: list[Cell] = []
            valid = True
            for step in range(1, length + 1):
                cell = (attach[0] + dr * step, attach[1] + dc * step)
                if not _in_bounds(cell, height, width) or cell in occupied:
                    valid = False
                    break
                allowed_neighbor = attach if step == 1 else branch[-1]
                occupied_neighbors = {
                    neighbor
                    for neighbor in _neighbors(cell)
                    if neighbor in occupied or neighbor in branch
                }
                if occupied_neighbors != {allowed_neighbor}:
                    valid = False
                    break
                branch.append(cell)
            if valid:
                candidates.append(branch)
        if candidates:
            return candidates
    return []


def _place_branches(
    grid: Grid,
    occupied: set[Cell],
    specs: list[tuple[str, Cell, int]],
    rng,
) -> dict[str, list[Cell]]:
    """Place all branch rays jointly so an early random choice cannot trap a later role."""
    height, width = len(grid), len(grid[0])

    def search(
        index: int,
        current_occupied: set[Cell],
        chosen: dict[str, list[Cell]],
    ) -> dict[str, list[Cell]] | None:
        if index == len(specs):
            return chosen
        name, attach, desired_length = specs[index]
        candidates = _branch_candidates(
            attach, current_occupied, height, width, desired_length, rng
        )
        rng.shuffle(candidates)
        for branch in candidates:
            result = search(
                index + 1,
                current_occupied | set(branch),
                {**chosen, name: branch},
            )
            if result is not None:
                return result
        return None

    result = search(0, set(occupied), {})
    if result is None:
        raise ValueError("unable to place the required branch roles jointly")
    for branch in result.values():
        for row, col in branch:
            grid[row][col] = 5
            occupied.add((row, col))
    return result


def _transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = "medium" if difficulty is None else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    slot = int(sample_index) % EXAMPLES_NEEDED
    profile = PROFILE_SCHEDULE[slot]
    rng = ctx.draw_rng("layout")

    orientation = _draw_choice_axis(
        ctx, overrides, "orientation", ORIENTATIONS, ORIENTATIONS
    )
    if slot < 2:
        # Canonical-profile anchor slots must retain a 9- or 10-cell primary
        # dimension.  The output dimensions are orientation-aware: (9, 9) is
        # the only canonical dimension whose vertical primary axis can carry
        # the canonical five gray path cells.
        anchor_h, anchor_w = (
            _ANCHOR_DIMS[band][slot]
            if orientation == "horizontal"
            else (9, 9)
        )
        scheduled_h = (anchor_h,)
        scheduled_w = (anchor_w,)
    else:
        scheduled_h, scheduled_w = _GENERAL_DIMS[band]
    grid_h = _draw_int_axis(ctx, overrides, "grid_h", scheduled_h, 7, 15)
    grid_w = _draw_int_axis(ctx, overrides, "grid_w", scheduled_w, 7, 17)
    scheduled_shape = ("straight",) if slot < 2 else ("two_turn",)
    path_shape = _draw_choice_axis(
        ctx, overrides, "path_shape", scheduled_shape, PATH_SHAPES
    )
    scheduled_side_mode = (SIDE_MODES[slot],)
    side_mode = _draw_choice_axis(
        ctx, overrides, "side_mode", scheduled_side_mode, SIDE_MODES
    )

    base_h, base_w = (grid_h, grid_w) if orientation == "horizontal" else (grid_w, grid_h)
    grid = full_grid(base_h, base_w, 0)
    path = _make_path(base_h, base_w, path_shape, rng)
    if len(path) < 5:
        raise ValueError("declared dimensions cannot support the corridor grammar")
    occupied = set(path)
    for row, col in path[1:-1]:
        grid[row][col] = 5
    red, blue = path[0], path[-1]
    grid[red[0]][red[1]] = 2
    grid[blue[0]][blue[1]] = 1

    if slot == 0:
        red_length, blue_length, neutral_length = 1, 2, 3
    elif slot == 1:
        red_length, blue_length, neutral_length = 2, 2, 3
    else:
        ranges = {"easy": (1, 2), "medium": (1, 3), "hard": (2, 3)}[band]
        red_length = rng.randint(*ranges)
        blue_length = rng.randint(*ranges)
        neutral_length = rng.randint(*ranges)

    red_attach = red if side_mode in {"direct", "red_direct"} else path[1]
    blue_attach = blue if side_mode in {"direct", "blue_direct"} else path[-2]

    # Put the neutral branch closer to one seed than the other. It still becomes
    # yellow, explicitly refuting a nearest-seed/Voronoi shortcut. Joint branch
    # placement backtracks over directions so exact small-canvas overrides are
    # honored rather than silently enlarged or randomly rejected.
    interior = list(range(2, len(path) - 2))
    if not interior:
        raise ValueError("path has no interior attachment point")
    preferred_index = interior[0] if slot in {0, 2} else interior[-1]
    neutral_candidates = [preferred_index] + [idx for idx in interior if idx != preferred_index]
    placed = False
    for index in neutral_candidates:
        try:
            _place_branches(
                grid,
                occupied,
                [
                    ("neutral", path[index], neutral_length),
                    ("red", red_attach, red_length),
                    ("blue", blue_attach, blue_length),
                ],
                rng,
            )
            placed = True
            break
        except ValueError:
            continue
    if not placed:
        raise ValueError("unable to place the required red/blue/neutral branches")

    if orientation == "vertical":
        grid = _transpose(grid)

    observed = observe_overrides(grid)
    expected = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "orientation": orientation,
        "path_shape": path_shape,
        "side_mode": side_mode,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes {expected} but observed {observed}")
    return grid
