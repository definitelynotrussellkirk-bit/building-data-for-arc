#!/usr/bin/env python3
"""Cross-check final ARCpuzzles evidence against the exact current source bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    repo = work / "repo"
    check = work / "checks/ad8f89160989"
    param = repo / "generators/ad8f89160989/workspace/parametric"

    tests = load(work / "checks/ad8f89160989-tests-final-v3/result.json")
    audit = load(param / "evidence/adversarial-final.json")
    manifest_path = param / "evidence/manifest.json"
    manifest = load(manifest_path)
    qualification_path = check / "qualification/qualification.json"
    execution_path = check / "qualification/execution.json"
    qualification = load(qualification_path)
    execution = load(execution_path)
    witness_path = check / "causal/witness.json"
    replay_path = check / "causal/replay.json"
    witness = load(witness_path)
    replay = load(replay_path)
    preview = load(check / "preview-verify.json")
    first_turn = load(check / "first-turn.json")
    public = load(check / "public-export-check.json")
    red = load(work / "checks/red-self-check-dimensions/command.json")
    green = load(work / "checks/green-self-check-dimensions/command.json")

    manifest_hashes = {
        row["path"]: sha256(repo / row["path"]) == row["sha256"]
        for row in manifest["files"]
    }
    qualification_hashes = {
        row["path"]: sha256(repo / row["path"]) == row["sha256"]
        for row in qualification["source_binding"]["files"]
    }
    generator_path = repo / "generators/ad8f89160989/generator.py"
    generator_text = generator_path.read_text(encoding="utf-8")
    version = re.search(r'^VERSION\s*=\s*"([^"]+)"', generator_text, re.MULTILINE)
    private_qualification = check / "preview/private/qualification.json"

    checks = {
        "generator_version_3_2_1": bool(version and version.group(1) == "3.2.1"),
        "manifest_all_file_hashes_current": all(manifest_hashes.values()),
        "qualification_all_file_hashes_current": all(qualification_hashes.values()),
        "manifest_generator_matches_current": manifest["generator_sha256"] == sha256(generator_path),
        "qualification_generator_matches_current": qualification["source_binding"]["generator_sha256"] == sha256(generator_path),
        "manifest_and_qualification_canonical_match": manifest["canonical_program_sha256"] == qualification["source_binding"]["canonical_program_sha256"],
        "witness_binding_matches_qualification": witness["source_binding"] == qualification["source_binding"],
        "replay_binding_matches_qualification": replay["source_binding"] == qualification["source_binding"],
        "replay_witness_hash_matches": replay["witness_sha256"] == sha256(witness_path),
        "qualification_execution_hash_matches": qualification["execution"]["sha256"] == sha256(execution_path),
        "preview_private_qualification_hash_matches": sha256(private_qualification) == sha256(qualification_path),
        "focused_tests_19_of_19": tests["passed"] is True and tests["test_counts"] == {"tests": 19, "failed": 0, "errors": 0, "skipped": 0, "passed": 19},
        "adversarial_audit_passed": audit["passed"] is True and audit["failures"] == [] and audit["seed_count"] == 96 and audit["episodes_checked"] == 192 and audit["labeled_pairs_checked"] == 1344,
        "protected_preflight_passed": execution["base_review"]["status"] == "passed" and execution["racket_evaluations"] == 40 and len(qualification["jobs"]) == 4,
        "owner_acceptance_not_claimed": qualification["owner_accepted"] is False and replay["owner_acceptance"] == "not_performed",
        "training_admission_not_claimed": qualification["training_admitted"] is False and replay["training_admitted"] is False,
        "causal_counterfactual_changes_output": len(witness["cases"]) == 1 and witness["cases"][0]["counterfactual_output"] != witness["cases"][0]["output"],
        "causal_replay_passed": replay["status"] == "reviewer_replayed" and replay["replay"]["status"] == "reviewer_replayed",
        "projection_verified": preview["status"] == "verified_projection" and preview["episodes"] == 4 and preview["views"] == 16,
        "first_turn_boundary_passed": first_turn["status"] == "passed" and first_turn["failures"] == [] and first_turn["invariance_checks"] == 24 and first_turn["public_views_checked"] == 16,
        "saved_public_export_passed": public["status"] == "passed" and public["findings"] == [] and public["files_checked"] == 16,
        "dimension_regression_was_red_then_green": red["returncode"] != 0 and green["returncode"] == 0,
        "packaged_audit_copy_matches_source": sha256(check / "adversarial-final.json") == sha256(param / "evidence/adversarial-final.json"),
        "packaged_finding_copy_matches_source": sha256(check / "shortcut-finding-and-repair.json") == sha256(param / "evidence/shortcut-finding-and-repair.json"),
        "packaged_manifest_copy_matches_source": sha256(check / "source-manifest.json") == sha256(manifest_path),
    }
    failures = [name for name, passed in checks.items() if not passed]
    report = {
        "schema": "ad8f89160989-final-consistency-v1",
        "task_id": "ad8f89160989",
        "status": "passed" if not failures else "failed",
        "checks": checks,
        "failures": failures,
        "hashes": {
            "generator_sha256": sha256(generator_path),
            "manifest_sha256": sha256(manifest_path),
            "qualification_sha256": sha256(qualification_path),
            "witness_sha256": sha256(witness_path),
            "replay_sha256": sha256(replay_path),
        },
        "manifest_file_count": len(manifest_hashes),
        "qualification_bound_file_count": len(qualification_hashes),
        "limits": "Static cross-artifact consistency and retained finite check status only; no owner acceptance or training admission.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failures": failures, "hashes": report["hashes"]}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
