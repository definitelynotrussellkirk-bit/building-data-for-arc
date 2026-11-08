"""Generator for 95be702ec4db — rotational equivalence matrix.

Hollow color-9 frames contain single-color shapes.  Frames are ordered by
column; output cell (r,c) is cyan exactly when the two inner shapes are equal
up to quarter-turn rotation, ignoring color and empty margin.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "95be702ec4db"
VERSION = "3.3.0"
TASK_ID = GENERATOR_ID
RULE_HASH = "4810d55a18e8"
SUMMARY = (
    "A gallery of three to five separated hollow color-9 frames. Each contains "
    "one connected single-color shape, and the output is the cyan pairwise "
    "rotation-equivalence matrix over frames ordered from left to right."
)

INVARIANTS = [
    "background is 0",
    "3 to 5 separated hollow square color-9 frames are ordered by column",
    "each frame contains one connected nonzero, non-9, single-color shape",
    "ordinary examples contain at least two equivalence classes and one repeated class",
]

DEGENERATE_TEXTURES = ("all_same_family", "all_distinct_families", "empty_interiors")
TEXTURES = ("standard", *DEGENERATE_TEXTURES)
AXES = {
    "grid_h": {"type": "int", "default": "rng 8..9", "valid": "8..9"},
    "grid_w": {"type": "int", "default": "6*n_frames", "valid": "18..30 and >=6*n_frames"},
    "n_frames": {"type": "int", "default": "difficulty-aware 3..5", "valid": "3..5"},
    "texture": {"type": "str", "default": "standard", "valid": "|".join(TEXTURES)},
}
_ALLOWED_OVERRIDES = frozenset(AXES)
_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))

_SHAPE_FAMILIES = [
    [
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 1), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1)],
    ],
    [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
    ],
    [[(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]],
    [
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 0)],
    ],
]


def _strict_axis(ctx, label: str, default_lo: int, default_hi: int, global_lo: int, global_hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _texture(overrides: dict) -> str:
    value = overrides.get("texture", "standard")
    if type(value) is not str or value not in TEXTURES:
        raise ValueError(f"texture must be one of {TEXTURES}")
    return value


def _draw_frame(grid, top, left, size=5):
    for c in range(left, left + size):
        grid[top][c] = 9
        grid[top + size - 1][c] = 9
    for r in range(top, top + size):
        grid[r][left] = 9
        grid[r][left + size - 1] = 9


def _paint_shape(grid, top, left, shape, color):
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _partition_labels(count, rng):
    for _ in range(100):
        classes = rng.randint(2, min(4, count - 1))
        labels = [rng.randrange(classes) for _ in range(count)]
        used = sorted(set(labels))
        if len(used) >= 2 and max(labels.count(value) for value in used) >= 2:
            remap = {value: index for index, value in enumerate(used)}
            return [remap[value] for value in labels]
    return ([0, 0] + list(range(1, count - 1)))[:count]


def _frame_starts(width: int, count: int, rng) -> list[int]:
    minimum = 5 * count + (count - 1)
    extra = width - minimum
    if extra < 1:
        raise ValueError(f"grid_w must be at least {minimum + 1} for {count} frames")
    gaps = [0] * (count + 1)
    for _ in range(extra):
        gaps[rng.randrange(count + 1)] += 1
    starts = []
    cursor = gaps[0]
    for index in range(count):
        starts.append(cursor)
        cursor += 5
        if index < count - 1:
            cursor += 1 + gaps[index + 1]
    return starts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    texture = _texture(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        count = _strict_axis(ctx, "n_frames", 3, 3, 3, 5)
    elif difficulty == "hard":
        count = _strict_axis(ctx, "n_frames", 5, 5, 3, 5)
    else:
        count = _strict_axis(ctx, "n_frames", 3, 5, 3, 5)
    height = _strict_axis(ctx, "grid_h", 8, 9, 8, 9)
    if overrides.get("grid_w") is not None:
        width = ctx.draw_int_strict("grid_w", 18, 30)
    else:
        width = 6 * count
    if width < 6 * count:
        raise ValueError(f"grid_w must be at least {6 * count} for n_frames={count}")

    rng = ctx.draw_rng("layout")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, height, width, count, rng)

    starts = _frame_starts(width, count, rng)
    top = height - 5
    grid = full_grid(height, width, 0)
    for left in starts:
        _draw_frame(grid, top, left)

    colors = rng.sample(range(1, 9), count)
    labels = _partition_labels(count, rng)
    selected_families = rng.sample(range(len(_SHAPE_FAMILIES)), max(labels) + 1)
    for left, color, label in zip(starts, colors, labels):
        shape = rng.choice(_SHAPE_FAMILIES[selected_families[label]])
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        inner_top = top + 1 + rng.randint(0, 3 - shape_h)
        inner_left = left + 1 + rng.randint(0, 3 - shape_w)
        _paint_shape(grid, inner_top, inner_left, shape, color)
    errors = self_check(grid)
    if errors:
        raise ValueError("generated invalid frame gallery: " + "; ".join(errors))
    return grid


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def _frame_facts(grid) -> list[dict]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
    facts = []
    for component in _components(cells):
        r1 = min(r for r, _ in component)
        c1 = min(c for _, c in component)
        r2 = max(r for r, _ in component)
        c2 = max(c for _, c in component)
        inner = {(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)}
        shape = {(r, c) for r, c in inner if grid[r][c] not in (0, 9)}
        facts.append({"bbox": (r1, c1, r2, c2), "border_cells": component,
                      "inner_cells": inner, "shape_cells": shape})
    return sorted(facts, key=lambda fact: (fact["bbox"][1], fact["bbox"][0]))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid is not rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integers in 0..9"]
    height = len(grid)
    errors = []
    if not 8 <= height <= 9 or not 18 <= width <= 30:
        errors.append(f"expected 8..9 by 18..30 gallery; got {height}x{width}")
    facts = _frame_facts(grid)
    if not 3 <= len(facts) <= 5:
        errors.append(f"expected 3 to 5 color-9 frames; got {len(facts)}")
    for index, fact in enumerate(facts):
        r1, c1, r2, c2 = fact["bbox"]
        frame_h, frame_w = r2 - r1 + 1, c2 - c1 + 1
        if frame_h != frame_w or frame_h not in (5, 6):
            errors.append(f"frame {index} must be a 5x5 or 6x6 square")
            continue
        expected_border = {
            (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if fact["border_cells"] != expected_border:
            errors.append(f"frame {index} has a missing or extra border cell")
        if any(grid[r][c] == 9 for r, c in fact["inner_cells"]):
            errors.append(f"frame {index} contains color 9 inside its border")
        shape = fact["shape_cells"]
        colors = {grid[r][c] for r, c in shape}
        if not shape:
            errors.append(f"frame {index} has an empty interior")
        elif len(colors) != 1:
            errors.append(f"frame {index} must contain exactly one shape color")
        elif len(_components(shape)) != 1:
            errors.append(f"frame {index} shape must be four-connected")
    return errors


def _draw_from_degenerate(name, height, width, count, rng):
    count = min(count, width // 6)
    starts = _frame_starts(width, count, rng)
    top = height - 5
    grid = full_grid(height, width, 0)
    for left in starts:
        _draw_frame(grid, top, left)
    if name == "empty_interiors":
        return grid
    if name == "all_same_family":
        family_ids = [0] * count
    else:
        family_ids = list(range(count))
    for index, (left, family_id) in enumerate(zip(starts, family_ids)):
        family = _SHAPE_FAMILIES[family_id % len(_SHAPE_FAMILIES)]
        _paint_shape(grid, top + 1, left + 1, family[index % len(family)], 1 + index)
    return grid
