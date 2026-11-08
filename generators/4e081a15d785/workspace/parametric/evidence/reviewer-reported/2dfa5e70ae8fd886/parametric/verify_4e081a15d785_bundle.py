#!/usr/bin/env python3
"""Fresh source-bound verifier for the retained 4e081a15d785 prototype bundle."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("compression_axes_prototype", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_manifest(evidence: Path) -> dict[str, Any]:
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    declared = {row["path"]: row["sha256"] for row in manifest["files"]}
    actual = {
        path.relative_to(evidence).as_posix(): sha256(path)
        for path in evidence.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual != declared:
        missing = sorted(set(declared) - set(actual))
        extra = sorted(set(actual) - set(declared))
        changed = sorted(path for path in set(actual) & set(declared) if actual[path] != declared[path])
        raise AssertionError({"manifest_missing": missing, "manifest_extra": extra, "manifest_changed": changed})
    return {"files_checked": len(actual), "manifest_sha256": sha256(evidence / "manifest.json")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--adversarial", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    evidence = args.evidence.resolve()
    prototype_path = repo / "generators/4e081a15d785/workspace/parametric/prototype.py"
    test_path = repo / "generators/4e081a15d785/tests/test_parametric_compression_axes.py"
    generator_path = repo / "generators/4e081a15d785/generator.py"
    prototype = load_module(prototype_path)

    live = prototype.verify_evidence(evidence, root=repo)
    if live["status"] != "pass" or live["live_labels_checked"] != 27:
        raise AssertionError(f"unexpected live verification: {live}")

    report = json.loads((evidence / "report.json").read_text(encoding="utf-8"))
    expected_sources = {
        "prototype": sha256(prototype_path),
        "focused_test": sha256(test_path),
        "production_generator": sha256(generator_path),
    }
    for key, digest in expected_sources.items():
        if report["sources"][key]["sha256"] != digest:
            raise AssertionError(f"stale source hash for {key}")
    if report["status"] != "proposed_unapproved":
        raise AssertionError("prototype approval status changed")
    if report["parameter"] != {
        "name": "compression_axes",
        "allowed_values": ["both", "rows", "columns"],
        "original_default": "both",
        "input_constraints": (
            "Every authored episode input has at least one adjacent duplicate whole "
            "row and column so demonstrations identify the selected axis behavior."
        ),
    }:
        raise AssertionError("parameter declaration changed")
    if report["counts"] != {
        "episodes": 3,
        "settings_exercised": 3,
        "demonstrations": 9,
        "queries": 12,
        "ambiguous_parameter_rivals": 0,
    }:
        raise AssertionError(f"unexpected report counts: {report['counts']}")

    public_checks = []
    for row in report["episodes"]:
        path = evidence / row["public_path"]
        digest = sha256(path)
        if digest != row["public_id"] or path.name != f"challenge-{digest}.json":
            raise AssertionError(f"public name/hash mismatch: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if len(payload["train"]) != 3 or len(payload["test"]) != 4:
            raise AssertionError(f"unexpected public counts: {path}")
        if any("output" in item for item in payload["test"]):
            raise AssertionError(f"query output leaked: {path}")
        public_checks.append({"path": row["public_path"], "sha256": digest})

    adversarial = json.loads(args.adversarial.read_text(encoding="utf-8"))
    if adversarial.get("status") != "pass" or any(
        value.get("status") != "pass" for value in adversarial.get("surfaces", {}).values()
    ):
        raise AssertionError("adversarial evidence is not fully passing")

    results = json.loads(args.results.read_text(encoding="utf-8"))
    tickets = results.get("supplementary_tickets")
    if not isinstance(tickets, list) or len(tickets) != 2:
        raise AssertionError("RESULTS.json must contain exactly two ticket rows")
    if {(row["ticket_id"], row["status"]) for row in tickets} != {
        ("ticket-485745f9689b7127", "completed"),
        ("ticket-8e7311626482b984", "completed"),
    }:
        raise AssertionError("supplementary ticket statuses changed")
    for command in results.get("verification_commands", []):
        for rel in command.get("evidence_paths", []):
            if not (repo.parent / rel).is_file():
                raise AssertionError(f"missing declared evidence path: {rel}")

    summary = {
        "schema": "arcpuzzles-compression-axes-final-verification-v1",
        "status": "pass",
        "task_id": "4e081a15d785",
        "source_hashes": expected_sources,
        "manifest": check_manifest(evidence),
        "live_racket": live,
        "public_challenges": public_checks,
        "adversarial_surfaces": sorted(adversarial["surfaces"]),
        "supplementary_tickets": [
            {"ticket_id": row["ticket_id"], "status": row["status"]} for row in tickets
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "live_labels_checked": live["live_labels_checked"],
        "manifest_files_checked": summary["manifest"]["files_checked"],
        "public_challenges_checked": len(public_checks),
        "tickets_checked": len(tickets),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
