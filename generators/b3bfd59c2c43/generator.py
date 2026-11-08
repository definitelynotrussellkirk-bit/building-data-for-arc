"""Constructive input sampler for ARC task b3bfd59c2c43.

The canonical rule recolors the exposed 4-neighbor boundary of every nonzero
component to 8 while preserving cells that are surrounded on all four sides by
the component.  This sampler deliberately includes the canonical shape family
(squares, diamonds, corner-rounded squares, and three-cell-thick crosses) plus
some solid rectangles.  Every ordinary object therefore has both a boundary
and a nonempty core; whole-object recoloring is never an accidental solution.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b3bfd59c2c43"
TASK_ID = GENERATOR_ID
RULE_HASH = "28b8cf49f820"
VERSION = "2.2.0"
SUMMARY = (
    "Two or three separated monochrome components on background 0. Components "
    "are solid squares/rectangles, diamonds, rounded squares, or thick crosses; "
    "each has a nonempty interior. The rule recolors exactly the exposed outer "
    "4-neighbor layer to 8 and preserves the inner core color."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and input object colors are distinct members of 1..7",
    "exactly 2 or 3 pairwise separated 4-connected monochrome components",
    "every component is hole-free and contains at least one four-neighbor-surrounded core cell",
    "grid size and object count overrides are exact and recoverable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile weighted", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "canonical-profile weighted", "valid": "12..20"},
    "object_count": {"type": "int", "default": "usually 2, sometimes 3", "valid": "2..3"},
}
# The smallest legal 10x12 canvas constructively fits three 3x3 core-bearing
# objects separated by blank columns, so the full Cartesian override domain is valid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CANONICAL_PROFILES = ((11, 15), (12, 12), (13, 15))
_ALLOWED_COLORS = tuple(range(1, 8))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _neighbors4(r: int, c: int) -> tuple[tuple[int, int], ...]:
    return tuple((r + dr, c + dc) for dr, dc in _CARDINAL)


def _binary_components(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    """4-connected components of all nonzero cells, matching the Racket rule."""
    h, w = len(grid), len(grid[0])
    occupied = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[frozenset[tuple[int, int]]] = []
    while occupied:
        start = min(occupied)
        stack = [start]
        occupied.remove(start)
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in _neighbors4(r, c):
                if point in occupied:
                    occupied.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(frozenset(cells))
    return result


def _color_components(grid: list[list[int]]) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[tuple[int, frozenset[tuple[int, int]]]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        stack = [start]
        unseen.remove(start)
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in _neighbors4(r, c):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append((color, frozenset(cells)))
    return result


def _core_cells(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cell_set = frozenset(cells)
    return frozenset(
        (r, c)
        for r, c in cell_set
        if all(point in cell_set for point in _neighbors4(r, c))
    )


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cell_set = frozenset(cells)
    min_r = min(r for r, _ in cell_set)
    min_c = min(c for _, c in cell_set)
    return frozenset((r - min_r, c - min_c) for r, c in cell_set)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cell_set = tuple(cells)
    rows = [r for r, _ in cell_set]
    cols = [c for _, c in cell_set]
    return min(rows), min(cols), max(rows), max(cols)


def _has_hole(cells: Iterable[tuple[int, int]]) -> bool:
    """Whether a component encloses a zero cell inside its own bounding box."""
    cell_set = frozenset(cells)
    top, left, bottom, right = _bbox(cell_set)
    empty = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if (r, c) not in cell_set
    }
    frontier = [
        point
        for point in empty
        if point[0] in (top, bottom) or point[1] in (left, right)
    ]
    reachable = set(frontier)
    while frontier:
        r, c = frontier.pop()
        for point in _neighbors4(r, c):
            if point in empty and point not in reachable:
                reachable.add(point)
                frontier.append(point)
    return bool(empty - reachable)


def _filled_rectangle(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset((r, c) for r in range(height) for c in range(width))


def _diamond(radius: int) -> frozenset[tuple[int, int]]:
    size = 2 * radius + 1
    return frozenset(
        (r, c)
        for r in range(size)
        for c in range(size)
        if abs(r - radius) + abs(c - radius) <= radius
    )


def _rounded_square(size: int) -> frozenset[tuple[int, int]]:
    corners = {(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)}
    return frozenset(
        (r, c)
        for r in range(size)
        for c in range(size)
        if (r, c) not in corners
    )


def _thick_cross(size: int) -> frozenset[tuple[int, int]]:
    mid = size // 2
    return frozenset(
        (r, c)
        for r in range(size)
        for c in range(size)
        if abs(r - mid) <= 1 or abs(c - mid) <= 1
    )


def _notched_rectangle(height: int, width: int) -> frozenset[tuple[int, int]]:
    """A narrow core-bearing shape that refutes bounding-box perimeter."""
    cells = set(_filled_rectangle(height, width))
    if height >= 5:
        cells.remove((height // 2, 0))
    elif width >= 5:
        cells.remove((0, width // 2))
    else:  # Constructive slots always have one dimension at least five.
        raise ValueError("notched witness needs a 5x3 or 3x5 envelope")
    return frozenset(cells)


def _teaching_shape(max_h: int, max_w: int, rng) -> frozenset[tuple[int, int]]:
    """Return a fitting object whose true boundary differs from its bbox."""
    if min(max_h, max_w) >= 7:
        return rng.choice([_diamond(2), _diamond(3), _thick_cross(7)])
    if min(max_h, max_w) >= 5:
        return _diamond(2)
    if max_h >= 5 and max_w >= 3:
        return _notched_rectangle(5, min(5, max_w))
    if max_w >= 5 and max_h >= 3:
        return _notched_rectangle(min(5, max_h), 5)
    raise ValueError(f"slot {max_h}x{max_w} cannot fit a semantic teaching witness")


def _canonical_templates() -> frozenset[frozenset[tuple[int, int]]]:
    shapes: set[frozenset[tuple[int, int]]] = set()
    for size in (3, 5, 7):
        shapes.add(_filled_rectangle(size, size))
        shapes.add(_rounded_square(size))
        shapes.add(_diamond(size // 2))
        if size >= 5:
            shapes.add(_thick_cross(size))
    return frozenset(shapes)


_CANONICAL_TEMPLATES = _canonical_templates()


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {"grid_h": (10, 18), "grid_w": (12, 20), "object_count": (2, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")


def _partition(length: int, count: int, rng) -> list[tuple[int, int]]:
    """Partition an axis into `count` strips separated by one blank cell."""
    usable = length - (count - 1)
    base, remainder = divmod(usable, count)
    if base < 3:
        raise ValueError(f"cannot fit {count} core-bearing objects along axis length {length}")
    sizes = [base] * count
    order = list(range(count))
    rng.shuffle(order)
    for index in order[:remainder]:
        sizes[index] += 1
    result = []
    start = 0
    for size in sizes:
        result.append((start, size))
        start += size + 1
    return result


def _layout_slots(height: int, width: int, count: int, rng) -> list[tuple[int, int, int, int]]:
    feasible = []
    if (width - (count - 1)) // count >= 3:
        feasible.append("columns")
    if (height - (count - 1)) // count >= 3:
        feasible.append("rows")
    if not feasible:
        raise ValueError(f"{height}x{width} cannot fit {count} separated core-bearing objects")
    axis = rng.choice(feasible)
    if axis == "columns":
        return [(0, start, height, size) for start, size in _partition(width, count, rng)]
    return [(start, 0, size, width) for start, size in _partition(height, count, rng)]


def _pick_size(options: list[int], rng, difficulty: str | None) -> int:
    if not options:
        raise ValueError("shape has no fitting size")
    largest = max(options)
    smallest = min(options)
    weighted = list(options)
    if difficulty == "easy":
        weighted += [smallest] * 3
    elif difficulty == "hard":
        weighted += [largest] * 4
    else:
        weighted += [largest] * 2
    return rng.choice(weighted)


def _shape_for_slot(max_h: int, max_w: int, rng, difficulty: str | None) -> frozenset[tuple[int, int]]:
    odd_sizes = [size for size in (3, 5, 7) if size <= min(max_h, max_w)]
    families: list[str] = []
    if odd_sizes:
        # Canonical irregular families are intentionally common: they teach that
        # object boundary, not bounding-box border or whole-object recoloring, matters.
        families += ["square"] * 3
        families += ["diamond"] * 4
        families += ["rounded"] * 4
        if any(size >= 5 for size in odd_sizes):
            families += ["cross"] * (2 if difficulty == "easy" else 4)
    families += ["rectangle"] * 2
    family = rng.choice(families)

    if family == "square":
        size = _pick_size(odd_sizes, rng, difficulty)
        return _filled_rectangle(size, size)
    if family == "diamond":
        size = _pick_size(odd_sizes, rng, difficulty)
        return _diamond(size // 2)
    if family == "rounded":
        size = _pick_size(odd_sizes, rng, difficulty)
        return _rounded_square(size)
    if family == "cross":
        size = _pick_size([s for s in odd_sizes if s >= 5], rng, difficulty)
        return _thick_cross(size)

    heights = list(range(3, min(7, max_h) + 1))
    widths = list(range(3, min(7, max_w) + 1))
    rh = _pick_size(heights, rng, difficulty)
    rw = _pick_size(widths, rng, difficulty)
    return _filled_rectangle(rh, rw)


def _biased_offset(limit: int, rng) -> int:
    if limit <= 0:
        return 0
    # Edge placements are real canonical support, not accidental clipping.
    return rng.choice(list(range(limit + 1)) + [0, limit, 0, limit])


def _place_shape(
    grid: list[list[int]],
    shape: frozenset[tuple[int, int]],
    slot: tuple[int, int, int, int],
    color: int,
    rng,
) -> None:
    slot_r, slot_c, slot_h, slot_w = slot
    _, _, bottom, right = _bbox(shape)
    shape_h, shape_w = bottom + 1, right + 1
    if shape_h > slot_h or shape_w > slot_w:
        raise ValueError("selected shape does not fit its constructive slot")
    r0 = slot_r + _biased_offset(slot_h - shape_h, rng)
    c0 = slot_c + _biased_offset(slot_w - shape_w, rng)
    for dr, dc in shape:
        if grid[r0 + dr][c0 + dc] != 0:
            raise RuntimeError("constructive slots overlapped")
        grid[r0 + dr][c0 + dc] = color


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = ctx.draw_rng("canonical_canvas_profile").choice(_CANONICAL_PROFILES)
    # Repetition provides strong linked canonical-profile support while retaining
    # every advertised override value in every difficulty band.
    h = ctx.draw_choice("grid_h", [profile[0]] * 48 + list(range(10, 19)))
    w = ctx.draw_choice("grid_w", [profile[1]] * 48 + list(range(12, 21)))
    count = ctx.draw_choice("object_count", [2] * 18 + [3] * 2)

    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("layout")
    slots = _layout_slots(h, w, count, layout_rng)
    colors = ctx.draw_rng("colors").sample(list(_ALLOWED_COLORS), count)
    teaching_index = ctx.draw_rng("teaching_slot").randrange(count)
    for index, (slot, color) in enumerate(zip(slots, colors)):
        shape_rng = ctx.draw_rng(f"shape_{index}")
        # Every generated input includes an explicit counterexample to the
        # tempting "bounding-box perimeter" shortcut. Rotate that witness among
        # constructive strips so its semantic role is not tied to position.
        shape = (
            _teaching_shape(slot[2], slot[3], shape_rng)
            if index == teaching_index
            else _shape_for_slot(slot[2], slot[3], shape_rng, difficulty)
        )
        _place_shape(grid, shape, slot, color, shape_rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator violated its contract: " + "; ".join(errors))
    return grid


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_count": len(_color_components(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 7 for row in grid for value in row):
        return ["cells must be integer colors 0..7; input color 8 is reserved for output"]

    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 30 or not 8 <= width <= 30:
        errors.append(f"grid shape {height}x{width} outside the task's supported envelope")

    colors = {value for row in grid for value in row if value != 0}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2..3 object colors, found {len(colors)}")
    if all(value != 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    components = _color_components(grid)
    counts: dict[int, int] = {}
    for color, _ in components:
        counts[color] = counts.get(color, 0) + 1
    split = sorted(color for color, count in counts.items() if count != 1)
    if split:
        errors.append(f"each color must form exactly one connected component; split colors {split}")

    for color, cells in components:
        top, left, bottom, right = _bbox(cells)
        if bottom - top + 1 < 3 or right - left + 1 < 3:
            errors.append(f"color {color} component must span at least 3x3")
        if len(cells) < 5:
            errors.append(f"color {color} component is too small ({len(cells)} cells)")
        if not _core_cells(cells):
            errors.append(f"color {color} component has no preserved inner core")
        if _has_hole(cells):
            errors.append(f"color {color} component contains a hole")

    occupied = {
        (r, c): grid[r][c]
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    for (r, c), color in occupied.items():
        for dr, dc in _EIGHT:
            other = occupied.get((r + dr, c + dc))
            if other is not None and other != color:
                errors.append("different-colored components must have a one-cell separation")
                return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical canvas/profile and component shape family."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]))
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"canvas {profile} is outside the three canonical profiles")
    components = _color_components(grid)
    if len(components) != 2:
        errors.append(f"canonical lessons contain exactly two components, found {len(components)}")
    for color, cells in components:
        shape = _normalize(cells)
        if shape not in _CANONICAL_TEMPLATES:
            errors.append(f"color {color} shape is outside the canonical square/diamond/rounded/cross family")
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket boundary-peeling rule."""
    out = [list(row) for row in grid]
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    for r, c in occupied:
        if any(point not in occupied for point in _neighbors4(r, c)):
            out[r][c] = 8
    return out


