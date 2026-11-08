"""Generator for ``38200022d1b7`` — copy by point reflection around color 5.

The unique gray cell is the pivot.  Every other nonzero input cell is retained
and copied, with its color unchanged, to the antipodal coordinate
``(2*pr-r, 2*pc-c)``.  A four-profile schedule preserves canonical two-blob
scenes while adding off-center pivots, axis evidence, and sources on multiple
sides of the pivot.  Those cases refute the strongest canonical-fitting
shortcuts: reflecting around the grid center and reflecting only cells above
the pivot.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "38200022d1b7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "514de6262239"

SUMMARY = (
    "Keep every source cell and copy it by 180-degree point reflection around "
    "the unique color-5 pivot. Canonical two-blob scenes are interleaved with "
    "off-center, axis-mixed, and multi-quadrant counterexamples."
)

INVARIANTS = [
    "background is 0 and there is exactly one color-5 pivot",
    "the pivot lies within one cell of the geometric grid center",
    "there are 4..8 source cells using exactly 2 or 3 non-{0,5} colors",
    "every reflected target is in bounds, blank, and disjoint from the source",
    "four consecutive draws cover canonical, off-center, axis, and multi-side evidence",
]

_LAYOUTS = (
    "canonical_two_blobs",
    "quadrant_blob",
    "axis_mix",
    "multi_quadrant",
)
SCHEDULE_PROFILES = _LAYOUTS
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 9..13 with canonical 9|10|11",
        "valid": "9..13",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 9..13 with canonical 9|10|11",
        "valid": "9..13",
    },
    "pivot_dr": {
        "type": "int",
        "default": "scheduled -1..1 relative to h//2",
        "valid": "-1..1",
    },
    "pivot_dc": {
        "type": "int",
        "default": "scheduled -1..1 relative to w//2",
        "valid": "-1..1",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 4..8; canonical 5|7",
        "valid": "4..8",
    },
    "n_colors": {
        "type": "int",
        "default": "scheduled 2|3; canonical 2",
        "valid": "2..3",
    },
    "layout_profile": {
        "type": "str",
        "default": "four-draw teaching schedule",
        "valid": "|".join(_LAYOUTS),
    },
}

# Radius-three templates fit every declared 9..13 grid and every pivot offset.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Prefixes of every template remain lawful for every n_cells in 4..8.
_CANONICAL_TEMPLATES = (
    (
        (-1, -2), (-1, -1), (-1, 1), (-1, 2),
        (-2, -2), (-2, 2), (-2, -1), (-2, 1),
    ),
    (
        (-1, -3), (-2, -3), (-1, 1), (-2, 1),
        (-2, -2), (-3, 1), (-3, -3), (-2, 2),
    ),
    (
        (-1, -1), (-2, -1), (-1, 2), (-2, 2),
        (-2, -2), (-3, 2), (-3, -1), (-2, 3),
    ),
)

_TEMPLATES = {
    "quadrant_blob": (
        (-1, -1), (-1, -2), (-2, -1), (-2, -2),
        (-3, -1), (-3, -2), (-2, -3), (-1, -3),
    ),
    "axis_mix": (
        (0, -1), (0, -2), (-1, 0), (-2, 0),
        (-1, -1), (-1, -2), (-2, -1), (-2, -2),
    ),
    "multi_quadrant": (
        (-1, -1), (1, -3), (-2, 1), (3, 1),
        (-1, -2), (2, -3), (-2, 2), (3, 2),
    ),
}

_CANONICAL_VARIANTS = (
    # height, width, source count, exact canonical palette
    (9, 9, 5, (2, 3)),
    (10, 10, 5, (1, 7)),
    (11, 11, 7, (4, 6)),
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Any four consecutive sample indexes contain all teaching profiles."""
    del seed, difficulty
    return _LAYOUTS[int(sample_index) % len(_LAYOUTS)]


