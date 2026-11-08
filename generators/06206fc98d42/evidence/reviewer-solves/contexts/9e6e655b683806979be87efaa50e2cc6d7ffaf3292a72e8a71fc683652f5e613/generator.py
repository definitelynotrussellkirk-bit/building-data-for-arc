"""Generator for arc_puzzle_bank_nineteenth21:E133.

Rule: replace every same-color 4-connected object by one same-colored cell at
its bounding-box center, using floor division for even-sized boxes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "06206fc98d42"
VERSION = "3.1.0"
TASK_ID = "06206fc98d42"
RULE_HASH = "9f601f00a9b1"

SUMMARY = (
    "A 0-background grid contains 2-4 well-separated, same-color objects. "
    "The output clears every object and keeps one cell in its color at "
    "floor((r1+r2)/2), floor((c1+c2)/2). Helpful branches include hollow "
    "objects whose center was background, repeated object colors, and even "
    "bounding-box dimensions. Placement is exact: the realized object count "
    "always equals the keyed draw or explicit override."
)

# Shortcut controls:
# - hollow_center refutes "keep one occupied cell" because a new center cell is
#   painted where the input was background;
# - even_size_objects refutes nearest/ceiling rounding;
# - repeat_color refutes one-output-per-color and modal-color shortcuts.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "normal draws contain exactly 2-4 same-color 4-connected objects",
    "objects are the same-color 4-connected components used by the oracle",
    "all bbox centers are pairwise distinct",
]

DEGENERATE_TEXTURES = (
    "no_objects",
    "single_cell_objects",
    "even_size_objects",
)
HELPFUL_TEXTURES = ("plain", "hollow_center", "repeat_color")
_ALL_TEXTURES = HELPFUL_TEXTURES + DEGENERATE_TEXTURES

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 5..14", "valid": "5..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware 5..15", "valid": "5..16"},
    "objects": {"type": "int", "default": "difficulty-aware 2..4", "valid": "2..4"},
    "texture": {
        "type": "str",
        "default": "rng helpful",
        "valid": (
            "plain|hollow_center|repeat_color|no_objects|"
            "single_cell_objects|even_size_objects"
        ),
        "doc": (
            "hollow_center guarantees a center cell that was background; "
            "no_objects and single_cell_objects are explicit rule-hiding "
            "diagnostics and never occur on normal draws."
        ),
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BAND_RANGES = {
    None: ((5, 12), (6, 13)),
    "easy": ((5, 8), (5, 9)),
    "medium": ((6, 11), (6, 12)),
    "hard": ((9, 14), (9, 15)),
}


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _center(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return (r1 + r2) // 2, (c1 + c2) // 2


def _components(grid):
    """Return the same-color 4-connected objects used by the Racket oracle."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            color = grid[row0][col0]
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nr, nc = row + drow, col + dcol
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            box = _bbox(cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": box,
                    "center": ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2),
                }
            )
    return components


