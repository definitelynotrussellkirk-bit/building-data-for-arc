"""Generator for ARC task ``1b9d8370e28b``.

The input has one straight split between cyan (8) and blue (1) background
regions.  Red (2) connected objects lie in both regions.  The rule compacts
each row's red cells independently inside its region: against the left edge
of a cyan region and against the right edge of a blue region.

The canonical examples contain only rectangular red objects.  That leaves a
plausible shortcut: slide each connected object rigidly to its directed edge.
Every generated scene therefore contains a connected non-rectangular object
whose row offsets make rigid sliding disagree with the row-count rule.
"""
from __future__ import annotations

from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "1b9d8370e28b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c5b820b4a73f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 9..15 grid is split horizontally or vertically into cyan(8) and "
    "blue(1) regions.  Three to five separated red(2) objects occur in both "
    "regions.  Preserve each row's red count per region, compacting left in "
    "cyan and right in blue.  A ragged connected object distinguishes this "
    "row-wise rule from rigidly sliding whole components."
)

INVARIANTS = [
    "one unambiguous straight split separates background colors 8 and 1",
    "red cells occur in both background regions",
    "the input contains three to five 4-connected red objects",
    "every generated input changes under the canonical row-compaction rule",
    "every generated input contains a ragged component that refutes rigid sliding",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed draw",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed draw",
        "valid": "9..15",
    },
    "split_axis": {
        "type": "str",
        "default": "keyed draw",
        "valid": "h|v",
    },
    "tl_color": {
        "type": "color",
        "default": "keyed draw",
        "valid": "1|8",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _other(color: int) -> int:
    return 1 if color == 8 else 8


def _background_grid(h: int, w: int, axis: str, split: int, first: int) -> list[list[int]]:
    second = _other(first)
    return [
        [
            first if (r < split if axis == "h" else c < split) else second
            for c in range(w)
        ]
        for r in range(h)
    ]


def _candidate_layouts(grid: list[list[int]]) -> list[tuple[str, int, int]]:
    """Return all straight 1/8 splits compatible with non-red cells."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    candidates: list[tuple[str, int, int]] = []
    for split in range(1, h):
        for first in (1, 8):
            second = _other(first)
            if all(
                value == 2 or value == (first if r < split else second)
                for r, row in enumerate(grid)
                for value in row
            ):
                candidates.append(("h", split, first))
    for split in range(1, w):
        for first in (1, 8):
            second = _other(first)
            if all(
                value == 2 or value == (first if c < split else second)
                for row in grid
                for c, value in enumerate(row)
            ):
                candidates.append(("v", split, first))
    return candidates


def _infer_layout(grid: list[list[int]]) -> tuple[str, int, int]:
    candidates = _candidate_layouts(grid)
    if len(candidates) != 1:
        raise ValueError(
            f"expected one unambiguous 1/8 split, found {len(candidates)}: {candidates}"
        )
    return candidates[0]


def _region_bounds(
    axis: str,
    split: int,
    h: int,
    w: int,
    region_index: int,
) -> tuple[int, int, int, int]:
    """Return half-open (r0, r1, c0, c1) bounds for one background region."""
    if axis == "h":
        return (0, split, 0, w) if region_index == 0 else (split, h, 0, w)
    return (0, h, 0, split) if region_index == 0 else (0, h, split, w)


def _region_index(axis: str, split: int, r: int, c: int) -> int:
    return int(r >= split) if axis == "h" else int(c >= split)


def _red_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def _is_filled_rectangle(component: set[tuple[int, int]]) -> bool:
    if not component:
        return False
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    expected = {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }
    return component == expected


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only by task-local tests and semantic probes."""
    axis, split, first = _infer_layout(grid)
    h, w = len(grid), len(grid[0])
    out = _background_grid(h, w, axis, split, first)
    for r in range(h):
        regions = ((0, w),) if axis == "h" else ((0, split), (split, w))
        for c0, c1 in regions:
            count = sum(grid[r][c] == 2 for c in range(c0, c1))
            if not count:
                continue
            background = out[r][c0]
            if background == 8:
                for c in range(c0, c0 + count):
                    out[r][c] = 2
            else:
                for c in range(c1 - count, c1):
                    out[r][c] = 2
    return out


def _rigid_components(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: slide each red component rigidly to its edge.

    Components closest to the destination edge move first; later components
    stop at either the edge or an already placed component.  Canonical red
    objects are rectangles on disjoint row ranges, so this rival reproduces all
    public outputs while preserving the decisive row offsets of ragged shapes.
    """
    axis, split, first = _infer_layout(grid)
    h, w = len(grid), len(grid[0])
    out = _background_grid(h, w, axis, split, first)
    by_region: dict[int, list[set[tuple[int, int]]]] = {0: [], 1: []}
    for component in _red_components(grid):
        memberships = {_region_index(axis, split, r, c) for r, c in component}
        if len(memberships) != 1:
            # This is outside the documented grammar; preserve it rather than
            # inventing how one rigid object should cross two directed regions.
            for r, c in component:
                out[r][c] = 2
            continue
        by_region[memberships.pop()].append(component)

    occupied: set[tuple[int, int]] = set()
    for region_index, components in by_region.items():
        r0, r1, c0, c1 = _region_bounds(axis, split, h, w, region_index)
        background = first if region_index == 0 else _other(first)
        direction = -1 if background == 8 else 1
        if direction < 0:
            components.sort(key=lambda comp: min(c for _, c in comp))
        else:
            components.sort(key=lambda comp: -max(c for _, c in comp))

        for component in components:
            shifted = set(component)
            while True:
                candidate = {(r, c + direction) for r, c in shifted}
                if any(not (r0 <= r < r1 and c0 <= c < c1) for r, c in candidate):
                    break
                if candidate & occupied:
                    break
                shifted = candidate
            occupied.update(shifted)
            for r, c in shifted:
                out[r][c] = 2
    return out


def _has_ragged_component(grid: list[list[int]]) -> bool:
    return (
        any(not _is_filled_rectangle(component) for component in _red_components(grid))
        and _rigid_components(grid) != rule_mirror(grid)
    )


def _touches_existing(
    candidate: set[tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> bool:
    if candidate & occupied:
        return True
    return any(
        (r + dr, c + dc) in occupied
        for r, c in candidate
        for dr, dc in _NEIGHBORS
    )


def _ragged_offsets(background: int, variant: int) -> set[tuple[int, int]]:
    """Return a connected row-offset witness aimed at the directed edge."""
    if background == 8:
        options = (
            {(0, 0), (0, 1), (1, 1)},
            {(0, 0), (0, 1), (1, 1), (1, 2)},
            {(0, 0), (0, 1), (1, 1), (2, 1)},
        )
    else:
        options = (
            {(0, 0), (0, 1), (1, 0)},
            {(0, 1), (0, 2), (1, 0), (1, 1)},
            {(0, 1), (1, 0), (1, 1), (2, 0)},
        )
    return set(options[variant % len(options)])


def _rectangle_offsets(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, c) for r in range(height) for c in range(width)}


def _translate(offsets: Iterable[tuple[int, int]], r0: int, c0: int) -> set[tuple[int, int]]:
    return {(r0 + dr, c0 + dc) for dr, dc in offsets}


def _place_component(
    *,
    offsets: set[tuple[int, int]],
    bounds: tuple[int, int, int, int],
    background: int,
    occupied: set[tuple[int, int]],
    rng,
) -> set[tuple[int, int]] | None:
    r0, r1, c0, c1 = bounds
    shape_h = max(r for r, _ in offsets) + 1
    shape_w = max(c for _, c in offsets) + 1
    row_starts = list(range(r0, r1 - shape_h + 1))
    col_starts = list(range(c0, c1 - shape_w + 1))

    # Every object must actually move under the official rule.  Keeping it one
    # cell away from its destination edge also leaves room for exact observation
    # of the underlying split.
    if background == 8:
        col_starts = [c for c in col_starts if c > c0]
    else:
        col_starts = [c for c in col_starts if c + shape_w < c1]

    positions = [(r, c) for r in row_starts for c in col_starts]
    rng.shuffle(positions)
    for rr, cc in positions:
        candidate = _translate(offsets, rr, cc)
        if not _touches_existing(candidate, occupied):
            return candidate
    return None


def _component_plan(component_count: int, ragged_region: int, rng) -> list[tuple[int, bool]]:
    other = 1 - ragged_region
    regions = [ragged_region, other]
    while len(regions) < component_count:
        regions.append(len(regions) % 2)
    tail = regions[1:]
    rng.shuffle(tail)
    return [(ragged_region, True)] + [(region, False) for region in tail]


def _sample_scene(
    *,
    h: int,
    w: int,
    axis: str,
    split: int,
    first: int,
    component_count: int,
    rng,
) -> list[list[int]] | None:
    grid = _background_grid(h, w, axis, split, first)
    occupied: set[tuple[int, int]] = set()
    ragged_region = rng.randrange(2)
    plan = _component_plan(component_count, ragged_region, rng)

    for index, (region_index, ragged) in enumerate(plan):
        background = first if region_index == 0 else _other(first)
        bounds = _region_bounds(axis, split, h, w, region_index)
        if ragged:
            offsets = _ragged_offsets(background, rng.randrange(3))
        else:
            shapes = ((1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2))
            shape_h, shape_w = shapes[rng.randrange(len(shapes))]
            offsets = _rectangle_offsets(shape_h, shape_w)

        component = _place_component(
            offsets=offsets,
            bounds=bounds,
            background=background,
            occupied=occupied,
            rng=rng,
        )
        if component is None:
            return None
        occupied.update(component)
        for r, c in component:
            grid[r][c] = 2

    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical teaching domain and Racket-safe split grammar."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]

    h = len(grid)
    w = len(grid[0])
    if not (9 <= h <= 15 and 9 <= w <= 15):
        errors.append(f"grid dimensions {h}x{w} outside 9..15 teaching envelope")
    for row in grid:
        if not isinstance(row, list) or len(row) != w:
            return errors + ["ragged grid"]
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool):
                return errors + [f"non-integer cell value {value!r}"]
            if value not in {1, 2, 8}:
                return errors + [f"unexpected cell color {value}; expected only 1,2,8"]

    colors = {value for row in grid for value in row}
    if colors != {1, 2, 8}:
        errors.append(f"expected palette {{1,2,8}}, found {sorted(colors)}")

    try:
        axis, split, first = _infer_layout(grid)
    except ValueError as exc:
        return errors + [str(exc)]

    dimension = h if axis == "h" else w
    if split < 3 or dimension - split < 3:
        errors.append(f"split at {split} leaves a region thinner than 3 cells")

    region_red = [0, 0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                region_red[_region_index(axis, split, r, c)] += 1
    if any(count == 0 for count in region_red):
        errors.append(f"red cells must occur in both regions, found counts {region_red}")

    components = _red_components(grid)
    if not (2 <= len(components) <= 6):
        errors.append(f"expected 2..6 red components, found {len(components)}")

    # The Racket authority discovers the split by scanning for a non-red cell.
    # Keep each row-region non-full, and keep the leading region visible along
    # the orthogonal scan direction, so no red object can manufacture a false
    # earlier split.
    regions = ((0, w),) if axis == "h" else ((0, split), (split, w))
    for r in range(h):
        for c0, c1 in regions:
            if all(grid[r][c] == 2 for c in range(c0, c1)):
                errors.append(f"row {r} fully masks region columns {c0}..{c1 - 1}")
    if axis == "h":
        for c in range(w):
            if all(grid[r][c] == 2 for r in range(0, split)):
                errors.append(f"column {c} fully masks the leading horizontal region")
    else:
        for r in range(h):
            if all(grid[r][c] == 2 for c in range(0, split)):
                errors.append(f"row {r} fully masks the leading vertical region")

    # Keep this local variable intentional: it documents which color the Racket
    # scanner must recover at the top/left corner without over-constraining where
    # individual red objects may occur.
    del first
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    if self_check(grid):
        raise ValueError("cannot observe overrides from a grid outside the task grammar")
    axis, _split, first = _infer_layout(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "split_axis": axis,
        "tl_color": first,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 9, 15)
    w = ctx.draw_int("grid_w", 9, 15)
    axis = ctx.draw_choice("split_axis", ("h", "v"))
    first = ctx.draw_choice("tl_color", (1, 8))

    rng = ctx.draw_rng(f"scene:{difficulty or 'medium'}")
    dimension = h if axis == "h" else w
    split = rng.randint(4, dimension - 4)
    if difficulty == "easy":
        component_count = 3 + rng.randrange(2)
    elif difficulty == "hard":
        component_count = 4 + rng.randrange(2)
    else:
        component_count = 3 + rng.randrange(3)

    for _attempt in range(512):
        grid = _sample_scene(
            h=h,
            w=w,
            axis=axis,
            split=split,
            first=first,
            component_count=component_count,
            rng=rng,
        )
        if grid is None:
            continue
        if self_check(grid):
            continue
        if len(_red_components(grid)) != component_count:
            continue
        if rule_mirror(grid) == grid:
            continue
        if not _has_ragged_component(grid):
            continue
        return grid
    raise RuntimeError(
        f"failed to place a lawful {component_count}-component scene after 512 attempts"
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "ragged_component": _has_ragged_component,
}
SEMANTIC_RIVALS = {"rigid_components": _rigid_components}
WITNESS_RIVALS = {"ragged_component": ["rigid_components"]}
CANONICAL_SHORTCUTS = {"rigid_components": _rigid_components}
LESSON_COMPETITORS = {"rigid_components": _rigid_components}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but answers the query differently"
                )
            else:
                reasons.append(f"{name} survives every demonstration and the query")
    return reasons
