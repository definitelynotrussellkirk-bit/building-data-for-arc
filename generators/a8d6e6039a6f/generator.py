"""Semantic generator for ARC task a8d6e6039a6f.

A free two-color template is stamped into each hollow gray frame.  A nearby
key selects the transform: 1 keeps the template, 2 rotates clockwise, 3
flips left/right, and 4 flips up/down.  The output contains only the frames
and their centered transformed stamps; the loose template and keys vanish.
"""
from __future__ import annotations

import itertools

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "a8d6e6039a6f"
TASK_ID = "a8d6e6039a6f"
VERSION = "4.0.0"
RULE_HASH = "9921e422d6f8"
SUMMARY = (
    "Find the free multicolor template and every hollow gray frame. Read the "
    "single nearby key for each frame, transform the template by 1=identity, "
    "2=rotate clockwise, 3=flip left/right, or 4=flip up/down, and center the "
    "transformed stamp inside that frame. Remove the source template and keys."
)
INVARIANTS = [
    "the background is black (0) and every destination is a hollow gray frame",
    "each frame has exactly one nearby key in 1,2,3,4",
    "three-frame scenes use three distinct keys and four-frame scenes use all four",
    "the loose template is one connected two-color object using colors 6 through 9",
    "every transformed template fits completely inside its destination interior",
    "the template and key cells are absent from the output",
    "scene_code reconstructs every frame, key, template, palette, and placement fact",
]


def _rotate_cw(pattern):
    return tuple(tuple(row) for row in zip(*pattern[::-1]))


def _flip_lr(pattern):
    return tuple(tuple(reversed(row)) for row in pattern)


def _flip_ud(pattern):
    return tuple(reversed(pattern))


def _variants(pattern):
    out = []
    current = pattern
    for _ in range(4):
        for candidate in (current, _flip_lr(current)):
            if candidate not in out:
                out.append(candidate)
        current = _rotate_cw(current)
    return tuple(out)


def _canonical_labels(pattern):
    """Name the first occupied color role 1, eliminating color-swap aliases."""
    first = next(value for row in pattern for value in row if value)
    if first == 1:
        return pattern
    return tuple(
        tuple(0 if value == 0 else 3 - value for value in row)
        for row in pattern
    )


def _connected_pattern(pattern):
    cells = {
        (row, col)
        for row, values in enumerate(pattern)
        for col, value in enumerate(values)
        if value
    }
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row + 1, col), (row - 1, col),
            (row, col + 1), (row, col - 1),
        ):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


PUBLIC_PATTERN = ((1, 0), (1, 2))
PUBLIC_PATTERNS = tuple(dict.fromkeys(
    _canonical_labels(pattern) for pattern in _variants(PUBLIC_PATTERN)
))
PUBLIC_PATTERN_COUNT = len(PUBLIC_PATTERNS)


