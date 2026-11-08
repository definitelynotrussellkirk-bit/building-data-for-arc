"""Contrastive input sampler for Fill Between Matching Endpoints.

The unchanged Racket authority fills, independently within each row, the span
between the minimum and maximum occurrence of every repeated nonzero color.
This sampler stays on an order-independent subdomain: each repeated color occurs
exactly twice and repeated-color spans within a row are disjoint.

Every ordinary draw contains two teaching counterexamples missing from the
canonical demonstrations:

* a row with two different singleton endpoint colors, refuting "fill between any
  two nonzero cells"; and
* a row with two disjoint repeated-color pairs, refuting "only rows containing
  exactly two endpoints can change".
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2038a3a66886"
TASK_ID = GENERATOR_ID
RULE_HASH = "aefdabd461d1"
VERSION = "2.1.0"
SUMMARY = (
    "Rows contain one or two disjoint same-color endpoint pairs whose interiors "
    "must be filled independently. Every sampled puzzle also includes a row "
    "with two different-color singleton endpoints, which must remain unchanged."
)

INVARIANTS = [
    "background is 0 and all non-background cells use colors 1..9",
    "each repeated color occurs exactly twice with at least one blank between endpoints",
    "a row has at most two repeated colors and their horizontal spans are disjoint",
    "ordinary draws contain at least one mismatched-endpoint decoy row",
    "ordinary draws contain at least one row with two independent endpoint pairs",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 6..12", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "canonical-weighted 9..16", "valid": "9..16"},
    "pair_rows": {"type": "int", "default": "difficulty-weighted 2..4", "valid": "2..4"},
    "double_pair_rows": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
    "decoy_rows": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
    "palette_size": {"type": "int", "default": "canonical-weighted 2..5", "valid": "2..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# (height, width, non-background palette size). Including background, these are
# the exact five canonical profile signatures used by the profile-floor gate.
_CANONICAL_PROFILES = (
    (6, 9, 2),
    (7, 10, 3),
    (7, 13, 3),
    (8, 12, 3),
    (9, 11, 3),
)


def _weighted_int(ctx, name: str, lo: int, hi: int, favored: int) -> int:
    """Draw across the full override domain while strongly favoring one value."""
    if not lo <= favored <= hi:
        raise ValueError(f"favored {name}={favored} outside [{lo}, {hi}]")
    choices = list(range(lo, hi + 1)) + [favored] * 64
    return ctx.draw_choice(name, choices)


def _difficulty_favorites(difficulty) -> tuple[int, int, int]:
    if difficulty == "easy":
        return 2, 1, 1
    if difficulty == "hard":
        return 4, 2, 2
    return 3, 1, 1


def _single_span(width: int, rng) -> tuple[int, int]:
    left = rng.randint(0, width - 3)
    right = rng.randint(left + 2, width - 1)
    return left, right


def _double_spans(width: int, rng) -> tuple[tuple[int, int], tuple[int, int]]:
    """Two disjoint endpoint spans, each with at least one interior blank."""
    cut = rng.randint(3, width - 4)
    left0 = rng.randint(0, cut - 2)
    left1 = rng.randint(left0 + 2, cut)
    right0 = rng.randint(cut + 1, width - 3)
    right1 = rng.randint(right0 + 2, width - 1)
    return (left0, left1), (right0, right1)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


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

    # A shared profile draw keeps exact canonical (h, w, palette) signatures
    # frequent, while each axis still exposes its complete documented domain.
    profile_options = list(_CANONICAL_PROFILES)
    if difficulty == "easy":
        profile_options += [_CANONICAL_PROFILES[0], _CANONICAL_PROFILES[1]] * 8
    elif difficulty == "hard":
        profile_options += [_CANONICAL_PROFILES[3], _CANONICAL_PROFILES[4]] * 8
    else:
        profile_options += list(_CANONICAL_PROFILES) * 3
    target_h, target_w, target_palette = ctx.draw_choice(
        "canonical_profile", profile_options
    )

    height = _weighted_int(ctx, "grid_h", 6, 12, target_h)
    width = _weighted_int(ctx, "grid_w", 9, 16, target_w)
    palette_size = _weighted_int(ctx, "palette_size", 2, 5, target_palette)
    favorite_pairs, favorite_double, favorite_decoys = _difficulty_favorites(difficulty)
    pair_rows = _weighted_int(ctx, "pair_rows", 2, 4, favorite_pairs)
    double_pair_rows = _weighted_int(
        ctx, "double_pair_rows", 1, 2, favorite_double
    )
    decoy_rows = _weighted_int(ctx, "decoy_rows", 1, 2, favorite_decoys)

    # The global bounds make every Cartesian override combination constructive:
    # pair_rows + decoy_rows <= 6 <= grid_h and width >= 9 fits two spans.
    grid = full_grid(height, width, 0)
    row_rng = ctx.draw_rng("row_assignment")
    chosen_rows = row_rng.sample(range(height), pair_rows + decoy_rows)
    pair_row_ids = chosen_rows[:pair_rows]
    decoy_row_ids = chosen_rows[pair_rows:]
    double_ids = set(row_rng.sample(pair_row_ids, double_pair_rows))

    palette = ctx.draw_rng("palette").sample(range(1, 10), palette_size)
    # One token per simple pair, two per double pair, and two per decoy row.
    # Cycling a shuffled palette covers every requested color and guarantees
    # adjacent two-token groups use different colors because palette_size >= 2.
    role_count = pair_rows + double_pair_rows + 2 * decoy_rows
    role_colors = [palette[index % palette_size] for index in range(role_count)]
    cursor = 0

    for row in pair_row_ids:
        rng = ctx.draw_rng(f"pair_row_{row}")
        if row in double_ids:
            color_a, color_b = role_colors[cursor], role_colors[cursor + 1]
            cursor += 2
            (a0, a1), (b0, b1) = _double_spans(width, rng)
            grid[row][a0] = grid[row][a1] = color_a
            grid[row][b0] = grid[row][b1] = color_b
        else:
            color = role_colors[cursor]
            cursor += 1
            left, right = _single_span(width, rng)
            grid[row][left] = grid[row][right] = color

    for row in decoy_row_ids:
        color_a, color_b = role_colors[cursor], role_colors[cursor + 1]
        cursor += 2
        left, right = _single_span(width, ctx.draw_rng(f"decoy_row_{row}"))
        grid[row][left] = color_a
        grid[row][right] = color_b

    return grid


def _row_contract(row: list[int]) -> tuple[list[str], int, int]:
    """Return (errors, repeated-color count, decoy flag) for one row."""
    errors: list[str] = []
    counts = Counter(value for value in row if value != 0)
    if any(count > 2 for count in counts.values()):
        errors.append("a color occurs more than twice")
    repeated = [color for color, count in counts.items() if count == 2]
    singleton = [color for color, count in counts.items() if count == 1]
    if len(repeated) > 2:
        errors.append("more than two repeated colors in one row")

    spans: list[tuple[int, int, int]] = []
    for color in repeated:
        columns = [index for index, value in enumerate(row) if value == color]
        left, right = columns
        if right - left < 2:
            errors.append(f"color {color} endpoints are adjacent")
        spans.append((left, right, color))
    spans.sort()
    for (_, previous_right, previous_color), (next_left, _, next_color) in zip(
        spans, spans[1:]
    ):
        if next_left <= previous_right:
            errors.append(
                f"color-{previous_color} and color-{next_color} spans overlap"
            )

    if repeated and singleton:
        errors.append("pair rows may not mix repeated colors with singleton colors")
    if not repeated and singleton:
        columns = [index for index, value in enumerate(row) if value != 0]
        if len(singleton) != 2 or len(columns) != 2:
            errors.append("non-pair rows must be blank or contain two singleton colors")
        elif columns[1] - columns[0] < 2:
            errors.append("singleton decoy endpoints are adjacent")
        elif row[columns[0]] == row[columns[1]]:
            errors.append("singleton decoy endpoints must have different colors")
    decoy = int(not repeated and len(singleton) == 2 and not errors)
    return errors, len(repeated), decoy


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 12:
        errors.append(f"grid_h={height} outside [6,12]")
    if not 9 <= width <= 16:
        errors.append(f"grid_w={width} outside [9,16]")
    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"cells must be integer colors 0..9; first bad cell {bad_cells[0]}")
        return errors

    pair_rows = 0
    for row_index, row in enumerate(grid):
        row_errors, repeated_count, _ = _row_contract(list(row))
        pair_rows += int(repeated_count > 0)
        errors.extend(f"row {row_index}: {message}" for message in row_errors)
    if pair_rows < 2:
        errors.append(f"expected at least two rows with repeated-color pairs, found {pair_rows}")
    palette = {value for row in grid for value in row if value != 0}
    if not 2 <= len(palette) <= 5:
        errors.append(f"non-background palette size {len(palette)} outside [2,5]")
    return errors


def strict_canonical_like(grid):
    """Lawful, unambiguous row-span instances including all canonical inputs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    pair_rows = double_pair_rows = decoy_rows = 0
    for row in grid:
        row_errors, repeated_count, decoy = _row_contract(list(row))
        if row_errors:
            raise ValueError(f"cannot observe malformed row: {row_errors}")
        pair_rows += int(repeated_count > 0)
        double_pair_rows += int(repeated_count == 2)
        decoy_rows += decoy
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "pair_rows": pair_rows,
        "double_pair_rows": double_pair_rows,
        "decoy_rows": decoy_rows,
        "palette_size": len({value for row in grid for value in row if value != 0}),
    }


