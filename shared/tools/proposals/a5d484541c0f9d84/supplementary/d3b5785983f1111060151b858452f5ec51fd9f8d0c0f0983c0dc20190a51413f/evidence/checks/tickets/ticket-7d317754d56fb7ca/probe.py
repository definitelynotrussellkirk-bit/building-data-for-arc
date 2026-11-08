#!/usr/bin/env python3
"""Reproduce the pinned tool-request asset state without modifying shared tools."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TICKET_ID = "ticket-7d317754d56fb7ca"
REQUEST_ID = "review-3081544e90ba3334:v0001:F2"
PROBE_SEED = "cac7e237156f3730459ea503af06e0a5e0bcff071ac5b4486b958b6260471e53"
EXPECTED = {
    "assets_manifest_sha256": "1af29a79ccedc3e758cc139ce73c6d8b66167ae17d0df70569892c2cfab51734",
    "request_source_sha256": "67fdad2e6b3cdd0fa6d8aeeff83afa2790f0fa67260178aab768276cae85e633",
    "request_sha256": "524d7489c1e5d62a153414c0bba166fccc1f212ad11a9344a0c3661cadd4ff70",
    "generator_sha256": "aa9940392c76ce0e2006361be2bb1c4e874ea6bb0969d96106a62783941744af",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    work = Path(__file__).resolve().parents[3]
    proposal = work / "repo/shared/tools/proposals/a5d484541c0f9d84"
    manifest_path = proposal / "manifest.json"
    suggestions_path = work / "repo/REVIEW/suggestions.json"
    generator_path = work / "repo/generators/646eeb47599b/generator.py"

    suggestions = json.loads(suggestions_path.read_text(encoding="utf-8"))
    matches = [row for row in suggestions.get("items", []) if row.get("request_id") == REQUEST_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one pinned request, found {len(matches)}")
    request = matches[0]
    request_sha = hashlib.sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed_files = []
    for row in manifest.get("files", []):
        path = work / "repo" / row["path"]
        listed_files.append(
            {
                "path": path.relative_to(work).as_posix(),
                "exists": path.is_file(),
                "expected_sha256": row["sha256"],
                "actual_sha256": sha256(path) if path.is_file() else None,
                "hash_matches": path.is_file() and sha256(path) == row["sha256"],
            }
        )

    source_manifest_relative = manifest.get("source_proposal", {}).get("manifest")
    source_manifest = work / "repo" / source_manifest_relative if source_manifest_relative else None
    checks = {
        "assets_manifest_hash": sha256(manifest_path) == EXPECTED["assets_manifest_sha256"],
        "request_source_hash": sha256(suggestions_path) == EXPECTED["request_source_sha256"],
        "request_hash": request_sha == EXPECTED["request_sha256"],
        "generator_hash": sha256(generator_path) == EXPECTED["generator_sha256"],
        "listed_assets_match": bool(listed_files) and all(row["hash_matches"] for row in listed_files),
        "source_proposal_manifest_present": bool(source_manifest and source_manifest.is_file()),
        "assignment_verified": manifest.get("assignment_verified") is True,
        "runtime_approved": manifest.get("runtime_approved") is True,
    }
    report = {
        "schema": "arcpuzzles-tool-reproduction-ticket-v1",
        "ticket_id": TICKET_ID,
        "probe_seed": PROBE_SEED,
        "request_id": REQUEST_ID,
        "request_status": request.get("status"),
        "request_reason": request.get("reason"),
        "request_text": request.get("text"),
        "pinned_hashes": EXPECTED,
        "observed": {
            "assets_manifest": manifest_path.relative_to(work).as_posix(),
            "request_source": suggestions_path.relative_to(work).as_posix(),
            "generator": generator_path.relative_to(work).as_posix(),
            "source_proposal_manifest": source_manifest.relative_to(work).as_posix() if source_manifest else None,
            "listed_files": listed_files,
            "manifest_scope": manifest.get("scope"),
            "assignment_verified": manifest.get("assignment_verified"),
            "runtime_approved": manifest.get("runtime_approved"),
        },
        "checks": checks,
        "reproduced_state": "assets_only_unverified" if all(
            checks[key] for key in (
                "assets_manifest_hash",
                "request_source_hash",
                "request_hash",
                "generator_hash",
                "listed_assets_match",
            )
        ) and not checks["source_proposal_manifest_present"]
        and not checks["assignment_verified"]
        and not checks["runtime_approved"] else "unexpected",
        "proposed_disposition": {
            "status": "needs_evidence",
            "action": "retain_as_unverified_request_not_implementation",
            "reason": (
                "The pinned hashes and feedback asset reproduce, but the source proposal manifest is absent and "
                "the retained manifest explicitly records assignment_verified=false and runtime_approved=false. "
                "No runnable shared template or green verification receipt is present."
            ),
            "possible_reference": (
                "The task-local 78e3f26e92aa parametric prototype in this return demonstrates the requested "
                "public/private writer and verifier pattern, but it is not a shared-tool implementation or admission."
            ),
        },
    }
    out = Path(__file__).with_name("probe.json")
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "reproduced_state": report["reproduced_state"]}, sort_keys=True))
    return 0 if report["reproduced_state"] == "assets_only_unverified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
