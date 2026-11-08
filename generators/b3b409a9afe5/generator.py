"""Generator for S24_M5 — count connected components by onion depth.

Every non-zero, non-9 cell belongs to a binary 4-connected mask.  Repeatedly
remove the mask boundary; the last occupied peel number is the component's
onion depth.  The answer is a 1x4 row containing the number of components with
depth 1, 2, 3, and 4.

The teaching distribution deliberately includes non-rectangular diamonds,
clipped squares, and thin polyominoes, plus repeated colors on disconnected
components.  This blocks the former shortcuts "ceil(min bbox side / 2)" and
"one color equals one component" while preserving the canonical rule.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b3b409a9afe5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e8b62e10ad85"

SUMMARY = (
    "Count 4-connected non-zero/non-9 components by maximum onion-peel depth "
    "1..4. Generated scenes mix solid and non-rectangular exact-depth shapes, "
    "randomize positions, and sometimes reuse colors across components."
)

INVARIANTS = [
    "background is 0 and color 9 is absent because the oracle ignores 9",
    "every component is monochrome, 4-connected, and has onion depth 1..4",
    "ordinary scenes contain at least two depth classes and a singleton class count",
    "ordinary scenes contain at least one non-rectangular component",
    "components are separated, while disconnected components may share a color",
]

HELPFUL_TEXTURES = ("mixed", "irregular")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "difficulty-skewed", "valid": "10..30"},
    "n_comps": {"type": "int", "default": "difficulty-skewed", "valid": "2..7"},
    "texture": {
        "type": "str",
        "default": "rng helpful",
        "valid": "mixed|irregular",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    ranges = {"grid_h": (8, 18), "grid_w": (10, 30), "n_comps": (2, 7)}
    for name, (lo, hi) in ranges.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES:
        raise ValueError("texture must be 'mixed' or 'irregular'")


def _components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(h):
        for col in range(w):
            if (row, col) in seen or grid[row][col] in (0, 9):
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    nxt = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] not in (0, 9)
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append({"cells": set(cells), "color": color})
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [cell[0] for cell in cells]
    cols = [cell[1] for cell in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _onion_depth(cells: Iterable[tuple[int, int]]) -> int:
    remaining = set(cells)
    depth = 0
    while remaining:
        depth += 1
        boundary = {
            (row, col)
            for row, col in remaining
            if any((row + dr, col + dc) not in remaining for dr, dc in _CARDINAL)
        }
        remaining.difference_update(boundary)
    return depth


def _is_solid(cells: set[tuple[int, int]]) -> bool:
    r0, c0, r1, c1 = _bbox(cells)
    return len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)


def semantic_observables(grid: list[list[int]]) -> dict:
    """Recover task-linked facts from returned cells only."""
    comps = _components(grid) if grid and grid[0] else []
    depths = [_onion_depth(comp["cells"]) for comp in comps]
    solid_flags = [_is_solid(comp["cells"]) for comp in comps]
    colors = [comp["color"] for comp in comps]
    counts = [depths.count(depth) for depth in range(1, 5)]
    if len(comps) == 1:
        texture = "single_component"
    elif depths and set(depths) == {1}:
        texture = "all_thin"
    elif depths and len(set(depths)) == 1:
        texture = "all_same_class"
    elif comps and all(not value for value in solid_flags):
        texture = "irregular"
    elif comps and any(solid_flags) and any(not value for value in solid_flags):
        texture = "mixed"
    else:
        texture = "solid_only"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_comps": len(comps),
        "texture": texture,
        "depths": depths,
        "depth_counts": counts,
        "solid_components": sum(solid_flags),
        "irregular_components": len(solid_flags) - sum(solid_flags),
        "component_colors": colors,
        "distinct_component_colors": len(set(colors)),
        "repeated_color": len(set(colors)) < len(colors),
    }


def observe_overrides(grid: list[list[int]]) -> dict:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python test mirror; Racket remains output authority."""
    depths = [_onion_depth(comp["cells"]) for comp in _components(grid)]
    return [[depths.count(depth) for depth in range(1, 5)]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete ordinary teaching grammar, not only its palette."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid value"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    h = len(grid)
    if not 8 <= h <= 18 or not 10 <= width <= 31:
        errors.append(f"dimensions {h}x{width} outside 8..18 by 10..31 (31 is canonical-only)")
    if any(value == 9 for row in grid for value in row):
        errors.append("color 9 is forbidden because the oracle ignores it")

    comps = _components(grid)
    if not 2 <= len(comps) <= 7:
        errors.append(f"expected 2..7 components; found {len(comps)}")
    for index, comp in enumerate(comps):
        component_colors = {grid[row][col] for row, col in comp["cells"]}
        if len(component_colors) != 1:
            errors.append(f"component {index} is not monochrome")

    depths = [_onion_depth(comp["cells"]) for comp in comps]
    if any(depth not in (1, 2, 3, 4) for depth in depths):
        errors.append(f"component depths must lie in 1..4; found {depths}")
    if len(set(depths)) < 2:
        errors.append("at least two onion-depth classes must be represented")
    counts = Counter(depths)
    if depths and 1 not in counts.values():
        errors.append("at least one represented depth class must occur exactly once")
    if comps and all(_is_solid(comp["cells"]) for comp in comps):
        errors.append("at least one component must be non-rectangular")
    colors = {comp["color"] for comp in comps}
    if len(colors) < 2:
        errors.append("at least two component colors are required")
    return errors


def _normalize(shape: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    shape = tuple(shape)
    r0 = min(row for row, _ in shape)
    c0 = min(col for _, col in shape)
    return frozenset((row - r0, col - c0) for row, col in shape)


def _rotate(shape: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    shape = _normalize(shape)
    max_row = max(row for row, _ in shape)
    return _normalize((col, max_row - row) for row, col in shape)


def _oriented(shape, turns: int):
    result = _normalize(shape)
    for _ in range(turns % 4):
        result = _rotate(result)
    return result


def _solid_shape(depth: int, rng, *, compact: bool = False) -> frozenset[tuple[int, int]]:
    if compact and depth == 1:
        height, width = rng.choice(((1, 1), (1, 2), (2, 1)))
        return frozenset((row, col) for row in range(height) for col in range(width))
    min_side = 2 * depth - 1 + rng.randint(0, 1)
    other_side = min_side + rng.randint(0, 2)
    if rng.random() < 0.5:
        height, width = min_side, other_side
    else:
        height, width = other_side, min_side
    return frozenset((row, col) for row in range(height) for col in range(width))


def _irregular_shape(depth: int, rng, *, compact: bool = False) -> frozenset[tuple[int, int]]:
    if depth == 1:
        options = (
            {(0, 0), (1, 0), (1, 1)},
            {(0, 0), (0, 1), (1, 1), (1, 2)},
            {(0, 0), (0, 1), (0, 2), (1, 1)},
            {(0, 0), (1, 0), (2, 0), (2, 1)},
            # A one-cell-wide bent path whose 5x5 bounding box would
            # misleadingly suggest depth 3 under the old rectangle shortcut.
            {(0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
             (3, 2), (3, 3), (3, 4), (4, 4)},
        )
        return _oriented(rng.choice(options), rng.randrange(4))

    side = 2 * depth - 1
    center = depth - 1
    roll = rng.random()
    if not compact and roll < 0.60:
        # Start with an exact-depth diamond and attach two thin orthogonal
        # tails.  The tails enlarge BOTH bbox dimensions without surrounding
        # the protected center, so onion depth stays d while
        # ceil(min(bbox_side)/2) becomes wrong.
        radius = depth - 1
        tail = 2
        shape = {
            (row, col)
            for row in range(-radius, radius + 1)
            for col in range(-radius, radius + 1)
            if abs(row) + abs(col) <= radius
        }
        shape.update((-radius - step, 0) for step in range(1, tail + 1))
        shape.update((0, -radius - step) for step in range(1, tail + 1))
    elif roll < 0.82:
        shape = {
            (row, col)
            for row in range(side)
            for col in range(side)
            if abs(row - center) + abs(col - center) <= depth - 1
        }
    else:
        shape = {(row, col) for row in range(side) for col in range(side)}
        shape.difference_update({(0, 0), (0, side - 1), (side - 1, 0), (side - 1, side - 1)})
    shape = _oriented(shape, rng.randrange(4))
    assert _onion_depth(shape) == depth and not _is_solid(set(shape))
    return shape


def _shape_dims(shape) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _can_place(grid, shape, row0: int, col0: int) -> bool:
    h, w = len(grid), len(grid[0])
    placed = {(row0 + row, col0 + col) for row, col in shape}
    if any(not (0 <= row < h and 0 <= col < w) for row, col in placed):
        return False
    halo = set(placed)
    for row, col in placed:
        halo.update((row + dr, col + dc) for dr, dc in _CARDINAL)
    return all(
        not (0 <= row < h and 0 <= col < w) or grid[row][col] == 0
        for row, col in halo
    )


def _place_shapes(h: int, w: int, specs: list[tuple[frozenset, int]], rng):
    # Large shapes first makes the greedy randomized packing stable.
    ordered = sorted(specs, key=lambda item: (-len(item[0]), -max(_shape_dims(item[0]))))
    for _ in range(16):
        grid = full_grid(h, w, 0)
        success = True
        for base_shape, color in ordered:
            orientations = list({_oriented(base_shape, turns) for turns in range(4)})
            rng.shuffle(orientations)
            candidates = []
            for shape in orientations:
                sh, sw = _shape_dims(shape)
                for row0 in range(h - sh + 1):
                    for col0 in range(w - sw + 1):
                        candidates.append((shape, row0, col0))
            rng.shuffle(candidates)
            chosen = next(
                ((shape, row0, col0) for shape, row0, col0 in candidates
                 if _can_place(grid, shape, row0, col0)),
                None,
            )
            if chosen is None:
                success = False
                break
            shape, row0, col0 = chosen
            for row, col in shape:
                grid[row0 + row][col0 + col] = color
        if success:
            return grid
    return None


def _choose_classes(n: int, difficulty, max_depth: int, rng) -> list[int]:
    ceiling = {
        "easy": min(2, max_depth),
        "medium": min(3, max_depth),
        "hard": min(4, max_depth),
    }.get(difficulty, min(4, max_depth))
    ceiling = max(2, ceiling)
    available = list(range(1, ceiling + 1))
    k = rng.randint(2, min(len(available), n))
    selected = rng.sample(available, k)
    protected = rng.choice(selected)
    classes = list(selected)
    allocation_targets = [value for value in selected if value != protected] or selected
    while len(classes) < n:
        classes.append(rng.choice(allocation_targets))
    rng.shuffle(classes)
    return classes


def _styles(texture: str, n: int, rng) -> list[str]:
    if texture == "irregular":
        return ["irregular"] * n
    styles = ["solid", "irregular"]
    styles.extend(rng.choice(("solid", "irregular")) for _ in range(n - 2))
    rng.shuffle(styles)
    return styles


def _colors(n: int, rng, *, canonical_profile: bool) -> list[int]:
    if canonical_profile:
        colors = [2, 3, 4, 5]
        rng.shuffle(colors)
        return colors
    palette_size = n if rng.random() < 0.45 else rng.randint(2, min(n, 5))
    palette = rng.sample(list(range(1, 9)), palette_size)
    colors = list(palette)
    while len(colors) < n:
        colors.append(rng.choice(palette))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    canonical_profile = (
        sample_index % 5 == 0
        and not any(name in overrides for name in ("grid_h", "grid_w", "n_comps"))
    )
    if canonical_profile:
        n = ctx.draw_int("n_comps", 4, 4)
        h = ctx.draw_int("grid_h", 13, 13)
        w = ctx.draw_int("grid_w", 30, 30)
    else:
        n = ctx.draw_int_diff("n_comps", 2, 7)
        h_lo = 12 if n >= 6 and "grid_h" not in overrides else 8
        w_lo = 18 if n >= 6 and "grid_w" not in overrides else 10
        h = ctx.draw_int_diff("grid_h", h_lo, 18)
        w = ctx.draw_int_diff("grid_w", w_lo, 30)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    max_depth = min(4, (min(h, w) + 1) // 2)
    dense_layout = h * w <= 16 * n
    for attempt in range(72):
        if canonical_profile:
            classes = [1, 2, 3, 4]
            if texture == "mixed":
                styles = ["solid", "solid", "irregular", "irregular"]
            else:
                styles = ["irregular"] * 4
        else:
            # At the extreme small-grid/high-count boundary, use a compact but
            # still semantically rich profile rather than spending time trying
            # geometries that cannot pack.  The depth-2 singleton preserves the
            # count-by-onion-depth lesson while the remaining thin components
            # exercise connectivity and repeated-color cases.
            if dense_layout:
                classes = [2] + [1] * (n - 1)
                rng.shuffle(classes)
            else:
                local_ceiling = max(2, max_depth - attempt // 24)
                classes = _choose_classes(n, difficulty, local_ceiling, rng)
            styles = _styles(texture, n, rng)
        colors = _colors(n, rng, canonical_profile=canonical_profile)
        specs = []
        for depth, style, color in zip(classes, styles, colors):
            shape = (_solid_shape(depth, rng, compact=dense_layout) if style == "solid"
                     else _irregular_shape(depth, rng, compact=dense_layout))
            specs.append((shape, color))
        grid = _place_shapes(h, w, specs, rng)
        if grid is None:
            continue
        if self_check(grid):
            continue
        if observe_overrides(grid) != {
            "grid_h": h,
            "grid_w": w,
            "n_comps": n,
            "texture": texture,
        }:
            continue
        return grid

    raise ValueError(
        "incompatible grid dimensions, component count, and texture; "
        "no exact lawful placement exists"
    )
