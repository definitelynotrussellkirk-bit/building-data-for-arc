"""Semantic generator for ARC task ``586db18f9bd7``.

The first four cells encode a library index, a six-way transform code, a fill
color, and a border color.  Three monochrome polyominoes form the library.
Select the indexed shape, crop it, apply the requested transform, recolor its
support, and add a one-cell rectangular border.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "586db18f9bd7"
TASK_ID = GENERATOR_ID
VERSION = "4.0.1"
RULE_HASH = "a93fb42e6980"

SUMMARY = (
    "Read header cells (panel index, transform code, fill color, border color); "
    "select one of three 5x5 library shapes, crop-normalize it, apply transform "
    "code 0..5, recolor every occupied cell to the fill color, and surround "
    "the result with a one-cell rectangular border."
)

INVARIANTS = [
    "the input is a 6x17 grid with a four-cell command header",
    "rows 1..5 contain three nonempty monochrome 5x5 panels at columns 0, 6, and 12",
    "columns 5 and 11 and header columns 4..16 are blank separators",
    "the panel index is 1..3 and the transform code is 0..5",
    "fill and border colors are nonzero and distinct",
    "the selected support is crop-normalized before transformation",
]

# Latin ordering: every cyclic window of six profiles covers all six transform
# codes and all three panel indices.  Across the full period all 18 index/code
# combinations occur exactly once.
_PROFILE_ROWS = tuple(
    (f"panel_{((command + block) % 3) + 1}_transform_{command}",
     ((command + block) % 3) + 1,
     command)
    for block in range(3)
    for command in range(6)
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_PAIR = {(row[1], row[2]): row[0] for row in _PROFILE_ROWS}

AXES = {
    "panel_index": {
        "type": "int",
        "default": "deterministic curriculum",
        "valid": "1..3",
    },
    "command": {
        "type": "int",
        "default": "deterministic curriculum",
        "valid": "0..5",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 5

# Deterministic fallbacks, all connected, transform-sensitive under codes 0..5,
# and pairwise non-equivalent under the full dihedral group.
_FALLBACK_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0)),
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum profile for this lesson position."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _normalize_cells(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    if not rows:
        return ()
    top, left = min(rows), min(cols)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _cells_to_mask(cells: Sequence[tuple[int, int]]) -> list[list[int]]:
    norm = _normalize_cells(cells)
    if not norm:
        return [[0]]
    height = max(row for row, _ in norm) + 1
    width = max(col for _, col in norm) + 1
    mask = full_grid(height, width, 0)
    for row, col in norm:
        mask[row][col] = 1
    return mask


def _mask_support(mask: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return _normalize_cells(
        [(row, col) for row, values in enumerate(mask)
         for col, value in enumerate(values) if value != 0]
    )


def _rotate_cw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _transform_mask(mask: Sequence[Sequence[int]], code: int) -> list[list[int]]:
    grid = [list(row) for row in mask]
    transforms = {
        0: lambda value: value,
        1: _rotate_cw,
        2: _rotate_180,
        3: _rotate_ccw,
        4: _flip_lr,
        5: _flip_ud,
    }
    if code not in transforms:
        raise ValueError(f"transform code must be 0..5, got {code!r}")
    return transforms[code](grid)


def _dihedral_signatures(cells: Sequence[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    mask = _cells_to_mask(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    rotated = mask
    for _ in range(4):
        variants.add(_mask_support(rotated))
        variants.add(_mask_support(_flip_lr(rotated)))
        rotated = _rotate_cw(rotated)
    return variants


def _dihedral_key(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_dihedral_signatures(cells))


def _all_six_transforms_distinct(cells: Sequence[tuple[int, int]]) -> bool:
    mask = _cells_to_mask(cells)
    return len({_mask_support(_transform_mask(mask, code)) for code in range(6)}) == 6


def _connected(cells: Sequence[tuple[int, int]]) -> bool:
    support = set(cells)
    if not support:
        return False
    frontier = [next(iter(support))]
    seen = {frontier[0]}
    while frontier:
        row, col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + dr, col + dc)
            if neighbor in support and neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return len(seen) == len(support)


def _random_shape(rng, band: str) -> tuple[tuple[int, int], ...]:
    limits = {
        "easy": (3, 4, 6),
        "medium": (4, 5, 8),
        "hard": (5, 6, 10),
    }
    max_dim, min_area, max_area = limits[band]
    target = rng.randint(min_area, max_area)
    cells = {(rng.randint(0, max_dim - 1), rng.randint(0, max_dim - 1))}
    guard = 0
    while len(cells) < target and guard < 500:
        guard += 1
        row, col = rng.choice(sorted(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        nr, nc = row + dr, col + dc
        if 0 <= nr < max_dim and 0 <= nc < max_dim:
            cells.add((nr, nc))
    return _normalize_cells(tuple(cells))


def _shape_library(rng, band: str) -> list[tuple[tuple[int, int], ...]]:
    shapes: list[tuple[tuple[int, int], ...]] = []
    keys: set[tuple[tuple[int, int], ...]] = set()
    for _ in range(1500):
        candidate = _random_shape(rng, band)
        if len(candidate) < 4 or not _connected(candidate):
            continue
        if not _all_six_transforms_distinct(candidate):
            continue
        key = _dihedral_key(candidate)
        if key in keys:
            continue
        shapes.append(candidate)
        keys.add(key)
        if len(shapes) == 3:
            return shapes
    for fallback in _FALLBACK_SHAPES:
        key = _dihedral_key(fallback)
        if key not in keys:
            shapes.append(fallback)
            keys.add(key)
        if len(shapes) == 3:
            return shapes
    raise RuntimeError("could not construct three distinguishable library shapes")


def _paint(grid: list[list[int]], top: int, left: int,
           cells: Sequence[tuple[int, int]], color: int) -> None:
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
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _panel_cells(grid: Sequence[Sequence[int]], left: int) -> list[tuple[int, int]]:
    return [
        (row - 1, col - left)
        for row in range(1, 6)
        for col in range(left, left + 5)
        if grid[row][col] != 0
    ]


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if (height, width) != (6, 17):
        return {"errors": [f"expected 6x17 grid, got {height}x{width}"]}

    index, command, fill_color, border_color = grid[0][:4]
    if not 1 <= index <= 3:
        errors.append(f"panel index must be 1..3, got {index!r}")
    if not 0 <= command <= 5:
        errors.append(f"transform code must be 0..5, got {command!r}")
    if fill_color == 0:
        errors.append("fill color must be nonzero")
    if border_color == 0:
        errors.append("border color must be nonzero")
    if fill_color == border_color:
        errors.append("fill and border colors must be distinct")
    if any(grid[0][col] != 0 for col in range(4, 17)):
        errors.append("header columns 4..16 must be blank")
    for separator in (5, 11):
        if any(grid[row][separator] != 0 for row in range(1, 6)):
            errors.append(f"separator column {separator} must be blank")

    panels: list[dict[str, Any]] = []
    for panel_number, left in enumerate((0, 6, 12), start=1):
        cells = _panel_cells(grid, left)
        colors = {
            grid[row][col]
            for row in range(1, 6)
            for col in range(left, left + 5)
            if grid[row][col] != 0
        }
        if not cells:
            errors.append(f"library panel {panel_number} is empty")
        if len(colors) > 1:
            errors.append(f"library panel {panel_number} must be monochrome")
        if cells and not _connected(cells):
            errors.append(f"library panel {panel_number} must be 4-connected")
        panels.append({"cells": _normalize_cells(cells), "colors": colors})

    profile = _PROFILE_BY_PAIR.get((index, command))
    return {
        "errors": errors,
        "index": index,
        "command": command,
        "fill_color": fill_color,
        "border_color": border_color,
        "panels": panels,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int]:
    """Recover the exact declared panel index and transform code."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "panel_index": analysis["index"],
        "command": analysis["command"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding layouts."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    realized = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and realized.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {realized.get(name)!r}"
            )
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    scheduled = schedule_profile(seed, sample_index, band)
    scheduled_index, scheduled_command = _PROFILE_BY_NAME[scheduled]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    index_bounds = (1, 3) if overrides.get("panel_index") is not None else (scheduled_index, scheduled_index)
    command_bounds = (0, 5) if overrides.get("command") is not None else (scheduled_command, scheduled_command)
    index = ctx.draw_int("panel_index", *index_bounds)
    command = ctx.draw_int("command", *command_bounds)
    rng = ctx.draw_rng("library")
    shapes = _shape_library(rng, band)
    fill_color, border_color = rng.sample(list(range(2, 10)), 2)

    grid = full_grid(6, 17, 0)
    grid[0][0] = index
    grid[0][1] = command
    grid[0][2] = fill_color
    grid[0][3] = border_color
    for left, shape in zip((0, 6, 12), shapes):
        _paint(grid, 1, left, shape, 1)
    return grid


