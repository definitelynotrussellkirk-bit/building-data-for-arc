"""Reproduce the source-bound dimension-control audit finding.

Run from the packet root through review.py run; the payload cwd is WORK/repo.
Exit zero means that the documented defects were reproduced, not that the
generator satisfied its declared control contract.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "007721bb99b0"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = Path("generators") / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_dimension_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    catalog = Catalog()
    metadata = catalog.get(TASK_ID)
    pairs = canonical_pairs(TASK_ID, root=find_root(source))
    cases = []
    for overrides in ({"grid_h": 15, "grid_w": 3}, {"grid_h": 3, "grid_w": 15}):
        case = {"seed": 0, "sample_index": 0, "difficulty": None,
                "overrides": overrides,
                "expected_dimensions": [overrides["grid_h"], overrides["grid_w"]]}
        try:
            grid = generator.generate(0, 0, **overrides)
        except ValueError as exc:
            case.update(actual_error=f"ValueError: {exc}",
                        finding_reproduced="outside [2, 14]" in str(exc))
        else:
            case.update(actual_dimensions=[len(grid), len(grid[0])],
                        finding_reproduced=False)
        cases.append(case)

    controls = {"grid_h": 2, "grid_w": 2}
    grid = generator.generate(0, 0, **controls)
    actual_shape = [len(grid), len(grid[0])]
    errors = generator.self_check(grid, meta={"overrides": controls})
    cases.append({"seed": 0, "sample_index": 0, "difficulty": None,
                  "overrides": controls, "expected_dimensions": [2, 2],
                  "actual_dimensions": actual_shape, "input": grid,
                  "self_check_with_requested_overrides": errors,
                  "finding_reproduced": actual_shape == [2, 3] and errors == []})
    reference = catalog.apply(TASK_ID, [grid])
    expected_output = [row[:2] for row in grid[:2]]
    actual_output = reference["results"][0]["output"]
    assert reference["rule_hash_matches_catalog"]
    assert reference["results"][0]["error"] is None
    assert actual_output == expected_output
    report = {
        "schema": "007721bb99b0-dimension-audit-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "catalog_rule_hash": metadata["rule_hash"],
        "declared_dimension_axes": {axis: generator.AXES[axis] for axis in ("grid_h", "grid_w")},
        "canonical_pairs_inspected": [
            {"variant": pair["variant"], "split": pair["split"],
             "pair_index": pair["pair_index"],
             "input_dimensions": [len(pair["input"]), len(pair["input"][0])],
             "output_dimensions": [len(pair["output"]), len(pair["output"][0])],
             "output_matches_top_left_crop": pair["output"] == [row[:2] for row in pair["input"][:2]]}
            for pair in pairs
        ],
        "cases": cases,
        "reference_expected_output": expected_output,
        "reference_execution": reference,
        "finding_reproduced": all(case["finding_reproduced"] for case in cases),
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"task_id": TASK_ID, "source_sha256": report["source_sha256"],
                      "finding_reproduced": report["finding_reproduced"],
                      "cases": cases, "executed_rule_hash": reference["executed_rule_hash"],
                      "reference_output": actual_output}, indent=2))
    return int(not report["finding_reproduced"])


if __name__ == "__main__":
    raise SystemExit(main())
