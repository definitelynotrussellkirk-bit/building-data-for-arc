"""Constructive sampler for the row-local exact-two-fives span rule.

For each row independently, the selected Racket authority acts only when the
row contains exactly two color-5 cells, they are non-adjacent, and every cell
strictly between them is 0.  It replaces that whole zero interior with color 3.
All other rows are unchanged.

The default three-slot curriculum alternates canonical-profile inputs with two
teaching profiles.  Every three consecutive examples therefore contains a
minimal one-zero positive and counterexamples to four plausible shortcuts:
ignoring blockers, accepting three-or-more 5s, generalizing to any repeated
color, and requiring at least two zeros in the span.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3a96552d8c7c"
TASK_ID = GENERATOR_ID
RULE_HASH = "91ba1164c014"
VERSION = "2.0.0"

SUMMARY = (
    "Rows with exactly two separated 5s and an all-zero interior are filled "
    "with 3 between the endpoints; blocked, wrong-color, and three-5 rows stay unchanged."
)

EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0; positive rows contain exactly two color-5 endpoints",
    "positive interiors are nonempty and all 0 before rule execution",
    "the minimum legal one-zero span is represented in every default draw",
    "negative curricula isolate blockers, >2 endpoints, and wrong-color repetition",
    "2..4 positive rows ensure every generated input changes under the authority",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 6..10", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "scheduled 8..14", "valid": "8..14"},
    "n_fill_rows": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "span_style": {
        "type": "str",
        "default": "scheduled short/long/mixed",
        "valid": "short|long|mixed",
    },
    "negative_mode": {
        "type": "str",
        "default": "scheduled none/mixed",
        "valid": "none|blocked|three_fives|wrong_color|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_INT_DOMAINS = {
    "grid_h": (6, 10),
    "grid_w": (8, 14),
    "n_fill_rows": (2, 4),
}
_CHOICE_DOMAINS = {
    "span_style": ("short", "long", "mixed"),
    "negative_mode": ("none", "blocked", "three_fives", "wrong_color", "mixed"),
}
_NEGATIVE_ROWS = {
    "none": 0,
    "blocked": 1,
    "three_fives": 1,
    "wrong_color": 1,
    "mixed": 2,
}

SCHEDULE_PROFILES = ("canonical", "teaching_a", "teaching_b")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Three-slot curriculum; any three consecutive samples cover all profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(profile: str, sample_index: int, difficulty) -> dict[str, Any]:
    if profile == "canonical":
        # Rotate through all public canonical (height, width, palette-size) profiles.
        canonical = (
            dict(grid_h=6, grid_w=8, n_fill_rows=3),
            dict(grid_h=7, grid_w=9, n_fill_rows=3),
            dict(grid_h=8, grid_w=10, n_fill_rows=4),
        )
        row = dict(canonical[(int(sample_index) // 3) % len(canonical)])
        row.update(span_style="mixed", negative_mode="none")
        return row

    teaching = {
        "easy": {
            "teaching_a": dict(grid_h=6, grid_w=8, n_fill_rows=2),
            "teaching_b": dict(grid_h=7, grid_w=10, n_fill_rows=3),
        },
        "medium": {
            "teaching_a": dict(grid_h=8, grid_w=11, n_fill_rows=3),
            "teaching_b": dict(grid_h=9, grid_w=12, n_fill_rows=4),
        },
        "hard": {
            "teaching_a": dict(grid_h=10, grid_w=14, n_fill_rows=4),
            "teaching_b": dict(grid_h=9, grid_w=13, n_fill_rows=3),
        },
    }
    band = difficulty if difficulty in teaching else "medium"
    row = dict(teaching[band][profile])
    row.update(span_style="mixed", negative_mode="mixed")
    return row


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_DOMAINS:
            lo, hi = _INT_DOMAINS[name]
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        else:
            options = _CHOICE_DOMAINS[name]
            if type(value) is not str or value not in options:
                raise ValueError(f"{name} must be one of {options}, not {value!r}")


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _span_candidates(width: int, kind: str, *, exact_one: bool = False) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for left in range(width):
        for right in range(left + 2, width):
            gap = right - left - 1
            if exact_one and gap != 1:
                continue
            if kind == "short" and gap <= 2:
                candidates.append((left, right))
            elif kind == "long" and gap >= 3:
                candidates.append((left, right))
    if not candidates:
        qualifier = "one-zero " if exact_one else ""
        raise ValueError(f"grid_w={width} cannot realize {qualifier}{kind!r} spans")
    return candidates


def _span_kinds(style: str, count: int, rng) -> list[str]:
    if style == "short":
        return ["short"] * count
    if style == "long":
        return ["long"] * count
    kinds = ["short", "long"]
    kinds.extend(rng.choice(("short", "long")) for _ in range(count - 2))
    rng.shuffle(kinds)
    return kinds


def _place_negative_rows(grid: list[list[int]], rows: list[int], mode: str) -> None:
    width = len(grid[0])
    if mode == "none":
        return
    if mode == "blocked":
        row = grid[rows[0]]
        row[0] = row[-1] = 5
        row[width // 2] = 4
        return
    if mode == "three_fives":
        row = grid[rows[0]]
        for column in (0, width // 2, width - 1):
            row[column] = 5
        return
    if mode == "wrong_color":
        row = grid[rows[0]]
        row[1] = row[-2] = 4
        return
    if mode == "mixed":
        combined = grid[rows[0]]
        combined[0] = combined[-1] = 5
        combined[2] = combined[-3] = 4
        three = grid[rows[1]]
        for column in (1, width // 2, width - 2):
            three[column] = 5
        return
    raise AssertionError(f"unhandled negative mode {mode!r}")


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
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(profile, sample_index, difficulty)

    height = _scheduled_int(ctx, "grid_h", 6, 10, int(defaults["grid_h"]))
    width = _scheduled_int(ctx, "grid_w", 8, 14, int(defaults["grid_w"]))
    n_fill_rows = _scheduled_int(
        ctx, "n_fill_rows", 2, 4, int(defaults["n_fill_rows"])
    )
    span_style = _scheduled_choice(
        ctx, "span_style", _CHOICE_DOMAINS["span_style"], str(defaults["span_style"])
    )
    negative_mode = _scheduled_choice(
        ctx,
        "negative_mode",
        _CHOICE_DOMAINS["negative_mode"],
        str(defaults["negative_mode"]),
    )

    required_rows = n_fill_rows + _NEGATIVE_ROWS[negative_mode]
    if required_rows > height:  # defensive; declared domains make this unreachable
        raise ValueError(
            f"grid_h={height} cannot hold n_fill_rows={n_fill_rows} "
            f"with negative_mode={negative_mode!r}"
        )

    grid = full_grid(height, width, 0)
    rows = list(range(height))
    ctx.draw_rng("row_order").shuffle(rows)
    fill_rows = rows[:n_fill_rows]
    negative_rows = rows[n_fill_rows:required_rows]

    kinds = _span_kinds(span_style, n_fill_rows, ctx.draw_rng("span_kind_order"))
    endpoint_rng = ctx.draw_rng("endpoints")
    used_one_zero = False
    for row_index, kind in zip(fill_rows, kinds):
        exact_one = kind == "short" and not used_one_zero
        candidates = _span_candidates(width, kind, exact_one=exact_one)
        left, right = endpoint_rng.choice(candidates)
        grid[row_index][left] = 5
        grid[row_index][right] = 5
        if right - left == 2:
            used_one_zero = True

    _place_negative_rows(grid, negative_rows, negative_mode)
    return grid


def _classify_row(row: list[int]) -> tuple[str, int | None]:
    nonzero = [(column, value) for column, value in enumerate(row) if value]
    if not nonzero:
        return "empty", None
    fives = [column for column, value in nonzero if value == 5]
    fours = [column for column, value in nonzero if value == 4]
    values = {value for _, value in nonzero}

    if values == {5} and len(fives) == 2 and fives[1] > fives[0] + 1:
        return "trigger", fives[1] - fives[0] - 1
    if values == {5} and len(fives) == 3:
        return "three_fives", None
    if values == {4} and len(fours) == 2 and fours[1] > fours[0] + 1:
        return "wrong_color", None
    if values == {4, 5} and len(fives) == 2 and len(fours) in (1, 2):
        left, right = fives
        if all(left < column < right for column in fours):
            if len(fours) == 1:
                return "blocked", None
            if fours[1] > fours[0] + 1:
                return "blocked_wrong_color", None
    return "malformed", None


def _inspect(grid) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 10:
        errors.append(f"grid_h={height} outside [6,10]")
    if not 8 <= width <= 14:
        errors.append(f"grid_w={width} outside [8,14]")

    row_kinds: list[str] = []
    gaps: list[int] = []
    for row_index, raw_row in enumerate(grid):
        kind, gap = _classify_row(list(raw_row))
        row_kinds.append(kind)
        if kind == "malformed":
            errors.append(f"row {row_index} is outside the reviewed row grammar")
        if gap is not None:
            gaps.append(gap)

    n_fill_rows = row_kinds.count("trigger")
    if not 2 <= n_fill_rows <= 4:
        errors.append(f"n_fill_rows={n_fill_rows} outside [2,4]")

    has_short = any(gap <= 2 for gap in gaps)
    has_long = any(gap >= 3 for gap in gaps)
    span_style = None
    if gaps:
        span_style = "mixed" if has_short and has_long else ("short" if has_short else "long")

    negative_counts = Counter(
        kind for kind in row_kinds if kind not in {"empty", "trigger", "malformed"}
    )
    if not negative_counts:
        negative_mode = "none"
    elif negative_counts == Counter({"blocked": 1}):
        negative_mode = "blocked"
    elif negative_counts == Counter({"three_fives": 1}):
        negative_mode = "three_fives"
    elif negative_counts == Counter({"wrong_color": 1}):
        negative_mode = "wrong_color"
    elif negative_counts == Counter({"blocked_wrong_color": 1, "three_fives": 1}):
        negative_mode = "mixed"
    else:
        negative_mode = None
        errors.append(f"unrecognized negative-row combination: {dict(negative_counts)}")

    observed = {
        "grid_h": height,
        "grid_w": width,
        "n_fill_rows": n_fill_rows,
        "span_style": span_style,
        "negative_mode": negative_mode,
    }
    return observed, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _inspect(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the explicit lawful grammar, including reviewed teaching negatives."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover all advertised exact controls from returned pixels."""
    observed, errors = _inspect(grid)
    if observed is None or errors:
        raise ValueError("; ".join(errors))
    return observed


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        fives = [column for column, value in enumerate(row) if value == 5]
        if len(fives) != 2:
            continue
        left, right = fives
        if right <= left + 1:
            continue
        if all(row[column] == 0 for column in range(left + 1, right)):
            for column in range(left + 1, right):
                out[row_index][column] = 3
    return out


