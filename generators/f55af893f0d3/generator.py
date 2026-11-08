"""Generator for arc_additional_puzzle_bank_volume10:E68.

A connected orange motif left of a full-height magenta divider is reflected
across that divider.  The reflected cells are painted cyan while the input is
otherwise preserved.  Multi-colour decorations on both sides are distractors:
only orange is reflected.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f55af893f0d3"
TASK_ID = "f55af893f0d3"
VERSION = "3.0.0"
RULE_HASH = "ed8c541c1cad"

SUMMARY = (
    "A 0-background grid contains exactly one full-height magenta (6) "
    "divider, one connected asymmetric orange (7) motif entirely to its "
    "left, and non-orange decorations on both sides. Mirror every orange "
    "cell across the divider and paint the empty reflected location cyan "
    "(8). Preserve the divider, source motif, background, and all decorations."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is 0 and the input contains no cyan 8",
    "there is exactly one full-height magenta divider column and no other 6",
    "the orange source is one 4-connected asymmetric motif left of the divider",
    "every orange reflection is in bounds and initially empty",
    "at least two non-orange decoration colours occur on both sides",
    "an in-bounds left decoration has an empty mirror, rebutting reflect-all shortcuts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..12",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 13..18",
        "valid": "13..18",
    },
    "divider_col": {
        "type": "int",
        "default": "keyed draw 5..8",
        "valid": "5..8",
    },
    "motif_cells": {
        "type": "int",
        "default": "difficulty-aware 3..8",
        "valid": "3..8",
    },
    "n_decor_cells": {
        "type": "int",
        "default": "difficulty-aware 8..16",
        "valid": "8..16",
    },
    "n_decor_colors": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DECOR_COLORS = (1, 2, 3, 4, 5, 9)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _horizontal_reflection(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    width = max(col for _, col in cells) + 1
    return _normalize((row, width - 1 - col) for row, col in cells)


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for drow, dcol in _DIR4:
            nxt = row + drow, col + dcol
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen) == len(cells)


def _grow_asymmetric_motif(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Return a compact 4-connected motif that differs from its h-flip."""
    for _ in range(256):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = sorted(
                {
                    (row + drow, col + dcol)
                    for row, col in cells
                    for drow, dcol in _DIR4
                    if (row + drow, col + dcol) not in cells
                }
            )
            cells.add(rng.choice(frontier))
        normalized = _normalize(cells)
        height = max(row for row, _ in normalized) + 1
        width = max(col for _, col in normalized) + 1
        if (
            height >= 2
            and width >= 2
            and width <= 4
            and height <= 6
            and normalized != _horizontal_reflection(normalized)
        ):
            return normalized
    # Deterministic fallback families, all connected and horizontally asymmetric.
    fallback = {
        3: ((0, 0), (1, 0), (1, 1)),
        4: ((0, 0), (1, 0), (1, 1), (2, 0)),
        5: ((0, 0), (1, 0), (1, 1), (2, 0), (3, 0)),
        6: ((0, 0), (1, 0), (1, 1), (2, 0), (3, 0), (3, 1)),
        7: ((0, 0), (1, 0), (1, 1), (2, 0), (3, 0), (3, 1), (4, 0)),
        8: ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (4, 0), (4, 1)),
    }
    return fallback[size]


def _component(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    if not cells:
        return set()
    start = min(cells)
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for drow, dcol in _DIR4:
            nxt = row + drow, col + dcol
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
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
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
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
        if all(grid[row][col] == 6 for row in range(height))
    ]
    if len(divider_columns) != 1:
        errors.append(
            f"expected exactly one full-height colour-6 divider, got {divider_columns}"
        )
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "palette": palette,
        }
    divider = divider_columns[0]
    stray_sixes = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 6 and col != divider
    ]
    if stray_sixes:
        errors.append(f"colour 6 occurs outside the divider: {stray_sixes[:4]}")

    orange = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    if not 3 <= len(orange) <= 8:
        errors.append(f"orange motif must contain 3-8 cells, got {len(orange)}")
    if orange and _component(orange) != orange:
        errors.append("orange motif is not one 4-connected component")
    if any(col >= divider for _, col in orange):
        errors.append("every orange source cell must lie left of the divider")

    normalized_orange: tuple[tuple[int, int], ...] = ()
    if orange:
        normalized_orange = _normalize(orange)
        rows = {row for row, _ in normalized_orange}
        cols = {col for _, col in normalized_orange}
        if len(rows) < 2 or len(cols) < 2:
            errors.append("orange motif must span at least two rows and two columns")
        if normalized_orange == _horizontal_reflection(normalized_orange):
            errors.append("orange motif is horizontally symmetric and hides reflection")

    mirror_cells: set[tuple[int, int]] = set()
    for row, col in orange:
        target = row, 2 * divider - col
        if not (0 <= target[1] < width):
            errors.append(f"orange reflection is out of bounds at {target}")
            continue
        mirror_cells.add(target)
        if grid[target[0]][target[1]] != 0:
            errors.append(
                f"orange reflection target {target} is not empty "
                f"(found {grid[target[0]][target[1]]})"
            )

    decoration = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 6, 7, 8)
    ]
    decoration_colors = {value for _, _, value in decoration}
    if not 2 <= len(decoration_colors) <= 6:
        errors.append(
            "expected at least two non-orange decoration colours, got "
            f"{sorted(decoration_colors)}"
        )
    left_decor = [(r, c, v) for r, c, v in decoration if c < divider]
    right_decor = [(r, c, v) for r, c, v in decoration if c > divider]
    if not left_decor or not right_decor:
        errors.append("decorations must occur on both sides of the divider")

    left_selectivity = []
    for row, col, value in left_decor:
        target_col = 2 * divider - col
        if 0 <= target_col < width and grid[row][target_col] == 0:
            left_selectivity.append((row, col, value, target_col))

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "divider": divider,
        "orange": orange,
        "normalized_orange": normalized_orange,
        "mirror_cells": mirror_cells,
        "decoration": decoration,
        "decoration_colors": decoration_colors,
        "left_decor": left_decor,
        "right_decor": right_decor,
        "left_selectivity": left_selectivity,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and exact-axis drift."""
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
    """Recover every declared exact axis directly from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "divider_col": analysis["divider"],
        "motif_cells": len(analysis["orange"]),
        "n_decor_cells": len(analysis["decoration"]),
        "n_decor_colors": len(analysis["decoration_colors"]),
    }


