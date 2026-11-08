"""Generator for task 48c4c6a42b59: complete local horizontal symmetry.

Each nonzero same-color object is treated independently.  Its tight bounding
box is the mirror frame; original cells remain and their left-right reflected
cells are added in the same color.  The generator deliberately varies object
size, bbox aspect ratio, palette, count, and absolute position while keeping
the three exact declared axes directly observable from the returned input.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "48c4c6a42b59"
TASK_ID = "48c4c6a42b59"
VERSION = "3.0.0"
RULE_HASH = "cecf4f1691f5"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.05

SUMMARY = (
    "An 11..13 by 11..13 zero-background grid contains two or three "
    "separated, distinct-color, 4-connected objects.  Objects have 6..11 "
    "cells in 3..5-cell local bboxes and every object is asymmetric under "
    "left-right reflection.  For each object independently, keep its original "
    "cells and add their horizontal reflections inside that object's own tight "
    "bounding box."
)

INVARIANTS = [
    "background is 0 and remains the strict majority",
    "2-3 distinct-color same-color 4-connected objects",
    "every object changes under bbox-local horizontal union",
    "all local mirrored footprints stay in bounds and are pairwise disjoint",
    "grid_h, grid_w, and n_blobs are exact observable axes",
    "a four-profile schedule exposes canonical, aspect-ratio, size, and palette branches",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased 11..13",
        "valid": "11..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased 11..13",
        "valid": "11..13",
    },
    "n_blobs": {
        "type": "int",
        "default": "uniform 2..3",
        "valid": "2..3",
    },
}

_VALID_H = (11, 13)
_VALID_W = (11, 13)
_VALID_N = (2, 3)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

SCHEDULE_PROFILES = (
    "canonical_square",
    "mixed_bbox",
    "size_contrast",
    "palette_counterexample",
)

# Exact normalized input morphologies from the four public demonstrations and
# held-out canonical query.  These anchor strict support without making color
# or absolute position semantic.
_CANONICAL_SHAPES = (
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 4), (4, 3), (4, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 2), (3, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (3, 4), (4, 2), (4, 3), (4, 4)),
    ((0, 2), (0, 3), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2)),
    ((0, 4), (1, 3), (1, 4), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3), (4, 0), (4, 1)),
    ((0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
)

# Rectangular-bbox objects are lawful extrapolations and are important
# counterexamples to a "square box only" or vertical-reflection shortcut.
_RECTANGULAR_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 2), (2, 3)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 3), (2, 4), (3, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 2), (4, 0), (4, 1), (4, 2), (4, 3)),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _mirror_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    _, width = _dims(cells)
    return _normalize((r, width - 1 - c) for r, c in cells)


def _vertical_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    height, _ = _dims(cells)
    return _normalize((height - 1 - r, c) for r, c in cells)


_MIRRORED_CANONICAL = tuple(_mirror_shape(shape) for shape in _CANONICAL_SHAPES)
_MIRRORED_RECTANGULAR = tuple(_mirror_shape(shape) for shape in _RECTANGULAR_SHAPES)
_ALLOWED_SHAPES = frozenset(
    _CANONICAL_SHAPES
    + _MIRRORED_CANONICAL
    + _RECTANGULAR_SHAPES
    + _MIRRORED_RECTANGULAR
)
_CANONICAL_SHAPE_SET = frozenset(_CANONICAL_SHAPES)

_SQUARE_BY_SIDE = {
    side: tuple(shape for shape in _CANONICAL_SHAPES if _dims(shape) == (side, side))
    for side in (3, 4, 5)
}
_CANONICAL_BY_SIZE = {
    size: tuple(shape for shape in _CANONICAL_SHAPES if len(shape) == size)
    for size in (6, 8, 10, 11)
}
_RECT_BY_DIMS = {
    dims: tuple(shape for shape in _RECTANGULAR_SHAPES if _dims(shape) == dims)
    for dims in ((3, 4), (4, 3), (4, 5), (5, 4))
}


def _expanded(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """One-cell Chebyshev halo used only for source-object separation."""
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _components(grid):
    """Same-color 4-connected components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r0 in range(height):
        for c0 in range(width):
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
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (r1, c1, r2, c2),
                    "shape": _normalize(cells),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                    "size": len(cells),
                }
            )
    return result


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive indices cover every curriculum branch in each band."""
    del seed
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return SCHEDULE_PROFILES[(sample_index + offset) % len(SCHEDULE_PROFILES)]


def _shape_schedule(profile: str, n: int, rng):
    """Choose a guaranteed-placeable, branch-specific set of local shapes."""
    if profile == "canonical_square":
        if n == 2:
            return [rng.choice(_SQUARE_BY_SIDE[3]), rng.choice(_SQUARE_BY_SIDE[5])]
        return [
            rng.choice(_SQUARE_BY_SIDE[3]),
            rng.choice(_SQUARE_BY_SIDE[4]),
            rng.choice(_SQUARE_BY_SIDE[5]),
        ]
    if profile == "mixed_bbox":
        if n == 2:
            return [rng.choice(_RECT_BY_DIMS[(3, 4)]), rng.choice(_SQUARE_BY_SIDE[5])]
        return [
            rng.choice(_RECT_BY_DIMS[(3, 4)]),
            rng.choice(_RECT_BY_DIMS[(4, 3)]),
            rng.choice(_SQUARE_BY_SIDE[3]),
        ]
    if profile == "size_contrast":
        if n == 2:
            return [rng.choice(_CANONICAL_BY_SIZE[6]), rng.choice(_CANONICAL_BY_SIZE[11])]
        return [
            rng.choice(_CANONICAL_BY_SIZE[6]),
            rng.choice(_CANONICAL_BY_SIZE[8]),
            rng.choice(_CANONICAL_BY_SIZE[11]),
        ]
    if profile == "palette_counterexample":
        if n == 2:
            return [rng.choice(_SQUARE_BY_SIDE[4]), rng.choice(_RECT_BY_DIMS[(5, 4)])]
        return [
            rng.choice(_SQUARE_BY_SIDE[3]),
            rng.choice(_RECT_BY_DIMS[(3, 4)]),
            rng.choice(_SQUARE_BY_SIDE[5]),
        ]
    raise ValueError(f"unknown schedule profile {profile!r}")


def _place_shapes(h, w, shapes, colors, rng):
    """Backtrack over at most three <=5x5 local mirror footprints."""
    items = sorted(
        zip(shapes, colors),
        key=lambda item: (_dims(item[0])[0] * _dims(item[0])[1], len(item[0])),
        reverse=True,
    )
    candidates = []
    for index, (shape, color) in enumerate(items):
        mirror = _mirror_shape(shape)
        footprint = set(shape) | set(mirror)
        shape_h, shape_w = _dims(shape)
        positions = [
            (r, c)
            for r in range(h - shape_h + 1)
            for c in range(w - shape_w + 1)
            # Guarantee at least one object's local axis is not the canvas axis.
            if index != 0 or 2 * c + shape_w - 1 != w - 1
        ]
        rng.shuffle(positions)
        candidates.append((shape, footprint, color, positions))

    placements: list[tuple[tuple[tuple[int, int], ...], int, int, int]] = []

    def search(
        index: int,
        reserved_sources: set[tuple[int, int]],
        reserved_unions: set[tuple[int, int]],
    ) -> bool:
        if index == len(candidates):
            return True
        shape, footprint, color, positions = candidates[index]
        for r0, c0 in positions:
            source = {(r0 + r, c0 + c) for r, c in shape}
            union = {(r0 + r, c0 + c) for r, c in footprint}
            if _expanded(source) & reserved_sources:
                continue
            if union & reserved_unions:
                continue
            placements.append((shape, r0, c0, color))
            if search(index + 1, reserved_sources | source, reserved_unions | union):
                return True
            placements.pop()
        return False

    if not search(0, set(), set()):
        raise ValueError(
            f"could not place {len(shapes)} separated mirror footprints on {h}x{w}"
        )

    grid = full_grid(h, w, 0)
    for shape, r0, c0, color in placements:
        for r, c in shape:
            grid[r0 + r][c0 + c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if isinstance(difficulty, str) and difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy/medium/hard/None, got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

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

    profile = schedule_profile(seed, sample_index, difficulty)
    shapes = _shape_schedule(profile, n, rng)
    if profile == "palette_counterexample":
        colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 9), n)
    else:
        colors = rng.sample(range(1, 10), n)

    grid = _place_shapes(h, w, shapes, colors, rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"generator emitted an invalid grid: {errors}")
    return grid


def observe_overrides(grid):
    """Recover every declared exact axis from the returned input grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_blobs": len(_components(grid)) if grid and grid[0] else 0,
    }


