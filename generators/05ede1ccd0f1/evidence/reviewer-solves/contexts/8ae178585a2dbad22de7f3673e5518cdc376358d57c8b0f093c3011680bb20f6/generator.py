"""Source-bound generator for task 05ede1ccd0f1: mirror across a cyan wall.

The selected canonical Racket rule finds the first full-height color-8 column,
keeps the input, and copies every non-{0,8} cell strictly left of that column to
``(row, 2 * axis - col)`` when that destination is in bounds.  The source stays
in place, out-of-bounds reflections vanish, destination content is overwritten,
and isolated color-8 cells are not copied.

Ordinary even schedule slots stay close to the canonical demonstrations: one
connected single-color source object, an empty right side, canonical dimensions,
and a centered wall.  Odd slots are off-center semantic witnesses and rotate
through the lawful plain, overwrite, clipping, and off-axis-8 cases.  Those
slots also use multiple source colors/components.  Thus every three
demonstrations selected from a four-pair lesson refute the canonical shortcuts
"reflect about grid center," "mirror one color," and "mirror one component."
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "05ede1ccd0f1"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "55bc14a48684"

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))

SUMMARY = (
    "Preserve the input and the full-height cyan (8) divider. For every "
    "non-{0,8} cell strictly left of that divider, copy its color to the "
    "same row at column 2*axis-col when in bounds. Sources remain, clipped "
    "copies vanish, copied cells overwrite destination content, and off-axis "
    "8-cells are skipped."
)

INVARIANTS = [
    "exactly one full-height color-8 divider column, strictly inside the grid",
    "at least two non-{0,8} source cells occur left of the divider",
    "at least one source reflection lands in bounds, so the task is not identity",
    "ordinary canonical profiles contain one connected single-color source object",
]

HELPFUL_TEXTURES = ("plain", "clip", "right_content", "eight_decoy")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
RETAINED_NEGATIVE_FIXTURES = ("source_on_right",)
_SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8-slot schedule; canonical anchors use h=4..5",
        "valid": "4..12",
    },
    "grid_w": {
        "type": "int",
        "default": "8-slot schedule; canonical anchors use w=7,9,11",
        "valid": "6..16",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled connected source size",
        "valid": "2..8",
    },
    "texture": {
        "type": "str",
        "default": "plain canonical anchors plus scheduled edge cases",
        "valid": "|".join(HELPFUL_TEXTURES),
        "doc": (
            "plain: all copies fit on an empty right side; clip: both in-bounds "
            "and out-of-bounds copies; right_content: a true destination starts "
            "occupied and is overwritten; eight_decoy: an off-axis 8 is skipped"
        ),
    },
}

# Every declared axis combination is constructible.  The retained identity
# fixture is deliberately outside the valid texture domain.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Even slots are canonical-structure anchors.  Odd slots are guaranteed
# off-center witnesses; every cyclic length-4 window contains two of them, so
# every 3-demo holdout contains at least one witness.
_SCHEDULE = (
    {"dims": (5, 7),  "n_cells": 5, "texture": "plain",         "centered": True,  "colors": (2, 3, 4)},
    {"texture": "plain",         "centered": False, "colors": _SOURCE_COLORS},
    {"dims": (4, 9),  "n_cells": 4, "texture": "plain",         "centered": True,  "colors": (3, 4, 5)},
    {"texture": "right_content", "centered": False, "colors": _SOURCE_COLORS},
    {"dims": (5, 11), "n_cells": 6, "texture": "plain",         "centered": True,  "colors": (4, 5, 6)},
    {"texture": "clip",          "centered": False, "colors": _SOURCE_COLORS},
    {"dims": (5, 7),  "n_cells": 5, "texture": "plain",         "centered": True,  "colors": (1, 5, 7, 9)},
    {"texture": "eight_decoy",   "centered": False, "colors": _SOURCE_COLORS},
)

_ODD_DIMS = {
    "easy": ((5, 8), (6, 9), (6, 10)),
    "medium": ((7, 10), (8, 12), (8, 13)),
    "hard": ((9, 13), (10, 14), (12, 16)),
    None: ((6, 8), (7, 11), (9, 14)),
}


def _validate_sample_index(sample_index: Any) -> int:
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    return sample_index


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: int,
    lo: int,
    hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _draw_choice_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: Sequence[str],
) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, tuple(options)))
    return str(ctx.draw_choice(label, (default,)))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return _validate_sample_index(sample_index) % LESSON_SCHEDULE_PERIOD


def _scheduled_defaults(ctx, seed: int, sample_index: int, difficulty) -> dict[str, Any]:
    del seed
    slot = schedule_profile(0, sample_index, difficulty)
    spec = _SCHEDULE[slot]
    rng = ctx.draw_rng("scheduled-defaults")

    if "dims" in spec:
        h, w = spec["dims"]
        n_cells = int(spec["n_cells"])
    else:
        dims = _ODD_DIMS.get(difficulty, _ODD_DIMS[None])
        h, w = rng.choice(dims)
        n_cells = rng.randint(3, min(8, max(3, h)))

    return {
        "slot": slot,
        "grid_h": h,
        "grid_w": w,
        "n_cells": n_cells,
        "texture": spec["texture"],
        "centered": bool(spec["centered"]),
        "source_color": rng.choice(spec["colors"]),
    }


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            type(value) is int and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _axis_geometry(height: int, width: int, axis: int) -> dict[str, int]:
    safe_lo = max(0, 2 * axis - width + 1)
    return {
        "safe_lo": safe_lo,
        "safe_capacity": height * max(0, axis - safe_lo),
        "oob_capacity": height * safe_lo,
        "left_capacity": height * axis,
    }


def _axis_supports(height: int, width: int, axis: int, n_cells: int, texture: str) -> bool:
    if not 1 <= axis <= width - 2:
        return False
    geom = _axis_geometry(height, width, axis)
    if texture in ("plain", "right_content"):
        return geom["safe_capacity"] >= n_cells
    if texture == "eight_decoy":
        return geom["safe_capacity"] >= n_cells and geom["left_capacity"] >= n_cells + 1
    if texture == "clip":
        return (
            geom["safe_capacity"] >= 1
            and geom["oob_capacity"] >= 1
            and geom["left_capacity"] >= n_cells
        )
    raise ValueError(f"unknown texture {texture!r}")


def _choose_axis(
    height: int,
    width: int,
    n_cells: int,
    texture: str,
    *,
    centered: bool,
    rng,
) -> int:
    candidates = [
        axis
        for axis in range(1, width - 1)
        if _axis_supports(height, width, axis, n_cells, texture)
    ]
    if not candidates:
        raise ValueError(
            f"cannot place texture={texture!r}, n_cells={n_cells} in {height}x{width}"
        )

    if not centered:
        off_center = [axis for axis in candidates if 2 * axis != width - 1]
        if off_center:
            candidates = off_center
        # Prefer a conspicuously off-center legal wall, with deterministic
        # seed/index variation only among equal-distance candidates.
        farthest = max(abs(2 * axis - (width - 1)) for axis in candidates)
        candidates = [
            axis for axis in candidates
            if abs(2 * axis - (width - 1)) == farthest
        ]
    else:
        nearest = min(abs(2 * axis - (width - 1)) for axis in candidates)
        candidates = [
            axis for axis in candidates
            if abs(2 * axis - (width - 1)) == nearest
        ]
    return int(rng.choice(sorted(candidates)))


def _neighbors(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _connected_cells(
    allowed: set[tuple[int, int]],
    n_cells: int,
    rng,
    *,
    required: Sequence[tuple[int, int]] = (),
) -> set[tuple[int, int]]:
    if n_cells < 1 or len(allowed) < n_cells:
        raise ValueError("connected-cell request exceeds its legal region")
    required_set = set(required)
    if not required_set <= allowed or len(required_set) > n_cells:
        raise ValueError("required source cells are outside the legal region")

    if required_set:
        cells = set(required_set)
    else:
        cells = {rng.choice(sorted(allowed))}

    while len(cells) < n_cells:
        frontier = sorted({q for cell in cells for q in _neighbors(cell) if q in allowed - cells})
        if not frontier:
            raise AssertionError("connected source growth unexpectedly exhausted its frontier")
        cells.add(rng.choice(frontier))
    return cells


def _build_source_cells(
    height: int,
    width: int,
    axis: int,
    n_cells: int,
    texture: str,
    rng,
    *,
    top_anchored: bool,
) -> set[tuple[int, int]]:
    geom = _axis_geometry(height, width, axis)
    safe_lo = geom["safe_lo"]
    if texture in ("plain", "right_content", "eight_decoy"):
        allowed = {(r, c) for r in range(height) for c in range(safe_lo, axis)}
        required = ((0, axis - 1),) if top_anchored else ()
        return _connected_cells(allowed, n_cells, rng, required=required)

    if texture == "clip":
        # One adjacent pair straddles the in-bounds threshold.  Growing inside
        # the full left rectangle keeps the object connected while preserving
        # at least one clipped and at least one visible reflection.
        if safe_lo <= 0 or safe_lo >= axis:
            raise ValueError("clip texture requires both safe and clipped left columns")
        row = 0 if top_anchored else rng.randrange(height)
        required: tuple[tuple[int, int], ...] = (
            (row, safe_lo - 1),
            (row, safe_lo),
        )
        if n_cells >= 3:
            # Two safe cells of opposite checkerboard parity let a scheduled
            # multicolor clip example prove that every source color is copied.
            required += (((row + 1) % height, safe_lo),)
        allowed = {(r, c) for r in range(height) for c in range(axis)}
        return _connected_cells(allowed, n_cells, rng, required=required)

    raise ValueError(f"unknown texture {texture!r}")


def _different_source_color(source_color: int, rng) -> int:
    return int(rng.choice([color for color in _SOURCE_COLORS if color != source_color]))


def _paint_source(
    grid: list[list[int]],
    source_cells: set[tuple[int, int]],
    primary_color: int,
    *,
    multicolor: bool,
    rng,
) -> None:
    if not multicolor:
        for r, c in source_cells:
            grid[r][c] = primary_color
        return

    secondary_color = _different_source_color(primary_color, rng)
    parity0 = (min(source_cells)[0] + min(source_cells)[1]) % 2
    for r, c in source_cells:
        grid[r][c] = primary_color if (r + c) % 2 == parity0 else secondary_color


def _decorate_texture(
    grid: list[list[int]],
    axis: int,
    source_cells: set[tuple[int, int]],
    texture: str,
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    if texture == "right_content":
        # Occupy one true mirror destination with another color.  The authority
        # must overwrite it rather than requiring an empty right side.
        source = rng.choice(sorted(source_cells))
        r, c = source
        destination = (r, 2 * axis - c)
        grid[destination[0]][destination[1]] = _different_source_color(grid[r][c], rng)

        # When possible, retain one unrelated right-side cell as evidence that
        # non-destination content is preserved.
        mirror_targets = {(rr, 2 * axis - cc) for rr, cc in source_cells}
        untouched = [
            (rr, cc)
            for rr in range(h)
            for cc in range(axis + 1, w)
            if (rr, cc) not in mirror_targets and grid[rr][cc] == 0
        ]
        if untouched:
            rr, cc = rng.choice(untouched)
            first_source = min(source_cells)
            reference = grid[first_source[0]][first_source[1]]
            grid[rr][cc] = _different_source_color(reference, rng)

    elif texture == "eight_decoy":
        candidates = [
            (r, c)
            for r in range(h)
            for c in range(axis)
            if (r, c) not in source_cells
        ]
        if not candidates:
            raise AssertionError("eight_decoy axis selection left no decoy location")
        # Prefer a decoy separated from the wall so its exclusion is visually
        # distinct from the full divider.
        separated = [(r, c) for r, c in candidates if c < axis - 1]
        r, c = rng.choice(separated or candidates)
        grid[r][c] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    sample_index = _validate_sample_index(sample_index)
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(ctx, seed, sample_index, difficulty)

    h = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 4, 12)
    w = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 6, 16)
    n_cells = _draw_int_axis(ctx, overrides, "n_cells", defaults["n_cells"], 2, 8)
    texture = _draw_choice_axis(
        ctx,
        overrides,
        "texture",
        defaults["texture"],
        HELPFUL_TEXTURES,
    )

    layout_rng = ctx.draw_rng("layout")
    axis = _choose_axis(
        h,
        w,
        n_cells,
        texture,
        centered=defaults["centered"],
        rng=layout_rng,
    )
    source_cells = _build_source_cells(
        h,
        w,
        axis,
        n_cells,
        texture,
        layout_rng,
        top_anchored=not defaults["centered"],
    )
    source_color = int(defaults["source_color"])

    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][axis] = 8
    _paint_source(
        grid,
        source_cells,
        source_color,
        multicolor=not defaults["centered"],
        rng=layout_rng,
    )
    _decorate_texture(grid, axis, source_cells, texture, layout_rng)

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator emitted invalid grid: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_cells": n_cells,
        "texture": texture,
    }
    if observed != expected:
        raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "axis": None,
        "left_sources": (),
        "source_colors": (),
        "in_bounds_source_count": 0,
        "oob_source_count": 0,
        "right_cells": (),
        "right_cell_count": 0,
        "off_axis_eights": (),
        "off_axis_eight_count": 0,
        "texture": None,
    }
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts["height"], facts["width"] = h, w
    if not 4 <= h <= 12:
        errors.append(f"grid height must be 4..12, got {h}")
    if not 6 <= w <= 16:
        errors.append(f"grid width must be 6..16, got {w}")

    axes = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(axes) != 1:
        errors.append(f"expected exactly one full-height color-8 column, got {len(axes)}")
        return facts
    axis = axes[0]
    facts["axis"] = axis
    if not 0 < axis < w - 1:
        errors.append("the color-8 divider must be strictly inside the grid")

    left_sources = tuple(
        (r, c)
        for r in range(h)
        for c in range(axis)
        if grid[r][c] not in (0, 8)
    )
    facts["left_sources"] = left_sources
    facts["source_colors"] = tuple(sorted({grid[r][c] for r, c in left_sources}))
    if len(left_sources) < 2:
        errors.append(
            f"need at least 2 non-{{0,8}} source cells left of the divider, got {len(left_sources)}"
        )

    in_bounds = [(r, c) for r, c in left_sources if 0 <= 2 * axis - c < w]
    oob = [(r, c) for r, c in left_sources if not 0 <= 2 * axis - c < w]
    facts["in_bounds_source_count"] = len(in_bounds)
    facts["oob_source_count"] = len(oob)
    if not in_bounds:
        errors.append("at least one source reflection must land in bounds")

    right_cells = tuple(
        (r, c)
        for r in range(h)
        for c in range(axis + 1, w)
        if grid[r][c] != 0
    )
    off_axis_eights = tuple(
        (r, c)
        for r in range(h)
        for c in range(w)
        if c != axis and grid[r][c] == 8
    )
    facts["right_cells"] = right_cells
    facts["right_cell_count"] = len(right_cells)
    facts["off_axis_eights"] = off_axis_eights
    facts["off_axis_eight_count"] = len(off_axis_eights)

    if right_cells:
        facts["texture"] = "right_content"
    elif off_axis_eights:
        facts["texture"] = "eight_decoy"
    elif oob:
        facts["texture"] = "clip"
    else:
        facts["texture"] = "plain"
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Selected-source manifold plus the authority's explicit lawful edge cases."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": int(facts["height"]),
        "grid_w": int(facts["width"]),
        "n_cells": len(facts["left_sources"]),
        "texture": str(facts["texture"]),
    }


def _rule_axis_and_sources(grid: Any) -> tuple[int, tuple[tuple[int, int], ...]]:
    if not _is_arc_grid(grid):
        raise ValueError("grid must be a nonempty rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    axes = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not axes:
        raise ValueError("the selected Racket rule requires a full-height color-8 column")
    axis = axes[0]
    sources = tuple(
        (r, c)
        for r in range(h)
        for c in range(axis)
        if grid[r][c] not in (0, 8)
    )
    return axis, sources


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic Python translation of the pinned Racket authority."""
    axis, sources = _rule_axis_and_sources(grid)
    width = len(grid[0])
    out = deepcopy(grid)
    for r, c in sources:
        mirror_col = 2 * axis - c
        if 0 <= mirror_col < width:
            out[r][mirror_col] = grid[r][c]
    return out


