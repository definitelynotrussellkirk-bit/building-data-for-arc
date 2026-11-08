#!/usr/bin/env python3
"""Bounded count/privacy inspection of pinned 27b865c5f43a parameter evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "27b865c5f43a"
TICKET_ID = "ticket-6a1f2ccb735751c0"
MANIFEST = REPO / "generators" / TASK / "workspace" / "parametric" / "evidence" / "manifest.json"
MANIFEST_SHA256 = "0673f178d57f4ce029714e80e0690d8430830ef830862932de4c3c72520a410b"
GENERATOR = REPO / "generators" / TASK / "generator.py"
GENERATOR_SHA256 = "495ba0e0517cf001c44dfcd69c0ca56e98e4bc767fdcfd76e56e726424be377e"
OUT = HERE / "inspection.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    assert sha256_file(MANIFEST) == MANIFEST_SHA256
    assert sha256_file(GENERATOR) == GENERATOR_SHA256
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["task_id"] == TASK
    assert manifest["generator_sha256"] == GENERATOR_SHA256
    assert manifest["production_parametric_api"] is False
    assert manifest["variant_approved"] is False

    verified_files = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"]
        verified_files.append({
            "path": path.relative_to(REPO).as_posix(),
            "sha256": actual,
            "bytes": path.stat().st_size,
        })

    challenge_rows = []
    for row in manifest["files"]:
        if "/challenge-gap-" not in row["path"]:
            continue
        path = REPO / row["path"]
        challenge = json.loads(path.read_text(encoding="utf-8"))
        train = challenge.get("train")
        test = challenge.get("test")
        assert type(train) is list and type(test) is list
        assert all(set(pair) == {"input", "output"} for pair in train)
        assert all(set(pair) == {"input"} for pair in test)
        visible_bytes = public_challenge_bytes(challenge)
        content_id = public_challenge_id(challenge)
        expected_name = f"challenge-{content_id}.json"
        raw = path.read_text(encoding="utf-8")
        forbidden_body_terms = [
            term for term in ("gallery_gap", "episode_seed", "racket", "parameters", "query_output")
            if term in raw
        ]
        challenge_rows.append({
            "path": path.relative_to(REPO).as_posix(),
            "stored_filename": path.name,
            "demonstrations": len(train),
            "queries": len(test),
            "query_inputs_only": True,
            "forbidden_body_terms": forbidden_body_terms,
            "body_private_fields_absent": not forbidden_body_terms,
            "visible_content_id": content_id,
            "content_addressed_filename": path.name == expected_name,
            "expected_content_addressed_filename": expected_name,
            "stored_bytes_equal_canonical_visible_bytes": path.read_bytes() == visible_bytes,
        })

    assert len(challenge_rows) == 3
    assert all(row["demonstrations"] == 4 for row in challenge_rows)
    assert all(row["queries"] == 1 for row in challenge_rows)
    assert all(row["body_private_fields_absent"] for row in challenge_rows)
    assert all(not row["content_addressed_filename"] for row in challenge_rows)

    report = {
        "schema": "arcpuzzles-parameter-queries-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "support_gap_observed",
        "task_id": TASK,
        "source_binding": {
            "evidence_manifest_sha256": MANIFEST_SHA256,
            "generator_sha256": GENERATOR_SHA256,
            "canonical_rule_hash": manifest["canonical_rule_hash"],
            "return_id": manifest["return_id"],
        },
        "verified_files": verified_files,
        "boundary_checked": "query_count_and_public_identifier_privacy",
        "challenge_rows": challenge_rows,
        "assessment": {
            "body_redaction": "pass",
            "four_query_support": "missing_retained_evidence_has_one_query_per_setting",
            "public_identifier_privacy": "needs_followup_setting_is_exposed_in_filename_and_name_is_not_visible-content-addressed",
            "variant_approval": "not_assessed_and_remains_false",
        },
        "limitations": [
            "This is a static inspection of the exact retained evidence; the prototype was not regenerated.",
            "The observation is support/tooling feedback, not a peer safety finding.",
            "No production API, variant approval, or training admission is implied.",
        ],
        "command": "python3 review.py run python3 ../checks/tickets/ticket-6a1f2ccb735751c0/inspect.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "challenges": len(challenge_rows),
        "queries_each": [row["queries"] for row in challenge_rows],
        "out": str(OUT),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
