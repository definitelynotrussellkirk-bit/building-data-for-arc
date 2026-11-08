"""Generator for b46e718788e1 — keep only border-touching objects.

The authoritative rule is object-local: find every 4-connected monochrome
nonzero component and keep the complete component iff at least one of its
cells touches the outer grid border.  Fully interior components are erased.

The canonical examples leave two tempting shortcuts underdetermined: both
training outputs keep exactly one corner/top-touching object, and no canonical
color occurs in both a kept and an erased component.  The generated curriculum
therefore schedules edge-only/non-top border objects, scenes with two kept
objects, and disconnected same-colored kept/erased objects.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b46e718788e1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "9502d1357bdc"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find each 4-connected monochrome nonzero component. Keep the entire "
    "component exactly when at least one of its cells touches the outer grid "
    "border; replace every fully interior component with background 0. "
    "Four-example teaching windows include non-top and edge-only border "
    "objects, multiple kept components, and a repeated color split across a "
    "kept and erased component so position/connectivity—not color, count, or "
    "corner membership—identifies the rule."
)

INVARIANTS = [
    "background is 0",
    "nonzero objects are monochrome 4-connected components separated orthogonally by background",
    "every object has at least two cells",
    "at least one object touches the outer grid border and is kept",
    "at least one object is fully interior and is erased",
    "ordinary four-sample windows refute border-color, top-only, corner-only, and one-object shortcuts",
]

# Every public axis is exact and directly recoverable from the returned input.
# Shape, color, border side, and color reuse are deliberate nuisance variation,
# not pseudo-overrides.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus larger variants",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus larger variants",
        "valid": "5..11",
    },
    "border_objects": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "interior_objects": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_SIDES = ("top", "right", "bottom", "left")
# Two exact canonical profile anchors are intentionally present: 5x6 with
# three distinct nonzero colors (palette size 4), and 6x7 with four (size 5).
_SCHEDULE = (
    {"h": 5, "w": 6, "border": 1, "interior": 2, "side": "top", "corner": True, "reuse": False},
    {"h": 6, "w": 7, "border": 2, "interior": 2, "side": "right", "corner": True, "reuse": False},
    {"h": 7, "w": 8, "border": 1, "interior": 2, "side": "bottom", "corner": False, "reuse": True},
    {"h": 8, "w": 9, "border": 2, "interior": 1, "side": "left", "corner": False, "reuse": False},
)

# Small polyominoes keep canonical object scale while still varying topology.
_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1)),
)


@dataclass(frozen=True)
class _Object:
    color: int
    cells: frozenset[tuple[int, int]]
    touches_border: bool

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def touches_corner(self) -> bool:
        # Filled in by callers that know dimensions; kept for API symmetry only.
        return False


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


def _scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int, overrides: dict[str, Any]) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (scheduled,)))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-residue teaching schedule to the semantic gate."""
    del seed, difficulty
    return sample_index % EXAMPLES_NEEDED


SCHEDULE_PROFILES = tuple(range(EXAMPLES_NEEDED))


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
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
    if height < 5 or width < 5:
        errors.append("task grids must be at least 5 by 5")

    # The canonical manifold treats each colored shape as an isolated object.
    # Reject orthogonally touching different colors instead of letting a color
    # boundary masquerade as object separation.
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
    if len(components) < 2:
        errors.append("at least two nonzero objects are required")
    if any(obj.size < 2 for obj in components):
        errors.append("every object must contain at least two cells")
    border = [obj for obj in components if obj.touches_border]
    interior = [obj for obj in components if not obj.touches_border]
    if not border:
        errors.append("at least one object must touch the outer grid border")
    if not interior:
        errors.append("at least one object must be fully interior")
    return components, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural task grammar; accepts all canonical train/test inputs."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict manifold used by semantic coverage gates."""
    return self_check(grid)


def _touches_side(cells: set[tuple[int, int]] | frozenset[tuple[int, int]], side: str, h: int, w: int) -> bool:
    if side == "top":
        return any(row == 0 for row, _ in cells)
    if side == "bottom":
        return any(row == h - 1 for row, _ in cells)
    if side == "left":
        return any(col == 0 for _, col in cells)
    if side == "right":
        return any(col == w - 1 for _, col in cells)
    raise ValueError(f"unknown side: {side!r}")


def _contains_corner(cells: set[tuple[int, int]] | frozenset[tuple[int, int]], h: int, w: int) -> bool:
    return bool(set(cells) & {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)})


