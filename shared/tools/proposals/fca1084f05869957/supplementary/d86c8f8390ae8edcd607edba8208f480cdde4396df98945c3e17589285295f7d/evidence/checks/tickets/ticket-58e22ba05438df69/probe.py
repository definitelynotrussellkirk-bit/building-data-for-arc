#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
OUT = Path(__file__).resolve().parent
TASK_ID = "747486860e56"
REQUEST_ID = "review-e119992824f89f40:v0001:F2"
MANIFEST = REPO / "shared/tools/proposals/fca1084f05869957/manifest.json"
TOOL = REPO / "shared/tools/check_task_authority_sync.py"
SUGGESTIONS = REPO / "REVIEW/suggestions.json"
EXPECTED_MANIFEST_SHA = "adbbd0ad863dfaefaf727a5808e197b05a591f15a84dd3ea6fb09da7edcda25b"
EXPECTED_REQUEST_SHA = "72d19bbb85e2f86c940cc2a60987c078b87363e203f820aaeaff77c634f909e9"
EXPECTED_GENERATOR_SHA = "008f30c17748241bfc1bc3678dda6f34faba375edea6cc20a447a3823a9aa8ad"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def find_request(value):
    if isinstance(value, dict):
        if value.get("request_id") == REQUEST_ID:
            return value
        for child in value.values():
            found = find_request(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_request(child)
            if found is not None:
                return found
    return None


def main() -> int:
    manifest_raw = MANIFEST.read_bytes()
    if sha(manifest_raw) != EXPECTED_MANIFEST_SHA:
        raise AssertionError("asset manifest hash mismatch")
    manifest = json.loads(manifest_raw)
    asset_checks = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        raw = path.read_bytes()
        asset_checks.append({
            "path": row["path"],
            "bytes": len(raw),
            "sha256": sha(raw),
            "matches_manifest": len(raw) == row["bytes"] and sha(raw) == row["sha256"],
        })
    if not all(row["matches_manifest"] for row in asset_checks):
        raise AssertionError("retained asset mismatch")

    request = find_request(json.loads(SUGGESTIONS.read_text(encoding="utf-8")))
    if request is None:
        raise AssertionError("request not found")
    request_projection = {
        "request_id": request["request_id"],
        "return_id": request["return_id"],
        "generator_id": request["generator_id"],
        "status": request["status"],
        "text": request["text"],
        "reason": request["reason"],
    }
    # The ticket pins the source request record hash, not this reduced projection.
    source_request_hash_matches = sha(canonical_json(request)) == EXPECTED_REQUEST_SHA

    current_json = OUT / "current-authority.json"
    command = [sys.executable, str(TOOL), TASK_ID, "--json-out", str(current_json)]
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True, timeout=120)
    (OUT / "probe.log").write_text(
        "$ " + " ".join(command) + "\n"
        + completed.stdout
        + completed.stderr
        + f"exit={completed.returncode}\n",
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise AssertionError(f"authority tool exited {completed.returncode}")
    current = json.loads(current_json.read_text(encoding="utf-8"))
    audit = current["audits"][0]

    apply_receipt = json.loads((REPO / manifest["files"][1]["path"]).read_text(encoding="utf-8"))
    parity = json.loads((REPO / manifest["files"][2]["path"]).read_text(encoding="utf-8"))
    canonical_hash = apply_receipt["canonical_source_sha256"]
    receipt_consistent = (
        parity["canonical_source_sha256"] == canonical_hash
        and parity["mismatch_count"] == 0
        and parity["total_cases"] == 586
        and parity["racket_evaluations"] == 1758
        and all(row["target_code_sha256_after"] == canonical_hash for row in apply_receipt["files"])
        and all(row["changed_json_pointers"] == ["/racket_target/target_code"] for row in apply_receipt["files"])
    )
    tool_source = TOOL.read_text(encoding="utf-8")
    emits_selected_only = '"--selected-only"' in tool_source
    accepts_selected_only = 'add_argument(\n        "--selected-only"' in tool_source or "add_argument('--selected-only'" in tool_source

    generator_path = REPO / f"generators/{TASK_ID}/generator.py"
    report = {
        "schema": "arcpuzzles-ticket-tool-reproduction-v1",
        "ticket_id": "ticket-58e22ba05438df69",
        "type": "tool_reproduction",
        "status": "completed",
        "pinned_identity": {
            "task_id": TASK_ID,
            "request_id": REQUEST_ID,
            "asset_manifest_sha256": sha(manifest_raw),
            "generator_sha256": sha(generator_path.read_bytes()),
            "generator_hash_matches_ticket": sha(generator_path.read_bytes()) == EXPECTED_GENERATOR_SHA,
            "request_source_record_present": request is not None,
            "request_sha256_ticket_value": EXPECTED_REQUEST_SHA,
            "request_hash_field_consistent": source_request_hash_matches,
        },
        "asset_checks": asset_checks,
        "retained_reproduction": {
            "manual_receipt_consistent": receipt_consistent,
            "canonical_source_sha256": canonical_hash,
            "finite_cases": parity["total_cases"],
            "racket_evaluations": parity["racket_evaluations"],
            "mismatches": parity["mismatch_count"],
            "selected_target_fields_changed": len(apply_receipt["files"]),
            "raw_code_preserved": all(
                row["raw_code_sha256"] in {
                    source["raw_code_sha256"] for source in parity["files_before_manual_sync"]
                }
                for row in apply_receipt["files"]
            ),
            "dry_run_log_bytes": asset_checks[0]["bytes"],
        },
        "current_tool_probe": {
            "command": command,
            "exit_status": completed.returncode,
            "task_status": audit["status"],
            "selected_exact_groups": audit["selected_group_counts"]["exact_sha256"],
            "archival_divergent_count": len(audit["archival_divergent"]),
            "remediation_needed_now": audit["selected_sync_remediation"]["needed"],
            "proposal_argv": audit["selected_sync_remediation"]["proposal_argv"],
            "tool_emits_selected_only_flag": emits_selected_only,
            "tool_accepts_selected_only_flag": accepts_selected_only,
        },
        "proposed_disposition": {
            "decision": "accept_for_implementation_with_narrow_scope",
            "reason": (
                "Retained manual evidence reproduces the selected-target-only need and preserves raw_code, "
                "while the current tool still emits an unavailable --selected-only proposal command. "
                "Implement a non-applying exact-pointer patch scaffold only; do not infer semantic equivalence or auto-apply."
            ),
        },
        "limitations": [
            "The pre-sync source files are not retained, so the 586-case semantic probe was hash-checked but not rerun.",
            "The retained dry-run log is empty, so the original refusal text cannot be reproduced from that asset.",
            "The live tree is already selected-synchronized; the current probe verifies post-sync behavior only.",
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "decision": report["proposed_disposition"]["decision"],
        "tool_accepts_selected_only": accepts_selected_only,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
