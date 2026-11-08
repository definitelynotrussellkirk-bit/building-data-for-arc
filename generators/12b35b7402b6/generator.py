"""Generator for Marker Count Matches Size (12b35b7402b6).

Count every gray(5) cell in the top row.  Exactly one 4-connected blue(1)
component below has that many cells; the canonical rule recolors it red(2).

The previous generator mixed three invalid diagnostic textures into its public
axis, silently accepted unknown/coerced overrides, and always used a contiguous
left-anchored marker run.  This implementation exposes only exact, realizable
controls and deliberately alternates contiguous and scattered marker layouts so
cell count cannot be replaced by horizontal span.
"""
from __future__ import annotations

import math
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12b35b7402b6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "cb01ed25524c"
SUMMARY = (
    "Count all gray(5) top-row markers and recolor the unique blue(1) "
    "4-connected component with that many cells red(2)."
)

_H_LO, _H_HI = 9, 30
_W_LO, _W_HI = 12, 30
_M_LO, _M_HI = 2, 6
_N_LO, _N_HI = 2, 4
_MARKER_LAYOUTS = ("contiguous", "scattered")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..30 with a canonical-profile prior",
        "valid": "9..30",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 12..30 with a canonical-profile prior",
        "valid": "12..30",
        "doc": "Exact returned grid width.",
    },
    "marker_count": {
        "type": "int",
        "default": "difficulty-aware 2..6",
        "valid": "2..6",
        "doc": "Exact number of gray cells and exact target component size.",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
        "doc": "Exact number of separated blue components.",
    },
    "marker_layout": {
        "type": "str",
        "default": "alternates contiguous/scattered by sample index",
        "valid": "contiguous|scattered",
        "doc": "Whether gray markers form one run or have at least one gap.",
    },
}

INVARIANTS = [
    "background is 0 and all cells are exact ARC integers",
    "gray(5) occurs only in the top row and at least two markers exist",
    "blue(1) occurs only below the top row",
    "there are 2..4 separated 4-connected blue components",
    "exactly one blue component size equals the total gray-cell count",
]

COUNTER_HYPOTHESES = [
    "use the horizontal span or rightmost marker instead of counting gray cells",
    "select the largest, smallest, topmost, or leftmost blue object",
    "treat diagonally touching cells as connected",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", _H_LO, _H_HI),
        ("grid_w", _W_LO, _W_HI),
        ("marker_count", _M_LO, _M_HI),
        ("n_objects", _N_LO, _N_HI),
    ):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an exact integer in {lo}..{hi}; bool is forbidden")
    value = overrides.get("marker_layout")
    if value is not None and (type(value) is not str or value not in _MARKER_LAYOUTS):
        raise ValueError("marker_layout must be 'contiguous' or 'scattered'")


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _component_cells(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: (cells[0], len(cells)))


