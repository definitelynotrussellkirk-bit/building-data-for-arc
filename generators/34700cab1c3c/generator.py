"""Generator for arc_puzzle_bank_sixth21:M38.

Rule: find each same-color nonzero 4-connected object, crop it to its own
bounding box, transpose the occupied cells inside that local frame, and paste
the transposed object at the original bounding-box top-left on a fresh zero
canvas.

The four-sample curriculum schedule alternates canonical tetromino profiles,
mixed wide/tall profiles, square-bbox asymmetric objects, and size variation.
Every ordinary object changes under transpose.  The schedule therefore rebuts
identity, union, rotation, reflection, non-square-only, first-object-only, and
global-coordinate shortcuts while keeping regular support on the three linked
canonical profiles.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "34700cab1c3c"
TASK_ID = "34700cab1c3c"
VERSION = "3.0.0"
RULE_HASH = "1259a82b7164"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.05

SUMMARY = (
    "A zero-background 8..10 by 10..12 grid contains two or three separated, "
    "distinct-color, 4-connected asymmetric objects. Each object has 4..5 "
    "cells and a local footprint at most 3x3. The answer independently "
    "transposes every object's occupied offsets inside its own bounding box, "
    "keeps that box's top-left anchor fixed, and paints only the transposed "
    "cells on a fresh zero canvas."
)

INVARIANTS = [
    "background is 0 and is the strict majority color",
    "2-3 distinct-color 4-connected objects, each color used by one object",
    "every object changes under bbox-local transpose",
    "source and transposed footprints are in bounds and pairwise disjoint",
    "declared grid_h, grid_w, and n_blobs are exactly observable",
    "sample_index modulo four covers canonical, square-bbox, and size branches",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased 8..10", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "difficulty-biased 10..12", "valid": "10..12"},
    "n_blobs": {"type": "int", "default": "uniform 2..3", "valid": "2..3"},
}

_VALID_H = (8, 10)
_VALID_W = (10, 12)
_VALID_N = (2, 3)

# Exact normalized input morphologies from the two train inputs and held-out
# test input.  Canonical profiles always link the lower color to a wide 2x3
# tetromino and the higher color to a tall 3x2 tetromino.
_CANONICAL_WIDE4 = (
    ((0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
)
_CANONICAL_TALL4 = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
)

# Additional morphology deliberately outside the exact canonical profiles.
_WIDE5 = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2)),
)
_TALL5 = tuple(
    tuple(sorted((c, r) for r, c in shape))
    for shape in _WIDE5
)
_SQUARE5 = (
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
)

_CANONICAL_PROFILE = {
    (8, 10): (2, 3),
    (9, 11): (4, 5),
    (10, 12): (6, 7),
}
_CANONICAL_SHAPES = frozenset(_CANONICAL_WIDE4 + _CANONICAL_TALL4)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _transpose_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, r) for r, c in cells)


def _expanded(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """One-cell Chebyshev halo, used to keep source/output roles separable."""
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _components(grid):
    """Same-color 4-connected components in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            out.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "bbox": (r1, c1, r2, c2),
                "shape": _normalize(cells),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "size": len(cells),
            })
    return out


def _shape_schedule(slot: int, n: int, rng):
    """Four consecutive samples jointly expose every decisive branch."""
    if slot in (0, 1):
        shapes = [
            rng.choice(_CANONICAL_WIDE4),
            rng.choice(_CANONICAL_TALL4),
            rng.choice(_SQUARE5),
        ]
    elif slot == 2:
        shapes = [
            rng.choice(_SQUARE5),
            rng.choice(_WIDE5),
            rng.choice(_CANONICAL_TALL4),
        ]
    else:
        shapes = [
            rng.choice(_WIDE5),
            rng.choice(_TALL5),
            rng.choice(_SQUARE5),
        ]
    return shapes[:n]


