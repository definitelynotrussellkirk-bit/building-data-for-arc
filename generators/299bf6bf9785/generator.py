"""Semantic generator for ARC task 299bf6bf9785.

Filter all objects to solid color-1 rectangles, sort by cell count, choose
index floor(n/2), and recolor that entire rectangle to 8. Thus even counts
use the upper median; non-solid blue objects and other-color rectangles are
ignored.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "299bf6bf9785"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3cd4b679fcd2"
SUMMARY = "Recolor the upper-median-area solid color-1 rectangle to 8 after filtering all other objects."

INVARIANTS = [
    "at least one solid color-1 rectangle exists",
    "candidate rectangle areas are distinct",
    "the floor(n/2) size-sorted candidate is recolored to 8",
    "all non-target cells remain unchanged",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "three_rectangles",
    "one_rectangle",
    "two_rectangles",
    "four_rectangles",
    "five_rectangles",
    "nonsolid_blue_decoy",
    "solid_other_color_decoy",
    "mixed_filtered_decoys",
    "median_at_edge",
    "median_skinny",
    "spatial_order_counterexample",
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


# Role 1 remains literal color 1 because it is semantic. Other nonzero roles
# are nuisance decorations whose actual colors may vary.
_PUBLIC_MASKS = {
    "public_train_1": (
        "00000000000000", "00000001111000", "00000001111000", "00222000000000",
        "00020000000000", "00000000111100", "00000000111100", "00000000111100",
        "00000000111100", "00000000000000", "00000000110000", "00000000110000",
        "00000000000000", "00000000000000",
    ),
    "public_train_2": (
        "000000000222", "011111000020", "011111000000", "000000000000",
        "000000000000", "000111110111", "000111110111", "000111110111",
        "000111110111", "000000000000", "000000000000", "000000000000",
    ),
    "public_train_3": (
        "0000000000000", "0000000000000", "0000000000000", "0000000000000",
        "0000000000000", "0000002220000", "0000000200000", "1100000000000",
        "1100111011110", "1100111011110", "0000111011110", "0000111011110",
        "0000000000000",
    ),
    "public_train_4": (
        "0000000022200", "0000000002000", "0000000000000", "0000111100000",
        "0000111100000", "0000000000000", "0000000000000", "0011111011110",
        "0011111011110", "0011111011110", "0000000011110", "0000000000000",
        "0000000000000",
    ),
    "public_test_1": (
        "000000000000", "002220001110", "000200001110", "000000001110",
        "000000000000", "000000111110", "000000111110", "000000000000",
        "000000000000", "000000000000", "000000011110", "000000011110",
    ),
}
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}


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
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in _CARDINAL:
                    nr, nc = current_row + dr, current_col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
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
                "solid": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
            })
    return components


def _semantic_signature(grid):
    others = []
    for row in grid:
        for value in row:
            if value not in (0, 1) and value not in others:
                others.append(value)
    roles = {value: index + 2 for index, value in enumerate(others)}
    return tuple(
        "".join("1" if value == 1 else str(roles.get(value, 0)) for value in row)
        for row in grid
    )


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
    components = _components(grid) if not errors else []
    candidates = [component for component in components if component["color"] == 1 and component["solid"]]
    if not candidates:
        errors.append("at least one solid color-1 rectangle is required")
    if len(candidates) > 5:
        errors.append(f"expected at most five candidate rectangles, got {len(candidates)}")
    if len({component["size"] for component in candidates}) != len(candidates):
        errors.append("candidate rectangle areas must be distinct")
    result = {
        "errors": errors,
        "components": components,
        "candidates": candidates,
        "scene_profile": None,
        "height": height,
        "width": width,
    }
    if errors:
        return result

    ordered = sorted(candidates, key=lambda component: component["size"])
    target = ordered[len(ordered) // 2]
    output = [list(row) for row in grid]
    for row, col in target["cells"]:
        output[row][col] = 8
    nonsolid_blue = any(component["color"] == 1 and not component["solid"] for component in components)
    solid_other = any(component["color"] != 1 and component["solid"] for component in components)
    nonsolid_other = any(component["color"] != 1 and not component["solid"] for component in components)
    sizes = tuple(component["size"] for component in ordered)
    profile = _PUBLIC_SIGNATURES.get(_semantic_signature(grid))
    if profile is None:
        if nonsolid_blue and solid_other and sizes == (4, 8, 15):
            profile = "mixed_filtered_decoys"
        elif nonsolid_blue and not solid_other and sizes == (4, 8, 15):
            profile = "nonsolid_blue_decoy"
        elif solid_other and not nonsolid_blue and sizes == (4, 8, 15):
            profile = "solid_other_color_decoy"
        elif sizes == (6,) and nonsolid_other:
            profile = "one_rectangle"
        elif sizes == (4, 9) and nonsolid_other:
            profile = "two_rectangles"
        elif sizes == (2, 6, 12, 20) and nonsolid_other:
            profile = "four_rectangles"
        elif sizes == (2, 4, 8, 12, 20) and nonsolid_other:
            profile = "five_rectangles"
        elif sizes == (4, 8, 15) and (target["r1"] in (0, height - 1) or target["c1"] in (0, width - 1) or target["r2"] == height - 1 or target["c2"] == width - 1):
            profile = "median_at_edge"
        elif sizes == (4, 8, 12) and (target["r1"] == target["r2"] or target["c1"] == target["c2"]):
            profile = "median_skinny"
        elif sizes == (4, 8, 15) and [component["size"] for component in candidates] == [15, 8, 4]:
            profile = "spatial_order_counterexample"
        elif sizes == (4, 8, 15) and nonsolid_other:
            profile = "three_rectangles"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized rectangle lesson {profile!r}")
    result.update({
        "errors": errors,
        "ordered": ordered,
        "target": target,
        "output": output,
        "candidate_sizes": sizes,
        "nonsolid_blue": nonsolid_blue,
        "solid_other": solid_other,
        "scene_profile": profile,
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
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _grid_from_public(profile, decoration_color):
    return [
        [0 if role == "0" else 1 if role == "1" else decoration_color for role in row]
        for row in _PUBLIC_MASKS[profile]
    ]


def _difficulty_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(11, 14), rng.randint(12, 15)
    if difficulty == "hard":
        return rng.randint(16, 21), rng.randint(17, 22)
    return rng.randint(13, 17), rng.randint(14, 18)


def _rectangle_cells(row, col, rect_height, rect_width):
    return tuple(
        (row + dr, col + dc)
        for dr in range(rect_height)
        for dc in range(rect_width)
    )


def _bbox(cells):
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def _boxes_touch(first, second, moat=1):
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    return not (ar2 + moat < br1 or br2 + moat < ar1 or ac2 + moat < bc1 or bc2 + moat < ac1)


def _place_rectangles(rng, height, width, shapes, *, edge_index=None, spatial=False):
    if spatial:
        # Areas arrive ascending; place largest, median, smallest top-to-bottom.
        placements = [None] * 3
        row = 0
        for index in (2, 1, 0):
            rect_height, rect_width = shapes[index]
            placements[index] = _rectangle_cells(row, 1, rect_height, rect_width)
            row += rect_height + 1
        return placements
    placements = []
    boxes = []
    for index, (rect_height, rect_width) in enumerate(shapes):
        for _ in range(300):
            if index == edge_index:
                side = rng.choice(("bottom", "right"))
                row = height - rect_height if side == "bottom" else rng.randint(0, height - rect_height)
                col = width - rect_width if side == "right" else rng.randint(0, width - rect_width)
            else:
                row = rng.randint(1, height - rect_height - 1)
                col = rng.randint(1, width - rect_width - 1)
            cells = _rectangle_cells(row, col, rect_height, rect_width)
            box = _bbox(cells)
            if all(not _boxes_touch(box, old) for old in boxes):
                placements.append(cells)
                boxes.append(box)
                break
        else:
            return None
    return placements


_SPECS = {
    "three_rectangles": ((2, 2), (2, 4), (3, 5)),
    "one_rectangle": ((2, 3),),
    "two_rectangles": ((2, 2), (3, 3)),
    "four_rectangles": ((1, 2), (2, 3), (3, 4), (4, 5)),
    "five_rectangles": ((1, 2), (2, 2), (2, 4), (3, 4), (4, 5)),
    "nonsolid_blue_decoy": ((2, 2), (2, 4), (3, 5)),
    "solid_other_color_decoy": ((2, 2), (2, 4), (3, 5)),
    "mixed_filtered_decoys": ((2, 2), (2, 4), (3, 5)),
    "median_at_edge": ((2, 2), (2, 4), (3, 5)),
    "median_skinny": ((2, 2), (1, 8), (3, 4)),
    "spatial_order_counterexample": ((2, 2), (2, 4), (3, 5)),
}


def _place_decoration(grid, rng, shape, color, occupied_boxes):
    height, width = len(grid), len(grid[0])
    shape_height = max(r for r, _ in shape) + 1
    shape_width = max(c for _, c in shape) + 1
    for _ in range(200):
        top = rng.randint(0, height - shape_height)
        left = rng.randint(0, width - shape_width)
        box = (top, left, top + shape_height - 1, left + shape_width - 1)
        if all(not _boxes_touch(box, old) for old in occupied_boxes):
            for row, col in shape:
                grid[top + row][left + col] = color
            occupied_boxes.append(box)
            return True
    return False


def _general_grid(rng, difficulty, profile, decoration_colors):
    shapes = _SPECS[profile]
    for _ in range(100):
        height, width = _difficulty_dimensions(rng, difficulty)
        placements = _place_rectangles(
            rng,
            height,
            width,
            shapes,
            edge_index=1 if profile == "median_at_edge" else None,
            spatial=profile == "spatial_order_counterexample",
        )
        if placements is None:
            continue
        grid = _blank(height, width)
        for cells in placements:
            for row, col in cells:
                grid[row][col] = 1
        occupied = [_bbox(cells) for cells in placements]
        additions = []
        if profile in ("nonsolid_blue_decoy", "mixed_filtered_decoys"):
            additions.append((((0, 0), (1, 0), (1, 1)), 1))
        if profile in ("solid_other_color_decoy", "mixed_filtered_decoys"):
            additions.append((((0, 0), (0, 1), (1, 0), (1, 1)), decoration_colors[0]))
        # Public inputs contain an irrelevant non-solid decoration too.
        additions.append((((0, 0), (0, 1), (0, 2), (1, 1)), decoration_colors[-1]))
        if not all(_place_decoration(grid, rng, shape, color, occupied) for shape, color in additions):
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
    decoration_colors = tuple(context.draw_distinct_colors("decoration_colors", n=2, exclude={0, 1, 8}))
    rng = context.draw_rng("scene")
    # Eight nuisance colors let each materialized seed retain a distinct linked
    # public input. Color 8 is safe here: only color-1 rectangles are candidates.
    public_palette = (2, 3, 4, 5, 6, 7, 8, 9)
    public_color = public_palette[
        (seed + PUBLIC_PROFILES.index(profile) * 2) % len(public_palette)
    ] if profile in PUBLIC_PROFILES else None
    grid = (
        _grid_from_public(profile, public_color)
        if profile in PUBLIC_PROFILES
        else _general_grid(rng, difficulty, profile, decoration_colors)
    )
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
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
        changed = {
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if info["output"][row][col] != value
        }
        if changed != set(info["target"]["cells"]):
            errors.append("output must change exactly the upper-median rectangle cells")
    return errors
