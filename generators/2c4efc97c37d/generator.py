"""Input sampler for ARC task 2c4efc97c37d (Max-Depth Strip).

The unchanged Racket authority treats every cell except 0 and 9 as foreground,
orders the resulting 4-connected components from left to right, repeatedly
peels each component's cardinal boundary, and reports the largest peel index.

This generator deliberately includes non-rectangular components whose true
onion depth disagrees with bounding-box thickness.  It also exposes the
authority's binary-mask semantics: disconnected components may share a color,
a connected component may contain multiple colors, and color 9 is background.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from copy import deepcopy
from functools import lru_cache
from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c4efc97c37d"
TASK_ID = GENERATOR_ID
RULE_HASH = "dcdf1daba7ab"
VERSION = "3.1.0"
SUMMARY = (
    "Order binary foreground components from left to right and output each "
    "component's maximum cardinal onion-peel depth as one row."
)

INVARIANTS = [
    "colors 0 and 9 are background; all other ARC colors are foreground",
    "three or four binary components are separated by at least one zero column",
    "every generated grid refutes one-object-per-color and nonzero-foreground shortcuts",
    "reading order is increasing minimum column, breaking ties by minimum row",
    "at least one irregular L-tailed component refutes bounding-box thickness",
    "advertised axes are exact and recoverable from the returned grid",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..18", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled 25..30", "valid": "25..30"},
    "object_count": {"type": "int", "default": "scheduled 3..4", "valid": "3..4"},
    "max_depth": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "irregular_count": {"type": "int", "default": "scheduled 1..3", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

# The first three slots exactly cover every canonical input profile.  The
# remaining slots break pairwise axis locks and broaden the default manifold.
_DEFAULT_PROFILES = (
    (9, 25, 3),
    (11, 25, 3),
    (11, 27, 3),
    (9, 27, 4),
    (12, 28, 4),
    (15, 30, 3),
    (18, 26, 4),
    (12, 30, 3),
)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Record an exact scheduled default while preserving the full override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # A singleton keyed choice records honest default provenance.  Explicit
    # overrides take the full strict-int branch above, so every advertised
    # boundary remains accepted in every difficulty band.
    return ctx.draw_choice(name, (default,))


def _shape_bounds(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _square(depth: int) -> set[tuple[int, int]]:
    side = 2 * depth - 1
    return {(row, col) for row in range(side) for col in range(side)}


def _diamond(depth: int) -> set[tuple[int, int]]:
    radius = depth - 1
    side = 2 * radius + 1
    return {
        (row, col)
        for row in range(side)
        for col in range(side)
        if abs(row - radius) + abs(col - radius) <= radius
    }


def _l_tailed_square(depth: int) -> set[tuple[int, int]]:
    """Depth ``d`` but a (2d+1)x(2d+1) box, so the bbox shortcut says d+1.

    Start with a (2d-1)-square shifted two cells down and right.  A two-cell
    tail extends upward from the square's top-middle cell and another extends
    leftward from its middle-left cell.  The tails enlarge both bounding-box
    dimensions without shielding all sides of any deeper core layer.
    """
    side = 2 * depth - 1
    middle = depth - 1
    cells = {
        (row + 2, col + 2)
        for row in range(side)
        for col in range(side)
    }
    center_col = middle + 2
    center_row = middle + 2
    cells.update({(0, center_col), (1, center_col)})
    cells.update({(center_row, 0), (center_row, 1)})
    return cells


@lru_cache(maxsize=None)
def _depth_sequences(
    object_count: int, max_depth: int, irregular_count: int
) -> tuple[tuple[int, ...], ...]:
    """All output rows that fit the narrowest advertised canvas.

    A square of depth d needs width 2d-1.  The mandatory rival-refuting
    L-tailed component adds two columns.  Extra irregular components use
    same-width diamonds whenever their depth is at least two; depth-one
    irregulars need another two-column L tail.
    """
    feasible: list[tuple[int, ...]] = []
    for depths in product(range(1, max_depth + 1), repeat=object_count):
        if max(depths) != max_depth or len(set(depths)) < 2:
            continue
        base_width = sum(2 * depth - 1 for depth in depths) + object_count - 1
        non_primary_deep = sum(depth >= 2 for depth in depths) - 1
        depth_one_extras = max(0, irregular_count - 1 - non_primary_deep)
        minimum_width = base_width + 2 + 2 * depth_one_extras
        if minimum_width <= 25:
            feasible.append(tuple(depths))
    if not feasible:
        raise ValueError(
            "no constructive depth rows for "
            f"object_count={object_count}, max_depth={max_depth}, "
            f"irregular_count={irregular_count}"
        )
    return tuple(feasible)


def _scatter_slack(rng, amount: int, slots: int) -> list[int]:
    values = [0] * slots
    for _ in range(amount):
        values[rng.randrange(slots)] += 1
    return values


def _colorized_shapes(
    rng,
    depths: list[int],
    shapes: list[set[tuple[int, int]]],
    mode: str,
) -> list[dict[tuple[int, int], int]]:
    """Assign colors that make binary connectivity visibly necessary."""
    if mode not in {"reused", "mixed"}:
        raise ValueError(f"unknown color topology mode {mode!r}")

    palette = rng.sample(list(range(1, 9)), len(shapes) + 1)
    base_colors = palette[: len(shapes)]
    accent = palette[-1]

    mixed_index: int | None = None
    accent_cells: set[tuple[int, int]] = set()
    if mode == "reused":
        unequal_pairs = [
            (left, right)
            for left in range(len(depths))
            for right in range(left + 1, len(depths))
            if depths[left] != depths[right]
        ]
        left, right = rng.choice(unequal_pairs)
        base_colors[right] = base_colors[left]
    else:
        candidates = [index for index, depth in enumerate(depths) if depth >= 2]
        mixed_index = rng.choice(candidates)
        min_row = min(row for row, _ in shapes[mixed_index])
        accent_cells = {
            point for point in shapes[mixed_index] if point[0] == min_row
        }

    colored: list[dict[tuple[int, int], int]] = []
    for index, shape in enumerate(shapes):
        cells = {point: base_colors[index] for point in shape}
        if index == mixed_index:
            for point in accent_cells:
                cells[point] = accent
        colored.append(cells)
    return colored


def _isolated_zero_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Background cells not cardinally adjacent to any foreground cell."""
    height, width = len(grid), len(grid[0])
    candidates: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if all(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] == 0
                for dr, dc in _CARDINAL
            ):
                candidates.append((row, col))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_h, profile_w, profile_count = _DEFAULT_PROFILES[sample_index % len(_DEFAULT_PROFILES)]
    band_offset = _BAND_OFFSET.get(difficulty, 0)
    default_max_depth = 2 + ((int(seed) + int(sample_index) + band_offset) % 3)
    default_irregular = 1 + ((2 * int(seed) + int(sample_index) // 2 + band_offset) % 3)

    height = _scheduled_int(ctx, "grid_h", 9, 18, profile_h)
    width = _scheduled_int(ctx, "grid_w", 25, 30, profile_w)
    object_count = _scheduled_int(ctx, "object_count", 3, 4, profile_count)
    max_depth = _scheduled_int(ctx, "max_depth", 2, 4, default_max_depth)
    irregular_count = _scheduled_int(ctx, "irregular_count", 1, 3, default_irregular)
    default_color_topology = ("reused", "mixed")[int(sample_index) % 2]
    color_topology = ctx.draw_choice("color_topology", (default_color_topology,))

    rng = ctx.draw_rng("layout")
    depth_rng = ctx.draw_rng("depth_row")
    palette_rng = ctx.draw_rng("palette")
    witness_rng = ctx.draw_rng("background_nine")
    depths = list(
        depth_rng.choice(_depth_sequences(object_count, max_depth, irregular_count))
    )

    max_indices = [index for index, depth in enumerate(depths) if depth == max_depth]
    max_index = rng.choice(max_indices)
    deep_candidates = [
        index
        for index, depth in enumerate(depths)
        if index != max_index and depth >= 2
    ]
    unit_candidates = [
        index
        for index, depth in enumerate(depths)
        if index != max_index and depth == 1
    ]
    rng.shuffle(deep_candidates)
    rng.shuffle(unit_candidates)
    extras = (deep_candidates + unit_candidates)[: irregular_count - 1]
    irregular_indices = {max_index, *extras}

    shapes: list[set[tuple[int, int]]] = []
    for index, depth in enumerate(depths):
        if index == max_index:
            # This object always falsifies bounding-box thickness.
            shape = _l_tailed_square(depth)
        elif index not in irregular_indices:
            shape = _square(depth)
        elif depth == 1:
            shape = _l_tailed_square(depth)
        else:
            # A Manhattan diamond is irregular without consuming extra width.
            shape = _diamond(depth)
        shapes.append(shape)

    dimensions = [_shape_bounds(shape) for shape in shapes]
    minimum_width = sum(shape_w for _, shape_w in dimensions) + object_count - 1
    if minimum_width > width:
        # This should be unreachable for the declared domain.  It is loud so a
        # future axis expansion cannot silently clip an exact request.
        raise ValueError(
            f"declared combination needs width {minimum_width}, requested {width}"
        )
    if max(shape_h for shape_h, _ in dimensions) > height:
        raise ValueError("declared combination does not fit requested grid_h")

    horizontal = _scatter_slack(rng, width - minimum_width, object_count + 1)
    colored_shapes = _colorized_shapes(palette_rng, depths, shapes, color_topology)
    grid = full_grid(height, width, 0)

    column = horizontal[0]
    for index, (shape, colored, (shape_h, shape_w)) in enumerate(
        zip(shapes, colored_shapes, dimensions)
    ):
        row0 = rng.randint(0, height - shape_h)
        for row, col in sorted(shape):
            grid[row0 + row][column + col] = colored[(row, col)]
        column += shape_w
        if index + 1 < object_count:
            column += 1 + horizontal[index + 1]

    # A single isolated 9 is ignored by the authority but becomes a separate
    # object under the common shortcut “every nonzero cell is foreground.”
    witness_cells = _isolated_zero_cells(grid)
    if not witness_cells:
        raise AssertionError("construction left no isolated cell for color-9 witness")
    witness_row, witness_col = witness_rng.choice(witness_cells)
    grid[witness_row][witness_col] = 9

    # Construction assertions are independent of caller metadata and turn any
    # future geometry drift into a local, reproducible failure.
    realized = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "object_count": object_count,
        "max_depth": max_depth,
        "irregular_count": irregular_count,
    }
    if realized != requested:
        raise AssertionError(f"construction drift: requested {requested}, realized {realized}")
    intended = rule_mirror(grid)
    if _bbox_rectangle_depth(grid) == intended:
        raise AssertionError("construction failed to refute bounding-box depth")
    if _color_partition_depth(grid) == intended:
        raise AssertionError("construction failed to refute one-object-per-color")
    if _nonzero_foreground_depth(grid) == intended:
        raise AssertionError("construction failed to refute nonzero foreground")
    return grid


# ---------------------------------------------------------------------------
# Independent-from-layout analysis used by validation and semantic contracts.
# ---------------------------------------------------------------------------

def _components_ignoring(
    grid: list[list[int]], backgrounds: set[int]
) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] in backgrounds:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in _CARDINAL:
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] not in backgrounds
                    ):
                        seen.add(point)
                        stack.append(point)
            found.append(cells)
    found.sort(key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))
    return found