def _profile_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    block = int(sample_index) // len(_LAYOUTS)
    if profile == "canonical_two_blobs":
        h, w, n_cells, palette = _CANONICAL_VARIANTS[block % len(_CANONICAL_VARIANTS)]
        return {
            "grid_h": h,
            "grid_w": w,
            "pivot_dr": 0,
            "pivot_dc": 0,
            "n_cells": n_cells,
            "n_colors": 2,
            "layout_profile": profile,
            "canonical_palette": palette,
        }

    base = {"easy": 9, "medium": 11, "hard": 13}.get(difficulty, 11)
    offsets = ((1, -1), (-1, 1), (1, 1), (-1, -1))
    pivot_dr, pivot_dc = offsets[block % len(offsets)]
    if profile == "quadrant_blob":
        return {
            "grid_h": base,
            "grid_w": min(13, base + 1),
            "pivot_dr": pivot_dr,
            "pivot_dc": pivot_dc,
            "n_cells": 4 + (block % 5),
            "n_colors": 2 + (block % 2),
            "layout_profile": profile,
            "canonical_palette": None,
        }
    if profile == "axis_mix":
        return {
            "grid_h": min(13, base + 1),
            "grid_w": base,
            "pivot_dr": pivot_dr,
            "pivot_dc": 0 if pivot_dc else 1,
            "n_cells": 4 + ((block + 2) % 5),
            "n_colors": 2 + ((block + 1) % 2),
            "layout_profile": profile,
            "canonical_palette": None,
        }
    return {
        "grid_h": max(10, base),
        "grid_w": max(10, base),
        "pivot_dr": pivot_dr,
        "pivot_dc": pivot_dc,
        "n_cells": 6 + (block % 3),
        "n_colors": 2 + (block % 2),
        "layout_profile": profile,
        "canonical_palette": None,
    }