def _scene_analysis(grid):
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return [], ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return [], ["grid must be rectangular and non-empty"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        errors.append(f"grid shape outside ARC bounds: {len(grid)}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return [], errors + ["grid colors must be integers in 0..9"]

    components = _components(grid)
    centers = [obj["center"] for obj in components]
    if len(set(centers)) != len(centers):
        errors.append(f"bbox centers are not pairwise distinct: {centers}")
    return components, errors


def _meta_overrides(meta):
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return nested
    return meta


def self_check(grid, *, difficulty=None, meta=None):
    """Check the structural grammar and texture-specific teaching claims."""
    del difficulty
    components, errors = _scene_analysis(grid)
    if errors:
        return errors

    overrides = _meta_overrides(meta)
    texture = overrides.get("texture")
    requested_objects = overrides.get("objects")
    count = len(components)

    if texture == "no_objects":
        if count:
            errors.append(f"no_objects requires 0 objects, got {count}")
        return errors

    expected = int(requested_objects) if requested_objects is not None else None
    if expected is not None and count != expected:
        errors.append(f"expected exactly {expected} objects, got {count}")
    elif expected is None and not 2 <= count <= 4:
        errors.append(f"expected 2-4 objects, got {count}")

    sizes = [len(obj["cells"]) for obj in components]
    if texture == "single_cell_objects":
        if any(size != 1 for size in sizes):
            errors.append(f"single_cell_objects requires all sizes=1, got {sizes}")
        return errors

    if texture == "even_size_objects":
        bad = [
            obj["bbox"]
            for obj in components
            if len(obj["cells"]) != 4
            or obj["bbox"][2] - obj["bbox"][0] + 1 != 2
            or obj["bbox"][3] - obj["bbox"][1] + 1 != 2
        ]
        if bad:
            errors.append(f"even_size_objects requires solid 2x2 objects, bad bboxes={bad}")
        return errors

    if any(size < 3 for size in sizes):
        errors.append(f"normal objects must contain at least 3 cells, got sizes={sizes}")
    oversized = [
        obj["bbox"]
        for obj in components
        if obj["bbox"][2] - obj["bbox"][0] + 1 > 4
        or obj["bbox"][3] - obj["bbox"][1] + 1 > 4
    ]
    if oversized:
        errors.append(f"normal object bbox exceeds 4x4: {oversized}")

    colors = [obj["color"] for obj in components]
    if texture in {"plain", "hollow_center"} and len(set(colors)) != count:
        errors.append(f"{texture} requires distinct object colors, got {colors}")
    if texture == "repeat_color" and len(set(colors)) != 1:
        errors.append(f"repeat_color requires one shared color, got {colors}")
    if texture == "hollow_center" and not any(
        grid[row][col] == 0 for row, col in (obj["center"] for obj in components)
    ):
        errors.append("hollow_center requires an object whose bbox center is background")
    return errors


def observe_overrides(grid):
    components, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"objects": len(components)}


def rule_mirror(grid):
    """Python test mirror; the canonical Racket program remains the oracle."""
    components, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = full_grid(len(grid), len(grid[0]), 0)
    for obj in components:
        row, col = obj["center"]
        output[row][col] = obj["color"]
    return output


def _layout_options(height, width, target, min_box):
    if target == 0:
        return [(1, 1)]
    options = []
    for rows in range(1, target + 1):
        for cols in range(1, target + 1):
            slots = rows * cols
            if not target <= slots <= target + 1:
                continue
            need_h = rows * min_box + rows - 1
            need_w = cols * min_box + cols - 1
            if height >= need_h and width >= need_w:
                options.append((rows, cols))
    return options


def _validated_override(overrides, name):
    if name not in overrides or overrides[name] is None:
        return None
    value = int(overrides[name])
    if not 5 <= value <= 16:
        raise ValueError(f"{name} override {value} outside [5, 16]")
    return value


def _choose_canvas(ctx, target, min_box, difficulty, overrides):
    if difficulty not in _BAND_RANGES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    fixed_h = _validated_override(overrides, "grid_h")
    fixed_w = _validated_override(overrides, "grid_w")
    (h_lo, h_hi), (w_lo, w_hi) = _BAND_RANGES[difficulty]
    heights = [fixed_h] if fixed_h is not None else list(range(h_lo, h_hi + 1))
    widths = [fixed_w] if fixed_w is not None else list(range(w_lo, w_hi + 1))

    def candidates(hs, ws):
        return [
            (height, width)
            for height in hs
            for width in ws
            if _layout_options(height, width, target, min_box)
        ]

    feasible = candidates(heights, widths)
    if not feasible and not (fixed_h is not None and fixed_w is not None):
        heights = [fixed_h] if fixed_h is not None else list(range(5, 17))
        widths = [fixed_w] if fixed_w is not None else list(range(5, 17))
        feasible = candidates(heights, widths)
    if not feasible:
        raise ValueError(
            "incompatible grid/object/texture overrides: "
            f"grid_h={fixed_h!r}, grid_w={fixed_w!r}, objects={target}, "
            f"minimum object box={min_box}"
        )

    height, width = ctx.draw_rng("canvas").choice(feasible)
    # Fixed keyed draws retain exact provenance for the override/default gate.
    height = ctx.draw_int("grid_h", height, height)
    width = ctx.draw_int("grid_w", width, width)
    return height, width


def _partition(length, parts, rng):
    usable = length - (parts - 1)
    base, extra = divmod(usable, parts)
    sizes = [base + (index < extra) for index in range(parts)]
    rng.shuffle(sizes)
    spans = []
    start = 0
    for size in sizes:
        spans.append((start, start + size))
        start += size + 1
    return spans


def _slots(height, width, target, min_box, rng):
    rows, cols = rng.choice(_layout_options(height, width, target, min_box))
    row_spans = _partition(height, rows, rng)
    col_spans = _partition(width, cols, rng)
    slots = [
        (r0, r1, c0, c1)
        for r0, r1 in row_spans
        for c0, c1 in col_spans
    ]
    rng.shuffle(slots)
    return slots[:target]


def _ring(rng):
    """A 3x3 ring or C whose bbox center (1,1) is background."""
    cells = [(row, col) for row in range(3) for col in range(3) if (row, col) != (1, 1)]
    if rng.random() < 0.5:
        drop = rng.choice(((0, 1), (1, 0), (1, 2), (2, 1)))
        cells.remove(drop)
    return cells


def _grow(rng, size, max_h, max_w):
    start = (rng.randrange(max_h), rng.randrange(max_w))
    cells = {start}
    attempts = 0
    while len(cells) < size:
        attempts += 1
        if attempts > 2000:
            raise ValueError("could not grow a connected object")
        row, col = rng.choice(tuple(sorted(cells)))
        drow, dcol = rng.choice(_DIR4)
        nr, nc = row + drow, col + dcol
        if 0 <= nr < max_h and 0 <= nc < max_w:
            cells.add((nr, nc))
    min_r = min(row for row, _ in cells)
    min_c = min(col for _, col in cells)
    return sorted((row - min_r, col - min_c) for row, col in cells)


def _random_shape(rng, slot_h, slot_w, *, force_even):
    max_h = min(4, slot_h)
    max_w = min(4, slot_w)
    if force_even and max_h >= 2 and max_w >= 2:
        variants = (
            ((0, 0), (0, 1), (1, 0)),
            ((0, 0), (0, 1), (1, 1), (1, 2)),
            ((0, 0), (1, 0), (1, 1), (2, 1)),
        )
        legal = [
            list(shape)
            for shape in variants
            if max(row for row, _ in shape) < max_h
            and max(col for _, col in shape) < max_w
        ]
        if legal:
            return rng.choice(legal)
    max_cells = min(8, max_h * max_w)
    return _grow(rng, rng.randint(3, max_cells), max_h, max_w)


def _place_shape(grid, slot, shape, color, rng):
    r0, r1, c0, c1 = slot
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    top = rng.randint(r0, r1 - shape_h)
    left = rng.randint(c0, c1 - shape_w)
    for row, col in shape:
        grid[top + row][left + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if "texture" in overrides:
        texture = ctx.draw_choice("texture", _ALL_TEXTURES)
    else:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "hollow_center", "repeat_color")
        )

    if texture == "no_objects":
        if overrides.get("objects") is not None:
            raise ValueError("texture='no_objects' is incompatible with an objects override")
        target = 0
    elif overrides.get("objects") is not None:
        target = ctx.draw_int("objects", 2, 4)
    elif difficulty == "easy":
        target = ctx.draw_int("objects", 2, 2)
    elif difficulty == "hard":
        target = ctx.draw_int("objects", 3, 4)
    else:
        target = ctx.draw_int("objects", 2, 4)

    min_box = {
        "single_cell_objects": 1,
        "even_size_objects": 2,
    }.get(texture, 3)
    height, width = _choose_canvas(ctx, target, min_box, difficulty, overrides)
    grid = full_grid(height, width, 0)
    if texture == "no_objects":
        return grid

    rng = ctx.draw_rng("layout")
    slots = _slots(height, width, target, min_box, rng)
    if texture == "repeat_color":
        colors = [rng.choice(range(1, 10))] * target
    else:
        colors = rng.sample(range(1, 10), target)

    for index, (slot, color) in enumerate(zip(slots, colors)):
        r0, r1, c0, c1 = slot
        slot_h, slot_w = r1 - r0, c1 - c0
        if texture == "single_cell_objects":
            shape = [(0, 0)]
        elif texture == "even_size_objects":
            shape = [(0, 0), (0, 1), (1, 0), (1, 1)]
        elif texture == "hollow_center" and index == 0:
            shape = _ring(rng)
        else:
            shape = _random_shape(
                rng,
                slot_h,
                slot_w,
                force_even=index == 0 and rng.random() < 0.65,
            )
        _place_shape(grid, slot, shape, color, rng)

    messages = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"texture": texture, "objects": target}},
    )
    if messages:
        raise AssertionError("internal generator invariant failure: " + "; ".join(messages))
    return grid
