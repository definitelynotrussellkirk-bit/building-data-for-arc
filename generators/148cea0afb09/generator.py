"""Generator for ARC task 148cea0afb09: rank an object by cell area and scale it 2x.

The top-left cell is a one-based rank.  After clearing that legend cell,
4-connected nonzero objects are sorted by their number of cells.  The ranked
object is cropped to its tight bounding box and every crop cell is replicated
into a 2x2 block.

Every generated instance is also a counterexample to the plausible but wrong
shortcut "rank by bounding-box area".  That distinction is intentional teaching
support; it does not replace the canonical Racket program as label authority.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, product
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "148cea0afb09"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "c113614858b9"

SUMMARY = (
    "Cell (0,0) contains a one-based rank R. Clear it, find the 2-3 "
    "4-connected nonzero objects, sort them by CELL COUNT ascending, choose "
    "the R-th object, crop it to its tight bbox, and scale the crop 2x2. "
    "Generated lessons deliberately distinguish cell-count rank from the "
    "canonical-fitting bbox-area shortcut."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0",
    "cell (0,0) is an isolated one-based rank in 1..number of objects",
    "there are 2-3 separated 4-connected objects",
    "all object cells share one color from 4..9",
    "object cell counts are strictly distinct",
    "the cell-count rank and bbox-area rank choose different objects",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10..11 easy / 10..12 medium / 11..12 hard",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "11..12 easy / 11..13 medium / 12..13 hard",
        "valid": "11..13",
    },
    "n_components": {
        "type": "int",
        "default": "keyed uniform 2..3 (forced to 3 for rank=3)",
        "valid": "2..3",
    },
    "rank": {
        "type": "int",
        "default": "keyed uniform 1..n_components",
        "valid": "1..3",
    },
    "component_color": {
        "type": "int",
        "default": "keyed uniform 4..9",
        "valid": "4..9",
    },
}

# rank=3 cannot coexist with only two components.  All other advertised tuples
# are exact and are recoverable through observe_overrides().
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_components": 2, "rank": 3},
]

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _reject_unknown_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


@lru_cache(maxsize=None)
def _fixed_polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All translation-normalized fixed polyominoes of a small cell count.

    Rotations and reflections remain distinct.  Every set conversion is sorted
    before it influences a keyed choice, so PYTHONHASHSEED cannot change pixels.
    """
    if type(size) is not int or size < 1:
        raise ValueError("polyomino size must be a positive integer")
    shapes: set[tuple[tuple[int, int], ...]] = {((0, 0),)}
    for target_size in range(2, size + 1):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in sorted(shapes):
            base = set(shape)
            for r, c in shape:
                for dr, dc in _DIR4:
                    grown = set(base)
                    grown.add((r + dr, c + dc))
                    if len(grown) == target_size:
                        expanded.add(_normalize(grown))
        shapes = expanded
    return tuple(sorted(shapes))