def _make_patterns():
    patterns = list(PUBLIC_PATTERNS)
    seen = set(patterns)
    for height, width in ((2, 2), (2, 3), (3, 2), (3, 3)):
        area = height * width
        for occupied_mask in range(1, 1 << area):
            occupied = [index for index in range(area) if occupied_mask >> index & 1]
            if not 3 <= len(occupied) <= 8:
                continue
            rows = {index // width for index in occupied}
            cols = {index % width for index in occupied}
            if len(rows) != height or len(cols) != width:
                continue
            binary = tuple(
                tuple(int(row * width + col in occupied) for col in range(width))
                for row in range(height)
            )
            if not _connected_pattern(binary):
                continue
            for label_mask in range(1, (1 << len(occupied)) - 1):
                if label_mask & 1:
                    continue
                labels = {
                    index: 2 if label_mask >> offset & 1 else 1
                    for offset, index in enumerate(occupied)
                }
                pattern = tuple(
                    tuple(labels.get(row * width + col, 0) for col in range(width))
                    for row in range(height)
                )
                if pattern in seen:
                    continue
                seen.add(pattern)
                patterns.append(pattern)
                if len(patterns) == 256:
                    return tuple(patterns)
    raise RuntimeError("could not enumerate 256 connected two-color templates")


PATTERNS = _make_patterns()
PATTERN_TO_INDEX = {pattern: index for index, pattern in enumerate(PATTERNS)}
PATTERN_COUNT = len(PATTERNS)
assert PUBLIC_PATTERN_COUNT == 8
assert PATTERN_COUNT == 256

PALETTES = tuple(itertools.permutations((6, 7, 8, 9), 2))
PALETTE_TO_INDEX = {palette: index for index, palette in enumerate(PALETTES)}
PALETTE_COUNT = len(PALETTES)
KEY_ORDERS = {
    3: tuple(itertools.permutations((1, 2, 3, 4), 3)),
    4: tuple(itertools.permutations((1, 2, 3, 4), 4)),
}
KEY_TO_INDEX = {
    count: {keys: index for index, keys in enumerate(orders)}
    for count, orders in KEY_ORDERS.items()
}
KEY_ORDER_COUNT = 24
KEY_SPOT_COUNT = 8
PLACEMENT_COUNT = 4


def _border_cells(frame):
    top, bottom, left, right = frame
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _key_spots(frame):
    top, bottom, left, right = frame
    return (
        (top - 1, left), (top - 1, right),
        (bottom + 1, left), (bottom + 1, right),
        (top, left - 1), (top, right + 1),
        (bottom, left - 1), (bottom, right + 1),
    )


def _layout_valid(height, width, frames):
    borders = [_border_cells(frame) for frame in frames]
    if any(
        top < 1 or left < 1 or bottom >= height - 1 or right >= width - 1
        for top, bottom, left, right in frames
    ):
        return False
    for index, border in enumerate(borders):
        expanded = {
            neighbor
            for row, col in border
            for neighbor in (
                (row, col), (row + 1, col), (row - 1, col),
                (row, col + 1), (row, col - 1),
            )
        }
        if any(expanded & borders[other] for other in range(index)):
            return False
    return bool(_valid_spot_indexes(height, width, frames))


def _valid_spot_indexes(height, width, frames):
    borders = [_border_cells(frame) for frame in frames]
    union = set().union(*borders)
    valid = []
    for spot_index in range(KEY_SPOT_COUNT):
        keys = [_key_spots(frame)[spot_index] for frame in frames]
        if len(set(keys)) != len(keys):
            continue
        if any(
            not (0 <= row < height and 0 <= col < width) or (row, col) in union
            for row, col in keys
        ):
            continue
        key_set = set(keys)
        if any(
            len(key_set & set(_key_spots(frame))) != 1
            for frame in frames
        ):
            continue
        valid.append(spot_index)
    return tuple(valid)


PUBLIC_LAYOUTS = (
    (12, 18, ((1, 4, 8, 11), (1, 4, 13, 16), (7, 10, 10, 13)),
     ((1, 1), (4, 1), (7, 3), (1, 4))),
    (14, 20, ((1, 4, 10, 13), (1, 4, 15, 18),
              (8, 11, 10, 13), (8, 11, 15, 18)),
     ((2, 2), (1, 1), (6, 2), (10, 1))),
    (13, 20, ((1, 4, 10, 13), (1, 4, 15, 18), (7, 10, 12, 15)),
     ((8, 1), (1, 1), (4, 2), (9, 4))),
    (15, 21, ((1, 4, 11, 14), (1, 4, 16, 19),
              (9, 12, 11, 14), (9, 12, 16, 19)),
     ((3, 1), (1, 3), (7, 1), (11, 3))),
)


def _make_layouts():
    layouts = list(PUBLIC_LAYOUTS)
    seen = {(height, width, frames) for height, width, frames, _ in layouts}
    candidates = []
    for height, width in ((14, 21), (15, 21), (15, 22), (16, 21), (16, 22)):
        for size in (4, 5):
            for top in (1, 2):
                bottom = height - size - 1
                if bottom <= top + size:
                    continue
                for shift in (0, 1):
                    left = width - 12 - shift
                    right = width - size - 1
                    boxes = (
                        (top, top + size - 1, left, left + size - 1),
                        (top, top + size - 1, right, right + size - 1),
                        (bottom, bottom + size - 1, left, left + size - 1),
                        (bottom, bottom + size - 1, right, right + size - 1),
                    )
                    for omitted in (None, 3, 2, 1, 0):
                        frames = tuple(
                            box for index, box in enumerate(boxes) if index != omitted
                        )
                        identity = (height, width, frames)
                        if identity in seen or not _layout_valid(height, width, frames):
                            continue
                        placements = (
                            (1, 1), (1, 4), (height - 4, 1), (height - 4, 4)
                        )
                        candidates.append((height, width, frames, placements))
                        seen.add(identity)
    # Alternate three- and four-frame candidates so each branch has broad
    # dimensional and geometric support.
    by_count = {
        count: [layout for layout in candidates if len(layout[2]) == count]
        for count in (3, 4)
    }
    for offset in range(14):
        for count in (3, 4):
            layouts.append(by_count[count][offset])
    if len(layouts) != 32:
        raise RuntimeError("expected 32 frame layouts")
    return tuple(layouts)


LAYOUTS = _make_layouts()
LAYOUT_TO_INDEX = {
    (height, width, frames): index
    for index, (height, width, frames, _) in enumerate(LAYOUTS)
}
LAYOUT_COUNT = len(LAYOUTS)
LAYOUT_SPOTS = tuple(
    _valid_spot_indexes(height, width, frames)
    for height, width, frames, _ in LAYOUTS
)
GENERAL_LAYOUTS = {
    count: tuple(
        index for index, layout in enumerate(LAYOUTS[4:], start=4)
        if len(layout[2]) == count
    )
    for count in (3, 4)
}
assert tuple(map(len, GENERAL_LAYOUTS.values())) == (14, 14)
assert all(_layout_valid(height, width, frames) for height, width, frames, _ in LAYOUTS)

LAYOUT_PATTERN_COUNTS = tuple(
    PUBLIC_PATTERN_COUNT if index < len(PUBLIC_LAYOUTS) else PATTERN_COUNT
    for index in range(LAYOUT_COUNT)
)
LAYOUT_BLOCK_SIZES = tuple(
    KEY_ORDER_COUNT * len(LAYOUT_SPOTS[index]) * pattern_count
    * PALETTE_COUNT * PLACEMENT_COUNT
    for index, pattern_count in enumerate(LAYOUT_PATTERN_COUNTS)
)
LAYOUT_OFFSETS = []
_offset = 0
for _block_size in LAYOUT_BLOCK_SIZES:
    LAYOUT_OFFSETS.append(_offset)
    _offset += _block_size
SCENE_COUNT = _offset

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": (
            "deterministic schedule over full frame layout, key order and "
            "location, two-color template, palette, and loose placement"
        ),
        "valid": "0..61489151",
        "doc": (
            "Exact variable-radix index. Public 4x4-frame layouts use the "
            "eight fitting L templates; generalized layouts use all 256 templates."
        ),
    }
}


