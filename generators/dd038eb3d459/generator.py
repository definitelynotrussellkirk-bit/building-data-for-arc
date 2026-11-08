"""Canonical-scale curriculum for ``dd038eb3d459``.

A blue corner cell is a four-way rotation key (TL=0, TR=1, BR=2, BL=3
clockwise quarter turns).  Normalize the red shape and the rotated green shape,
XOR their cells, normalize the result, and paint it cyan on the tight crop.

The four-example schedule deliberately includes every corner.  In particular,
the top-left example uses a green shape whose 0° and 180° answers differ.  That
counterexample rules out the strongest key-map ambiguity left by the canonical
examples: treating TL as 180° instead of 0°.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dd038eb3d459"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "624c38e915df"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A black canonical-scale grid contains exactly one blue control in a "
    "corner, one connected red polyomino, and one connected green polyomino. "
    "The control maps TL/TR/BR/BL to 0/1/2/3 clockwise quarter-turns. "
    "Normalize red, rotate then normalize green, take their symmetric XOR, "
    "normalize that mask, and emit its tight cyan(8) crop."
)

INVARIANTS = [
    "the input palette is exactly drawn from {0,1,2,3} with background visible",
    "there is one blue control cell at a grid corner",
    "red and green are each one 4-connected 3..5-cell polyomino",
    "red and green have a one-cell Chebyshev buffer",
    "the normalized red / rotated-green XOR is nonempty",
    "every four consecutive defaults cover TL, TR, BR and BL",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five canonical profiles scheduled by sample_index",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "five canonical profiles scheduled by sample_index",
        "valid": "10..12",
    },
    "corner_position": {
        "type": "str",
        "default": "four-slot TL/TR/BR/BL lesson schedule",
        "valid": "tl|tr|br|bl",
    },
    "red_size": {
        "type": "int",
        "default": "difficulty-aware 3..5 schedule",
        "valid": "3..5",
    },
    "green_size": {
        "type": "int",
        "default": "difficulty-aware 3..5 schedule",
        "valid": "3..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = ("tl", "tr", "br", "bl")
_CANONICAL_PROFILES = ((8, 10), (9, 11), (10, 10), (9, 12), (10, 12))
_CORNER_CODES = {"tl": 0, "tr": 1, "br": 2, "bl": 3}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_RANGES = {
    "grid_h": (8, 10),
    "grid_w": (10, 12),
    "red_size": (3, 5),
    "green_size": (3, 5),
}
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

Grid = list[list[int]]
Shape = tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _connected(cells: Sequence[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen = set(stack)
    while stack:
        row, col = stack.pop()
        for dr, dc in _NEIGHBORS4:
            nxt = (row + dr, col + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == remaining


def _build_shape_bank(size: int) -> tuple[Shape, ...]:
    """All normalized connected ``size``-cell subsets of a 3x3 box."""
    cells = tuple((row, col) for row in range(3) for col in range(3))
    shapes = {
        _normalize(candidate)
        for candidate in combinations(cells, size)
        if _connected(candidate)
    }
    return tuple(sorted(shapes))


_SHAPES = {size: _build_shape_bank(size) for size in (3, 4, 5)}


def _rotate90(shape: Shape) -> Shape:
    height = max(row for row, _col in shape) + 1
    return _normalize((col, height - 1 - row) for row, col in shape)


def _rotate(shape: Shape, code: int) -> Shape:
    result = _normalize(shape)
    for _ in range(code % 4):
        result = _rotate90(result)
    return result


def _xor_shape(red: Shape, green: Shape, code: int) -> Shape:
    return _normalize(set(_normalize(red)).symmetric_difference(_rotate(green, code)))


def _paint_shape(shape: Shape, color: int = 8) -> Grid:
    if not shape:
        return [[0]]
    height = max(row for row, _col in shape) + 1
    width = max(col for _row, col in shape) + 1
    cells = set(shape)
    return [
        [color if (row, col) in cells else 0 for col in range(width)]
        for row in range(height)
    ]


def _output_for_shapes(red: Shape, green: Shape, code: int) -> Grid:
    return _paint_shape(_xor_shape(red, green, code))


@lru_cache(maxsize=None)
def _shape_pairs(red_size: int, green_size: int, code: int) -> tuple[tuple[Shape, Shape], ...]:
    """Lawful pairs; TL pairs also refute the 180°-TL rival by construction."""
    pairs: list[tuple[Shape, Shape]] = []
    for red in _SHAPES[red_size]:
        for green in _SHAPES[green_size]:
            official = _output_for_shapes(red, green, code)
            if official == [[0]]:
                continue
            if code == 0 and official == _output_for_shapes(red, green, 2):
                continue
            pairs.append((red, green))
    if not pairs:
        raise AssertionError(
            f"no shape pair for red_size={red_size}, green_size={green_size}, code={code}"
        )
    return tuple(pairs)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name, value in overrides.items():
        if value is None:
            continue
        if name == "corner_position":
            if type(value) is not str or value not in _CORNER_CODES:
                raise ValueError(
                    "corner_position must be one of 'tl', 'tr', 'br', or 'bl'"
                )
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the four-slot corner curriculum to lesson audits."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, name: str, scheduled: int) -> int:
    lo, hi = _AXIS_RANGES[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _draw_scheduled_choice(ctx, name: str, options: Sequence[str], scheduled: str) -> str:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _default_sizes(sample_index: int, difficulty: Any) -> tuple[int, int]:
    band_offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    red_size = 3 + ((sample_index + band_offset) % 3)
    green_size = 3 + ((2 * sample_index + 1 + band_offset) % 3)
    return red_size, green_size


def _corner_cell(name: str, height: int, width: int) -> tuple[int, int]:
    return {
        "tl": (0, 0),
        "tr": (0, width - 1),
        "br": (height - 1, width - 1),
        "bl": (height - 1, 0),
    }[name]


def _shape_extent(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


def _placements(shape: Shape, height: int, width: int) -> list[tuple[int, int]]:
    shape_h, shape_w = _shape_extent(shape)
    return [
        (top, left)
        for top in range(1, height - shape_h)
        for left in range(1, width - shape_w)
    ]


def _translate(shape: Shape, top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + row, left + col) for row, col in shape)


def _chebyshev_separated(
    first: Sequence[tuple[int, int]], second: Sequence[tuple[int, int]]
) -> bool:
    return all(
        max(abs(row - other_row), abs(col - other_col)) > 1
        for row, col in first
        for other_row, other_col in second
    )


def _side_candidates(
    shape: Shape,
    side: str,
    height: int,
    width: int,
    control: tuple[int, int],
) -> list[tuple[tuple[int, int], ...]]:
    """Interior placements confined to one half of the canvas."""
    shape_h, shape_w = _shape_extent(shape)
    middle = width // 2
    if side == "left":
        columns = range(1, middle - shape_w)
    elif side == "right":
        columns = range(middle + 1, width - shape_w)
    else:  # internal programming error, not caller input
        raise AssertionError(f"unknown side: {side!r}")

    placements = []
    for top in range(1, height - shape_h):
        for left in columns:
            cells = _translate(shape, top, left)
            if _chebyshev_separated(cells, (control,)):
                placements.append(cells)
    return placements


def _place_operands(
    red: Shape,
    green: Shape,
    height: int,
    width: int,
    control: tuple[int, int],
    rng,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """Place operands constructively in opposite canvas halves.

    Opposite-half placement gives a hard one-cell horizontal buffer even on
    the minimum 8x10 canvas.  This avoids retry loops and keeps exhaustive
    override probes fast while row/side choices still vary by keyed RNG.
    """
    red_side = "left" if rng.randrange(2) == 0 else "right"
    green_side = "right" if red_side == "left" else "left"
    red_options = _side_candidates(red, red_side, height, width, control)
    green_options = _side_candidates(green, green_side, height, width, control)
    if not red_options or not green_options:
        raise AssertionError(
            f"no opposite-half placement on {height}x{width} with control={control}"
        )
    red_cells = red_options[rng.randrange(len(red_options))]
    green_cells = green_options[rng.randrange(len(green_options))]
    if not _chebyshev_separated(red_cells, green_cells):
        raise AssertionError("opposite-half placement violated the separation invariant")
    return red_cells, green_cells


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_call(difficulty, overrides)
    effective = {name: value for name, value in overrides.items() if value is not None}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    scheduled_h, scheduled_w = _CANONICAL_PROFILES[
        sample_index % len(_CANONICAL_PROFILES)
    ]
    scheduled_corner = schedule_profile(seed, sample_index, difficulty)
    scheduled_red, scheduled_green = _default_sizes(sample_index, difficulty)

    height = _draw_scheduled_int(ctx, "grid_h", scheduled_h)
    width = _draw_scheduled_int(ctx, "grid_w", scheduled_w)
    corner = _draw_scheduled_choice(
        ctx, "corner_position", SCHEDULE_PROFILES, scheduled_corner
    )
    red_size = _draw_scheduled_int(ctx, "red_size", scheduled_red)
    green_size = _draw_scheduled_int(ctx, "green_size", scheduled_green)

    code = _CORNER_CODES[corner]
    pair_rng = ctx.draw_rng("shape_pair")
    candidates = _shape_pairs(red_size, green_size, code)
    red_shape, green_shape = candidates[pair_rng.randrange(len(candidates))]

    control = _corner_cell(corner, height, width)
    red_cells, green_cells = _place_operands(
        red_shape,
        green_shape,
        height,
        width,
        control,
        ctx.draw_rng("operand_placement"),
    )

    grid = full_grid(height, width, 0)
    grid[control[0]][control[1]] = 1
    for row, col in red_cells:
        grid[row][col] = 2
    for row, col in green_cells:
        grid[row][col] = 3
    return grid


def _components(grid: Sequence[Sequence[int]], color: int) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for dr, dc in _NEIGHBORS4:
                    nxt = (rr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(sorted(cells))
    return result


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {}, ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")

    height = len(grid)
    palette = {value for row in grid for value in row if type(value) is int}
    if not 8 <= height <= 10 or not 10 <= width <= 12:
        errors.append(f"grid dimensions must be 8..10 by 10..12, got {height}x{width}")
    if not palette <= {0, 1, 2, 3}:
        errors.append(f"input palette must be a subset of {{0,1,2,3}}, got {sorted(palette)}")
    if 0 not in palette:
        errors.append("background color 0 must remain visible")

    controls = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    corner_cells = {
        "tl": (0, 0),
        "tr": (0, width - 1),
        "br": (height - 1, width - 1),
        "bl": (height - 1, 0),
    }
    corner = next(
        (name for name, cell in corner_cells.items() if controls == [cell]), None
    )
    if corner is None:
        errors.append(f"expected exactly one color-1 control in a corner, got {controls}")

    red_components = _components(grid, 2)
    green_components = _components(grid, 3)
    if len(red_components) != 1:
        errors.append(f"expected exactly one connected red shape, got {len(red_components)}")
    if len(green_components) != 1:
        errors.append(
            f"expected exactly one connected green shape, got {len(green_components)}"
        )

    red_cells = red_components[0] if len(red_components) == 1 else []
    green_cells = green_components[0] if len(green_components) == 1 else []
    if red_cells and not 3 <= len(red_cells) <= 5:
        errors.append(f"red shape must contain 3..5 cells, got {len(red_cells)}")
    if green_cells and not 3 <= len(green_cells) <= 5:
        errors.append(f"green shape must contain 3..5 cells, got {len(green_cells)}")
    if red_cells and green_cells and not _chebyshev_separated(red_cells, green_cells):
        errors.append("red and green must have a one-cell Chebyshev buffer")

    red_shape = _normalize(red_cells) if red_cells else ()
    green_shape = _normalize(green_cells) if green_cells else ()
    if corner is not None and red_shape and green_shape:
        if not _xor_shape(red_shape, green_shape, _CORNER_CODES[corner]):
            errors.append("normalized red XOR rotated green must be nonempty")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "palette": frozenset(palette),
        "control": controls[0] if len(controls) == 1 else None,
        "corner_position": corner,
        "red_cells": tuple(red_cells),
        "green_cells": tuple(green_cells),
        "red_size": len(red_cells),
        "green_size": len(green_cells),
        "red_shape": red_shape,
        "green_shape": green_shape,
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int | str]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid rotation-XOR input: " + "; ".join(errors))
    return {name: facts[name] for name in AXES}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    requested: dict[str, Any] = {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        requested.update(nested)
    requested.update({name: meta[name] for name in AXES if name in meta})
    return requested


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    if errors:
        return errors
    observed = {name: facts[name] for name in AXES}
    for name, wanted in _meta_overrides(meta).items():
        if name in AXES and wanted is not None and observed.get(name) != wanted:
            errors.append(
                f"override {name} requested {wanted!r}, observed {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This task's lawful manifold; all defaults and canonical inputs satisfy it."""
    return self_check(grid)


