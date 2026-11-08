"""Behavioral tests for the portable, fail-closed evidence-joining CLI."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

CLI = Path(__file__).resolve().parents[1] / "workspace" / "verify_lesson_evidence.py"
TASK = "fixture_task"
RIVALS = ["fixture:arbitrary_one", "fixture:another_rival"]
ZERO_COUNTS = ("materialization_errors", "ambiguous", "hook_warnings",
               "scoring_errors", "ambiguous_rotations", "rotation_hook_warnings",
               "rotation_scoring_errors")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def score():
    return {"rivals": dict.fromkeys(RIVALS, "refuted"), "ambiguous": False,
            "warnings": [], "errors": [], "contract": "rivals",
            "searched_rivals": {"candidates": {}, "provider_status": "not_declared",
                                "errors": [], "truncated": False, "ambiguous": False}}


def report(source_hash, schedule):
    bands, period, demos, queries = ["easy", "hard"], 2, 2, 1
    lessons = []
    for band in bands:
        for index in range(period):
            seed = 41 if schedule else 100 + 10 * bands.index(band) + index
            pairs = [{"input": [[(index + j) % 8 + 1]], "output": [[0]]}
                     for j in range(demos + queries)]
            instance = {
                "task_id": TASK, "rule_task_id": TASK, "rule_file": "data/rule.json",
                "seed": seed, "sample_index": index,
                "train": pairs[:demos], "test": pairs[demos:],
                "sampling": {
                    "schema": "arcpuzzles-pair-sampling-v1", "requested_start": index,
                    "next_sample_index": index + len(pairs), "attempted_pairs": len(pairs),
                    "rejections": [],
                    "accepted_pairs": [
                        {"split": "train" if j < demos else "test",
                         "pair_index": j if j < demos else j - demos,
                         "sample_index": index + j, "input_sha256": digest(pair["input"])}
                        for j, pair in enumerate(pairs)],
                },
            }
            lesson = dict(score(), band=band, index=index, seed=seed, sample_index=index,
                          instance=instance, instance_sha256=digest(instance))
            lesson["rotations"] = [
                dict(score(), query_index=q, train_indices=[j for j in range(len(pairs)) if j != q])
                for q in range(len(pairs))]
            lessons.append(lesson)
    count, pair_count = len(lessons), len(lessons) * (demos + queries)
    per_band = {
        band: {"requested": period, "materialized": period,
               "pairs": period * (demos + queries), "rotations": period * (demos + queries),
               **dict.fromkeys(ZERO_COUNTS, 0),
               "rivals": {name: {"refuted": period} for name in RIVALS}}
        for band in bands
    }
    manifest = {
        "schema": "arcpuzzles-runtime-v1", "task_id": TASK, "task_ids": [TASK],
        "files": [
            {"library_path": f"generators/{TASK}/generator.py",
             "runtime_path": f"puzzle_generators/per_puzzle/{TASK}/generator.py", "sha256": source_hash},
            {"library_path": "shared/data/rule.json", "runtime_path": "data/rule.json", "sha256": "d" * 64}],
    }
    result = {
        "schema": "arcpuzzles-lesson-census-v1", "task_id": TASK,
        "generator_sha256": source_hash, "declared_rule_hash": "a" * 12,
        "rule_source_sha256": "b" * 64, "rule_callable_sha256": "c" * 64,
        "rule_task_id": TASK, "rule_file": "data/rule.json",
        "contract": "rivals", "rivals": RIVALS[:], "errors": [], "lessons": lessons,
        "per_band": per_band, "status": "no_ambiguity_found",
        "production_status": "no_ambiguity_found", "rotation_status": "no_ambiguity_found",
        "rotation_policy": "require",
        "summary": {"requested": count, "materialized": count, "pairs": pair_count,
                    "rotations": pair_count, **dict.fromkeys(ZERO_COUNTS, 0)},
        "sampler": {"task_id": TASK, "per_band": period, "n_demos": demos,
                    "n_queries": queries, "period": 6, "bands": bands,
                    "rotate_query": True, "rotation_policy": "require",
                    "enumerate_schedule_period": schedule, "schedule_seed": 41},
        "limits": ["Fixture report: does not run or certify a rule."],
        "declared_schedule_period": period, "reporting_residue_modulus": 6,
        "enumerated_schedule_period": period if schedule else None,
        "warnings": [] if schedule else ["Declared short schedule was not explicitly enumerated"],
        "runtime_manifest": manifest, "runtime_manifest_sha256": digest(manifest),
        "execution": {"exit_code": 0, "timed_out": False, "stderr": ""},
        "materializer_rejection_logs": {}, "catalog_provenance": {"rule_hash": "a" * 12, "approved": False},
    }
    if schedule:
        result["schedule_coverage"] = {
            "status": "complete_fixed_seed", "contract": "LESSON_SCHEDULE_PERIOD",
            "period": period, "seed": 41, "bands": bands[:],
            "generator_sha256": source_hash, "rule_source_sha256": "b" * 64,
            "expected_lessons": count, "expected_rotations": pair_count,
        }
    return result


@pytest.fixture
def inputs(tmp_path):
    source = tmp_path / "generator.py"
    source.write_text(
        'GENERATOR_ID = "fixture_task"\nTASK_ID = GENERATOR_ID\n'
        'RULE_HASH = "aaaaaaaaaaaa"\nLESSON_SCHEDULE_PERIOD = 2\nEXAMPLES_NEEDED = 2\n'
        'raise RuntimeError("verifier must not execute generator code")\n')
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    return source, report(sha, False), report(sha, True)


def invoke(tmp_path, inputs, *, output=False):
    source, random_report, schedule_report = inputs
    random_path, schedule_path = tmp_path / "random.json", tmp_path / "schedule.json"
    random_path.write_text(json.dumps(random_report))
    schedule_path.write_text(json.dumps(schedule_report))
    args = [sys.executable, str(CLI), "--generator", str(source),
            "--random-census", str(random_path), "--schedule-census", str(schedule_path)]
    if output:
        args += ["--output", str(tmp_path / "receipt.json")]
    proc = subprocess.run(args, cwd=tmp_path, text=True, capture_output=True)
    return proc, json.loads(proc.stdout) if proc.stdout else None


def test_valid_pair_emits_bounded_receipt_without_executing_source(tmp_path, inputs):
    proc, receipt = invoke(tmp_path, inputs, output=True)
    assert proc.returncode == 0, proc.stderr
    assert receipt["status"] == "evidence_verified"
    assert receipt["task_id"] == TASK
    assert receipt["rival_count"] == len(RIVALS)
    assert receipt["random_census"]["lessons"] == 4
    assert receipt["schedule_census"]["rotations"] == 12
    assert receipt["schedule_census"]["start_residues"] == [0, 1]
    assert receipt["schedule_census"]["query_positions"] == [0, 1, 2]
    assert receipt["global_approval"] is False
    assert receipt["shared_semantic_gate"]["resolved"] is False
    assert receipt["shared_semantic_gate"]["warning"] == "declared_period_not_enumerated"
    assert receipt["limits"]
    assert json.loads((tmp_path / "receipt.json").read_text()) == receipt


def test_source_change_rejects_old_reports_and_replaces_prior_receipt(tmp_path, inputs):
    (tmp_path / "receipt.json").write_text('{"status":"evidence_verified"}')
    inputs[0].write_text(inputs[0].read_text() + "# current source changed\n")
    proc, receipt = invoke(tmp_path, inputs, output=True)
    assert proc.returncode != 0
    assert receipt["status"] == "rejected"
    assert "generator_sha256" in receipt["error"]
    assert json.loads((tmp_path / "receipt.json").read_text())["status"] == "rejected"


@pytest.mark.parametrize("field,value", [
    ("generator_sha256", "e" * 64), ("rule_source_sha256", "e" * 64),
    ("rule_callable_sha256", "e" * 64), ("declared_rule_hash", "e" * 12),
    ("task_id", "other"), ("rule_task_id", "other"), ("rule_file", "data/other.json"),
])
def test_mismatched_binding_is_rejected(tmp_path, inputs, field, value):
    inputs[2][field] = value
    proc, receipt = invoke(tmp_path, inputs)
    assert proc.returncode != 0 and receipt["status"] == "rejected"
    assert field in receipt["error"]


@pytest.mark.parametrize("field", ZERO_COUNTS)
@pytest.mark.parametrize("report_index", [1, 2])
def test_nonzero_error_counters_are_rejected(tmp_path, inputs, field, report_index):
    inputs[report_index]["summary"][field] = 1
    proc, receipt = invoke(tmp_path, inputs)
    assert proc.returncode != 0 and field in receipt["error"]


@pytest.mark.parametrize("location", ["lesson", "rotation"])
@pytest.mark.parametrize("field,value", [("errors", ["scoring failed"]),
                                         ("warnings", ["hook failed"]), ("ambiguous", True)])
def test_nested_scoring_problems_cannot_hide_behind_zero_summary(tmp_path, inputs, location, field, value):
    node = inputs[2]["lessons"][0]
    if location == "rotation":
        node = node["rotations"][0]
    node[field] = value
    proc, receipt = invoke(tmp_path, inputs)
    assert proc.returncode != 0 and field in receipt["error"]


@pytest.mark.parametrize("change", ["missing_rotation", "duplicate_query", "query_in_training",
                                   "missing_lesson", "duplicate_residue", "wrong_seed",
                                   "wrong_period", "missing_band", "wrong_expected_total"])
def test_incomplete_schedule_is_rejected_even_with_success_status(tmp_path, inputs, change):
    schedule = inputs[2]
    if change == "missing_rotation":
        schedule["lessons"][0]["rotations"].pop()
    elif change == "duplicate_query":
        schedule["lessons"][0]["rotations"][1]["query_index"] = 0
    elif change == "query_in_training":
        schedule["lessons"][0]["rotations"][0]["train_indices"] = [0, 1]
    elif change == "missing_lesson":
        schedule["lessons"].pop()
    elif change == "duplicate_residue":
        schedule["lessons"][1] = copy.deepcopy(schedule["lessons"][0])
    elif change == "wrong_seed":
        schedule["lessons"][0]["seed"] = 99
    elif change == "wrong_period":
        schedule["enumerated_schedule_period"] = 6
    elif change == "missing_band":
        schedule["schedule_coverage"]["bands"].pop()
    else:
        schedule["schedule_coverage"]["expected_rotations"] = 9
    proc, receipt = invoke(tmp_path, inputs)
    assert proc.returncode != 0 and receipt["status"] == "rejected"


@pytest.mark.parametrize("change", ["rotation_policy", "nested_policy", "not_enumerated", "summary_count",
                                   "band_count", "missing_rival", "unrefuted_rival", "failed_execution",
                                   "timeout", "manifest_hash", "unknown_schema", "bool_counter",
                                   "missing_error_counter", "searched_error", "rejections"])
def test_malformed_or_incomplete_evidence_is_rejected(tmp_path, inputs, change):
    data = inputs[2]
    if change == "rotation_policy":
        data["rotation_policy"] = "advisory"
    elif change == "nested_policy":
        data["sampler"]["rotation_policy"] = "advisory"
    elif change == "not_enumerated":
        data["sampler"]["enumerate_schedule_period"] = False
    elif change == "summary_count":
        data["summary"]["materialized"] = 3
    elif change == "band_count":
        data["per_band"]["easy"]["rotations"] = 0
    elif change == "missing_rival":
        data["lessons"][0]["rivals"].pop(RIVALS[0])
    elif change == "unrefuted_rival":
        data["lessons"][0]["rotations"][0]["rivals"][RIVALS[0]] = "ambiguous"
    elif change == "failed_execution":
        data["execution"]["exit_code"] = 1
    elif change == "timeout":
        data["execution"]["timed_out"] = True
    elif change == "manifest_hash":
        data["runtime_manifest"]["files"][0]["sha256"] = "f" * 64
    elif change == "unknown_schema":
        data["schema"] = "future-schema"
    elif change == "bool_counter":
        data["summary"]["scoring_errors"] = False
    elif change == "missing_error_counter":
        del data["summary"]["hook_warnings"]
    elif change == "searched_error":
        data["lessons"][0]["searched_rivals"]["errors"] = ["provider failed"]
    else:
        data["lessons"][0]["instance"]["sampling"]["rejections"] = [{"reason": "bad pair"}]
    proc, receipt = invoke(tmp_path, inputs)
    assert proc.returncode != 0 and receipt["status"] == "rejected"


def test_duplicate_json_keys_are_rejected(tmp_path, inputs):
    source, random_report, schedule_report = inputs
    random_path, schedule_path = tmp_path / "random.json", tmp_path / "schedule.json"
    random_path.write_text('{"schema":"wrong","schema":"arcpuzzles-lesson-census-v1"}')
    schedule_path.write_text(json.dumps(schedule_report))
    proc = subprocess.run([sys.executable, str(CLI), "--generator", str(source),
                           "--random-census", str(random_path), "--schedule-census", str(schedule_path)],
                          text=True, capture_output=True)
    assert proc.returncode != 0
    assert "duplicate" in json.loads(proc.stdout)["error"].lower()


def test_boolean_training_index_is_not_an_integer_position(tmp_path, inputs):
    inputs[2]["lessons"][0]["rotations"][0]["train_indices"] = [True, 2]
    proc, receipt = invoke(tmp_path, inputs)
    assert proc.returncode != 0
    assert receipt["status"] == "rejected"
    assert "train_indices" in receipt["error"]
