"""Bounded demonstration-only shortcut audit for the marker-slice relay family.

Native qualification supplies protected-Racket intended labels.  This tool checks
explicit deterministic rival algorithms only against the visible demonstrations,
then reports any survivor that changes a retained query.  Its finite rival set is
adversarial evidence, not a universal uniqueness proof.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
TASK_ID = "78cc0b96bc87"
Grid = list[list[int]]
Solver = Callable[[Grid], Grid]


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_78cc0b96bc87_audit_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ImportError("prototype import escaped its task home")
    return module


PROTOTYPE = _load_prototype()


def _grid(value: Any) -> Grid:
    if (
        type(value) is not list
        or not value
        or type(value[0]) is not list
        or not value[0]
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("expected rectangular exact-integer ARC grid")
    return copy.deepcopy(value)


def _checkerboard_variant(grid: Grid, mode: str) -> Grid:
    facts = PROTOTYPE.analyze_input(grid)
    stage = PROTOTYPE.checkerboard_only(grid)
    frame = facts["frame"]
    left_color, right_color = facts["left_color"], facts["right_color"]
    if mode == "swapped":
        even, odd = right_color, left_color
    elif mode == "solid_left":
        even = odd = left_color
    elif mode == "solid_right":
        even = odd = right_color
    elif mode == "numeric_order":
        even, odd = sorted((left_color, right_color))
    else:
        raise ValueError(mode)
    output = copy.deepcopy(stage)
    for row in range(frame["top"] + 1, frame["bottom"]):
        for column in range(frame["left"] + 1, frame["right"]):
            parity = (row - frame["top"] - 1 + column - frame["left"] - 1) % 2
            output[row][column] = even if parity == 0 else odd
    return output


def preserve_external_cues(grid: Grid) -> Grid:
    facts = PROTOTYPE.analyze_input(grid)
    frame = facts["frame"]
    output = PROTOTYPE.checkerboard_only(grid)
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            inside = frame["top"] <= row <= frame["bottom"] and frame["left"] <= column <= frame["right"]
            if not inside and value != 0:
                output[row][column] = value
    return output


def _relay_with_values(grid: Grid, value_mode: str, orientation: str = "both") -> Grid:
    facts = PROTOTYPE.analyze_input(grid)
    stage = PROTOTYPE.checkerboard_only(grid)
    output = copy.deepcopy(stage)
    for lane in facts["relay_lanes"]:
        horizontal = lane["side"] in ("left", "right")
        if orientation == "horizontal" and not horizontal:
            continue
        if orientation == "vertical" and horizontal:
            continue
        stage_values = [stage[row][column] for row, column in lane["source"]]
        if value_mode == "stage":
            values = stage_values
        elif value_mode == "raw":
            values = [grid[row][column] for row, column in lane["source"]]
        elif value_mode == "reverse":
            values = list(reversed(stage_values))
        elif value_mode == "shift_one":
            values = stage_values[1:] + stage_values[:1]
        elif value_mode == "left":
            values = [facts["left_color"]] * len(stage_values)
        elif value_mode == "right":
            values = [facts["right_color"]] * len(stage_values)
        elif value_mode == "marker":
            values = [8] * len(stage_values)
        else:
            raise ValueError(value_mode)
        for (row, column), value in zip(lane["target"], values):
            output[row][column] = value
    return output


def raw_slice_relay(grid: Grid) -> Grid:
    return _relay_with_values(grid, "raw")


def reversed_slice_relay(grid: Grid) -> Grid:
    return _relay_with_values(grid, "reverse")


def shifted_slice_relay(grid: Grid) -> Grid:
    return _relay_with_values(grid, "shift_one")


def left_color_lane(grid: Grid) -> Grid:
    return _relay_with_values(grid, "left")


def right_color_lane(grid: Grid) -> Grid:
    return _relay_with_values(grid, "right")


def marker_color_lane(grid: Grid) -> Grid:
    return _relay_with_values(grid, "marker")


def horizontal_only_relay(grid: Grid) -> Grid:
    return _relay_with_values(grid, "stage", "horizontal")


def vertical_only_relay(grid: Grid) -> Grid:
    return _relay_with_values(grid, "stage", "vertical")


def relay_to_canvas_boundary(grid: Grid) -> Grid:
    facts = PROTOTYPE.analyze_input(grid)
    stage = PROTOTYPE.checkerboard_only(grid)
    output = PROTOTYPE.solve_python(grid, {"relay_rule": "marker_slice_relay"})
    for lane in facts["relay_lanes"]:
        values = [stage[row][column] for row, column in lane["source"]]
        row, column = lane["marker"]
        if lane["side"] == "left":
            extra = [(row, c) for c in range(0, column)]
        elif lane["side"] == "right":
            extra = [(row, c) for c in range(column + 1, facts["width"])]
        elif lane["side"] == "up":
            extra = [(r, column) for r in range(0, row)]
        else:
            extra = [(r, column) for r in range(row + 1, facts["height"])]
        for index, (erow, ecolumn) in enumerate(extra):
            output[erow][ecolumn] = values[index % len(values)]
    return output


def _rivals(settings: dict[str, Any]) -> dict[str, Solver]:
    rule = PROTOTYPE.normalize_settings(settings)["relay_rule"]
    if rule == "checkerboard_only":
        return {
            "other_setting_marker_slice_relay": lambda grid: PROTOTYPE.solve_python(
                grid, {"relay_rule": "marker_slice_relay"}
            ),
            "checkerboard_swapped_phase": lambda grid: _checkerboard_variant(grid, "swapped"),
            "solid_left_seed_color": lambda grid: _checkerboard_variant(grid, "solid_left"),
            "solid_right_seed_color": lambda grid: _checkerboard_variant(grid, "solid_right"),
            "numeric_color_order": lambda grid: _checkerboard_variant(grid, "numeric_order"),
            "preserve_external_markers": preserve_external_cues,
        }
    return {
        "other_setting_checkerboard_only": PROTOTYPE.checkerboard_only,
        "copy_raw_sparse_slice": raw_slice_relay,
        "reverse_completed_slice": reversed_slice_relay,
        "shift_completed_slice_one_cell": shifted_slice_relay,
        "fill_lane_left_seed_color": left_color_lane,
        "fill_lane_right_seed_color": right_color_lane,
        "fill_lane_marker_color": marker_color_lane,
        "horizontal_markers_only": horizontal_only_relay,
        "vertical_markers_only": vertical_only_relay,
        "continue_relay_to_canvas_boundary": relay_to_canvas_boundary,
    }


def _difference(expected: Grid, actual: Grid) -> dict[str, Any] | None:
    if expected == actual:
        return None
    if len(expected) != len(actual) or len(expected[0]) != len(actual[0]):
        return {
            "expected_shape": [len(expected), len(expected[0])],
            "rival_shape": [len(actual), len(actual[0])],
        }
    changed = 0
    first = None
    for row in range(len(expected)):
        for column in range(len(expected[0])):
            if expected[row][column] != actual[row][column]:
                changed += 1
                if first is None:
                    first = {
                        "row": row,
                        "column": column,
                        "expected": expected[row][column],
                        "rival": actual[row][column],
                    }
    assert first is not None
    return {**first, "changed_cells": changed}


def audit_episode(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    for split in ("train", "test"):
        if type(episode.get(split)) is not list or not episode[split]:
            raise ValueError(f"episode requires a nonempty {split} list")
        for pair in episode[split]:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair needs input and output")
            _grid(pair["input"])
            _grid(pair["output"])

    rows = []
    evaluations = 0
    for name, solver in _rivals(settings).items():
        demo_differences = []
        query_differences = []
        for index, pair in enumerate(episode["train"]):
            actual = _grid(solver(pair["input"]))
            evaluations += 1
            difference = _difference(pair["output"], actual)
            if difference is not None:
                demo_differences.append({"index": index, **difference})
        if not demo_differences:
            for index, pair in enumerate(episode["test"]):
                actual = _grid(solver(pair["input"]))
                evaluations += 1
                difference = _difference(pair["output"], actual)
                if difference is not None:
                    query_differences.append({"index": index, **difference})
        rows.append({
            "name": name,
            "demo_survives": not demo_differences,
            "demo_differences": demo_differences,
            "query_differences": query_differences,
            "ambiguous": not demo_differences and bool(query_differences),
            "equivalent_on_retained_pairs": not demo_differences and not query_differences,
        })
    return {
        "settings": copy.deepcopy(settings),
        "rival_count": len(rows),
        "rival_evaluations": evaluations,
        "rivals": rows,
        "demo_survivors": [row["name"] for row in rows if row["demo_survives"]],
        "ambiguous_rivals": [row["name"] for row in rows if row["ambiguous"]],
        "equivalent_survivors": [row["name"] for row in rows if row["equivalent_on_retained_pairs"]],
    }


def audit_qualification(qualification: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    if (
        qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
    ):
        raise ValueError("expected a qualified native receipt for this task")
    racket = execution.get("racket", {})
    if racket.get("backend") != "racket" or racket.get("protected") is not True:
        raise ValueError("self-audit requires protected-Racket qualification labels")
    episodes = execution.get("episodes")
    if type(episodes) is not list or not episodes:
        raise ValueError("qualification execution has no episodes")
    rows = [audit_episode(episode, episode["settings"]) for episode in episodes]
    survivors = [
        {"episode_index": index, "settings": row["settings"], "rivals": row["demo_survivors"]}
        for index, row in enumerate(rows)
        if row["demo_survivors"]
    ]
    return {
        "schema": "arcpuzzles-78cc0b96bc87-finite-self-audit-v1",
        "task_id": TASK_ID,
        "status": "pass" if not survivors else "finite_rival_survivors",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "scope": "native qualification episodes; six canonical and ten relay rivals",
        "limits": "finite rival elimination does not prove universal program uniqueness",
        "episodes": rows,
        "demo_survivor_findings": survivors,
        "counts": {
            "episodes": len(rows),
            "rivals": sum(row["rival_count"] for row in rows),
            "rival_evaluations": sum(row["rival_evaluations"] for row in rows),
            "qualification_racket_evaluations": execution.get("racket_evaluations"),
        },
    }


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--execution", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    qualification = json.loads(args.qualification.read_text())
    execution_path = args.execution or args.qualification.with_name("execution.json")
    execution = json.loads(execution_path.read_text())
    report = audit_qualification(qualification, execution)
    _write(args.out, report)
    print(json.dumps({"status": report["status"], **report["counts"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
