"""Generator for arc_puzzle_bank_21_more:easy_b05.

Rule: move every nonzero input cell one row down and one column right on a
fresh zero-filled canvas of the same size. Cells whose destination is outside
the canvas are clipped.

The generated foreground consists of one to three separated, monochrome
components. At least one component contains an orthogonal corner, so ordinary
instances cannot collapse to a singleton, straight line, or filled rectangle.
The ``edge_mode`` axis explicitly covers both fully in-bounds translations and
mixed scenes where some cells clip while others still move.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a85b9271a0ee"
VERSION = "3.0.0"
TASK_ID = "a85b9271a0ee"
RULE_HASH = "966b5b4d8247"

SUMMARY = (
    "A 6..12 by 6..12 zero-background grid containing exactly 3..12 "
    "nonzero cells in 1..3 separated, monochrome components. Different "
    "components use distinct colors, and at least one component contains an "
    "orthogonal corner. The edge_mode axis is either in_bounds (every cell "
    "has a valid (+1,+1) destination) or mixed (at least one cell clips at "
    "the bottom/right edge while at least one cell moves). The output rule "
    "starts from a fresh zero canvas and shifts each nonzero cell by (+1,+1), "
    "dropping out-of-bounds destinations."
)

INVARIANTS = [
    "rectangular ARC grid with 0 background and dimensions 6..12",
    "exactly 3..12 nonzero cells",
    "1..3 four-connected foreground components",
    "each component is monochrome and component colors are distinct",
    "at least one foreground cell has perpendicular foreground neighbours",
    "foreground is not a filled bounding rectangle or a straight line",
    "at least one cell has an in-bounds (+1,+1) destination",
    "edge_mode is observable as in_bounds or mixed",
]

EDGE_MODES = ("in_bounds", "mixed")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "difficulty-biased", "valid": "6..12"},
    "n_cells": {"type": "int", "default": "difficulty-biased", "valid": "3..12"},
    "n_components": {
        "type": "int",
        "default": "difficulty-biased subject to n_cells",
        "valid": "1..3",
    },
    "edge_mode": {
        "type": "enum",
        "default": "keyed random",
        "valid": "|".join(EDGE_MODES),
    },
}

_NEIGHBOURS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _valid_cell(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9


def _foreground(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }


def _components(
    cells: Iterable[tuple[int, int]],
) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    out: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _NEIGHBOURS:
                neighbour = row + drow, col + dcol
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        out.append(component)
    return sorted(out, key=lambda component: min(component))


def _has_orthogonal_corner(cells: set[tuple[int, int]]) -> bool:
    for row, col in cells:
        vertical = ((row - 1, col), (row + 1, col))
        horizontal = ((row, col - 1), (row, col + 1))
        if any(v in cells for v in vertical) and any(h in cells for h in horizontal):
            return True
    return False


def _is_filled_bounding_rectangle(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    return len(cells) == height * width


def _edge_mode(cells: set[tuple[int, int]], height: int, width: int) -> str:
    clips = any(row == height - 1 or col == width - 1 for row, col in cells)
    return "mixed" if clips else "in_bounds"


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Return exact, grid-observable values for every declared axis."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    cells = _foreground(grid) if grid and width else set()
    return {
        "grid_h": height,
        "grid_w": width,
        "n_cells": len(cells),
        "n_components": len(_components(cells)),
        "edge_mode": _edge_mode(cells, height, width) if cells else "in_bounds",
    }


def self_check(
    grid: list[list[int]], *, difficulty=None, meta=None
) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding input scenes."""
    del difficulty
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(not _valid_cell(value) for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 12 or not 6 <= width <= 12:
        errors.append(f"expected dimensions in 6..12; got {height}x{width}")

    cells = _foreground(grid)
    if not 3 <= len(cells) <= 12:
        errors.append(f"expected 3..12 nonzero cells; got {len(cells)}")
    if not cells:
        return errors

    components = _components(cells)
    if not 1 <= len(components) <= 3:
        errors.append(f"expected 1..3 foreground components; got {len(components)}")

    component_colors: list[int] = []
    for index, component in enumerate(components):
        colors = {grid[row][col] for row, col in component}
        if len(colors) != 1:
            errors.append(
                f"component {index} must be monochrome; got colors {sorted(colors)}"
            )
        else:
            component_colors.append(next(iter(colors)))
    if len(component_colors) != len(set(component_colors)):
        errors.append("different components must use distinct nonzero colors")

    if not _has_orthogonal_corner(cells):
        errors.append("foreground must contain an orthogonal corner")
    if _is_filled_bounding_rectangle(cells):
        errors.append("foreground may not fill its bounding rectangle")

    movable = [(row, col) for row, col in cells if row < height - 1 and col < width - 1]
    if not movable:
        errors.append("at least one nonzero cell must have an in-bounds (+1,+1) target")

    observed = observe_overrides(grid)
    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(overrides, dict):
        for axis, requested in overrides.items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed {observed[axis]!r}"
                )
    return errors


