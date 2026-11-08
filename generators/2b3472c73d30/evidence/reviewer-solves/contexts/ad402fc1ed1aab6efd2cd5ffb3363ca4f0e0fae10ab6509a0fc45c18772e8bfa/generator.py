"""Semantic generator for ARC task 2b3472c73d30.

For each row and each nonzero color appearing exactly twice, fill the inclusive
horizontal interval when every cell strictly between the endpoints is black.
All other cells remain unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2b3472c73d30"
VERSION = "3.0.0"
TASK_ID = "2b3472c73d30"
RULE_HASH = "9f6d9dc4a68d"
SUMMARY = (
    "Fill the blank horizontal interval between the two occurrences of each "
    "nonzero row-local color; preserve colors with any other count or with a "
    "nonzero blocker between their two occurrences."
)
EXAMPLES_NEEDED = 3
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized (3:7)",
        "valid": "linked|generalized",
        "doc": (
            "linked preserves one complete public row/span relation under "
            "legal row, reflection, and color transforms; generalized varies "
            "positive bridges and exact-count/blocker near misses"
        ),
    },
}
INVARIANTS = [
    "input and output have identical dimensions",
    "all original nonzero cells are preserved",
    "at least two row-local endpoint pairs have a visible blank interval",
    "only blank cells inside eligible same-color intervals are changed",
    "blocked, adjacent, singleton, and three-plus occurrences remain unchanged",
]

BACKGROUND = 0
COLORS = tuple(range(1, 10))
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
GENERAL_PROFILES = (
    "plain",
    "multirow",
    "multi_color_row",
    "blocked",
    "count_decoys",
    "shared_color_rows",
    "mixed",
)

# Input-only descriptors for the two train examples and held-out example.
# Each span is (left_endpoint, right_endpoint); active row order and colors
# may be permuted, and every descriptor may be reflected left-right.
PUBLIC_PROFILES = (
    ("public_train_1", 7, 9, ((0, 2), (1, 5), (3, 7))),
    ("public_train_2", 6, 10, ((1, 4), (2, 6), (5, 8))),
    ("public_test_1", 7, 10, ((0, 3), (1, 6), (4, 8))),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _span_signature(width, spans):
    direct = tuple(sorted(spans))
    reflected = tuple(
        sorted((width - 1 - right, width - 1 - left) for left, right in spans)
    )
    return min(direct, reflected)


_PUBLIC_SIGNATURE_TO_PROFILE = {
    (height, width, _span_signature(width, spans)): profile
    for profile, height, width, spans in PUBLIC_PROFILES
}


def _public_signature(grid):
    height = len(grid)
    width = len(grid[0])
    spans = []
    colors = []
    for row in grid:
        nonzero = [(col, value) for col, value in enumerate(row) if value]
        if not nonzero:
            continue
        if (
            len(nonzero) != 2
            or nonzero[0][1] != nonzero[1][1]
            or nonzero[1][0] - nonzero[0][0] < 2
        ):
            return None
        spans.append((nonzero[0][0], nonzero[1][0]))
        colors.append(nonzero[0][1])
    if len(spans) != 3 or len(set(colors)) != 3:
        return None
    return height, width, _span_signature(width, spans)


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular matrix"], "facts": None}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {"errors": ["grid must be rectangular and nonempty"], "facts": None}
    height = len(grid)
    width = next(iter(widths))
    if not (5 <= height <= 30 and 7 <= width <= 30):
        errors.append("grid must be 5..30 rows by 7..30 columns")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cell values must be integer ARC colors 0..9")
        return {"errors": errors, "facts": None}

    output = _copy_grid(grid)
    eligible = []
    blocked = []
    adjacent = []
    singleton = []
    repeated = []
    row_eligible_counts = []
    changed_cells = []
    eligible_colors_by_row = []
    for row_index, row in enumerate(grid):
        row_colors = []
        for value in row:
            if value and value not in row_colors:
                row_colors.append(value)
        row_eligible = []
        for color in row_colors:
            columns = [col for col, value in enumerate(row) if value == color]
            if len(columns) == 1:
                singleton.append((row_index, color, tuple(columns)))
            elif len(columns) == 2:
                left, right = columns
                if any(row[col] != BACKGROUND for col in range(left + 1, right)):
                    blocked.append((row_index, color, left, right))
                elif right - left == 1:
                    adjacent.append((row_index, color, left, right))
                else:
                    eligible.append((row_index, color, left, right))
                    row_eligible.append(color)
                    for col in range(left, right + 1):
                        output[row_index][col] = color
                    changed_cells.extend(
                        (row_index, col) for col in range(left + 1, right)
                    )
            else:
                repeated.append((row_index, color, tuple(columns)))
        row_eligible_counts.append(len(row_eligible))
        eligible_colors_by_row.append(tuple(row_eligible))

    if len(eligible) < 2:
        errors.append("need at least two visible eligible endpoint pairs")
    if len(changed_cells) < 2:
        errors.append("need at least two newly filled bridge cells")
    occupied = sum(value != BACKGROUND for row in grid for value in row)
    if occupied > 0.45 * height * width:
        errors.append("nonzero occupancy must leave substantial black context")

    signature = _public_signature(grid)
    linked_profile = _PUBLIC_SIGNATURE_TO_PROFILE.get(signature)
    family = "linked" if linked_profile else "generalized"
    has_count_decoy = bool(adjacent or repeated)
    eligible_color_rows = {}
    for row_index, colors in enumerate(eligible_colors_by_row):
        for color in colors:
            eligible_color_rows.setdefault(color, []).append(row_index)
    shared_color = any(len(rows) >= 2 for rows in eligible_color_rows.values())
    if blocked and has_count_decoy:
        generalized_profile = "mixed"
    elif any(count >= 2 for count in row_eligible_counts):
        generalized_profile = "multi_color_row"
    elif blocked:
        generalized_profile = "blocked"
    elif has_count_decoy:
        generalized_profile = "count_decoys"
    elif shared_color:
        generalized_profile = "shared_color_rows"
    elif len(eligible) >= 5:
        generalized_profile = "multirow"
    else:
        generalized_profile = "plain"

    facts = {
        "height": height,
        "width": width,
        "output": output,
        "eligible": tuple(eligible),
        "blocked": tuple(blocked),
        "adjacent": tuple(adjacent),
        "singleton": tuple(singleton),
        "repeated": tuple(repeated),
        "eligible_count": len(eligible),
        "blocked_count": len(blocked),
        "adjacent_count": len(adjacent),
        "singleton_count": len(singleton),
        "repeated_count": len(repeated),
        "changed_cells": tuple(changed_cells),
        "changed_count": len(changed_cells),
        "occupied_count": occupied,
        "density": occupied / (height * width),
        "family": family,
        "linked_profile": linked_profile,
        "generalized_profile": generalized_profile,
        "row_eligible_counts": tuple(row_eligible_counts),
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["family"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["family"]}


def _build_linked(rng):
    profile, height, width, raw_spans = rng.choice(PUBLIC_PROFILES)
    spans = list(raw_spans)
    if rng.random() < 0.5:
        spans = [
            (width - 1 - right, width - 1 - left)
            for left, right in spans
        ]
    rng.shuffle(spans)
    rows = rng.sample(range(height), len(spans))
    colors = rng.sample(COLORS, len(spans))
    grid = full_grid(height, width, BACKGROUND)
    for row, (left, right), color in zip(rows, spans, colors):
        grid[row][left] = color
        grid[row][right] = color
    analysis = _analyze(grid)
    if (
        analysis["errors"]
        or analysis["facts"]["linked_profile"] != profile
    ):
        raise RuntimeError("linked profile construction drift")
    return grid


def _shape_for_band(rng, band):
    ranges = {
        "easy": ((6, 8), (9, 12)),
        "medium": ((9, 13), (12, 16)),
        "hard": ((14, 18), (16, 21)),
    }
    (height_low, height_high), (width_low, width_high) = ranges[band]
    return rng.randint(height_low, height_high), rng.randint(width_low, width_high)


def _place_positive(grid, row, color, rng):
    width = len(grid[0])
    left = rng.randint(0, width - 4)
    right = rng.randint(left + 2, width - 1)
    grid[row][left] = color
    grid[row][right] = color


def _place_two_positive(grid, row, first_color, second_color, rng):
    width = len(grid[0])
    split = width // 2
    first_left = rng.randint(0, max(0, split - 3))
    first_right = rng.randint(first_left + 2, split - 1)
    second_left = rng.randint(split, width - 3)
    second_right = rng.randint(second_left + 2, width - 1)
    grid[row][first_left] = first_color
    grid[row][first_right] = first_color
    grid[row][second_left] = second_color
    grid[row][second_right] = second_color


def _place_blocked(grid, row, pair_color, blocker_color, rng):
    width = len(grid[0])
    left = rng.randint(0, width - 5)
    right = rng.randint(left + 4, width - 1)
    blocker_col = rng.randint(left + 1, right - 1)
    grid[row][left] = pair_color
    grid[row][right] = pair_color
    grid[row][blocker_col] = blocker_color


def _place_triple(grid, row, color, rng):
    for col in rng.sample(range(len(grid[0])), 3):
        grid[row][col] = color


def _place_adjacent(grid, row, color, rng):
    left = rng.randrange(len(grid[0]) - 1)
    grid[row][left] = color
    grid[row][left + 1] = color


def _build_generalized(rng, band):
    for _ in range(100):
        profile = rng.choice(GENERAL_PROFILES)
        height, width = _shape_for_band(rng, band)
        grid = full_grid(height, width, BACKGROUND)
        rows = list(range(height))
        rng.shuffle(rows)
        colors = list(COLORS)
        rng.shuffle(colors)

        if profile == "multirow":
            for index in range(5):
                _place_positive(
                    grid, rows[index], colors[index % len(colors)], rng
                )
        elif profile == "multi_color_row":
            _place_two_positive(
                grid, rows[0], colors[0], colors[1], rng
            )
            _place_positive(grid, rows[1], colors[2], rng)
        elif profile == "blocked":
            _place_positive(grid, rows[0], colors[0], rng)
            _place_positive(grid, rows[1], colors[1], rng)
            _place_blocked(grid, rows[2], colors[2], colors[3], rng)
        elif profile == "count_decoys":
            _place_positive(grid, rows[0], colors[0], rng)
            _place_positive(grid, rows[1], colors[1], rng)
            _place_triple(grid, rows[2], colors[2], rng)
            _place_adjacent(grid, rows[3], colors[3], rng)
        elif profile == "shared_color_rows":
            _place_positive(grid, rows[0], colors[0], rng)
            _place_positive(grid, rows[1], colors[0], rng)
            _place_positive(grid, rows[2], colors[1], rng)
        elif profile == "mixed":
            _place_positive(grid, rows[0], colors[0], rng)
            _place_positive(grid, rows[1], colors[1], rng)
            _place_blocked(grid, rows[2], colors[2], colors[3], rng)
            _place_triple(grid, rows[3], colors[4], rng)
        else:
            for index in range(3):
                _place_positive(grid, rows[index], colors[index], rng)

        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["family"] == "generalized"
            and analysis["facts"]["generalized_profile"] == profile
        ):
            return grid
    raise RuntimeError("could not realize generalized row-bridge scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family",
        (
            "linked",
            "linked",
            "linked",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
        ),
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['family']}"
                ]
            )
        )
    return grid
