"""Generator for ARC task 5bcc776c32fb.

Intended transformation
-----------------------
For every monochromatic color-1 object that is exactly one horizontal row,
has odd size, and has length at least three, recolor its middle cell to 2.
All other cells are preserved.

The generated curriculum makes every clause observable without overloading a
single grid.  Three scheduled scene profiles distribute parity/orientation,
minimum/color, and object-connectivity negatives so any two profile types
refute every declared shortcut.  Every scene also contains a length-nine target
to rule out memorizing the canonical positive lengths 3/5/7.
"""
from __future__ import annotations

from typing import Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5bcc776c32fb"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "51414a828017"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find each color-1 object that is a single horizontal row of odd length "
    "at least 3, recolor exactly its middle cell to 2, and preserve every "
    "other object and cell."
)

INVARIANTS = [
    "background color is 0 and remains visible",
    "ordinary draws contain one or two isolated qualifying color-1 targets",
    "three scheduled profiles distribute parity, orientation, minimum-length, object-connectivity, and color witnesses",
    "any two profile types jointly refute every declared shortcut",
    "ordinary draws use exactly one non-rule distractor color",
    "every ordinary draw contains a qualifying length-9 target",
]

DISTRACTOR_COLORS = (4, 5, 6, 7, 9)
SCENE_PROFILES = ("parity_orientation_shape", "minimum_color_shape", "minimum_color_parity_orientation")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule",
        "valid": "8..10",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule conditional on grid_h",
        "valid": "10..13",
        "doc": "Exact returned grid width.",
    },
    "n_targets": {
        "type": "int",
        "default": "keyed draw 1..2",
        "valid": "1..2",
        "doc": "Exact number of qualifying color-1 horizontal components.",
    },
    "distractor_color": {
        "type": "color",
        "default": "keyed choice from canonical distractor colors",
        "valid": "4|5|6|7|9",
        "doc": "The sole non-background, non-blue input color.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CANONICAL_WIDTHS = {
    8: (10, 11),
    9: (12,),
    10: (13,),
}


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}"
        )


def _validate_difficulty(difficulty) -> None:
    if difficulty is not None and difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"invalid difficulty: {difficulty!r}")


