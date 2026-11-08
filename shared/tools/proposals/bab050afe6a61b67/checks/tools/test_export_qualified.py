"""Evidence-only export boundary tests; fixtures are synthetic, not qualification.

The fixture copies the packet's native verifier code and public-byte helper but
never generates or labels a puzzle. Adapter import and binary execution cannot
succeed in the fixture. These tests therefore prove export behavior only.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


TOOLS = Path(__file__).resolve().parent
PACKET_REPO = TOOLS.parents[1] / "repo"
EXPORTER = TOOLS / "export_qualified.py"
TASK = "synthetic_export_fixture"
EXECUTORS = ("parametric_promotion.py", "parametric_worker.py", "catalog.py",
             "runtime.py", "parametric_priority.py")


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw(value))


@pytest.fixture
def exporter():
    if not EXPORTER.is_file():
        return None
    spec = importlib.util.spec_from_file_location("tested_qualified_export", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(PACKET_REPO / "src/arcpuzzles", root / "src/arcpuzzles",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    runtime = root / "shared/runtime"
    for name in ("reviewer_support.py", "arc_repl/__init__.py",
                 "arc_repl/racket_bridge.py", "arc_repl/security.py",
                 "arc_repl/parser.py", "arc_repl/racket_prelude/arc-prelude.rkt"):
        target = runtime / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PACKET_REPO / "shared/runtime" / name, target)
    generator = root / f"generators/{TASK}/generator.py"
    generator.parent.mkdir(parents=True)
    generator.write_text("raise AssertionError('export must not import a generator')\n")
    home = generator.parent / "workspace/parametric"
    home.mkdir(parents=True)
    (home / "adapter.py").write_text("raise AssertionError('export must not import the adapter')\n")
    programs = {"a": "(lambda (grid) grid)", "b": "(lambda (grid) (reverse grid))"}
    contract = {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK}/workspace/parametric/adapter.py",
        "parameters": {"direction": ["a", "b"]},
        "default": {"direction": "a"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }
    put(home / "promotion.json", contract)
    generator_hash = digest(generator.read_bytes())
    rule_hash = digest(" ".join(programs["a"].split()).encode())[:12]
    put(root / "catalog/puzzles.jsonl", {
        "id": TASK, "generator": generator.relative_to(root).as_posix(),
        "train_safety": "reviewed_safe", "mix_weight": 1,
        "reviewed_generator_sha256": generator_hash, "reviewed_rule_hash": rule_hash,
    })
    put(root / "shared/data/canonical/puzzles.jsonl", {
        "task_id": TASK, "program_solution": programs["a"], "train": [], "test": [],
    })
    put(home / "evidence/manifest.json", {
        "task_id": TASK, "generator_sha256": generator_hash,
        "canonical_rule_hash": rule_hash, "verification_status": "reviewer_reported",
        "parameters": contract["parameters"],
        "files": [{"path": contract["adapter"], "sha256": digest((home / "adapter.py").read_bytes())}],
    })
    sources = [generator, home / "promotion.json", home / "adapter.py"]
    sources.extend(p for p in runtime.rglob("*") if p.is_file() and p.suffix in {".py", ".rkt", ".json"})
    binding = {
        "task_id": TASK, "rule_task_id": TASK, "generator_sha256": generator_hash,
        "rule_hash": rule_hash, "canonical_program_sha256": digest(programs["a"].encode()),
        "files": [{"path": p.relative_to(root).as_posix(), "sha256": digest(p.read_bytes())}
                  for p in sorted(sources)],
        "executor": {name: digest((root / "src/arcpuzzles" / name).read_bytes()) for name in EXECUTORS},
    }
    # Pure imports from this packet, without instantiating a Racket bridge.
    from arc_repl.racket_bridge import _BOOT_SCRIPT
    from arc_repl.security import policy_sha256
    binary = tmp_path / "hash-only-racket-fixture"
    binary.write_bytes(b"synthetic non-executable binary identity fixture\n")
    identity = {
        "schema": "arc-protected-racket-runtime-v1", "backend": "racket", "protected": True,
        "binary_sha256": digest(binary.read_bytes()),
        "prelude_sha256": digest((runtime / "arc_repl/racket_prelude/arc-prelude.rkt").read_bytes()),
        "bridge_sha256": digest((runtime / "arc_repl/racket_bridge.py").read_bytes()),
        "boot_script_sha256": digest(_BOOT_SCRIPT.encode()),
        "candidate_symbol_policy_sha256": policy_sha256(),
    }
    jobs, episodes, checks = [], [], []
    for option in ("a", "b"):
        for seed in (17, 29):
            setting = {"direction": option}
            job = {"seed": seed, "settings": setting, "demos": 2, "queries": 4}
            jobs.append(job)
            pairs = [{"input": [[i, seed % 10]], "output": [[(i + (option == "b")) % 10]]}
                     for i in range(1, 7)]
            episodes.append({"task_id": TASK, "seed": seed, "settings": setting,
                             "train": pairs[:2], "test": pairs[2:], "program": programs[option],
                             "program_sha256": digest(programs[option].encode()),
                             "reference": "accepted_parametric"})
            checks.append({"settings": setting, "seed": seed, "counts": {"demos": 2, "queries": 4},
                           "survivors": [setting], "label_count": 6})
    execution = {"episodes": episodes, "checks": checks, "racket": identity,
                 "racket_evaluations": 32}
    evidence = tmp_path / "qualification"
    put(evidence / "execution.json", execution)
    qualification = {
        "schema": "arcpuzzles-parametric-qualification-v1", "status": "qualified", "task_id": TASK,
        "source_binding": binding, "contract": contract, "jobs": jobs,
        "programs": {raw({"direction": k}).decode().strip(): digest(v.encode()) for k, v in programs.items()},
        "execution": {"path": "execution.json", "sha256": digest(raw(execution))},
        "limits": "Synthetic export fixture; this is not protected-execution evidence.",
        "training_admitted": False,
    }
    put(evidence / "qualification.json", qualification)
    return {"root": root, "qualification": evidence / "qualification.json",
            "execution": evidence / "execution.json", "binary": binary,
            "q": qualification, "e": execution, "out": tmp_path / "export"}


def export(exporter, bundle, **kwargs):
    assert exporter is not None, "qualification-to-single-query export tool is missing"
    return exporter.export_qualified(bundle["qualification"], kwargs.pop("output", bundle["out"]),
                                     root=bundle["root"], task_id=TASK,
                                     racket_binary=bundle["binary"], **kwargs)


def rewrite_execution(bundle):
    put(bundle["execution"], bundle["e"])
    bundle["q"]["execution"]["sha256"] = digest(bundle["execution"].read_bytes())
    put(bundle["qualification"], bundle["q"])


def test_projects_only_current_query_with_exact_public_byte_ids(exporter, bundle):
    report = export(exporter, bundle, seeds=[17])
    assert report["status"] == "qualified_owner_acceptance_pending"
    assert report["accepted"] is False
    assert report["training_admitted"] is False
    assert report["controller_count"] == 2
    assert report["controller_queries"] == 4
    public_files = sorted((bundle["out"] / "actor").glob("*.json"))
    assert public_files
    for path in public_files:
        public = json.loads(path.read_bytes())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 2
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert path.stem == digest(path.read_bytes())
        assert path.read_bytes() == raw(public)
    controllers = list((bundle["out"] / "private/controllers").glob("*.json"))
    assert len(controllers) == 2
    for path in controllers:
        controller = json.loads(path.read_bytes())
        assert controller["seed"] == 17
        assert len(controller["queries"]) == 4
        assert controller["program"] in {"(lambda (grid) grid)", "(lambda (grid) (reverse grid))"}
        for query in controller["queries"]:
            actor_path = bundle["out"] / query["actor_path"]
            assert query["public_id"] == digest(actor_path.read_bytes())
            actor = json.loads(actor_path.read_bytes())
            assert actor["test"] == [{"input": query["input"]}]
            assert "output" in query
    assert json.loads((bundle["out"] / "manifest.json").read_bytes()) == report


def test_first_turn_bytes_do_not_encode_requested_future_count(exporter, bundle):
    one = bundle["out"].with_name("one-query")
    four = bundle["out"].with_name("four-queries")
    export(exporter, bundle, output=one, queries=1, seeds=[17])
    export(exporter, bundle, output=four, queries=4, seeds=[17])
    def first_turns(directory):
        result = {}
        for path in (directory / "private/controllers").glob("*.json"):
            controller = json.loads(path.read_bytes())
            first = controller["queries"][0]
            result[controller["settings"]["direction"]] = (directory / first["actor_path"]).read_bytes()
        return result
    assert first_turns(one) == first_turns(four)
    assert all(len(json.loads(b)["test"]) == 1 for b in first_turns(four).values())


def test_cli_supports_documented_repo_relative_evidence_paths(bundle):
    result = subprocess.run([
        sys.executable, str(EXPORTER), "--root", ".", "--task-id", TASK,
        "--qualification", "../qualification/qualification.json", "--out", "../cli-export",
        "--racket-binary", "../hash-only-racket-fixture", "--seed", "17",
    ], cwd=bundle["root"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["controller_count"] == 2
    assert report["controller_queries"] == 4
    assert Path(report["manifest"]).is_file()


@pytest.mark.parametrize("queries", [True, False, 1.0, "4", 0, -1, 5])
def test_rejects_invalid_requested_query_counts_before_writing(exporter, bundle, queries):
    with pytest.raises(ValueError):
        export(exporter, bundle, queries=queries)
    assert not bundle["out"].exists()


@pytest.mark.parametrize("seeds", [[True], [17.0], ["17"], [-1], [2**63], [], [17, 17], [999]])
def test_rejects_invalid_or_unqualified_seed_selection(exporter, bundle, seeds):
    with pytest.raises(ValueError):
        export(exporter, bundle, seeds=seeds)
    assert not bundle["out"].exists()


def test_rejects_changed_execution_bytes(exporter, bundle):
    bundle["execution"].write_bytes(bundle["execution"].read_bytes() + b" ")
    with pytest.raises(ValueError):
        export(exporter, bundle)
    assert not bundle["out"].exists()


@pytest.mark.parametrize("kind", ["adapter", "executor", "canonical", "extra_source"])
def test_rejects_changed_current_source_binding(exporter, bundle, kind):
    root = bundle["root"]
    if kind == "adapter":
        path = root / f"generators/{TASK}/workspace/parametric/adapter.py"
    elif kind == "executor":
        path = root / "src/arcpuzzles/parametric_worker.py"
    elif kind == "canonical":
        path = root / "shared/data/canonical/puzzles.jsonl"
        row = json.loads(path.read_bytes())
        row["program_solution"] += " ; changed canonical bytes"
        put(path, row)
        path = None
    else:
        path = root / f"generators/{TASK}/workspace/parametric/new_source.py"
    if path is not None:
        with path.open("ab") as handle:
            handle.write(b"\n# source changed after qualification\n")
    with pytest.raises(ValueError):
        export(exporter, bundle)
    assert not bundle["out"].exists()


@pytest.mark.parametrize("field", ["protected", "binary_sha256", "bridge_sha256", "prelude_sha256",
                                   "boot_script_sha256", "candidate_symbol_policy_sha256"])
def test_rejects_execution_identity_forgery_even_with_rehashed_execution(exporter, bundle, field):
    bundle["e"]["racket"][field] = False if field == "protected" else "0" * 64
    rewrite_execution(bundle)
    with pytest.raises(ValueError):
        export(exporter, bundle)
    assert not bundle["out"].exists()


@pytest.mark.parametrize("kind", ["seed_bool", "demos_float", "queries_bool", "label_count_float",
                                  "counts_float", "racket_evaluations_float", "grid_bool", "grid_float",
                                  "wrong_survivor", "wrong_program_hash", "duplicate_job", "missing_setting"])
def test_rejects_malformed_or_incomplete_native_evidence(exporter, bundle, kind):
    q, e = bundle["q"], bundle["e"]
    if kind == "seed_bool":
        q["jobs"][0]["seed"] = True
        e["episodes"][0]["seed"] = True
        e["checks"][0]["seed"] = True
    elif kind == "demos_float":
        q["jobs"][0]["demos"] = 2.0
    elif kind == "queries_bool":
        q["jobs"][0]["queries"] = True
    elif kind == "label_count_float":
        e["checks"][0]["label_count"] = 6.0
    elif kind == "counts_float":
        e["checks"][0]["counts"]["queries"] = 4.0
    elif kind == "racket_evaluations_float":
        e["racket_evaluations"] = 32.0
    elif kind in {"grid_bool", "grid_float"}:
        e["episodes"][0]["test"][0]["input"][0][0] = True if kind == "grid_bool" else 3.0
    elif kind == "wrong_survivor":
        e["checks"][0]["survivors"] = [{"direction": "b"}]
    elif kind == "wrong_program_hash":
        e["episodes"][0]["program_sha256"] = "0" * 64
    elif kind == "duplicate_job":
        q["jobs"][1] = copy.deepcopy(q["jobs"][0])
        e["episodes"][1] = copy.deepcopy(e["episodes"][0])
        e["checks"][1] = copy.deepcopy(e["checks"][0])
    else:
        q["jobs"] = q["jobs"][:2]
        e["episodes"] = e["episodes"][:2]
        e["checks"] = e["checks"][:2]
        e["racket_evaluations"] = 16
    rewrite_execution(bundle)
    with pytest.raises(ValueError):
        export(exporter, bundle)
    assert not bundle["out"].exists()


def test_rejects_existing_empty_output_directory(exporter, bundle):
    bundle["out"].mkdir()
    with pytest.raises(FileExistsError):
        export(exporter, bundle)
    assert list(bundle["out"].iterdir()) == []


def test_rejects_existing_output_without_overwriting(exporter, bundle):
    export(exporter, bundle)
    before = {p.relative_to(bundle["out"]): p.read_bytes()
              for p in bundle["out"].rglob("*") if p.is_file()}
    with pytest.raises(FileExistsError):
        export(exporter, bundle)
    assert {p.relative_to(bundle["out"]): p.read_bytes()
            for p in bundle["out"].rglob("*") if p.is_file()} == before


def test_rejects_symlinked_evidence(exporter, bundle):
    real = bundle["execution"].with_name("real-execution.json")
    bundle["execution"].rename(real)
    bundle["execution"].symlink_to(real.name)
    with pytest.raises(ValueError):
        export(exporter, bundle)
    assert not bundle["out"].exists()


def test_rejects_symlinked_output_parent(exporter, bundle):
    destination = bundle["out"].with_name("destination")
    destination.mkdir()
    link = bundle["out"].with_name("linked-output-parent")
    link.symlink_to(destination.name, target_is_directory=True)
    with pytest.raises(ValueError):
        export(exporter, bundle, output=link / "export")
    assert list(destination.iterdir()) == []


def test_requires_matching_expected_task(exporter, bundle):
    with pytest.raises(ValueError):
        exporter.export_qualified(bundle["qualification"], bundle["out"], root=bundle["root"],
                                  task_id="wrong_task", racket_binary=bundle["binary"])
    assert not bundle["out"].exists()


def test_manifest_is_absent_if_payload_write_fails(exporter, bundle, monkeypatch):
    # A disk failure is the only mocked external side effect; real data validation
    # and the first actor/controller writes run before the injected I/O exception.
    original = exporter._write_exclusive
    calls = []
    def failing_write(path, data):
        calls.append(path)
        if len(calls) == 2:
            raise OSError("simulated full disk")
        return original(path, data)
    monkeypatch.setattr(exporter, "_write_exclusive", failing_write)
    with pytest.raises(OSError, match="simulated full disk"):
        export(exporter, bundle)
    assert len(calls) == 2
    assert not (bundle["out"] / "manifest.json").exists()
    assert any(p.is_file() for p in bundle["out"].rglob("*"))
