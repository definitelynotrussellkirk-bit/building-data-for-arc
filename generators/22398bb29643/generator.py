"""Constructive input generator for task 22398bb29643.

The authoritative rule finds every nonzero 4-connected component, orders the
components by bounding-box top row and then left column, and emits one row of
component colors.  This module generates only the inputs; ``rule_mirror`` is a
pure-Python review oracle for tests and semantic-rival checks.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22398bb29643"
TASK_ID = GENERATOR_ID
RULE_HASH = "bea915e9e998"
VERSION = "3.0.0"
SUMMARY = (
    "Three to six separated monochrome polyominoes, each of size 3..5, are "
    "summarized by their colors in bounding-box top/left order. Canonical-scale "
    "profiles alternate with repeated-color witnesses in every difficulty band, "
    "so color-deduplication is not a valid lesson shortcut."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly 3..6 nonzero 4-connected components",
    "every component is monochrome, has 3..5 cells, and is separated by background",
    "at least two distinct nonzero colors occur",
    "components are ordered by bounding-box top row and then left column",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "9..14",
    },
    "components": {
        "type": "int",
        "default": "scheduled 4 or 6",
        "valid": "3..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# (height, width, number of distinct nonzero colors).  The corresponding total
# distinct-color profiles are 6, 4, 4, 6 and 4 because background is also present.
_CANONICAL_PROFILES = (
    (10, 10, 5),
    (9, 9, 3),
    (9, 10, 3),
    (9, 12, 5),
    (9, 11, 3),
)
SCHEDULE_PROFILES = tuple(
    f"{mode}_{height}x{width}_{colors}_colors"
    for height, width, colors in _CANONICAL_PROFILES
    for mode in ("canonical", "repeated_color_witness")
)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Every shape fits a 3x2 slot.  Horizontal-slot variants are transposes.
_VERTICAL_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
}


def _validate_controls(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    bounds = {
        "grid_h": (9, 12),
        "grid_w": (9, 14),
        "components": (3, 6),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")
        low, high = bounds[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the canonical-scale profile scheduled for this sample index."""
    del seed
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int) -> tuple[int, int, int, bool]:
    profile = _CANONICAL_PROFILES[(sample_index // 2) % len(_CANONICAL_PROFILES)]
    return (*profile, sample_index % 2 == 1)


def _scheduled_int(ctx, label: str, low: int, high: int, default: int) -> int:
    """Use a scheduled default while preserving the complete exact override domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, low, high)
    return ctx.draw_int_strict(label, default, default)


def _transpose(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return tuple((col, row) for row, col in shape)


def _shape_for_slot(rng, size: int, block_h: int, block_w: int) -> tuple[tuple[int, int], ...]:
    candidates = _VERTICAL_SHAPES[size]
    shape = rng.choice(candidates)
    if (block_h, block_w) == (2, 3):
        shape = _transpose(shape)
    if rng.random() < 0.5:
        shape = tuple((block_h - 1 - row, col) for row, col in shape)
    if rng.random() < 0.5:
        shape = tuple((row, block_w - 1 - col) for row, col in shape)
    return tuple(sorted(shape))


def _slot_origins(height: int, width: int, count: int, rng):
    feasible = []
    for block_h, block_w in ((3, 2), (2, 3)):
        row_slots = (height + 1) // (block_h + 1)
        col_slots = (width + 1) // (block_w + 1)
        capacity = row_slots * col_slots
        if capacity < count:
            continue
        used_h = row_slots * block_h + max(0, row_slots - 1)
        used_w = col_slots * block_w + max(0, col_slots - 1)
        feasible.append((block_h, block_w, row_slots, col_slots, used_h, used_w))
    if not feasible:
        raise RuntimeError(
            f"no separated-slot layout fits {count} components in {height}x{width}"
        )

    block_h, block_w, row_slots, col_slots, used_h, used_w = rng.choice(feasible)
    top = rng.randrange(height - used_h + 1)
    left = rng.randrange(width - used_w + 1)
    origins = [
        (top + row * (block_h + 1), left + col * (block_w + 1))
        for row in range(row_slots)
        for col in range(col_slots)
    ]
    return block_h, block_w, rng.sample(origins, count)


def _component_sizes(count: int, rng) -> list[int]:
    # Every generated scene includes canonical sizes 3, 4, and 5.  Remaining
    # components vary independently within the canonical range.
    sizes = [5, 4, 3]
    sizes.extend(rng.choice((3, 4, 5)) for _ in range(count - len(sizes)))
    rng.shuffle(sizes)
    return sizes


def _components(grid) -> list[list[tuple[int, int]]]:
    """Return all nonzero 4-connected components in row-major discovery order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            result.append(component)
    return result


def _component_key(component: list[tuple[int, int]]) -> tuple[int, int]:
    return (
        min(row for row, _ in component),
        min(col for _, col in component),
    )


def _component_color(grid, component: list[tuple[int, int]]) -> int:
    row, col = min(component)
    return grid[row][col]


def rule_mirror(grid):
    """Pure-Python mirror of the selected Racket component-order rule."""
    components = sorted(_components(grid), key=_component_key)
    return [[_component_color(grid, component) for component in components]]


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"], "height": 0, "width": 0, "components": []}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be sequences"], "height": len(grid), "width": 0, "components": []}
    width = len(grid[0])
    if width == 0:
        return {"errors": ["empty grid row"], "height": len(grid), "width": 0, "components": []}
    if any(len(row) != width for row in grid):
        return {"errors": ["ragged grid"], "height": len(grid), "width": width, "components": []}

    height = len(grid)
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")
    invalid = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append("grid cells must be literal ARC color integers 0..9")
        return {"errors": errors, "height": height, "width": width, "components": []}

    values = {value for row in grid for value in row}
    if 0 not in values:
        errors.append("background color 0 must be present")

    components = _components(grid)
    if not 3 <= len(components) <= 6:
        errors.append(f"expected 3..6 components, found {len(components)}")

    component_colors: list[int] = []
    component_sizes: list[int] = []
    for index, component in enumerate(components):
        colors = {grid[row][col] for row, col in component}
        if len(colors) != 1:
            errors.append(f"component {index} is not monochrome: {sorted(colors)}")
        component_sizes.append(len(component))
        if not 3 <= len(component) <= 5:
            errors.append(
                f"component {index} has {len(component)} cells; expected 3..5"
            )
        component_colors.append(_component_color(grid, component))

    if len(set(component_colors)) < 2:
        errors.append("need at least two distinct component colors")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "component_colors": component_colors,
        "component_sizes": component_sizes,
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "components": len(analysis["components"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for name, expected in meta["overrides"].items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The selected rule's complete intended input grammar."""
    return self_check(grid)


def _deduplicate_component_colors(grid):
    """RIVAL: emit each component color only at its first ordered occurrence."""
    ordered = rule_mirror(grid)[0]
    seen: set[int] = set()
    output: list[int] = []
    for color in ordered:
        if color not in seen:
            seen.add(color)
            output.append(color)
    return [output]


def _has_repeated_component_color(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    colors = analysis["component_colors"]
    return len(colors) > len(set(colors))


SEMANTIC_RIVALS = {
    "deduplicate_component_colors": _deduplicate_component_colors,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "repeated_component_color": _has_repeated_component_color,
}
WITNESS_RIVALS = {
    "repeated_component_color": ["deduplicate_component_colors"],
}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival only when it fits all demos and changes the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"{name} could not be evaluated: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful input with exact observable controls."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    default_h, default_w, default_colors, witness_profile = _profile_defaults(sample_index)
    default_components = default_colors

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, "grid_h", 9, 12, default_h)
    width = _scheduled_int(ctx, "grid_w", 9, 14, default_w)
    component_count = _scheduled_int(ctx, "components", 3, 6, default_components)

    # Even schedule slots retain exact canonical color support. Odd slots keep
    # the same canonical component count but repeat one color, providing a
    # direct counterexample to the canonical-fitting deduplication shortcut.
    distinct_colors = min(default_colors, component_count)
    if witness_profile:
        distinct_colors = max(2, distinct_colors - 1)

    layout_rng = ctx.draw_rng("component_layout")
    block_h, block_w, origins = _slot_origins(
        height, width, component_count, layout_rng
    )
    sizes = _component_sizes(component_count, ctx.draw_rng("component_sizes"))

    band = difficulty or "medium"
    palette_rng = ctx.draw_rng(f"component_palette_{band}")
    first_color = {"easy": 1, "medium": 2, "hard": 3}[band]
    remaining = [color for color in range(1, 10) if color != first_color]
    palette = [first_color, *palette_rng.sample(remaining, distinct_colors - 1)]
    colors = list(palette)
    while len(colors) < component_count:
        colors.append(palette[(len(colors) - len(palette)) % len(palette)])
    tail = colors[1:]
    palette_rng.shuffle(tail)
    colors[1:] = tail

    grid = full_grid(height, width, 0)
    shape_rng = ctx.draw_rng("component_shapes")
    for origin, size, color in zip(origins, sizes, colors):
        top, left = origin
        for delta_row, delta_col in _shape_for_slot(
            shape_rng, size, block_h, block_w
        ):
            grid[top + delta_row][left + delta_col] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid
