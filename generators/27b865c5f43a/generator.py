"""Generator for 17b:hard_119 — build an ordered pairwise-union gallery.

Input grammar
-------------
A 0-background 8x17..9x20 grid contains exactly three isolated,
monochrome, 4-connected shapes.  Their leftmost columns are distinct,
their source colors are distinct, every crop fits in 3x3, and the three
binary crops are different.  At least one crop has height 3 and at least
one has width 3.

Rule
----
Sort the shapes by leftmost column (top row breaks a tie), binary-crop
each shape, and top-left-pad all crops to the common 3x3 panel size.  Build
an ordered 3x3 gallery: panel (r,c) is the cellwise OR of shape r and shape
c, painted color 8.  Separate adjacent panels by one background row/column.

The canonical examples accidentally make both source-color order and top-row
order agree with left-to-right order.  Default generation therefore includes
non-monotone palettes and non-aligned rows, with executable rivals and witness
predicates, so every four-demonstration lesson teaches the intended ordering.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "27b865c5f43a"
TASK_ID = GENERATOR_ID
RULE_HASH = "de4d9d03f710"
VERSION = "3.0.0"
SUMMARY = (
    "Three distinct isolated shapes are ordered left-to-right, binary-cropped, "
    "top-left padded to 3x3, and expanded into a color-8 ordered pairwise-OR "
    "gallery with one-cell separators."
)

INVARIANTS = [
    "background is 0 and cells are ARC colors 0..9",
    "exactly three isolated monochrome 4-connected components",
    "component colors, leftmost columns, and binary crops are pairwise distinct",
    "every crop is at most 3x3 and the common panel size is exactly 3x3",
    "gallery ordering is by leftmost column, not source color or top row",
]

PALETTE_KINDS = ("ascending", "mixed", "permuted", "descending")
SHAPE_SETS = ("sparse", "mixed", "dense")
ROW_PATTERNS = ("aligned", "reverse", "valley", "peak")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical-profile schedule",
        "valid": "8..9",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical-profile schedule over 17,18,20",
        "valid": "17..20",
    },
    "palette_kind": {
        "type": "str",
        "default": "six-slot schedule with four color-order conflicts",
        "valid": "|".join(PALETTE_KINDS),
    },
    "shape_set": {
        "type": "str",
        "default": "three-slot schedule",
        "valid": "|".join(SHAPE_SETS),
    },
    "row_pattern": {
        "type": "str",
        "default": "four-slot schedule with three row-order conflicts",
        "valid": "|".join(ROW_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.75

_INT_DOMAINS = {
    "grid_h": tuple(range(8, 10)),
    "grid_w": tuple(range(17, 21)),
}
_STR_DOMAINS = {
    "palette_kind": PALETTE_KINDS,
    "shape_set": SHAPE_SETS,
    "row_pattern": ROW_PATTERNS,
}

_CANONICAL_PROFILES = ((8, 17), (8, 18), (9, 18), (9, 20))
_PROFILE_SCHEDULES = {
    None: _CANONICAL_PROFILES,
    "easy": ((8, 18), (8, 17), (9, 20), (9, 18)),
    "medium": ((9, 18), (8, 17), (9, 20), (8, 18)),
    "hard": ((9, 20), (9, 18), (8, 18), (8, 17)),
}
# Any five consecutive examples contain at least three color-order witnesses;
# after any one query rotation, the remaining four demos still contain one.
_PALETTE_SCHEDULE = (
    "ascending",
    "permuted",
    "descending",
    "mixed",
    "permuted",
    "descending",
)
_SHAPE_SCHEDULE = ("sparse", "mixed", "dense")
# Three of four positions conflict with top-row sorting.  This has the same
# query-rotation robustness as the palette schedule.
_ROW_SCHEDULE = ("aligned", "reverse", "valley", "peak")

_PALETTES = {
    "ascending": (2, 3, 4),
    "mixed": (2, 5, 8),
    "permuted": (7, 2, 5),
    "descending": (9, 6, 1),
}
_ROW_OFFSETS = {
    "aligned": (0, 0, 0),
    "reverse": (2, 1, 0),
    "valley": (1, 0, 1),
    "peak": (0, 1, 0),
}
# Each triplet has a unique ordered cell-count signature, making shape_set
# exactly observable without exposing a brittle template identifier.
_SHAPES = {
    "sparse": (
        ((0, 0), (1, 0), (2, 0), (2, 1)),                    # L tetromino, 3x2
        ((0, 0), (0, 1), (0, 2), (1, 1)),                    # T tetromino, 2x3
        ((0, 1), (0, 2), (1, 0), (1, 1)),                    # S tetromino, 2x3
    ),
    "mixed": (
        ((0, 0), (1, 0), (2, 0), (2, 1)),                    # 4
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),            # 5
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),    # 6, 3x3
    ),
    "dense": (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),    # 6
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        tuple((row, col) for row in range(3) for col in range(3) if (row, col) != (1, 1)),
    ),
}


def _validate_request(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value} outside {domain[0]}..{domain[-1]}")
    for name, domain in _STR_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value!r} not in {domain}")


def _scheduled_axis(ctx, name: str, domain: tuple[Any, ...], scheduled: Any) -> Any:
    """Honor exact overrides while recording deterministic curriculum defaults."""
    value = ctx.draw_choice(name, domain)
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return value
    # GenCtx currently exposes no public scheduled-value setter.  _record is the
    # same provenance path used by typed draws and is isolated here for migration.
    return ctx._record(name, scheduled, from_override=False)


def _default_axes(
    sample_index: int, difficulty: str | None
) -> tuple[int, int, str, str, str]:
    grid_h, grid_w = _PROFILE_SCHEDULES[difficulty][sample_index % 4]
    palette = _PALETTE_SCHEDULE[sample_index % len(_PALETTE_SCHEDULE)]
    shape_set = _SHAPE_SCHEDULE[sample_index % len(_SHAPE_SCHEDULE)]
    row_pattern = _ROW_SCHEDULE[sample_index % len(_ROW_SCHEDULE)]
    return grid_h, grid_w, palette, shape_set, row_pattern


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _transform_shape(
    shape: tuple[tuple[int, int], ...], transform: int
) -> tuple[tuple[int, int], ...]:
    """Apply a bbox-preserving dihedral transform for seed-level diversity."""
    height, width = _shape_dims(shape)
    if transform == 0:
        cells = shape
    elif transform == 1:
        cells = tuple((row, width - 1 - col) for row, col in shape)
    elif transform == 2:
        cells = tuple((height - 1 - row, col) for row, col in shape)
    elif transform == 3:
        cells = tuple(
            (height - 1 - row, width - 1 - col) for row, col in shape
        )
    else:
        raise ValueError(f"unknown transform {transform}")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_palette, default_shapes, default_rows = _default_axes(
        sample_index, difficulty
    )
    grid_h = int(_scheduled_axis(ctx, "grid_h", _INT_DOMAINS["grid_h"], default_h))
    grid_w = int(_scheduled_axis(ctx, "grid_w", _INT_DOMAINS["grid_w"], default_w))
    palette_kind = str(
        _scheduled_axis(ctx, "palette_kind", PALETTE_KINDS, default_palette)
    )
    shape_set = str(_scheduled_axis(ctx, "shape_set", SHAPE_SETS, default_shapes))
    row_pattern = str(
        _scheduled_axis(ctx, "row_pattern", ROW_PATTERNS, default_rows)
    )

    rng = ctx.draw_rng("layout")
    shapes = tuple(
        _transform_shape(shape, rng.randrange(4)) for shape in _SHAPES[shape_set]
    )
    row_offsets = _ROW_OFFSETS[row_pattern]
    max_extent = max(
        row_offsets[index] + _shape_dims(shape)[0]
        for index, shape in enumerate(shapes)
    )
    base_row = rng.randint(0, grid_h - max_extent)

    widths = tuple(_shape_dims(shape)[1] for shape in shapes)
    columns = (
        rng.randint(0, 2),
        rng.randint(6, 8),
        rng.randint(grid_w - 5, grid_w - widths[2]),
    )
    grid = full_grid(grid_h, grid_w, 0)
    for index, (shape, color) in enumerate(zip(shapes, _PALETTES[palette_kind])):
        top = base_row + row_offsets[index]
        left = columns[index]
        for dr, dc in shape:
            grid[top + dr][left + dc] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator produced invalid input: " + "; ".join(errors))
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    rr, cc = point
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and point not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            found.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "size": len(cells),
                }
            )
    return found


def _binary_crop(component: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    r0, c0, r1, c1 = component["bbox"]
    crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for row, col in component["cells"]:
        crop[row - r0][col - c0] = 1
    return tuple(tuple(row) for row in crop)


def _parse_grid(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse the complete input grammar and return concise diagnostics."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return None, ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0:
        return None, ["grid rows must be non-empty"]
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if height not in _INT_DOMAINS["grid_h"]:
        errors.append(f"height {height} outside 8..9")
    if width not in _INT_DOMAINS["grid_w"]:
        errors.append(f"width {width} outside 17..20")
    if errors:
        return None, errors

    objects = _components([list(row) for row in grid])
    if len(objects) != 3:
        return None, [f"expected exactly 3 components, got {len(objects)}"]
    objects = sorted(objects, key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))

    colors = tuple(obj["color"] for obj in objects)
    if len(set(colors)) != 3:
        errors.append(f"component colors must be distinct, got {colors}")
    leftmosts = tuple(obj["bbox"][1] for obj in objects)
    if len(set(leftmosts)) != 3:
        errors.append(f"leftmost columns must be distinct, got {leftmosts}")

    shapes = tuple(_binary_crop(obj) for obj in objects)
    if len(set(shapes)) != 3:
        errors.append("the three binary crops must be pairwise distinct")
    dimensions = tuple((len(shape), len(shape[0])) for shape in shapes)
    if any(not (1 <= h <= 3 and 1 <= w <= 3) for h, w in dimensions):
        errors.append(f"every binary crop must fit in 3x3, got {dimensions}")
    if max(h for h, _ in dimensions) != 3 or max(w for _, w in dimensions) != 3:
        errors.append(
            f"common panel must be exactly 3x3, got max dimensions {dimensions}"
        )
    sizes = tuple(obj["size"] for obj in objects)
    if any(not 4 <= size <= 8 for size in sizes):
        errors.append(f"component sizes must be 4..8, got {sizes}")

    for left_index, left in enumerate(objects):
        for right in objects[left_index + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in left["cells"]
                for r2, c2 in right["cells"]
            ):
                errors.append("components must be isolated by at least one background cell")
                break
        if errors and errors[-1].startswith("components must be isolated"):
            break

    if errors:
        return None, errors
    return {
        "grid_h": height,
        "grid_w": width,
        "objects": objects,
        "colors": colors,
        "shapes": shapes,
        "sizes": sizes,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete ordinary input grammar; metadata never waives it."""
    del difficulty, meta
    _state, errors = _parse_grid(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require a lawful input and one of the four exact canonical profiles."""
    state, errors = _parse_grid(grid)
    if errors:
        return errors
    assert state is not None
    profile = (state["grid_h"], state["grid_w"])
    if profile not in set(_CANONICAL_PROFILES):
        return [f"strict canonical profile requires one of {_CANONICAL_PROFILES}, got {profile}"]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    """Decode every public axis from a generated input, or reject ambiguity."""
    state, errors = _parse_grid(grid)
    if errors or state is None:
        raise ValueError("invalid pairwise-gallery input: " + "; ".join(errors))
    palette_lookup = {value: name for name, value in _PALETTES.items()}
    signature_lookup = {
        (4, 4, 4): "sparse",
        (4, 5, 6): "mixed",
        (6, 7, 8): "dense",
    }
    row_lookup = {value: name for name, value in _ROW_OFFSETS.items()}
    colors = tuple(state["colors"])
    sizes = tuple(state["sizes"])
    top_rows = tuple(obj["bbox"][0] for obj in state["objects"])
    minimum = min(top_rows)
    relative_rows = tuple(value - minimum for value in top_rows)
    if colors not in palette_lookup:
        raise ValueError(f"unrecognized generated palette {colors}")
    if sizes not in signature_lookup:
        raise ValueError(f"unrecognized generated shape signature {sizes}")
    if relative_rows not in row_lookup:
        raise ValueError(f"unrecognized generated row pattern {relative_rows}")
    return {
        "grid_h": state["grid_h"],
        "grid_w": state["grid_w"],
        "palette_kind": palette_lookup[colors],
        "shape_set": signature_lookup[sizes],
        "row_pattern": row_lookup[relative_rows],
    }


def _gallery_for_order(
    grid: Any, key: Callable[[dict[str, Any]], Any]
) -> list[list[int]]:
    state, errors = _parse_grid(grid)
    if errors or state is None:
        raise ValueError("invalid pairwise-gallery input: " + "; ".join(errors))
    objects = sorted(state["objects"], key=key)
    shapes = [_binary_crop(obj) for obj in objects]
    panel_h = max(len(shape) for shape in shapes)
    panel_w = max(len(shape[0]) for shape in shapes)
    padded: list[list[list[int]]] = []
    for shape in shapes:
        panel = [[0] * panel_w for _ in range(panel_h)]
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                panel[row][col] = value
        padded.append(panel)

    count = len(padded)
    output = full_grid(count * panel_h + count - 1, count * panel_w + count - 1, 0)
    for gallery_row, first in enumerate(padded):
        for gallery_col, second in enumerate(padded):
            top = gallery_row * (panel_h + 1)
            left = gallery_col * (panel_w + 1)
            for row in range(panel_h):
                for col in range(panel_w):
                    if first[row][col] or second[row][col]:
                        output[top + row][left + col] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the selected Racket rule."""
    return _gallery_for_order(grid, lambda obj: (obj["bbox"][1], obj["bbox"][0]))


def _color_sorted_gallery(grid) -> list[list[int]]:
    """Plausible shortcut: source color determines object order."""
    return _gallery_for_order(
        grid, lambda obj: (obj["color"], obj["bbox"][1], obj["bbox"][0])
    )


def _row_sorted_gallery(grid) -> list[list[int]]:
    """Plausible shortcut: top-row scan order determines object order."""
    return _gallery_for_order(grid, lambda obj: (obj["bbox"][0], obj["bbox"][1]))


def _color_order_conflict(grid) -> bool:
    try:
        state, errors = _parse_grid(grid)
        if errors or state is None:
            return False
        by_column = list(state["objects"])
        by_color = sorted(
            state["objects"],
            key=lambda obj: (obj["color"], obj["bbox"][1], obj["bbox"][0]),
        )
        return [obj["cells"] for obj in by_column] != [obj["cells"] for obj in by_color]
    except (TypeError, ValueError):
        return False


def _row_order_conflict(grid) -> bool:
    try:
        state, errors = _parse_grid(grid)
        if errors or state is None:
            return False
        by_column = list(state["objects"])
        by_row = sorted(
            state["objects"], key=lambda obj: (obj["bbox"][0], obj["bbox"][1])
        )
        return [obj["cells"] for obj in by_column] != [obj["cells"] for obj in by_row]
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "color_order_conflict": _color_order_conflict,
    "row_order_conflict": _row_order_conflict,
}
BRANCH_WITNESSES = ("color_order_conflict", "row_order_conflict")
SEMANTIC_RIVALS = {
    "color_sort": _color_sorted_gallery,
    "row_sort": _row_sorted_gallery,
}
WITNESS_RIVALS = {
    "color_order_conflict": ("color_sort",),
    "row_order_conflict": ("row_sort",),
}
CANONICAL_SHORTCUTS = {
    "color_sort": _color_sorted_gallery,
    "row_sort": _row_sorted_gallery,
}
LESSON_COMPETITORS = {
    "color_sort": _color_sorted_gallery,
    "row_sort": _row_sorted_gallery,
}


def _labeled_pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input invalid: {'; '.join(errors)}"]
    try:
        expected = rule_mirror(pair["input"])
    except (TypeError, ValueError) as exc:
        return [f"{label} rule mirror failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output does not match the pairwise-union rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful labels and demos that refute both canonical shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence of labeled pairs"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"
        )
    for index, demo in enumerate(demos):
        reasons.extend(_labeled_pair_errors(demo, f"demo {index}"))
    reasons.extend(_labeled_pair_errors(query, "query"))
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"{name} fits every demonstration; include its witness")
    return reasons
