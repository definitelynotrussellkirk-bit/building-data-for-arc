"""Generator for ``d48ec0001283`` (fill matching row endpoints).

The canonical rule is local to each row.  When a row contains exactly two
non-zero cells, those cells have the same color, and at least one background
cell lies between them, paint the inclusive horizontal span with that color.
Every other row is unchanged.

Ordinary lessons use a four-sample schedule: an exact public-profile anchor, an
all-controls scene, another all-controls scene, then another anchor.  Each
control scene contains a mixed-endpoint row, a blocked-span row, and a row with
three separated same-color markers.  Every sliding three-demo lesson therefore
refutes the principal row-local shortcut rules while half of the ordinary
stream remains on the exact public joint manifold.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d48ec0001283"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "ff9a3ff6c04a"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "A color-0 grid contains 2..3 independent horizontal endpoint pairs. "
    "A fillable row has exactly two equal non-zero cells with at least one "
    "zero between them; the output fills that inclusive row interval in the "
    "endpoint color.  Optional negative-control rows contain two different "
    "endpoint colors, equal endpoints plus a different-color blocker, or three "
    "separated same-color markers; all controls remain unchanged."
)

INVARIANTS = [
    "background is color 0",
    "every normal draw contains at least two fillable same-color row spans",
    "every fillable span has at least one zero cell strictly between endpoints",
    "at most three recognized negative-control rows are present, and none is fillable",
    "every declared axis is exactly recoverable from the returned input grid",
    "the canonical Racket rule, not this module's Python mirror, is output authority",
]

_GAP_PROFILES = ("compact", "wide", "mixed")
_EDGE_PROFILES = ("interior", "left", "right", "both")
_COLOR_MODES = ("distinct", "reused")
_DISTRACTOR_MODES = (
    "none",
    "mixed_endpoints",
    "blocked_span",
    "same_color_triplet",
    "both_controls",
    "all_controls",
)
_DISTRACTOR_COUNTS = {
    "none": 0,
    "mixed_endpoints": 1,
    "blocked_span": 1,
    "same_color_triplet": 1,
    "both_controls": 2,
    "all_controls": 3,
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": 5, "span_count": 3, "distractor_mode": "all_controls"},
]
_CANONICAL_WIDTH_GAPS = {6: 3, 7: 4, 8: 4}
_CANONICAL_WIDTH_STARTS = {6: (1, 0), 7: (0, 1), 8: (1, 0)}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/band draw", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "scheduled/band draw", "valid": "6..14"},
    "span_count": {"type": "int", "default": "scheduled/band draw", "valid": "2..3"},
    "gap_profile": {
        "type": "enum",
        "default": "scheduled",
        "valid": "compact|wide|mixed",
    },
    "edge_profile": {
        "type": "enum",
        "default": "scheduled",
        "valid": "interior|left|right|both",
    },
    "color_mode": {
        "type": "enum",
        "default": "scheduled",
        "valid": "distinct|reused",
    },
    "distractor_mode": {
        "type": "enum",
        "default": "scheduled",
        "valid": "none|mixed_endpoints|blocked_span|same_color_triplet|both_controls|all_controls",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "span_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("gap_profile", "edge_profile", "color_mode", "distractor_mode"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _band_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (5, 7), (6, 8), (2, 2)
    if difficulty == "hard":
        return (9, 12), (11, 14), (3, 3)
    return (7, 9), (8, 11), (2, 3)


def _draw_int(ctx, overrides: dict[str, Any], name: str, default: tuple[int, int],
              valid: tuple[int, int]) -> int:
    """Use the full declared domain for an exact override in every band."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid[0], valid[1])
    return ctx.draw_int(name, default[0], default[1])


def _draw_choice(ctx, overrides: dict[str, Any], name: str,
                 options: tuple[str, ...], defaults: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, defaults)


