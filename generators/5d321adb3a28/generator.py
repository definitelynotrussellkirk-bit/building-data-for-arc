"""Generator for arc_puzzle_bank_21_set18_bundle:easy_p07.

Fill a zero cell when its immediate horizontal or vertical neighbours are the
same nonzero color.  Every generated lesson includes three positive gaps in a
canonical 2:1 orientation split plus four nearby counterexamples: mismatched
horizontal and vertical endpoints and same-color horizontal and vertical spans
with two interior zeros.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d321adb3a28"
VERSION = "3.2.2"  # canonical target multiplicity plus shortcut declaration repair
TASK_ID = "5d321adb3a28"
RULE_HASH = "980e1ed5540b"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Fill each zero cell whose immediate left/right neighbours match and are "
    "nonzero; otherwise fill it when its immediate up/down neighbours match "
    "and are nonzero. Preserve every other cell. Generated lessons include "
    "both positive orientations, mismatched endpoints, and longer same-color "
    "spans that must remain unchanged. Each generated grid contains three "
    "fillable gaps, matching the canonical 2:1 horizontal/vertical profiles."
)

INVARIANTS = [
    "background is 0 and exactly three nonzero colors are used",
    "ordinary draws contain three fillable gaps in a 2h1v or 1h2v profile",
    "ordinary draws contain one mismatched and one long-gap control per orientation",
    "all motif endpoints are isolated from unintended relations",
    "every ordinary draw changes exactly three cells under the canonical rule",
]

SCENE_PROFILES = ("6x10", "7x8", "7x9", "8x8")
TARGET_RELATIONS = ("same", "different")
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng canonical profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "target_relation": {
        "type": "str",
        "default": "rng same|different",
        "valid": "|".join(TARGET_RELATIONS),
    },
}

_H_TARGET = "horizontal_target"
_V_TARGET = "vertical_target"
_H_MISMATCH = "horizontal_mismatch"
_V_MISMATCH = "vertical_mismatch"
_H_LONG = "horizontal_long_gap"
_V_LONG = "vertical_long_gap"
_TARGET_COUNT_PROFILES = ("2h1v", "1h2v")
_GENERATED_SIGNATURES = {
    "2h1v": Counter(
        {
            _H_TARGET: 2,
            _V_TARGET: 1,
            _H_MISMATCH: 1,
            _V_MISMATCH: 1,
            _H_LONG: 1,
            _V_LONG: 1,
        }
    ),
    "1h2v": Counter(
        {
            _H_TARGET: 1,
            _V_TARGET: 2,
            _H_MISMATCH: 1,
            _V_MISMATCH: 1,
            _H_LONG: 1,
            _V_LONG: 1,
        }
    ),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic, non-degenerate teaching input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    target_relation = ctx.draw_choice("target_relation", TARGET_RELATIONS)
    height, width = (int(part) for part in scene_profile.split("x"))
    rng = ctx.draw_rng(f"layout:{difficulty or 'unspecified'}")
    target_count_profile = rng.choice(_TARGET_COUNT_PROFILES)
    separate_control_lead = rng.choice((False, True))

    for _ in range(512):
        grid = _draw_scene(
            height,
            width,
            target_relation,
            target_count_profile,
            separate_control_lead,
            rng,
        )
        analysis = _analyze_grid(grid)
        if (
            analysis["counts"] == _GENERATED_SIGNATURES[target_count_profile]
            and not analysis["ambiguous_cells"]
            and not analysis["uncovered_cells"]
            and 6 <= _object_count(grid) <= 10
            and observe_overrides(grid)
            == {
                "scene_profile": scene_profile,
                "target_relation": target_relation,
            }
        ):
            return grid
    raise ValueError(
        "unable to place the complete lesson grammar without an unintended relation"
    )


def _draw_scene(
    height: int,
    width: int,
    target_relation: str,
    target_count_profile: str,
    separate_control_lead: bool,
    rng,
):
    """Draw seven relations as two compact, canonical-scale endpoint clusters.

    Adjacent same-color endpoints connect pairs of motifs without sharing a
    motif endpoint.  The result retains all decisive semantic relations while
    keeping the non-background object count in the canonical neighbourhood
    (normally seven or eight rather than fourteen isolated dots).
    """
    grid = full_grid(height, width, 0)

    # The duplicated target is adjacent to its same-orientation partner, so it
    # adds canonical target multiplicity without adding disconnected objects.
    horizontal_rows = 4 if target_count_profile == "2h1v" else 3
    vertical_columns = 4 if target_count_profile == "1h2v" else 3
    h_top = rng.randrange(height - horizontal_rows + 1)
    v_top = rng.randrange(height - 5)
    cluster_on_left = rng.choice((True, False))
    h_left = 0 if cluster_on_left else width - 6
    v_left = width - vertical_columns if cluster_on_left else 0

    color_a, color_b, color_c = rng.sample(range(1, 10), 3)
    vertical_target_color = color_a if target_relation == "same" else color_b
    horizontal_mismatch_lead = color_c if separate_control_lead else color_a
    vertical_mismatch_lead = (
        (color_b if vertical_target_color == color_a else color_a)
        if separate_control_lead
        else vertical_target_color
    )

    horizontal = [
        (((h_top, h_left), (h_top, h_left + 2)), (color_a, color_a)),
    ]
    next_horizontal_row = h_top + 1
    if target_count_profile == "2h1v":
        horizontal.append(
            (
                (
                    (next_horizontal_row, h_left),
                    (next_horizontal_row, h_left + 2),
                ),
                (color_a, color_a),
            )
        )
        next_horizontal_row += 1
    horizontal.extend(
        [
            (
                (
                    (next_horizontal_row, h_left),
                    (next_horizontal_row, h_left + 2),
                ),
                (horizontal_mismatch_lead, color_b),
            ),
            (
                (
                    (next_horizontal_row + 1, h_left + 2),
                    (next_horizontal_row + 1, h_left + 5),
                ),
                (color_b, color_b),
            ),
        ]
    )

    vertical = [
        (
            ((v_top, v_left), (v_top + 2, v_left)),
            (vertical_target_color, vertical_target_color),
        ),
    ]
    next_vertical_column = v_left + 1
    if target_count_profile == "1h2v":
        vertical.append(
            (
                (
                    (v_top, next_vertical_column),
                    (v_top + 2, next_vertical_column),
                ),
                (vertical_target_color, vertical_target_color),
            )
        )
        next_vertical_column += 1
    vertical.extend(
        [
            (
                (
                    (v_top, next_vertical_column),
                    (v_top + 2, next_vertical_column),
                ),
                (vertical_mismatch_lead, color_c),
            ),
            (
                (
                    (v_top + 2, next_vertical_column + 1),
                    (v_top + 5, next_vertical_column + 1),
                ),
                (color_c, color_c),
            ),
        ]
    )

    motifs = tuple(horizontal + vertical)
    if rng.choice((True, False)):
        motifs = tuple(reversed(motifs))
    for cells, colors in motifs:
        for (row, column), color in zip(cells, colors):
            if grid[row][column] not in (0, color):
                return grid
            grid[row][column] = color

    if rng.choice((True, False)):
        grid = list(reversed(grid))
    if rng.choice((True, False)):
        grid = [list(reversed(row)) for row in grid]
    return grid


def _object_count(grid) -> int:
    """Count same-color 4-connected nonzero components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    count = 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            count += 1
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            while stack:
                current_row, current_column = stack.pop()
                for drow, dcolumn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + drow
                    next_column = current_column + dcolumn
                    if not (0 <= next_row < height and 0 <= next_column < width):
                        continue
                    cell = (next_row, next_column)
                    if cell in seen or grid[next_row][next_column] != color:
                        continue
                    seen.add(cell)
                    stack.append(cell)
    return count


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze_grid(grid)
    horizontal_colors = analysis["colors"][_H_TARGET]
    vertical_colors = analysis["colors"][_V_TARGET]
    if len(set(horizontal_colors)) != 1 or len(set(vertical_colors)) != 1:
        raise ValueError("target_relation is not observable from this grid")
    return {
        "scene_profile": f"{len(grid)}x{len(grid[0])}",
        "target_relation": (
            "same" if horizontal_colors[0] == vertical_colors[0] else "different"
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons while accepting every canonical input."""
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors

    analysis = _analyze_grid(grid)
    errors.extend(_structural_errors(grid, analysis))

    requested = _requested_overrides(meta)
    if requested and not errors:
        observed = observe_overrides(grid)
        for key, value in requested.items():
            if key in AXES and observed.get(key) != value:
                errors.append(
                    f"{key} requested {value!r}, observed {observed.get(key)!r}"
                )
    return errors


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be ARC colors 0..9"]
    return []


def _requested_overrides(meta) -> dict:
    if not isinstance(meta, dict):
        return {}
    requested = dict(meta.get("overrides") or {})
    for key in AXES:
        if key in meta and key not in requested:
            requested[key] = meta[key]
    return requested


def _structural_errors(grid, analysis) -> list[str]:
    counts: Counter[str] = analysis["counts"]
    errors: list[str] = []
    if analysis["ambiguous_cells"]:
        errors.append(
            "motif endpoints participate in multiple relations: "
            f"{analysis['ambiguous_cells'][:6]}"
        )
    if analysis["uncovered_cells"]:
        errors.append(
            "nonzero cells outside the lesson grammar: "
            f"{analysis['uncovered_cells'][:6]}"
        )

    control_total = sum(
        counts[kind] for kind in (_H_MISMATCH, _V_MISMATCH, _H_LONG, _V_LONG)
    )
    pure_canonical = control_total == 0
    generated = any(counts == signature for signature in _GENERATED_SIGNATURES.values())
    if pure_canonical:
        if counts[_H_TARGET] < 1 or counts[_V_TARGET] < 1:
            errors.append(
                "canonical form must contain at least one horizontal and one vertical gap"
            )
    elif not generated:
        errors.append(
            "generated form must contain a 2h1v or 1h2v target profile plus exactly "
            "one mismatch and one long-gap motif per orientation"
        )

    palette = {value for row in grid for value in row}
    if generated and len(palette) != 4:
        errors.append(f"generated form must use background plus three colors; got {palette}")
    return errors


def _analyze_grid(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    motifs: list[tuple[str, tuple[tuple[int, int], ...], tuple[int, ...]]] = []

    for row in range(height):
        for column in range(1, width - 1):
            left = grid[row][column - 1]
            middle = grid[row][column]
            right = grid[row][column + 1]
            if middle == 0 and left != 0 and right != 0:
                kind = _H_TARGET if left == right else _H_MISMATCH
                motifs.append(
                    (kind, ((row, column - 1), (row, column + 1)), (left, right))
                )

    for row in range(1, height - 1):
        for column in range(width):
            above = grid[row - 1][column]
            middle = grid[row][column]
            below = grid[row + 1][column]
            if middle == 0 and above != 0 and below != 0:
                kind = _V_TARGET if above == below else _V_MISMATCH
                motifs.append(
                    (kind, ((row - 1, column), (row + 1, column)), (above, below))
                )

    for row in range(height):
        for column in range(width - 3):
            endpoint = grid[row][column]
            if (
                endpoint != 0
                and grid[row][column + 1] == 0
                and grid[row][column + 2] == 0
                and grid[row][column + 3] == endpoint
            ):
                motifs.append(
                    (
                        _H_LONG,
                        ((row, column), (row, column + 3)),
                        (endpoint, endpoint),
                    )
                )

    for row in range(height - 3):
        for column in range(width):
            endpoint = grid[row][column]
            if (
                endpoint != 0
                and grid[row + 1][column] == 0
                and grid[row + 2][column] == 0
                and grid[row + 3][column] == endpoint
            ):
                motifs.append(
                    (
                        _V_LONG,
                        ((row, column), (row + 3, column)),
                        (endpoint, endpoint),
                    )
                )

    memberships: Counter[tuple[int, int]] = Counter()
    colors: dict[str, list[int]] = {
        kind: []
        for kind in (
            _H_TARGET,
            _V_TARGET,
            _H_MISMATCH,
            _V_MISMATCH,
            _H_LONG,
            _V_LONG,
        )
    }
    for kind, cells, motif_colors in motifs:
        memberships.update(cells)
        colors[kind].append(motif_colors[0])
    nonzero = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    }
    return {
        "counts": Counter(kind for kind, _, _ in motifs),
        "motifs": motifs,
        "colors": colors,
        "ambiguous_cells": sorted(
            cell for cell, count in memberships.items() if count != 1
        ),
        "uncovered_cells": sorted(nonzero - set(memberships)),
    }


def rule_mirror(grid):
    """Input-pure Python mirror; the canonical Racket program is authority."""
    output = copy.deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 0:
                continue
            if (
                0 < column < width - 1
                and grid[row][column - 1] != 0
                and grid[row][column - 1] == grid[row][column + 1]
            ):
                output[row][column] = grid[row][column - 1]
            elif (
                0 < row < height - 1
                and grid[row - 1][column] != 0
                and grid[row - 1][column] == grid[row + 1][column]
            ):
                output[row][column] = grid[row - 1][column]
    return output


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------


def strict_canonical_like(grid) -> list[str]:
    """The repaired distribution stays entirely inside the task grammar."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def _has(kind: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: not self_check(grid) and _analyze_grid(grid)["counts"][kind] > 0


def _has_three_rule_changes(grid) -> bool:
    if self_check(grid):
        return False
    output = rule_mirror(grid)
    return sum(
        before != after
        for input_row, output_row in zip(grid, output)
        for before, after in zip(input_row, output_row)
    ) == 3


SEMANTIC_WITNESSES = {
    "horizontal_positive": _has(_H_TARGET),
    "vertical_positive": _has(_V_TARGET),
    "horizontal_mismatch_control": _has(_H_MISMATCH),
    "vertical_mismatch_control": _has(_V_MISMATCH),
    "horizontal_long_gap_control": _has(_H_LONG),
    "vertical_long_gap_control": _has(_V_LONG),
    "canonical_target_multiplicity": _has_three_rule_changes,
}


def _rival_horizontal_only(grid):
    output = copy.deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for column in range(1, width - 1):
            if (
                grid[row][column] == 0
                and grid[row][column - 1] != 0
                and grid[row][column - 1] == grid[row][column + 1]
            ):
                output[row][column] = grid[row][column - 1]
    return output


def _rival_vertical_only(grid):
    output = copy.deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(1, height - 1):
        for column in range(width):
            if (
                grid[row][column] == 0
                and grid[row - 1][column] != 0
                and grid[row - 1][column] == grid[row + 1][column]
            ):
                output[row][column] = grid[row - 1][column]
    return output


def _rival_ignore_endpoint_equality(grid):
    output = copy.deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 0:
                continue
            if (
                0 < column < width - 1
                and grid[row][column - 1] != 0
                and grid[row][column + 1] != 0
            ):
                output[row][column] = grid[row][column - 1]
            elif (
                0 < row < height - 1
                and grid[row - 1][column] != 0
                and grid[row + 1][column] != 0
            ):
                output[row][column] = grid[row - 1][column]
    return output


def _rival_fill_long_spans(grid):
    output = rule_mirror(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for left in range(width):
            color = grid[row][left]
            if color == 0:
                continue
            for right in range(left + 3, width):
                if grid[row][right] != color:
                    continue
                if all(grid[row][column] == 0 for column in range(left + 1, right)):
                    for column in range(left + 1, right):
                        output[row][column] = color
    for column in range(width):
        for top in range(height):
            color = grid[top][column]
            if color == 0:
                continue
            for bottom in range(top + 3, height):
                if grid[bottom][column] != color:
                    continue
                if all(grid[row][column] == 0 for row in range(top + 1, bottom)):
                    for row in range(top + 1, bottom):
                        output[row][column] = color
    return output


def _rival_two_change_cap(grid):
    """Distribution shortcut: apply at most two row-major canonical changes."""
    intended = rule_mirror(grid)
    output = copy.deepcopy(grid)
    changes_left = 2
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if changes_left and intended[row][column] != value:
                output[row][column] = intended[row][column]
                changes_left -= 1
    return output


SEMANTIC_RIVALS = {
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "ignore_endpoint_equality": _rival_ignore_endpoint_equality,
    "fill_arbitrary_distance_spans": _rival_fill_long_spans,
    "two_change_cap": _rival_two_change_cap,
}
WITNESS_RIVALS = {
    "horizontal_positive": ["vertical_only"],
    "vertical_positive": ["horizontal_only"],
    "horizontal_mismatch_control": ["ignore_endpoint_equality"],
    "vertical_mismatch_control": ["ignore_endpoint_equality"],
    "horizontal_long_gap_control": ["fill_arbitrary_distance_spans"],
    "vertical_long_gap_control": ["fill_arbitrary_distance_spans"],
    "canonical_target_multiplicity": ["two_change_cap"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "ignore_endpoint_equality",
        "fill_arbitrary_distance_spans",
    )
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson under which a named plausible wrong rule survives."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output disagrees with the canonical rule")

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if not survives:
            continue
        competitor_answer = competitor(query["input"])
        if competitor_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
        else:
            reasons.append(
                f"competing rule {name!r} is answer-equivalent across the lesson"
            )
    return reasons


def mutation_fixtures():
    """Return task-specific malformed near-misses that self_check must reject."""
    valid = generate(
        7001,
        2,
        difficulty="medium",
        scene_profile="7x9",
        target_relation="different",
    )
    analysis = _analyze_grid(valid)
    fixtures = []

    missing_endpoint = copy.deepcopy(valid)
    row, column = analysis["motifs"][0][1][0]
    missing_endpoint[row][column] = 0
    fixtures.append(("missing_target_endpoint", missing_endpoint))

    filled_target = copy.deepcopy(valid)
    target = next(item for item in analysis["motifs"] if item[0] == _H_TARGET)
    (row, left), (_, right) = target[1]
    filled_target[row][(left + right) // 2] = valid[row][left]
    fixtures.append(("pre_filled_target_gap", filled_target))

    mismatched_target = copy.deepcopy(valid)
    target = next(item for item in analysis["motifs"] if item[0] == _V_TARGET)
    (_, column), (bottom, _) = target[1]
    mismatched_target[bottom][column] = next(
        color
        for color in range(1, 10)
        if color != mismatched_target[target[1][0][0]][column]
    )
    fixtures.append(("target_endpoint_color_changed", mismatched_target))

    isolated = copy.deepcopy(valid)
    for row_index, values in enumerate(isolated):
        for column_index, value in enumerate(values):
            if value == 0:
                isolated[row_index][column_index] = 9
                if self_check(isolated):
                    fixtures.append(("isolated_nonzero_decoration", isolated))
                    return fixtures
                isolated[row_index][column_index] = 0
    raise AssertionError("could not construct isolated-cell mutation")
