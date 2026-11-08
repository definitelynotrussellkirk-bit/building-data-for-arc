"""Generator for ARC task 539a4f51 / content hash 8e6c44aee812.

A lawful input is a square staircase of nested L-shaped bands.  Reading the
main diagonal gives the band sequence.  An optional final zero is padding, not
part of the period.  The Racket rule doubles both dimensions and continues the
staircase with ``active_diag[max(row, col) % period]``.

The curriculum deliberately varies three independent, observable controls:
period, optional zero padding, and active-diagonal repetition pattern.  Its
12-slot schedule supplies five demonstrations and one query. Every single
query holdout retains both padding branches, a canonical 5x5 case, a larger
case, and evidence for separated repetitions of both first and later colors.
All three pattern classes, including contiguous and separated repetitions,
remain in the generated support.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8e6c44aee812"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "2f49d92711a1"

SUMMARY = (
    "Read the main diagonal of the square nested-L staircase. Strip an "
    "optional trailing zero padding band, then double the input height and "
    "width. Output cell (r,c) is active_diagonal[max(r,c) modulo period]. "
    "Repeated active colors are lawful and the final zero is optional."
)

INVARIANTS = [
    "input is a 4x4..10x10 square staircase with cell (r,c)=diag[max(r,c)]",
    "the active diagonal has length 4..9, contains only nonzero ARC colors, and uses at least two colors",
    "the diagonal has either no padding or exactly one trailing zero padding cell",
    "active diagonal colors may repeat; distinctness is not part of the rule",
    "the authoritative output is 2h x 2w and cycles the active diagonal by max(row,col)",
]

PATTERN_CLASSES = ("distinct", "prefix_run", "complex_repeat")
PADDING_MODES = ("none", "one")

AXES = {
    "period": {
        "type": "int",
        "default": "12-slot schedule: 4, 5, then difficulty-scaled 6..9",
        "valid": "4..9",
    },
    "padding": {
        "type": "str",
        "default": "alternating schedule",
        "valid": "none|one",
    },
    "pattern_class": {
        "type": "str",
        "default": "six-slot cadence with two rich recurrence witnesses",
        "valid": "distinct|prefix_run|complex_repeat",
    },
}

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.30
SCHEDULE_PROFILES = tuple(range(12))
LESSON_SCHEDULE_PERIOD = 12

_DIFFICULTY_PERIOD_RANGES = {
    None: (6, 9),
    "easy": (6, 7),
    "medium": (6, 8),
    "hard": (7, 9),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic curriculum slot; seed and band do not alias it."""
    del difficulty
    _validate_call_integers(seed, sample_index)
    return sample_index % LESSON_SCHEDULE_PERIOD


def _validate_call_integers(seed, sample_index) -> None:
    """Preserve signed seeds while refusing silent numeric/string coercion."""
    if type(seed) is not int:
        raise ValueError("seed must be a literal Python integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal Python integer")


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["grid cells must be literal ARC integers in 0..9"]
    return []