def _scheduled_defaults(sample_index: int, rng, difficulty: Any) -> dict[str, Any]:
    """Four samples: anchor, all controls, all controls, anchor.

    Combining all three decisive negative controls in both middle slots makes
    every sliding three-example window identify the exact-two condition.
    """
    slot = int(sample_index) % 4
    if slot in (0, 3):
        widths = (6, 7, 8)
        width = widths[(rng.randrange(len(widths)) + slot) % len(widths)]
        return {
            "grid_h": 5,
            "grid_w": width,
            "span_count": 2,
            "gap_profile": "wide",
            "edge_profile": "left",
            "color_mode": "distinct",
            "distractor_mode": "none",
        }

    hrange, wrange, srange = _band_ranges(difficulty)
    if slot == 1:
        return {
            "grid_h": max(6, rng.randint(*hrange)),
            "grid_w": max(7, rng.randint(*wrange)),
            "span_count": 2,
            "gap_profile": "mixed",
            "edge_profile": "both",
            "color_mode": "reused",
            "distractor_mode": "all_controls",
        }
    return {
        "grid_h": max(6, rng.randint(*hrange)),
        "grid_w": max(7, rng.randint(*wrange)),
        "span_count": 2,
        "gap_profile": "mixed",
        "edge_profile": "right",
        "color_mode": "reused",
        "distractor_mode": "all_controls",
    }


def _edge_roles(span_count: int, edge_profile: str) -> list[str]:
    roles = ["interior"] * span_count
    if edge_profile == "left":
        roles[0] = "left"
    elif edge_profile == "right":
        roles[0] = "right"
    elif edge_profile == "both":
        roles[0] = "left"
        roles[1] = "right"
    return roles


def _gap_categories(span_count: int, gap_profile: str) -> list[str]:
    if gap_profile == "compact":
        return ["compact"] * span_count
    if gap_profile == "wide":
        return ["wide"] * span_count
    return ["compact", "wide"] + [
        "compact" if index % 2 == 0 else "wide"
        for index in range(span_count - 2)
    ]


def _choose_gap(rng, width: int, role: str, category: str) -> int:
    max_gap = width - 3 if role == "interior" else width - 2
    if category == "compact":
        return 2
    if max_gap < 3:
        raise ValueError(f"cannot place a wide span in width {width} with role {role}")
    return rng.randint(3, max_gap)


def _choose_columns(rng, width: int, role: str, gap: int) -> tuple[int, int]:
    if role == "left":
        return 0, gap
    if role == "right":
        return width - gap - 1, width - 1
    left = rng.randint(1, width - gap - 2)
    return left, left + gap


def _active_colors(rng, span_count: int, mode: str) -> list[int]:
    if mode == "reused":
        return [rng.choice(range(1, 10))] * span_count
    return rng.sample(range(1, 10), span_count)


def _fresh_color(rng, excluded: set[int]) -> int:
    choices = [color for color in range(1, 10) if color not in excluded]
    if not choices:
        raise ValueError("no color remains for distractor construction")
    return rng.choice(choices)


def _place_distractor(grid: list[list[int]], row: int, mode: str, rng,
                      used_colors: set[int]) -> None:
    width = len(grid[0])
    if mode == "none":
        return
    left = rng.randint(0, 1)
    right = rng.randint(width - 2, width - 1)
    if right - left < 2:
        left, right = 0, width - 1
    if mode == "mixed_endpoints":
        first = _fresh_color(rng, used_colors)
        second = _fresh_color(rng, used_colors | {first})
        grid[row][left] = first
        grid[row][right] = second
        return
    if mode == "same_color_triplet":
        color = _fresh_color(rng, used_colors)
        left, right = 0, width - 1
        middle = rng.randint(left + 2, right - 2)
        grid[row][left] = color
        grid[row][middle] = color
        grid[row][right] = color
        return
    endpoint = _fresh_color(rng, used_colors)
    blocker = _fresh_color(rng, used_colors | {endpoint})
    middle = rng.randint(left + 1, right - 1)
    grid[row][left] = endpoint
    grid[row][middle] = blocker
    grid[row][right] = endpoint


