#!/usr/bin/env python3
"""One bounded, source-bound reproduction probe for ticket-f2a160180086c138."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # WORK/
REPO = ROOT / "repo"
OUT = Path(__file__).resolve().parent / "verification.json"

REQUEST_ID = "review-7828727efa750acb:v0001:F2"
PINNED = {
    "request_source_sha256": "67fdad2e6b3cdd0fa6d8aeeff83afa2790f0fa67260178aab768276cae85e633",
    "request_sha256": "04ae5a5d00139648e6b1d18a3b22ce6610586ffd6a137806394428850e2a2f63",
    "assets_manifest_sha256": "189bfec5db90a3edab5f6d106b8094aee4d9173fe1c523ca1cae63b0db9310cf",
    "asset_sha256": "a798a79c40f967e4bb6bf83506fa36c9adda186cce94e82b05485459690399f8",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def line_number(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return index
    return None


def main() -> int:
    request_source = REPO / "REVIEW" / "suggestions.json"
    manifest_path = REPO / "shared" / "tools" / "proposals" / "48a2f096bb283428" / "manifest.json"
    checker_path = REPO / "shared" / "tools" / "check_generator_override_contract.py"
    cli_path = REPO / "src" / "arcpuzzles" / "cli.py"
    tests_path = REPO / "tests" / "test_override_reporting.py"

    suggestions = json.loads(request_source.read_text())
    matches = [item for item in suggestions["items"] if item.get("request_id") == REQUEST_ID]
    assert len(matches) == 1, f"expected one request record, found {len(matches)}"
    request = matches[0]

    assert sha256(request_source) == PINNED["request_source_sha256"]
    assert canonical_sha256(request) == PINNED["request_sha256"]
    assert request["status"] == "accepted"

    assert sha256(manifest_path) == PINNED["assets_manifest_sha256"]
    manifest = json.loads(manifest_path.read_text())
    assert manifest["request_id"] == REQUEST_ID
    assert len(manifest["files"]) == 1
    asset_meta = manifest["files"][0]
    asset_path = REPO / asset_meta["path"]
    assert sha256(asset_path) == asset_meta["sha256"] == PINNED["asset_sha256"]
    assert asset_path.stat().st_size == asset_meta["bytes"]

    report = json.loads(asset_path.read_text())
    root_causes = report["root_causes"]
    category_totals = Counter()
    for cause in root_causes:
        witness = cause.get("minimized_witness")
        assert isinstance(witness, dict) and witness.get("message")
        category_totals[cause["category"]] += cause["count"]

    assert report["draws_total"] == report["draws"] == 47_880
    assert report["finding_count"] == 5_332
    assert len(root_causes) == 27
    assert len(report["findings"]) == 27
    assert sum(cause["count"] for cause in root_causes) == report["finding_count"]
    assert dict(sorted(category_totals.items())) == report["finding_categories"]
    assert report["report_mode"] == "summary"
    assert report["findings_complete"] is False
    assert report["settings"]["full_results"] is False
    assert report["case_result_rows_total"] == report["case_result_rows_omitted"] == 1_596
    assert report["cases"] == []

    checker = checker_path.read_text()
    cli = cli_path.read_text()
    tests = tests_path.read_text()
    implementation = {
        "default_json_is_root_cause_summary": all(
            needle in checker
            for needle in (
                "audit_summary = not args.full_results and not args.compact_results",
                '"report_mode": "summary" if audit_summary',
                "rows = []  # root_causes retain exact minimized replay calls and counts",
            )
        ),
        "full_rows_require_full_results": (
            "--full-results retains every case" in checker
            and "default is root-cause summary" in cli
        ),
        "summary_regression_test_present": (
            'summary["report_mode"]=="summary"' in tests
            and 'len(summary["findings"])==len(full["root_causes"])' in tests
            and 'not summary["cases"]' in tests
        ),
        "console_still_foregrounds_raw_finding_count": (
            'f"override-contract: {status} {args.task_id}: {len(findings)} "' in checker
        ),
        "console_still_prints_per_seed_witnesses_by_default": (
            'print("  PER-SEED WITNESSES:")' in checker
            and 'for finding in list(findings)[: args.max_findings]:' in checker
        ),
        "console_prints_root_causes_first": (
            'f"  ROOT CAUSES ({len(root_causes)} groups' in checker
        ),
    }
    assert all(implementation.values())

    result = {
        "schema": "arcpuzzles-bounded-tool-reproduction-v1",
        "ticket_id": "ticket-f2a160180086c138",
        "request_id": REQUEST_ID,
        "status": "completed",
        "identity": {
            "request_source": str(request_source.relative_to(ROOT)),
            "request_source_sha256": sha256(request_source),
            "request_record_sha256": canonical_sha256(request),
            "assets_manifest": str(manifest_path.relative_to(ROOT)),
            "assets_manifest_sha256": sha256(manifest_path),
            "asset": str(asset_path.relative_to(ROOT)),
            "asset_sha256": sha256(asset_path),
            "checker_sha256": sha256(checker_path),
            "cli_sha256": sha256(cli_path),
            "reporting_tests_sha256": sha256(tests_path),
        },
        "reproduction": {
            "draws_total": report["draws_total"],
            "finding_count": report["finding_count"],
            "root_cause_count": len(root_causes),
            "root_cause_count_sum": sum(cause["count"] for cause in root_causes),
            "category_totals": dict(sorted(category_totals.items())),
            "minimized_witnesses": sum(bool(cause.get("minimized_witness")) for cause in root_causes),
            "directly_replayable_minimized_witnesses": sum(
                bool(cause.get("minimized_witness", {}).get("generate_call")) for cause in root_causes
            ),
            "report_mode": report["report_mode"],
            "retained_representative_findings": len(report["findings"]),
            "case_result_rows_total": report["case_result_rows_total"],
            "case_result_rows_omitted": report["case_result_rows_omitted"],
            "implementation_state": implementation,
            "source_lines": {
                "summary_mode": line_number(checker, "audit_summary = not args.full_results"),
                "root_causes_first": line_number(checker, "# ---- root causes FIRST"),
                "raw_count_header": line_number(checker, 'f"override-contract: {status} {args.task_id}: {len(findings)} "'),
                "per_seed_witnesses": line_number(checker, 'print("  PER-SEED WITNESSES:")'),
                "cli_full_results_help": line_number(cli, "default is root-cause summary"),
            },
        },
        "proposed_disposition": {
            "status": "accepted_narrowed",
            "summary": (
                "Keep the request accepted, but narrow the remaining work to human-facing console/aggregate ordering. "
                "The pinned report already defaults to summary mode, omits all 1,596 case rows, retains 27 root causes "
                "with minimized witnesses, and exposes full rows only behind --full-results. The console still leads with "
                "5,332 raw findings and prints per-seed witnesses by default; make category/root-cause totals primary and "
                "raw witnesses opt-in. No shared tooling change was made by this ticket."
            ),
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
