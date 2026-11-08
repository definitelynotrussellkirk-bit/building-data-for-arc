"""Generator for selecting the unique holed object, transforming it, and scaling 2x.

The first row contains one transform code.  Below a blank separator row are
three monochrome objects; exactly one has one enclosed hole.  The answer is the
tight crop of that object, transformed by the code, then upscaled by two.
"""
from __future__ import annotations

from copy import deepcopy
from math import lcm
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "147c2b92e5c1"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "93c771e66aca"

SUMMARY = (
    "Read the unique code in row 0: 1=identity, 2=rotate 90 degrees clockwise, "
    "3=rotate 180 degrees, 4=rotate 90 degrees counter-clockwise, 5=flip "
    "left-right, and 6=flip up-down. Among the three separated monochrome "
    "objects below the blank row 1, select the unique object with exactly one "
    "enclosed hole, crop it tightly, apply the coded transform, and scale every "
    "cell to a 2x2 block. Discard the two solid distractors. The curriculum "
    "cycles all six codes, spans the declared size ranges, retains regular exact "
    "canonical-profile anchors, and uses transform-visible asymmetric holed objects."
)

INVARIANTS = [
    "background is 0",
    "row 0 contains exactly one transform code in 1..6 and row 1 is blank",
    "the body contains exactly three separated monochrome 4-connected objects",
    "exactly one body object has one enclosed hole; the other two have none",
    "the selected crop is transformed by the code and then upscaled by two",
]

