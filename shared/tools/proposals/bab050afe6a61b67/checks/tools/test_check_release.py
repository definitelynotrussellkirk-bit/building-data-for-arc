"""Small synthetic tests for release consistency; no native execution claims."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


CHECKER = Path(__file__).with_name("check_release.py")
EXECUTORS = ("parametric_promotion.py", "parametric_worker.py", "catalog.py", "runtime.py", "parametric_priority.py")


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw(value))


@pytest.fixture
def checker():
    if not CHECKER.is_file():
        return None
    spec = importlib.util.spec_from_file_location("tested_release_checker", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def release(tmp_path):
    work, root = tmp_path, tmp_path / "repo"
    for name in EXECUTORS:
        path = root / "src/arcpuzzles" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("raise AssertionError('release checker must not import repository code')\n")
    for name in ("reviewer_support.py", "arc_repl/racket_bridge.py", "arc_repl/racket_prelude/arc-prelude.rkt"):
        path = root / "shared/runtime" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("hash-only source fixture\n")
    exporter = work / "checks/tools/export_qualified.py"
    exporter.parent.mkdir(parents=True)
    exporter.write_text("raise AssertionError('release checker must not import exporter code')\n")
    catalog, canonical, targets, artifacts = [], [], [], {}
    for tid in ("fixture_a", "fixture_b"):
        home = root / "generators" / tid
        base = home / "workspace/parametric"
        base.mkdir(parents=True)
        for path in (home / "generator.py", base / "adapter.py"):
            path.write_text("raise AssertionError('release checker must not import task code')\n")
        programs = {"a": "(lambda (g) g)", "b": "(lambda (g) (reverse g))"}
        contract = {"schema": "arcpuzzles-parametric-adapter-v1",
                    "adapter": (base / "adapter.py").relative_to(root).as_posix(),
                    "parameters": {"kind": ["a", "b"]}, "default": {"kind": "a"},
                    "limits": {"demos": [2, 6], "queries": [1, 4]}}
        put(base / "promotion.json", contract)
        genhash = sha((home / "generator.py").read_bytes())
        rulehash = sha(" ".join(programs["a"].split()).encode())[:12]
        catalog.append({"id": tid, "generator": f"generators/{tid}/generator.py"})
        canonical.append({"task_id": tid, "program_solution": programs["a"]})
        sources = [home / "generator.py", base / "adapter.py", base / "promotion.json"]
        sources += [p for p in (root / "shared/runtime").rglob("*") if p.is_file()]
        binding = {"task_id": tid, "rule_task_id": tid, "generator_sha256": genhash,
                   "rule_hash": rulehash, "canonical_program_sha256": sha(programs["a"].encode()),
                   "files": [{"path": p.relative_to(root).as_posix(), "sha256": sha(p.read_bytes())}
                             for p in sorted(sources)],
                   "executor": {name: sha((root / "src/arcpuzzles" / name).read_bytes()) for name in EXECUTORS}}
        jobs, episodes, checks = [], [], []
        for kind in ("a", "b"):
            for seed in (17, 29):
                setting = {"kind": kind}
                pairs = [{"input": [[i, seed % 10]], "output": [[i]]} for i in range(1, 7)]
                jobs.append({"settings": setting, "seed": seed, "demos": 2, "queries": 4})
                episodes.append({"task_id": tid, "seed": seed, "settings": setting, "train": pairs[:2],
                                 "test": pairs[2:], "program": programs[kind],
                                 "program_sha256": sha(programs[kind].encode()), "reference": "accepted_parametric"})
                checks.append({"settings": setting, "seed": seed, "counts": {"demos": 2, "queries": 4},
                               "survivors": [setting], "label_count": 6})
        identity = {"schema": "arc-protected-racket-runtime-v1", "backend": "racket", "protected": True,
                    "binary_sha256": "a" * 64, "boot_script_sha256": "b" * 64,
                    "candidate_symbol_policy_sha256": "c" * 64,
                    "bridge_sha256": sha((root / "shared/runtime/arc_repl/racket_bridge.py").read_bytes()),
                    "prelude_sha256": sha((root / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt").read_bytes())}
        directory = work / "checks" / tid
        qpath, epath = directory / "qualification/qualification.json", directory / "qualification/execution.json"
        execution = {"episodes": episodes, "checks": checks, "racket": identity, "racket_evaluations": 32}
        put(epath, execution)
        qualification = {"schema": "arcpuzzles-parametric-qualification-v1", "status": "qualified", "task_id": tid,
                         "source_binding": binding, "contract": contract, "jobs": jobs,
                         "programs": {raw({"kind": k}).decode().strip(): sha(p.encode()) for k, p in programs.items()},
                         "execution": {"path": "execution.json", "sha256": sha(epath.read_bytes())}, "training_admitted": False}
        put(qpath, qualification)
        proof = base / "evidence/current-native/proof.json"
        put(proof, {"reported": True})
        files = [home / "generator.py", base / "adapter.py", base / "promotion.json", proof]
        inventory = {"schema": "arcpuzzles-parametric-prototype-evidence-v1", "task_id": tid,
                     "generator_sha256": genhash, "canonical_rule_hash": rulehash, "rule_task_id": tid,
                     "canonical_program_sha256": binding["canonical_program_sha256"],
                     "parameters": contract["parameters"], "default": contract["default"], "limits": contract["limits"],
                     "training_admitted": False, "verification_status": "reviewer_reported",
                     "files": [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())} for p in files]}
        ipath = base / "evidence/manifest.json"
        put(ipath, inventory)
        dependency = {k: "authored fixture " + k for k in ("step_a", "intermediate", "step_b", "why_b_depends_on_a")}
        episode = episodes[0]
        case = {"input": episode["test"][0]["input"], "output": episode["test"][0]["output"],
                "settings": episode["settings"], "program": episode["program"],
                "counterfactual_program": "(lambda (g) '((0)))", "counterfactual_output": [[0]],
                "intermediate_value": [[1]], "ablation": "wrong_intermediate",
                "qualified_case": {"episode_index": 0, "split": "test", "pair_index": 0}}
        witness = {"schema": "arcpuzzles-sequential-dependency-witness-v1", "source_binding": binding,
                   "racket": {"backend": "racket", "protected": True}, **dependency, "cases": [case]}
        wpath, rpath = directory / "causal/witness.json", directory / "causal/replay.json"
        put(wpath, witness)
        replay = {"schema": "arcpuzzles-reviewer-witness-check-v1", "status": "reviewer_replayed", "task_id": tid,
                  "source_binding": binding, "qualification_sha256": sha(qpath.read_bytes()),
                  "witness_sha256": sha(wpath.read_bytes()), "training_admitted": False, "owner_acceptance": "not_performed",
                  "replay": {"status": "reviewer_replayed", "racket": identity, "evaluations": 2,
                             "cases": [{"index": 0, "input": case["input"], "output": case["output"],
                                        "counterfactual_output": case["counterfactual_output"],
                                        "program_sha256": sha(case["program"].encode()),
                                        "counterfactual_program_sha256": sha(case["counterfactual_program"].encode())}]}}
        put(rpath, replay)
        export_dir = directory / "qualified-export"
        payloads, turns = {}, []
        for index, query in enumerate(episode["test"]):
            public = raw({"train": episode["train"], "test": [{"input": query["input"]}]})
            public_id = sha(public)
            path = f"actor/{public_id}.json"
            payloads[path] = public
            turns.append({"turn_index": index, "actor_path": path, "public_id": public_id, **query})
        controller = {"schema": "arc-qualified-single-query-controller-v1", "status": "qualified_owner_acceptance_pending",
                      "accepted": False, "training_admitted": False, "task_id": tid, "seed": episode["seed"],
                      "settings": episode["settings"], "program": episode["program"], "program_sha256": episode["program_sha256"],
                      "train": episode["train"], "queries": turns,
                      "qualification_sha256": sha(qpath.read_bytes()), "execution_sha256": sha(epath.read_bytes())}
        payloads[f"private/controllers/{sha(raw(controller))}.json"] = raw(controller)
        for name, data in payloads.items():
            path = export_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        manifest = {"schema": "arc-qualified-single-query-export-v1", "status": "qualified_owner_acceptance_pending",
                    "accepted": False, "training_admitted": False, "owner_acceptance": "pending", "task_id": tid,
                    "qualification_path": qpath.relative_to(work).as_posix(), "qualification_sha256": sha(qpath.read_bytes()),
                    "execution_sha256": sha(epath.read_bytes()), "source_binding_sha256": sha(raw(binding)), "racket": identity,
                    "controller_count": 1, "controller_queries": 4, "actor_file_count": 4, "seeds": [17], "demos": [2],
                    "exporter_sha256": sha(exporter.read_bytes()),
                    "files": [{"path": p, "sha256": sha(b)} for p, b in sorted(payloads.items())]}
        mpath = export_dir / "manifest.json"
        put(mpath, manifest)
        before = directory / "review-regression-before.json"
        put(before, {"source_binding": {"files": [{"path": "old.py", "sha256": "0" * 64}]}, "passed": False})
        progress = {"status": "ready", "promotion_path": (base / "promotion.json").relative_to(work).as_posix(),
                    "inventory_path": ipath.relative_to(work).as_posix(), "qualification_path": qpath.relative_to(work).as_posix(),
                    "sequential_dependency": {**dependency, "witness_path": wpath.relative_to(work).as_posix()}}
        targets.append({"task_id": tid, "parametric_work": progress,
                        "evidence_paths": [p.relative_to(work).as_posix() for p in (qpath, epath, wpath, rpath, mpath, before)]})
        artifacts[tid] = {"q": qpath, "e": epath, "i": ipath, "w": wpath, "r": rpath, "m": mpath,
                          "proof": proof, "adapter": base / "adapter.py"}
    for name, rows in (("catalog/puzzles.jsonl", catalog), ("shared/data/canonical/puzzles.jsonl", canonical)):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"".join(raw(row) for row in rows))
    results = work / "RESULTS.json"
    put(results, {"repair_targets": targets})
    return {"root": root, "results": results, "artifacts": artifacts}


def check(checker, release):
    assert checker is not None, "release consistency checker is missing"
    return checker.check_release(release["root"], release["results"])


def test_checks_all_final_evidence_without_import_or_replay(checker, release):
    report = check(checker, release)
    assert report["status"] == "consistent", report["findings"]
    assert report["findings"] == []
    assert report["racket_replay_performed"] is False
    assert report["owner_acceptance_performed"] is False
    assert report["training_admitted"] is False
    assert report["task_ids"] == ["fixture_a", "fixture_b"]
    assert len(report["hashed_files"]) == report["hashed_file_count"] > 30
    assert all(row["sha256"] == sha((release["root"].parent / row["path"]).read_bytes()) for row in report["hashed_files"])
    assert any("review-regression-before.json" in row["path"] for row in report["hashed_files"])


@pytest.mark.parametrize("kind", ["adapter", "new_source", "executor", "inventory", "execution", "witness_program", "replay_program", "projection", "public_leak"])
def test_detects_tamper_and_stale_final_evidence(checker, release, kind):
    a = release["artifacts"]["fixture_a"]
    if kind == "new_source":
        a["adapter"].with_name("new_native_source.py").write_text("# added after qualification\n")
    elif kind in {"adapter", "executor", "inventory", "execution"}:
        path = {"adapter": a["adapter"], "executor": release["root"] / "src/arcpuzzles/parametric_worker.py",
                "inventory": a["proof"], "execution": a["e"]}[kind]
        path.write_bytes(path.read_bytes() + b" \n")
    elif kind == "witness_program":
        witness = json.loads(a["w"].read_bytes())
        witness["cases"][0]["program"] = "(lambda (g) '((9)))"
        put(a["w"], witness)
        replay = json.loads(a["r"].read_bytes())
        replay["witness_sha256"] = sha(a["w"].read_bytes())
        put(a["r"], replay)
    elif kind == "replay_program":
        replay = json.loads(a["r"].read_bytes())
        replay["replay"]["cases"][0]["program_sha256"] = "0" * 64
        put(a["r"], replay)
    else:
        manifest = json.loads(a["m"].read_bytes())
        prefix = "private/controllers/" if kind == "projection" else "actor/"
        row = next(item for item in manifest["files"] if item["path"].startswith(prefix))
        path = a["m"].parent / row["path"]
        payload = json.loads(path.read_bytes())
        if kind == "projection":
            payload["queries"][0]["output"] = [[9]]
        else:
            payload["test"][0]["output"] = [[3]]
        data = raw(payload)
        old_path = row["path"]
        renamed = path.with_name(sha(data) + ".json")
        path.unlink()
        renamed.write_bytes(data)
        row.update(path=renamed.relative_to(a["m"].parent).as_posix(), sha256=sha(data))
        if kind == "public_leak":
            # Rehash every link too: only the forbidden actor output field
            # should make the otherwise self-consistent export fail.
            for other in manifest["files"]:
                if not other["path"].startswith("private/controllers/"):
                    continue
                old = a["m"].parent / other["path"]
                controller = json.loads(old.read_bytes())
                for turn in controller["queries"]:
                    if turn["actor_path"] == old_path:
                        turn.update(actor_path=row["path"], public_id=row["sha256"])
                changed = raw(controller)
                replacement = old.with_name(sha(changed) + ".json")
                old.unlink()
                replacement.write_bytes(changed)
                other.update(path=replacement.relative_to(a["m"].parent).as_posix(), sha256=sha(changed))
        put(a["m"], manifest)
    report = check(checker, release)
    assert report["status"] == "inconsistent"
    assert report["findings"]


def test_requires_final_export_to_be_explicit_results_evidence(checker, release):
    results = json.loads(release["results"].read_bytes())
    row = results["repair_targets"][0]
    row["evidence_paths"] = [p for p in row["evidence_paths"] if "qualified-export" not in p]
    put(release["results"], results)
    assert check(checker, release)["status"] == "inconsistent"


def test_cli_writes_actual_report_to_a_fresh_path(release):
    argv = [sys.executable, str(CHECKER), "--root", ".", "--results", "../RESULTS.json",
            "--out", "../checks/release.json"]
    result = subprocess.run(argv, cwd=release["root"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr + result.stdout
    output = release["root"].parent / "checks/release.json"
    original = output.read_bytes()
    report = json.loads(original)
    assert report["findings"] == []
    assert json.loads(result.stdout)["hashed_file_count"] == report["hashed_file_count"]
    repeated = subprocess.run(argv, cwd=release["root"], capture_output=True, text=True, timeout=30)
    assert repeated.returncode != 0
    assert output.read_bytes() == original
