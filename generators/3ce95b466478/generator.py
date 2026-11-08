"""Input sampler for extracting the second-largest red component.

The unchanged Racket authority ranks 4-connected color-2 components by cell
count (descending, then top row), selects the second component, crops it to its
bounding box, and recolors it color 8.  This sampler includes a scheduled
counterexample to the canonical-fitting but wrong "rank by perimeter" rule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ce95b466478"
TASK_ID = GENERATOR_ID
RULE_HASH = "e0019367e92e"
VERSION = "4.0.1"
SUMMARY = (
    "A 0-background grid contains 3-5 separated red (2) polyominoes with "
    "distinct cell counts and one 1-3-cell non-red decoration. Rank the red "
    "components by cell count, choose the second-largest, crop its bounding "
    "box, and recolor its cells cyan (8). Exact controls cover dimensions and "
    "component count; decoration color/size, layouts, and shapes vary "
    "internally. Every three consecutive samples include a size-vs-perimeter "
    "counterexample."
)

INVARIANTS = [
    "3-5 separated 4-connected color-2 components with distinct cell counts",
    "exactly one 1-3-cell decoration component in one color from 3..9",
    "the second-largest-by-size component is unambiguous",
    "every three consecutive samples refute second-largest-by-perimeter",
]

AXES = {
    # The inherited override checker executes every boundary case over three
    # bands and thirty seeds.  These finite values retain every canonical
    # dimension plus a broader endpoint without exploding that matrix.
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted",
        "valid": "8|9|10|16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted",
        "valid": "11|12|13|16",
    },
    "n_blobs": {"type": "int", "default": "3..5", "valid": "3..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_CANONICAL_PROFILES = (
    (8, 12),
    (9, 11),
    (9, 13),
    (10, 12),
    (10, 13),
)
_AXIS_DOMAINS = {
    "grid_h": (8, 9, 10, 16),
    "grid_w": (11, 12, 13, 16),
    "n_blobs": (3, 4, 5),
}
_DECORATION_COLORS = tuple(range(3, 10))
_DECORATION_SIZES = (1, 2, 3)

# Cell-count ordering: 6 > 5 > 3 > 2 > 1.
# Perimeter ordering: 5-cell staircase (12) > 6-cell rectangle (10) > ... .
# Therefore size and perimeter select different second-ranked components.
_PERIMETER_TRAP_SHAPES = {
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    5: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    3: ((0, 0), (0, 1), (0, 2)),
    2: ((0, 0), (0, 1)),
    1: ((0, 0),),
}
_PERIMETER_TRAP_SIZES = (6, 5, 3, 2, 1)


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _connected(cells) -> bool:
    cells = set(cells)
    stack = [next(iter(cells))]
    seen = set(stack)
    while stack:
        r, c = stack.pop()
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == len(cells)


@lru_cache(maxsize=1)
def _polyominoes():
    """All normalized 4-connected shapes that fit in a 3x3 slot."""
    universe = tuple((r, c) for r in range(3) for c in range(3))
    by_size: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(1, 10):
        shapes = {
            _normalize(cells)
            for cells in combinations(universe, size)
            if _connected(cells)
        }
        by_size[size] = tuple(sorted(shapes))
    return by_size


def _symmetries(cells):
    """Unique rotations/reflections, normalized to the top-left."""
    current = tuple(cells)
    found = set()
    for reflected in (False, True):
        shape = tuple((r, -c if reflected else c) for r, c in current)
        for _ in range(4):
            found.add(_normalize(shape))
            shape = tuple((c, -r) for r, c in shape)
    return tuple(sorted(found))


def _starts(length: int, count: int):
    return tuple(
        values
        for values in combinations(range(length - 2), count)
        if all(b - a >= 4 for a, b in zip(values, values[1:]))
    )


@lru_cache(maxsize=54)
def _layouts(h: int, w: int):
    """Six disjoint 3x3 slots, in either a 2x3 or 3x2 arrangement."""
    layouts = []
    for rows in _starts(h, 2):
        for cols in _starts(w, 3):
            layouts.append(tuple((r, c) for r in rows for c in cols))
    if h >= 11:
        for rows in _starts(h, 3):
            for cols in _starts(w, 2):
                layouts.append(tuple((r, c) for r in rows for c in cols))
    if not layouts:
        raise ValueError(f"no six-slot layout for {h}x{w}")
    return tuple(layouts)


def _weighted_axis(ctx, name: str, anchor: int, weight: int = 24) -> int:
    return ctx.draw_choice(name, _AXIS_DOMAINS[name] + (anchor,) * weight)


def _validate_overrides(overrides) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if value is not None and value not in _AXIS_DOMAINS[name]:
            raise ValueError(
                f"{name}={value!r} is outside declared values "
                f"{_AXIS_DOMAINS[name]}"
            )


def _shape_for(ctx, *, size: int, label: str, perimeter_trap: bool):
    rng = ctx.draw_rng(label)
    if perimeter_trap:
        return rng.choice(_symmetries(_PERIMETER_TRAP_SHAPES[size]))
    return rng.choice(_polyominoes()[size])


def _paint_in_slot(grid, slot, shape, color, rng) -> None:
    bh = max(r for r, _ in shape) + 1
    bw = max(c for _, c in shape) + 1
    dr = rng.randint(0, 3 - bh)
    dc = rng.randint(0, 3 - bw)
    top, left = slot
    for r, c in shape:
        if grid[top + dr + r][left + dc + c] != 0:
            raise RuntimeError("constructive slot collision")
        grid[top + dr + r][left + dc + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_h, canonical_w = ctx.draw_choice(
        "canonical_profile", _CANONICAL_PROFILES
    )
    h = _weighted_axis(ctx, "grid_h", canonical_h)
    w = _weighted_axis(ctx, "grid_w", canonical_w)

    difficulty_anchor = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
    n_blobs = _weighted_axis(ctx, "n_blobs", difficulty_anchor, weight=5)
    decoration_anchor = {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 2)
    decoration_size = ctx.draw_choice(
        "internal_decoration_size",
        _DECORATION_SIZES + (decoration_anchor,) * 3,
    )
    decoration_color = ctx.draw_choice(
        "internal_decoration_color",
        _DECORATION_COLORS + (5, 6, 7, 9) * 2,
    )

    grid = full_grid(h, w, 0)
    slots = list(ctx.draw_rng("slot_layout").choice(_layouts(h, w)))
    ctx.draw_rng("slot_assignment").shuffle(slots)

    perimeter_trap = sample_index % 3 == 0
    if perimeter_trap:
        sizes = list(_PERIMETER_TRAP_SIZES[:n_blobs])
    else:
        sizes = ctx.draw_rng("blob_sizes").sample(range(2, 9), n_blobs)
    ctx.draw_rng("size_to_slot").shuffle(sizes)

    offsets_rng = ctx.draw_rng("shape_offsets")
    for index, (slot, size) in enumerate(zip(slots[:n_blobs], sizes)):
        shape = _shape_for(
            ctx,
            size=size,
            label=f"blob_shape_{index}",
            perimeter_trap=perimeter_trap,
        )
        _paint_in_slot(grid, slot, shape, 2, offsets_rng)

    decoration_shape = ctx.draw_rng("decoration_shape").choice(
        _polyominoes()[decoration_size]
    )
    _paint_in_slot(
        grid,
        slots[n_blobs],
        decoration_shape,
        decoration_color,
        offsets_rng,
    )
    return grid


def _grid_error(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return "empty or non-list grid"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "ragged grid"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return f"invalid cell value {value!r}"
    return None


def _components(grid, color: int):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nxt in ((rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)):
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(cells)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    error = _grid_error(grid)
    if error:
        return [error]
    h, w = len(grid), len(grid[0])
    errors = []
    if not 8 <= h <= 16:
        errors.append(f"grid_h={h} outside 8..16")
    if not 11 <= w <= 16:
        errors.append(f"grid_w={w} outside 11..16")

    colors = {value for row in grid for value in row}
    if 0 not in colors:
        errors.append("background color 0 is absent")
    decorations = sorted(colors - {0, 2})
    if len(decorations) != 1:
        errors.append(f"expected one decoration color, found {decorations}")
        decoration_color = None
    else:
        decoration_color = decorations[0]
        if not 3 <= decoration_color <= 9:
            errors.append(f"decoration color {decoration_color} outside 3..9")

    red_components = _components(grid, 2)
    if not 3 <= len(red_components) <= 5:
        errors.append(f"expected 3..5 red components, found {len(red_components)}")
    sizes = [len(cells) for cells in red_components]
    if len(sizes) != len(set(sizes)):
        errors.append(f"red component sizes are not distinct: {sorted(sizes)}")

    if decoration_color is not None:
        decoration_components = _components(grid, decoration_color)
        decoration_size = sum(len(cells) for cells in decoration_components)
        if len(decoration_components) != 1:
            errors.append(
                f"expected one decoration component, found {len(decoration_components)}"
            )
        if not 1 <= decoration_size <= 3:
            errors.append(f"decoration size {decoration_size} outside 1..3")
    return errors


def strict_canonical_like(grid):
    """All returned grids are lawful members of the intended task domain."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(_components(grid, 2)),
    }


