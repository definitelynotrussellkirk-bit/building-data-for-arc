#!/usr/bin/env python3
"""Bounded source-bound check of retained four-query/privacy evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
TASK = WORK / "repo/generators/7355dc4aa5e5"
EVIDENCE = TASK / "workspace/parametric/evidence/diagonal-radius-v1"
MANIFEST = TASK / "workspace/parametric/evidence/manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    report = json.loads((EVIDENCE / "report.json").read_text())
    rows = []
    for episode_row in report["episodes"]:
        private_path = EVIDENCE / episode_row["private_path"]
        public_path = EVIDENCE / episode_row["public_path"]
        private = json.loads(private_path.read_text())
        public = json.loads(public_path.read_text())
        rotations = private["rotations"]
        production = [row for row in rotations if row["is_production_query"]]
        public_query = public["test"]
        rows.append({
            "diagonal_radius": private["parameters"]["diagonal_radius"],
            "private_sha256_matches_report": sha256(private_path) == episode_row["private_sha256"],
            "public_sha256_matches_report": sha256(public_path) == episode_row["public_sha256"],
            "four_distinct_query_rotations": len(rotations) == 4 and {row["query_pair_index"] for row in rotations} == {0, 1, 2, 3},
            "three_demonstrations_per_rotation": all(len(row["demonstration_pair_indices"]) == 3 for row in rotations),
            "declared_rival_refuted_before_each_query": all(
                len(row["rivals"]) == 1
                and row["rivals"][0]["status"] == "refuted_by_demonstrations"
                and row["rivals"][0]["query_disagrees"] is True
                for row in rotations
            ),
            "one_production_projection": len(production) == 1 and len(public["train"]) == 3 and len(public_query) == 1,
            "public_query_answer_hidden": len(public_query) == 1 and set(public_query[0]) == {"input"},
            "public_train_labels_present": all(set(pair) == {"input", "output"} for pair in public["train"]),
            "production_query_matches_private_pair": (
                len(production) == 1
                and public_query[0]["input"] == private["pairs"][production[0]["query_pair_index"]]["input"]
            ),
        })

    boolean_checks = [
        value
        for row in rows
        for value in row.values()
        if isinstance(value, bool)
    ]
    summary = {
        "schema": "arcpuzzles-parameter-query-ticket-v1",
        "ticket_id": "ticket-4169c7e1d2de9350",
        "task_id": "7355dc4aa5e5",
        "generator_sha256": sha256(TASK / "generator.py"),
        "evidence_manifest_sha256": sha256(MANIFEST),
        "manifest_variant_approved": manifest["variant_approved"],
        "manifest_production_parametric_api": manifest["production_parametric_api"],
        "report_status": report["status"],
        "episode_checks": rows,
        "boundary_passed": all(boolean_checks),
        "scope": "retained evidence only: four private rotations and one answer-masked production projection per setting; no approval inference",
    }
    summary["status"] = "completed" if (
        summary["boundary_passed"]
        and summary["generator_sha256"] == manifest["generator_sha256"]
        and summary["evidence_manifest_sha256"] == "fbf26f419f74c21a21e44516000b7b6914b93a29e39490348197edadbcc12885"
        and summary["manifest_variant_approved"] is False
        and summary["manifest_production_parametric_api"] is False
    ) else "finding"
    out = Path(__file__).with_name("summary.json")
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
