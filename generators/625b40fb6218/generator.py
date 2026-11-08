"""Input generator for ARC task 625b40fb6218 (original ARC d47aa2ff).

A full-height gray (5) column divides two equal-width panels.  The authoritative
rule compares aligned cells and returns only the left-sized panel:

* left nonzero, right zero -> red (2)
* left zero, right nonzero -> blue (1)
* otherwise -> the left value

The canonical demonstrations contain equal-colored overlaps only.  Ordinary
samples therefore include unequal-colored overlaps so that two especially
plausible canonical shortcuts become observably wrong: preserving an overlap
only when its colors match, and giving the right panel priority on conflicts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "625b40fb6218"
TASK_ID = GENERATOR_ID
RULE_HASH = "53f987296312"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Compare aligned cells in two panels separated by gray: left-only becomes "
    "2, right-only becomes 1, and overlaps preserve the left color."
)

INVARIANTS = [
    "one centered full-height color-5 separator divides equal-width panels",
    "input foreground uses 2..5 colors drawn from 3,4,6,7,8,9",
    "every lawful input contains left-only, right-only, and equal-overlap cells",
    "ordinary defaults also contain unequal overlaps that expose left priority",
    "all advertised controls are exact and recoverable from returned pixels",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 6..14 with canonical-height anchors",
        "valid": "6..14",
        "doc": "Exact input height; explicit overrides have the same domain in every band.",
    },
    "half_w": {
        "type": "int",
        "default": "scheduled 4..12 with canonical-width anchors",
        "valid": "4..12",
        "doc": "Exact width of each panel; total input width is 2*half_w+1.",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "2..5",
        "doc": "Exact number of nonseparator foreground colors realized in the input.",
    },
    "n_left_only": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
        "doc": "Exact aligned positions occupied only in the left panel.",
    },
    "n_right_only": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
        "doc": "Exact aligned positions occupied only in the right panel.",
    },
    "n_shared_equal": {
        "type": "int",
        "default": "scheduled 3..8",
        "valid": "3..8",
        "doc": "Exact aligned positions occupied by the same color in both panels.",
    },
    "n_shared_conflict": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "0..4",
        "doc": "Exact aligned positions occupied by different nonzero colors.",
    },
}

_INPUT_COLORS = (3, 4, 6, 7, 8, 9)
_BOUNDS = {
    "grid_h": (6, 14),
    "half_w": (4, 12),
    "palette_size": (2, 5),
    "n_left_only": (1, 4),
    "n_right_only": (1, 4),
    "n_shared_equal": (3, 8),
    "n_shared_conflict": (0, 4),
}
_BAND_OFFSET = {None: 0, "easy": 1, "medium": 3, "hard": 5}

# (height, half width, foreground palette, left-only, right-only,
#  equal overlap, unequal overlap).  Profiles 0 and 1 exactly match the
# canonical (height, total width, total palette size) profiles while still
# adding a conflict witness absent from the canonical demonstrations.
SCHEDULE_PROFILES = tuple(range(8))
_PROFILE_SPECS = (
    (10, 10, 2, 1, 1, 6, 1),
    (10, 10, 3, 2, 2, 6, 2),
    (6, 4, 2, 1, 1, 3, 1),
    (7, 5, 3, 2, 1, 4, 1),
    (8, 6, 4, 2, 2, 5, 2),
    (11, 7, 5, 3, 3, 6, 2),
    (12, 9, 4, 4, 3, 7, 3),
    (14, 12, 5, 4, 4, 8, 4),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Deterministic eight-profile cycle; bands rotate rather than narrow it."""
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    # Use a coefficient pair that remains coprime to the eight-profile cycle
    # under common paired seed/sample-index sweeps (including i and 11*i).
    return (
        int(seed) + int(sample_index) * 2 + _BAND_OFFSET[difficulty]
    ) % len(SCHEDULE_PROFILES)


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_exact_int(ctx, name: str, scheduled: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty sequence of rows"
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return "every row must be a sequence"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "grid values must be integer ARC colors in 0..9"
    return None


def _split(grid: list[list[int]] | tuple[tuple[int, ...], ...]):
    height = len(grid)
    width = len(grid[0])
    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(
            f"expected exactly one full-height color-5 separator, found {separators}"
        )
    separator = separators[0]
    if separator * 2 + 1 != width:
        raise ValueError("separator must be centered between equal-width panels")
    left = [list(row[:separator]) for row in grid]
    right = [list(row[separator + 1 :]) for row in grid]
    return separator, left, right


def _branch_counts(left, right) -> dict[str, int]:
    counts = {
        "n_left_only": 0,
        "n_right_only": 0,
        "n_shared_equal": 0,
        "n_shared_conflict": 0,
    }
    for left_row, right_row in zip(left, right):
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                counts["n_left_only"] += 1
            elif left_value == 0 and right_value != 0:
                counts["n_right_only"] += 1
            elif left_value != 0 and right_value != 0:
                if left_value == right_value:
                    counts["n_shared_equal"] += 1
                else:
                    counts["n_shared_conflict"] += 1
    return counts


def _analyze(grid: Any) -> dict[str, Any]:
    error = _shape_error(grid)
    if error:
        return {"errors": [error]}

    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    try:
        half_w, left, right = _split(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}

    if not _BOUNDS["grid_h"][0] <= height <= _BOUNDS["grid_h"][1]:
        errors.append(f"grid height {height} outside 6..14")
    if not _BOUNDS["half_w"][0] <= half_w <= _BOUNDS["half_w"][1]:
        errors.append(f"panel width {half_w} outside 4..12")

    allowed = {0, 5, *_INPUT_COLORS}
    unexpected = sorted({value for row in grid for value in row} - allowed)
    if unexpected:
        errors.append(f"unexpected input colors: {unexpected}")
    if any(value == 5 for row in left + right for value in row):
        errors.append("color 5 may appear only in the separator")

    foreground = {
        value for row in left + right for value in row if value not in (0, 5)
    }
    palette_size = len(foreground)
    lo, hi = _BOUNDS["palette_size"]
    if not lo <= palette_size <= hi:
        errors.append(f"foreground palette size {palette_size} outside [{lo}, {hi}]")

    counts = _branch_counts(left, right)
    for name, value in counts.items():
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            errors.append(f"{name}={value} outside [{lo}, {hi}]")

    return {
        "errors": errors,
        "grid_h": height,
        "half_w": half_w,
        "palette_size": palette_size,
        **counts,
        "left": left,
        "right": right,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = dict(zip(AXES, _PROFILE_SPECS[profile]))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    values = {name: _draw_exact_int(ctx, name, scheduled[name]) for name in AXES}

    height = values["grid_h"]
    half_w = values["half_w"]
    needed_positions = (
        values["n_left_only"]
        + values["n_right_only"]
        + values["n_shared_equal"]
        + values["n_shared_conflict"]
    )
    if needed_positions > height * half_w:
        raise ValueError(
            f"requested {needed_positions} occupied aligned positions but "
            f"{height}x{half_w} panels have only {height * half_w}"
        )

    positions = [(row, col) for row in range(height) for col in range(half_w)]
    placement_rng = ctx.draw_rng("placement")
    placement_rng.shuffle(positions)
    positions = positions[:needed_positions]

    palette = list(_INPUT_COLORS)
    color_rng = ctx.draw_rng("palette")
    color_rng.shuffle(palette)
    palette = palette[: values["palette_size"]]

    assignment_count = (
        values["n_left_only"]
        + values["n_right_only"]
        + values["n_shared_equal"]
        + 2 * values["n_shared_conflict"]
    )
    if assignment_count < len(palette):
        raise ValueError(
            "requested branch counts cannot realize the requested palette size"
        )
    # Every requested color appears at least once; adjacent tokens are distinct,
    # so every conflict is a true unequal overlap.
    start = color_rng.randrange(len(palette))
    tokens = [palette[(start + index) % len(palette)] for index in range(assignment_count)]

    width = 2 * half_w + 1
    separator = half_w
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][separator] = 5

    position_index = 0
    token_index = 0
    for _ in range(values["n_left_only"]):
        row, col = positions[position_index]
        position_index += 1
        grid[row][col] = tokens[token_index]
        token_index += 1

    for _ in range(values["n_right_only"]):
        row, col = positions[position_index]
        position_index += 1
        grid[row][separator + 1 + col] = tokens[token_index]
        token_index += 1

    for _ in range(values["n_shared_equal"]):
        row, col = positions[position_index]
        position_index += 1
        color = tokens[token_index]
        token_index += 1
        grid[row][col] = color
        grid[row][separator + 1 + col] = color

    for _ in range(values["n_shared_conflict"]):
        row, col = positions[position_index]
        position_index += 1
        left_color = tokens[token_index]
        right_color = tokens[token_index + 1]
        token_index += 2
        if left_color == right_color:
            raise AssertionError("constructed shared-conflict colors must differ")
        grid[row][col] = left_color
        grid[row][separator + 1 + col] = right_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != values:
        raise AssertionError(
            f"axis realization mismatch: expected {values}, observed {observed}"
        )
    return grid


# ---------------------------------------------------------------------------
# Public structural and semantic contracts
# ---------------------------------------------------------------------------


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {name: analysis[name] for name in AXES}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    _, left, right = _split(grid)
    output: list[list[int]] = []
    for left_row, right_row in zip(left, right):
        out_row: list[int] = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            else:
                out_row.append(left_value)
        output.append(out_row)
    return output


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {name: analysis[name] for name in AXES}


def _has_branch(name: str):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis[name] > 0

    return predicate


def _equal_overlap_only(grid):
    """Rival: unequal occupied overlaps are erased instead of left-priority."""
    error = _shape_error(grid)
    if error:
        return None
    _, left, right = _split(grid)
    output: list[list[int]] = []
    for left_row, right_row in zip(left, right):
        out_row: list[int] = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            elif left_value == right_value:
                out_row.append(left_value)
            else:
                out_row.append(0)
        output.append(out_row)
    return output


def _right_priority_overlap(grid):
    """Rival: use the right value rather than the left on occupied conflicts."""
    error = _shape_error(grid)
    if error:
        return None
    _, left, right = _split(grid)
    output: list[list[int]] = []
    for left_row, right_row in zip(left, right):
        out_row: list[int] = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            elif left_value != 0 and right_value != 0:
                out_row.append(right_value)
            else:
                out_row.append(0)
        output.append(out_row)
    return output


def _color_priority_overlap(color: int):
    """Lesson rival: an occupied overlap prefers one foreground color."""
    def competitor(grid):
        error = _shape_error(grid)
        if error:
            return None
        _, left, right = _split(grid)
        output = rule_mirror(grid)
        for row, (left_row, right_row) in enumerate(zip(left, right)):
            for col, (left_value, right_value) in enumerate(zip(left_row, right_row)):
                if left_value != 0 and right_value != 0 and color in (left_value, right_value):
                    output[row][col] = color
        return output

    return competitor


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "left_only": _has_branch("n_left_only"),
    "right_only": _has_branch("n_right_only"),
    "equal_overlap": _has_branch("n_shared_equal"),
    "unequal_overlap": _has_branch("n_shared_conflict"),
}
BRANCH_WITNESSES = ("left_only", "right_only", "equal_overlap")
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]] | None]] = {
    "equal_overlap_only": _equal_overlap_only,
    "right_priority_overlap": _right_priority_overlap,
}
WITNESS_RIVALS = {
    "unequal_overlap": ["equal_overlap_only", "right_priority_overlap"]
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Sampling and canonical shortcut contracts stay unchanged. Reject a lesson
# only when a surviving color preference changes this particular query.
LESSON_COMPETITORS.update({
    f"color_priority_{color}": _color_priority_overlap(color)
    for color in _INPUT_COLORS
})
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the two-panel grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the two-panel grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the selected rule")
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
