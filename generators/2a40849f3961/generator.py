"""Sampler for task 2a40849f3961: connect checkpoints through a maze.

The selected Racket authority runs three independent 4-neighbor breadth-first
searches, 1->2, 2->3, and 3->4, through every non-5 cell.  Its neighbor order is
up, down, left, right.  Only zero-valued interior cells on the selected paths
are recolored 8; checkpoints and walls remain unchanged.

The public examples do not distinguish left-before-right from right-before-left
when equal shortest paths exist.  The production schedule therefore alternates
canonical-like irregular mazes with explicit equal-length left/right detours.
Every four-pair lesson has two tie-break witnesses, so every one-query rotation
still leaves at least one witness in the demonstrations.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2a40849f3961"
TASK_ID = GENERATOR_ID
RULE_HASH = "cd7f3a44d341"
VERSION = "3.0.0"
SUMMARY = (
    "On a zero-background maze with gray(5) walls and one checkpoint each of "
    "colors 1,2,3,4, find shortest 4-neighbor paths 1->2, 2->3, and 3->4 "
    "through non-wall cells. Resolve equal paths in up/down/left/right BFS "
    "order and paint only zero-valued interior route cells cyan(8)."
)

INVARIANTS = [
    "background is 0; walls are 5; checkpoints 1,2,3,4 occur exactly once",
    "generated scenes contain 3..8 separate wall components and all three legs are reachable",
    "generated outputs change at least five zero cells and never overwrite walls or checkpoints",
    "tie_break scenes contain a real left/right equal-shortest-path counterexample",
    "canonical_maze scenes retain irregular barriers but avoid that specific tie ambiguity",
]

SCENE_PATTERNS = ("canonical_maze", "tie_break")
SCHEDULE_PROFILES = SCENE_PATTERNS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "11..13; canonical 11/12-row profiles strongly weighted",
        "valid": "11..13",
    },
    "grid_w": {
        "type": "int",
        "default": "12..14; canonical 12/13-column profiles strongly weighted",
        "valid": "12..14",
    },
    "scene_pattern": {
        "type": "str",
        "default": "alternating canonical_maze|tie_break lesson schedule",
        "valid": "|".join(SCENE_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

# Racket's cardinal-deltas order in the pinned runtime.
_UP_DOWN_LEFT_RIGHT = ((-1, 0), (1, 0), (0, -1), (0, 1))
# Strongest wrong rule retained by all five labeled canonical pairs.
_UP_DOWN_RIGHT_LEFT = ((-1, 0), (1, 0), (0, 1), (0, -1))

# Exact canonical input profiles plus the full advertised shape envelope.  These
# are size anchors only; no canonical cell layout is replayed.
_CANONICAL_PROFILES = ((11, 12), (12, 12), (11, 13))
_ALL_PROFILES = tuple((height, width) for height in range(11, 14) for width in range(12, 15))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the ordinary production branch for source-bound lesson audits."""
    del seed, difficulty
    return SCENE_PATTERNS[int(sample_index) % len(SCENE_PATTERNS)]


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    pattern = overrides.get("scene_pattern")
    if pattern is not None and type(pattern) is not str:
        raise ValueError(
            f"scene_pattern must be a string, not {type(pattern).__name__}"
        )


def _profile_options(difficulty) -> tuple[tuple[int, int], ...]:
    if difficulty == "easy":
        canonical_weight, broad_weight = 28, 1
    elif difficulty == "hard":
        canonical_weight, broad_weight = 18, 2
    else:
        canonical_weight, broad_weight = 24, 1
    return (
        tuple(profile for profile in _CANONICAL_PROFILES for _ in range(canonical_weight))
        + tuple(profile for profile in _ALL_PROFILES for _ in range(broad_weight))
    )


def _weighted_axis(ctx, name: str, values, anchor: int) -> int:
    # Keep the complete exact domain in every band while heavily favoring the
    # source-bound profile selected above.
    return ctx.draw_choice(name, tuple(values) + (anchor,) * 40)


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return None
    return len(grid), width


def _checkpoint_positions(grid):
    positions = {color: [] for color in (1, 2, 3, 4)}
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
            neighbor = (point[0] + delta_row, point[1] + delta_col)
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


