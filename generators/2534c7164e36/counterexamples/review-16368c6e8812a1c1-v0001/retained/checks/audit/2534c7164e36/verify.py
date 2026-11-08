"""Compare retained supported Racket results to the source-bound audit probe."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
probe = json.loads((HERE / "probe.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
assert hashlib.sha256((ROOT / "repo/generators/2534c7164e36/generator.py").read_bytes()).hexdigest() == probe["generator_sha256"]
assert racket["generator_sha256"] == probe["generator_sha256"]
assert racket["executed_rule_hash"] == probe["declared_rule_hash"]
assert racket["rule_hash_matches_catalog"] is True
assert len(racket["results"]) == len(probe["cases"]) == 9
cases = []
for index, (case, result) in enumerate(zip(probe["cases"], racket["results"])):
    assert result["index"] == index
    assert result["input"] == case["input"]
    assert result["error"] is None
    assert result["valid_output"] is True
    assert result["output"] == case["reference_expected_by_independent_overlay"]
    if "published_output" in case:
        assert result["output"] == case["published_output"]
    cases.append({**case, "actual_authoritative_racket_output": result["output"],
                  "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"],
                  "rival_disagreeing_cells": sum(a != b for ar, br in zip(result["output"], case["rival_output"])
                                                for a, b in zip(ar, br)), "cell_denominator": 16})
summary = {
    "task_id": probe["task_id"],
    "generator_sha256": probe["generator_sha256"],
    "canonical_rule_sha256": probe["rule_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "executed_rule_text_sha256": racket["rule_text_sha256"],
    "reference_command": probe["reproduction"]["reference_argv"],
    "command_cwd": "packet_root",
    "actual_reference_cwd": racket["cwd"],
    "racket_success_count": 9,
    "racket_input_denominator": 9,
    "unique_racket_inputs": len({json.dumps(c["input"]) for c in cases}),
    "canonical_published_output_match_count": 6,
    "unique_canonical_denominator": 6,
    "independent_overlay_match_count": 9,
    "cases": cases[:3],
    "limitations": [
        "The lookup rival explicitly uses all six public labels, including the training-row test pair.",
        "Published test geometry is also a training pair in the task's augmented row; split isolation is a policy question.",
        "Forced control samples use Python rule_mirror, with authoritative execution limited to these nine inputs.",
        "No natural lesson sampling, complete lesson witness coverage, full battery, or universal semantic correctness claim."
    ],
}
(HERE / "counterexamples.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k not in ("cases", "limitations")}, indent=2))
print(json.dumps([{k: c[k] for k in ("name", "validator_pass", "rival_disagreeing_cells", "cell_denominator")}
                  for c in summary["cases"]], indent=2))
