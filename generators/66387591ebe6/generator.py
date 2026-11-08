"""Generator for ARC task 66387591ebe6 — key-controlled pivot rotation.

The integer key at ``(0, 0)`` selects ``key - 1`` clockwise quarter-turns.
The unique maroon (9) cell is the fixed pivot.  Every other nonzero cell is
moved rigidly around that pivot with its own color preserved; the output is a
fresh zero canvas containing only the key, pivot, and rotated object.

The curriculum deliberately stays close to the four canonical inputs: 9x9 or
11x11 canvases, a connected three- or four-cell object within radius three of
the pivot, and a canonical-palette monochrome branch.  Scheduled multicolor
objects and off-center pivots refute shortcuts that the public examples alone
cannot falsify.  Ordinary draws use keys 2, 3, and 4 so every training pair is
non-identity; key 1 remains an exact, observable override because it is a
lawful identity branch of the authority.
"""
from __future__ import annotations

import copy
from collections import deque
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Point = tuple[int, int]

GENERATOR_ID = "66387591ebe6"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "60007e76f218"
ALLOW_IDENTITY_OUTPUT = True

SUMMARY = (
    "Read key k at (0,0), keep the unique color-9 pivot fixed, and rotate every "
    "other nonzero cell with its color preserved by k-1 clockwise quarter-turns "
    "around that pivot on a fresh zero canvas."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid height and width are independently 9 or 11",
    "(0,0) is a key in 1..4 and there is exactly one color-9 pivot",
    "the object has three or four 4-connected cells within radius three of the pivot",
    "the keyed rotation stays in bounds and never lands on the key or pivot",
    "ordinary four-example windows contain keys 2, 3, and 4, an off-center pivot, and a multicolor witness",
    "key 1 is supported only through an explicit exact override because it lawfully produces identity output",
]

PIVOT_REGIONS = ("center", "northwest", "northeast", "southwest", "southeast")
TEXTURES = ("mono", "multicolor")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical height",
        "valid": "9|11",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical width",
        "valid": "9|11",
    },
    "key": {
        "type": "int",
        "default": "four-slot nonidentity schedule",
        "valid": "1..4",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 3 or 4",
        "valid": "3|4",
    },
    "pivot_region": {
        "type": "str",
        "default": "five-region schedule",
        "valid": "|".join(PIVOT_REGIONS),
    },
    "texture": {
        "type": "str",
        "default": "four-slot mono/multicolor schedule",
        "valid": "|".join(TEXTURES),
        "doc": (
            "mono matches the canonical one-object-color palette; multicolor "
            "proves that colors move cell-by-cell rather than being flattened"
        ),
    },
}

# Every Cartesian combination of the exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("key_2", "key_3", "key_4")

