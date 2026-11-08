"""Sampler for dcf954423fbb: recolor border-touching blue components.

The selected Racket authority recolors every 4-connected color-1 component that
touches any of the four grid borders to color 2.  Inputs retain fully interior
blue components and one non-blue decoration component.  Ordinary draws include
structural counterexamples to geometric shortcuts and lesson schedules that
refute fixed-count shortcuts such as always recoloring the two or three nearest
components.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dcf954423fbb"
TASK_ID = GENERATOR_ID
RULE_HASH = "77b049629337"
VERSION = "2.1.0"
SUMMARY = (
    "Generate 3-6 separated blue components: horizontal- and vertical-edge "
    "examples, a distance-one interior decoy, optional deep/inter-edge "
    "components, one preserved decoration component, and count-varying lesson "
    "schedules. Recolor whole blue components iff they touch any grid border."
)

INVARIANTS = [
    "exactly 3..6 separated 4-connected color-1 components",
    "at least one left/right-only border component and one top/bottom border component",
    "at least one fully interior component exactly one cell from a border",
    "every border component extends inward, so whole-component recoloring is visible",
    "exactly one connected decoration component in one of colors 4,5,6,7,9",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule",
        "valid": "10..13",
    },
    "n_blobs": {
        "type": "int",
        "default": "difficulty-aware schedule",
        "valid": "3..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
EXAMPLES_NEEDED = 3

_CANONICAL_PROFILES = ((8, 10), (9, 12), (8, 11), (10, 13), (9, 12))
_DECORATION_COLORS = (4, 5, 6, 7, 9)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# A small connected-shape vocabulary.  All dihedral variants are derived below.
_BASE_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
)

Grid = list[list[int]]
Cell = tuple[int, int]
Component = tuple[Cell, ...]


def _normalize(cells: Iterable[Cell]) -> Component:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _dihedral_variants(shape: Sequence[Cell]) -> tuple[Component, ...]:
    variants: set[Component] = set()
    for reflected in (False, True):
        points = [(row, -col if reflected else col) for row, col in shape]
        for turns in range(4):
            transformed: list[Cell] = []
            for row, col in points:
                rr, cc = row, col
                for _ in range(turns):
                    rr, cc = cc, -rr
                transformed.append((rr, cc))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


_SHAPES = tuple(
    sorted(
        {variant for base in _BASE_SHAPES for variant in _dihedral_variants(base)},
        key=lambda cells: (len(cells), cells),
    )
)


def _border_sides(cells: Iterable[Cell], height: int, width: int) -> frozenset[str]:
    cells = tuple(cells)
    sides: set[str] = set()
    if any(row == 0 for row, _ in cells):
        sides.add("top")
    if any(row == height - 1 for row, _ in cells):
        sides.add("bottom")
    if any(col == 0 for _, col in cells):
        sides.add("left")
    if any(col == width - 1 for _, col in cells):
        sides.add("right")
    return frozenset(sides)


def _min_border_distance(cells: Iterable[Cell], height: int, width: int) -> int:
    return min(
        min(row, height - 1 - row, col, width - 1 - col)
        for row, col in cells
    )


def _role_matches(role: str, cells: Component, height: int, width: int) -> bool:
    sides = _border_sides(cells, height, width)
    if role in {"left", "right", "top", "bottom"}:
        # Side-specific components may not touch a corner or a second side, and
        # must visibly extend inward so the rule cannot be learned as a border-
        # cell recolor.
        return sides == {role} and any(
            0 < row < height - 1 and 0 < col < width - 1
            for row, col in cells
        )
    if role.startswith("near_"):
        if sides:
            return False
        side = role.removeprefix("near_")
        if side == "left":
            return min(col for _, col in cells) == 1
        if side == "right":
            return max(col for _, col in cells) == width - 2
        if side == "top":
            return min(row for row, _ in cells) == 1
        if side == "bottom":
            return max(row for row, _ in cells) == height - 2
        return False
    if role == "deep":
        return _min_border_distance(cells, height, width) >= 2
    raise ValueError(f"unknown component role {role!r}")


@lru_cache(maxsize=256)
def _role_candidates(height: int, width: int, role: str) -> tuple[Component, ...]:
    candidates: set[Component] = set()
    for shape in _SHAPES:
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        for top in range(height - shape_height + 1):
            for left in range(width - shape_width + 1):
                cells = tuple(sorted((top + row, left + col) for row, col in shape))
                if _role_matches(role, cells, height, width):
                    candidates.add(cells)
    return tuple(sorted(candidates))


def _separated(cells: Component, occupied: set[Cell]) -> bool:
    for row, col in cells:
        if (row, col) in occupied:
            return False
        if any((row + dr, col + dc) in occupied for dr, dc in _ORTHOGONAL):
            return False
    return True


def _component_roles(sample_index: int, n_blobs: int) -> tuple[str, ...]:
    # Any three consecutive schedule entries jointly cover all four sides.
    vertical, horizontal = (
        ("left", "top"),
        ("right", "bottom"),
        ("left", "bottom"),
        ("right", "top"),
    )[sample_index % 4]
    near_side = ("left", "right", "top", "bottom")[(sample_index // 2) % 4]
    roles = [vertical, horizontal, f"near_{near_side}"]
    if n_blobs >= 4:
        # The fourth blob is another true border component.  Together with the
        # blob-count schedules below, this varies the number of transformed
        # components inside every three-example lesson and refutes fixed-count
        # shortcuts ("always recolor two/three nearest components").
        roles.append("right" if vertical == "left" else "left")
    if n_blobs >= 5:
        roles.append("deep")
    if n_blobs >= 6:
        roles.append("bottom" if horizontal == "top" else "top")
    return tuple(roles)


def _place_components(ctx, height: int, width: int, roles: Sequence[str]) -> list[Component]:
    candidate_lists: list[list[Component]] = []
    for index, role in enumerate(roles):
        candidates = list(_role_candidates(height, width, role))
        ctx.draw_rng(f"component_role_{index}_{role}").shuffle(candidates)
        candidate_lists.append(candidates)

    chosen: list[Component] = []
    occupied: set[Cell] = set()

    def search(index: int) -> bool:
        if index == len(roles):
            return True
        for cells in candidate_lists[index]:
            if not _separated(cells, occupied):
                continue
            chosen.append(cells)
            occupied.update(cells)
            if search(index + 1):
                return True
            for cell in cells:
                occupied.remove(cell)
            chosen.pop()
        return False

    if not search(0):
        raise RuntimeError(
            f"constructive placement failed for {height}x{width} roles={tuple(roles)}"
        )
    return chosen


def _draw_exact_axis(ctx, overrides: dict[str, Any], label: str, default: int, lo: int, hi: int) -> int:
    # Default schedules provide guaranteed profile/teaching support.  Explicit
    # controls still traverse the entire advertised domain through draw_int.
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (default,)))


def _default_blob_count(sample_index: int, difficulty: Any) -> int:
    schedules = {
        # Every cyclic three-example window varies the number of true border
        # components: easy alternates 2/3; medium uses 2/3/3/2; hard uses
        # 3/3/4/4; the unbanded schedule uses 2/3/3/4.
        "easy": (3, 4, 3, 4),
        "medium": (3, 4, 5, 3),
        "hard": (4, 5, 6, 6),
        None: (3, 4, 5, 6),
    }
    schedule = schedules.get(difficulty, schedules[None])
    return schedule[sample_index % len(schedule)]


def _decoration_shape(ctx) -> Component:
    choices = (
        ((0, 0),),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    )
    return tuple(ctx.draw_choice("decoration_shape", choices))


def _place_decoration(grid: Grid, ctx) -> None:
    height, width = len(grid), len(grid[0])
    requested = _decoration_shape(ctx)
    # Prefer the selected connected shape; fall back through smaller connected
    # shapes only if a dense six-component scene leaves no placement.
    fallbacks = (requested, ((0, 0), (0, 1), (1, 0)), ((0, 0),))
    seen: set[Component] = set()
    for shape in fallbacks:
        normalized = _normalize(shape)
        if normalized in seen:
            continue
        seen.add(normalized)
        shape_height = max(row for row, _ in normalized) + 1
        shape_width = max(col for _, col in normalized) + 1
        candidates = [
            (top, left)
            for top in range(height - shape_height + 1)
            for left in range(width - shape_width + 1)
            if all(grid[top + row][left + col] == 0 for row, col in normalized)
        ]
        if not candidates:
            continue
        top, left = ctx.draw_rng("decoration_position").choice(candidates)
        color = ctx.draw_choice("decoration_color", _DECORATION_COLORS)
        for row, col in normalized:
            grid[top + row][left + col] = color
        return
    raise RuntimeError("no background cell available for decoration")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _CANONICAL_PROFILES[int(sample_index) % len(_CANONICAL_PROFILES)]
    height = _draw_exact_axis(ctx, overrides, "grid_h", profile[0], 8, 10)
    width = _draw_exact_axis(ctx, overrides, "grid_w", profile[1], 10, 13)
    n_blobs = _draw_exact_axis(
        ctx,
        overrides,
        "n_blobs",
        _default_blob_count(int(sample_index), difficulty),
        3,
        6,
    )

    grid = full_grid(height, width, 0)
    roles = _component_roles(int(sample_index), n_blobs)
    for component in _place_components(ctx, height, width, roles):
        for row, col in component:
            grid[row][col] = 1
    _place_decoration(grid, ctx)
    return grid


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty row sequence"
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return "every row must be a nonempty sequence"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid rows must have equal width"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid cells must be integer ARC colors 0..9 (not bools)"
    return None


def _components_of_color(grid: Sequence[Sequence[int]], color: int) -> list[Component]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[Component] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for dr, dc in _ORTHOGONAL:
                    neighbor = (rr + dr, cc + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(cells)))
    return components


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(_components_of_color(grid, 1)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared input grammar while accepting every canonical pair."""
    del difficulty, meta
    error = _grid_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 8 <= height <= 10:
        errors.append(f"grid height {height} outside 8..10")
    if not 10 <= width <= 13:
        errors.append(f"grid width {width} outside 10..13")

    palette = {value for row in grid for value in row}
    if 2 in palette:
        errors.append("input must not contain output color 2")
    if 0 not in palette or 1 not in palette:
        errors.append("input must contain background 0 and blue 1")
    decorations = palette - {0, 1}
    if len(decorations) != 1 or not decorations <= set(_DECORATION_COLORS):
        errors.append(
            "input must contain exactly one decoration color from 4,5,6,7,9"
        )

    blue_components = _components_of_color(grid, 1)
    if not 3 <= len(blue_components) <= 6:
        errors.append(f"expected 3..6 color-1 components; got {len(blue_components)}")
    if any(not 2 <= len(component) <= 4 for component in blue_components):
        errors.append("every color-1 component must contain 2..4 cells")
    border = [
        component
        for component in blue_components
        if _border_sides(component, height, width)
    ]
    interior = [
        component
        for component in blue_components
        if not _border_sides(component, height, width)
    ]
    if len(border) < 2:
        errors.append(f"expected at least two border-touching blue components; got {len(border)}")
    if not interior:
        errors.append("expected at least one fully interior blue component")

    if len(decorations) == 1:
        color = next(iter(decorations))
        decoration_components = _components_of_color(grid, color)
        count = sum(len(component) for component in decoration_components)
        if len(decoration_components) != 1 or not 1 <= count <= 5:
            errors.append("decoration must be one connected component of 1..5 cells")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _paint_components(grid: Sequence[Sequence[int]], predicate: Callable[[Component, int, int], bool]) -> Grid:
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for component in _components_of_color(grid, 1):
        if predicate(component, height, width):
            for row, col in component:
                output[row][col] = 2
    return output


