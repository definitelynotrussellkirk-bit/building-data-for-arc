"""Generator for ``dfc3ce537883`` — mirror left content across a 9-divider.

A lawful input is a 5..12 by 9..15 background-0 grid with exactly one
full-height color-9 vertical divider.  Three to eight colored source cells lie
strictly on the left, form one or two 4-connected components, and have empty,
in-bounds mirror destinations.  The selected Racket rule preserves the input
and copies every source color to ``(row, 2 * divider_col - col)``.

The four-sample curriculum schedule deliberately repeats two independent
teaching witnesses: disconnected sources refute "largest component only", and
multicolored sources refute "copy the shape in one color".  Any five
consecutive pairs therefore retain both witnesses after any one query is held
out, while one profile keeps exact canonical size/palette support.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dfc3ce537883"
TASK_ID = GENERATOR_ID
RULE_HASH = "6177794736be"  # sha256[:12] of normalized canonical program_solution
VERSION = "2.0.0"
SUMMARY = (
    "Mirror every colored cell left of one full-height color-9 divider to the "
    "equal-distance cell on the right, preserving each source color. Lawful "
    "inputs vary dimensions, source count, palette cardinality, connectedness, "
    "and centered/off-center divider placement."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "rectangular 5..12 by 9..15 integer grid with background 0",
    "exactly one full-height color-9 divider and no stray color-9 cells",
    "3..8 source cells using 1..3 colors from 1..8 lie strictly left of the divider",
    "source union has exactly one or two 4-connected components",
    "right side is initially empty and every reflected destination is in-bounds background",
    "at least one source cell is two or more columns from the divider",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 5|6 or difficulty-aware 5..12",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 9|10|11 or difficulty-aware 9..15",
        "valid": "9..15",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 3..7 or difficulty-aware 3..8",
        "valid": "3..8",
    },
    "n_colors": {
        "type": "int",
        "default": "scheduled 1|2|3",
        "valid": "1..3",
    },
    "layout": {
        "type": "str",
        "default": "scheduled connected|split",
        "valid": "connected|split",
    },
    "axis_position": {
        "type": "str",
        "default": "scheduled center|off_center",
        "valid": "center|off_center",
    },
}

# Every cross-product combination is constructive at the minimum 5x9 canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Malformed structural probes are not ordinary training axes.
DEGENERATE_TEXTURES = (
    "no_divider",
    "multiple_dividers",
    "no_left_content",
    "right_content",
    "stray_divider_color",
    "clipped_reflection",
    "three_components",
    "too_many_colors",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical",
    "split_multicolor",
    "split_monochrome",
    "connected_multicolor",
)

_INT_DOMAINS = {
    "grid_h": (5, 12),
    "grid_w": (9, 15),
    "n_cells": (3, 8),
    "n_colors": (1, 3),
}
_ENUM_DOMAINS = {
    "layout": ("connected", "split"),
    "axis_position": ("center", "off_center"),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SIZES = ((5, 9), (5, 10), (6, 11))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Public, deterministic curriculum profile for schedule audits."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(
            f"unknown texture {texture!r}; malformed probes are {list(DEGENERATE_TEXTURES)}"
        )

    for name, (lo, hi) in _INT_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    for name, options in _ENUM_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")
        if value not in options:
            raise ValueError(f"{name}={value!r} not in {list(options)}")


def _draw_int_axis(
    ctx,
    name: str,
    lo: int,
    hi: int,
    scheduled: int | None,
    overrides: dict[str, Any],
) -> int:
    """Keep the full override domain while allowing a deterministic profile."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    if scheduled is not None:
        return ctx.draw_choice(name, (scheduled,))
    return ctx.draw_int_diff(name, lo, hi)


def _draw_enum_axis(
    ctx,
    name: str,
    options: tuple[str, ...],
    scheduled: str,
    overrides: dict[str, Any],
) -> str:
    choices = options if name in overrides and overrides[name] is not None else (scheduled,)
    return ctx.draw_choice(name, choices)


def _full_divider_columns(grid: list[list[int]]) -> list[int]:
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    return [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]


