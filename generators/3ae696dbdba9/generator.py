"""Generator for ``3ae696dbdba9`` — component-wise vertical span closure.

For every 4-connected non-zero component, inspect each column occupied by that
component.  The output fills every zero between the topmost and bottommost
component cell in that column with the component color.  Components whose
columns are already contiguous are unchanged.

The ordinary five-profile schedule deliberately contains:

* two canonical-scale anchors (two fillable 8-cell components plus one
  unchanged column-convex control),
* a same-color recombination trap that separates component-wise closure from
  whole-color/global column closure,
* irregular short/mixed/long gaps and one-/multi-column closures,
* scenes with two through five components, with and without a control, and
  interior as well as boundary-touching layouts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ae696dbdba9"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "116e45f72631"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "Close vertical holes independently inside every 4-connected non-zero "
    "component: in each occupied component column, paint the inclusive span "
    "from its topmost to bottommost cell in that component color. Already "
    "column-convex controls remain unchanged."
)

INVARIANTS = [
    "background is color 0",
    "there are two to five cardinally separated non-zero components",
    "at least one component has a zero inside a per-column vertical span",
    "zero or one column-convex control remains unchanged",
    "same-colored components are still processed independently",
    "the canonical Racket rule, not the Python mirror, is output authority",
]

_GAP_PROFILES = ("short", "mixed", "long")
_CONTROL_MODES = ("none", "one")
_COLOR_MODES = ("distinct", "reused")
_EDGE_PROFILES = ("interior", "touching")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile canonical/generalization schedule",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile canonical/generalization schedule",
        "valid": "12..20",
    },
    "component_count": {
        "type": "int",
        "default": "scheduled 2|3|4|5",
        "valid": "2..5",
    },
    "max_gap_columns": {
        "type": "int",
        "default": "scheduled 1|2|3",
        "valid": "1..3",
    },
    "gap_profile": {
        "type": "str",
        "default": "scheduled short|mixed|long",
        "valid": "|".join(_GAP_PROFILES),
    },
    "control_mode": {
        "type": "str",
        "default": "scheduled none|one",
        "valid": "|".join(_CONTROL_MODES),
    },
    "color_mode": {
        "type": "str",
        "default": "scheduled distinct|reused",
        "valid": "|".join(_COLOR_MODES),
    },
    "edge_profile": {
        "type": "str",
        "default": "scheduled interior|touching",
        "valid": "|".join(_EDGE_PROFILES),
    },
}

# Every boundary tuple produced by override-contract v7 is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor_15",
    "same_color_short_recombination",
    "canonical_anchor_16",
    "irregular_mixed_controls",
    "long_boundary_generalization",
)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

Shape = tuple[tuple[int, int], ...]


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return a stable cyclic profile, phase-shifted by difficulty band."""
    del seed
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(int(sample_index) + band_offset) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


# Exact canonical-role motifs.  The first two each contain eight cells: a
# 3x3 ring has one fillable column, and a 4x3 C has two.  The controls are
# connected and column-convex, so the true rule leaves them unchanged.
_RING3 = _normalize(
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))
)
_C4_LEFT = _normalize(
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2))
)
_C4_RIGHT = _normalize((r, 2 - c) for r, c in _C4_LEFT)
_T5 = _normalize(((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)))
_STAIR6 = _normalize(((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)))
_LARGE_CONTROL = _normalize(
    (
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2),
        (2, 0), (2, 1), (2, 2), (2, 3),
        (3, 0), (3, 1), (3, 2), (3, 3),
    )
)


