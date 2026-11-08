#!/usr/bin/env python3
"""Bounded source-bound check of one retained four-query public episode."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "5b18a320e97b"
EXPECTED_SOURCE_SHA256 = "e5f2b973ea40e89ba3fa7149a629a013c0a46aa16992d06b0f36133948de668f"
MANIFEST_REL = Path("generators/5b18a320e97b/workspace/parametric/evidence/manifest.json")
EXPECTED_MANIFEST_SHA256 = "1f9103377eb4368dfcd31e83062194d9fd2cd9d399f70a456041c157622a8292"
EXPECTED_RULE_HASH = "9a2961f7f72d"
SETTING = "reverse"
EXPECTED_DEMOS = 3
EXPECTED_QUERIES = 4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe.py OUTPUT.json")
    output = Path(sys.argv[1])
    repo = Path.cwd().resolve()

    _module, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        fail(f"peer source differs: {source_sha256}")

    manifest_path = repo / MANIFEST_REL
    if sha256(manifest_path) != EXPECTED_MANIFEST_SHA256:
        fail("pinned parameter-evidence manifest differs")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("generator_sha256") != EXPECTED_SOURCE_SHA256:
        fail("manifest generator identity differs")
    if manifest.get("canonical_rule_hash") != EXPECTED_RULE_HASH:
        fail("manifest rule identity differs")

    records = {row["path"]: row for row in manifest["files"]}
    for relative, row in records.items():
        path = repo / relative
        if not path.is_file() or sha256(path) != row["sha256"]:
            fail(f"manifest member differs: {relative}")

    report_rel = next(path for path in records if path.endswith("/report.json"))
    evidence_root = (repo / report_rel).parent
    report = json.loads((repo / report_rel).read_text())
    if report.get("status") != "proposed_unapproved" or report.get("approved") is not False:
        fail("retained evidence no longer has unapproved-prototype status")

    episode_row = next(
        row for row in report["episodes"]
        if row.get("parameters", {}).get("read_direction") == SETTING
    )
    if episode_row["demo_count"] != EXPECTED_DEMOS:
        fail("demonstration count differs")
    if episode_row["query_count"] != EXPECTED_QUERIES:
        fail("query count differs")

    private = json.loads((evidence_root / episode_row["private_path"]).read_text())
    public_path = evidence_root / episode_row["public_path"]
    public_bytes = public_path.read_bytes()
    public = json.loads(public_bytes)

    if private.get("parameters") != {"read_direction": SETTING}:
        fail("episode setting is not fixed to reverse")
    if len(private["train"]) != EXPECTED_DEMOS or len(private["test"]) != EXPECTED_QUERIES:
        fail("private split counts differ")
    if len(public["train"]) != EXPECTED_DEMOS or len(public["test"]) != EXPECTED_QUERIES:
        fail("public split counts differ")

    expected_public = {
        "train": [{"input": row["input"], "output": row["output"]} for row in private["train"]],
        "test": [{"input": row["input"]} for row in private["test"]],
    }
    if public != expected_public:
        fail("public projection leaks, drops, or changes fields")
    if any(set(row) != {"input"} for row in public["test"]):
        fail("query answer or private metadata is visible")
    if any(set(row) != {"input", "output"} for row in public["train"]):
        fail("demonstration projection differs")
    if any("output" not in row for row in private["test"]):
        fail("private query labels are unavailable for verification")

    payload_sha256 = hashlib.sha256(public_bytes).hexdigest()
    if payload_sha256 != episode_row["public_id"]:
        fail("public ID is not the exact visible-byte hash")
    if public_path.name != f"challenge-{payload_sha256}.json":
        fail("public filename does not match visible-byte identity")

    input_hashes = [
        hashlib.sha256(json.dumps(row["input"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        for row in private["train"] + private["test"]
    ]
    if len(set(input_hashes)) != EXPECTED_DEMOS + EXPECTED_QUERIES:
        fail("episode inputs are not all distinct")

    rivals = {row["read_direction"]: row for row in episode_row["rivals"]}
    if rivals[SETTING]["status"] != "matches_episode":
        fail("selected setting does not match its episode")
    if rivals["forward"]["status"] != "refuted_by_demonstrations":
        fail("alternative setting is not identified from demonstrations")

    result = {
        "schema": "arcpuzzles-ticket-parameter-queries-v1",
        "ticket_id": "ticket-97ead9fe6fa33275",
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(repo)),
        "source_sha256": source_sha256,
        "rule_hash": EXPECTED_RULE_HASH,
        "manifest_path": str(MANIFEST_REL),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "setting_checked": SETTING,
        "demonstrations": EXPECTED_DEMOS,
        "queries": EXPECTED_QUERIES,
        "distinct_inputs": len(set(input_hashes)),
        "query_outputs_visible": False,
        "private_query_labels_present": True,
        "public_id_matches_visible_bytes": True,
        "alternative_refuted_by_demonstrations": True,
        "support_status": "retained_evidence_supports_four_queries",
        "variant_approved": False,
        "scope_limit": "Static replay of one pinned reverse-setting episode; no new labels or approval claim.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
