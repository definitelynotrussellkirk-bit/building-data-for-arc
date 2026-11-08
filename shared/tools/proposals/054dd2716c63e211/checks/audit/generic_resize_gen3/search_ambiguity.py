"""Read-only audit probe for generic_resize_gen3.

Searches for a generated task whose demonstrations admit a different scale map
that changes a held-out test answer.  It also records the first task that
collapses to a simpler constant-per-axis resize.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / "generic_resize_gen3" / "generator.py"
OUT = Path(__file__).with_name("ambiguity.json")


def load_module():
    spec = importlib.util.spec_from_file_location("audit_generic_resize_gen3", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def scale_map(grid, row_scales, col_scales):
    output = []
    for row_index, row in enumerate(grid):
        expanded = []
        for col_index, value in enumerate(row):
            expanded.extend([value] * col_scales[col_index])
        output.extend([expanded[:]] * row_scales[row_index])
    return output


def candidate_vectors(length, total):
    for values in itertools.product((1, 2, 3), repeat=length):
        if sum(values) == total:
            yield values


def fit_all(pairs, row_scales, col_scales):
    return all(scale_map(pair["input"], row_scales, col_scales) == pair["output"] for pair in pairs)


def differing_test(task, row_scales, col_scales):
    for index, pair in enumerate(task["test"]):
        rival = scale_map(pair["input"], row_scales, col_scales)
        if rival != pair["output"]:
            return index, rival
    return None


def main():
    module = load_module()
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    first_uniform = None
    finding = None
    searched = 0
    for seed in range(100_000):
        task = module.generate_task(seed, difficulty="easy")
        searched += 1
        true_rows = tuple(task["meta"]["row_scales"])
        true_cols = tuple(task["meta"]["col_scales"])
        if first_uniform is None and len(set(true_rows)) == 1 and len(set(true_cols)) == 1:
            first_uniform = {
                "seed": seed,
                "row_scales": list(true_rows),
                "col_scales": list(true_cols),
                "program": task["program"],
            }

        for candidate_rows in candidate_vectors(len(true_rows), sum(true_rows)):
            if candidate_rows == true_rows:
                continue
            if not fit_all(task["train"], candidate_rows, true_cols):
                continue
            differs = differing_test(task, candidate_rows, true_cols)
            if differs is not None:
                test_index, rival = differs
                finding = {
                    "axis": "row",
                    "seed": seed,
                    "difficulty": "easy",
                    "true_row_scales": list(true_rows),
                    "alternative_row_scales": list(candidate_rows),
                    "true_col_scales": list(true_cols),
                    "program": task["program"],
                    "train": task["train"],
                    "test_index": test_index,
                    "test_input": task["test"][test_index]["input"],
                    "authoritative_output": task["test"][test_index]["output"],
                    "rival_output": rival,
                }
                break
        if finding is not None:
            break

        for candidate_cols in candidate_vectors(len(true_cols), sum(true_cols)):
            if candidate_cols == true_cols:
                continue
            if not fit_all(task["train"], true_rows, candidate_cols):
                continue
            differs = differing_test(task, true_rows, candidate_cols)
            if differs is not None:
                test_index, rival = differs
                finding = {
                    "axis": "column",
                    "seed": seed,
                    "difficulty": "easy",
                    "true_row_scales": list(true_rows),
                    "true_col_scales": list(true_cols),
                    "alternative_col_scales": list(candidate_cols),
                    "program": task["program"],
                    "train": task["train"],
                    "test_index": test_index,
                    "test_input": task["test"][test_index]["input"],
                    "authoritative_output": task["test"][test_index]["output"],
                    "rival_output": rival,
                }
                break
        if finding is not None:
            break

    result = {
        "schema": "generic-resize-gen3-audit-v1",
        "task_id": "generic_resize_gen3",
        "generator_sha256": source_sha,
        "searched_easy_seeds": searched,
        "finding": finding,
        "first_uniform_axis_task": first_uniform,
        "replay": {
            "cwd": "repo",
            "argv": ["python3", "../checks/audit/generic_resize_gen3/search_ambiguity.py"],
        },
        "scope": (
            "Independent positive-integer scale-map enumeration over ratios 1..3. "
            "The finding is a lesson-identifiability counterexample, not a label-parity claim."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "searched": searched,
        "found_ambiguity": finding is not None,
        "seed": finding and finding["seed"],
        "axis": finding and finding["axis"],
        "uniform": first_uniform,
        "out": str(OUT),
    }, indent=2))
    raise SystemExit(0 if finding is not None else 1)


if __name__ == "__main__":
    main()
