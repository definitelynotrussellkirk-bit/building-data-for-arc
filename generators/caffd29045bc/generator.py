"""Generator for ARC task caffd29045bc — reflect across the color-9 guide.

A lawful input has one full vertical color-9 guide and a sparse colored source
wholly on one side.  The unchanged Racket authority preserves the input and
copies every non-{0,9} source cell to the equal-distance column on the other
side.  The four-profile schedule deliberately refutes the strongest shortcuts
left open by the all-left, centered, connected and guide-gapped canonical set.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "caffd29045bc"
TASK_ID = GENERATOR_ID
RULE_HASH = "71b211cdd7c0"
VERSION = "3.0.0"

SUMMARY = (
    "Exactly one full vertical color-9 guide and a 3..8-cell, 1..3-color "
    "source wholly on one side. Preserve the input and copy every source cell "
    "to its equal-distance mirror. A balanced four-profile lesson schedule "
    "covers centered/off-center guides, left/right sources, connected/split "
    "sources, and guide-adjacent/gapped sources."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "center_left_connected_gapped",
    "offcenter_right_connected_adjacent",
    "offcenter_left_split_adjacent",
    "center_right_split_gapped",
)
_CANONICAL_PROFILE_ANCHORS = ((7, 9, 3), (8, 11, 4), (9, 11, 4))

_PROFILE_CONFIG = {
    SCHEDULE_PROFILES[0]: {
        "axis_mode": "center",
        "source_side": "left",
        "layout": "connected",
        "guide_contact": "gapped",
        "canonical_prior": True,
    },
    SCHEDULE_PROFILES[1]: {
        "axis_mode": "offcenter",
        "source_side": "right",
        "layout": "connected",
        "guide_contact": "adjacent",
        "canonical_prior": False,
    },
    SCHEDULE_PROFILES[2]: {
        "axis_mode": "offcenter",
        "source_side": "left",
        "layout": "split",
        "guide_contact": "adjacent",
        "canonical_prior": False,
    },
    SCHEDULE_PROFILES[3]: {
        "axis_mode": "center",
        "source_side": "right",
        "layout": "split",
        "guide_contact": "gapped",
        "canonical_prior": False,
    },
}

INVARIANTS = [
    "rectangular 6..14 by 8..17 grid with background 0",
    "exactly one full vertical color-9 guide and no stray 9-cells",
    "3..8 non-{0,9} source cells lie wholly on exactly one side",
    "every source cell has an in-bounds equal-distance mirror destination",
    "source union has one or two 4-connected components",
    "guide contact is observable as adjacent (distance 1 occurs) or gapped (all distances >=2)",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 6..14", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..17", "valid": "8..17"},
    "source_cell_count": {"type": "int", "default": "difficulty/profile-aware 3..8", "valid": "3..8"},
    "source_color_count": {"type": "int", "default": "profile-aware 1..3", "valid": "1..3"},
    "source_side": {"type": "str", "default": "four-profile left|right schedule", "valid": "left|right"},
    "layout": {"type": "str", "default": "four-profile connected|split schedule", "valid": "connected|split"},
    "guide_contact": {"type": "str", "default": "four-profile adjacent|gapped schedule", "valid": "adjacent|gapped"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Malformed task-linked probes used by defect lint; not training axes.
DEGENERATE_TEXTURES = (
    "no_axis",
    "multiple_axes",
    "both_sides_filled",
    "no_source",
    "clipped_reflection",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic branch for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _component_sets(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    out: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        out.append(component)
    return out


def _component_count(cells: set[tuple[int, int]]) -> int:
    return len(_component_sets(cells))


def _find_axis(grid: list[list[int]]) -> list[int]:
    if not grid or not grid[0]:
        return []
    return [
        c for c in range(len(grid[0]))
        if all(row[c] == 9 for row in grid)
    ]


def _source_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    }


def _columns_for(w: int, axis: int, side: str, guide_contact: str) -> tuple[int, ...]:
    span = min(axis, w - 1 - axis)
    distances = range(1 if guide_contact == "adjacent" else 2, span + 1)
    if side == "left":
        return tuple(axis - distance for distance in distances)
    if side == "right":
        return tuple(axis + distance for distance in distances)
    raise ValueError(f"unknown source_side {side!r}")


def _region(h: int, w: int, axis: int, side: str, guide_contact: str) -> set[tuple[int, int]]:
    return {(r, c) for r in range(h) for c in _columns_for(w, axis, side, guide_contact)}


def _split_counts(count: int) -> tuple[int, int]:
    return count // 2, count - count // 2


def _axis_feasible(
    h: int,
    w: int,
    axis: int,
    side: str,
    layout: str,
    guide_contact: str,
    count: int,
) -> bool:
    columns = _columns_for(w, axis, side, guide_contact)
    if not columns:
        return False
    # Adjacent witnesses also require an offset-two cell, so the source cannot
    # collapse to the guide-neighbor column.
    if guide_contact == "adjacent" and min(axis, w - 1 - axis) < 2:
        return False
    if layout == "connected":
        return h * len(columns) >= count
    gap_row = h // 2
    top_rows = gap_row
    bottom_rows = h - gap_row - 1
    first, second = _split_counts(count)
    return top_rows * len(columns) >= first and bottom_rows * len(columns) >= second


def _choose_axis(
    rng,
    h: int,
    w: int,
    *,
    axis_mode: str,
    side: str,
    layout: str,
    guide_contact: str,
    count: int,
) -> int:
    all_candidates = [
        c for c in range(2, w - 2)
        if _axis_feasible(h, w, c, side, layout, guide_contact, count)
    ]
    if not all_candidates:
        raise ValueError("requested controls leave no feasible mirror guide")
    centers = {(w - 1) // 2, w // 2}
    if axis_mode == "center":
        preferred = [w // 2] if w // 2 in all_candidates else [c for c in all_candidates if c in centers]
    elif axis_mode == "offcenter":
        preferred = [c for c in all_candidates if c not in centers]
    else:
        raise ValueError(f"unknown axis mode {axis_mode!r}")
    return rng.choice(preferred or all_candidates)


def _grow_from(
    rng,
    allowed: set[tuple[int, int]],
    target_count: int,
    initial: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    if not initial or not initial <= allowed:
        raise ValueError("connected-growth seed is outside the legal source region")
    if target_count < len(initial) or target_count > len(allowed):
        raise ValueError("connected-growth target does not fit the legal source region")
    cells = set(initial)
    frontier = {
        nxt
        for r, c in cells
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if nxt in allowed and nxt not in cells
    }
    while len(cells) < target_count:
        if not frontier:
            raise ValueError("connected-growth frontier exhausted")
        cell = rng.choice(sorted(frontier))
        frontier.remove(cell)
        cells.add(cell)
        r, c = cell
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in allowed and nxt not in cells:
                frontier.add(nxt)
    return cells


def _side_column(axis: int, side: str, distance: int) -> int:
    return axis - distance if side == "left" else axis + distance


def _draw_source_cells(
    rng,
    *,
    h: int,
    w: int,
    axis: int,
    side: str,
    layout: str,
    guide_contact: str,
    count: int,
) -> set[tuple[int, int]]:
    allowed = _region(h, w, axis, side, guide_contact)
    if layout == "connected":
        row = rng.randrange(h)
        if guide_contact == "adjacent":
            initial = {
                (row, _side_column(axis, side, 1)),
                (row, _side_column(axis, side, 2)),
            }
        else:
            far_col = min(c for _, c in allowed) if side == "left" else max(c for _, c in allowed)
            initial = {(row, far_col)}
        return _grow_from(rng, allowed, count, initial)

    if layout != "split":
        raise ValueError(f"unknown layout {layout!r}")
    gap_row = h // 2
    top = {point for point in allowed if point[0] < gap_row}
    bottom = {point for point in allowed if point[0] > gap_row}
    first_count, second_count = _split_counts(count)
    top_row = rng.choice(sorted({r for r, _ in top}))
    bottom_row = rng.choice(sorted({r for r, _ in bottom}))
    if guide_contact == "adjacent":
        first_start = (top_row, _side_column(axis, side, 1))
        second_start = (bottom_row, _side_column(axis, side, 2))
    else:
        top_col = min(c for _, c in top) if side == "left" else max(c for _, c in top)
        bottom_col = min(c for _, c in bottom) if side == "left" else max(c for _, c in bottom)
        first_start = (top_row, top_col)
        second_start = (bottom_row, bottom_col)
    first = _grow_from(rng, top, first_count, {first_start})
    second = _grow_from(rng, bottom, second_count, {second_start})
    return first | second


def _validate_call(difficulty, overrides: dict[str, object]) -> None:
    allowed = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if isinstance(difficulty, str) and difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"unsupported difficulty {difficulty!r}")


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

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(str(texture), ctx)
    if texture is not None:
        raise ValueError(f"unknown texture {texture!r}")

    profile_name = schedule_profile(seed, sample_index, difficulty)
    profile = _PROFILE_CONFIG[profile_name]

    canonical_anchor = None
    if profile["canonical_prior"]:
        canonical_anchor = _CANONICAL_PROFILE_ANCHORS[
            (int(sample_index) // LESSON_SCHEDULE_PERIOD) % len(_CANONICAL_PROFILE_ANCHORS)
        ]

    if "grid_h" in overrides:
        h = ctx.draw_int_strict("grid_h", 6, 14)
    elif canonical_anchor is not None:
        h = ctx.draw_int("grid_h", canonical_anchor[0], canonical_anchor[0])
    else:
        h = ctx.draw_int_diff("grid_h", 6, 14)

    if "grid_w" in overrides:
        w = ctx.draw_int_strict("grid_w", 8, 17)
    elif canonical_anchor is not None:
        w = ctx.draw_int("grid_w", canonical_anchor[1], canonical_anchor[1])
    else:
        w = ctx.draw_int_diff("grid_w", 8, 17)

    if "source_cell_count" in overrides:
        source_cell_count = ctx.draw_int_strict("source_cell_count", 3, 8)
    elif canonical_anchor is not None:
        source_cell_count = ctx.draw_int(
            "source_cell_count", canonical_anchor[2], canonical_anchor[2]
        )
    else:
        source_cell_count = ctx.draw_int_diff("source_cell_count", 3, 8)

    if "source_color_count" in overrides:
        source_color_count = ctx.draw_int_strict("source_color_count", 1, 3)
    elif profile["canonical_prior"]:
        source_color_count = ctx.draw_int("source_color_count", 1, 2)
    else:
        source_color_count = ctx.draw_int("source_color_count", 1, 3)

    source_side = ctx.draw_choice(
        "source_side",
        ("left", "right") if "source_side" in overrides else (profile["source_side"],),
    )
    layout = ctx.draw_choice(
        "layout",
        ("connected", "split") if "layout" in overrides else (profile["layout"],),
    )
    guide_contact = ctx.draw_choice(
        "guide_contact",
        ("adjacent", "gapped") if "guide_contact" in overrides else (profile["guide_contact"],),
    )

    geometry_rng = ctx.draw_rng("layout_geometry")
    axis = _choose_axis(
        geometry_rng,
        h,
        w,
        axis_mode=str(profile["axis_mode"]),
        side=source_side,
        layout=layout,
        guide_contact=guide_contact,
        count=source_cell_count,
    )
    cells = _draw_source_cells(
        geometry_rng,
        h=h,
        w=w,
        axis=axis,
        side=source_side,
        layout=layout,
        guide_contact=guide_contact,
        count=source_cell_count,
    )

    palette_rng = ctx.draw_rng("source_palette")
    palette = palette_rng.sample(range(1, 9), source_color_count)
    ordered_cells = sorted(cells)
    palette_rng.shuffle(ordered_cells)

    grid = full_grid(h, w, 0)
    for row in range(h):
        grid[row][axis] = 9
    for index, (row, col) in enumerate(ordered_cells):
        grid[row][col] = palette[index % source_color_count]
    return grid


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every advertised exact control from returned pixels."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    axes = _find_axis(grid)
    if len(axes) != 1:
        return {"grid_h": h, "grid_w": w}
    axis = axes[0]
    source = _source_cells(grid)
    colors = {grid[r][c] for r, c in source}
    left = any(c < axis for _, c in source)
    right = any(c > axis for _, c in source)
    side = "left" if left and not right else "right" if right and not left else "mixed"
    components = _component_count(source) if source else 0
    layout = "connected" if components == 1 else "split" if components == 2 else "other"
    contact = (
        "adjacent"
        if source and min(abs(c - axis) for _, c in source) == 1
        else "gapped"
    )
    return {
        "grid_h": h,
        "grid_w": w,
        "source_cell_count": len(source),
        "source_color_count": len(colors),
        "source_side": side,
        "layout": layout,
        "guide_contact": contact,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete one-sided reflection teaching grammar."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    height = len(grid)
    if not (6 <= height <= 14 and 8 <= width <= 17):
        errors.append(f"grid dimensions {height}x{width} outside 6..14 by 8..17")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    axes = _find_axis(grid)
    if len(axes) != 1:
        errors.append(f"expected exactly one full color-9 column, found {len(axes)}")
        return errors
    axis = axes[0]
    stray_nines = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9 and c != axis
    ]
    if stray_nines:
        errors.append(f"found {len(stray_nines)} stray color-9 cells outside the guide")

    source = _source_cells(grid)
    if not (3 <= len(source) <= 8):
        errors.append(f"expected 3..8 source cells, found {len(source)}")
    colors = {grid[r][c] for r, c in source}
    if not (1 <= len(colors) <= 3):
        errors.append(f"expected 1..3 source colors, found {len(colors)}")

    left = {(r, c) for r, c in source if c < axis}
    right = {(r, c) for r, c in source if c > axis}
    if bool(left) == bool(right):
        errors.append("source cells must lie wholly on exactly one side of the guide")
    clipped = [(r, c) for r, c in source if not 0 <= 2 * axis - c < width]
    if clipped:
        errors.append(f"{len(clipped)} source cells have out-of-bounds mirrors")

    if source:
        components = _component_count(source)
        if components not in (1, 2):
            errors.append(f"source union must have one or two components, found {components}")
        if max(abs(c - axis) for _, c in source) < 2:
            errors.append("source needs at least one cell at guide distance >=2")

    observed = observe_overrides(grid)
    requested: dict[str, object] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    for name, value in requested.items():
        if name in AXES and observed.get(name) != value:
            errors.append(f"override {name} requested {value!r}, observed {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid):
    """This generator's declared lawful reflection manifold."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for tests and rival diagnostics."""
    axes = _find_axis(grid)
    if len(axes) != 1:
        return deepcopy(grid)
    return _reflect_cells(grid, axes[0], _source_cells(grid))