def _whole_object_output(grid: list[list[int]]) -> list[list[int]]:
    return [[8 if value != 0 else 0 for value in row] for row in grid]


def _bbox_perimeter_output(grid: list[list[int]]) -> list[list[int]]:
    out = [list(row) for row in grid]
    for cells in _binary_components(grid):
        top, left, bottom, right = _bbox(cells)
        for r, c in cells:
            if r in (top, bottom) or c in (left, right):
                out[r][c] = 8
    return out


def _has_preserved_core(grid: list[list[int]]) -> bool:
    return self_check(grid) == [] and any(_core_cells(cells) for cells in _binary_components(grid))


def _has_irregular_core(grid: list[list[int]]) -> bool:
    if self_check(grid):
        return False
    # Radius-1 diamonds / 3x3 rounded squares are irregular but the incorrect
    # bounding-box-perimeter rule happens to agree on them.  A semantic witness
    # must certify an actual answer disagreement, not merely a visual feature.
    return _bbox_perimeter_output(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "preserved_core": _has_preserved_core,
    "irregular_component_boundary": _has_irregular_core,
}
SEMANTIC_RIVALS = {
    "recolor_entire_component": _whole_object_output,
    "bounding_box_perimeter_only": _bbox_perimeter_output,
}
WITNESS_RIVALS = {
    "preserved_core": ["recolor_entire_component"],
    "irregular_component_boundary": ["bounding_box_perimeter_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits every demo but changes query."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        input_grid = pair.get("input") if isinstance(pair, dict) else None
        output_grid = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"{role} input is outside the teaching grammar: {errors[0]}")
            continue
        if output_grid != rule_mirror(input_grid):
            reasons.append(f"{role} output disagrees with the pinned boundary rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons
