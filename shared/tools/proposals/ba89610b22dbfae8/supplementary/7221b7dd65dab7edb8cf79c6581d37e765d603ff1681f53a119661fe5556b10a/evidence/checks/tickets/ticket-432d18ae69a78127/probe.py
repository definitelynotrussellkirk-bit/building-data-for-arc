from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[3] / "repo"
PROPOSAL = REPO / "shared/tools/proposals/ba89610b22dbfae8"
SUMMARY = PROPOSAL / "checks/lesson-census.summary.json"
RETAINED = PROPOSAL / "checks/lesson-census.json"
MANIFEST = PROPOSAL / "manifest.json"
SUGGESTIONS = REPO / "REVIEW/suggestions.json"
LESSON_CENSUS = REPO / "src/arcpuzzles/lesson_census.py"
CLI = REPO / "src/arcpuzzles/cli.py"
REQUEST_ID = "review-f66d8e89d07cd028:v0001:F4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_request(data: object) -> dict:
    if isinstance(data, dict):
        if data.get("request_id") == REQUEST_ID:
            return data
        for value in data.values():
            try:
                return find_request(value)
            except LookupError:
                pass
    elif isinstance(data, list):
        for value in data:
            try:
                return find_request(value)
            except LookupError:
                pass
    raise LookupError(REQUEST_ID)


manifest = json.loads(MANIFEST.read_text())
summary = json.loads(SUMMARY.read_text())
request = find_request(json.loads(SUGGESTIONS.read_text()))
full_report = summary["full_report"]
recorded_path = Path(full_report["path"])
relative_candidates = [
    key for key in ("relative_path", "workspace_relative_path", "portable_path")
    if key in full_report
]
manifest_by_source = {row["source_member"]: row for row in manifest["files"]}
retained_row = manifest_by_source["checks/lesson-census.json"]
lesson_source = LESSON_CENSUS.read_text()
cli_source = CLI.read_text()

result = {
    "schema": "arcpuzzles-tool-request-reproduction-v1",
    "ticket_id": "ticket-432d18ae69a78127",
    "request_id": REQUEST_ID,
    "bindings": {
        "suggestions_sha256": sha256(SUGGESTIONS),
        "manifest_sha256": sha256(MANIFEST),
        "summary_sha256": sha256(SUMMARY),
        "retained_report_sha256": sha256(RETAINED),
        "generator_sha256": summary.get("source_binding", {}).get("generator_sha256"),
        "declared_rule_hash": summary.get("source_binding", {}).get("declared_rule_hash"),
    },
    "request": {
        "status": request.get("status"),
        "text_sha256": hashlib.sha256(request["text"].encode()).hexdigest(),
        "request_sha256_matches_ticket": hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest() == "66fb50e68add11e52f37a58193cbd5484079297279ddcd6924e3030f63e2cdf5",
    },
    "observed": {
        "recorded_full_report_path": full_report["path"],
        "recorded_path_is_absolute": recorded_path.is_absolute(),
        "recorded_path_exists_in_current_workspace": recorded_path.exists(),
        "portable_path_fields_present": relative_candidates,
        "retained_companion_exists": RETAINED.exists(),
        "retained_companion_workspace_relative_path": str(RETAINED.relative_to(REPO)),
        "retained_companion_hash_matches_recorded_full_report_hash": sha256(RETAINED) == full_report["sha256"],
        "retained_companion_is_intentionally_compacted": "selection" in retained_row,
        "manifest_preserves_original_full_report_hash": retained_row.get("source_member_sha256") == full_report["sha256"],
        "current_writer_accepts_only_full_report_path": "def census_companion(report, *, full_report_sha256, full_report_path, invocation):" in lesson_source,
        "current_cli_passes_resolved_absolute_path": "full_report_path=str(args.out.resolve())" in cli_source,
        "current_cli_records_absolute_cwd": "'cwd': str(Path.cwd())" in lesson_source,
    },
    "reproduction": {
        "confirmed": bool(
            recorded_path.is_absolute()
            and not recorded_path.exists()
            and not relative_candidates
            and "full_report_path=str(args.out.resolve())" in cli_source
        ),
        "portable_lookup_can_be_inferred_only_from_external_manifest": True,
        "note": (
            "The moved summary names only an extraction-specific absolute path. "
            "The proposal manifest preserves a compact retained companion and the original report hash, "
            "but the summary itself has no workspace-relative locator."
        ),
    },
    "proposed_disposition": {
        "status": "confirmed_actionable",
        "recommendation": (
            "Keep the accepted request open for shared-tool implementation. Add a workspace-relative "
            "full-report path to census companions (and gzip companion paths), while retaining the "
            "absolute run root only as optional diagnostics."
        ),
        "implementation_scope": [
            "src/arcpuzzles/lesson_census.py:census_companion",
            "src/arcpuzzles/cli.py:lesson-census companion construction",
            "tests covering packet relocation",
        ],
        "shared_code_changed_by_this_ticket": False,
    },
}

# The ticket pins these identities; fail the one allowed probe if they drift.
assert result["bindings"]["suggestions_sha256"] == "6c85823f8430070c462f9834d4b48778ffb8e1d58021ca748e366eefbc58d642"
assert result["bindings"]["manifest_sha256"] == "1dbc74f8b415f0f91d3b3605961f77bcb7241f90e6f49e2d2c14d01269ba6968"
assert result["bindings"]["generator_sha256"] == "3649031665011fb6e1cfb9b7a1532efc12bc9cb4996555661e564e2410c7ade4"
assert result["bindings"]["declared_rule_hash"] == "febf74c1fcfe"
assert result["reproduction"]["confirmed"]

out = Path(__file__).with_name("result.json")
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "ticket_id": result["ticket_id"],
    "confirmed": result["reproduction"]["confirmed"],
    "recorded_path_exists": result["observed"]["recorded_path_exists_in_current_workspace"],
    "portable_path_fields_present": result["observed"]["portable_path_fields_present"],
    "proposed_disposition": result["proposed_disposition"]["status"],
}, sort_keys=True))
