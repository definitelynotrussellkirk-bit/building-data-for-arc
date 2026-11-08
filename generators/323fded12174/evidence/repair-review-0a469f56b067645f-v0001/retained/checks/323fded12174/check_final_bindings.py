#!/usr/bin/env python3
"""Read-only final binding comparison; no owner acceptance is performed."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from check_export_integrity import inspect, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--checks", type=Path, required=True)
    args = parser.parse_args()
    repo, checks = args.repo.resolve(), args.checks.resolve()
    execution_path = checks / "examples-report.json"
    audit_path = checks / "audit-final/private/audit.json"
    report = inspect(repo, checks / "examples", execution_path, audit_path)
    report["schema"] = "arcpuzzles-task-final-binding-comparison-v1"
    findings = report["findings"]

    def require(condition, detail):
        if not condition:
            findings.append(detail)

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def verify_sources(records, label):
        for record in records:
            path = repo / record["path"]
            require(path.resolve().is_relative_to(repo) and path.is_file()
                    and not path.is_symlink() and digest(path) == record["sha256"],
                    f"{label} source hash differs: {record['path']}")
            if "bytes" in record:
                require(path.stat().st_size == record["bytes"], f"{label} file size differs: {record['path']}")

    execution = read_json(execution_path)
    qualification_path = checks / "qualification/qualification.json"
    qualification_execution_path = checks / "qualification/execution.json"
    qualification = read_json(qualification_path)
    qualified_execution = read_json(qualification_execution_path)
    binding = qualification["source_binding"]
    require(qualification["status"] == "qualified" and qualification["training_admitted"] is False,
            "Qualification status/admission flag differs")
    require(qualification["execution"]["sha256"] == digest(qualification_execution_path),
            "Qualification execution hash differs")
    require(qualified_execution["racket"] == execution["racket"],
            "Qualification and export Racket identities differ")
    verify_sources(binding["files"], "qualification")
    executors = [{"path": "src/arcpuzzles/" + name, "sha256": sha} for name, sha in binding["executor"].items()]
    verify_sources(executors, "qualification executor")
    qualified_sources = {row["path"]: row["sha256"] for row in binding["files"] + executors}
    common = sorted(set(execution["source_sha256"]) & set(qualified_sources))
    require(all(execution["source_sha256"][name] == qualified_sources[name] for name in common),
            "Qualification and export source bindings differ")
    example_rows = [json.loads(line) for line in (checks / "examples/private/metadata.jsonl").read_text().splitlines()]
    for row in example_rows:
        example = row["episode"]
        matches = [item for item in qualified_execution["episodes"]
                   if item["seed"] == example["seed"] and item["settings"] == example["settings"]]
        require(len(matches) == 1 and all(matches[0][key] == example[key]
                for key in ("train", "test", "program", "program_sha256")),
                "Exported episode differs from corresponding qualified episode")

    inventory_path = repo / "generators" / execution["task_id"] / "workspace/parametric/evidence/manifest.json"
    inventory = read_json(inventory_path)
    verify_sources(inventory["files"], "prototype inventory")
    require(inventory["limits"] == qualification["contract"]["limits"], "Inventory and qualification limits differ")
    require(inventory["canonical_program_sha256"] == binding["canonical_program_sha256"]
            and inventory["generator_sha256"] == binding["generator_sha256"],
            "Inventory and qualification canonical/production hashes differ")
    require(inventory["variant_approved"] is False and inventory["training_admitted"] is False,
            "Inventory must retain pending approval and no training admission")

    replay_path, witness_path = checks / "causal/replay.json", checks / "causal/witness.json"
    replay, witness = read_json(replay_path), read_json(witness_path)
    require(replay["status"] == replay["replay"]["status"] == "reviewer_replayed", "Causal replay status differs")
    require(replay["qualification_sha256"] == digest(qualification_path), "Causal qualification hash differs")
    require(replay["witness_sha256"] == digest(witness_path), "Causal witness hash differs")
    require(replay["source_binding"] == witness["source_binding"] == binding,
            "Causal and qualification source bindings differ")
    require(replay["construction"]["racket"] == replay["replay"]["racket"] == execution["racket"],
            "Causal, qualification, and export Racket identities differ")
    require(witness["racket"].get("backend") == "racket" and witness["racket"].get("protected") is True
            and all(execution["racket"].get(key) == value for key, value in witness["racket"].items()),
            "Causal witness runtime summary differs from its fully identified replay")
    require(replay["owner_acceptance"] == "not_performed" and replay["training_admitted"] is False,
            "Causal approval/admission flags differ")

    report.update({
        "status": "failed" if findings else "passed",
        "qualification": {
            "status": qualification["status"], "episodes": len(qualified_execution["episodes"]),
            "racket_evaluations": qualified_execution["racket_evaluations"],
            "source_files_checked": len(binding["files"]), "executor_files_checked": len(executors),
            "shared_export_sources_checked": len(common),
        },
        "prototype_inventory": {
            "files_checked": len(inventory["files"]), "verification_status": inventory["verification_status"],
            "builder_executed_checks": inventory["builder_executed_checks"], "variant_approved": inventory["variant_approved"],
        },
        "causal": {
            "status": replay["status"], "witnesses": len(witness["cases"]),
            "construction_evaluations": replay["construction"]["evaluations"],
            "replay_evaluations": replay["replay"]["evaluations"], "owner_acceptance": replay["owner_acceptance"],
        },
        "artifact_sha256": {str(path.relative_to(checks) if path.is_relative_to(checks) else path.relative_to(repo)): digest(path)
                            for path in (execution_path, audit_path, qualification_path, qualification_execution_path,
                                         inventory_path, replay_path, witness_path,
                                         Path(__file__).resolve(), Path(__file__).with_name("check_export_integrity.py").resolve())},
        "scope": "Exact current-source, saved-file, report-hash and runtime-identity comparisons. Protected execution counts refer to separate frozen reports. This check performs no reference executions, owner acceptance, universal identifiability proof or training admission.",
    })
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
