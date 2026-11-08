"""Verify retained official labels and write the compact audit finding."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_SOURCE = "80d94a6e64895839b4da9c63524f47d7ea1568fa2714a8f846933ccd166fb497"


def read(name):
    return json.loads((HERE / name).read_text())


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


probe = read("probe.json")
oracle = read("racket.json")
generated = read("generated-racket.json")
inp = read("input.json")
rival = read("rival.json")
actual = oracle["results"][0]["output"]
source = HERE.parents[2] / "repo" / "generators" / "d476983a3d6c" / "generator.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SOURCE
for result in (oracle, generated):
    assert result["generator_sha256"] == EXPECTED_SOURCE
    assert result["executed_rule_hash"] == "c83bfd047bef"
    assert result["rule_hash_matches_catalog"]
    assert result["results"][0]["valid_output"]
    assert result["results"][0]["error"] is None
assert actual == read("python-mirror.json")
assert actual != rival
assert generated["results"][0]["output"] == read("generated-rival.json")
assert oracle["results"][0]["input_sha256"] == grid_hash(inp)
assert oracle["results"][0]["output_sha256"] == grid_hash(actual)
diffs = [{"row": r, "column": c, "racket": actual[r][c], "rival": rival[r][c]}
         for r in range(len(inp)) for c in range(len(inp[0])) if actual[r][c] != rival[r][c]]
result = {
    "task_id": "d476983a3d6c",
    "finding": "Object-color-count parity selects the command branch throughout the declared generator domain",
    "severity": "high teaching defect; no generated-label mismatch alleged",
    "source_sha256": EXPECTED_SOURCE,
    "executed_rule_hash": oracle["executed_rule_hash"],
    "rule_text_sha256": oracle["rule_text_sha256"],
    "canonical_pairs_matching_rival": [probe["canonical_rival_matches"], probe["canonical_pairs"]],
    "generated_draws_matching_rival_and_mirror": [probe["generated_rival_matches"], probe["draw_count"]],
    "officially_labeled_generated_draw": {
        "seed": 476984, "sample_index": 0, "difficulty": "medium",
        "validator_errors": [],
        "racket_matches_rival": True,
        "input_sha256": generated["results"][0]["input_sha256"],
        "output_sha256": generated["results"][0]["output_sha256"],
    },
    "minimal_marker_count_counterfactual": {
        "input_file": "input.json", "actual_file": "racket.json", "rival_file": "rival.json",
        "input_sha256": grid_hash(inp), "actual_sha256": grid_hash(actual),
        "rival_sha256": grid_hash(rival),
        "self_check": probe["witness"]["self_check"],
        "strict_canonical_like": probe["witness"]["strict_canonical_like"],
        "differing_cells": diffs,
        "scope": "Handcrafted separating case rejected only by the current scene-signature restriction; not claimed to be a generated draw.",
    },
    "scope": "Read assigned source, notes, tests and current evidence index; used portable helpers for 3 labeled canonical pairs and 36 generated draws; two official Racket apply calls. No source changes or full audit battery.",
}
(HERE / "finding.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2))
