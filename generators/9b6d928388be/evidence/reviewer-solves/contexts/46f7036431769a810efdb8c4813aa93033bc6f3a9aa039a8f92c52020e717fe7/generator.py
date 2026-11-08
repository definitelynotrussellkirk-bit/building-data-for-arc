"""Semantic generator for ARC task 9b6d928388be.

Three hollow gray frames carry singleton keys immediately above their top
midpoints.  Key colors 1, 2, and 3 request a loose object with respectively
zero, one, and two enclosed holes.  The selected objects are removed from
their source positions and centered on the keyed frame interiors; objects
wider or taller than an interior may overwrite part of the gray border.
"""
from __future__ import annotations

import itertools

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9b6d928388be"
TASK_ID = "9b6d928388be"
VERSION = "4.0.0"
RULE_HASH = "71c56654a6ea"
SUMMARY = (
    "Find the three hollow gray frames and read each singleton key above its "
    "top midpoint.  Match key 1/2/3 to the loose object with 0/1/2 enclosed "
    "holes, erase all loose source objects, and center each matched crop on "
    "the corresponding frame interior without recoloring it."
)
INVARIANTS = [
    "the background is black (0) and the three hollow frames are gray (5)",
    "each frame has exactly one midpoint key and the keys are a permutation of 1,2,3",
    "there are exactly three loose connected objects with distinct colors",
    "the loose objects have the unique hole counts 0,1,2",
    "the one-hole object is never gray, so it cannot masquerade as a gray frame",
    "all frame, key, object-shape, color, and placement facts reconstruct from scene_code",
    "difficulty changes object density/complexity, never the matching rule",
]


def _pattern_key(pattern):
    return tuple(tuple(int(value) for value in row) for row in pattern)


def _connected(pattern):
    points = {
        (row, col)
        for row, values in enumerate(pattern)
        for col, value in enumerate(values)
        if value
    }
    if not points:
        return False
    seen = {next(iter(points))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row + 1, col), (row - 1, col),
            (row, col + 1), (row, col - 1),
        ):
            if neighbor in points and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == points


def _pattern_holes(pattern):
    height, width = len(pattern), len(pattern[0])
    free = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if not pattern[row][col]
    }
    seen = set()
    holes = 0
    for start in free:
        if start in seen:
            continue
        seen.add(start)
        stack = [start]
        touches_edge = False
        while stack:
            row, col = stack.pop()
            if row in (0, height - 1) or col in (0, width - 1):
                touches_edge = True
            for neighbor in (
                (row + 1, col), (row - 1, col),
                (row, col + 1), (row, col - 1),
            ):
                if neighbor in free and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        if not touches_edge:
            holes += 1
    return holes


PUBLIC_ZERO_PATTERNS = (
    ((1, 1), (1, 1)),
    ((1, 1, 1), (1, 1, 1), (1, 1, 1)),
)
PUBLIC_ONE_PATTERN = ((1, 1, 1), (1, 0, 1), (1, 1, 1))
PUBLIC_TWO_PATTERN = (
    (1, 1, 1, 1, 1),
    (1, 0, 1, 0, 1),
    (1, 1, 1, 1, 1),
)


def _enumerate_patterns(hole_count, dimensions, limit, public):
    """Enumerate small, connected, bbox-pinned topology templates."""
    patterns = list(public)
    seen = set(patterns)
    for height, width in dimensions:
        for mask in range(1, 1 << (height * width)):
            pattern = tuple(
                tuple((mask >> (row * width + col)) & 1 for col in range(width))
                for row in range(height)
            )
            if pattern in seen:
                continue
            if not all(any(row) for row in pattern):
                continue
            if not all(any(pattern[row][col] for row in range(height))
                       for col in range(width)):
                continue
            if not _connected(pattern) or _pattern_holes(pattern) != hole_count:
                continue
            seen.add(pattern)
            patterns.append(pattern)
            if len(patterns) >= limit:
                return tuple(patterns)
    return tuple(patterns)


_ZERO_CANDIDATES = _enumerate_patterns(
    0,
    ((2, 2), (2, 3), (3, 2), (3, 3), (3, 4), (4, 3)),
    260,
    PUBLIC_ZERO_PATTERNS,
)
ZERO_PATTERNS = _ZERO_CANDIDATES[:256]


def _rect_outline_pattern(pattern):
    height, width = len(pattern), len(pattern[0])
    occupied = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if pattern[row][col]
    }
    border = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    return occupied == border


# A gray 2x2/2x3 solid is itself a complete bbox border and would therefore
# be detected as a frame by the executable rule.  Index gray zero-hole shapes
# through an equal-sized safe bank; its first entry is the public gray 3x3.
GRAY_ZERO_PATTERNS = tuple(
    [PUBLIC_ZERO_PATTERNS[1]]
    + [
        pattern for pattern in _ZERO_CANDIDATES
        if pattern != PUBLIC_ZERO_PATTERNS[1] and not _rect_outline_pattern(pattern)
    ][:255]
)
ONE_PATTERNS = _enumerate_patterns(
    1,
    ((3, 3), (3, 4), (4, 3), (4, 4)),
    256,
    (PUBLIC_ONE_PATTERN,),
)
TWO_PATTERNS = _enumerate_patterns(
    2,
    ((3, 5), (5, 3), (4, 4)),
    78,
    (PUBLIC_TWO_PATTERN,),
)
PATTERN_BANKS = (ZERO_PATTERNS, ONE_PATTERNS, TWO_PATTERNS)
PATTERN_TO_INDEX = tuple(
    {pattern: index for index, pattern in enumerate(bank)}
    for bank in PATTERN_BANKS
)
PATTERN_COUNTS = tuple(len(bank) for bank in PATTERN_BANKS)

assert PATTERN_COUNTS == (256, 256, 78)
assert len(GRAY_ZERO_PATTERNS) == PATTERN_COUNTS[0]
assert all(not _rect_outline_pattern(pattern) for pattern in GRAY_ZERO_PATTERNS)

# Object colors are distinct and disjoint from the key colors.  Gray is
# lawful for the zero- or two-hole loose object (as in two public cases), but
# excluding it from the one-hole role prevents a rectangular ring from being
# detected as a fourth gray frame.
PALETTES = tuple(
    palette
    for palette in itertools.permutations((4, 5, 6, 7, 8, 9), 3)
    if palette[1] != 5
)
PALETTE_TO_INDEX = {palette: index for index, palette in enumerate(PALETTES)}
KEY_PERMUTATIONS = tuple(itertools.permutations((1, 2, 3)))
KEY_TO_INDEX = {keys: index for index, keys in enumerate(KEY_PERMUTATIONS)}


def _border_cells(bbox):
    top, bottom, left, right = bbox
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _layout_valid(height, width, frames):
    borders = [_border_cells(frame) for frame in frames]
    if any(
        top < 1 or left < 0 or bottom >= height or right >= width
        for top, bottom, left, right in frames
    ):
        return False
    if any(borders[i] & borders[j] for i in range(3) for j in range(i)):
        return False
    for i in range(3):
        expanded = {
            neighbor
            for row, col in borders[i]
            for neighbor in ((row + 1, col), (row - 1, col),
                             (row, col + 1), (row, col - 1))
        }
        if any(expanded & borders[j] for j in range(i)):
            return False
    keys = [(top - 1, (left + right) // 2) for top, _, left, right in frames]
    if len(set(keys)) != 3 or any(key in set().union(*borders) for key in keys):
        return False
    return True


# (height, width, sorted frame bboxes, doubled object centers by hole role,
# family index).  The first four entries reconstruct the three train inputs
# and one held-out input exactly when combined with PUBLIC_SCENES below.
_PUBLIC_LAYOUTS = (
    (15, 24, ((2, 6, 12, 16), (4, 8, 19, 23), (8, 12, 12, 16)),
     ((5, 3), (16, 4), (24, 6)), 0),
    (16, 24, ((2, 6, 11, 15), (5, 9, 19, 23), (8, 12, 12, 16)),
     ((26, 4), (4, 4), (16, 6)), 1),
    (15, 25, ((2, 6, 14, 18), (5, 9, 21, 24), (8, 12, 14, 18)),
     ((17, 3), (24, 14), (6, 6)), 2),
    (15, 24, ((2, 6, 12, 16), (3, 7, 19, 23), (8, 12, 12, 16)),
     ((4, 4), (16, 4), (22, 16)), 3),
)


def _make_layouts():
    layouts = list(_PUBLIC_LAYOUTS)
    seen = {(h, w, frames) for h, w, frames, _, _ in layouts}
    role_orders = tuple(itertools.permutations(range(3)))
    dimensions = ((15, 24), (16, 24), (15, 25), (16, 25))
    candidates = {dims: [] for dims in dimensions}
    for height, width in dimensions:
        bottom_center = 24 if height == 15 else 26
        for left_col in range(11, 15):
            for right_col in range(18, 22):
                for top_row in range(1, 4):
                    for right_row in range(2, 7):
                        for bottom_row in range(8, 11):
                            for right_width in (4, 5):
                                frames = tuple(sorted((
                                    (top_row, top_row + 4, left_col, left_col + 4),
                                    (right_row, right_row + 4,
                                     right_col, right_col + right_width - 1),
                                    (bottom_row, bottom_row + 4,
                                     left_col, left_col + 4),
                                )))
                                identity = (height, width, frames)
                                if identity in seen or not _layout_valid(
                                    height, width, frames
                                ):
                                    continue
                                candidates[(height, width)].append(frames)
                                seen.add(identity)
    # Round-robin dimensions rather than exhausting one shape first.  With
    # the four public profiles included, the final catalog is exactly balanced
    # at 32 layouts for each of the four 15/16 x 24/25 dimensions.
    offsets = {dims: 0 for dims in dimensions}
    while len(layouts) < 128:
        for height, width in dimensions:
            if sum(1 for layout in layouts if layout[:2] == (height, width)) >= 32:
                continue
            offset = offsets[(height, width)]
            if offset >= len(candidates[(height, width)]):
                raise RuntimeError(f"too few layouts for {(height, width)}")
            frames = candidates[(height, width)][offset]
            offsets[(height, width)] += 1
            index = len(layouts)
            bottom_center = 24 if height == 15 else 26
            row_centers = (4, 14, bottom_center)
            order = role_orders[index % len(role_orders)]
            col_centers = (4, 14, 4 if index % 2 else 14)
            centers = [None, None, None]
            for band, role in enumerate(order):
                centers[role] = (row_centers[band], col_centers[band])
            family = ((index - 4) // 2) % 4
            layouts.append(
                (height, width, frames, tuple(centers), family)
            )
            if len(layouts) == 128:
                break
    if all(sum(1 for layout in layouts if layout[:2] == dims) == 32
           for dims in dimensions):
        return tuple(layouts)
    raise RuntimeError("could not construct 128 lawful frame layouts")


LAYOUTS = _make_layouts()
LAYOUT_TO_INDEX = {
    (height, width, frames): index
    for index, (height, width, frames, _, _) in enumerate(LAYOUTS)
}
LAYOUT_COUNT = len(LAYOUTS)
PALETTE_COUNT = len(PALETTES)
KEY_COUNT = len(KEY_PERMUTATIONS)
SCENE_COUNT = (
    LAYOUT_COUNT * KEY_COUNT * PALETTE_COUNT
    * PATTERN_COUNTS[0] * PATTERN_COUNTS[1] * PATTERN_COUNTS[2]
)

assert LAYOUT_COUNT == 128
assert PALETTE_COUNT == 100
assert KEY_COUNT == 6

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": (
            "deterministic schedule over linked frame layout, key permutation, "
            "ordered loose-object palette, and exact 0/1/2-hole shapes"
        ),
        "valid": "0..392586854399",
        "doc": (
            "Exact mixed-radix index over 128 layouts, all six key orders, "
            "100 lawful ordered palettes, and the three topology banks."
        ),
    }
}


