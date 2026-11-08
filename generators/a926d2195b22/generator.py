"""E98: recolor the row-major first smallest monochromatic component to 9.

Only inputs are sampled here. The selected canonical Racket program remains the
label authority. Python mirrors below exist for tests, semantic rivals, and
review diagnostics.

The ordinary four-example curriculum contains two repeated-color witnesses,
two tied-minimum witnesses, and two examples where a larger component precedes
the target in row-major order. Consequently, every three-of-four lesson refutes
the globally-rarest-color, all-minima, and first-component shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a926d2195b22"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "eb3b09c1bddc"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, find monochromatic four-connected components, "
    "rank them by cell count with row-major order as the tie break, and "
    "recolor only the first smallest component to maroon (9). Vary canonical "
    "dimensions, object count, connected shapes, positions, minimum size, "
    "minimum ties, repeated colors, and target position relative to larger objects."
)
INVARIANTS = [
    "rectangular literal-integer ARC grid with background 0 and no input 9",
    "three to five separated monochromatic four-connected components",
    "minimum component size 1..3, attained by one or two components",
    "row-major first minimum is the selected target when sizes tie",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile cycle", "valid": "8..13"},
    "grid_w": {"type": "int", "default": "canonical-profile cycle", "valid": "8..14"},
    "num_objects": {"type": "int", "default": "canonical-profile cycle", "valid": "3..5"},
    "smallest_size": {"type": "int", "default": "curriculum cycle", "valid": "1..3"},
    "minimum_count": {"type": "int", "default": "semantic cycle", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# These are explicit invalid fixtures. They are deliberately outside AXES and
# can never be mixed with ordinary overrides.
DEGENERATE_TEXTURES = ("only_one_object", "input_contains_9", "three_way_minimum")
HELPFUL_TEXTURES = ()

CANONICAL_PROFILES = (
    (9, 10, 4),
    (10, 10, 3),
    (8, 12, 4),
    (9, 11, 3),
    (10, 12, 4),
)
SEMANTIC_PROFILES = ("repeat_and_tie", "repeat_only", "tie_only", "plain")
_AXIS_LIMITS = {
    "grid_h": (8, 13),
    "grid_w": (8, 14),
    "num_objects": (3, 5),
    "smallest_size": (1, 3),
    "minimum_count": (1, 2),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Sliding semantic schedule; seed/difficulty alter layout, not coverage."""
    del seed, difficulty
    return SEMANTIC_PROFILES[sample_index % len(SEMANTIC_PROFILES)]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise TypeError(f"unknown override axes: {', '.join(unknown)}")
    for name, (lo, hi) in _AXIS_LIMITS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be a literal integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _scheduled_int(ctx, label, scheduled, overrides):
    lo, hi = _AXIS_LIMITS[label]
    bounds = (lo, hi) if overrides.get(label) is not None else (scheduled, scheduled)
    return ctx.draw_int_strict(label, *bounds)


def _negative(texture):
    grid = full_grid(8, 8, 0)
    if texture == "only_one_object":
        grid[2][2] = grid[2][3] = grid[3][2] = 4
    elif texture == "input_contains_9":
        grid[1][1] = 9
        grid[3][3:5] = [4, 4]
        grid[6][5:8] = [7, 7, 7]
    elif texture == "three_way_minimum":
        grid[0][0] = 2
        grid[0][7] = 3
        grid[7][0] = 4
        grid[6][5:8] = [7, 7, 7]
    else:  # defensive: callers validate the name first
        raise ValueError(f"unknown negative fixture: {texture!r}")
    return grid


def _split_with_gutters(rng, total, parts, minimum):
    """Return disjoint intervals separated by exactly one background cell."""
    usable = total - (parts - 1)
    if usable < parts * minimum:
        raise ValueError(f"cannot split length {total} into {parts} regions of {minimum}")
    lengths = [minimum] * parts
    for _ in range(usable - parts * minimum):
        lengths[rng.randrange(parts)] += 1
    intervals = []
    start = 0
    for length in lengths:
        intervals.append((start, length))
        start += length + 1
    return intervals


def _regions(rng, height, width, num_objects):
    if num_objects <= 4:
        rows = _split_with_gutters(rng, height, 2, 3)
        cols = _split_with_gutters(rng, width, 2, 3)
    else:
        rows = _split_with_gutters(rng, height, 2, 2)
        cols = _split_with_gutters(rng, width, 3, 2)
    slots = [(r, c, rh, cw) for r, rh in rows for c, cw in cols]
    rng.shuffle(slots)
    # Keep the random subset, then assign object roles in row-major region order.
    # This makes positional teaching witnesses exact without constraining shapes.
    return sorted(slots[:num_objects])


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return sorted((r - top, c - left) for r, c in cells)


