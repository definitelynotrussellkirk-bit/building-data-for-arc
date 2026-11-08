"""Generator for d032febdce34 — keep only border-touching objects.

The selected rule is object-local: find every 4-connected monochrome nonzero
component and keep the complete component iff at least one of its cells touches
the outer grid border. Fully interior components are erased to background 0.

The three canonical examples leave several plausible shortcuts weakly tested:
colors are object-unique, object counts are small, and border objects often sit
at corners. The generated curriculum therefore schedules non-top edge-only
objects, two kept objects, opposite fates for disconnected same-colored
objects, and both kept-smaller and kept-larger size relations.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d032febdce34"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "9502d1357bdc"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find each 4-connected monochrome nonzero component. Keep the entire "
    "component exactly when at least one cell touches the outer grid border; "
    "erase every fully interior component to background 0. Four-example "
    "teaching windows include canonical 7x7 anchors, non-top edge-only border "
    "objects, multiple kept objects, opposite kept/erased fates for one color, "
    "and both size-order directions so color, count, corner, side, and size "
    "shortcuts do not identify the query answer."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "nonzero objects are monochrome 4-connected components separated orthogonally by background",
    "2-4 objects total, with 1-2 border-touching and 1-2 fully interior objects",
    "the output keeps every cell of every border-touching object and erases every interior object",
    "ordinary four-sample windows refute color-, count-, side-, corner-, border-cell-, and size-based shortcuts",
]

COUNTER_HYPOTHESES = [
    "keep every object",
    "erase every object",
    "keep only top-touching objects",
    "keep only corner-touching objects",
    "keep only one object in reading order",
    "keep every disconnected component whose color appears on the border",
    "keep only the largest or only the smallest objects",
    "keep only the cells physically lying on the border",
]

# Every public axis is exact, independently overrideable in every difficulty
# band, and directly recoverable from the returned input. Shape, side, color,
# size relation, and cross-component color reuse are deliberate nuisance
# variation rather than pseudo-overrides.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 7x7 anchors plus band-scaled variants",
        "valid": "5..12",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 7x7 anchors plus band-scaled variants",
        "valid": "5..12",
        "doc": "Exact returned grid width.",
    },
    "border_objects": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
        "doc": "Exact number of monochrome components touching the outer border.",
    },
    "interior_objects": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
        "doc": "Exact number of monochrome components fully inside the border.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_SIDES = ("top", "right", "bottom", "left")

# Every four consecutive sample indexes contain all decisive controls. The
# first two slots are exact canonical-profile anchors: 7x7 with three distinct
# nonzero colors, hence palette size four including background.
_SCHEDULE = (
    {
        "name": "canonical_border_smaller",
        "h": 7,
        "w": 7,
        "border": 2,
        "interior": 1,
        "side": "top",
        "corner": True,
        "reuse": False,
        "size_relation": "border_smaller",
        "require_inward": False,
    },
    {
        "name": "canonical_border_larger",
        "h": 7,
        "w": 7,
        "border": 1,
        "interior": 2,
        "side": "right",
        "corner": True,
        "reuse": False,
        "size_relation": "border_larger",
        "require_inward": True,
    },
    {
        "name": "bottom_edge_shared_color",
        "h": 8,
        "w": 9,
        "border": 1,
        "interior": 2,
        "side": "bottom",
        "corner": False,
        "reuse": True,
        "size_relation": "overlap",
        "require_inward": True,
    },
    {
        "name": "left_edge_multiple_kept",
        "h": 9,
        "w": 8,
        "border": 2,
        "interior": 1,
        "side": "left",
        "corner": False,
        "reuse": False,
        "size_relation": "overlap",
        "require_inward": True,
    },
)
SCHEDULE_PROFILES = tuple(slot["name"] for slot in _SCHEDULE)

# Fixed polyomino orientations by exact cell count. The generator normally uses
# sizes 1..4; self_check accepts canonical singletons and caps objects at six
# cells so mutation fixtures cannot smuggle in a large texture field.
_SHAPES_BY_SIZE: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (
        ((0, 0),),
    ),
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
    ),
}


@dataclass(frozen=True)
class _Object:
    color: int
    cells: frozenset[tuple[int, int]]
    touches_border: bool

    @property
    def size(self) -> int:
        return len(self.cells)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    for name in AXES:
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Expose the four-residue teaching schedule to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_dimensions(slot: dict[str, Any], difficulty: Any) -> tuple[int, int]:
    """Keep two canonical anchors while broadening the two control slots."""
    if slot["name"].startswith("canonical_"):
        return int(slot["h"]), int(slot["w"])
    delta = {"easy": -1, "medium": 0, "hard": 2}.get(difficulty, 0)
    return (
        max(5, min(12, int(slot["h"]) + delta)),
        max(5, min(12, int(slot["w"]) + delta)),
    )


def _scheduled_int(
    ctx,
    label: str,
    scheduled: int,
    lo: int,
    hi: int,
    overrides: dict[str, Any],
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    # A singleton choice still records exact keyed provenance without marking a
    # scheduler-selected value as a caller override.
    return int(ctx.draw_choice(label, (scheduled,)))


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _components_by_color(grid: list[list[int]]) -> list[_Object]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[_Object] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            touches = any(
                rr in (0, height - 1) or cc in (0, width - 1)
                for rr, cc in cells
            )
            components.append(_Object(color, frozenset(cells), touches))
    components.sort(key=lambda obj: (min(obj.cells), obj.color))
    return components


def _analyze(grid: Any) -> tuple[list[_Object], list[str]]:
    errors = _shape_errors(grid)
    if errors:
        return [], errors
    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 12 and 5 <= width <= 12):
        errors.append(f"task grids must be 5..12 by 5..12, got {height}x{width}")

    # The selected Racket authority reasons over monochrome components. Reject
    # orthogonally touching different colors so a color boundary cannot act as
    # an implicit separator or produce ambiguous object parsing.
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if (
                    nr < height
                    and nc < width
                    and grid[nr][nc] != 0
                    and grid[nr][nc] != color
                ):
                    errors.append("different-colored objects touch orthogonally")
                    return [], errors

    components = _components_by_color(grid)
    if not (2 <= len(components) <= 4):
        errors.append(f"expected 2-4 nonzero objects, found {len(components)}")
    if any(not (1 <= obj.size <= 6) for obj in components):
        errors.append("every object must contain 1..6 cells")
    border = [obj for obj in components if obj.touches_border]
    interior = [obj for obj in components if not obj.touches_border]
    if not (1 <= len(border) <= 2):
        errors.append(f"expected 1-2 border-touching objects, found {len(border)}")
    if not (1 <= len(interior) <= 2):
        errors.append(f"expected 1-2 fully interior objects, found {len(interior)}")
    return components, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Mutation-sensitive authority-compatible input grammar."""
    del difficulty
    _, errors = _analyze(grid)
    if errors:
        return sorted(set(errors))

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"{axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """The strict linked manifold is the structural border-object grammar."""
    return self_check(grid)


def _touches_side(
    cells: set[tuple[int, int]] | frozenset[tuple[int, int]],
    side: str,
    h: int,
    w: int,
) -> bool:
    if side == "top":
        return any(row == 0 for row, _ in cells)
    if side == "bottom":
        return any(row == h - 1 for row, _ in cells)
    if side == "left":
        return any(col == 0 for _, col in cells)
    if side == "right":
        return any(col == w - 1 for _, col in cells)
    raise ValueError(f"unknown side: {side!r}")


def _contains_corner(
    cells: set[tuple[int, int]] | frozenset[tuple[int, int]], h: int, w: int
) -> bool:
    return bool(
        set(cells) & {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    )


def _has_inward_cell(
    cells: set[tuple[int, int]] | frozenset[tuple[int, int]], h: int, w: int
) -> bool:
    return any(0 < row < h - 1 and 0 < col < w - 1 for row, col in cells)


def _orthogonal_guard(
    cells: set[tuple[int, int]], h: int, w: int
) -> set[tuple[int, int]]:
    guarded = set(cells)
    for row, col in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row + dr, col + dc
            if 0 <= rr < h and 0 <= cc < w:
                guarded.add((rr, cc))
    return guarded


def _placements(
    h: int,
    w: int,
    *,
    role: str,
    size: int,
    primary_side: str | None,
    require_corner: bool | None,
    require_inward: bool,
) -> list[set[tuple[int, int]]]:
    placements: list[set[tuple[int, int]]] = []
    for shape in _SHAPES_BY_SIZE[size]:
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        if shape_h > h or shape_w > w:
            continue
        for top in range(h - shape_h + 1):
            for left in range(w - shape_w + 1):
                cells = {(top + row, left + col) for row, col in shape}
                touches_border = any(
                    row in (0, h - 1) or col in (0, w - 1)
                    for row, col in cells
                )
                if role == "interior" and touches_border:
                    continue
                if role == "border" and not touches_border:
                    continue
                if primary_side is not None and not _touches_side(
                    cells, primary_side, h, w
                ):
                    continue
                if require_corner is True and not _contains_corner(cells, h, w):
                    continue
                if require_corner is False and _contains_corner(cells, h, w):
                    continue
                if require_inward and not _has_inward_cell(cells, h, w):
                    continue
                placements.append(cells)
    return placements


def _size_plan(
    relation: str,
    border_count: int,
    interior_count: int,
    h: int,
    w: int,
    difficulty: Any,
) -> tuple[list[int], list[int]]:
    tight = min(h, w) <= 5
    if relation == "border_smaller":
        border_size = 1 if tight else 2
        interior_size = 2 if tight else 4
    elif relation == "border_larger":
        border_size = 2 if tight else 4
        interior_size = 1 if tight else 2
    else:
        if tight:
            border_size = interior_size = 2
        elif difficulty == "hard":
            border_size = interior_size = 4
        else:
            border_size = interior_size = 3
    return [border_size] * border_count, [interior_size] * interior_count


def _search_layout(
    h: int,
    w: int,
    specs: list[dict[str, Any]],
    rng,
) -> list[set[tuple[int, int]]] | None:
    pools: list[list[set[tuple[int, int]]]] = []
    for spec in specs:
        pool = _placements(h, w, **spec)
        rng.shuffle(pool)
        pools.append(pool)
    if any(not pool for pool in pools):
        return None

    order = sorted(range(len(specs)), key=lambda index: len(pools[index]))
    chosen: list[set[tuple[int, int]] | None] = [None] * len(specs)

    def search(depth: int, reserved: set[tuple[int, int]]) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for cells in pools[index]:
            if cells & reserved:
                continue
            chosen[index] = cells
            if search(depth + 1, reserved | _orthogonal_guard(cells, h, w)):
                return True
        chosen[index] = None
        return False

    if not search(0, set()):
        return None
    return [set(cells) for cells in chosen if cells is not None]


def _layout_objects(
    h: int,
    w: int,
    border_count: int,
    interior_count: int,
    *,
    primary_side: str,
    require_corner: bool,
    require_inward: bool,
    size_relation: str,
    rng,
    difficulty: Any,
) -> tuple[list[set[tuple[int, int]]], list[set[tuple[int, int]]]]:
    border_sizes, interior_sizes = _size_plan(
        size_relation, border_count, interior_count, h, w, difficulty
    )
    specs: list[dict[str, Any]] = []
    for index, size in enumerate(border_sizes):
        specs.append(
            {
                "role": "border",
                "size": size,
                "primary_side": primary_side if index == 0 else None,
                "require_corner": require_corner if index == 0 else None,
                "require_inward": require_inward if index == 0 else False,
            }
        )
    for size in interior_sizes:
        specs.append(
            {
                "role": "interior",
                "size": size,
                "primary_side": None,
                "require_corner": None,
                "require_inward": False,
            }
        )

    chosen = _search_layout(h, w, specs, rng)
    if chosen is None:
        # Exact public overrides must remain satisfiable at the 5x5 / four-object
        # boundary. Side, size relation, and inward extension are internal
        # curriculum controls, so a tight explicit shape/count combination may
        # lawfully fall back to compact objects while preserving every exact
        # declared axis and both keep/erase branches.
        compact_specs: list[dict[str, Any]] = []
        for index in range(border_count):
            compact_specs.append(
                {
                    "role": "border",
                    "size": 1,
                    "primary_side": primary_side if index == 0 else None,
                    "require_corner": require_corner if index == 0 else None,
                    "require_inward": False,
                }
            )
        for _ in range(interior_count):
            compact_specs.append(
                {
                    "role": "interior",
                    "size": 1,
                    "primary_side": None,
                    "require_corner": None,
                    "require_inward": False,
                }
            )
        chosen = _search_layout(h, w, compact_specs, rng)
    if chosen is None:
        raise ValueError(
            f"could not place {border_count} border and {interior_count} "
            f"interior objects in {h}x{w}"
        )
    return chosen[:border_count], chosen[border_count:]


def _object_colors(ctx, total: int, *, reuse_cross_fate: bool) -> list[int]:
    distinct_count = total - 1 if reuse_cross_fate else total
    return list(
        ctx.draw_distinct_colors(
            "object_colors", n=distinct_count, exclude={0}
        )
    )


def _assign_colors(
    colors: list[int],
    border_count: int,
    interior_count: int,
    *,
    reuse_cross_fate: bool,
) -> tuple[list[int], list[int]]:
    if not reuse_cross_fate:
        return colors[:border_count], colors[border_count:]

    # The first kept and first erased object deliberately share a color. They
    # remain disconnected, so the selected component-local rule keeps one and
    # erases the other while the global-border-color shortcut keeps both.
    border_colors = [colors[0]]
    next_index = 1
    for _ in range(1, border_count):
        border_colors.append(colors[next_index])
        next_index += 1
    interior_colors = [colors[0]]
    for _ in range(1, interior_count):
        interior_colors.append(colors[next_index])
        next_index += 1
    return border_colors, interior_colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; every declared override is exact."""
    _validate_call(difficulty, overrides)
    slot = _SCHEDULE[sample_index % len(_SCHEDULE)]
    scheduled_h, scheduled_w = _scheduled_dimensions(slot, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, "grid_h", scheduled_h, 5, 12, overrides)
    w = _scheduled_int(ctx, "grid_w", scheduled_w, 5, 12, overrides)
    border_count = _scheduled_int(
        ctx, "border_objects", int(slot["border"]), 1, 2, overrides
    )
    interior_count = _scheduled_int(
        ctx, "interior_objects", int(slot["interior"]), 1, 2, overrides
    )

    rng = ctx.draw_rng(f"layout:{difficulty or 'all'}")
    border_cells, interior_cells = _layout_objects(
        h,
        w,
        border_count,
        interior_count,
        primary_side=str(slot["side"]),
        require_corner=bool(slot["corner"]),
        require_inward=bool(slot["require_inward"]),
        size_relation=str(slot["size_relation"]),
        rng=rng,
        difficulty=difficulty,
    )

    total = border_count + interior_count
    reuse = bool(slot["reuse"])
    colors = _object_colors(ctx, total, reuse_cross_fate=reuse)
    border_colors, interior_colors = _assign_colors(
        colors,
        border_count,
        interior_count,
        reuse_cross_fate=reuse,
    )

    grid = full_grid(h, w, 0)
    for cells, color in zip(border_cells, border_colors):
        for row, col in cells:
            grid[row][col] = color
    for cells, color in zip(interior_cells, interior_colors):
        for row, col in cells:
            grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(
            "constructed invalid border-filter scene: " + "; ".join(errors)
        )
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "border_objects": border_count,
        "interior_objects": interior_count,
    }
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost exact axes: expected {expected}, got {observed}"
        )

    # Ordinary schedule slots are semantic obligations, not probabilistic
    # hopes. Explicit public overrides may force compact fallback geometry, but
    # the default teaching lane must retain each slot's decisive witness.
    if not overrides:
        profile = semantic_profile(grid)
        relation = str(slot["size_relation"])
        if relation != "overlap" and profile["size_relation"] != relation:
            raise RuntimeError(
                f"scheduled {relation} relation was lost: {profile['size_relation']}"
            )
        if slot["reuse"] and not profile["shared_color_cross_fate"]:
            raise RuntimeError("scheduled shared-color opposite-fate witness was lost")
        if slot["require_inward"] and profile["inward_border_objects"] < 1:
            raise RuntimeError("scheduled inward-extending border object was lost")
    return grid


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact public axis from a lawful returned grid."""
    components, errors = _analyze(grid)
    if errors:
        raise ValueError(
            "cannot observe axes from malformed grid: " + "; ".join(errors)
        )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "border_objects": sum(obj.touches_border for obj in components),
        "interior_objects": sum(not obj.touches_border for obj in components),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for evidence only; Racket remains authority."""
    components, errors = _analyze(grid)
    if errors:
        raise ValueError(
            "rule_mirror expects a lawful scene: " + "; ".join(errors)
        )
    output = full_grid(len(grid), len(grid[0]), 0)
    for obj in components:
        if obj.touches_border:
            for row, col in obj.cells:
                output[row][col] = obj.color
    return output


