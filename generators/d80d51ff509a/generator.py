"""Generator for rank-selected component transforms.

The two nonzero cells in the top row are keys.  The left key is a 1-based
rank into body components ordered by ``(area, bounding box)``; the right key
selects identity, clockwise rotation, left/right reflection, or 180-degree
rotation.  The output is the transformed crop of the selected component.

Four linked profiles reproduce the complete official morphology up to body
translation and lawful color renaming.  A generalized branch uses four or
five components, making every generalized draw an explicit non-replay witness.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d80d51ff509a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "42fbd45b778a"

SUMMARY = (
    "Read the rank key at the top-left and the transform key at the top-right. "
    "Sort body components by area, breaking equal-area ties by bounding-box "
    "position, select the indicated 1-based rank, crop it, and transform the "
    "crop (4 identity, 5 clockwise, 6 left/right reflection, 7 rotate 180)."
)

INVARIANTS = [
    "background is 0 and the rest of the top row is empty",
    "the rank key indexes 3..5 body components after deterministic area/bbox sorting",
    "the transform key is one of 4, 5, 6, 7",
    "body colors are distinct and avoid both key colors",
    "equal-size components are lawful and are ordered by bounding box",
]

_PROFILE_NAMES = tuple(f"canonical_{i}" for i in range(4))
AXES = {
    "grid_h": {"type": "int", "default": "rng 9..15", "valid": "9..15"},
    "grid_w": {"type": "int", "default": "rng 12..18", "valid": "12..18"},
    "profile_kind": {
        "type": "str",
        "default": "40% linked canonical profile, 60% generalized",
        "valid": "canonical_0|canonical_1|canonical_2|canonical_3|generalized",
    },
}

# Each profile stores (height, width, rank key, transform key, body shapes in
# exact oracle sort order).  Shapes are normalized cell-coordinate tuples.
_PROFILE_SPECS = (
    (
        9,
        14,
        1,
        5,
        (
            ((0, 0), (1, 0), (1, 1)),
            ((0, 0), (1, 0), (2, 0), (2, 1)),
            ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
        ),
    ),
    (
        10,
        15,
        2,
        6,
        (
            ((0, 0), (0, 1), (0, 2)),
            ((0, 0), (1, 0), (2, 0), (2, 1)),
            ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ),
    ),
    (
        10,
        16,
        3,
        7,
        (
            ((0, 0), (1, 0), (1, 1)),
            ((0, 0), (0, 1), (0, 2), (0, 3)),
            ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        ),
    ),
    (
        9,
        15,
        2,
        5,
        (
            ((0, 0), (1, 0), (1, 1)),
            ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
            ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ),
    ),
)

_CARDINALS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _normalize_shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _components(grid):
    """Return body components with the same color-sensitive semantics as Racket."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(1, h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINALS:
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            r1 = max(r for r, _ in cells)
            c1 = max(c for _, c in cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (r0, c0, r1, c1),
                    "bbox_h": r1 - r0 + 1,
                    "bbox_w": c1 - c0 + 1,
                    "shape": _normalize_shape(cells),
                }
            )
    return sorted(components, key=lambda comp: (comp["size"], comp["bbox"]))


def canonical_profile_signature(grid):
    """Complete linked official-profile signature, quotienting nuisance colors/translation."""
    if not grid or not grid[0]:
        return None
    return (
        len(grid),
        len(grid[0]),
        grid[0][0],
        grid[0][-1],
        tuple(component["shape"] for component in _components(grid)),
    )


_CANONICAL_SIGNATURES = tuple(
    (h, w, rank_key, transform_key, shapes)
    for h, w, rank_key, transform_key, shapes in _PROFILE_SPECS
)
_CANONICAL_SIGNATURE_TO_NAME = dict(zip(_CANONICAL_SIGNATURES, _PROFILE_NAMES))


def _shape_dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(grid, shape, r0, c0):
    h, w = len(grid), len(grid[0])
    cells = {(r0 + r, c0 + c) for r, c in shape}
    if any(not (1 <= r < h and 0 <= c < w) for r, c in cells):
        return False
    for r, c in cells:
        if grid[r][c] != 0:
            return False
        for dr, dc in _CARDINALS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                return False
    return True


def _crop_component(component):
    r0, c0, r1, c1 = component["bbox"]
    out = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
    for r, c in component["cells"]:
        out[r - r0][c - c0] = component["color"]
    return out