def _polyomino(rng, size, height, width):
    """Grow one connected shape inside a finite box without rejection loops."""
    if size > height * width:
        raise ValueError("component size exceeds its construction region")
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < size:
        frontier = {
            (nr, nc)
            for r, c in cells
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0))
            for nr, nc in ((r + dr, c + dc),)
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in cells
        }
        if not frontier:
            raise AssertionError("connected growth exhausted a non-full region")
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def _place_shape(rng, shape, region, *, anchor_top_left=False):
    r0, c0, rh, rw = region
    ph = max(r for r, _ in shape) + 1
    pw = max(c for _, c in shape) + 1
    top = r0 if anchor_top_left else r0 + rng.randrange(rh - ph + 1)
    left = c0 if anchor_top_left else c0 + rng.randrange(rw - pw + 1)
    return sorted((top + r, left + c) for r, c in shape)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                "texture supports only explicit negative fixtures: "
                + ", ".join(DEGENERATE_TEXTURES)
            )
        if any(overrides.get(name) is not None for name in AXES):
            exc = ValueError("negative fixtures cannot be combined with ordinary axes")
            exc.incompatible_axes = tuple(
                name for name in AXES if overrides.get(name) is not None
            )
            raise exc
        return _negative(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_h, profile_w, profile_n = CANONICAL_PROFILES[sample_index % len(CANONICAL_PROFILES)]
    semantic = schedule_profile(seed, sample_index, difficulty)
    scheduled_small = (1, 2, 3, 2)[(sample_index // len(CANONICAL_PROFILES)) % 4]
    scheduled_min_count = 2 if semantic in ("repeat_and_tie", "tie_only") else 1

    height = _scheduled_int(ctx, "grid_h", profile_h, overrides)
    width = _scheduled_int(ctx, "grid_w", profile_w, overrides)
    num_objects = _scheduled_int(ctx, "num_objects", profile_n, overrides)
    smallest_size = _scheduled_int(ctx, "smallest_size", scheduled_small, overrides)
    minimum_count = _scheduled_int(ctx, "minimum_count", scheduled_min_count, overrides)

    rng = ctx.draw_rng(f"layout:{difficulty or 'none'}")
    regions = _regions(rng, height, width, num_objects)

    larger_sizes = []
    for _ in range(num_objects - minimum_count):
        larger_sizes.append(rng.randint(smallest_size + 1, 4))
    sizes = [smallest_size] * minimum_count + larger_sizes
    rng.shuffle(sizes)

    # Two profiles deliberately put a larger object before the selected minimum;
    # the other two put a minimum first. Every three-of-four lesson therefore
    # contains a counterexample to "always recolor the first/topmost object".
    target_late = semantic in ("repeat_and_tie", "repeat_only")
    first_is_minimum = sizes[0] == smallest_size
    if target_late == first_is_minimum:
        wanted = (
            next(index for index, size in enumerate(sizes) if size > smallest_size)
            if target_late
            else next(index for index, size in enumerate(sizes) if size == smallest_size)
        )
        sizes[0], sizes[wanted] = sizes[wanted], sizes[0]

    placed = []
    for index, (size, region) in enumerate(zip(sizes, regions)):
        shape = _polyomino(rng, size, region[2], region[3])
        # Anchor the first assigned object so its component is truly row-major
        # first; other objects retain random offsets inside their regions.
        placed.append(_place_shape(rng, shape, region, anchor_top_left=index == 0))

    colors = rng.sample(list(range(1, 9)), num_objects)
    if semantic in ("repeat_and_tie", "repeat_only"):
        target_index = min(
            (index for index, size in enumerate(sizes) if size == smallest_size),
            key=lambda index: min(placed[index]),
        )
        larger_indices = [index for index, size in enumerate(sizes) if size > smallest_size]
        repeat_index = rng.choice(larger_indices)
        colors[repeat_index] = colors[target_index]

    grid = full_grid(height, width, 0)
    for cells, color in zip(placed, colors):
        for row, col in cells:
            grid[row][col] = color

    requested = {
        "grid_h": height,
        "grid_w": width,
        "num_objects": num_objects,
        "smallest_size": smallest_size,
        "minimum_count": minimum_count,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise AssertionError(f"layout realized {observed}, expected {requested}")
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": requested})
    if errors:
        raise AssertionError("generated invalid instance: " + "; ".join(errors))
    return grid


def _components(grid):
    """Row-major monochromatic four-connected components."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            ordered = sorted(cells)
            result.append(
                {
                    "color": color,
                    "cells": ordered,
                    "size": len(ordered),
                    "first": ordered[0],
                }
            )
    return result


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid rows must be nonempty sequences"]
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be literal integer ARC colors 0..9"]

    errors = []
    if not (8 <= height <= 13 and 8 <= width <= 14):
        errors.append(f"grid dimensions must be within 8..13 by 8..14, got {height}x{width}")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background 0 must be present")
    if any(value == 9 for row in grid for value in row):
        errors.append("input must not already contain recolor target 9")

    components = _components(grid)
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 components, found {len(components)}")
    if components:
        minimum = min(obj["size"] for obj in components)
        minimum_count = sum(obj["size"] == minimum for obj in components)
        if not 1 <= minimum <= 3:
            errors.append(f"minimum component size must be 1..3, got {minimum}")
        if not 1 <= minimum_count <= 2:
            errors.append(f"minimum must occur once or twice, got {minimum_count}")
        if any(obj["size"] > 4 for obj in components):
            errors.append("components must have at most four cells")
        distinct_colors = len({obj["color"] for obj in components})
        if distinct_colors not in (len(components), len(components) - 1):
            errors.append(
                "foreground colors must be all distinct or contain exactly one repeated color"
            )

    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    other = grid[nr][nc]
                    if other not in (0, value):
                        errors.append("different-colored components must not touch orthogonally")
                        row = height
                        break
            else:
                continue
            break

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict) and components:
        realized = observe_overrides(grid)
        for key, value in requested.items():
            if key in AXES and value is not None and realized[key] != value:
                errors.append(f"override {key}={value!r} realized as {realized[key]!r}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    components = _components(grid)
    minimum = min((obj["size"] for obj in components), default=0)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "num_objects": len(components),
        "smallest_size": minimum,
        "minimum_count": sum(obj["size"] == minimum for obj in components),
    }


def _paint_nine(grid, components):
    output = deepcopy(grid)
    for obj in components:
        for row, col in obj["cells"]:
            output[row][col] = 9
    return output


def rule_mirror(grid):
    """Diagnostic mirror of the pinned Racket rule; never label authority."""
    components = _components(grid)
    if not components:
        raise ValueError("cannot select a smallest component from empty foreground")
    target = min(components, key=lambda obj: (obj["size"], obj["first"]))
    return _paint_nine(grid, [target])


def _rival_rarest_color(grid):
    """Canonical-fitting shortcut: recolor the globally least frequent color."""
    components = _components(grid)
    if not components:
        raise ValueError("cannot select a color from empty foreground")
    counts = Counter(value for row in grid for value in row if value != 0)
    target = min(components, key=lambda obj: (counts[obj["color"]], obj["first"]))
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == target["color"]:
                output[row][col] = 9
    return output


def _rival_all_minima(grid):
    components = _components(grid)
    if not components:
        raise ValueError("cannot select minimum components from empty foreground")
    smallest = min(obj["size"] for obj in components)
    return _paint_nine(grid, [obj for obj in components if obj["size"] == smallest])


def _rival_first_component(grid):
    """Spatial shortcut: recolor the row-major first foreground component."""
    components = _components(grid)
    if not components:
        raise ValueError("cannot select the first component from empty foreground")
    return _paint_nine(grid, [components[0]])


SEMANTIC_RIVALS = {
    "rarest_color": _rival_rarest_color,
    "all_minima": _rival_all_minima,
    "first_component": _rival_first_component,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"rarest_color": _rival_rarest_color}


def _repeated_color_witness(grid):
    return _rival_rarest_color(grid) != rule_mirror(grid)


def _tied_minimum_witness(grid):
    return _rival_all_minima(grid) != rule_mirror(grid)


def _nonfirst_target_witness(grid):
    return _rival_first_component(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "component_size_not_global_color_frequency": _repeated_color_witness,
    "row_major_first_minimum_not_all_minima": _tied_minimum_witness,
    "minimum_size_not_first_component": _nonfirst_target_witness,
}
WITNESS_RIVALS = {
    "component_size_not_global_color_frequency": ["rarest_color"],
    "row_major_first_minimum_not_all_minima": ["all_minima"],
    "minimum_size_not_first_component": ["first_component"],
}


def lesson_identifiable(demos, query):
    """Finite-rival lesson check; not a claim against every imaginable rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output")
            continue
        reasons = self_check(pair["input"])
        errors.extend(f"demo {index}: {reason}" for reason in reasons)
        if not reasons and rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demo {index}: incorrect output")
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query must contain an input")
    else:
        reasons = self_check(query["input"])
        errors.extend(f"query: {reason}" for reason in reasons)
        if not reasons and "output" in query and rule_mirror(query["input"]) != query["output"]:
            errors.append("query: incorrect output")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} survives all demonstrations")
    return errors