def rule_mirror(grid):
    """Independent Python oracle for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    structural_errors = [
        reason
        for reason in analysis["errors"]
        if not reason.startswith("orange motif is horizontally symmetric")
        and not reason.startswith("decorations must occur")
        and not reason.startswith("expected at least two non-orange")
    ]
    if structural_errors:
        raise ValueError("invalid mirror scene: " + "; ".join(structural_errors))
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row, col in analysis["orange"]:
        target_col = 2 * divider - col
        if 0 <= target_col < analysis["width"] and output[row][target_col] == 0:
            output[row][target_col] = 8
    return output


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if not 9 <= analysis["height"] <= 12:
        reasons.append("height is outside the canonical 9-12 teaching envelope")
    if not 13 <= analysis["width"] <= 18:
        reasons.append("width is outside the canonical 13-18 teaching envelope")
    if not 5 <= len(analysis["palette"]) <= 7:
        reasons.append("input palette should contain 5-7 colours")
    return reasons


def _witness_asymmetric_source(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and (
        analysis["normalized_orange"]
        != _horizontal_reflection(analysis["normalized_orange"])
    )


def _witness_multiple_mirror_distances(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len({col for _, col in analysis["orange"]}) >= 2


def _witness_bilateral_distractors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(
        analysis["left_decor"] and analysis["right_decor"]
    )


def _witness_only_orange_reflects(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["left_selectivity"])


SEMANTIC_WITNESSES = {
    "asymmetric_orange_source": _witness_asymmetric_source,
    "orange_spans_multiple_reflection_distances": _witness_multiple_mirror_distances,
    "decorations_on_both_sides": _witness_bilateral_distractors,
    "left_distractor_with_empty_mirror_rebuts_reflect_all": _witness_only_orange_reflects,
}


def _competitor_reflect_all_colours(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row in range(analysis["height"]):
        for col in range(divider):
            value = grid[row][col]
            target_col = 2 * divider - col
            if (
                value not in (0, 6)
                and 0 <= target_col < analysis["width"]
                and output[row][target_col] == 0
            ):
                output[row][target_col] = 8
    return output


def _competitor_translate_without_flipping(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    min_col = min(col for _, col in analysis["orange"])
    shift = analysis["divider"] + 1 - min_col
    for row, col in analysis["orange"]:
        target_col = col + shift
        if 0 <= target_col < analysis["width"] and output[row][target_col] == 0:
            output[row][target_col] = 8
    return output


def _competitor_recolour_source_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    for row, col in analysis["orange"]:
        output[row][col] = 8
    return output


_LESSON_COMPETITORS = {
    "reflect every coloured cell on the left": _competitor_reflect_all_colours,
    "translate the orange shape without horizontal reflection": _competitor_translate_without_flipping,
    "recolour the source orange cells instead of adding a copy": _competitor_recolour_source_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut survives all demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the divider-reflection rule")
    query_input = query["input"]
    query_answer = rule_mirror(query_input)
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the divider-reflection rule")
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query_input) != query_answer:
            reasons.append(
                f"demonstrations remain consistent with shortcut: {name}"
            )
    return reasons


def _allocate_counts(total: int, groups: int, rng) -> list[int]:
    counts = [2] * groups
    for _ in range(total - 2 * groups):
        counts[rng.randrange(groups)] += 1
    return counts


def _grow_decoration(
    grid: list[list[int]],
    *,
    color: int,
    count: int,
    anchor: tuple[int, int],
    divider: int,
    side: str,
    forbidden: set[tuple[int, int]],
    rng,
) -> None:
    height, width = len(grid), len(grid[0])

    cells: set[tuple[int, int]] = set()

    def legal(cell: tuple[int, int]) -> bool:
        row, col = cell
        return (
            0 <= row < height
            and 0 <= col < width
            and grid[row][col] == 0
            and cell not in cells
            and cell not in forbidden
            and ((side == "left" and col < divider) or (side == "right" and col > divider))
        )

    if not legal(anchor):
        raise ValueError(f"decoration anchor {anchor} is not available")
    cells.add(anchor)
    while len(cells) < count:
        frontier = sorted(
            {
                (row + drow, col + dcol)
                for row, col in cells
                for drow, dcol in _DIR4
                if legal((row + drow, col + dcol))
            }
        )
        if frontier:
            cells.add(rng.choice(frontier))
            continue
        fallback = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if legal((row, col))
        ]
        if not fallback:
            raise ValueError("insufficient space for requested decoration cells")
        fallback.sort(
            key=lambda cell: (
                abs(cell[0] - anchor[0]) + abs(cell[1] - anchor[1]),
                cell,
            )
        )
        cells.add(fallback[0])
    for row, col in cells:
        grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 9, 12)
    width = ctx.draw_int_diff("grid_w", 13, 18)
    divider = ctx.draw_int("divider_col", 5, 8)
    motif_count = ctx.draw_int_diff("motif_cells", 3, 8)
    decor_count = ctx.draw_int_diff("n_decor_cells", 8, 16)
    decor_color_count = ctx.draw_int_diff("n_decor_colors", 2, 4)

    motif_rng = ctx.draw_rng("motif-shape")
    placement_rng = ctx.draw_rng("motif-placement")
    decor_rng = ctx.draw_rng("decoration-layout")
    palette_rng = ctx.draw_rng("decoration-palette")

    motif_shape = _grow_asymmetric_motif(motif_rng, motif_count)
    motif_height = max(row for row, _ in motif_shape) + 1
    motif_width = max(col for _, col in motif_shape) + 1
    left_min = max(0, 2 * divider - (width - 1))
    left_max = divider - motif_width
    if left_max < left_min:
        raise ValueError(
            "divider/grid/motif override combination leaves no mirrorable source placement"
        )

    schedule = sample_index % 4
    if schedule == 0:
        motif_left = left_max
        motif_top = 0
    elif schedule == 1:
        motif_left = left_min
        motif_top = height - motif_height
    elif schedule == 2:
        motif_left = left_max
        motif_top = height - motif_height
    else:
        motif_left = placement_rng.randint(left_min, left_max)
        motif_top = placement_rng.randint(0, height - motif_height)

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 6
    orange = {
        (motif_top + row, motif_left + col) for row, col in motif_shape
    }
    for row, col in orange:
        grid[row][col] = 7
    mirror_cells = {(row, 2 * divider - col) for row, col in orange}

    left_witness_candidates = [
        (row, col)
        for row in range(height)
        for col in range(divider)
        if grid[row][col] == 0
        and (row, col) not in mirror_cells
        and 0 <= 2 * divider - col < width
        and grid[row][2 * divider - col] == 0
        and (row, 2 * divider - col) not in mirror_cells
    ]
    if not left_witness_candidates:
        raise ValueError("no lawful left-side selectivity witness placement")
    left_anchor = decor_rng.choice(left_witness_candidates)
    protected_blank = (left_anchor[0], 2 * divider - left_anchor[1])

    right_candidates = [
        (row, col)
        for row in range(height)
        for col in range(divider + 1, width)
        if grid[row][col] == 0
        and (row, col) not in mirror_cells
        and (row, col) != protected_blank
    ]
    if not right_candidates:
        raise ValueError("no lawful right-side decoration placement")
    right_anchor = decor_rng.choice(right_candidates)

    colors = list(_DECOR_COLORS)
    palette_rng.shuffle(colors)
    colors = colors[:decor_color_count]
    counts = _allocate_counts(decor_count, decor_color_count, decor_rng)
    forbidden = set(mirror_cells) | {protected_blank}

    anchors: list[tuple[int, int]] = [left_anchor, right_anchor]
    sides = ["left", "right"]
    for index in range(2, decor_color_count):
        side = "left" if index % 2 == 0 else "right"
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 0
            and (row, col) not in forbidden
            and (row, col) not in set(anchors)
            and ((side == "left" and col < divider) or (side == "right" and col > divider))
        ]
        if not candidates:
            raise ValueError("insufficient space for decoration colour anchors")
        anchors.append(decor_rng.choice(candidates))
        sides.append(side)

    reserved_anchors = set(anchors)
    for color, count, anchor, side in zip(colors, counts, anchors, sides):
        _grow_decoration(
            grid,
            color=color,
            count=count,
            anchor=anchor,
            divider=divider,
            side=side,
            forbidden=forbidden | (reserved_anchors - {anchor}),
            rng=decor_rng,
        )

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generator invariant failure: " + "; ".join(errors))
    return grid