def _scheduled_int(
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


def _scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: tuple[str, ...],
) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _transform(offset: tuple[int, int], orientation: int) -> tuple[int, int]:
    """Apply one of the eight D4 transforms to an offset."""
    dr, dc = offset
    if orientation >= 4:
        dc = -dc
    for _ in range(orientation % 4):
        dr, dc = dc, -dr
    return dr, dc


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _pivot_and_sources(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected exactly one color-5 pivot, found {len(pivots)}")
    sources = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    return pivots[0], sources


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    groups: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        group = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    queue.append(neighbor)
        groups.append(group)
    return groups


def _classify_layout(grid) -> str:
    try:
        (pr, pc), sources = _pivot_and_sources(grid)
    except (TypeError, ValueError):
        return "unclassified"
    if not sources:
        return "unclassified"
    offsets = [(r - pr, c - pc) for r, c in sources]
    components = _components(sources)

    if any(dr == 0 for dr, _ in offsets) and any(dc == 0 for _, dc in offsets):
        return "axis_mix"
    if (
        any(dr < 0 for dr, _ in offsets)
        and any(dr > 0 for dr, _ in offsets)
        and any(dc < 0 for _, dc in offsets)
        and any(dc > 0 for _, dc in offsets)
    ):
        return "multi_quadrant"
    if all(dr < 0 for dr, _ in offsets) and len(components) >= 2:
        return "canonical_two_blobs"
    one_quadrant = (
        (all(dr < 0 for dr, _ in offsets) or all(dr > 0 for dr, _ in offsets))
        and (all(dc < 0 for _, dc in offsets) or all(dc > 0 for _, dc in offsets))
    )
    if one_quadrant and len(components) == 1:
        return "quadrant_blob"
    return "unclassified"


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact AXES value from a generated input."""
    (pr, pc), sources = _pivot_and_sources(grid)
    colors = {grid[r][c] for r, c in sources}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "pivot_dr": pr - len(grid) // 2,
        "pivot_dc": pc - len(grid[0]) // 2,
        "n_cells": len(sources),
        "n_colors": len(colors),
        "layout_profile": _classify_layout(grid),
    }


def rule_mirror(grid):
    """Independent Python mirror of the selected row-major Racket rule."""
    (pr, pc), _ = _pivot_and_sources(grid)
    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5):
                continue
            rr, cc = 2 * pr - r, 2 * pc - c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-only inputs outside the teaching domain."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 9 <= height <= 13:
        errors.append(f"height {height} outside 9..13")
    if not 9 <= width <= 13:
        errors.append(f"width {width} outside 9..13")

    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-5 pivot, found {len(pivots)}")
        return errors
    pr, pc = pivots[0]
    pivot_dr, pivot_dc = pr - height // 2, pc - width // 2
    if pivot_dr not in (-1, 0, 1) or pivot_dc not in (-1, 0, 1):
        errors.append(
            f"pivot offset ({pivot_dr},{pivot_dc}) outside the center neighborhood"
        )

    sources = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if not 4 <= len(sources) <= 8:
        errors.append(f"expected 4..8 source cells, found {len(sources)}")
    colors = {grid[r][c] for r, c in sources}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2 or 3 source colors, found {len(colors)}")

    source_set = set(sources)
    for r, c in sources:
        rr, cc = 2 * pr - r, 2 * pc - c
        if not (0 <= rr < height and 0 <= cc < width):
            errors.append(f"reflection of ({r},{c}) is out of bounds: ({rr},{cc})")
        elif (rr, cc) in source_set or grid[rr][cc] != 0:
            errors.append(f"reflected target ({rr},{cc}) is occupied")

    profile = _classify_layout(grid)
    if profile not in _LAYOUTS:
        errors.append("source geometry does not match a declared layout profile")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the exact public morphology envelope, not only dimensions/palette."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = observe_overrides(grid)
    if (profile["grid_h"], profile["grid_w"]) not in {(9, 9), (10, 10), (11, 11)}:
        reasons.append(
            "canonical dimensions are 9x9, 10x10, or 11x11; found "
            f"{profile['grid_h']}x{profile['grid_w']}"
        )
    if (profile["pivot_dr"], profile["pivot_dc"]) != (0, 0):
        reasons.append("canonical pivot is at the geometric grid center")
    if profile["n_cells"] not in (5, 7):
        reasons.append(f"canonical source count is 5 or 7, found {profile['n_cells']}")
    if profile["n_colors"] != 2:
        reasons.append(f"canonical source color count is 2, found {profile['n_colors']}")

    (pr, _), sources = _pivot_and_sources(grid)
    if any(r >= pr for r, _ in sources):
        reasons.append("canonical sources are strictly above the pivot")
    component_count = len(_components(sources))
    if component_count not in (2, 3):
        reasons.append(f"canonical source component count is 2 or 3, found {component_count}")
    return reasons


def _copy_about(grid, center: tuple[int, int], *, predicate=lambda _r, _c: True):
    out = [list(row) for row in grid]
    pr, pc = center
    height, width = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5) or not predicate(r, c):
                continue
            rr, cc = 2 * pr - r, 2 * pc - c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
    return out


def _rival_grid_center(grid):
    return _copy_about(grid, (len(grid) // 2, len(grid[0]) // 2))


def _rival_above_only(grid):
    (pr, pc), _ = _pivot_and_sources(grid)
    return _copy_about(grid, (pr, pc), predicate=lambda r, _c: r < pr)


def _rival_move_instead_of_copy(grid):
    (pr, pc), sources = _pivot_and_sources(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    out[pr][pc] = 5
    for r, c in sources:
        out[2 * pr - r][2 * pc - c] = grid[r][c]
    return out


def _rival_horizontal_only(grid):
    (pr, pc), sources = _pivot_and_sources(grid)
    out = [list(row) for row in grid]
    for r, c in sources:
        out[r][2 * pc - c] = grid[r][c]
    return out


def _rival_vertical_only(grid):
    (pr, pc), sources = _pivot_and_sources(grid)
    out = [list(row) for row in grid]
    for r, c in sources:
        out[2 * pr - r][c] = grid[r][c]
    return out


def _rival_largest_component_only(grid):
    (pr, pc), sources = _pivot_and_sources(grid)
    groups = _components(sources)
    chosen = min(groups, key=lambda group: (-len(group), sorted(group)))
    out = [list(row) for row in grid]
    for r, c in chosen:
        out[2 * pr - r][2 * pc - c] = grid[r][c]
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "grid_center": _rival_grid_center,
    "above_only": _rival_above_only,
    "move_instead_of_copy": _rival_move_instead_of_copy,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "largest_component_only": _rival_largest_component_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "grid_center": _rival_grid_center,
    "above_only": _rival_above_only,
}


def _valid_and_disagrees(grid, rival: Callable) -> bool:
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "off_center_pivot_refutes_grid_center": lambda grid: (
        not self_check(grid)
        and _pivot_and_sources(grid)[0] != (len(grid) // 2, len(grid[0]) // 2)
        and _rival_grid_center(grid) != rule_mirror(grid)
    ),
    "non_above_source_refutes_above_only": lambda grid: _valid_and_disagrees(
        grid, _rival_above_only
    ),
    "retained_source_refutes_move": lambda grid: _valid_and_disagrees(
        grid, _rival_move_instead_of_copy
    ),
    "point_reflection_refutes_axis_mirrors": lambda grid: (
        _valid_and_disagrees(grid, _rival_horizontal_only)
        and _valid_and_disagrees(grid, _rival_vertical_only)
    ),
    "multiple_components_refute_largest_only": lambda grid: (
        not self_check(grid)
        and len(_components(_pivot_and_sources(grid)[1])) >= 2
        and _rival_largest_component_only(grid) != rule_mirror(grid)
    ),
}

WITNESS_RIVALS = {
    "off_center_pivot_refutes_grid_center": ["grid_center"],
    "non_above_source_refutes_above_only": ["above_only"],
    "retained_source_refutes_move": ["move_instead_of_copy"],
    "point_reflection_refutes_axis_mirrors": ["horizontal_only", "vertical_only"],
    "multiple_components_refute_largest_only": ["largest_component_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demonstrations that collectively refute every competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact point-reflection copy")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")

    defaults = _profile_defaults(int(sample_index), difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, overrides, "grid_h", defaults["grid_h"], 9, 13)
    width = _scheduled_int(ctx, overrides, "grid_w", defaults["grid_w"], 9, 13)
    pivot_dr = _scheduled_int(ctx, overrides, "pivot_dr", defaults["pivot_dr"], -1, 1)
    pivot_dc = _scheduled_int(ctx, overrides, "pivot_dc", defaults["pivot_dc"], -1, 1)
    n_cells = _scheduled_int(ctx, overrides, "n_cells", defaults["n_cells"], 4, 8)
    n_colors = _scheduled_int(ctx, overrides, "n_colors", defaults["n_colors"], 2, 3)
    profile = _scheduled_choice(
        ctx,
        overrides,
        "layout_profile",
        defaults["layout_profile"],
        _LAYOUTS,
    )

    pivot = (height // 2 + pivot_dr, width // 2 + pivot_dc)
    layout_rng = ctx.draw_rng("layout")
    if profile == "canonical_two_blobs":
        template = layout_rng.choice(_CANONICAL_TEMPLATES)
        offsets = list(template[:n_cells])
    else:
        orientation = layout_rng.randrange(8)
        offsets = [_transform(offset, orientation) for offset in _TEMPLATES[profile][:n_cells]]

    positions = [(pivot[0] + dr, pivot[1] + dc) for dr, dc in offsets]
    reflected = [(2 * pivot[0] - r, 2 * pivot[1] - c) for r, c in positions]
    if (
        len(set(positions)) != n_cells
        or any(not (0 <= r < height and 0 <= c < width) for r, c in positions + reflected)
        or set(positions) & set(reflected)
        or pivot in positions
    ):
        raise RuntimeError(
            f"internal template escaped or overlapped: profile={profile} "
            f"grid={height}x{width} pivot={pivot} positions={positions}"
        )

    canonical_palette = defaults.get("canonical_palette")
    if profile == "canonical_two_blobs" and n_colors == 2 and canonical_palette:
        palette = list(canonical_palette)
        if layout_rng.randrange(2):
            palette.reverse()
        assignments = [palette[0] if dc < 0 else palette[1] for _, dc in offsets]
    else:
        palette = list(ctx.draw_distinct_colors("palette", n=n_colors, exclude={0, 5}))
        assignments = list(palette)
        assignments.extend(layout_rng.choice(palette) for _ in range(n_cells - n_colors))
        layout_rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    grid[pivot[0]][pivot[1]] = 5
    for (r, c), color in zip(positions, assignments):
        grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "pivot_dr": pivot_dr,
        "pivot_dc": pivot_dc,
        "n_cells": n_cells,
        "n_colors": n_colors,
        "layout_profile": profile,
    }
    if observed != requested:
        raise RuntimeError(f"internal override mismatch: requested={requested}, observed={observed}")
    return grid