def _perimeter(cells) -> int:
    cells = set(cells)
    return sum(
        (r + dr, c + dc) not in cells
        for r, c in cells
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _crop(cells):
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _second_largest_size(grid):
    reds = _components(grid, 2)
    target = sorted(reds, key=lambda cells: (-len(cells), min(r for r, _ in cells)))[1]
    return _crop(target)


def _second_largest_perimeter(grid):
    """Plausible wrong rule that fits every published canonical pair."""
    reds = _components(grid, 2)
    target = sorted(
        reds,
        key=lambda cells: (-_perimeter(cells), min(r for r, _ in cells)),
    )[1]
    return _crop(target)


def _size_vs_perimeter(grid) -> bool:
    return _second_largest_size(grid) != _second_largest_perimeter(grid)


SEMANTIC_WITNESSES = {"size_vs_perimeter": _size_vs_perimeter}
BRANCH_WITNESSES = {"size_vs_perimeter"}
SEMANTIC_RIVALS = {"second_largest_perimeter": _second_largest_perimeter}
WITNESS_RIVALS = {
    "size_vs_perimeter": ["second_largest_perimeter"],
}
CANONICAL_SHORTCUTS = {
    "second_largest_perimeter": _second_largest_perimeter,
}
LESSON_COMPETITORS = {
    "second_largest_perimeter": _second_largest_perimeter,
}
EXAMPLES_NEEDED = 3


def lesson_identifiable(demos, query):
    del query
    if all(
        _second_largest_perimeter(pair["input"]) == pair["output"]
        for pair in demos
    ):
        return ["second-largest-by-perimeter rival fits every demonstration"]
    return []