def _row_entries(grid: list[list[int]], row: int) -> list[tuple[int, int]]:
    return [(column, value) for column, value in enumerate(grid[row]) if value != 0]


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "errors": [],
        "active_spans": [],
        "distractor_rows": [],
        "grid_h": 0,
        "grid_w": 0,
    }
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        info["errors"].append("grid must be a non-empty list of rows")
        return info
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        info["errors"].append("grid must be rectangular and non-empty")
        return info
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        info["errors"].append("grid colors must be integers in 0..9")
        return info

    height = len(grid)
    info["grid_h"], info["grid_w"] = height, width
    for row in range(height):
        entries = _row_entries(grid, row)
        if not entries:
            continue
        active = None
        if len(entries) == 2:
            (left, first), (right, second) = entries
            if first == second and right - left >= 2:
                active = {
                    "row": row,
                    "left": left,
                    "right": right,
                    "gap": right - left,
                    "color": first,
                }
        if active is not None:
            info["active_spans"].append(active)
        else:
            info["distractor_rows"].append({"row": row, "entries": entries})

    spans = info["active_spans"]
    gaps = [span["gap"] for span in spans]
    compact = any(gap == 2 for gap in gaps)
    wide = any(gap >= 3 for gap in gaps)
    info["gap_profile"] = (
        "mixed" if compact and wide else "compact" if compact else "wide"
    )

    touches_left = any(span["left"] == 0 for span in spans)
    touches_right = any(span["right"] == width - 1 for span in spans)
    info["edge_profile"] = (
        "both" if touches_left and touches_right
        else "left" if touches_left
        else "right" if touches_right
        else "interior"
    )

    colors = [span["color"] for span in spans]
    if colors and len(set(colors)) == 1:
        info["color_mode"] = "reused"
    elif len(set(colors)) == len(colors):
        info["color_mode"] = "distinct"
    else:
        info["color_mode"] = "partial_reuse"
        info["errors"].append("active colors must be all distinct or all reused")

    distractors = info["distractor_rows"]
    recognized: list[str] = []
    for distractor in distractors:
        entries = distractor["entries"]
        kind = None
        if (
            len(entries) == 2
            and entries[0][1] != entries[1][1]
            and entries[1][0] - entries[0][0] >= 2
        ):
            kind = "mixed_endpoints"
        elif len(entries) == 3:
            (left, first), (middle, blocker), (right, second) = entries
            if first == second == blocker and right - left >= 3:
                kind = "same_color_triplet"
            elif first == second and blocker != first and left < middle < right:
                kind = "blocked_span"
        if kind is None:
            info["errors"].append(
                f"unrecognized negative-control row {distractor['row']}"
            )
        else:
            recognized.append(kind)

    if not distractors:
        mode = "none"
    elif len(distractors) == 1 and len(recognized) == 1:
        mode = recognized[0]
    elif len(distractors) == 2 and sorted(recognized) == ["blocked_span", "mixed_endpoints"]:
        mode = "both_controls"
    elif len(distractors) == 3 and sorted(recognized) == [
        "blocked_span", "mixed_endpoints", "same_color_triplet"
    ]:
        mode = "all_controls"
    else:
        mode = "invalid"
        info["errors"].append(
            "negative controls must be none, one recognized row, the legacy two-control pair, "
            "or exactly one of all three types"
        )
    info["distractor_mode"] = mode
    info["span_count"] = len(spans)
    return info


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {name: info[name] for name in AXES}


