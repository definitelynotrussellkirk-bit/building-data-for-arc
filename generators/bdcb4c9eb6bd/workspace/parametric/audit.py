"""Bounded visible-lesson shortcut audit for the projection/bridge family.

The CLI consumes native qualification evidence, whose intended labels were
executed in protected Racket.  It then checks explicit, deterministic rival
algorithms against demonstrations only and reports any rival that survives the
visible lesson but changes a retained query.  This is finite adversarial
coverage, not a proof of universal rule uniqueness.
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
TASK_ID = "bdcb4c9eb6bd"


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_bdcb4c9eb6bd_audit_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ImportError("prototype import escaped its task home")
    return module


PROTOTYPE = _load_prototype()
Grid = list[list[int]]
Solver = Callable[[Grid], Grid]


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
        raise ValueError("expected a rectangular exact-integer ARC grid")
    return copy.deepcopy(value)


def _partial_stage(
    grid: Grid,
    *,
    selected: set[int] | None = None,
    fill: bool = True,
    project: bool = True,
    paint: int = 2,
) -> Grid:
    """Execute a deliberately incomplete/wrong Stage A competitor."""
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    background = PROTOTYPE.background_color(grid)
    output = copy.deepcopy(grid)
    rectangles = PROTOTYPE._rectangles(grid)
    for index, facts in enumerate(rectangles):
        if selected is not None and index not in selected:
            continue
        top, bottom = facts["top"], facts["bottom"]
        left, right = facts["left"], facts["right"]
        if fill:
            for row in range(top + 1, bottom):
                for column in range(left + 1, right):
                    if output[row][column] == background:
                        output[row][column] = paint
        if not project:
            continue
        gap_row, gap_column = facts["gap"]
        if facts["side"] == "left":
            points = ((gap_row, column) for column in range(0, left + 1))
        elif facts["side"] == "right":
            points = ((gap_row, column) for column in range(right, width))
        elif facts["side"] == "up":
            points = ((row, gap_column) for row in range(0, top + 1))
        else:
            points = ((row, gap_column) for row in range(bottom, height))
        for row, column in points:
            if output[row][column] == background:
                output[row][column] = paint
    return output


def _bridge_variant(
    grid: Grid,
    *,
    rows: bool,
    columns: bool,
    any_contact: bool = False,
    paint: int = 3,
    overwrite: bool = False,
    require_cross: bool = False,
) -> Grid:
    stage = PROTOTYPE.project_only(grid)
    background = PROTOTYPE.background_color(grid)
    height, width = len(stage), len(stage[0])
    paired_rows = [
        row
        for row in range(height)
        if (stage[row][0] == 2 or stage[row][width - 1] == 2)
        if any_contact or stage[row][0] == stage[row][width - 1] == 2
    ]
    paired_columns = [
        column
        for column in range(width)
        if (stage[0][column] == 2 or stage[height - 1][column] == 2)
        if any_contact or stage[0][column] == stage[height - 1][column] == 2
    ]
    if require_cross and (not paired_rows or not paired_columns):
        return stage
    output = copy.deepcopy(stage)
    if rows:
        for row in paired_rows:
            for column in range(width):
                if overwrite or output[row][column] == background:
                    output[row][column] = paint
    if columns:
        for column in paired_columns:
            for row in range(height):
                if overwrite or output[row][column] == background:
                    output[row][column] = paint
    return output


def bridge_horizontal_only(grid: Grid) -> Grid:
    return _bridge_variant(grid, rows=True, columns=False)


def bridge_vertical_only(grid: Grid) -> Grid:
    return _bridge_variant(grid, rows=False, columns=True)


def bridge_any_border_contact(grid: Grid) -> Grid:
    return _bridge_variant(grid, rows=True, columns=True, any_contact=True)


def bridge_color2(grid: Grid) -> Grid:
    return _bridge_variant(grid, rows=True, columns=True, paint=2)


def bridge_overwrite_axis(grid: Grid) -> Grid:
    return _bridge_variant(grid, rows=True, columns=True, overwrite=True)


def bridge_cross_only(grid: Grid) -> Grid:
    return _bridge_variant(grid, rows=True, columns=True, require_cross=True)


def _rivals(settings: dict[str, Any]) -> dict[str, Solver]:
    rule = PROTOTYPE.normalize_settings(settings)["finish_rule"]
    if rule == "project_only":
        return {
            "other_setting_project_then_bridge": lambda grid: PROTOTYPE.solve_python(
                grid, {"finish_rule": "project_then_bridge"}
            ),
            "fill_without_projection": lambda grid: _partial_stage(grid, project=False),
            "projection_without_fill": lambda grid: _partial_stage(grid, fill=False),
            "first_rectangle_only": lambda grid: _partial_stage(grid, selected={0}),
            "last_rectangle_only": lambda grid: _partial_stage(
                grid, selected={len(PROTOTYPE._rectangles(grid)) - 1}
            ),
            "stage_a_uses_color3": lambda grid: _partial_stage(grid, paint=3),
        }
    return {
        "other_setting_project_only": PROTOTYPE.project_only,
        "bridge_horizontal_only": bridge_horizontal_only,
        "bridge_vertical_only": bridge_vertical_only,
        "bridge_any_border_contact": bridge_any_border_contact,
        "bridge_color2": bridge_color2,
        "bridge_overwrites_axis": bridge_overwrite_axis,
        "bridge_requires_cross": bridge_cross_only,
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
        rows.append(
            {
                "name": name,
                "demo_survives": not demo_differences,
                "demo_differences": demo_differences,
                "query_differences": query_differences,
                "ambiguous": not demo_differences and bool(query_differences),
                "equivalent_on_retained_pairs": not demo_differences and not query_differences,
            }
        )
    return {
        "settings": copy.deepcopy(settings),
        "rival_count": len(rows),
        "rival_evaluations": evaluations,
        "rivals": rows,
        "demo_survivors": [row["name"] for row in rows if row["demo_survives"]],
        "ambiguous_rivals": [row["name"] for row in rows if row["ambiguous"]],
        "equivalent_survivors": [
            row["name"] for row in rows if row["equivalent_on_retained_pairs"]
        ],
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
        "schema": "arcpuzzles-bdcb4c9eb6bd-finite-self-audit-v1",
        "task_id": TASK_ID,
        "status": "pass" if not survivors else "finite_rival_survivors",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "scope": "native qualification episodes; six or seven declared plausible rivals per setting",
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
