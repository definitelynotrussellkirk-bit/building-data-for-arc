"""Generator for ARC task ``0da360b839c1`` — point reflection about 9.

The unique maroon cell (9) is the point-reflection anchor.  Every other
non-zero cell moves to the antipodal coordinate ``(2*ar-r, 2*ac-c)``; the
source location is erased and the anchor remains.  A four-profile schedule
makes complete lessons refute shortcuts that fit the public examples:
reflecting only cells above the anchor and refusing occupied destinations.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0da360b839c1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "05f942009299"

SUMMARY = (
    "Move every nonzero, non-9 cell to its 180-degree point reflection around "
    "the unique 9 anchor, erasing the source.  Four scheduled layouts include "
    "off-center anchors, disconnected sources, anchor-axis cells, and occupied "
    "antipodal destinations so each four-demo lesson refutes named shortcuts."
)

INVARIANTS = [
    "background is 0 and every cell is an integer ARC color 0..9",
    "there is exactly one 9 anchor within one cell of the grid center",
    "there are 3..8 colored source cells using 2..3 non-anchor colors",
    "every antipodal destination is in bounds",
    "the intended point-reflection output is non-identity",
]

_LAYOUTS = ("one_side", "split_side", "axis_cross", "swap_pair")
SCHEDULE_PROFILES = _LAYOUTS
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 7|8|9|10..13", "valid": "7..13"},
    "grid_w": {"type": "int", "default": "scheduled 7|8|9|10..13", "valid": "7..13"},
    "anchor_dr": {"type": "int", "default": "scheduled -1..1", "valid": "-1..1"},
    "anchor_dc": {"type": "int", "default": "scheduled -1..1", "valid": "-1..1"},
    "n_cells": {"type": "int", "default": "scheduled 4..8", "valid": "4..8"},
    "n_colors": {"type": "int", "default": "scheduled 2|3", "valid": "2..3"},
    "layout_profile": {
        "type": "str",
        "default": "four-draw teaching schedule",
        "valid": "|".join(_LAYOUTS),
    },
}

# Every boundary cross-product is constructible on a 7x7 or larger grid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Offset templates are ordered.  For swap_pair the first two positions are an
# occupied antipodal pair and receive different colors by construction.
_TEMPLATES: dict[str, tuple[tuple[int, int], ...]] = {
    "one_side": (
        (-1, -1), (-1, 0), (-1, 1), (-2, 0),
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    ),
    "split_side": (
        (-1, -2), (-2, -2), (-1, 2), (-2, 2),
        (-2, -1), (-2, 1), (-1, -1), (-1, 1),
    ),
    "axis_cross": (
        (-1, 0), (-2, 0), (0, 1), (0, 2),
        (-1, 1), (-2, 1), (-1, 2), (-2, 2),
    ),
    "swap_pair": (
        (-1, -1), (1, 1), (-1, 0), (-2, 0),
        (-2, -1), (1, 0), (2, 0), (2, 1),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Any four consecutive sample indexes contain every teaching profile."""
    del seed, difficulty
    return _LAYOUTS[int(sample_index) % len(_LAYOUTS)]