def _crop_nonzero(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _transform(grid, key):
    if key == 4:
        return [row[:] for row in grid]
    if key == 5:
        return _crop_nonzero([list(row) for row in zip(*grid[::-1])])
    if key == 6:
        return _crop_nonzero([list(reversed(row)) for row in grid])
    return _crop_nonzero([list(reversed(row)) for row in reversed(grid)])


def _random_shape(rng, size):
    """Grow a connected polyomino, bounded to 4x4, with deterministic retries."""
    for _ in range(128):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = sorted(
                {
                    (r + dr, c + dc)
                    for r, c in cells
                    for dr, dc in _CARDINALS
                    if (r + dr, c + dc) not in cells
                }
            )
            cells.add(rng.choice(frontier))
        shape = _normalize_shape(cells)
        sh, sw = _shape_dims(shape)
        if sh <= 4 and sw <= 4:
            return shape
    raise ValueError(f"could not grow a bounded connected shape of size {size}")


def _place_scene(h, w, rank_key, transform_key, shapes, colors, rng, expected=None):
    """Place a complete requested scene or fail closed; never simplify it."""
    for _ in range(240):
        grid = full_grid(h, w, 0)
        grid[0][0] = rank_key
        grid[0][w - 1] = transform_key
        order = list(range(len(shapes)))
        rng.shuffle(order)
        placed = True
        for index in order:
            shape = shapes[index]
            sh, sw = _shape_dims(shape)
            positions = [
                (r0, c0)
                for r0 in range(1, h - sh + 1)
                for c0 in range(w - sw + 1)
            ]
            rng.shuffle(positions)
            for r0, c0 in positions:
                if not _free(grid, shape, r0, c0):
                    continue
                for dr, dc in shape:
                    grid[r0 + dr][c0 + dc] = colors[index]
                break
            else:
                placed = False
                break
        if not placed:
            continue
        if expected is not None and canonical_profile_signature(grid) != expected:
            continue
        components = _components(grid)
        bbox_isolated = True
        for component in components:
            r0, c0, r1, c1 = component["bbox"]
            if any(
                grid[r][c] not in (0, component["color"])
                for r in range(r0, r1 + 1)
                for c in range(c0, c1 + 1)
            ):
                bbox_isolated = False
                break
        if not bbox_isolated:
            continue
        selected = components[rank_key - 1]
        crop = _crop_component(selected)
        if transform_key != 4 and _transform(crop, transform_key) == crop:
            continue
        return grid
    raise ValueError("requested component scene could not be placed exactly")


def _compatible_profiles(overrides):
    requested_h = overrides.get("grid_h")
    requested_w = overrides.get("grid_w")
    names = []
    for name, (h, w, _rank, _tf, _shapes) in zip(_PROFILE_NAMES, _PROFILE_SPECS):
        if requested_h is not None and int(requested_h) != h:
            continue
        if requested_w is not None and int(requested_w) != w:
            continue
        names.append(name)
    return names


def _generalized_sizes(rng, count, tie_probability, minimum_size):
    legal_sizes = list(range(minimum_size, 9))
    if rng.random() >= tie_probability:
        return rng.sample(legal_sizes, count)
    repeated = rng.choice(legal_sizes[:-1])
    remaining = [size for size in legal_sizes if size != repeated]
    sizes = [repeated, repeated, *rng.sample(remaining, count - 2)]
    rng.shuffle(sizes)
    return sizes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    compatible = _compatible_profiles(overrides)
    options = [name for name in compatible for _ in range(2)] + ["generalized"] * 12
    profile_kind = ctx.draw_choice("profile_kind", options)

    if profile_kind.startswith("canonical_"):
        profile_index = int(profile_kind.rsplit("_", 1)[1])
        h, w, rank_key, transform_key, shapes = _PROFILE_SPECS[profile_index]
        h = ctx.draw_choice("grid_h", [h])
        w = ctx.draw_choice("grid_w", [w])
        color_rng = ctx.draw_rng(f"canonical-colors-{profile_index}")
        legal = [color for color in range(1, 10) if color not in {rank_key, transform_key}]
        colors = color_rng.sample(legal, len(shapes))
        return _place_scene(
            h,
            w,
            rank_key,
            transform_key,
            shapes,
            colors,
            ctx.draw_rng(f"canonical-layout-{profile_index}"),
            expected=_CANONICAL_SIGNATURES[profile_index],
        )

    h = ctx.draw_int("grid_h", 9, 15)
    w = ctx.draw_int("grid_w", 12, 18)
    structure_rng = ctx.draw_rng("generalized-structure")
    if difficulty == "easy":
        count, tie_probability = 4, 0.20
    elif difficulty == "hard":
        count, tie_probability = 5, 0.55
    else:
        count = 4 + structure_rng.randrange(2)
        tie_probability = 0.35
    rank_key = structure_rng.randint(1, count)
    transform_key = structure_rng.randint(4, 7)
    minimum_size = 2 if transform_key in (4, 5) else 3
    sizes = _generalized_sizes(
        structure_rng, count, tie_probability, minimum_size
    )
    shapes = []
    used_shapes = Counter()
    for size in sizes:
        for _ in range(128):
            shape = _random_shape(structure_rng, size)
            shape_grid = full_grid(*_shape_dims(shape), 0)
            for r, c in shape:
                shape_grid[r][c] = 1
            if transform_key != 4 and _transform(shape_grid, transform_key) == shape_grid:
                continue
            key = (size, shape)
            if used_shapes[key] == 0:
                used_shapes[key] += 1
                shapes.append(shape)
                break
        else:
            raise ValueError(
                f"could not draw a transform-sensitive shape of size {size}"
            )
    legal = [color for color in range(1, 10) if color not in {rank_key, transform_key}]
    colors = structure_rng.sample(legal, count)
    return _place_scene(
        h,
        w,
        rank_key,
        transform_key,
        shapes,
        colors,
        ctx.draw_rng("generalized-layout"),
    )


def observe_overrides(grid):
    signature = canonical_profile_signature(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "profile_kind": _CANONICAL_SIGNATURE_TO_NAME.get(signature, "generalized"),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    w = len(grid[0])
    if not w or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]
    h = len(grid)
    errors = []
    if not (9 <= h <= 15 and 12 <= w <= 18):
        errors.append("grid dimensions must be within 9..15 by 12..18")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid colors must be integers in 0..9")
        return sorted(set(errors))
    if any(grid[0][c] != 0 for c in range(1, w - 1)):
        errors.append("top row must be empty except for the two corner keys")
    rank_key = grid[0][0]
    transform_key = grid[0][-1]
    if transform_key not in (4, 5, 6, 7):
        errors.append("top-right transform key must be one of 4, 5, 6, 7")
    components = _components(grid)
    count = len(components)
    if not (3 <= count <= 5):
        errors.append("body component count must be within 3..5")
    if not (1 <= rank_key <= count):
        errors.append(f"rank key {rank_key} is outside 1..{count}")
    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        errors.append("body components must use distinct colors")
    if rank_key in colors or transform_key in colors:
        errors.append("body colors must avoid both key colors")
    for component in components:
        if not (2 <= component["size"] <= 8):
            errors.append("component sizes must be within 2..8")
        if component["bbox_h"] > 4 or component["bbox_w"] > 4:
            errors.append("component bounding boxes must be at most 4x4")
        r0, c0, r1, c1 = component["bbox"]
        if any(
            grid[r][c] not in (0, component["color"])
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        ):
            errors.append("component bounding boxes may not contain other colors")
    nonzero_body = {(r, c) for r in range(1, h) for c in range(w) if grid[r][c]}
    for r, c in nonzero_body:
        for dr, dc in _CARDINALS:
            nr, nc = r + dr, c + dc
            if (nr, nc) in nonzero_body and grid[nr][nc] != grid[r][c]:
                errors.append("differently colored components may not touch cardinally")
    counts = Counter(value for row in grid for value in row)
    if counts[0] <= max((n for color, n in counts.items() if color != 0), default=0):
        errors.append("background color 0 must be strictly modal")
    if 1 <= rank_key <= count and transform_key in (4, 5, 6, 7):
        crop = _crop_component(components[rank_key - 1])
        transformed = _transform(crop, transform_key)
        if not transformed:
            errors.append("selected component transform must be non-empty")
        if transform_key != 4 and transformed == crop:
            errors.append("non-identity transform must visibly change the selected crop")
    return sorted(set(errors))
