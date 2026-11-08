"""Generator for ARC task 270af96a99b0: perimeter-sort and horizontal pack.

The selected rule extracts every same-color 4-connected nonzero object,
normalizes it to its tight bounding box, sorts components by
``(true exposed-edge perimeter, source top row, source left column)``, and
packs the crops left-to-right with one zero column between them.  Crops are
top-aligned and retain holes/background inside their bounding boxes.

Three scheduled shape profiles make the perimeter key and its source-position
tie-break visible while refuting tempting area, bounding-box-perimeter, color,
source-order, alignment, gap, and filled-bbox shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "270af96a99b0"
TASK_ID = "270af96a99b0"
VERSION = "3.0.0"
RULE_HASH = "cf57cf408f13"

SUMMARY = (
    "Place four isolated, distinctly colored polyominoes on a zero background. "
    "Extract each tight bbox crop, compute the object's true exposed-edge "
    "perimeter, and sort by (perimeter, source top row, source left column) "
    "ascending. Pack the normalized crops left-to-right with one zero column "
    "between them and top-align them. Scheduled profiles include equal-"
    "perimeter components with unequal areas and a concave object whose true "
    "perimeter differs from its bbox perimeter."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "background is 0 and every foreground value is an integer ARC color 1..9",
    "there are exactly four isolated 4-connected components in four distinct colors",
    "components have a one-cell Chebyshev moat and at least one crop is non-rectangular",
    "at least two components share a true perimeter so source-position tie-breaking matters",
    "row-major source order is not already canonical perimeter order",
    "crops are sorted by true exposed-edge perimeter, then source bbox position",
    "output crops are top-aligned with one zero separator column",
]

PALETTE_KINDS = ("low", "high", "mixed")
SHAPE_PROFILES = ("p8_tie", "p10_tie", "p12_tie")
SCHEDULE_PROFILES = SHAPE_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed uniform 8..14 with periodic canonical anchors",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed uniform 9..16 with periodic canonical anchors",
        "valid": "9..16",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice",
        "valid": "|".join(PALETTE_KINDS),
    },
    "shape_profile": {
        "type": "str",
        "default": "sample_index modulo three",
        "valid": "|".join(SHAPE_PROFILES),
    },
}

Shape = tuple[tuple[int, int], ...]

# Perimeters: singleton=4, vertical domino=6, square/line-3=8,
# rectangle-3x2/line-4=10, U/branched-6/line-5=12, and tree-6=14.
# Every scheduled source gallery is exactly nine columns wide after its three
# moat columns, so the canonical transformation always shrinks rather than
# widening the input.
_SINGLE: Shape = ((0, 0),)
_DOMINO_V: Shape = ((0, 0), (1, 0))
_LINE3_V: Shape = ((0, 0), (1, 0), (2, 0))
_LINE4_V: Shape = ((0, 0), (1, 0), (2, 0), (3, 0))
_LINE5_V: Shape = ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0))
_SQUARE: Shape = ((0, 0), (0, 1), (1, 0), (1, 1))
_RECT_3X2: Shape = (
    (0, 0), (0, 1),
    (1, 0), (1, 1),
    (2, 0), (2, 1),
)
_U3X2: Shape = ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1))
_TREE6_4X2: Shape = (
    (0, 0),
    (1, 0), (1, 1),
    (2, 1),
    (3, 0), (3, 1),
)
_P12_6_4X2: Shape = (
    (0, 0), (0, 1),
    (1, 0), (1, 1),
    (2, 0),
    (3, 0),
)

# Source order is the listed left-to-right order.  The boolean allows only
# dimension-preserving reflections/half-turns, never a width-changing rotation.
_PROFILE_ITEMS: dict[str, tuple[tuple[Shape, bool], ...]] = {
    # Source P: 12, 8, 10, 8. Equal-P components have areas 4 and 3 in
    # the opposite order from area sorting.
    "p8_tie": ((_U3X2, True), (_SQUARE, False), (_LINE4_V, False), (_LINE3_V, False)),
    # Source P: 12, 10, 4, 10. Equal-P components have areas 6 and 4.
    "p10_tie": ((_U3X2, True), (_RECT_3X2, False), (_SINGLE, False), (_LINE4_V, False)),
    # Source P: 14, 12, 6, 12. Equal-P components have areas 6 and 5.
    "p12_tie": ((_TREE6_4X2, True), (_P12_6_4X2, True), (_DOMINO_V, False), (_LINE5_V, False)),
}

_PROFILE_BY_PERIMETERS = {
    (8, 8, 10, 12): "p8_tie",
    (4, 10, 10, 12): "p10_tie",
    (6, 12, 12, 14): "p12_tie",
}


class _Object:
    __slots__ = ("cells", "color", "r1", "c1", "r2", "c2")

    def __init__(
        self,
        cells: tuple[tuple[int, int], ...],
        color: int,
        r1: int,
        c1: int,
        r2: int,
        c2: int,
    ) -> None:
        self.cells = cells
        self.color = color
        self.r1 = r1
        self.c1 = c1
        self.r2 = r2
        self.c2 = c2

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
    def perimeter(self) -> int:
        occupied = set(self.cells)
        return sum(
            (row + dr, column + dc) not in occupied
            for row, column in self.cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )

    @property
    def canonical_key(self) -> tuple[int, int, int]:
        return (self.perimeter, self.r1, self.c1)


def _normalize(shape: Any) -> Shape:
    cells = {(int(row), int(column)) for row, column in shape}
    if not cells:
        raise ValueError("shape must contain at least one cell")
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_column) for row, column in cells))


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(column for _, column in shape) + 1,
    )


def _dihedral_variants(shape: Shape) -> tuple[Shape, ...]:
    variants: set[Shape] = set()
    current = shape
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((row, -column) for row, column in current))
        current = _normalize((column, -row) for row, column in current)
    return tuple(sorted(variants))


def _extract_components(grid: list[list[int]]) -> list[_Object]:
    """Extract same-color 4-connected components in row-major source order."""
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


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    for name, lower, upper in (("grid_h", 8, 14), ("grid_w", 9, 16)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, got {value!r}")
        if not lower <= value <= upper:
            raise ValueError(f"{name}={value} outside {lower}..{upper}")
    for name, choices in (
        ("palette_kind", PALETTE_KINDS),
        ("shape_profile", SHAPE_PROFILES),
    ):
        if name not in overrides:
            continue
        value = overrides[name]
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string, got {value!r}")
        if value not in choices:
            raise ValueError(f"{name}={value!r} not in {choices!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return SHAPE_PROFILES[int(sample_index) % len(SHAPE_PROFILES)]


def _palette(kind: str, rng) -> list[int]:
    if kind == "low":
        chosen = sorted(rng.sample([1, 2, 3, 4, 5], 4))
    elif kind == "high":
        chosen = sorted(rng.sample([5, 6, 7, 8, 9], 4))
    elif kind == "mixed":
        chosen = sorted(rng.sample([1, 2, 3, 4], 2) + rng.sample([6, 7, 8, 9], 2))
    else:  # draw_choice and explicit validation make this unreachable.
        raise ValueError(f"unsupported palette_kind {kind!r}")
    # Deliberately unrelated to canonical perimeter order.  In source-slot
    # order this is low, high, mid-low, mid-high.
    return [chosen[0], chosen[3], chosen[1], chosen[2]]


def _choose_shape(shape: Shape, may_transform: bool, rng) -> Shape:
    if not may_transform:
        return shape
    dimensions = _shape_dims(shape)
    variants = [
        candidate
        for candidate in _dihedral_variants(shape)
        if _shape_dims(candidate) == dimensions
    ]
    return rng.choice(variants)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, fully observable perimeter-sorting lesson."""
    _validate_overrides(overrides)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    effective = dict(overrides)
    effective.setdefault("shape_profile", schedule_profile(seed, sample_index, difficulty))

    # Every fourth draw is a canonical-size anchor.  The three successive
    # anchor widths exactly cover the catalog's 8x9, 8x10, and 8x11 profiles.
    if int(sample_index) % 4 == 0:
        anchor = (int(sample_index) // 4) % 3
        effective.setdefault("grid_h", 8)
        effective.setdefault("grid_w", (9, 10, 11)[anchor])

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 8, 14)
    width = ctx.draw_int("grid_w", 9, 16)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    shape_profile = ctx.draw_choice("shape_profile", SHAPE_PROFILES)
    rng = ctx.draw_rng(f"layout_{band}")

    colors = _palette(palette_kind, rng)
    chosen_shapes = [
        _choose_shape(shape, may_transform, rng)
        for shape, may_transform in _PROFILE_ITEMS[shape_profile]
    ]
    packed_width = sum(_shape_dims(shape)[1] for shape in chosen_shapes) + 3
    if packed_width != 9:
        raise AssertionError(f"profile {shape_profile!r} has width {packed_width}, expected 9")

    # Distribute all spare columns among the two margins and three inter-crop
    # moats.  This preserves source order, keeps every pair Chebyshev-separated,
    # and adds layout diversity without changing crop geometry.
    spare_columns = [0, 0, 0, 0, 0]
    for _ in range(width - packed_width):
        spare_columns[rng.randrange(len(spare_columns))] += 1
    max_shape_height = max(_shape_dims(shape)[0] for shape in chosen_shapes)
    row0 = rng.randint(0, height - max_shape_height)
    column0 = spare_columns[0]

    grid = full_grid(height, width, 0)
    for index, (shape, color) in enumerate(zip(chosen_shapes, colors)):
        _, shape_width = _shape_dims(shape)
        for row, column in shape:
            grid[row0 + row][column0 + column] = color
        column0 += shape_width
        if index < len(chosen_shapes) - 1:
            column0 += 1 + spare_columns[index + 1]
    if column0 + spare_columns[-1] != width:
        raise AssertionError("horizontal gallery accounting drifted")

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid


def _palette_kind(colors: set[int]) -> str:
    if colors and max(colors) <= 5:
        return "low"
    if colors and min(colors) >= 5:
        return "high"
    if colors and min(colors) <= 4 and max(colors) >= 6:
        return "mixed"
    raise ValueError(f"palette {sorted(colors)} is outside the declared kinds")


def _shape_profile(components: list[_Object]) -> str:
    signature = tuple(sorted(obj.perimeter for obj in components))
    try:
        return _PROFILE_BY_PERIMETERS[signature]
    except KeyError as exc:
        raise ValueError(f"unrecognized perimeter profile {signature}") from exc


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a generated input."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    components = _extract_components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_kind": _palette_kind({obj.color for obj in components}),
        "shape_profile": _shape_profile(components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and scenes that hide the canonical mechanics."""
    del difficulty
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]

    height = len(grid)
    errors: list[str] = []
    if not (8 <= height <= 14 and 9 <= width <= 16):
        errors.append(f"grid dimensions {height}x{width} outside 8..14 by 9..16")
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{column_index})={value!r} is not an integer color 0..9"
                )
    if errors:
        return errors

    components = _extract_components(grid)
    if len(components) != 4:
        errors.append(f"expected exactly four foreground components, found {len(components)}")
    colors = [obj.color for obj in components]
    if len(set(colors)) != len(colors):
        errors.append(f"components must use four distinct colors, got {colors}")

    for index, obj in enumerate(components):
        if not 1 <= obj.area <= 8:
            errors.append(f"object {index} area {obj.area} outside 1..8")
        if obj.height > 5 or obj.width > 4:
            errors.append(f"object {index} bbox {obj.height}x{obj.width} exceeds 5x4")

    if components and all(obj.area == obj.height * obj.width for obj in components):
        errors.append("at least one object crop must contain background")
    perimeters = [obj.perimeter for obj in components]
    if len(perimeters) == len(set(perimeters)):
        errors.append("at least two components must share a true perimeter")
    source_keys = [obj.canonical_key for obj in components]
    if source_keys == sorted(source_keys):
        errors.append("source order already equals canonical perimeter order")
    if components and len({obj.height for obj in components}) < 2:
        errors.append("crop heights must vary so top alignment is observable")

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

    if meta and isinstance(meta, dict):
        requested = {
            key: value
            for key, value in meta.items()
            if key in AXES
        }
        if requested:
            try:
                actual = observe_overrides(grid)
            except ValueError:
                # Canonical catalog examples need not use a generated profile.
                actual = {"grid_h": height, "grid_w": width}
            for key, expected in requested.items():
                if key in actual and actual[key] != expected:
                    errors.append(
                        f"observable {key}={actual[key]!r}, expected {expected!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is deliberately a strict extension of catalog scenes."""
    return list(self_check(grid))


def _pack_components(
    components: list[_Object],
    *,
    gap: int = 1,
    alignment: str = "top",
    fill_bbox: bool = False,
) -> list[list[int]]:
    if not components:
        return []
    output_height = max(obj.height for obj in components)
    output_width = sum(obj.width for obj in components) + gap * (len(components) - 1)
    output = full_grid(output_height, output_width, 0)
    left = 0
    for obj in components:
        if alignment == "top":
            top = 0
        elif alignment == "bottom":
            top = output_height - obj.height
        else:
            raise ValueError(f"unknown alignment {alignment!r}")
        if fill_bbox:
            for row in range(obj.height):
                for column in range(obj.width):
                    output[top + row][left + column] = obj.color
        else:
            for row, column in obj.cells:
                output[top + row - obj.r1][left + column - obj.c1] = obj.color
        left += obj.width + gap
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Supplementary Python mirror; the selected Racket rule remains authority."""
    ordered = sorted(_extract_components(grid), key=lambda obj: obj.canonical_key)
    return _pack_components(ordered)


def _rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    components = _extract_components(grid)
    if name == "source_order":
        ordered = components
    elif name == "area_then_position":
        ordered = sorted(components, key=lambda obj: (obj.area, obj.r1, obj.c1))
    elif name == "bbox_perimeter_then_position":
        ordered = sorted(
            components,
            key=lambda obj: (2 * (obj.height + obj.width), obj.r1, obj.c1),
        )
    elif name == "color_order":
        ordered = sorted(components, key=lambda obj: obj.color)
    elif name == "descending_perimeter":
        ordered = sorted(components, key=lambda obj: obj.canonical_key, reverse=True)
    elif name == "bottom_aligned":
        ordered = sorted(components, key=lambda obj: obj.canonical_key)
        return _pack_components(ordered, alignment="bottom")
    elif name == "no_gap":
        ordered = sorted(components, key=lambda obj: obj.canonical_key)
        return _pack_components(ordered, gap=0)
    elif name == "fill_bbox":
        ordered = sorted(components, key=lambda obj: obj.canonical_key)
        return _pack_components(ordered, fill_bbox=True)
    else:
        raise ValueError(f"unknown rival {name!r}")
    return _pack_components(ordered)


def _rival_source_order(grid):
    return _rival_output(grid, "source_order")


def _rival_area_then_position(grid):
    return _rival_output(grid, "area_then_position")


def _rival_bbox_perimeter_then_position(grid):
    return _rival_output(grid, "bbox_perimeter_then_position")


def _rival_color_order(grid):
    return _rival_output(grid, "color_order")


def _rival_descending_perimeter(grid):
    return _rival_output(grid, "descending_perimeter")


def _rival_bottom_aligned(grid):
    return _rival_output(grid, "bottom_aligned")


def _rival_no_gap(grid):
    return _rival_output(grid, "no_gap")


def _rival_fill_bbox(grid):
    return _rival_output(grid, "fill_bbox")


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "source_order": _rival_source_order,
    "area_then_position": _rival_area_then_position,
    "bbox_perimeter_then_position": _rival_bbox_perimeter_then_position,
    "color_order": _rival_color_order,
    "descending_perimeter": _rival_descending_perimeter,
    "bottom_aligned": _rival_bottom_aligned,
    "no_gap": _rival_no_gap,
    "fill_bbox": _rival_fill_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "source_order",
        "area_then_position",
        "bbox_perimeter_then_position",
        "color_order",
    )
}


def _witness_rival(name: str, grid: Any) -> bool:
    return self_check(grid) == [] and _rival_output(grid, name) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "source_order": lambda grid: _witness_rival("source_order", grid),
    "area_then_position": lambda grid: _witness_rival("area_then_position", grid),
    "bbox_perimeter_then_position": lambda grid: _witness_rival("bbox_perimeter_then_position", grid),
    "color_order": lambda grid: _witness_rival("color_order", grid),
    "descending_perimeter": lambda grid: _witness_rival("descending_perimeter", grid),
    "bottom_aligned": lambda grid: _witness_rival("bottom_aligned", grid),
    "no_gap": lambda grid: _witness_rival("no_gap", grid),
    "fill_bbox": lambda grid: _witness_rival("fill_bbox", grid),
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when a declared alternative survives every demonstration."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    usable: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        input_errors = self_check(pair["input"])
        if input_errors:
            reasons.append(f"demo {index} input invalid: {input_errors[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        usable.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query output disagrees with the selected rule")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_all_demos = bool(usable) and all(
            competitor(pair["input"]) == pair["output"]
            for pair in usable
        )
        if fits_all_demos and competitor(query["input"]) != query_truth:
            reasons.append(
                f"rival {name!r} fits every demonstration but changes the query answer"
            )
    return reasons