def _has_mismatched_endpoints(grid) -> bool:
    return observe_overrides(grid)["decoy_rows"] > 0


def _has_two_pairs_in_one_row(grid) -> bool:
    return observe_overrides(grid)["double_pair_rows"] > 0


def _outermost_nonzero_span(grid):
    """Rival: fill between any row's outermost nonzero cells using the left color."""
    result = [list(row) for row in grid]
    for r, row in enumerate(grid):
        columns = [c for c, value in enumerate(row) if value != 0]
        if len(columns) >= 2:
            color = row[columns[0]]
            for c in range(columns[0], columns[-1] + 1):
                result[r][c] = color
    return result


def _exactly_two_endpoints_only(grid):
    """Rival: only rows with exactly two equal nonzero cells may change."""
    result = [list(row) for row in grid]
    for r, row in enumerate(grid):
        columns = [c for c, value in enumerate(row) if value != 0]
        if len(columns) == 2 and row[columns[0]] == row[columns[1]]:
            color = row[columns[0]]
            for c in range(columns[0], columns[1] + 1):
                result[r][c] = color
    return result


SEMANTIC_WITNESSES = {
    "mismatched_endpoints": _has_mismatched_endpoints,
    "multiple_pairs_one_row": _has_two_pairs_in_one_row,
}
SEMANTIC_RIVALS = {
    "outermost_nonzero_span": _outermost_nonzero_span,
    "exactly_two_endpoints_only": _exactly_two_endpoints_only,
}
WITNESS_RIVALS = {
    "mismatched_endpoints": ["outermost_nonzero_span"],
    "multiple_pairs_one_row": [
        "outermost_nonzero_span",
        "exactly_two_endpoints_only",
    ],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
