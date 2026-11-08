"""Generator for ARC task 4ff4c9da / task-local id d3575d4206d7.

Uniform full rows and columns partition the input into rectangular panels.  A
panel containing cyan (8) supplies a mask.

Primary branch
--------------
For an unmarked panel of the same shape to be a *match*, it must agree with the
marked panel outside the cyan mask and hold one uniform non-zero color under the
mask.  The first match fixes the target color.  Matching panels in the marked
column select panel-row indices; matching panels in the marked row select
panel-column indices.  Cyan is stamped into every same-size, unmarked panel at
the Cartesian product of those selected rows and columns when its masked cells
already hold the target color.  Agreement outside the mask is only needed for
row/column selection, not for the final Cartesian-product panels.

Secondary branch
----------------
Only when there are no primary matches, a marked panel with a completely cyan
row activates the fallback.  Among unmarked panels in the same panel-column and
of the same width, collect all uniform row colors and choose their mode.  Paint
a panel's row only when that panel has exactly one row entirely equal to the
modal color.

The canonical Racket program remains the sole output authority.  ``rule_mirror``
is a test-only, independently implemented Python mirror used to audit generated
lessons and semantic rivals.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d3575d4206d7"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "abf875129734"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Use cyan panel masks on a uniform-divider lattice. Exact outside-mask "
    "matches select target panel rows and columns for a Cartesian-product "
    "stamp; when no such match exists, a full cyan row invokes a same-column "
    "modal-uniform-row fallback with an exactly-one-hit guard."
)

INVARIANTS = [
    "all full divider rows and columns use one non-cyan divider color",
    "cyan occurs only inside panels and every cyan-bearing panel activates exactly one rule branch",
    "primary scenes contain row and column selectors, a non-exact Cartesian intersection, and a global target-color decoy",
    "secondary scenes contain same-column unique-row targets, a duplicate-row guard, and an off-column decoy",
    "ordinary three-demo lessons contrast first-minority and first-majority primary match colors",
    "the output is non-identical and changes only non-cyan cells to cyan",
    "generated inputs use one of the four canonical shape/lattice profiles and exactly four colors",
]

Grid = list[list[int]]
Panel = dict[str, Any]
Trace = dict[str, Any]

LAYOUTS = ("canonical_17", "canonical_21", "canonical_23", "canonical_27")
SCENE_MODES = ("primary", "secondary", "mixed")
SIGNAL_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
DIVIDER_COLORS = (0, 1, 2, 3, 4, 5, 6, 7, 9)

# Segment lengths between divider lines.  canonical_27 ends with a divider,
# exactly as the held-out canonical example does.
_LAYOUT_SPECS: dict[str, tuple[tuple[int, ...], bool]] = {
    "canonical_17": ((3, 3, 3, 3, 1), False),
    "canonical_21": ((3, 3, 3, 3, 3, 1), False),
    "canonical_23": ((3, 1, 1, 3, 3, 1, 1, 3), False),
    "canonical_27": ((2, 2, 2, 2, 2, 2, 2, 2, 2), True),
}
_SHAPE_TO_LAYOUT = {17: "canonical_17", 21: "canonical_21", 23: "canonical_23", 27: "canonical_27"}
_SCENE_SCHEDULE = ("primary", "mixed", "mixed", "mixed")
_LAYOUT_SCHEDULE = {
    None: ("canonical_23", "canonical_21", "canonical_17", "canonical_27"),
    "easy": ("canonical_17", "canonical_21", "canonical_17", "canonical_21"),
    "medium": ("canonical_21", "canonical_23", "canonical_17", "canonical_23"),
    "hard": ("canonical_23", "canonical_27", "canonical_21", "canonical_27"),
}
SCHEDULE_PROFILES = (
    "canonical_17:primary",
    "canonical_17:mixed",
    "canonical_21:primary",
    "canonical_21:mixed",
    "canonical_23:primary",
    "canonical_23:mixed",
    "canonical_27:mixed",
)

AXES = {
    "layout": {
        "type": "str",
        "default": "difficulty-aware four-step canonical profile schedule",
        "valid": "|".join(LAYOUTS),
    },
    "scene_mode": {
        "type": "str",
        "default": "four-step primary|mixed|mixed|mixed teaching schedule",
        "valid": "|".join(SCENE_MODES),
    },
    "signal_color": {
        "type": "color",
        "default": "keyed draw from nonzero non-cyan ARC colors",
        "valid": "1..7|9",
    },
    "divider_color": {
        "type": "color",
        "default": "keyed draw from non-cyan ARC colors",
        "valid": "0..7|9",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the deterministic teaching schedule to semantic tooling."""
    del seed
    if difficulty not in _LAYOUT_SCHEDULE:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    index = int(sample_index) % len(_SCENE_SCHEDULE)
    return f"{_LAYOUT_SCHEDULE[difficulty][index]}:{_SCENE_SCHEDULE[index]}"


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _LAYOUT_SCHEDULE:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["grid rows must be lists"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _ranges_between(dividers: Iterable[int], total: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    previous = -1
    for divider in sorted(dividers):
        if previous + 1 <= divider - 1:
            ranges.append((previous + 1, divider - 1))
        previous = divider
    if previous + 1 <= total - 1:
        ranges.append((previous + 1, total - 1))
    return ranges


def _panelize(grid: Grid) -> dict[str, Any]:
    h, w = len(grid), len(grid[0])
    uniform_rows = [r for r in range(h) if len(set(grid[r])) == 1]
    uniform_cols = [c for c in range(w) if len({grid[r][c] for r in range(h)}) == 1]
    row_ranges = _ranges_between(uniform_rows, h)
    col_ranges = _ranges_between(uniform_cols, w)
    panels: list[Panel] = []
    for ri, (r1, r2) in enumerate(row_ranges):
        for ci, (c1, c2) in enumerate(col_ranges):
            pattern = [list(grid[r][c1 : c2 + 1]) for r in range(r1, r2 + 1)]
            panels.append(
                {
                    "ri": ri,
                    "ci": ci,
                    "r1": r1,
                    "c1": c1,
                    "h": r2 - r1 + 1,
                    "w": c2 - c1 + 1,
                    "pat": pattern,
                    "has8": any(value == 8 for row in pattern for value in row),
                }
            )
    return {
        "uniform_rows": uniform_rows,
        "uniform_cols": uniform_cols,
        "row_ranges": row_ranges,
        "col_ranges": col_ranges,
        "panels": panels,
    }


def _mask_positions(panel: Panel) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(panel["h"])
        for c in range(panel["w"])
        if panel["pat"][r][c] == 8
    ]


def _mask_value(panel: Panel, mask: list[tuple[int, int]]) -> int | None:
    values = {panel["pat"][r][c] for r, c in mask}
    return next(iter(values)) if len(values) == 1 else None


def _agrees_outside(marked: Panel, other: Panel, mask: list[tuple[int, int]]) -> bool:
    mask_set = set(mask)
    return all(
        marked["pat"][r][c] == other["pat"][r][c]
        for r in range(marked["h"])
        for c in range(marked["w"])
        if (r, c) not in mask_set
    )


def _mode_first(values: list[int]) -> int | None:
    """Mirror pinned Racket 8.10 mode-list on this four-color input profile.

    The historical function name is retained; ties are NOT first-seen.
    mode-list sorts hash entries by descending frequency. Its small table
    visits integer buckets modulo eight, with colliding keys in reverse first
    insertion order. This was checked on every insertion order of up to three
    noncyan ARC colors and on actual reference-labelled grids. Four input
    colors including cyan permit at most three distinct fallback row colors.
    Wider tied palettes need the Racket authority, not an extrapolated mirror.
    """
    if not values:
        return None
    counts = Counter(values)
    best = max(counts.values())
    tied = [value for value in counts if counts[value] == best]
    if len(tied) == 1:
        return tied[0]
    if len(counts) > 3:
        raise ValueError("Racket tie mirror is calibrated for at most three distinct row colors")
    first_index = {value: values.index(value) for value in counts}
    return min(tied, key=lambda value: (value % 8, -first_index[value]))


def _trace_marker(panels: list[Panel], marked: Panel) -> Trace:
    mask = _mask_positions(marked)
    same_shape = [
        panel
        for panel in panels
        if not panel["has8"]
        and panel["h"] == marked["h"]
        and panel["w"] == marked["w"]
    ]
    matches = [
        panel
        for panel in same_shape
        if _agrees_outside(marked, panel, mask)
        and (_mask_value(panel, mask) is not None)
        and int(_mask_value(panel, mask)) > 0
    ]
    if matches:
        target = _mask_value(matches[0], mask)
        assert target is not None
        target_rows = {marked["ri"]}
        target_rows.update(
            panel["ri"]
            for panel in matches
            if panel["ci"] == marked["ci"] and _mask_value(panel, mask) == target
        )
        target_cols = {marked["ci"]}
        target_cols.update(
            panel["ci"]
            for panel in matches
            if panel["ri"] == marked["ri"] and _mask_value(panel, mask) == target
        )
        painted = [
            panel
            for panel in same_shape
            if panel["ri"] in target_rows
            and panel["ci"] in target_cols
            and all(panel["pat"][r][c] == target for r, c in mask)
        ]
        global_target_panels = [
            panel
            for panel in same_shape
            if all(panel["pat"][r][c] == target for r, c in mask)
        ]
        return {
            "branch": "primary",
            "marked": marked,
            "mask": mask,
            "matches": matches,
            "target": target,
            "target_rows": sorted(target_rows),
            "target_cols": sorted(target_cols),
            "painted": painted,
            "global_target_panels": global_target_panels,
        }

    full_cyan_rows = [
        r for r, row in enumerate(marked["pat"]) if row and all(value == 8 for value in row)
    ]
    if not full_cyan_rows:
        return {
            "branch": "inert",
            "marked": marked,
            "mask": mask,
            "matches": [],
            "painted": [],
        }

    col_mates = [
        panel
        for panel in panels
        if not panel["has8"]
        and panel["ci"] == marked["ci"]
        and panel["w"] == marked["w"]
    ]
    uniform_values: list[int] = []
    row_hits: dict[tuple[int, int], list[int]] = {}
    for panel in col_mates:
        for row_index, row in enumerate(panel["pat"]):
            if len(set(row)) == 1:
                uniform_values.append(row[0])
    base = _mode_first(uniform_values)
    painted: list[Panel] = []
    if base is not None:
        for panel in col_mates:
            hits = [
                row_index
                for row_index, row in enumerate(panel["pat"])
                if row and all(value == base for value in row)
            ]
            row_hits[(panel["ri"], panel["ci"])] = hits
            if len(hits) == 1:
                painted.append(panel)
    return {
        "branch": "secondary",
        "marked": marked,
        "mask": mask,
        "matches": [],
        "full_cyan_rows": full_cyan_rows,
        "col_mates": col_mates,
        "uniform_values": uniform_values,
        "base": base,
        "row_hits": row_hits,
        "painted": painted,
    }


def _apply_trace(output: Grid, trace: Trace) -> None:
    if trace["branch"] == "primary":
        mask = trace["mask"]
        for panel in trace["painted"]:
            for dr, dc in mask:
                output[panel["r1"] + dr][panel["c1"] + dc] = 8
    elif trace["branch"] == "secondary" and trace.get("base") is not None:
        for panel in trace["painted"]:
            hit = trace["row_hits"][(panel["ri"], panel["ci"])][0]
            for dc in range(panel["w"]):
                output[panel["r1"] + hit][panel["c1"] + dc] = 8


def _official_python_unchecked(grid: Grid) -> tuple[Grid, dict[str, Any], list[Trace]]:
    facts = _panelize(grid)
    traces = [
        _trace_marker(facts["panels"], panel)
        for panel in facts["panels"]
        if panel["has8"]
    ]
    output = copy.deepcopy(grid)
    for trace in traces:
        _apply_trace(output, trace)
    return output, facts, traces


def rule_mirror(grid: Grid) -> Grid:
    """Test-only Python mirror; the pinned Racket rule is authoritative."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output, _, _ = _official_python_unchecked(grid)
    return output


def _layout_signature(facts: dict[str, Any]) -> tuple[tuple[int, ...], tuple[int, ...], bool, bool]:
    h = max((end for _, end in facts["row_ranges"]), default=-1) + 1
    w = max((end for _, end in facts["col_ranges"]), default=-1) + 1
    row_lengths = tuple(end - start + 1 for start, end in facts["row_ranges"])
    col_lengths = tuple(end - start + 1 for start, end in facts["col_ranges"])
    trailing_row_divider = bool(facts["uniform_rows"] and facts["uniform_rows"][-1] >= h)
    trailing_col_divider = bool(facts["uniform_cols"] and facts["uniform_cols"][-1] >= w)
    return row_lengths, col_lengths, trailing_row_divider, trailing_col_divider


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    assert isinstance(grid, list)
    h, w = len(grid), len(grid[0])
    palette = sorted({value for row in grid for value in row})
    if len(palette) != 4:
        return {"errors": [f"expected exactly four input colors, got {len(palette)}: {palette}"]}
    if h > 30 or w > 30:
        errors.append(f"grid shape {h}x{w} exceeds ARC's 30x30 bound")

    output, facts, traces = _official_python_unchecked(grid)
    if not facts["uniform_rows"] or not facts["uniform_cols"]:
        errors.append("expected at least one uniform divider row and column")

    divider_colors = {
        grid[r][0] for r in facts["uniform_rows"]
    } | {
        grid[0][c] for c in facts["uniform_cols"]
    }
    if len(divider_colors) != 1:
        errors.append(f"all uniform divider lines must share one color, got {sorted(divider_colors)}")
    divider_color = next(iter(divider_colors)) if len(divider_colors) == 1 else None
    if divider_color == 8:
        errors.append("cyan cannot be the divider color")

    if len(facts["row_ranges"]) < 4 or len(facts["col_ranges"]) < 4:
        errors.append("divider lattice must expose at least four panel rows and columns")
    if not facts["panels"]:
        errors.append("divider lattice produced no panels")

    if 8 not in palette:
        errors.append("input must contain at least one cyan mask")

    cyan_on_divider = any(grid[r][c] == 8 for r in facts["uniform_rows"] for c in range(w)) or any(
        grid[r][c] == 8 for c in facts["uniform_cols"] for r in range(h)
    )
    if cyan_on_divider:
        errors.append("cyan may not occur on divider rows or columns")

    if not traces:
        errors.append("expected at least one cyan-bearing marked panel")
    for index, trace in enumerate(traces):
        if trace["branch"] == "inert":
            errors.append(f"marked panel {index} activates neither primary nor secondary branch")
        if not trace["painted"]:
            errors.append(f"marked panel {index} activates {trace['branch']} but paints no target panel")
        if trace["branch"] == "secondary" and trace.get("base") is None:
            errors.append(f"marked panel {index} has no modal uniform-row color")

    changed = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if output[r][c] != grid[r][c]
    ]
    if not changed:
        errors.append("official rule must change at least one cell")
    bad_changes = [
        (r, c, grid[r][c], output[r][c])
        for r, c in changed
        if output[r][c] != 8 or grid[r][c] == 8
    ]
    if bad_changes:
        errors.append(f"official rule may only paint new cyan cells: {bad_changes[:4]}")

    branch_set = {trace["branch"] for trace in traces if trace["branch"] != "inert"}
    if branch_set == {"primary"}:
        scene_mode = "primary"
    elif branch_set == {"secondary"}:
        scene_mode = "secondary"
    elif branch_set == {"primary", "secondary"}:
        scene_mode = "mixed"
    else:
        scene_mode = None

    signal_values = [
        int(trace["target"])
        for trace in traces
        if trace["branch"] == "primary" and trace.get("target") is not None
    ] + [
        int(trace["base"])
        for trace in traces
        if trace["branch"] == "secondary" and trace.get("base") is not None
    ]
    signal_color = signal_values[0] if signal_values and len(set(signal_values)) == 1 else None
    layout = _SHAPE_TO_LAYOUT.get(h) if h == w else None

    primary_nonexact = any(
        any(
            panel not in trace["matches"]
            and panel["ri"] != trace["marked"]["ri"]
            and panel["ci"] != trace["marked"]["ci"]
            for panel in trace["painted"]
        )
        for trace in traces
        if trace["branch"] == "primary"
    )
    primary_global_decoy = any(
        any(panel not in trace["painted"] for panel in trace["global_target_panels"])
        for trace in traces
        if trace["branch"] == "primary"
    )

    secondary_unique_guard = any(
        any(len(hits) >= 2 for hits in trace.get("row_hits", {}).values())
        for trace in traces
        if trace["branch"] == "secondary"
    )
    secondary_column_scope = False
    for trace in traces:
        if trace["branch"] != "secondary" or trace.get("base") is None:
            continue
        marked = trace["marked"]
        base = trace["base"]
        for panel in facts["panels"]:
            if panel["has8"] or panel["ci"] == marked["ci"] or panel["w"] != marked["w"]:
                continue
            hits = [row for row in panel["pat"] if row and all(value == base for value in row)]
            if len(hits) == 1:
                secondary_column_scope = True
                break

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "palette": palette,
        "divider_color": divider_color,
        "layout": layout,
        "scene_mode": scene_mode,
        "signal_color": signal_color,
        "facts": facts,
        "traces": traces,
        "output": output,
        "changed_cells": changed,
        "primary_nonexact_intersection": primary_nonexact,
        "primary_global_decoy": primary_global_decoy,
        "secondary_unique_row_guard": secondary_unique_guard,
        "secondary_column_scope": secondary_column_scope,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad authority grammar, including every canonical input."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Require one exact canonical square profile in addition to rule validity."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    layout = analysis["layout"]
    if layout is None:
        errors.append(f"shape {analysis['grid_h']}x{analysis['grid_w']} is not a canonical profile")
        return errors
    expected_lengths, expected_trailing = _LAYOUT_SPECS[layout]
    row_lengths = tuple(end - start + 1 for start, end in analysis["facts"]["row_ranges"])
    col_lengths = tuple(end - start + 1 for start, end in analysis["facts"]["col_ranges"])
    if sorted(row_lengths) != sorted(expected_lengths):
        errors.append(f"row panel lengths {row_lengths} do not match {layout}")
    if sorted(col_lengths) != sorted(expected_lengths):
        errors.append(f"column panel lengths {col_lengths} do not match {layout}")
    last_row_is_divider = analysis["facts"]["uniform_rows"][-1] == analysis["grid_h"] - 1
    last_col_is_divider = analysis["facts"]["uniform_cols"][-1] == analysis["grid_w"] - 1
    if last_row_is_divider != expected_trailing or last_col_is_divider != expected_trailing:
        errors.append(f"trailing-divider profile does not match {layout}")
    return errors


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    primary_count = sum(trace["branch"] == "primary" for trace in analysis["traces"])
    secondary_count = sum(trace["branch"] == "secondary" for trace in analysis["traces"])
    return {
        "layout": analysis["layout"],
        "scene_mode": analysis["scene_mode"],
        "signal_color": analysis["signal_color"],
        "divider_color": analysis["divider_color"],
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "panel_rows": len(analysis["facts"]["row_ranges"]),
        "panel_cols": len(analysis["facts"]["col_ranges"]),
        "primary_marker_count": primary_count,
        "secondary_marker_count": secondary_count,
        "changed_cell_count": len(analysis["changed_cells"]),
        "primary_nonexact_intersection": analysis["primary_nonexact_intersection"],
        "primary_global_decoy": analysis["primary_global_decoy"],
        "secondary_unique_row_guard": analysis["secondary_unique_row_guard"],
        "secondary_column_scope": analysis["secondary_column_scope"],
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    observed = {axis: facts[axis] for axis in AXES}
    if observed["layout"] not in LAYOUTS or observed["scene_mode"] not in SCENE_MODES:
        raise ValueError("generated grid does not expose an exact declared layout/scene mode")
    if observed["signal_color"] not in SIGNAL_COLORS:
        raise ValueError("generated grid does not expose one exact signal color")
    if observed["divider_color"] not in DIVIDER_COLORS:
        raise ValueError("generated grid does not expose one exact divider color")
    return observed


def _line_plan(lengths: list[int], trailing: bool) -> tuple[list[tuple[int, int]], list[int], int]:
    ranges: list[tuple[int, int]] = []
    dividers: list[int] = []
    cursor = 0
    for index, length in enumerate(lengths):
        ranges.append((cursor, cursor + length - 1))
        cursor += length
        if index < len(lengths) - 1 or trailing:
            dividers.append(cursor)
            cursor += 1
    return ranges, dividers, cursor


def _set_panel(grid: Grid, panel: Panel, pattern: Grid) -> None:
    if len(pattern) != panel["h"] or any(len(row) != panel["w"] for row in pattern):
        raise ValueError("panel pattern has the wrong shape")
    for r in range(panel["h"]):
        for c in range(panel["w"]):
            grid[panel["r1"] + r][panel["c1"] + c] = pattern[r][c]


def _panel_map(facts: dict[str, Any]) -> dict[tuple[int, int], Panel]:
    return {(panel["ri"], panel["ci"]): panel for panel in facts["panels"]}


def _body_pattern(h: int, w: int, body0: int, body1: int, variant: int) -> Grid:
    if h == 1 and w == 1:
        return [[body0]]
    # Checker-like panels use both body colors and keep every row/column
    # non-uniform whenever its length permits.  This prevents accidental
    # primary selectors and avoids polluting the secondary uniform-row mode.
    return [
        [body0 if (r + c + variant) % 2 == 0 else body1 for c in range(w)]
        for r in range(h)
    ]


def _primary_mask(h: int, w: int, variant: int) -> list[tuple[int, int]]:
    if (h, w) == (2, 2):
        options = (
            ((0, 0), (0, 1), (1, 0)),
            ((0, 0), (1, 1)),
        )
        return list(options[variant % len(options)])
    if (h, w) == (3, 3):
        options = (
            ((0, 0), (1, 1), (2, 2)),
            ((0, 1), (1, 0), (1, 2), (2, 1)),
            ((0, 0), (0, 2), (2, 0), (2, 2)),
            ((0, 1), (1, 0), (1, 1), (1, 2)),
        )
        return list(options[variant % len(options)])
    raise ValueError(f"primary controls require 2x2 or 3x3 panels, got {h}x{w}")


def _replace_mask(pattern: Grid, mask: list[tuple[int, int]], value: int) -> Grid:
    result = copy.deepcopy(pattern)
    for r, c in mask:
        result[r][c] = value
    return result


def _mutate_outside(pattern: Grid, mask: list[tuple[int, int]], body0: int, body1: int) -> Grid:
    result = copy.deepcopy(pattern)
    mask_set = set(mask)
    outside = [
        (r, c)
        for r in range(len(pattern))
        for c in range(len(pattern[0]))
        if (r, c) not in mask_set
    ]
    if not outside:
        raise ValueError("primary mask must leave at least one outside cell")
    r, c = outside[0]
    result[r][c] = body1 if result[r][c] == body0 else body0
    return result


def _construct_primary(
    grid: Grid,
    panel_by_pos: dict[tuple[int, int], Panel],
    rows: list[int],
    cols: list[int],
    signal: int,
    body0: int,
    body1: int,
    variant: int,
    *,
    alternate: int,
    contrast: bool = False,
    minority: bool = False,
) -> dict[str, Any]:
    marked_pos = (rows[0], cols[0])
    row_match_pos = (rows[0], cols[1])
    col_match_pos = (rows[1], cols[0])
    intersection_pos = (rows[1], cols[1])
    row_only_decoy_pos = (rows[1] if contrast else rows[0], cols[2])
    global_decoy_pos = (rows[2], cols[1] if contrast else cols[2])
    marked = panel_by_pos[marked_pos]
    mask = _primary_mask(marked["h"], marked["w"], variant)
    template = _body_pattern(marked["h"], marked["w"], body0, body1, variant + 11)
    outside = [
        (r, c)
        for r in range(marked["h"])
        for c in range(marked["w"])
        if (r, c) not in set(mask)
    ]
    # In particular, a 2x2 diagonal mask leaves two off-diagonal cells.
    # Give those cells an asymmetric signature so checkerboard background
    # panels cannot become accidental primary selectors.
    if len(outside) >= 2:
        for index, (r, c) in enumerate(outside):
            template[r][c] = body0 if index % 2 == 0 else body1

    _set_panel(grid, marked, _replace_mask(template, mask, 8))
    exact_match = _replace_mask(template, mask, signal)
    _set_panel(grid, panel_by_pos[row_match_pos], exact_match)
    _set_panel(grid, panel_by_pos[col_match_pos], exact_match)

    nonexact = _mutate_outside(template, mask, body0, body1)
    _set_panel(grid, panel_by_pos[intersection_pos], _replace_mask(nonexact, mask, signal))
    _set_panel(grid, panel_by_pos[row_only_decoy_pos], _replace_mask(nonexact, mask, signal))
    decoy = _mutate_outside(nonexact, mask, body0, body1)
    # Ensure the second mutation cannot accidentally return to the template.
    if decoy == template:
        outside = [
            (r, c)
            for r in range(marked["h"])
            for c in range(marked["w"])
            if (r, c) not in set(mask)
        ]
        r, c = outside[-1]
        decoy[r][c] = body1 if decoy[r][c] == body0 else body0
    _set_panel(grid, panel_by_pos[global_decoy_pos], _replace_mask(decoy, mask, signal))
    exact_positions = {row_match_pos, col_match_pos}
    if contrast:
        # The off-axis first match chooses the signal before any axis match.
        # Later foreign-color matches must neither choose the target nor expand
        # its selected rows/columns. The last exact match has the foreign color.
        first_pos = (rows[3], cols[2])
        _set_panel(grid, panel_by_pos[first_pos], exact_match)
        exact_positions.add(first_pos)
        alternate_positions = [(rows[3], cols[0]), (rows[0], cols[2]), (rows[2], cols[0])]
        if minority:
            alternate_positions.append((rows[3], cols[1]))
        else:
            extra_signal = (rows[3], cols[1])
            _set_panel(grid, panel_by_pos[extra_signal], exact_match)
            exact_positions.add(extra_signal)
    else:
        # A random-placement majority control counters "choose the rare color".
        # The marked row precedes the selector row, so this cannot be first.
        alternate_positions = [(rows[1], cols[2])]
    for position in alternate_positions:
        _set_panel(grid, panel_by_pos[position], _replace_mask(template, mask, alternate))
        exact_positions.add(position)
    return {
        "marked": marked_pos,
        "row_match": row_match_pos,
        "col_match": col_match_pos,
        "intersection": intersection_pos,
        "row_only_decoy": row_only_decoy_pos,
        "global_decoy": global_decoy_pos,
        "mask": mask,
        "exact_positions": exact_positions,
    }


def _nonuniform_row(width: int, body0: int, body1: int, phase: int) -> list[int]:
    if width < 2:
        return [body0]
    row = [body0 if (index + phase) % 2 == 0 else body1 for index in range(width)]
    if len(set(row)) == 1:
        row[-1] = body1 if row[-1] == body0 else body0
    return row


def _secondary_pattern(
    h: int,
    w: int,
    body0: int,
    body1: int,
    variant: int,
    *,
    signal: int | None = None,
    signal_rows: tuple[int, ...] = (),
    cyan_row: int | None = None,
) -> Grid:
    pattern = [
        _nonuniform_row(w, body0, body1, phase=variant + r)
        for r in range(h)
    ]
    if signal is not None:
        for r in signal_rows:
            pattern[r] = [signal] * w
    if cyan_row is not None:
        pattern[cyan_row] = [8] * w
    return pattern


def _read_panel(grid: Grid, panel: Panel) -> Grid:
    return [
        list(grid[panel["r1"] + r][panel["c1"] : panel["c1"] + panel["w"]])
        for r in range(panel["h"])
    ]


def _toggle_body(value: int, body0: int, body1: int) -> int:
    return body1 if value == body0 else body0


def _uniform_row_signature(pattern: Grid) -> tuple[int | None, ...]:
    return tuple(row[0] if row and len(set(row)) == 1 else None for row in pattern)


def _break_outside_agreement(
    pattern: Grid,
    outside: list[tuple[int, int]],
    marked_pat: Grid,
    body0: int,
    body1: int,
) -> Grid:
    """Change an outside-mask value without changing uniform-row semantics."""
    before_signature = _uniform_row_signature(pattern)

    def acceptable(candidate: Grid) -> bool:
        return (
            _uniform_row_signature(candidate) == before_signature
            and any(candidate[r][c] != marked_pat[r][c] for r, c in outside)
        )

    for r, c in outside:
        candidate = copy.deepcopy(pattern)
        candidate[r][c] = _toggle_body(candidate[r][c], body0, body1)
        if acceptable(candidate):
            return candidate
    for index, (r1, c1) in enumerate(outside):
        for r2, c2 in outside[index + 1 :]:
            if pattern[r1][c1] == pattern[r2][c2]:
                continue
            candidate = copy.deepcopy(pattern)
            candidate[r1][c1], candidate[r2][c2] = candidate[r2][c2], candidate[r1][c1]
            if acceptable(candidate):
                return candidate
    candidate = copy.deepcopy(pattern)
    for r, c in outside:
        candidate[r][c] = _toggle_body(candidate[r][c], body0, body1)
    if acceptable(candidate):
        return candidate
    raise AssertionError("could not break accidental match without changing uniform-row semantics")


def _sanitize_primary_matches(
    grid: Grid,
    panel_by_pos: dict[tuple[int, int], Panel],
    control: dict[str, Any],
    body0: int,
    body1: int,
    preserve_uniform_positions: set[tuple[int, int]] | None = None,
) -> None:
    """Remove incidental selector matches while preserving teaching controls."""
    preserve_uniform_positions = preserve_uniform_positions or set()
    marked = panel_by_pos[control["marked"]]
    marked_pat = _read_panel(grid, marked)
    mask = list(control["mask"])
    mask_set = set(mask)
    exact_positions = control["exact_positions"]
    outside = [
        (r, c)
        for r in range(marked["h"])
        for c in range(marked["w"])
        if (r, c) not in mask_set
    ]
    for position, panel in panel_by_pos.items():
        pattern = _read_panel(grid, panel)
        if position == control["marked"] or position in exact_positions:
            continue
        if any(value == 8 for row in pattern for value in row):
            continue
        if (panel["h"], panel["w"]) != (marked["h"], marked["w"]):
            continue
        values = {pattern[r][c] for r, c in mask}
        agrees = all(pattern[r][c] == marked_pat[r][c] for r, c in outside)
        if len(values) != 1 or next(iter(values)) == 0 or not agrees:
            continue
        if position in preserve_uniform_positions:
            pattern = _break_outside_agreement(
                pattern, outside, marked_pat, body0, body1
            )
        else:
            r, c = outside[0]
            pattern[r][c] = _toggle_body(pattern[r][c], body0, body1)
        _set_panel(grid, panel, pattern)


def _sanitize_secondary_matches(
    grid: Grid,
    panel_by_pos: dict[tuple[int, int], Panel],
    control: dict[str, Any],
    body0: int,
    body1: int,
    primary_control: dict[str, Any] | None = None,
) -> None:
    """Guarantee the full-cyan-row marker reaches the fallback branch."""
    marked = panel_by_pos[control["marked"]]
    marked_pat = _read_panel(grid, marked)
    mask = [
        (r, c)
        for r in range(marked["h"])
        for c in range(marked["w"])
        if marked_pat[r][c] == 8
    ]
    mask_set = set(mask)
    outside = [
        (r, c)
        for r in range(marked["h"])
        for c in range(marked["w"])
        if (r, c) not in mask_set
    ]
    protected = primary_control["exact_positions"] if primary_control else set()

    def matches_marker(pattern: Grid) -> bool:
        values = {pattern[r][c] for r, c in mask}
        return (len(values) == 1 and next(iter(values)) != 0
                and all(pattern[r][c] == marked_pat[r][c] for r, c in outside))

    # Foreign primary colors can equal a body color and create a uniform row.
    # Change the secondary marker's noncyan signature instead of corrupting
    # an intentional primary match while forcing the fallback branch.
    if any(matches_marker(_read_panel(grid, panel_by_pos[pos])) for pos in protected):
        for r, c in outside:
            marked_pat[r][c] = _toggle_body(marked_pat[r][c], body0, body1)
        if any(matches_marker(_read_panel(grid, panel_by_pos[pos])) for pos in protected):
            raise AssertionError("secondary signature conflicts with intentional primary matches")
        _set_panel(grid, marked, marked_pat)
    for position, panel in panel_by_pos.items():
        if position == control["marked"] or position in protected:
            continue
        pattern = _read_panel(grid, panel)
        if any(value == 8 for row in pattern for value in row):
            continue
        if (panel["h"], panel["w"]) != (marked["h"], marked["w"]):
            continue
        values = {pattern[r][c] for r, c in mask}
        agrees = all(pattern[r][c] == marked_pat[r][c] for r, c in outside)
        if len(values) != 1 or next(iter(values)) == 0 or not agrees:
            continue
        if panel["ci"] == marked["ci"]:
            pattern = _break_outside_agreement(
                pattern, outside, marked_pat, body0, body1
            )
        else:
            r, c = outside[0]
            pattern[r][c] = _toggle_body(pattern[r][c], body0, body1)
        _set_panel(grid, panel, pattern)


def _construct_secondary(
    grid: Grid,
    panel_by_pos: dict[tuple[int, int], Panel],
    rows: list[int],
    cols: list[int],
    signal: int,
    body0: int,
    body1: int,
    variant: int,
) -> dict[str, Any]:
    column = cols[3]
    marker_pos = (rows[0], column)
    unique_a_pos = (rows[1], column)
    duplicate_pos = (rows[2], column)
    unique_b_pos = (rows[3], column)
    off_column_pos = (rows[3], cols[2])

    marker = panel_by_pos[marker_pos]
    cyan_row = variant % marker["h"]
    _set_panel(
        grid,
        marker,
        _secondary_pattern(
            marker["h"], marker["w"], body0, body1, variant + 3, cyan_row=cyan_row
        ),
    )

    unique_a = panel_by_pos[unique_a_pos]
    unique_a_row = (variant + 1) % unique_a["h"]
    _set_panel(
        grid,
        unique_a,
        _secondary_pattern(
            unique_a["h"], unique_a["w"], body0, body1, variant + 7,
            signal=signal, signal_rows=(unique_a_row,),
        ),
    )

    duplicate = panel_by_pos[duplicate_pos]
    duplicate_rows = (0, 1)
    _set_panel(
        grid,
        duplicate,
        _secondary_pattern(
            duplicate["h"], duplicate["w"], body0, body1, variant + 13,
            signal=signal, signal_rows=duplicate_rows,
        ),
    )

    unique_b = panel_by_pos[unique_b_pos]
    unique_b_row = (variant + 2) % unique_b["h"]
    _set_panel(
        grid,
        unique_b,
        _secondary_pattern(
            unique_b["h"], unique_b["w"], body0, body1, variant + 17,
            signal=signal, signal_rows=(unique_b_row,),
        ),
    )

    off_column = panel_by_pos[off_column_pos]
    off_row = (variant + 1) % off_column["h"]
    _set_panel(
        grid,
        off_column,
        _secondary_pattern(
            off_column["h"], off_column["w"], body0, body1, variant + 23,
            signal=signal, signal_rows=(off_row,),
        ),
    )
    return {
        "marked": marker_pos,
        "unique_a": unique_a_pos,
        "duplicate": duplicate_pos,
        "unique_b": unique_b_pos,
        "off_column": off_column_pos,
        "cyan_row": cyan_row,
    }


def _palette_plan(signal: int, divider: int, rng, *, prefer_larger: bool = False) -> tuple[int, int]:
    candidates = [color for color in range(10) if color != 8 and color not in {signal, divider}]
    rng.shuffle(candidates)
    if prefer_larger and signal < 9 and divider <= signal:
        # Keep four colors while ensuring a numerical-maximum rival is false.
        higher = next(color for color in candidates if color > signal)
        candidates.remove(higher)
        candidates.insert(0, higher)
    elif not prefer_larger and signal > 1 and not 0 < divider < signal:
        lower = next(color for color in candidates if 0 < color < signal)
        candidates.remove(lower)
        candidates.insert(0, lower)
    if signal != divider:
        # The divider may also occur inside panels; body0 guarantees every
        # non-divider line still contains a color different from the divider.
        return candidates[0], divider
    return candidates[0], candidates[1]


def _build_scene(
    layout: str,
    scene_mode: str,
    signal: int,
    divider: int,
    rng,
    *,
    schedule_index: int = 0,
) -> Grid:
    base_lengths, trailing = _LAYOUT_SPECS[layout]
    row_lengths = list(base_lengths)
    col_lengths = list(base_lengths)
    # The exact multiset is canonical.  Moving short panels broadens placement
    # support while retaining the same strict morphology profile.
    rng.shuffle(row_lengths)
    rng.shuffle(col_lengths)
    row_ranges, _, height = _line_plan(row_lengths, trailing)
    col_ranges, _, width = _line_plan(col_lengths, trailing)
    grid = full_grid(height, width, divider)

    facts = _panelize(grid)
    # A divider-only grid has no panel ranges under the authority parser, so use
    # the construction ranges directly for the initial overwrite.
    panels: list[Panel] = []
    for ri, (r1, r2) in enumerate(row_ranges):
        for ci, (c1, c2) in enumerate(col_ranges):
            panels.append({
                "ri": ri,
                "ci": ci,
                "r1": r1,
                "c1": c1,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            })
    panel_by_pos = {(panel["ri"], panel["ci"]): panel for panel in panels}

    contrast = schedule_index != 3
    minority = schedule_index in (0, 2)
    target_low = schedule_index in (0, 3)
    body0, body1 = _palette_plan(signal, divider, rng, prefer_larger=target_low)
    alternate = (max if target_low else min)(color for color in (body0, body1) if color > 0)
    for panel in panels:
        _set_panel(
            grid,
            panel,
            _body_pattern(
                panel["h"], panel["w"], body0, body1,
                variant=panel["ri"] * 11 + panel["ci"] * 7,
            ),
        )

    major = max(base_lengths)
    major_rows = [index for index, length in enumerate(row_lengths) if length == major]
    major_cols = [index for index, length in enumerate(col_lengths) if length == major]
    rng.shuffle(major_rows)
    rng.shuffle(major_cols)
    if len(major_rows) < 4 or len(major_cols) < 4:
        raise AssertionError(f"layout {layout} lacks four major panel rows/columns")
    secondary_rows = major_rows
    if scene_mode in ("primary", "mixed"):
        if contrast:
            r0, r1, r2, r3 = sorted(major_rows[:4])
            c0, c1, c2 = sorted(major_cols[:3])
            major_rows = [r2, r1, r3, r0]
            secondary_rows = [r2, r1, r0, r3]
            major_cols = [c1, c2, c0, major_cols[3]]
        elif major_rows[0] > major_rows[1]:
            major_rows[0], major_rows[1] = major_rows[1], major_rows[0]
    variant = rng.randrange(10_000)

    primary_control = None
    secondary_control = None
    if scene_mode in ("primary", "mixed"):
        primary_control = _construct_primary(
            grid, panel_by_pos, major_rows, major_cols,
            signal, body0, body1, variant,
            alternate=alternate, contrast=contrast, minority=minority,
        )
    if scene_mode in ("secondary", "mixed"):
        # Normalize every unmarked panel in the selected secondary column to
        # non-uniform rows first, preventing incidental body-color modes.
        secondary_col = major_cols[3]
        for ri in range(len(row_ranges)):
            panel = panel_by_pos[(ri, secondary_col)]
            _set_panel(
                grid,
                panel,
                _secondary_pattern(
                    panel["h"], panel["w"], body0, body1,
                    variant=variant + 31 + ri,
                ),
            )
        secondary_control = _construct_secondary(
            grid, panel_by_pos, secondary_rows, major_cols,
            signal, body0, body1, variant,
        )

    if primary_control is not None:
        protected: set[tuple[int, int]] = set()
        if secondary_control is not None:
            secondary_column = secondary_control["marked"][1]
            protected.update(
                position for position in panel_by_pos if position[1] == secondary_column
            )
            protected.add(secondary_control["off_column"])
        _sanitize_primary_matches(
            grid, panel_by_pos, primary_control, body0, body1, protected
        )
    if secondary_control is not None:
        _sanitize_secondary_matches(
            grid, panel_by_pos, secondary_control, body0, body1, primary_control
        )

    analysis = _analysis(grid)
    expected = {
        "primary": (True, True, False, False),
        "secondary": (False, False, True, True),
        "mixed": (True, True, True, True),
    }[scene_mode]
    actual = (
        analysis["primary_nonexact_intersection"],
        analysis["primary_global_decoy"],
        analysis["secondary_unique_row_guard"],
        analysis["secondary_column_scope"],
    )
    if analysis["errors"] or analysis["scene_mode"] != scene_mode or actual != expected:
        raise AssertionError(
            "constructed scene violates its semantic contract: "
            f"mode={scene_mode!r} observed={analysis.get('scene_mode')!r} "
            f"witnesses={actual!r} expected={expected!r} errors={analysis['errors']!r}"
        )
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    index = int(sample_index) % len(_SCENE_SCHEDULE)
    effective = {key: value for key, value in overrides.items() if value is not None}
    effective.setdefault("layout", _LAYOUT_SCHEDULE[difficulty][index])
    effective.setdefault("scene_mode", _SCENE_SCHEDULE[index])

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    layout = str(ctx.draw_choice("layout", LAYOUTS))
    scene_mode = str(ctx.draw_choice("scene_mode", SCENE_MODES))
    signal_choices = SIGNAL_COLORS
    if "signal_color" not in effective:
        signal_choices = tuple(color for color in SIGNAL_COLORS
                               if (color < 9 if index in (0, 3) else color > 1))
    signal = int(ctx.draw_choice("signal_color", signal_choices))
    divider = int(ctx.draw_choice("divider_color", DIVIDER_COLORS))
    grid = _build_scene(
        layout, scene_mode, signal, divider, ctx.draw_rng("construction"), schedule_index=index
    )

    observed = observe_overrides(grid)
    requested = {
        "layout": layout,
        "scene_mode": scene_mode,
        "signal_color": signal,
        "divider_color": divider,
    }
    if observed != requested:
        raise AssertionError(f"override observability mismatch: requested={requested}, observed={observed}")
    return grid


# ---------------------------------------------------------------------------
# Semantic rivals, witnesses, and lesson identifiability
# ---------------------------------------------------------------------------

def _solve_with_policy(
    grid: Grid,
    *,
    primary_exact_only: bool = False,
    primary_all_global: bool = False,
    primary_union: bool = False,
    secondary_all_columns: bool = False,
    secondary_all_hits: bool = False,
    primary_target_policy: str | None = None,
    primary_ignore_selector_color: bool = False,
) -> Grid:
    output, facts, traces = _official_python_unchecked(grid)
    del output
    result = copy.deepcopy(grid)
    panels = facts["panels"]
    for trace in traces:
        if trace["branch"] == "primary":
            if primary_target_policy is not None or primary_ignore_selector_color:
                marked = trace["marked"]
                mask = trace["mask"]
                colors = [_mask_value(panel, mask) for panel in trace["matches"]]
                target = trace["target"]
                if primary_target_policy in ("modal", "least_frequent"):
                    counts = Counter(colors)
                    count = (max if primary_target_policy == "modal" else min)(counts.values())
                    target = next(color for color in colors if counts[color] == count)
                elif primary_target_policy == "last":
                    target = colors[-1]
                elif primary_target_policy == "maximum":
                    target = max(colors)
                elif primary_target_policy == "minimum":
                    target = min(colors)
                elif primary_target_policy == "first_axis":
                    aligned = [panel for panel in trace["matches"]
                               if panel["ri"] == marked["ri"] or panel["ci"] == marked["ci"]]
                    if aligned:
                        target = _mask_value(aligned[0], mask)
                elif primary_target_policy == "first_row":
                    aligned = [panel for panel in trace["matches"] if panel["ri"] == marked["ri"]]
                    if aligned:
                        target = _mask_value(aligned[0], mask)
                elif primary_target_policy is not None:
                    raise ValueError(f"unknown primary target policy: {primary_target_policy}")
                selectors = [panel for panel in trace["matches"]
                             if primary_ignore_selector_color or _mask_value(panel, mask) == target]
                rows = {marked["ri"]} | {panel["ri"] for panel in selectors if panel["ci"] == marked["ci"]}
                cols = {marked["ci"]} | {panel["ci"] for panel in selectors if panel["ri"] == marked["ri"]}
                candidates = [panel for panel in panels
                              if not panel["has8"]
                              and (panel["h"], panel["w"]) == (marked["h"], marked["w"])
                              and _mask_value(panel, mask) == target]
                trace = {**trace, "target": target, "target_rows": rows, "target_cols": cols,
                         "global_target_panels": candidates,
                         "painted": [panel for panel in candidates if panel["ri"] in rows and panel["ci"] in cols]}
            if primary_exact_only:
                targets = trace["matches"]
            elif primary_all_global:
                targets = trace["global_target_panels"]
            elif primary_union:
                targets = [
                    panel
                    for panel in trace["global_target_panels"]
                    if panel["ri"] in trace["target_rows"] or panel["ci"] in trace["target_cols"]
                ]
            else:
                targets = trace["painted"]
            for panel in targets:
                for dr, dc in trace["mask"]:
                    result[panel["r1"] + dr][panel["c1"] + dc] = 8
        elif trace["branch"] == "secondary" and trace.get("base") is not None:
            marked = trace["marked"]
            if secondary_all_columns:
                candidates = [
                    panel for panel in panels
                    if not panel["has8"] and panel["w"] == marked["w"]
                ]
            else:
                candidates = trace["col_mates"]
            for panel in candidates:
                hits = [
                    row_index
                    for row_index, row in enumerate(panel["pat"])
                    if row and all(value == trace["base"] for value in row)
                ]
                selected = hits if secondary_all_hits else (hits if len(hits) == 1 else [])
                for row_index in selected:
                    for dc in range(panel["w"]):
                        result[panel["r1"] + row_index][panel["c1"] + dc] = 8
    return result


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "primary_exact_pattern_only": lambda grid: _solve_with_policy(grid, primary_exact_only=True),
    "primary_paint_all_signal_panels": lambda grid: _solve_with_policy(grid, primary_all_global=True),
    "primary_row_or_column_union": lambda grid: _solve_with_policy(grid, primary_union=True),
    "secondary_ignore_column_scope": lambda grid: _solve_with_policy(grid, secondary_all_columns=True),
    "secondary_paint_every_matching_row": lambda grid: _solve_with_policy(grid, secondary_all_hits=True),
    "primary_modal_match_color": lambda grid: _solve_with_policy(grid, primary_target_policy="modal"),
    "primary_last_match_color": lambda grid: _solve_with_policy(grid, primary_target_policy="last"),
    "primary_maximum_match_color": lambda grid: _solve_with_policy(grid, primary_target_policy="maximum"),
    "primary_first_axis_match": lambda grid: _solve_with_policy(grid, primary_target_policy="first_axis"),
    "primary_first_row_match": lambda grid: _solve_with_policy(grid, primary_target_policy="first_row"),
    "primary_ignore_selector_color": lambda grid: _solve_with_policy(grid, primary_ignore_selector_color=True),
    "primary_least_frequent_match_color": lambda grid: _solve_with_policy(grid, primary_target_policy="least_frequent"),
    "primary_minimum_match_color": lambda grid: _solve_with_policy(grid, primary_target_policy="minimum"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
_FIRST_MATCH_SHORTCUTS = (
    "primary_modal_match_color", "primary_last_match_color",
    "primary_first_axis_match", "primary_first_row_match", "primary_ignore_selector_color",
)
# The older geometry/fallback rivals, and least-frequency selection, are useful
# lesson competitors but are already refuted by the canonical demonstrations.
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                       for name in (*_FIRST_MATCH_SHORTCUTS, "primary_maximum_match_color")}


def _witness(name: str) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])
    return predicate


def _rival_witness(names: tuple[str, ...]) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        if self_check(grid):
            return False
        expected = rule_mirror(grid)
        return all(SEMANTIC_RIVALS[name](grid) != expected for name in names)
    return predicate


SEMANTIC_WITNESSES = {
    "primary_nonexact_intersection": _witness("primary_nonexact_intersection"),
    "primary_global_decoy": _witness("primary_global_decoy"),
    "secondary_unique_row_guard": _witness("secondary_unique_row_guard"),
    "secondary_column_scope": _witness("secondary_column_scope"),
    "primary_first_match_color": _rival_witness(_FIRST_MATCH_SHORTCUTS),
    "primary_first_majority_color": _rival_witness(("primary_least_frequent_match_color",)),
    "primary_nonmaximum_color": _rival_witness(("primary_maximum_match_color",)),
    "primary_nonminimum_color": _rival_witness(("primary_minimum_match_color",)),
}
WITNESS_RIVALS = {
    "primary_nonexact_intersection": ["primary_exact_pattern_only"],
    "primary_global_decoy": ["primary_paint_all_signal_panels", "primary_row_or_column_union"],
    "secondary_unique_row_guard": ["secondary_paint_every_matching_row"],
    "secondary_column_scope": ["secondary_ignore_column_scope"],
    "primary_first_match_color": list(_FIRST_MATCH_SHORTCUTS),
    "primary_first_majority_color": ["primary_least_frequent_match_color"],
    "primary_nonmaximum_color": ["primary_maximum_match_color"],
    "primary_nonminimum_color": ["primary_minimum_match_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a short lesson to expose both branches and all shortcut guards."""
    reasons: list[str] = []
    witness_hits = {name: False for name in SEMANTIC_WITNESSES}
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output does not match the panel-mask rule")
        valid_demos.append(demo)
        for name, witness in SEMANTIC_WITNESSES.items():
            witness_hits[name] = witness_hits[name] or witness(demo["input"])
    missing = [name for name, hit in witness_hits.items() if not hit]
    if missing:
        reasons.append(f"demos miss required semantic controls: {', '.join(missing)}")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {'; '.join(query_errors)}")
        return reasons
    official_query = rule_mirror(query["input"])
    if query["output"] != official_query:
        reasons.append("query output does not match the panel-mask rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = bool(valid_demos) and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if survives and competitor(query["input"]) != official_query:
            reasons.append(f"competing rule '{name}' fits every demo but changes the query")
    return reasons


# ---------------------------------------------------------------------------
# Negative fixtures
# ---------------------------------------------------------------------------

def mutation_fixtures() -> list[tuple[str, Grid]]:
    valid_primary = generate(91_337, 0, difficulty="medium", scene_mode="primary")
    valid_secondary = generate(91_337, 2, difficulty="medium", scene_mode="secondary")
    fixtures: list[tuple[str, Grid]] = []

    no_cyan = copy.deepcopy(valid_primary)
    for r, row in enumerate(no_cyan):
        for c, value in enumerate(row):
            if value == 8:
                no_cyan[r][c] = 0
    fixtures.append(("no_cyan_mask", no_cyan))

    cyan_divider = copy.deepcopy(valid_primary)
    facts = _panelize(cyan_divider)
    divider_row = facts["uniform_rows"][0]
    cyan_divider[divider_row] = [8] * len(cyan_divider[0])
    fixtures.append(("cyan_divider_line", cyan_divider))

    fifth_color = copy.deepcopy(valid_primary)
    palette = {value for row in fifth_color for value in row}
    absent = next(color for color in range(10) if color not in palette)
    panel = next(panel for panel in _panelize(fifth_color)["panels"] if not panel["has8"])
    fifth_color[panel["r1"]][panel["c1"]] = absent
    fixtures.append(("fifth_palette_color", fifth_color))

    inert_primary = copy.deepcopy(valid_primary)
    analysis = _analysis(inert_primary)
    primary = next(trace for trace in analysis["traces"] if trace["branch"] == "primary")
    for panel in primary["matches"]:
        for dr, dc in primary["mask"]:
            inert_primary[panel["r1"] + dr][panel["c1"] + dc] = 0
    fixtures.append(("primary_marker_without_nonzero_match", inert_primary))

    inert_secondary = copy.deepcopy(valid_secondary)
    analysis = _analysis(inert_secondary)
    secondary = next(trace for trace in analysis["traces"] if trace["branch"] == "secondary")
    base = secondary["base"]
    replacement = next(
        value for value in analysis["palette"] if value not in {8, base}
    )
    for panel in secondary["col_mates"]:
        hits = secondary["row_hits"].get((panel["ri"], panel["ci"]), [])
        for hit in hits:
            inert_secondary[panel["r1"] + hit][panel["c1"]] = replacement
    fixtures.append(("secondary_marker_without_unique_modal_row", inert_secondary))

    base_analysis = _analysis(valid_primary)
    painted_ids = {
        (panel["ri"], panel["ci"])
        for trace in base_analysis["traces"]
        for panel in trace["painted"]
    }
    stray_fixture = None
    for panel in base_analysis["facts"]["panels"]:
        if panel["has8"] or (panel["ri"], panel["ci"]) in painted_ids:
            continue
        for dr in range(panel["h"]):
            for dc in range(panel["w"]):
                candidate = copy.deepcopy(valid_primary)
                candidate[panel["r1"] + dr][panel["c1"] + dc] = 8
                if self_check(candidate):
                    stray_fixture = candidate
                    break
            if stray_fixture is not None:
                break
        if stray_fixture is not None:
            break
    if stray_fixture is None:
        raise AssertionError("could not construct an invalid stray-cyan mutation")
    fixtures.append(("inert_stray_cyan_panel", stray_fixture))
    return fixtures


def negative_recombination_fixture() -> tuple[Grid, Grid]:
    """Return (source, recombined) for distribution-vs-oracle calibration.

    A cyan-bearing panel from one valid scene is transplanted into a different
    palette/layout scene.  The structural distribution checker must reject the
    recombination, while the total Racket/Python oracle remains executable.
    """
    source = generate(
        707_001, 0, difficulty="medium",
        layout="canonical_21", scene_mode="primary", signal_color=2, divider_color=4,
    )
    destination = generate(
        707_002, 2, difficulty="medium",
        layout="canonical_23", scene_mode="secondary", signal_color=6, divider_color=1,
    )
    source_marked = next(panel for panel in _panelize(source)["panels"] if panel["has8"])
    dest_facts = _panelize(destination)
    destination_panel = next(
        panel for panel in dest_facts["panels"]
        if not panel["has8"]
        and panel["h"] == source_marked["h"]
        and panel["w"] == source_marked["w"]
    )
    recombined = copy.deepcopy(destination)
    _set_panel(recombined, destination_panel, source_marked["pat"])
    return source, recombined