def _binary_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    return _components_ignoring(grid, {0, 9})


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


def _is_rectangle(cells: Iterable[tuple[int, int]]) -> bool:
    points = set(cells)
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return len(points) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _analysis(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "components": [],
        "depths": [],
        "colors": [],
        "color_topology": None,
        "grid_h": None,
        "grid_w": None,
        "object_count": 0,
        "max_depth": None,
        "irregular_count": 0,
    }
    errors: list[str] = facts["errors"]
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a non-empty list of rows")
        return facts
    if any(not isinstance(row, list) for row in grid):
        errors.append("every row must be a list")
        return facts
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        errors.append("grid must be a non-empty rectangle")
        return facts

    height, width = len(grid), len(grid[0])
    facts["grid_h"], facts["grid_w"] = height, width
    if not (9 <= height <= 18):
        errors.append(f"grid_h must be in 9..18; got {height}")
    if not (25 <= width <= 30):
        errors.append(f"grid_w must be in 25..30; got {width}")

    for row in grid:
        for value in row:
            if type(value) is not int:
                errors.append("all cells must be integers (not bool)")
                return facts
            if not (0 <= value <= 9):
                errors.append(f"cell colors must be in 0..9; got {value}")
                return facts

    components = _binary_components(grid)
    depths = [_onion_depth(cells) for cells in components]
    colors = [
        tuple(sorted({grid[row][col] for row, col in cells}))
        for cells in components
    ]
    monochrome = [entry[0] for entry in colors if len(entry) == 1]
    color_topology = (
        "mixed"
        if any(len(entry) > 1 for entry in colors)
        else "reused"
        if len(monochrome) != len(set(monochrome))
        else "unique"
    )

    facts.update(
        {
            "components": components,
            "depths": depths,
            "colors": colors,
            "color_topology": color_topology,
            "object_count": len(components),
            "max_depth": max(depths) if depths else None,
            "irregular_count": sum(not _is_rectangle(cells) for cells in components),
        }
    )

    if not (3 <= len(components) <= 4):
        errors.append(f"expected 3..4 components; got {len(components)}")
    if not depths:
        return facts
    if not (2 <= max(depths) <= 4):
        errors.append(f"maximum onion depth must be in 2..4; got {max(depths)}")
    if len(set(depths)) < 2:
        errors.append(f"examples need at least two distinct depths; got {depths}")
    irregular = facts["irregular_count"]
    if not (1 <= irregular <= 3):
        errors.append(f"expected 1..3 irregular components; got {irregular}")
    return facts


