"""Generator for horizontal-run midpoint extraction (ARC task 27bc4c66eed7).

For every maximal non-zero horizontal run, the selected rule paints the run's
right-middle cell (``start + length // 2``) in the same color on a fresh zero
grid.  Runs may share rows or colors, and lengths may be odd, even, or one.

The ordinary five-example schedule keeps four canonical-scale anchors and one
adversarial repeated-color scene.  Consequently every five consecutive lesson
examples contain a counterexample to the strongest canonical-fitting shortcut:
"emit at most one midpoint per color".
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "27bc4c66eed7"
TASK_ID = "27bc4c66eed7"
VERSION = "3.0.0"
RULE_HASH = "a6711bc4802c"
EXAMPLES_NEEDED = 5

SUMMARY = (
    "A 5-7 by 7-10 zero-background grid contains 2-5 maximal horizontal "
    "monochrome runs. Runs can share a row or a color; lengths cover 1-5, "
    "including singleton and even runs. On a fresh zero grid, replace every "
    "run independently by one same-colored cell at start + length // 2 "
    "(the right-middle cell for even lengths)."
)

INVARIANTS = [
    "background is 0 and foreground colors are 1..9",
    "ordinary inputs contain 2-5 maximal non-zero horizontal runs",
    "each run has length 1-5",
    "every run is transformed independently, even when colors repeat",
]

COLOR_MODES = ("distinct", "repeat")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted schedule",
        "valid": "5..7",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted schedule",
        "valid": "7..10",
    },
    "n_runs": {
        "type": "int",
        "default": "canonical-weighted 2..5",
        "valid": "2..5",
    },
    "color_mode": {
        "type": "enum",
        "default": "four distinct-color anchors, then one repeated-color witness",
        "valid": "distinct|repeat",
    },
    "run_length": {
        "type": "int",
        "default": "cycles 0,2,3,4,5; 0 means mixed lengths",
        "valid": "0..5",
        "description": "0 means at least two distinct lengths; 1..5 fixes every run to that length",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Four exact (height, width, palette-size) anchors from the public task, then
# one extrapolative branch.  The lengths are reordered only so the first pair
# can share a row constructively; the canonical length multisets are retained.
_PROFILE_SPECS = {
    "canonical_5x7_palette3": {
        "h": 5,
        "w": 7,
        "n_runs": 2,
        "lengths": (5, 3),
        "shared": False,
    },
    "canonical_5x7_palette5": {
        "h": 5,
        "w": 7,
        "n_runs": 4,
        "lengths": (3, 2, 5, 3),
        "shared": True,
    },
    "canonical_5x9_palette4": {
        "h": 5,
        "w": 9,
        "n_runs": 3,
        "lengths": (3, 3, 5),
        "shared": True,
    },
    "canonical_6x8_palette5": {
        "h": 6,
        "w": 8,
        "n_runs": 4,
        "lengths": (3, 3, 5, 3),
        "shared": True,
    },
    "adversarial_repeated_color": None,
}
SCHEDULE_PROFILES = tuple(_PROFILE_SPECS)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the finite curriculum branch used by an ordinary draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not all(isinstance(row, list) and row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _horizontal_runs(grid):
    """Return row-major maximal non-zero same-color horizontal runs."""
    runs = []
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            color = row[column]
            start = column
            while column + 1 < len(row) and row[column + 1] == color:
                column += 1
            runs.append((row_index, start, column, color))
            column += 1
    return runs


def apply_rule(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    shape = _grid_shape(grid)
    if shape is None:
        raise ValueError("grid must be a non-empty rectangle")
    height, width = shape
    output = full_grid(height, width, 0)
    for row, start, end, color in _horizontal_runs(grid):
        output[row][start + (end - start + 1) // 2] = color
    return output


rule_mirror = apply_rule


def _one_midpoint_per_color(grid) -> list[list[int]]:
    """Canonical-fitting rival: keep only the first run seen for each color."""
    shape = _grid_shape(grid)
    if shape is None:
        raise ValueError("grid must be a non-empty rectangle")
    height, width = shape
    output = full_grid(height, width, 0)
    seen: set[int] = set()
    for row, start, end, color in _horizontal_runs(grid):
        if color in seen:
            continue
        seen.add(color)
        output[row][start + (end - start + 1) // 2] = color
    return output


def _has_repeated_color_runs(grid) -> bool:
    colors = [color for _, _, _, color in _horizontal_runs(grid)]
    return len(colors) > len(set(colors))


SEMANTIC_WITNESSES = {
    "repeated_color_runs": _has_repeated_color_runs,
}
SEMANTIC_RIVALS = {
    "one_midpoint_per_color": _one_midpoint_per_color,
}
WITNESS_RIVALS = {
    "repeated_color_runs": ("one_midpoint_per_color",),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

def _is_monochrome_solid_2x2(grid) -> bool:
    """The generic rule handles this, but it is an ambiguous teaching-only case."""
    foreground = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]
    if len(foreground) != 4 or len({value for _, _, value in foreground}) != 1:
        return False
    rows = {row for row, _, _ in foreground}
    columns = {column for _, column, _ in foreground}
    return (
        len(rows) == 2
        and len(columns) == 2
        and max(rows) - min(rows) == 1
        and max(columns) - min(columns) == 1
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the finite teaching grammar without narrowing the authority."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of rows"]
    height, width = shape
    errors: list[str] = []
    if not 5 <= height <= 7:
        errors.append(f"height must be in 5..7, got {height}")
    if not 7 <= width <= 10:
        errors.append(f"width must be in 7..10, got {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid colors must be integers in 0..9")
        return sorted(set(errors))

    runs = _horizontal_runs(grid)
    if _is_monochrome_solid_2x2(grid):
        errors.append(
            "a lone monochrome solid 2x2 is outside the teaching grammar; "
            "it aliases a two-dimensional object with two independent row runs"
        )
    if not 2 <= len(runs) <= 5:
        errors.append(f"expected 2-5 horizontal runs, found {len(runs)}")
    for row, start, end, _ in runs:
        length = end - start + 1
        if not 1 <= length <= 5:
            errors.append(
                f"run at row {row}, columns {start}..{end} has length {length}; expected 1..5"
            )
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public exact axis from a returned valid input."""
    shape = _grid_shape(grid)
    if shape is None:
        return {
            "grid_h": -1,
            "grid_w": -1,
            "n_runs": -1,
            "color_mode": "invalid",
            "run_length": -1,
        }
    height, width = shape
    runs = _horizontal_runs(grid)
    colors = [color for _, _, _, color in runs]
    lengths = [end - start + 1 for _, start, end, _ in runs]
    common_length = lengths[0] if lengths and len(set(lengths)) == 1 else 0
    return {
        "grid_h": height,
        "grid_w": width,
        "n_runs": len(runs),
        "color_mode": "distinct" if len(colors) == len(set(colors)) else "repeat",
        "run_length": common_length,
    }


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))
    ranges = {
        "grid_h": (5, 7),
        "grid_w": (7, 10),
        "n_runs": (2, 5),
        "run_length": (0, 5),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in ranges:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
            low, high = ranges[name]
            if not low <= value <= high:
                raise ValueError(f"{name}={value} outside declared range {low}..{high}")
        elif name == "color_mode" and value not in COLOR_MODES:
            raise ValueError(
                f"color_mode={value!r} outside declared values {COLOR_MODES}"
            )


def _draw_scheduled_int(ctx, label: str, scheduled: int, low: int, high: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, low, high)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled, options: tuple):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _broad_defaults(ctx, difficulty) -> tuple[int, int, int]:
    rng = ctx.draw_rng("broad_defaults")
    if difficulty == "easy":
        return rng.choice((5, 6)), rng.choice((7, 8, 9)), rng.choice((2, 3))
    if difficulty == "hard":
        return rng.choice((6, 7)), rng.choice((9, 10)), rng.choice((4, 5))
    return rng.choice((5, 6, 7)), rng.choice((7, 8, 9, 10)), rng.choice((3, 4))


