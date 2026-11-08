#!/usr/bin/env python3
"""Build strict public examples from already-qualified native episodes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

execution_path = HERE / "qualification" / "execution.json"
execution = json.loads(execution_path.read_text(encoding="utf-8"))
public_dir = HERE / "public"
public_dir.mkdir(parents=True, exist_ok=True)
for old in public_dir.glob("*.json"):
    old.unlink()

rows = []
selected = [episode for episode in execution["episodes"] if episode["seed"] == 0]
assert {episode["settings"]["fill_passes"] for episode in selected} == {1, 2}
for episode in sorted(selected, key=lambda row: row["settings"]["fill_passes"]):
    visible = {"train": episode["train"], "test": episode["test"]}
    raw = public_challenge_bytes(visible)
    public_id = public_challenge_id(visible)
    assert public_id == hashlib.sha256(raw).hexdigest()
    path = public_dir / f"{public_id}.json"
    path.write_bytes(raw)

    parsed = json.loads(raw)
    assert set(parsed) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in parsed["train"])
    assert all(set(pair) == {"input"} for pair in parsed["test"])
    assert len(parsed["test"]) == 4

    # Settings/program/reference fields and query answers are private and must
    # not alter either visible bytes or the content-derived public identifier.
    mutated = copy.deepcopy(episode)
    mutated["settings"] = {"fill_passes": 999}
    mutated["program"] = "PRIVATE PROGRAM MUTATED"
    mutated["program_sha256"] = "0" * 64
    mutated["reference"] = "PRIVATE REFERENCE MUTATED"
    for pair in mutated["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(mutated) == raw
    assert public_challenge_id(mutated) == public_id

    # A four-query container is controller data.  The first model-visible turn
    # projects demonstrations plus only query 1, identically to single-query use.
    one_query = {"train": episode["train"], "test": [episode["test"][0]]}
    sequential_first_turn = {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][0]["input"])}],
    }
    first_turn_bytes = public_challenge_bytes(one_query)
    assert public_challenge_bytes(sequential_first_turn) == first_turn_bytes
    first_turn_parsed = json.loads(first_turn_bytes)
    assert len(first_turn_parsed["test"]) == 1
    assert "output" not in first_turn_parsed["test"][0]

    inputs = [pair["input"] for pair in [*parsed["train"], *parsed["test"]]]
    encoded_inputs = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    assert len(encoded_inputs) == len(set(encoded_inputs))

    rows.append({
        "fill_passes": episode["settings"]["fill_passes"],
        "seed": episode["seed"],
        "public_id": public_id,
        "path": f"checks/fe54bfae4cee/public/{path.name}",
        "bytes": len(raw),
        "demonstrations": len(parsed["train"]),
        "queries": len(parsed["test"]),
        "first_turn_sha256": hashlib.sha256(first_turn_bytes).hexdigest(),
        "private_metadata_and_answers_invariant": True,
        "first_turn_matches_single_query": True,
    })

report = {
    "schema": "arcpuzzles-public-projection-evidence-v1",
    "task_id": "fe54bfae4cee",
    "status": "passed",
    "source_execution": "checks/fe54bfae4cee/qualification/execution.json",
    "source_execution_sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest(),
    "episodes": rows,
    "checks": {
        "canonical_public_bytes": True,
        "hash_names_exact_saved_bytes": True,
        "private_settings_programs_and_query_answers_excluded": True,
        "four_queries_distinct": True,
        "single_query_and_sequential_first_turn_identical": True,
        "future_queries_absent_from_first_turn": True,
        "total_query_count_absent_from_first_turn": True,
    },
    "limits": "Projection and identity checks only; Racket labels are inherited from the bound native qualification execution.",
}
(HERE / "public-projection.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "files": len(rows), "public_ids": [r["public_id"] for r in rows]}, indent=2))