def _orthogonal_guard(cells: set[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
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
    primary_side: str | None,
    require_corner: bool | None,
    shape_order: tuple[int, ...],
) -> list[set[tuple[int, int]]]:
    placements: list[set[tuple[int, int]]] = []
    for shape_index in shape_order:
        shape = _SHAPES[shape_index]
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
                if primary_side is not None and not _touches_side(cells, primary_side, h, w):
                    continue
                if require_corner is True and not _contains_corner(cells, h, w):
                    continue
                if require_corner is False and _contains_corner(cells, h, w):
                    continue
                placements.append(cells)
    return placements


def _layout_objects(
    h: int,
    w: int,
    border_count: int,
    interior_count: int,
    *,
    primary_side: str,
    require_corner: bool,
    rng,
    difficulty: str | None,
) -> tuple[list[set[tuple[int, int]]], list[set[tuple[int, int]]]]:
    # Hard favors larger shapes, easy favors canonical-size dominoes/triominoes,
    # but every band retains smaller fallbacks so exact dimension overrides are
    # always satisfiable, including the 5x5 boundary.
    indices = list(range(len(_SHAPES)))
    if difficulty == "hard":
        indices.sort(key=lambda i: (-len(_SHAPES[i]), i))
    elif difficulty == "easy":
        indices.sort(key=lambda i: (len(_SHAPES[i]), i))
    else:
        rng.shuffle(indices)
    shape_order = tuple(indices)

    specs: list[tuple[str, str | None, bool | None]] = [
        ("border", primary_side, require_corner)
    ]
    specs.extend(("border", None, None) for _ in range(border_count - 1))
    specs.extend(("interior", None, None) for _ in range(interior_count))

    pools: list[list[set[tuple[int, int]]]] = []
    for role, side, corner in specs:
        pool = _placements(
            h,
            w,
            role=role,
            primary_side=side,
            require_corner=corner,
            shape_order=shape_order,
        )
        rng.shuffle(pool)
        pools.append(pool)
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
        raise ValueError(
            f"could not place {border_count} border and {interior_count} interior objects in {h}x{w}"
        )
    border = [set(chosen[index]) for index in range(border_count)]
    interior = [
        set(chosen[border_count + index]) for index in range(interior_count)
    ]
    return border, interior


def _object_colors(ctx, total: int, *, reuse_cross_fate: bool) -> list[int]:
    if reuse_cross_fate:
        # One fewer distinct color; caller assigns colors[0] to the first kept
        # and first erased object.  This kills the canonical border-color
        # shortcut while keeping the two same-colored components disconnected.
        distinct = list(
            ctx.draw_distinct_colors("object_colors", n=total - 1, exclude={0})
        )
        return distinct
    return list(ctx.draw_distinct_colors("object_colors", n=total, exclude={0}))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; every declared override is exact."""
    _validate_call(difficulty, overrides)
    slot = _SCHEDULE[sample_index % len(_SCHEDULE)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, "grid_h", slot["h"], 5, 10, overrides)
    w = _scheduled_int(ctx, "grid_w", slot["w"], 5, 11, overrides)
    border_count = _scheduled_int(
        ctx, "border_objects", slot["border"], 1, 2, overrides
    )
    interior_count = _scheduled_int(
        ctx, "interior_objects", slot["interior"], 1, 2, overrides
    )

    rng = ctx.draw_rng(f"layout:{difficulty or 'all'}")
    border_cells, interior_cells = _layout_objects(
        h,
        w,
        border_count,
        interior_count,
        primary_side=slot["side"],
        require_corner=bool(slot["corner"]),
        rng=rng,
        difficulty=difficulty,
    )

    total = border_count + interior_count
    reuse = bool(slot["reuse"])
    colors = _object_colors(ctx, total, reuse_cross_fate=reuse)
    if reuse:
        # border[0] and interior[0] share a color; remaining objects get the
        # remaining distinct colors.
        border_colors = [colors[0]]
        next_index = 1
        for _ in range(1, border_count):
            border_colors.append(colors[next_index])
            next_index += 1
        interior_colors = [colors[0]]
        for _ in range(1, interior_count):
            interior_colors.append(colors[next_index])
            next_index += 1
    else:
        border_colors = colors[:border_count]
        interior_colors = colors[border_count:]

    grid = full_grid(h, w, 0)
    for cells, color in zip(border_cells, border_colors):
        for row, col in cells:
            grid[row][col] = color
    for cells, color in zip(interior_cells, interior_colors):
        for row, col in cells:
            grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid border-filter scene: " + "; ".join(errors))
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
    return grid


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact public axis from a lawful returned grid."""
    components, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe axes from malformed grid: " + "; ".join(errors))
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
        raise ValueError("rule_mirror expects a lawful scene: " + "; ".join(errors))
    output = full_grid(len(grid), len(grid[0]), 0)
    for obj in components:
        if obj.touches_border:
            for row, col in obj.cells:
                output[row][col] = obj.color
    return output


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
        "border_sides": sides,
        "edge_only_border_objects": sum(
            obj.touches_border and not _contains_corner(obj.cells, h, w)
            for obj in components
        ),
        "shared_color_cross_fate": bool(border_colors & interior_colors),
        "changed_cell_count": sum(obj.size for obj in interior),
    }


