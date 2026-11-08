"""Episode-fixed closure-order family for ARC task 89dfcff52ee8.

The exact canonical setting, ``rows_only``, closes each active row between its
leftmost and rightmost nonzero markers.  The alternate, ``rows_then_columns``,
first computes that input-dependent row closure and then closes every occupied
column over the intermediate cells.  The second stage therefore cannot be
chosen or executed correctly without the first stage's per-input result.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_path, find_root

TASK_ID = "89dfcff52ee8"
REPO = find_root(__file__)
HERE = Path(__file__).resolve().parent
PARAMETERS = {"closure": ["rows_only", "rows_then_columns"]}
DEFAULT = {"closure": "rows_only"}
SETTINGS = [{"closure": value} for value in PARAMETERS["closure"]]
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4

DEMO_SIZES = ((8, 10), (10, 13), (12, 16), (14, 19), (18, 23), (22, 27))
QUERY_SIZES = ((9, 12), (15, 18), (24, 27), (30, 30))


def _canonical_program() -> str:
    matches: list[str] = []
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if not matches or len(set(matches)) != 1:
        raise RuntimeError(f"expected one exact canonical program for {TASK_ID}")
    return matches[0]


CANONICAL_PROGRAM = _canonical_program()
_CANONICAL_FINAL = (
    "(paint-cells (empty-grid (rows g) (cols g) 0) "
    "(row-close (pos-only (nonzero-cells g))) 8)"
)
if CANONICAL_PROGRAM.count(_CANONICAL_FINAL) != 1:
    raise RuntimeError("canonical final expression changed")

_COL_CLOSE_DEF = (
    "(define (col-close cells) "
    "(remove-duplicates "
    "(flatmap "
    "(lambda (c) "
    "(let* ((rs (sort (map first (filter (lambda (p) (= (second p) c)) cells)) <))) "
    "(if (empty? rs) (list) "
    "(for/list ((r (in-range (first rs) (+ (last rs) 1)))) (list r c))))) "
    "(remove-duplicates (map second cells)))))"
)

_ROWS_THEN_COLUMNS_FINAL = (
    f"(let () {_COL_CLOSE_DEF} "
    "(let* ((markers (pos-only (nonzero-cells g))) "
    "(horizontal (row-close markers)) "
    "(completed (col-close horizontal))) "
    "(paint-cells (empty-grid (rows g) (cols g) 0) completed 8)))"
)
_SKIP_ROW_CLOSURE_FINAL = (
    f"(let () {_COL_CLOSE_DEF} "
    "(let* ((markers (pos-only (nonzero-cells g))) "
    "(completed (col-close markers))) "
    "(paint-cells (empty-grid (rows g) (cols g) 0) completed 8)))"
)
_COLUMNS_THEN_ROWS_FINAL = (
    f"(let () {_COL_CLOSE_DEF} "
    "(let* ((markers (pos-only (nonzero-cells g))) "
    "(vertical (col-close markers)) "
    "(completed (row-close vertical))) "
    "(paint-cells (empty-grid (rows g) (cols g) 0) completed 8)))"
)

ROWS_THEN_COLUMNS_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_FINAL, _ROWS_THEN_COLUMNS_FINAL
)
SKIP_ROW_CLOSURE_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_FINAL, _SKIP_ROW_CLOSURE_FINAL
)
COLUMNS_THEN_ROWS_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_FINAL, _COLUMNS_THEN_ROWS_FINAL
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"closure"}:
        raise ValueError("settings must contain exactly closure")
    closure = value["closure"]
    if type(closure) is not str or closure not in PARAMETERS["closure"]:
        raise ValueError("closure must be rows_only or rows_then_columns")
    return {"closure": closure}


def program(settings: object) -> str:
    selected = _settings(settings)
    return (
        CANONICAL_PROGRAM
        if selected["closure"] == "rows_only"
        else ROWS_THEN_COLUMNS_PROGRAM
    )


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 1..30 list")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact ARC integers in a rectangle")
    return copy.deepcopy(value)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def marker_positions(grid: object) -> frozenset[tuple[int, int]]:
    checked = _grid(grid)
    return frozenset(
        (r, c)
        for r, row in enumerate(checked)
        for c, value in enumerate(row)
        if value != 0
    )


def _row_close(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    rows = sorted({r for r, _ in cells})
    result: set[tuple[int, int]] = set()
    for row in rows:
        cols = [c for r, c in cells if r == row]
        result.update((row, col) for col in range(min(cols), max(cols) + 1))
    return frozenset(result)


def _column_close(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cols = sorted({c for _, c in cells})
    result: set[tuple[int, int]] = set()
    for col in cols:
        rows = [r for r, c in cells if c == col]
        result.update((row, col) for row in range(min(rows), max(rows) + 1))
    return frozenset(result)


def row_intermediate(grid: object) -> frozenset[tuple[int, int]]:
    return _row_close(marker_positions(grid))


def _paint(height: int, width: int, cells: frozenset[tuple[int, int]]) -> list[list[int]]:
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in cells:
        output[row][col] = 8
    return output


def transform(grid: object, settings: object) -> list[list[int]]:
    checked = _grid(grid)
    selected = _settings(settings)
    horizontal = _row_close(marker_positions(checked))
    completed = (
        horizontal
        if selected["closure"] == "rows_only"
        else _column_close(horizontal)
    )
    return _paint(len(checked), len(checked[0]), completed)


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    payload = f"{TASK_ID}|{seed}|{stream}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _spread_rows(height: int, count: int, *, boundary: bool) -> list[int]:
    start, end = (0, height - 1) if boundary else (1, height - 2)
    if end - start + 1 < count:
        raise ValueError("not enough rows for scene profile")
    result = [round(start + index * (end - start) / (count - 1)) for index in range(count)]
    # Round-to-nearest is unique for the admitted dimensions, but fail closed if
    # a future size schedule violates that constructive assumption.
    if len(set(result)) != count:
        raise RuntimeError("row spread collapsed")
    return result


def _intervals(width: int, count: int, rng: random.Random, *, boundary: bool) -> list[tuple[int, int]]:
    """Construct broad overlapping spans with mostly unique marker columns.

    The final column is reserved for one singleton row.  Span endpoints are
    unique, so column-first closure cannot reconstruct the row-closure
    intermediate.  Their order is seed-shuffled to vary geometry while every
    span retains a substantial overlap with the others.
    """
    span_count = count - 1
    first_left = 0 if boundary else 1
    lefts = list(range(first_left, first_left + span_count))
    rights = list(range(width - 2, width - 2 - span_count, -1))
    rng.shuffle(rights)
    if any(right - left < 3 for left, right in zip(lefts, rights)):
        raise RuntimeError("size schedule cannot support the closure lesson")
    spans = iter(zip(lefts, rights))
    result: list[tuple[int, int]] = []
    for row_index in range(count):
        if row_index == 2:
            result.append((width - 1, width - 1))
        else:
            result.append(next(spans))
    return result


def _scene(seed: int, stream: str, index: int) -> list[list[int]]:
    if stream == "demo":
        height, width = DEMO_SIZES[index]
    elif stream == "query":
        height, width = QUERY_SIZES[index]
    else:
        raise ValueError(stream)
    boundary = (stream == "query" and index >= 2) or (stream == "demo" and index == 5)
    count = 4 if height < 14 else (5 if height < 22 else 6)
    rows = _spread_rows(height, count, boundary=boundary)
    rng = _rng(seed, stream, index)
    intervals = _intervals(width, count, rng, boundary=boundary)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(palette)
    cursor = 0
    span_indices = [item for item, interval in enumerate(intervals) if interval[0] != interval[1]]
    overlap_left = max(intervals[item][0] for item in span_indices)
    overlap_right = min(intervals[item][1] for item in span_indices)
    shared_candidates = list(range(overlap_left + 1, overlap_right))
    if not shared_candidates:
        raise RuntimeError("spans lack an interior shared probe column")
    shared_column = shared_candidates[len(shared_candidates) // 2]
    shared_rows = {span_indices[0], span_indices[-1]}
    for item, (row, (left, right)) in enumerate(zip(rows, intervals)):
        if left == right:
            grid[row][left] = palette[cursor % len(palette)]
            cursor += 1
            continue
        columns = [left, right]
        if item in shared_rows and shared_column not in columns:
            columns.append(shared_column)
        for column in sorted(set(columns)):
            grid[row][column] = palette[cursor % len(palette)]
            cursor += 1
    scene_profile = profile(grid)
    if not scene_profile["sequentially_decisive"]:
        raise RuntimeError("constructive scene did not expose the sequential dependency")
    if scene_profile["singleton_rows"] != 1:
        raise RuntimeError("constructive scene lost its singleton witness")
    if scene_profile["mixed_color_spans"] < 2:
        raise RuntimeError("constructive scene lost mixed-color span evidence")
    return grid


def profile(grid: object) -> dict[str, Any]:
    checked = _grid(grid)
    markers = marker_positions(checked)
    horizontal = _row_close(markers)
    composed = _column_close(horizontal)
    skipped = _column_close(markers)
    wrong_order = _row_close(skipped)
    active_rows = sorted({r for r, _ in markers})
    singleton_rows = 0
    mixed_color_spans = 0
    for row in active_rows:
        cells = [(c, checked[row][c]) for r, c in markers if r == row]
        if len(cells) == 1:
            singleton_rows += 1
        elif len({value for _, value in cells}) >= 2:
            mixed_color_spans += 1
    if composed:
        rows = [r for r, _ in composed]
        cols = [c for _, c in composed]
        touches = min(rows) == 0 and max(rows) == len(checked) - 1 and min(cols) == 0 and max(cols) == len(checked[0]) - 1
    else:
        touches = False
    return {
        "dimensions": [len(checked), len(checked[0])],
        "active_rows": len(active_rows),
        "marker_cells": len(markers),
        "singleton_rows": singleton_rows,
        "mixed_color_spans": mixed_color_spans,
        "row_intermediate_cells": len(horizontal),
        "composed_cells": len(composed),
        "extension_cells": len(composed - horizontal),
        "touches_all_boundaries": touches,
        "sequentially_decisive": (
            horizontal != markers
            and composed != horizontal
            and composed != skipped
            and composed != wrong_order
        ),
    }


def recolor_markers(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    result = copy.deepcopy(checked)
    for row in range(len(result)):
        for col in range(len(result[0])):
            if result[row][col] != 0:
                result[row][col] = 9 if result[row][col] != 9 else 1
    return result


def shift_one_endpoint(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    result = copy.deepcopy(checked)
    for row, values in enumerate(result):
        cols = [col for col, value in enumerate(values) if value != 0]
        if len(cols) < 2:
            continue
        left, right = min(cols), max(cols)
        if right + 1 < len(values) and values[right + 1] == 0:
            values[right + 1] = values[right]
            values[right] = 0
            return result
        if left > 0 and values[left - 1] == 0:
            values[left - 1] = values[left]
            values[left] = 0
            return result
    raise ValueError("no movable endpoint")


def _remove_singleton_rows(grid: list[list[int]]) -> list[list[int]]:
    result = copy.deepcopy(grid)
    for row in result:
        if sum(value != 0 for value in row) == 1:
            for col in range(len(row)):
                row[col] = 0
    return result


def _same_color_row_close(grid: list[list[int]]) -> frozenset[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        selected = frozenset(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        )
        cells.update(_row_close(selected))
    return frozenset(cells)


def _rival(name: str, grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    checked = _grid(grid)
    selected = _settings(settings)
    markers = marker_positions(checked)
    horizontal = _row_close(markers)
    height, width = len(checked), len(checked[0])
    if name == "endpoints_only":
        cells = markers
    elif name == "columns_only":
        cells = _column_close(markers)
    elif name == "parallel_row_column":
        cells = horizontal | _column_close(markers)
    elif name == "columns_then_rows":
        cells = _row_close(_column_close(markers))
    elif name == "bounding_box":
        rows = [r for r, _ in markers]
        cols = [c for _, c in markers]
        cells = frozenset(
            (r, c)
            for r in range(min(rows), max(rows) + 1)
            for c in range(min(cols), max(cols) + 1)
        )
    elif name == "same_color_rows":
        cells = _same_color_row_close(checked)
        if selected["closure"] == "rows_then_columns":
            cells = _column_close(cells)
    elif name == "ignore_singletons":
        return transform(_remove_singleton_rows(checked), selected)
    elif name == "longest_row_only":
        spans = []
        for row in sorted({r for r, _ in markers}):
            cols = [c for r, c in markers if r == row]
            spans.append((max(cols) - min(cols), row, min(cols), max(cols)))
        _, row, left, right = max(spans)
        cells = frozenset((row, col) for col in range(left, right + 1))
        if selected["closure"] == "rows_then_columns":
            cells = _column_close(cells)
    else:
        raise KeyError(name)
    return _paint(height, width, cells)


RIVAL_NAMES = (
    "endpoints_only",
    "columns_only",
    "parallel_row_column",
    "columns_then_rows",
    "bounding_box",
    "same_color_rows",
    "ignore_singletons",
    "longest_row_only",
)


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    selected = _settings(episode.get("settings"))
    expected_program = program(selected)
    if episode.get("program_solution") != expected_program:
        raise ValueError("program_solution does not match fixed settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not DEMO_LIMITS[0] <= len(train) <= DEMO_LIMITS[1]:
        raise ValueError("train must contain 2..6 demonstrations")
    if type(test) is not list or len(test) != QUERY_COUNT:
        raise ValueError("test must contain exactly four queries")
    pairs = train + test
    normalized: list[dict[str, list[list[int]]]] = []
    for pair in pairs:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each pair needs input and output")
        normalized.append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    if len({digest(pair["input"]) for pair in normalized}) != len(normalized):
        raise ValueError("all demonstration and query inputs must be distinct")

    if execute is None:
        def apply(source: str, grid: list[list[int]]) -> list[list[int]]:
            setting = next((item for item in SETTINGS if program(item) == source), None)
            if setting is None:
                raise ValueError("unknown program")
            return transform(grid, setting)
    else:
        apply = execute

    train_norm = normalized[: len(train)]
    test_norm = normalized[len(train) :]
    declaration_records = []
    survivors: list[dict[str, str]] = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train_norm]
        disagreements = [
            index
            for index, (prediction, pair) in enumerate(zip(predictions, train_norm))
            if prediction != pair["output"]
        ]
        declaration_records.append({"settings": copy.deepcopy(setting), "disagreeing_demo_indices": disagreements})
        if not disagreements:
            survivors.append(copy.deepcopy(setting))
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify the selected setting: {survivors}")

    extra_refutations: dict[str, list[int]] = {}
    for name in RIVAL_NAMES:
        disagreements = [
            index
            for index, pair in enumerate(train_norm)
            if _rival(name, pair["input"], selected) != pair["output"]
        ]
        if not disagreements:
            raise ValueError(f"shortcut rival {name!r} survives all demonstrations")
        extra_refutations[name] = disagreements

    query_records = []
    for pair in test_norm:
        actual = apply(expected_program, pair["input"])
        if actual != pair["output"]:
            raise ValueError("query label disagrees with the fixed program")
        scene = profile(pair["input"])
        if not scene["sequentially_decisive"]:
            raise ValueError("query does not expose the sequential intermediate")
        query_records.append({
            "input_sha256": digest(pair["input"]),
            "output_sha256": digest(pair["output"]),
            "profile": scene,
        })
    return {
        "scope": "two declared closure settings plus eight finite shortcut rivals",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "declared_refutations": declaration_records,
        "extra_refutations": extra_refutations,
        "queries": query_records,
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", DEMO_LIMITS[0], DEMO_LIMITS[1])
    if type(queries) is not int or queries != QUERY_COUNT:
        raise ValueError("queries must be the exact integer 4")
    selected = _settings(settings)
    train = []
    for index in range(demos):
        grid = _scene(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    test = []
    for index in range(QUERY_COUNT):
        grid = _scene(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    episode: dict[str, Any] = {
        "schema": "arcpuzzles-89df-row-column-closure-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    _integer(query_index, "query_index", 0, QUERY_COUNT - 1)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERY_COUNT:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def execute_rule(program_text: str, grid: object, bridge=None) -> list[list[int]]:
    """Execute one exact program with a supplied or temporary protected bridge."""
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.racket_bridge import RacketBridge

    checked = _grid(grid)
    owned = bridge is None
    runner = RacketBridge(timeout=60) if owned else bridge
    try:
        identity = runner.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")
        wrapped = wrap_rule(program_text)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in checked) + ")"
        return _grid(runner.eval_text(f"({wrapped} {literal})"))
    finally:
        if owned:
            runner.close()
