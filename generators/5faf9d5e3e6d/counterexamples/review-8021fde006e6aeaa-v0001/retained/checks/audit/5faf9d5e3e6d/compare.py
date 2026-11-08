#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK_ID = "5faf9d5e3e6d"
root = find_root(__file__)
gen, _, source_sha = load_selected_generator(TASK_ID, root=root)
episode = json.loads((HERE / "default_episode.jsonl").read_text().splitlines()[0])
racket = json.loads((HERE / "racket.json").read_text())
rival = json.loads((HERE / "rival.json").read_text())
pairs = [*episode["train"], *episode["test"]]
inputs = [pair["input"] for pair in pairs]
episode_outputs = [pair["output"] for pair in pairs]
racket_outputs = [row["output"] for row in racket["results"]]
assert source_sha == racket["generator_sha256"]
assert racket_outputs == episode_outputs
self_checks = [gen.self_check(grid) for grid in inputs]
assert all(not errors for errors in self_checks)
agreement = [actual == expected for actual, expected in zip(rival["outputs"], racket_outputs)]
assert agreement == [True, True, True, False]
report = {
    "schema": "audit-racket-bound-comparison-v1",
    "task_id": TASK_ID,
    "generator_sha256": source_sha,
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "sample_indices": episode["sample_indices"],
    "keys": [grid[0][0] for grid in inputs],
    "self_checks": self_checks,
    "rival_agrees_with_racket": agreement,
    "all_demonstrations_fit": all(agreement[:3]),
    "query_differs": not agreement[3],
    "racket_query_output": racket_outputs[3],
    "rival_query_output": rival["outputs"][3],
    "evidence": {
        "episode": "default_episode.jsonl",
        "inputs": "input.json",
        "racket": "racket.json",
        "rival": "rival.json",
        "analysis": "analysis.json",
    },
}
(HERE / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
