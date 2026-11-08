#!/usr/bin/env python3
"""Explicit synthetic counting demonstration; no census/source compatibility claim."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from shortcut_coverage import score_window


def constant_zero(grid):
    return [[0]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New synthetic result JSON")
    args = parser.parse_args()
    cases = json.loads((Path(__file__).parent / "fixtures/synthetic_windows.json").read_text())
    rows = []
    for case in cases:
        pairs = [{"input": [[value]], "output": [[value]]} for value in case["values"]]
        metric = score_window(pairs[:4], pairs[4], {"synthetic_constant_zero": constant_zero})["shortcuts"]["synthetic_constant_zero"]
        rows.append({"name": case["name"], "window_values": case["values"], **metric})
    result = {
        "schema": "shortcut-coverage-synthetic-demonstration-v1",
        "evidence_type": "synthetic; not a public lesson census or source-bound generation result",
        "reference": "identity on a one-cell grid",
        "shortcut": "always return [[0]]",
        "proof_shortcut_is_wrong_outside_all_zero_window": {
            "input": [[1]], "reference_output": [[1]], "shortcut_output": constant_zero([[1]])},
        "cases": rows,
        "summary": {
            "cases": len(rows),
            "unrefuted_demo_cases": sum(row["teaching_covered"] is False for row in rows),
            "rotation_fragile_cases": sum(row["rotation_robust"] is False for row in rows),
        },
    }
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "summary": result["summary"]}))
    # Exit 1 explicitly demonstrates the diagnostic's gap semantics.
    return 1 if result["summary"]["rotation_fragile_cases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