def _component_sets(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def _grow_connected(
    rng,
    allowed: set[tuple[int, int]],
    count: int,
    *,
    start: tuple[int, int],
) -> set[tuple[int, int]]:
    if count < 1 or count > len(allowed) or start not in allowed:
        raise ValueError(
            f"cannot grow {count} connected cells from {start} in region of size {len(allowed)}"
        )
    cells = {start}
    frontier = {
        (start[0] + dr, start[1] + dc)
        for dr, dc in _CARDINAL
        if (start[0] + dr, start[1] + dc) in allowed
    }
    while len(cells) < count:
        if not frontier:
            raise RuntimeError("connected-growth frontier exhausted")
        cell = rng.choice(sorted(frontier))
        frontier.remove(cell)
        cells.add(cell)
        r, c = cell
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in allowed and nxt not in cells:
                frontier.add(nxt)
    return cells


def _axis_column(w: int, axis_position: str, rng) -> int:
    if axis_position == "center":
        return w // 2
    if axis_position != "off_center":
        raise ValueError(f"unknown axis_position {axis_position!r}")
    candidates = [c for c in range(3, w - 3) if c != w // 2]
    if not candidates:
        raise ValueError(f"width {w} has no supported off-center divider")
    return rng.choice(candidates)


def _source_region(h: int, w: int, axis: int) -> set[tuple[int, int]]:
    span = min(axis, w - 1 - axis)
    if span < 3:
        raise ValueError("divider must leave at least three mirrorable source columns")
    return {(r, c) for r in range(h) for c in range(axis - span, axis)}


def _draw_source_cells(
    rng,
    region: set[tuple[int, int]],
    count: int,
    layout: str,
    h: int,
) -> set[tuple[int, int]]:
    far_col = min(c for _, c in region)
    if layout == "connected":
        starts = sorted(point for point in region if point[1] == far_col)
        return _grow_connected(rng, region, count, start=rng.choice(starts))
    if layout != "split":
        raise ValueError(f"unknown layout {layout!r}")

    # An empty separator row gives exactly two unambiguous components.  At the
    # 5x9 minimum each side has capacity six, enough for the 8-cell maximum.
    gap_row = h // 2
    upper = {point for point in region if point[0] < gap_row}
    lower = {point for point in region if point[0] > gap_row}
    first_count = count // 2
    second_count = count - first_count
    if first_count > len(upper) or second_count > len(lower):
        raise ValueError("split layout does not fit requested dimensions/count")
    first_starts = sorted(point for point in upper if point[1] == far_col)
    second_starts = sorted(point for point in lower if point[1] == far_col)
    first = _grow_connected(rng, upper, first_count, start=rng.choice(first_starts))
    second = _grow_connected(rng, lower, second_count, start=rng.choice(second_starts))
    return first | second


def _profile_defaults(sample_index: int) -> dict[str, int | str | None]:
    profile = schedule_profile(0, sample_index)
    if profile == "canonical":
        h, w = _CANONICAL_SIZES[(sample_index // len(SCHEDULE_PROFILES)) % len(_CANONICAL_SIZES)]
        return {
            "grid_h": h,
            "grid_w": w,
            "n_cells": 3 + ((sample_index // len(SCHEDULE_PROFILES)) % 2),
            "n_colors": 1,
            "layout": "connected",
            "axis_position": "center",
        }
    if profile == "split_multicolor":
        return {
            "grid_h": None,
            "grid_w": None,
            "n_cells": 6,
            "n_colors": 3,
            "layout": "split",
            "axis_position": "off_center",
        }
    if profile == "split_monochrome":
        return {
            "grid_h": None,
            "grid_w": None,
            "n_cells": 5,
            "n_colors": 1,
            "layout": "split",
            "axis_position": "center",
        }
    return {
        "grid_h": None,
        "grid_w": None,
        "n_cells": 7,
        "n_colors": 2,
        "layout": "connected",
        "axis_position": "off_center",
    }


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

    texture = overrides.get("texture")
    if texture is not None:
        return _draw_from_degenerate(texture, ctx)

    defaults = _profile_defaults(int(sample_index))
    h = _draw_int_axis(ctx, "grid_h", 5, 12, defaults["grid_h"], overrides)
    w = _draw_int_axis(ctx, "grid_w", 9, 15, defaults["grid_w"], overrides)
    n_cells = _draw_int_axis(ctx, "n_cells", 3, 8, defaults["n_cells"], overrides)
    n_colors = _draw_int_axis(ctx, "n_colors", 1, 3, defaults["n_colors"], overrides)
    layout = _draw_enum_axis(
        ctx, "layout", ("connected", "split"), str(defaults["layout"]), overrides
    )
    axis_position = _draw_enum_axis(
        ctx,
        "axis_position",
        ("center", "off_center"),
        str(defaults["axis_position"]),
        overrides,
    )

    axis = _axis_column(w, axis_position, ctx.draw_rng("axis_geometry"))
    region = _source_region(h, w, axis)
    cells = _draw_source_cells(
        ctx.draw_rng("source_geometry"), region, n_cells, layout, h
    )

    colors = ctx.draw_rng("palette").sample(list(range(1, 9)), n_colors)
    ordered_cells = sorted(cells)
    assignments = [colors[index % n_colors] for index in range(len(ordered_cells))]
    ctx.draw_rng("color_assignment").shuffle(assignments)

    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][axis] = 9
    for (r, c), color in zip(ordered_cells, assignments, strict=True):
        grid[r][c] = color
    return grid


def _basic_grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must contain nonempty row sequences"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (bools are not colors)"], h, w
    return [], h, w


def _source_cells(grid, axis: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c in range(axis)
        if row[c] not in (0, 9)
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from pixels, never RNG bookkeeping."""
    basic, h, w = _basic_grid_errors(grid)
    if basic:
        raise ValueError("cannot observe malformed grid: " + "; ".join(basic))
    dividers = _full_divider_columns(grid)
    if len(dividers) != 1:
        raise ValueError(f"cannot observe grid with {len(dividers)} full dividers")
    axis = dividers[0]
    cells = _source_cells(grid, axis)
    components = _component_sets(cells)
    return {
        "grid_h": h,
        "grid_w": w,
        "n_cells": len(cells),
        "n_colors": len({grid[r][c] for r, c in cells}),
        "layout": "connected" if len(components) == 1 else "split" if len(components) == 2 else "other",
        "axis_position": "center" if axis == w // 2 else "off_center",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete declared input grammar and requested exact axes."""
    del difficulty
    errors, h, w = _basic_grid_errors(grid)
    if errors:
        return errors
    if not (5 <= h <= 12 and 9 <= w <= 15):
        errors.append(f"grid dimensions {h}x{w} outside 5..12 by 9..15")

    dividers = _full_divider_columns(grid)
    if len(dividers) != 1:
        errors.append(f"expected exactly one full color-9 divider, found {len(dividers)}")
        return errors
    axis = dividers[0]
    stray_nines = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 9 and c != axis
    ]
    if stray_nines:
        errors.append(f"found {len(stray_nines)} stray color-9 cells outside divider")

    span = min(axis, w - 1 - axis)
    if span < 3:
        errors.append("divider leaves fewer than three mirrorable columns per side")

    cells = _source_cells(grid, axis)
    if not 3 <= len(cells) <= 8:
        errors.append(f"expected 3..8 source cells, found {len(cells)}")
    colors = {grid[r][c] for r, c in cells}
    if not colors <= set(range(1, 9)):
        errors.append(f"source colors must be in 1..8, found {sorted(colors)}")
    if not 1 <= len(colors) <= 3:
        errors.append(f"expected 1..3 source colors, found {len(colors)}")

    right_cells = [
        (r, c)
        for r in range(h)
        for c in range(axis + 1, w)
        if grid[r][c] not in (0, 9)
    ]
    if right_cells:
        errors.append(f"right side must start empty, found {len(right_cells)} content cells")

    clipped: list[tuple[int, int, int]] = []
    occupied: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r, c in cells:
        mirror = 2 * axis - c
        if not 0 <= mirror < w:
            clipped.append((r, c, mirror))
        elif grid[r][mirror] != 0:
            occupied.append(((r, c), (r, mirror)))
    if clipped:
        errors.append(f"{len(clipped)} source cells have out-of-bounds mirrors")
    if occupied:
        errors.append(f"{len(occupied)} source cells have occupied mirror targets")

    components = _component_sets(cells)
    if len(components) not in (1, 2):
        errors.append(f"source union must have one or two components, found {len(components)}")
    if cells and max(axis - c for _, c in cells) < 2:
        errors.append("all source cells touch the divider; need an offset >=2 cue")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    if requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for name, value in requested.items():
                if name in observed and value is not None and observed[name] != value:
                    errors.append(
                        f"override {name} requested {value!r}, observed {observed[name]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical scale/palette manifold retained by the schedule."""
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    reasons: list[str] = []
    if (observed["grid_h"], observed["grid_w"]) not in _CANONICAL_SIZES:
        reasons.append(
            f"canonical dimensions are {_CANONICAL_SIZES}, got "
            f"{observed['grid_h']}x{observed['grid_w']}"
        )
    if observed["n_cells"] not in (3, 4):
        reasons.append(f"canonical source count is 3 or 4, got {observed['n_cells']}")
    if observed["n_colors"] != 1:
        reasons.append(f"canonical sources are monochrome, got {observed['n_colors']} colors")
    if observed["layout"] != "connected":
        reasons.append(f"canonical source is connected, got {observed['layout']}")
    if observed["axis_position"] != "center":
        reasons.append(f"canonical divider uses center profile, got {observed['axis_position']}")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid rule input: " + "; ".join(errors))
    axis = _full_divider_columns(grid)[0]
    out = deepcopy(grid)
    for r, c in _source_cells(grid, axis):
        out[r][2 * axis - c] = grid[r][c]
    return out


def _largest_component_only(grid) -> list[list[int]]:
    """Wrong canonical-fitting rival: reflect only the largest component."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    axis = _full_divider_columns(grid)[0]
    components = _component_sets(_source_cells(grid, axis))
    chosen = min(components, key=lambda cells: (-len(cells), min(cells)))
    out = deepcopy(grid)
    for r, c in chosen:
        out[r][2 * axis - c] = grid[r][c]
    return out


def _monochrome_copy(grid) -> list[list[int]]:
    """Wrong canonical-fitting rival: use the first source color everywhere."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    axis = _full_divider_columns(grid)[0]
    cells = sorted(_source_cells(grid, axis))
    color = grid[cells[0][0]][cells[0][1]]
    out = deepcopy(grid)
    for r, c in cells:
        out[r][2 * axis - c] = color
    return out


def _witness_split_source(grid) -> bool:
    try:
        return observe_overrides(grid)["layout"] == "split"
    except ValueError:
        return False


def _witness_multicolor_source(grid) -> bool:
    try:
        return int(observe_overrides(grid)["n_colors"]) > 1
    except ValueError:
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "largest_component_only": _largest_component_only,
    "monochrome_copy": _monochrome_copy,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "split_source": _witness_split_source,
    "multicolor_source": _witness_multicolor_source,
}
WITNESS_RIVALS = {
    "split_source": ["largest_component_only"],
    "multicolor_source": ["monochrome_copy"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Finite declared-rival check; never a universal induction claim."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
        return reasons
    true_query = rule_mirror(query["input"])
    if "output" in query and query["output"] != true_query:
        reasons.append("query output disagrees with the endpoint rule")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the endpoint rule")
            continue
        valid_demos.append(demo)
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if rival(query["input"]) == true_query:
            continue
        if not any(rival(demo["input"]) != demo["output"] for demo in valid_demos):
            reasons.append(
                f"query distinguishes {name!r}, but no demonstration refutes that rival"
            )
    return reasons


def _base_degenerate_grid(h: int = 6, w: int = 9, axis: int = 4) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][axis] = 9
    return grid


def _draw_from_degenerate(name: str, ctx) -> list[list[int]]:
    """Return deterministic malformed scenes that ``self_check`` must reject."""
    rng = ctx.draw_rng(f"degenerate_{name}")
    h = 6 + rng.randint(0, 2)
    w = 9 + 2 * rng.randint(0, 1)
    axis = w // 2
    grid = _base_degenerate_grid(h, w, axis)

    if name == "no_divider":
        for r in range(h):
            grid[r][axis] = 0
        grid[1][1] = 4
        grid[1][2] = 4
        grid[2][1] = 4
    elif name == "multiple_dividers":
        for r in range(h):
            grid[r][axis - 2] = 9
        grid[1][axis - 1] = 4
        grid[2][axis - 1] = 4
        grid[3][axis - 1] = 4
    elif name == "no_left_content":
        pass
    elif name == "right_content":
        grid[1][axis - 2] = 4
        grid[2][axis - 2] = 4
        grid[3][axis - 2] = 4
        grid[1][axis + 2] = 6
    elif name == "stray_divider_color":
        grid[1][axis - 3] = 4
        grid[2][axis - 3] = 4
        grid[3][axis - 3] = 4
        grid[0][0] = 9
    elif name == "clipped_reflection":
        for r in range(h):
            grid[r][axis] = 0
            grid[r][w - 2] = 9
        grid[1][0] = 4
        grid[2][0] = 4
        grid[3][0] = 4
    elif name == "three_components":
        for r, c in ((0, axis - 3), (h // 2, axis - 3), (h - 1, axis - 3)):
            grid[r][c] = 4
    elif name == "too_many_colors":
        for index, color in enumerate((1, 2, 3, 4)):
            grid[index][axis - 3] = color
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-linked near-misses retained for structural regression checks."""
    fixtures = []
    for index, name in enumerate(DEGENERATE_TEXTURES, start=1):
        ctx = gen_ctx(
            seed=700 + index,
            sample_index=index,
            version=VERSION,
            task_id=TASK_ID,
        )
        fixtures.append((name, _draw_from_degenerate(name, ctx)))
    return fixtures
