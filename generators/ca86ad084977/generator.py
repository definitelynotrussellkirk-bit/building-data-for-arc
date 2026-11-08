"""Sampler for task ca86ad084977: connect ordered checkpoints through a maze.

The selected Racket authority performs independent 4-neighbor breadth-first
searches 2->3, 3->4, and 4->7 through every non-5 cell.  Neighbors are explored
up, down, left, right.  Every interior cell of every selected path is painted
cyan(8), including another checkpoint when a later segment crosses it.

The public labels leave two important alternatives underdetermined: swapping
left/right BFS priority still fits all five examples, while prose-only readings
may incorrectly preserve crossed checkpoints.  The production schedule therefore
alternates canonical-like sparse mazes with a compact scene that refutes both
rivals.  Any four-pair lesson contains two such witnesses, so every one-query
rotation leaves one in the demonstrations.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ca86ad084977"
TASK_ID = GENERATOR_ID
RULE_HASH = "1c1d9560813f"
VERSION = "3.0.0"
SUMMARY = (
    "On a zero-background grid with gray(5) wall objects and one checkpoint "
    "each of colors 2,3,4,7, find shortest 4-neighbor paths 2->3, 3->4, and "
    "4->7 through non-wall cells. Resolve equal paths in up/down/left/right "
    "BFS order, then paint every interior route cell cyan(8), even when that "
    "cell was another checkpoint."
)

INVARIANTS = [
    "background is 0; walls are 5; checkpoints 2,3,4,7 occur exactly once",
    "ordinary draws use 12..13 rows, 12..14 columns, and 2..3 sparse wall components",
    "all three ordered legs are reachable and produce a non-identity output",
    "semantic_witness scenes expose both left-before-right BFS and checkpoint overwrite",
    "canonical_maze scenes retain sparse irregular barriers without either targeted ambiguity",
]

SCENE_PATTERNS = ("canonical_maze", "semantic_witness")
SCHEDULE_PROFILES = SCENE_PATTERNS
LESSON_SCHEDULE_PERIOD = 4

AXES = {
    "grid_h": {
        "type": "int",
        "default": "12..13; canonical shape profiles strongly weighted",
        "valid": "12..13",
    },
    "grid_w": {
        "type": "int",
        "default": "12..14; canonical shape profiles strongly weighted",
        "valid": "12..14",
    },
    "scene_pattern": {
        "type": "str",
        "default": "alternating canonical_maze|semantic_witness lesson schedule",
        "valid": "|".join(SCENE_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

_CHECKPOINTS = (2, 3, 4, 7)
_LEGS = ((2, 3), (3, 4), (4, 7))
# Racket's cardinal-deltas order in the pinned runtime.
_UP_DOWN_LEFT_RIGHT = ((-1, 0), (1, 0), (0, -1), (0, 1))
# Strongest task-local canonical-fitting priority rival.
_UP_DOWN_RIGHT_LEFT = ((-1, 0), (1, 0), (0, 1), (0, -1))

# Five labeled shape profiles plus the one missing cell in the advertised
# 12..13 x 12..14 envelope.  The weights mirror source support without replaying
# any canonical layout.
_CANONICAL_PROFILES = ((12, 13), (13, 14), (12, 12), (12, 14), (13, 12))
_ALL_PROFILES = tuple((height, width) for height in range(12, 14) for width in range(12, 15))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the ordinary production branch for source-bound lesson audits."""
    del seed, difficulty
    return SCENE_PATTERNS[int(sample_index) % len(SCENE_PATTERNS)]


