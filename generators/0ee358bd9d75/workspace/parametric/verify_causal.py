"""Replay a source-bound, same-shape divider-ablation witness through Racket.

Run after native qualification. The helper checks the qualification's source
binding and execution hash, then changes only an input-derived divider binding.
It never grants acceptance or modifies qualification evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_promotion import _check_execution, _ready
from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import find_root


TASK_ID = "0ee358bd9d75"
CAUSAL_INPUT = [
    [1, 2, 0, 5, 5, 5, 4, 0],
    [1, 0, 0, 5, 4, 0, 5, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 5, 0, 7, 7, 8, 7, 7],
    [5, 6, 0, 7, 0, 7, 0, 7],
    [0, 5, 0, 7, 7, 0, 7, 8],
    [5, 0, 0, 7, 8, 7, 7, 0],
    [5, 5, 0, 0, 7, 7, 7, 7],
]
DEPENDENCY = {
    "step_a": "Detect full-zero separator rows/columns and derive ordered section bounds.",
    "intermediate": "Input-dependent row/column spans defining each section's cell membership.",
    "step_b": "Count present nonzero colors inside each inferred section and select its episode-fixed frequency extreme.",
    "why_b_depends_on_a": "The section bounds determine which cells contribute to each histogram and where its answer belongs; wrong bounds can change selected colors even with the same output dimensions.",
}


def replace_binding(program, name, expression):
    """Replace this task's single parenthesized let binding, failing on drift."""
    marker = "(" + name + " "
    if program.count(marker) != 1:
        raise ValueError("Expected one canonical " + name + " binding")
    start = program.index(marker)
    depth = 0
    for end in range(start, len(program)):
        depth += (program[end] == "(") - (program[end] == ")")
        if depth == 0:
            return program[:start] + "(" + name + " " + expression + ")" + program[end + 1:]
    raise ValueError("Unbalanced canonical binding")


def _shape(grid):
    return [len(grid), len(grid[0])]


def _spans(length, dividers):
    bounds = [-1, *dividers, length]
    return [[lo + 1, hi] for lo, hi in zip(bounds, bounds[1:])]


def find_counterfactual(program, grid, settings, apply):
    """Find a finite wrong-bound witness; retain the full programs and labels."""
    grid = _grid(grid)
    height, width = _shape(grid)
    zero_rows = [r for r, row in enumerate(grid) if not any(row)]
    zero_cols = [c for c in range(width) if not any(row[c] for row in grid)]
    output = _grid(apply(program, grid))
    attempts = 0
    for name, original, length in (("zero-rows", zero_rows, height), ("zero-cols", zero_cols, width)):
        for index, divider in enumerate(original):
            # Closest wrong boundaries first; never change the section count.
            candidates = sorted(range(1, length - 1), key=lambda value: (abs(value - divider), value))
            for wrong in candidates:
                if wrong == divider:
                    continue
                replaced = list(original)
                replaced[index] = wrong
                if replaced != sorted(set(replaced)) or any(hi <= lo for lo, hi in _spans(length, replaced)):
                    continue
                expression = "(list " + " ".join(map(str, replaced)) + ")"
                counterfactual = replace_binding(program, name, expression)
                attempts += 1
                try:
                    changed = _grid(apply(counterfactual, grid))
                except (ValueError, RuntimeError):
                    # An empty wrong section is not causal evidence.
                    continue
                if _shape(changed) == _shape(output) and changed != output:
                    return {
                        "input": deepcopy(grid), "settings": deepcopy(settings),
                        "intermediate_value": {
                            "actual_zero_rows": zero_rows, "actual_zero_cols": zero_cols,
                            "row_spans_half_open": _spans(height, zero_rows),
                            "column_spans_half_open": _spans(width, zero_cols),
                            "replaced_binding": name, "counterfactual_dividers": replaced,
                        },
                        "program": program, "output": output,
                        "counterfactual_program": counterfactual,
                        "counterfactual_output": changed, "ablation": "wrong_intermediate",
                        "same_output_shape": _shape(output), "attempts": attempts,
                    }
    raise ValueError("No same-shape changed-color witness in this bounded divider search")


def build_witness(qualification_path, output_path):
    root = find_root(__file__)
    path, output_path = Path(qualification_path), Path(output_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    qualification = json.loads(path.read_bytes())
    if qualification.get("task_id") != TASK_ID or qualification.get("status") != "qualified":
        raise ValueError("Expected this task's native qualified report")
    contract, binding = _ready(Catalog(root), TASK_ID)
    if qualification.get("source_binding") != binding or qualification.get("contract") != contract:
        raise ValueError("Qualification does not bind current source/contract")
    execution_path = path.parent / "execution.json"
    execution_bytes = execution_path.read_bytes()
    if qualification.get("execution") != {"path": "execution.json", "sha256": hashlib.sha256(execution_bytes).hexdigest()}:
        raise ValueError("Qualification execution bytes differ")
    execution = json.loads(execution_bytes)
    programs = _check_execution(execution, qualification["jobs"], binding, contract)
    if programs != qualification["programs"]:
        raise ValueError("Qualification programs differ from execution")
    episode = next(row for row in execution["episodes"] if row["settings"] == contract["default"])
    if hashlib.sha256(episode["program"].encode()).hexdigest() != binding["canonical_program_sha256"]:
        raise ValueError("Causal witness must execute the exact qualified canonical default")
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    try:
        case = find_counterfactual(episode["program"], CAUSAL_INPUT, episode["settings"], apply)
    finally:
        bridge.close()
    # The repeated 5 changes in only one location: a per-color lookup cannot
    # collapse this grouping dependence into a cosmetic output recoloring.
    if case["output"] != [[1, 5], [5, 7]] or case["counterfactual_output"] != [[5, 7], [5, 7]]:
        raise ValueError("The retained repeated-color witness changed")
    report = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1", "task_id": TASK_ID,
        "source_binding": binding, **DEPENDENCY,
        "racket": {"backend": identity["backend"], "protected": identity["protected"]},
        "runtime_identity": identity, "cases": [case],
        "input_scope": "Hand-constructed lawful 8x8 task input, separate from qualification draws.",
        "limits": "Finite source-bound wrong-intermediate witness; causal interpretation requires owner review. No acceptance or training admission.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = build_witness(args.qualification, args.out)
    print(json.dumps({"status": "witness_replayed", "cases": len(report["cases"]),
                      "backend": report["racket"]["backend"], "protected": report["racket"]["protected"],
                      "out": str(args.out)}))


if __name__ == "__main__":
    main()
