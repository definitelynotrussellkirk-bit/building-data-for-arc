#!/usr/bin/env python3
"""Bind the audit comparison to retained raw public-command results."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
raw = json.loads((HERE / "racket.json").read_text())
rivals = json.loads((HERE / "rival.json").read_text())
mirrors = json.loads((HERE / "python_mirror.json").read_text())
finding = json.loads((HERE / "finding.json").read_text())
inputs = json.loads((HERE / "input.json").read_text())
results = raw["results"]
assert len(results) == len(inputs) == len(rivals) == len(mirrors) == 10
assert raw["executed_rule_hash"] == finding["rule_hash"] == "75437b07b887"
assert raw["generator_sha256"] == finding["generator_sha256"]
source = PACKET / "repo/generators/0dba62203065/generator.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == finding["generator_sha256"]
case_checks = []
for index, result in enumerate(results):
    assert result["index"] == index
    assert result["input"] == inputs[index]
    assert result["valid_output"] and result["error"] is None
    assert result["output"] == mirrors[index]
    differences = [
        {"row": r, "column": c, "racket": value, "rival": rivals[index][r][c]}
        for r, row in enumerate(result["output"]) for c, value in enumerate(row)
        if value != rivals[index][r][c]
    ]
    assert bool(differences) == (index == 0)
    case_checks.append({"index": index, "label": finding["input_labels_in_order"][index],
                        "valid_racket_output": True, "mirror_matches_racket": True,
                        "rival_matches_racket": not differences, "differences": differences,
                        "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"]})
report = {
    "status": "pass", "task_id": raw["task_id"],
    "generator_sha256": raw["generator_sha256"], "executed_rule_hash": raw["executed_rule_hash"],
    "executed_rule_text_sha256": raw["rule_text_sha256"],
    "raw_racket_valid_outputs": "10/10", "python_mirror_matches_raw_racket": "10/10",
    "conditional_rival_matches_raw_canonical_outputs": "3/3",
    "conditional_rival_matches_raw_generated_outputs": "6/6",
    "conditional_rival_differs_on_validator_accepted_out_of_generator_support_witness": True,
    "case_checks": case_checks,
    "raw_racket_sha256": hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest(),
    "source_unchanged": True,
    "interpretation": "Reproduces a remaining conditional shortcut and a broader-domain failure; does not demonstrate incorrect labels or a failure on generator-supported inputs.",
}
(HERE / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k:v for k,v in report.items() if k != "case_checks"}, indent=2))