def rule_mirror(grid):
    """Independent Python oracle for tests and semantic rivals.

    The canonical Racket program remains the authoritative output rule.
    """
    out = [list(row) for row in grid]
    for obj in _components(grid):
        _, c1, _, c2 = obj["bbox"]
        for r, c in obj["cells"]:
            out[r][c1 + c2 - c] = obj["color"]
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_replace_with_local_mirror(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for obj in _components(grid):
        _, c1, _, c2 = obj["bbox"]
        for r, c in obj["cells"]:
            out[r][c1 + c2 - c] = obj["color"]
    return out


def _rival_vertical_bbox_union(grid):
    out = [list(row) for row in grid]
    for obj in _components(grid):
        r1, _, r2, _ = obj["bbox"]
        for r, c in obj["cells"]:
            out[r1 + r2 - r][c] = obj["color"]
    return out


def _rival_global_horizontal_union(grid):
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                out[r][w - 1 - c] = grid[r][c]
    return out


def _rival_selected_objects(grid, selector):
    out = [list(row) for row in grid]
    comps = _components(grid)
    selected = set(selector(comps))
    for index, obj in enumerate(comps):
        if index not in selected:
            continue
        _, c1, _, c2 = obj["bbox"]
        for r, c in obj["cells"]:
            out[r][c1 + c2 - c] = obj["color"]
    return out


def _rival_first_object_only(grid):
    return _rival_selected_objects(grid, lambda comps: [0] if comps else [])


def _rival_largest_object_only(grid):
    def choose(comps):
        if not comps:
            return []
        return [max(range(len(comps)), key=lambda i: (comps[i]["size"], -i))]

    return _rival_selected_objects(grid, choose)


def _rival_color_8_only(grid):
    return _rival_selected_objects(
        grid,
        lambda comps: [i for i, obj in enumerate(comps) if obj["color"] == 8],
    )


def _rival_fill_each_bbox(grid):
    out = [list(row) for row in grid]
    for obj in _components(grid):
        r1, c1, r2, c2 = obj["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = obj["color"]
    return out


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "replace_with_local_mirror": _rival_replace_with_local_mirror,
    "vertical_bbox_union": _rival_vertical_bbox_union,
    "global_horizontal_union": _rival_global_horizontal_union,
    "first_object_only": _rival_first_object_only,
    "largest_object_only": _rival_largest_object_only,
    "color_8_only": _rival_color_8_only,
    "fill_each_bbox": _rival_fill_each_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _all_objects_change(grid) -> bool:
    comps = _components(grid)
    return bool(comps) and all(
        obj["shape"] != _mirror_shape(obj["shape"]) for obj in comps
    )


def _bbox_local_not_global(grid) -> bool:
    return rule_mirror(grid) != _rival_global_horizontal_union(grid)


def _horizontal_not_vertical(grid) -> bool:
    return rule_mirror(grid) != _rival_vertical_bbox_union(grid)


def _non_filled_mirror_union(grid) -> bool:
    return rule_mirror(grid) != _rival_fill_each_bbox(grid)


def _has_three_objects(grid) -> bool:
    return (
        len(_components(grid)) == 3
        and rule_mirror(grid) != _rival_first_object_only(grid)
    )


def _has_rectangular_bbox(grid) -> bool:
    return (
        any(obj["height"] != obj["width"] for obj in _components(grid))
        and rule_mirror(grid) != _rival_vertical_bbox_union(grid)
    )


def _palette_without_eight(grid) -> bool:
    comps = _components(grid)
    return (
        bool(comps)
        and all(obj["color"] != 8 for obj in comps)
        and rule_mirror(grid) != _rival_color_8_only(grid)
    )


def _has_size_contrast(grid) -> bool:
    sizes = {obj["size"] for obj in _components(grid)}
    return len(sizes) >= 2 and rule_mirror(grid) != _rival_largest_object_only(grid)


SEMANTIC_WITNESSES = {
    "every_object_changes": _all_objects_change,
    "bbox_local_not_global": _bbox_local_not_global,
    "horizontal_not_vertical": _horizontal_not_vertical,
    "non_filled_mirror_union": _non_filled_mirror_union,
    "three_objects": _has_three_objects,
    "rectangular_bbox": _has_rectangular_bbox,
    "palette_without_eight": _palette_without_eight,
    "size_contrast": _has_size_contrast,
}

WITNESS_RIVALS = {
    "every_object_changes": [
        "identity",
        "replace_with_local_mirror",
        "first_object_only",
        "largest_object_only",
        "color_8_only",
    ],
    "bbox_local_not_global": ["global_horizontal_union"],
    "horizontal_not_vertical": ["vertical_bbox_union"],
    "non_filled_mirror_union": ["fill_each_bbox"],
    "three_objects": ["first_object_only", "largest_object_only"],
    "rectangular_bbox": ["vertical_bbox_union"],
    "palette_without_eight": ["color_8_only"],
    "size_contrast": ["largest_object_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named wrong rule survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} does not match bbox-local mirror union")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(d["input"]) == d["output"] for d in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural, mutation-sensitive checker for the teaching distribution."""
    del meta
    if isinstance(difficulty, str) and difficulty not in _VALID_DIFFICULTIES:
        return [f"invalid difficulty {difficulty!r}"]
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

    transformed_sets = []
    for obj in comps:
        if not 6 <= obj["size"] <= 11:
            errors.append(
                f"color {obj['color']} size {obj['size']} outside canonical 6..11 envelope"
            )
        if not 3 <= obj["height"] <= 5 or not 3 <= obj["width"] <= 5:
            errors.append(
                f"color {obj['color']} bbox {obj['height']}x{obj['width']} outside 3..5"
            )
        if obj["shape"] not in _ALLOWED_SHAPES:
            errors.append(f"color {obj['color']} morphology is outside the reviewed library")
        mirrored_shape = _mirror_shape(obj["shape"])
        if mirrored_shape == obj["shape"]:
            errors.append(f"color {obj['color']} is horizontally symmetric (rule-hiding)")
        r1, c1, _, _ = obj["bbox"]
        transformed = {
            (r1 + r, c1 + c)
            for r, c in (set(obj["shape"]) | set(mirrored_shape))
        }
        if any(not (0 <= r < height and 0 <= c < width) for r, c in transformed):
            errors.append(f"color {obj['color']} mirrored footprint leaves the grid")
        transformed_sets.append((obj["color"], transformed))

    for i, (color_i, cells_i) in enumerate(transformed_sets):
        for color_j, cells_j in transformed_sets[i + 1 :]:
            if cells_i & cells_j:
                errors.append(
                    f"local mirror unions for colors {color_i} and {color_j} collide"
                )

    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero * 2 >= height * width:
        errors.append("background 0 must be the strict majority")
    if not errors and rule_mirror(grid) == grid:
        errors.append("whole scene is identity under bbox-local mirror union")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical morphology manifold, with color and position as nuisance."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if h != w or h not in (11, 12, 13):
        return [f"canonical canvases are square 11x11, 12x12, or 13x13; got {h}x{w}"]
    comps = _components(grid)
    if len(comps) != 2:
        return [f"canonical inputs contain exactly 2 objects, got {len(comps)}"]
    if any(obj["shape"] not in _CANONICAL_SHAPE_SET for obj in comps):
        return ["canonical-like inputs must use an exact linked canonical morphology"]
    return []