def _requested_int(
    overrides: dict[str, object], name: str, low: int, high: int
) -> int | None:
    value = overrides.get(name)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} override must be an integer, not bool")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} override must be an integer") from exc
    if not low <= parsed <= high:
        raise ValueError(f"{name} override {parsed} outside [{low}, {high}]")
    return parsed


def _component_sizes(total: int, count: int, rng) -> list[int]:
    sizes = [3] + [1] * (count - 1)
    for _ in range(total - sum(sizes)):
        sizes[rng.randrange(count)] += 1
    return sizes


def _all_cells(height: int, width: int, *, avoid_clip_edge: bool) -> set[tuple[int, int]]:
    row_stop = height - 1 if avoid_clip_edge else height
    col_stop = width - 1 if avoid_clip_edge else width
    return {(row, col) for row in range(row_stop) for col in range(col_stop)}


def _l_candidates(
    height: int, width: int, *, must_touch_clip_edge: bool
) -> list[tuple[tuple[int, int], ...]]:
    candidates: list[tuple[tuple[int, int], ...]] = []
    for top in range(height - 1):
        for left in range(width - 1):
            square = (
                (top, left),
                (top + 1, left),
                (top, left + 1),
                (top + 1, left + 1),
            )
            for missing in range(4):
                shape = tuple(cell for index, cell in enumerate(square) if index != missing)
                touches = any(
                    row == height - 1 or col == width - 1 for row, col in shape
                )
                if touches == must_touch_clip_edge:
                    candidates.append(shape)
    return candidates


def _grow_component(
    component: set[tuple[int, int]],
    target_size: int,
    *,
    allowed: set[tuple[int, int]],
    blocked: set[tuple[int, int]],
    rng,
) -> bool:
    while len(component) < target_size:
        frontier: set[tuple[int, int]] = set()
        for row, col in component:
            for drow, dcol in _NEIGHBOURS:
                candidate = row + drow, col + dcol
                if candidate not in allowed or candidate in component or candidate in blocked:
                    continue
                if any(
                    (candidate[0] + dr, candidate[1] + dc) in blocked
                    for dr, dc in _NEIGHBOURS
                ):
                    continue
                frontier.add(candidate)
        if not frontier:
            return False
        component.add(rng.choice(sorted(frontier)))
    return True


def _seed_candidates(
    *,
    allowed: set[tuple[int, int]],
    occupied: set[tuple[int, int]],
    require_clip_edge: bool,
    height: int,
    width: int,
) -> list[tuple[int, int]]:
    candidates = []
    for cell in sorted(allowed - occupied):
        row, col = cell
        if require_clip_edge and row != height - 1 and col != width - 1:
            continue
        if any((row + dr, col + dc) in occupied for dr, dc in _NEIGHBOURS):
            continue
        candidates.append(cell)
    return candidates


