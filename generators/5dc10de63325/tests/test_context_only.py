"""Small integrity and known-shortcut fixtures for accepted-context scoring."""
from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


TOOL_PATH = Path(__file__).resolve().parents[1] / "workspace/score_context_only.py"
SPEC = importlib.util.spec_from_file_location("cyan_accepted_context_tool", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def fixture_census():
    task = TOOL.TASK_ID
    source_hash = "a" * 64
    manifest = {"task_id": task, "files": [{
        "library_path": f"generators/{task}/generator.py", "sha256": source_hash,
    }]}
    lessons = []
    for start in range(4):
        q = [(start + i) % 4 + 1 for i in range(4)]
        pairs = [{"input": [[value]], "output": deepcopy(TOOL.GLYPHS[value])} for value in q]
        trace = [{"split": "train" if i < 3 else "test", "pair_index": i if i < 3 else 0,
                  "sample_index": i, "input_sha256": TOOL.digest(pair["input"])} for i, pair in enumerate(pairs)]
        instance = {
            "task_id": task, "rule_task_id": task, "rule_file": "fixture-rule",
            "seed": start, "sample_index": 0, "train": pairs[:3], "test": pairs[3:],
            "sampling": {"schema": "arcpuzzles-pair-sampling-v1", "accepted_pairs": trace},
        }
        lessons.append({"band": "fixture", "index": start, "seed": start, "sample_index": 0,
                        "instance": instance, "instance_sha256": TOOL.digest(instance), "errors": [], "rotations": []})
    return {
        "schema": "arcpuzzles-lesson-census-v1", "task_id": task, "rule_task_id": task,
        "rule_file": "fixture-rule", "generator_sha256": source_hash,
        "status": "no_ambiguity_found", "production_status": "no_ambiguity_found",
        "rotation_status": "not_requested", "errors": [],
        "execution": {"exit_code": 0, "timed_out": False},
        "runtime_manifest": manifest,
        "runtime_manifest_sha256": hashlib.sha256((json.dumps(manifest, indent=2) + "\n").encode()).hexdigest(),
        "lessons": lessons,
        "summary": {"requested": 4, "materialized": 4, "pairs": 16, "rotations": 0,
                    "materialization_errors": 0, "scoring_errors": 0, "rotation_scoring_errors": 0},
        "per_band": {"fixture": {"requested": 4, "materialized": 4}},
        "sampler": {"n_demos": 3, "n_queries": 1, "rotate_query": False, "per_band": 4,
                    "bands": ["fixture"], "authority": "synthetic unit fixture, not executed Racket"},
    }


def test_three_demo_period_four_missing_glyph_is_perfect_even_after_holdouts():
    result = TOOL.score_census(fixture_census())
    original = result["original_query"]["only_missing_q_else_abstain"]
    rotated = result["query_rotations"]["only_missing_q_else_abstain"]
    assert (original["correct"], original["episodes"]) == (4, 4)
    assert (rotated["correct"], rotated["episodes"]) == (16, 16)
    assert "only_missing_q_else_abstain" in result["perfect_predictors_in_sample"]["original_query"]
    assert result["population"]["accepted_pairs"] == 16
    assert result["population"]["new_racket_executions"] == 0


def test_unknown_output_glyph_rejects_instead_of_counting_its_color():
    census = fixture_census()
    row = census["lessons"][0]
    row["instance"]["train"][0]["output"] = [[0] * 5 for _ in range(5)]
    row["instance_sha256"] = TOOL.digest(row["instance"])
    with pytest.raises(ValueError, match="four fixed cyan glyphs"):
        TOOL.score_census(census)


@pytest.mark.parametrize("failure", ("incomplete", "recorded_error", "broken_accepted_trace"))
def test_incomplete_errored_or_unbound_evidence_fails_loudly(failure):
    census = fixture_census()
    if failure == "incomplete":
        census["summary"]["requested"] = 5
    elif failure == "recorded_error":
        census["errors"] = ["fixture materializer failed"]
    else:
        row = census["lessons"][0]
        row["instance"]["sampling"]["accepted_pairs"].pop()
        row["instance_sha256"] = TOOL.digest(row["instance"])
    with pytest.raises(ValueError):
        TOOL.score_census(census)


def test_json_and_gzip_cli_reuse_the_same_labels_and_error_reports(tmp_path):
    data = json.dumps(fixture_census()).encode()
    plain, packed = tmp_path / "census.json", tmp_path / "census.json.gz"
    plain.write_bytes(data)
    packed.write_bytes(gzip.compress(data))
    outputs = []
    for i, source in enumerate((plain, packed)):
        target = tmp_path / f"scores-{i}.json"
        assert TOOL.main(["--input", str(source), "--out", str(target)]) == 0
        outputs.append(json.loads(target.read_text()))
    assert outputs[0]["input_census"]["json_bytes_sha256"] == outputs[1]["input_census"]["json_bytes_sha256"]
    assert outputs[0]["original_query"] == outputs[1]["original_query"]
    assert outputs[0]["query_rotations"] == outputs[1]["query_rotations"]
    bad = tmp_path / "incomplete.json"
    broken = fixture_census()
    broken["status"] = "incomplete"
    bad.write_text(json.dumps(broken))
    target = tmp_path / "error.json"
    assert TOOL.main(["--input", str(bad), "--out", str(target)]) == 2
    result = json.loads(target.read_text())
    assert result["status"] == "error" and result["errors"]