def _profile_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    if profile == "one_side":
        return dict(grid_h=7, grid_w=7, anchor_dr=0, anchor_dc=0,
                    n_cells=4, n_colors=2, layout_profile=profile)
    if profile == "split_side":
        return dict(grid_h=8, grid_w=8, anchor_dr=0, anchor_dc=1,
                    n_cells=4, n_colors=2, layout_profile=profile)
    if profile == "axis_cross":
        return dict(grid_h=9, grid_w=9, anchor_dr=0, anchor_dc=0,
                    n_cells=4, n_colors=2, layout_profile=profile)

    # Generalization profile: vary size and support cardinality deterministically
    # without weakening the four-residue semantic schedule.
    block = int(sample_index) // len(_LAYOUTS)
    base_h, base_w = {
        "easy": (10, 11),
        "medium": (11, 12),
        "hard": (13, 13),
    }.get(difficulty, (11, 12))
    return dict(
        grid_h=max(10, min(13, base_h - (block % 2))),
        grid_w=max(10, min(13, base_w - ((block // 2) % 2))),
        anchor_dr=1,
        anchor_dc=-1,
        n_cells=4 + (block % 5),
        n_colors=3,
        layout_profile=profile,
    )


def _scheduled_int(ctx, overrides: dict[str, Any], label: str,
                   default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, overrides: dict[str, Any], label: str,
                      default: str, choices: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (default,))


def _rotate(offset: tuple[int, int], turns: int) -> tuple[int, int]:
    dr, dc = offset
    for _ in range(turns % 4):
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


def colored_cells_and_anchor(grid) -> tuple[list[tuple[int, int]], tuple[int, int]]:
    """Return non-{0,9} coordinates and the unique anchor; raise if malformed."""
    anchors = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        raise ValueError(f"expected exactly one 9 anchor, found {len(anchors)}")
    cells = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    return cells, anchors[0]


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
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


def _classify_layout(grid) -> str | None:
    try:
        cells, (ar, ac) = colored_cells_and_anchor(grid)
    except (TypeError, ValueError):
        return None
    cell_set = set(cells)
    if any((2 * ar - r, 2 * ac - c) in cell_set for r, c in cells):
        return "swap_pair"
    offsets = [(r - ar, c - ac) for r, c in cells]
    if any(dr == 0 for dr, _ in offsets) and any(dc == 0 for _, dc in offsets):
        return "axis_cross"
    one_open_halfplane = any((
        all(dr < 0 for dr, _ in offsets),
        all(dr > 0 for dr, _ in offsets),
        all(dc < 0 for _, dc in offsets),
        all(dc > 0 for _, dc in offsets),
    ))
    if one_open_halfplane:
        n_components = len(_components(cell_set))
        if n_components == 1:
            return "one_side"
        if n_components == 2:
            return "split_side"
    return None


def observe_overrides(grid) -> dict[str, int | str]:
    cells, (ar, ac) = colored_cells_and_anchor(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "anchor_dr": ar - len(grid) // 2,
        "anchor_dc": ac - len(grid[0]) // 2,
        "n_cells": len(cells),
        "n_colors": len({grid[r][c] for r, c in cells}),
        "layout_profile": _classify_layout(grid) or "unclassified",
    }


def rule_mirror(grid):
    """Independent Python mirror for tests; selected Racket remains authority."""
    cells, (ar, ac) = colored_cells_and_anchor(grid)
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    out[ar][ac] = 9
    for r, c in cells:
        nr, nc = 2 * ar - r, 2 * ac - c
        if 0 <= nr < height and 0 <= nc < width:
            out[nr][nc] = grid[r][c]
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, rule-hiding, and out-of-domain point-reflection inputs."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 7 <= height <= 13:
        errors.append(f"height {height} outside 7..13")
    if not 7 <= width <= 13:
        errors.append(f"width {width} outside 7..13")

    anchors = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor, found {len(anchors)}")
        return errors
    ar, ac = anchors[0]
    anchor_dr, anchor_dc = ar - height // 2, ac - width // 2
    if anchor_dr not in (-1, 0, 1) or anchor_dc not in (-1, 0, 1):
        errors.append(
            f"anchor offset ({anchor_dr},{anchor_dc}) outside the center-neighborhood"
        )

    cells = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not 3 <= len(cells) <= 8:
        errors.append(f"expected 3..8 colored source cells, found {len(cells)}")
    colors = {grid[r][c] for r, c in cells}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2..3 non-anchor colors, found {len(colors)}")

    for r, c in cells:
        nr, nc = 2 * ar - r, 2 * ac - c
        if not (0 <= nr < height and 0 <= nc < width):
            errors.append(
                f"colored cell ({r},{c}) reflects out of bounds to ({nr},{nc})"
            )
            break

    profile = _classify_layout(grid)
    if profile not in _LAYOUTS:
        errors.append("source support does not match any declared layout profile")

    if not errors:
        try:
            if rule_mirror(grid) == [list(row) for row in grid]:
                errors.append("point reflection is identity on this input")
        except Exception as exc:  # defensive: malformed grids should not escape
            errors.append(f"point-reflection oracle raised: {type(exc).__name__}: {exc}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The measured public manifold: exact dimensions/palette and 3..4 sources."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = observe_overrides(grid)
    if (profile["grid_h"], profile["grid_w"]) not in {(7, 7), (8, 8), (9, 9)}:
        reasons.append(
            f"canonical dimensions are 7x7, 8x8, or 9x9; found "
            f"{profile['grid_h']}x{profile['grid_w']}"
        )
    if profile["n_colors"] != 2:
        reasons.append(f"canonical non-anchor color count is 2, found {profile['n_colors']}")
    if profile["n_cells"] not in (3, 4):
        reasons.append(f"canonical source-cell count is 3 or 4, found {profile['n_cells']}")
    return reasons


def _blank_with_anchor(grid) -> tuple[list[list[int]], list[tuple[int, int]], tuple[int, int]]:
    cells, anchor = colored_cells_and_anchor(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    out[anchor[0]][anchor[1]] = 9
    return out, cells, anchor


def _rival_grid_center(grid):
    out, cells, anchor = _blank_with_anchor(grid)
    cr, cc = len(grid) // 2, len(grid[0]) // 2
    for r, c in cells:
        nr, nc = 2 * cr - r, 2 * cc - c
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
            out[nr][nc] = grid[r][c]
    return out


def _rival_above_only(grid):
    out, cells, (ar, ac) = _blank_with_anchor(grid)
    for r, c in cells:
        if r < ar:
            out[2 * ar - r][2 * ac - c] = grid[r][c]
    return out


def _rival_empty_destination_only(grid):
    out, cells, (ar, ac) = _blank_with_anchor(grid)
    occupied = set(cells)
    for r, c in cells:
        nr, nc = 2 * ar - r, 2 * ac - c
        if (nr, nc) not in occupied:
            out[nr][nc] = grid[r][c]
    return out


def _rival_copy_and_reflect(grid):
    out = [list(row) for row in grid]
    cells, (ar, ac) = colored_cells_and_anchor(grid)
    for r, c in cells:
        out[2 * ar - r][2 * ac - c] = grid[r][c]
    return out


def _rival_horizontal_only(grid):
    out, cells, (ar, ac) = _blank_with_anchor(grid)
    for r, c in cells:
        out[r][2 * ac - c] = grid[r][c]
    return out


def _rival_vertical_only(grid):
    out, cells, (ar, ac) = _blank_with_anchor(grid)
    for r, c in cells:
        out[2 * ar - r][c] = grid[r][c]
    return out


def _rival_largest_component_only(grid):
    out, cells, (ar, ac) = _blank_with_anchor(grid)
    components = _components(set(cells))
    if not components:
        return out
    chosen = min(components, key=lambda group: (-len(group), sorted(group)))
    for r, c in chosen:
        out[2 * ar - r][2 * ac - c] = grid[r][c]
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "grid_center": _rival_grid_center,
    "above_only": _rival_above_only,
    "empty_destination_only": _rival_empty_destination_only,
    "copy_and_reflect": _rival_copy_and_reflect,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "largest_component_only": _rival_largest_component_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "above_only": _rival_above_only,
    "empty_destination_only": _rival_empty_destination_only,
}


def _valid_and_disagrees(grid, rival: Callable) -> bool:
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "off_center_anchor_refutes_grid_center": lambda grid: (
        not self_check(grid)
        and colored_cells_and_anchor(grid)[1] != (len(grid) // 2, len(grid[0]) // 2)
        and _rival_grid_center(grid) != rule_mirror(grid)
    ),
    "non_above_source_refutes_above_only": lambda grid: _valid_and_disagrees(
        grid, _rival_above_only
    ),
    "occupied_antipode_refutes_empty_destination": lambda grid: _valid_and_disagrees(
        grid, _rival_empty_destination_only
    ),
    "erasure_refutes_copy_and_reflect": lambda grid: _valid_and_disagrees(
        grid, _rival_copy_and_reflect
    ),
    "point_symmetry_refutes_axis_mirrors": lambda grid: (
        _valid_and_disagrees(grid, _rival_horizontal_only)
        and _valid_and_disagrees(grid, _rival_vertical_only)
    ),
    "disconnected_source_refutes_largest_component": lambda grid: (
        not self_check(grid)
        and len(_components(set(colored_cells_and_anchor(grid)[0]))) >= 2
        and _rival_largest_component_only(grid) != rule_mirror(grid)
    ),
}

WITNESS_RIVALS = {
    "off_center_anchor_refutes_grid_center": ["grid_center"],
    "non_above_source_refutes_above_only": ["above_only"],
    "occupied_antipode_refutes_empty_destination": ["empty_destination_only"],
    "erasure_refutes_copy_and_reflect": ["copy_and_reflect"],
    "point_symmetry_refutes_axis_mirrors": ["horizontal_only", "vertical_only"],
    "disconnected_source_refutes_largest_component": ["largest_component_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively refute every declared competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    profiles: set[str] = set()
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
            reasons.append(f"demo {index} output is not the exact point reflection")
            continue
        profiles.add(str(observe_overrides(demo["input"])["layout_profile"]))
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected

    missing_profiles = sorted(set(SCHEDULE_PROFILES) - profiles)
    if missing_profiles:
        reasons.append(f"demonstrations omit scheduled profile(s): {missing_profiles}")
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
    height = _scheduled_int(ctx, overrides, "grid_h", defaults["grid_h"], 7, 13)
    width = _scheduled_int(ctx, overrides, "grid_w", defaults["grid_w"], 7, 13)
    anchor_dr = _scheduled_int(ctx, overrides, "anchor_dr", defaults["anchor_dr"], -1, 1)
    anchor_dc = _scheduled_int(ctx, overrides, "anchor_dc", defaults["anchor_dc"], -1, 1)
    n_cells = _scheduled_int(ctx, overrides, "n_cells", defaults["n_cells"], 4, 8)
    n_colors = _scheduled_int(ctx, overrides, "n_colors", defaults["n_colors"], 2, 3)
    profile = _scheduled_choice(
        ctx, overrides, "layout_profile", defaults["layout_profile"], _LAYOUTS
    )

    anchor = (height // 2 + anchor_dr, width // 2 + anchor_dc)
    orientation = ctx.draw_rng("orientation").randrange(4)
    offsets = [_rotate(offset, orientation) for offset in _TEMPLATES[profile][:n_cells]]
    positions = [(anchor[0] + dr, anchor[1] + dc) for dr, dc in offsets]
    reflected = [(2 * anchor[0] - r, 2 * anchor[1] - c) for r, c in positions]
    if any(not (0 <= r < height and 0 <= c < width) for r, c in positions + reflected):
        raise RuntimeError(
            f"internal template escaped {height}x{width} at anchor {anchor}: {positions}"
        )

    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={0, 9})
    assignment_rng = ctx.draw_rng("color_assignment")
    if profile == "swap_pair":
        assignments = [palette[0], palette[1]]
        tail = [palette[index % n_colors] for index in range(2, n_cells)]
        assignment_rng.shuffle(tail)
        assignments.extend(tail)
    else:
        assignments = list(palette)
        assignments.extend(assignment_rng.choice(palette) for _ in range(n_cells - n_colors))
        assignment_rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    grid[anchor[0]][anchor[1]] = 9
    for (r, c), color in zip(positions, assignments):
        grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "anchor_dr": anchor_dr,
        "anchor_dc": anchor_dc,
        "n_cells": n_cells,
        "n_colors": n_colors,
        "layout_profile": profile,
    }
    if observed != requested:
        raise RuntimeError(f"internal override mismatch: requested={requested}, observed={observed}")
    return grid
