"""Generator for ARC task ``823621e5aa1f`` (original slug ``332202d5``).

The input contains one vertical marker column: marker value 1 identifies a
horizontal colored stripe and marker value 8 identifies an orange background
row.  The output replaces each stripe row by blue (1), expands the nearest
stripe colors through the intervening rows, and inserts a blue separator at
the exact middle of an odd-sized gap when the two bounding stripe colors
differ.  The marker column becomes 8 on stripe rows and 1 elsewhere.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "823621e5aa1f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c6a5c373c678"

SUMMARY = (
    "Find the unique vertical column made only of colors 1 and 8. Rows where "
    "that column is 1 are full horizontal color stripes; rows where it is 8 "
    "are orange background. Replace stripe rows by color 1 with an 8 in the "
    "marker column. Before the first and after the last stripe, extend the "
    "nearest stripe color. Between stripes of the same color, keep that color. "
    "Between different colors, split an even-sized gap evenly; for an odd-sized "
    "gap, place color 1 on the middle row and use the upper/lower stripe colors "
    "on the two sides. All non-stripe marker cells become color 1."
)

INVARIANTS = [
    "the grid is rectangular, 16..22 rows by 8..22 columns",
    "exactly one column contains only colors 1 and 8",
    "the marker column is 1 exactly on horizontal stripe rows and 8 otherwise",
    "every non-marker row is uniformly orange 7 or uniformly one stripe color",
    "there are 2..5 interior stripe rows separated by at least one background row",
    "stripe colors avoid 1, 7, and 8 and at least two distinct stripe colors occur",
    "ordinary lessons include odd-different, odd-same, and even-different gaps",
    "the Racket oracle remains the sole output authority",
]

AXES = {
    "height": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-scaled",
        "valid": "16..22",
    },
    "width": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-scaled",
        "valid": "8..22",
    },
    "marker_side": {
        "type": "str",
        "default": "center on canonical anchors; varied on generalization draws",
        "valid": "left|center|right",
    },
    "stripe_count": {
        "type": "int",
        "default": "4 on canonical anchors; 5 on generalization draws",
        "valid": "2..5",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.60
_PROFILE_NAMES = (
    "canonical_anchor_a",
    "canonical_anchor_b",
    "canonical_anchor_c",
    "generalized_scale",
)
SCHEDULE_PROFILES = _PROFILE_NAMES

_ALLOWED_STRIPE_COLORS = (0, 2, 3, 4, 5, 6, 9)
_REL_ODD_DIFFERENT = "odd_different"
_REL_ODD_SAME = "odd_same"
_REL_EVEN_DIFFERENT = "even_different"


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive draws contain three exact canonical-scale anchors."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}"
        )


def _scheduled_int(ctx, overrides, label, default, lo, hi):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, overrides, label, default, options):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _profile_defaults(sample_index, difficulty):
    profile = schedule_profile(0, sample_index, difficulty)
    if profile != "generalized_scale":
        return 16, 16, "center", 4
    return {
        "easy": (16, 12, "left", 5),
        "medium": (19, 18, "right", 5),
        "hard": (22, 22, "left", 5),
    }.get(difficulty, (18, 17, "right", 5))


def _marker_column(width, marker_side):
    if marker_side == "left":
        return 0
    if marker_side == "right":
        return width - 1
    return width // 2


def _relation_template(stripe_count, rng):
    """Return per-gap semantic relations; ordinary count>=4 covers all branches."""
    if stripe_count == 2:
        return [_REL_ODD_DIFFERENT]
    if stripe_count == 3:
        relations = [_REL_ODD_DIFFERENT, _REL_ODD_SAME]
        rng.shuffle(relations)
        return relations
    relations = [
        _REL_ODD_DIFFERENT,
        _REL_ODD_SAME,
        _REL_EVEN_DIFFERENT,
    ]
    rng.shuffle(relations)
    while len(relations) < stripe_count - 1:
        relations.append(
            rng.choice((_REL_ODD_DIFFERENT, _REL_EVEN_DIFFERENT))
        )
    return relations


def _gap_sizes(height, stripe_count, relations, rng):
    minimum = [2 if rel == _REL_EVEN_DIFFERENT else 1 for rel in relations]
    max_gap_total = height - stripe_count - 2  # one row before and after
    if sum(minimum) > max_gap_total:
        raise ValueError(
            f"height {height} cannot hold {stripe_count} separated stripes"
        )

    gaps = minimum[:]
    spare = max_gap_total - sum(gaps)
    # Preserve each decisive parity while varying gap magnitudes.
    parity_slots = list(range(min(3, len(gaps))))
    rng.shuffle(parity_slots)
    for slot in parity_slots:
        if spare >= 2 and rng.choice((False, True)):
            gaps[slot] += 2
            spare -= 2
    # Extra relations may absorb arbitrary even increments as well.
    extra_slots = list(range(3, len(gaps)))
    rng.shuffle(extra_slots)
    for slot in extra_slots:
        if spare >= 2 and rng.choice((False, True)):
            gaps[slot] += 2
            spare -= 2

    before = rng.randint(1, spare + 1)
    after = spare + 2 - before
    rows = [before]
    for gap in gaps:
        rows.append(rows[-1] + gap + 1)
    assert rows[-1] == height - after - 1
    return rows


def _stripe_colors(stripe_count, relations, rng):
    pool = list(_ALLOWED_STRIPE_COLORS)
    rng.shuffle(pool)
    colors = [pool.pop()]
    for relation in relations:
        if relation == _REL_ODD_SAME:
            colors.append(colors[-1])
        else:
            choices = [color for color in pool if color != colors[-1]]
            if not choices:
                choices = [
                    color
                    for color in _ALLOWED_STRIPE_COLORS
                    if color != colors[-1]
                ]
            chosen = rng.choice(choices)
            colors.append(chosen)
            if chosen in pool:
                pool.remove(chosen)
    if len(set(colors)) < 2:
        raise RuntimeError("failed to construct at least two stripe colors")
    return colors


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and len(value) == 1 and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _rectangular_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple, str)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple, str)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    return []


def _analyze(grid):
    errors = _rectangular_errors(grid)
    if errors:
        return None, errors
    grid = _coerce_grid(grid)
    height, width = len(grid), len(grid[0])
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["every cell must be an integer ARC color 0..9"]

    marker_columns = [
        col
        for col in range(width)
        if all(grid[row][col] in (1, 8) for row in range(height))
    ]
    if len(marker_columns) != 1:
        return None, [
            f"expected exactly one all-1/8 marker column, found {len(marker_columns)}"
        ]
    marker_col = marker_columns[0]
    stripe_rows = []
    stripe_colors = []
    for row in range(height):
        outside = [grid[row][col] for col in range(width) if col != marker_col]
        if len(set(outside)) != 1:
            errors.append(f"row {row} is not uniform outside the marker column")
            continue
        fill = outside[0]
        marker = grid[row][marker_col]
        if marker == 8:
            if fill != 7:
                errors.append(
                    f"background row {row} has fill {fill}; expected orange 7"
                )
        elif marker == 1:
            if fill in (1, 7, 8):
                errors.append(
                    f"stripe row {row} has illegal stripe color {fill}"
                )
            else:
                stripe_rows.append(row)
                stripe_colors.append(fill)
        else:
            errors.append(f"marker at row {row} must be 1 or 8")
    analysis = {
        "grid": grid,
        "height": height,
        "width": width,
        "marker_col": marker_col,
        "stripe_rows": stripe_rows,
        "stripe_colors": stripe_colors,
    }
    return analysis, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed scenes and task-hiding impostors."""
    del difficulty, meta
    analysis, errors = _analyze(grid)
    if analysis is None:
        return errors
    height = analysis["height"]
    width = analysis["width"]
    rows = analysis["stripe_rows"]
    colors = analysis["stripe_colors"]

    if not 16 <= height <= 22:
        errors.append(f"height {height} outside 16..22")
    if not 8 <= width <= 22:
        errors.append(f"width {width} outside 8..22")
    if not 2 <= len(rows) <= 5:
        errors.append(f"expected 2..5 stripe rows, found {len(rows)}")
    if rows:
        if rows[0] == 0 or rows[-1] == height - 1:
            errors.append("stripe rows must be interior, leaving exterior regions")
        if any(b - a < 2 for a, b in zip(rows, rows[1:])):
            errors.append("adjacent stripe rows are not allowed")
    if colors and len(set(colors)) < 2:
        errors.append("at least two distinct stripe colors are required")
    return errors