def _run_lengths(values: Sequence[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    for value in values:
        if runs and runs[-1][0] == value:
            prior, count = runs[-1]
            runs[-1] = (prior, count + 1)
        else:
            runs.append((value, 1))
    return runs


def _classify_pattern(active: Sequence[int]) -> str | None:
    runs = _run_lengths(active)
    if runs and all(count == 1 for _, count in runs) and len(set(active)) == len(active):
        return "distinct"
    if runs and runs[0][1] >= 2 and all(count == 1 for _, count in runs[1:]):
        return "prefix_run"
    if (
        len(runs) >= 3
        and runs[0][1] >= 2
        and runs[-1][1] >= 2
        and all(count == 1 for _, count in runs[1:-1])
    ):
        return "complex_repeat"
    if runs and all(count == 1 for _, count in runs) and len(set(active)) < len(active):
        return "complex_repeat"
    return None


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return {}, errors

    height, width = len(grid), len(grid[0])
    if height != width:
        return {}, [f"staircase input must be square, found {height}x{width}"]
    if not 4 <= height <= 10:
        errors.append(f"staircase size must be in 4..10, found {height}")

    diag = [grid[index][index] for index in range(height)]
    trailing_zeros = 0
    for value in reversed(diag):
        if value != 0:
            break
        trailing_zeros += 1
    active = diag[: height - trailing_zeros] if trailing_zeros else diag[:]

    if trailing_zeros > 1:
        errors.append(
            f"teaching grammar permits at most one trailing zero padding band, found {trailing_zeros}"
        )
    if not 4 <= len(active) <= 9:
        errors.append(f"active diagonal period must be in 4..9, found {len(active)}")
    if any(value == 0 for value in active):
        errors.append("zero may occur only as the optional final padding band")
    if len(set(active)) < 2:
        errors.append("active diagonal must use at least two colors so the rule is visible")
    pattern_class = _classify_pattern(active)
    if active and pattern_class is None:
        errors.append(
            "active diagonal repetition must be distinct, a single prefix run, "
            "or the scheduled complex-repeat regime"
        )

    for row in range(height):
        for col in range(width):
            expected = diag[max(row, col)]
            if grid[row][col] != expected:
                errors.append(
                    f"cell ({row},{col})={grid[row][col]} breaks the diagonal staircase; expected {expected}"
                )
                return {}, errors

    return {
        "height": height,
        "width": width,
        "diag": diag,
        "active": active,
        "period": len(active),
        "padding": "one" if trailing_zeros == 1 else "none",
        "trailing_zeros": trailing_zeros,
        "pattern_class": pattern_class,
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding staircase inputs."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Official empirical manifold: a lawful 5x5 staircase input."""
    analysis, errors = _analyze(grid)
    if errors:
        return errors
    if analysis["height"] != 5:
        return [f"canonical train/test inputs are 5x5, found {analysis['height']}x{analysis['width']}"]
    return []


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact generated axis from a returned grid."""
    analysis, errors = _analyze(grid)
    if errors:
        return {"period": None, "padding": None, "pattern_class": None}
    return {
        "period": analysis["period"],
        "padding": analysis["padding"],
        "pattern_class": analysis["pattern_class"],
    }


def _draw_period(ctx, sample_index: int, difficulty) -> int:
    if ctx.overrides.get("period") is not None:
        return ctx.draw_int("period", 4, 9)
    slot = int(sample_index) % 4
    if slot == 0:
        return ctx.draw_int("period", 4, 4)
    if slot == 1:
        return ctx.draw_int("period", 5, 5)
    lo, hi = _DIFFICULTY_PERIOD_RANGES[difficulty]
    return ctx.draw_int_diff("period", lo, hi)


def _draw_scheduled_choice(ctx, label: str, values: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, values))
    return str(ctx.draw_choice(label, (scheduled,)))


def _active_sequence(period: int, pattern_class: str, rng, *, separated=False) -> list[int]:
    colors = list(range(1, 10))
    if pattern_class == "distinct":
        return list(rng.sample(colors, period))

    if pattern_class == "prefix_run":
        if separated:
            run_length = rng.randint(2, period - 2)
            palette = rng.sample(colors, period - run_length)
            active = [palette[0]] * run_length + palette[1:]
            position = rng.randint(run_length + 1, len(active))
            return active[:position] + [palette[0]] + active[position:]
        run_length = rng.randint(2, period - 1)
        palette = rng.sample(colors, 1 + period - run_length)
        return [palette[0]] * run_length + palette[1:]

    if pattern_class == "complex_repeat":
        if separated or period == 4:
            # Each rich witness repeats both the first color and a later
            # color in distinct runs, covering both role-conditioned rivals.
            # At period four this is ABAB; contiguous complex patterns need
            # at least three runs and therefore at least five active cells.
            if period >= 6 and rng.randrange(2):
                palette = rng.sample(colors, period - 4)
                return [palette[0], *palette, palette[0], palette[1], palette[1]]
            palette = rng.sample(colors, period - 2)
            return [*palette, *palette[:2]]
        middle_count = period - 4
        palette = rng.sample(colors, middle_count + 2)
        return [palette[0], palette[0], *palette[1:-1], palette[-1], palette[-1]]

    raise ValueError(f"unsupported pattern_class: {pattern_class!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; the Racket rule owns outputs."""
    _validate_call_integers(seed, sample_index)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in _DIFFICULTY_PERIOD_RANGES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    period_override = overrides.get("period")
    if period_override is not None and (
        type(period_override) is not int or not 4 <= period_override <= 9
    ):
        raise ValueError("period must be a literal Python integer in 4..9")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    period = _draw_period(ctx, sample_index, difficulty)
    padding = _draw_scheduled_choice(
        ctx,
        "padding",
        PADDING_MODES,
        "one" if int(sample_index) % 2 == 0 else "none",
    )
    alternate = (sample_index // 3 + seed) % 2
    slot = sample_index % 3
    scheduled_pattern = PATTERN_CLASSES[slot]
    if slot == 0 and alternate == 1:
        scheduled_pattern = "complex_repeat"
    pattern_class = _draw_scheduled_choice(
        ctx,
        "pattern_class",
        PATTERN_CLASSES,
        scheduled_pattern,
    )

    # Every six-slot window has two rich complex witnesses and one separated
    # prefix witness. The other slots retain distinct and contiguous families.
    # Seed parity varies their pairing with padding without changing coverage.
    separated = ((pattern_class == "prefix_run" and alternate == 1)
                 or (pattern_class == "complex_repeat" and slot == 2))
    active = _active_sequence(period, pattern_class, ctx.draw_rng("active_sequence"),
                              separated=separated)
    diag = active + ([0] if padding == "one" else [])
    size = len(diag)
    grid = full_grid(size, size, 0)
    for row in range(size):
        for col in range(size):
            grid[row][col] = diag[max(row, col)]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid staircase scene: {errors}")
    observed = observe_overrides(grid)
    requested = {
        "period": period,
        "padding": padding,
        "pattern_class": pattern_class,
    }
    if observed != requested:
        raise RuntimeError(f"axis observer mismatch: requested={requested}, observed={observed}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------

def _active_diagonal(grid: Sequence[Sequence[int]]) -> list[int]:
    diag = [grid[index][index] for index in range(min(len(grid), len(grid[0])))]
    while diag and diag[-1] == 0:
        diag.pop()
    return diag


def _build_from_sequence(grid: Sequence[Sequence[int]], sequence: Sequence[int], *, height=None, width=None):
    out_h = 2 * len(grid) if height is None else int(height)
    out_w = 2 * len(grid[0]) if width is None else int(width)
    period = len(sequence)
    return [
        [sequence[max(row, col) % period] for col in range(out_w)]
        for row in range(out_h)
    ]


def _expected_output(grid):
    """Python test mirror only; generation never substitutes it for Racket."""
    return _build_from_sequence(grid, _active_diagonal(grid))


def _tile_input_quadrants(grid):
    height, width = len(grid), len(grid[0])
    return [
        [grid[row % height][col % width] for col in range(2 * width)]
        for row in range(2 * height)
    ]


def _row_period_only(grid):
    sequence = _active_diagonal(grid)
    return [
        [sequence[row % len(sequence)] for _ in range(2 * len(grid[0]))]
        for row in range(2 * len(grid))
    ]


def _column_period_only(grid):
    sequence = _active_diagonal(grid)
    row = [sequence[col % len(sequence)] for col in range(2 * len(grid[0]))]
    return [row[:] for _ in range(2 * len(grid))]


def _keep_terminal_zero_in_period(grid):
    sequence = [grid[index][index] for index in range(len(grid))]
    return _build_from_sequence(grid, sequence)


def _always_drop_last_diagonal(grid):
    sequence = [grid[index][index] for index in range(len(grid) - 1)]
    return _build_from_sequence(grid, sequence)


def _deduplicate_active_diagonal(grid):
    sequence: list[int] = []
    for value in _active_diagonal(grid):
        if value not in sequence:
            sequence.append(value)
    return _build_from_sequence(grid, sequence)


def _first_run_per_color(grid):
    """Canonical-fitting rival: keep a color's first full run, skip later runs."""
    seen: set[int] = set()
    sequence: list[int] = []
    for value, count in _run_lengths(_active_diagonal(grid)):
        if value not in seen:
            seen.add(value)
            sequence.extend([value] * count)
    return _build_from_sequence(grid, sequence)


def _role_exempt_first_run(grid, *, exempt_first: bool):
    active = _active_diagonal(grid)
    seen: set[int] = set()
    sequence: list[int] = []
    for value, count in _run_lengths(active):
        exempt = (value == active[0]) == exempt_first
        if exempt or value not in seen:
            sequence.extend([value] * count)
        seen.add(value)
    return _build_from_sequence(grid, sequence)


def _first_color_exempt_first_run(grid):
    """Preserve all first-color runs, but only the first run of other colors."""
    return _role_exempt_first_run(grid, exempt_first=True)


def _other_colors_exempt_first_run(grid):
    """Preserve all later-color runs, but only the first run of the first color."""
    return _role_exempt_first_run(grid, exempt_first=False)


def _fixed_period_four(grid):
    return _build_from_sequence(grid, _active_diagonal(grid)[:4])


def _fixed_output_size_ten(grid):
    return _build_from_sequence(grid, _active_diagonal(grid), height=10, width=10)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "tile_input_quadrants": _tile_input_quadrants,
    "row_period_only": _row_period_only,
    "column_period_only": _column_period_only,
    "keep_terminal_zero_in_period": _keep_terminal_zero_in_period,
    "always_drop_last_diagonal": _always_drop_last_diagonal,
    "deduplicate_active_diagonal": _deduplicate_active_diagonal,
    "first_run_per_color": _first_run_per_color,
    "first_color_exempt_first_run": _first_color_exempt_first_run,
    "other_colors_exempt_first_run": _other_colors_exempt_first_run,
    "fixed_period_four": _fixed_period_four,
    "fixed_output_size_ten": _fixed_output_size_ten,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_output_size_ten": _fixed_output_size_ten,
    "first_run_per_color": _first_run_per_color,
    "first_color_exempt_first_run": _first_color_exempt_first_run,
    "other_colors_exempt_first_run": _other_colors_exempt_first_run,
}


def _analysis_or_none(grid) -> dict[str, Any] | None:
    analysis, errors = _analyze(grid)
    return None if errors else analysis


def _padding_is(mode: str):
    return lambda grid: (
        (analysis := _analysis_or_none(grid)) is not None
        and analysis["padding"] == mode
    )


def _pattern_is(name: str):
    return lambda grid: (
        (analysis := _analysis_or_none(grid)) is not None
        and analysis["pattern_class"] == name
    )


def _canonical_size(grid) -> bool:
    analysis = _analysis_or_none(grid)
    return analysis is not None and analysis["height"] == 5


def _generalized_size(grid) -> bool:
    analysis = _analysis_or_none(grid)
    return analysis is not None and analysis["height"] != 5


def _period_above_five(grid) -> bool:
    analysis = _analysis_or_none(grid)
    return analysis is not None and analysis["period"] > 5


def _cross_axis_geometry(grid) -> bool:
    return _analysis_or_none(grid) is not None


def _separated_color_reappearance(grid) -> bool:
    analysis = _analysis_or_none(grid)
    if analysis is None:
        return False
    runs = [value for value, _ in _run_lengths(analysis["active"])]
    return len(runs) > len(set(runs))


SEMANTIC_WITNESSES = {
    "padding_none": _padding_is("none"),
    "padding_one": _padding_is("one"),
    "pattern_distinct": _pattern_is("distinct"),
    "pattern_prefix_run": _pattern_is("prefix_run"),
    "pattern_complex_repeat": _pattern_is("complex_repeat"),
    "canonical_size_five": _canonical_size,
    "generalized_size": _generalized_size,
    "period_above_five": _period_above_five,
    "cross_axis_max_geometry": _cross_axis_geometry,
    "separated_color_reappearance": _separated_color_reappearance,
}

WITNESS_RIVALS = {
    "padding_none": ["always_drop_last_diagonal"],
    "padding_one": ["keep_terminal_zero_in_period"],
    "pattern_distinct": ["row_period_only", "column_period_only"],
    "pattern_prefix_run": ["deduplicate_active_diagonal"],
    "pattern_complex_repeat": ["deduplicate_active_diagonal", "first_color_exempt_first_run",
                               "other_colors_exempt_first_run"],
    "canonical_size_five": ["tile_input_quadrants"],
    "generalized_size": ["fixed_output_size_ten"],
    "period_above_five": ["fixed_period_four"],
    "separated_color_reappearance": ["first_run_per_color", "first_color_exempt_first_run",
                                      "other_colors_exempt_first_run"],
    "cross_axis_max_geometry": [
        "tile_input_quadrants",
        "row_period_only",
        "column_period_only",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every lesson to refute the named plausible wrong rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful staircase grammar")
    elif "output" in query and query["output"] != _expected_output(query["input"]):
        reasons.append("query output is not the authoritative periodic staircase")

    valid_demos: list[dict[str, Any]] = []
    observed: list[dict[str, object]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the lawful staircase grammar")
            continue
        expected = _expected_output(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the authoritative periodic staircase")
            continue
        valid_demos.append(demo)
        observed.append(observe_overrides(demo["input"]))

    if valid_demos:
        padding_seen = {str(item["padding"]) for item in observed}
        sizes_seen = {len(demo["input"]) == 5 for demo in valid_demos}
        periods_seen = {int(item["period"]) for item in observed}
        if padding_seen != set(PADDING_MODES):
            reasons.append(f"demonstrations must cover both padding branches, saw {sorted(padding_seen)}")
        if sizes_seen != {False, True}:
            reasons.append("demonstrations must include canonical-size and generalized-size inputs")
        if not any(period > 5 for period in periods_seen):
            reasons.append("demonstrations must include a period above five")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