_AXES_ORDER = (
    "grid_h",
    "grid_w",
    "transform_code",
    "palette_profile",
    "target_slot",
    "target_rank",
)
_PALETTE_PROFILES = ("shared", "distinct")
_TARGET_SLOTS = ("left", "right")
_TARGET_RANKS = ("largest", "middle")
_CANONICAL_PROFILES = (
    (9, 11, "distinct"),
    (9, 12, "shared"),
    (9, 12, "distinct"),
    (10, 12, "distinct"),
    (10, 13, "distinct"),
)
# A 20-slot broad schedule. Slots 0, 5, 10, 15, and 19 are the five
# canonical dimension/palette profiles, while the remaining slots exercise the
# full declared height/width domains. Every cyclic 20-draw window therefore
# contains every canonical anchor and all advertised dimension values.
_SIZE_PALETTE_SCHEDULE = (
    (9, 11, "distinct"),
    (11, 14, "shared"),
    (12, 15, "distinct"),
    (13, 16, "shared"),
    (14, 11, "distinct"),
    (9, 12, "shared"),
    (15, 12, "distinct"),
    (11, 13, "shared"),
    (12, 14, "distinct"),
    (13, 15, "shared"),
    (9, 12, "distinct"),
    (14, 16, "shared"),
    (15, 11, "distinct"),
    (11, 12, "shared"),
    (12, 13, "distinct"),
    (10, 12, "distinct"),
    (13, 14, "shared"),
    (14, 15, "distinct"),
    (15, 16, "shared"),
    (10, 13, "distinct"),
)
_SLOT_RANK_PROFILES = (
    ("left", "largest"),
    ("right", "largest"),
    ("left", "middle"),
    ("right", "middle"),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "deterministic broad schedule with canonical anchors",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "deterministic broad schedule with canonical anchors",
        "valid": "11..16",
    },
    "transform_code": {
        "type": "int",
        "default": "deterministic six-code schedule",
        "valid": "1..6",
    },
    "palette_profile": {
        "type": "str",
        "default": "deterministic broad schedule with canonical anchors",
        "valid": "shared|distinct",
    },
    "target_slot": {
        "type": "str",
        "default": "deterministic four-profile schedule",
        "valid": "left|right",
    },
    "target_rank": {
        "type": "str",
        "default": "deterministic four-profile schedule",
        "valid": "largest|middle",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
_FULL_CYCLE = lcm(len(_SIZE_PALETTE_SCHEDULE), 6, 4)

# Each row is a connected one-hole binary shape.  Every shape has six distinct
# results under the authority's six transforms.  Width is four or five so the
# shape fits either top slot even on the smallest 9x11 scene.
_TARGET_PATTERNS: tuple[tuple[str, ...], ...] = (
    ("####", "#.#.", "###."),
    ("####", "##.#", ".###"),
    ("####.", ".#.##", ".###."),
    ("#####", "##.#.", ".###."),
    ("#####", "#..#.", "####."),
    ("#####", ".#.#.", "####."),
    ("####.", "##.##", ".###."),
    ("####.", "##.#.", ".####"),
    ("#####", "##.#.", "####."),
    ("#####", "##..#", ".####"),
    ("#####", "#.##.", "####."),
)

# Seven-cell solid distractor used when the target must be the largest object.
_SMALL_MAIN_PATTERN = ("###..", ".##..", "..##.")
# Fifteen-cell solid distractor used when the target must be the middle object.
_LARGE_MAIN_PATTERN = ("#####", "#####", "#####")
# Four-cell solid distractor in the lower slot.
_BOTTOM_PATTERN = ("##.", "#..", "#..")

Grid = list[list[int]]
Cell = tuple[int, int]


def _strict_scalar_inputs(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> dict[str, Any]:
    """Return the full deterministic curriculum profile for one draw."""
    _strict_scalar_inputs(seed, sample_index)
    _band(difficulty)
    phase = seed + sample_index
    grid_h, grid_w, palette_profile = _SIZE_PALETTE_SCHEDULE[
        phase % len(_SIZE_PALETTE_SCHEDULE)
    ]
    target_slot, target_rank = _SLOT_RANK_PROFILES[phase % 4]
    return {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "transform_code": phase % 6 + 1,
        "palette_profile": palette_profile,
        "target_slot": target_slot,
        "target_rank": target_rank,
    }


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int, overrides: dict) -> int:
    if label in overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_scheduled_choice(ctx, label: str, options: Sequence[str], scheduled: str, overrides: dict) -> str:
    return ctx.draw_choice(label, options if label in overrides else (scheduled,))


def _pattern_cells(pattern: Sequence[str]) -> list[Cell]:
    return [
        (row, col)
        for row, line in enumerate(pattern)
        for col, value in enumerate(line)
        if value == "#"
    ]


def _normalize_cells(cells: Iterable[Cell]) -> list[Cell]:
    cells = list(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return sorted((row - top, col - left) for row, col in cells)


def _transform_cells(cells: Iterable[Cell], code: int) -> list[Cell]:
    normalized = _normalize_cells(cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    if code == 1:
        transformed = normalized
    elif code == 2:
        transformed = [(col, height - 1 - row) for row, col in normalized]
    elif code == 3:
        transformed = [(height - 1 - row, width - 1 - col) for row, col in normalized]
    elif code == 4:
        transformed = [(width - 1 - col, row) for row, col in normalized]
    elif code == 5:
        transformed = [(row, width - 1 - col) for row, col in normalized]
    elif code == 6:
        transformed = [(height - 1 - row, col) for row, col in normalized]
    else:
        raise ValueError(f"transform code must be in 1..6, found {code!r}")
    return _normalize_cells(transformed)


def _place_cells(grid: Grid, cells: Iterable[Cell], top: int, left: int, color: int) -> None:
    for row, col in cells:
        grid[top + row][left + col] = color


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 9 <= len(grid) <= 15 or not 11 <= width <= 16:
        return [f"grid dimensions must be in 9..15 by 11..16, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _body_components(grid: Sequence[Sequence[int]]) -> list[list[Cell]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[list[Cell]] = []
    for start_row in range(2, height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[Cell] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (2 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(sorted(cells))
    return components


def _bbox(cells: Sequence[Cell]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _crop_component(grid: Sequence[Sequence[int]], cells: Sequence[Cell]) -> Grid:
    top, left, bottom, right = _bbox(cells)
    keep = set(cells)
    return [
        [grid[row][col] if (row, col) in keep else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def _hole_count(shape: Sequence[Sequence[int]]) -> int:
    height, width = len(shape), len(shape[0])
    zeros = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if shape[row][col] == 0
    }
    seen: set[Cell] = set()
    holes = 0
    for start in sorted(zeros):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        touches_edge = False
        while stack:
            row, col = stack.pop()
            if row in (0, height - 1) or col in (0, width - 1):
                touches_edge = True
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                cell = (next_row, next_col)
                if cell in zeros and cell not in seen:
                    seen.add(cell)
                    stack.append(cell)
        if not touches_edge:
            holes += 1
    return holes


def _component_info(grid: Sequence[Sequence[int]], cells: Sequence[Cell]) -> dict[str, Any]:
    top, left, bottom, right = _bbox(cells)
    shape = _crop_component(grid, cells)
    return {
        "cells": list(cells),
        "shape": shape,
        "color": grid[cells[0][0]][cells[0][1]],
        "size": len(cells),
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "holes": _hole_count(shape),
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    row0 = [(col, grid[0][col]) for col in range(width) if grid[0][col] != 0]
    if len(row0) != 1:
        errors.append(f"row 0 must contain exactly one code cell, found {len(row0)}")
        code = None
    else:
        code = row0[0][1]
        if code not in range(1, 7):
            errors.append(f"row 0 code must be in 1..6, found {code}")
    if any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")

    components = [_component_info(grid, cells) for cells in _body_components(grid)]
    if len(components) != 3:
        errors.append(f"body must contain exactly three objects, found {len(components)}")
    if any(component["size"] < 3 for component in components):
        errors.append("every body object must contain at least three cells")

    holed = [component for component in components if component["holes"] == 1]
    if len(holed) != 1:
        errors.append(f"body must contain exactly one one-hole object, found {len(holed)}")
        target = None
    else:
        target = holed[0]
        if not 8 <= target["size"] <= 15:
            errors.append(f"one-hole object size must be in 8..15, found {target['size']}")
    if any(component["holes"] not in (0, 1) for component in components):
        errors.append("body objects may contain at most one enclosed hole")
    if target is not None and any(
        component is not target and component["holes"] != 0 for component in components
    ):
        errors.append("the two distractors must be holeless")

    palette_profile = None
    target_slot = None
    target_rank = None
    if code is not None:
        body_values = {
            grid[row][col]
            for row in range(2, height)
            for col in range(width)
            if grid[row][col] != 0
        }
        palette_profile = "shared" if code in body_values else "distinct"
    if target is not None and len(components) == 3:
        top_pair = sorted(components, key=lambda item: (item["top"], item["left"]))[:2]
        if target in top_pair:
            other = top_pair[0] if top_pair[1] is target else top_pair[1]
            target_slot = "left" if target["left"] < other["left"] else "right"
        sizes = sorted(component["size"] for component in components)
        if target["size"] == sizes[-1] and sizes[-1] > sizes[-2]:
            target_rank = "largest"
        elif sizes[0] < target["size"] < sizes[-1]:
            target_rank = "middle"

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "code": code,
        "components": components,
        "target": target,
        "palette_profile": palette_profile,
        "target_slot": target_slot,
        "target_rank": target_rank,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared control from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "transform_code": analysis["code"],
        "palette_profile": analysis["palette_profile"],
        "target_slot": analysis["target_slot"],
        "target_rank": analysis["target_rank"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or ambiguous scenes."""
    if difficulty is not None:
        try:
            _band(difficulty)
        except (TypeError, ValueError) as exc:
            return [str(exc)]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    if observed.get("target_slot") not in _TARGET_SLOTS:
        errors.append("one-hole target must occupy one of the two upper object slots")
    if observed.get("target_rank") not in _TARGET_RANKS:
        errors.append("one-hole target must be strictly largest or strictly middle-sized")
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical object/header grammar on any declared scene size."""
    return self_check(grid)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_scalar_inputs(seed, sample_index)
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    scheduled = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, "grid_h", 9, 15, scheduled["grid_h"], overrides)
    width = _draw_scheduled_int(ctx, "grid_w", 11, 16, scheduled["grid_w"], overrides)
    code = _draw_scheduled_int(
        ctx, "transform_code", 1, 6, scheduled["transform_code"], overrides
    )
    palette_profile = _draw_scheduled_choice(
        ctx,
        "palette_profile",
        _PALETTE_PROFILES,
        scheduled["palette_profile"],
        overrides,
    )
    target_slot = _draw_scheduled_choice(
        ctx, "target_slot", _TARGET_SLOTS, scheduled["target_slot"], overrides
    )
    target_rank = _draw_scheduled_choice(
        ctx, "target_rank", _TARGET_RANKS, scheduled["target_rank"], overrides
    )

    layout_rng = ctx.draw_rng("layout")
    shape_rng = ctx.draw_rng(f"target-shape-{band}")
    color_rng = ctx.draw_rng("colors")
    grid = full_grid(height, width, 0)
    grid[0][layout_rng.randint(0, width - 1)] = code

    if band == "easy":
        pattern_pool = _TARGET_PATTERNS[:5]
    elif band == "hard":
        pattern_pool = _TARGET_PATTERNS[4:]
    else:
        pattern_pool = _TARGET_PATTERNS
    target_cells = _pattern_cells(shape_rng.choice(pattern_pool))
    # These four transforms preserve a three-row footprint while varying the
    # actual target appearance. Authority outputs still expose all six codes.
    target_cells = _transform_cells(target_cells, shape_rng.choice((1, 3, 5, 6)))

    main_pattern = _SMALL_MAIN_PATTERN if target_rank == "largest" else _LARGE_MAIN_PATTERN
    main_cells = _pattern_cells(main_pattern)
    bottom_cells = _pattern_cells(_BOTTOM_PATTERN)

    if palette_profile == "shared":
        remaining = [color for color in range(1, 10) if color != code]
        target_color, bottom_color = color_rng.sample(remaining, 2)
        main_color = code
    else:
        target_color, main_color, bottom_color = color_rng.sample(
            [color for color in range(1, 10) if color != code], 3
        )

    body_top = layout_rng.randint(2, height - 7)
    scene_left = layout_rng.randint(0, width - 11)
    left_slot = scene_left
    right_slot = scene_left + 6
    target_left = left_slot if target_slot == "left" else right_slot
    main_left = right_slot if target_slot == "left" else left_slot
    target_width = max(col for _, col in target_cells) + 1
    target_left += layout_rng.randint(0, 5 - target_width)

    _place_cells(grid, target_cells, body_top, target_left, target_color)
    _place_cells(grid, main_cells, body_top, main_left, main_color)
    _place_cells(grid, bottom_cells, body_top + 4, scene_left + 4, bottom_color)

    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid


def _transform_grid(shape: Sequence[Sequence[int]], code: int) -> Grid:
    source = [list(row) for row in shape]
    if code == 1:
        return deepcopy(source)
    if code == 2:
        return [list(row) for row in zip(*source[::-1])]
    if code == 3:
        return [row[::-1] for row in source[::-1]]
    if code == 4:
        return [list(row) for row in zip(*source)][::-1]
    if code == 5:
        return [row[::-1] for row in source]
    if code == 6:
        return source[::-1]
    raise ValueError(f"transform code must be in 1..6, found {code!r}")


def _scale2(shape: Sequence[Sequence[int]]) -> Grid:
    output: Grid = []
    for row in shape:
        doubled = [value for value in row for _ in range(2)]
        output.extend([list(doubled), list(doubled)])
    return output


def _render_component(grid, component: dict[str, Any], code: int) -> Grid:
    return _scale2(_transform_grid(component["shape"], code))


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Python mirror for tests; the synchronized Racket remains authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _render_component(grid, analysis["target"], analysis["code"])


def _fallback_grid(grid: Any) -> Grid:
    if isinstance(grid, (list, tuple)) and grid and isinstance(grid[0], (list, tuple)):
        return [list(row) for row in grid]
    return [[0]]


def _fixed_transform_rival(code: int) -> Callable[[Any], Grid]:
    def rival(grid) -> Grid:
        analysis = _analysis(grid)
        if analysis["errors"]:
            return _fallback_grid(grid)
        return _render_component(grid, analysis["target"], code)

    return rival


def _selection_rival(selector: Callable[[list[dict[str, Any]]], dict[str, Any]]) -> Callable[[Any], Grid]:
    def rival(grid) -> Grid:
        analysis = _analysis(grid)
        if analysis["errors"]:
            return _fallback_grid(grid)
        selected = selector(list(analysis["components"]))
        return _render_component(grid, selected, analysis["code"])

    return rival


def _largest(components: list[dict[str, Any]]) -> dict[str, Any]:
    return max(components, key=lambda item: (item["size"], -item["top"], -item["left"]))


def _middle(components: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(components, key=lambda item: (item["size"], item["top"], item["left"]))[1]


def _leftmost(components: list[dict[str, Any]]) -> dict[str, Any]:
    return min(components, key=lambda item: (item["left"], item["top"]))


def _rightmost(components: list[dict[str, Any]]) -> dict[str, Any]:
    return max(components, key=lambda item: (item["right"], -item["top"]))


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    **{
        f"fixed_transform_{code}": _fixed_transform_rival(code)
        for code in range(1, 7)
    },
    "select_largest_object": _selection_rival(_largest),
    "select_middle_object": _selection_rival(_middle),
    "select_leftmost_object": _selection_rival(_leftmost),
    "select_rightmost_object": _selection_rival(_rightmost),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _observed_value(name: str, value: Any) -> Callable[[Any], bool]:
    def witness(grid) -> bool:
        return observe_overrides(grid).get(name) == value

    return witness


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    **{
        f"not_code_{code}": (
            lambda grid, fixed=code: observe_overrides(grid).get("transform_code") not in (None, fixed)
        )
        for code in range(1, 7)
    },
    "target_is_middle": _observed_value("target_rank", "middle"),
    "target_is_largest": _observed_value("target_rank", "largest"),
    "target_is_right": _observed_value("target_slot", "right"),
    "target_is_left": _observed_value("target_slot", "left"),
}
WITNESS_RIVALS: dict[str, list[str]] = {
    **{f"not_code_{code}": [f"fixed_transform_{code}"] for code in range(1, 7)},
    "target_is_middle": ["select_largest_object"],
    "target_is_largest": ["select_middle_object"],
    "target_is_right": ["select_leftmost_object"],
    "target_is_left": ["select_rightmost_object"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"demo {index} violates strict grammar: {'; '.join(grammar)}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the canonical rule")
    query_grammar = strict_canonical_like(query["input"])
    if query_grammar:
        reasons.append("query violates strict grammar: " + "; ".join(query_grammar))
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the canonical rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