def strict_canonical_like(grid):
    """Empirical public manifold: exact 16x16 scale and 2..4 stripes."""
    reasons = list(self_check(grid))
    analysis, analysis_errors = _analyze(grid)
    if analysis is None:
        return reasons or analysis_errors
    if analysis["height"] != 16 or analysis["width"] != 16:
        reasons.append(
            f"canonical dimensions are 16x16, found {analysis['height']}x{analysis['width']}"
        )
    if not 2 <= len(analysis["stripe_rows"]) <= 4:
        reasons.append(
            f"canonical stripe count is 2..4, found {len(analysis['stripe_rows'])}"
        )
    palette_size = len({value for row in analysis["grid"] for value in row})
    if palette_size not in (5, 6):
        reasons.append(f"canonical palette size is 5 or 6, found {palette_size}")
    if analysis["marker_col"] in (0, analysis["width"] - 1):
        reasons.append("canonical marker column is interior")
    return reasons


def _side_from_column(width, col):
    if col == 0:
        return "left"
    if col == width - 1:
        return "right"
    if col == width // 2:
        return "center"
    return "other"


def observe_overrides(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        return {}
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "marker_side": _side_from_column(
            analysis["width"], analysis["marker_col"]
        ),
        "stripe_count": len(analysis["stripe_rows"]),
    }


