"""Semantic generator for ARC task 0162460030af.

The input contains two or more separated foreground objects.  Sort objects by
leftmost column and recolor them 2, 8, 2, 8, ... when read from right to left;
equivalently, the rightmost object is always 8 and colors alternate leftward.

The default curriculum deliberately interleaves canonical 7-row, color-2,
solid-2x2 scenes with lawful shape/color generalizations.  Four consecutive
pairs remain identifiable under any three-demo/one-query rotation: they always
contain an even object count (which fixes the parity anchor) and a generalized
scene (which defeats color-2-only and 2x2-only shortcuts).
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0162460030af"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "617100877d72"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Two to nine separated nonzero objects are sorted by leftmost column and "
    "recolored with a right-anchored 2/8 alternation: the rightmost object is "
    "8, its left neighbor 2, and so on. Default lessons mix exact canonical "
    "2x2/color-2 profiles with shape and source-color counterexamples."
)
INVARIANTS = [
    "background is color 0",
    "2..9 nonzero 4-connected components have distinct leftmost columns",
    "each component is one supported connected shape in one source color",
    "grid height is 4..14 and width is at most 30",
    "default four-pair windows identify the right anchor and defeat canonical shortcuts",
]

SHAPE_OFFSETS = {
    "L": ((0, 0), (1, 0), (1, 1)),
    "vertical_2": ((0, 0), (1, 0)),
    "block_2x2": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "T": ((0, 0), (0, 1), (1, 0)),
    "s_shape": ((0, 1), (1, 0), (1, 1)),
    "single": ((0, 0),),
}
OBJECT_SHAPES = tuple(SHAPE_OFFSETS)
GENERALIZED_SHAPES = tuple(shape for shape in OBJECT_SHAPES if shape != "block_2x2")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "curriculum-weighted 4..14; canonical anchors use 7",
        "valid": "4..14",
    },
    "object_count": {
        "type": "int",
        "default": "curriculum-weighted 2..9 with alternating parity",
        "valid": "2..9",
    },
    "source_color": {
        "type": "color",
        "default": "canonical anchors use 2; generalized scenes use nonzero colors",
        "valid": "1..9",
    },
    "object_shape_kind": {
        "type": "str",
        "default": "canonical anchors use block_2x2; generalized scenes vary",
        "valid": "L|vertical_2|block_2x2|T|s_shape|single",
    },
    "column_spacing": {
        "type": "int",
        "default": "2 or 3 columns between successive left edges",
        "valid": "2..3",
    },
    "mixed_shapes": {
        "type": "bool",
        "default": "rng 0|1 outside canonical anchors",
        "valid": "0|1",
    },
    "mixed_colors": {
        "type": "bool",
        "default": "rng 0|1 outside canonical anchors",
        "valid": "0|1",
    },
}

_INT_AXES = {"grid_h", "object_count", "source_color", "column_spacing"}
_BOOL_AXES = {"mixed_shapes", "mixed_colors"}


def _validate_call(seed, sample_index) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coerced scalar)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool or a coerced scalar)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _validate_difficulty(difficulty) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    for name in _INT_AXES:
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
    for name in _BOOL_AXES:
        if (name in overrides and overrides[name] is not None
                and type(overrides[name]) not in (bool, int)):
            raise TypeError(f"override {name!r} must be False/True or 0/1")
    if "object_shape_kind" in overrides and overrides["object_shape_kind"] is not None:
        if not isinstance(overrides["object_shape_kind"], str):
            raise TypeError("override 'object_shape_kind' must be a string")


def _axis_choice(ctx, label: str, defaults: tuple, full_domain: tuple):
    """Use the full legal domain for explicit overrides, scheduled defaults otherwise."""
    explicit = label in ctx.overrides and ctx.overrides[label] is not None
    return ctx.draw_choice(label, full_domain if explicit else defaults)


def _band(difficulty) -> str:
    return difficulty if difficulty in {"easy", "medium", "hard"} else "medium"


def _canonical_profile(band: str, even_count: bool) -> tuple[int, int, int, int]:
    """Return (count, spacing, first_column, width), all exact canonical profiles."""
    if band == "easy":
        return (2, 3, 0, 5) if even_count else (3, 2, 0, 7)
    if band == "hard":
        return (6, 2, 1, 14) if even_count else (7, 2, 0, 15)
    return (6, 2, 1, 14) if even_count else (3, 2, 0, 7)


def _draw_axes(ctx, *, canonical_anchor: bool) -> dict[str, int | str]:
    band = _band(ctx.difficulty)
    even_count = ctx.sample_index % 2 == 0

    if canonical_anchor:
        count_default, spacing_default, _, _ = _canonical_profile(band, even_count)
        height_defaults = (7,)
        count_defaults = (count_default,)
        color_defaults = (2,)
        shape_defaults = ("block_2x2",)
        spacing_defaults = (spacing_default,)
        mixed_shape_defaults = (0,)
        mixed_color_defaults = (0,)
    else:
        height_defaults = {
            "easy": tuple(range(4, 8)),
            "medium": tuple(range(6, 11)),
            "hard": tuple(range(9, 15)),
        }[band]
        count_pool = {
            "easy": tuple(range(2, 6)),
            "medium": tuple(range(2, 8)),
            "hard": tuple(range(4, 10)),
        }[band]
        count_defaults = tuple(n for n in count_pool if (n % 2 == 0) == even_count)
        color_defaults = (1, 3, 4, 5, 6, 7, 8, 9)
        shape_defaults = GENERALIZED_SHAPES
        spacing_defaults = (2, 3)
        mixed_shape_defaults = (0, 1)
        mixed_color_defaults = (0, 1)

    return {
        "grid_h": _axis_choice(ctx, "grid_h", height_defaults, tuple(range(4, 15))),
        "object_count": _axis_choice(
            ctx, "object_count", count_defaults, tuple(range(2, 10))
        ),
        "source_color": _axis_choice(
            ctx, "source_color", color_defaults, tuple(range(1, 10))
        ),
        "object_shape_kind": _axis_choice(
            ctx, "object_shape_kind", shape_defaults, OBJECT_SHAPES
        ),
        "column_spacing": _axis_choice(
            ctx, "column_spacing", spacing_defaults, (2, 3)
        ),
        "mixed_shapes": _axis_choice(
            ctx, "mixed_shapes", mixed_shape_defaults, (0, 1)
        ),
        "mixed_colors": _axis_choice(
            ctx, "mixed_colors", mixed_color_defaults, (0, 1)
        ),
    }


def _component_cells(grid) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return sorted(components, key=lambda cells: min(c for _, c in cells))


def _normalized_shape(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    row0 = min(row for row, _ in cells)
    col0 = min(column for _, column in cells)
    return tuple(sorted((row - row0, column - col0) for row, column in cells))


_SHAPE_BY_CELLS = {tuple(sorted(offsets)): name for name, offsets in SHAPE_OFFSETS.items()}


def _shape_name(cells: list[tuple[int, int]]) -> str | None:
    return _SHAPE_BY_CELLS.get(_normalized_shape(cells))


def _validate_grid(grid: object) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generated input grammar and all canonical inputs."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 4 <= height <= 14:
        errors.append("height must be in 4..14")
    if not 3 <= width <= 30:
        errors.append("width must be in 3..30")

    components = _component_cells(grid)
    if not 2 <= len(components) <= 9:
        errors.append(f"expected 2..9 foreground components, got {len(components)}")
        return errors
    lefts = [min(column for _, column in cells) for cells in components]
    if len(set(lefts)) != len(lefts):
        errors.append("components must have distinct leftmost columns")
    for index, cells in enumerate(components):
        colors = {grid[row][column] for row, column in cells}
        if len(colors) != 1:
            errors.append(f"component {index} must use one source color")
        if _shape_name(cells) is None:
            errors.append(f"component {index} is not a supported shape")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 7-row, color-2, solid-2x2 task manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if len(grid) != 7:
        reasons.append("canonical inputs have height 7")
    if {value for row in grid for value in row} != {0, 2}:
        reasons.append("canonical inputs use exactly colors 0 and 2")
    components = _component_cells(grid)
    if any(_shape_name(cells) != "block_2x2" for cells in components):
        reasons.append("canonical objects are solid 2x2 blocks")
    return reasons


def _stamp(grid, shape: str, row0: int, col0: int, color: int) -> None:
    for dr, dc in SHAPE_OFFSETS[shape]:
        grid[row0 + dr][col0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index)
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Explicit overrides use the broad constructor.  Defaults reserve every
    # third accepted index for an exact canonical profile.
    canonical_anchor = not overrides and sample_index % 3 == 0
    axes = _draw_axes(ctx, canonical_anchor=canonical_anchor)
    height = int(axes["grid_h"])
    count = int(axes["object_count"])
    source_color = int(axes["source_color"])
    base_shape = str(axes["object_shape_kind"])
    spacing = int(axes["column_spacing"])
    mixed_shapes = bool(axes["mixed_shapes"])
    mixed_colors = bool(axes["mixed_colors"])
    rng = ctx.draw_rng("layout")

    if canonical_anchor:
        _, _, first_column, width = _canonical_profile(
            _band(difficulty), count % 2 == 0
        )
    else:
        first_column = rng.choice((0, 1))
        trailing = rng.choice((0, 1))
        width = first_column + (count - 1) * spacing + 2 + trailing
    if width > 30:
        raise AssertionError(f"constructed width {width} exceeds ARC limit")

    shapes = [base_shape]
    if mixed_shapes:
        alternatives = [shape for shape in OBJECT_SHAPES if shape != base_shape]
        shapes.extend(alternatives[(index - 1) % len(alternatives)] for index in range(1, count))
    else:
        shapes.extend(base_shape for _ in range(1, count))

    colors = [source_color]
    if mixed_colors:
        alternatives = [color for color in range(1, 10) if color != source_color]
        colors.extend(alternatives[(index - 1) % len(alternatives)] for index in range(1, count))
    else:
        colors.extend(source_color for _ in range(1, count))

    grid = full_grid(height, width, 0)
    row_pair = None
    if spacing == 2:
        # Width-two neighbors have touching columns.  Choose two disjoint
        # two-row bands from the seeded layout stream, then alternate them.
        row_pairs = [
            (first, second)
            for first in range(height - 1)
            for second in range(height - 1)
            if abs(first - second) >= 2
        ]
        row_pair = rng.choice(row_pairs)

    for index, (shape, color) in enumerate(zip(shapes, colors)):
        column = first_column + index * spacing
        if row_pair is not None:
            row = row_pair[index % 2]
        else:
            row = rng.randint(0, height - 2)
        _stamp(grid, shape, row, column, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"constructed invalid grid: {errors}")
    observed = observe_overrides(grid)
    for name, expected in axes.items():
        if observed[name] != expected:
            raise AssertionError(
                f"axis {name!r} realized as {observed[name]!r}, expected {expected!r}"
            )
    return grid


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every advertised semantic axis from a returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    components = _component_cells(grid)
    lefts = [min(column for _, column in cells) for cells in components]
    spacings = {right - left for left, right in zip(lefts, lefts[1:])}
    if len(spacings) != 1:
        raise ValueError("component left edges do not have constant spacing")
    shapes = [_shape_name(cells) for cells in components]
    colors = [grid[cells[0][0]][cells[0][1]] for cells in components]
    return {
        "grid_h": len(grid),
        "object_count": len(components),
        "source_color": colors[0],
        "object_shape_kind": shapes[0],
        "column_spacing": spacings.pop(),
        "mixed_shapes": len(set(shapes)) > 1,
        "mixed_colors": len(set(colors)) > 1,
    }


def _reference_output(grid: list[list[int]]) -> list[list[int]]:
    """Small Python mirror used only by semantic audits and focused tests."""
    output = deepcopy(grid)
    components = _component_cells(grid)
    count = len(components)
    for index, cells in enumerate(components):
        color = 8 if (count - index) % 2 == 1 else 2
        for row, column in cells:
            output[row][column] = color
    return output


def _rival_left_anchored_eight(grid):
    output = deepcopy(grid)
    for index, cells in enumerate(_component_cells(grid)):
        color = 8 if index % 2 == 0 else 2
        for row, column in cells:
            output[row][column] = color
    return output


def _rival_color_two_only(grid):
    foreground = {value for row in grid for value in row if value != 0}
    return _reference_output(grid) if foreground == {2} else deepcopy(grid)


def _rival_block_two_by_two_only(grid):
    components = _component_cells(grid)
    if components and all(_shape_name(cells) == "block_2x2" for cells in components):
        return _reference_output(grid)
    return deepcopy(grid)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "leftmost_is_8": _rival_left_anchored_eight,
    "only_color_2_objects_change": _rival_color_two_only,
    "only_solid_2x2_objects_change": _rival_block_two_by_two_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "only_color_2_objects_change": _rival_color_two_only,
    "only_solid_2x2_objects_change": _rival_block_two_by_two_only,
}


def _w_even_count(grid) -> bool:
    return _reference_output(grid) != _rival_left_anchored_eight(grid)


def _w_non_two_source(grid) -> bool:
    return _reference_output(grid) != _rival_color_two_only(grid)


def _w_non_block_shape(grid) -> bool:
    return _reference_output(grid) != _rival_block_two_by_two_only(grid)


SEMANTIC_WITNESSES = {
    "even_count_fixes_right_anchor": _w_even_count,
    "non_two_source_is_still_recolored": _w_non_two_source,
    "non_2x2_shape_is_still_recolored": _w_non_block_shape,
}
WITNESS_RIVALS = {
    "even_count_fixes_right_anchor": ["leftmost_is_8"],
    "non_two_source_is_still_recolored": ["only_color_2_objects_change"],
    "non_2x2_shape_is_still_recolored": ["only_solid_2x2_objects_change"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        if _reference_output(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")
    if not isinstance(query, dict) or "input" not in query:
        return reasons + ["query is not an input pair"]
    expected = _reference_output(query["input"])
    if "output" in query and query["output"] != expected:
        reasons.append("query output does not match the canonical rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != expected:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Small malformed grids for structural-checker regression probes."""
    valid = generate(991, 4, difficulty="medium")
    blank = [[0 for _ in row] for row in valid]
    one_component = deepcopy(blank)
    one_component[0][0] = 3
    unsupported = deepcopy(blank)
    for column in range(3):
        unsupported[0][column] = 4
    unsupported[-1][-1] = 6
    ragged = deepcopy(valid)
    ragged[0] = ragged[0][:-1]
    return [
        ("blank", blank),
        ("one_component", one_component),
        ("unsupported_horizontal_three", unsupported),
        ("ragged", ragged),
    ]