def _solve_with_order(grid, order):
    positions = _checkpoint_positions(grid)
    if positions is None:
        return [list(row) for row in grid]
    path_cells = set()
    for first, second in ((1, 2), (2, 3), (3, 4)):
        path = _bfs_path(grid, positions[first], positions[second], order)
        path_cells.update(path[1:-1])
    output = [list(row) for row in grid]
    for row, col in path_cells:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


def _selected_output(grid):
    return _solve_with_order(grid, _UP_DOWN_LEFT_RIGHT)


def _right_before_left(grid):
    """Wrong rival: swap only the final two BFS neighbor priorities."""
    return _solve_with_order(grid, _UP_DOWN_RIGHT_LEFT)


def _segment_options(grid, reserved, *, min_length=2, max_length=None):
    """Enumerate separate straight wall components in deterministic order."""
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
                    # Cardinal separation preserves the requested wall-component
                    # count while allowing diagonal adjacency as in the source.
                    touches_existing = False
                    for row, col in cells:
                        for delta_row, delta_col in _UP_DOWN_LEFT_RIGHT:
                            rr, cc = row + delta_row, col + delta_col
                            if (
                                0 <= rr < height
                                and 0 <= cc < width
                                and grid[rr][cc] == 5
                            ):
                                touches_existing = True
                                break
                        if touches_existing:
                            break
                    if not touches_existing:
                        options.append(cells)
    return options


