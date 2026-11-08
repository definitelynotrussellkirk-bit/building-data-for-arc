"""Analyze current 7284e86d3539 audit probe and public Racket outputs."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path.cwd().parent / "checks" / "audit" / "7284e86d3539"
cases_doc = json.loads((OUT / "cases.json").read_text())
overrides = json.loads((OUT / "overrides.json").read_text())
racket = json.loads((OUT / "racket.json").read_text())
cases = cases_doc["cases"]
results = racket["results"]
assert len(cases) == len(results)
for case, result in zip(cases, results):
    assert result["valid_output"] and result["error"] is None
    assert result["input"] == case["input"]

generated = cases[:-1]
generated_results = results[:-1]
witness = cases[-1]
witness_result = results[-1]

summary = {
    "task_id": "7284e86d3539",
    "generator_sha256": cases_doc["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "normal_sample_policy": {"difficulties": ["easy", "medium", "hard"],
                             "seeds": [0, 1, 2, 3], "sample_indices": [0], "overrides": {}},
    "normal_generated_count": len(generated),
    "unique_normal_inputs": len({result["input_sha256"] for result in generated_results}),
    "normal_selfcheck_passes": sum(not case["self_check"] for case in generated),
    "normal_valid_racket_outputs": sum(result["valid_output"] for result in generated_results),
    "normal_vertical_rival_matches": sum(case["rival_output"] == result["output"]
                                           for case, result in zip(generated, generated_results)),
    "normal_row0_empty": sum(all(value == 0 for value in result["output"][0])
                              for result in generated_results),
    "canonical_witness_selfcheck": witness["self_check"],
    "canonical_witness_reference_label_matches": int(witness_result["output"] == witness["expected_canonical_output"]),
    "canonical_witness_rival_matches": int(witness_result["output"] == witness["rival_output"]),
    "canonical_witness_row0_empty": int(all(value == 0 for value in witness_result["output"][0])),
    "override_cases": len(overrides["checks"]),
    "override_cases_identical_to_baseline": sum(row["identical_to_baseline"] for row in overrides["checks"]),
    "lesson_tested": False,
    "limits": "Bounded example census and generated-only rival; no lesson census or canonical-fitting rival claim.",
}

counterexample = {
    "task_id": "7284e86d3539",
    "generator_sha256": cases_doc["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "finding_id": "A2-D1",
    "kind": "canonical_witness",
    "canonical_fitting_shortcut_claim": False,
    "variant": witness["variant"],
    "split": witness["split"],
    "pair_index": witness["pair_index"],
    "input": witness["input"],
    "expected_canonical_output": witness["expected_canonical_output"],
    "actual_racket_output": witness_result["output"],
    "rival_output": witness["rival_output"],
    "self_check": witness["self_check"],
    "actual_matches_canonical": witness_result["output"] == witness["expected_canonical_output"],
    "rival_matches_racket": witness_result["output"] == witness["rival_output"],
    "actual_row0_empty": all(value == 0 for value in witness_result["output"][0]),
    "authority_command": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
                 "7284e86d3539", "--input", "../checks/audit/7284e86d3539/input.json",
                 "--out", "../checks/audit/7284e86d3539/racket.json"],
    },
    "rival_source": "checks/audit/7284e86d3539/probe.py:rival",
}

assert summary["normal_selfcheck_passes"] == len(generated)
assert summary["normal_valid_racket_outputs"] == len(generated)
assert summary["normal_vertical_rival_matches"] == len(generated)
assert summary["normal_row0_empty"] == len(generated)
assert summary["canonical_witness_reference_label_matches"] == 1
assert summary["canonical_witness_rival_matches"] == 0
assert summary["canonical_witness_row0_empty"] == 0
assert summary["override_cases_identical_to_baseline"] == summary["override_cases"]

(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(OUT / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
print(json.dumps(summary, indent=2))
