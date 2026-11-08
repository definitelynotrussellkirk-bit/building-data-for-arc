"""Exact odd-run-center generator with executable teaching contracts.

Each input is a zero-background grid containing three to five horizontal runs.
Every run has odd length 1, 3, or 5, every run uses a distinct nonzero color,
and no row contains more than one run.  The selected rule erases every run
cell except its unique center.  Defaults cycle through the three canonical
input profiles; the four declared axes remain exact and constructive in every
difficulty band.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5000bcb83fa9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2b45ada2fe3e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Place 3-5 distinct-color horizontal runs of odd length 1, 3, or 5 on "
    "separate rows of a zero-background grid.  Reduce every run to its unique "
    "central cell, preserving that cell's color and position."
)
INVARIANTS = [
    "background is 0 and all cells are ARC integer colors 0..9",
    "there are 3..5 maximal nonzero horizontal runs on distinct rows",
    "run lengths are 1, 3, or 5 and at most two runs are singletons",
    "each run uses a distinct nonzero color and at least one run is nontrivial",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical profile schedule", "valid": "5..9"},
    "grid_w": {"type": "int", "default": "canonical profile schedule", "valid": "9..13"},
    "run_count": {"type": "int", "default": "4", "valid": "3..5"},
    "singleton_count": {"type": "int", "default": "1", "valid": "0..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_BOUNDS = {
    "grid_h": (5, 9),
    "grid_w": (9, 13),
    "run_count": (3, 5),
    "singleton_count": (0, 2),
}
_CANONICAL_SHAPES = ((6, 10), (7, 9), (5, 11))
Grid = list[list[int]]
Run = tuple[int, int, int, int]  # row, start, end-exclusive, color


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> tuple[int, int]:
    """Cycle through every canonical input shape in every difficulty band."""
    del seed, difficulty
    return _CANONICAL_SHAPES[int(sample_index) % len(_CANONICAL_SHAPES)]


def _validate_request(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    scheduled: int,
) -> int:
    """Record a scheduled default while retaining the full exact axis bounds."""
    lo, hi = _AXIS_BOUNDS[label]
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    if type(scheduled) is not int or not lo <= scheduled <= hi:
        raise AssertionError(f"internal {label} default {scheduled!r} outside [{lo}, {hi}]")
    ctx.draw_bounds_store[label] = (lo, hi)
    return int(ctx._record(label, scheduled, from_override=False))


def _run_lengths(run_count: int, singleton_count: int, band: str, sample_index: int) -> list[int]:
    """Construct the requested count without retries and keep every scene nonidentity."""
    long_count = run_count - singleton_count
    if long_count < 1:
        raise ValueError("singleton_count must leave at least one non-singleton run")
    if band == "easy":
        long_lengths = [3] * long_count
    elif band == "hard":
        long_lengths = [5] * long_count
    else:
        # Both long lengths occur in every ordinary medium/default scene with
        # at least two long runs; the phase changes with sample_index.
        long_lengths = [3 if (sample_index + i) % 2 == 0 else 5 for i in range(long_count)]
    return [1] * singleton_count + long_lengths


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; every advertised override is exact."""
    _validate_request(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    default_h, default_w = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, overrides, "grid_h", default_h)
    w = _scheduled_int(ctx, overrides, "grid_w", default_w)
    run_count = _scheduled_int(ctx, overrides, "run_count", 4)
    singleton_count = _scheduled_int(ctx, overrides, "singleton_count", 1)

    lengths = _run_lengths(run_count, singleton_count, band, int(sample_index))
    colors = list(ctx.draw_distinct_colors("colors", n=run_count, exclude={0}))
    rng = ctx.draw_rng("layout")
    rows = rng.sample(range(h), run_count)
    rng.shuffle(lengths)
    rng.shuffle(colors)

    grid = full_grid(h, w, 0)
    for row, length, color in zip(rows, lengths, colors):
        start = rng.randint(0, w - length)
        grid[row][start:start + length] = [color] * length

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _shape_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], 0, 0
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return errors, h, w
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (bool is not a color)")
    if not 5 <= h <= 9:
        errors.append(f"grid height {h} outside sampler domain 5..9")
    if not 9 <= w <= 13:
        errors.append(f"grid width {w} outside sampler domain 9..13")
    return errors, h, w


