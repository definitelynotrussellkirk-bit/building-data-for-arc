"""Check retained real-Racket evidence against the proposed audit claims."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from rival import solve

here = Path(__file__).resolve().parent
repo = here.parents[2] / "repo"


def read(name):
    return json.loads((here / name).read_text())


def save(name, value):
    (here / name).write_text(json.dumps(value, indent=2) + "\n")


identity = read("source_identity.json")
racket = read("racket.json")
lesson = read("lesson-default.jsonl")
explicit_lesson = read("lesson.jsonl")
assert hashlib.sha256((repo / identity["generator_file"]).read_bytes()).hexdigest() == identity["generator_sha256"]
assert racket["generator_sha256"] == identity["generator_sha256"]
assert racket["executed_rule_hash"] == identity["canonical_rule_normalized_hash"]
assert racket["rule_hash_matches_catalog"] is True
assert all(item["valid_output"] and item["error"] is None for item in racket["results"])
assert lesson["train"] == explicit_lesson["train"] and lesson["test"] == explicit_lesson["test"]
assert lesson["provenance"]["demonstration_policy"]["automatic"] is True
assert lesson["sample_indices"] == [0, 1, 2, 3]
assert lesson["rejections"] == []
assert [p["input"][0][0] for p in lesson["train"] + lesson["test"]] == [1, 1, 1, 2]
assert lesson["provenance"]["generator_sha256"] == identity["generator_sha256"]
assert lesson["executed_rule_hash"] == identity["canonical_rule_normalized_hash"]
predictions = []
for index, pair in enumerate(lesson["train"] + lesson["test"]):
    actual = racket["results"][index+2]
    assert pair["input"] == actual["input"]
    assert pair["output"] == actual["output"]
    rival = solve(pair["input"])
    predictions.append({"split": "train" if index < 3 else "test",
                        "pair_index": index if index < 3 else 0,
                        "sample_index": index, "input": pair["input"],
                        "racket_output": actual["output"], "rival_output": rival,
                        "matches_racket": rival == actual["output"]})
assert all(p["matches_racket"] for p in predictions[:3])
assert predictions[3]["matches_racket"] is False
save("rival_outputs.json", {"rival": "rival.py:solve", "description": "Remove corner, crop all body cells, always flip left-right",
                            "source_identity": identity, "results": predictions})
overrides = read("override_probes.json")["results"]
assert overrides[1]["overrides"] == {"blob_size": 7}
assert overrides[1]["profile"]["body_size"] == 4
assert overrides[1]["equal_to_default"] is True
assert overrides[1]["overrides_used"] == {}
assert overrides[1]["profile"]["self_check"] == []
assert overrides[1]["input"] == racket["results"][0]["input"]
canonical = read("canonical_task.json")
assert racket["results"][1]["input"] == canonical["test"][0]["input"]
assert racket["results"][1]["output"] == canonical["test"][0]["output"]
findings = {
    "task_id": identity["task_id"], "claim_class": "reproduced",
    "generator_sha256": identity["generator_sha256"],
    "canonical_rule_source_sha256": identity["canonical_rule_text_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "executed_callable_text_sha256": racket["rule_text_sha256"],
    "automatic_lesson": {"seed": 3, "sample_index": 0, "sample_indices": [0, 1, 2, 3],
        "difficulty": "medium", "overrides": {}, "demonstrations": 3, "queries": 1,
        "keys": [1, 1, 1, 2], "public_sampler_rejections": [],
        "lesson_check": lesson["lesson_check"], "rival_fit_demos": [True, True, True],
        "rival_query_matches": False, "racket_query_output": predictions[3]["racket_output"],
        "rival_query_output": predictions[3]["rival_output"]},
    "ignored_override": {"seed": 0, "sample_index": 0, "difficulty": "medium",
        "overrides": {"blob_size": 7}, "actual_body_size": 4, "self_check": [],
        "same_input_as_default": True, "racket_output": racket["results"][0]["output"]},
    "canonical_support": {
        "unreachable_features_from_source": ["body contains color 2", "monochrome body", "two 4-connected body components", "width 7 under any difficulty"],
        "canonical_test_validator": "accepted", "canonical_test_self_check": [],
        "canonical_test_racket_output_matches": True,
        "scope": "Structural exclusion in ordinary generation; explicit degenerate fixtures are not sampled as lawful lessons"},
    "limitations": ["No full battery or statistical lesson census was run", "Only one medium-band automatic lesson is replayed", "Ignored controls and canonical support are generation defects; all six reference applications returned valid outputs", "No source was edited outside this task's checks/audit directory"],
}
save("findings.json", findings)
print(json.dumps(findings, indent=2))
