#!/usr/bin/env python3
"""Compare a task-local export with its execution and independent audit bindings.

This read-only check does not execute a reference rule, prove identifiability,
replace check_public_exports.py, or grant native acceptance/training admission.
It emits a private verification report for the controller/reviewer.
"""
import argparse
import hashlib
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inspect(repo, bundle, execution_path, audit_path):
    repo, bundle = Path(repo).resolve(), Path(bundle).resolve()
    execution, audit = read_json(execution_path), read_json(audit_path)
    manifest = read_json(bundle / "manifest.json")
    findings = []

    def require(condition, detail):
        if not condition:
            findings.append(detail)

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def check_binding(binding, label):
        for name, expected in binding.items():
            path = repo / name
            require(path.resolve().is_relative_to(repo) and path.is_file()
                    and not path.is_symlink() and digest(path) == expected,
                    f"{label} source differs: {name}")

    source_binding, audit_binding = execution["source_sha256"], audit["source_files_sha256"]
    check_binding(source_binding, "export")
    check_binding(audit_binding, "audit")
    common = sorted(set(source_binding) & set(audit_binding))
    require(all(source_binding[name] == audit_binding[name] for name in common),
            "Export and audit disagree on a shared source hash")
    require(execution["racket"] == audit["racket"], "Export and audit Racket identities differ")
    require(execution["racket"].get("backend") == "racket"
            and execution["racket"].get("protected") is True, "Execution identity is not protected Racket")
    require(audit["status"] == "passed", "The bound independent audit did not pass")
    require(manifest.get("complete") is True, "The export manifest is incomplete")
    require(manifest.get("native_acceptance") == execution.get("native_acceptance") == "owner_pending",
            "Acceptance must remain owner_pending")
    require(manifest.get("training_admitted") is execution.get("training_admitted") is False,
            "Training admission must remain false")

    actual_files = {path.relative_to(bundle).as_posix(): path for path in bundle.rglob("*") if path.is_file()}
    actual_files.pop("manifest.json", None)
    require(set(actual_files) == set(manifest["files"]), "Manifest file inventory differs from saved files")
    for name, expected in manifest["files"].items():
        path = actual_files.get(name)
        require(path is not None and not path.is_symlink() and digest(path) == expected,
                f"Saved file hash differs: {name}")

    rows = [json.loads(line) for line in (bundle / "private/metadata.jsonl").read_text().splitlines()]
    require(len(rows) == manifest["episodes"] == len(execution["settings"]), "Episode count differs")
    require(sorted(row["public_id"] for row in rows) == execution["public_ids"], "Public identifier list differs")
    turn_ids = [turn for row in rows for turn in row["turn_ids"]]
    require(sorted(turn_ids) == execution["turn_ids"] and len(turn_ids) == manifest["turns"],
            "Actor-turn identifier list differs")
    settings = lambda values: sorted(json.dumps(value, sort_keys=True) for value in values)
    require(settings(row["episode"]["settings"] for row in rows) == settings(execution["settings"]),
            "Declared setting coverage differs")
    inputs = []
    query_shapes = []
    for row in rows:
        episode, private = row["episode"], row["episode"]["private"]
        require(private["source_sha256"] == source_binding, "Private source binding differs")
        require(private["racket"] == execution["racket"], "Private Racket identity differs")
        require(private["native_acceptance"] == "owner_pending" and private["training_admitted"] is False,
                "Private acceptance/admission flags differ")
        require(private["demo_only_certificate"]["survivors"] == [episode["settings"]],
                "Declared-setting certificate has a different survivor")
        require(episode["reference"] == "protected_racket_pending_acceptance", "Private reference label differs")
        require(hashlib.sha256(episode["program"].encode()).hexdigest() == episode["program_sha256"],
                "Private program bytes differ from their hash")
        require(len(episode["train"]) == execution["demos"] and len(episode["test"]) == execution["queries"],
                "Private demonstration/query count differs")
        controller = read_json(bundle / "public" / (row["public_id"] + ".json"))
        require(controller == {"train": episode["train"], "test": [{"input": p["input"]} for p in episode["test"]]},
                "Controller payload differs from private episode projection")
        for index, turn_id in enumerate(row["turn_ids"]):
            turn = read_json(bundle / "turns" / (turn_id + ".json"))
            require(turn == {"train": episode["train"], "test": [{"input": episode["test"][index]["input"]}]},
                    "Actor turn differs from its one-query private projection")
        inputs.append([pair["input"] for pair in episode["train"] + episode["test"]])
        query_shapes.append([[len(p["input"]), len(p["input"][0])] for p in episode["test"]])
        require(all(len(pair["output"]) == 3 and all(len(r) == 6 for r in pair["output"])
                    for pair in episode["train"] + episode["test"]), "An output is not the fixed 3x6 emblem")
    require(all(value == inputs[0] for value in inputs), "Input bank differs across declared settings")
    return {
        "schema": "e971e0773705-export-integrity-v1", "visibility": "controller_private",
        "status": "failed" if findings else "passed", "findings": findings,
        "episodes": len(rows), "actor_turns": len(turn_ids), "demonstrations": execution["demos"],
        "queries": execution["queries"], "query_shapes_by_episode": query_shapes,
        "manifest_files_checked": len(manifest["files"]), "export_sources_checked": len(source_binding),
        "audit_sources_checked": len(audit_binding), "shared_sources_checked": len(common),
        "protected_example_evaluations": execution["racket_evaluations"],
        "native_acceptance": "owner_pending", "training_admitted": False,
        "scope": "Saved bytes, private/public projection, and current-source/identity agreement only. Reference execution and finite identifiability are established by the separately bound execution/audit reports.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.repo, args.bundle, args.execution, args.audit)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