def _validate_call_arguments(seed, sample_index, difficulty) -> None:
    if type(seed) is not int:
        raise ValueError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise ValueError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, lower, upper in (("grid_h", 12, 13), ("grid_w", 12, 14)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not lower <= value <= upper:
            raise ValueError(f"{name}={value} outside [{lower}, {upper}]")
    pattern = overrides.get("scene_pattern")
    if pattern is not None:
        if type(pattern) is not str:
            raise ValueError(
                f"scene_pattern must be a string, not {type(pattern).__name__}"
            )
        if pattern not in SCENE_PATTERNS:
            raise ValueError(
                f"scene_pattern={pattern!r} not in {list(SCENE_PATTERNS)}"
            )


def _profile_options(difficulty) -> tuple[tuple[int, int], ...]:
    if difficulty == "easy":
        canonical_weight, broad_weight = 30, 1
    elif difficulty == "hard":
        canonical_weight, broad_weight = 20, 2
    else:
        canonical_weight, broad_weight = 25, 1
    return (
        tuple(profile for profile in _CANONICAL_PROFILES for _ in range(canonical_weight))
        + tuple(profile for profile in _ALL_PROFILES for _ in range(broad_weight))
    )


def _weighted_axis(ctx, name: str, values, anchor: int) -> int:
    return ctx.draw_choice(name, tuple(values) + (anchor,) * 40)


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return None
    return len(grid), width


def _checkpoint_positions(grid):
    positions = {color: [] for color in _CHECKPOINTS}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in positions:
                positions[value].append((row, col))
    if any(len(points) != 1 for points in positions.values()):
        return None
    return {color: points[0] for color, points in positions.items()}


def _bfs_path(grid, start, goal, order):
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}
    while queue:
        point = queue.popleft()
        if point == goal:
            break
        for delta_row, delta_col in order:
            neighbor = point[0] + delta_row, point[1] + delta_col
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and grid[neighbor[0]][neighbor[1]] != 5
                and neighbor not in parent
            ):
                parent[neighbor] = point
                queue.append(neighbor)
    if goal not in parent:
        return []
    path = []
    point = goal
    while point is not None:
        path.append(point)
        point = parent[point]
    return list(reversed(path))


def _solve_with_order(grid, order, *, preserve_checkpoints=False):
    positions = _checkpoint_positions(grid)
    if positions is None:
        return [list(row) for row in grid]
    path_cells = set()
    for first, second in _LEGS:
        path = _bfs_path(grid, positions[first], positions[second], order)
        path_cells.update(path[1:-1])
    output = [list(row) for row in grid]
    for row, col in path_cells:
        if not preserve_checkpoints or output[row][col] == 0:
            output[row][col] = 8
    return output


def _selected_output(grid):
    return _solve_with_order(grid, _UP_DOWN_LEFT_RIGHT)


def _right_before_left(grid):
    """Wrong rival: swap only the final two BFS neighbor priorities."""
    return _solve_with_order(grid, _UP_DOWN_RIGHT_LEFT)


def _preserve_checkpoints(grid):
    """Wrong rival: paint only zero cells and retain crossed markers."""
    return _solve_with_order(
        grid, _UP_DOWN_LEFT_RIGHT, preserve_checkpoints=True
    )


def _wall_component_sizes(grid):
    walls = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    seen = set()
    sizes = []
    for start in walls:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for delta_row, delta_col in _UP_DOWN_LEFT_RIGHT:
                neighbor = row + delta_row, col + delta_col
                if neighbor in walls and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _segment_options(grid, reserved, *, min_length=2, max_length=None):
    """Enumerate cardinally separated straight wall objects."""
    height, width = len(grid), len(grid[0])
    if max_length is None:
        max_length = max(height, width)
    options = []
    for vertical in (True, False):
        line_limit = height if vertical else width
        fixed_limit = width if vertical else height
        for length in range(min_length, min(max_length, line_limit) + 1):
            for start in range(line_limit - length + 1):
                for fixed in range(fixed_limit):
                    cells = [
                        (start + offset, fixed)
                        if vertical
                        else (fixed, start + offset)
                        for offset in range(length)
                    ]
                    if any(
                        point in reserved or grid[point[0]][point[1]] != 0
                        for point in cells
                    ):
                        continue
                    if any(
                        0 <= row + delta_row < height
                        and 0 <= col + delta_col < width
                        and grid[row + delta_row][col + delta_col] == 5
                        for row, col in cells
                        for delta_row, delta_col in _UP_DOWN_LEFT_RIGHT
                    ):
                        continue
                    options.append(cells)
    return options