def _size_relation(components: list[_Object]) -> str:
    border_sizes = [obj.size for obj in components if obj.touches_border]
    interior_sizes = [obj.size for obj in components if not obj.touches_border]
    if max(border_sizes) < min(interior_sizes):
        return "border_smaller"
    if min(border_sizes) > max(interior_sizes):
        return "border_larger"
    return "overlap"


def semantic_profile(grid: Any) -> dict[str, Any]:
    components, errors = _analyze(grid)
    if errors:
        return {"valid": False, "errors": errors}
    h, w = len(grid), len(grid[0])
    border = [obj for obj in components if obj.touches_border]
    interior = [obj for obj in components if not obj.touches_border]
    border_colors = {obj.color for obj in border}
    interior_colors = {obj.color for obj in interior}
    sides = {
        side: sum(_touches_side(obj.cells, side, h, w) for obj in border)
        for side in _SIDES
    }
    return {
        "valid": True,
        **observe_overrides(grid),
        "palette_size": len({value for row in grid for value in row}),
        "object_sizes": tuple(obj.size for obj in components),
        "border_sizes": tuple(obj.size for obj in border),
        "interior_sizes": tuple(obj.size for obj in interior),
        "size_relation": _size_relation(components),
        "border_sides": sides,
        "edge_only_border_objects": sum(
            obj.touches_border and not _contains_corner(obj.cells, h, w)
            for obj in components
        ),
        "inward_border_objects": sum(
            obj.touches_border and _has_inward_cell(obj.cells, h, w)
            for obj in components
        ),
        "singleton_objects": sum(obj.size == 1 for obj in components),
        "shared_color_cross_fate": bool(border_colors & interior_colors),
        "changed_cell_count": sum(obj.size for obj in interior),
        "kept_cell_count": sum(obj.size for obj in border),
    }


