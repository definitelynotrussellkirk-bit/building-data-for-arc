"""Generator for ARC task 22168020 / 806425ca81b3.

For each row and each nonzero color independently, preserve the original
anchors and fill every zero strictly between that color's leftmost and
rightmost anchors.  Colors with fewer than two anchors do not create a span.

The four-sample schedule deliberately alternates a canonical-scale anchor,
a row containing two disjoint colored spans, a singleton-color distractor,
and an edge-touching span.  Every four consecutive demonstrations therefore
refutes the main row-global, exactly-two-anchor, singleton-expansion, and
interior-only shortcuts while retaining broad position and palette variation.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "806425ca81b3"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "c27cec63afa0"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "In every row, process each nonzero color independently: preserve its "
    "anchors and fill zero cells strictly between its leftmost and rightmost "
    "anchors. A singleton color creates no span, and two disjoint color spans "
    "in the same row remain separate."
)

INVARIANTS = [
    "background is 0 and foreground colors are integers 1..9",
    "at least one repeated-color row span contains a zero to be filled",
    "repeated-color spans in the same row are disjoint, avoiding precedence ambiguity",
    "ordinary lessons cycle through canonical-scale, mixed-color, singleton-distractor, and edge-span profiles",
]

SCENE_PROFILES = (
    "canonical_rows",
    "mixed_disjoint",
    "singleton_distractor",
    "edge_spans",
)
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "mixed_disjoint",
    "singleton_distractor",
    "edge_spans",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 8..14; canonical schedule pins 10",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 9..14; canonical schedule pins 10",
        "valid": "9..14",
    },
    "active_rows": {
        "type": "int",
        "default": "difficulty-weighted 1..5; canonical schedule pins 5",
        "valid": "1..5",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-phase sample_index schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)


def _row_facts(row: list[int]) -> dict:
    positions: dict[int, list[int]] = {}
    for col, value in enumerate(row):
        if value != 0:
            positions.setdefault(value, []).append(col)
    repeated = {color: cols for color, cols in positions.items() if len(cols) >= 2}
    singletons = {color: cols[0] for color, cols in positions.items() if len(cols) == 1}
    spans = {color: (min(cols), max(cols)) for color, cols in repeated.items()}
    nontrivial = {
        color: any(row[col] == 0 for col in range(left + 1, right))
        for color, (left, right) in spans.items()
    }
    overlaps: list[tuple[int, int]] = []
    colors = sorted(spans)
    for index, color_a in enumerate(colors):
        left_a, right_a = spans[color_a]
        for color_b in colors[index + 1 :]:
            left_b, right_b = spans[color_b]
            if max(left_a, left_b) <= min(right_a, right_b):
                overlaps.append((color_a, color_b))
    return {
        "positions": positions,
        "repeated": repeated,
        "singletons": singletons,
        "spans": spans,
        "nontrivial": nontrivial,
        "overlaps": overlaps,
    }


def _analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid is empty"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid has no columns"]}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged"]}
    if not 6 <= height <= 30 or not 6 <= width <= 30:
        errors.append(f"grid dimensions {height}x{width} are outside the calibrated 6..30 range")
    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("grid values must be integer ARC colors 0..9")

    row_facts = [_row_facts(row) for row in grid]
    active_rows = [index for index, facts in enumerate(row_facts) if facts["positions"]]
    if not active_rows:
        errors.append("expected at least one active row")

    nontrivial_count = 0
    for row_index in active_rows:
        facts = row_facts[row_index]
        if not facts["repeated"]:
            errors.append(f"active row {row_index} has no repeated color anchor pair")
        if facts["overlaps"]:
            errors.append(
                f"active row {row_index} has overlapping repeated-color spans {facts['overlaps']}"
            )
        nontrivial_count += sum(facts["nontrivial"].values())
    if active_rows and nontrivial_count == 0:
        errors.append("all repeated-color spans are already solid/adjacent; transformation is identity")

    distinct_colors = sorted({value for row in grid for value in row if value != 0})
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "row_facts": row_facts,
        "active_rows": active_rows,
        "nontrivial_count": nontrivial_count,
        "distinct_colors": distinct_colors,
    }


def _classify_profile(analysis: dict) -> str:
    row_facts = analysis["row_facts"]
    active_rows = analysis["active_rows"]
    if any(row_facts[row]["singletons"] for row in active_rows):
        return "singleton_distractor"
    if any(len(row_facts[row]["repeated"]) >= 2 for row in active_rows):
        return "mixed_disjoint"
    if any(
        any(left == 0 or right == analysis["width"] - 1 for left, right in row_facts[row]["spans"].values())
        for row in active_rows
    ):
        return "edge_spans"
    return "canonical_rows"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the calibrated, unambiguous teaching grammar."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked public scale/palette/row grammar, not only marginals."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) != (10, 10):
        reasons.append("canonical inputs are 10x10")
    if not 4 <= len(analysis["active_rows"]) <= 9:
        reasons.append("canonical inputs have 4..9 active rows")
    if not 1 <= len(analysis["distinct_colors"]) <= 3:
        reasons.append("canonical inputs use 1..3 nonzero colors")
    if any(
        analysis["row_facts"][row]["singletons"]
        for row in analysis["active_rows"]
    ):
        reasons.append("canonical inputs contain no singleton-only colors")
    return reasons


def observe_overrides(grid) -> dict:
    """Recover every declared exact axis from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "active_rows": len(analysis["active_rows"]),
        "scene_profile": _classify_profile(analysis),
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(sample_index: int) -> dict:
    phase = sample_index % len(SCHEDULE_PROFILES)
    if phase == 0:
        return {
            "grid_h": 10,
            "grid_w": 10,
            "active_rows": 5,
            "scene_profile": "canonical_rows",
        }
    return {"scene_profile": SCENE_PROFILES[phase]}


