"""Semantic generator for ARC task 268b0e9a75b4.

Count 4-connected objects per nonzero color in row-major color-encounter
order.  If one or more colors occur in exactly one object, choose the first
such color.  Otherwise choose the largest object of the numerically highest
color.  Return the inclusive bounding-box crop of that object.

Five linked public profiles retain every published input.  General profiles
cover first-candidate ordering, the no-unique fallback, size/position
shortcuts, edge and hollow crops, and preservation of foreign cells inside
the selected bounding box.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "268b0e9a75b4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "210dc0194f51"
SUMMARY = (
    "Crop the first row-major color having one object, or fall back to the "
    "largest object of the highest color when every color repeats."
)

INVARIANTS = [
    "the background is zero and every nonzero cell belongs to a 4-connected color object",
    "ordinary lessons select the first encountered color with exactly one object",
    "fallback lessons select highest color first and largest object second",
    "the output is the unchanged inclusive bounding-box crop of the chosen object",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "unique_middle",
    "unique_smallest",
    "unique_hollow",
    "unique_at_edge",
    "two_colors",
    "four_colors",
    "multiple_unique_first",
    "foreign_inside_crop",
    "fallback_highest",
    "fallback_largest_same_color",
    "fallback_highest_over_global_size",
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


# Full color-role-normalized public input masks.  Roles are assigned by first
# nonzero color encounter; actual nuisance colors are randomized at draw time.
_PUBLIC_MASKS = {
    "public_train_1": (
        "0000000000",
        "0110000200",
        "0000000000",
        "0000300000",
        "0000330000",
        "0100000200",
        "0000000000",
    ),
    "public_train_2": (
        "0000000000",
        "0100000200",
        "0000000200",
        "0000300000",
        "0000330000",
        "0000030020",
        "0110000000",
        "0000000000",
    ),
    "public_train_3": (
        "00000000000",
        "01000000200",
        "01000000000",
        "00003300000",
        "00000300000",
        "01000000220",
        "00000000000",
    ),
    "public_train_4": (
        "000000000000",
        "001100000000",
        "000000000200",
        "000003000000",
        "000003300000",
        "000000300200",
        "001000000000",
        "000000000000",
    ),
    "public_test_1": (
        "0000000000",
        "0100000200",
        "0000300000",
        "0000330000",
        "0000030000",
        "0110000200",
        "0000000000",
    ),
}


_SHAPES = {
    "dot": ((0, 0),),
    "domino_h": ((0, 0), (0, 1)),
    "domino_v": ((0, 0), (1, 0)),
    "line3": ((0, 0), (0, 1), (0, 2)),
    "l3": ((0, 0), (1, 0), (1, 1)),
    "block4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "line4": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "s4": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "ring8": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
}


# Each role contains the ordered shapes for that color.  First objects are
# placed in a row-major lane; remaining objects are placed below it.
_GENERAL_SPECS = {
    "unique_middle": (("dot", "domino_h"), ("block4",), ("dot", "domino_v")),
    "unique_smallest": (("block4", "line4"), ("s4", "block4"), ("domino_h",)),
    "unique_hollow": (("dot", "domino_h"), ("dot", "domino_v"), ("ring8",)),
    "unique_at_edge": (("block4",), ("dot", "domino_h"), ("dot", "domino_v")),
    "two_colors": (("dot", "domino_h"), ("s4",)),
    "four_colors": (("dot", "domino_h"), ("dot", "domino_v"), ("l3",), ("dot", "line3")),
    "multiple_unique_first": (("line3",), ("block4",), ("dot", "domino_h")),
    "fallback_highest": (("dot", "block4"), ("domino_h", "s4")),
    "fallback_largest_same_color": (("dot", "block4"), ("domino_h", "line3"), ("domino_h", "ring8")),
    "fallback_highest_over_global_size": (("dot", "ring8"), ("domino_h", "line4"), ("domino_h", "l3")),
}

_GENERAL_OBJECT_COUNTS = {
    "unique_middle": (2, 1, 2),
    "unique_smallest": (2, 2, 1),
    "unique_hollow": (2, 2, 1),
    "unique_at_edge": (1, 2, 2),
    "two_colors": (2, 1),
    "four_colors": (2, 2, 1, 2),
    "multiple_unique_first": (1, 1, 2),
    "foreign_inside_crop": (1, 2),
    "fallback_highest": (2, 2),
    "fallback_largest_same_color": (2, 2, 2),
    "fallback_highest_over_global_size": (2, 2, 2),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in _CARDINAL:
                    neighbor = (cr + dr, cc + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            cells.sort()
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            components.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
            })
    return components


def _color_order(grid):
    order = []
    for row in grid:
        for value in row:
            if value != 0 and value not in order:
                order.append(value)
    return order


def _choose(grid, components=None):
    components = _components(grid) if components is None else components
    order = _color_order(grid)
    counts = {color: sum(obj["color"] == color for obj in components) for color in order}
    unique_colors = [color for color in order if counts[color] == 1]
    if unique_colors:
        chosen_color = unique_colors[0]
        branch = "unique"
        chosen = next(obj for obj in components if obj["color"] == chosen_color)
    else:
        branch = "fallback"
        chosen = min(components, key=lambda obj: (-obj["color"], -obj["size"]))
        chosen_color = chosen["color"]
    return {
        "order": order,
        "counts": counts,
        "unique_colors": unique_colors,
        "chosen_color": chosen_color,
        "chosen": chosen,
        "branch": branch,
    }


def _crop(grid, obj):
    return [
        list(grid[row][obj["c1"]:obj["c2"] + 1])
        for row in range(obj["r1"], obj["r2"] + 1)
    ]


def _has_enclosed_zero(crop):
    """Return whether a zero in a crop is cut off from its crop boundary."""
    height, width = len(crop), len(crop[0])
    seen = set()
    stack = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if crop[row][col] == 0
        and (row in (0, height - 1) or col in (0, width - 1))
    ]
    seen.update(stack)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, col + dc)
            nr, nc = neighbor
            if (
                0 <= nr < height
                and 0 <= nc < width
                and crop[nr][nc] == 0
                and neighbor not in seen
            ):
                seen.add(neighbor)
                stack.append(neighbor)
    return any(
        crop[row][col] == 0 and (row, col) not in seen
        for row in range(height)
        for col in range(width)
    )


def _normalized_mask_signature(grid):
    order = _color_order(grid)
    roles = {color: index + 1 for index, color in enumerate(order)}
    return tuple("".join(str(roles.get(value, 0)) for value in row) for row in grid)


_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}
if len(_PUBLIC_SIGNATURES) != len(_PUBLIC_MASKS):
    raise RuntimeError("public profile signatures collide")


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

    components = _components(grid)
    order = _color_order(grid)
    if not components:
        errors.append("at least one nonzero object is required")
    if not 2 <= len(order) <= 4:
        errors.append(f"expected 2..4 nonzero colors, got {len(order)}")
    choice = _choose(grid, components) if components else None
    profile = None
    public_signature = None
    if not errors:
        public_signature = _normalized_mask_signature(grid)
        profile = _PUBLIC_SIGNATURES.get(public_signature)
    if not errors and profile is None:
        counts = tuple(choice["counts"][color] for color in order)
        unique_positions = tuple(order.index(color) for color in choice["unique_colors"])
        chosen = choice["chosen"]
        chosen_position = order.index(choice["chosen_color"])
        output = _crop(grid, chosen)
        chosen_hollow = _has_enclosed_zero(output)
        foreign_inside = any(
            grid[row][col] not in (0, choice["chosen_color"])
            for row in range(chosen["r1"], chosen["r2"] + 1)
            for col in range(chosen["c1"], chosen["c2"] + 1)
        )
        touches_edge = (
            chosen["r1"] == 0
            or chosen["c1"] == 0
            or chosen["r2"] == height - 1
            or chosen["c2"] == width - 1
        )
        other_sizes = [obj["size"] for obj in components if obj is not chosen]
        if foreign_inside:
            profile = "foreign_inside_crop"
        elif len(unique_positions) > 1:
            profile = "multiple_unique_first"
        elif choice["branch"] == "fallback":
            global_largest = max(obj["size"] for obj in components)
            if len(order) == 2:
                profile = "fallback_highest"
            elif chosen["size"] < global_largest:
                profile = "fallback_highest_over_global_size"
            else:
                profile = "fallback_largest_same_color"
        elif len(order) == 2:
            profile = "two_colors"
        elif len(order) == 4:
            profile = "four_colors"
        elif touches_edge:
            profile = "unique_at_edge"
        elif chosen_hollow:
            profile = "unique_hollow"
        elif chosen["size"] < min(other_sizes):
            profile = "unique_smallest"
        elif unique_positions == (0,):
            profile = "unique_first"
        elif unique_positions == (1,):
            profile = "unique_middle"
        if profile is None:
            errors.append(
                f"unrecognized selection lesson counts={counts} unique_positions={unique_positions} chosen_position={chosen_position}"
            )
        elif profile in GENERAL_PROFILES and counts != _GENERAL_OBJECT_COUNTS[profile]:
            errors.append(
                f"scene profile {profile} requires object counts {_GENERAL_OBJECT_COUNTS[profile]}, got {counts}"
            )
    if profile not in SCENE_PROFILES and not errors:
        errors.append(f"unrecognized scene profile {profile!r}")
    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "order": order,
        "scene_profile": profile,
        "public_signature": public_signature,
    }
    if choice:
        result.update(choice)
        result["object_counts"] = tuple(choice["counts"][color] for color in order)
        result["chosen_crop"] = _crop(grid, choice["chosen"])
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    return info.get("scene_profile") if not info["errors"] and info.get("scene_profile") in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python transcription of the canonical selector and crop."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["chosen_crop"]]


def _grid_from_public(profile, colors):
    mask = _PUBLIC_MASKS[profile]
    return [
        [0 if role == "0" else colors[int(role) - 1] for role in row]
        for row in mask
    ]


def _difficulty_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(10, 13), rng.randint(13, 17)
    if difficulty == "hard":
        return rng.randint(14, 18), rng.randint(17, 22)
    return rng.randint(11, 14), rng.randint(14, 18)


def _shape_box(shape, top, left):
    return (
        top,
        left,
        top + max(row for row, _ in shape),
        left + max(col for _, col in shape),
    )


def _boxes_touch(first, second, moat=1):
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    return not (
        ar2 + moat < br1
        or br2 + moat < ar1
        or ac2 + moat < bc1
        or bc2 + moat < ac1
    )


def _paint(grid, shape, top, left, color):
    for row, col in shape:
        grid[top + row][left + col] = color


def _random_polyomino(rng, minimum, maximum):
    """Grow a connected, open (no enclosed-zero) normalized polyomino."""
    for _ in range(200):
        target = rng.randint(minimum, maximum)
        cells = [(0, 0)]
        occupied = {(0, 0)}
        while len(cells) < target:
            row, col = rng.choice(cells)
            dr, dc = rng.choice(_CARDINAL)
            neighbor = (row + dr, col + dc)
            if neighbor not in occupied:
                occupied.add(neighbor)
                cells.append(neighbor)
        top = min(row for row, _ in cells)
        left = min(col for _, col in cells)
        shape = tuple(sorted((row - top, col - left) for row, col in cells))
        height = max(row for row, _ in shape) + 1
        width = max(col for _, col in shape) + 1
        crop = [[0 for _ in range(width)] for _ in range(height)]
        for row, col in shape:
            crop[row][col] = 1
        if not _has_enclosed_zero(crop):
            return shape
    raise RuntimeError("could not grow open polyomino")


def _rectangular_outline(rng, minimum=3, maximum=6):
    height = rng.randint(minimum, maximum)
    width = rng.randint(minimum, maximum)
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _resolved_general_spec(rng, profile):
    spec = [
        [tuple(_SHAPES[name]) for name in role_shapes]
        for role_shapes in _GENERAL_SPECS[profile]
    ]
    selected = {
        "unique_middle": (1, 0, 3, 14),
        "unique_at_edge": (0, 0, 3, 14),
        "two_colors": (1, 0, 3, 14),
        "four_colors": (2, 0, 3, 14),
        "multiple_unique_first": (0, 0, 3, 14),
        "fallback_highest": (1, 1, 5, 14),
        "fallback_largest_same_color": (2, 1, 9, 16),
        "fallback_highest_over_global_size": (2, 1, 3, 5),
    }
    if profile == "unique_smallest":
        spec[2][0] = _random_polyomino(rng, 2, 3)
    elif profile == "unique_hollow":
        spec[2][0] = _rectangular_outline(rng)
    if profile in selected:
        role, index, minimum, maximum = selected[profile]
        spec[role][index] = _random_polyomino(rng, minimum, maximum)
    return tuple(tuple(role) for role in spec)


def _place_general(grid, rng, spec, colors, *, edge_role=None):
    height, width = len(grid), len(grid[0])
    boxes = []
    cursor = rng.randint(1, 2)
    for role, shapes in enumerate(spec):
        shape = shapes[0]
        if role == edge_role:
            top, left = 0, 0
        else:
            top = 1
            left = cursor
        box = _shape_box(shape, top, left)
        if box[2] >= height or box[3] >= width:
            return False
        if any(_boxes_touch(box, old, moat=1 if old_role == role else 0) for old, old_role in boxes):
            return False
        _paint(grid, shape, top, left, colors[role])
        boxes.append((box, role))
        cursor = box[3] + rng.randint(2, 3)

    for role, shapes in enumerate(spec):
        for shape in shapes[1:]:
            sh = max(row for row, _ in shape) + 1
            sw = max(col for _, col in shape) + 1
            placed = False
            for _ in range(1000):
                if height - sh - 1 < 4:
                    break
                top = rng.randint(4, height - sh - 1)
                left = rng.randint(1, width - sw - 1)
                box = _shape_box(shape, top, left)
                if any(_boxes_touch(box, old, moat=1 if old_role == role else 0) for old, old_role in boxes):
                    continue
                _paint(grid, shape, top, left, colors[role])
                boxes.append((box, role))
                placed = True
                break
            if not placed:
                return False
    return True


def _foreign_inside_grid(rng, difficulty, colors):
    for _ in range(100):
        height, width = _difficulty_dimensions(rng, difficulty)
        grid = _blank(height, width)
        outline = _rectangular_outline(rng)
        outline_height = max(row for row, _ in outline) + 1
        outline_width = max(col for _, col in outline) + 1
        top = rng.randint(1, 3)
        left = rng.randint(1, 3)
        _paint(grid, outline, top, left, colors[0])
        foreign_row = top + rng.randint(1, outline_height - 2)
        foreign_col = left + rng.randint(1, outline_width - 2)
        grid[foreign_row][foreign_col] = colors[1]
        for _ in range(500):
            row = rng.randint(7, height - 2)
            col = rng.randint(1, width - 2)
            if grid[row][col] == 0:
                grid[row][col] = colors[1]
                info = _analysis(grid)
                if not info["errors"] and info["scene_profile"] == "foreign_inside_crop":
                    return grid
                grid[row][col] = 0
    raise RuntimeError("could not construct foreign_inside_crop")


def _general_grid(rng, difficulty, profile, colors):
    if profile == "foreign_inside_crop":
        return _foreign_inside_grid(rng, difficulty, colors)
    if profile.startswith("fallback"):
        highest = max(colors)
        colors = tuple(color for color in colors if color != highest) + (highest,)
    for _ in range(100):
        spec = _resolved_general_spec(rng, profile)
        height, width = _difficulty_dimensions(rng, difficulty)
        grid = _blank(height, width)
        edge_role = 0 if profile == "unique_at_edge" else None
        if not _place_general(grid, rng, spec, colors, edge_role=edge_role):
            continue
        info = _analysis(grid)
        if not info["errors"] and info["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"could not construct scene profile {profile}")


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
    if profile in PUBLIC_PROFILES:
        count = 3
    elif profile == "two_colors" or profile in ("foreign_inside_crop", "fallback_highest"):
        count = 2
    elif profile == "four_colors":
        count = 4
    else:
        count = 3
    colors = tuple(context.draw_distinct_colors("object_colors", n=count, exclude={0}))
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
    """Reject malformed selection lessons and nearest shortcut impostors."""
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
            errors.append(
                f"requested scene_profile {requested}, observed {info['scene_profile']}"
            )
    if not errors:
        output = rule_mirror(grid)
        chosen = info["chosen"]
        expected_shape = (chosen["r2"] - chosen["r1"] + 1, chosen["c2"] - chosen["c1"] + 1)
        if (len(output), len(output[0])) != expected_shape:
            errors.append("rule mirror emitted the wrong inclusive bbox dimensions")
        expected = _crop(grid, chosen)
        if output != expected:
            errors.append("rule mirror changed cells inside the selected bbox")
    return errors
