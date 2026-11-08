"""Generator for ``Exact Vertical Quadruples`` (task ``f1bb0165c32b``).

The input is a zero-background grid containing maximal vertical runs of blue
cells.  The authoritative Racket rule recolors *every* blue run of exact length
four red and leaves shorter and longer runs blue.

The generator is deliberately constructive rather than retry-based.  Every
ordinary draw contains multiple targets, at least one shorter non-target, and
at least one longer non-target.  A four-slot schedule varies stacking,
horizontal contact, and edge placement so a lesson cannot reduce the rule to
component size, extremal length, fixed position, or a single selected run.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f1bb0165c32b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ed1061be40ca"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, find each maximal vertical run of blue (1) cells. "
    "Recolor every run whose length is exactly four to red (2), including "
    "runs touching an edge, touching another target horizontally, or sharing "
    "a column with a separately gapped run. Leave all shorter and longer "
    "vertical runs blue."
)

INVARIANTS = [
    "the input palette is exactly a subset of {0, 1}",
    "all foreground cells decompose into maximal vertical blue runs",
    "ordinary draws contain two or three exact-length-four target runs",
    "ordinary draws contain both a shorter-than-four and a longer-than-four run",
    "stacked runs in one column are separated by at least one background cell",
    "the four-slot schedule varies stacking, target contact, and edge placement",
]

# Public axes are limited to values exactly recoverable from the returned grid.
# Placement profile, individual run lengths, columns, and row offsets are
# deterministic nuisance variation rather than caller-visible promises.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed choice in 8..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed choice in 10..14",
        "valid": "10..14",
    },
    "n_runs": {
        "type": "int",
        "default": "difficulty-skewed choice in 5..8",
        "valid": "5..8",
    },
    "n_length4": {
        "type": "int",
        "default": "choice in 2..3",
        "valid": "2..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

# Every four consecutive sample indices contain all decisive layout profiles.
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Observable curriculum slot used by the sliding-window semantic gate."""
    return sample_index % len(SCHEDULE_PROFILES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")


def _difficulty_options(difficulty: Any) -> tuple[list[int], list[int], list[int]]:
    """Return skewed options while keeping every public value overrideable."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if difficulty == "easy":
        return (
            [8, 8, 8, 9, 9, 10, 10, 11, 12],
            [10, 10, 10, 11, 12, 12, 13, 14],
            [5, 5, 5, 6, 6, 7, 8],
        )
    if difficulty == "hard":
        return (
            # Keep every value reachable, but deliberately anchor hard draws
            # to the canonical (8x10, 9x12, 10x12) size profiles as well as
            # exploring larger lattices.
            [8, 9, 10, 10, 11, 10, 12, 10, 10],
            [10, 12, 12, 12, 11, 12, 12, 13, 14],
            [5, 6, 6, 7, 7, 8, 8, 8],
        )
    return (
        [8, 9, 9, 10, 10, 10, 11, 11, 12],
        [10, 10, 11, 11, 12, 12, 12, 13, 14],
        [5, 5, 6, 6, 7, 7, 8, 8],
    )


def _place_run(grid: list[list[int]], column: int, start: int, length: int) -> None:
    """Place one blue vertical run, rejecting accidental same-column merging."""
    h = len(grid)
    if not (0 <= column < len(grid[0]) and 0 <= start <= h - length):
        raise ValueError("run placement is outside the grid")
    if start > 0 and grid[start - 1][column] != 0:
        raise ValueError("run lacks a background separator above")
    if start + length < h and grid[start + length][column] != 0:
        raise ValueError("run lacks a background separator below")
    if any(grid[row][column] != 0 for row in range(start, start + length)):
        raise ValueError("run placement overlaps an existing run")
    for row in range(start, start + length):
        grid[row][column] = 1


def _fresh_column(rng, width: int, used: set[int], *, avoid_adjacent_to: set[int] = frozenset()) -> int:
    candidates = [
        column
        for column in range(width)
        if column not in used
        and all(abs(column - other) > 1 for other in avoid_adjacent_to)
    ]
    if not candidates:
        candidates = [column for column in range(width) if column not in used]
    if not candidates:
        raise RuntimeError("not enough columns for the requested run count")
    return rng.choice(candidates)


def _random_start(rng, height: int, length: int, *, prefer: str | None = None) -> int:
    maximum = height - length
    if prefer == "top":
        return 0
    if prefer == "bottom":
        return maximum
    if prefer == "interior" and maximum >= 2:
        return rng.randint(1, maximum - 1)
    return rng.randint(0, maximum)


def _run_lengths(n_runs: int, n_length4: int, rng, sample_index: int) -> tuple[list[int], list[int]]:
    """Return target and non-target lengths with both sides of four present."""
    target_lengths = [4] * n_length4
    non_target_count = n_runs - n_length4
    short = (1, 2, 3)[sample_index % 3]
    long = (5, 6)[(sample_index // 2) % 2]
    non_targets = [short, long]
    pool = [1, 2, 3, 5, 6]
    while len(non_targets) < non_target_count:
        non_targets.append(rng.choice(pool))
    tail = non_targets[2:]
    rng.shuffle(tail)
    non_targets[2:] = tail
    return target_lengths, non_targets


def _construct_grid(
    height: int,
    width: int,
    n_runs: int,
    n_length4: int,
    profile: int,
    rng,
    sample_index: int,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    targets, non_targets = _run_lengths(n_runs, n_length4, rng, sample_index)
    used_columns: set[int] = set()
    placed = 0

    def place_fresh(length: int, *, prefer: str | None = None, avoid: set[int] = frozenset()) -> int:
        nonlocal placed
        column = _fresh_column(rng, width, used_columns, avoid_adjacent_to=avoid)
        used_columns.add(column)
        _place_run(grid, column, _random_start(rng, height, length, prefer=prefer), length)
        placed += 1
        return column

    # Profile 0: one target and one short run share a column but remain
    # separated, proving that maximal runs—not whole columns—are selected.
    if profile == 0:
        column = _fresh_column(rng, width, used_columns)
        used_columns.add(column)
        short = non_targets.pop(0)
        if sample_index % 2 == 0:
            _place_run(grid, column, 0, targets.pop(0))
            _place_run(grid, column, height - short, short)
        else:
            _place_run(grid, column, 0, short)
            _place_run(grid, column, height - 4, targets.pop(0))
        placed += 2
        place_fresh(targets.pop(0), prefer="interior", avoid={column})

    # Profile 1: two exact-four runs touch horizontally while keeping distinct
    # vertical starts.  They form one 4-connected component of size eight, so a
    # component-size-four shortcut fails.
    elif profile == 1:
        left = rng.randint(0, width - 2)
        used_columns.update((left, left + 1))
        _place_run(grid, left, 0, targets.pop(0))
        _place_run(grid, left + 1, 1, targets.pop(0))
        placed += 2

    # Profile 2: target runs occupy opposite vertical boundaries.  Position is
    # therefore varied without making an edge marker the answer.
    elif profile == 2:
        first = place_fresh(targets.pop(0), prefer="top")
        place_fresh(targets.pop(0), prefer="bottom", avoid={first})

    # Profile 3 combines contact with a separately stacked short run.  The
    # overlap is intentional and remains exactly two vertical target runs.
    else:
        left = rng.randint(0, width - 2)
        used_columns.update((left, left + 1))
        short = non_targets.pop(0)
        _place_run(grid, left, 0, targets.pop(0))
        _place_run(grid, left, height - short, short)
        _place_run(grid, left + 1, 1, targets.pop(0))
        placed += 3

    # Any additional targets and non-targets occupy fresh columns.  Prefer an
    # interior target and alternate edge/interior nuisance placements so fixed
    # position remains unusable across seeds.
    for index, length in enumerate(targets):
        preference = "interior" if index == 0 else None
        place_fresh(length, prefer=preference)
    for index, length in enumerate(non_targets):
        preference = ("bottom" if (sample_index + index) % 4 == 0 else None)
        place_fresh(length, prefer=preference)

    if placed != n_runs:
        raise RuntimeError(f"constructed {placed} runs, expected {n_runs}")
    return grid


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
    h_options, w_options, run_options = _difficulty_options(difficulty)
    height = ctx.draw_choice("grid_h", h_options)
    width = ctx.draw_choice("grid_w", w_options)
    n_runs = ctx.draw_choice("n_runs", run_options)
    n_length4 = ctx.draw_choice("n_length4", [2, 2, 2, 3])
    profile = sample_index % len(SCHEDULE_PROFILES)
    rng = ctx.draw_rng("layout")

    grid = _construct_grid(
        height,
        width,
        n_runs,
        n_length4,
        profile,
        rng,
        sample_index,
    )
    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError("constructed invalid exact-quadruple scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_runs": n_runs,
        "n_length4": n_length4,
    }
    if observed != expected:
        raise RuntimeError(f"keyed-axis mismatch: expected {expected}, observed {observed}")
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _vertical_runs(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int, int]]:
    """Return ``(column, start, end, value)`` maximal nonzero vertical runs."""
    runs: list[tuple[int, int, int, int]] = []
    height, width = len(grid), len(grid[0])
    for column in range(width):
        row = 0
        while row < height:
            value = grid[row][column]
            if value == 0:
                row += 1
                continue
            start = row
            while row + 1 < height and grid[row + 1][column] == value:
                row += 1
            runs.append((column, start, row, value))
            row += 1
    return runs


def _run_length(run: tuple[int, int, int, int]) -> int:
    return run[2] - run[1] + 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's sparse vertical-run input grammar.

    This checker deliberately says nothing about the output.  It rejects
    malformed or rule-hiding lesson inputs while accepting all four canonical
    train/test inputs.
    """
    errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 12:
        errors.append(f"height must be in 8..12, got {height}")
    if not 10 <= width <= 14:
        errors.append(f"width must be in 10..14, got {width}")

    palette = {value for row in grid for value in row}
    if not palette <= {0, 1}:
        errors.append(f"input palette must be a subset of {{0, 1}}, got {sorted(palette)}")
    if 0 not in palette:
        errors.append("input must retain a zero background")

    runs = _vertical_runs(grid)
    lengths = [_run_length(run) for run in runs]
    if not 4 <= len(runs) <= 8:
        errors.append(f"need 4..8 maximal vertical runs, got {len(runs)}")
    if any(run[3] != 1 for run in runs):
        errors.append("every foreground run must be blue (1)")
    if any(not 1 <= length <= 6 for length in lengths):
        errors.append("every vertical run must have length in 1..6")
    if not any(length == 4 for length in lengths):
        errors.append("need at least one exact-length-four target run")
    if not any(length != 4 for length in lengths):
        errors.append("need at least one non-four contrast run")
    if sum(value != 0 for row in grid for value in row) > (height * width) // 2:
        errors.append("foreground is too dense for the sparse run grammar")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked predicate used by the strict semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    runs = _vertical_runs(grid)
    target_count = sum(_run_length(run) == 4 and run[3] == 1 for run in runs)
    non_target_count = len(runs) - target_count
    if target_count < 1:
        errors.append("no exact-length-four target is observable")
    if non_target_count < 1:
        errors.append("no unchanged contrast run is observable")
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    runs = _vertical_runs(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_runs": len(runs),
        "n_length4": sum(_run_length(run) == 4 and run[3] == 1 for run in runs),
    }


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; the canonical Racket rule is authoritative."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    output = [list(row) for row in grid]
    for column, start, end, value in _vertical_runs(grid):
        if value == 1 and end - start + 1 == 4:
            for row in range(start, end + 1):
                output[row][column] = 2
    return output


def _recolor_runs_where(grid, predicate: Callable[[int], bool]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for column, start, end, value in _vertical_runs(grid):
        length = end - start + 1
        if value == 1 and predicate(length):
            for row in range(start, end + 1):
                output[row][column] = 2
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _recolor_all_blue(grid):
    return [[2 if value == 1 else value for value in row] for row in grid]


def _recolor_at_least_four(grid):
    return _recolor_runs_where(grid, lambda length: length >= 4)


def _recolor_at_most_four(grid):
    return _recolor_runs_where(grid, lambda length: length <= 4)


def _recolor_longest_runs(grid):
    runs = [run for run in _vertical_runs(grid) if run[3] == 1]
    longest = max((_run_length(run) for run in runs), default=0)
    return _recolor_runs_where(grid, lambda length: length == longest)


def _recolor_first_exact_four(grid):
    output = [list(row) for row in grid]
    for column, start, end, value in _vertical_runs(grid):
        if value == 1 and end - start + 1 == 4:
            for row in range(start, end + 1):
                output[row][column] = 2
            break
    return output


def _recolor_horizontal_fours(grid):
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        column = 0
        while column < width:
            if grid[row][column] != 1:
                column += 1
                continue
            start = column
            while column + 1 < width and grid[row][column + 1] == 1:
                column += 1
            if column - start + 1 == 4:
                for current in range(start, column + 1):
                    output[row][current] = 2
            column += 1
    return output


def _blue_components(grid) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 1
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            row, column = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        components.append(component)
    return components


def _recolor_components_of_size_four(grid):
    output = [list(row) for row in grid]
    for component in _blue_components(grid):
        if len(component) == 4:
            for row, column in component:
                output[row][column] = 2
    return output


def _recolor_edge_exact_fours(grid):
    height = len(grid)
    output = [list(row) for row in grid]
    for column, start, end, value in _vertical_runs(grid):
        if value == 1 and end - start + 1 == 4 and (start == 0 or end == height - 1):
            for row in range(start, end + 1):
                output[row][column] = 2
    return output


def _recolor_interior_exact_fours(grid):
    height = len(grid)
    output = [list(row) for row in grid]
    for column, start, end, value in _vertical_runs(grid):
        if value == 1 and end - start + 1 == 4 and start > 0 and end < height - 1:
            for row in range(start, end + 1):
                output[row][column] = 2
    return output


def _recolor_target_columns(grid):
    """Shortcut: recolor every blue cell in a column containing a target run."""
    target_columns = {
        column
        for column, start, end, value in _vertical_runs(grid)
        if value == 1 and end - start + 1 == 4
    }
    return [
        [2 if value == 1 and column in target_columns else value
         for column, value in enumerate(row)]
        for row in grid
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "identity": _identity,
    "recolor_all_blue": _recolor_all_blue,
    "recolor_runs_length_at_least_four": _recolor_at_least_four,
    "recolor_runs_length_at_most_four": _recolor_at_most_four,
    "recolor_longest_runs": _recolor_longest_runs,
    "recolor_only_first_exact_four": _recolor_first_exact_four,
    "recolor_horizontal_exact_fours": _recolor_horizontal_fours,
    "recolor_4_connected_components_of_size_four": _recolor_components_of_size_four,
    "recolor_edge_exact_fours": _recolor_edge_exact_fours,
    "recolor_interior_exact_fours": _recolor_interior_exact_fours,
    "recolor_all_blue_in_target_columns": _recolor_target_columns,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _target_runs(grid):
    return [run for run in _vertical_runs(grid) if run[3] == 1 and _run_length(run) == 4]


def _multiple_targets(grid) -> bool:
    return len(_target_runs(grid)) >= 2


def _shorter_non_target(grid) -> bool:
    return any(run[3] == 1 and _run_length(run) < 4 for run in _vertical_runs(grid))


def _longer_non_target(grid) -> bool:
    return any(run[3] == 1 and _run_length(run) > 4 for run in _vertical_runs(grid))


def _stacked_column(grid) -> bool:
    counts: dict[int, int] = {}
    for column, *_ in _vertical_runs(grid):
        counts[column] = counts.get(column, 0) + 1
    return any(count >= 2 for count in counts.values())


def _touching_target_runs(grid) -> bool:
    targets = _target_runs(grid)
    for index, left in enumerate(targets):
        for right in targets[index + 1:]:
            if abs(left[0] - right[0]) != 1:
                continue
            if max(left[1], right[1]) <= min(left[2], right[2]):
                return True
    return False


def _edge_and_interior_targets(grid) -> bool:
    height = len(grid)
    targets = _target_runs(grid)
    return (
        any(start == 0 or end == height - 1 for _, start, end, _ in targets)
        and any(start > 0 and end < height - 1 for _, start, end, _ in targets)
    )


def _vertical_not_horizontal(grid) -> bool:
    return rule_mirror(grid) != _recolor_horizontal_fours(grid)


SEMANTIC_WITNESSES = {
    "multiple_exact_four_targets": _multiple_targets,
    "shorter_unchanged_run": _shorter_non_target,
    "longer_unchanged_run": _longer_non_target,
    "separately_stacked_runs": _stacked_column,
    "touching_targets_are_columnwise_runs": _touching_target_runs,
    "edge_and_interior_targets": _edge_and_interior_targets,
    "vertical_not_horizontal": _vertical_not_horizontal,
}

WITNESS_RIVALS = {
    "multiple_exact_four_targets": ["recolor_only_first_exact_four"],
    "shorter_unchanged_run": ["recolor_all_blue", "recolor_runs_length_at_most_four"],
    "longer_unchanged_run": [
        "recolor_all_blue",
        "recolor_runs_length_at_least_four",
        "recolor_longest_runs",
    ],
    "separately_stacked_runs": ["recolor_all_blue_in_target_columns"],
    "touching_targets_are_columnwise_runs": ["recolor_4_connected_components_of_size_four"],
    "edge_and_interior_targets": ["recolor_edge_exact_fours", "recolor_interior_exact_fours"],
    "vertical_not_horizontal": ["identity", "recolor_horizontal_exact_fours"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a named shortcut survives all demonstrations."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output grids")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"{role} output does not match exact vertical quadruple recoloring")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked malformed or rule-hiding scenes that must be rejected."""
    blank = full_grid(9, 12, 0)

    no_target = full_grid(9, 12, 0)
    for column, start, length in ((1, 1, 1), (3, 1, 2), (5, 1, 3), (8, 1, 5)):
        _place_run(no_target, column, start, length)

    all_targets = full_grid(9, 12, 0)
    for column, start in ((1, 0), (4, 1), (7, 2), (10, 4)):
        _place_run(all_targets, column, start, 4)

    horizontal_quadruple = full_grid(9, 12, 0)
    for column in range(2, 6):
        horizontal_quadruple[4][column] = 1

    wrong_palette = _construct_grid(9, 12, 5, 2, 0, gen_ctx(
        seed=91,
        sample_index=0,
        version=VERSION,
        task_id=TASK_ID,
    ).draw_rng("fixture"), 0)
    wrong_palette[0][0] = 2

    overlong = full_grid(9, 12, 0)
    for row in range(1, 8):
        overlong[row][1] = 1
    for column, start, length in ((3, 0, 4), (5, 1, 4), (7, 1, 2)):
        _place_run(overlong, column, start, length)

    return [
        ("blank_no_runs", blank),
        ("no_exact_four_target", no_target),
        ("all_runs_are_targets", all_targets),
        ("horizontal_quadruple_only", horizontal_quadruple),
        ("input_contains_output_color", wrong_palette),
        ("overlong_vertical_run", overlong),
    ]
