"""Meaningful synthetic cases: the reference is identity; rival is constant zero."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).resolve().parents[1]


def tool():
    path = TOOL_DIR / "shortcut_coverage.py"
    assert path.is_file(), "The shortcut coverage implementation is not present yet"
    spec = importlib.util.spec_from_file_location("shortcut_coverage_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pair(value):
    return {"input": [[value]], "output": [[value]]}


def constant_zero(grid):
    return [[0]]


@pytest.mark.parametrize("case", json.loads((TOOL_DIR / "fixtures/synthetic_windows.json").read_text()))
def test_actual_refutation_counts_and_holdouts(case):
    coverage = tool()
    pairs = [pair(value) for value in case["values"]]
    result = coverage.score_window(pairs[:4], pairs[4], {"CANONICAL_SHORTCUTS:under_generalized": constant_zero})
    metric = result["shortcuts"]["CANONICAL_SHORTCUTS:under_generalized"]
    assert metric["demo_refutations"] == case["demo_refutations"]
    assert metric["window_refutations"] == case["window_refutations"]
    assert metric["query_matches"] == case["query_matches"]
    assert metric["rotation_robust"] == case["rotation_robust"]
    assert metric["holdout_demo_refutations"] == case["holdout_demo_refutations"]


def test_rival_exception_is_unknown_not_counterexample():
    coverage = tool()
    def broken(grid):
        raise ValueError("synthetic rival failure")
    result = coverage.score_window([pair(0)] * 4, pair(0), {"CANONICAL_SHORTCUTS:broken": broken})
    metric = result["shortcuts"]["CANONICAL_SHORTCUTS:broken"]
    assert metric["demo_refutations"] is None
    assert metric["rotation_robust"] is None
    assert len(metric["errors"]) == 5


def test_mutating_rival_cannot_change_saved_labels_or_next_prediction():
    coverage = tool()
    pairs = [pair(value) for value in [1, 2, 0, 0, 0]]
    before = copy.deepcopy(pairs)
    def mutating(grid):
        grid[0][0] = 9
        return grid
    result = coverage.score_window(pairs[:4], pairs[4], {
        "CANONICAL_SHORTCUTS:mutating": mutating,
        "CANONICAL_SHORTCUTS:under_generalized": constant_zero,
    })
    assert pairs == before
    assert result["shortcuts"]["CANONICAL_SHORTCUTS:under_generalized"]["demo_refutations"] == 2


def test_only_actual_canonical_namespace_is_discovered():
    coverage = tool()
    report = {"rivals": ["LESSON_COMPETITORS:extra", "CANONICAL_SHORTCUTS:arbitrary_name", "SEMANTIC_RIVALS:extra"]}
    assert coverage.discover_shortcuts(report) == ["CANONICAL_SHORTCUTS:arbitrary_name"]


def test_changed_source_bytes_are_rejected(tmp_path):
    coverage = tool()
    source = tmp_path / "generator.py"
    source.write_text("CANONICAL_SHORTCUTS = {}\n")
    original = coverage.file_hash(source)
    source.write_text("CANONICAL_SHORTCUTS = {}\n# changed\n")
    with pytest.raises(coverage.CoverageError, match="hash mismatch"):
        coverage.require_file_hash(source, original, "generator")


def make_report(coverage):
    instance = {"train": [pair(0)] * 4, "test": [pair(0)]}
    return {"schema": "arcpuzzles-lesson-census-v1", "task_id": "synthetic_fixture",
            "generator_sha256": "0" * 64, "rule_source_sha256": "1" * 64,
            "rule_callable_sha256": "2" * 64, "declared_rule_hash": "1" * 12,
            "rivals": ["CANONICAL_SHORTCUTS:under_generalized"],
            "sampler": {"n_demos": 4, "n_queries": 1}, "errors": [],
            "lessons": [{"index": 0, "band": "synthetic", "seed": 0, "sample_index": 0,
                         "instance": instance, "instance_sha256": coverage.json_hash(instance),
                         "rivals": {"CANONICAL_SHORTCUTS:under_generalized": "survived_all"}, "errors": []}]}


def test_survived_all_in_saved_report_does_not_waive_teaching(tmp_path):
    coverage = tool()
    report = make_report(coverage)
    path = tmp_path / "synthetic.json.gz"
    with gzip.open(path, "wt") as stream:
        json.dump(report, stream)
    loaded = coverage.read_census(path)
    result = coverage.analyze_census(loaded, {"CANONICAL_SHORTCUTS:under_generalized": constant_zero})
    assert result["status"] == "coverage_gaps"
    assert result["summary"]["unrefuted_demo_rows"] == 1
    assert result["summary"]["rotation_fragile_rows"] == 1
    assert result["lessons"][0]["shortcuts"]["CANONICAL_SHORTCUTS:under_generalized"]["saved_outcome"] == "survived_all"


def test_corrupted_instance_is_not_silently_scored():
    coverage = tool()
    report = make_report(coverage)
    report["lessons"][0]["instance"]["train"][0]["output"] = [[3]]
    result = coverage.analyze_census(report, {"CANONICAL_SHORTCUTS:under_generalized": constant_zero})
    assert result["status"] == "incomplete_evidence"
    assert result["summary"]["complete_lessons"] == 0
    assert "instance hash mismatch" in result["lessons"][0]["error"]


def test_missing_query_label_is_incomplete_even_with_matching_instance_hash():
    coverage = tool()
    report = make_report(coverage)
    del report["lessons"][0]["instance"]["test"][0]["output"]
    report["lessons"][0]["instance_sha256"] = coverage.json_hash(report["lessons"][0]["instance"])
    result = coverage.analyze_census(report, {"CANONICAL_SHORTCUTS:under_generalized": constant_zero})
    assert result["status"] == "incomplete_evidence"
    assert result["summary"]["complete_lessons"] == 0


def test_inventory_disagreement_cannot_be_reported_as_coverage():
    coverage = tool()
    with pytest.raises(coverage.CoverageError, match="inventory mismatch"):
        coverage.analyze_census(make_report(coverage), {"CANONICAL_SHORTCUTS:renamed": constant_zero})