def _put_random_segments(
    grid, reserved, count, rng, *, min_length=2, max_length=7
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
        for first, second in ((1, 2), (2, 3), (3, 4))
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


def _build_canonical_maze(height, width, rng):
    """Build an irregular multi-barrier maze without the retained tie rival."""
    for _attempt in range(96):
        grid = full_grid(height, width, 0)
        zones = (
            [
                (row, col)
                for row in range(0, max(2, height // 3))
                for col in range(0, max(2, width // 3))
            ],
            [
                (row, col)
                for row in range(1, max(2, height // 2 + 1))
                for col in range(max(2, width // 2), width)
            ],
            [
                (row, col)
                for row in range(max(1, height // 2), height)
                for col in range(max(2, width // 2), width)
            ],
            [
                (row, col)
                for row in range(max(2, 2 * height // 3), height)
                for col in range(0, max(2, width // 3 + 1))
            ],
        )
        checkpoints = []
        for zone in zones:
            choices = [
                point
                for point in zone
                if all(
                    abs(point[0] - other[0]) + abs(point[1] - other[1]) >= 4
                    for other in checkpoints
                )
            ]
            if not choices:
                break
            checkpoints.append(rng.choice(choices))
        if len(checkpoints) != 4:
            continue

        reserved = set(checkpoints)
        component_count = rng.choice((4, 4, 5))
        # One source-scale wall object restores the long barrier morphology in
        # the canonical examples; remaining components stay shorter and varied.
        if not _put_random_segments(
            grid,
            reserved,
            1,
            rng,
            min_length=8,
            max_length=max(height, width),
        ):
            continue
        if not _put_random_segments(
            grid,
            reserved,
            component_count - 1,
            rng,
            min_length=3,
            max_length=7,
        ):
            continue
        for color, (row, col) in enumerate(checkpoints, 1):
            grid[row][col] = color

        paths, detours, turns = _path_metrics(grid)
        changed = _changed_count(grid)
        if any(not path for path in paths):
            continue
        if not 5 <= changed <= 60 or detours < 1 or turns < 2:
            continue
        if _selected_output(grid) != _right_before_left(grid):
            continue
        return grid
    raise RuntimeError("could not construct a canonical_maze scene")


def _build_tie_break_maze(height, width, rng):
    """Build a symmetric obstacle whose equal detours expose L-before-R BFS."""
    for _attempt in range(64):
        grid = full_grid(height, width, 0)
        middle_col = rng.randint(4, width - 5)
        barrier_row = rng.randint(3, height - 5)
        p1 = (rng.randint(0, 1), middle_col)
        p2 = (barrier_row + rng.choice((2, 3)), middle_col)
        if p2[0] >= height - 3:
            continue
        p3 = (p2[0], rng.choice((width - 3, width - 2)))
        p4 = (rng.choice((height - 2, height - 1)), p3[1])
        checkpoints = (p1, p2, p3, p4)
        if len(set(checkpoints)) != 4:
            continue

        for col in range(middle_col - 1, middle_col + 2):
            grid[barrier_row][col] = 5

        # Keep a five-column corridor around the symmetric detour untouched,
        # and preserve direct corridors for legs 2->3 and 3->4.  Decorative
        # components outside it add canonical morphology without changing the
        # purpose of the witness.
        protected = set(checkpoints)
        for row in range(0, p2[0] + 1):
            for col in range(max(0, middle_col - 2), min(width, middle_col + 3)):
                protected.add((row, col))
        for col in range(min(p2[1], p3[1]), max(p2[1], p3[1]) + 1):
            protected.add((p2[0], col))
        for row in range(min(p3[0], p4[0]), max(p3[0], p4[0]) + 1):
            protected.add((row, p3[1]))

        if not _put_random_segments(
            grid, protected, rng.choice((3, 4, 4)), rng, min_length=2
        ):
            continue
        for color, (row, col) in enumerate(checkpoints, 1):
            grid[row][col] = color

        paths, _detours, _turns = _path_metrics(grid)
        wall_count = sum(value == 5 for row in grid for value in row)
        changed = _changed_count(grid)
        if any(not path for path in paths):
            continue
        if not 12 <= wall_count <= 40 or not 5 <= changed <= 60:
            continue
        if _selected_output(grid) == _right_before_left(grid):
            continue
        return grid
    raise RuntimeError("could not construct a tie_break scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
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
    height = _weighted_axis(ctx, "grid_h", range(11, 14), anchor_height)
    width = _weighted_axis(ctx, "grid_w", range(12, 15), anchor_width)

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("scene_pattern") is not None:
        pattern = ctx.draw_choice("scene_pattern", SCENE_PATTERNS)
    else:
        pattern = ctx.draw_choice("scene_pattern", (scheduled,))

    rng = ctx.draw_rng("maze_layout")
    if pattern == "tie_break":
        return _build_tie_break_maze(height, width, rng)
    return _build_canonical_maze(height, width, rng)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate broad canonical-lawful inputs, including disconnected legs."""
    del difficulty, meta
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors = []
    if not 5 <= height <= 30 or not 5 <= width <= 30:
        errors.append(f"shape {height}x{width} outside supported [5,30] envelope")
    if any(
        type(value) is not int or value not in (0, 1, 2, 3, 4, 5)
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer colors from 0,1,2,3,4,5")
        return errors

    positions = _checkpoint_positions(grid)
    if positions is None:
        counts = {
            color: sum(value == color for row in grid for value in row)
            for color in (1, 2, 3, 4)
        }
        errors.append(f"expected exactly one checkpoint of each color 1..4; got {counts}")
        return errors

    flat = [value for row in grid for value in row]
    if 5 not in flat:
        errors.append("expected at least one gray(5) wall")
    if flat.count(0) <= max(flat.count(5), 4):
        errors.append("zero must be the modal open-background color")

    paths = [
        _bfs_path(grid, positions[first], positions[second], _UP_DOWN_LEFT_RIGHT)
        for first, second in ((1, 2), (2, 3), (3, 4))
    ]
    if not any(paths):
        errors.append("all three checkpoint legs are disconnected")
    if _selected_output(grid) == [list(row) for row in grid]:
        errors.append("selected rule would make no output change")
    return errors


def strict_canonical_like(grid):
    """Task-law manifold used by semantic and profile checks."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis from pixels alone."""
    findings = self_check(grid)
    if findings:
        raise ValueError("invalid grid: " + "; ".join(findings))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_pattern": (
            "tie_break"
            if _selected_output(grid) != _right_before_left(grid)
            else "canonical_maze"
        ),
    }


def _left_right_tie_witness(grid) -> bool:
    return _selected_output(grid) != _right_before_left(grid)


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


SEMANTIC_WITNESSES = {"left_right_tie": _left_right_tie_witness}
SEMANTIC_RIVALS = {"right_before_left": _right_before_left}
WITNESS_RIVALS = {"left_right_tie": ["right_before_left"]}
CANONICAL_SHORTCUTS = {"right_before_left": _right_before_left}
LESSON_COMPETITORS = {"right_before_left": _right_before_left}