def _needs_two_zeros(grid):
    """Rival: requires at least two zeros, missing the legal 5-0-5 boundary."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        fives = [column for column, value in enumerate(row) if value == 5]
        if len(fives) == 2:
            left, right = fives
            if right - left - 1 >= 2 and all(
                row[column] == 0 for column in range(left + 1, right)
            ):
                for column in range(left + 1, right):
                    out[row_index][column] = 3
    return out


def _ignore_blockers(grid):
    """Rival: any separated exact pair of 5s paints its entire interior."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        fives = [column for column, value in enumerate(row) if value == 5]
        if len(fives) == 2 and fives[1] > fives[0] + 1:
            for column in range(fives[0] + 1, fives[1]):
                out[row_index][column] = 3
    return out


def _at_least_two_fives(grid):
    """Rival: uses the outermost pair whenever a row has two or more 5s."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        fives = [column for column, value in enumerate(row) if value == 5]
        if len(fives) >= 2:
            for column in range(min(fives) + 1, max(fives)):
                if out[row_index][column] == 0:
                    out[row_index][column] = 3
    return out


def _any_matching_color(grid):
    """Rival: generalizes the exact-pair rule from color 5 to any nonzero color."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        by_color: dict[int, list[int]] = {}
        for column, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append(column)
        for columns in by_color.values():
            if len(columns) != 2 or columns[1] <= columns[0] + 1:
                continue
            if all(row[column] == 0 for column in range(columns[0] + 1, columns[1])):
                for column in range(columns[0] + 1, columns[1]):
                    out[row_index][column] = 3
    return out


