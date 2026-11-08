#!/usr/bin/env python3
"""Reproduce one retained shared-tool request from its pinned assets.

The probe verifies the request/source identities, validates every retained asset,
and recomputes the two concrete lesson-ambiguity claims from the stored grids.
It does not implement or activate shared tooling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TICKET_ID = "ticket-33570482635e6a19"
REQUEST_ID = "review-803b0250fdb9ec1a:v0001:F1"
REQUEST_SHA256 = "efbf2e2a274ba9aa4f4d056908d6a21130321ff3a0e7a001abd74dba2ef31245"
REQUEST_SOURCE_SHA256 = "6c85823f8430070c462f9834d4b48778ffb8e1d58021ca748e366eefbc58d642"
ASSET_MANIFEST_SHA256 = "5b438e8675224732d54480fea5de0bfda79fa9a3b6b3154965c53c2d472732fa"
GENERATOR_SHA256 = "d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a"
RULE_HASH = "bb6a3cb8ba31"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_difference(a: list[list[int]], b: list[list[int]]) -> dict[str, Any] | None:
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        return {"kind": "shape", "left_shape": [len(a), len(a[0]) if a else 0], "right_shape": [len(b), len(b[0]) if b else 0]}
    for r, (row_a, row_b) in enumerate(zip(a, b)):
        for c, (x, y) in enumerate(zip(row_a, row_b)):
            if x != y:
                return {"kind": "cell", "row": r, "col": c, "intended": x, "rival": y}
    return None


def difference_count(a: list[list[int]], b: list[list[int]]) -> int | None:
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        return None
    return sum(x != y for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b))


def reproduce_pair(repo: Path, root: Path, task_id: str, ambiguity_name: str) -> dict[str, Any]:
    task_root = root / "checks" / "audit" / task_id
    ambiguity_path = task_root / ambiguity_name
    confirmation_path = task_root / "confirmation.json"
    ambiguity = read_json(ambiguity_path)
    confirmation = read_json(confirmation_path)

    train = ambiguity["train"]
    query = ambiguity["query"]
    intended_key = "intended_output" if "intended_output" in query else "intended_shape_output"
    intended = query[intended_key]
    rival = query["rival_output"]
    evidence_hashes = confirmation.get("evidence_sha256", {})

    checks = {
        "task_ids_match": ambiguity.get("task_id") == confirmation.get("task_id") == task_id,
        "generator_hashes_match": ambiguity.get("generator_sha256") == confirmation.get("generator_sha256"),
        "seed_matches": ambiguity.get("seed") == confirmation.get("seed") == query.get("seed"),
        "difficulty_matches": ambiguity.get("difficulty") == confirmation.get("difficulty") == query.get("difficulty"),
        "query_index_matches": query.get("sample_index") == confirmation.get("query_sample_index"),
        "all_demonstrations_fit_rival": bool(train) and all(row.get("rival_matches") is True for row in train),
        "query_refutes_rival": query.get("rival_matches") is False and intended != rival,
        "confirmation_fits_demos": confirmation.get("rival_fits_all_demonstrations") is True,
        "confirmation_refutes_query": confirmation.get("rival_disagrees_on_query") is True,
        "confirmation_racket_differs": confirmation.get("actual_racket_differs_from_rival_output") is True,
        "confirmation_rule_hash_matches": confirmation.get("rule_hash_matches_catalog") is True,
        "ambiguity_hash_retained": evidence_hashes.get(ambiguity_name) == sha256(ambiguity_path),
        "self_checks_clean_where_retained": all(row.get("self_check", []) == [] for row in train) and query.get("self_check", []) == [],
    }
    if task_id == "67e9e17efb62":
        checks["canonical_pairs_fit_position_rival"] = (
            ambiguity.get("rival_fits_all_canonical_pairs") is True
            and confirmation.get("rival_fits_all_canonical_pairs") is True
        )
        checks["racket_matches_intended"] = confirmation.get("actual_racket_equals_rule_mirror") is True
    else:
        checks["racket_matches_intended"] = confirmation.get("actual_racket_equals_intended_shape_output") is True

    return {
        "task_id": task_id,
        "ambiguity_path": ambiguity_path.relative_to(repo).as_posix(),
        "ambiguity_sha256": sha256(ambiguity_path),
        "confirmation_path": confirmation_path.relative_to(repo).as_posix(),
        "confirmation_sha256": sha256(confirmation_path),
        "executed_rule_hash": confirmation.get("executed_rule_hash"),
        "generator_sha256": confirmation.get("generator_sha256"),
        "rival_rule": ambiguity.get("rival_rule"),
        "demonstration_count": len(train),
        "query_sample_index": query.get("sample_index"),
        "first_query_difference": first_difference(intended, rival),
        "same_shape_difference_count": difference_count(intended, rival),
        "checks": checks,
        "reproduced": all(checks.values()),
        "limitations": ambiguity.get("limitations"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    work = args.work_root.resolve()
    repo = work / "repo"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    suggestions_path = repo / "REVIEW" / "suggestions.json"
    manifest_path = repo / "shared" / "tools" / "proposals" / "4535e6312cdf5c66" / "manifest.json"
    proposal_root = manifest_path.parent
    generator_path = repo / "generators" / "2a5919c40197" / "generator.py"

    source_checks = {
        "request_source_sha256": sha256(suggestions_path),
        "request_source_matches_pin": sha256(suggestions_path) == REQUEST_SOURCE_SHA256,
        "asset_manifest_sha256": sha256(manifest_path),
        "asset_manifest_matches_pin": sha256(manifest_path) == ASSET_MANIFEST_SHA256,
        "generator_sha256": sha256(generator_path),
        "generator_matches_pin": sha256(generator_path) == GENERATOR_SHA256,
    }
    if not all(v for k, v in source_checks.items() if k.endswith("matches_pin")):
        raise AssertionError(f"pinned identity mismatch: {source_checks}")

    suggestions = read_json(suggestions_path)
    matches = [row for row in suggestions["items"] if row.get("request_id") == REQUEST_ID]
    if len(matches) != 1:
        raise AssertionError(f"expected one request row, found {len(matches)}")
    request = matches[0]
    request_sha = canonical_sha(request)
    request_checks = {
        "canonical_request_sha256": request_sha,
        "request_matches_pin": request_sha == REQUEST_SHA256,
        "status": request.get("status"),
        "accepted": request.get("status") == "accepted",
        "generator_id": request.get("generator_id"),
        "generator_source_matches": request.get("source_sha256") == GENERATOR_SHA256,
        "manifest_reference_matches": request.get("assets_manifest", {}).get("sha256") == ASSET_MANIFEST_SHA256,
    }
    if not request_checks["request_matches_pin"]:
        raise AssertionError("request row identity drift")

    manifest = read_json(manifest_path)
    asset_checks = []
    for item in manifest["files"]:
        path = repo / item["path"]
        actual = {"path": item["path"], "exists": path.is_file()}
        if path.is_file():
            actual.update(
                bytes=path.stat().st_size,
                sha256=sha256(path),
                bytes_match=path.stat().st_size == item["bytes"],
                sha256_match=sha256(path) == item["sha256"],
            )
        asset_checks.append(actual)
    assets_valid = all(row.get("exists") and row.get("bytes_match") and row.get("sha256_match") for row in asset_checks)
    if not assets_valid:
        raise AssertionError("retained asset manifest did not verify")

    reproductions = [
        reproduce_pair(repo, proposal_root, "67e9e17efb62", "position_shortcut_ambiguity.json"),
        reproduce_pair(repo, proposal_root, "1a21a4a82b48", "size_shortcut_ambiguity.json"),
    ]
    reproduced = all(row["reproduced"] for row in reproductions)
    if not reproduced:
        raise AssertionError("one or more retained ambiguity claims did not reproduce")

    lesson_census_path = repo / "shared" / "tools" / "lesson_census.py"
    lesson_census_text = lesson_census_path.read_text(encoding="utf-8")
    exact_interface_markers = (
        "NUISANCE_AXES",
        "SAFE_PAIRED_OVERRIDES",
        "COUNTERFACTUAL_MUTATIONS",
        "nuisance_axis",
    )
    implemented_markers = [marker for marker in exact_interface_markers if marker in lesson_census_text]

    result = {
        "schema": "arcpuzzles-tool-reproduction-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "request": {
            "request_id": REQUEST_ID,
            "request_sha256": request_sha,
            "source_path": "repo/REVIEW/suggestions.json",
            "source_sha256": source_checks["request_source_sha256"],
            "status": request.get("status"),
            "reason": request.get("reason"),
            "text": request.get("text"),
        },
        "pinned_identity": {
            **source_checks,
            "rule_hash": RULE_HASH,
            "request_checks": request_checks,
            "manifest_scope": manifest.get("scope"),
            "runtime_approved": manifest.get("runtime_approved"),
        },
        "asset_verification": {
            "manifest_path": "repo/shared/tools/proposals/4535e6312cdf5c66/manifest.json",
            "manifest_sha256": source_checks["asset_manifest_sha256"],
            "file_count": len(asset_checks),
            "all_files_valid": assets_valid,
            "files": asset_checks,
        },
        "reproductions": reproductions,
        "conclusion": "All four retained assets match the pinned manifest. Both lesson windows reproduce the stated pattern: three demonstrations fit the task-local nuisance-conditioned rival, while the fourth/query output differs and the retained Racket confirmation agrees with the intended output. This validates the bounded evidence package, not prevalence or global counterfactual validity.",
        "implementation_check": {
            "lesson_census_path": "repo/shared/tools/lesson_census.py",
            "lesson_census_sha256": sha256(lesson_census_path),
            "current_behavior": "The shared census scores task-declared rivals and query rotations. No exact opt-in nuisance-axis/paired-override declaration marker from this request is present in the selected tool source.",
            "exact_interface_markers_found": implemented_markers,
            "implemented_as_requested": False,
            "limit": "Absence of these exact interface markers is a bounded source inspection, not proof that no adjacent or future mechanism could serve the same purpose.",
        },
        "proposed_disposition": {
            "status": "retain_open_accepted",
            "reason": "The request is already accepted for maintainer prioritization and its two concrete witnesses reproduce from retained assets, but the manifest says runtime_approved=false and the selected lesson census lacks the requested opt-in nuisance-axis/paired-override interface. Do not mark fulfilled or close as implemented.",
            "implementation_boundary": "Any future implementation should require task-declared lawful interventions, canonical Racket labels on both sides, source/rule/input-hash caching, and advisory treatment for auto-discovered axes. A concrete surviving rival/query pair may be blocking only under the task's declared domain and assembly policy.",
            "no_change": "No shared tool, admission rule, generator, approval, or audit disposition changed in this return.",
        },
        "limits": [
            "Reproduction uses retained source-bound assets; it does not rerun the old generators or Racket runtime because those source programs are not among the retained proposal files.",
            "The two witnesses establish existence, not frequency, corpus-wide value, or safety of every nuisance intervention.",
            "The audited task IDs and generator hashes differ from the ticket anchor generator; the anchor binds the request provenance, not the witness source bytes.",
            "No peer safety finding is created and no AUDIT.md section is warranted.",
        ],
        "new_racket_runs": 0,
        "new_model_jobs": 0,
        "shared_tool_changed": False,
    }

    result_path = out / "result.json"
    write_json(result_path, result)
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "assets_valid": assets_valid,
        "reproduced_witnesses": sum(row["reproduced"] for row in reproductions),
        "proposed_disposition": result["proposed_disposition"]["status"],
        "result": result_path.relative_to(work).as_posix(),
        "result_sha256": sha256(result_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