def _shape_extent(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


@lru_cache(maxsize=None)
def _shapes_with_bbox(
    size: int, area: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    result = tuple(
        shape
        for shape in _fixed_polyominoes(size)
        if _bbox_area(shape) == area and max(_shape_extent(shape)) <= 4
    )
    if not result:
        raise RuntimeError(f"no shape catalog entry for size={size}, bbox_area={area}")
    return result


# Exact compact-polyomino support used by the schedule enumerator.  Keeping
# this tiny table explicit avoids re-enumerating all size-9 fixed polyominoes in
# every isolated checker subprocess; _shapes_with_bbox still verifies each
# selected pair by materializing a real shape.
_BBOX_AREAS_BY_SIZE = {
    3: (3, 4),
    4: (4, 6),
    5: (6, 8, 9),
    6: (6, 8, 9, 12),
    7: (8, 9, 12, 16),
    8: (8, 9, 12, 16),
}


@lru_cache(maxsize=None)
def _shape_schedules(
    n_components: int, rank: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Varied cell-count/bbox schedules that refute bbox ranking at ``rank``.

    Cell counts are strictly increasing within every schedule.  Bbox areas are
    distinct, but their order places a different object at the requested rank.
    Enumerating many schedules prevents the rank marker from becoming an
    absolute-size lookup table in synthetic lessons.
    """
    if n_components not in (2, 3) or not 1 <= rank <= n_components:
        raise ValueError(
            f"unsupported component/rank combination: "
            f"n_components={n_components}, rank={rank}"
        )

    schedules: list[tuple[tuple[int, int], ...]] = []
    for sizes in combinations(sorted(_BBOX_AREAS_BY_SIZE), n_components):
        area_domains = tuple(_BBOX_AREAS_BY_SIZE[size] for size in sizes)
        for areas in product(*area_domains):
            if len(set(areas)) != n_components:
                continue
            bbox_order = sorted(range(n_components), key=lambda index: areas[index])
            if bbox_order[rank - 1] == rank - 1:
                continue
            schedules.append(tuple(zip(sizes, areas)))
    if not schedules:
        raise RuntimeError(
            f"no rival-refuting schedules for n_components={n_components}, rank={rank}"
        )
    return tuple(schedules)


def _translated(
    shape: Iterable[tuple[int, int]], origin: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    r0, c0 = origin
    return tuple((r0 + r, c0 + c) for r, c in shape)


def _separated(
    cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]
) -> bool:
    for r, c in cells:
        if (r, c) in occupied:
            return False
        if any((r + dr, c + dc) in occupied for dr, dc in _DIR4):
            return False
    return True


def _place_shapes(
    h: int,
    w: int,
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    rng,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Randomized deterministic backtracking with one-cell 4-neighbor separation."""
    occupied: set[tuple[int, int]] = {(0, 0)}
    placed: list[tuple[tuple[int, int], ...]] = []

    def search(index: int) -> bool:
        if index == len(shapes):
            return True
        shape = shapes[index]
        sh, sw = _shape_extent(shape)
        origins = [
            (r0, c0)
            for r0 in range(h - sh + 1)
            for c0 in range(w - sw + 1)
        ]
        rng.shuffle(origins)
        for origin in origins:
            cells = _translated(shape, origin)
            if not _separated(cells, occupied):
                continue
            occupied.update(cells)
            placed.append(cells)
            if search(index + 1):
                return True
            placed.pop()
            occupied.difference_update(cells)
        return False

    if not search(0):
        raise RuntimeError(
            f"could not place {len(shapes)} separated shapes on {h}x{w} canvas"
        )
    return tuple(placed)


def _dimension_bounds(difficulty) -> tuple[int, int, int, int]:
    if difficulty == "easy":
        return 10, 11, 11, 12
    if difficulty == "hard":
        return 11, 12, 12, 13
    return 10, 12, 11, 13


def _draw_strict_full_range_on_override(
    ctx, label: str, lo: int, hi: int, full_lo: int, full_hi: int
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, full_lo, full_hi)
    return ctx.draw_int_strict(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input; every advertised override is exact."""
    _reject_unknown_overrides(overrides)

    # Fail an impossible joint request before any random work and name both axes
    # for the strict override checker.
    if overrides.get("n_components") == 2 and overrides.get("rank") == 3:
        raise ValueError("incompatible overrides: n_components=2 and rank=3")

    # Validate rank early because it conditions the component-count draw.
    if "rank" in overrides:
        requested_rank = overrides["rank"]
        if type(requested_rank) is not int:
            raise TypeError("rank override must be an integer (not bool)")
        if not 1 <= requested_rank <= 3:
            raise ValueError("rank override must be in 1..3")
    else:
        requested_rank = None

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_lo, h_hi, w_lo, w_hi = _dimension_bounds(difficulty)
    h = _draw_strict_full_range_on_override(ctx, "grid_h", h_lo, h_hi, 10, 12)
    w = _draw_strict_full_range_on_override(ctx, "grid_w", w_lo, w_hi, 11, 13)
    n_lo = 3 if requested_rank == 3 and "n_components" not in overrides else 2
    n_components = ctx.draw_int_strict("n_components", n_lo, 3)
    rank = ctx.draw_int_strict("rank", 1, n_components)
    color = ctx.draw_int_strict("component_color", 4, 9)

    shape_schedule = ctx.draw_rng("shape_schedule").choice(
        _shape_schedules(n_components, rank)
    )
    shapes = tuple(
        ctx.draw_rng(f"shape_{index}").choice(_shapes_with_bbox(size, area))
        for index, (size, area) in enumerate(shape_schedule)
    )
    cells_by_component = _place_shapes(h, w, shapes, ctx.draw_rng("layout"))

    grid = full_grid(h, w, 0)
    grid[0][0] = rank
    for cells in cells_by_component:
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    if not _has_bbox_counterexample(grid):
        raise RuntimeError("internal generator error: bbox rival was not refuted")
    return grid


def _grid_shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer colors in 0..9 (bool is not a color)"
    return None


def _components(grid) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def _scene_components(grid) -> list[tuple[tuple[int, int], ...]]:
    work = [list(row) for row in grid]
    work[0][0] = 0
    return _components(work)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the documented task manifold; solid selected objects are lawful."""
    error = _grid_shape_error(grid)
    if error:
        return [error]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (10 <= h <= 12 and 11 <= w <= 13):
        errors.append(f"grid dimensions {h}x{w} outside 10..12 by 11..13")

    rank = grid[0][0]
    if any(
        0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
        for nr, nc in ((1, 0), (0, 1))
    ):
        errors.append("rank legend at (0,0) must be 4-neighbor isolated")

    comps = _scene_components(grid)
    if not 2 <= len(comps) <= 3:
        errors.append(f"expected 2-3 objects after clearing rank, found {len(comps)}")
    if type(rank) is not int or not 1 <= rank <= len(comps):
        errors.append(f"rank {rank!r} outside 1..{len(comps)}")

    sizes = [len(cells) for cells in comps]
    if any(size < 3 for size in sizes):
        errors.append(f"every object must contain at least 3 cells, got {sorted(sizes)}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"object cell counts must be strictly distinct, got {sorted(sizes)}")

    colors = {grid[r][c] for cells in comps for r, c in cells}
    if len(colors) != 1:
        errors.append(f"objects must share one color, found {sorted(colors)}")
    elif colors and next(iter(colors)) not in range(4, 10):
        errors.append(f"object color must be in 4..9, found {next(iter(colors))}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful source-bound task instances, not a generic visual-shape test."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid scene: " + "; ".join(errors))
    comps = _scene_components(grid)
    colors = {grid[r][c] for cells in comps for r, c in cells}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_components": len(comps),
        "rank": grid[0][0],
        "component_color": next(iter(colors)),
    }


def _crop_and_scale(
    grid, cells: Iterable[tuple[int, int]]
) -> list[list[int]]:
    cells = tuple(cells)
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    selected = set(cells)
    crop = [
        [grid[r][c] if (r, c) in selected else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    output: list[list[int]] = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        output.extend([doubled[:], doubled[:]])
    return output


def _ranked_output(
    grid, key: Callable[[tuple[tuple[int, int], ...]], int]
) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("ranked solver requires a lawful input: " + "; ".join(errors))
    comps = sorted(_scene_components(grid), key=key)
    return _crop_and_scale(grid, comps[grid[0][0] - 1])


def _cell_area_rank(grid) -> list[list[int]]:
    """Test/contract mirror only; canonical Racket remains label authority."""
    return _ranked_output(grid, len)


def _bbox_area_rank(grid) -> list[list[int]]:
    """RIVAL: incorrectly ranks objects by tight-bbox area."""
    return _ranked_output(grid, _bbox_area)


def _has_bbox_counterexample(grid) -> bool:
    try:
        return _cell_area_rank(grid) != _bbox_area_rank(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {"bbox_area_counterexample": _has_bbox_counterexample}
SEMANTIC_RIVALS = {"bbox_area_rank": _bbox_area_rank}
WITNESS_RIVALS = {"bbox_area_counterexample": ["bbox_area_rank"]}
CANONICAL_SHORTCUTS = {"bbox_area_rank": _bbox_area_rank}
LESSON_COMPETITORS = {"bbox_area_rank": _bbox_area_rank}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared plausible rival fits demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["lesson must provide a demo list and one query pair"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # noqa: BLE001 - semantic diagnostics must be loud
            reasons.append(f"{name} scoring failed: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(
                f"{name} fits all {len(demos)} demonstrations but changes the query"
            )
    return reasons
