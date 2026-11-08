"""Small schema fixtures are synthetic tests, never reported census evidence."""
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "workspace" / "audit_rival_coverage.py"
spec = importlib.util.spec_from_file_location("task_rival_coverage", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture():
    names = ["SEMANTIC_RIVALS:same_name", "LESSON_COMPETITORS:same_name"]
    pair = {"input": [[1]], "output": [[2]]}
    instance = {"train": [pair], "test": [deepcopy(pair)]}
    scores = {names[0]: "survived_all", names[1]: "refuted"}
    row = {"band": "easy", "index": 0, "instance": instance,
           "instance_sha256": digest(instance), "rivals": scores,
           "errors": [], "ambiguous": False,
           "rotations": [{"query_index": i, "train_indices": [1-i],
                          "rivals": dict(scores), "errors": [], "ambiguous": False}
                         for i in range(2)]}
    return {"schema": "arcpuzzles-lesson-census-v1", "task_id": "747486860e56",
            "generator_sha256": "a"*64, "rule_source_sha256": "b"*64,
            "rule_callable_sha256": "c"*64, "rivals": names,
            "status": "no_ambiguity_found", "production_status": "no_ambiguity_found",
            "rotation_status": "no_ambiguity_found", "errors": [],
            "execution": {"timed_out": False, "exit_code": 0},
            "canonical_pairs": 2,
            "canonical_rival_fit": {name: {"pairs": 2, "fits": 1, "errors": [], "status": "refuted"}
                                    for name in names},
            "lessons": [row], "sampler": {"n_demos": 1, "n_queries": 1, "rotate_query": True,
                                           "bands": ["easy"], "per_band": 1},
            "per_band": {"easy": {"requested": 1, "materialized": 1}},
            "summary": {"requested": 1, "materialized": 1, "materialization_errors": 0,
                        "pairs": 2, "scoring_errors": 0, "rotations": 2,
                        "rotation_scoring_errors": 0}}


def test_gap_is_visible_despite_ambiguity_green_and_names_stay_distinct():
    report = audit.analyze(fixture())
    assert report["status"] == "finite_coverage_gap"
    assert report["coverage_gaps"] == ["SEMANTIC_RIVALS:same_name"]
    assert len(report["rivals"]) == 2
    assert report["rivals"]["LESSON_COMPETITORS:same_name"]["generated_refuted_lessons"] == 1


def test_canonical_fitting_survivor_is_not_a_coverage_gap():
    census = fixture()
    row = census["canonical_rival_fit"]["SEMANTIC_RIVALS:same_name"]
    row.update(fits=2, status="fits_all")
    assert audit.analyze(census)["status"] == "no_finite_coverage_gap_found"


@pytest.mark.parametrize("damage", ["incomplete", "errors", "missing_rival", "canonical_error",
                                    "missing_rotation", "wrong_instance_hash", "wrong_count", "malformed_rotation"])
def test_incomplete_or_inconsistent_receipts_never_pass(damage):
    census = fixture()
    if damage == "incomplete": census["status"] = "incomplete"
    elif damage == "errors": census["lessons"][0]["errors"] = ["rival crashed"]
    elif damage == "missing_rival": census["lessons"][0]["rivals"].pop(census["rivals"][0])
    elif damage == "canonical_error": census["canonical_rival_fit"][census["rivals"][0]]["errors"] = ["crashed"]
    elif damage == "missing_rotation": census["lessons"][0]["rotations"].pop()
    elif damage == "wrong_instance_hash": census["lessons"][0]["instance_sha256"] = "0"*64
    elif damage == "malformed_rotation": census["lessons"][0]["rotations"][0] = []
    else: census["summary"]["pairs"] = 3
    with pytest.raises(ValueError): audit.analyze(census)


def rescore(census):
    return {"schema": "arcpuzzles-lesson-rescore-v1", "task_id": census["task_id"],
            "status": census["status"], "production_status": census["production_status"],
            "rotation_status": census["rotation_status"], "errors": [],
            "execution": census["execution"], "rival_source_stable": True,
            "input_generator_sha256": "d"*64, "rival_generator_sha256": census["generator_sha256"],
            "retained_rule_source_sha256": census["rule_source_sha256"],
            "retained_rule_callable_sha256": census["rule_callable_sha256"],
            "rival_summary": {name: {} for name in census["rivals"]},
            "lessons": deepcopy(census["lessons"]), "summary": {"lessons": 1, "rotations": 2}}


def test_rescore_requires_source_bound_canonical_join():
    canonical = fixture()
    receipt = rescore(canonical)
    with pytest.raises(ValueError): audit.analyze(receipt)
    assert audit.analyze(receipt, canonical)["status"] == "finite_coverage_gap"
    for key in ("generator_sha256", "rule_source_sha256", "rule_callable_sha256", "task_id"):
        wrong = deepcopy(canonical)
        wrong[key] = "e"*64
        with pytest.raises(ValueError): audit.analyze(receipt, wrong)


def test_cli_gzip_and_explicit_gap_exit_code(tmp_path):
    path, out = tmp_path / "fixture.json.gz", tmp_path / "summary.json"
    with gzip.open(path, "wt") as stream: json.dump(fixture(), stream)
    completed = subprocess.run([sys.executable, str(SCRIPT), str(path), "--out", str(out)],
                               capture_output=True, text=True)
    assert completed.returncode == 1, completed.stderr
    assert json.loads(out.read_text())["status"] == "finite_coverage_gap"
    assert json.loads(out.read_text())["input_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_cli_invalid_receipt_is_an_explicit_error(tmp_path):
    path, out = tmp_path / "fixture.json", tmp_path / "summary.json"
    path.write_text(json.dumps({"schema": "arcpuzzles-lesson-census-v1", "status": "incomplete"}))
    completed = subprocess.run([sys.executable, str(SCRIPT), str(path), "--out", str(out)], capture_output=True)
    assert completed.returncode == 2
    assert json.loads(out.read_text())["status"] == "error"


def test_actual_retained_census_when_available():
    # Optional real-receipt verification in this packet; no copied or fake run data.
    path = SCRIPT.parents[3].parent / "checks" / "lesson-census-v1.json"
    if not path.exists():
        pytest.skip("the original review census is not retained in this checkout")
    census = json.loads(path.read_text())
    report = audit.analyze(census)
    assert report["generated_lessons"] == census["summary"]["materialized"]
    assert report["generated_pair_occurrences"] == census["summary"]["pairs"]
    assert set(report["rivals"]) == set(census["rivals"])
