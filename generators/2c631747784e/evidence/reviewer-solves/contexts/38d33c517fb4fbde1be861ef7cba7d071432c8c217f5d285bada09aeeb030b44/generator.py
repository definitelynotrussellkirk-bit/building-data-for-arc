"""Generator for ARC task 5792cb4d / content hash 2c631747784e.

The input is a cyan (8) background containing exactly one simple 4-connected
path.  The output keeps the path coordinates and reverses only the sequence of
colors encountered while walking from either endpoint.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c631747784e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1b96d7f1e866"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a cyan-8 background, find the single non-branching 4-connected path. "
    "Walk from either endpoint, reverse the encountered color sequence, and "
    "repaint those same coordinates in the reversed order."
)

INVARIANTS = [
    "the background is color 8",
    "all non-background cells form one simple 4-connected path",
    "the path has exactly two endpoints",
    "the path contains 8-32 cells and 2-7 distinct non-cyan colors",
    "the path color sequence is non-palindromic, so reversal is visible",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "8..16"},
    "path_length": {"type": "int", "default": "difficulty-aware", "valid": "8..32"},
    "n_distinct_colors": {"type": "int", "default": "difficulty-aware", "valid": "2..7"},
    "anchor_corner": {"type": "bool", "default": "scheduled", "valid": "true|false"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 0.15

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_LENGTHS = (8, 12, 28)


def _axis_int(ctx: Any, label: str, lo: int, hi: int, default: int | tuple[int, int]) -> int:
    """Use full declared bounds for overrides and a narrower lawful default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if isinstance(default, tuple):
        return ctx.draw_int(label, default[0], default[1])
    return ctx.draw_int(label, default, default)


def _axis_choice(ctx: Any, label: str, all_options: tuple[Any, ...], default: Any) -> Any:
    options = all_options if label in ctx.overrides else (default,)
    return ctx.draw_choice(label, options)


def _turn_count(path: list[tuple[int, int]]) -> int:
    directions = [
        (b[0] - a[0], b[1] - a[1])
        for a, b in zip(path, path[1:])
    ]
    return sum(a != b for a, b in zip(directions, directions[1:]))


def _row_major_mapping_matches_path(path: list[tuple[int, int]]) -> bool:
    """Return whether row-major reversal implements the same cell mapping.

    Comparing only the two orders is insufficient: other permutations can also
    commute with reversal.  Compare the source cell assigned to every
    destination cell instead, so every retained geometry can separate the
    intended path-order rule from the row-major shortcut.
    """
    path_index = {cell: index for index, cell in enumerate(path)}
    ordered = sorted(path)
    ordered_index = {cell: index for index, cell in enumerate(ordered)}
    n = len(path)
    for destination in path:
        intended_source = path[n - 1 - path_index[destination]]
        row_major_source = ordered[n - 1 - ordered_index[destination]]
        if intended_source != row_major_source:
            return False
    return True


def _horizontal_master(h: int, run_width: int) -> list[tuple[int, int]]:
    """Return a maximal induced snake with separated horizontal runs.

    Consecutive occupied runs sit two rows apart and are joined by a single
    connector.  Thus no nonconsecutive path cells are 4-neighbors.
    """
    path: list[tuple[int, int]] = []
    for run_index, row in enumerate(range(0, h, 2)):
        columns = (
            range(run_width)
            if run_index % 2 == 0
            else range(run_width - 1, -1, -1)
        )
        path.extend((row, col) for col in columns)
        if row + 2 < h:
            connector_col = run_width - 1 if run_index % 2 == 0 else 0
            path.append((row + 1, connector_col))
    return path


def _transform_path(
    path: list[tuple[int, int]], h: int, w: int, *, transpose: bool, flip_r: bool, flip_c: bool
) -> list[tuple[int, int]]:
    transformed: list[tuple[int, int]] = []
    for r, c in path:
        if transpose:
            r, c = c, r
        if flip_r:
            r = h - 1 - r
        if flip_c:
            c = w - 1 - c
        transformed.append((r, c))
    return transformed