def _shape_size(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _mirror(shape: Shape) -> Shape:
    _, width = _shape_size(shape)
    return _normalize((r, width - 1 - c) for r, c in shape)


def _fillable_shape(profile: str, gap_columns: int, *, staggered: bool) -> Shape:
    """Connected component with an exact vertical-gap profile.

    A solid spine connects every endpoint.  Target columns then carry:
    short  -> one missing row,
    long   -> one missing run of three rows,
    mixed  -> one missing row and one missing run of two rows.

    Staggering offsets alternating target columns, refuting the canonical-only
    shortcut "fill only full top/bottom frame shapes" while preserving the
    same per-column rule.
    """
    if not 1 <= gap_columns <= 3:
        raise ValueError("gap_columns must be in 1..3")
    if profile == "short":
        height = 4 if staggered else 3
        # Every target column shares one horizontal attachment row.  This is
        # important: alternating endpoint rows would create disconnected
        # same-colored fragments rather than one Racket object.
        patterns = ((1, 3),) if staggered else ((0, 2),)
    elif profile == "long":
        height = 6 if staggered else 5
        patterns = ((1, 5),) if staggered else ((0, 4),)
    elif profile == "mixed":
        height = 7 if staggered else 6
        patterns = ((1, 3, 6),) if staggered else ((0, 2, 5),)
    else:
        raise ValueError(f"unsupported gap profile {profile!r}")

    cells = {(r, 0) for r in range(height)}
    for col in range(1, gap_columns + 1):
        cells.update((row, col) for row in patterns[(col - 1) % len(patterns)])
    return _normalize(cells)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "component_count", "max_gap_columns"):
        value = overrides.get(name)
        if value is not None and (isinstance(value, bool) or type(value) is not int):
            raise ValueError(f"{name} must be an integer")
    for name in ("gap_profile", "control_mode", "color_mode", "edge_profile"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _draw_int(ctx, overrides: dict[str, Any], name: str, default: int,
              lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_choice(ctx, overrides: dict[str, Any], name: str, default: str,
                 options: tuple[str, ...]) -> str:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells = {(sr, sc)}
            seen.add((sr, sc))
            stack = [(sr, sc)]
            while stack:
                r, c = stack.pop()
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            out.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return out


def _missing_runs(rows: list[int]) -> list[int]:
    occupied = set(rows)
    runs: list[int] = []
    current = 0
    for row in range(min(rows), max(rows) + 1):
        if row in occupied:
            if current:
                runs.append(current)
                current = 0
        else:
            current += 1
    if current:
        runs.append(current)
    return runs


def _component_facts(component: dict[str, Any], h: int, w: int) -> dict[str, Any]:
    by_col: dict[int, list[int]] = {}
    for r, c in component["cells"]:
        by_col.setdefault(c, []).append(r)
    gap_columns: dict[int, list[int]] = {}
    for col, rows in by_col.items():
        runs = _missing_runs(rows)
        if runs:
            gap_columns[col] = runs
    r1, c1, r2, c2 = component["bbox"]
    top_full = all((r1, c) in component["cells"] for c in range(c1, c2 + 1))
    bottom_full = all((r2, c) in component["cells"] for c in range(c1, c2 + 1))
    return {
        **component,
        "size": len(component["cells"]),
        "gap_columns": gap_columns,
        "gap_column_count": len(gap_columns),
        "gap_runs": [run for runs in gap_columns.values() for run in runs],
        "fillable": bool(gap_columns),
        "touches_edge": r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1,
        "frame_like": top_full and bottom_full,
        "bbox_full": len(component["cells"]) == (r2 - r1 + 1) * (c2 - c1 + 1),
    }


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        info["errors"].append("grid must be a non-empty list of rows")
        return info
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        info["errors"].append("grid must be rectangular and non-empty")
        return info
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= 9:
                info["errors"].append(
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                )
                return info

    h, w = len(grid), width
    # Different-colored cardinal neighbors are separate Racket objects but do
    # not match this task's deliberately separated-component teaching grammar.
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other not in (0, value):
                        info["errors"].append(
                            f"different-colored components touch at ({r},{c}) and ({nr},{nc})"
                        )
                        return info

    facts = [_component_facts(component, h, w) for component in _components(grid)]
    fillable = [component for component in facts if component["fillable"]]
    controls = [component for component in facts if not component["fillable"]]
    runs = [run for component in fillable for run in component["gap_runs"]]
    has_short = any(run == 1 for run in runs)
    has_long = any(run >= 2 for run in runs)
    gap_profile = "mixed" if has_short and has_long else "short" if has_short else "long"
    colors = [component["color"] for component in facts]
    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "components": facts,
            "fillable_components": fillable,
            "controls": controls,
            "component_count": len(facts),
            "fillable_count": len(fillable),
            "control_count": len(controls),
            "max_gap_columns": max(
                (component["gap_column_count"] for component in fillable), default=0
            ),
            "gap_profile": gap_profile,
            "control_mode": "one" if len(controls) == 1 else "none" if not controls else "many",
            "color_mode": "distinct" if len(colors) == len(set(colors)) else "reused",
            "edge_profile": "touching" if any(c["touches_edge"] for c in facts) else "interior",
        }
    )
    return info


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {name: info[name] for name in AXES}


