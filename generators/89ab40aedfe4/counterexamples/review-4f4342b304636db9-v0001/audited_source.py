"""Generator for ARC task 85b81ff1 / content hash 89ab40aedfe4.

The input is a row of full-height foreground carrier columns.  Each carrier is
followed by one foreground/zero bit column, and adjacent slots are separated by
one or more all-zero columns.  Sort only the bit columns by ascending foreground
population; carrier and separator columns stay fixed.  Equal populations retain
left-to-right source order.

The four-sample schedule is deliberately semantic rather than cosmetic:

* ``canonical_anchor`` reproduces the public 13x14, five-slot, spacing-three,
  high-density morphology;
* ``topmost_conflict`` makes population order disagree with first-active-row
  order;
* ``stable_tie`` gives two distinct equal-population columns whose source order
  must be preserved; and
* ``marker_only`` includes a top-marker-only column that still participates in
  the sort.

Every four consecutive demonstrations contain all four profiles, so the lesson
cannot hide the stable-tie or marker-only branches behind aggregate coverage.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "89ab40aedfe4"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4bc48cdc5789"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Full-height foreground carrier columns mark regularly spaced slots. "
    "Sort the following foreground/zero bit columns by ascending foreground "
    "population while leaving carriers and zero separators fixed; equal-count "
    "columns keep their original left-to-right order."
)

INVARIANTS = [
    "background is 0 and one nonzero foreground color fills every carrier column",
    "the top row contains runs of exactly two foreground cells, separated regularly by 1..3 zero columns",
    "the first column of every slot is foreground for the full grid height",
    "the second column of every slot contains only foreground/zero bits and is not a full carrier",
    "bit-column patterns are distinct and their population order is not already sorted",
    "every four-sample lesson window covers canonical scale, position conflict, stable ties, and a marker-only column",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 13 every fourth sample; otherwise difficulty-banded 8..16",
        "valid": "8..16",
    },
    "slot_count": {
        "type": "int",
        "default": "canonical 5 every fourth sample; otherwise difficulty-banded 3..6",
        "valid": "3..6",
    },
    "slot_spacing": {
        "type": "int",
        "default": "canonical 3 every fourth sample; otherwise difficulty-banded 3..5",
        "valid": "3..5",
    },
    "fg_color": {
        "type": "color",
        "default": "keyed draw from 1..9",
        "valid": "1..9",
    },
}

# Every boundary combination above is constructible.  Declaring the empty
# strict set prevents an arbitrary multi-axis ValueError from being mistaken
# for an intentional incompatibility by the override checker.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "topmost_conflict",
    "stable_tie",
    "marker_only",
)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _coerce_grid(grid: Any) -> list[list[int]] | None:
    if not isinstance(grid, list) or not grid:
        return None
    rows: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(ch not in "0123456789" for ch in row):
                return None
            rows.append([int(ch) for ch in row])
        elif isinstance(row, list) and row:
            rows.append(
                [
                    int(value)
                    if isinstance(value, str) and value.isdigit()
                    else value
                    for value in row
                ]
            )
        else:
            return None
    return rows


def _analysis(grid: Any) -> dict[str, Any]:
    """Parse the task grammar and return exact slot observables."""
    errors: list[str] = []
    coerced = _coerce_grid(grid)
    if coerced is None:
        return {"errors": ["grid must be a non-empty list of non-empty rows"]}
    height = len(coerced)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return {"errors": ["grid must be rectangular"], "grid": coerced}
    if not 8 <= height <= 16:
        errors.append(f"grid height must be in 8..16, got {height}")
    if not 8 <= width <= 27:
        errors.append(f"grid width must be in 8..27, got {width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {
            "errors": errors,
            "grid": coerced,
            "height": height,
            "width": width,
        }

    fg = coerced[0][0]
    if not 1 <= fg <= 9:
        errors.append("top-left foreground color must be in 1..9")
        return {
            "errors": errors,
            "grid": coerced,
            "height": height,
            "width": width,
            "fg": fg,
        }
    if any(value not in (0, fg) for row in coerced for value in row):
        errors.append("grid may use only background 0 and the top-left foreground color")

    top = coerced[0]
    runs: list[tuple[int, int]] = []
    col = 0
    while col < width:
        if top[col] == 0:
            col += 1
            continue
        start = col
        while col < width and top[col] == fg:
            col += 1
        runs.append((start, col))
    malformed_runs = [(start, end) for start, end in runs if end - start != 2]
    if malformed_runs:
        errors.append(f"top-row foreground runs must have length 2, got {malformed_runs}")
    starts = [start for start, _end in runs]
    if not 3 <= len(starts) <= 6:
        errors.append(f"expected 3..6 slots, found {len(starts)}")
    if starts and starts[0] != 0:
        errors.append("the first marker pair must begin at column 0")

    spacing = None
    if len(starts) >= 2:
        spacings = [right - left for left, right in zip(starts, starts[1:])]
        if len(set(spacings)) != 1:
            errors.append(f"slot starts must be regularly spaced, got {spacings}")
        else:
            spacing = spacings[0]
            if not 3 <= spacing <= 5:
                errors.append(f"slot spacing must be in 3..5, got {spacing}")
    if starts and starts[-1] + 2 != width:
        errors.append(
            f"grid must end after the final bit column; last start {starts[-1]}, width {width}"
        )

    slot_columns = {column for start in starts for column in (start, start + 1)}
    patterns: list[tuple[int, ...]] = []
    counts: list[int] = []
    for index, start in enumerate(starts):
        if start + 1 >= width:
            errors.append(f"slot {index} at column {start} has no bit column")
            continue
        if any(coerced[row][start] != fg for row in range(height)):
            errors.append(f"carrier column {start} is not full-height foreground")
        bit_pattern = tuple(coerced[row][start + 1] for row in range(height))
        if bit_pattern[0] != fg:
            errors.append(f"bit column {start + 1} is missing its top marker")
        if any(value not in (0, fg) for value in bit_pattern):
            errors.append(f"bit column {start + 1} contains a foreign color")
        count = sum(value == fg for value in bit_pattern)
        if count == height:
            errors.append(f"bit column {start + 1} duplicates a full carrier")
        patterns.append(bit_pattern)
        counts.append(count)

    for column in range(width):
        if column in slot_columns:
            continue
        if any(coerced[row][column] != 0 for row in range(height)):
            errors.append(f"separator column {column} is not all background")
            break

    if patterns and len(set(patterns)) != len(patterns):
        errors.append("bit-column patterns must be pairwise distinct")
    if counts and len(set(counts)) < 2:
        errors.append(f"all bit columns have the same population {counts}")
    if counts and counts == sorted(counts):
        errors.append(f"identity lesson: bit-column populations are already sorted {counts}")

    return {
        "errors": errors,
        "grid": coerced,
        "height": height,
        "width": width,
        "fg": fg,
        "starts": starts,
        "spacing": spacing,
        "patterns": tuple(patterns),
        "counts": tuple(counts),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, and rule-hiding slot scenes."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked public morphology, not independent marginals."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) != (13, 14):
        reasons.append("canonical inputs are 13x14")
    if len(analysis["starts"]) != 5:
        reasons.append("canonical inputs have five slots")
    if analysis["spacing"] != 3:
        reasons.append("canonical slot starts are three columns apart")
    counts = analysis["counts"]
    if len(set(counts)) != len(counts):
        reasons.append("canonical bit-column populations are distinct")
    if any(not 7 <= count <= 12 for count in counts):
        reasons.append(f"canonical bit-column populations lie in 7..12, got {counts}")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "slot_count": len(analysis["starts"]),
        "slot_spacing": analysis["spacing"],
        "fg_color": analysis["fg"],
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the deterministic four-slot semantic curriculum."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))


def _draw_scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    full_lo: int,
    full_hi: int,
    default: int | tuple[int, int],
) -> int:
    """Honor the full override domain while pinning ordinary schedule defaults."""
    if label in overrides:
        return ctx.draw_int(label, full_lo, full_hi)
    if isinstance(default, tuple):
        return ctx.draw_int(label, default[0], default[1])
    return ctx.draw_int(label, default, default)


def _nontrivial_permutation(values: list[int], rng) -> list[int]:
    ordered = sorted(values)
    reversed_order = list(reversed(ordered))
    for _ in range(200):
        candidate = list(values)
        rng.shuffle(candidate)
        if candidate != ordered and candidate != reversed_order:
            return candidate
    # This path is unreachable for the 3..6 element domains, but keep a loud,
    # deterministic fallback rather than returning an identity episode.
    candidate = ordered[1:] + ordered[:1]
    if candidate == reversed_order:
        candidate = ordered[2:] + ordered[:2]
    return candidate


def _counts_for_profile(profile: str, height: int, slot_count: int, rng) -> list[int]:
    if profile == "canonical_anchor":
        low = max(2, height - slot_count - 1)
        population = list(range(low, height))
        if len(population) < slot_count:
            population = list(range(2, height))
        return _nontrivial_permutation(rng.sample(population, slot_count), rng)

    if profile == "topmost_conflict":
        return _nontrivial_permutation(list(range(2, slot_count + 2)), rng)

    if profile == "stable_tie":
        tie_count = min(4, height - 2)
        others = [count for count in range(2, height) if count != tie_count]
        values = [tie_count, tie_count] + rng.sample(others, slot_count - 2)
        for _ in range(200):
            rng.shuffle(values)
            if values != sorted(values):
                return values
        return values[1:] + values[:1]

    if profile == "marker_only":
        others = rng.sample(list(range(2, height)), slot_count - 1)
        rng.shuffle(others)
        insertion = max(1, min(slot_count - 1, slot_count // 2))
        values = list(others)
        values.insert(insertion, 1)
        if values == sorted(values):
            values = values[1:] + values[:1]
        return values

    raise AssertionError(f"unsupported schedule profile {profile!r}")


def _pattern_with_count(
    height: int,
    count: int,
    rng,
    used: set[tuple[int, ...]],
    *,
    first_body_row: int | None = None,
) -> tuple[int, ...]:
    if not 1 <= count < height:
        raise ValueError(f"bit-column count {count} outside 1..{height - 1}")
    for _ in range(400):
        body_count = count - 1
        if body_count == 0:
            body_rows: list[int] = []
        elif first_body_row is None:
            body_rows = rng.sample(list(range(1, height)), body_count)
        else:
            if not 1 <= first_body_row < height:
                raise ValueError(f"invalid first body row {first_body_row}")
            tail = list(range(first_body_row + 1, height))
            if body_count - 1 > len(tail):
                raise ValueError(
                    f"count {count} cannot start at row {first_body_row} in height {height}"
                )
            body_rows = [first_body_row]
            if body_count > 1:
                body_rows.extend(rng.sample(tail, body_count - 1))
        occupied = {0, *body_rows}
        pattern = tuple(1 if row in occupied else 0 for row in range(height))
        if pattern not in used:
            used.add(pattern)
            return pattern
    raise ValueError(f"could not draw a distinct count-{count} bit column")


def _patterns_for_profile(
    profile: str,
    height: int,
    counts: list[int],
    rng,
) -> list[tuple[int, ...]]:
    used: set[tuple[int, ...]] = set()
    patterns: list[tuple[int, ...]] = []
    sorted_counts = sorted(set(counts))
    for count in counts:
        first_body_row = None
        if profile == "topmost_conflict":
            rank = sorted_counts.index(count)
            # Smaller populations start later; first-active-row sorting therefore
            # reverses the population rank while remaining fully constructive.
            first_body_row = len(sorted_counts) - rank
        patterns.append(
            _pattern_with_count(
                height,
                count,
                rng,
                used,
                first_body_row=first_body_row,
            )
        )
    return patterns


def _build_grid(
    height: int,
    slot_count: int,
    spacing: int,
    fg: int,
    patterns: list[tuple[int, ...]],
) -> list[list[int]]:
    starts = [index * spacing for index in range(slot_count)]
    width = starts[-1] + 2
    grid = full_grid(height, width, 0)
    for start, pattern in zip(starts, patterns):
        for row in range(height):
            grid[row][start] = fg
            grid[row][start + 1] = fg if pattern[row] else 0
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    if profile == "canonical_anchor":
        height_default: int | tuple[int, int] = 13
        slot_default: int | tuple[int, int] = 5
        spacing_default: int | tuple[int, int] = 3
    else:
        height_default = {
            "easy": (8, 10),
            "medium": (10, 13),
            "hard": (13, 16),
        }[band]
        slot_default = {
            "easy": (3, 4),
            "medium": (4, 5),
            "hard": (5, 6),
        }[band]
        spacing_default = {
            "easy": (3, 4),
            "medium": (3, 4),
            "hard": (4, 5),
        }[band]

    height = _draw_scheduled_int(ctx, overrides, "grid_h", 8, 16, height_default)
    slot_count = _draw_scheduled_int(ctx, overrides, "slot_count", 3, 6, slot_default)
    spacing = _draw_scheduled_int(ctx, overrides, "slot_spacing", 3, 5, spacing_default)
    fg = ctx.draw_color("fg_color", exclude=(0,))
    rng = ctx.draw_rng("layout")

    counts = _counts_for_profile(profile, height, slot_count, rng)
    patterns = _patterns_for_profile(profile, height, counts, rng)
    grid = _build_grid(height, slot_count, spacing, fg, patterns)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    requested = ctx.recorded_draws()
    observed = observe_overrides(grid)
    for axis in AXES:
        if requested.get(axis) != observed.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )

    official = rule_mirror(grid)
    if official == grid:
        raise AssertionError("ordinary generation produced an identity transformation")
    if profile == "topmost_conflict" and _rival_topmost_first(grid) == official:
        raise AssertionError("topmost-conflict profile failed to refute its rival")
    if profile == "stable_tie" and _rival_reverse_equal_ties(grid) == official:
        raise AssertionError("stable-tie profile failed to refute reverse tie order")
    if profile == "marker_only" and _rival_keep_marker_only_fixed(grid) == official:
        raise AssertionError("marker-only profile failed to refute fixed empty slots")
    return grid


def _copy_in_order(grid: Any, source_order: list[int]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    source = analysis["grid"]
    output = copy.deepcopy(source)
    starts = analysis["starts"]
    if sorted(source_order) != list(range(len(starts))):
        raise ValueError(f"invalid source order {source_order}")
    for destination_index, source_index in enumerate(source_order):
        destination_column = starts[destination_index] + 1
        source_column = starts[source_index] + 1
        for row in range(analysis["height"]):
            output[row][destination_column] = source[row][source_column]
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror; the selected Racket rule remains authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    order = sorted(range(len(analysis["starts"])), key=lambda index: (analysis["counts"][index], index))
    return _copy_in_order(analysis["grid"], order)


def _rival_identity(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["grid"])


def _rival_descending_population(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    order = sorted(range(len(analysis["starts"])), key=lambda index: (-analysis["counts"][index], index))
    return _copy_in_order(analysis["grid"], order)


def _rival_topmost_first(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    source = analysis["grid"]
    fg = analysis["fg"]

    def first_body(index: int) -> int:
        column = analysis["starts"][index] + 1
        return next(
            (row for row in range(1, analysis["height"]) if source[row][column] == fg),
            analysis["height"],
        )

    order = sorted(range(len(analysis["starts"])), key=lambda index: (first_body(index), index))
    return _copy_in_order(source, order)


def _rival_reverse_equal_ties(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    order = sorted(range(len(analysis["starts"])), key=lambda index: (analysis["counts"][index], -index))
    return _copy_in_order(analysis["grid"], order)


def _rival_keep_marker_only_fixed(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    order = list(range(len(analysis["starts"])))
    movable_destinations = [index for index, count in enumerate(analysis["counts"]) if count > 1]
    movable_sources = sorted(
        movable_destinations,
        key=lambda index: (analysis["counts"][index], index),
    )
    for destination, source in zip(movable_destinations, movable_sources):
        order[destination] = source
    return _copy_in_order(analysis["grid"], order)


def _witness_nonidentity(grid: Any) -> bool:
    return rule_mirror(grid) != _rival_identity(grid)


def _witness_topmost_conflict(grid: Any) -> bool:
    return rule_mirror(grid) != _rival_topmost_first(grid)


def _witness_stable_tie(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and len(set(analysis["counts"])) < len(analysis["counts"])
        and rule_mirror(grid) != _rival_reverse_equal_ties(grid)
    )


def _witness_marker_only(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and 1 in analysis["counts"]
        and rule_mirror(grid) != _rival_keep_marker_only_fixed(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "population_sort_changes_layout": _witness_nonidentity,
    "population_not_first_active_row": _witness_topmost_conflict,
    "equal_counts_keep_source_order": _witness_stable_tie,
    "marker_only_column_participates": _witness_marker_only,
}

SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "descending_population": _rival_descending_population,
    "first_active_row": _rival_topmost_first,
    "reverse_equal_population_ties": _rival_reverse_equal_ties,
    "keep_marker_only_columns_fixed": _rival_keep_marker_only_fixed,
}

WITNESS_RIVALS = {
    "population_sort_changes_layout": ["identity", "descending_population"],
    "population_not_first_active_row": ["first_active_row"],
    "equal_counts_keep_source_order": ["reverse_equal_population_ties"],
    "marker_only_column_participates": ["keep_marker_only_columns_fixed"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Neither shortcut can be falsified by the public examples: canonical counts
# are all unique and every bit column contains at least one body cell.
CANONICAL_SHORTCUTS = {
    "reverse_equal_population_ties": _rival_reverse_equal_ties,
    "keep_marker_only_columns_fixed": _rival_keep_marker_only_fixed,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
    return reasons


def mutation_fixtures():
    """Named malformed/rule-hiding grids the structural checker must reject."""
    fixtures: list[tuple[str, list[list[int]]]] = []
    fixtures.append(("all_background", full_grid(8, 8, 0)))

    broken_carrier = generate(9101, 0, difficulty="easy")
    broken_carrier[1][0] = 0
    fixtures.append(("broken_full_height_carrier", broken_carrier))

    separator_noise = generate(9102, 1, difficulty="medium")
    facts = _analysis(separator_noise)
    separator_noise[1][facts["starts"][0] + 2] = facts["fg"]
    fixtures.append(("nonzero_separator_column", separator_noise))

    malformed_pair = generate(9103, 2, difficulty="hard")
    facts = _analysis(malformed_pair)
    malformed_pair[0][facts["starts"][1] + 1] = 0
    fixtures.append(("broken_top_marker_pair", malformed_pair))

    sorted_identity = rule_mirror(generate(9104, 3, difficulty="easy"))
    fixtures.append(("already_sorted_identity", sorted_identity))

    duplicate_pattern = generate(9105, 0, difficulty="medium")
    facts = _analysis(duplicate_pattern)
    source_column = facts["starts"][0] + 1
    destination_column = facts["starts"][1] + 1
    for row in range(facts["height"]):
        duplicate_pattern[row][destination_column] = duplicate_pattern[row][source_column]
    fixtures.append(("duplicate_bit_column", duplicate_pattern))

    foreign_color = generate(9106, 1, difficulty="hard")
    facts = _analysis(foreign_color)
    column = facts["starts"][0] + 1
    row = next(row for row in range(1, facts["height"]) if foreign_color[row][column] == facts["fg"])
    foreign_color[row][column] = 1 if facts["fg"] != 1 else 2
    fixtures.append(("foreign_color_in_bit_column", foreign_color))
    return fixtures
