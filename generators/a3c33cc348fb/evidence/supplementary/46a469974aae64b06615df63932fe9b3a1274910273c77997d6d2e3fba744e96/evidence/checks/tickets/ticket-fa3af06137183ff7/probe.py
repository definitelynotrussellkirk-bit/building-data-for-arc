#!/usr/bin/env python3
"""Bounded count/privacy probe for pinned a3c33cc348fb parametric evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / "WORK"
TASK = WORK / "repo" / "generators" / "a3c33cc348fb"
EVIDENCE = TASK / "workspace" / "parametric" / "evidence"
RETAINED = EVIDENCE / "retained"
OUT = Path(__file__).resolve().parent / "report.json"

EXPECTED = {
    "generator.py": "fc9d54b672dcf95bf69009b7592d5793033df45d073c0c208ad05d4c16c1d478",
    "evidence/manifest.json": "a28e8e6db6170e9e1c5f64cb6871a3d2f99379f1dc6ceac2fc373f647a0efbbe",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = TASK / "generator.py"
    manifest_path = EVIDENCE / "manifest.json"
    report_path = RETAINED / "report.json"
    manifest = json.loads(manifest_path.read_text())
    retained_report = json.loads(report_path.read_text())

    public_rows = []
    for public_path in sorted((RETAINED / "public").glob("*.json")):
        payload = json.loads(public_path.read_text())
        exact_hash = sha256(public_path)
        stem = public_path.stem
        serialized = json.dumps(payload, sort_keys=True)
        public_rows.append(
            {
                "path": str(public_path.relative_to(WORK)),
                "bytes": public_path.stat().st_size,
                "sha256": exact_hash,
                "filename_stem": stem,
                "filename_is_exact_visible_sha256": stem == exact_hash,
                "train_count": len(payload.get("train", [])),
                "test_count": len(payload.get("test", [])),
                "all_queries_unlabeled": all(
                    set(query) == {"input"} for query in payload.get("test", [])
                ),
                "hidden_terms_absent": all(
                    term not in serialized
                    for term in (
                        "expansion_mode",
                        "bbox",
                        "corridor",
                        "program",
                        "seed",
                    )
                ),
            }
        )

    checks = {
        "generator_hash_matches_pin": sha256(source) == EXPECTED["generator.py"],
        "evidence_manifest_hash_matches_pin": (
            sha256(manifest_path) == EXPECTED["evidence/manifest.json"]
        ),
        "retained_report_passed": retained_report.get("status") == "pass",
        "two_episodes": retained_report.get("summary", {}).get("episodes") == 2,
        "sixteen_racket_applications": (
            retained_report.get("summary", {}).get("racket_rule_applications") == 16
        ),
        "eight_query_rotations": (
            retained_report.get("summary", {}).get("query_rotations") == 8
        ),
        "each_public_artifact_is_three_demo_one_query": all(
            row["train_count"] == 3 and row["test_count"] == 1
            for row in public_rows
        ),
        "public_queries_are_unlabeled": all(
            row["all_queries_unlabeled"] for row in public_rows
        ),
        "hidden_terms_absent_from_public_json": all(
            row["hidden_terms_absent"] for row in public_rows
        ),
        "public_filenames_are_not_exact_visible_hashes": all(
            not row["filename_is_exact_visible_sha256"] for row in public_rows
        ),
        "variant_remains_unapproved": manifest.get("variant_approved") is False,
        "no_production_parametric_api": (
            manifest.get("production_parametric_api") is False
        ),
    }
    if not public_rows:
        raise SystemExit("no retained public artifacts found")
    failed = [name for name, passed in checks.items() if not passed]
    result = {
        "schema": "supplementary-parameter-query-probe-v1",
        "ticket_id": "ticket-fa3af06137183ff7",
        "task_id": "a3c33cc348fb",
        "status": "passed" if not failed else "failed",
        "checks": checks,
        "failed_checks": failed,
        "public_artifacts": public_rows,
        "retained_summary": retained_report.get("summary", {}),
        "boundary_result": {
            "count_support": (
                "The retained evidence exercises four query rotations per episode, "
                "but each visible challenge contains three demonstrations and one query; "
                "it is not a four-simultaneous-query export."
            ),
            "privacy": (
                "The visible JSON omits the hidden mode, seed, program, and query answer."
            ),
            "identifier": (
                "The public filenames are opaque episode IDs, not SHA-256 hashes of the "
                "exact visible file bytes."
            ),
            "approval": (
                "The pinned manifest still marks the variant unapproved and exposes no "
                "production parametric API."
            ),
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "ticket_id": result["ticket_id"],
        "public_artifacts": len(public_rows),
        "train_counts": [row["train_count"] for row in public_rows],
        "test_counts": [row["test_count"] for row in public_rows],
        "exact_visible_hash_filenames": [
            row["filename_is_exact_visible_sha256"] for row in public_rows
        ],
    }, sort_keys=True))
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