# Canonical connected object geometries plus nearby asymmetric variants.  D4
# transforms preserve connectivity and keep every offset within radius three.
_SHAPES: dict[int, tuple[tuple[Point, ...], ...]] = {
    3: (
        ((-2, 0), (-2, 1), (-1, 1)),
        ((0, 2), (1, 2), (1, 3)),
        ((-1, -1), (-1, 0), (0, -1)),
        ((-2, -1), (-1, -1), (-1, 0)),
    ),
    4: (
        ((-2, 0), (-2, 1), (-1, 1), (0, 1)),
        ((-3, 0), (-3, 1), (-2, 1), (-1, 1)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((-1, -2), (-1, -1), (0, -1), (1, -1)),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the nonidentity key schedule to the semantic census."""
    del seed, difficulty
    return ("key_2", "key_3", "key_4", "key_2")[int(sample_index) % 4]


def _pivot_positions(height: int, width: int) -> dict[str, Point]:
    center = (height // 2, width // 2)
    row, col = center
    return {
        "center": center,
        "northwest": (row - 1, col - 1),
        "northeast": (row - 1, col + 1),
        "southwest": (row + 1, col - 1),
        "southeast": (row + 1, col + 1),
    }


def _turn(offset: Point, turns: int) -> Point:
    """Rotate one relative offset clockwise by ``turns`` quarter-turns."""
    row, col = offset
    for _ in range(turns % 4):
        row, col = col, -row
    return row, col


def _d4(offset: Point, transform_index: int) -> Point:
    """Apply one of eight D4 transforms for presentation diversity."""
    row, col = offset
    if transform_index >= 4:
        col = -col
    return _turn((row, col), transform_index % 4)


def _connected(cells: Iterable[Point]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = next(iter(remaining))
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if point in remaining and point not in seen:
                seen.add(point)
                queue.append(point)
    return seen == remaining


def _shape_candidates(n_cells: int) -> tuple[tuple[Point, ...], ...]:
    """Enumerate translated D4 presentations of the canonical shape family.

    The baseline rewrite still had a small finite presentation vocabulary,
    especially in the easy band.  Translating the same connected polyomino
    within the lawful radius preserves task semantics while preventing large
    lesson censuses from repeating identical inputs.  Corner offsets (±3, ±3)
    are excluded because an off-center 9x9 pivot could rotate one onto the key
    cell at (0, 0).
    """
    candidates: set[tuple[Point, ...]] = set()
    for base in _SHAPES[n_cells]:
        for transform_index in range(8):
            transformed = tuple(_d4(point, transform_index) for point in base)
            for shift_row in range(-6, 7):
                for shift_col in range(-6, 7):
                    shifted = tuple(
                        sorted(
                            (row + shift_row, col + shift_col)
                            for row, col in transformed
                        )
                    )
                    if len(set(shifted)) != n_cells:
                        continue
                    if (0, 0) in shifted:
                        continue
                    if any(max(abs(row), abs(col)) > 3 for row, col in shifted):
                        continue
                    if any(abs(row) == 3 and abs(col) == 3 for row, col in shifted):
                        continue
                    if len({row for row, _ in shifted}) < 2:
                        continue
                    if len({col for _, col in shifted}) < 2:
                        continue
                    if _connected(shifted):
                        candidates.add(shifted)
    return tuple(sorted(candidates))


_CANDIDATE_SHAPES = {
    n_cells: _shape_candidates(n_cells) for n_cells in sorted(_SHAPES)
}


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["rows must be non-empty lists"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if height not in (9, 11):
        errors.append(f"height must be 9 or 11, got {height}")
    if width not in (9, 11):
        errors.append(f"width must be 9 or 11, got {width}")

    key = grid[0][0]
    if not 1 <= key <= 4:
        errors.append(f"key at (0,0) must be in 1..4, got {key}")

    pivots = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    pivot = pivots[0] if len(pivots) == 1 else None
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-9 pivot, found {len(pivots)}")

    cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if (row, col) != (0, 0) and grid[row][col] not in (0, 9)
    ]
    if len(cells) not in (3, 4):
        errors.append(f"expected three or four object cells, found {len(cells)}")

    positions = [(row, col) for row, col, _ in cells]
    if positions and not _connected(positions):
        errors.append("object cells must form one 4-connected component")
    if positions:
        if len({row for row, _ in positions}) < 2 or len({col for _, col in positions}) < 2:
            errors.append("object must span at least two rows and two columns")

    region = None
    offsets: tuple[Point, ...] = ()
    rotated: tuple[Point, ...] = ()
    if pivot is not None:
        expected_regions = _pivot_positions(height, width)
        region = next((name for name, point in expected_regions.items() if point == pivot), None)
        if region is None:
            errors.append("pivot must occupy one of the five declared center regions")
        offsets = tuple((row - pivot[0], col - pivot[1]) for row, col in positions)
        if any(max(abs(dr), abs(dc)) > 3 for dr, dc in offsets):
            errors.append("every object cell must lie within Chebyshev radius three")
        turns = (key - 1) % 4 if isinstance(key, int) else 0
        rotated = tuple(
            (pivot[0] + dr, pivot[1] + dc)
            for dr, dc in (_turn(offset, turns) for offset in offsets)
        )
        for point in rotated:
            row, col = point
            if not (0 <= row < height and 0 <= col < width):
                errors.append("keyed rotation leaves the grid")
                break
        if (0, 0) in rotated:
            errors.append("keyed rotation collides with the key cell")
        if pivot in rotated:
            errors.append("keyed rotation collides with the pivot")

    colors = {value for _, _, value in cells}
    texture = "mono" if len(colors) == 1 else ("multicolor" if len(colors) >= 2 else None)

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "key": key,
        "pivot": pivot,
        "pivot_region": region,
        "cells": cells,
        "positions": positions,
        "offsets": offsets,
        "rotated": rotated,
        "texture": texture,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the task-linked generated manifold and all canonical inputs."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """All generated scenes and all four canonical inputs satisfy this grammar."""
    return self_check(grid)


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    """Recover every exact axis from returned pixels rather than RNG metadata."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "key": analysis["key"],
        "n_cells": len(analysis["cells"]),
        "pivot_region": analysis["pivot_region"],
        "texture": analysis["texture"],
    }


def _render_rule(
    grid: Sequence[Sequence[int]],
    *,
    turns: int | None = None,
    center: Point | None = None,
    overlay: bool = False,
    keep_pivot: bool = True,
    flatten_color: bool = False,
) -> Grid:
    analysis = _analyze(copy.deepcopy(grid))
    if analysis["errors"]:
        raise ValueError("invalid rotation scene: " + "; ".join(analysis["errors"]))

    height, width = analysis["height"], analysis["width"]
    key = analysis["key"]
    pivot = analysis["pivot"]
    rotation_center = pivot if center is None else center
    actual_turns = (key - 1) % 4 if turns is None else turns % 4
    output = copy.deepcopy(grid) if overlay else full_grid(height, width, 0)
    output[0][0] = key
    if keep_pivot:
        output[pivot[0]][pivot[1]] = 9
    elif not overlay:
        output[pivot[0]][pivot[1]] = 0

    first_color = analysis["cells"][0][2]
    for row, col, color in analysis["cells"]:
        rel = (row - rotation_center[0], col - rotation_center[1])
        dr, dc = _turn(rel, actual_turns)
        new_row, new_col = rotation_center[0] + dr, rotation_center[1] + dc
        if 0 <= new_row < height and 0 <= new_col < width:
            output[new_row][new_col] = first_color if flatten_color else color
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; the selected Racket rule is authority."""
    return _render_rule(grid)


def _rival_identity(grid: Sequence[Sequence[int]]) -> Grid:
    return copy.deepcopy(grid)


def _rival_fixed_clockwise(grid: Sequence[Sequence[int]]) -> Grid:
    return _render_rule(grid, turns=1)


def _rival_key_direct(grid: Sequence[Sequence[int]]) -> Grid:
    analysis = _analyze(grid)
    return _render_rule(grid, turns=analysis["key"] % 4)


def _rival_counterclockwise(grid: Sequence[Sequence[int]]) -> Grid:
    analysis = _analyze(grid)
    return _render_rule(grid, turns=(-(analysis["key"] - 1)) % 4)


def _rival_grid_center(grid: Sequence[Sequence[int]]) -> Grid:
    analysis = _analyze(grid)
    center = (analysis["height"] // 2, analysis["width"] // 2)
    return _render_rule(grid, center=center)


def _rival_overlay(grid: Sequence[Sequence[int]]) -> Grid:
    return _render_rule(grid, overlay=True)


def _rival_erase_pivot(grid: Sequence[Sequence[int]]) -> Grid:
    return _render_rule(grid, keep_pivot=False)


def _rival_monochrome(grid: Sequence[Sequence[int]]) -> Grid:
    return _render_rule(grid, flatten_color=True)


def _rival_no_key1_identity(grid: Sequence[Sequence[int]]) -> Grid:
    analysis = _analyze(grid)
    turns = 1 if analysis["key"] == 1 else analysis["key"] - 1
    return _render_rule(grid, turns=turns)


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "identity": _rival_identity,
    "fixed_clockwise": _rival_fixed_clockwise,
    "key_direct_quarter_turns": _rival_key_direct,
    "counterclockwise_about_pivot": _rival_counterclockwise,
    "rotate_about_grid_center": _rival_grid_center,
    "overlay_instead_of_rebuild": _rival_overlay,
    "erase_pivot": _rival_erase_pivot,
    "flatten_object_to_first_color": _rival_monochrome,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These two wrong rules reproduce every public pair and can be falsified by
# ordinary nonidentity training draws.
CANONICAL_SHORTCUTS = {
    "rotate_about_grid_center": _rival_grid_center,
    "flatten_object_to_first_color": _rival_monochrome,
}

# The canonical examples also cannot distinguish a solver that rejects key 1.
# That ambiguity is kept executable for an explicit-override probe, but is not
# advertised to the lesson gate: key 1 lawfully returns the input unchanged and
# the generic rule-smoke gate rejects identity unless canonical training itself
# contains an identity pair.  See FEEDBACK_TO_CODEX.md and the lesson probe.
EXTRAPOLATION_RIVALS = {
    "keys_2_to_4_only": _rival_no_key1_identity,
}


def _rival_differs(grid: Sequence[Sequence[int]], name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


def _witness_identity(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "identity")


def _witness_fixed_clockwise(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "fixed_clockwise")


def _witness_key_direct(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "key_direct_quarter_turns")


def _witness_counterclockwise(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "counterclockwise_about_pivot")


def _witness_off_center(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "rotate_about_grid_center")


def _witness_rebuild(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "overlay_instead_of_rebuild")


def _witness_pivot(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "erase_pivot")


def _witness_multicolor(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_differs(grid, "flatten_object_to_first_color")


SEMANTIC_WITNESSES = {
    "nonidentity_refutes_copy_input": _witness_identity,
    "key_controls_more_than_fixed_clockwise": _witness_fixed_clockwise,
    "turn_count_is_key_minus_one": _witness_key_direct,
    "clockwise_not_counterclockwise": _witness_counterclockwise,
    "pivot_not_grid_center": _witness_off_center,
    "output_rebuilds_and_clears_source": _witness_rebuild,
    "pivot_is_preserved": _witness_pivot,
    "cell_colors_are_preserved": _witness_multicolor,
}

WITNESS_RIVALS = {
    "nonidentity_refutes_copy_input": ["identity"],
    "key_controls_more_than_fixed_clockwise": ["fixed_clockwise"],
    "turn_count_is_key_minus_one": ["key_direct_quarter_turns"],
    "clockwise_not_counterclockwise": ["counterclockwise_about_pivot"],
    "pivot_not_grid_center": ["rotate_about_grid_center"],
    "output_rebuilds_and_clears_source": ["overlay_instead_of_rebuild"],
    "pivot_is_preserved": ["erase_pivot"],
    "cell_colors_are_preserved": ["flatten_object_to_first_color"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require every named wrong rule to be refuted by the demonstrations."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the keyed-pivot rule")
    if isinstance(query, dict) and "input" in query and query.get("output") is not None:
        if query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the keyed-pivot rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _scheduled_choice(ctx, label: str, options: tuple[Any, ...], scheduled: Any) -> Any:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _choose_offsets(ctx, n_cells: int, difficulty: Any) -> tuple[Point, ...]:
    rng = ctx.draw_rng("shape")
    max_radius = 2 if difficulty == "easy" else 3
    pool = tuple(
        shape
        for shape in _CANDIDATE_SHAPES[n_cells]
        if max(max(abs(row), abs(col)) for row, col in shape) <= max_radius
    )
    if not pool:
        raise RuntimeError("internal shape pool is empty")
    return rng.choice(pool)


def _object_colors(ctx, key: int, n_cells: int, texture: str) -> list[int]:
    rng = ctx.draw_rng("object_colors")
    palette = [color for color in range(1, 9) if color != key]
    rng.shuffle(palette)
    if texture == "mono":
        return [palette[0]] * n_cells
    first, second = palette[:2]
    colors = [first if index % 2 == 0 else second for index in range(n_cells)]
    # Rotate the alternation without changing the guaranteed two-color support.
    shift = rng.randrange(n_cells)
    return colors[shift:] + colors[:shift]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    _validate_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    slot = int(sample_index) % 4
    scheduled_dim = (9, 11, 9, 11)[slot]
    height = _scheduled_choice(ctx, "grid_h", (9, 11), scheduled_dim)
    width = _scheduled_choice(ctx, "grid_w", (9, 11), scheduled_dim)
    key = _scheduled_choice(ctx, "key", (1, 2, 3, 4), (2, 3, 4, 2)[slot])
    n_cells = _scheduled_choice(ctx, "n_cells", (3, 4), (3, 4, 3, 4)[slot])
    region = _scheduled_choice(
        ctx,
        "pivot_region",
        PIVOT_REGIONS,
        PIVOT_REGIONS[int(sample_index) % len(PIVOT_REGIONS)],
    )
    texture = _scheduled_choice(
        ctx,
        "texture",
        TEXTURES,
        ("mono", "mono", "multicolor", "mono")[slot],
    )

    pivot = _pivot_positions(height, width)[region]
    offsets = _choose_offsets(ctx, n_cells, difficulty)
    colors = _object_colors(ctx, key, n_cells, texture)

    grid = full_grid(height, width, 0)
    grid[0][0] = key
    grid[pivot[0]][pivot[1]] = 9
    for (dr, dc), color in zip(offsets, colors):
        row, col = pivot[0] + dr, pivot[1] + dc
        if grid[row][col] != 0:
            raise RuntimeError("internal object placement collided")
        grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    return grid
