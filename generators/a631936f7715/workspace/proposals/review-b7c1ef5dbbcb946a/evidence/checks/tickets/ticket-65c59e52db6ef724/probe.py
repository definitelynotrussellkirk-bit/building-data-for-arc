#!/usr/bin/env python3
"""Bounded reproduction of the selected task-test-summary tool request."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

TICKET_ID = "ticket-65c59e52db6ef724"
REQUEST_ID = "review-6e327f73fe1ea04f:v0001:F3"
EXPECTED = {
    "request_source": "6c85823f8430070c462f9834d4b48778ffb8e1d58021ca748e366eefbc58d642",
    "request": "c9957722a4e083b52f18a40b8f84a98347e0792432a28d6fef4f24ddea07767b",
    "assets_manifest": "fb291b0aa4aa2f0aea8c350b64952c2142a93066590301899d20d931177a36e6",
    "generator": "062022af105768f36ba1765278dd9792f991b83eff36bf06b77523d368d915dd",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def find_request(value: object) -> dict:
    if isinstance(value, dict):
        if value.get("request_id") == REQUEST_ID:
            return value
        for child in value.values():
            try:
                return find_request(child)
            except LookupError:
                pass
    elif isinstance(value, list):
        for child in value:
            try:
                return find_request(child)
            except LookupError:
                pass
    raise LookupError(REQUEST_ID)


def main() -> int:
    repo = Path.cwd()
    request_source = repo / "REVIEW/suggestions.json"
    manifest_path = repo / "shared/tools/proposals/65ed520abff52536/manifest.json"
    battery_path = repo / "shared/tools/run_generator_battery.sh"
    generator_path = repo / "generators/a41ff6269d40/generator.py"
    notes_path = repo / "generators/a41ff6269d40/notes.md"
    tests_path = repo / "generators/a41ff6269d40/tests"

    request = find_request(json.loads(request_source.read_text()))
    manifest = json.loads(manifest_path.read_text())
    retained_rel = manifest["files"][0]["path"]
    retained_path = repo / retained_rel
    retained = json.loads(retained_path.read_text())
    battery_text = battery_path.read_text()
    stage_match = re.search(r"^STAGES=\(([^)]*)\)", battery_text, flags=re.MULTILINE)
    if not stage_match:
        raise AssertionError("battery STAGES declaration not found")
    stages = stage_match.group(1).split()

    observed_hashes = {
        "request_source": sha(request_source),
        "request": canon_sha(request),
        "assets_manifest": sha(manifest_path),
        "generator": sha(generator_path),
        "retained_result": sha(retained_path),
    }
    hash_checks = {name: observed_hashes[name] == expected for name, expected in EXPECTED.items()}
    manifest_asset_hash_ok = observed_hashes["retained_result"] == manifest["files"][0]["sha256"]
    source_has_task_stage = "task_tests" in stages
    source_mentions_task_tests = bool(re.search(r"\btask_tests\b", battery_text))
    notes = notes_path.read_text()
    notes_separate_receipts = "After battery: 12/12 green" in notes and "Focused tests: 40/40 pass" in notes
    retained_counts = retained.get("test_counts", {})
    retained_is_independent = retained.get("battery_summary") is None

    reproduced = all(hash_checks.values()) and manifest_asset_hash_ok and (
        len(stages) == 12
        and not source_has_task_stage
        and not source_mentions_task_tests
        and tests_path.is_dir()
        and retained.get("passed") is True
        and retained.get("stage") == "task_tests"
        and retained_counts.get("passed") == 40
        and retained_counts.get("failed") == 0
        and retained_is_independent
        and notes_separate_receipts
    )
    report = {
        "schema": "tool-request-reproduction-v1",
        "ticket_id": TICKET_ID,
        "request_id": REQUEST_ID,
        "passed": reproduced,
        "pinned_hashes": EXPECTED,
        "observed_hashes": observed_hashes,
        "hash_checks": hash_checks,
        "manifest_asset_hash_ok": manifest_asset_hash_ok,
        "current_battery": {
            "path": "repo/shared/tools/run_generator_battery.sh",
            "stage_count": len(stages),
            "stage_order": stages,
            "task_tests_in_stage_order": source_has_task_stage,
            "task_tests_token_present": source_mentions_task_tests,
        },
        "target": {
            "task_id": "a41ff6269d40",
            "test_directory_exists": tests_path.is_dir(),
            "notes_report_battery_and_task_tests_separately": notes_separate_receipts,
            "retained_task_test_result": {
                "stage": retained.get("stage"),
                "passed": retained.get("passed"),
                "counts": retained_counts,
                "battery_summary": retained.get("battery_summary"),
                "stdout": retained.get("stdout", "").strip(),
            },
        },
        "reproduction": (
            "The current default battery can still report all 12 declared stages green while "
            "the selected task's existing tests remain a separate, independently invoked receipt."
        ),
        "proposed_request_disposition": "accept_as_actionable_open_request",
        "recommended_minimum": (
            "When a selected task test directory exists, add task_tests to the completion summary "
            "or emit an explicit NOT RUN status plus the exact command; never infer pass from the battery."
        ),
        "scope_limit": "Static, source-bound reproduction using the pinned request and retained 40-test asset; no shared-tool implementation was attempted.",
    }
    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": reproduced, "stage_count": len(stages), "disposition": report["proposed_request_disposition"]}))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