def _mixed_lengths(n_runs: int, rng) -> list[int]:
    """At least one singleton, one even run, and two distinct lengths."""
    tail = [3, 4, 5]
    rng.shuffle(tail)
    return ([1, 2] + tail)[:n_runs]


def _colors_for(n_runs: int, color_mode: str, rng) -> list[int]:
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if color_mode == "distinct":
        return palette[:n_runs]
    # Exactly one repeated pair and all other runs distinct.  Keeping the pair
    # first lets the shared-row branch expose two separated runs of one color.
    return [palette[0], palette[0], *palette[1 : n_runs - 1]]


def _paint_run(grid, row: int, start: int, length: int, color: int) -> None:
    for column in range(start, start + length):
        if grid[row][column] != 0:
            raise AssertionError("constructive placement attempted to overlap runs")
        grid[row][column] = color


def _place_runs(
    height: int,
    width: int,
    lengths: list[int],
    colors: list[int],
    *,
    prefer_shared: bool,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    rows = list(range(height))
    rng.shuffle(rows)
    n_runs = len(lengths)

    share_first_pair = (
        prefer_shared
        and n_runs >= 2
        and lengths[0] + 1 + lengths[1] <= width
    )
    placed_from = 0
    used_row_count = 0
    if share_first_pair:
        order = [0, 1]
        rng.shuffle(order)
        total = lengths[order[0]] + 1 + lengths[order[1]]
        left = rng.randint(0, width - total)
        first = order[0]
        second = order[1]
        _paint_run(grid, rows[0], left, lengths[first], colors[first])
        second_start = left + lengths[first] + 1
        _paint_run(grid, rows[0], second_start, lengths[second], colors[second])
        placed_from = 2
        used_row_count = 1

    if not share_first_pair:
        placed_from = 0
        used_row_count = 0
        # Avoid the one minimal shape intentionally excluded by self_check.
        # It is authority-lawful but visually aliases one 2-D square with two
        # independent horizontal runs, so it is too weak for the curriculum.
        if (
            n_runs == 2
            and colors[0] == colors[1]
            and lengths == [2, 2]
            and abs(rows[0] - rows[1]) == 1
        ):
            replacement = next(
                index for index in range(2, len(rows))
                if abs(rows[0] - rows[index]) > 1
            )
            rows[1], rows[replacement] = rows[replacement], rows[1]

    for index in range(placed_from, n_runs):
        row = rows[used_row_count]
        used_row_count += 1
        start = rng.randint(0, width - lengths[index])
        _paint_run(grid, row, start, lengths[index], colors[index])
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic task input with exact public overrides."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    spec = _PROFILE_SPECS[profile]
    if spec is None:
        scheduled_h, scheduled_w, scheduled_runs = _broad_defaults(ctx, difficulty)
        scheduled_color_mode = "repeat"
        prefer_shared = True
        preset_lengths = None
    else:
        scheduled_h = int(spec["h"])
        scheduled_w = int(spec["w"])
        scheduled_runs = int(spec["n_runs"])
        scheduled_color_mode = "distinct"
        prefer_shared = bool(spec["shared"])
        preset_lengths = list(spec["lengths"])

    height = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 5, 7)
    width = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 7, 10)
    n_runs = _draw_scheduled_int(ctx, "n_runs", scheduled_runs, 2, 5)
    color_mode = _draw_scheduled_choice(
        ctx, "color_mode", scheduled_color_mode, COLOR_MODES
    )
    scheduled_run_length = (
        0
        if profile == "adversarial_repeated_color"
        else (0, 2, 3, 4, 5)[(int(sample_index) // 5) % 5]
    )
    run_length = _draw_scheduled_int(
        ctx, "run_length", scheduled_run_length, 0, 5
    )

    layout_rng = ctx.draw_rng("layout")
    use_preset = (
        preset_lengths is not None
        and n_runs == scheduled_runs
        and run_length == 0
        and overrides.get("n_runs") is None
        and overrides.get("run_length") is None
    )
    if use_preset:
        lengths = preset_lengths
    elif run_length == 0:
        lengths = _mixed_lengths(n_runs, ctx.draw_rng("mixed_lengths"))
    else:
        lengths = [run_length] * n_runs

    colors = _colors_for(n_runs, color_mode, ctx.draw_rng("colors"))
    grid = _place_runs(
        height,
        width,
        lengths,
        colors,
        prefer_shared=prefer_shared,
        rng=layout_rng,
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_runs": n_runs,
        "color_mode": color_mode,
        "run_length": run_length,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    return grid


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons in which the declared canonical-fitting rival survives."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = apply_rule(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the midpoint rule")
    try:
        query_answer = apply_rule(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the midpoint rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-linked malformed inputs that the structural validator must reject."""
    blank = full_grid(5, 7, 0)
    one_run = full_grid(5, 7, 0)
    one_run[1][1:4] = [3, 3, 3]
    too_long = full_grid(5, 7, 0)
    too_long[0][0:6] = [4] * 6
    too_long[3][2:4] = [7, 7]
    too_many = full_grid(7, 7, 0)
    for row in range(6):
        too_many[row][row % 5] = row % 9 + 1
    bad_color = full_grid(5, 7, 0)
    bad_color[0][0] = 10
    bad_color[2][2] = 3
    solid_2x2 = full_grid(5, 7, 0)
    for row in (0, 1):
        for column in (0, 1):
            solid_2x2[row][column] = 6
    return [
        ("blank grid has no runs", blank),
        ("only one run", one_run),
        ("run longer than five", too_long),
        ("more than five runs", too_many),
        ("out-of-range color", bad_color),
        ("ambiguous monochrome solid 2x2", solid_2x2),
    ]
