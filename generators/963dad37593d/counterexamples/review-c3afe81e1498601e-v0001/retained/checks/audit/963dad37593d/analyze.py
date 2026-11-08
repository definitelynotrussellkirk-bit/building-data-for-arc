"""Analyze current 963dad37593d audit probe and public Racket outputs."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path.cwd().parent / "checks" / "audit" / "963dad37593d"
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
    "task_id": "963dad37593d",
    "generator_sha256": cases_doc["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "normal_sample_policy": {
        "difficulties": ["easy", "medium", "hard"],
        "seeds": list(range(20)),
        "sample_indices": [0],
        "overrides": {},
    },
    "normal_generated_count": len(generated),
    "unique_normal_inputs": len({case["input_sha256"] for case in generated}),
    "normal_selfcheck_passes": sum(not case["self_check"] for case in generated),
    "normal_prefix_equals_count": sum(case["prefix_equals_count"] for case in generated),
    "normal_prefix_rival_matches_racket": sum(case["rival_output"] == result["output"]
                                                for case, result in zip(generated, generated_results)),
    "normal_valid_racket_outputs": sum(result["valid_output"] for result in generated_results),
    "canonical_witness_selfcheck": witness["self_check"],
    "canonical_witness_header_positions": witness["header_positions"],
    "canonical_witness_header_count": witness["header_count"],
    "canonical_witness_prefix_rank": witness["leading_prefix_rank"],
    "canonical_witness_reference_label_matches": int(witness_result["output"] == witness["expected_canonical_output"]),
    "canonical_witness_prefix_rival_matches": int(witness_result["output"] == witness["rival_output"]),
    "override_cases": len(overrides["checks"]),
    "override_cases_identical_to_baseline": sum(row.get("identical_to_baseline") is True
                                                  for row in overrides["checks"]),
    "observable_dimension_override_cases_identical": sum(
        row["axis"] in {"grid_h", "grid_w"} and row.get("identical_to_baseline") is True
        for row in overrides["checks"]),
    "helpful_palette_or_texture_cases_identical": sum(
        row["axis"] in {"palette_kind", "texture"} and row.get("identical_to_baseline") is True
        for row in overrides["checks"]),
    "hard_default_rank_counts": overrides["hard_default_rank_counts"],
    "hard_default_rank_above_advertised_1_to_3": sum(
        int(count) for rank, count in overrides["hard_default_rank_counts"].items() if int(rank) > 3),
    "lesson_tested": False,
    "limits": "Bounded source-bound audit; no lesson census or canonical-fitting universal rival claim.",
}

counterexample = {
    "task_id": "963dad37593d",
    "generator_sha256": cases_doc["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "finding_id": "A1-D1",
    "kind": "canonical_witness",
    "variant": witness["variant"],
    "split": witness["split"],
    "pair_index": witness["pair_index"],
    "input": witness["input"],
    "expected_canonical_output": witness["expected_canonical_output"],
    "actual_racket_output": witness_result["output"],
    "self_check": witness["self_check"],
    "header_positions": witness["header_positions"],
    "header_count": witness["header_count"],
    "leading_prefix_rank": witness["leading_prefix_rank"],
    "prefix_rival_output": witness["rival_output"],
    "actual_matches_canonical": witness_result["output"] == witness["expected_canonical_output"],
    "prefix_rival_matches_racket": witness_result["output"] == witness["rival_output"],
    "authority_command": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
                 "963dad37593d", "--input", "../checks/audit/963dad37593d/input.json",
                 "--out", "../checks/audit/963dad37593d/racket.json"],
    },
    "rival_source": "checks/audit/963dad37593d/probe.py:prefix_rival",
}

assert summary["normal_selfcheck_passes"] == len(generated)
assert summary["normal_prefix_equals_count"] == len(generated)
assert summary["normal_prefix_rival_matches_racket"] == len(generated)
assert summary["canonical_witness_reference_label_matches"] == 1
assert summary["canonical_witness_prefix_rival_matches"] == 0
assert summary["observable_dimension_override_cases_identical"] == 4
assert summary["helpful_palette_or_texture_cases_identical"] == 8
assert summary["hard_default_rank_above_advertised_1_to_3"] > 0

(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(OUT / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
print(json.dumps(summary, indent=2))