def _apply_rule(grid):
    """Python audit mirror; the selected Racket program remains authority."""
    return _paint_components(
        grid,
        lambda component, height, width: bool(
            _border_sides(component, height, width)
        ),
    )


def _horizontal_edges_only(grid):
    return _paint_components(
        grid,
        lambda component, height, width: any(
            row in (0, height - 1) for row, _ in component
        ),
    )


def _near_border_recolors(grid):
    return _paint_components(
        grid,
        lambda component, height, width: _min_border_distance(
            component, height, width
        )
        <= 1,
    )


def _border_cells_only(grid):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 1 and (
                row in (0, height - 1) or col in (0, width - 1)
            ):
                output[row][col] = 2
    return output


def _all_blue_recolors(grid):
    return [[2 if value == 1 else value for value in row] for row in grid]


def _nearest_k_components(grid, count: int):
    """Plausible wrong lesson rule: recolor a fixed number nearest an edge."""
    height, width = len(grid), len(grid[0])
    components = _components_of_color(grid, 1)
    ranked = sorted(
        range(len(components)),
        key=lambda index: (
            _min_border_distance(components[index], height, width),
            components[index],
        ),
    )
    selected = set(ranked[:count])
    output = [list(row) for row in grid]
    for index, component in enumerate(components):
        if index in selected:
            for row, col in component:
                output[row][col] = 2
    return output