def _encode_scene(
    layout_index, key_index, spot_index,
    pattern_index, palette_index, placement_index,
):
    pattern_count = LAYOUT_PATTERN_COUNTS[layout_index]
    if not 0 <= pattern_index < pattern_count:
        raise ValueError("template does not fit the selected layout family")
    try:
        spot_slot = LAYOUT_SPOTS[layout_index].index(spot_index)
    except ValueError as exc:
        raise ValueError("key location is ambiguous for the selected layout") from exc
    value = key_index
    value = value * len(LAYOUT_SPOTS[layout_index]) + spot_slot
    value = value * pattern_count + pattern_index
    value = value * PALETTE_COUNT + palette_index
    value = value * PLACEMENT_COUNT + placement_index
    return LAYOUT_OFFSETS[layout_index] + value


def _decode_scene(scene_code):
    if isinstance(scene_code, bool) or not isinstance(scene_code, int):
        raise TypeError("scene_code must be a literal integer")
    if not 0 <= scene_code < SCENE_COUNT:
        raise ValueError(f"scene_code must be in 0..{SCENE_COUNT - 1}")
    layout_index = max(
        index for index, offset in enumerate(LAYOUT_OFFSETS)
        if offset <= scene_code
    )
    value = scene_code - LAYOUT_OFFSETS[layout_index]
    value, placement_index = divmod(value, PLACEMENT_COUNT)
    value, palette_index = divmod(value, PALETTE_COUNT)
    pattern_count = LAYOUT_PATTERN_COUNTS[layout_index]
    value, pattern_index = divmod(value, pattern_count)
    key_index, spot_slot = divmod(value, len(LAYOUT_SPOTS[layout_index]))
    spot_index = LAYOUT_SPOTS[layout_index][spot_slot]
    return (
        layout_index, key_index, spot_index,
        pattern_index, palette_index, placement_index,
    )