def _facts_or_raise(grid) -> dict[str, Any]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("input is outside the rotation-XOR domain: " + "; ".join(errors))
    return facts


def _output_with_code(facts: dict[str, Any], code: int) -> Grid:
    return _output_for_shapes(facts["red_shape"], facts["green_shape"], code)


def rule_mirror(grid) -> Grid:
    """Independent Python mirror; canonical Racket remains label authority."""
    facts = _facts_or_raise(grid)
    return _output_with_code(facts, _CORNER_CODES[facts["corner_position"]])


def _rival_top_left_is_180_degrees(grid) -> Grid:
    """Plausible canonical-fit rival: TL maps to 180°, not 0°; others correct."""
    facts = _facts_or_raise(grid)
    corner = facts["corner_position"]
    code = 2 if corner == "tl" else _CORNER_CODES[corner]
    return _output_with_code(facts, code)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "top_left_is_180_degrees": _rival_top_left_is_180_degrees,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_top_left_rotation_discriminator(grid) -> bool:
    try:
        facts = _facts_or_raise(grid)
    except ValueError:
        return False
    return bool(
        facts["corner_position"] == "tl"
        and rule_mirror(grid) != _rival_top_left_is_180_degrees(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "top_left_rotation_discriminator": _witness_top_left_rotation_discriminator,
}
WITNESS_RIVALS = {
    "top_left_rotation_discriminator": ["top_left_is_180_degrees"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid labels and a demonstration falsifying every declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is outside the rule domain: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the rotation-XOR rule")
        else:
            valid_demos.append(pair)

    try:
        expected_query = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query input is outside the rule domain: {exc}")
        return reasons
    if "output" in query and query["output"] != expected_query:
        reasons.append("query output disagrees with the rotation-XOR rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
