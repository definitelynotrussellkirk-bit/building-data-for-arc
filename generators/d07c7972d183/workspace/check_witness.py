"""Compare declared diagnostic rivals with a retained public Racket receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import types

from probe_curriculum import support


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    support()
    source = Path(__file__).resolve().parents[1] / "generator.py"
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    module = types.ModuleType("witness_generator")
    exec(compile(raw, str(source), "exec"), module.__dict__)
    receipt = json.loads(args.receipt.read_text())
    assert receipt["generator_sha256"] == digest, "stale receipt: rerun public apply"
    assert receipt["executed_rule_hash"] == module.RULE_HASH
    comparisons = []
    for case in receipt["results"]:
        assert case["valid_output"] and not case["error"]
        grid, output = case["input"], case["output"]
        errors = module.self_check(grid)
        rivals = {name: {"output": fn(grid), "refuted": fn(grid) != output}
                  for name, fn in module.LESSON_COMPETITORS.items()}
        comparisons.append({"input": grid, "reference_output": output,
                            "validator_errors": errors, "rivals": rivals})
    passed = all(not c["validator_errors"] and all(r["refuted"] for r in c["rivals"].values())
                 for c in comparisons)
    report = {"task_id": module.TASK_ID, "generator_sha256": digest,
              "rule_hash": module.RULE_HASH,
              "receipt_sha256": hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
              "authority": "retained public arcpuzzles apply receipt; no labels generated here",
              "status": "passed" if passed else "failed", "comparisons": comparisons}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "inputs": len(comparisons),
                      "rivals": list(module.LESSON_COMPETITORS), "generator_sha256": digest}))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