def self_check(grid: Any, *, difficulty: Any = None,
               meta: dict[str, Any] | None = None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if not 5 <= info["grid_h"] <= 12:
        errors.append(f"height {info['grid_h']} outside 5..12")
    if not 6 <= info["grid_w"] <= 14:
        errors.append(f"width {info['grid_w']} outside 6..14")
    if not 2 <= info["span_count"] <= 3:
        errors.append(f"fillable span count {info['span_count']} outside 2..3")
    if info["distractor_mode"] not in _DISTRACTOR_MODES:
        errors.append("invalid distractor mode")
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            try:
                observed = observe_overrides(grid)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                for axis, value in requested.items():
                    if axis in AXES and observed.get(axis) != value:
                        errors.append(
                            f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                        )
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python test mirror; the canonical Racket rule remains authority."""
    out = deepcopy(grid)
    for row in range(len(grid)):
        entries = _row_entries(grid, row)
        if len(entries) != 2 or entries[0][1] != entries[1][1]:
            continue
        left, color = entries[0]
        right = entries[1][0]
        for column in range(left, right + 1):
            out[row][column] = color
    return out


def _canonical_signature(grid: Any) -> tuple[Any, ...] | None:
    info = _analyze(grid)
    if info["errors"]:
        return None
    spans = sorted(info["active_spans"], key=lambda span: span["row"])
    return (
        info["grid_h"],
        info["grid_w"],
        tuple(span["row"] for span in spans),
        tuple(span["left"] for span in spans),
        tuple(span["gap"] for span in spans),
        info["color_mode"],
        info["distractor_mode"],
    )


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept exactly the three public linked input profiles, modulo colors."""
    info = _analyze(grid)
    if info["errors"]:
        return list(info["errors"])
    width = info["grid_w"]
    expected_gap = _CANONICAL_WIDTH_GAPS.get(width)
    expected = (
        5,
        width,
        (1, 3),
        _CANONICAL_WIDTH_STARTS.get(width),
        (expected_gap, expected_gap),
        "distinct",
        "none",
    )
    if expected_gap is None or _canonical_signature(grid) != expected:
        return [f"joint canonical signature not observed: {_canonical_signature(grid)!r}"]
    return []


def semantic_signature(grid: Any) -> dict[str, Any]:
    """Expose linked output-grammar observables for review tooling."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    spans = sorted(info["active_spans"], key=lambda span: span["row"])
    output = rule_mirror(grid)
    changed = sum(
        input_value != output_value
        for input_row, output_row in zip(grid, output)
        for input_value, output_value in zip(input_row, output_row)
    )
    return {
        **observe_overrides(grid),
        "active_rows": tuple(span["row"] for span in spans),
        "span_starts": tuple(span["left"] for span in spans),
        "span_gaps": tuple(span["gap"] for span in spans),
        "changed_cells": changed,
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _has_left(grid: Any) -> bool:
    return any(span["left"] == 0 for span in _analyze(grid)["active_spans"])


def _has_right(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["right"] == info["grid_w"] - 1 for span in info["active_spans"])


def _has_interior(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["left"] > 0 and span["right"] < info["grid_w"] - 1
               for span in info["active_spans"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "left_edge_span": _has_left,
    "right_edge_span": _has_right,
    "interior_span": _has_interior,
    "compact_gap": lambda grid: any(span["gap"] == 2 for span in _analyze(grid)["active_spans"]),
    "wide_gap": lambda grid: any(span["gap"] >= 3 for span in _analyze(grid)["active_spans"]),
    "reused_active_color": lambda grid: _analyze(grid)["color_mode"] == "reused",
    "blocked_span_distractor": lambda grid: _analyze(grid)["distractor_mode"] in (
        "blocked_span", "both_controls", "all_controls"
    ),
    "mixed_endpoint_distractor": lambda grid: _analyze(grid)["distractor_mode"] in (
        "mixed_endpoints", "both_controls", "all_controls"
    ),
    "same_color_triplet_distractor": lambda grid: _analyze(grid)["distractor_mode"] in (
        "same_color_triplet", "all_controls"
    ),
    "exact_public_anchor": lambda grid: not strict_canonical_like(grid),
}


def _fill_any_two_nonzeros(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for row in range(len(grid)):
        entries = _row_entries(grid, row)
        if len(entries) == 2:
            left, color = entries[0]
            right = entries[1][0]
            for column in range(left, right + 1):
                out[row][column] = color
    return out


def _ignore_extra_nonzeros(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for row in range(len(grid)):
        entries = _row_entries(grid, row)
        by_color: dict[int, list[int]] = {}
        for column, color in entries:
            by_color.setdefault(color, []).append(column)
        for color, columns in by_color.items():
            if len(columns) == 2:
                for column in range(columns[0], columns[1] + 1):
                    if out[row][column] == 0:
                        out[row][column] = color
    return out


def _fill_same_color_extrema(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: fill extrema whenever every marker in a row has one color."""
    out = deepcopy(grid)
    for row in range(len(grid)):
        entries = _row_entries(grid, row)
        if len(entries) < 2 or len({color for _, color in entries}) != 1:
            continue
        left, color = entries[0]
        right = entries[-1][0]
        for column in range(left, right + 1):
            out[row][column] = color
    return out


def _edge_only(grid: list[list[int]], edge: str) -> list[list[int]]:
    out = deepcopy(grid)
    info = _analyze(grid)
    for span in info["active_spans"]:
        eligible = span["left"] == 0 if edge == "left" else span["right"] == info["grid_w"] - 1
        if eligible:
            for column in range(span["left"], span["right"] + 1):
                out[span["row"]][column] = span["color"]
    return out


def _interior_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    info = _analyze(grid)
    for span in info["active_spans"]:
        if span["left"] > 0 and span["right"] < info["grid_w"] - 1:
            for column in range(span["left"], span["right"] + 1):
                out[span["row"]][column] = span["color"]
    return out


def _distinct_colors_only(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    return rule_mirror(grid) if info["color_mode"] == "distinct" else deepcopy(grid)


def _canonical_rows_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    info = _analyze(grid)
    for span in info["active_spans"]:
        if span["row"] in (1, 3):
            for column in range(span["left"], span["right"] + 1):
                out[span["row"]][column] = span["color"]
    return out


def _widest_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    info = _analyze(grid)
    if not info["active_spans"]:
        return out
    maximum = max(span["gap"] for span in info["active_spans"])
    for span in info["active_spans"]:
        if span["gap"] == maximum:
            for column in range(span["left"], span["right"] + 1):
                out[span["row"]][column] = span["color"]
    return out


def _gap_class_only(grid: list[list[int]], category: str) -> list[list[int]]:
    out = deepcopy(grid)
    info = _analyze(grid)
    for span in info["active_spans"]:
        eligible = span["gap"] == 2 if category == "compact" else span["gap"] >= 3
        if eligible:
            for column in range(span["left"], span["right"] + 1):
                out[span["row"]][column] = span["color"]
    return out


_COMPETING_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fill_between_any_two_nonzeros": _fill_any_two_nonzeros,
    "ignore_extra_nonzeros": _ignore_extra_nonzeros,
    "fill_same_color_extrema": _fill_same_color_extrema,
    "left_anchored_only": lambda grid: _edge_only(grid, "left"),
    "right_anchored_only": lambda grid: _edge_only(grid, "right"),
    "interior_only": _interior_only,
    "distinct_span_colors_only": _distinct_colors_only,
    "canonical_rows_only": _canonical_rows_only,
    "widest_span_only": _widest_only,
    "compact_gaps_only": lambda grid: _gap_class_only(grid, "compact"),
    "wide_gaps_only": lambda grid: _gap_class_only(grid, "wide"),
}

# Machine-checkable shortcut claims.  Every semantic witness names at least one
# rival that must disagree on every grid where that witness fires.  The
# canonical-only shortcuts below deliberately fit all public pairs; generated
# controls and schedule variation must supply their counterexamples.
SEMANTIC_RIVALS = _COMPETING_RULES
WITNESS_RIVALS = {
    "left_edge_span": ["right_anchored_only"],
    "right_edge_span": ["left_anchored_only"],
    "interior_span": ["left_anchored_only"],
    "compact_gap": ["wide_gaps_only", "widest_span_only"],
    "wide_gap": ["compact_gaps_only"],
    "reused_active_color": ["distinct_span_colors_only"],
    "blocked_span_distractor": ["ignore_extra_nonzeros", "canonical_rows_only"],
    "mixed_endpoint_distractor": ["fill_between_any_two_nonzeros"],
    "same_color_triplet_distractor": ["fill_same_color_extrema"],
    "exact_public_anchor": ["left_anchored_only"],
}
LESSON_COMPETITORS = _COMPETING_RULES
CANONICAL_SHORTCUTS = {
    "fill_between_any_two_nonzeros": _fill_any_two_nonzeros,
    "ignore_extra_nonzeros": _ignore_extra_nonzeros,
    "fill_same_color_extrema": _fill_same_color_extrema,
    "distinct_span_colors_only": _distinct_colors_only,
    "canonical_rows_only": _canonical_rows_only,
    "widest_span_only": _widest_only,
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons where a named shortcut fits demos but changes the query."""
    reasons: list[str] = []
    all_pairs = [("demo", index, pair) for index, pair in enumerate(demos)] + [
        ("query", 0, query)
    ]
    for kind, index, pair in all_pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{kind} {index}: pair must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.extend(f"{kind} {index}: {error}" for error in errors)
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{kind} {index}: output does not match the row-span rule")
    if reasons:
        return reasons

    for name, candidate in _COMPETING_RULES.items():
        if all(candidate(pair["input"]) == pair["output"] for pair in demos):
            if candidate(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demos: {name}")
    return reasons


def _build_anchor(width: int, rng) -> list[list[int]]:
    gap = _CANONICAL_WIDTH_GAPS[width]
    grid = full_grid(5, width, 0)
    colors = rng.sample(range(1, 10), 2)
    first_start, second_start = _CANONICAL_WIDTH_STARTS[width]
    grid[1][first_start] = colors[0]
    grid[1][first_start + gap] = colors[0]
    grid[3][second_start] = colors[1]
    grid[3][second_start + gap] = colors[1]
    return grid


def generate(seed: int, sample_index: int, *, difficulty: Any = None,
             **overrides: Any) -> list[list[int]]:
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng(f"layout|{difficulty or 'medium'}")

    if not overrides:
        scheduled = _scheduled_defaults(sample_index, rng, difficulty)
        height = ctx.draw_int("grid_h", scheduled["grid_h"], scheduled["grid_h"])
        width = ctx.draw_int("grid_w", scheduled["grid_w"], scheduled["grid_w"])
        span_count = ctx.draw_int("span_count", scheduled["span_count"], scheduled["span_count"])
        gap_profile = ctx.draw_choice("gap_profile", [scheduled["gap_profile"]])
        edge_profile = ctx.draw_choice("edge_profile", [scheduled["edge_profile"]])
        color_mode = ctx.draw_choice("color_mode", [scheduled["color_mode"]])
        distractor_mode = ctx.draw_choice("distractor_mode", [scheduled["distractor_mode"]])
    else:
        hrange, wrange, srange = _band_ranges(difficulty)
        explicit_span = overrides.get("span_count")
        explicit_distractor = overrides.get("distractor_mode")
        minimum_span = explicit_span if explicit_span is not None else 2
        minimum_controls = (
            _DISTRACTOR_COUNTS[explicit_distractor]
            if explicit_distractor is not None
            else 0
        )
        minimum_height = minimum_span + minimum_controls
        if overrides.get("grid_h") is not None:
            height = _draw_int(ctx, overrides, "grid_h", hrange, (5, 12))
        else:
            lower = max(hrange[0], minimum_height)
            upper = max(lower, hrange[1])
            height = ctx.draw_int("grid_h", lower, min(12, upper))
        width = _draw_int(ctx, overrides, "grid_w", wrange, (6, 14))

        span_count = (
            _draw_int(ctx, overrides, "span_count", srange, (2, 3))
            if explicit_span is not None
            else None
        )
        distractor_mode = (
            _draw_choice(
                ctx,
                overrides,
                "distractor_mode",
                _DISTRACTOR_MODES,
                _DISTRACTOR_MODES,
            )
            if explicit_distractor is not None
            else None
        )
        candidate_spans = (
            [span_count]
            if span_count is not None
            else list(range(srange[0], srange[1] + 1))
        )
        candidate_modes = (
            [distractor_mode]
            if distractor_mode is not None
            else list(_DISTRACTOR_MODES)
        )
        legal_pairs = [
            (candidate_span, candidate_mode)
            for candidate_span in candidate_spans
            for candidate_mode in candidate_modes
            if candidate_span + _DISTRACTOR_COUNTS[candidate_mode] <= height
        ]
        if not legal_pairs and span_count is None:
            candidate_spans = [2, 3]
            legal_pairs = [
                (candidate_span, candidate_mode)
                for candidate_span in candidate_spans
                for candidate_mode in candidate_modes
                if candidate_span + _DISTRACTOR_COUNTS[candidate_mode] <= height
            ]
        if not legal_pairs:
            raise ValueError(
                "incompatible overrides: grid_h, span_count, and distractor_mode "
                f"must satisfy span_count + controls <= grid_h; got grid_h={height}, "
                f"span_count={span_count!r}, distractor_mode={distractor_mode!r}"
            )
        if span_count is None and distractor_mode is None:
            chosen_span, chosen_mode = rng.choice(legal_pairs)
            span_count = ctx.draw_int("span_count", chosen_span, chosen_span)
            distractor_mode = ctx.draw_choice("distractor_mode", [chosen_mode])
        elif span_count is None:
            compatible_spans = sorted({pair[0] for pair in legal_pairs})
            span_count = ctx.draw_int(
                "span_count", compatible_spans[0], compatible_spans[-1]
            )
        elif distractor_mode is None:
            compatible_modes = tuple(pair[1] for pair in legal_pairs)
            distractor_mode = ctx.draw_choice("distractor_mode", compatible_modes)

        gap_profile = _draw_choice(
            ctx, overrides, "gap_profile", _GAP_PROFILES,
            ("compact", "wide") if difficulty == "easy" else
            ("wide", "mixed") if difficulty == "hard" else _GAP_PROFILES,
        )
        edge_profile = _draw_choice(
            ctx, overrides, "edge_profile", _EDGE_PROFILES, _EDGE_PROFILES,
        )
        color_mode = _draw_choice(
            ctx, overrides, "color_mode", _COLOR_MODES, _COLOR_MODES,
        )

    distractor_count = _DISTRACTOR_COUNTS[distractor_mode]
    if span_count + distractor_count > height:
        raise ValueError(
            f"span_count={span_count} plus distractor does not fit grid_h={height}"
        )

    if not overrides and int(sample_index) % 4 in (0, 3):
        grid = _build_anchor(width, rng)
    else:
        grid = full_grid(height, width, 0)
        rows = rng.sample(range(height), span_count + distractor_count)
        if (
            distractor_mode == "all_controls"
            and all(row in (1, 3) for row in rows[:span_count])
        ):
            # Public pairs place their two active spans on rows 1 and 3.  A
            # control scene must itself refute that layout-only shortcut, so
            # swap one sampled control row into the active set when necessary.
            replacement = next(
                index
                for index in range(span_count, len(rows))
                if rows[index] not in (1, 3)
            )
            rows[span_count - 1], rows[replacement] = (
                rows[replacement],
                rows[span_count - 1],
            )
        active_rows = rows[:span_count]
        colors = _active_colors(rng, span_count, color_mode)
        roles = _edge_roles(span_count, edge_profile)
        categories = _gap_categories(span_count, gap_profile)
        for row, color, role, category in zip(active_rows, colors, roles, categories):
            gap = _choose_gap(rng, width, role, category)
            left, right = _choose_columns(rng, width, role, gap)
            grid[row][left] = color
            grid[row][right] = color
        if distractor_mode in ("both_controls", "all_controls"):
            control_modes = ["mixed_endpoints", "blocked_span"]
            if distractor_mode == "all_controls":
                control_modes.append("same_color_triplet")
            control_rows = rows[-len(control_modes):]
            used = set(colors)
            for control_row, control_mode in zip(control_rows, control_modes):
                _place_distractor(grid, control_row, control_mode, rng, used)
                used = {value for grid_row in grid for value in grid_row if value != 0}
        elif distractor_count:
            _place_distractor(grid, rows[-1], distractor_mode, rng, set(colors))

    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "span_count": span_count,
        "gap_profile": gap_profile,
        "edge_profile": edge_profile,
        "color_mode": color_mode,
        "distractor_mode": distractor_mode,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes drifted: expected {expected}, observed {observed}")
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed grid failed self_check: {errors}")
    return grid
