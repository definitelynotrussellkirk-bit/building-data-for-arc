"""Generator for arc_additional_puzzle_bank_volume21:E145.

A connected blue motif lies left of a full-height maroon divider.  Reflect the
blue motif across that divider, painting the reflected cells cyan.  Existing
non-blue decorations are preserved unless they occupy a reflected target; a
cyan reflected cell overwrites such a decoration, matching the canonical rule.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a6b5a6d9b5ef"
TASK_ID = "a6b5a6d9b5ef"
VERSION = "2.0.0"
RULE_HASH = "ad8d431b217a"

SUMMARY = (
    "A 0-background grid contains exactly one full-height maroon (9) divider, "
    "one connected blue (1) motif entirely to its left, and non-blue coloured "
    "decorations. Reflect every blue cell across the divider and paint the "
    "reflected destination cyan (8), overwriting a decoration when it occupies "
    "that destination. Preserve the source motif, divider, background, and all "
    "decorations outside blue reflection targets."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is 0 and cyan 8 is absent from the input",
    "there is exactly one full-height maroon 9 divider and no stray maroon",
    "blue 1 cells form one connected motif entirely left of the divider",
    "the blue motif spans multiple rows and reflection distances",
    "every blue reflection target is in bounds and off the divider",
    "non-blue decorations are ignored except when a blue reflection overwrites them",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped 8..18",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped 11..20",
        "valid": "11..20",
    },
    "divider_col": {
        "type": "int",
        "default": "keyed off-centre draw 4..8",
        "valid": "4..8",
    },
    "n_blue": {
        "type": "int",
        "default": "difficulty-shaped 3..10",
        "valid": "3..10",
    },
    "n_distractors": {
        "type": "int",
        "default": "difficulty-shaped 4..12",
        "valid": "4..12",
    },
    "n_distractor_colors": {
        "type": "int",
        "default": "difficulty-shaped 1..3",
        "valid": "1..3",
    },
    "n_target_collisions": {
        "type": "int",
        "default": "difficulty-shaped 1..2",
        "valid": "1..2",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DISTRACTOR_COLORS = (2, 3, 4, 5, 6, 7)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _horizontal_reflection(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    if not normalized:
        return ()
    width = max(col for _, col in normalized) + 1
    return _normalize((row, width - 1 - col) for row, col in normalized)


def _component(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    if not cells:
        return set()
    start = min(cells)
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for drow, dcol in _DIR4:
            neighbor = row + drow, col + dcol
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colours 0..9")

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background colour 0 is absent")
    if 8 in palette:
        errors.append("input must not contain cyan 8")

    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(divider_columns) != 1:
        errors.append(
            f"expected exactly one full-height maroon divider, got {divider_columns}"
        )
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "palette": palette,
        }
    divider = divider_columns[0]
    stray_maroon = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9 and col != divider
    ]
    if stray_maroon:
        errors.append(f"maroon 9 occurs outside the divider: {stray_maroon[:4]}")

    blue = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    if not blue:
        errors.append("blue source motif is absent")
    if blue and _component(blue) != blue:
        errors.append("blue source cells must form one 4-connected motif")
    if any(col >= divider for _, col in blue):
        errors.append("every blue source cell must lie left of the divider")
    if blue and len({row for row, _ in blue}) < 2:
        errors.append("blue source motif must span at least two rows")
    if blue and len({col for _, col in blue}) < 2:
        errors.append("blue source motif must span at least two columns")

    mirror_cells: set[tuple[int, int]] = set()
    for row, col in blue:
        target_col = 2 * divider - col
        if not 0 <= target_col < width:
            errors.append(f"blue reflection is out of bounds at {(row, target_col)}")
            continue
        if target_col == divider:
            errors.append("blue reflection target may not be the divider")
            continue
        mirror_cells.add((row, target_col))

    distractors = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 1, 8, 9)
    ]
    if not distractors:
        errors.append("at least one non-blue decoration is required")
    distractor_colors = {value for _, _, value in distractors}
    left_distractors = [item for item in distractors if item[1] < divider]
    right_distractors = [item for item in distractors if item[1] > divider]
    target_collisions = [
        item for item in distractors if (item[0], item[1]) in mirror_cells
    ]
    left_selectivity = []
    for row, col, value in left_distractors:
        target_col = 2 * divider - col
        if (
            0 <= target_col < width
            and (row, target_col) not in mirror_cells
            and grid[row][target_col] == 0
        ):
            left_selectivity.append((row, col, value, target_col))

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "divider": divider,
        "blue": blue,
        "normalized_blue": _normalize(blue),
        "mirror_cells": mirror_cells,
        "distractors": distractors,
        "distractor_colors": distractor_colors,
        "left_distractors": left_distractors,
        "right_distractors": right_distractors,
        "target_collisions": target_collisions,
        "left_selectivity": left_selectivity,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed rule-hiding scenes while accepting all canonical inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in observed and observed[name] != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed[name]!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from a returned lawful grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "divider_col": analysis["divider"],
        "n_blue": len(analysis["blue"]),
        "n_distractors": len(analysis["distractors"]),
        "n_distractor_colors": len(analysis["distractor_colors"]),
        "n_target_collisions": len(analysis["target_collisions"]),
    }


def rule_mirror(grid):
    """Independent Python test oracle; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid divider-reflection scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row, col in analysis["blue"]:
        output[row][2 * divider - col] = 8
    return output


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if not 8 <= analysis["height"] <= 18:
        reasons.append("height is outside the canonical teaching envelope 8..18")
    if not 11 <= analysis["width"] <= 20:
        reasons.append("width is outside the canonical teaching envelope 11..20")
    if not 4 <= analysis["divider"] <= 8:
        reasons.append("divider is outside the canonical teaching envelope 4..8")
    if not 3 <= len(analysis["blue"]) <= 10:
        reasons.append("blue motif size is outside the teaching envelope 3..10")
    if not 3 <= len(analysis["distractors"]) <= 12:
        reasons.append("decoration count is outside the teaching envelope 3..12")
    return reasons