def _strict_override_types(overrides: dict) -> None:
    for name in ("grid_h", "grid_w", "n_targets", "distractor_color"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")


def _draw_axes(ctx) -> tuple[int, int, int, int]:
    """Draw four exact, observable axes while anchoring defaults to profiles."""
    if "grid_h" in ctx.overrides and ctx.overrides["grid_h"] is not None:
        height = ctx.draw_int_strict("grid_h", 8, 10)
    else:
        height = ctx.draw_choice("grid_h", (8, 9, 10))

    if "grid_w" in ctx.overrides and ctx.overrides["grid_w"] is not None:
        width = ctx.draw_int_strict("grid_w", 10, 13)
    else:
        # This keeps every default draw on an observed canonical (h,w,palette)
        # profile without coupling explicit overrides.
        width = ctx.draw_choice("grid_w", _CANONICAL_WIDTHS[height])

    targets = ctx.draw_int_strict("n_targets", 1, 2)
    distractor = ctx.draw_choice("distractor_color", DISTRACTOR_COLORS)
    return height, width, targets, distractor


def _put(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        if grid[row][col] != 0:
            raise RuntimeError(f"internal layout overlap at ({row},{col})")
        grid[row][col] = color


def _line(row: int, start: int, length: int) -> list[tuple[int, int]]:
    return [(row, start + offset) for offset in range(length)]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Cycle three complementary profiles independently of seed/difficulty."""
    del seed, difficulty
    return int(sample_index) % len(SCENE_PROFILES)


def _base_scene(
    rng,
    n_targets: int,
    distractor_color: int,
    difficulty,
    profile_index: int,
) -> list[list[int]]:
    """Construct one canonical-scale 8x10 curriculum scene.

    Rows 0 and 2 are target slots and row 3 is a separator.  The three
    profiles intentionally omit different negative branches.  Every optional
    witness occurs in two of the three profiles except the junction witness,
    which occurs in the first two; therefore any two profile types cover all
    five conditional rivals while each grid has only 4--6 objects.
    """
    grid = full_grid(8, 10, 0)

    # Length nine is deliberately outside the canonical positive lengths
    # {3,5,7}; it makes the memorized-length shortcut visibly wrong.
    first_start = rng.choice((0, 1))
    _put(grid, _line(0, first_start, 9), 1)

    if n_targets == 2:
        lengths_by_band = {
            "easy": (3, 5),
            "medium": (5, 7),
            "hard": (7, 9),
            None: (3, 5, 7, 9),
        }
        length = rng.choice(lengths_by_band[difficulty])
        start = rng.randint(0, 10 - length)
        _put(grid, _line(2, start, length), 1)

    profile = SCENE_PROFILES[profile_index]
    has_parity_orientation = profile in {
        "parity_orientation_shape",
        "minimum_color_parity_orientation",
    }
    has_minimum_color = profile in {
        "minimum_color_shape",
        "minimum_color_parity_orientation",
    }
    has_junction = profile in {
        "parity_orientation_shape",
        "minimum_color_shape",
    }

    if has_parity_orientation:
        # Parity negative: an even horizontal blue component.
        even_length = rng.choice((2, 4))
        _put(grid, _line(4, 0, even_length), 1)
        # Orientation negative: an odd vertical blue component.
        _put(grid, ((4, 5), (5, 5), (6, 5)), 1)

    if has_minimum_color:
        # Minimum-size negative: a blue singleton.
        _put(grid, ((4, rng.choice((8, 9))),), 1)

    if has_junction:
        # Object-vs-row-run negative: a bent object with an odd row run.
        stem_col = rng.choice((0, 1, 2))
        _put(grid, ((6, 0), (6, 1), (6, 2), (7, stem_col)), 1)

    if has_minimum_color:
        # Color negative: a qualifying odd horizontal line in another color.
        distractor_start = rng.choice((6, 7))
        _put(grid, _line(7, distractor_start, 3), distractor_color)
    else:
        # Keep the exact distractor-color axis observable without accidentally
        # teaching the color-blind rival in this profile.
        _put(grid, ((7, 8),), distractor_color)
    return grid


def _transform_and_embed(
    base: Sequence[Sequence[int]],
    *,
    height: int,
    width: int,
    flip_vertical: bool,
    flip_horizontal: bool,
    row_offset: int,
    col_offset: int,
) -> list[list[int]]:
    source = [list(row) for row in base]
    if flip_vertical:
        source.reverse()
    if flip_horizontal:
        source = [list(reversed(row)) for row in source]

    grid = full_grid(height, width, 0)
    for row in range(8):
        for col in range(10):
            grid[row + row_offset][col + col_offset] = source[row][col]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    _validate_difficulty(difficulty)
    _strict_override_types(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, n_targets, distractor = _draw_axes(ctx)
    rng = ctx.draw_rng("layout")
    profile_index = schedule_profile(seed, sample_index, difficulty)
    base = _base_scene(rng, n_targets, distractor, difficulty, profile_index)
    grid = _transform_and_embed(
        base,
        height=height,
        width=width,
        flip_vertical=bool(rng.randrange(2)),
        flip_horizontal=bool(rng.randrange(2)),
        row_offset=rng.randint(0, height - 8),
        col_offset=rng.randint(0, width - 10),
    )

    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_targets": n_targets,
        "distractor_color": distractor,
    }
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid scene: {errors}")
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"axis round-trip failed: expected={expected}, observed={observed}")
    return grid


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty 2D list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must contain non-empty rows"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            return ["grid rows must be rectangular non-empty lists"]
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) has invalid ARC color {value!r}"
                )
    return errors


def _components(
    grid: Sequence[Sequence[int]], *, colors: Iterable[int] | None = None
) -> list[dict[str, object]]:
    allowed = None if colors is None else set(colors)
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
        and (allowed is None or grid[row][col] in allowed)
    }
    components: list[dict[str, object]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for next_cell in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if next_cell in unseen and grid[next_cell[0]][next_cell[1]] == color:
                    unseen.remove(next_cell)
                    cells.add(next_cell)
                    stack.append(next_cell)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        components.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "size": len(cells),
                "r1": min(rows),
                "r2": max(rows),
                "c1": min(cols),
                "c2": max(cols),
                "h": max(rows) - min(rows) + 1,
                "w": max(cols) - min(cols) + 1,
            }
        )
    return components


def _is_target(component: dict[str, object], *, minimum: int = 3) -> bool:
    return (
        component["color"] == 1
        and component["h"] == 1
        and component["size"] >= minimum
        and component["size"] % 2 == 1
    )


def observe_overrides(grid) -> dict[str, int]:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    other_colors = sorted(
        {value for row in grid for value in row if value not in {0, 1}}
    )
    if len(other_colors) != 1 or other_colors[0] not in DISTRACTOR_COLORS:
        raise ValueError(
            "expected exactly one declared distractor color outside {0,1}, "
            f"found {other_colors}"
        )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": sum(
            _is_target(component) for component in _components(grid, colors={1})
        ),
        "distractor_color": other_colors[0],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad authority-compatible input grammar, never labels."""
    del difficulty
    errors = _validate_grid(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 10 and 10 <= width <= 13):
        errors.append(f"grid dimensions must be 8..10 by 10..13, got {height}x{width}")
    colors = {value for row in grid for value in row}
    if 0 not in colors:
        errors.append("background color 0 must remain visible")
    if 2 in colors:
        errors.append("input must not already contain output marker color 2")
    non_rule = sorted(colors - {0, 1})
    if len(non_rule) != 1 or non_rule[0] not in DISTRACTOR_COLORS:
        errors.append(
            "expected exactly one distractor color from "
            f"{DISTRACTOR_COLORS}, got {non_rule}"
        )

    targets = [obj for obj in _components(grid, colors={1}) if _is_target(obj)]
    if not targets:
        errors.append("no horizontal color-1 object of odd length >=3")
    if len(targets) > 2:
        errors.append(f"expected at most two qualifying targets, got {len(targets)}")

    # When the override harness supplies exact requested axes, verify them here
    # as a second, independent postcondition in addition to observe_overrides.
    if isinstance(meta, dict) and not errors:
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            expected = {name: requested[name] for name in AXES if name in requested}
            if expected:
                try:
                    actual = observe_overrides(grid)
                except ValueError as exc:
                    errors.append(f"cannot observe requested overrides: {exc}")
                else:
                    for name, value in expected.items():
                        if actual.get(name) != value:
                            errors.append(
                                f"override {name!r} requested {value!r}, observed {actual.get(name)!r}"
                            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical-scale, three-color task grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if (height, width) not in {(8, 10), (8, 11), (9, 12), (10, 13)}:
        errors.append(f"dimensions {height}x{width} are outside canonical profiles")
    colors = {value for row in grid for value in row}
    if len(colors) != 3:
        errors.append(f"canonical palette size is 3, got {len(colors)}")
    blue = _components(grid, colors={1})
    if not any(not _is_target(obj) for obj in blue):
        errors.append("canonical-like scene needs at least one non-target blue object")
    return errors


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def rule_mirror(grid) -> list[list[int]]:
    """Small semantic mirror for tests; canonical Racket remains authority."""
    output = _copy_grid(grid)
    for component in _components(grid, colors={1}):
        if _is_target(component):
            output[component["r1"]][(component["c1"] + component["c2"]) // 2] = 2
    return output


def _solve_components(grid, predicate, *, colors=None) -> list[list[int]]:
    output = _copy_grid(grid)
    for component in _components(grid, colors=colors):
        if predicate(component):
            row = (component["r1"] + component["r2"]) // 2
            col = (component["c1"] + component["c2"]) // 2
            output[row][col] = 2
    return output


def _rival_color_blind(grid):
    return _solve_components(
        grid,
        lambda obj: obj["h"] == 1 and obj["size"] >= 3 and obj["size"] % 2 == 1,
    )


def _rival_no_minimum(grid):
    return _solve_components(
        grid,
        lambda obj: obj["color"] == 1 and obj["h"] == 1 and obj["size"] % 2 == 1,
        colors={1},
    )


def _rival_lengths_357(grid):
    return _solve_components(
        grid,
        lambda obj: obj["color"] == 1 and obj["h"] == 1 and obj["size"] in {3, 5, 7},
        colors={1},
    )


def _rival_parity_blind(grid):
    return _solve_components(
        grid,
        lambda obj: obj["color"] == 1 and obj["h"] == 1 and obj["size"] >= 2,
        colors={1},
    )


def _rival_orientation_blind(grid):
    return _solve_components(
        grid,
        lambda obj: (
            obj["color"] == 1
            and (obj["h"] == 1 or obj["w"] == 1)
            and obj["size"] >= 3
            and obj["size"] % 2 == 1
        ),
        colors={1},
    )


def _rival_row_runs(grid):
    output = _copy_grid(grid)
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            if row[col] != 1:
                col += 1
                continue
            start = col
            while col < len(row) and row[col] == 1:
                col += 1
            length = col - start
            if length >= 3 and length % 2 == 1:
                output[row_index][start + length // 2] = 2
    return output


def _row_run_lengths(component: dict[str, object]) -> list[int]:
    by_row: dict[int, list[int]] = {}
    for row, col in component["cells"]:
        by_row.setdefault(row, []).append(col)
    lengths: list[int] = []
    for cols in by_row.values():
        ordered = sorted(cols)
        start = previous = ordered[0]
        for col in ordered[1:]:
            if col != previous + 1:
                lengths.append(previous - start + 1)
                start = col
            previous = col
        lengths.append(previous - start + 1)
    return lengths


def _positive_target(grid) -> bool:
    return any(_is_target(obj) for obj in _components(grid, colors={1}))


def _even_horizontal_negative(grid) -> bool:
    return any(
        obj["h"] == 1 and obj["size"] >= 2 and obj["size"] % 2 == 0
        for obj in _components(grid, colors={1})
    )


def _vertical_negative(grid) -> bool:
    return any(
        obj["w"] == 1 and obj["h"] >= 3 and obj["size"] % 2 == 1
        for obj in _components(grid, colors={1})
    )


def _junction_negative(grid) -> bool:
    return any(
        obj["h"] > 1
        and obj["w"] > 1
        and any(length >= 3 and length % 2 == 1 for length in _row_run_lengths(obj))
        for obj in _components(grid, colors={1})
    )


def _singleton_negative(grid) -> bool:
    return any(obj["size"] == 1 for obj in _components(grid, colors={1}))


def _color_specific_distractor(grid) -> bool:
    return any(
        obj["color"] != 1
        and obj["h"] == 1
        and obj["size"] >= 3
        and obj["size"] % 2 == 1
        for obj in _components(grid)
    )


def _length9_target(grid) -> bool:
    return any(
        _is_target(obj) and obj["size"] >= 9
        for obj in _components(grid, colors={1})
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "positive_target": _positive_target,
    "even_horizontal_negative": _even_horizontal_negative,
    "vertical_negative": _vertical_negative,
    "junction_negative": _junction_negative,
    "singleton_negative": _singleton_negative,
    "color_specific_distractor": _color_specific_distractor,
    "length9_target": _length9_target,
}
BRANCH_WITNESSES = list(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "color_blind": _rival_color_blind,
    "no_minimum": _rival_no_minimum,
    "lengths_357": _rival_lengths_357,
    "parity_blind": _rival_parity_blind,
    "orientation_blind": _rival_orientation_blind,
    "row_runs": _rival_row_runs,
}
WITNESS_RIVALS = {
    "color_specific_distractor": ["color_blind"],
    "singleton_negative": ["no_minimum"],
    "length9_target": ["lengths_357"],
    "even_horizontal_negative": ["parity_blind"],
    "vertical_negative": ["orientation_blind"],
    "junction_negative": ["row_runs"],
}
CANONICAL_SHORTCUTS = {
    "color_blind": _rival_color_blind,
    "no_minimum": _rival_no_minimum,
    "lengths_357": _rival_lengths_357,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to refute every named rival that predicts the query wrong."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    errors: list[str] = []
    pairs = [*demos, query]
    valid_pairs = True
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} is missing input/output")
            valid_pairs = False
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            errors.append(f"pair {index} input is invalid: {type(exc).__name__}: {exc}")
            valid_pairs = False
            continue
        if pair["output"] != expected:
            errors.append(f"pair {index} output disagrees with intended midpoint rule")
            valid_pairs = False
    if not valid_pairs:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if rival(query["input"]) == query["output"]:
                continue
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                errors.append(f"demonstrations do not refute query-relevant rival: {name}")
        except Exception as exc:
            errors.append(f"rival {name} raised {type(exc).__name__}: {exc}")
    return errors