def self_check(grid: Any, *, difficulty: Any = None,
               meta: dict[str, Any] | None = None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if not 10 <= info["grid_h"] <= 16:
        errors.append(f"grid height {info['grid_h']} outside 10..16")
    if not 12 <= info["grid_w"] <= 20:
        errors.append(f"grid width {info['grid_w']} outside 12..20")
    if not 2 <= info["component_count"] <= 5:
        errors.append(f"component count {info['component_count']} outside 2..5")
    if info["fillable_count"] < 1:
        errors.append("no component has a fillable vertical column gap")
    if info["control_count"] > 1:
        errors.append(f"expected at most one unchanged control, got {info['control_count']}")
    for index, component in enumerate(info["fillable_components"]):
        if not 1 <= component["gap_column_count"] <= 3:
            errors.append(
                f"fillable component {index} has {component['gap_column_count']} gap columns; expected 1..3"
            )
    if info["gap_profile"] not in _GAP_PROFILES:
        errors.append(f"unrecognized gap profile {info['gap_profile']!r}")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests; canonical Racket remains authoritative."""
    out = deepcopy(grid)
    for component in _components(grid):
        by_col: dict[int, list[int]] = {}
        for r, c in component["cells"]:
            by_col.setdefault(c, []).append(r)
        for col, rows in by_col.items():
            for row in range(min(rows), max(rows) + 1):
                out[row][col] = component["color"]
    return out


def strict_canonical_like(grid: Any) -> list[str]:
    info = _analyze(grid)
    reasons = list(info["errors"])
    if reasons:
        return reasons
    if (info["grid_h"], info["grid_w"]) not in {(10, 15), (10, 16)}:
        reasons.append("canonical dimensions are 10x15 or 10x16")
    if info["component_count"] != 3:
        reasons.append("canonical scenes contain exactly three components")
    if info["fillable_count"] != 2 or info["control_count"] != 1:
        reasons.append("canonical scenes contain two fillable components and one unchanged control")
    if info["color_mode"] != "distinct":
        reasons.append("canonical component colors are distinct")
    if info["edge_profile"] != "interior":
        reasons.append("canonical components do not touch the grid boundary")
    if info["gap_profile"] != "mixed":
        reasons.append("canonical scenes jointly contain one-row and multi-row gaps")
    if sorted(c["gap_column_count"] for c in info["fillable_components"]) != [1, 2]:
        reasons.append("canonical fillable components have one and two gap columns")
    if sorted(c["size"] for c in info["fillable_components"]) != [8, 8]:
        reasons.append("canonical fillable components each contain eight input cells")
    if info["controls"] and info["controls"][0]["size"] not in (5, 6):
        reasons.append("canonical unchanged control contains five or six cells")
    return reasons


def _paint_component_spans(out: list[list[int]], component: dict[str, Any]) -> None:
    by_col: dict[int, list[int]] = {}
    for r, c in component["cells"]:
        by_col.setdefault(c, []).append(r)
    for col, rows in by_col.items():
        for row in range(min(rows), max(rows) + 1):
            out[row][col] = component["color"]


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def _global_same_color_column_closure(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        for col in range(len(grid[0])):
            rows = [row for row in range(len(grid)) if grid[row][col] == color]
            if rows:
                for row in range(min(rows), max(rows) + 1):
                    out[row][col] = color
    return out


def _fill_component_bboxes(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for component in _components(grid):
        r1, c1, r2, c2 = component["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                out[row][col] = component["color"]
    return out


def _largest_components_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    components = _components(grid)
    largest = max(len(component["cells"]) for component in components)
    for component in components:
        if len(component["cells"]) == largest:
            _paint_component_spans(out, component)
    return out


def _eight_cell_components_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for component in _components(grid):
        if len(component["cells"]) == 8:
            _paint_component_spans(out, component)
    return out


def _first_two_fillable_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    facts = [_component_facts(component, len(grid), len(grid[0])) for component in _components(grid)]
    for component in [c for c in facts if c["fillable"]][:2]:
        _paint_component_spans(out, component)
    return out


def _frame_like_components_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    facts = [_component_facts(component, len(grid), len(grid[0])) for component in _components(grid)]
    for component in facts:
        if component["frame_like"]:
            _paint_component_spans(out, component)
    return out


def _short_gaps_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    facts = [_component_facts(component, len(grid), len(grid[0])) for component in _components(grid)]
    for component in facts:
        by_col: dict[int, list[int]] = {}
        for r, c in component["cells"]:
            by_col.setdefault(c, []).append(r)
        for col, rows in by_col.items():
            if _missing_runs(rows) and all(run == 1 for run in _missing_runs(rows)):
                for row in range(min(rows), max(rows) + 1):
                    out[row][col] = component["color"]
    return out


def _first_gap_column_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    facts = [_component_facts(component, len(grid), len(grid[0])) for component in _components(grid)]
    for component in facts:
        if not component["gap_columns"]:
            continue
        col = min(component["gap_columns"])
        rows = [r for r, c in component["cells"] if c == col]
        for row in range(min(rows), max(rows) + 1):
            out[row][col] = component["color"]
    return out


def _row_span_closure(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for component in _components(grid):
        by_row: dict[int, list[int]] = {}
        for r, c in component["cells"]:
            by_row.setdefault(r, []).append(c)
        for row, cols in by_row.items():
            for col in range(min(cols), max(cols) + 1):
                out[row][col] = component["color"]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "global_same_color_column_closure": _global_same_color_column_closure,
    "fill_component_bboxes": _fill_component_bboxes,
    "largest_components_only": _largest_components_only,
    "eight_cell_components_only": _eight_cell_components_only,
    "first_two_fillable_only": _first_two_fillable_only,
    "frame_like_components_only": _frame_like_components_only,
    "short_gaps_only": _short_gaps_only,
    "first_gap_column_only": _first_gap_column_only,
    "row_span_closure": _row_span_closure,
}

LESSON_COMPETITORS = SEMANTIC_RIVALS

# These fit all three real canonical pairs and therefore require generated
# counterexamples; the schedule supplies at least two independent rebuttals.
CANONICAL_SHORTCUTS = {
    "global_same_color_column_closure": _global_same_color_column_closure,
    "largest_components_only": _largest_components_only,
    "eight_cell_components_only": _eight_cell_components_only,
    "first_two_fillable_only": _first_two_fillable_only,
    "frame_like_components_only": _frame_like_components_only,
}


def _has_short_gap(grid: Any) -> bool:
    return any(run == 1 for c in _analyze(grid)["fillable_components"] for run in c["gap_runs"])


def _has_long_gap(grid: Any) -> bool:
    return any(run >= 2 for c in _analyze(grid)["fillable_components"] for run in c["gap_runs"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "short_gap_run": _has_short_gap,
    "long_gap_run": _has_long_gap,
    "unchanged_column_convex_control": lambda grid: bool(_analyze(grid)["controls"]),
    "repeated_color_components": lambda grid: _analyze(grid)["color_mode"] == "reused",
    "multiple_gap_columns": lambda grid: any(
        c["gap_column_count"] >= 2 for c in _analyze(grid)["fillable_components"]
    ),
    "non_frame_fillable": lambda grid: any(
        not c["frame_like"] for c in _analyze(grid)["fillable_components"]
    ),
    "more_than_two_fillable_components": lambda grid: _analyze(grid)["fillable_count"] > 2,
    "fillable_smaller_than_largest": lambda grid: any(
        c["fillable"] and c["size"] < max(x["size"] for x in _analyze(grid)["components"])
        for c in _analyze(grid)["components"]
    ),
    "non_eight_cell_fillable": lambda grid: any(
        c["size"] != 8 for c in _analyze(grid)["fillable_components"]
    ),
}

WITNESS_RIVALS = {
    "short_gap_run": ["identity"],
    "long_gap_run": ["short_gaps_only"],
    "unchanged_column_convex_control": ["fill_component_bboxes"],
    "repeated_color_components": ["global_same_color_column_closure"],
    "multiple_gap_columns": ["first_gap_column_only"],
    "non_frame_fillable": ["frame_like_components_only"],
    "more_than_two_fillable_components": ["first_two_fillable_only"],
    "fillable_smaller_than_largest": ["largest_components_only"],
    "non_eight_cell_fillable": ["eight_cell_components_only"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demonstrations: {name}")
    return reasons


def _place_shape(grid: list[list[int]], shape: Shape, r0: int, c0: int, color: int) -> None:
    for dr, dc in shape:
        grid[r0 + dr][c0 + dc] = color


def _can_place(grid: list[list[int]], shape: Shape, r0: int, c0: int) -> bool:
    h, w = len(grid), len(grid[0])
    cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
    if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        return False
    for r, c in cells:
        if grid[r][c] != 0:
            return False
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells and grid[nr][nc] != 0:
                return False
    return True


def _candidate_positions(h: int, w: int, shape: Shape, *, touching: bool) -> list[tuple[int, int]]:
    sh, sw = _shape_size(shape)
    positions: list[tuple[int, int]] = []
    for r0 in range(0, h - sh + 1):
        for c0 in range(0, w - sw + 1):
            is_touching = r0 == 0 or c0 == 0 or r0 + sh == h or c0 + sw == w
            if touching != is_touching:
                continue
            positions.append((r0, c0))
    return positions


def _pack_shapes(h: int, w: int, shapes: list[Shape], colors: list[int], rng,
                 edge_profile: str) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    order = sorted(range(len(shapes)), key=lambda i: len(shapes[i]), reverse=True)

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        touching = edge_profile == "touching" and depth == 0
        candidates = _candidate_positions(h, w, shapes[index], touching=touching)
        rng.shuffle(candidates)
        # Prefer interior candidates for every component after the required edge witness.
        if not touching:
            interior = [p for p in candidates if p[0] > 0 and p[1] > 0
                        and p[0] + _shape_size(shapes[index])[0] < h
                        and p[1] + _shape_size(shapes[index])[1] < w]
            boundary = [p for p in candidates if p not in set(interior)]
            candidates = interior + boundary
        for r0, c0 in candidates:
            if not _can_place(grid, shapes[index], r0, c0):
                continue
            _place_shape(grid, shapes[index], r0, c0, colors[index])
            if search(depth + 1):
                return True
            for dr, dc in shapes[index]:
                grid[r0 + dr][c0 + dc] = 0
        return False

    if not search(0):
        raise ValueError(
            f"could not pack {len(shapes)} separated components in {h}x{w}"
        )
    return grid


def _canonical_anchor(ctx, width: int, variant: int) -> list[list[int]]:
    h = 10
    rng = ctx.draw_rng(f"anchor-layout-{variant}")
    palettes = ((2, 3, 4), (4, 6, 7), (2, 4, 6), (3, 5, 8))
    colors = list(palettes[rng.randrange(len(palettes))])
    rng.shuffle(colors)
    c_shape = _C4_LEFT if rng.randrange(2) == 0 else _C4_RIGHT
    control = _T5 if (rng.randrange(2) + variant) % 2 == 0 else _STAIR6
    grid = full_grid(h, width, 0)

    left_c = 1 + rng.randrange(2)
    right_c = width - 4 - rng.randrange(2)
    left_r = 1 + rng.randrange(2)
    right_r = 1
    control_c = 4 + rng.randrange(max(1, width - 9))
    _place_shape(grid, _RING3, left_r, left_c, colors[0])
    _place_shape(grid, c_shape, right_r, right_c, colors[1])
    _place_shape(grid, control, 6, control_c, colors[2])
    return grid


def _profile_short_recombination(ctx) -> list[list[int]]:
    rng = ctx.draw_rng("short-recombination-layout")
    grid = full_grid(12, 14, 0)
    color = rng.choice((2, 3, 5, 6, 7, 8))
    top = _fillable_shape("short", 1, staggered=False)   # 5 cells
    bottom = _fillable_shape("short", 1, staggered=True)  # 6 cells
    col = 2 + rng.randrange(4)
    _place_shape(grid, top, 1, col, color)
    _place_shape(grid, bottom, 7, col, color)
    return grid


def _profile_irregular_mixed(ctx) -> list[list[int]]:
    rng = ctx.draw_rng("irregular-mixed-layout")
    grid = full_grid(14, 17, 0)
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 8, 9), 4)
    shapes_and_pos = (
        (_fillable_shape("mixed", 2, staggered=True), 1, 1),
        (_fillable_shape("short", 1, staggered=True), 1, 6),
        (_fillable_shape("long", 2, staggered=True), 7, 6),
        (_LARGE_CONTROL, 9, 11),
    )
    for color, (shape, r0, c0) in zip(colors, shapes_and_pos):
        _place_shape(grid, shape, r0, c0, color)
    return grid


def _profile_long_boundary(ctx) -> list[list[int]]:
    rng = ctx.draw_rng("long-boundary-layout")
    grid = full_grid(14, 18, 0)
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 8, 9), 4)
    repeated, color_c, color_d, control_color = colors
    shapes_and_pos = (
        (_fillable_shape("long", 2, staggered=True), 0, 1, repeated),
        (_fillable_shape("long", 2, staggered=True), 8, 1, repeated),
        (_fillable_shape("long", 3, staggered=True), 0, 6, color_c),
        (_fillable_shape("long", 1, staggered=False), 8, 7, color_d),
        (_LARGE_CONTROL, 9, 12, control_color),
    )
    for shape, r0, c0, color in shapes_and_pos:
        _place_shape(grid, shape, r0, c0, color)
    return grid


def _generic_scene(ctx, overrides: dict[str, Any]) -> list[list[int]]:
    # Safe defaults make every boundary pair in override-contract v7 fit.  The
    # ordinary no-override teaching distribution is the richer schedule above.
    component_count = _draw_int(ctx, overrides, "component_count", 3, 2, 5)
    max_gap_columns = _draw_int(ctx, overrides, "max_gap_columns", 1, 1, 3)
    gap_profile = _draw_choice(ctx, overrides, "gap_profile", "short", _GAP_PROFILES)
    control_mode = _draw_choice(ctx, overrides, "control_mode", "one", _CONTROL_MODES)
    color_mode = _draw_choice(ctx, overrides, "color_mode", "distinct", _COLOR_MODES)
    edge_profile = _draw_choice(ctx, overrides, "edge_profile", "interior", _EDGE_PROFILES)

    control_count = 1 if control_mode == "one" else 0
    fillable_count = component_count - control_count
    if fillable_count < 1:
        raise ValueError("component_count and control_mode leave no fillable component")

    grid_h = _draw_int(ctx, overrides, "grid_h", 16, 10, 16)
    grid_w = _draw_int(ctx, overrides, "grid_w", 20, 12, 20)
    shapes = [
        _fillable_shape(gap_profile, max_gap_columns, staggered=(index % 2 == 1))
        for index in range(fillable_count)
    ]
    if control_count:
        shapes.append(_T5)

    rng = ctx.draw_rng("generic-layout")
    palette = rng.sample((1, 2, 3, 4, 5, 6, 7, 8, 9), component_count)
    if color_mode == "reused":
        colors = [palette[0], palette[0], *palette[2:component_count]]
    else:
        colors = palette
    grid = _pack_shapes(grid_h, grid_w, shapes, colors, rng, edge_profile)
    return grid


def generate(seed: int, sample_index: int, *, difficulty: Any = None,
             **overrides: Any) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides:
        grid = _generic_scene(ctx, overrides)
    else:
        profile = schedule_profile(seed, sample_index, difficulty)
        if profile == "canonical_anchor_15":
            expected = {
                "grid_h": 10, "grid_w": 15, "component_count": 3,
                "max_gap_columns": 2, "gap_profile": "mixed",
                "control_mode": "one", "color_mode": "distinct",
                "edge_profile": "interior",
            }
            grid = _canonical_anchor(ctx, 15, 0)
        elif profile == "same_color_short_recombination":
            expected = {
                "grid_h": 12, "grid_w": 14, "component_count": 2,
                "max_gap_columns": 1, "gap_profile": "short",
                "control_mode": "none", "color_mode": "reused",
                "edge_profile": "interior",
            }
            grid = _profile_short_recombination(ctx)
        elif profile == "canonical_anchor_16":
            expected = {
                "grid_h": 10, "grid_w": 16, "component_count": 3,
                "max_gap_columns": 2, "gap_profile": "mixed",
                "control_mode": "one", "color_mode": "distinct",
                "edge_profile": "interior",
            }
            grid = _canonical_anchor(ctx, 16, 1)
        elif profile == "irregular_mixed_controls":
            expected = {
                "grid_h": 14, "grid_w": 17, "component_count": 4,
                "max_gap_columns": 2, "gap_profile": "mixed",
                "control_mode": "one", "color_mode": "distinct",
                "edge_profile": "interior",
            }
            grid = _profile_irregular_mixed(ctx)
        else:
            expected = {
                "grid_h": 14, "grid_w": 18, "component_count": 5,
                "max_gap_columns": 3, "gap_profile": "long",
                "control_mode": "one", "color_mode": "reused",
                "edge_profile": "touching",
            }
            grid = _profile_long_boundary(ctx)

        # Record every declared exact axis through GenCtx, then prove the
        # returned grid realizes the same values.
        _draw_int(ctx, overrides, "grid_h", expected["grid_h"], 10, 16)
        _draw_int(ctx, overrides, "grid_w", expected["grid_w"], 12, 20)
        _draw_int(ctx, overrides, "component_count", expected["component_count"], 2, 5)
        _draw_int(ctx, overrides, "max_gap_columns", expected["max_gap_columns"], 1, 3)
        _draw_choice(ctx, overrides, "gap_profile", expected["gap_profile"], _GAP_PROFILES)
        _draw_choice(ctx, overrides, "control_mode", expected["control_mode"], _CONTROL_MODES)
        _draw_choice(ctx, overrides, "color_mode", expected["color_mode"], _COLOR_MODES)
        _draw_choice(ctx, overrides, "edge_profile", expected["edge_profile"], _EDGE_PROFILES)

    observed = observe_overrides(grid)
    drawn = ctx.recorded_draws()
    expected_axes = {name: drawn[name] for name in AXES}
    if observed != expected_axes:
        raise RuntimeError(f"constructed axes drifted: expected {expected_axes}, observed {observed}")
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed grid failed self_check: {errors}")
    return grid
