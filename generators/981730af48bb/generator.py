"""Input generator for task 981730af48bb — stamp pair midpoints.

Every active row contains exactly two equal-colored endpoints at an even
horizontal distance.  The unchanged Racket authority emits an otherwise blank
grid with that color at the integer midpoint of each pair.

The ordinary sampler keeps canonical 2/4 per-row span variation in every
lesson, plus uniform short and width-relative wide cases.  Exact overrides expose
only axes that are recoverable from returned pixels.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "981730af48bb"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "250fc3187c8a"

SUMMARY = (
    "Each active row has two equal-colored endpoints at an even distance; "
    "replace every pair by one same-colored dot at its integer midpoint."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0",
    "the grid is 4..12 rows by 6..16 columns",
    "generated scenes have 2..4 active rows",
    "each active row has exactly two equal nonzero endpoint colors",
    "each endpoint distance is positive and even",
    "the output is blank except for one same-colored midpoint per active row",
]

SPAN_PROFILES = ("short", "wide", "canonical")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile cycle plus difficulty-aware broad draws",
        "valid": "4..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile cycle plus difficulty-aware broad draws",
        "valid": "6..16",
    },
    "pairs": {
        "type": "int",
        "default": "2 canonical/easy, 3 medium, 4 hard broad draws",
        "valid": "2..4",
    },
    "span_profile": {
        "type": "str",
        "default": "canonical 2/4 variation plus short/wide broad draws",
        "valid": "short|wide|canonical",
    },
}

# With grid_h >= 4 and 2 <= pairs <= 4, every advertised Cartesian
# combination is constructively supported in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_INT_RANGES = {
    "grid_h": (4, 12),
    "grid_w": (6, 16),
    "pairs": (2, 4),
}
_CANONICAL_PROFILES = ((5, 7), (4, 6), (5, 8))


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_RANGES:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = _INT_RANGES[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "span_profile":
            if type(value) is not str:
                raise TypeError(
                    f"span_profile must be a string, not {type(value).__name__}"
                )
            if value not in SPAN_PROFILES:
                raise ValueError(
                    f"span_profile={value!r} not in {SPAN_PROFILES!r}"
                )


def _draw_int_axis(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _INT_RANGES[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _draw_choice_axis(
    ctx, overrides: dict[str, Any], name: str, default: str, options: tuple[str, ...]
) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _default_profile(ctx, sample_index: int, difficulty: str) -> tuple[int, int, int]:
    """Return one exact default (height, width, pair count).

    Three residues replay the three public size profiles with two colors/pairs.
    The fourth is a broader difficulty-aware draw.  This keeps canonical scale
    present in every band without collapsing the rest of the distribution.
    """
    residue = sample_index % 4
    if residue < 3:
        h, w = _CANONICAL_PROFILES[residue]
        return h, w, 2

    ranges = {
        "easy": ((4, 6), (6, 9), (2, 2)),
        "medium": ((6, 9), (9, 13), (3, 3)),
        "hard": ((9, 12), (13, 16), (4, 4)),
    }
    (h_lo, h_hi), (w_lo, w_hi), (p_lo, p_hi) = ranges[difficulty]
    rng = ctx.draw_rng("broad_profile")
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi), rng.randint(p_lo, p_hi)


def _span_for(width: int, profile: str) -> int:
    if profile == "short":
        return 2
    # Greatest positive even distance that fits in the row.
    return 2 * ((width - 1) // 2)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _validate_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    default_h, default_w, default_pairs = _default_profile(ctx, sample_index, band)
    height = _draw_int_axis(ctx, overrides, "grid_h", default_h)
    width = _draw_int_axis(ctx, overrides, "grid_w", default_w)
    pair_count = _draw_int_axis(ctx, overrides, "pairs", default_pairs)
    if sample_index % 4 < 3:
        default_span = "canonical"
    else:
        default_span = SPAN_PROFILES[(sample_index // 4) % len(SPAN_PROFILES)]
    span_profile = _draw_choice_axis(
        ctx, overrides, "span_profile", default_span, SPAN_PROFILES
    )

    if span_profile == "short":
        spans = [2] * pair_count
    elif span_profile == "wide":
        spans = [_span_for(width, "wide")] * pair_count
    else:
        # Canonical examples mix distances 2 and 4 within one grid.  Alternating
        # them prevents a solver from reusing one row's offset for every row.
        spans = [2 if index % 2 == 0 else 4 for index in range(pair_count)]

    rows = ctx.draw_rng("active_rows").sample(range(height), pair_count)
    colors = ctx.draw_rng("pair_colors").sample(range(1, 10), pair_count)
    positions = ctx.draw_rng("endpoint_positions")

    grid = full_grid(height, width, 0)
    for row, color, span in zip(rows, colors, spans):
        left = positions.randint(0, width - span - 1)
        grid[row][left] = color
        grid[row][left + span] = color

    expected = {
        "grid_h": height,
        "grid_w": width,
        "pairs": pair_count,
        "span_profile": span_profile,
    }
    observed = observe_overrides(grid)
    if observed != expected:  # pragma: no cover - fail-loud internal contract
        raise RuntimeError(
            f"generated scene lost exact axes: expected {expected}, observed {observed}"
        )
    errors = self_check(grid)
    if errors:  # pragma: no cover - fail-loud internal contract
        raise RuntimeError("generated invalid midpoint scene: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"], len(grid), 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"], len(grid), width

    errors: list[str] = []
    height = len(grid)
    if not 4 <= height <= 12 or not 6 <= width <= 16:
        errors.append(f"grid dimensions {height}x{width} outside 4..12 by 6..16")
    bad = sorted(
        {
            repr(value)
            for row in grid
            for value in row
            if type(value) is not int or not 0 <= value <= 9
        }
    )
    if bad:
        errors.append("cells must be integer ARC colors 0..9; found " + ", ".join(bad[:5]))
    return errors, height, width


def _analysis(grid) -> dict[str, Any]:
    errors, height, width = _basic_grid_errors(grid)
    result: dict[str, Any] = {
        "errors": errors,
        "height": height,
        "width": width,
        "rows": [],
        "spans": [],
        "colors": [],
    }
    if not height or not width or any("ragged" in error for error in errors):
        return result
    if any("cells must" in error for error in errors):
        return result

    active = []
    for row_index, row in enumerate(grid):
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        if not cells:
            continue
        if len(cells) != 2:
            errors.append(
                f"row {row_index}: expected exactly 2 non-background cells, found {len(cells)}"
            )
            continue
        (left, left_color), (right, right_color) = cells
        if left_color != right_color:
            errors.append(
                f"row {row_index}: endpoint colors differ ({left_color} vs {right_color})"
            )
        span = right - left
        if span <= 0 or span % 2:
            errors.append(
                f"row {row_index}: endpoint distance {span} must be positive and even"
            )
        active.append(
            {
                "row": row_index,
                "left": left,
                "right": right,
                "span": span,
                "color": left_color,
            }
        )

    if not 1 <= len(active) <= 4:
        errors.append(f"expected 1..4 active rows, found {len(active)}")
    result.update(
        {
            "rows": active,
            "spans": [item["span"] for item in active],
            "colors": [item["color"] for item in active],
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """All generated draws stay inside the selected task grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    spans = analysis["spans"]
    wide = _span_for(analysis["width"], "wide")
    if all(span == 2 for span in spans):
        profile = "short"
    elif all(span == wide for span in spans):
        profile = "wide"
    elif all(span in {2, 4} for span in spans):
        # Generated canonical-profile scenes contain both values.  The broader
        # acceptance also recognizes the public width-8 example whose two rows
        # both use distance 4.
        profile = "canonical"
    else:
        raise ValueError("active rows do not match a declared span profile")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "pairs": len(analysis["rows"]),
        "span_profile": profile,
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for tests and rival diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for item in analysis["rows"]:
        output[item["row"]][(item["left"] + item["right"]) // 2] = item["color"]
    return output


def _rival_identity(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    return [list(row) for row in grid]


def _rival_fill_segment(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    for item in analysis["rows"]:
        for column in range(item["left"], item["right"] + 1):
            output[item["row"]][column] = item["color"]
    return output


def _single_dot_rival(grid, column_fn: Callable[[dict[str, int]], int]):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    for item in analysis["rows"]:
        output[item["row"]][column_fn(item)] = item["color"]
    return output


def _rival_left_inner(grid):
    return _single_dot_rival(grid, lambda item: item["left"] + 1)


def _rival_right_inner(grid):
    return _single_dot_rival(grid, lambda item: item["right"] - 1)


def _rival_first_pair_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    color = analysis["rows"][0]["color"]
    for item in analysis["rows"]:
        output[item["row"]][(item["left"] + item["right"]) // 2] = color
    return output


def _rival_first_active_row_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    item = analysis["rows"][0]
    output[item["row"]][(item["left"] + item["right"]) // 2] = item["color"]
    return output


def _rival_span_four_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    for item in analysis["rows"]:
        if item["span"] == 4:
            output[item["row"]][(item["left"] + item["right"]) // 2] = item["color"]
    return output


def _rival_reuse_first_row_half_span(grid):
    """Wrong shortcut: infer one horizontal offset and reuse it for all rows."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid midpoint-pair grid")
    output = full_grid(analysis["height"], analysis["width"], 0)
    half_span = analysis["rows"][0]["span"] // 2
    for item in analysis["rows"]:
        column = item["left"] + half_span
        if 0 <= column < analysis["width"]:
            output[item["row"]][column] = item["color"]
    return output


SEMANTIC_RIVALS = {
    "keep_endpoints": _rival_identity,
    "fill_between_endpoints": _rival_fill_segment,
    "choose_left_inner_cell": _rival_left_inner,
    "choose_right_inner_cell": _rival_right_inner,
    "use_first_pair_color": _rival_first_pair_color,
    "process_first_active_row_only": _rival_first_active_row_only,
    "process_only_span_four": _rival_span_four_only,
    "reuse_first_row_half_span": _rival_reuse_first_row_half_span,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_any_pair(grid) -> bool:
    return _lawful(grid) is not None


def _witness_wide_span(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and any(span > 2 for span in analysis["spans"]))


def _witness_multiple_colors(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and len(set(analysis["colors"])) >= 2)


def _witness_multiple_rows(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and len(analysis["rows"]) >= 2)


def _witness_non_four_span(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and any(span != 4 for span in analysis["spans"]))


def _witness_per_row_span(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and len(set(analysis["spans"])) >= 2)


SEMANTIC_WITNESSES = {
    "midpoint_replaces_endpoints": _witness_any_pair,
    "wide_span_requires_true_midpoint": _witness_wide_span,
    "row_colors_are_independent": _witness_multiple_colors,
    "all_active_rows_are_processed": _witness_multiple_rows,
    "non_four_span_is_processed": _witness_non_four_span,
    "span_is_computed_per_row": _witness_per_row_span,
}
WITNESS_RIVALS = {
    "midpoint_replaces_endpoints": ["keep_endpoints", "fill_between_endpoints"],
    "wide_span_requires_true_midpoint": [
        "choose_left_inner_cell",
        "choose_right_inner_cell",
    ],
    "row_colors_are_independent": ["use_first_pair_color"],
    "all_active_rows_are_processed": ["process_first_active_row_only"],
    "non_four_span_is_processed": ["process_only_span_four"],
    "span_is_computed_per_row": ["reuse_first_row_half_span"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Finite check that every named plausible rival is refuted by the demos."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"at least {EXAMPLES_NEEDED} demonstrations are required")
        return reasons

    labelled = [*(demos or []), query]
    for index, pair in enumerate(labelled):
        label = "query" if index == len(labelled) - 1 else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output grids")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            reasons.append(f"{label} input is outside the rule domain: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"{label} output does not match the midpoint rule")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"declared competitor {name!r} fits every demonstration")
    return reasons
