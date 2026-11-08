"""Focused behavior tests for the native target-waypoint parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "7ce16af847d6"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
MODES = ("canonical", "bridge_centers")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _modules():
    return _load("targets_family_tests", HOME / "family.py"), _load("targets_adapter_tests", HOME / "adapter.py")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str)}
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_contract_and_exact_canonical_default():
    family, adapter = _modules()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": list(MODES)}
    assert contract["default"] == {"mode": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert adapter.program({"mode": "canonical"}) == _canonical_program()
    assert family.program({"mode": "canonical"}) == _canonical_program()


@pytest.mark.parametrize("seed", [0, 17, 211])
def test_inputs_are_matched_distinct_and_setting_is_taught(seed):
    family, adapter = _modules()
    episodes = {mode: adapter.generate(seed, {"mode": mode}, demos=2, queries=4) for mode in MODES}
    assert _inputs(episodes["canonical"]) == _inputs(episodes["bridge_centers"])
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episodes["canonical"])}) == 6
    for mode, episode in episodes.items():
        survivors = [candidate for candidate in MODES if all(family.transform(pair["input"], candidate) == pair["output"] for pair in episode["train"])]
        assert survivors == [mode]
        assert family.teaching_audit(episode)["query_disagreeing_named_survivors"] == []


@pytest.mark.parametrize("mode", MODES)
def test_counts_are_prefix_stable_and_copy_isolated(mode):
    _, adapter = _modules()
    full = adapter.generate(431, {"mode": mode}, demos=6, queries=4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(431, {"mode": mode}, demos=demos, queries=queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]
    small = adapter.generate(431, {"mode": mode}, demos=2, queries=1)
    small["train"][0]["input"][0][0] = 9
    assert adapter.generate(431, {"mode": mode}, demos=2, queries=1)["train"][0]["input"][0][0] != 9


def test_bridge_consumes_stage_a_targets_and_skip_a_changes_output():
    family, adapter = _modules()
    pair = adapter.generate(97, {"mode": "bridge_centers"}, demos=2, queries=4)["test"][0]
    trace = family.dependency_trace(pair["input"])
    assert trace["intermediate"] == family.transform(pair["input"], "canonical")
    assert trace["output"] == pair["output"]
    assert trace["skip_a_output"] != trace["output"]
    assert trace["derived_waypoints"] >= 2


def test_30x30_query_is_substantive_and_rule_sensitive():
    family, adapter = _modules()
    grid = adapter.generate(20261025, {"mode": "bridge_centers"}, demos=3, queries=4)["test"][3]["input"]
    facts = family.analyse(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["targets"] >= 4
    assert facts["blue_distractors"] >= 5
    assert facts["nonzero"] >= 90
    assert family.transform(grid, "canonical") != family.transform(grid, "bridge_centers")


@pytest.mark.parametrize("settings", [None, {}, {"mode": True}, {"mode": "other"}, {"mode": "canonical", "extra": 1}])
def test_invalid_settings_reject(settings):
    _, adapter = _modules()
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize("seed,demos,queries", [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5), (0, True, 4), (0, 2, True)])
def test_invalid_request_controls_reject(seed, demos, queries):
    _, adapter = _modules()
    with pytest.raises(ValueError):
        adapter.generate(seed, {"mode": "canonical"}, demos=demos, queries=queries)
