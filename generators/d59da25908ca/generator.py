"""Generator for the vertical-domino promotion task.

Authority: every maximal vertical run of green (3) with exact length two is
recolored orange (7).  Green runs of every other length remain unchanged.

The production curriculum alternates scenes with and without a length-four
negative.  Every four-pair lesson contains two of each, so all query rotations
refute both the canonical-fitting shortcut "recolor every even-length green
run" and the distribution shortcut "apply the rule only when length four is
present".
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d59da25908ca"
TASK_ID = "d59da25908ca"
VERSION = "2.1.0"
RULE_HASH = "ae357e8ac60c"
SUMMARY = (
    "Exact length-2 vertical green runs turn orange; length-1 and length-3+ "
    "controls stay green."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

INVARIANTS = [
    "background is 0 and foreground is green 3",
    "foreground components are separated straight vertical runs",
    "each lesson input has 1-2 exact-length-2 targets and one scheduled length-1/3/5 control",
    "the six-slot curriculum alternates length-4 present/absent so every four-pair lesson has two of each",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors and difficulty-scaled broad profile",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors and difficulty-scaled broad profile",
        "valid": "7..10",
    },
    "n_targets": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "with_length4_singleton",
    "without_length4_length3",
    "with_length4_length5",
    "without_length4_singleton",
    "with_length4_length3",
    "without_length4_length5",
)
_CONTROL_LENGTH = {
    "with_length4_singleton": 1,
    "without_length4_length3": 3,
    "with_length4_length5": 5,
    "without_length4_singleton": 1,
    "with_length4_length3": 3,
    "without_length4_length5": 5,
}
_HAS_LENGTH4 = {
    "with_length4_singleton": True,
    "without_length4_length3": False,
    "with_length4_length5": True,
    "without_length4_singleton": False,
    "with_length4_length3": True,
    "without_length4_length5": False,
}
_DIFFICULTIES = (None, "easy", "medium", "hard")

Grid = list[list[int]]
Run = tuple[int, int, int]  # column, first row, length


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the six-slot teaching schedule to lesson-level checks."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTIES or isinstance(difficulty, bool):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")


def _scheduled_defaults(profile: str, difficulty: str | None) -> tuple[int, int, int]:
    # Four of every six samples anchor exact public profiles (5x7 and 7x7,
    # palette size two).  The two length-5 slots broaden scale without starving
    # any band.
    if profile in {"with_length4_singleton", "without_length4_singleton"}:
        return 5, 7, 2
    if profile in {"without_length4_length3", "with_length4_length3"}:
        return 7, 7, 1
    broad = {
        None: (8, 9, 2),
        "easy": (6, 8, 2),
        "medium": (8, 9, 2),
        "hard": (10, 10, 2),
    }
    return broad[difficulty]


def _draw_exact_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    lo: int,
    hi: int,
    scheduled: int,
) -> int:
    """Honor the complete advertised override domain or record one default."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (scheduled,)))