def _mirror_about_grid_center(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical shortcut: ignore the wall position and use grid center."""
    try:
        _, sources = _rule_axis_and_sources(grid)
    except ValueError:
        return deepcopy(grid)
    width = len(grid[0])
    out = deepcopy(grid)
    for r, c in sources:
        out[r][width - 1 - c] = grid[r][c]
    return out


def _source_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    try:
        _, sources = _rule_axis_and_sources(grid)
    except ValueError:
        return []
    remaining = set(sources)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            cell = stack.pop()
            for q in _neighbors(cell):
                if q in remaining and grid[q[0]][q[1]] == color:
                    remaining.remove(q)
                    component.add(q)
                    stack.append(q)
        components.append(component)
    return components


def _mirror_first_source_color(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: copy only the lowest-valued source color."""
    try:
        axis, sources = _rule_axis_and_sources(grid)
    except ValueError:
        return deepcopy(grid)
    colors = sorted({grid[r][c] for r, c in sources})
    if not colors:
        return deepcopy(grid)
    chosen = colors[0]
    width = len(grid[0])
    out = deepcopy(grid)
    for r, c in sources:
        mirror_col = 2 * axis - c
        if grid[r][c] == chosen and 0 <= mirror_col < width:
            out[r][mirror_col] = grid[r][c]
    return out


def _mirror_first_source_component(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: reflect only one left-side component."""
    try:
        axis, _ = _rule_axis_and_sources(grid)
    except ValueError:
        return deepcopy(grid)
    components = _source_components(grid)
    if not components:
        return deepcopy(grid)
    chosen = min(components, key=lambda cells: min(cells))
    width = len(grid[0])
    out = deepcopy(grid)
    for r, c in chosen:
        mirror_col = 2 * axis - c
        if 0 <= mirror_col < width:
            out[r][mirror_col] = grid[r][c]
    return out


def _mirror_only_when_wall_is_first_foreground(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut tied to row-major foreground order."""
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    axis = int(facts["axis"])
    if any(grid[0][c] != 0 for c in range(axis)):
        return deepcopy(grid)
    return rule_mirror(grid)


def _witness_off_center_axis(grid: Any) -> bool:
    facts = _analyze(grid)
    return bool(
        not facts["errors"]
        and 2 * int(facts["axis"]) != int(facts["width"]) - 1
    )


def _witness_multiple_source_colors(grid: Any) -> bool:
    facts = _analyze(grid)
    return bool(not facts["errors"] and len(facts["source_colors"]) >= 2)


def _witness_multiple_source_components(grid: Any) -> bool:
    facts = _analyze(grid)
    return bool(not facts["errors"] and len(_source_components(grid)) >= 2)


def _witness_source_precedes_wall_in_scan(grid: Any) -> bool:
    facts = _analyze(grid)
    if facts["errors"]:
        return False
    axis = int(facts["axis"])
    return any(grid[0][c] not in (0, 8) for c in range(axis))


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "mirror_about_grid_center": _mirror_about_grid_center,
    "mirror_first_source_color": _mirror_first_source_color,
    "mirror_first_source_component": _mirror_first_source_component,
    "mirror_only_when_wall_is_first_foreground": _mirror_only_when_wall_is_first_foreground,
}
SEMANTIC_WITNESSES = {
    "off_center_axis": _witness_off_center_axis,
    "multiple_source_colors": _witness_multiple_source_colors,
    "multiple_source_components": _witness_multiple_source_components,
    "source_precedes_wall_in_scan": _witness_source_precedes_wall_in_scan,
}
WITNESS_RIVALS = {
    "off_center_axis": ["mirror_about_grid_center"],
    "multiple_source_colors": ["mirror_first_source_color"],
    "multiple_source_components": ["mirror_first_source_component"],
    "source_precedes_wall_in_scan": ["mirror_only_when_wall_is_first_foreground"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = strict_canonical_like(pair["input"])
    if errors:
        return [f"{label}: {reason}" for reason in errors]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label}: {exc}"]
    if pair["output"] != expected:
        return [f"{label}: output does not follow the pinned cyan-wall reflection rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where the canonical center-axis shortcut remains viable."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    if not any(_witness_off_center_axis(pair["input"]) for pair in demos):
        reasons.append("demonstrations never distinguish the cyan wall from the grid center")
    if not any(_witness_multiple_source_colors(pair["input"]) for pair in demos):
        reasons.append("demonstrations never prove that every non-cyan source color is copied")
    if not any(_witness_multiple_source_components(pair["input"]) for pair in demos):
        reasons.append("demonstrations never prove that every left-side source component is copied")
    if not any(_witness_source_precedes_wall_in_scan(pair["input"]) for pair in demos):
        reasons.append("demonstrations never break the canonical foreground scan order")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_every_demo = all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        )
        if fits_every_demo and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def generate_degenerate(seed, sample_index, name: str) -> list[list[int]]:
    """Retained negative fixture: content only right of the wall gives identity."""
    sample_index = _validate_sample_index(sample_index)
    if name not in RETAINED_NEGATIVE_FIXTURES:
        raise ValueError(f"unknown degenerate texture {name!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=f"{TASK_ID}:degenerate:{name}",
        overrides={},
    )
    rng = ctx.draw_rng("degenerate-layout")
    h = rng.randint(5, 8)
    w = rng.randint(7, 11)
    axis = rng.randint(1, w - 3)
    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][axis] = 8
    cells = [
        (r, c)
        for r in range(h)
        for c in range(axis + 1, w)
    ]
    rng.shuffle(cells)
    color = rng.choice(_SOURCE_COLORS)
    for r, c in cells[: rng.randint(2, min(4, len(cells)))]:
        grid[r][c] = color
    return grid
