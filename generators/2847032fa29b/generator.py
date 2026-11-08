"""Semantic generator for ARC task 2847032fa29b.

Extract every 4-connected nonzero color component, sort components by cell
count and then numeric color, crop each component from the unchanged input,
and concatenate those crops top-aligned with one zero column between them.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "2847032fa29b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4aee1598717a"
SUMMARY = "Sort component crops by (cell count, numeric color) and form a top-aligned one-column-gapped gallery."

INVARIANTS = [
    "the input contains 2..5 four-connected nonzero color components",
    "components are ordered by cell count ascending and numeric color ascending on ties",
    "each crop is an unchanged inclusive bbox subgrid of the input",
    "crops are top-aligned and separated by exactly one zero column",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_train_4", "public_test_1",
)
GENERAL_PROFILES = (
    "equal_size_color_order", "varied_sizes", "two_objects", "four_objects", "five_objects",
    "tall_wide_alignment", "foreign_inside_crop", "hollow_object", "same_color_components",
    "size_over_color", "cell_count_not_bbox_area",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "weighted rng; five linked public profiles in sixteen", "valid": "|".join(SCENE_PROFILES)}}

_PUBLIC_MASKS = {
    "public_train_1": ("000000000000", "010000000000", "010000000000", "011000000000", "000000022000", "000000002200", "003330000000", "000300000000", "000000000000"),
    "public_train_2": ("0000000000000", "0000000011000", "0000000001000", "0000000001100", "0000000000000", "0200000000000", "0200003300000", "0220003300000", "0000003000000", "0000000000000"),
    "public_train_3": ("00000000000", "01110000000", "00100000000", "00000000000", "00000220000", "00000022000", "00000000300", "00000000300", "00000000330"),
    "public_train_4": ("000000000000", "001100000000", "001100000000", "001000000000", "000000022000", "000000002000", "000000002200", "030000000000", "030000000000", "033000000000"),
    "public_test_1": ("0000000000000", "0110000000000", "0011000000000", "0000000222000", "0000000020000", "0003300000000", "0003300000000", "0003000000000", "0000000000000"),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _components(grid):
    height, width = len(grid), len(grid[0]); seen = set(); components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]; seen.add((row, col)); cells = []
            while stack:
                cr, cc = stack.pop(); cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            cells.sort()
            components.append({"color": color, "cells": tuple(cells), "size": len(cells),
                               "r1": min(r for r, _ in cells), "c1": min(c for _, c in cells),
                               "r2": max(r for r, _ in cells), "c2": max(c for _, c in cells)})
    return components


def _crop(grid, component):
    return [list(grid[row][component["c1"]:component["c2"] + 1]) for row in range(component["r1"], component["r2"] + 1)]


def _gallery(grid, components=None):
    components = _components(grid) if components is None else components
    ordered = sorted(components, key=lambda component: (component["size"], component["color"]))
    crops = [_crop(grid, component) for component in ordered]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = _blank(height, width); left = 0
    for crop in crops:
        for row, values in enumerate(crop):
            output[row][left:left + len(values)] = values
        left += len(crop[0]) + 1
    return ordered, crops, output


def _color_order(grid):
    order = []
    for row in grid:
        for value in row:
            if value and value not in order: order.append(value)
    return order


def _normalized_mask_signature(grid):
    roles = {color: index + 1 for index, color in enumerate(_color_order(grid))}
    return tuple("".join(str(roles.get(value, 0)) for value in row) for row in grid)


_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}


def _has_enclosed_zero(crop):
    height, width = len(crop), len(crop[0]); seen = set()
    stack = [(r, c) for r in range(height) for c in range(width) if crop[r][c] == 0 and (r in (0, height - 1) or c in (0, width - 1))]
    seen.update(stack)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            cell = (row + dr, col + dc); r, c = cell
            if 0 <= r < height and 0 <= c < width and crop[r][c] == 0 and cell not in seen:
                seen.add(cell); stack.append(cell)
    return any(crop[r][c] == 0 and (r, c) not in seen for r in range(height) for c in range(width))


def _analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty grid"]}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid): return {"errors": ["ragged grid"]}
    errors = []
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9"); break
        if errors: break
    components = _components(grid) if not errors else []
    if not 2 <= len(components) <= 5: errors.append(f"expected 2..5 components, got {len(components)}")
    result = {"errors": errors, "height": height, "width": width, "components": components, "scene_profile": None}
    if errors: return result
    ordered, crops, output = _gallery(grid, components)
    foreign = any(any(value not in (0, component["color"]) for row in crop for value in row) for component, crop in zip(ordered, crops))
    hollow = any(_has_enclosed_zero(crop) for crop in crops)
    colors = [component["color"] for component in components]
    count = len(components); sizes = [component["size"] for component in ordered]
    areas = [(component["r2"] - component["r1"] + 1) * (component["c2"] - component["c1"] + 1) for component in ordered]
    heights = [len(crop) for crop in crops]; widths = [len(crop[0]) for crop in crops]
    profile = _PUBLIC_SIGNATURES.get(_normalized_mask_signature(grid))
    if profile is None:
        if foreign: profile = "foreign_inside_crop"
        elif len(set(colors)) < count: profile = "same_color_components"
        elif hollow: profile = "hollow_object"
        elif count == 2: profile = "two_objects"
        elif count == 4: profile = "four_objects"
        elif count == 5: profile = "five_objects"
        elif max(heights) >= 6 and max(widths) >= 6: profile = "tall_wide_alignment"
        elif any(areas[index] > areas[index + 1] for index in range(len(areas) - 1)): profile = "cell_count_not_bbox_area"
        elif len(set(sizes)) == 1: profile = "equal_size_color_order"
        elif len(set(sizes)) == count and [component["color"] for component in ordered] == sorted(colors, reverse=True): profile = "size_over_color"
        else: profile = "varied_sizes"
    if profile not in SCENE_PROFILES: errors.append(f"unrecognized gallery lesson {profile!r}")
    result.update({"errors": errors, "ordered": ordered, "crops": crops, "output": output, "sizes": tuple(sizes),
                   "bbox_areas": tuple(areas), "colors": tuple(colors), "foreign_inside": foreign,
                   "hollow": hollow, "scene_profile": profile, "output_shape": (len(output), len(output[0]))})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid); profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _grid_from_public(profile, colors):
    return [[0 if role == "0" else colors[int(role) - 1] for role in row] for row in _PUBLIC_MASKS[profile]]


def _difficulty_dimensions(rng, difficulty):
    if difficulty == "easy": return rng.randint(9, 11), rng.randint(11, 14)
    if difficulty == "hard": return rng.randint(12, 16), rng.randint(15, 20)
    return rng.randint(10, 13), rng.randint(12, 16)


def _normalize(shape):
    top = min(r for r, _ in shape); left = min(c for _, c in shape)
    return tuple(sorted((r - top, c - left) for r, c in shape))


def _transform(shape, variant):
    cells = list(shape)
    if variant & 4: cells = [(r, -c) for r, c in cells]
    for _ in range(variant & 3): cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _random_open_polyomino(rng, minimum, maximum):
    for _ in range(200):
        target = rng.randint(minimum, maximum); cells = {(0, 0)}
        while len(cells) < target:
            row, col = rng.choice(tuple(cells)); dr, dc = rng.choice(_CARDINAL); cells.add((row + dr, col + dc))
        shape = _normalize(cells); h = max(r for r, _ in shape) + 1; w = max(c for _, c in shape) + 1
        crop = _blank(h, w)
        for r, c in shape: crop[r][c] = 1
        if h >= 2 and w >= 2 and not _has_enclosed_zero(crop): return shape
    raise RuntimeError("could not grow open polyomino")


_DOMINO = ((0, 0), (0, 1))
_L3 = ((0, 0), (1, 0), (1, 1))
_BLOCK4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
_PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_OPEN7 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))
_OPEN8 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1))
_RING8 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))
_ZIG4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_LINE5 = tuple((0, c) for c in range(5))
_VLINE6 = tuple((r, 0) for r in range(6))
_HLINE6 = tuple((0, c) for c in range(6))


def _box(shape, top, left):
    return top, left, top + max(r for r, _ in shape), left + max(c for _, c in shape)


def _boxes_touch(first, second, moat=1):
    ar1, ac1, ar2, ac2 = first; br1, bc1, br2, bc2 = second
    return not (ar2 + moat < br1 or br2 + moat < ar1 or ac2 + moat < bc1 or bc2 + moat < ac1)


def _place_shapes(rng, height, width, shapes):
    placements = []
    for shape in shapes:
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        for _ in range(300):
            top = rng.randint(0, height - sh); left = rng.randint(0, width - sw); box = _box(shape, top, left)
            if all(not _boxes_touch(box, old_box) for _, _, old_box in placements):
                placements.append((top, left, box)); break
        else: return None
    return placements


def _paint_scene(grid, shapes, colors, placements):
    for shape, color, (top, left, _) in zip(shapes, colors, placements):
        for row, col in shape: grid[top + row][left + col] = color


def _general_spec(rng, profile, colors):
    variant = lambda shape: _transform(shape, rng.randrange(8))
    if profile == "equal_size_color_order":
        shapes = [variant(_L4), variant(_ZIG4), variant(_BLOCK4)]; assigned = list(colors[:3])
    elif profile in ("varied_sizes", "size_over_color"):
        shapes = [variant(_DOMINO), variant(_BLOCK4), variant(_OPEN8)]
        assigned = sorted(colors[:3], reverse=profile == "size_over_color")
    elif profile == "two_objects":
        shapes = [_random_open_polyomino(rng, 3, 5), _random_open_polyomino(rng, 7, 11)]; assigned = list(colors[:2])
    elif profile == "four_objects":
        shapes = [variant(_DOMINO), variant(_L3), _random_open_polyomino(rng, 5, 7), _random_open_polyomino(rng, 8, 12)]; assigned = list(colors[:4])
    elif profile == "five_objects":
        shapes = [((0, 0),), variant(_DOMINO), variant(_L3), variant(_L4), _random_open_polyomino(rng, 5, 8)]; assigned = list(colors[:5])
    elif profile == "tall_wide_alignment":
        shapes = [variant(_L3), _VLINE6, _HLINE6]; assigned = list(colors[:3])
    elif profile == "hollow_object":
        shapes = [variant(_DOMINO), variant(_BLOCK4), _RING8]; assigned = list(colors[:3])
    elif profile == "same_color_components":
        shapes = [variant(_L3), _random_open_polyomino(rng, 5, 6), _random_open_polyomino(rng, 8, 10)]; assigned = [colors[0], colors[0], colors[1]]
    elif profile == "cell_count_not_bbox_area":
        shapes = [variant(_ZIG4), variant(_LINE5), variant(_OPEN7)]; assigned = list(colors[:3])
    else: raise ValueError(f"unknown profile {profile}")
    return shapes, assigned


def _foreign_scene(rng, difficulty, colors):
    height, width = _difficulty_dimensions(rng, difficulty); grid = _blank(height, width)
    top = rng.randint(1, height - 5); left = rng.randint(1, width - 5)
    for row, col in _RING8: grid[top + row][left + col] = colors[0]
    grid[top + 1][left + 1] = colors[1]
    line = _transform(_L4, rng.randrange(8)); sh = max(r for r, _ in line) + 1; sw = max(c for _, c in line) + 1
    for _ in range(200):
        r0 = rng.randint(0, height - sh); c0 = rng.randint(0, width - sw)
        if not _boxes_touch(_box(line, r0, c0), (top, left, top + 2, left + 2), moat=1):
            for row, col in line: grid[r0 + row][c0 + col] = colors[2]
            return grid
    raise RuntimeError("could not place external component")


def _general_grid(rng, difficulty, profile, colors):
    if profile == "foreign_inside_crop": return _foreign_scene(rng, difficulty, colors)
    shapes, assigned = _general_spec(rng, profile, colors)
    for _ in range(100):
        height, width = _difficulty_dimensions(rng, difficulty); placements = _place_shapes(rng, height, width, shapes)
        if placements is None: continue
        if profile == "equal_size_color_order":
            spatial = sorted(range(len(placements)), key=lambda i: (placements[i][0], placements[i][1]))
            descending = sorted(assigned, reverse=True); remapped = assigned[:]
            for index, color in zip(spatial, descending): remapped[index] = color
            assigned = remapped
        grid = _blank(height, width); _paint_scene(grid, shapes, assigned, placements)
        info = _analysis(grid)
        if not info["errors"] and info["scene_profile"] == profile: return grid
    raise RuntimeError(f"could not construct scene profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown: raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES: raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    if profile in PUBLIC_PROFILES or profile in ("equal_size_color_order", "varied_sizes", "tall_wide_alignment", "foreign_inside_crop", "hollow_object", "size_over_color", "cell_count_not_bbox_area"):
        count = 3
    elif profile == "same_color_components" or profile == "two_objects": count = 2
    elif profile == "four_objects": count = 4
    else: count = 5
    colors = tuple(context.draw_distinct_colors("scene_colors", n=count, exclude={0})); rng = context.draw_rng("scene")
    grid = _grid_from_public(profile, colors) if profile in PUBLIC_PROFILES else _general_grid(rng, difficulty, profile, colors)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}: raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid); errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown: errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES: errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested: errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    if not errors:
        ordered = sorted(info["components"], key=lambda component: (component["size"], component["color"]))
        if info["ordered"] != ordered: errors.append("component ordering is not (size, color)")
        expected_width = sum(component["c2"] - component["c1"] + 1 for component in ordered) + len(ordered) - 1
        if info["output_shape"][1] != expected_width: errors.append("gallery width or one-column gaps are wrong")
    return errors
