"""Compare the frozen source, native evidence and exported payloads; no Racket rerun."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
TASK = "8de1c257a9c7"
HOME = ROOT / "generators" / TASK / "workspace/parametric"
CHECKS = ROOT.parent / "checks" / TASK


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def module(name):
    spec = importlib.util.spec_from_file_location("binding_check_" + name, HOME / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


def main():
    qpath = CHECKS / "qualification/qualification.json"
    q = read(qpath)
    execution_path = qpath.with_name("execution.json")
    execution = read(execution_path)
    assert q["status"] == "qualified" and q["task_id"] == TASK
    assert q["execution"]["sha256"] == sha(execution_path)
    assert q["training_admitted"] is False
    for row in q["source_binding"]["files"]:
        assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
    for name, expected in q["source_binding"]["executor"].items():
        assert sha(ROOT / "src/arcpuzzles" / name) == expected, name
    inventory = read(HOME / "evidence/manifest.json")
    for row in inventory["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], row["path"]
    assert inventory["builder_executed_checks"] is False
    assert inventory["training_admitted"] is False
    audit = read(CHECKS / "native-audit-final/report.json")
    assert audit["status"] == "passed" and audit["runtime"] == execution["racket"]
    for row in audit["source_files"]:
        assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
    audit_episodes = read(CHECKS / "native-audit-final/episodes.private.json")
    audited_labels = {(row["program_sha256"], row["input_sha256"]): row["output_sha256"]
                      for row in read(CHECKS / "native-audit-final/executions.json")}
    assert len(audited_labels) == audit["racket_evaluations"]
    for row in audit["episodes"]:
        assert row["certificate"]["survivors"] == ["setting:" + row["settings"]["stamp_transform"]]
        assert row["certificate_sha256_before_queries"] == row["certificate_sha256_after_queries"]
    for episode in audit_episodes:
        native = next(e for e in execution["episodes"]
                      if e["seed"] == episode["seed"] and e["settings"] == episode["settings"])
        count = min(len(native["train"]), len(episode["train"]))
        assert native["train"][:count] == episode["train"][:count]
        assert native["test"] == episode["test"]
        assert native["program"] == episode["program_solution"]
        for pair in episode["train"] + episode["test"]:
            assert audited_labels[(native["program_sha256"], digest(pair["input"]))] == digest(pair["output"])
    examples = read(CHECKS / "examples-report.json")
    bundle = CHECKS / "examples"
    manifest = read(bundle / "manifest.json")
    assert manifest["status"] == "complete" and manifest["training_admitted"] is False
    assert examples["manifest_sha256"] == sha(bundle / "manifest.json")
    assert examples["source_sha256"] == manifest["source_sha256"]
    assert examples["racket"] == execution["racket"]
    for name, expected in examples["source_sha256"].items():
        assert sha(ROOT / name) == expected, name
    actual_files = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    assert actual_files == set(manifest["files"]) | {"manifest.json"}
    for name, expected in manifest["files"].items():
        path = bundle / name
        assert path.stat().st_size == expected["bytes"] and sha(path) == expected["sha256"], name
        if name.startswith(("controller/", "onequery/")):
            assert path.stem == sha(path), name
    exporter = module("export")
    rows = [json.loads(line) for line in (bundle / "private/metadata.jsonl").read_text().splitlines()]
    for row in rows:
        episode = row["episode"]
        native = next(e for e in execution["episodes"]
                      if e["seed"] == episode["seed"] and e["settings"] == episode["settings"])
        assert all(episode[k] == native[k] for k in ("train", "test", "program", "program_sha256"))
        assert episode["private"]["racket"] == execution["racket"]
        assert episode["private"]["native_acceptance"] == "owner_pending"
        authored = episode["private"]["adapter_episode"]
        assert authored["train"] == native["train"] and authored["test"] == native["test"]
        assert authored["program_solution"] == native["program"]
        controller = {"train": episode["train"], "test": [{"input": p["input"]} for p in episode["test"]]}
        assert (bundle / "controller" / (row["public_id"] + ".json")).read_bytes() == exporter.public_challenge_bytes(controller)
        for index, turn in enumerate(row["turn_ids"]):
            assert (bundle / "onequery" / (turn + ".json")).read_bytes() == exporter.public_challenge_bytes(exporter.public_turn(episode, index))
    witness_path = CHECKS / "causal/witness.json"
    witness, replay = read(witness_path), read(CHECKS / "causal/replay.json")
    assert witness["source_binding"] == q["source_binding"] == replay["source_binding"]
    assert replay["qualification_sha256"] == sha(qpath)
    assert replay["witness_sha256"] == sha(witness_path)
    assert replay["status"] == "reviewer_replayed" and replay["owner_acceptance"] == "not_performed"
    assert replay["construction"]["racket"] == execution["racket"]
    assert replay["replay"]["racket"] == execution["racket"]
    for case in witness["cases"]:
        assert case["output"] != case["counterfactual_output"]
        if "expected_counterfactual_output" in case["intermediate_value"]:
            assert case["counterfactual_output"] == case["intermediate_value"]["expected_counterfactual_output"]
    legacy = read(CHECKS / "legacy-count-shortcut.json")
    audit_module = module("audit_native")
    for row in legacy["episodes"]:
        assert row["rival_program"] == audit_module.rival_program(row["rival_name"], row["settings"])
    geometry = read(CHECKS / "geometry-gate-native.json")
    assert geometry["status"] == "passed" and geometry["episodes_passed"] == len(rows)
    assert geometry["checker_sha256"] == sha(HOME / "check_geometry_gate.py")
    assert geometry["source_sha256"] == sha(bundle / "private/metadata.jsonl")
    report = {
        "schema": "stamp-final-binding-check-v1", "status": "passed", "findings": [],
        "task_id": TASK, "qualification_files": len(q["source_binding"]["files"]),
        "executor_files": len(q["source_binding"]["executor"]),
        "inventory_files": len(inventory["files"]), "audit_source_files": len(audit["source_files"]),
        "export_source_files": len(examples["source_sha256"]), "export_payload_files": len(manifest["files"]),
        "qualified_episodes": len(execution["episodes"]), "qualification_evaluations": execution["racket_evaluations"],
        "audit_evaluations": audit["racket_evaluations"], "export_evaluations": examples["racket_evaluations"],
        "causal_cases": len(witness["cases"]), "causal_construction_evaluations": replay["construction"]["evaluations"],
        "causal_replay_evaluations": replay["replay"]["evaluations"],
        "legacy_count_programs_match_current": True,
        "scope": "Current source/hash, exact saved-label and payload comparisons only; no additional Racket execution or owner acceptance. Legacy helper hash remains its historical capture; exact retained rival program strings still match current programs.",
        "owner_acceptance": "not_performed", "training_admitted": False,
    }
    with (CHECKS / "final-binding.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