def _two_nearest_components(grid):
    return _nearest_k_components(grid, 2)


def _three_nearest_components(grid):
    return _nearest_k_components(grid, 3)


def _side_only_border_component(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        _border_sides(component, height, width) in ({"left"}, {"right"})
        for component in _components_of_color(grid, 1)
    )


def _near_border_interior_component(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        not _border_sides(component, height, width)
        and _min_border_distance(component, height, width) == 1
        for component in _components_of_color(grid, 1)
    )


def _border_component_extends_inward(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        _border_sides(component, height, width)
        and any(
            0 < row < height - 1 and 0 < col < width - 1
            for row, col in component
        )
        for component in _components_of_color(grid, 1)
    )


def _interior_component_preserved(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        not _border_sides(component, height, width)
        for component in _components_of_color(grid, 1)
    )


def _border_component_count(grid) -> int:
    height, width = len(grid), len(grid[0])
    return sum(
        bool(_border_sides(component, height, width))
        for component in _components_of_color(grid, 1)
    )


def _border_component_count_not_two(grid) -> bool:
    return _border_component_count(grid) != 2


def _border_component_count_not_three(grid) -> bool:
    return _border_component_count(grid) != 3


SEMANTIC_WITNESSES = {
    "side_only_border_component": _side_only_border_component,
    "near_border_interior_component": _near_border_interior_component,
    "border_component_extends_inward": _border_component_extends_inward,
    "interior_component_preserved": _interior_component_preserved,
    "border_component_count_not_two": _border_component_count_not_two,
    "border_component_count_not_three": _border_component_count_not_three,
}
SEMANTIC_RIVALS = {
    "horizontal_edges_only": _horizontal_edges_only,
    "near_border_recolors": _near_border_recolors,
    "border_cells_only": _border_cells_only,
    "all_blue_recolors": _all_blue_recolors,
    "two_nearest_components": _two_nearest_components,
    "three_nearest_components": _three_nearest_components,
}
WITNESS_RIVALS = {
    "side_only_border_component": ["horizontal_edges_only"],
    "near_border_interior_component": ["near_border_recolors"],
    "border_component_extends_inward": ["border_cells_only"],
    "interior_component_preserved": ["all_blue_recolors"],
    "border_component_count_not_two": ["two_nearest_components"],
    "border_component_count_not_three": ["three_nearest_components"],
}
CANONICAL_SHORTCUTS = {
    "near_border_recolors": _near_border_recolors,
    "three_nearest_components": _three_nearest_components,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _validate_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the declared grammar: {errors[0]}"]
    if pair["output"] != _apply_rule(pair["input"]):
        return [f"{label} output disagrees with border-component recoloring"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a materialized lesson if any declared plausible rival survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    reasons.extend(_validate_pair(query, "query"))
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
