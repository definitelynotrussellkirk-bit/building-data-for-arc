#!/usr/bin/env python3
"""Verify the final source/evidence binding for review-fdc6a9b2aee6af87."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

WORK = Path(__file__).resolve().parents[1]
REPO = WORK / "repo"
TASK = REPO / "generators/a9c4475d7cda"
EXPECTED_GENERATOR_SHA256 = "1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    base = json.loads(
        (REPO / "shared/data/base/solutions/training/6773b310__a9c4475d7cda.json").read_text()
    )
    canonical = base["racket_target"]["target_code"]
    threshold2 = (TASK / "workspace/parametric/programs/threshold-2.rkt").read_text()
    manifest_path = TASK / "workspace/parametric/evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text())

    rows = []
    for declared in manifest["files"]:
        path = REPO / declared["path"]
        actual = sha256(path)
        rows.append(
            {
                "path": declared["path"],
                "expected_sha256": declared["sha256"],
                "actual_sha256": actual,
                "ok": actual == declared["sha256"],
            }
        )

    generator_sha256 = sha256(TASK / "generator.py")
    report = {
        "schema": "a9c4475d7cda-final-binding-v1",
        "task_id": "a9c4475d7cda",
        "generator_sha256": generator_sha256,
        "generator_expected_sha256": EXPECTED_GENERATOR_SHA256,
        "generator_unchanged": generator_sha256 == EXPECTED_GENERATOR_SHA256,
        "canonical_default_byte_exact": threshold2 == canonical,
        "evidence_manifest_sha256": sha256(manifest_path),
        "evidence_files": rows,
        "evidence_files_all_match": all(row["ok"] for row in rows),
        "audit_md_absent": not (WORK / "AUDIT.md").exists(),
        "results_completion_state": json.loads((WORK / "RESULTS.json").read_text())[
            "completion_state"
        ],
    }
    required = (
        report["generator_unchanged"],
        report["canonical_default_byte_exact"],
        report["evidence_files_all_match"],
        report["audit_md_absent"],
        report["results_completion_state"] == "complete",
    )
    if not all(required):
        raise SystemExit(json.dumps(report, sort_keys=True))

    (WORK / "checks/final-binding.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "evidence_files"},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