@lru_cache(maxsize=None)
def _path_candidates(
    h: int, w: int, length: int, anchor_corner: bool
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate shortcut-separating induced paths for every legal axis tuple."""
    candidates: set[tuple[tuple[int, int], ...]] = set()
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    for transpose in (False, True):
        source_h, source_w = (w, h) if transpose else (h, w)
        for run_width in range(3, source_w + 1):
            master = _horizontal_master(source_h, run_width)
            if len(master) < length:
                continue
            for flip_r in (False, True):
                for flip_c in (False, True):
                    variant = _transform_path(
                        master, h, w, transpose=transpose, flip_r=flip_r, flip_c=flip_c
                    )
                    for ordered_variant in (variant, list(reversed(variant))):
                        for start in range(0, len(ordered_variant) - length + 1):
                            segment = ordered_variant[start : start + length]
                            if _turn_count(segment) < 1:
                                continue
                            endpoint_corner = segment[0] in corners or segment[-1] in corners
                            if endpoint_corner != anchor_corner:
                                continue
                            if _row_major_mapping_matches_path(segment):
                                continue
                            candidates.add(tuple(segment))
    return tuple(sorted(candidates))

def _build_path(rng: Any, h: int, w: int, length: int, anchor_corner: bool) -> list[tuple[int, int]]:
    candidates = _path_candidates(h, w, length, anchor_corner)
    if not candidates:
        raise ValueError(
            f"no induced path candidate for h={h}, w={w}, length={length}, "
            f"anchor_corner={anchor_corner}"
        )
    return list(rng.choice(candidates))


def _grid_with_sequence(
    h: int, w: int, path: list[tuple[int, int]], sequence: list[int]
) -> list[list[int]]:
    grid = full_grid(h, w, 8)
    for (r, c), color in zip(path, sequence):
        grid[r][c] = color
    return grid


def _candidate_sequence(rng: Any, length: int, n_distinct: int) -> list[int]:
    palette = rng.sample([color for color in range(10) if color != 8], n_distinct)
    sequence = list(palette)
    sequence.extend(rng.choice(palette) for _ in range(length - n_distinct))
    rng.shuffle(sequence)
    return sequence


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    canonical_anchor = not overrides and int(sample_index) % 4 in (0, 1)

    if canonical_anchor:
        canonical_slot = (int(sample_index) // 2) % len(_CANONICAL_LENGTHS)
        default_length = _CANONICAL_LENGTHS[canonical_slot]
        h = _axis_int(ctx, "grid_h", 8, 16, 10)
        w = _axis_int(ctx, "grid_w", 8, 16, 10)
        path_length = _axis_int(ctx, "path_length", 8, 32, default_length)
        n_distinct = _axis_int(
            ctx, "n_distinct_colors", 2, 7, 7 if default_length == 28 else 6
        )
        anchor_corner = bool(_axis_choice(ctx, "anchor_corner", (False, True), False))
    else:
        if difficulty == "easy":
            h_default, w_default = (8, 10), (8, 10)
            length_default, colors_default = (8, 12), (2, 4)
        elif difficulty == "hard":
            h_default, w_default = (12, 16), (12, 16)
            length_default, colors_default = (20, 32), (5, 7)
        else:
            h_default, w_default = (9, 13), (9, 13)
            length_default, colors_default = (12, 22), (3, 6)
        h = _axis_int(ctx, "grid_h", 8, 16, h_default)
        w = _axis_int(ctx, "grid_w", 8, 16, w_default)
        path_length = _axis_int(ctx, "path_length", 8, 32, length_default)
        n_distinct = _axis_int(ctx, "n_distinct_colors", 2, 7, colors_default)
        default_anchor = bool((int(seed) + int(sample_index)) % 3 == 0)
        anchor_corner = bool(
            _axis_choice(ctx, "anchor_corner", (False, True), default_anchor)
        )

    path = _build_path(rng, h, w, path_length, anchor_corner)
    for _ in range(256):
        sequence = _candidate_sequence(rng, path_length, n_distinct)
        grid = _grid_with_sequence(h, w, path, sequence)
        authoritative = rule_mirror(grid)
        if authoritative == grid:
            continue
        if authoritative == _row_major_reverse(grid):
            continue
        if authoritative == _swap_endpoints_only(grid):
            continue
        if authoritative == _sort_path_colors(grid):
            continue
        errors = self_check(grid)
        if not errors:
            return grid
    raise ValueError("could not construct a shortcut-separating color sequence")


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "errors": [],
        "grid_h": 0,
        "grid_w": 0,
        "path": [],
        "degrees": {},
        "endpoints": [],
        "colors": [],
        "path_length": 0,
        "n_distinct_colors": 0,
        "anchor_corner": False,
        "turn_count": 0,
    }
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        info["errors"].append("grid must be a non-empty list of rows")
        return info
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        info["errors"].append("grid must be rectangular and non-empty")
        return info
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        info["errors"].append("grid values must be integer colors in 0..9")
        return info

    h, w = len(grid), width
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 8}
    info["grid_h"], info["grid_w"] = h, w
    if len(cells) < 2:
        info["errors"].append("expected at least two non-cyan path cells")
        return info

    degrees = {
        cell: sum((cell[0] + dr, cell[1] + dc) in cells for dr, dc in _DIRS)
        for cell in cells
    }
    endpoints = sorted(cell for cell, degree in degrees.items() if degree == 1)
    info["degrees"] = degrees
    info["endpoints"] = endpoints
    if len(endpoints) != 2 or any(degree not in (1, 2) for degree in degrees.values()):
        info["errors"].append(
            f"expected exactly two endpoints and no branches; degrees={sorted(degrees.values())}"
        )
        return info

    seen = {endpoints[0]}
    queue = deque([endpoints[0]])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRS:
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    if seen != cells:
        info["errors"].append("non-cyan cells are disconnected")
        return info

    path = [endpoints[0]]
    previous: tuple[int, int] | None = None
    while len(path) < len(cells):
        current = path[-1]
        neighbors = sorted(
            (current[0] + dr, current[1] + dc)
            for dr, dc in _DIRS
            if (current[0] + dr, current[1] + dc) in cells
            and (current[0] + dr, current[1] + dc) != previous
        )
        if not neighbors:
            info["errors"].append("path traversal ended before visiting every cell")
            return info
        previous, next_cell = current, neighbors[0]
        path.append(next_cell)

    colors = [grid[r][c] for r, c in path]
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    info.update(
        {
            "path": path,
            "colors": colors,
            "path_length": len(path),
            "n_distinct_colors": len(set(colors)),
            "anchor_corner": bool(path[0] in corners or path[-1] in corners),
            "turn_count": _turn_count(path),
        }
    )
    return info


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {axis: info[axis] for axis in AXES}


def self_check(grid: Any, *, difficulty: Any = None, meta: dict[str, Any] | None = None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if not 8 <= info["grid_h"] <= 16 or not 8 <= info["grid_w"] <= 16:
        errors.append("grid dimensions must each be in 8..16")
    if not 8 <= info["path_length"] <= 32:
        errors.append("path length must be in 8..32")
    if not 2 <= info["n_distinct_colors"] <= 7:
        errors.append("path must use 2-7 distinct non-cyan colors")
    if info["n_distinct_colors"] >= info["path_length"]:
        errors.append("path must repeat at least one color")
    if info["colors"] == list(reversed(info["colors"])):
        errors.append("path color sequence is palindromic, so reversal is invisible")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    info = _analyze(grid)
    reasons = self_check(grid)
    if reasons:
        return reasons
    if (info["grid_h"], info["grid_w"]) != (10, 10):
        reasons.append("canonical inputs are 10x10")
    if info["path_length"] not in _CANONICAL_LENGTHS:
        reasons.append("canonical path lengths are 8, 12, or 28")
    if info["n_distinct_colors"] not in (6, 7):
        reasons.append("canonical paths use six or seven distinct colors")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python semantic mirror used only for tests; Racket remains authority."""
    info = _analyze(grid)
    if info["errors"]:
        return []
    output = [row[:] for row in grid]
    for (r, c), color in zip(info["path"], reversed(info["colors"])):
        output[r][c] = color
    return output


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _row_major_reverse(grid: list[list[int]]) -> list[list[int]]:
    positions = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 8
    )
    colors = [grid[r][c] for r, c in positions]
    output = [row[:] for row in grid]
    for (r, c), color in zip(positions, reversed(colors)):
        output[r][c] = color
    return output