def _put_random_segments(
    grid, reserved, count, rng, *, min_length=2, max_length=6
) -> bool:
    for _ in range(count):
        options = _segment_options(
            grid, reserved, min_length=min_length, max_length=max_length
        )
        if not options:
            return False
        for row, col in rng.choice(options):
            grid[row][col] = 5
    return True


def _path_metrics(grid):
    positions = _checkpoint_positions(grid)
    if positions is None:
        return [], 0, 0
    paths = [
        _bfs_path(grid, positions[first], positions[second], _UP_DOWN_LEFT_RIGHT)
        for first, second in _LEGS
    ]
    detours = 0
    turns = 0
    for path in paths:
        if not path:
            continue
        manhattan = abs(path[0][0] - path[-1][0]) + abs(path[0][1] - path[-1][1])
        detours += len(path) - 1 > manhattan
        for index in range(1, len(path) - 1):
            before = (
                path[index][0] - path[index - 1][0],
                path[index][1] - path[index - 1][1],
            )
            after = (
                path[index + 1][0] - path[index][0],
                path[index + 1][1] - path[index][1],
            )
            turns += before != after
    return paths, detours, turns


def _changed_count(grid) -> int:
    output = _selected_output(grid)
    return sum(
        before != after
        for input_row, output_row in zip(grid, output)
        for before, after in zip(input_row, output_row)
    )


def _pick_zone_point(zone, chosen, rng):
    choices = [
        point
        for point in zone
        if all(
            abs(point[0] - other[0]) + abs(point[1] - other[1]) >= 3
            for other in chosen
        )
    ]
    return rng.choice(choices) if choices else None


