"""Generator for arc_puzzle_bank_tenth21:E70.

A zero/nonzero header row defines a per-column recoloring legend.  Nonzero
body cells beneath a nonzero header take that header color; cells beneath an
empty (zero) header are preserved.  The default distribution retains a linked
prior over all three official input archetypes, then adds controlled size,
occupancy, and empty-header passthrough variation.

Counter-hypotheses exercised by the generated lessons:
  * repeat/copy the whole header row — partial body rows remain zero;
  * use one global source-to-target recolor — one source color appears under
    multiple headers and therefore maps to different outputs;
  * infer the answer from the body marker color — one column contains multiple
    source colors that all map to its header;
  * clear every body cell under a zero header — passthrough lessons place
    nonzero cells there and the Racket oracle preserves them.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "751baf3d18b2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
# Normalized current canonical program_solution.
RULE_HASH = "56d0892cc35d"

SUMMARY = (
    "An alternating zero/nonzero top row is a column legend. Recolor each "
    "nonzero body cell under an active header to that header color; preserve "
    "zeros, the header row, and optional body cells under empty headers."
)

INVARIANTS = [
    "background is 0 and the first row alternates empty and nonzero headers",
    "active header colors are distinct and every active column has body evidence",
    "body occupancy includes a dense, one-full-row, two-full-row, or sparse profile",
    "one source color occurs under different headers and maps differently by column",
    "one active column contains multiple source colors that share one output color",
    "body cells under empty headers, when present, are preserved by the oracle",
]

HEADER_PATTERNS = ("alternating_even", "alternating_odd")
BODY_PROFILES = ("mixed_one_full", "mixed_two_full", "dense", "sparse")
EMPTY_HEADER_BODY_MODES = ("absent", "present")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "36% linked official prior; otherwise difficulty-aware 4..10",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "36% linked official prior; otherwise difficulty-aware 5..14",
        "valid": "5..14",
    },
    "header_pattern": {
        "type": "str",
        "default": "linked official prior or keyed choice",
        "valid": "|".join(HEADER_PATTERNS),
    },
    "body_profile": {
        "type": "str",
        "default": "linked official prior or keyed choice",
        "valid": "|".join(BODY_PROFILES),
    },
    "empty_header_body": {
        "type": "str",
        "default": "linked official prior is absent; generalized draws vary",
        "valid": "|".join(EMPTY_HEADER_BODY_MODES),
    },
}

# These are whole linked input profiles, not independently recombined
# marginals.  Row-count order is retained here; the semantic census treats row
# permutation as rule-irrelevant nuisance variation.
_LINKED_CANONICAL_PROFILES = (
    {
        "grid_h": 4,
        "grid_w": 7,
        "header_pattern": "alternating_even",
        "body_profile": "mixed_one_full",
        "empty_header_body": "absent",
        "active_row_counts": (4, 2, 3),
    },
    {
        "grid_h": 4,
        "grid_w": 8,
        "header_pattern": "alternating_odd",
        "body_profile": "mixed_two_full",
        "empty_header_body": "absent",
        "active_row_counts": (4, 4, 2),
    },
    {
        "grid_h": 4,
        "grid_w": 8,
        "header_pattern": "alternating_even",
        "body_profile": "dense",
        "empty_header_body": "absent",
        "active_row_counts": (4, 4, 4),
    },
)
_LINKED_PRIOR = 0.36

_BAND_H = {
    "easy": (4, 5),
    "medium": (4, 7),
    "hard": (6, 10),
    None: (4, 10),
}
_BAND_W = {
    "easy": (5, 8),
    "medium": (7, 11),
    "hard": (10, 14),
    None: (5, 14),
}
_BAND_BODY_PROFILES = {
    "easy": ("mixed_one_full", "dense", "sparse"),
    "medium": BODY_PROFILES,
    "hard": ("mixed_two_full", "dense", "sparse", "mixed_one_full"),
    None: BODY_PROFILES,
}
_BAND_EMPTY_HEADER_BODY = {
    "easy": ("absent", "absent", "present"),
    "medium": ("absent", "present"),
    "hard": ("present", "absent", "present"),
    None: ("absent", "present"),
}


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, lo, hi in (("grid_h", 4, 10), ("grid_w", 5, 14)):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{label} must be in {lo}..{hi}")
    for label, options in (
        ("header_pattern", HEADER_PATTERNS),
        ("body_profile", BODY_PROFILES),
        ("empty_header_body", EMPTY_HEADER_BODY_MODES),
    ):
        value = overrides.get(label)
        if value is not None and value not in options:
            raise ValueError(f"{label} must be one of {options}")


def _draw_int_axis(ctx, label: str, band: tuple[int, int], valid: tuple[int, int]) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *band)


def _draw_choice_axis(ctx, label: str, band_options, valid_options):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, valid_options)
    return ctx.draw_choice(label, band_options)


def _draw_axes(ctx, difficulty: str | None, overrides: dict[str, Any]):
    explicit = any(value is not None for value in overrides.values())
    prior_rng = ctx.draw_rng("linked_canonical_profile")
    if not explicit and prior_rng.random() < _LINKED_PRIOR:
        profile = dict(prior_rng.choice(_LINKED_CANONICAL_PROFILES))
        h = ctx.draw_int("grid_h", profile["grid_h"], profile["grid_h"])
        w = ctx.draw_int("grid_w", profile["grid_w"], profile["grid_w"])
        header_pattern = ctx.draw_choice(
            "header_pattern", (profile["header_pattern"],)
        )
        body_profile = ctx.draw_choice("body_profile", (profile["body_profile"],))
        empty_header_body = ctx.draw_choice(
            "empty_header_body", (profile["empty_header_body"],)
        )
        return (
            h,
            w,
            header_pattern,
            body_profile,
            empty_header_body,
            tuple(profile["active_row_counts"]),
            True,
        )

    h = _draw_int_axis(ctx, "grid_h", _BAND_H[difficulty], (4, 10))
    w = _draw_int_axis(ctx, "grid_w", _BAND_W[difficulty], (5, 14))
    header_pattern = _draw_choice_axis(
        ctx, "header_pattern", HEADER_PATTERNS, HEADER_PATTERNS
    )
    body_profile = _draw_choice_axis(
        ctx,
        "body_profile",
        _BAND_BODY_PROFILES[difficulty],
        BODY_PROFILES,
    )
    empty_header_body = _draw_choice_axis(
        ctx,
        "empty_header_body",
        _BAND_EMPTY_HEADER_BODY[difficulty],
        EMPTY_HEADER_BODY_MODES,
    )
    return h, w, header_pattern, body_profile, empty_header_body, None, False


def _active_columns(width: int, header_pattern: str) -> list[int]:
    phase = 0 if header_pattern == "alternating_even" else 1
    return list(range(phase, width, 2))


def _sparse_row_sets(active: list[int], body_rows: int, rng) -> list[set[int]]:
    """Build nonempty, non-full rows covering all active columns plus a repeat."""
    n_active = len(active)
    targets = [1] * body_rows
    required_total = max(body_rows, n_active + 1)
    while sum(targets) < required_total:
        candidates = [i for i, target in enumerate(targets) if target < n_active - 1]
        if not candidates:
            break
        targets[rng.choice(candidates)] += 1

    row_sets = [set() for _ in range(body_rows)]
    shuffled = list(active)
    rng.shuffle(shuffled)
    row_order = list(range(body_rows))
    rng.shuffle(row_order)
    for index, column in enumerate(shuffled):
        candidates = [
            row_index
            for row_index in row_order[index % body_rows :] + row_order[: index % body_rows]
            if len(row_sets[row_index]) < targets[row_index]
        ]
        if not candidates:
            candidates = [
                row_index
                for row_index in range(body_rows)
                if len(row_sets[row_index]) < n_active - 1
            ]
        row_sets[rng.choice(candidates)].add(column)

    first = active[0]
    holders = [i for i, cells in enumerate(row_sets) if first in cells]
    if len(holders) < 2:
        candidates = [
            i
            for i, cells in enumerate(row_sets)
            if first not in cells and len(cells) < targets[i]
        ]
        if not candidates:
            candidates = [
                i
                for i, cells in enumerate(row_sets)
                if first not in cells and len(cells) < n_active - 1
            ]
        row_sets[rng.choice(candidates)].add(first)

    for row_index, target in enumerate(targets):
        choices = [column for column in active if column not in row_sets[row_index]]
        rng.shuffle(choices)
        while len(row_sets[row_index]) < target:
            row_sets[row_index].add(choices.pop())
    return row_sets


def _occupancy(
    active: list[int],
    body_rows: int,
    body_profile: str,
    rng,
    exact_row_counts: tuple[int, ...] | None,
) -> list[set[int]]:
    n_active = len(active)
    if exact_row_counts is not None:
        if len(exact_row_counts) != body_rows:
            raise ValueError("linked profile row count does not match grid height")
        rows = []
        for count in exact_row_counts:
            if count == n_active:
                rows.append(set(active))
            else:
                rows.append(set(rng.sample(active, count)))
        first = active[0]
        if sum(first in cells for cells in rows) < 2:
            candidates = [
                cells for cells in rows if first not in cells and len(cells) < n_active
            ]
            cells = rng.choice(candidates)
            cells.remove(rng.choice(sorted(cells)))
            cells.add(first)
        return rows

    if body_profile == "dense":
        return [set(active) for _ in range(body_rows)]
    if body_profile == "sparse":
        return _sparse_row_sets(active, body_rows, rng)

    full_count = 1 if body_profile == "mixed_one_full" else 2
    full_rows = set(rng.sample(range(body_rows), full_count))
    rows: list[set[int]] = []
    for row_index in range(body_rows):
        if row_index in full_rows:
            rows.append(set(active))
        else:
            count = rng.randint(1, n_active - 1)
            rows.append(set(rng.sample(active, count)))

    # The first active column must occur in at least two rows so one column can
    # carry distinct source colors.  A full row already supplies one witness.
    first = active[0]
    holders = [i for i, cells in enumerate(rows) if first in cells]
    if len(holders) < 2:
        candidates = [
            i for i, cells in enumerate(rows) if first not in cells and len(cells) < n_active
        ]
        cells = rows[rng.choice(candidates)]
        if len(cells) == n_active - 1:
            cells.remove(rng.choice(sorted(cells)))
        cells.add(first)
    return rows


def _paint_body_colors(
    grid: list[list[int]],
    active: list[int],
    row_sets: list[set[int]],
    rng,
    *,
    exact_palette: bool,
) -> None:
    by_column: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_offset, columns in enumerate(row_sets, start=1):
        for column in sorted(columns):
            by_column[column].append((row_offset, column))
            legal = [color for color in range(1, 10) if color != grid[0][column]]
            grid[row_offset][column] = rng.choice(legal)

    first, second = active[:2]
    first_positions = by_column[first]
    second_positions = by_column[second]
    if len(first_positions) < 2:
        raise ValueError("occupancy failed to repeat the first active column")

    protected = {
        first_positions[0],
        first_positions[1],
        second_positions[0],
    }
    shared_options = [
        color
        for color in range(1, 10)
        if color not in {grid[0][first], grid[0][second]}
    ]
    shared = rng.choice(shared_options)
    alternate = rng.choice(
        [color for color in range(1, 10) if color not in {grid[0][first], shared}]
    )
    for row, column in (first_positions[0], second_positions[0]):
        grid[row][column] = shared
    row, column = first_positions[1]
    grid[row][column] = alternate

    if not exact_palette:
        return

    # Official inputs use every ARC color.  Keep that property in the linked
    # prior without making it a universal constraint on generalized lessons.
    current = {value for row in grid for value in row}
    missing = [color for color in range(1, 10) if color not in current]
    candidates = [
        position
        for positions in by_column.values()
        for position in positions
        if position not in protected
    ]
    rng.shuffle(candidates)
    for color in missing:
        for index, (row, column) in enumerate(candidates):
            old = grid[row][column]
            counts = sum(value == old for line in grid for value in line)
            safe_to_replace = old in grid[0] or counts > 1
            if color != grid[0][column] and safe_to_replace:
                grid[row][column] = color
                candidates.pop(index)
                break
        else:
            raise ValueError(f"could not realize canonical palette color {color}")


def _add_empty_header_body(
    grid: list[list[int]],
    inactive: list[int],
    mode: str,
    rng,
) -> None:
    if mode == "absent":
        return
    body_rows = len(grid) - 1
    count = min(max(2, body_rows // 2), body_rows * len(inactive))
    positions = [(row, column) for row in range(1, len(grid)) for column in inactive]
    for row, column in rng.sample(positions, count):
        grid[row][column] = rng.choice(range(1, 10))


def _analyze(grid) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"], {}
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"], {}
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular with nonempty rows"], {}
    height = len(grid)
    if not 4 <= height <= 10:
        errors.append(f"grid height {height} outside 4..10")
    if not 5 <= width <= 14:
        errors.append(f"grid width {width} outside 5..14")
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{column}) must be an integer ARC color 0..9"
                )
                return errors, {}

    active = [column for column, value in enumerate(grid[0]) if value != 0]
    even = list(range(0, width, 2))
    odd = list(range(1, width, 2))
    if active == even:
        header_pattern = "alternating_even"
    elif active == odd:
        header_pattern = "alternating_odd"
    else:
        header_pattern = "invalid"
        errors.append(
            "row 0 must alternate nonzero headers and zero gaps from even or odd phase"
        )
    inactive = [column for column in range(width) if column not in active]
    header_colors = [grid[0][column] for column in active]
    if len(header_colors) < 2:
        errors.append("at least two active header columns are required")
    if len(header_colors) != len(set(header_colors)):
        errors.append("active header colors must be pairwise distinct")

    active_row_counts = [
        sum(grid[row][column] != 0 for column in active)
        for row in range(1, height)
    ]
    if any(count == 0 for count in active_row_counts):
        errors.append("every body row must contain at least one active-column cell")
    active_col_values = {
        column: [
            grid[row][column]
            for row in range(1, height)
            if grid[row][column] != 0
        ]
        for column in active
    }
    missing_columns = [column for column, values in active_col_values.items() if not values]
    if missing_columns:
        errors.append(f"active header columns without body evidence: {missing_columns}")

    changed = sum(
        grid[row][column] != 0
        and grid[0][column] != 0
        and grid[row][column] != grid[0][column]
        for row in range(1, height)
        for column in active
    )
    if changed == 0:
        errors.append("no active-column body cell differs from its header; rule would be hidden")

    body_colors = {
        grid[row][column]
        for row in range(1, height)
        for column in range(width)
        if grid[row][column] != 0
    }
    if len(body_colors) < 2:
        errors.append("body must use at least two nonzero source colors")

    source_columns: dict[int, set[int]] = defaultdict(set)
    for column, values in active_col_values.items():
        for value in values:
            source_columns[value].add(column)
    if not any(len(columns) >= 2 for columns in source_columns.values()):
        errors.append("no source color is reused under two different headers")
    if not any(len(set(values)) >= 2 for values in active_col_values.values()):
        errors.append("no active column contains two distinct source colors")

    full_rows = sum(count == len(active) for count in active_row_counts)
    if active_row_counts and full_rows == len(active_row_counts):
        body_profile = "dense"
    elif full_rows == 2 and all(count > 0 for count in active_row_counts):
        body_profile = "mixed_two_full"
    elif full_rows == 1 and all(count > 0 for count in active_row_counts):
        body_profile = "mixed_one_full"
    elif full_rows == 0 and all(count > 0 for count in active_row_counts):
        body_profile = "sparse"
    else:
        body_profile = "invalid"
        errors.append("body occupancy does not match a declared profile")

    inactive_body_count = sum(
        grid[row][column] != 0
        for row in range(1, height)
        for column in inactive
    )
    empty_header_body = "present" if inactive_body_count else "absent"
    if empty_header_body == "present" and inactive_body_count < 2:
        errors.append("empty-header passthrough mode requires at least two body witnesses")

    features = {
        "grid_h": height,
        "grid_w": width,
        "header_pattern": header_pattern,
        "body_profile": body_profile,
        "empty_header_body": empty_header_body,
        "active_header_count": len(active),
        "active_row_counts": tuple(active_row_counts),
        "inactive_body_count": inactive_body_count,
        "changed_active_cells": changed,
    }
    return errors, features


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate structural grammar and reject declared override drift."""
    del difficulty
    errors, features = _analyze(grid)
    if errors:
        return errors
    requested = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        requested = nested if isinstance(nested, dict) else meta
    for name, value in requested.items():
        if name in AXES and features.get(name) != value:
            errors.append(
                f"override {name}={value!r} realized as {features.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid itself."""
    errors, features = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {
        key: features[key]
        for key in (
            "grid_h",
            "grid_w",
            "header_pattern",
            "body_profile",
            "empty_header_body",
        )
    }


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
    (
        height,
        width,
        header_pattern,
        body_profile,
        empty_header_body,
        exact_row_counts,
        linked_prior,
    ) = _draw_axes(ctx, difficulty, overrides)

    active = _active_columns(width, header_pattern)
    inactive = [column for column in range(width) if column not in active]
    grid = full_grid(height, width, 0)

    header_rng = ctx.draw_rng("header_colors")
    header_colors = header_rng.sample(range(1, 10), len(active))
    for column, color in zip(active, header_colors):
        grid[0][column] = color

    occupancy_rng = ctx.draw_rng("body_occupancy")
    row_sets = _occupancy(
        active,
        height - 1,
        body_profile,
        occupancy_rng,
        exact_row_counts,
    )
    color_rng = ctx.draw_rng("body_colors")
    _paint_body_colors(
        grid,
        active,
        row_sets,
        color_rng,
        exact_palette=linked_prior,
    )
    passthrough_rng = ctx.draw_rng("empty_header_body_cells")
    _add_empty_header_body(grid, inactive, empty_header_body, passthrough_rng)

    errors = self_check(grid, difficulty=difficulty, meta=None)
    if errors:
        raise RuntimeError("constructed invalid lesson: " + "; ".join(errors))
    return grid