def _swap_endpoints_only(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    if info["errors"]:
        return []
    output = [row[:] for row in grid]
    first, last = info["path"][0], info["path"][-1]
    output[first[0]][first[1]], output[last[0]][last[1]] = (
        output[last[0]][last[1]],
        output[first[0]][first[1]],
    )
    return output


def _sort_path_colors(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    if info["errors"]:
        return []
    output = [row[:] for row in grid]
    for (r, c), color in zip(info["path"], sorted(info["colors"])):
        output[r][c] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_no_change": _identity,
    "reverse_row_major_noncyan_cells": _row_major_reverse,
    "swap_only_path_endpoints": _swap_endpoints_only,
    "sort_colors_along_path": _sort_path_colors,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _valid_info(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return info


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "visible_nonidentity_reversal": lambda grid: rule_mirror(grid) != _identity(grid),
    "path_order_differs_from_row_major": lambda grid: rule_mirror(grid) != _row_major_reverse(grid),
    "interior_cells_require_full_reversal": lambda grid: rule_mirror(grid) != _swap_endpoints_only(grid),
    "color_order_not_sorting": lambda grid: rule_mirror(grid) != _sort_path_colors(grid),
}

WITNESS_RIVALS = {
    "visible_nonidentity_reversal": ["identity_no_change"],
    "path_order_differs_from_row_major": ["reverse_row_major_noncyan_cells"],
    "interior_cells_require_full_reversal": ["swap_only_path_endpoints"],
    "color_order_not_sorting": ["sort_colors_along_path"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demonstrations: {name}")
    return reasons