def _build_canonical_maze(height, width, rng):
    """Build a sparse irregular scene without either targeted rival branch."""
    for _attempt in range(320):
        grid = full_grid(height, width, 0)
        zones = (
            # 2: lower-right
            [
                (row, col)
                for row in range(max(2, 2 * height // 3), height)
                for col in range(max(2, 2 * width // 3), width)
            ],
            # 3: middle-right
            [
                (row, col)
                for row in range(max(2, height // 3), max(3, 2 * height // 3 + 1))
                for col in range(max(2, width // 2), width)
            ],
            # 4: middle-left
            [
                (row, col)
                for row in range(max(1, height // 3), max(3, 2 * height // 3 + 1))
                for col in range(0, max(3, width // 2))
            ],
            # 7: upper-left
            [
                (row, col)
                for row in range(0, max(2, height // 3))
                for col in range(0, max(3, width // 3 + 1))
            ],
        )
        checkpoints = []
        for zone in zones:
            point = _pick_zone_point(zone, checkpoints, rng)
            if point is None:
                break
            checkpoints.append(point)
        if len(checkpoints) != 4:
            continue
        if len({point[0] for point in checkpoints}) < 3:
            continue

        reserved = set(checkpoints)
        component_count = rng.choice((2, 2, 3))
        # Match the source's sparse segmented walls: one moderately long object
        # plus one or two short, cardinally separate objects.
        if not _put_random_segments(
            grid, reserved, 1, rng, min_length=4, max_length=7
        ):
            continue
        if not _put_random_segments(
            grid,
            reserved,
            component_count - 1,
            rng,
            min_length=2,
            max_length=5,
        ):
            continue
        for color, (row, col) in zip(_CHECKPOINTS, checkpoints):
            grid[row][col] = color

        paths, detours, turns = _path_metrics(grid)
        changed = _changed_count(grid)
        wall_sizes = _wall_component_sizes(grid)
        if any(not path for path in paths):
            continue
        if not 6 <= sum(wall_sizes) <= 15 or len(wall_sizes) != component_count:
            continue
        if not 6 <= changed <= 48 or detours < 1 or turns < 2:
            continue
        # Keep this branch source-like and unambiguous with respect to the two
        # named alternatives; the alternating witness branch teaches them.
        if _selected_output(grid) != _right_before_left(grid):
            continue
        if _selected_output(grid) != _preserve_checkpoints(grid):
            continue
        return grid
    raise RuntimeError("could not construct a canonical_maze scene")


def _build_semantic_witness(height, width, rng, variant):
    """Build one compact scene that refutes both retained rival rules.

    ``overwrite_2`` places colors 3,2,4 on one line, then gives 4->7 an
    equal left/right detour. ``overwrite_4`` places 2,4,3 on one line with a
    symmetric barrier between 4 and 3, so 2->3 overwrites 4 and the same
    barrier exposes left-before-right priority.  The four-step production
    period alternates these two canonical-observed overwrite transitions.
    """
    if variant not in ("overwrite_2", "overwrite_4"):
        raise ValueError(f"unknown semantic witness variant {variant!r}")
    for _attempt in range(128):
        grid = full_grid(height, width, 0)
        center_col = rng.randint(3, width - 4)
        top_row = rng.choice((0, 1))

        if variant == "overwrite_2":
            p3 = (top_row, center_col)
            p2 = (top_row + 2, center_col)
            p4 = (top_row + 4, center_col)
            barrier_row = top_row + 6
            p7 = (barrier_row + 3, center_col)
            if p7[0] >= height:
                continue
            protected = {p2, p3, p4, p7}
            for row in range(top_row, p7[0] + 1):
                for col in range(center_col - 2, center_col + 3):
                    if 0 <= col < width:
                        protected.add((row, col))
        else:
            p2 = (top_row, center_col)
            p4 = (top_row + 2, center_col)
            barrier_row = top_row + 3
            p3 = (top_row + 5, center_col)
            # Keep 4->7 horizontal so the only overwritten checkpoint is 4.
            direction = rng.choice((-1, 1))
            p7 = (p4[0], center_col + 3 * direction)
            if p3[0] >= height or not 0 <= p7[1] < width:
                continue
            protected = {p2, p3, p4, p7}
            for row in range(top_row, p3[0] + 1):
                for col in range(center_col - 2, center_col + 3):
                    if 0 <= col < width:
                        protected.add((row, col))
            for col in range(min(p4[1], p7[1]), max(p4[1], p7[1]) + 1):
                protected.add((p4[0], col))

        checkpoints = (p2, p3, p4, p7)
        for col in range(center_col - 1, center_col + 2):
            grid[barrier_row][col] = 5

        component_count = rng.choice((2, 3))
        if not _put_random_segments(
            grid,
            protected,
            component_count - 1,
            rng,
            min_length=3,
            max_length=5,
        ):
            continue
        for color, (row, col) in zip(_CHECKPOINTS, checkpoints):
            grid[row][col] = color

        paths, _detours, _turns = _path_metrics(grid)
        wall_sizes = _wall_component_sizes(grid)
        changed = _changed_count(grid)
        if any(not path for path in paths):
            continue
        if not 6 <= sum(wall_sizes) <= 15 or len(wall_sizes) != component_count:
            continue
        if not 6 <= changed <= 48:
            continue
        if _selected_output(grid) == _right_before_left(grid):
            continue
        if _selected_output(grid) == _preserve_checkpoints(grid):
            continue
        overwritten = {
            grid[row][col]
            for row in range(height)
            for col in range(width)
            if grid[row][col] in _CHECKPOINTS
            and _selected_output(grid)[row][col] == 8
        }
        expected = {2} if variant == "overwrite_2" else {4}
        if overwritten != expected:
            continue
        return grid
    raise RuntimeError(f"could not construct a semantic_witness scene ({variant})")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_height, anchor_width = ctx.draw_choice(
        "curriculum_size_profile", _profile_options(difficulty)
    )
    height = _weighted_axis(ctx, "grid_h", range(12, 14), anchor_height)
    width = _weighted_axis(ctx, "grid_w", range(12, 15), anchor_width)

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("scene_pattern") is not None:
        pattern = ctx.draw_choice("scene_pattern", SCENE_PATTERNS)
    else:
        pattern = ctx.draw_choice("scene_pattern", (scheduled,))

    rng = ctx.draw_rng("maze_layout")
    if pattern == "semantic_witness":
        variant = "overwrite_2" if (sample_index // 2) % 2 == 0 else "overwrite_4"
        return _build_semantic_witness(height, width, rng, variant)
    return _build_canonical_maze(height, width, rng)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate task-lawful inputs while remaining broader than the sampler."""
    del difficulty, meta
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors = []
    if not 5 <= height <= 30 or not 5 <= width <= 30:
        errors.append(f"shape {height}x{width} outside supported [5,30] envelope")
    if any(
        type(value) is not int or value not in (0, 2, 3, 4, 5, 7)
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer colors from 0,2,3,4,5,7")
        return errors

    positions = _checkpoint_positions(grid)
    if positions is None:
        counts = {
            color: sum(value == color for row in grid for value in row)
            for color in _CHECKPOINTS
        }
        errors.append(
            f"expected exactly one checkpoint of colors 2,3,4,7; got {counts}"
        )
        return errors

    flat = [value for row in grid for value in row]
    if 5 not in flat:
        errors.append("expected at least one gray(5) wall")
    if flat.count(0) <= max(flat.count(5), 4):
        errors.append("zero must be the modal open-background color")

    paths = [
        _bfs_path(grid, positions[first], positions[second], _UP_DOWN_LEFT_RIGHT)
        for first, second in _LEGS
    ]
    if not all(paths):
        errors.append("every ordered checkpoint leg must be reachable")
    if _selected_output(grid) == [list(row) for row in grid]:
        errors.append("selected rule would make no output change")
    return errors


def strict_canonical_like(grid):
    """Source-bound morphology used by semantic and profile checks."""
    errors = list(self_check(grid))
    shape = _shape(grid)
    if shape is None or errors:
        return errors
    height, width = shape
    if not (12 <= height <= 13 and 12 <= width <= 14):
        errors.append(f"shape {height}x{width} outside canonical 12..13 x 12..14 envelope")
    flat = [value for row in grid for value in row]
    if set(flat) != {0, 2, 3, 4, 5, 7}:
        errors.append("expected exact canonical input palette {0,2,3,4,5,7}")
    wall_sizes = _wall_component_sizes(grid)
    if not 6 <= sum(wall_sizes) <= 15:
        errors.append(f"wall count {sum(wall_sizes)} outside canonical-like 6..15")
    if not 2 <= len(wall_sizes) <= 3:
        errors.append(f"wall component count {len(wall_sizes)} outside 2..3")
    positions = _checkpoint_positions(grid)
    if positions is not None and len({point[0] for point in positions.values()}) < 3:
        errors.append("checkpoints should span at least three rows")
    changed = _changed_count(grid)
    if not 6 <= changed <= 48:
        errors.append(f"selected output changes {changed} cells outside 6..48")
    return errors


def observe_overrides(grid):
    """Recover every advertised exact axis from pixels alone."""
    findings = strict_canonical_like(grid)
    if findings:
        raise ValueError("invalid grid: " + "; ".join(findings))
    tie = _selected_output(grid) != _right_before_left(grid)
    overwrite = _selected_output(grid) != _preserve_checkpoints(grid)
    if tie != overwrite:
        raise ValueError(
            "scene exhibits only one semantic-witness branch; generated domain requires both or neither"
        )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_pattern": "semantic_witness" if tie else "canonical_maze",
    }


def _left_right_tie_witness(grid) -> bool:
    return _selected_output(grid) != _right_before_left(grid)


def _checkpoint_overwrite_witness(grid) -> bool:
    return _selected_output(grid) != _preserve_checkpoints(grid)


def lesson_identifiable(demos, query):
    """Report any declared rival that fits demos but changes the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but predicts a different query output"
                )
    return reasons


SEMANTIC_WITNESSES = {
    "left_right_tie": _left_right_tie_witness,
    "checkpoint_overwrite": _checkpoint_overwrite_witness,
}
SEMANTIC_RIVALS = {
    "right_before_left": _right_before_left,
    "preserve_checkpoints": _preserve_checkpoints,
}
WITNESS_RIVALS = {
    "left_right_tie": ["right_before_left"],
    "checkpoint_overwrite": ["preserve_checkpoints"],
}
CANONICAL_SHORTCUTS = {"right_before_left": _right_before_left}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
