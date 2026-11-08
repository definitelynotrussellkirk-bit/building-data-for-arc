"""Check the retained public Racket receipt against this audit's exact inputs."""
import hashlib
import json
from pathlib import Path

from probe import predict


root = Path(__file__).resolve().parent
probe = json.loads((root / "probe.json").read_text())
receipt = json.loads((root / "racket.json").read_text())
inputs = json.loads((root / "racket-inputs.json").read_text())
assert receipt["task_id"] == probe["task_id"] == "eb46daa8881c"
assert receipt["generator_sha256"] == probe["generator_sha256"]
assert receipt["rule_hash_matches_catalog"] is True
assert len(receipt["results"]) == len(inputs) == 5
for grid, result in zip(inputs, receipt["results"], strict=True):
    assert result["input"] == grid and result["error"] is None
    assert result["valid_output"] is True
    assert result["output"] == predict(grid, clean_diagonals=False)
counterexample = receipt["results"][0]
assert probe["diagonal_counterexample"]["self_check_easy"] == []
assert counterexample["output"] != predict(counterexample["input"], clean_diagonals=True)
assert counterexample["output"][2][2] == 8
for case in probe["ignored_exact_controls"]:
    assert case["observed_nonzero_colors"] == 3 and case["requested"] == 1
    assert case["same_as_no_override"] and case["self_check"] == []
summary = {
    "task_id": receipt["task_id"],
    "generator_sha256": receipt["generator_sha256"],
    "executed_rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "racket_receipt_sha256": hashlib.sha256((root / "racket.json").read_bytes()).hexdigest(),
    "racket_verified_inputs": 5,
    "canonical_rival_matches": probe["canonical"]["clean_diagonal_rival_matches"],
    "canonical_pairs": probe["canonical"]["pairs"],
    "default_draws": 300,
    "default_rival_agreement_with_python_mirror": 300,
    "ignored_exact_controls": [case["axis"] for case in probe["ignored_exact_controls"]],
    "diagonal_counterexample_refutes_rival": True,
    "support": "validator_accepted, outside documented clean-footprint default support",
    "prior_lead": "review-50a65f644b693fed:v0001, same generator source",
    "source_modified": False,
    "status": "reproduced_findings",
}
(root / "verified-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
