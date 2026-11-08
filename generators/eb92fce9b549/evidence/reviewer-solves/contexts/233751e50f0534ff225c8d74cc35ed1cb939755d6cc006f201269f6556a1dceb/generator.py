"""Task-local input sampler for eb92fce9b549.

The unchanged authority finds every 4-connected nonzero component, orders the
components by *bounding-box area* descending, then repaints them 2, 3, 4, ...
on a zero background.  This sampler keeps a canonical nested-frame family and
adds a constructive counterexample to the strongest public-demo shortcut:
ordering by cell count instead of bounding-box area.

Outputs are never generated here; the shared runner applies the Racket rule.
Independent Python oracles and long-run probes live under ``workspace/``.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb92fce9b549"
TASK_ID = GENERATOR_ID
RULE_HASH = "45c25a11961c"
VERSION = "3.0.0"
SUMMARY = (
    "A square zero-background grid contains 2..4 disconnected objects in one "
    "foreground color. Nested rectangular rings preserve the canonical visual "
    "family. Scattered examples contain a sparse 3x3-bbox object and a denser "
    "2x3-bbox object, so bbox-area ranking and cell-count ranking disagree. "
    "The authority recolors components by descending bbox area as 2,3,4,..."
)

INVARIANTS = [
    "the grid is square with side 7..24 and uses exactly one nonzero input color",
    "there are exactly 2..4 four-connected foreground components",
    "component bounding-box areas are unique, so the authority's ranking is unambiguous",
    "every default three-example window contains a bbox-vs-cell-count counterexample",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "canonical side length 7|9|11|13|15",
        "valid": "7..24",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-aware 2..4, adapted to an explicitly small ring grid",
        "valid": "2..4",
    },
    "layout": {
        "type": "str",
        "default": "sample-index schedule: rings, scattered, scattered",
        "valid": "rings|scattered",
    },
    "foreground_color": {
        "type": "int",
        "default": "uniform nonzero ARC color",
        "valid": "1..9",
    },
}

# A same-color ring family needs one blank moat between components. With n
# objects, the smallest outer square is 4*(n-1)+1. Every other advertised
# combination is constructive; partial overrides adapt unpinned axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"layout": "rings", "grid_size": size, "n_objects": count}
    for count in (3, 4)
    for size in range(7, 4 * (count - 1) + 1)
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SIZES = (7, 9, 11, 13, 15)
_LAYOUTS = ("rings", "scattered")

# Local 7x7 scattered curriculum. Bounding-box areas are 9, 6, 4, 2.
# Cell counts are 5, 6, 4, 2, so the first two swap under the shortcut.
_SCATTERED_COMPONENTS = (
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 4), (0, 5), (0, 6), (1, 4), (1, 5), (1, 6)),
    ((4, 0), (4, 1), (4, 2), (4, 3)),
    ((6, 5), (6, 6)),
)


def _ring_min_size(n_objects: int) -> int:
    return 4 * (n_objects - 1) + 1


def _incompatible(message: str, *axes: str) -> ValueError:
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)  # checker-recognized structured veto
    return error


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in ("grid_size", "n_objects", "foreground_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    layout = overrides.get("layout")
    if layout is not None and type(layout) is not str:
        raise ValueError(f"layout must be a string, not {type(layout).__name__}")

    ranges = {
        "grid_size": (7, 24),
        "n_objects": (2, 4),
        "foreground_color": (1, 9),
    }
    for name, (low, high) in ranges.items():
        value = overrides.get(name)
        if value is not None and not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")
    if layout is not None and layout not in _LAYOUTS:
        raise ValueError(f"layout={layout!r} not in {_LAYOUTS}")

    if layout == "rings" and overrides.get("grid_size") is not None and overrides.get("n_objects") is not None:
        size = overrides["grid_size"]
        count = overrides["n_objects"]
        if size < _ring_min_size(count):
            raise _incompatible(
                f"grid_size={size} cannot fit {count} same-color nested rings with a blank moat",
                "layout", "grid_size", "n_objects",
            )


def _difficulty_counts(difficulty) -> tuple[int, ...]:
    if difficulty == "easy":
        return (2, 2, 2, 3)
    if difficulty == "hard":
        return (3, 4, 4, 4)
    return (2, 2, 3, 3, 4)


def _difficulty_sizes(difficulty) -> tuple[int, ...]:
    if difficulty == "easy":
        return (7, 7, 9, 9, 11, 13, 15)
    if difficulty == "hard":
        return (7, 9, 11, 13, 13, 15, 15)
    return _CANONICAL_SIZES


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input grid with a fully observable exact API."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Any three consecutive samples contain at least two semantic witnesses.
    # When an unpinned layout would make two pinned numeric axes impossible,
    # choose the constructive scattered branch instead of discarding a request.
    scheduled_layout = "rings" if sample_index % 3 == 0 else "scattered"
    pinned_size = overrides.get("grid_size")
    pinned_count = overrides.get("n_objects")
    if (
        "layout" not in overrides
        and pinned_size is not None
        and pinned_count is not None
        and pinned_size < _ring_min_size(pinned_count)
    ):
        scheduled_layout = "scattered"
    layout_options = _LAYOUTS if "layout" in overrides else (scheduled_layout,)
    layout = ctx.draw_choice("layout", layout_options)

    if "n_objects" in overrides:
        n_objects = ctx.draw_int("n_objects", 2, 4)
    else:
        count_options = _difficulty_counts(difficulty)
        if layout == "rings" and pinned_size is not None:
            feasible_counts = tuple(
                count for count in range(2, 5) if _ring_min_size(count) <= pinned_size
            )
            count_options = tuple(
                count for count in count_options if count in feasible_counts
            ) or feasible_counts
        if not count_options:
            raise RuntimeError("internal count schedule has no feasible option")
        n_objects = ctx.draw_choice("n_objects", count_options)

    if "grid_size" in overrides:
        grid_size = ctx.draw_int("grid_size", 7, 24)
    else:
        size_options = _difficulty_sizes(difficulty)
        if layout == "rings":
            size_options = tuple(size for size in size_options if size >= _ring_min_size(n_objects))
        if not size_options:
            raise RuntimeError("internal size schedule has no feasible option")
        grid_size = ctx.draw_choice("grid_size", size_options)

    if layout == "rings" and grid_size < _ring_min_size(n_objects):
        explicit = tuple(
            name for name in ("layout", "grid_size", "n_objects") if name in overrides
        )
        raise _incompatible(
            f"grid_size={grid_size} cannot fit n_objects={n_objects} in layout='rings'",
            *(explicit or ("layout", "grid_size", "n_objects")),
        )

    foreground_color = ctx.draw_int("foreground_color", 1, 9)
    if layout == "rings":
        return _draw_rings(ctx, grid_size, n_objects, foreground_color)
    return _draw_scattered(ctx, grid_size, n_objects, foreground_color)


def _draw_rings(ctx, size: int, n_objects: int, color: int) -> list[list[int]]:
    """Nested same-color rectangular perimeters separated by one blank moat."""
    minimum = _ring_min_size(n_objects)
    shape_rng = ctx.draw_rng("ring_shape")
    # Favor an inset-by-one canonical silhouette when it can still fit the
    # requested number of components, but retain rectangular/asymmetric cases.
    height_choices = list(range(minimum, size + 1))
    width_choices = list(range(minimum, size + 1))
    if size - 2 >= minimum:
        height_choices += [size - 2] * 3
        width_choices += [size - 2] * 3
    outer_h = shape_rng.choice(height_choices)
    outer_w = shape_rng.choice(width_choices)
    position_rng = ctx.draw_rng("ring_position")
    top = position_rng.randint(0, size - outer_h)
    left = position_rng.randint(0, size - outer_w)

    grid = full_grid(size, size, 0)
    for index in range(n_objects):
        inset = 2 * index
        r0, c0 = top + inset, left + inset
        r1 = top + outer_h - 1 - inset
        c1 = left + outer_w - 1 - inset
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if row in (r0, r1) or col in (c0, c1):
                    grid[row][col] = color
    return grid


def _transform_cell(row: int, col: int, transform: int) -> tuple[int, int]:
    """One of the eight D4 transforms of a coordinate in a 7x7 square."""
    if transform >= 4:
        col = 6 - col
        transform -= 4
    for _ in range(transform):
        row, col = col, 6 - row
    return row, col


def _draw_scattered(ctx, size: int, n_objects: int, color: int) -> list[list[int]]:
    """Construct the bbox-area-vs-cell-count teaching counterexample."""
    transform = ctx.draw_rng("scattered_transform").randrange(8)
    position_rng = ctx.draw_rng("scattered_position")
    top = position_rng.randint(0, size - 7)
    left = position_rng.randint(0, size - 7)
    grid = full_grid(size, size, 0)
    for cells in _SCATTERED_COMPONENTS[:n_objects]:
        for row, col in cells:
            rr, cc = _transform_cell(row, col, transform)
            grid[top + rr][left + cc] = color
    return grid


def _components(grid) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, tuple(sorted(cells))))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = _bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _rank_output(grid, *, by: str) -> list[list[int]]:
    comps = _components(grid)
    if by == "bbox":
        key = lambda item: (-_bbox_area(item[1]), _bbox(item[1]), item[1])
    elif by == "cells":
        key = lambda item: (-len(item[1]), -_bbox_area(item[1]), _bbox(item[1]), item[1])
    else:
        raise ValueError(f"unknown rank mode {by!r}")
    ordered = sorted(comps, key=key)
    out = full_grid(len(grid), len(grid[0]), 0)
    for rank, (_, cells) in enumerate(ordered, start=2):
        for row, col in cells:
            out[row][col] = rank
    return out


def _cell_count_rank(grid):
    """Plausible WRONG rule: order components by occupied-cell count."""
    return _rank_output(grid, by="cells")


def _is_perimeter(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    r0, c0, r1, c1 = _bbox(cells)
    expected = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }
    return cells == expected


def _is_nested_rings(grid) -> bool:
    comps = _components(grid)
    if len(comps) < 2 or not all(_is_perimeter(cells) for _, cells in comps):
        return False
    boxes = sorted(
        (_bbox(cells) for _, cells in comps),
        key=lambda box: -((box[2] - box[0] + 1) * (box[3] - box[1] + 1)),
    )
    return all(
        outer[0] + 1 < inner[0]
        and outer[1] + 1 < inner[1]
        and inner[2] + 1 < outer[2]
        and inner[3] + 1 < outer[3]
        for outer, inner in zip(boxes, boxes[1:])
    )


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact public axis from the returned pixels."""
    comps = _components(grid)
    colors = {color for color, _ in comps}
    if len(colors) != 1:
        raise ValueError(f"expected one foreground color, found {sorted(colors)}")
    if len(grid) != len(grid[0]):
        raise ValueError("expected a square grid")
    return {
        "grid_size": len(grid),
        "n_objects": len(comps),
        "layout": "rings" if _is_nested_rings(grid) else "scattered",
        "foreground_color": next(iter(colors)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler manifold and authority preconditions."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty square grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if height != width:
        errors.append(f"expected a square grid, got {height}x{width}")
    if not 7 <= height <= 24 or not 7 <= width <= 24:
        errors.append(f"grid dimensions {height}x{width} outside 7..24")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    comps = _components(grid)
    if not 2 <= len(comps) <= 4:
        errors.append(f"expected 2..4 foreground components, found {len(comps)}")
    colors = {color for color, _ in comps}
    if len(colors) != 1:
        errors.append(f"expected exactly one foreground color, found {sorted(colors)}")
    areas = [_bbox_area(cells) for _, cells in comps]
    if len(areas) != len(set(areas)):
        errors.append(f"component bbox areas must be unique, found {sorted(areas)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful examples in the declared task manifold, including both curricula."""
    return self_check(grid)


def _bbox_vs_cell_count(grid) -> bool:
    return self_check(grid) == [] and _rank_output(grid, by="bbox") != _cell_count_rank(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is identifiable when a demo refutes cell-count ranking."""
    del query
    for pair in demos:
        try:
            if _cell_count_rank(pair["input"]) != pair["output"]:
                return []
        except Exception as exc:
            return [f"could not score cell-count competitor: {type(exc).__name__}: {exc}"]
    return ["cell-count ranking still fits every demonstration"]


SEMANTIC_WITNESSES = {"bbox_vs_cell_count": _bbox_vs_cell_count}
SEMANTIC_RIVALS = {"cell_count_rank": _cell_count_rank}
WITNESS_RIVALS = {"bbox_vs_cell_count": ["cell_count_rank"]}
CANONICAL_SHORTCUTS = {"cell_count_rank": _cell_count_rank}
LESSON_COMPETITORS = {"cell_count_rank": _cell_count_rank}