def blue_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    return _component_cells(grid, 1)


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}
    h, w = len(grid), len(grid[0])
    markers = [c for c, value in enumerate(grid[0]) if value == 5]
    components = blue_components([list(row) for row in grid]) if all(len(row) == w for row in grid) else []
    sizes = [len(component) for component in components]
    marker_count = len(markers)
    marker_span = (max(markers) - min(markers) + 1) if markers else 0
    layout = "contiguous" if markers and marker_span == marker_count else "scattered"
    return {
        "grid_h": h,
        "grid_w": w,
        "marker_count": marker_count,
        "marker_span": marker_span,
        "marker_layout": layout,
        "n_objects": len(components),
        "blue_component_sizes": sizes,
        "matching_object_count": sum(size == marker_count for size in sizes),
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful input domain, including canonical examples."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty row"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(f"dimensions {h}x{w} outside {_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        errors.append("cells must be exact integer ARC colors 0..9; bool is forbidden")
        return errors
    colors = {cell for row in grid for cell in row}
    if not colors <= {0, 1, 5}:
        errors.append(f"input may use only colors 0,1,5; found {sorted(colors)}")
    grays = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not (_M_LO <= len(grays) <= _M_HI):
        errors.append(f"expected {_M_LO}..{_M_HI} gray markers; found {len(grays)}")
    if any(r != 0 for r, _ in grays):
        errors.append("gray markers may occur only in the top row")
    if any(grid[0][c] == 1 for c in range(w)):
        errors.append("blue objects must stay below the top row")
    components = blue_components([list(row) for row in grid])
    if not (_N_LO <= len(components) <= _N_HI):
        errors.append(f"expected {_N_LO}..{_N_HI} blue components; found {len(components)}")
    sizes = [len(component) for component in components]
    matches = sum(size == len(grays) for size in sizes)
    if matches != 1:
        errors.append(f"expected exactly one blue component of marker size {len(grays)}; found {matches}")
    return errors


def _partition_slots(h: int, w: int, n: int) -> list[tuple[int, int, int, int]]:
    """Return n separated body slots as (r0,c0,height,width)."""
    body_top = 2
    body_h = h - body_top
    rows = 1 if n <= 2 else 2
    cols = math.ceil(n / rows)
    # One-cell gutters between slot bands.
    usable_h = body_h - (rows - 1)
    usable_w = w - (cols - 1)
    heights = [usable_h // rows + (i < usable_h % rows) for i in range(rows)]
    widths = [usable_w // cols + (i < usable_w % cols) for i in range(cols)]
    r_starts = []
    cursor = body_top
    for value in heights:
        r_starts.append(cursor)
        cursor += value + 1
    c_starts = []
    cursor = 0
    for value in widths:
        c_starts.append(cursor)
        cursor += value + 1
    slots = [
        (r_starts[r], c_starts[c], heights[r], widths[c])
        for r in range(rows)
        for c in range(cols)
    ]
    return slots[:n]


def _shape(rng, size: int, height: int, width: int) -> list[tuple[int, int]]:
    if size > height * width:
        raise ValueError("component does not fit its slot")
    for _ in range(200):
        start = (rng.randrange(height), rng.randrange(width))
        cells = {start}
        while len(cells) < size:
            frontier = sorted({
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < height and 0 <= c + dc < width and (r + dr, c + dc) not in cells
            })
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) == size:
            return sorted(cells)
    # Deterministic connected snake fallback.
    snake = [(r, c) for r in range(height) for c in (range(width) if r % 2 == 0 else range(width - 1, -1, -1))]
    return snake[:size]


def _marker_columns(rng, count: int, width: int, layout: str) -> list[int]:
    if layout == "contiguous":
        start = rng.randint(0, width - count)
        return list(range(start, start + count))
    # Force at least one gap and vary both span and anchoring.
    for _ in range(100):
        cols = sorted(rng.sample(range(width), count))
        if cols[-1] - cols[0] + 1 > count:
            return cols
    raise RuntimeError("could not construct scattered marker positions")


def _sizes(rng, marker_count: int, n_objects: int, capacity: int) -> list[int]:
    pool = [size for size in range(1, min(capacity, 12) + 1) if size != marker_count]
    if len(pool) < n_objects - 1:
        raise ValueError("grid too small for distinct component sizes")
    # Mix lower and higher distractors so target rank is not fixed.
    lower = [value for value in pool if value < marker_count]
    higher = [value for value in pool if value > marker_count]
    picked: list[int] = []
    if lower and len(picked) < n_objects - 1 and rng.random() < 0.75:
        picked.append(rng.choice(lower))
    if higher and len(picked) < n_objects - 1:
        picked.append(rng.choice(higher))
    remaining = [value for value in pool if value not in picked]
    rng.shuffle(remaining)
    picked.extend(remaining[: n_objects - 1 - len(picked)])
    values = [marker_count, *picked]
    rng.shuffle(values)
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    explicit_dims = overrides.get("grid_h") is not None or overrides.get("grid_w") is not None
    canonical_prior = not explicit_dims and sample_index % 4 == 0
    band = difficulty or "medium"
    if canonical_prior:
        profile = rng.choice(((9, 12), (10, 12), (11, 13)))
        h_lo = h_hi = profile[0]
        w_lo = w_hi = profile[1]
    elif band == "easy":
        h_lo, h_hi, w_lo, w_hi = 9, 11, 12, 15
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 16, 30, 18, 30
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 18, 13, 22
    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI)

    if band == "easy":
        m_lo, m_hi, n_lo, n_hi = 2, 4, 2, 3
    elif band == "hard":
        m_lo, m_hi, n_lo, n_hi = 4, 6, 3, 4
    else:
        m_lo, m_hi, n_lo, n_hi = 2, 6, 2, 4
    marker_count = _banded_int(ctx, overrides, "marker_count", m_lo, m_hi, _M_LO, _M_HI)
    n_objects = _banded_int(ctx, overrides, "n_objects", n_lo, n_hi, _N_LO, _N_HI)
    if overrides.get("marker_layout") is not None:
        marker_layout = ctx.draw_choice("marker_layout", _MARKER_LAYOUTS)
    else:
        scheduled = _MARKER_LAYOUTS[sample_index % len(_MARKER_LAYOUTS)]
        marker_layout = ctx.draw_choice("marker_layout", (scheduled,))

    slots = _partition_slots(h, w, n_objects)
    minimum_capacity = min(sh * sw for _, _, sh, sw in slots)
    sizes = _sizes(rng, marker_count, n_objects, minimum_capacity)
    rng.shuffle(slots)

    grid = full_grid(h, w, 0)
    for col in _marker_columns(rng, marker_count, w, marker_layout):
        grid[0][col] = 5
    for size, (r0, c0, sh, sw) in zip(sizes, slots):
        for dr, dc in _shape(rng, size, sh, sw):
            grid[r0 + dr][c0 + dc] = 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator error: {errors}")
    return grid
