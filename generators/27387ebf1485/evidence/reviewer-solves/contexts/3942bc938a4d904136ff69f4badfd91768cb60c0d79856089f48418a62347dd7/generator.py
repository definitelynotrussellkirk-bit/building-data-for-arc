"""Semantic generator for ARC task 27387ebf1485.

The nonzero cell at (0, 0) names a target color.  Ignore that cell while
computing the bounding box of every other cell of the target color, then
return the unchanged input subgrid inside that inclusive box.

Five linked public profiles retain every published input.  General profiles
cover disconnected and sparse target sets, one-dimensional boxes, edge
placement, foreign cells inside the crop, and the subtle case where (0, 0)
falls inside the computed box and is therefore preserved in the output.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "27387ebf1485"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ea5b14ea2c9d"
SUMMARY = (
    "Crop the unchanged bbox around all cells matching the top-left marker "
    "color, excluding the top-left cell only from bbox computation."
)

INVARIANTS = [
    "(0, 0) contains a nonzero target-color marker",
    "at least one other target-color cell exists",
    "the bbox is computed from every target-color cell except (0, 0)",
    "the output preserves every input value inside that inclusive bbox",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "varied_poly",
    "target_multicomponent",
    "singleton_target",
    "horizontal_line",
    "vertical_line",
    "target_at_edge",
    "foreign_inside_crop",
    "origin_inside_crop",
    "wide_bbox_sparse",
    "two_colors",
    "five_colors",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng; five linked public profiles in sixteen",
        "valid": "|".join(SCENE_PROFILES),
    }
}


# Complete color-role-normalized public inputs.  Role 1 is always the marker
# color at (0, 0); actual nuisance colors are randomized at draw time.
_PUBLIC_MASKS = {
    "public_train_1": (
        "1000000000",
        "0000002200",
        "0100002200",
        "0100000000",
        "0111000000",
        "0000033300",
        "0000000000",
        "0000000000",
    ),
    "public_train_2": (
        "100000000",
        "000000220",
        "011100220",
        "001000000",
        "001000000",
        "000003000",
        "000003300",
        "000003330",
        "000000000",
    ),
    "public_train_3": (
        "10000000000",
        "00000002000",
        "00000002000",
        "00110002220",
        "00010000000",
        "00011000000",
        "00000033300",
        "00000000000",
    ),
    "public_train_4": (
        "1000000000",
        "0000002220",
        "0000000200",
        "0000000200",
        "0101000000",
        "0101000000",
        "0111000000",
        "0000000330",
        "0000000330",
        "0000000000",
    ),
    "public_test_1": (
        "100000000000",
        "000000002200",
        "001000000200",
        "001100000220",
        "001110000000",
        "000000000000",
        "000000033300",
        "000000000000",
        "000000000000",
    ),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _color_order(grid):
    order = []
    for row in grid:
        for value in row:
            if value != 0 and value not in order:
                order.append(value)
    return order


def _normalized_mask_signature(grid):
    roles = {color: index + 1 for index, color in enumerate(_color_order(grid))}
    return tuple("".join(str(roles.get(value, 0)) for value in row) for row in grid)


_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}
if len(_PUBLIC_SIGNATURES) != len(_PUBLIC_MASKS):
    raise RuntimeError("public profile signatures collide")


def _target_components(cells):
    remaining = set(cells)
    components = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        stack = [seed]
        component = []
        while stack:
            row, col = stack.pop()
            component.append((row, col))
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(components)


def _analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty grid"]}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    errors = []
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                break
        if errors:
            break
    if errors:
        return {"errors": errors, "height": height, "width": width, "scene_profile": None}

    marker = grid[0][0]
    if marker == 0:
        errors.append("(0, 0) must contain a nonzero marker color")
    target_cells = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == marker and (row, col) != (0, 0)
    ) if marker else ()
    if not target_cells:
        errors.append("at least one target-color cell outside (0, 0) is required")
    colors = _color_order(grid)
    if len(colors) not in (2, 3, 5):
        errors.append(f"expected 2, 3, or 5 nonzero colors, got {len(colors)}")

    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "marker": marker,
        "colors": colors,
        "target_cells": target_cells,
        "scene_profile": None,
    }
    if errors:
        return result

    r1 = min(row for row, _ in target_cells)
    c1 = min(col for _, col in target_cells)
    r2 = max(row for row, _ in target_cells)
    c2 = max(col for _, col in target_cells)
    bbox = (r1, c1, r2, c2)
    crop = [list(grid[row][c1:c2 + 1]) for row in range(r1, r2 + 1)]
    components = _target_components(target_cells)
    foreign_inside = any(
        grid[row][col] not in (0, marker)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
    )
    origin_inside = r1 == 0 and c1 == 0
    touches_edge = r2 == height - 1 or c2 == width - 1
    area = (r2 - r1 + 1) * (c2 - c1 + 1)
    density = len(target_cells) / area

    signature = _normalized_mask_signature(grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None:
        if origin_inside:
            profile = "origin_inside_crop"
        elif foreign_inside:
            profile = "foreign_inside_crop"
        elif len(colors) == 2:
            profile = "two_colors"
        elif len(colors) == 5:
            profile = "five_colors"
        elif len(target_cells) == 1:
            profile = "singleton_target"
        elif r1 == r2:
            profile = "horizontal_line"
        elif c1 == c2:
            profile = "vertical_line"
        elif touches_edge:
            profile = "target_at_edge"
        elif len(components) >= 2 and area >= 35 and density <= 0.22:
            profile = "wide_bbox_sparse"
        elif len(components) >= 2:
            profile = "target_multicomponent"
        elif len(components) == 1:
            profile = "varied_poly"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized marker-crop lesson {profile!r}")
    result.update({
        "errors": errors,
        "bbox": bbox,
        "crop": crop,
        "components": components,
        "component_count": len(components),
        "foreign_inside": foreign_inside,
        "origin_inside": origin_inside,
        "touches_edge": touches_edge,
        "target_density": density,
        "scene_profile": profile,
        "public_signature": signature,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python transcription of the canonical bbox computation."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["crop"]]


def _grid_from_public(profile, colors):
    return [
        [0 if role == "0" else colors[int(role) - 1] for role in row]
        for row in _PUBLIC_MASKS[profile]
    ]


def _difficulty_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(8, 10), rng.randint(9, 12)
    if difficulty == "hard":
        return rng.randint(11, 14), rng.randint(13, 17)
    return rng.randint(9, 12), rng.randint(11, 14)


def _random_polyomino(rng, minimum=4, maximum=14):
    for _ in range(200):
        target = rng.randint(minimum, maximum)
        cells = {(0, 0)}
        while len(cells) < target:
            row, col = rng.choice(tuple(cells))
            dr, dc = rng.choice(_CARDINAL)
            cells.add((row + dr, col + dc))
        top = min(row for row, _ in cells)
        left = min(col for _, col in cells)
        shape = tuple(sorted((row - top, col - left) for row, col in cells))
        if max(row for row, _ in shape) >= 1 and max(col for _, col in shape) >= 1:
            return shape
    raise RuntimeError("could not grow a two-dimensional target polyomino")


def _paint(grid, cells, color):
    for row, col in cells:
        grid[row][col] = color


def _translated(shape, top, left):
    return tuple((top + row, left + col) for row, col in shape)


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _outside_bbox(cell, bbox):
    row, col = cell
    r1, c1, r2, c2 = bbox
    return not (r1 <= row <= r2 and c1 <= col <= c2)


def _add_distractors(grid, rng, colors, target_bbox, occupied):
    height, width = len(grid), len(grid[0])
    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) != (0, 0)
        and (row, col) not in occupied
        and _outside_bbox((row, col), target_bbox)
    ]
    rng.shuffle(available)
    for color in colors:
        if not available:
            raise RuntimeError("no room for distractor colors")
        first = available.pop()
        grid[first[0]][first[1]] = color
        occupied.add(first)
        candidates = [
            (first[0] + dr, first[1] + dc)
            for dr, dc in _CARDINAL
            if (first[0] + dr, first[1] + dc) in available
        ]
        if candidates and rng.random() < 0.8:
            second = rng.choice(candidates)
            grid[second[0]][second[1]] = color
            occupied.add(second)
            available.remove(second)


def _interior_poly(rng, height, width):
    for _ in range(100):
        shape = _random_polyomino(rng)
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        if shape_h <= height - 3 and shape_w <= width - 2:
            top = rng.randint(2, height - shape_h - 1)
            left = rng.randint(1, width - shape_w - 1)
            return _translated(shape, top, left)
    raise RuntimeError("could not fit target polyomino")


def _general_grid(rng, difficulty, profile, colors):
    height, width = _difficulty_dimensions(rng, difficulty)
    grid = _blank(height, width)
    marker = colors[0]
    grid[0][0] = marker

    if profile in ("varied_poly", "two_colors", "five_colors"):
        targets = _interior_poly(rng, height, width)
    elif profile == "target_multicomponent":
        top = rng.randint(2, height - 6)
        left = rng.randint(1, width - 7)
        first_shape = rng.choice((
            ((0, 0), (1, 0), (1, 1)),
            ((0, 0), (0, 1), (1, 0)),
        ))
        second_shape = rng.choice((
            ((0, 1), (1, 0), (1, 1)),
            ((0, 0), (0, 1), (1, 1)),
        ))
        first = _translated(first_shape, top, left)
        second = _translated(second_shape, top + 2, left + 3)
        targets = first + second
    elif profile == "singleton_target":
        targets = ((rng.randint(2, height - 2), rng.randint(1, width - 2)),)
    elif profile == "horizontal_line":
        length = rng.randint(3, min(8, width - 2))
        row = rng.randint(2, height - 2)
        left = rng.randint(1, width - length - 1)
        targets = tuple((row, left + offset) for offset in range(length))
    elif profile == "vertical_line":
        length = rng.randint(3, min(8, height - 2))
        top = rng.randint(2, height - length)
        col = rng.randint(1, width - 2)
        targets = tuple((top + offset, col) for offset in range(length))
    elif profile == "target_at_edge":
        for _ in range(100):
            shape = _random_polyomino(rng, 4, min(12, height + width))
            shape_h = max(row for row, _ in shape) + 1
            shape_w = max(col for _, col in shape) + 1
            if shape_h <= height - 2 and shape_w <= width - 1:
                break
        else:
            raise RuntimeError("could not fit edge target polyomino")
        if rng.random() < 0.5 and shape_h <= height - 2:
            top = height - shape_h
            left = rng.randint(1, width - shape_w)
        else:
            top = rng.randint(2, height - shape_h)
            left = width - shape_w
        targets = _translated(shape, top, left)
    elif profile == "foreign_inside_crop":
        box_h = rng.randint(3, min(6, height - 3))
        box_w = rng.randint(3, min(7, width - 2))
        top = rng.randint(2, height - box_h - 1)
        left = rng.randint(1, width - box_w - 1)
        corners = (
            (top, left), (top, left + box_w - 1),
            (top + box_h - 1, left), (top + box_h - 1, left + box_w - 1),
        )
        boundary = [
            (row, col)
            for row in range(top, top + box_h)
            for col in range(left, left + box_w)
            if row in (top, top + box_h - 1) or col in (left, left + box_w - 1)
            if (row, col) not in corners
        ]
        extras = rng.sample(boundary, rng.randint(0, min(4, len(boundary))))
        targets = corners + tuple(extras)
    elif profile == "origin_inside_crop":
        box_h = rng.randint(3, min(6, height - 1))
        box_w = rng.randint(3, min(7, width - 1))
        corners = ((0, box_w - 1), (box_h - 1, 0), (box_h - 1, box_w - 1))
        boundary = [
            (row, col)
            for row in range(box_h)
            for col in range(box_w)
            if row in (0, box_h - 1) or col in (0, box_w - 1)
            if (row, col) not in corners and (row, col) != (0, 0)
        ]
        extras = rng.sample(boundary, rng.randint(1, min(5, len(boundary))))
        targets = corners + tuple(extras)
    elif profile == "wide_bbox_sparse":
        top = 2
        left = 1
        bottom = height - 2
        right = width - 2
        first_neighbor = rng.choice(((top, left + 1), (top + 1, left)))
        second_neighbor = rng.choice(((bottom, right - 1), (bottom - 1, right)))
        targets = ((top, left), first_neighbor, second_neighbor, (bottom, right))
    else:
        raise ValueError(f"unknown general profile: {profile}")

    occupied = {(0, 0), *targets}
    _paint(grid, targets, marker)
    target_bbox = _bbox(targets)

    distractor_colors = list(colors[1:])
    if profile == "foreign_inside_crop":
        r1, c1, r2, c2 = target_bbox
        inside = [
            (row, col)
            for row in range(r1 + 1, r2)
            for col in range(c1 + 1, c2)
            if (row, col) not in occupied
        ]
        cell = rng.choice(inside)
        foreign = distractor_colors.pop(0)
        grid[cell[0]][cell[1]] = foreign
        occupied.add(cell)
    _add_distractors(grid, rng, distractor_colors, target_bbox, occupied)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    color_count = 2 if profile == "two_colors" else 5 if profile == "five_colors" else 3
    colors = tuple(context.draw_distinct_colors("scene_colors", n=color_count, exclude={0}))
    rng = context.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        grid = _grid_from_public(profile, colors)
    else:
        grid = _general_grid(rng, difficulty, profile, colors)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed marker-crop lessons and nearest shortcut impostors."""
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    if not errors:
        expected = [
            list(grid[row][info["bbox"][1]:info["bbox"][3] + 1])
            for row in range(info["bbox"][0], info["bbox"][2] + 1)
        ]
        if rule_mirror(grid) != expected:
            errors.append("rule mirror changed cells inside the inclusive target bbox")
    return errors