def _identity(grid):
    return [list(row) for row in grid]


def _erase_all(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _keep_if(grid, predicate: Callable[[_Object, int, int], bool]):
    components, errors = _analyze(grid)
    if errors:
        return [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for obj in components:
        if predicate(obj, h, w):
            for row, col in obj.cells:
                output[row][col] = obj.color
    return output


def _keep_top_touching(grid):
    return _keep_if(
        grid, lambda obj, h, w: _touches_side(obj.cells, "top", h, w)
    )


def _keep_corner_touching(grid):
    return _keep_if(grid, lambda obj, h, w: _contains_corner(obj.cells, h, w))


def _keep_first_component(grid):
    components, errors = _analyze(grid)
    if errors or not components:
        return [list(row) for row in grid]
    first = components[0]
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, col in first.cells:
        output[row][col] = first.color
    return output


def _keep_border_colors_globally(grid):
    """Shortcut: select COLORS seen on the border, not connected objects."""
    if _shape_errors(grid):
        return [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    border_colors = {
        grid[row][col]
        for row in range(h)
        for col in range(w)
        if (row in (0, h - 1) or col in (0, w - 1)) and grid[row][col] != 0
    }
    return [
        [value if value in border_colors else 0 for value in row]
        for row in grid
    ]


def _keep_extreme_size(grid, *, largest: bool):
    components, errors = _analyze(grid)
    if errors or not components:
        return [list(row) for row in grid]
    target = (
        max(obj.size for obj in components)
        if largest
        else min(obj.size for obj in components)
    )
    return _keep_if(grid, lambda obj, h, w: obj.size == target)


def _keep_largest(grid):
    return _keep_extreme_size(grid, largest=True)


def _keep_smallest(grid):
    return _keep_extreme_size(grid, largest=False)


def _keep_border_cells_only(grid):
    h, w = len(grid), len(grid[0])
    return [
        [
            value if (row in (0, h - 1) or col in (0, w - 1)) else 0
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


def _kept_and_erased_witness(grid) -> bool:
    components, errors = _analyze(grid)
    return not errors and any(obj.touches_border for obj in components) and any(
        not obj.touches_border for obj in components
    )


def _non_top_border_witness(grid) -> bool:
    components, errors = _analyze(grid)
    if errors:
        return False
    h, w = len(grid), len(grid[0])
    return any(
        obj.touches_border and not _touches_side(obj.cells, "top", h, w)
        for obj in components
    )


def _edge_only_border_witness(grid) -> bool:
    components, errors = _analyze(grid)
    if errors:
        return False
    h, w = len(grid), len(grid[0])
    return any(
        obj.touches_border and not _contains_corner(obj.cells, h, w)
        for obj in components
    )


def _multiple_kept_witness(grid) -> bool:
    components, errors = _analyze(grid)
    return not errors and sum(obj.touches_border for obj in components) >= 2


def _shared_color_cross_fate_witness(grid) -> bool:
    components, errors = _analyze(grid)
    if errors:
        return False
    border_colors = {obj.color for obj in components if obj.touches_border}
    interior_colors = {obj.color for obj in components if not obj.touches_border}
    return bool(border_colors & interior_colors)


def _border_smaller_witness(grid) -> bool:
    components, errors = _analyze(grid)
    return not errors and _size_relation(components) == "border_smaller"


def _border_larger_witness(grid) -> bool:
    components, errors = _analyze(grid)
    return not errors and _size_relation(components) == "border_larger"


def _inward_border_witness(grid) -> bool:
    components, errors = _analyze(grid)
    if errors:
        return False
    h, w = len(grid), len(grid[0])
    return any(
        obj.touches_border and _has_inward_cell(obj.cells, h, w)
        for obj in components
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "kept_and_erased_components": _kept_and_erased_witness,
    "non_top_border_component": _non_top_border_witness,
    "edge_only_border_component": _edge_only_border_witness,
    "multiple_kept_components": _multiple_kept_witness,
    "shared_color_opposite_fate": _shared_color_cross_fate_witness,
    "border_components_smaller_than_interior": _border_smaller_witness,
    "border_components_larger_than_interior": _border_larger_witness,
    "border_component_extends_inward": _inward_border_witness,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_keep_everything": _identity,
    "erase_everything": _erase_all,
    "keep_top_touching_only": _keep_top_touching,
    "keep_corner_touching_only": _keep_corner_touching,
    "keep_one_reading_order_component": _keep_first_component,
    "keep_every_component_of_a_border_color": _keep_border_colors_globally,
    "keep_largest_components": _keep_largest,
    "keep_smallest_components": _keep_smallest,
    "keep_only_cells_on_outer_border": _keep_border_cells_only,
}

WITNESS_RIVALS = {
    "kept_and_erased_components": [
        "identity_keep_everything",
        "erase_everything",
    ],
    "non_top_border_component": ["keep_top_touching_only"],
    "edge_only_border_component": ["keep_corner_touching_only"],
    "multiple_kept_components": ["keep_one_reading_order_component"],
    "shared_color_opposite_fate": [
        "keep_every_component_of_a_border_color"
    ],
    "border_components_smaller_than_interior": ["keep_largest_components"],
    "border_components_larger_than_interior": ["keep_smallest_components"],
    "border_component_extends_inward": ["keep_only_cells_on_outer_border"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every canonical nonzero color belongs to only one component, so selecting
    # a whole color whenever that color appears on the border reproduces all
    # three canonical pairs. Slot 2 supplies the decisive disconnected
    # same-color kept/erased counterexample.
    "keep_every_component_of_a_border_color": _keep_border_colors_globally,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require four demonstrations that eliminate every named rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"{role} is missing an input grid")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is invalid: {errors[0]}")
            continue
        if "output" in pair and pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the selected rule")

    killed = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            continue
        for name, competitor in LESSON_COMPETITORS.items():
            killed[name] = killed[name] or competitor(pair["input"]) != expected
    for name, was_killed in killed.items():
        if not was_killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def mutation_fixtures():
    """Named malformed scenes that structural self_check must reject."""
    no_objects = full_grid(7, 7, 0)

    all_border = full_grid(7, 7, 0)
    all_border[0][1] = all_border[0][2] = 2
    all_border[5][6] = all_border[6][6] = 4

    all_interior = full_grid(7, 7, 0)
    all_interior[2][2] = all_interior[2][3] = 3
    all_interior[4][4] = all_interior[4][5] = 6

    too_many = full_grid(7, 7, 0)
    for color, (row, col) in enumerate(
        ((0, 0), (0, 3), (2, 2), (4, 4), (6, 6)), start=1
    ):
        too_many[row][col] = color

    touching_colors = full_grid(7, 7, 0)
    touching_colors[0][1] = touching_colors[0][2] = 2
    touching_colors[3][2] = touching_colors[3][3] = 3
    touching_colors[4][3] = touching_colors[4][4] = 4

    oversized = full_grid(7, 7, 0)
    oversized[0][0] = oversized[0][1] = 2
    for col in range(7):
        oversized[3][col] = 5

    return [
        ("all_background", no_objects),
        ("border_objects_only_identity_scene", all_border),
        ("interior_objects_only_erase_all_scene", all_interior),
        ("five_object_scene", too_many),
        ("orthogonally_touching_different_colors", touching_colors),
        ("oversized_interior_texture", oversized),
    ]
