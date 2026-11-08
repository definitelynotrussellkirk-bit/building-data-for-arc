"""Generator for ARC task ``5ad4f10b``.

The input contains a block-pixel shape whose bounding box is a 3x3 lattice of
solid square macro-cells, plus noisy cells in one other color.  The canonical
Racket rule emits the 3x3 occupancy mask of that shape, recolored with the
noise color.

This module intentionally keeps the Racket program as the sole output oracle.
Its job is to generate inputs whose intended rule is structurally recoverable
and whose declared controls are exact and observable from the returned grid.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f5b34c95896"
TASK_ID = "3f5b34c95896"
VERSION = "4.0.0"  # honest axes, structural grammar, semantic lesson schedule
RULE_HASH = "d802005f9274"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A black 20..24 by 23..26 grid contains exactly two foreground colors. "
    "One color forms 4..7 solid square macro-cells on a 3x3 lattice; its "
    "overall bounding box is therefore three equal blocks tall and wide. "
    "The other color appears as 12..55 small noise components. Divide the "
    "shape-color bounding box into its 3x3 macro-cells and output a 3x3 grid: "
    "paint a cell with the noise color exactly when the corresponding source "
    "macro-cell is occupied, otherwise paint 0."
)

INVARIANTS = [
    "background is 0 and exactly two nonzero colors are present",
    "the shape color is recoverable as the color of the largest 4-connected component",
    "the shape-color bbox is a square 3x3 lattice of solid equal-sized blocks",
    "4..7 macro-cells are occupied and collectively span all three rows and columns",
    "every noise-color component is smaller than one shape block",
    "the output is the nontrivial 3x3 occupancy mask recolored with the noise color",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled over canonical heights",
        "valid": "20..24",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled over canonical widths",
        "valid": "23..26",
    },
    "block_size": {
        "type": "int",
        "default": "difficulty/sample schedule",
        "valid": "3..5",
    },
    "n_occupied": {
        "type": "int",
        "default": "4..5 easy, 5..6 medium, 6..7 hard",
        "valid": "4..7",
    },
    "dot_count": {
        "type": "int",
        "default": "17..40 easy, 26..48 medium, 36..55 hard",
        "valid": "12..55",
    },
    "shape_color": {
        "type": "color",
        "default": "seed/sample schedule over 1..9",
        "valid": "1..9",
    },
    "dot_color": {
        "type": "color",
        "default": "seed/sample schedule over 1..9, distinct from shape_color",
        "valid": "1..9",
    },
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_RANGES = {
    "grid_h": (20, 24),
    "grid_w": (23, 26),
    "block_size": (3, 5),
    "n_occupied": (4, 7),
    "dot_count": (12, 55),
    "shape_color": (1, 9),
    "dot_color": (1, 9),
}
_CANONICAL_PROFILES = ((22, 23), (20, 24), (24, 23), (22, 26))
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")
    if (
        overrides.get("shape_color") is not None
        and overrides.get("shape_color") == overrides.get("dot_color")
    ):
        raise ValueError("shape_color and dot_color must be distinct")


def _draw_scheduled_int(ctx, name: str, scheduled: int) -> int:
    lo, hi = _AXIS_RANGES[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _draw_scheduled_color(
    ctx, name: str, scheduled: int, *, excluded: Iterable[int] = ()
) -> int:
    choices = [value for value in range(1, 10) if value not in set(excluded)]
    if ctx.overrides.get(name) is not None:
        return int(ctx.draw_choice(name, choices))
    if scheduled not in choices:
        scheduled = choices[0]
    return int(ctx.draw_choice(name, [scheduled]))


def _defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, int]:
    band = "medium" if difficulty is None else difficulty
    phase = sample_index % 3
    grid_h, grid_w = _CANONICAL_PROFILES[sample_index % len(_CANONICAL_PROFILES)]

    if band == "easy":
        block_size = (3, 3, 4)[phase]
        n_occupied = (4, 4, 5)[phase]
        dot_count = (40, 17, 32)[phase]
    elif band == "hard":
        block_size = (3, 5, 5)[phase]
        n_occupied = (6, 6, 7)[phase]
        dot_count = (55, 36, 55)[phase]
    else:
        # The first two demonstrations deliberately have equal occupied-count
        # but different masks.  The first also has more noise cells than total
        # shape cells (48 > 5*3^2), refuting total-frequency shortcuts.
        block_size = (3, 4, 5)[phase]
        n_occupied = (5, 5, 6)[phase]
        dot_count = (48, 30, 40)[phase]

    # A simple arithmetic schedule guarantees distinct color roles across the
    # three-demo lesson while remaining uniform over seeds.  Values are still
    # recorded through GenCtx below, so exact provenance is preserved.
    shape_color = 1 + ((seed + 2 * sample_index) % 9)
    dot_color = 1 + ((seed + 2 * sample_index + 1) % 9)
    if dot_color == shape_color:
        dot_color = 1 + (dot_color % 9)

    return {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "block_size": block_size,
        "n_occupied": n_occupied,
        "dot_count": dot_count,
        "shape_color": shape_color,
        "dot_color": dot_color,
    }


def _mask_transform(mask: frozenset[tuple[int, int]], index: int):
    def transform(cell: tuple[int, int]) -> tuple[int, int]:
        row, col = cell
        if index == 0:
            return row, col
        if index == 1:
            return col, 2 - row
        if index == 2:
            return 2 - row, 2 - col
        if index == 3:
            return 2 - col, row
        if index == 4:
            return row, 2 - col
        if index == 5:
            return 2 - row, col
        if index == 6:
            return col, row
        return 2 - col, 2 - row

    return frozenset(transform(cell) for cell in mask)


def _orbit_size(mask: frozenset[tuple[int, int]]) -> int:
    return len({_mask_transform(mask, index) for index in range(8)})


def _candidate_masks(n_occupied: int, phase: int) -> list[frozenset[tuple[int, int]]]:
    all_cells = tuple((row, col) for row in range(3) for col in range(3))
    if phase == 0:
        required, forbidden = {(0, 0)}, {(0, 2)}
    elif phase == 1:
        required, forbidden = {(0, 2)}, {(0, 0)}
    else:
        required, forbidden = {(1, 1)}, set()

    candidates: list[frozenset[tuple[int, int]]] = []
    for combo in combinations(all_cells, n_occupied):
        mask = frozenset(combo)
        if not required <= mask or mask & forbidden:
            continue
        if {row for row, _col in mask} != {0, 1, 2}:
            continue
        if {col for _row, col in mask} != {0, 1, 2}:
            continue
        # Ordinary lessons use fully asymmetric masks so rotations/reflections
        # are not answer-equivalent shortcuts.  Canonical symmetric masks are
        # still accepted by self_check; this is a generation prior only.
        if _orbit_size(mask) != 8:
            continue
        candidates.append(mask)
    if not candidates:
        raise ValueError(
            f"no asymmetric spanning 3x3 mask for n_occupied={n_occupied}, phase={phase}"
        )
    return candidates


def _choose_mask(ctx, n_occupied: int, sample_index: int):
    candidates = _candidate_masks(n_occupied, sample_index % 3)
    rng = ctx.draw_rng("occupancy_mask")
    return candidates[rng.randrange(len(candidates))]


def _shape_origin(
    ctx, sample_index: int, grid_h: int, grid_w: int, shape_size: int
) -> tuple[int, int]:
    max_row = grid_h - shape_size
    max_col = grid_w - shape_size
    if max_row < 0 or max_col < 0:
        raise ValueError(
            f"block_size requires {shape_size}x{shape_size} bbox inside "
            f"{grid_h}x{grid_w} grid"
        )
    phase = sample_index % 3
    if phase == 0:
        return min(1, max_row), min(1, max_col)
    if phase == 1:
        return max_row // 2, max_col // 2
    return max_row, max_col


def _dot_component(grid, start: tuple[int, int], dot_color: int):
    h, w = len(grid), len(grid[0])
    queue = deque([start])
    seen = {start}
    while queue:
        row, col = queue.popleft()
        for dr, dc in _NEIGHBORS4:
            nxt = row + dr, col + dc
            if (
                0 <= nxt[0] < h
                and 0 <= nxt[1] < w
                and nxt not in seen
                and grid[nxt[0]][nxt[1]] == dot_color
            ):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _can_add_dot(grid, row: int, col: int, dot_color: int, max_component: int) -> bool:
    neighboring_components: list[set[tuple[int, int]]] = []
    seen_neighbors: set[tuple[int, int]] = set()
    h, w = len(grid), len(grid[0])
    for dr, dc in _NEIGHBORS4:
        nxt = row + dr, col + dc
        if not (0 <= nxt[0] < h and 0 <= nxt[1] < w):
            continue
        if grid[nxt[0]][nxt[1]] != dot_color or nxt in seen_neighbors:
            continue
        component = _dot_component(grid, nxt, dot_color)
        neighboring_components.append(component)
        seen_neighbors.update(component)
    return 1 + sum(len(component) for component in neighboring_components) <= max_component


def _place_dots(grid, ctx, dot_color: int, dot_count: int, block_size: int) -> None:
    max_component = min(4, block_size * block_size - 1)
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0
    ]
    rng = ctx.draw_rng("dot_layout")
    rng.shuffle(candidates)
    placed = 0
    for row, col in candidates:
        if placed >= dot_count:
            break
        if grid[row][col] != 0:
            continue
        if not _can_add_dot(grid, row, col, dot_color, max_component):
            continue
        grid[row][col] = dot_color
        placed += 1
    if placed != dot_count:
        raise ValueError(
            f"could place only {placed}/{dot_count} noise cells while keeping "
            f"components below one {block_size}x{block_size} shape block"
        )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _defaults(seed, sample_index, difficulty)

    grid_h = _draw_scheduled_int(ctx, "grid_h", defaults["grid_h"])
    grid_w = _draw_scheduled_int(ctx, "grid_w", defaults["grid_w"])
    block_size = _draw_scheduled_int(ctx, "block_size", defaults["block_size"])
    n_occupied = _draw_scheduled_int(ctx, "n_occupied", defaults["n_occupied"])
    dot_count = _draw_scheduled_int(ctx, "dot_count", defaults["dot_count"])

    requested_dot = overrides.get("dot_color")
    shape_scheduled = defaults["shape_color"]
    if requested_dot is not None and shape_scheduled == requested_dot:
        shape_scheduled = 1 + (shape_scheduled % 9)
    shape_color = _draw_scheduled_color(
        ctx, "shape_color", shape_scheduled, excluded=(() if requested_dot is None else (requested_dot,))
    )
    dot_color = _draw_scheduled_color(
        ctx, "dot_color", defaults["dot_color"], excluded=(shape_color,)
    )

    mask = _choose_mask(ctx, n_occupied, sample_index)
    shape_size = 3 * block_size
    row0, col0 = _shape_origin(ctx, sample_index, grid_h, grid_w, shape_size)
    grid = full_grid(grid_h, grid_w, 0)
    for macro_row, macro_col in mask:
        for dr in range(block_size):
            for dc in range(block_size):
                grid[
                    row0 + macro_row * block_size + dr
                ][col0 + macro_col * block_size + dc] = shape_color

    _place_dots(grid, ctx, dot_color, dot_count, block_size)
    return grid


def _components(grid) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                current = queue.popleft()
                cells.add(current)
                for dr, dc in _NEIGHBORS4:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            components.append({"color": color, "cells": frozenset(cells), "size": len(cells)})
    return components


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular and nonempty"]
    grid_h, grid_w = len(grid), width
    if not 20 <= grid_h <= 24:
        errors.append(f"grid height must be 20..24, got {grid_h}")
    if not 23 <= grid_w <= 26:
        errors.append(f"grid width must be 23..26, got {grid_w}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
        return {}, errors

    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 2:
        errors.append(f"expected exactly two nonzero colors, got {colors}")
        return {}, errors

    components = _components(grid)
    if not components:
        errors.append("missing foreground components")
        return {}, errors
    largest_size = max(component["size"] for component in components)
    largest_colors = {
        component["color"] for component in components if component["size"] == largest_size
    }
    if len(largest_colors) != 1:
        errors.append(
            "largest 4-connected component is tied across colors, so the Racket shape color is ambiguous"
        )
        return {}, errors
    shape_color = next(iter(largest_colors))
    dot_color = next(color for color in colors if color != shape_color)
    shape_cells = {
        (row, col)
        for row in range(grid_h)
        for col in range(grid_w)
        if grid[row][col] == shape_color
    }
    dot_cells = {
        (row, col)
        for row in range(grid_h)
        for col in range(grid_w)
        if grid[row][col] == dot_color
    }

    row0 = min(row for row, _col in shape_cells)
    row1 = max(row for row, _col in shape_cells)
    col0 = min(col for _row, col in shape_cells)
    col1 = max(col for _row, col in shape_cells)
    bbox_h, bbox_w = row1 - row0 + 1, col1 - col0 + 1
    if bbox_h % 3 or bbox_w % 3:
        errors.append(f"shape bbox {bbox_h}x{bbox_w} is not divisible into a 3x3 lattice")
        return {}, errors
    block_h, block_w = bbox_h // 3, bbox_w // 3
    if block_h != block_w or not 3 <= block_h <= 5:
        errors.append(
            f"shape macro-blocks must be square with size 3..5, got {block_h}x{block_w}"
        )
        return {}, errors
    block_size = block_h

    occupied: set[tuple[int, int]] = set()
    for macro_row in range(3):
        for macro_col in range(3):
            count = sum(
                grid[row][col] == shape_color
                for row in range(row0 + macro_row * block_size, row0 + (macro_row + 1) * block_size)
                for col in range(col0 + macro_col * block_size, col0 + (macro_col + 1) * block_size)
            )
            if count == block_size * block_size:
                occupied.add((macro_row, macro_col))
            elif count != 0:
                errors.append(
                    f"macro-cell ({macro_row},{macro_col}) is partial: {count}/{block_size * block_size} shape cells"
                )
    if not 4 <= len(occupied) <= 7:
        errors.append(f"occupied macro-cell count must be 4..7, got {len(occupied)}")
    if occupied and {row for row, _col in occupied} != {0, 1, 2}:
        errors.append("occupied macro-cells must span all three lattice rows")
    if occupied and {col for _row, col in occupied} != {0, 1, 2}:
        errors.append("occupied macro-cells must span all three lattice columns")
    expected_shape_cells = len(occupied) * block_size * block_size
    if len(shape_cells) != expected_shape_cells:
        errors.append(
            f"shape color has {len(shape_cells)} cells, expected {expected_shape_cells} from solid macro-cells"
        )

    if not 12 <= len(dot_cells) <= 55:
        errors.append(f"noise-cell count must be 12..55, got {len(dot_cells)}")
    dot_components = [
        component["size"] for component in components if component["color"] == dot_color
    ]
    if dot_components and max(dot_components) >= block_size * block_size:
        errors.append(
            "a noise component is at least as large as one shape block, making largest-object color selection unsafe"
        )

    facts = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "block_size": block_size,
        "n_occupied": len(occupied),
        "dot_count": len(dot_cells),
        "shape_color": shape_color,
        "dot_color": dot_color,
        "shape_bbox": (row0, col0, row1, col1),
        "occupied": frozenset(occupied),
        "orbit_size": _orbit_size(frozenset(occupied)) if occupied else 0,
        "shape_cell_count": len(shape_cells),
        "largest_dot_component": max(dot_components, default=0),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {name: int(facts[name]) for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes, including override drift."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors and requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name} requested {value!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is a conservative superset of all canonical inputs."""
    _facts, errors = _analyze(grid)
    return errors