def _encode_scene(
    layout_index, key_index, palette_index,
    zero_index, one_index, two_index,
):
    code = layout_index
    code = code * KEY_COUNT + key_index
    code = code * PALETTE_COUNT + palette_index
    code = code * PATTERN_COUNTS[0] + zero_index
    code = code * PATTERN_COUNTS[1] + one_index
    return code * PATTERN_COUNTS[2] + two_index


def _decode_scene(scene_code):
    scene_code, two_index = divmod(scene_code, PATTERN_COUNTS[2])
    scene_code, one_index = divmod(scene_code, PATTERN_COUNTS[1])
    scene_code, zero_index = divmod(scene_code, PATTERN_COUNTS[0])
    scene_code, palette_index = divmod(scene_code, PALETTE_COUNT)
    layout_index, key_index = divmod(scene_code, KEY_COUNT)
    return (
        layout_index, key_index, palette_index,
        zero_index, one_index, two_index,
    )


def _top_left(center, pattern):
    center_row2, center_col2 = center
    height, width = len(pattern), len(pattern[0])
    return (
        (center_row2 - (height - 1)) // 2,
        (center_col2 - (width - 1)) // 2,
    )


def _paint_pattern(grid, top, left, pattern, color):
    for row, values in enumerate(pattern):
        for col, occupied in enumerate(values):
            if occupied:
                grid[top + row][left + col] = color