def _witness_cyan_reflection(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["blue"])


def _witness_asymmetric_multiple_distances(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and (
        len({col for _, col in analysis["blue"]}) >= 2
        and analysis["normalized_blue"]
        != _horizontal_reflection(analysis["normalized_blue"])
    )


def _witness_bilateral_selectivity(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(
        analysis["left_distractors"]
        and analysis["right_distractors"]
        and analysis["left_selectivity"]
    )


def _witness_target_collision(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["target_collisions"])


def _witness_grid_center_rule_disagrees(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and 2 * analysis["divider"] != analysis["width"] - 1
        and _rival_grid_center_reflection(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "blue_reflection_is_added_as_cyan": _witness_cyan_reflection,
    "asymmetric_source_spans_multiple_reflection_distances": _witness_asymmetric_multiple_distances,
    "bilateral_distractors_include_left_selectivity_counterexample": _witness_bilateral_selectivity,
    "occupied_reflection_target_is_overwritten": _witness_target_collision,
    "off_center_divider_changes_answer_vs_grid_center": _witness_grid_center_rule_disagrees,
}


def _rival_same_color_reflection(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row, col in analysis["blue"]:
        output[row][2 * divider - col] = 1
    return output


def _rival_reflect_all_nonbackground(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row in range(analysis["height"]):
        for col in range(divider):
            if grid[row][col] in (0, 9):
                continue
            target_col = 2 * divider - col
            if 0 <= target_col < analysis["width"]:
                output[row][target_col] = 8
    return output


def _rival_translate_without_reflection(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    min_col = min(col for _, col in analysis["blue"])
    shift = analysis["divider"] + 1 - min_col
    for row, col in analysis["blue"]:
        target_col = col + shift
        if 0 <= target_col < analysis["width"]:
            output[row][target_col] = 8
    return output


def _rival_grid_center_reflection(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    center = (analysis["width"] - 1) // 2
    for row, col in analysis["blue"]:
        target_col = 2 * center - col
        if 0 <= target_col < analysis["width"] and target_col != center:
            output[row][target_col] = 8
    return output


def _rival_recolor_source_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    for row, col in analysis["blue"]:
        output[row][col] = 8
    return output


def _rival_reflect_only_into_empty(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row, col in analysis["blue"]:
        target_col = 2 * divider - col
        if output[row][target_col] == 0:
            output[row][target_col] = 8
    return output


SEMANTIC_RIVALS = {
    "same_color_reflection": _rival_same_color_reflection,
    "reflect_every_nonbackground_left_cell": _rival_reflect_all_nonbackground,
    "translate_without_horizontal_reflection": _rival_translate_without_reflection,
    "reflect_across_grid_center": _rival_grid_center_reflection,
    "recolor_source_only": _rival_recolor_source_only,
    "reflect_only_into_empty_targets": _rival_reflect_only_into_empty,
}

WITNESS_RIVALS = {
    "blue_reflection_is_added_as_cyan": [
        "same_color_reflection",
        "recolor_source_only",
    ],
    "asymmetric_source_spans_multiple_reflection_distances": [
        "translate_without_horizontal_reflection",
    ],
    "bilateral_distractors_include_left_selectivity_counterexample": [
        "reflect_every_nonbackground_left_cell",
    ],
    "occupied_reflection_target_is_overwritten": [
        "reflect_only_into_empty_targets",
    ],
    "off_center_divider_changes_answer_vs_grid_center": [
        "reflect_across_grid_center",
    ],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "reflect_across_grid_center": _rival_grid_center_reflection,
    "reflect_only_into_empty_targets": _rival_reflect_only_into_empty,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible wrong rule survives the demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(
                f"demo {index} output does not match blue divider reflection"
            )
    query_input = query["input"]
    query_answer = rule_mirror(query_input)
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match blue divider reflection")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query_input) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _grow_blue_motif(
    rng,
    *,
    height: int,
    source_columns: tuple[int, ...],
    count: int,
) -> set[tuple[int, int]]:
    allowed = {
        (row, col)
        for row in range(height)
        for col in source_columns
    }
    for _ in range(512):
        cells = {rng.choice(sorted(allowed))}
        while len(cells) < count:
            frontier = sorted(
                {
                    (row + drow, col + dcol)
                    for row, col in cells
                    for drow, dcol in _DIR4
                    if (row + drow, col + dcol) in allowed
                    and (row + drow, col + dcol) not in cells
                }
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != count:
            continue
        normalized = _normalize(cells)
        if (
            len({row for row, _ in cells}) >= 2
            and len({col for _, col in cells}) >= 2
            and normalized != _horizontal_reflection(normalized)
        ):
            return cells
    raise ValueError("could not construct a connected asymmetric blue motif")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 8, 18)
    width = ctx.draw_int_diff("grid_w", 11, 20)
    if "divider_col" in overrides:
        divider = ctx.draw_int("divider_col", 4, 8)
    else:
        divider_options = tuple(
            col for col in range(4, 9) if 2 * col != width - 1
        )
        divider = ctx.draw_choice("divider_col", divider_options)
    n_blue = ctx.draw_int_diff("n_blue", 3, 10)
    n_distractors = ctx.draw_int_diff("n_distractors", 4, 12)
    n_distractor_colors = ctx.draw_int_diff("n_distractor_colors", 1, 3)
    n_target_collisions = ctx.draw_int_diff("n_target_collisions", 1, 2)

    source_columns = tuple(range(max(0, 2 * divider - (width - 1)), divider))
    if len(source_columns) < 2:
        raise ValueError("grid/divider combination leaves fewer than two reflection distances")

    motif_rng = ctx.draw_rng("blue-motif")
    placement_rng = ctx.draw_rng("decoration-placement")
    palette_rng = ctx.draw_rng("decoration-palette")
    blue = _grow_blue_motif(
        motif_rng,
        height=height,
        source_columns=source_columns,
        count=n_blue,
    )
    mirror_cells = {(row, 2 * divider - col) for row, col in blue}

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 9
    for row, col in blue:
        grid[row][col] = 1

    collision_positions = placement_rng.sample(
        sorted(mirror_cells), n_target_collisions
    )
    reserved = set(collision_positions)

    left_candidates = [
        (row, col)
        for row in range(height)
        for col in source_columns
        if grid[row][col] == 0
        and (row, col) not in reserved
        and (row, 2 * divider - col) not in mirror_cells
        and grid[row][2 * divider - col] == 0
    ]
    if not left_candidates:
        raise ValueError("no left-side selectivity witness placement is available")
    left_witness = placement_rng.choice(left_candidates)
    reserved.add(left_witness)
    protected_empty_mirror = (left_witness[0], 2 * divider - left_witness[1])

    right_candidates = [
        (row, col)
        for row in range(height)
        for col in range(divider + 1, width)
        if grid[row][col] == 0
        and (row, col) not in mirror_cells
        and (row, col) not in reserved
        and (row, col) != protected_empty_mirror
    ]
    if not right_candidates:
        raise ValueError("no right-side preserved decoration placement is available")
    right_witness = placement_rng.choice(right_candidates)
    reserved.add(right_witness)

    positions = list(collision_positions) + [left_witness, right_witness]
    remaining = n_distractors - len(positions)
    if remaining < 0:
        raise ValueError(
            "n_distractors must cover collisions plus bilateral selectivity witnesses"
        )
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
        and col != divider
        and (row, col) not in mirror_cells
        and (row, col) not in reserved
        and (row, col) != protected_empty_mirror
    ]
    if len(candidates) < remaining:
        raise ValueError("insufficient empty cells for requested decorations")
    positions.extend(placement_rng.sample(candidates, remaining))

    colors = list(_DISTRACTOR_COLORS)
    palette_rng.shuffle(colors)
    colors = colors[:n_distractor_colors]
    assignments = list(colors)
    while len(assignments) < len(positions):
        assignments.append(palette_rng.choice(colors))
    palette_rng.shuffle(assignments)
    for (row, col), color in zip(positions, assignments):
        grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generator invariant failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "divider_col": divider,
        "n_blue": n_blue,
        "n_distractors": n_distractors,
        "n_distractor_colors": n_distractor_colors,
        "n_target_collisions": n_target_collisions,
    }
    if observed != expected:
        raise ValueError(
            f"internal exact-axis mismatch: expected {expected}, observed {observed}"
        )
    if strict_canonical_like(grid):
        raise ValueError("internal generator produced a non-canonical-like scene")
    return grid
