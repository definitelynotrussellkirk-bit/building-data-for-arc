#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
TASK_ID = "83ca9df09514"
TICKET_ID = "ticket-008118e37b3e4bd6"
PINNED_SOURCE_SHA256 = "70db137b815d1463c9b759c9258749291aef361633d91fbf64e7c72c8d6f2233"
PINNED_MANIFEST_SHA256 = "f357ded774526708b2f4a9b3728489b03eeef489d830b4af12fb6075c9d0739f"
PINNED_RULE_HASH = "1dc6f00b70c9"
MANIFEST_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/evidence/manifest.json"
FORBIDDEN_PUBLIC_KEYS = {
    "seed", "setting", "duplicate_precedence", "program", "rival",
    "answer", "answers", "private", "metadata",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def main() -> None:
    source_path = ROOT / f"generators/{TASK_ID}/generator.py"
    source_sha = sha256(source_path.read_bytes())
    manifest_sha = sha256(MANIFEST_PATH.read_bytes())
    assert source_sha == PINNED_SOURCE_SHA256, (source_sha, PINNED_SOURCE_SHA256)
    assert manifest_sha == PINNED_MANIFEST_SHA256, (manifest_sha, PINNED_MANIFEST_SHA256)

    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["task_id"] == TASK_ID
    assert manifest["generator_sha256"] == PINNED_SOURCE_SHA256
    assert manifest["canonical_rule_hash"] == PINNED_RULE_HASH
    assert manifest["variant_approved"] is False
    assert manifest["production_parametric_api"] is False
    assert manifest["owner_program_changes"] is False
    inspection = manifest["owner_public_inspection"]
    assert inspection["status"] == "static_projection_only"
    assert len(inspection["public_files"]) == 2

    rows = [row for row in manifest["files"] if "/public/challenge-" in row["path"]]
    assert len(rows) == 2
    public_records = []
    for row in sorted(rows, key=lambda item: item["path"]):
        path = ROOT / row["path"]
        raw = path.read_bytes()
        digest = sha256(raw)
        assert digest == row["sha256"]
        assert path.stem == f"challenge-{digest}"
        assert len(raw) == row["bytes"]

        payload = json.loads(raw)
        assert set(payload) == {"train", "test"}
        assert len(payload["train"]) == 2
        assert len(payload["test"]) == 4
        assert all(set(item) == {"input", "output"} for item in payload["train"])
        assert all(set(item) == {"input"} for item in payload["test"])
        query_serializations = [json.dumps(item["input"], separators=(",", ":")) for item in payload["test"]]
        assert len(set(query_serializations)) == 4
        leaked = sorted(FORBIDDEN_PUBLIC_KEYS.intersection(walk_keys(payload)))
        assert leaked == [], leaked
        public_records.append({
            "path": row["path"],
            "sha256": digest,
            "bytes": len(raw),
            "train_examples": len(payload["train"]),
            "queries": len(payload["test"]),
            "distinct_queries": len(set(query_serializations)),
            "payload": payload,
        })

    declared = sorted((row["sha256"], row["queries"]) for row in inspection["public_files"])
    observed = sorted((row["sha256"], row["queries"]) for row in public_records)
    assert declared == observed

    left, right = [row["payload"] for row in public_records]
    assert [item["input"] for item in left["train"]] == [item["input"] for item in right["train"]]
    assert [item["input"] for item in left["test"]] == [item["input"] for item in right["test"]]
    assert [item["output"] for item in left["train"]] != [item["output"] for item in right["train"]]

    for row in public_records:
        del row["payload"]
    result = {
        "schema": "arcpuzzles-ticket-parameter-queries-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source_sha256": source_sha,
        "manifest_sha256": manifest_sha,
        "rule_hash": PINNED_RULE_HASH,
        "public_files": public_records,
        "paired_train_inputs_match": True,
        "paired_query_inputs_match": True,
        "paired_train_outputs_differ": True,
        "hidden_keys_absent": sorted(FORBIDDEN_PUBLIC_KEYS),
        "variant_approved": False,
        "production_parametric_api": False,
        "inspection_status": inspection["status"],
        "verdict": "four-query visible-only projection passes static privacy and count checks; no semantic execution or variant approval",
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "completed",
        "public_files": len(public_records),
        "queries_per_file": [row["queries"] for row in public_records],
        "distinct_queries_per_file": [row["distinct_queries"] for row in public_records],
        "hidden_key_leaks": 0,
        "variant_approved": False,
        "result": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
