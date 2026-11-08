from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

REPO = Path.cwd().resolve()
WORK = REPO.parent
TASK_ID = "0be8ff9b4144"
HOME = REPO / "generators" / TASK_ID / "workspace" / "parametric"
QUALIFICATION = WORK / "checks" / TASK_ID / "qualification" / "qualification.json"
OUT = WORK / "checks" / TASK_ID / "sequential_dependency.json"

spec = importlib.util.spec_from_file_location("causal_witness_prototype", HOME / "prototype.py")
if spec is None or spec.loader is None:
    raise ImportError("prototype")
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)

episode = prototype.generate_episode(
    0, intersection_policy="same_parity", demos=3, queries=4
)
grid = episode["test"][1]["input"]  # 18x25; four active rows and six active columns.
program = (HOME / "rules" / "same_parity.rkt").read_text()
needle = "(active-cols (filter (lambda (c) (= (at g 0 c) 2)) (range 1 (cols g))))"
replacement = "(active-cols (reverse (filter (lambda (c) (= (at g 0 c) 2)) (range 1 (cols g)))))"
if program.count(needle) != 1:
    raise RuntimeError("qualified program structure changed")
counterfactual = program.replace(needle, replacement)

runtime = REPO / "shared" / "runtime"
with _local_imports(runtime, runtime):
    apply, identity, bridge = _real_evaluator(runtime)
    try:
        output = _grid(apply(program, grid))
        counterfactual_output = _grid(apply(counterfactual, grid))
    finally:
        bridge.close()

expected = _grid(episode["test"][1]["output"])
if output != expected:
    raise AssertionError("qualified same_parity program disagrees with generated label")
if output == counterfactual_output:
    raise AssertionError("wrong-intermediate counterfactual did not change final output")

active_rows, active_cols = prototype.active_axes(grid)
differences = sum(
    a != b
    for row_a, row_b in zip(output, counterfactual_output)
    for a, b in zip(row_a, row_b)
)
qualification = json.loads(QUALIFICATION.read_text())

step_a = "Decode exact color-3 row headers and exact color-2 column headers into ordered active-axis lists."
intermediate = "The coordinate-ordered active row and active column lists, whose list indices define row_rank and col_rank."
step_b = "Paint an active intersection exactly when the parity of row_rank + col_rank matches the episode policy."
why = (
    "Step B cannot choose cells from coordinates alone: it needs Step A's ordered lists to assign ranks. "
    "Reversing the six-column intermediate while keeping the same input and parity rule flips every selected rank class and changes the protected-Racket output."
)

witness = {
    "schema": "arcpuzzles-sequential-dependency-witness-v1",
    "source_binding": qualification["source_binding"],
    "racket": {"backend": "racket", "protected": True},
    "step_a": step_a,
    "intermediate": intermediate,
    "step_b": step_b,
    "why_b_depends_on_a": why,
    "cases": [
        {
            "input": grid,
            "settings": {"intersection_policy": "same_parity"},
            "intermediate_value": {
                "active_rows": active_rows,
                "active_cols": active_cols,
                "row_rank_by_coordinate": {str(value): rank for rank, value in enumerate(active_rows)},
                "col_rank_by_coordinate": {str(value): rank for rank, value in enumerate(active_cols)},
                "counterfactual_active_cols": list(reversed(active_cols)),
            },
            "program": program,
            "output": output,
            "counterfactual_program": counterfactual,
            "counterfactual_output": counterfactual_output,
            "ablation": "wrong_intermediate",
        }
    ],
}
OUT.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "status": "passed",
    "witness": str(OUT),
    "racket": identity,
    "active_rows": active_rows,
    "active_cols": active_cols,
    "changed_cells": differences,
}, indent=2, sort_keys=True))