def _official_output(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        raise ValueError(f"invalid task grid: {errors}")
    height = analysis["height"]
    width = analysis["width"]
    marker_col = analysis["marker_col"]
    stripes = list(zip(analysis["stripe_rows"], analysis["stripe_colors"]))
    output = full_grid(height, width, 1)
    stripe_lookup = dict(stripes)
    for row in range(height):
        if row in stripe_lookup:
            fill = 1
            marker = 8
        else:
            above = [item for item in stripes if item[0] < row]
            below = [item for item in stripes if item[0] > row]
            if not above:
                fill = below[0][1]
            elif not below:
                fill = above[-1][1]
            else:
                upper_row, upper_color = above[-1]
                lower_row, lower_color = below[0]
                gap = lower_row - upper_row - 1
                pos = row - upper_row - 1
                if upper_color == lower_color:
                    fill = upper_color
                elif gap % 2 == 0:
                    fill = upper_color if pos < gap // 2 else lower_color
                else:
                    middle = gap // 2
                    fill = (
                        upper_color
                        if pos < middle
                        else 1
                        if pos == middle
                        else lower_color
                    )
            marker = 1
        for col in range(width):
            output[row][col] = marker if col == marker_col else fill
    return output


def rule_mirror(grid):
    """Independent test mirror; canonical Racket remains authoritative."""
    return _official_output(grid)


def _rival_nearest_without_separator(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        raise ValueError(errors)
    out = _official_output(grid)
    marker_col = analysis["marker_col"]
    stripes = list(zip(analysis["stripe_rows"], analysis["stripe_colors"]))
    for (upper_row, upper_color), (lower_row, lower_color) in zip(
        stripes, stripes[1:]
    ):
        gap = lower_row - upper_row - 1
        if upper_color != lower_color and gap % 2 == 1:
            middle_row = upper_row + 1 + gap // 2
            for col in range(analysis["width"]):
                out[middle_row][col] = 1 if col == marker_col else upper_color
    return out


def _rival_separator_for_same_odd_gap(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        raise ValueError(errors)
    out = _official_output(grid)
    marker_col = analysis["marker_col"]
    stripes = list(zip(analysis["stripe_rows"], analysis["stripe_colors"]))
    for (upper_row, upper_color), (lower_row, lower_color) in zip(
        stripes, stripes[1:]
    ):
        gap = lower_row - upper_row - 1
        if upper_color == lower_color and gap % 2 == 1:
            middle_row = upper_row + 1 + gap // 2
            for col in range(analysis["width"]):
                out[middle_row][col] = 1
            out[middle_row][marker_col] = 1
    return out


def _rival_upper_color_across_even_gap(grid):
    analysis, errors = _analyze(grid)
    if analysis is None or errors:
        raise ValueError(errors)
    out = _official_output(grid)
    marker_col = analysis["marker_col"]
    stripes = list(zip(analysis["stripe_rows"], analysis["stripe_colors"]))
    for (upper_row, upper_color), (lower_row, lower_color) in zip(
        stripes, stripes[1:]
    ):
        gap = lower_row - upper_row - 1
        if upper_color != lower_color and gap % 2 == 0:
            for row in range(upper_row + 1, lower_row):
                for col in range(analysis["width"]):
                    out[row][col] = 1 if col == marker_col else upper_color
    return out


SEMANTIC_RIVALS = {
    "nearest_without_blue_separator": _rival_nearest_without_separator,
    "blue_separator_even_for_same_color": _rival_separator_for_same_odd_gap,
    "upper_color_fills_even_gap": _rival_upper_color_across_even_gap,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_relation(grid, relation):
    analysis, errors = _analyze(grid)
    if analysis is None or errors or self_check(grid):
        return False
    stripes = list(zip(analysis["stripe_rows"], analysis["stripe_colors"]))
    for (upper_row, upper_color), (lower_row, lower_color) in zip(
        stripes, stripes[1:]
    ):
        gap = lower_row - upper_row - 1
        if (
            relation == _REL_ODD_DIFFERENT
            and gap % 2 == 1
            and upper_color != lower_color
        ):
            return True
        if (
            relation == _REL_ODD_SAME
            and gap % 2 == 1
            and upper_color == lower_color
        ):
            return True
        if (
            relation == _REL_EVEN_DIFFERENT
            and gap % 2 == 0
            and upper_color != lower_color
        ):
            return True
    return False


SEMANTIC_WITNESSES = {
    "odd_different_gap_inserts_blue_separator": lambda grid: _has_relation(
        grid, _REL_ODD_DIFFERENT
    ),
    "odd_same_gap_stays_same_color": lambda grid: _has_relation(
        grid, _REL_ODD_SAME
    ),
    "even_different_gap_splits_without_separator": lambda grid: _has_relation(
        grid, _REL_EVEN_DIFFERENT
    ),
}

WITNESS_RIVALS = {
    "odd_different_gap_inserts_blue_separator": [
        "nearest_without_blue_separator"
    ],
    "odd_same_gap_stays_same_color": [
        "blue_separator_even_for_same_color"
    ],
    "even_different_gap_splits_without_separator": [
        "upper_color_fills_even_gap"
    ],
}


def lesson_identifiable(demos, query):
    """Require exact demos that collectively falsify every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons = []
    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = _official_output(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the rule")
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


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
    default_h, default_w, default_side, default_count = _profile_defaults(
        sample_index, difficulty
    )
    height = _scheduled_int(ctx, overrides, "height", default_h, 16, 22)
    width = _scheduled_int(ctx, overrides, "width", default_w, 8, 22)
    marker_side = _scheduled_choice(
        ctx,
        overrides,
        "marker_side",
        default_side,
        ("left", "center", "right"),
    )
    stripe_count = _scheduled_int(
        ctx, overrides, "stripe_count", default_count, 2, 5
    )

    rng = ctx.draw_rng("scene")
    relations = _relation_template(stripe_count, rng)
    stripe_rows = _gap_sizes(height, stripe_count, relations, rng)
    stripe_colors = _stripe_colors(stripe_count, relations, rng)
    marker_col = _marker_column(width, marker_side)

    grid = full_grid(height, width, 7)
    for row in range(height):
        grid[row][marker_col] = 8
    for row, color in zip(stripe_rows, stripe_colors):
        for col in range(width):
            grid[row][col] = color
        grid[row][marker_col] = 1

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid task grid: {errors}")
    return grid