def semantic_observables(grid: Any) -> dict[str, Any]:
    return _analysis(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "object_count": int(facts["object_count"]),
        "max_depth": int(facts["max_depth"]),
        "irregular_count": int(facts["irregular_count"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        realized = observe_overrides(grid)
        for name, expected in meta["overrides"].items():
            if name in AXES and expected is not None and realized[name] != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {realized[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Complete reviewed input grammar; all canonical pairs satisfy it."""
    return self_check(grid)


def rule_mirror(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [list(facts["depths"])]


def _bbox_rectangle_depth(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    values = []
    for cells in facts["components"]:
        shape_h, shape_w = _shape_bounds(cells)
        values.append((min(shape_h, shape_w) + 1) // 2)
    return [values]


def _color_partition_depth(grid: Any) -> list[list[int]]:
    """Plausible wrong rule: each non-background color is one object."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    groups: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (0, 9):
                groups.setdefault(value, []).append((row, col))
    ordered = sorted(
        groups.values(),
        key=lambda cells: (min(col for _, col in cells), min(row for row, _ in cells)),
    )
    return [[_onion_depth(cells) for cells in ordered]]


def _nonzero_foreground_depth(grid: Any) -> list[list[int]]:
    """Plausible wrong rule: only zero is background, so color 9 is foreground."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [[
        _onion_depth(cells)
        for cells in _components_ignoring(grid, {0})
    ]]


def _valid_rival_disagreement(grid: Any, rival: Callable[[Any], list[list[int]]]) -> bool:
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "bbox_rectangle_depth": _bbox_rectangle_depth,
    "color_partition_depth": _color_partition_depth,
    "nonzero_foreground_depth": _nonzero_foreground_depth,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "bbox_depth_disagreement": lambda grid: _valid_rival_disagreement(
        grid, _bbox_rectangle_depth
    ),
    "color_partition_disagreement": lambda grid: _valid_rival_disagreement(
        grid, _color_partition_depth
    ),
    "nonzero_foreground_disagreement": lambda grid: _valid_rival_disagreement(
        grid, _nonzero_foreground_depth
    ),
}
WITNESS_RIVALS = {
    "bbox_depth_disagreement": ("bbox_rectangle_depth",),
    "color_partition_disagreement": ("color_partition_depth",),
    "nonzero_foreground_disagreement": ("nonzero_foreground_depth",),
}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} is malformed"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input invalid: {errors[0]}"]
    if rule_mirror(pair["input"]) != pair["output"]:
        return [f"{label} output does not follow the selected rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """A three-demo lesson must falsify every declared executable shortcut."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"surviving lesson shortcut: {name}")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local near misses used by the generic self-check mutation gate."""
    source = generate(991, 0, difficulty="easy")

    illegal_color = deepcopy(source)
    illegal_color[0][0] = 10

    all_background = [[0 for _ in row] for row in source]

    return [
        ("illegal_arc_color", illegal_color),
        ("missing_binary_components", all_background),
    ]
