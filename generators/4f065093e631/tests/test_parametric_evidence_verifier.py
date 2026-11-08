"""Mutation tests for the reusable parametric evidence verifier."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


def tool():
    root = find_root(__file__)
    path = root / "generators/4f065093e631/workspace/tools/verify_parametric_bundle.py"
    assert path.is_file(), "The independent bundle verifier has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_evidence_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_fixture(tmp_path):
    source = tmp_path / "source.py"
    source.write_text("# Exact fixture source\n")
    programs = {
        "keep": "(rule! (lambda (g) g))",
        "reverse": "(rule! (lambda (g) (map reverse g)))",
    }
    inputs = [[[1, 0], [0, 2]], [[3, 0], [4, 0]], [[5, 0], [0, 6]]]
    pairs = [
        {"id": f"p{i}", "role": "train" if i < 2 else "test", "input": grid,
         "output": copy.deepcopy(grid), "input_sha256": digest(grid), "output_sha256": digest(grid)}
        for i, grid in enumerate(inputs)
    ]
    public = {"train": [{"input": p["input"], "output": p["output"]} for p in pairs[:2]],
              "test": [{"input": pairs[2]["input"]}]}
    public_path = tmp_path / "challenge-001.json"
    public_path.write_text(json.dumps(public))
    manifest = {
        "schema": "fixture-parametric-evidence-v1", "task_id": "fixture", "parameter_name": "mode",
        "source_hashes": {"source.py": hashlib.sha256(source.read_bytes()).hexdigest()},
        "programs": {name: {"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
                     for name, text in programs.items()},
        "episodes": [{"id": "e1", "seed": 17, "parameters": {"mode": "keep"}, "pairs": pairs}],
        "public_challenges": [{"path": public_path.name, "episode_id": "e1",
                               "sha256": hashlib.sha256(public_path.read_bytes()).hexdigest()}],
    }
    return manifest, public_path


def persist(tmp_path, manifest):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(manifest))
    return path


def evaluate(program, grid):
    """Independent tiny rule evaluator for the two explicit fixture programs."""
    if program == "(rule! (lambda (g) g))":
        return copy.deepcopy(grid)
    if program == "(rule! (lambda (g) (map reverse g)))":
        return [list(reversed(row)) for row in grid]
    raise ValueError("Unexpected fixture program")


def run(tmp_path, manifest, **kwargs):
    return tool().verify_bundle(persist(tmp_path, manifest), root=tmp_path,
                                evaluator=evaluate, require_identified=True,
                                require_rotations=True, **kwargs)


def test_valid_bundle_is_recomputed_not_trusted(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    manifest["episodes"][0]["rivals"] = {"untrusted_claim": "ignored"}
    report = run(tmp_path, manifest)
    assert report["passed"], report
    assert report["executed_pairs"] == 6
    assert report["production_ambiguities"] == 0
    assert report["rotation_ambiguities"] == 0


@pytest.mark.parametrize("mutation", ["parameter", "query_answer", "program", "extra_train_key", "boolean", "float"])
def test_public_projection_rejects_hidden_data_even_when_hash_refreshed(tmp_path, mutation):
    manifest, public_path = write_fixture(tmp_path)
    public = json.loads(public_path.read_text())
    if mutation == "parameter":
        public["parameters"] = {"mode": "keep"}
    elif mutation == "query_answer":
        public["test"][0]["output"] = [[5, 0], [0, 6]]
    elif mutation == "program":
        public["reference_program"] = "(rule! (lambda (g) g))"
    elif mutation == "extra_train_key":
        public["train"][0]["private_hint"] = "keep"
    else:
        public["train"][0]["input"][0][0] = True if mutation == "boolean" else 1.0
    public_path.write_text(json.dumps(public))
    manifest["public_challenges"][0]["sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("public projection" in issue for issue in report["issues"])


@pytest.mark.parametrize("mutation", ["source", "program", "input", "output"])
def test_digest_drift_is_rejected(tmp_path, mutation):
    manifest, _ = write_fixture(tmp_path)
    if mutation == "source":
        (tmp_path / "source.py").write_text("changed source\n")
    elif mutation == "program":
        manifest["programs"]["keep"]["text"] += " "
    else:
        manifest["episodes"][0]["pairs"][0][mutation][0][0] = 9
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("sha256" in issue for issue in report["issues"])


def test_wrong_episode_parameter_is_detected_by_execution(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    manifest["episodes"][0]["parameters"]["mode"] = "reverse"
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert report["label_mismatches"] == 3


def test_unteaching_demonstrations_and_rotation_are_reported(tmp_path):
    manifest, public_path = write_fixture(tmp_path)
    pairs = manifest["episodes"][0]["pairs"]
    for pair in pairs[:2]:
        pair["input"] = pair["output"] = [[1, 1], [2, 2]]
        pair["input_sha256"] = pair["output_sha256"] = digest(pair["input"])
    public = {"train": [{"input": p["input"], "output": p["output"]} for p in pairs[:2]],
              "test": [{"input": pairs[2]["input"]}]}
    public_path.write_text(json.dumps(public))
    manifest["public_challenges"][0]["sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert report["production_ambiguities"] == 1
    assert report["rotation_ambiguities"] == 1


def test_duplicate_episode_and_missing_public_projection_fail(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    manifest["episodes"].append(copy.deepcopy(manifest["episodes"][0]))
    manifest["public_challenges"] = []
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("duplicate episode" in issue for issue in report["issues"])
    assert any("public challenge" in issue for issue in report["issues"])


def test_malformed_public_path_produces_a_failed_receipt(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    manifest["public_challenges"][0]["path"] = ["not", "a", "path"]
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("public challenge" in issue for issue in report["issues"])


def test_duplicate_json_key_cannot_hide_a_query_label_in_public_bytes(tmp_path):
    manifest, public_path = write_fixture(tmp_path)
    public_path.write_text('{"test":[{"input":[[1]],"output":[[9]]}],' + public_path.read_text()[1:])
    manifest["public_challenges"][0]["sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("duplicate JSON key" in issue for issue in report["issues"])


@pytest.mark.parametrize("field", ["parameter_name", "role"])
def test_malformed_semantic_fields_produce_failed_receipts(tmp_path, field):
    manifest, _ = write_fixture(tmp_path)
    if field == "parameter_name":
        manifest[field] = []
    else:
        manifest["episodes"][0]["pairs"][0][field] = []
    report = run(tmp_path, manifest)
    assert not report["passed"]


def test_declared_rule_file_drift_is_rejected(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    (tmp_path / "keep.rkt").write_text("(rule! (lambda (g) (map reverse g)))")
    manifest["programs"]["keep"]["path"] = "keep.rkt"
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("program file" in issue for issue in report["issues"])


def test_optional_episode_program_hash_must_match_selected_setting(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    manifest["episodes"][0]["program_sha256"] = "0" * 64
    report = run(tmp_path, manifest)
    assert not report["passed"]
    assert any("program binding" in issue for issue in report["issues"])


def test_real_racket_executes_the_recorded_programs(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    module = tool()
    with module.RacketEvaluator(timeout=10) as evaluator:
        report = module.verify_bundle(persist(tmp_path, manifest), root=tmp_path,
                                      evaluator=evaluator, require_identified=True,
                                      require_rotations=True)
        assert isinstance(evaluator.runtime_identity(), dict)
    assert report["passed"], report
    assert report["executed_pairs"] == 6


def test_structural_mode_does_not_claim_execution_or_identifiability(tmp_path):
    manifest, _ = write_fixture(tmp_path)
    report = tool().verify_bundle(persist(tmp_path, manifest), root=tmp_path)
    assert report["passed"], report
    assert report["execution_status"] == "not_run"
    assert report["production_ambiguities"] is None
    assert report["rotation_ambiguities"] is None