def _one_zero_span(grid) -> bool:
    return any(
        len(fives := [column for column, value in enumerate(row) if value == 5]) == 2
        and fives[1] - fives[0] == 2
        and all(value in (0, 5) for value in row)
        for row in grid
    )


def _blocked_pair(grid) -> bool:
    return any(_classify_row(list(row))[0] in {"blocked", "blocked_wrong_color"} for row in grid)


def _three_five_row(grid) -> bool:
    return any(_classify_row(list(row))[0] == "three_fives" for row in grid)


def _wrong_color_pair(grid) -> bool:
    return any(
        _classify_row(list(row))[0] in {"wrong_color", "blocked_wrong_color"}
        for row in grid
    )


SEMANTIC_WITNESSES = {
    "one_zero_span": _one_zero_span,
    "blocked_pair": _blocked_pair,
    "three_five_row": _three_five_row,
    "wrong_color_pair": _wrong_color_pair,
}
SEMANTIC_RIVALS = {
    "needs_two_zeros": _needs_two_zeros,
    "ignore_blockers": _ignore_blockers,
    "at_least_two_fives": _at_least_two_fives,
    "any_matching_color": _any_matching_color,
}
WITNESS_RIVALS = {
    "one_zero_span": ["needs_two_zeros"],
    "blocked_pair": ["ignore_blockers"],
    "three_five_row": ["at_least_two_fives"],
    "wrong_color_pair": ["any_matching_color"],
}
CANONICAL_SHORTCUTS = {
    "ignore_blockers": _ignore_blockers,
    "at_least_two_fives": _at_least_two_fives,
    "any_matching_color": _any_matching_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when any declared alternative still fits every demo."""
    del query
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