def _place_span(row: list[int], color: int, left: int, right: int, marks: int, rng) -> None:
    if right - left < 2:
        raise ValueError("a teaching span must leave room for an interior cell")
    interior = list(range(left + 1, right))
    max_marks = 2 + max(0, len(interior) - 1)
    marks = max(2, min(marks, max_marks))
    chosen = [left, right]
    if marks > 2:
        chosen.extend(rng.sample(interior, marks - 2))
    for col in chosen:
        row[col] = color


def _place_regular_span(row: list[int], color: int, rng, *, force_three: bool = False) -> None:
    width = len(row)
    left = rng.randint(1, width - 4)
    right = rng.randint(left + 2, width - 2)
    marks = 3 if force_three and right - left >= 3 else rng.choice((2, 3))
    _place_span(row, color, left, right, marks, rng)


def _palette_for(profile: str, active_rows: int, rng) -> list[int]:
    if profile == "canonical_rows":
        count = 2
    else:
        count = min(5, max(2, (active_rows + 2) // 2))
    return rng.sample(list(range(1, 10)), count)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    effective_overrides = dict(overrides)
    for axis, value in _scheduled_defaults(sample_index).items():
        effective_overrides.setdefault(axis, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_diff("grid_h", 8, 14)
    width = ctx.draw_int_diff("grid_w", 9, 14)
    active_rows = ctx.draw_int_diff("active_rows", 1, 5)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("layout")

    grid = full_grid(height, width, 0)
    if profile == "canonical_rows":
        start = rng.randint(0, height - active_rows)
        rows = list(range(start, start + active_rows))
    else:
        rows = sorted(rng.sample(range(height), active_rows))
    palette = _palette_for(profile, active_rows, rng)

    special_row = rows[0]
    for row_offset, row_index in enumerate(rows):
        row = grid[row_index]
        color = palette[row_offset % len(palette)]
        if profile == "canonical_rows":
            # Canonical inputs contain adjacent 2x2 anchor blocks as well as
            # sparse spans.  Reproduce that linked morphology without letting
            # the whole lesson collapse to an identity transformation.
            if active_rows >= 3 and row_offset in (0, 1):
                color = palette[0]
                center = width // 2
                row[center - 1] = color
                row[center] = color
            else:
                _place_regular_span(
                    row,
                    color,
                    rng,
                    force_three=(row_offset == min(2, active_rows - 1)),
                )
            continue
        if row_index != special_row:
            _place_regular_span(
                row,
                color,
                rng,
                force_three=False,
            )
            continue

        if profile == "mixed_disjoint":
            other = palette[(row_offset + 1) % len(palette)]
            if other == color:
                other = next(candidate for candidate in range(1, 10) if candidate != color)
            _place_span(row, color, 1, 3, 2, rng)
            _place_span(row, other, width - 4, width - 2, 3, rng)
        elif profile == "singleton_distractor":
            other = palette[(row_offset + 1) % len(palette)]
            if other == color:
                other = next(candidate for candidate in range(1, 10) if candidate != color)
            if rng.randrange(2) == 0:
                row[1] = other
                _place_span(row, color, 3, width - 2, 3, rng)
            else:
                _place_span(row, color, 1, width - 4, 3, rng)
                row[width - 2] = other
        elif profile == "edge_spans":
            if rng.randrange(2) == 0:
                _place_span(row, color, 0, rng.randint(3, width - 2), 3, rng)
            else:
                _place_span(row, color, rng.randint(1, width - 4), width - 1, 3, rng)
        else:  # guarded by draw_choice; keep a loud defensive failure
            raise AssertionError(f"unsupported scene_profile {profile!r}")

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != requested[axis]:
            raise AssertionError(
                f"axis {axis!r} requested {requested[axis]!r}, observed {observed[axis]!r}"
            )
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    output = copy.deepcopy(grid)
    for row_index, row in enumerate(grid):
        colors: list[int] = []
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)
        positions = {
            color: [col for col, value in enumerate(row) if value == color]
            for color in colors
        }
        for col, value in enumerate(row):
            if value != 0:
                continue
            for color in colors:
                cols = positions[color]
                if min(cols) < col < max(cols):
                    output[row_index][col] = color
                    break
    return output


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return copy.deepcopy(grid)


def _rival_exactly_two_anchors(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append(col)
        for color, cols in positions.items():
            if len(cols) != 2:
                continue
            for col in range(cols[0] + 1, cols[-1]):
                if row[col] == 0:
                    output[row_index][col] = color
    return output


def _rival_global_row_span(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    for row_index, row in enumerate(grid):
        anchors = [(col, value) for col, value in enumerate(row) if value != 0]
        if len(anchors) < 2:
            continue
        left, right = anchors[0][0], anchors[-1][0]
        color = anchors[0][1]
        for col in range(left + 1, right):
            if row[col] == 0:
                output[row_index][col] = color
    return output


def _rival_expand_singletons(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append(col)
        all_anchors = sorted(col for cols in positions.values() for col in cols)
        for color, cols in positions.items():
            if len(cols) != 1:
                continue
            start = cols[0]
            others = [col for col in all_anchors if col != start]
            if not others:
                continue
            end = min(others, key=lambda col: (abs(col - start), col))
            for col in range(min(start, end) + 1, max(start, end)):
                if row[col] == 0:
                    output[row_index][col] = color
    return output


def _rival_interior_spans_only(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append(col)
        for color, cols in positions.items():
            if len(cols) < 2 or min(cols) == 0 or max(cols) == width - 1:
                continue
            for col in range(min(cols) + 1, max(cols)):
                if row[col] == 0:
                    output[row_index][col] = color
    return output


def _witness_nontrivial(grid) -> bool:
    return rule_mirror(grid) != grid


def _witness_three_plus(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and any(
            len(cols) >= 3
            for row in analysis["active_rows"]
            for cols in analysis["row_facts"][row]["repeated"].values()
        )
        and _rival_exactly_two_anchors(grid) != rule_mirror(grid)
    )


def _witness_mixed(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and _classify_profile(analysis) == "mixed_disjoint"
        and _rival_global_row_span(grid) != rule_mirror(grid)
    )


def _witness_singleton(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and _classify_profile(analysis) == "singleton_distractor"
        and _rival_expand_singletons(grid) != rule_mirror(grid)
    )


def _witness_edge(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and _classify_profile(analysis) == "edge_spans"
        and _rival_interior_spans_only(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "nontrivial_zero_fill": _witness_nontrivial,
    "three_plus_anchors_refute_exactly_two": _witness_three_plus,
    "mixed_colors_same_row": _witness_mixed,
    "singleton_color_creates_no_span": _witness_singleton,
    "edge_touching_span_is_lawful": _witness_edge,
}

SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "exactly_two_anchors_only": _rival_exactly_two_anchors,
    "one_global_span_per_row": _rival_global_row_span,
    "expand_singletons_to_nearest_anchor": _rival_expand_singletons,
    "interior_spans_only": _rival_interior_spans_only,
}

WITNESS_RIVALS = {
    "nontrivial_zero_fill": ["identity"],
    "three_plus_anchors_refute_exactly_two": ["exactly_two_anchors_only"],
    "mixed_colors_same_row": ["one_global_span_per_row"],
    "singleton_color_creates_no_span": ["expand_singletons_to_nearest_anchor"],
    "edge_touching_span_is_lawful": ["interior_spans_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "exactly_two_anchors_only": _rival_exactly_two_anchors,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival survives all demos but changes the query."""
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
    """Named malformed/rule-hiding inputs the structural checker must reject."""
    fixtures: list[tuple[str, list[list[int]]]] = []

    fixtures.append(("all_background", full_grid(8, 9, 0)))

    adjacent = full_grid(8, 9, 0)
    adjacent[3][3] = adjacent[3][4] = 2
    fixtures.append(("adjacent_pair_identity", adjacent))

    solid = full_grid(8, 9, 0)
    for row in (3, 4):
        solid[row][2:5] = [3, 3, 3]
    fixtures.append(("solid_rectangle_identity", solid))

    overlap = full_grid(8, 9, 0)
    overlap[3][1] = overlap[3][6] = 2
    overlap[3][3] = overlap[3][7] = 4
    fixtures.append(("overlapping_color_spans", overlap))

    singleton_only = full_grid(8, 9, 0)
    singleton_only[2][2] = 5
    singleton_only[4][6] = 7
    fixtures.append(("singleton_only_rows", singleton_only))

    bad_palette = generate(31337, 1)
    bad_palette[0][0] = 10
    fixtures.append(("non_arc_color", bad_palette))

    return fixtures