def _reflect_cells(
    grid: list[list[int]],
    axis: int,
    cells: set[tuple[int, int]],
) -> list[list[int]]:
    out = deepcopy(grid)
    width = len(grid[0]) if grid else 0
    for row, col in sorted(cells):
        mirrored = 2 * axis - col
        if 0 <= mirrored < width:
            out[row][mirrored] = grid[row][col]
    return out


def _geometric_center_axis(grid):
    if not grid or not grid[0]:
        return deepcopy(grid)
    return _reflect_cells(grid, len(grid[0]) // 2, _source_cells(grid))


def _left_source_only(grid):
    axes = _find_axis(grid)
    if len(axes) != 1:
        return deepcopy(grid)
    axis = axes[0]
    source = _source_cells(grid)
    if source and all(col < axis for _, col in source):
        return _reflect_cells(grid, axis, source)
    return deepcopy(grid)


def _largest_component_only(grid):
    axes = _find_axis(grid)
    if len(axes) != 1:
        return deepcopy(grid)
    components = _component_sets(_source_cells(grid))
    if not components:
        return deepcopy(grid)
    winner = min(components, key=lambda component: (-len(component), min(component)))
    return _reflect_cells(grid, axes[0], winner)


def _skip_guide_adjacent_cells(grid):
    axes = _find_axis(grid)
    if len(axes) != 1:
        return deepcopy(grid)
    axis = axes[0]
    cells = {(r, c) for r, c in _source_cells(grid) if abs(c - axis) >= 2}
    return _reflect_cells(grid, axis, cells)


def _off_center_axis(grid) -> bool:
    axes = _find_axis(grid)
    if len(axes) != 1 or not grid or not grid[0]:
        return False
    centers = {(len(grid[0]) - 1) // 2, len(grid[0]) // 2}
    return axes[0] not in centers


def _right_side_source(grid) -> bool:
    axes = _find_axis(grid)
    if len(axes) != 1:
        return False
    source = _source_cells(grid)
    return bool(source) and all(col > axes[0] for _, col in source)


def _split_source(grid) -> bool:
    source = _source_cells(grid)
    return bool(source) and _component_count(source) == 2


def _guide_adjacent_source(grid) -> bool:
    axes = _find_axis(grid)
    if len(axes) != 1:
        return False
    return any(abs(col - axes[0]) == 1 for _, col in _source_cells(grid))


SEMANTIC_WITNESSES = {
    "off_center_axis": _off_center_axis,
    "right_side_source": _right_side_source,
    "split_source": _split_source,
    "guide_adjacent_source": _guide_adjacent_source,
}
SEMANTIC_RIVALS = {
    "geometric_center_axis": _geometric_center_axis,
    "left_source_only": _left_source_only,
    "largest_component_only": _largest_component_only,
    "skip_guide_adjacent_cells": _skip_guide_adjacent_cells,
}
WITNESS_RIVALS = {
    "off_center_axis": ["geometric_center_axis"],
    "right_side_source": ["left_source_only"],
    "split_source": ["largest_component_only"],
    "guide_adjacent_source": ["skip_guide_adjacent_cells"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 1.0


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared rivals that fit every demo but alter the query label."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits and rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
        except Exception as exc:  # make contract failures explicit, never silent
            reasons.append(f"{name} scoring error: {type(exc).__name__}: {exc}")
    return reasons


def _draw_from_degenerate(name: str, ctx):
    """Return varied malformed examples that self_check must reject."""
    rng = ctx.draw_rng(f"degenerate_{name}")
    height = 7 + rng.randint(0, 2)
    width = 9 + 2 * rng.randint(0, 1)
    grid = full_grid(height, width, 0)
    axis = width // 2
    if name != "no_axis":
        for row in range(height):
            grid[row][axis] = 9
    if name == "multiple_axes":
        for row in range(height):
            grid[row][axis - 2] = 9
        grid[2][1] = grid[3][1] = grid[3][2] = 4
    elif name == "both_sides_filled":
        grid[2][axis - 2] = 4
        grid[3][axis - 2] = 4
        grid[4][axis + 2] = 6
    elif name == "no_source":
        pass
    elif name == "clipped_reflection":
        for row in range(height):
            grid[row][axis] = 0
            grid[row][width - 2] = 9
        grid[1][0] = grid[2][0] = grid[2][1] = 3
    else:  # no_axis
        grid[2][1] = grid[3][1] = grid[3][2] = 4
    return grid


def mutation_fixtures():
    """Task-linked structural impostors that every review must reject."""
    return [
        (
            name,
            _draw_from_degenerate(
                name,
                gen_ctx(seed=index, sample_index=index, version=VERSION, task_id=TASK_ID),
            ),
        )
        for index, name in enumerate(DEGENERATE_TEXTURES, start=1)
    ]