def _spaced_columns(width: int, count: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        option
        for option in combinations(range(width), count)
        if all(right - left >= 2 for left, right in zip(option, option[1:]))
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_targets = _scheduled_defaults(profile, difficulty)
    height = _draw_exact_int(ctx, overrides, "grid_h", 5, 10, default_h)
    width = _draw_exact_int(ctx, overrides, "grid_w", 7, 10, default_w)
    n_targets = _draw_exact_int(ctx, overrides, "n_targets", 1, 2, default_targets)

    lengths = [2] * n_targets + [_CONTROL_LENGTH[profile]]
    if _HAS_LENGTH4[profile]:
        lengths.append(4)
    choices = _spaced_columns(width, len(lengths))
    if not choices:  # The declared joint domain is constructive; retain a loud guard.
        raise ValueError(
            f"cannot place {len(lengths)} separated runs in grid width {width}"
        )

    rng = ctx.draw_rng("layout")
    columns = list(rng.choice(choices))
    rng.shuffle(lengths)
    rng.shuffle(columns)

    grid = full_grid(height, width, 0)
    for column, length in zip(columns, lengths, strict=True):
        first_row = rng.randint(0, height - length)
        for row in range(first_row, first_row + length):
            grid[row][column] = 3
    return grid


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def _scan_vertical_runs(grid: Grid) -> list[Run]:
    runs: list[Run] = []
    height, width = len(grid), len(grid[0])
    for column in range(width):
        row = 0
        while row < height:
            if grid[row][column] != 3:
                row += 1
                continue
            first = row
            while row < height and grid[row][column] == 3:
                row += 1
            runs.append((column, first, row - first))
    return runs


def _green_components(grid: Grid) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 3
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, column = stack.pop()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "runs": [],
        "target_count": 0,
        "control_lengths": (),
    }
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a non-empty rectangular ARC grid")
        return facts

    height, width = len(grid), len(grid[0])
    facts["height"], facts["width"] = height, width
    if not 5 <= height <= 10:
        errors.append(f"grid height must be 5..10, got {height}")
    if not 6 <= width <= 10:
        errors.append(f"grid width must be 6..10, got {width}")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 3}:
        errors.append(f"input palette must be a subset of {{0,3}}, got {sorted(palette)}")
    if errors:
        return facts

    component_runs: list[Run] = []
    for component in _green_components(grid):
        columns = {column for _, column in component}
        rows = sorted(row for row, _ in component)
        if len(columns) != 1 or rows != list(range(rows[0], rows[-1] + 1)):
            errors.append(
                "every green foreground component must be one straight vertical run"
            )
            continue
        column = next(iter(columns))
        component_runs.append((column, rows[0], len(rows)))

    duplicate_columns = [
        column
        for column in {run[0] for run in component_runs}
        if sum(run[0] == column for run in component_runs) > 1
    ]
    if duplicate_columns:
        errors.append(
            f"at most one green run is allowed per column; repeated {sorted(duplicate_columns)}"
        )

    component_runs.sort()
    facts["runs"] = component_runs
    bad_lengths = [length for _, _, length in component_runs if length not in (1, 2, 3, 4, 5)]
    if bad_lengths:
        errors.append(f"run lengths must be in 1..5, found {bad_lengths}")
    if not 2 <= len(component_runs) <= 4:
        errors.append(f"expected 2..4 separated vertical runs, found {len(component_runs)}")

    target_count = sum(length == 2 for _, _, length in component_runs)
    controls = tuple(sorted(length for _, _, length in component_runs if length != 2))
    facts["target_count"] = target_count
    facts["control_lengths"] = controls
    if not 1 <= target_count <= 2:
        errors.append(f"expected 1..2 exact-length-2 targets, found {target_count}")
    if not 1 <= len(controls) <= 2:
        errors.append(f"expected 1..2 non-target control runs, found {len(controls)}")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete public teaching grammar, including negatives."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_targets": facts["target_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Accept task-lawful inputs inside the public size/palette envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 7 and 6 <= width <= 7):
        return [
            f"grid {height}x{width} is outside canonical size envelope 5..7 by 6..7"
        ]
    return []


def _recolor_selected_runs(
    grid: Grid,
    predicate: Callable[[int], bool],
    *,
    limit: int | None = None,
) -> Grid:
    out = deepcopy(grid)
    changed = 0
    for column, first, length in _scan_vertical_runs(grid):
        if not predicate(length):
            continue
        if limit is not None and changed >= limit:
            continue
        for row in range(first, first + length):
            out[row][column] = 7
        changed += 1
    return out


def rule_mirror(grid: Grid) -> Grid:
    """Input-pure Python mirror used only by tests and semantic probes."""
    return _recolor_selected_runs(grid, lambda length: length == 2)


def _all_green_runs_rival(grid: Grid) -> Grid:
    return _recolor_selected_runs(grid, lambda length: True)


def _length_at_least_two_rival(grid: Grid) -> Grid:
    return _recolor_selected_runs(grid, lambda length: length >= 2)


def _even_length_rival(grid: Grid) -> Grid:
    return _recolor_selected_runs(grid, lambda length: length % 2 == 0)


def _first_exact_two_only_rival(grid: Grid) -> Grid:
    return _recolor_selected_runs(grid, lambda length: length == 2, limit=1)


def _requires_length4_context_rival(grid: Grid) -> Grid:
    if any(length == 4 for _, _, length in _scan_vertical_runs(grid)):
        return rule_mirror(grid)
    return deepcopy(grid)


def _has_length(grid: Grid, length: int) -> bool:
    return any(run_length == length for _, _, run_length in _scan_vertical_runs(grid))


def _has_multiple_targets(grid: Grid) -> bool:
    return sum(length == 2 for _, _, length in _scan_vertical_runs(grid)) >= 2


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "length4_even_counterexample": lambda grid: _has_length(grid, 4),
    "length4_absent_context": lambda grid: not _has_length(grid, 4),
    "singleton_control": lambda grid: _has_length(grid, 1),
    "length3_control": lambda grid: _has_length(grid, 3),
    "length5_control": lambda grid: _has_length(grid, 5),
    "multiple_exact_targets": _has_multiple_targets,
}

SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "all_green_runs": _all_green_runs_rival,
    "length_at_least_two": _length_at_least_two_rival,
    "even_length_runs": _even_length_rival,
    "first_exact_two_only": _first_exact_two_only_rival,
    "requires_length4_context": _requires_length4_context_rival,
}

WITNESS_RIVALS = {
    "length4_even_counterexample": [
        "all_green_runs",
        "length_at_least_two",
        "even_length_runs",
    ],
    "length4_absent_context": ["requires_length4_context"],
    "singleton_control": ["all_green_runs"],
    "length3_control": ["all_green_runs", "length_at_least_two"],
    "length5_control": ["all_green_runs", "length_at_least_two"],
    "multiple_exact_targets": ["first_exact_two_only"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "even_length_runs": _even_length_rival,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with exact-length-2 authority")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            differs_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and differs_query:
            reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
