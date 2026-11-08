"""Generator for ARC task 28c998e193d9: component-wise horizontal closure.

Every non-background 4-connected component is handled independently.  Within
one component, each occupied row is closed from that row's leftmost cell to its
rightmost cell and painted cyan (8).  Different components must never be
bridged merely because they share a row.

The imported generator emitted only disjoint hollow rectangles and described
the rule as whole-bounding-box fill.  That distribution taught several wrong
rules.  This version stays on the canonical 8x14 / 9x15 scale but always
includes at least one connected bent-outline component whose row spans change
with height.  It also places two or three components on shared rows, so each
grid separates component-wise row closure from whole-bbox fill, frame-by-frame
fill, global row closure, recolor-only, and vertical closure.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28c998e193d9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b18cc934f1d8"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A canonical-scale 0-background grid contains two or three red (2) "
    "4-connected outline components. For each component independently, fill "
    "every occupied row between that component's own leftmost and rightmost "
    "cells, painting the result cyan (8). Bent components have row spans that "
    "change with height, and components share rows without being bridged."
)

INVARIANTS = [
    "the grid is exactly 8x14 or 9x15 and uses only colors 0 and 2",
    "there are exactly two or three red 4-connected components",
    "every occupied component row has at least two red cells",
    "row closure adds at least one cell for every component",
    "at least two components share a row while remaining separated by zeroes",
    "generated scenes include one or two bent components whose row spans change with height",
]

PROFILE_NAMES = (
    "pair_one_bent",
    "triple_one_bent",
    "pair_two_bent",
    "triple_two_bent",
)
SCHEDULE_PROFILES = PROFILE_NAMES
AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "difficulty-aware four-profile cycle",
        "valid": "|".join(PROFILE_NAMES),
        "doc": "Observable component-count / bent-component curriculum profile.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

PALETTE_KINDS: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components_4(grid: Sequence[Sequence[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and grid[point[0]][point[1]] == 2
                        and point not in seen
                    ):
                        seen.add(point)
                        stack.append(point)
            components.append(tuple(sorted(cells)))
    return components


def _rows_of(cells: Iterable[tuple[int, int]]) -> dict[int, tuple[int, ...]]:
    rows: dict[int, list[int]] = {}
    for row, col in cells:
        rows.setdefault(row, []).append(col)
    return {row: tuple(sorted(cols)) for row, cols in rows.items()}


def _row_close_cells(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for row, cols in _rows_of(cells).items():
        result.update((row, col) for col in range(cols[0], cols[-1] + 1))
    return result


def _bbox_cells(cells: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    r1 = min(row for row, _ in cells)
    r2 = max(row for row, _ in cells)
    c1 = min(col for _, col in cells)
    c2 = max(col for _, col in cells)
    return {(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)}


def _vertical_close_cells(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    columns: dict[int, list[int]] = {}
    for row, col in cells:
        columns.setdefault(col, []).append(row)
    result: set[tuple[int, int]] = set()
    for col, rows in columns.items():
        result.update((row, col) for row in range(min(rows), max(rows) + 1))
    return result


def _paint(height: int, width: int, cells: Iterable[tuple[int, int]], color: int = 8):
    output = full_grid(height, width, 0)
    for row, col in cells:
        output[row][col] = color
    return output


def _has_cross_component_row_gap(records: Sequence[dict[str, Any]]) -> bool:
    for left_index, left in enumerate(records):
        left_rows = left["rows"]
        for right in records[left_index + 1 :]:
            right_rows = right["rows"]
            for row in set(left_rows) & set(right_rows):
                l1, l2 = left_rows[row][0], left_rows[row][-1]
                r1, r2 = right_rows[row][0], right_rows[row][-1]
                if l2 + 1 < r1 or r2 + 1 < l1:
                    return True
    return False


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "components": []}
    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if not palette <= {0, 2}:
        errors.append(f"palette must be a subset of {{0, 2}}, found {sorted(palette)}")
    components = _components_4(grid)
    records: list[dict[str, Any]] = []
    for cells in components:
        rows = _rows_of(cells)
        closure = _row_close_cells(cells)
        bbox = _bbox_cells(cells)
        r1 = min(row for row, _ in cells)
        r2 = max(row for row, _ in cells)
        c1 = min(col for _, col in cells)
        c2 = max(col for _, col in cells)
        records.append(
            {
                "cells": cells,
                "rows": rows,
                "closure": closure,
                "bbox": bbox,
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "bent": closure != bbox,
            }
        )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": records,
        "cross_component_row_gap": _has_cross_component_row_gap(records),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful canonical-scale input grammar, without mutation."""
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    height, width = analysis["height"], analysis["width"]
    if (height, width) not in {(8, 14), (9, 15)}:
        errors.append(f"grid must match canonical scale 8x14 or 9x15, got {height}x{width}")
    if analysis["palette"] != {0, 2}:
        errors.append(f"palette must be exactly {{0, 2}}, found {sorted(analysis['palette'])}")
    records = analysis["components"]
    if not 2 <= len(records) <= 3:
        errors.append(f"expected two or three red components, got {len(records)}")
    for index, record in enumerate(records):
        if record["height"] < 3 or record["width"] < 3:
            errors.append(f"component {index} bbox must be at least 3x3")
        if any(len(cols) < 2 for cols in record["rows"].values()):
            errors.append(f"component {index} has an occupied row with fewer than two red cells")
        if record["closure"] == set(record["cells"]):
            errors.append(f"component {index} row closure adds no cells")
    if records and not analysis["cross_component_row_gap"]:
        errors.append("no shared row separates two components by a zero gap")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar deliberately remains on the canonical manifold."""
    return self_check(grid)


def rule_mirror(grid):
    """Pure-Python diagnostic mirror of the selected Racket row-close rule."""
    errors = _grid_errors(grid)
    if errors:
        return None
    palette = {value for row in grid for value in row}
    if not palette <= {0, 2}:
        return None
    cells: set[tuple[int, int]] = set()
    for component in _components_4(grid):
        cells.update(_row_close_cells(component))
    return _paint(len(grid), len(grid[0]), cells, 8)


# ---------------------------------------------------------------- rivals

def _rival_component_bbox_fill(grid):
    if _grid_errors(grid):
        return None
    cells: set[tuple[int, int]] = set()
    for component in _components_4(grid):
        cells.update(_bbox_cells(component))
    return _paint(len(grid), len(grid[0]), cells, 8)


def _rival_global_row_close(grid):
    if _grid_errors(grid):
        return None
    cells = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value]
    return _paint(len(grid), len(grid[0]), _row_close_cells(cells), 8)


def _rival_recolor_only(grid):
    if _grid_errors(grid):
        return None
    return [[8 if value else 0 for value in row] for row in grid]


def _rival_vertical_close(grid):
    if _grid_errors(grid):
        return None
    cells: set[tuple[int, int]] = set()
    for component in _components_4(grid):
        cells.update(_vertical_close_cells(component))
    return _paint(len(grid), len(grid[0]), cells, 8)


def _rival_first_component_only(grid):
    if _grid_errors(grid):
        return None
    components = _components_4(grid)
    cells = _row_close_cells(components[0]) if components else set()
    return _paint(len(grid), len(grid[0]), cells, 8)


def _horizontal_runs(row: Sequence[int]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    start = None
    for index, value in enumerate((*row, 0)):
        if value == 2 and start is None:
            start = index
        elif value != 2 and start is not None:
            if index - start >= 3:
                result.append((start, index - 1))
            start = None
    return result


def _rival_frame_by_frame_fill(grid):
    """Plausible canonical shortcut: fill each top-bar/side-rail frame.

    It reproduces all supplied demonstrations, including the two touching
    frames that form one 4-connected component in the first demonstration,
    but it fails on bent rails that are not a stack of independent frames.
    """
    if _grid_errors(grid):
        return None
    height, width = len(grid), len(grid[0])
    painted: set[tuple[int, int]] = set()
    for top, values in enumerate(grid):
        for left, right in _horizontal_runs(values):
            bottom = top
            while (
                bottom + 1 < height
                and grid[bottom + 1][left] == 2
                and grid[bottom + 1][right] == 2
            ):
                bottom += 1
            if bottom > top:
                painted.update(
                    (row, col)
                    for row in range(top, bottom + 1)
                    for col in range(left, right + 1)
                )
    return _paint(height, width, painted, 8)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "frame_by_frame_fill": _rival_frame_by_frame_fill,
    "component_bbox_fill": _rival_component_bbox_fill,
    "global_row_close": _rival_global_row_close,
    "recolor_only": _rival_recolor_only,
    "vertical_close": _rival_vertical_close,
    "first_component_only": _rival_first_component_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"frame_by_frame_fill": _rival_frame_by_frame_fill}


def _refutes(rival_name: str):
    def witness(grid) -> bool:
        answer = rule_mirror(grid)
        rival = SEMANTIC_RIVALS[rival_name](grid)
        return answer is not None and rival is not None and answer != rival

    return witness


SEMANTIC_WITNESSES = {
    "bent_component_refutes_frame_fill": _refutes("frame_by_frame_fill"),
    "changing_row_spans_refute_bbox_fill": _refutes("component_bbox_fill"),
    "component_gap_refutes_global_row_close": _refutes("global_row_close"),
    "interior_gaps_refute_recolor_only": _refutes("recolor_only"),
    "horizontal_not_vertical_closure": _refutes("vertical_close"),
    "all_components_are_transformed": _refutes("first_component_only"),
}
WITNESS_RIVALS = {
    "bent_component_refutes_frame_fill": ["frame_by_frame_fill"],
    "changing_row_spans_refute_bbox_fill": ["component_bbox_fill"],
    "component_gap_refutes_global_row_close": ["global_row_close"],
    "interior_gaps_refute_recolor_only": ["recolor_only"],
    "horizontal_not_vertical_closure": ["vertical_close"],
    "all_components_are_transformed": ["first_component_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the lawful input grammar: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with component-wise row closure")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the lawful input grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with component-wise row closure")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            isinstance(demo, dict)
            and competitor(demo["input"]) == demo.get("output")
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


# -------------------------------------------------------------- templates

def _template(*rows: str) -> tuple[tuple[int, ...], ...]:
    width = len(rows[0])
    if any(len(row) != width or set(row) - {"0", "2"} for row in rows):
        raise ValueError("invalid template literal")
    return tuple(tuple(int(value) for value in row) for row in rows)


FRAME_3X3 = _template("222", "202", "202")
FRAME_4X3 = _template("222", "202", "202", "202")
FRAME_3X4 = _template("2222", "2002", "2002")
BENT_6X5 = _template(
    "22222",
    "20002",
    "20022",
    "20020",
    "22020",
    "02020",
)
FRAME_BANK = (FRAME_3X3, FRAME_4X3, FRAME_3X4)
NARROW_FRAME_BANK = (FRAME_3X3, FRAME_4X3)


def _flip_lr(template: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in template)


def _flip_ud(template: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in reversed(template))


def _transform(template: Sequence[Sequence[int]], code: int) -> tuple[tuple[int, ...], ...]:
    result = tuple(tuple(row) for row in template)
    if code & 1:
        result = _flip_lr(result)
    if code & 2:
        result = _flip_ud(result)
    return result


def _stamp(grid: list[list[int]], template: Sequence[Sequence[int]], top: int, left: int) -> None:
    height, width = len(grid), len(grid[0])
    for dr, row in enumerate(template):
        for dc, value in enumerate(row):
            if not value:
                continue
            rr, cc = top + dr, left + dc
            if not (0 <= rr < height and 0 <= cc < width):
                raise ValueError("internal template placement out of bounds")
            if grid[rr][cc] != 0:
                raise ValueError("internal template placement overlap")
            grid[rr][cc] = value


def _random_frame(rng, *, narrow: bool = False):
    bank = NARROW_FRAME_BANK if narrow else FRAME_BANK
    return _transform(rng.choice(bank), rng.randrange(4))


def _random_bent(rng):
    return _transform(BENT_6X5, rng.randrange(4))


_PROFILE_SCHEDULES = {
    "easy": (
        "pair_one_bent",
        "triple_one_bent",
        "pair_two_bent",
        "triple_two_bent",
    ),
    "medium": (
        "triple_one_bent",
        "pair_two_bent",
        "triple_two_bent",
        "pair_one_bent",
    ),
    "hard": (
        "pair_two_bent",
        "triple_two_bent",
        "pair_one_bent",
        "triple_one_bent",
    ),
}


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _PROFILE_SCHEDULES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return difficulty


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed
    band = _band(difficulty)
    schedule = _PROFILE_SCHEDULES[band]
    return schedule[int(sample_index) % len(schedule)]


def _draw_profile(ctx, default: str) -> str:
    if "scene_profile" in ctx.overrides and ctx.overrides["scene_profile"] is not None:
        return ctx.draw_choice("scene_profile", PROFILE_NAMES)
    return ctx.draw_choice("scene_profile", (default,))


def _build_profile(profile: str, rng) -> list[list[int]]:
    if profile == "pair_one_bent":
        grid = full_grid(8, 14, 0)
        _stamp(grid, _random_bent(rng), 1, 1)
        frame = _random_frame(rng)
        _stamp(grid, frame, rng.randint(1, 8 - len(frame) - 1), 9)
        return grid

    if profile == "triple_one_bent":
        grid = full_grid(9, 15, 0)
        _stamp(grid, _random_bent(rng), 1, 0)
        frame_a = _random_frame(rng)
        frame_b = _random_frame(rng, narrow=True)
        _stamp(grid, frame_a, rng.randint(1, 9 - len(frame_a) - 1), 7)
        _stamp(grid, frame_b, rng.randint(1, 9 - len(frame_b) - 1), 12)
        return grid

    if profile == "pair_two_bent":
        grid = full_grid(8, 14, 0)
        _stamp(grid, _random_bent(rng), 1, 1)
        _stamp(grid, _random_bent(rng), 1, 8)
        return grid

    if profile == "triple_two_bent":
        grid = full_grid(9, 15, 0)
        _stamp(grid, _random_bent(rng), 1, 0)
        _stamp(grid, _random_bent(rng), 1, 6)
        frame = _random_frame(rng, narrow=True)
        _stamp(grid, frame, rng.randint(1, 9 - len(frame) - 1), 12)
        return grid

    raise ValueError(f"unsupported scene profile: {profile!r}")


def _profile_from_analysis(analysis: dict[str, Any]) -> str | None:
    records = analysis.get("components", [])
    key = len(records), sum(bool(record["bent"]) for record in records)
    return {
        (2, 1): "pair_one_bent",
        (3, 1): "triple_one_bent",
        (2, 2): "pair_two_bent",
        (3, 2): "triple_two_bent",
    }.get(key)


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analysis(grid)
    profile = None if analysis["errors"] else _profile_from_analysis(analysis)
    if profile is None:
        return {"errors": list(analysis["errors"]) or ["unrecognized scene profile"]}
    return {"scene_profile": profile}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _draw_profile(ctx, schedule_profile(seed, sample_index, band))
    grid = _build_profile(profile, ctx.draw_rng("layout"))
    errors = self_check(grid, difficulty=band)
    if errors:
        raise ValueError(f"internal generator contract violation: {errors}")
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise ValueError(f"internal profile observation mismatch: {observed}")
    failed_witnesses = [name for name, witness in SEMANTIC_WITNESSES.items() if not witness(grid)]
    if failed_witnesses:
        raise ValueError(f"internal semantic witness failure: {failed_witnesses}")
    return [row[:] for row in grid]


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    blank = full_grid(8, 14, 0)

    one_component = full_grid(8, 14, 0)
    _stamp(one_component, BENT_6X5, 1, 1)

    no_closure = full_grid(8, 14, 0)
    for row in range(1, 4):
        for col in range(1, 4):
            no_closure[row][col] = 2
    for row in range(1, 4):
        for col in range(8, 11):
            no_closure[row][col] = 2

    wrong_color = generate(7, 0)
    first_red = next(
        (row, col)
        for row, values in enumerate(wrong_color)
        for col, value in enumerate(values)
        if value == 2
    )
    wrong_color[first_red[0]][first_red[1]] = 3

    no_shared_row = full_grid(9, 15, 0)
    _stamp(no_shared_row, FRAME_3X3, 0, 1)
    _stamp(no_shared_row, FRAME_3X3, 6, 10)

    ragged = generate(11, 1)
    ragged[-1] = ragged[-1][:-1]

    return [
        ("blank_no_components", blank),
        ("only_one_component", one_component),
        ("solid_components_no_closure", no_closure),
        ("wrong_nonbackground_color", wrong_color),
        ("components_share_no_row", no_shared_row),
        ("ragged_grid", ragged),
    ]
