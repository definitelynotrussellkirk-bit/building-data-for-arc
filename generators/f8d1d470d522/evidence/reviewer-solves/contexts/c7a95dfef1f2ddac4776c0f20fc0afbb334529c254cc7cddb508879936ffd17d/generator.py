"""Generator for clean-corridor path task f8d1d470d522.

Color 8 is walkable unless it is cardinally adjacent to color 7.  The two
color-9 markers are always walkable.  Connect the markers by the shortest
legal path, breaking equal-length ties by the fewest turns, and paint that
path color 9.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f8d1d470d522"
VERSION = "3.0.0"
TASK_ID = "f8d1d470d522"
RULE_HASH = "f1588fca855d"

SUMMARY = (
    "Construct a branching color-8 route network between two color-9 "
    "markers. Color-7 obstacles disable adjacent 8 cells and thereby alter "
    "the route. The selected route is shortest first and fewest-turns "
    "second; lessons cover both a unique shortest route and an equal-length "
    "tie with one uniquely straightest route."
)

INVARIANTS = [
    "zero is background and the source uses only colors 0, 7, 8, and 9",
    "exactly two color-9 markers are connected through a branching 8 network",
    "every scene contains at least one 8 cell disabled by adjacency to 7",
    "general lessons make the color-7 obstacle causally change the route",
    "the chosen route is shortest and then has the fewest direction changes",
    "the optimal fewest-turn route is unique and is painted color 9",
    "unused color-8 branches remain unchanged in the output",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_CARDINAL = ((0, 1), (1, 0), (0, -1), (-1, 0))
_SELECTION_MODES = ("unique_shortest", "fewest_turns")
_PROFILE_PRIOR = 0.12
_COUNT_CAP = 1_000_000_000

AXES = {
    "selection_mode": {
        "type": "str",
        "default": "difficulty-aware choice",
        "valid": "unique_shortest|fewest_turns",
    },
}

# The four distinct public scenes (three train and one held-out).  Keeping the
# complete source morphology matters here: the public task uses dense route
# networks, not a single corridor.  Profiles are augmented only by lawful D4
# transforms and zero padding.
_PROFILE_ROWS = (
    (
        "000000000",
        "088888889",
        "080008080",
        "088878780",
        "080808080",
        "088888880",
        "000000090",
    ),
    (
        "000000000",
        "088808880",
        "080878080",
        "980888089",
        "080000080",
        "088888880",
        "000000000",
    ),
    (
        "000090000",
        "088888880",
        "087000080",
        "088888880",
        "080080080",
        "088888880",
        "080000780",
        "088888880",
        "000090000",
    ),
    (
        "090000090",
        "088888880",
        "080878080",
        "088888880",
        "080878080",
        "088888880",
        "080808080",
        "088888880",
        "000000000",
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    mode = overrides.get("selection_mode")
    if mode is not None and (
        type(mode) is not str or mode not in _SELECTION_MODES
    ):
        raise ValueError(
            "selection_mode must be unique_shortest or fewest_turns"
        )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _is_rectangular_grid(grid):
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and all(
            isinstance(row, (list, tuple, str)) and bool(row)
            for row in grid
        )
        and len({len(row) for row in grid}) == 1
    )


def _adjacent_to_seven(grid, row, col):
    height = len(grid)
    width = len(grid[0])
    return any(
        0 <= row + dr < height
        and 0 <= col + dc < width
        and grid[row + dr][col + dc] == 7
        for dr, dc in _CARDINAL
    )


def _solve(grid, *, ignore_obstacles=False):
    """Return shortest/fewest-turn path facts, or ``None`` if unreachable."""
    height = len(grid)
    width = len(grid[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(markers) != 2:
        return None
    start, goal = markers

    allowed = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (
            grid[row][col] == 9
            or (
                grid[row][col] == 8
                and (
                    ignore_obstacles
                    or not _adjacent_to_seven(grid, row, col)
                )
            )
        )
    }

    distances = {start: 0}
    queue = deque((start,))
    while queue:
        row, col = queue.popleft()
        next_distance = distances[(row, col)] + 1
        for dr, dc in _CARDINAL:
            neighbor = row + dr, col + dc
            if neighbor in allowed and neighbor not in distances:
                distances[neighbor] = next_distance
                queue.append(neighbor)
    if goal not in distances:
        return None

    goal_distance = distances[goal]
    by_distance = [[] for _index in range(goal_distance + 1)]
    for cell, distance in distances.items():
        if distance <= goal_distance:
            by_distance[distance].append(cell)

    shortest_counts = {start: 1}
    for distance in range(goal_distance):
        for row, col in by_distance[distance]:
            count = shortest_counts.get((row, col), 0)
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if distances.get(neighbor) == distance + 1:
                    shortest_counts[neighbor] = min(
                        _COUNT_CAP,
                        shortest_counts.get(neighbor, 0) + count,
                    )

    # State value is (fewest turns, number of paths attaining that value,
    # representative path).  Restricting transitions to the BFS DAG first
    # enforces shortest length, exactly matching the rule's primary criterion.
    states = {(start, None): (0, 1, (start,))}
    for distance in range(goal_distance):
        current_states = [
            (key, value)
            for key, value in states.items()
            if distances[key[0]] == distance
        ]
        for ((row, col), previous_direction), (
            turns,
            path_count,
            path,
        ) in current_states:
            for direction in _CARDINAL:
                dr, dc = direction
                neighbor = row + dr, col + dc
                if distances.get(neighbor) != distance + 1:
                    continue
                next_turns = turns + (
                    previous_direction is not None
                    and previous_direction != direction
                )
                key = neighbor, direction
                candidate_path = path + (neighbor,)
                incumbent = states.get(key)
                if incumbent is None or next_turns < incumbent[0]:
                    states[key] = (
                        next_turns,
                        path_count,
                        candidate_path,
                    )
                elif next_turns == incumbent[0]:
                    states[key] = (
                        incumbent[0],
                        min(
                            _COUNT_CAP,
                            incumbent[1] + path_count,
                        ),
                        min(incumbent[2], candidate_path),
                    )

    goal_states = [
        value
        for (cell, _direction), value in states.items()
        if cell == goal
    ]
    if not goal_states:
        return None
    fewest_turns = min(value[0] for value in goal_states)
    optimal_states = [
        value for value in goal_states if value[0] == fewest_turns
    ]
    optimal_path_count = min(
        _COUNT_CAP,
        sum(value[1] for value in optimal_states),
    )
    path = min(value[2] for value in optimal_states)
    output = [row[:] for row in grid]
    for row, col in path:
        output[row][col] = 9
    return {
        "start": start,
        "goal": goal,
        "distance": goal_distance,
        "shortest_path_count": shortest_counts[goal],
        "fewest_turns": fewest_turns,
        "optimal_path_count": optimal_path_count,
        "path": path,
        "output": output,
    }


def _scene_analysis(grid):
    if not _is_rectangular_grid(grid):
        return None, None, ["grid must be non-empty and rectangular"]
    coerced = _coerce_grid(grid)
    height = len(coerced)
    width = len(coerced[0])
    errors = []
    if not 5 <= height <= 25 or not 5 <= width <= 25:
        errors.append("grid dimensions must be between 5 and 25")
    if any(
        type(value) is not int or value not in (0, 7, 8, 9)
        for row in coerced
        for value in row
    ):
        errors.append("cells must use only colors 0, 7, 8, and 9")
        return coerced, None, errors

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 9
    ]
    obstacles = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 7
    ]
    eight_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 8
    ]
    blocked_eights = [
        cell
        for cell in eight_cells
        if _adjacent_to_seven(coerced, *cell)
    ]
    if len(markers) != 2:
        errors.append("exactly two color-9 markers are required")
    if not 1 <= len(obstacles) <= 2:
        errors.append("one or two color-7 obstacles are required")
    if len(eight_cells) < 20:
        errors.append("at least twenty color-8 route cells are required")
    if not blocked_eights:
        errors.append("at least one color-8 cell must be disabled by color 7")
    if errors:
        return coerced, None, errors

    solution = _solve(coerced)
    if solution is None:
        errors.append("the markers must have a legal connecting route")
        return coerced, None, errors
    if solution["optimal_path_count"] != 1:
        errors.append("the shortest/fewest-turn route must be unique")
    path_eights = {
        cell
        for cell in solution["path"]
        if coerced[cell[0]][cell[1]] == 8
    }
    unused_eights = set(eight_cells) - path_eights
    if not unused_eights:
        errors.append("at least one unused color-8 branch must remain")
    if errors:
        return coerced, None, errors

    relaxed = _solve(coerced, ignore_obstacles=True)
    obstacle_causal = (
        relaxed is not None
        and relaxed["path"] != solution["path"]
    )
    selection_mode = (
        "unique_shortest"
        if solution["shortest_path_count"] == 1
        else "fewest_turns"
    )
    return coerced, {
        "height": height,
        "width": width,
        "markers": tuple(markers),
        "obstacles": tuple(obstacles),
        "blocked_eights": tuple(blocked_eights),
        "blocked_count": len(blocked_eights),
        "eight_count": len(eight_cells),
        "unused_eights": tuple(sorted(unused_eights)),
        "unused_count": len(unused_eights),
        "selection_mode": selection_mode,
        "obstacle_causal": obstacle_causal,
        **solution,
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"selection_mode": features["selection_mode"]}


def rule_mirror(grid):
    if not _is_rectangular_grid(grid):
        raise ValueError("grid must be non-empty and rectangular")
    coerced = _coerce_grid(grid)
    solution = _solve(coerced)
    if solution is None:
        raise ValueError("grid has no legal path between two color-9 markers")
    return [row[:] for row in solution["output"]]


def _grid_from_rows(rows):
    return [[int(value) for value in row] for row in rows]


def _rotate_90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _reflect_horizontal(grid):
    return [row[::-1] for row in grid]


def _transform(grid, transform):
    transformed = _coerce_grid(grid)
    if transform >= 4:
        transformed = _reflect_horizontal(transformed)
    for _turn in range(transform % 4):
        transformed = _rotate_90(transformed)
    return transformed


def _d4_variants(grid):
    return tuple(
        _transform(grid, transform) for transform in range(8)
    )


def _crop_zero(grid):
    coerced = _coerce_grid(grid)
    occupied = [
        (row, col)
        for row in range(len(coerced))
        for col in range(len(coerced[0]))
        if coerced[row][col] != 0
    ]
    if not occupied:
        return coerced
    top = min(row for row, _col in occupied)
    bottom = max(row for row, _col in occupied)
    left = min(col for _row, col in occupied)
    right = max(col for _row, col in occupied)
    return [
        row[left:right + 1]
        for row in coerced[top:bottom + 1]
    ]


def _signature(grid):
    return tuple(tuple(row) for row in _crop_zero(grid))


_PROFILE_GRIDS = tuple(
    _grid_from_rows(rows) for rows in _PROFILE_ROWS
)
_PROFILE_SIGNATURE_TO_INDEX = {
    _signature(variant): index
    for index, source in enumerate(_PROFILE_GRIDS)
    for variant in _d4_variants(source)
}


def canonical_profile_index(grid):
    if not _is_rectangular_grid(grid):
        return None
    return _PROFILE_SIGNATURE_TO_INDEX.get(_signature(grid))


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _polyline(points):
    cells = []
    for index, (start, end) in enumerate(zip(points, points[1:])):
        start_row, start_col = start
        end_row, end_col = end
        if start_row != end_row and start_col != end_col:
            raise ValueError("polyline segments must be orthogonal")
        row_step = (
            0
            if start_row == end_row
            else 1 if end_row > start_row else -1
        )
        col_step = (
            0
            if start_col == end_col
            else 1 if end_col > start_col else -1
        )
        length = max(
            abs(end_row - start_row),
            abs(end_col - start_col),
        )
        segment = [
            (
                start_row + row_step * step,
                start_col + col_step * step,
            )
            for step in range(length + 1)
        ]
        cells.extend(segment if index == 0 else segment[1:])
    return tuple(cells)


def _build_unique_shortest(rng):
    height = rng.choice((9, 11, 13, 15))
    width = rng.choice((9, 11, 13, 15, 17))
    middle = height // 2
    left = 1
    right = width - 2
    start = middle, 0
    goal = middle, width - 1
    direct = _polyline((start, goal))
    upper = _polyline((
        start,
        (middle, left),
        (middle - 3, left),
        (middle - 3, right),
        (middle, right),
        goal,
    ))
    lower = _polyline((
        start,
        (middle, left),
        (middle + 3, left),
        (middle + 3, right),
        (middle, right),
        goal,
    ))
    route_cells = set(direct) | set(upper) | set(lower)
    interior_columns = list(range(left + 1, right))
    direct_block_column = rng.choice(interior_columns)
    lower_columns = [
        col for col in interior_columns
        if col != direct_block_column
    ]
    lower_block_column = rng.choice(lower_columns)
    obstacles = {
        (middle - 1, direct_block_column),
        (middle + 2, lower_block_column),
    }
    grid = full_grid(height, width, 0)
    for row, col in route_cells:
        grid[row][col] = 8
    for row, col in obstacles:
        grid[row][col] = 7
    grid[start[0]][start[1]] = 9
    grid[goal[0]][goal[1]] = 9
    return grid


def _spaced_cuts(width, rng):
    left = 1
    right = width - 2
    candidates = [
        (a, b, c, d)
        for a in range(left + 1, right)
        for b in range(a + 2, right)
        for c in range(b + 2, right)
        for d in range(c + 2, right)
    ]
    return rng.choice(candidates)


def _build_fewest_turns(rng):
    height = rng.choice((13, 15, 17))
    width = rng.choice((13, 15, 17))
    middle = height // 2
    left = 1
    right = width - 2
    start = middle, 0
    goal = middle, width - 1
    a, b, c, d = _spaced_cuts(width, rng)
    direct = _polyline((start, goal))
    upper = _polyline((
        start,
        (middle, left),
        (middle - 5, left),
        (middle - 5, right),
        (middle, right),
        goal,
    ))
    lower = _polyline((
        start,
        (middle, left),
        (middle + 3, left),
        (middle + 3, a),
        (middle + 4, a),
        (middle + 4, b),
        (middle + 3, b),
        (middle + 3, c),
        (middle + 4, c),
        (middle + 4, d),
        (middle + 3, d),
        (middle + 3, right),
        (middle, right),
        goal,
    ))
    route_cells = set(direct) | set(upper) | set(lower)
    obstacle_column = rng.choice(
        list(range(left + 1, right))
    )
    obstacle = middle - 1, obstacle_column
    grid = full_grid(height, width, 0)
    for row, col in route_cells:
        grid[row][col] = 8
    grid[obstacle[0]][obstacle[1]] = 7
    grid[start[0]][start[1]] = 9
    grid[goal[0]][goal[1]] = 9
    return grid


def _pad_zero(grid, rng):
    top = rng.randint(0, 3)
    bottom = rng.randint(0, 3)
    left = rng.randint(0, 3)
    right = rng.randint(0, 3)
    width = len(grid[0]) + left + right
    padded = [[0] * width for _row in range(top)]
    padded.extend(
        [([0] * left) + row[:] + ([0] * right) for row in grid]
    )
    padded.extend([[0] * width for _row in range(bottom)])
    return padded


def _augment_scene(grid, rng):
    transformed = _transform(grid, rng.randrange(8))
    return _pad_zero(transformed, rng)


def _draw_profile(index, rng):
    return _augment_scene(_PROFILE_GRIDS[index], rng)


def _construct_general(mode, rng):
    builder = (
        _build_unique_shortest
        if mode == "unique_shortest"
        else _build_fewest_turns
    )
    for _attempt in range(120):
        grid = _augment_scene(builder(rng), rng)
        _coerced, features, errors = _scene_analysis(grid)
        if (
            not errors
            and features["selection_mode"] == mode
            and features["obstacle_causal"]
            and canonical_profile_index(grid) is None
        ):
            return grid
    raise RuntimeError(
        f"could not construct a valid {mode} route lesson"
    )


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
    band = difficulty or "medium"
    has_override = overrides.get("selection_mode") is not None

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_GRIDS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            profile_index,
            ctx.draw_rng("profile_transform"),
        )
        observed_mode = observe_overrides(grid)["selection_mode"]
        ctx.draw_choice("selection_mode", (observed_mode,))
    else:
        options = {
            "easy": (
                "unique_shortest",
                "unique_shortest",
                "unique_shortest",
                "fewest_turns",
            ),
            "medium": (
                "unique_shortest",
                "unique_shortest",
                "fewest_turns",
                "fewest_turns",
            ),
            "hard": (
                "unique_shortest",
                "fewest_turns",
                "fewest_turns",
                "fewest_turns",
            ),
        }[band]
        if has_override:
            options = _SELECTION_MODES
        mode = ctx.draw_choice("selection_mode", options)
        grid = _construct_general(
            mode,
            ctx.draw_rng("route_network"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
