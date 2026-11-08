#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "44d20451ce17"
EXPECTED_GENERATOR_SHA = "ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0"
EXPECTED_MANIFEST_SHA = "1b9b47b121dd90342cf731a3f3995c0efb02f0cbb4042c840ea26ece9cb93ff3"
start = time.monotonic()
root = find_root(__file__)
generator_path = root / "generators" / TASK_ID / "generator.py"
manifest_path = root / "generators" / TASK_ID / "workspace" / "parametric" / "evidence" / "manifest.json"
assert hashlib.sha256(generator_path.read_bytes()).hexdigest() == EXPECTED_GENERATOR_SHA
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == EXPECTED_MANIFEST_SHA
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
assert manifest["generator_sha256"] == EXPECTED_GENERATOR_SHA

report_path = root / "generators" / TASK_ID / "workspace" / "parametric" / "evidence" / "reviewer-reported" / "1fd2b1ab7f9d411a" / "parametric" / "destination-edge-v2-evidence.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
assert report["replay"]["n_train"] == 3
assert report["replay"]["n_test"] == 4
assert len(report["private_episodes"]) == 2
by_id = {record["public_id"]: record for record in report["public_files"]}
checks = []
for episode in report["private_episodes"]:
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    identities = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*episode["train"], *episode["test"]]
    ]
    assert len(identities) == len(set(identities)) == 7

    public_id = public_challenge_id(episode)
    payload = public_challenge_bytes(episode)
    record = by_id[public_id]
    public_path = root / record["path"]
    assert public_path.read_bytes() == payload
    assert hashlib.sha256(payload).hexdigest() == public_id == record["sha256"]
    public = json.loads(payload)
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input"} for pair in public["test"])

    private_only = deepcopy(episode)
    private_only["seed"] = 999
    private_only["parameters"] = {"destination_edge": "private-change"}
    private_only["program"] = "private-change"
    for pair in private_only["test"]:
        pair["output"] = [[9]]
    assert public_challenge_id(private_only) == public_id

    visible_change = deepcopy(episode)
    cell = visible_change["test"][0]["input"][0][0]
    visible_change["test"][0]["input"][0][0] = (cell + 1) % 10
    assert public_challenge_id(visible_change) != public_id
    checks.append(
        {
            "public_id": public_id,
            "setting": episode["parameters"]["destination_edge"],
            "demonstrations": len(episode["train"]),
            "queries": len(episode["test"]),
            "distinct_inputs": len(set(identities)),
            "query_answers_excluded_from_id": True,
            "query_input_affects_id": True,
        }
    )

result = {
    "ticket_id": "ticket-cc146f928b12545b",
    "type": "parameter_queries",
    "status": "completed",
    "bindings": {
        "generator_path": str(generator_path.relative_to(root)),
        "generator_sha256": EXPECTED_GENERATOR_SHA,
        "evidence_manifest_path": str(manifest_path.relative_to(root)),
        "evidence_manifest_sha256": EXPECTED_MANIFEST_SHA,
        "evidence_report_path": str(report_path.relative_to(root)),
        "evidence_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
    },
    "boundary": "retained 3-demo/4-query support and visible-only public identity",
    "episodes": checks,
    "finding": None,
    "approval_boundary": "Support verified; no variant or production approval inferred.",
    "elapsed_seconds": round(time.monotonic() - start, 6),
}
Path(__file__).with_name("result.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, sort_keys=True))
