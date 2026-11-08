#!/usr/bin/env python3
"""One source-bound probe of the existing audit-preset summary writer.

The controller input is reconstructed from the pinned historical console and
battery summary. No task tests, semantic gate, generator, or reference runtime
are executed. The exact current issued helper is invoked once; native retained
evidence must remain unchanged. This is a summary-function reproduction only.
"""
from __future__ import annotations

import argparse
import ast
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import time


TICKET = "ticket-b6e967a67119ff71"
AUTHORING_START_EPOCH = 1792752677.8312328


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", required=True, type=Path)
    parser.add_argument("--work-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("result.json"))
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    helper = args.work_root / "repo/generators/34569d6118b3/workspace/tools/package_sparse_return.py"
    spec = importlib.util.spec_from_file_location("verified_packet_imports", helper)
    packaging = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packaging)
    manifest, issued, archive_sha = packaging.read_issued(args.original_zip)
    assignment = json.loads((args.work_root / "AUDIT_ASSIGNMENT.json").read_text())
    assert assignment["packet_id"] == packaging.sha(issued["PACKET-MANIFEST.json"])
    ticket = next(t for t in assignment["tickets"] if t["ticket_id"] == TICKET)
    assert ticket["type"] == "tool_reproduction"
    request_source = ticket["request_source"]
    assert packaging.sha(issued[request_source["path"]]) == request_source["sha256"]
    request = next(r for r in json.loads(issued[request_source["path"]])["items"]
                   if r["request_id"] == ticket["request_id"])
    assert packaging.sha(packaging.canonical(request)) == ticket["request_sha256"]
    asset_pin = ticket["assets_manifest"]
    asset_bytes = issued[asset_pin["path"]]
    assert packaging.sha(asset_bytes) == asset_pin["sha256"]
    assets = json.loads(asset_bytes)
    assert assets["request_id"] == ticket["request_id"]
    bound = []
    payload = {}
    for row in assets["files"]:
        name = "repo/" + row["path"]
        raw = issued[name]
        assert len(raw) == row["bytes"] and packaging.sha(raw) == row["sha256"]
        bound.append({"path": name, "sha256": row["sha256"], "bytes": len(raw)})
        payload[row["source_member"]] = raw
    console_name = next(n for n in payload if n.endswith(".console.log"))
    summary_name = next(n for n in payload if n.endswith("_battery_summary.json"))
    console = payload[console_name].decode()
    historical = json.loads(payload[summary_name])
    controller = next(json.loads(line) for line in console.splitlines() if line.startswith('{"task_id"'))
    assert controller["stage"] == "audit" and controller["exit_code"] == 0 and controller["passed"] is True
    assert historical["task"] == controller["task_id"]
    assert historical["verdict"] == "incomplete" and historical["counts"]["pending"] == 11
    tests_passed = int(re.search(r"(\d+) passed in", console).group(1))
    semantic = historical["stages"]["semantic_gate"]
    assert semantic["status"] == "green" and semantic["exit"] == 0
    runtime_name = "repo/src/arcpuzzles/runtime.py"
    runtime_bytes = issued[runtime_name]
    assert (args.work_root / runtime_name).read_bytes() == runtime_bytes
    source_tree = ast.parse(runtime_bytes)
    function = next(n for n in source_tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "_write_audit_summary")
    check_function = next(n for n in source_tree.body if isinstance(n, ast.FunctionDef)
                          and n.name == "_check")
    hooks = [n.lineno for n in ast.walk(check_function)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "_write_audit_summary"]
    assert hooks
    result = {"task_id": historical["task"], "stage": "audit", "status": "completed",
              "passed": True, "runtime_manifest": {"files": [{
                  "library_path": f"generators/{historical['task']}/generator.py",
                  "sha256": historical["generator_file_sha256"]}]},
              "audit_stages": {
                  "task_tests": {"status": "completed", "passed": True, "exit_code": 0,
                                 "timed_out": False, "test_status": "executed",
                                 "test_counts": {"tests": tests_passed, "passed": tests_passed,
                                                 "failed": 0, "errors": 0, "skipped": 0}},
                  "semantic_gate": {"status": "completed", "passed": True, "exit_code": 0,
                                    "timed_out": False, "semantic_status": semantic["status"]}}}
    input_controller = copy.deepcopy(result)
    with tempfile.TemporaryDirectory(prefix="audit-summary-ticket-") as temporary:
        root = Path(temporary)
        native_path = root / f"checks/{historical['task']}_audit_battery_summary.json"
        native_path.parent.mkdir()
        native_path.write_bytes(payload[summary_name])
        with packaging.issued_imports(issued):
            from arcpuzzles.runtime import _write_audit_summary
            _write_audit_summary(root, result)  # The sole targeted function invocation.
        summary = result["audit_summary"]
        assert summary["verdict"] == "passed" and summary["preset_complete"] is True
        assert summary["expected_stages"] == ["task_tests", "semantic_gate"]
        assert summary["completed_stages"] == ["task_tests", "semantic_gate"]
        assert native_path.read_bytes() == payload[summary_name]
        written = json.loads((root / f"checks/{historical['task']}_audit_summary.json").read_text())
        assert written == summary
    elapsed = time.monotonic() - started
    assert elapsed <= 120
    receipt = {
        "schema": "arcpuzzles-tool-reproduction-observation-v1", "ticket_id": TICKET,
        "status": "completed", "consumer": ticket["consumer"],
        "request_id": ticket["request_id"], "request_sha256": ticket["request_sha256"],
        "request_source": request_source, "assets_manifest": asset_pin, "verified_assets": bound,
        "original_zip_sha256": archive_sha, "packet_id": assignment["packet_id"],
        "generator_binding": {k: ticket[k] for k in ("task_id", "generator_sha256", "rule_task_id", "rule_hash")},
        "current_runtime_source": {"path": runtime_name, "sha256": packaging.sha(runtime_bytes),
                                   "function": "_write_audit_summary", "first_line": function.lineno,
                                   "last_line": function.end_lineno, "final_check_hook_lines": sorted(hooks)},
        "probe_source_sha256": packaging.sha(Path(__file__).read_bytes()),
        "package_helper_sha256": packaging.sha(helper.read_bytes()),
        "command": {"cwd": "WORK", "argv": [sys.executable, *sys.argv], "exit_status": 0},
        "targeted_probe_count": 1, "targeted_probe_elapsed_seconds": elapsed,
        "authoring_elapsed_minutes_through_probe": (time.time() - AUTHORING_START_EPOCH) / 60,
        "input_provenance": "Controller data reconstructed from the two pinned historical assets; no fresh task-test or semantic-gate execution.",
        "input_controller": input_controller,
        "historical_native_verdict": historical["verdict"],
        "historical_native_pending_stages": historical["counts"]["pending"],
        "observed_current_preset_summary": summary, "native_battery_bytes_unchanged": True,
        "proposed_request_disposition": "implemented",
        "disposition_reason": "Current issued code writes a dedicated two-stage audit summary with a passed scoped verdict while preserving the incomplete twelve-stage battery summary, satisfying the request's dedicated-summary alternative.",
        "limits": ["One current summary-function invocation, plus static confirmation of final-check hooks.",
                   "Historical example tests, semantic gate, Racket labels, and end-to-end audit were not rerun.",
                   "No shared source or request disposition was changed; no generator safety finding or runtime qualification is claimed."]}
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "completed", "receipt": str(args.out),
                      "probe_elapsed_seconds": elapsed, "proposed_disposition": "implemented",
                      "preset_verdict": summary["verdict"], "native_verdict": historical["verdict"]}, sort_keys=True))


if __name__ == "__main__":
    main()
