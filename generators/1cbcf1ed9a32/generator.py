"""Generator for S11_H7: find the D4-common shape across three panels.

Each lawful input has three equal-width panels separated by full-height color-5
columns.  The unique largest object in each panel has the same cell count; two
largest objects are rotation/reflection variants of one another and the third
belongs to another D4 class.  The answer is the lexicographically canonical D4
form of the repeated class, normalized and recolored 8.

The equal-size construction is deliberate.  Earlier versions made the
distractor a different size, so a shortcut could select the repeated cell count
without comparing shape.  A four-slot schedule now also puts the distractor in
panel 0 twice per period, refuting the canonical-only shortcut "always use the
first panel" even under every one-pair query rotation of a five-pair window.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1cbcf1ed9a32"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "dc0d41aa47ba"
SUMMARY = (
    "Split at the two full-height color-5 dividers, compare each panel's "
    "unique largest object up to D4 symmetry, and output the repeated canonical "
    "shape in color 8."
)

INVARIANTS = [
    "two full-height color-5 columns split the input into three equal-width panels",
    "each panel has one uniquely largest monochrome four-connected object",
    "all three largest objects have the same cell count",
    "exactly two largest objects share a D4 canonical signature",
    "the output is that repeated canonical signature recolored 8",
]

COMMON_PAIRS = ("0,1", "0,2", "1,2")
PALETTE_KINDS = ("default", "warm", "cool", "varied")
SECONDARY_OBJECT_MODES = ("none", "singletons")
PALETTES = {
    "default": (2, 3, 4),
    "warm": (2, 4, 9),
    "cool": (1, 6, 8),
    "varied": (3, 7, 9),
}
_PALETTE_BY_SET = {frozenset(colors): name for name, colors in PALETTES.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot lesson schedule",
        "valid": "5..8",
    },
    "panel_w": {
        "type": "int",
        "default": "four-slot lesson schedule",
        "valid": "4..7",
    },
    "common_cells": {
        "type": "int",
        "default": "four-slot lesson schedule",
        "valid": "3..7",
    },
    "common_pair": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "0,1|0,2|1,2",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice",
        "valid": "default|warm|cool|varied",
    },
    "secondary_objects": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "none|singletons",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_panel0_distractor",
    "expanded_alternate_pair",
    "expanded_panel0_distractor",
    "expanded_pair01",
)
_SCHEDULE_DEFAULTS = (
    {
        "grid_h": 5,
        "panel_w": 4,
        "common_cells": 4,
        "common_pair": "1,2",
        "secondary_objects": "none",
    },
    {
        "grid_h": 8,
        "panel_w": 7,
        "common_cells": 7,
        "common_pair": "0,2",
        "secondary_objects": "singletons",
    },
    {
        "grid_h": 7,
        "panel_w": 6,
        "common_cells": 7,
        "common_pair": "1,2",
        "secondary_objects": "singletons",
    },
    {
        "grid_h": 6,
        "panel_w": 5,
        "common_cells": 6,
        "common_pair": "0,1",
        "secondary_objects": "none",
    },
)

_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        raise ValueError("cannot normalize an empty shape")
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def _rot90(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_row = max(row for row, _ in points)
    return _normalize((col, max_row - row) for row, col in points)


def _mirror_h(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_col = max(col for _, col in points)
    return _normalize((row, max_col - col) for row, col in points)


def _d4_orbit(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    base = _normalize(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        current = _mirror_h(base) if reflected else base
        for _ in range(4):
            variants.add(_normalize(current))
            current = _rot90(current)
    return tuple(sorted(variants))


def _canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _d4_orbit(cells)[0]


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    points = set(cells)
    if not points:
        return False
    seen = {next(iter(points))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _DIRECTIONS:
            point = row + dr, col + dc
            if point in points and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == points


def _build_shape_bank() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """Enumerate every free polyomino class through seven cells.

    Classes are grown one cell at a time and canonicalized under D4.  Instance
    generation later filters them by the current panel envelope, so canonical
    5x14 anchors remain constructible while larger scheduled canvases expose a
    much wider output codomain.
    """
    by_size: dict[int, set[tuple[tuple[int, int], ...]]] = {1: {((0, 0),)}}
    for size in range(2, 8):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in by_size[size - 1]:
            points = set(shape)
            boundary = {
                (row + dr, col + dc)
                for row, col in points
                for dr, dc in _DIRECTIONS
                if (row + dr, col + dc) not in points
            }
            for point in boundary:
                expanded.add(_canonical(points | {point}))
        by_size[size] = expanded
    expected_counts = {3: 2, 4: 5, 5: 12, 6: 35, 7: 108}
    result = {size: tuple(sorted(by_size[size])) for size in range(3, 8)}
    if {size: len(shapes) for size, shapes in result.items()} != expected_counts:
        raise RuntimeError("free-polyomino enumeration produced unexpected class counts")
    return result


def _max_side(shape: Iterable[tuple[int, int]]) -> int:
    normalized = _normalize(shape)
    return max(
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


_SHAPES_BY_SIZE = _build_shape_bank()


def _validate_seed_and_index(seed: object, sample_index: object) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer, excluding booleans")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, excluding booleans")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_difficulty(difficulty: object) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    _validate_seed_and_index(seed, sample_index)
    _validate_difficulty(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(sorted(unknown))}")
    integer_domains = {
        "grid_h": (5, 8),
        "panel_w": (4, 7),
        "common_cells": (3, 7),
    }
    enum_domains = {
        "common_pair": COMMON_PAIRS,
        "palette_kind": PALETTE_KINDS,
        "secondary_objects": SECONDARY_OBJECT_MODES,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in integer_domains:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, excluding booleans")
            low, high = integer_domains[name]
            if not low <= value <= high:
                raise ValueError(f"{name} must be in {low}..{high}, got {value!r}")
        else:
            if type(value) is not str:
                raise TypeError(f"{name} must be a string")
            if value not in enum_domains[name]:
                raise ValueError(
                    f"{name} must be one of {list(enum_domains[name])}, got {value!r}"
                )


def _paint(
    grid: list[list[int]],
    top: int,
    left: int,
    cells: Iterable[tuple[int, int]],
    color: int,
) -> None:
    for row, col in cells:
        grid[top + row][left + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic lawful input and honor every declared override."""
    _validate_seed_and_index(seed, sample_index)
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)

    slot = sample_index % LESSON_SCHEDULE_PERIOD
    effective_overrides = dict(overrides)
    for name, value in _SCHEDULE_DEFAULTS[slot].items():
        if effective_overrides.get(name) is None:
            effective_overrides[name] = value

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_strict("grid_h", 5, 8)
    panel_width = ctx.draw_int_strict("panel_w", 4, 7)
    common_cells = ctx.draw_int_strict("common_cells", 3, 7)
    common_pair = ctx.draw_choice("common_pair", COMMON_PAIRS)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    secondary_objects = ctx.draw_choice("secondary_objects", SECONDARY_OBJECT_MODES)

    band = difficulty or "mixed"
    geometry_rng = ctx.draw_rng(f"geometry_{band}")
    palette_rng = ctx.draw_rng(f"palette_order_{band}")

    max_shape_side = min(height - 2, panel_width)
    classes = tuple(
        shape for shape in _SHAPES_BY_SIZE[common_cells]
        if _max_side(shape) <= max_shape_side
    )
    if len(classes) < 2:
        raise RuntimeError("override combination leaves fewer than two D4 shape classes")
    common_candidates = tuple(shape for shape in classes if len(_d4_orbit(shape)) > 1)
    common_shape = geometry_rng.choice(common_candidates)
    common_signature = _canonical(common_shape)
    distractor_shape = geometry_rng.choice(
        tuple(shape for shape in classes if _canonical(shape) != common_signature)
    )

    common_orbit = _d4_orbit(common_shape)
    first_variant_index = geometry_rng.randrange(len(common_orbit))
    second_choices = tuple(
        index for index in range(len(common_orbit)) if index != first_variant_index
    )
    second_variant_index = geometry_rng.choice(second_choices)
    common_forms = (
        common_orbit[first_variant_index],
        common_orbit[second_variant_index],
    )
    distractor_form = geometry_rng.choice(_d4_orbit(distractor_shape))

    pair_indices = tuple(int(value) for value in common_pair.split(","))
    form_by_panel: dict[int, tuple[tuple[int, int], ...]] = {
        pair_indices[0]: common_forms[0],
        pair_indices[1]: common_forms[1],
    }
    distractor_panel = next(index for index in range(3) if index not in pair_indices)
    form_by_panel[distractor_panel] = distractor_form

    colors = palette_rng.sample(list(PALETTES[palette_kind]), 3)
    total_width = 3 * panel_width + 2
    grid = full_grid(height, total_width, 0)
    divider_columns = (panel_width, 2 * panel_width + 1)
    for row in range(height):
        for column in divider_columns:
            grid[row][column] = 5

    panel_starts = (0, panel_width + 1, 2 * panel_width + 2)
    # Main shapes live above rows height-2 and height-1.  The former is a
    # guaranteed blank separator; the latter stores optional singletons.
    main_height = height - 2
    for panel_index, panel_start in enumerate(panel_starts):
        shape = form_by_panel[panel_index]
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        if shape_height > main_height or shape_width > panel_width:
            raise RuntimeError("3x3 shape bank violated the placement envelope")
        top = geometry_rng.randint(0, main_height - shape_height)
        left = geometry_rng.randint(0, panel_width - shape_width)
        color = colors[panel_index]
        _paint(grid, top, panel_start + left, shape, color)
        if secondary_objects == "singletons":
            singleton_col = geometry_rng.randrange(panel_width)
            grid[height - 1][panel_start + singleton_col] = color

    return grid


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    return []