def _witness_asymmetric_mask(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["orbit_size"] == 8


def _witness_frequency_reversal(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["dot_count"] > facts["shape_cell_count"]


def _witness_off_origin(grid) -> bool:
    facts, errors = _analyze(grid)
    if errors:
        return False
    row0, col0, _row1, _col1 = facts["shape_bbox"]
    return (row0, col0) != (1, 1)


def _witness_nontrivial_mask(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and 0 < facts["n_occupied"] < 9


SEMANTIC_WITNESSES = {
    "nontrivial_occupancy_mask": _witness_nontrivial_mask,
    "fully_asymmetric_mask": _witness_asymmetric_mask,
    "dot_total_exceeds_shape_total": _witness_frequency_reversal,
    "shape_position_varies": _witness_off_origin,
}


def _mask_from_output(output) -> tuple[int, frozenset[tuple[int, int]]] | None:
    if (
        not isinstance(output, list)
        or len(output) != 3
        or any(not isinstance(row, list) or len(row) != 3 for row in output)
    ):
        return None
    colors = {value for row in output for value in row if value != 0}
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    mask = frozenset(
        (row, col)
        for row in range(3)
        for col in range(3)
        if output[row][col] == color
    )
    if any(value not in (0, color) for row in output for value in row):
        return None
    return color, mask


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that falsify the principal rival rules."""
    del query
    if len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    facts_list: list[dict[str, Any]] = []
    output_masks: list[frozenset[tuple[int, int]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} is not a pair dictionary")
            continue
        facts, errors = _analyze(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} input violates grammar: {errors[0]}")
            continue
        parsed = _mask_from_output(pair.get("output"))
        if parsed is None:
            reasons.append(f"demo {index} output is not a one-color 3x3 mask")
            continue
        output_color, output_mask = parsed
        if output_color != facts["dot_color"] or output_mask != facts["occupied"]:
            reasons.append(f"demo {index} output does not encode its source occupancy in dot color")
            continue
        facts_list.append(facts)
        output_masks.append(output_mask)

    if len(facts_list) < EXAMPLES_NEEDED:
        return reasons or ["too few complete demonstrations"]
    if len({facts["block_size"] for facts in facts_list}) < 2:
        reasons.append("no demo pair refutes a fixed source block size")
    if len({facts["shape_bbox"][:2] for facts in facts_list}) < 2:
        reasons.append("no demo pair refutes a fixed global shape position")
    if len({(facts["shape_color"], facts["dot_color"]) for facts in facts_list}) < 2:
        reasons.append("color roles do not vary across demonstrations")
    by_count: dict[int, set[frozenset[tuple[int, int]]]] = {}
    for facts, mask in zip(facts_list, output_masks):
        by_count.setdefault(facts["n_occupied"], set()).add(mask)
    if not any(len(masks) >= 2 for masks in by_count.values()):
        reasons.append("no equal-count/different-mask demos refute count-only prediction")
    if not any(facts["dot_count"] > facts["shape_cell_count"] for facts in facts_list):
        reasons.append("no demo refutes choosing the shape color by total frequency")
    if not any(facts["orbit_size"] == 8 for facts in facts_list):
        reasons.append("no asymmetric output refutes rotation/reflection shortcuts")
    return reasons
