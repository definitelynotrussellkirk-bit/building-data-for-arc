"""Matched-input parametric family for ff973026bfbe.

The canonical setting paints every blue-marked row × top-row red-marker column.
The alternate first measures the neutral signal object's cell count, then uses
that one-based rank to choose one top-row red marker before painting its column.
"""
from __future__ import annotations

from copy import deepcopy
from collections import namedtuple
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


TASK_ID = "ff973026bfbe"
CANONICAL = "all_top_markers"
ALTERNATE = "signal_ranked_marker"
SETTINGS = (CANONICAL, ALTERNATE)
MAX_SEED = 2**63 - 1

_CANONICAL_PATH = Path(__file__).with_name("canonical.rkt")

ALTERNATE_PROGRAM = """(rule!
  (let* ((mark-rows (map fst (find-color g 1)))
         (mark-cols (map snd (filter (lambda (p) (= (fst p) 0)) (find-color g 2))))
         (signal-color
           (find (lambda (c) (and (not (= c 1)) (not (= c 2))))
                 (grid-colors g 0)))
         (signal-size (count-color g signal-color))
         (selected-col (nth mark-cols (- signal-size 1))))
    (reduce (lambda (out r) (set-cell out r selected-col 3))
            g mark-rows)))"""


SceneSpec = namedtuple(
    "SceneSpec",
    "height width signal_size active_rows top_markers red_decoys stress",
    defaults=(False,),
)


DEMO_SPECS = (
    SceneSpec(9, 12, 2, 4, 6, 1),
    SceneSpec(10, 14, 5, 3, 7, 2),
    SceneSpec(12, 16, 3, 5, 7, 1),
    SceneSpec(14, 18, 6, 4, 8, 3),
    SceneSpec(16, 20, 4, 6, 8, 2),
    SceneSpec(18, 22, 2, 7, 9, 2),
)
QUERY_SPECS = (
    SceneSpec(14, 18, 3, 6, 8, 2),
    SceneSpec(19, 23, 6, 8, 10, 3),
    SceneSpec(24, 27, 4, 10, 12, 4),
    SceneSpec(30, 30, 5, 12, 14, 5, True),
)

_BASE_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
}


def validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"column_policy"}:
        raise ValueError("settings must contain exactly column_policy")
    selected = settings["column_policy"]
    if not isinstance(selected, str) or selected not in SETTINGS:
        raise ValueError(f"column_policy must be one of {SETTINGS}")
    return selected


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def program_for(selected: str) -> str:
    if selected == CANONICAL:
        return _CANONICAL_PATH.read_bytes().decode("utf-8")
    if selected == ALTERNATE:
        return ALTERNATE_PROGRAM
    raise ValueError(f"unknown setting: {selected!r}")


