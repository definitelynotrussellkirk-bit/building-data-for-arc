"""Generator for ``arc_puzzle_bank_21_set21_bundle:easy_p01``.

The canonical rule fills a horizontal span only when a row contains exactly
 two occurrences of one non-background color and every cell strictly between
 those endpoints is background.  Generated lessons include lawful positive
 rows plus explicit no-op distractors that rule out color-blind, blocker-blind,
 and "fill every non-empty row" shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "23038bd082f9"
VERSION = "3.0.0"
TASK_ID = "23038bd082f9"
RULE_HASH = "df33b603ecad"
SUMMARY = (
    "A zero-background grid contains one or more active rows.  An active row "
    "has exactly two cells of the same non-zero color, separated by at least "
    "one zero.  The output fills that inclusive horizontal span with the "
    "endpoint color.  Optional distractor rows contain either one marker, two "
    "different-color markers, or a same-color endpoint pair with a different-"
    "color blocker inside; those rows remain unchanged."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is 0",
    "at least one row has exactly two matching endpoints with a non-empty zero gap",
    "positive rows are the only rows changed by the canonical Racket rule",
    "distractor rows are single markers, mismatched endpoint pairs, or blocked matching pairs",
]

PALETTE_KINDS = ("canonical", "low_first", "high_first", "alternating")
GAP_STYLES = ("tight", "wide", "mixed")
DISTRACTOR_MODES = ("mismatch", "blocked", "single", "mixed")
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 6..12",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..16",
        "valid": "7..16",
    },
    "span_count": {
        "type": "int",
        "default": "difficulty-aware 2..6",
        "valid": "1..6",
    },
    "distractor_count": {
        "type": "int",
        "default": "scheduled 0..3",
        "valid": "0..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "canonical|low_first|high_first|alternating",
    },
    "gap_style": {
        "type": "str",
        "default": "rng helpful",
        "valid": "tight|wide|mixed",
    },
    "distractor_mode": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "mismatch|blocked|single|mixed",
    },
}

_PALETTES = {
    "canonical": (2, 3, 4, 5, 6, 7, 8, 9, 1),
    "low_first": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "high_first": (9, 8, 7, 6, 5, 4, 3, 2, 1),
    "alternating": (1, 9, 2, 8, 3, 7, 4, 6, 5),
}


def _validate_rectangular_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], 0, 0
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"], len(grid), width
    illegal = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if illegal:
        return ["grid colors must be integer values in 0..9"], len(grid), width
    return [], len(grid), width


def _classify_row(row: list[int]) -> dict[str, Any]:
    cells = [(column, value) for column, value in enumerate(row) if value != 0]
    if not cells:
        return {"kind": "empty"}
    if len(cells) == 1:
        column, color = cells[0]
        return {"kind": "single", "columns": (column,), "colors": (color,)}
    if len(cells) == 2:
        (left, left_color), (right, right_color) = cells
        gap = right - left - 1
        if gap < 1:
            return {"kind": "invalid_adjacent", "columns": (left, right)}
        if left_color == right_color:
            return {
                "kind": "active",
                "columns": (left, right),
                "colors": (left_color,),
                "gap": gap,
            }
        return {
            "kind": "mismatch",
            "columns": (left, right),
            "colors": (left_color, right_color),
            "gap": gap,
        }
    if len(cells) == 3:
        (left, left_color), (middle, middle_color), (right, right_color) = cells
        if (
            right - left >= 2
            and left < middle < right
            and left_color == right_color
            and middle_color != left_color
        ):
            return {
                "kind": "blocked",
                "columns": (left, middle, right),
                "colors": (left_color, middle_color),
                "gap": right - left - 1,
            }
    return {
        "kind": "invalid_pattern",
        "columns": tuple(column for column, _ in cells),
        "colors": tuple(value for _, value in cells),
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Return exact task-linked row roles and shortcut-rebutting witnesses."""
    errors, height, width = _validate_rectangular_grid(grid)
    if errors:
        return {"errors": errors, "grid_h": height, "grid_w": width}

    rows = [_classify_row(row) for row in grid]
    kind_counts: dict[str, int] = {}
    for row in rows:
        kind = str(row["kind"])
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    active_rows = [row for row in rows if row["kind"] == "active"]
    distractor_rows = [
        row for row in rows if row["kind"] in {"single", "mismatch", "blocked"}
    ]
    active_colors = [int(row["colors"][0]) for row in active_rows]
    active_spans = [tuple(row["columns"]) for row in active_rows]
    active_gaps = [int(row["gap"]) for row in active_rows]
    return {
        "errors": [],
        "grid_h": height,
        "grid_w": width,
        "rows": rows,
        "kind_counts": kind_counts,
        "span_count": len(active_rows),
        "distractor_count": len(distractor_rows),
        "active_colors": tuple(active_colors),
        "active_spans": tuple(active_spans),
        "active_gaps": tuple(active_gaps),
        "has_short_gap": any(gap <= 2 for gap in active_gaps),
        "has_wide_gap": any(gap >= 4 for gap in active_gaps),
        "has_edge_endpoint": any(
            left == 0 or right == width - 1 for left, right in active_spans
        ),
        "has_interior_span": any(
            left > 0 and right < width - 1 for left, right in active_spans
        ),
        "has_mismatch": kind_counts.get("mismatch", 0) > 0,
        "has_blocked": kind_counts.get("blocked", 0) > 0,
        "has_single": kind_counts.get("single", 0) > 0,
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact integer axis from the returned grid."""
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(str(item) for item in facts["errors"]))
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "span_count": int(facts["span_count"]),
        "distractor_count": int(facts["distractor_count"]),
    }


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default_lo: int,
    default_hi: int,
    valid_lo: int,
    valid_hi: int,
) -> int:
    lo, hi = (valid_lo, valid_hi) if label in overrides else (default_lo, default_hi)
    return ctx.draw_int(label, lo, hi)


def _band_ranges(difficulty: str | None) -> dict[str, tuple[int, int]]:
    if difficulty == "easy":
        return {
            "grid_h": (6, 7),
            "grid_w": (7, 9),
            "span_count": (2, 3),
            "distractor_count": (0, 2),
        }
    if difficulty == "hard":
        return {
            "grid_h": (9, 12),
            "grid_w": (11, 16),
            "span_count": (3, 6),
            "distractor_count": (1, 3),
        }
    return {
        "grid_h": (7, 10),
        "grid_w": (8, 13),
        "span_count": (2, 4),
        "distractor_count": (1, 3),
    }


def _span_columns(
    rng,
    width: int,
    gap_style: str,
    *,
    interior: bool = False,
    edge: bool = False,
) -> tuple[int, int]:
    if interior and edge:
        raise ValueError("span cannot be both interior and edge-anchored")

    min_distance = 2
    max_distance = width - 1
    if interior:
        max_distance = width - 3
    if gap_style == "tight":
        max_distance = min(max_distance, 3)
    elif gap_style == "wide":
        min_distance = min(max_distance, 5)
        min_distance = max(4, min_distance)
    if max_distance < min_distance:
        min_distance = max_distance
    distance = rng.randint(min_distance, max_distance)

    if interior:
        left = rng.randint(1, width - distance - 2)
    elif edge:
        left = 0 if rng.random() < 0.5 else width - distance - 1
    else:
        left = rng.randint(0, width - distance - 1)
    return left, left + distance


def _other_color(rng, palette: tuple[int, ...], excluded: set[int]) -> int:
    choices = [color for color in palette if color not in excluded]
    if not choices:
        raise ValueError("palette leaves no legal distractor color")
    return rng.choice(choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, shortcut-rebutting span-fill input grid."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    ranges = _band_ranges(difficulty)
    canonical_anchor = (
        difficulty is not None
        and sample_index % 9 in (3, 4, 5)
        and not ({"grid_h", "grid_w", "span_count", "distractor_count", "distractor_mode"} & set(overrides))
    )
    if canonical_anchor:
        ranges = {
            "grid_h": (6, 7),
            "grid_w": (7, 9),
            "span_count": (3, 3),
            "distractor_count": (0, 0),
        }

    explicit_span = None
    if "span_count" in overrides:
        explicit_span = ctx.draw_int("span_count", 1, 6)
    explicit_distractors = None
    if "distractor_count" in overrides:
        explicit_distractors = ctx.draw_int("distractor_count", 0, 3)

    reserve_spans = explicit_span if explicit_span is not None else ranges["span_count"][0]
    reserve_distractors = (
        explicit_distractors
        if explicit_distractors is not None
        else (1 if difficulty is None else ranges["distractor_count"][0])
    )
    required_rows = reserve_spans + reserve_distractors
    h_lo, h_hi = ranges["grid_h"]
    if "grid_h" not in overrides:
        h_lo = max(h_lo, required_rows)
        if h_lo > h_hi:
            h_hi = min(12, h_lo)
    height = _draw_int_axis(ctx, overrides, "grid_h", h_lo, h_hi, 6, 12)

    w_lo, w_hi = ranges["grid_w"]
    width = _draw_int_axis(ctx, overrides, "grid_w", w_lo, w_hi, 7, 16)

    if explicit_span is None:
        span_lo, span_hi = ranges["span_count"]
        reserved_for_distractors = (
            explicit_distractors
            if explicit_distractors is not None
            else (1 if difficulty is None else ranges["distractor_count"][0])
        )
        span_hi = min(span_hi, height - reserved_for_distractors)
        if span_hi < span_lo:
            span_lo = span_hi
        if span_lo < 1:
            raise ValueError("grid_h leaves no room for an active span row")
        span_count = ctx.draw_int("span_count", span_lo, span_hi)
    else:
        span_count = explicit_span

    if explicit_distractors is None:
        distract_lo, distract_hi = ranges["distractor_count"]
        if difficulty is None or "distractor_mode" in overrides:
            distract_lo = max(1, distract_lo)
        distract_hi = min(distract_hi, height - span_count)
        if distract_hi < distract_lo:
            distract_lo = distract_hi
        if distract_lo < 0:
            raise ValueError("grid_h leaves no room for requested rows")
        distractor_count = ctx.draw_int("distractor_count", distract_lo, distract_hi)
    else:
        distractor_count = explicit_distractors

    if span_count + distractor_count > height:
        raise ValueError(
            "grid_h is incompatible with span_count + distractor_count: "
            f"{height} < {span_count} + {distractor_count}"
        )

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    gap_style = ctx.draw_choice("gap_style", GAP_STYLES)
    if "distractor_mode" in overrides:
        distractor_mode = ctx.draw_choice("distractor_mode", DISTRACTOR_MODES)
    else:
        scheduled = DISTRACTOR_MODES[sample_index % 3]
        distractor_mode = ctx.draw_choice("distractor_mode", (scheduled,))
    if distractor_count == 0 and "distractor_mode" in overrides:
        raise ValueError(
            "distractor_mode is not observable when distractor_count is 0"
        )

    rng = ctx.draw_rng("layout")
    palette = _PALETTES[palette_kind]
    active_colors = list(palette[:span_count])
    rng.shuffle(active_colors)

    grid = full_grid(height, width, 0)
    selected_rows = rng.sample(range(height), span_count + distractor_count)
    active_rows = selected_rows[:span_count]
    distractor_rows = selected_rows[span_count:]

    for index, (row, color) in enumerate(zip(active_rows, active_colors)):
        left, right = _span_columns(
            rng,
            width,
            gap_style,
            interior=index == 0,
            edge=index == 1,
        )
        grid[row][left] = color
        grid[row][right] = color

    for index, row in enumerate(distractor_rows):
        mode = distractor_mode
        if mode == "mixed":
            mode = ("mismatch", "blocked", "single")[(index + sample_index) % 3]
        if mode == "single":
            grid[row][rng.randrange(width)] = _other_color(rng, palette, set())
            continue

        left, right = _span_columns(rng, width, gap_style)
        if mode == "mismatch":
            left_color = _other_color(rng, palette, set())
            right_color = _other_color(rng, palette, {left_color})
            grid[row][left] = left_color
            grid[row][right] = right_color
            continue

        endpoint_color = _other_color(rng, palette, set())
        blocker_color = _other_color(rng, palette, {endpoint_color})
        middle = rng.randint(left + 1, right - 1)
        grid[row][left] = endpoint_color
        grid[row][middle] = blocker_color
        grid[row][right] = endpoint_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid row-span lesson: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "span_count": span_count,
        "distractor_count": distractor_count,
    }
    if observed != expected:
        raise RuntimeError(f"keyed axes were not realized: {expected} -> {observed}")
    return deepcopy(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and the stronger generated teaching grammar."""
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    if facts["span_count"] < 1:
        errors.append("at least one active matching-endpoint row is required")
    invalid = {
        kind: count
        for kind, count in facts["kind_counts"].items()
        if kind not in {"empty", "active", "single", "mismatch", "blocked"}
    }
    if invalid:
        errors.append(f"unrecognized row pattern(s): {invalid}")
    if not facts["has_interior_span"]:
        errors.append("at least one active span must leave exterior background cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical row grammar, including explicit lawful no-ops."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror used only for focused tests and semantic evidence."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        colors = sorted({value for value in row if value != 0})
        for color in colors:
            columns = [column for column, value in enumerate(row) if value == color]
            if len(columns) != 2:
                continue
            left, right = columns
            if all(row[column] == 0 for column in range(left + 1, right)):
                for column in range(left, right + 1):
                    output[row_index][column] = color
    return output


def _fill_any_two_markers(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(cells) == 2:
            left, color = cells[0]
            right = cells[1][0]
            for column in range(left, right + 1):
                output[row_index][column] = color
    return output


def _ignore_blockers(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for color in sorted({value for value in row if value != 0}):
            columns = [column for column, value in enumerate(row) if value == color]
            if len(columns) == 2:
                for column in range(columns[0], columns[1] + 1):
                    output[row_index][column] = color
    return output


def _fill_entire_nonempty_row(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(cells) >= 2:
            fill = cells[0][1]
            output[row_index] = [fill if value == 0 else value for value in row]
    return output


def _fill_only_lowest_active_color(grid: list[list[int]]) -> list[list[int]]:
    active = []
    for row_index, row in enumerate(grid):
        role = _classify_row(row)
        if role["kind"] == "active":
            active.append((int(role["colors"][0]), row_index, role))
    if not active:
        return deepcopy(grid)
    chosen = min(color for color, _, _ in active)
    output = deepcopy(grid)
    for color, row_index, role in active:
        if color != chosen:
            continue
        left, right = role["columns"]
        for column in range(left, right + 1):
            output[row_index][column] = color
    return output


_RIVAL_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "color_blind_two_marker_fill": _fill_any_two_markers,
    "blocker_blind_matching_fill": _ignore_blockers,
    "fill_entire_nonempty_row": _fill_entire_nonempty_row,
    "fill_only_lowest_active_color": _fill_only_lowest_active_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every plausible shortcut to be falsified before the query."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if pair.get("output") != rule_mirror(pair.get("input")):
            reasons.append(f"demo {index} output disagrees with the canonical rule")
    if query.get("output") != rule_mirror(query.get("input")):
        reasons.append("query output disagrees with the canonical rule")
    if reasons:
        return reasons

    for name, rival in _RIVAL_RULES.items():
        agrees_with_demos = all(
            rival(pair["input"]) == pair["output"] for pair in demos
        )
        if agrees_with_demos and rival(query["input"]) != query["output"]:
            reasons.append(f"rival rule remains consistent: {name}")
    return reasons


def mutation_fixtures():
    """Task-local structural impostors that ``self_check`` must reject."""
    all_zero = full_grid(7, 9, 0)

    adjacent = full_grid(7, 9, 0)
    adjacent[2][3] = adjacent[2][4] = 4

    three_same = full_grid(7, 9, 0)
    three_same[2][1] = three_same[2][4] = three_same[2][7] = 5

    no_interior_span = full_grid(7, 9, 0)
    no_interior_span[2][0] = no_interior_span[2][8] = 6

    vertical_only = full_grid(7, 9, 0)
    vertical_only[1][4] = 3
    vertical_only[5][4] = 3

    return [
        ("all_zero_no_active_span", all_zero),
        ("adjacent_matching_markers", adjacent),
        ("three_same_color_markers", three_same),
        ("edge_to_edge_without_exterior_background", no_interior_span),
        ("vertical_pair_not_horizontal_span", vertical_only),
    ]


SEMANTIC_WITNESSES = {
    "matching_endpoint_span": lambda grid: semantic_observables(grid).get("span_count", 0) >= 1,
    "short_gap": lambda grid: bool(semantic_observables(grid).get("has_short_gap")),
    "wide_gap": lambda grid: bool(semantic_observables(grid).get("has_wide_gap")),
    "edge_endpoint": lambda grid: bool(semantic_observables(grid).get("has_edge_endpoint")),
    "interior_span": lambda grid: bool(semantic_observables(grid).get("has_interior_span")),
    "mismatched_endpoint_noop": lambda grid: bool(semantic_observables(grid).get("has_mismatch")),
    "blocked_matching_pair_noop": lambda grid: bool(semantic_observables(grid).get("has_blocked")),
    "single_marker_noop": lambda grid: bool(semantic_observables(grid).get("has_single")),
}