def _identity(grid):
    return [row[:] for row in grid]


def _erase_all(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _keep_if(grid, predicate: Callable[[_Object, int, int], bool]):
    components, errors = _analyze(grid)
    if errors:
        return [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for obj in components:
        if predicate(obj, h, w):
            for row, col in obj.cells:
                output[row][col] = obj.color
    return output


def _keep_top_touching(grid):
    return _keep_if(grid, lambda obj, h, w: _touches_side(obj.cells, "top", h, w))


def _keep_corner_touching(grid):
    return _keep_if(grid, lambda obj, h, w: _contains_corner(obj.cells, h, w))


def _keep_first_component(grid):
    components, errors = _analyze(grid)
    if errors or not components:
        return [row[:] for row in grid]
    first = components[0]
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, col in first.cells:
        output[row][col] = first.color
    return output


def _keep_border_colors_globally(grid):
    """Shortcut: choose COLORS seen on the border, not border-touching objects."""
    if _shape_errors(grid):
        return [row[:] for row in grid]
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


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "kept_and_erased_components": _kept_and_erased_witness,
    "non_top_border_component": _non_top_border_witness,
    "edge_only_border_component": _edge_only_border_witness,
    "multiple_kept_components": _multiple_kept_witness,
    "shared_color_opposite_fate": _shared_color_cross_fate_witness,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_keep_everything": _identity,
    "erase_everything": _erase_all,
    "keep_top_touching_only": _keep_top_touching,
    "keep_corner_touching_only": _keep_corner_touching,
    "keep_one_reading_order_component": _keep_first_component,
    "keep_every_component_of_a_border_color": _keep_border_colors_globally,
}

WITNESS_RIVALS = {
    "kept_and_erased_components": ["identity_keep_everything", "erase_everything"],
    "non_top_border_component": ["keep_top_touching_only"],
    "edge_only_border_component": ["keep_corner_touching_only"],
    "multiple_kept_components": ["keep_one_reading_order_component"],
    "shared_color_opposite_fate": ["keep_every_component_of_a_border_color"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All canonical objects use unique colors, so this globally color-based
    # shortcut agrees with every canonical pair even though it is not the rule.
    "keep_every_component_of_a_border_color": _keep_border_colors_globally,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits demos but changes the query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the border-object rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Named malformed scenes that structural self_check must reject."""
    no_objects = full_grid(6, 7, 0)

    all_border = full_grid(6, 7, 0)
    all_border[0][1] = all_border[0][2] = 2
    all_border[4][6] = all_border[5][6] = 4

    all_interior = full_grid(6, 7, 0)
    all_interior[2][2] = all_interior[2][3] = 3
    all_interior[4][4] = all_interior[4][5] = 6

    singleton_interior = full_grid(6, 7, 0)
    singleton_interior[0][1] = singleton_interior[0][2] = 2
    singleton_interior[3][3] = 4

    touching_colors = full_grid(6, 7, 0)
    touching_colors[0][1] = touching_colors[0][2] = 2
    touching_colors[2][2] = touching_colors[2][3] = 3
    touching_colors[3][3] = touching_colors[3][4] = 4  # color boundary at (2,3)/(3,3)

    return [
        ("all_background", no_objects),
        ("border_objects_only_identity_scene", all_border),
        ("interior_objects_only_erase_all_scene", all_interior),
        ("singleton_interior_object", singleton_interior),
        ("orthogonally_touching_different_colors", touching_colors),
    ]