def _selected_mask(grid: Sequence[Sequence[int]], index: int) -> list[list[int]]:
    left = (0, 6, 12)[index - 1]
    cells = _panel_cells(grid, left)
    return _cells_to_mask(cells)


def _output_from_parts(mask: Sequence[Sequence[int]], command: int,
                       fill_color: int, border_color: int,
                       *, include_border: bool = True,
                       preserve_source: bool = False) -> list[list[int]]:
    transformed = _transform_mask(mask, command)
    inner_color = 1 if preserve_source else fill_color
    if not include_border:
        return [
            [inner_color if value else 0 for value in row]
            for row in transformed
        ]
    height, width = len(transformed) + 2, len(transformed[0]) + 2
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            if row in (0, height - 1) or col in (0, width - 1):
                output[row][col] = border_color
    for row, values in enumerate(transformed):
        for col, value in enumerate(values):
            if value:
                output[row + 1][col + 1] = inner_color
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; the synchronized Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    mask = _selected_mask(grid, analysis["index"])
    return _output_from_parts(
        mask,
        analysis["command"],
        analysis["fill_color"],
        analysis["border_color"],
    )


def strict_canonical_like(grid) -> list[str]:
    """Require a lawful, shortcut-resistant library-decoding instance."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    palette_size = len({value for row in grid for value in row})
    if not 4 <= palette_size <= 6:
        errors.append(f"input palette size must stay in canonical range 4..6, got {palette_size}")
    output = rule_mirror(grid)
    if not any(value == analysis["fill_color"] for row in output for value in row):
        errors.append("output must visibly contain the fill color")
    if not any(value == analysis["border_color"] for row in output for value in row):
        errors.append("output must visibly contain the border color")
    return errors


def _rival_always_panel(panel_index: int):
    def rival(grid):
        analysis = _analysis(grid)
        if analysis["errors"]:
            return [list(row) for row in grid]
        return _output_from_parts(
            _selected_mask(grid, panel_index),
            analysis["command"],
            analysis["fill_color"],
            analysis["border_color"],
        )
    return rival


def _rival_ignore_transform(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _output_from_parts(
        _selected_mask(grid, analysis["index"]),
        0,
        analysis["fill_color"],
        analysis["border_color"],
    )


def _rival_always_rotate_cw(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _output_from_parts(
        _selected_mask(grid, analysis["index"]),
        1,
        analysis["fill_color"],
        analysis["border_color"],
    )


def _rival_no_border(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _output_from_parts(
        _selected_mask(grid, analysis["index"]),
        analysis["command"],
        analysis["fill_color"],
        analysis["border_color"],
        include_border=False,
    )


def _rival_preserve_source_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _output_from_parts(
        _selected_mask(grid, analysis["index"]),
        analysis["command"],
        analysis["fill_color"],
        analysis["border_color"],
        preserve_source=True,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "always_panel_1": _rival_always_panel(1),
    "always_panel_3": _rival_always_panel(3),
    "ignore_transform_code": _rival_ignore_transform,
    "always_rotate_cw": _rival_always_rotate_cw,
    "omit_rectangular_border": _rival_no_border,
    "preserve_source_color": _rival_preserve_source_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _profile_witness(*, index: int | None = None,
                     command: int | None = None):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        if analysis["errors"]:
            return False
        return ((index is None or analysis["index"] == index)
                and (command is None or analysis["command"] == command))
    return witness


SEMANTIC_WITNESSES = {
    "panel_index_1": _profile_witness(index=1),
    "panel_index_2": _profile_witness(index=2),
    "panel_index_3": _profile_witness(index=3),
    "transform_code_0": _profile_witness(command=0),
    "transform_code_1": _profile_witness(command=1),
    "transform_code_2": _profile_witness(command=2),
    "transform_code_3": _profile_witness(command=3),
    "transform_code_4": _profile_witness(command=4),
    "transform_code_5": _profile_witness(command=5),
    "rectangular_border_visible": lambda grid: _rival_no_border(grid) != rule_mirror(grid),
    "fill_recolor_visible": lambda grid: _rival_preserve_source_color(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "panel_index_1": ["always_panel_3"],
    "panel_index_2": ["always_panel_1", "always_panel_3"],
    "panel_index_3": ["always_panel_1"],
    "transform_code_0": ["always_rotate_cw"],
    "transform_code_1": ["ignore_transform_code"],
    "transform_code_2": ["ignore_transform_code"],
    "transform_code_3": ["ignore_transform_code"],
    "transform_code_4": ["ignore_transform_code"],
    "transform_code_5": ["ignore_transform_code"],
    "rectangular_border_visible": ["omit_rectangular_border"],
    "fill_recolor_visible": ["preserve_source_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a named shortcut viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    indices: set[int] = set()
    commands: set[int] = set()
    for position, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {position} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {position} disagrees with the canonical pipeline")
        analysis = _analysis(pair["input"])
        if not analysis["errors"]:
            indices.add(analysis["index"])
            commands.add(analysis["command"])
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the canonical pipeline")
    if indices != {1, 2, 3}:
        reasons.append("demonstrations must cover all three panel indices")
    if len(commands) < 5:
        reasons.append("demonstrations must cover five distinct transform codes")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
