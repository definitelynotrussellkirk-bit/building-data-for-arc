"""Generator for ``medium_k10``: crop, lexicographically sort, and pack components.

The canonical rule extracts each 4-connected non-background object, sorts its
bbox crop by ``(cell_count, bbox_height, bbox_width, color)`` ascending, and
packs the crops left-to-right with one zero column between them.  Crops are
bottom-aligned in an output whose height is the tallest crop.

Each scheduled teaching profile now carries evidence for two sort keys.  Any
four demonstrations selected from five consecutive sample indices therefore
retain evidence for area, height, width, and color, even when the query position
is rotated.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "78143e5d7ed1"
TASK_ID = "78143e5d7ed1"
VERSION = "2.1.0"
RULE_HASH = "d87cff5947e7"

SUMMARY = (
    "Place three or four isolated, single-color polyominoes on a zero "
    "background.  Extract each tight bbox crop and sort the components by "
    "(cell count, bbox height, bbox width, color) ascending.  Pack the crops "
    "left-to-right with one zero column between them and bottom-align every "
    "crop to the tallest one.  Each profile demonstrates two sort keys, so "
    "every four-of-five query rotation covers area, height, width, and color."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

INVARIANTS = [
    "background is 0 and every foreground cell is an integer color 1..9",
    "there are exactly 3 or 4 isolated 4-connected single-color components",
    "components have a one-cell Chebyshev moat and distinct colors",
    "every object is a connected crop of 3..7 cells and at least one crop is non-rectangular",
    "the full (area, height, width, color) sort keys are unique",
    "sample_index modulo four schedules paired, rotation-safe sort-key evidence",
]

PALETTE_KINDS = ("low", "high", "mixed")
TIE_PROFILES = ("area", "height", "width", "color")

# Every declared axis is exact, keyed through GenCtx, accepted over its full
# stated range in every difficulty band, and recoverable by observe_overrides.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed uniform with periodic canonical-scale anchors",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed uniform with periodic canonical-scale anchors",
        "valid": "12..20",
    },
    "n_objs": {
        "type": "int",
        "default": "keyed uniform 3..4; canonical-scale anchors use 3",
        "valid": "3..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice",
        "valid": "|".join(PALETTE_KINDS),
    },
    "tie_profile": {
        "type": "str",
        "default": "sample_index modulo four",
        "valid": "|".join(TIE_PROFILES),
    },
}

Shape = tuple[tuple[int, int], ...]

# Each three-object prefix demonstrates the named key plus one complementary
# key.  The paired evidence sets are chosen so any three distinct scheduled
# profiles cover all four lexicographic keys:
#   area -> {area, height}; height -> {height, color};
#   width -> {area, width}; color -> {width, color}.
# A fourth, area-7 shape preserves an exact, recoverable profile signature.
_AREA_SHAPES: tuple[Shape, ...] = (
    # Same area, different heights (height evidence).
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    # Different area (area evidence).
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
)

_HEIGHT_SHAPES: tuple[Shape, ...] = (
    # Same area/height/width, so color decides their order.
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1)),
    # Same area, different height (height evidence).
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
)

_WIDTH_SHAPES: tuple[Shape, ...] = (
    # Same area/height, different widths (width evidence).
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    # Different area (area evidence).
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
)

_COLOR_SHAPES: tuple[Shape, ...] = (
    # Same area/height/width, so color decides their order.
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1)),
    # Same area/height, different width (width evidence).
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
)

_PROFILE_SHAPES = {
    "area": _AREA_SHAPES,
    "height": _HEIGHT_SHAPES,
    "width": _WIDTH_SHAPES,
    "color": _COLOR_SHAPES,
}



@dataclass(frozen=True)
class _Object:
    cells: tuple[tuple[int, int], ...]
    color: int
    r1: int
    c1: int
    r2: int
    c2: int

    @property
    def area(self) -> int:
        return len(self.cells)

    @property
    def height(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def width(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def key(self) -> tuple[int, int, int, int]:
        return (self.area, self.height, self.width, self.color)


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(column for _, column in shape) + 1,
    )


def _shape_signature(shapes: list[Shape] | tuple[Shape, ...]) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        sorted((len(shape), *_shape_dims(shape)) for shape in shapes)
    )


_PROFILE_SIGNATURES = {
    profile: {
        count: _shape_signature(shapes[:count])
        for count in (3, 4)
    }
    for profile, shapes in _PROFILE_SHAPES.items()
}


def _shape_key(shape: Shape, color: int) -> tuple[int, int, int, int]:
    height, width = _shape_dims(shape)
    return (len(shape), height, width, color)


def _extract_components(grid: list[list[int]]) -> list[_Object]:
    """Extract same-color 4-connected components in row-major order."""
    height = len(grid)
    width = len(grid[0])
    visited: set[tuple[int, int]] = set()
    components: list[_Object] = []
    for start_row in range(height):
        for start_column in range(width):
            color = grid[start_row][start_column]
            if color == 0 or (start_row, start_column) in visited:
                continue
            stack = [(start_row, start_column)]
            visited.add((start_row, start_column))
            cells: list[tuple[int, int]] = []
            while stack:
                row, column = stack.pop()
                cells.append((row, column))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, column + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in visited
                        and grid[nr][nc] == color
                    ):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            columns = [column for _, column in cells]
            components.append(
                _Object(
                    cells=tuple(sorted(cells)),
                    color=color,
                    r1=min(rows),
                    c1=min(columns),
                    r2=max(rows),
                    c2=max(columns),
                )
            )
    return components


def _palette(kind: str, n_components: int, rng) -> list[int]:
    low = [1, 2, 3, 4]
    high = [6, 7, 8, 9]
    if kind == "low":
        colors = rng.sample(low, n_components)
    elif kind == "high":
        colors = rng.sample(high, n_components)
    elif kind == "mixed":
        n_low = rng.randint(1, n_components - 1)
        colors = rng.sample(low, n_low) + rng.sample(high, n_components - n_low)
        rng.shuffle(colors)
    else:  # draw_choice prevents this; retain a fail-loud guard.
        raise ValueError(f"unsupported palette_kind {kind!r}")
    return colors


def _assign_profile_colors(
    profile: str,
    shapes: list[Shape],
    colors: list[int],
    rng,
) -> list[int]:
    """Order a palette so each omission rival is deterministically rebutted."""
    assigned: list[int | None] = [None] * len(shapes)
    available = sorted(colors)
    if profile == "area":
        # Reverse color against geometry, making color-first ordering false.
        geometry_order = sorted(
            range(len(shapes)),
            key=lambda index: (len(shapes[index]), *_shape_dims(shapes[index])),
        )
        for index, color in zip(geometry_order, reversed(available)):
            assigned[index] = color
    elif profile == "height":
        # The height-2 crop must precede the tied height-3 pair canonically,
        # while an omit-height rival sees its deliberately largest color.
        assigned[2] = available[-1]
    elif profile == "width":
        # Width-2 must precede width-3 canonically, but not when width is omitted.
        assigned[0], assigned[1] = available[-1], available[0]
    elif profile == "color":
        # The width-2 crop must precede the tied width-3 pair canonically, while
        # an omit-width rival sees its deliberately largest color.
        assigned[2] = available[-1]

    remaining_colors = [color for color in available if color not in assigned]
    rng.shuffle(remaining_colors)
    for index, value in enumerate(assigned):
        if value is None:
            assigned[index] = remaining_colors.pop()
    return [int(color) for color in assigned]


def _source_order_teaches_color(items: list[tuple[Shape, int]]) -> bool:
    groups: dict[tuple[int, int, int], list[int]] = {}
    for shape, color in items:
        groups.setdefault((len(shape), *_shape_dims(shape)), []).append(color)
    tied_groups = [colors for colors in groups.values() if len(colors) > 1]
    return all(colors != sorted(colors) for colors in tied_groups)


def _quadrants(height: int, width: int) -> list[tuple[int, int, int, int]]:
    """Four boxes separated by one full zero row and column."""
    gap_row = height // 2
    gap_column = width // 2
    return [
        (0, gap_row - 1, 0, gap_column - 1),
        (0, gap_row - 1, gap_column + 1, width - 1),
        (gap_row + 1, height - 1, 0, gap_column - 1),
        (gap_row + 1, height - 1, gap_column + 1, width - 1),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, shortcut-rebutting input grid."""
    if not isinstance(sample_index, int) or isinstance(sample_index, bool):
        raise TypeError("sample_index must be a non-negative integer")
    if sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    unknown_overrides = sorted(set(overrides) - set(AXES))
    if unknown_overrides:
        names = ", ".join(unknown_overrides)
        raise ValueError(f"unknown override key(s): {names}")

    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    # Each profile carries two complementary key witnesses.  Any four demos
    # drawn from five consecutive indices retain all four sort-key witnesses.
    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "tie_profile", TIE_PROFILES[sample_index % len(TIE_PROFILES)]
    )

    # One draw in five is pinned to the canonical dimension/object-count
    # envelope.  Caller overrides still take precedence.
    if sample_index % 5 == 0:
        canonical_profiles = ((9, 12), (10, 12), (10, 14), (11, 13))
        canonical_slot = (sample_index // 5) % len(canonical_profiles)
        canonical_height, canonical_width = canonical_profiles[canonical_slot]
        effective_overrides.setdefault("grid_h", canonical_height)
        effective_overrides.setdefault("grid_w", canonical_width)
        effective_overrides.setdefault("n_objs", 3)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int("grid_h", 9, 14)
    width = ctx.draw_int("grid_w", 12, 20)
    n_components = ctx.draw_int("n_objs", 3, 4)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    tie_profile = ctx.draw_choice("tie_profile", TIE_PROFILES)

    rng = ctx.draw_rng(f"layout_{band}")
    shapes = list(_PROFILE_SHAPES[tie_profile][:n_components])
    colors = _assign_profile_colors(
        tie_profile,
        shapes,
        _palette(palette_kind, n_components, rng),
        rng,
    )
    items = list(zip(shapes, colors))

    # Row-major source order must refute scan-order and, when geometry ties,
    # stable omission of the final color key.  At most 4! permutations exist.
    target_keys = sorted(_shape_key(shape, color) for shape, color in items)
    candidates: list[list[tuple[Shape, int]]] = []
    from itertools import permutations

    candidates = [list(candidate) for candidate in permutations(items)]
    rng.shuffle(candidates)
    for candidate in candidates:
        candidate_keys = [_shape_key(shape, color) for shape, color in candidate]
        if candidate_keys == target_keys:
            continue
        if tie_profile in {"height", "color"} and not _source_order_teaches_color(
            candidate
        ):
            continue
        items = candidate
        break
    else:  # The fixed shape banks make this unreachable; keep a fail-loud guard.
        raise RuntimeError(f"cannot construct teaching source order for {tie_profile!r}")

    quadrant_ids = sorted(rng.sample(range(4), n_components))
    regions = _quadrants(height, width)
    grid = full_grid(height, width, 0)
    for (shape, color), quadrant_id in zip(items, quadrant_ids):
        row_lo, row_hi, column_lo, column_hi = regions[quadrant_id]
        shape_h, shape_w = _shape_dims(shape)
        if row_hi - row_lo + 1 < shape_h or column_hi - column_lo + 1 < shape_w:
            raise ValueError(
                f"{height}x{width} quadrant cannot fit {shape_h}x{shape_w} shape"
            )
        # Pin both components in a horizontal band to its first row.  The
        # selected quadrant order is then exactly the row-major component
        # order, so the deliberate item permutation cannot be undone by
        # independent vertical jitter.
        row0 = row_lo
        column0 = rng.randint(column_lo, column_hi - shape_w + 1)
        paint_at(grid, row0, column0, shape, color)
    return grid


def _component_signature(
    components: list[_Object],
) -> tuple[tuple[int, int, int], ...]:
    return tuple(sorted((obj.area, obj.height, obj.width) for obj in components))


def _evidence_keys(components: list[_Object]) -> set[str]:
    """Return lexicographic key levels that are observable in this scene."""
    evidence: set[str] = set()
    if len({obj.area for obj in components}) > 1:
        evidence.add("area")
    if any(
        left.area == right.area and left.height != right.height
        for index, left in enumerate(components)
        for right in components[index + 1 :]
    ):
        evidence.add("height")
    if any(
        left.area == right.area
        and left.height == right.height
        and left.width != right.width
        for index, left in enumerate(components)
        for right in components[index + 1 :]
    ):
        evidence.add("width")
    if any(
        (left.area, left.height, left.width)
        == (right.area, right.height, right.width)
        and left.color != right.color
        for index, left in enumerate(components)
        for right in components[index + 1 :]
    ):
        evidence.add("color")
    return evidence


def _profile(components: list[_Object]) -> str:
    signature = _component_signature(components)
    count = len(components)
    for profile, by_count in _PROFILE_SIGNATURES.items():
        if by_count.get(count) == signature:
            return profile
    return "hybrid"


def _palette_kind(colors: set[int]) -> str:
    if colors and all(1 <= color <= 4 for color in colors):
        return "low"
    if colors and all(6 <= color <= 9 for color in colors):
        return "high"
    return "mixed"


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact AXES value from the returned grid."""
    components = _extract_components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objs": len(components),
        "palette_kind": _palette_kind({obj.color for obj in components}),
        "tie_profile": _profile(components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or structurally shortcut-hiding scenes."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]

    errors: list[str] = []
    height = len(grid)
    if not (9 <= height <= 14 and 12 <= width <= 20):
        errors.append(f"grid dimensions {height}x{width} outside 9..14 by 12..20")
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9):
                errors.append(
                    f"cell ({row_index},{column_index})={value!r} is not an integer color 0..9"
                )

    if errors:
        return errors
    components = _extract_components(grid)
    if not (3 <= len(components) <= 4):
        errors.append(f"expected 3..4 components, found {len(components)}")
    colors = [obj.color for obj in components]
    if len(set(colors)) != len(colors):
        errors.append(f"components must use distinct colors, got {colors}")

    for index, obj in enumerate(components):
        if not (3 <= obj.area <= 7):
            errors.append(f"object {index} area {obj.area} outside 3..7")
        if obj.height > 4 or obj.width > 4:
            errors.append(
                f"object {index} bbox {obj.height}x{obj.width} exceeds 4x4"
            )
    if components and all(obj.area == obj.height * obj.width for obj in components):
        errors.append("all components are filled rectangles; crop structure is hidden")

    keys = [obj.key for obj in components]
    if len(set(keys)) != len(keys):
        errors.append(f"full sort keys must be unique, got {keys}")

    owner = {
        cell: object_index
        for object_index, obj in enumerate(components)
        for cell in obj.cells
    }
    for (row, column), object_index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                neighbor = (row + dr, column + dc)
                if neighbor in owner and owner[neighbor] != object_index:
                    errors.append("components touch across the required one-cell moat")
                    return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical envelope, broader only in object texture."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    components = _extract_components(grid)
    height, width = len(grid), len(grid[0])
    if not (9 <= height <= 11):
        reasons.append(f"height {height} outside canonical 9..11")
    if not (12 <= width <= 14):
        reasons.append(f"width {width} outside canonical 12..14")
    if len(components) != 3:
        reasons.append(f"canonical lessons contain 3 components, found {len(components)}")
    return reasons


def _crop(obj: _Object, grid: list[list[int]]) -> list[list[int]]:
    return [
        list(row[obj.c1 : obj.c2 + 1])
        for row in grid[obj.r1 : obj.r2 + 1]
    ]


def _pack_components(
    grid: list[list[int]],
    ordered: list[_Object],
    *,
    alignment: str = "bottom",
    gap: int = 1,
    fill_bboxes: bool = False,
) -> list[list[int]]:
    crops = [
        full_grid(obj.height, obj.width, obj.color)
        if fill_bboxes
        else _crop(obj, grid)
        for obj in ordered
    ]
    output_height = max(len(crop) for crop in crops)
    output_width = sum(len(crop[0]) for crop in crops) + gap * (len(crops) - 1)
    output = full_grid(output_height, output_width, 0)
    column0 = 0
    for crop in crops:
        if alignment == "bottom":
            row0 = output_height - len(crop)
        elif alignment == "top":
            row0 = 0
        else:
            raise ValueError(f"unknown alignment {alignment!r}")
        for row, values in enumerate(crop):
            for column, value in enumerate(values):
                if value != 0:
                    output[row0 + row][column0 + column] = value
        column0 += len(crop[0]) + gap
    return output


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    components = _extract_components(grid)
    return _pack_components(grid, sorted(components, key=lambda obj: obj.key))


def _rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    components = _extract_components(grid)
    if name == "scan_order":
        ordered = components
    elif name == "area_only_stable":
        ordered = sorted(components, key=lambda obj: obj.area)
    elif name == "area_height":
        ordered = sorted(components, key=lambda obj: (obj.area, obj.height))
    elif name == "area_height_width" or name == "omit_color_key":
        ordered = sorted(components, key=lambda obj: (obj.area, obj.height, obj.width))
    elif name == "omit_area_key":
        ordered = sorted(components, key=lambda obj: (obj.height, obj.width, obj.color))
    elif name == "omit_height_key":
        ordered = sorted(components, key=lambda obj: (obj.area, obj.width, obj.color))
    elif name == "omit_width_key":
        ordered = sorted(components, key=lambda obj: (obj.area, obj.height, obj.color))
    elif name == "bbox_area":
        ordered = sorted(components, key=lambda obj: obj.height * obj.width)
    elif name == "color_first":
        ordered = sorted(components, key=lambda obj: (obj.color, obj.area, obj.height, obj.width))
    elif name == "descending":
        ordered = sorted(components, key=lambda obj: obj.key, reverse=True)
    elif name == "top_aligned":
        ordered = sorted(components, key=lambda obj: obj.key)
        return _pack_components(grid, ordered, alignment="top")
    elif name == "no_gap":
        ordered = sorted(components, key=lambda obj: obj.key)
        return _pack_components(grid, ordered, gap=0)
    elif name == "fill_bbox_crops":
        ordered = sorted(components, key=lambda obj: obj.key)
        return _pack_components(grid, ordered, fill_bboxes=True)
    else:
        raise ValueError(f"unknown rival {name!r}")
    return _pack_components(grid, ordered)


_RIVALS = (
    "scan_order",
    "area_only_stable",
    "area_height",
    "omit_color_key",
    "omit_area_key",
    "omit_height_key",
    "omit_width_key",
    "bbox_area",
    "color_first",
    "descending",
    "top_aligned",
    "no_gap",
    "fill_bbox_crops",
)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    name: (lambda grid, rival=name: _rival_output(grid, rival))
    for name in _RIVALS
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons admitting a named rival with a different query answer."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    demonstrated_keys: set[str] = set()
    for index, pair in enumerate(demos):
        input_grid = pair.get("input") if isinstance(pair, dict) else None
        output_grid = pair.get("output") if isinstance(pair, dict) else None
        input_errors = self_check(input_grid)
        if input_errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(input_errors)}")
            continue
        components = _extract_components(input_grid)
        demonstrated_keys.update(_evidence_keys(components))
        expected = _solve_grid(input_grid)
        if output_grid != expected:
            reasons.append(f"demo {index} output disagrees with the canonical pack rule")
    missing_keys = {"area", "height", "width", "color"} - demonstrated_keys
    if missing_keys:
        reasons.append(
            "demonstrations miss sort-key evidence: "
            + ", ".join(sorted(missing_keys))
        )

    query_input = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        reasons.append("query input invalid: " + "; ".join(query_errors))
        return reasons
    intended_query = _solve_grid(query_input)
    if query_output is not None and query_output != intended_query:
        reasons.append("query output disagrees with the canonical pack rule")

    for rival, competitor in LESSON_COMPETITORS.items():
        consistent = all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
            if isinstance(pair, dict) and "input" in pair and "output" in pair
        )
        if consistent and competitor(query_input) != intended_query:
            reasons.append(
                f"rival {rival!r} fits every demonstration but changes the query answer"
            )
    return reasons


def _valid(grid: Any) -> bool:
    return self_check(grid) == []


def _rival_differs(name: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: _valid(grid) and SEMANTIC_RIVALS[name](grid) != _solve_grid(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "area_primary_key": _rival_differs("omit_area_key"),
    "height_tiebreak": _rival_differs("omit_height_key"),
    "width_tiebreak": _rival_differs("omit_width_key"),
    "color_tiebreak": _rival_differs("omit_color_key"),
    "source_order_rebuttal": _rival_differs("scan_order"),
    "bottom_alignment_decisive": _rival_differs("top_aligned"),
    "bbox_crop_contains_background": _rival_differs("fill_bbox_crops"),
}

WITNESS_RIVALS = {
    "area_primary_key": ["omit_area_key"],
    "height_tiebreak": ["omit_height_key"],
    "width_tiebreak": ["omit_width_key"],
    "color_tiebreak": ["omit_color_key"],
    "source_order_rebuttal": ["scan_order"],
    "bottom_alignment_decisive": ["top_aligned"],
    "bbox_crop_contains_background": ["fill_bbox_crops"],
}