def _horizontal_runs(grid) -> list[Run]:
    runs: list[Run] = []
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            start = column
            color = row[column]
            while column < len(row) and row[column] == color:
                column += 1
            runs.append((row_index, start, column, color))
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact sampled manifold, collecting independent findings."""
    del difficulty, meta
    errors, _, _ = _shape_errors(grid)
    if any("rectangular" in error for error in errors) or not grid or not grid[0]:
        return errors
    if any("cells must" in error for error in errors):
        return errors

    runs = _horizontal_runs(grid)
    lengths = [end - start for _, start, end, _ in runs]
    if not 3 <= len(runs) <= 5:
        errors.append(f"expected 3..5 horizontal runs, found {len(runs)}")
    for index, length in enumerate(lengths):
        if length not in (1, 3, 5):
            parity = "even" if length % 2 == 0 else "odd"
            errors.append(
                f"run {index} has {parity} length {length}; lawful odd lengths are 1, 3, or 5"
            )
    singleton_count = sum(length == 1 for length in lengths)
    if not 0 <= singleton_count <= 2:
        errors.append(f"expected 0..2 singleton runs, found {singleton_count}")
    if runs and all(length == 1 for length in lengths):
        errors.append("all-singleton scenes are identity examples; at least one run must be nontrivial")

    rows = [row for row, _, _, _ in runs]
    if len(rows) != len(set(rows)):
        errors.append("sampler domain permits at most one horizontal run per occupied row")
    colors = [color for _, _, _, color in runs]
    if len(colors) != len(set(colors)):
        errors.append("each nonzero color must appear in exactly one horizontal run")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover all four public controls from a lawful generated input."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    runs = _horizontal_runs(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "run_count": len(runs),
        "singleton_count": sum(end - start == 1 for _, start, end, _ in runs),
    }


def strict_canonical_like(grid) -> list[str]:
    """Require the exact structural profile shared by all canonical inputs."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if (observed["grid_h"], observed["grid_w"]) not in _CANONICAL_SHAPES:
        reasons.append("canonical inputs use one of 6x10, 7x9, or 5x11")
    if observed["run_count"] != 4:
        reasons.append("canonical inputs contain exactly four runs")
    if observed["singleton_count"] != 1:
        reasons.append("canonical inputs contain exactly one singleton")
    if len({value for row in grid for value in row}) != 5:
        reasons.append("canonical inputs contain background plus four run colors")
    return reasons


def rule_mirror(grid) -> Grid:
    """Executable diagnostic mirror; Racket remains the labeling authority."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for row, start, end, color in _horizontal_runs(grid):
        length = end - start
        if length % 2 == 1:
            out[row][start + length // 2] = color
    return out


def _endpoint_prediction(grid, *, right: bool) -> Grid:
    out = full_grid(len(grid), len(grid[0]), 0)
    for row, start, end, color in _horizontal_runs(grid):
        out[row][end - 1 if right else start] = color
    return out


def _left_endpoint(grid):
    return _endpoint_prediction(grid, right=False)


def _right_endpoint(grid):
    return _endpoint_prediction(grid, right=True)


def _keep_singletons_only(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for row, start, end, color in _horizontal_runs(grid):
        if end - start == 1:
            out[row][start] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "left_endpoint": _left_endpoint,
    "right_endpoint": _right_endpoint,
    "keep_singletons_only": _keep_singletons_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The public examples already refute these three elementary rivals, so there is
# no canonical-fitting shortcut to declare here.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}


def _has_nontrivial_odd_run(grid) -> bool:
    return any(end - start in (3, 5) for _, start, end, _ in _horizontal_runs(grid))


SEMANTIC_WITNESSES = {"nontrivial_odd_run": _has_nontrivial_odd_run}
WITNESS_RIVALS = {"nontrivial_odd_run": list(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query) -> list[str]:
    """Finite declared-rival screening, not universal program identification."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} disagrees with the odd-run-center rule")
    query_grid = query["input"] if isinstance(query, dict) else query
    expected_query = rule_mirror(query_grid)
    if isinstance(query, dict) and query.get("output") is not None and query["output"] != expected_query:
        reasons.append("query output disagrees with the odd-run-center rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair.get("output") for pair in demos):
            if rival(query_grid) != expected_query:
                reasons.append(f"query-relevant rival survives demonstrations: {name}")
    return reasons