def _attempt_layout(
    height: int,
    width: int,
    sizes: list[int],
    edge_mode: str,
    rng,
) -> list[set[tuple[int, int]]] | None:
    component_count = len(sizes)
    all_cells = _all_cells(height, width, avoid_clip_edge=False)
    interior = _all_cells(height, width, avoid_clip_edge=True)

    first_must_touch = edge_mode == "mixed" and component_count == 1
    first_candidates = _l_candidates(
        height, width, must_touch_clip_edge=first_must_touch
    )
    if not first_must_touch:
        first_candidates = [
            shape for shape in first_candidates if all(cell in interior for cell in shape)
        ]
    if not first_candidates:
        return None

    first = set(rng.choice(first_candidates))
    first_allowed = all_cells if first_must_touch else interior
    if not _grow_component(
        first,
        sizes[0],
        allowed=first_allowed,
        blocked=set(),
        rng=rng,
    ):
        return None

    components = [first]
    occupied = set(first)
    for index, target_size in enumerate(sizes[1:], start=1):
        require_clip_edge = edge_mode == "mixed" and index == 1
        seeds = _seed_candidates(
            allowed=all_cells if edge_mode == "mixed" else interior,
            occupied=occupied,
            require_clip_edge=require_clip_edge,
            height=height,
            width=width,
        )
        if not seeds:
            return None
        component = {rng.choice(seeds)}
        if not _grow_component(
            component,
            target_size,
            allowed=all_cells if edge_mode == "mixed" else interior,
            blocked=occupied,
            rng=rng,
        ):
            return None
        components.append(component)
        occupied.update(component)

    cells = set().union(*components)
    if len(cells) != sum(sizes):
        return None
    if len(_components(cells)) != component_count:
        return None
    if edge_mode == "in_bounds" and _edge_mode(cells, height, width) != "in_bounds":
        return None
    if edge_mode == "mixed" and _edge_mode(cells, height, width) != "mixed":
        return None
    if not any(row < height - 1 and col < width - 1 for row, col in cells):
        return None
    if not _has_orthogonal_corner(cells) or _is_filled_bounding_rectangle(cells):
        return None
    return components


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard") and not (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and 0.0 <= float(difficulty) <= 1.0
    ):
        raise ValueError("difficulty must be easy, medium, hard, None, or a number in [0,1]")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    requested_cells = _requested_int(overrides, "n_cells", 3, 12)
    requested_components = _requested_int(overrides, "n_components", 1, 3)
    minimum_cells = 3
    if requested_components is not None:
        minimum_cells = max(minimum_cells, requested_components + 2)
    if requested_cells is not None and requested_cells < minimum_cells:
        raise ValueError(
            f"n_cells={requested_cells} cannot realize n_components="
            f"{requested_components}; need at least {minimum_cells} cells"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 6, 12)
    width = ctx.draw_int_diff("grid_w", 6, 12)
    n_cells = ctx.draw_int_diff("n_cells", minimum_cells, 12)
    n_components = ctx.draw_int_diff("n_components", 1, min(3, n_cells - 2))
    edge_mode = ctx.draw_choice("edge_mode", EDGE_MODES)

    rng = ctx.draw_rng("layout")
    sizes = _component_sizes(n_cells, n_components, rng)
    components = None
    for _ in range(512):
        candidate_sizes = list(sizes)
        rng.shuffle(candidate_sizes)
        # Preserve the guaranteed corner-bearing component at index zero.
        if candidate_sizes[0] < 3:
            corner_index = next(
                (index for index, size in enumerate(candidate_sizes) if size >= 3),
                None,
            )
            if corner_index is None:
                continue
            candidate_sizes[0], candidate_sizes[corner_index] = (
                candidate_sizes[corner_index],
                candidate_sizes[0],
            )
        components = _attempt_layout(
            height, width, candidate_sizes, edge_mode, rng
        )
        if components is not None:
            break
    if components is None:
        raise RuntimeError(
            "failed to construct a lawful shift scene after 512 deterministic attempts"
        )

    colors = list(
        ctx.draw_distinct_colors("component_colors", n=n_components, exclude={0})
    )
    rng.shuffle(colors)
    grid = full_grid(height, width, 0)
    for component, color in zip(components, colors):
        for row, col in component:
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failure: {errors}")
    return grid