def _derived_rng(seed: int, role: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:parametric-v1:{seed}:{role}:{index}".encode()
    digest = hashlib.sha256(payload).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normalize(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _transform_shape(size: int, code: int) -> list[tuple[int, int]]:
    cells = list(_BASE_SHAPES[size])
    if code >= 4:
        cells = [(r, -c) for r, c in cells]
    for _ in range(code % 4):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _signal_cells(spec: SceneSpec, rng: random.Random) -> list[tuple[int, int]]:
    shape = _transform_shape(spec.signal_size, rng.randrange(8))
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    if spec.stress:
        anchor_r = spec.height - shape_h
        anchor_c = (spec.width - shape_w) // 2
    else:
        row_low = max(2, spec.height // 2)
        row_high = spec.height - shape_h
        if row_low > row_high:
            row_low = 1
        anchor_r = rng.randint(row_low, row_high)
        col_low = 1
        col_high = max(col_low, spec.width - shape_w - 1)
        anchor_c = rng.randint(col_low, col_high)
    return [(anchor_r + r, anchor_c + c) for r, c in shape]


def _build_scene(seed: int, role: str, index: int, spec: SceneSpec) -> list[list[int]]:
    rng = _derived_rng(seed, role, index)
    grid = [[0 for _ in range(spec.width)] for _ in range(spec.height)]
    signal_color = 4 + rng.randrange(6)
    signal_cells = _signal_cells(spec, rng)
    signal_rows = {r for r, _ in signal_cells}
    for r, c in signal_cells:
        grid[r][c] = signal_color

    row_candidates = [r for r in range(1, spec.height) if r not in signal_rows]
    if len(row_candidates) < spec.active_rows:
        raise ValueError("scene does not have enough rows outside the signal")
    rng.shuffle(row_candidates)
    active_rows = sorted(row_candidates[: spec.active_rows])

    # Keep active columns interior so blue boundary markers remain visible and
    # the 30x30 query can deliberately cover left/right with row markers.
    col_candidates = list(range(1, spec.width - 1))
    if len(col_candidates) < spec.top_markers:
        raise ValueError("scene does not have enough interior top columns")
    rng.shuffle(col_candidates)
    active_cols = sorted(col_candidates[: spec.top_markers])
    for col in active_cols:
        grid[0][col] = 2

    free_marker_cols = [c for c in range(1, spec.width - 1) if c not in active_cols]
    for position, row in enumerate(active_rows):
        if position == 0:
            col = 0
        elif spec.stress and position == 1:
            col = spec.width - 1
        else:
            col = rng.choice(free_marker_cols)
        grid[row][col] = 1

    inactive_rows = [
        r
        for r in range(1, spec.height)
        if r not in signal_rows and r not in set(active_rows)
    ]
    decoy_cols = [c for c in range(spec.width) if c not in set(active_cols)]
    rng.shuffle(inactive_rows)
    rng.shuffle(decoy_cols)
    if len(inactive_rows) < spec.red_decoys or len(decoy_cols) < spec.red_decoys:
        raise ValueError("scene does not have enough red-decoy positions")
    for row, col in zip(inactive_rows[: spec.red_decoys], decoy_cols[: spec.red_decoys], strict=True):
        if grid[row][col] != 0:
            alternatives = [c for c in decoy_cols if grid[row][c] == 0]
            if not alternatives:
                raise ValueError("no collision-free red-decoy column")
            col = alternatives[0]
        grid[row][col] = 2

    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("constructed invalid scene: " + "; ".join(analysis["errors"]))
    expected = {
        "height": spec.height,
        "width": spec.width,
        "signal_size": spec.signal_size,
        "active_row_count": spec.active_rows,
        "top_marker_count": spec.top_markers,
        "red_decoy_count": spec.red_decoys,
    }
    for key, value in expected.items():
        if analysis[key] != value:
            raise ValueError(f"constructed {key}={analysis[key]!r}, expected {value!r}")
    return grid


def _four_connected(cells: list[tuple[int, int]]) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    stack = [next(iter(remaining))]
    seen: set[tuple[int, int]] = set()
    while stack:
        cell = stack.pop()
        if cell in seen:
            continue
        seen.add(cell)
        r, c = cell
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining and neighbor not in seen:
                stack.append(neighbor)
    return len(seen) == len(remaining)


def analyze_input(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be non-empty and rectangular"]}
    height = len(grid)
    if height > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30")
    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"cells must be integer colors 0..9: {bad_cells[:3]}")
        return {"errors": errors, "height": height, "width": width}

    colors = {value for row in grid for value in row}
    signal_colors = sorted(colors - {0, 1, 2})
    if len(signal_colors) != 1 or signal_colors[0] == 3:
        errors.append(f"expected exactly one signal color from 4..9, found {signal_colors}")
        signal_color = None
    else:
        signal_color = signal_colors[0]

    blue_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if any(r == 0 for r, _ in blue_cells):
        errors.append("blue row markers must not occur in row 0")
    blue_by_row: dict[int, list[int]] = {}
    for r, c in blue_cells:
        blue_by_row.setdefault(r, []).append(c)
    if len(blue_cells) != len(blue_by_row) or len(blue_by_row) < 2:
        errors.append("expected exactly one blue marker in each of at least two active rows")
    active_rows = sorted(blue_by_row)

    top_cols = [c for c, value in enumerate(grid[0]) if value == 2]
    if len(top_cols) < 4:
        errors.append("expected at least four top-row red markers")
    if any(value not in (0, 2) for value in grid[0]):
        errors.append("row 0 may contain only background and red markers")

    red_decoys = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2 and r > 0
    ]
    if not red_decoys:
        errors.append("expected at least one off-top red decoy")
    if any(c in set(top_cols) for _, c in red_decoys):
        errors.append("off-top red decoys must use columns absent from the top row")
    if any(r in set(active_rows) for r, _ in red_decoys):
        errors.append("off-top red decoys must lie on inactive rows")

    signal_cells = (
        [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == signal_color]
        if signal_color is not None
        else []
    )
    signal_size = len(signal_cells)
    if signal_size not in _BASE_SHAPES:
        errors.append(f"signal size must be one of {sorted(_BASE_SHAPES)}, found {signal_size}")
    if signal_cells and not _four_connected(signal_cells):
        errors.append("signal cells must form one four-connected object")
    if any(r == 0 or r in set(active_rows) for r, _ in signal_cells):
        errors.append("signal object must lie on inactive non-top rows")
    if top_cols and signal_size and len(top_cols) < signal_size + 2:
        errors.append("top-row marker count must exceed signal rank by at least two")

    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    boundary_sides: set[str] = set()
    for r, c in nonzero:
        if r == 0:
            boundary_sides.add("top")
        if r == height - 1:
            boundary_sides.add("bottom")
        if c == 0:
            boundary_sides.add("left")
        if c == width - 1:
            boundary_sides.add("right")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "signal_color": signal_color,
        "signal_size": signal_size,
        "signal_cells": signal_cells,
        "active_rows": active_rows,
        "active_row_count": len(active_rows),
        "top_cols": top_cols,
        "top_marker_count": len(top_cols),
        "red_decoys": red_decoys,
        "red_decoy_count": len(red_decoys),
        "occupied_cells": len(nonzero),
        "canonical_painted_cells": len(active_rows) * len(top_cols),
        "boundary_sides": sorted(boundary_sides),
    }


def _paint(grid: list[list[int]], rows: list[int], cols: list[int]) -> list[list[int]]:
    output = deepcopy(grid)
    for row in rows:
        for col in cols:
            output[row][col] = 3
    return output


def solve(grid: list[list[int]], selected: str) -> list[list[int]]:
    if selected not in SETTINGS:
        raise ValueError(f"unknown setting: {selected!r}")
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid family input: " + "; ".join(analysis["errors"]))
    rows = analysis["active_rows"]
    cols = analysis["top_cols"]
    if selected == CANONICAL:
        return _paint(grid, rows, cols)
    selected_col = cols[analysis["signal_size"] - 1]
    return _paint(grid, rows, [selected_col])


def _solve_first(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    return _paint(grid, a["active_rows"], [a["top_cols"][0]])


def _solve_last(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    return _paint(grid, a["active_rows"], [a["top_cols"][-1]])


def _solve_middle(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    return _paint(grid, a["active_rows"], [a["top_cols"][(len(a["top_cols"]) - 1) // 2]])


def _solve_rank_from_right(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    return _paint(grid, a["active_rows"], [a["top_cols"][-a["signal_size"]]])


def _solve_rank_plus_one(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    return _paint(grid, a["active_rows"], [a["top_cols"][a["signal_size"]]])


def _solve_row_count_rank(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    index = min(len(a["active_rows"]), len(a["top_cols"])) - 1
    return _paint(grid, a["active_rows"], [a["top_cols"][index]])


def _solve_fixed(grid: list[list[int]], rank: int) -> list[list[int]]:
    a = analyze_input(grid)
    index = min(rank, len(a["top_cols"])) - 1
    return _paint(grid, a["active_rows"], [a["top_cols"][index]])


def _solve_all_red_columns(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    cols = sorted({c for row in grid for c, value in enumerate(row) if value == 2})
    return _paint(grid, a["active_rows"], cols)


def _solve_left_border_rows(grid: list[list[int]]) -> list[list[int]]:
    a = analyze_input(grid)
    rows = [r for r in range(1, len(grid)) if grid[r][0] == 1]
    return _paint(grid, rows, a["top_cols"])


DECLARED_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    CANONICAL: lambda grid: solve(grid, CANONICAL),
    ALTERNATE: lambda grid: solve(grid, ALTERNATE),
}
SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_top_marker": _solve_first,
    "last_top_marker": _solve_last,
    "middle_top_marker": _solve_middle,
    "signal_rank_from_right": _solve_rank_from_right,
    "signal_rank_plus_one": _solve_rank_plus_one,
    "blue_row_count_rank": _solve_row_count_rank,
    "fixed_rank_2": lambda grid: _solve_fixed(grid, 2),
    "fixed_rank_5": lambda grid: _solve_fixed(grid, 5),
    "all_red_columns": _solve_all_red_columns,
    "left_border_rows_only": _solve_left_border_rows,
}


def audit_episode(episode: dict[str, Any], selected: str) -> dict[str, Any]:
    if selected not in SETTINGS:
        raise ValueError(f"unknown setting: {selected!r}")
    train = episode["train"]
    test = episode["test"]
    surviving_rules = [
        name
        for name, rule in DECLARED_RULES.items()
        if all(rule(pair["input"]) == pair["output"] for pair in train)
    ]
    other = ALTERNATE if selected == CANONICAL else CANONICAL
    query_disagreements = sum(
        solve(pair["input"], other) != pair["output"] for pair in test
    )
    shortcut_survivors: list[str] = []
    harmful: list[dict[str, Any]] = []
    for name, rule in SHORTCUTS.items():
        if all(rule(pair["input"]) == pair["output"] for pair in train):
            shortcut_survivors.append(name)
            differing = [
                index
                for index, pair in enumerate(test)
                if rule(pair["input"]) != pair["output"]
            ]
            if differing:
                harmful.append({"name": name, "query_indices": differing})
    return {
        "selected": selected,
        "surviving_declared_rules": surviving_rules,
        "query_disagreements_against_other_setting": query_disagreements,
        "shortcut_survivors": shortcut_survivors,
        "harmful_shortcut_survivors": harmful,
    }


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid family input: " + "; ".join(analysis["errors"]))
    return {key: deepcopy(value) for key, value in analysis.items() if key not in {"errors", "signal_cells", "active_rows", "top_cols", "red_decoys"}}


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _strict_int("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def build_claimed_episode(seed: int, selected: str, demos: int, queries: int) -> dict[str, Any]:
    _strict_int("seed", seed, 0, MAX_SEED)
    _strict_int("demos", demos, 2, 6)
    _strict_int("queries", queries, 1, 4)
    if selected not in SETTINGS:
        raise ValueError(f"unknown setting: {selected!r}")
    train = []
    test = []
    for index, spec in enumerate(DEMO_SPECS[:demos]):
        grid = _build_scene(seed, "demo", index, spec)
        train.append({"input": grid, "output": solve(grid, selected)})
    for index, spec in enumerate(QUERY_SPECS[:queries]):
        grid = _build_scene(seed, "query", index, spec)
        test.append({"input": grid, "output": solve(grid, selected)})
    signatures = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in train + test
    ]
    if len(signatures) != len(set(signatures)):
        raise ValueError("episode inputs must be distinct")
    episode = {
        "train": train,
        "test": test,
        "program_solution": program_for(selected),
    }
    audit = audit_episode(episode, selected)
    if audit["surviving_declared_rules"] != [selected]:
        raise ValueError(f"demonstrations do not identify setting: {audit}")
    if audit["harmful_shortcut_survivors"]:
        raise ValueError(f"harmful shortcut survives demonstrations: {audit}")
    return deepcopy(episode)


def forced_rank_program(rank: int) -> str:
    _strict_int("rank", rank, 1, 16)
    return f"""(rule!
  (let* ((mark-rows (map fst (find-color g 1)))
         (mark-cols (map snd (filter (lambda (p) (= (fst p) 0)) (find-color g 2))))
         (selected-col (nth mark-cols {rank - 1})))
    (reduce (lambda (out r) (set-cell out r selected-col 3))
            g mark-rows)))"""


def causal_witness(seed: int) -> dict[str, Any]:
    _strict_int("seed", seed, 0, MAX_SEED)
    grid = _build_scene(seed, "query", 0, QUERY_SPECS[0])
    analysis = analyze_input(grid)
    wrong_signal_size = analysis["signal_size"] + 1
    output = solve(grid, ALTERNATE)
    counterfactual_output = _paint(
        grid,
        analysis["active_rows"],
        [analysis["top_cols"][wrong_signal_size - 1]],
    )
    differing = sum(
        left != right
        for row_left, row_right in zip(output, counterfactual_output, strict=True)
        for left, right in zip(row_left, row_right, strict=True)
    )
    return {
        "input": deepcopy(grid),
        "settings": {"column_policy": ALTERNATE},
        "signal_size": analysis["signal_size"],
        "wrong_signal_size": wrong_signal_size,
        "selected_col": analysis["top_cols"][analysis["signal_size"] - 1],
        "wrong_selected_col": analysis["top_cols"][wrong_signal_size - 1],
        "program": ALTERNATE_PROGRAM,
        "counterfactual_program": forced_rank_program(wrong_signal_size),
        "output": output,
        "counterfactual_output": counterfactual_output,
        "differing_cells": differing,
        "ablation": "wrong_intermediate",
    }