def _components(panel: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = len(panel), len(panel[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for row in range(height):
        for col in range(width):
            color = panel[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _DIRECTIONS:
                    point = r + dr, c + dc
                    rr, cc = point
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and point not in seen
                        and panel[rr][cc] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            components.append((color, tuple(cells)))
    return components


def _divider_columns(grid: list[list[int]]) -> list[int]:
    return [
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 5 for row in range(len(grid)))
    ]


def _panel_bounds(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    dividers = _divider_columns(grid)
    if len(dividers) != 2:
        raise ValueError(f"expected exactly two full-height color-5 dividers, got {dividers}")
    return (
        (0, dividers[0]),
        (dividers[0] + 1, dividers[1]),
        (dividers[1] + 1, len(grid[0])),
    )


def _largest_records(grid: list[list[int]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for start, stop in _panel_bounds(grid):
        panel = [list(row[start:stop]) for row in grid]
        components = _components(panel)
        if not components:
            raise ValueError("each panel must contain an object")
        largest_size = max(len(cells) for _, cells in components)
        largest = [(color, cells) for color, cells in components if len(cells) == largest_size]
        if len(largest) != 1:
            raise ValueError("each panel must have a unique largest object")
        color, cells = largest[0]
        records.append(
            {
                "color": color,
                "cells": _normalize(cells),
                "canonical": _canonical(cells),
                "size": len(cells),
                "component_sizes": tuple(sorted(len(part) for _, part in components)),
                "component_colors": tuple(sorted({component_color for component_color, _ in components})),
            }
        )
    return records


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the selected canonical-like manifold without consulting labels."""
    del meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    _validate_difficulty(difficulty)
    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 8:
        errors.append("grid height must be in 5..8")
    dividers = _divider_columns(grid)
    if len(dividers) != 2:
        errors.append(f"expected exactly two full-height color-5 dividers, got {dividers}")
        return errors
    bounds = (
        (0, dividers[0]),
        (dividers[0] + 1, dividers[1]),
        (dividers[1] + 1, width),
    )
    widths = [stop - start for start, stop in bounds]
    if len(set(widths)) != 1 or not 4 <= widths[0] <= 7:
        errors.append(f"expected three equal panel widths in 4..7, got {widths}")
    divider_set = set(dividers)
    if any(
        value == 5
        for row in grid
        for col, value in enumerate(row)
        if col not in divider_set
    ):
        errors.append("color 5 may appear only in the two divider columns")

    records: list[dict[str, object]] = []
    secondary_signatures: list[str] = []
    panel_colors: list[int] = []
    for panel_index, (start, stop) in enumerate(bounds):
        panel = [list(row[start:stop]) for row in grid]
        colors = {value for row in panel for value in row if value != 0}
        if len(colors) != 1:
            errors.append(
                f"panel {panel_index} must use exactly one nonzero object color, got {sorted(colors)}"
            )
        components = _components(panel)
        if not components:
            errors.append(f"panel {panel_index} is empty")
            continue
        largest_size = max(len(cells) for _, cells in components)
        largest = [(color, cells) for color, cells in components if len(cells) == largest_size]
        if len(largest) != 1:
            errors.append(f"panel {panel_index} must have a unique largest object")
            continue
        if len(components) == 1:
            secondary_signatures.append("none")
        elif len(components) == 2 and sorted(len(cells) for _, cells in components)[0] == 1:
            secondary_signatures.append("singletons")
        else:
            errors.append(
                f"panel {panel_index} may contain only its main object and one singleton"
            )
            secondary_signatures.append("invalid")
        color, cells = largest[0]
        panel_colors.append(color)
        records.append(
            {
                "color": color,
                "cells": _normalize(cells),
                "canonical": _canonical(cells),
                "size": len(cells),
            }
        )

    if len(panel_colors) == 3 and len(set(panel_colors)) != 3:
        errors.append("the three panel object colors must be distinct")
    if len(secondary_signatures) == 3 and len(set(secondary_signatures)) != 1:
        errors.append("secondary-object mode must be consistent across all panels")
    if len(records) == 3:
        sizes = {record["size"] for record in records}
        if len(sizes) != 1 or not 3 <= next(iter(sizes)) <= 7:
            errors.append(f"largest objects must have one shared size in 3..7, got {sorted(sizes)}")
        signatures = [record["canonical"] for record in records]
        counts = Counter(signatures)
        if sorted(counts.values()) != [1, 2]:
            errors.append(
                "exactly two panel-largest objects must share one D4 canonical signature"
            )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _common_pair_from_records(records: list[dict[str, object]]) -> str:
    signatures = [record["canonical"] for record in records]
    counts = Counter(signatures)
    common = next(signature for signature, count in counts.items() if count == 2)
    return ",".join(
        str(index) for index, signature in enumerate(signatures) if signature == common
    )


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    bounds = _panel_bounds(grid)
    panel_width = bounds[0][1] - bounds[0][0]
    records = _largest_records(grid)
    palette_set = frozenset(int(record["color"]) for record in records)
    palette_kind = _PALETTE_BY_SET.get(palette_set)
    if palette_kind is None:
        raise ValueError(f"unrecognized panel palette {sorted(palette_set)}")
    component_sizes = [record["component_sizes"] for record in records]
    secondary_objects = "none" if all(len(sizes) == 1 for sizes in component_sizes) else "singletons"
    return {
        "grid_h": len(grid),
        "panel_w": panel_width,
        "common_cells": int(records[0]["size"]),
        "common_pair": _common_pair_from_records(records),
        "palette_kind": palette_kind,
        "secondary_objects": secondary_objects,
    }


def _render_shape(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    normalized = _normalize(cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    output = full_grid(height, width, 0)
    for row, col in normalized:
        output[row][col] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    records = _largest_records(grid)
    signatures = [record["canonical"] for record in records]
    counts = Counter(signatures)
    common = next(signature for signature, count in counts.items() if count == 2)
    return _render_shape(common)


def _first_panel(grid) -> list[list[int]]:
    records = _largest_records(grid)
    return _render_shape(records[0]["canonical"])


def _repeated_cell_count_else_first_panel(grid) -> list[list[int]]:
    """Wrong rule retained from v1.4's distribution defect.

    If exactly two panel-largest objects share a cell count, select one of that
    pair; otherwise canonicalize panel 0.  It matches every canonical label and
    every old v1.4 ordinary draw, but the equal-size panel-0-distractor witness
    refutes it.
    """
    records = _largest_records(grid)
    sizes = [int(record["size"]) for record in records]
    size_counts = Counter(sizes)
    repeated_sizes = [size for size, count in size_counts.items() if count == 2]
    selected = sizes.index(repeated_sizes[0]) if len(repeated_sizes) == 1 else 0
    return _render_shape(records[selected]["canonical"])


def _panel_zero_distractor(grid) -> bool:
    try:
        if observe_overrides(grid)["common_pair"] != "1,2":
            return False
        truth = rule_mirror(grid)
        return all(rival(grid) != truth for rival in SEMANTIC_RIVALS.values())
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_panel": _first_panel,
    "repeated_cell_count_else_first_panel": _repeated_cell_count_else_first_panel,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"panel_zero_distractor": _panel_zero_distractor}
WITNESS_RIVALS = {
    "panel_zero_distractor": [
        "first_panel",
        "repeated_cell_count_else_first_panel",
    ]
}


def lesson_identifiable(demos, query):
    """Finite check against the declared plausible rivals."""
    query_input = query["input"]
    query_output = query.get("output")
    if query_output is None:
        query_output = rule_mirror(query_input)
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_input) != query_output:
                reasons.append(
                    f"declared rival fits demonstrations but changes query: {name}"
                )
    return reasons