def _paint_pattern(grid, top, left, pattern, palette):
    for row, values in enumerate(pattern):
        for col, label in enumerate(values):
            if label:
                grid[top + row][left + col] = palette[label - 1]


def _make_grid(layout, keys, spot_index, pattern, palette, placement_index):
    height, width, frames, placements = layout
    grid = [[0] * width for _ in range(height)]
    for frame, key in zip(frames, keys):
        for row, col in _border_cells(frame):
            grid[row][col] = 5
        key_row, key_col = _key_spots(frame)[spot_index]
        grid[key_row][key_col] = key
    top, left = placements[placement_index]
    _paint_pattern(grid, top, left, pattern, palette)
    return grid


def _grid_from_code(scene_code):
    decoded = _decode_scene(scene_code)
    layout_index, key_index, spot_index, pattern_index, palette_index, placement_index = decoded
    layout = LAYOUTS[layout_index]
    keys = KEY_ORDERS[len(layout[2])][key_index]
    return _make_grid(
        layout, keys, spot_index, PATTERNS[pattern_index],
        PALETTES[palette_index], placement_index,
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


def _components(grid, predicate=None, same_color=True):
    height, width = len(grid), len(grid[0])
    predicate = predicate or (lambda value: value != 0)
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or not predicate(grid[row][col]):
                continue
            color = grid[row][col]
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
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if neighbor in seen or not predicate(grid[nr][nc]):
                        continue
                    if same_color and grid[nr][nc] != color:
                        continue
                    seen.add(neighbor)
                    stack.append(neighbor)
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _rect_frame(component):
    return (
        component["color"] == 5
        and set(component["cells"]) == _border_cells(_bbox(component["cells"]))
    )


def _template_crop(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value >= 6
    ]
    if not cells:
        return None
    top, bottom, left, right = _bbox(cells)
    return tuple(
        tuple(grid[row][col] for col in range(left, right + 1))
        for row in range(top, bottom + 1)
    )


def _transform(pattern, key):
    if key == 2:
        return _rotate_cw(pattern)
    if key == 3:
        return _flip_lr(pattern)
    if key == 4:
        return _flip_ud(pattern)
    return pattern


def _paste_centered(grid, frame, pattern):
    top, bottom, left, right = frame
    interior_height = bottom - top - 1
    interior_width = right - left - 1
    paste_top = top + 1 + max(0, (interior_height - len(pattern)) // 2)
    paste_left = left + 1 + max(0, (interior_width - len(pattern[0])) // 2)
    for row, values in enumerate(pattern):
        for col, value in enumerate(values):
            rr, cc = paste_top + row, paste_left + col
            if value and 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                grid[rr][cc] = value


def rule_mirror(grid):
    """Input-pure Python mirror of the frame-key transform-stamp rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    frames = tuple(sorted(
        _bbox(component["cells"])
        for component in _components(grid)
        if _rect_frame(component)
    ))
    template = _template_crop(grid)
    if not frames or template is None:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for frame in frames:
        for row, col in _border_cells(frame):
            output[row][col] = 5
    for frame in frames:
        candidates = [
            grid[row][col]
            for row, col in _key_spots(frame)
            if 0 <= row < height and 0 <= col < width
            and 1 <= grid[row][col] <= 4
        ]
        key = min(candidates) if candidates else 1
        _paste_centered(output, frame, _transform(template, key))
    return output


def _pattern_from_grid(grid, cells, palette):
    top, bottom, left, right = _bbox(cells)
    color_to_label = {color: index + 1 for index, color in enumerate(palette)}
    return tuple(
        tuple(color_to_label.get(grid[row][col], 0) for col in range(left, right + 1))
        for row in range(top, bottom + 1)
    )


def _recover_scene(grid):
    height, width = len(grid), len(grid[0])
    frames = tuple(sorted(
        _bbox(component["cells"])
        for component in _components(grid)
        if _rect_frame(component)
    ))
    layout_index = LAYOUT_TO_INDEX.get((height, width, frames))
    if layout_index is None:
        return None
    layout = LAYOUTS[layout_index]
    key_candidates = []
    spot_indexes = []
    for frame in frames:
        candidates = [
            (index, grid[row][col])
            for index, (row, col) in enumerate(_key_spots(frame))
            if 0 <= row < height and 0 <= col < width
            and 1 <= grid[row][col] <= 4
        ]
        if len(candidates) != 1:
            return None
        spot, key = candidates[0]
        spot_indexes.append(spot)
        key_candidates.append(key)
    if len(set(spot_indexes)) != 1:
        return None
    keys = tuple(key_candidates)
    key_index = KEY_TO_INDEX[len(frames)].get(keys)
    if key_index is None:
        return None
    template_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value >= 6
    ]
    if not template_cells:
        return None
    template_components = _components(grid, lambda value: value >= 6, same_color=False)
    if len(template_components) != 1:
        return None
    palette = tuple(sorted({grid[row][col] for row, col in template_cells}))
    if len(palette) != 2:
        return None
    # Preserve the ordered semantic roles: label 1 is the first occupied cell
    # in reading order, label 2 is the other color.
    first_color = grid[min(template_cells)[0]][min(template_cells)[1]]
    ordered_palette = (first_color, next(color for color in palette if color != first_color))
    pattern = _pattern_from_grid(grid, template_cells, ordered_palette)
    pattern_index = PATTERN_TO_INDEX.get(pattern)
    palette_index = PALETTE_TO_INDEX.get(ordered_palette)
    if pattern_index is None or palette_index is None:
        return None
    top, _, left, _ = _bbox(template_cells)
    try:
        placement_index = layout[3].index((top, left))
    except ValueError:
        return None
    if pattern_index >= LAYOUT_PATTERN_COUNTS[layout_index]:
        return None
    scene_code = _encode_scene(
        layout_index, key_index, spot_indexes[0],
        pattern_index, palette_index, placement_index,
    )
    return (
        scene_code, layout_index, keys, spot_indexes[0],
        pattern_index, ordered_palette, placement_index,
    )


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    recovered = _recover_scene(grid)
    if recovered is None:
        errors.append("scene does not match a declared frame/key/template profile")
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    scene_code, layout_index, keys, spot_index, pattern_index, palette, placement = recovered
    expected = _grid_from_code(scene_code)
    if tuple(map(tuple, grid)) != tuple(map(tuple, expected)):
        errors.append("returned cells do not exactly reconstruct from scene_code")
    output = rule_mirror(grid)
    return {
        "errors": errors,
        "scene_code": scene_code,
        "facts": {
            "layout_index": layout_index,
            "dimensions": (len(grid), len(grid[0])),
            "frame_count": len(LAYOUTS[layout_index][2]),
            "keys": keys,
            "key_spot": spot_index,
            "pattern_index": pattern_index,
            "palette": palette,
            "placement": placement,
            "public_layout": layout_index < len(PUBLIC_LAYOUTS),
            "public_morphology": pattern_index < PUBLIC_PATTERN_COUNT,
        },
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Observational validation of the complete returned scene grammar."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_code": analysis["scene_code"]}


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    if (
        facts["public_layout"] and facts["public_morphology"]
        and facts["key_spot"] == 0
    ):
        return f"public_layout_{facts['layout_index']}"
    return "generalized"


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    return (
        f"frames_{facts['frame_count']}_size_"
        f"{facts['dimensions'][0]}x{facts['dimensions'][1]}"
    )


def _zigzag(value):
    return value if value >= 0 else -2 * value - 1


_BAND_INDEX = {None: 0, "easy": 1, "medium": 2, "hard": 3}


def _pattern_pool(difficulty):
    if difficulty == "easy":
        return tuple(range(PUBLIC_PATTERN_COUNT, 88))
    if difficulty == "medium":
        return tuple(range(88, 168))
    if difficulty == "hard":
        return tuple(range(168, PATTERN_COUNT))
    return tuple(range(PUBLIC_PATTERN_COUNT, PATTERN_COUNT))


def _natural_scene_code(seed, sample_index, difficulty):
    band = _BAND_INDEX[difficulty]
    raw = (
        _zigzag(seed)
        + 1_000_003 * _zigzag(sample_index)
        + 10_000_019 * band
    )
    remainder = raw % 5
    if remainder == 0:
        serial = raw // 5
        pattern_index = serial % PUBLIC_PATTERN_COUNT
        serial //= PUBLIC_PATTERN_COUNT
        layout_index = serial % len(PUBLIC_LAYOUTS)
        serial //= len(PUBLIC_LAYOUTS)
        palette_index = serial % PALETTE_COUNT
        serial //= PALETTE_COUNT
        key_index = serial % KEY_ORDER_COUNT
        serial //= KEY_ORDER_COUNT
        placement_index = serial % PLACEMENT_COUNT
        return _encode_scene(
            layout_index, key_index, 0,
            pattern_index, palette_index, placement_index,
        )
    serial = (raw // 5) * 4 + remainder - 1
    pool = _pattern_pool(difficulty)
    pattern_index = pool[serial % len(pool)]
    serial //= len(pool)
    palette_index = serial % PALETTE_COUNT
    serial //= PALETTE_COUNT
    if difficulty == "easy":
        layouts = GENERAL_LAYOUTS[3]
    elif difficulty == "hard":
        layouts = GENERAL_LAYOUTS[4]
    else:
        layouts = tuple(range(len(PUBLIC_LAYOUTS), LAYOUT_COUNT))
    layout_index = layouts[serial % len(layouts)]
    serial //= len(layouts)
    key_index = serial % KEY_ORDER_COUNT
    spots = LAYOUT_SPOTS[layout_index]
    spot_index = spots[(raw // 7) % len(spots)]
    placement_index = (raw // 11) % PLACEMENT_COUNT
    return _encode_scene(
        layout_index, key_index, spot_index,
        pattern_index, palette_index, placement_index,
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_INDEX:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    requested_code = overrides.get("scene_code")
    if requested_code is not None:
        _decode_scene(requested_code)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested_code is None:
        scheduled = _natural_scene_code(seed, sample_index, difficulty)
        scene_code = ctx.draw_int("scene_code", scheduled, scheduled)
    else:
        scene_code = ctx.draw_int("scene_code", 0, SCENE_COUNT - 1)
    return _grid_from_code(scene_code)