def _place_shapes(h, w, shapes, colors, rng):
    """Backtracking placement over at most three <=3x3 local footprints."""
    candidates = []
    for shape in shapes:
        transposed = _transpose_shape(shape)
        footprint = set(shape) | set(transposed)
        fh, fw = _dims(footprint)
        positions = [(r, c) for r in range(h - fh + 1) for c in range(w - fw + 1)]
        rng.shuffle(positions)
        candidates.append((shape, footprint, positions))

    placements: list[tuple[tuple[tuple[int, int], ...], int, int]] = []

    def search(index: int, reserved: set[tuple[int, int]]) -> bool:
        if index == len(candidates):
            return True
        shape, footprint, positions = candidates[index]
        for r0, c0 in positions:
            placed_footprint = {(r0 + r, c0 + c) for r, c in footprint}
            if _expanded(placed_footprint) & reserved:
                continue
            placements.append((shape, r0, c0))
            if search(index + 1, reserved | placed_footprint):
                return True
            placements.pop()
        return False

    if not search(0, set()):
        raise ValueError(
            f"could not place {len(shapes)} separated transpose footprints on {h}x{w}"
        )

    grid = full_grid(h, w, 0)
    for (shape, r0, c0), color in zip(placements, colors):
        for r, c in shape:
            grid[r0 + r][c0 + c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", *_VALID_H)
    w = ctx.draw_int_diff("grid_w", *_VALID_W)
    n = ctx.draw_int("n_blobs", *_VALID_N)
    rng = ctx.draw_rng("scene")

    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    slot = (sample_index + band_offset) % 4
    shapes = _shape_schedule(slot, n, rng)

    # Exact canonical palette linkage is frequent but not universal.  This
    # anchors the teaching distribution without making color semantic.
    if slot in (0, 1) and n == 2 and (h, w) in _CANONICAL_PROFILE:
        colors = list(_CANONICAL_PROFILE[(h, w)])
    else:
        colors = rng.sample(range(1, 10), n)

    return _place_shapes(h, w, shapes, colors, rng)


def observe_overrides(grid):
    """Recover every declared exact axis from the returned input grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_blobs": len(_components(grid)) if grid and grid[0] else 0,
    }


def _local_output(grid, mode: str):
    """Pure Python mirrors/competitors; Racket remains output authority."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    comps = _components(grid)
    for index, obj in enumerate(comps):
        r1, c1, _, _ = obj["bbox"]
        shape = obj["shape"]
        bh, bw = obj["height"], obj["width"]
        if mode == "transpose":
            transformed = [(c, r) for r, c in shape]
        elif mode == "rotate_cw":
            transformed = [(c, bh - 1 - r) for r, c in shape]
        elif mode == "rotate_ccw":
            transformed = [(bw - 1 - c, r) for r, c in shape]
        elif mode == "flip_lr":
            transformed = [(r, bw - 1 - c) for r, c in shape]
        elif mode == "flip_ud":
            transformed = [(bh - 1 - r, c) for r, c in shape]
        elif mode == "identity":
            transformed = list(shape)
        elif mode == "union":
            transformed = list(shape) + [(c, r) for r, c in shape]
        elif mode == "only_first":
            transformed = [(c, r) for r, c in shape] if index == 0 else list(shape)
        elif mode == "non_square_only":
            transformed = [(c, r) for r, c in shape] if bh != bw else list(shape)
        else:
            raise ValueError(f"unknown local output mode {mode}")
        for r, c in transformed:
            rr, cc = r1 + r, c1 + c
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = obj["color"]
    return out


def _global_transpose_output(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0 and c < h and r < w:
                out[c][r] = value
    return out


_LESSON_COMPETITORS = {
    "leave objects unchanged": lambda g: _local_output(g, "identity"),
    "union original with local transpose": lambda g: _local_output(g, "union"),
    "rotate each local crop clockwise": lambda g: _local_output(g, "rotate_cw"),
    "rotate each local crop counter-clockwise": lambda g: _local_output(g, "rotate_ccw"),
    "reflect each local crop left-right": lambda g: _local_output(g, "flip_lr"),
    "reflect each local crop up-down": lambda g: _local_output(g, "flip_ud"),
    "transpose only the first object": lambda g: _local_output(g, "only_first"),
    "transpose only non-square bboxes": lambda g: _local_output(g, "non_square_only"),
    "transpose in global grid coordinates": _global_transpose_output,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if _local_output(demo["input"], "transpose") != demo["output"]:
            reasons.append(f"demo {index} does not match bbox-local transpose")
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(d["input"]) == d["output"] for d in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def strict_canonical_like(grid) -> list[str]:
    """Exact linked empirical profile, with position treated as nuisance."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    expected_colors = _CANONICAL_PROFILE.get((h, w))
    if expected_colors is None:
        return [f"dimensions {h}x{w} are not one of the three canonical profiles"]
    comps = _components(grid)
    if len(comps) != 2:
        return [f"canonical profiles contain exactly 2 objects, got {len(comps)}"]
    by_color = {obj["color"]: obj for obj in comps}
    if set(by_color) != set(expected_colors):
        return [
            f"palette {sorted(by_color)} is not linked canonical palette "
            f"{list(expected_colors)} for {h}x{w}"
        ]
    lower, higher = expected_colors
    if (by_color[lower]["height"], by_color[lower]["width"]) != (2, 3):
        return ["lower canonical color must carry the wide 2x3 object"]
    if (by_color[higher]["height"], by_color[higher]["width"]) != (3, 2):
        return ["higher canonical color must carry the tall 3x2 object"]
    for obj in comps:
        if obj["size"] != 4 or obj["shape"] not in _CANONICAL_SHAPES:
            return ["canonical objects must be one of the six linked tetromino shapes"]
    return []


def _has_wide_and_tall(grid) -> bool:
    comps = _components(grid)
    return (
        any(obj["height"] < obj["width"] for obj in comps)
        and any(obj["height"] > obj["width"] for obj in comps)
    )


def _has_square_asymmetric(grid) -> bool:
    return any(
        obj["height"] == obj["width"]
        and obj["shape"] != _transpose_shape(obj["shape"])
        for obj in _components(grid)
    )


def _has_three_blobs(grid) -> bool:
    return len(_components(grid)) == 3


def _has_size_five(grid) -> bool:
    return any(obj["size"] == 5 for obj in _components(grid))


def _all_objects_change(grid) -> bool:
    comps = _components(grid)
    return bool(comps) and all(
        obj["shape"] != _transpose_shape(obj["shape"])
        for obj in comps
    )


SEMANTIC_WITNESSES = {
    "wide_and_tall_bboxes": _has_wide_and_tall,
    "square_asymmetric_bbox": _has_square_asymmetric,
    "three_objects": _has_three_blobs,
    "size_five_object": _has_size_five,
    "every_object_changes": _all_objects_change,
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural, mutation-sensitive checker for the teaching distribution."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged"]
    height = len(grid)
    errors: list[str] = []
    if not (_VALID_H[0] <= height <= _VALID_H[1]):
        errors.append(f"grid height {height} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= width <= _VALID_W[1]):
        errors.append(f"grid width {width} outside {_VALID_W[0]}..{_VALID_W[1]}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors

    comps = _components(grid)
    if not (_VALID_N[0] <= len(comps) <= _VALID_N[1]):
        errors.append(f"expected 2..3 objects, got {len(comps)}")
        return errors

    colors = [obj["color"] for obj in comps]
    nonzero_colors = {value for row in grid for value in row if value != 0}
    if len(colors) != len(nonzero_colors):
        errors.append("each nonzero color must form exactly one connected object")

    if any(not 4 <= obj["size"] <= 5 for obj in comps):
        errors.append(
            f"object sizes must stay in 4..5, got {sorted(obj['size'] for obj in comps)}"
        )
    if any(obj["height"] > 3 or obj["width"] > 3 for obj in comps):
        errors.append("each object bbox must fit within 3x3")

    transformed_sets = []
    for obj in comps:
        r1, c1, _, _ = obj["bbox"]
        transposed_shape = _transpose_shape(obj["shape"])
        if transposed_shape == obj["shape"]:
            errors.append(f"color {obj['color']} is transpose-symmetric (rule-hiding)")
        transformed = {(r1 + r, c1 + c) for r, c in transposed_shape}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in transformed):
            errors.append(f"color {obj['color']} transposed footprint leaves the grid")
        transformed_sets.append((obj["color"], transformed))

    for i, (color_i, cells_i) in enumerate(transformed_sets):
        for color_j, cells_j in transformed_sets[i + 1:]:
            if cells_i & cells_j:
                errors.append(
                    f"transposed footprints for colors {color_i} and {color_j} collide"
                )

    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero * 2 >= height * width:
        errors.append("background 0 must be the strict majority")

    if not errors and _local_output(grid, "transpose") == grid:
        errors.append("whole scene is identity under bbox-local transpose")
    return errors