def _make_grid(layout, keys, palette, patterns):
    height, width, frames, centers, _ = layout
    grid = [[0] * width for _ in range(height)]
    for frame, key in zip(frames, keys):
        for row, col in _border_cells(frame):
            grid[row][col] = 5
        top, _, left, right = frame
        grid[top - 1][(left + right) // 2] = key
    for role, (pattern, color) in enumerate(zip(patterns, palette)):
        top, left = _top_left(centers[role], pattern)
        _paint_pattern(grid, top, left, pattern, color)
    return grid


def _grid_from_code(scene_code):
    decoded = _decode_scene(scene_code)
    layout_index, key_index, palette_index = decoded[:3]
    pattern_indexes = decoded[3:]
    zero_bank = GRAY_ZERO_PATTERNS if PALETTES[palette_index][0] == 5 else ZERO_PATTERNS
    patterns = (
        zero_bank[pattern_indexes[0]],
        ONE_PATTERNS[pattern_indexes[1]],
        TWO_PATTERNS[pattern_indexes[2]],
    )
    return _make_grid(
        LAYOUTS[layout_index],
        KEY_PERMUTATIONS[key_index],
        PALETTES[palette_index],
        patterns,
    )


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["input must contain at least one row"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["input must contain at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC colors from zero through nine"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for neighbor in (
                    (cr + 1, cc), (cr - 1, cc),
                    (cr, cc + 1), (cr, cc - 1),
                ):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and neighbor not in seen and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _rect_frame(component):
    if component["color"] != 5:
        return False
    bbox = _bbox(component["cells"])
    return set(component["cells"]) == _border_cells(bbox)


def _component_pattern(component):
    top, bottom, left, right = _bbox(component["cells"])
    cells = set(component["cells"])
    return tuple(
        tuple(int((row, col) in cells) for col in range(left, right + 1))
        for row in range(top, bottom + 1)
    )


def _floor_half(value):
    return value // 2


def _erase_frames_and_keys(grid, frames):
    temp = [list(row) for row in grid]
    for frame in frames:
        for row, col in _border_cells(frame):
            temp[row][col] = 0
        top, _, left, right = frame
        temp[top - 1][(left + right) // 2] = 0
    return temp


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical keyed-hole assignment rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    frames = sorted(
        (_bbox(component["cells"]) for component in _components(grid)
         if _rect_frame(component)),
    )
    temp = _erase_frames_and_keys(grid, frames)
    loose = _components(temp)
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for frame in frames:
        for row, col in _border_cells(frame):
            output[row][col] = 5
    for frame in frames:
        top, bottom, left, right = frame
        key_row, key_col = top - 1, (left + right) // 2
        key = grid[key_row][key_col] if 0 <= key_row < height else 0
        if 0 <= key_row < height:
            output[key_row][key_col] = key
        candidates = [
            component for component in loose
            if _pattern_holes(_component_pattern(component)) == key - 1
        ]
        if not candidates:
            continue
        chosen = max(candidates, key=lambda component: len(component["cells"]))
        pattern = _component_pattern(chosen)
        crop_height, crop_width = len(pattern), len(pattern[0])
        interior_height = bottom - top - 1
        interior_width = right - left - 1
        paste_top = top + 1 + _floor_half(interior_height - crop_height)
        paste_left = left + 1 + _floor_half(interior_width - crop_width)
        color = chosen["color"]
        for row, values in enumerate(pattern):
            for col, occupied in enumerate(values):
                if occupied:
                    rr, cc = paste_top + row, paste_left + col
                    if 0 <= rr < height and 0 <= cc < width:
                        output[rr][cc] = color
    return output


def _recover_scene(grid):
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    frames = tuple(sorted(
        _bbox(component["cells"])
        for component in components if _rect_frame(component)
    ))
    layout_index = LAYOUT_TO_INDEX.get((height, width, frames))
    if layout_index is None:
        return None
    layout = LAYOUTS[layout_index]
    keys = tuple(
        grid[top - 1][(left + right) // 2]
        for top, _, left, right in frames
    )
    key_index = KEY_TO_INDEX.get(keys)
    if key_index is None:
        return None
    temp = _erase_frames_and_keys(grid, frames)
    loose = _components(temp)
    if len(loose) != 3:
        return None
    by_role = {}
    for component in loose:
        pattern = _component_pattern(component)
        role = _pattern_holes(pattern)
        if role not in (0, 1, 2) or role in by_role:
            return None
        expected_top_left = _top_left(layout[3][role], pattern)
        top, _, left, _ = _bbox(component["cells"])
        if (top, left) != expected_top_left:
            return None
        by_role[role] = (component["color"], pattern)
    if set(by_role) != {0, 1, 2}:
        return None
    palette = tuple(by_role[role][0] for role in range(3))
    palette_index = PALETTE_TO_INDEX.get(palette)
    if palette_index is None:
        return None
    zero_map = (
        {pattern: index for index, pattern in enumerate(GRAY_ZERO_PATTERNS)}
        if palette[0] == 5 else PATTERN_TO_INDEX[0]
    )
    pattern_maps = (zero_map, PATTERN_TO_INDEX[1], PATTERN_TO_INDEX[2])
    pattern_indexes = tuple(
        pattern_maps[role].get(by_role[role][1]) for role in range(3)
    )
    if any(index is None for index in pattern_indexes):
        return None
    scene_code = _encode_scene(
        layout_index, key_index, palette_index, *pattern_indexes
    )
    return scene_code, layout_index, keys, palette, pattern_indexes


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    recovered = _recover_scene(grid)
    if recovered is None:
        errors.append(
            "scene does not match a declared three-frame/key/topology profile"
        )
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    scene_code, layout_index, keys, palette, pattern_indexes = recovered
    expected = _grid_from_code(scene_code)
    if tuple(map(tuple, grid)) != tuple(map(tuple, expected)):
        errors.append("returned cells do not exactly reconstruct from scene_code")
    output = None
    try:
        output = rule_mirror(grid)
    except (IndexError, ValueError) as exc:
        errors.append(f"keyed-hole assignment failed: {exc}")
    height, width, frames, _, catalog_group = LAYOUTS[layout_index]
    facts = {
        "height": height,
        "width": width,
        "layout_index": layout_index,
        "layout_family": f"size_{height}x{width}",
        "catalog_group": catalog_group,
        "frames": frames,
        "keys": keys,
        "palette": palette,
        "pattern_indexes": pattern_indexes,
        "hole_counts": (0, 1, 2),
        "component_count": len(_components(grid)),
        "public_profile": _CANONICAL_EXACT.get(tuple(map(tuple, grid))),
    }
    return {"errors": errors, "scene_code": scene_code, "facts": facts, "output": output}


def canonical_profile_signature(grid):
    try:
        return _CANONICAL_EXACT.get(tuple(map(tuple, grid)))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return analysis["facts"]["layout_family"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {} if analysis["errors"] else {"scene_code": analysis["scene_code"]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


PUBLIC_SCENES = (
    (0, (1, 3, 2), (4, 6, 8), (0, 0, 0)),
    (1, (2, 1, 3), (4, 7, 9), (1, 0, 0)),
    (2, (3, 2, 1), (6, 4, 5), (0, 0, 0)),
    (3, (1, 3, 2), (5, 7, 9), (0, 0, 0)),
)
PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(4))


def _public_code(index):
    layout_index, keys, palette, patterns = PUBLIC_SCENES[index]
    return _encode_scene(
        layout_index,
        KEY_TO_INDEX[keys],
        PALETTE_TO_INDEX[palette],
        *patterns,
    )


def _public_grid(index):
    return _grid_from_code(_public_code(index))


_CANONICAL_EXACT = {
    tuple(map(tuple, _public_grid(index))): PUBLIC_PROFILES[index]
    for index in range(4)
}


def _complexity(pattern):
    area = len(pattern) * len(pattern[0])
    cells = sum(map(sum, pattern))
    return area - cells, area, -cells, pattern


def _partition_pool(bank):
    ordered = sorted(range(len(bank)), key=lambda index: _complexity(bank[index]))
    size = len(ordered)
    first = max(1, size // 3)
    second = max(first + 1, 2 * size // 3)
    return {
        "easy": tuple(ordered[:first]),
        "medium": tuple(ordered[first:second]),
        "hard": tuple(ordered[second:]),
    }


_PARTITIONS = tuple(_partition_pool(bank) for bank in PATTERN_BANKS)
PATTERN_POOLS = {
    None: tuple(tuple(range(len(bank))) for bank in PATTERN_BANKS),
    "easy": tuple(partition["easy"] for partition in _PARTITIONS),
    "medium": tuple(partition["medium"] for partition in _PARTITIONS),
    "hard": tuple(partition["hard"] for partition in _PARTITIONS),
}
_BAND_INDEX = {None: 0, "easy": 1, "medium": 2, "hard": 3}


def _zigzag(value):
    return 2 * value if value >= 0 else -2 * value - 1


def _pair_index(first, second):
    first, second = _zigzag(first), _zigzag(second)
    total = first + second
    return total * (total + 1) // 2 + second


def _mix64(value):
    mask = (1 << 64) - 1
    value &= mask
    value = (value + 0x9E3779B97F4A7C15) & mask
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
    return value ^ (value >> 31)


def _natural_scene_code(seed, sample_index, difficulty):
    band = _BAND_INDEX[difficulty]
    token = _pair_index(seed, sample_index)
    layout_index = _mix64(token + 11 + 101 * band) % LAYOUT_COUNT
    key_index = _mix64(token + 23 + 103 * band) % KEY_COUNT
    palette_index = _mix64(token + 37 + 107 * band) % PALETTE_COUNT
    pools = PATTERN_POOLS[difficulty]
    pattern_indexes = tuple(
        pool[_mix64(token + 53 + 29 * role + 109 * band) % len(pool)]
        for role, pool in enumerate(pools)
    )
    return _encode_scene(
        layout_index, key_index, palette_index, *pattern_indexes
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_INDEX:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    requested_code = overrides.get("scene_code")
    if requested_code is not None:
        if isinstance(requested_code, bool) or not isinstance(requested_code, int):
            raise TypeError("scene_code must be a literal integer")
        if not 0 <= requested_code < SCENE_COUNT:
            raise ValueError(f"scene_code must be in 0..{SCENE_COUNT - 1}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested_code is not None:
        scene_code = ctx.draw_int("scene_code", 0, SCENE_COUNT - 1)
    else:
        scheduled = _natural_scene_code(seed, sample_index, difficulty)
        scene_code = ctx.draw_int("scene_code", scheduled, scheduled)
    return _grid_from_code(scene_code)
