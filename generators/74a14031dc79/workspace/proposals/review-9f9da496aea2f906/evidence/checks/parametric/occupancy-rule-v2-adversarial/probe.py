#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SOURCE = ROOT / "generators/74a14031dc79/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("occupancy_rule_probe", SOURCE)
assert spec and spec.loader
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)

with RacketBridge() as bridge:
    episode = prototype.make_episode(
        1,
        n_train=12,
        n_test=12,
        root=ROOT,
        bridge=bridge,
    )

pairs = episode["train"] + episode["test"]
input_hashes = [prototype.grid_sha256(pair["input"]) for pair in pairs]
assert len(input_hashes) == len(set(input_hashes)) == 24
assert episode["ambiguities"] == []
for row in episode["parameter_rivals"]:
    if row["occupancy_rule"] == episode["parameters"]["occupancy_rule"]:
        assert row["demonstration_mismatch_indices"] == []
        assert row["query_mismatch_indices"] == []
    else:
        assert row["demonstration_mismatch_indices"] == list(range(12))
        assert row["query_mismatch_indices"] == list(range(12))

visible_before = public_challenge_bytes(episode)
private_mutation = copy.deepcopy(episode)
private_mutation["seed"] = 999
private_mutation["parameters"] = {"occupancy_rule": "and"}
private_mutation["rule"] = {"racket_source": "changed privately"}
for pair in private_mutation["test"]:
    pair["output"] = [[9]]
visible_after = public_challenge_bytes(private_mutation)
assert visible_after == visible_before
public_id = public_challenge_id(episode)
assert prototype.public_filename(prototype.public_challenge(episode)) == f"challenge-{public_id}.json"

duplicate_rejected = False
try:
    prototype._sorted_unique_episode_rows(
        [{"public_id": public_id}, {"public_id": public_id}]
    )
except ValueError as exc:
    duplicate_rejected = "duplicate visible public challenge" in str(exc)
assert duplicate_rejected

summary = {
    "schema": "arcpuzzles-occupancy-rule-v2-adversarial-v1",
    "status": "pass",
    "prototype_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 1,
    "setting": episode["parameters"]["occupancy_rule"],
    "n_train": 12,
    "n_test": 12,
    "distinct_inputs": len(set(input_hashes)),
    "all_inputs_have_complete_truth_table": all(
        prototype.relation_set(pair["input"]) == {"00", "10", "01", "11"}
        for pair in pairs
    ),
    "ambiguities": episode["ambiguities"],
    "public_id": public_id,
    "public_bytes_sha256": hashlib.sha256(visible_before).hexdigest(),
    "private_metadata_and_query_answer_invariant": visible_after == visible_before,
    "duplicate_visible_id_rejected": duplicate_rejected,
    "limits_exercised": {"n_train": 12, "n_test": 12},
}
(HERE / "result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, sort_keys=True))
